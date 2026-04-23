"""Programmes router: full-season fertilizer programme CRUD and generation."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
from app.services.aggregation import AggregationResult, aggregate_samples
from app.supabase_client import get_supabase_admin, run_sb

router = APIRouter(tags=["Programmes"])


# ── Pydantic models ──────────────────────────────────────────────────────


class BlockCreate(BaseModel):
    field_id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    area_ha: float | None = Field(None, gt=0, le=100_000)
    crop: str = Field(..., min_length=1, max_length=200)
    cultivar: str | None = Field(None, max_length=200)
    yield_target: float | None = Field(None, gt=0, le=1_000_000)
    yield_unit: str | None = Field(None, max_length=50)
    tree_age: int | None = Field(None, ge=0, le=200)
    pop_per_ha: int | None = Field(None, gt=0, le=1_000_000)
    soil_analysis_id: str | None = None
    notes: str | None = None


class ProgrammeCreate(BaseModel):
    client_id: str | None = None
    farm_id: str | None = None
    name: str = Field(..., min_length=1, max_length=300)
    season: str | None = Field(None, max_length=50)
    status: str | None = Field(None, max_length=20)
    notes: str | None = None
    blocks: list[BlockCreate] = Field(default_factory=list)


class ProgrammeUpdate(BaseModel):
    name: str | None = Field(None, max_length=300)
    season: str | None = Field(None, max_length=50)
    status: str | None = Field(None, max_length=20)
    notes: str | None = None


class BlockUpdate(BaseModel):
    field_id: str | None = None
    name: str | None = Field(None, max_length=200)
    area_ha: float | None = Field(None, gt=0, le=100_000)
    crop: str | None = Field(None, max_length=200)
    cultivar: str | None = Field(None, max_length=200)
    yield_target: float | None = Field(None, gt=0, le=1_000_000)
    yield_unit: str | None = Field(None, max_length=50)
    tree_age: int | None = Field(None, ge=0, le=200)
    pop_per_ha: int | None = Field(None, gt=0, le=1_000_000)
    soil_analysis_id: str | None = None
    notes: str | None = None


# ── Helpers ──────────────────────────────────────────────────────────────


def _audit(sb, user: CurrentUser, action: str, record_id: str | None = None, detail: dict | None = None):
    try:
        sb.rpc("log_audit_event", {
            "p_event_type": action,
            "p_entity_type": "programmes",
            "p_entity_id": record_id,
            "p_metadata": detail or {},
            "p_user_id": user.id,
        }).execute()
    except Exception as _audit_exc:
        import logging as _logging
        _logging.getLogger("sapling.audit").debug(
            "log_audit_event failed: %s", _audit_exc, extra={"event_type": action}
        )


def _check_access(sb, programme_id: str, user: CurrentUser) -> dict:
    """Load a programme and verify access. Returns the programme dict.

    Wrapped in run_sb so transient httpx.ReadError from Supabase's
    HTTP/2 connection pool gets one retry before surfacing as a 500.
    Reproduced on /season-manager/[id] when the pool had stale conns.
    """
    result = run_sb(lambda: sb.table("programmes").select("*").eq(
        "id", programme_id
    ).is_("deleted_at", "null").execute())
    if not result.data:
        raise HTTPException(404, "Programme not found")
    prog = result.data[0]
    if prog["agent_id"] != user.id and user.role != "admin":
        raise HTTPException(403, "Access denied")
    return prog


# ── CRUD ─────────────────────────────────────────────────────────────────


@router.post("/", status_code=201)
def create_programme(body: ProgrammeCreate, user: CurrentUser = Depends(get_current_user)):
    """Create a new programme with optional initial blocks."""
    sb = get_supabase_admin()

    prog_data = {
        "agent_id": user.id,
        "client_id": body.client_id,
        "farm_id": body.farm_id,
        "name": body.name,
        "season": body.season,
        "notes": body.notes,
        "status": body.status if body.status in ("draft", "active") else "draft",
    }
    result = sb.table("programmes").insert(prog_data).execute()
    if not result.data:
        raise HTTPException(500, "Failed to create programme")
    programme = result.data[0]

    # Create blocks if provided
    blocks = []
    for block_data in body.blocks:
        block = block_data.model_dump(exclude_none=True)
        block["programme_id"] = programme["id"]

        # Auto-populate nutrient_targets from linked soil analysis
        if block.get("soil_analysis_id") and not block.get("nutrient_targets"):
            try:
                analysis = sb.table("soil_analyses").select("nutrient_targets").eq("id", block["soil_analysis_id"]).execute()
                if analysis.data and analysis.data[0].get("nutrient_targets"):
                    block["nutrient_targets"] = analysis.data[0]["nutrient_targets"]
            except Exception:
                pass  # Non-critical — targets can be added later

        block_result = sb.table("programme_blocks").insert(block).execute()
        if block_result.data:
            blocks.append(block_result.data[0])

    _audit(sb, user, "programme_create", programme["id"], {
        "name": body.name,
        "num_blocks": len(blocks),
    })

    programme["blocks"] = blocks
    return programme


class ProgrammeFromFieldsCreate(BaseModel):
    client_id: str
    farm_id: str
    name: str = Field(..., min_length=1, max_length=300)
    season: str | None = Field(None, max_length=50)
    notes: str | None = None
    field_ids: list[str] = Field(..., min_length=1)


@router.post("/from-fields", status_code=201)
def create_programme_from_fields(
    body: ProgrammeFromFieldsCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """Create a programme by selecting fields. Blocks are auto-populated from field data."""
    sb = get_supabase_admin()

    # Validate fields belong to the specified farm
    fields_result = (
        sb.table("fields")
        .select("*")
        .in_("id", body.field_ids)
        .eq("farm_id", body.farm_id)
        .execute()
    )
    fields = fields_result.data or []
    if len(fields) != len(body.field_ids):
        raise HTTPException(400, "Some field IDs are invalid or don't belong to this farm")

    # Create programme
    prog_data = {
        "agent_id": user.id,
        "client_id": body.client_id,
        "farm_id": body.farm_id,
        "name": body.name,
        "season": body.season,
        "notes": body.notes,
        "status": "draft",
    }
    result = sb.table("programmes").insert(prog_data).execute()
    if not result.data:
        raise HTTPException(500, "Failed to create programme")
    programme = result.data[0]

    # Create blocks from fields
    blocks = []
    for field in fields:
        block_data = {
            "programme_id": programme["id"],
            "field_id": field["id"],
            "name": field["name"],
            "area_ha": field.get("size_ha"),
            "crop": field.get("crop", ""),
            "cultivar": field.get("cultivar"),
            "yield_target": field.get("yield_target"),
            "yield_unit": field.get("yield_unit"),
            "tree_age": field.get("tree_age"),
            "pop_per_ha": field.get("pop_per_ha"),
            "soil_analysis_id": field.get("latest_analysis_id"),
        }

        # Auto-populate nutrient_targets from linked soil analysis
        if block_data.get("soil_analysis_id"):
            try:
                analysis = sb.table("soil_analyses").select("nutrient_targets").eq("id", block_data["soil_analysis_id"]).execute()
                if analysis.data and analysis.data[0].get("nutrient_targets"):
                    block_data["nutrient_targets"] = analysis.data[0]["nutrient_targets"]
            except Exception:
                pass

        block_result = sb.table("programme_blocks").insert(block_data).execute()
        if block_result.data:
            blocks.append(block_result.data[0])

    _audit(sb, user, "programme_create", programme["id"], {
        "name": body.name,
        "num_blocks": len(blocks),
        "from_fields": True,
    })

    programme["blocks"] = blocks
    return programme


@router.get("/")
def list_programmes(
    page: PageParams = Depends(PageParams.as_query),
    user: CurrentUser = Depends(get_current_user),
    client_id: str | None = Query(None, description="Filter by client ID"),
    farm_id: str | None = Query(None, description="Filter by farm ID"),
    status: str | None = Query(None, description="Filter by programme status"),
):
    """List programmes. Agents see own, admins see all."""
    sb = get_supabase_admin()

    query = sb.table("programmes").select(
        "*, programme_blocks(id, name, crop, area_ha, blend_group)",
        count="exact",
    ).is_("deleted_at", "null")

    if user.role != "admin":
        query = query.eq("agent_id", user.id)

    if client_id:
        query = query.eq("client_id", client_id)
    if farm_id:
        query = query.eq("farm_id", farm_id)
    if status:
        query = query.eq("status", status)

    query = apply_page(query, page, default_order="created_at")
    result = query.execute()
    return Page.from_result(result, page)


@router.get("/{programme_id}")
def get_programme(programme_id: str, user: CurrentUser = Depends(get_current_user)):
    """Get a programme with all blocks and blends."""
    sb = get_supabase_admin()
    prog = _check_access(sb, programme_id, user)

    # Load blocks
    blocks = sb.table("programme_blocks").select("*").eq("programme_id", programme_id).execute()
    prog["blocks"] = blocks.data or []

    # Load blends
    blends = sb.table("programme_blends").select("*").eq("programme_id", programme_id).execute()
    prog["blends"] = blends.data or []

    return prog


@router.patch("/{programme_id}")
def update_programme(
    programme_id: str,
    body: ProgrammeUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Update programme metadata. A status transition draft → active
    snapshots the programme as the baseline, which every later
    comparison anchors to."""
    sb = get_supabase_admin()
    prog_before = _check_access(sb, programme_id, user)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")

    result = sb.table("programmes").update(updates).eq("id", programme_id).execute()
    _audit(sb, user, "programme_update", programme_id, updates)

    # Snapshot on activation. If a baseline already exists (e.g., re-
    # activation after a pause), we leave it alone unless nothing exists.
    becoming_active = (
        updates.get("status") == "active"
        and (prog_before.get("status") or "draft") != "active"
    )
    if becoming_active:
        try:
            from app.services.baseline_manager import (
                create_baseline,
                get_current_baseline,
            )
            existing = get_current_baseline(sb, programme_id)
            if not existing:
                create_baseline(
                    sb,
                    programme_id=programme_id,
                    reason="activation",
                    created_by=user.id,
                )
        except Exception:
            pass  # Non-critical — activation succeeds regardless

    return result.data[0] if result.data else {"id": programme_id}


@router.post("/{programme_id}/delete")
def delete_programme(programme_id: str, user: CurrentUser = Depends(get_current_user)):
    """Soft-delete a programme."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    sb.table("programmes").update({
        "deleted_at": "now()",
        "deleted_by": user.id,
    }).eq("id", programme_id).execute()

    _audit(sb, user, "programme_delete", programme_id)
    return {"deleted": True}


# ── Block management ─────────────────────────────────────────────────────


@router.post("/{programme_id}/blocks", status_code=201)
def add_block(
    programme_id: str,
    body: BlockCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """Add a block to a programme."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    block_data = body.model_dump(exclude_none=True)
    block_data["programme_id"] = programme_id

    result = sb.table("programme_blocks").insert(block_data).execute()
    if not result.data:
        raise HTTPException(500, "Failed to create block")

    _audit(sb, user, "block_create", programme_id, {"block_name": body.name})
    return result.data[0]


@router.patch("/{programme_id}/blocks/{block_id}")
def update_block(
    programme_id: str,
    block_id: str,
    body: BlockUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Update a block."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")

    # If soil_analysis_id is (re)linked, refresh the cached nutrient_targets
    # from that analysis. The season tracker assumes the block cache is in
    # sync with its source analysis, so reattaching a newer analysis must
    # sync the targets — otherwise the next generate will use stale data.
    if "soil_analysis_id" in updates and updates["soil_analysis_id"]:
        try:
            sa = (
                sb.table("soil_analyses")
                .select("nutrient_targets")
                .eq("id", updates["soil_analysis_id"])
                .limit(1)
                .execute()
            )
            if sa.data and sa.data[0].get("nutrient_targets"):
                updates["nutrient_targets"] = sa.data[0]["nutrient_targets"]
        except Exception:
            pass  # Non-critical — user can regenerate targets later

    result = (
        sb.table("programme_blocks")
        .update(updates)
        .eq("id", block_id)
        .eq("programme_id", programme_id)
        .execute()
    )
    return result.data[0] if result.data else {"id": block_id}


@router.delete("/{programme_id}/blocks/{block_id}")
def delete_block(
    programme_id: str,
    block_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Remove a block from a programme."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    sb.table("programme_blocks").delete().eq("id", block_id).eq("programme_id", programme_id).execute()
    _audit(sb, user, "block_delete", programme_id, {"block_id": block_id})
    return {"deleted": True}


# ── Generation ───────────────────────────────────────────────────────────


@router.post("/{programme_id}/preview-schedule")
def preview_schedule(programme_id: str, user: CurrentUser = Depends(get_current_user)):
    """Preview the feeding schedule without saving. Used by the wizard's Schedule Review step."""
    from app.services.programme_engine import generate_block_plans, _group_blocks_by_npk

    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    blocks_result = sb.table("programme_blocks").select("*").eq("programme_id", programme_id).execute()
    blocks = blocks_result.data or []
    if not blocks:
        raise HTTPException(400, "Programme has no blocks.")

    # Separate blocks with/without nutrient targets. Blocks without targets
    # cannot be planned yet, but shouldn't block the rest of the programme —
    # surface them as warnings and plan the others.
    planable = [b for b in blocks if b.get("nutrient_targets")]
    unplanable_blocks = [
        {"block_id": b["id"], "block_name": b["name"], "reason": "missing_targets"}
        for b in blocks if not b.get("nutrient_targets")
    ]
    if not planable:
        raise HTTPException(
            400,
            f"No block has nutrient targets yet. Upload a soil analysis first "
            f"(missing: {', '.join(b['name'] for b in blocks)}).",
        )

    # Generate plans for the planable subset
    block_plans = generate_block_plans(planable, sb)

    # Blocks with targets but no growth stages for their crop — surface but
    # don't fail the whole preview
    for bp in block_plans:
        if bp.get("missing_stages"):
            unplanable_blocks.append({
                "block_id": bp["block"]["id"],
                "block_name": bp["block"]["name"],
                "reason": "missing_growth_stages",
                "crop": bp["block"].get("crop"),
            })

    # Keep only plans we can render
    block_plans = [bp for bp in block_plans if not bp.get("missing_stages")]

    # Load variability margin
    margin = 0.15
    try:
        dm = sb.table("default_materials").select("variability_margin").execute()
        if dm.data and dm.data[0].get("variability_margin"):
            margin = dm.data[0]["variability_margin"] / 100
    except Exception:
        pass

    groups = _group_blocks_by_npk(block_plans, margin=margin)

    # Flatten schedule items for frontend
    schedule = []
    for bp in block_plans:
        for i, item in enumerate(bp["items"]):
            schedule.append({
                "block_id": bp["block"]["id"],
                "block_name": bp["block"]["name"],
                "feeding_order": i,
                **item,
            })

    # Build block info with growth stages, nutrient targets, and soil corrections
    from app.services.soil_corrections import calculate_all_corrections, calculate_corrective_targets

    block_info = []
    all_corrections = []
    for bp in block_plans:
        b = bp["block"]
        crop = b.get("crop", "")
        base_crop = crop.split("(")[0].strip() if "(" in crop else crop
        stages_result = sb.table("crop_growth_stages").select(
            "stage_name, stage_order, month_start, month_end, n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct"
        ).eq("crop", crop).order("stage_order").execute()
        stages = stages_result.data or []
        if not stages and base_crop != crop:
            stages_result = sb.table("crop_growth_stages").select(
                "stage_name, stage_order, month_start, month_end, n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct"
            ).eq("crop", base_crop).order("stage_order").execute()
            stages = stages_result.data or []

        # Get accepted methods from field
        accepted_methods = []
        if b.get("field_id"):
            try:
                fr = sb.table("fields").select("accepted_methods, irrigation_type").eq("id", b["field_id"]).execute()
                if fr.data:
                    accepted_methods = fr.data[0].get("accepted_methods") or []
            except Exception:
                pass
        if not accepted_methods:
            # Fall back to crop methods
            try:
                cm = sb.table("crop_application_methods").select("method").eq("crop", crop).execute()
                accepted_methods = [m["method"] for m in (cm.data or [])]
            except Exception:
                accepted_methods = ["broadcast"]

        # Load soil analysis for corrections
        corrections_result = {"corrections": [], "nutrient_explanations": []}
        corrective_result = {"corrective_items": [], "missing_data": []}
        analysis_id = b.get("soil_analysis_id")
        if analysis_id:
            try:
                ar = sb.table("soil_analyses").select(
                    "soil_values, classifications, ratio_results, nutrient_targets, norms_snapshot"
                ).eq("id", analysis_id).execute()
                if ar.data:
                    a = ar.data[0]
                    soil_vals = a.get("soil_values") or {}
                    nut_targets = a.get("nutrient_targets") or b.get("nutrient_targets") or []
                    corrections_result = calculate_all_corrections(
                        soil_values=soil_vals,
                        classifications=a.get("classifications") or {},
                        ratio_results=a.get("ratio_results"),
                        nutrient_targets=nut_targets,
                        crop=crop,
                    )
                    for c in corrections_result["corrections"]:
                        c["block_id"] = b["id"]
                        c["block_name"] = b["name"]
                    all_corrections.extend(corrections_result["corrections"])

                    # Calculate corrective action timelines
                    snapshot = a.get("norms_snapshot") or {}
                    suf_rows = snapshot.get("sufficiency") or []
                    try:
                        pm = sb.table("soil_parameter_map").select("*").execute()
                        pm_rows = pm.data or []
                    except Exception:
                        pm_rows = []
                    if suf_rows:
                        corrective_result = calculate_corrective_targets(
                            soil_values=soil_vals,
                            nutrient_targets=nut_targets,
                            sufficiency_rows=suf_rows,
                            param_map_rows=pm_rows,
                        )
            except Exception:
                pass

        # Look up crop type
        crop_type = "annual"
        try:
            ct = sb.table("crop_requirements").select("crop_type").eq("crop", crop).limit(1).execute()
            if ct.data:
                crop_type = ct.data[0].get("crop_type", "annual") or "annual"
            elif base_crop != crop:
                ct = sb.table("crop_requirements").select("crop_type").eq("crop", base_crop).limit(1).execute()
                if ct.data:
                    crop_type = ct.data[0].get("crop_type", "annual") or "annual"
        except Exception:
            pass

        block_info.append({
            "block_id": b["id"],
            "block_name": b["name"],
            "crop": crop,
            "crop_type": crop_type,
            "growth_stages": stages,
            "nutrient_targets": b.get("nutrient_targets", []),
            "accepted_methods": accepted_methods,
            "corrections": corrections_result["corrections"],
            "nutrient_explanations": corrections_result["nutrient_explanations"],
            "corrective_targets": corrective_result["corrective_items"],
            "missing_corrective_data": corrective_result["missing_data"],
        })

    return {
        "schedule": schedule,
        "block_info": block_info,
        "corrections": all_corrections,
        "unplanable_blocks": unplanable_blocks,
    }


class UserApplication(BaseModel):
    block_id: str
    month: int = Field(..., ge=1, le=12)
    method: str = Field(..., max_length=50)


class PlantingMonth(BaseModel):
    block_id: str
    month: int = Field(..., ge=1, le=12)


class GenerateRequest(BaseModel):
    applications: list[UserApplication] | None = None
    planting_months: list[PlantingMonth] | None = None


@router.post("/{programme_id}/generate")
def generate_programme(
    programme_id: str,
    body: GenerateRequest | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    """Generate or regenerate feeding plans and blend groups for all blocks.

    If applications are provided, distributes nutrients across those user-chosen
    months based on growth stage percentages. Otherwise uses engine defaults.
    """
    from app.services.programme_engine import build_programme

    sb = get_supabase_admin()
    prog = _check_access(sb, programme_id, user)

    # Load blocks
    blocks_result = sb.table("programme_blocks").select("*").eq("programme_id", programme_id).execute()
    all_blocks = blocks_result.data or []

    if not all_blocks:
        raise HTTPException(400, "Programme has no blocks. Add blocks first.")

    # Only generate for blocks with targets; report the skipped ones so the
    # tracker can flag them for the agronomist to resolve.
    blocks = [b for b in all_blocks if b.get("nutrient_targets")]
    skipped_blocks = [
        {"block_id": b["id"], "block_name": b["name"], "reason": "missing_targets"}
        for b in all_blocks if not b.get("nutrient_targets")
    ]
    if not blocks:
        names = ", ".join(b["name"] for b in all_blocks)
        raise HTTPException(
            400,
            f"No block has nutrient targets. Upload a soil analysis first "
            f"(blocks: {names}).",
        )

    # If user provided applications, distribute nutrients across their chosen months
    user_apps = body.applications if body else None

    # Generate base plans (for growth stage data + grouping)
    result = build_programme(
        programme_id=programme_id,
        blocks=blocks,
        agent_id=user.id,
    )

    # If user specified applications, redistribute nutrients across their months
    if user_apps:
        for bp in result["block_plans"]:
            block = bp["block"]
            block_apps = [a for a in user_apps if a.block_id == block["id"]]
            if not block_apps:
                continue

            # Load growth stages for this block's crop
            crop = block.get("crop", "")
            base_crop = crop.split("(")[0].strip() if "(" in crop else crop
            stages_r = sb.table("crop_growth_stages").select("*").eq("crop", crop).order("stage_order").execute()
            stages = stages_r.data or []
            if not stages and base_crop != crop:
                stages_r = sb.table("crop_growth_stages").select("*").eq("crop", base_crop).order("stage_order").execute()
                stages = stages_r.data or []

            if not stages:
                continue

            # Get total nutrient targets for this block (use Final_Target_kg_ha for ratio-adjusted values)
            targets = block.get("nutrient_targets", [])
            total_nutrients = {}
            for t in targets:
                nut = t.get("Nutrient", t.get("nutrient", "")).lower()
                val = float(t.get("Final_Target_kg_ha", t.get("Target_kg_ha", t.get("target_kg_ha", 0))))
                if nut and val > 0:
                    total_nutrients[nut] = val

            # Calculate planting offset
            planting_offset = 0
            if body and body.planting_months:
                pm = next((p for p in body.planting_months if p.block_id == block["id"]), None)
                if pm and stages:
                    default_start = stages[0].get("month_start", 1)
                    planting_offset = pm.month - default_start

            def shift_month(m, offset):
                r = ((m - 1 + offset) % 12) + 1
                return r if r > 0 else r + 12

            # Find which stage each user month falls in (with offset applied)
            def month_in_stage(month, stage):
                ms = shift_month(stage.get("month_start", 1), planting_offset)
                me = shift_month(stage.get("month_end", 12), planting_offset)
                if ms <= me:
                    return ms <= month <= me
                return month >= ms or month <= me  # Wraps around year

            # Calculate weight per user application
            items = []
            total_weight = 0
            app_weights = []
            for app in block_apps:
                # Find matching stage
                matched_stage = None
                for s in stages:
                    if month_in_stage(app.month, s):
                        matched_stage = s
                        break
                if not matched_stage:
                    matched_stage = stages[-1]  # fallback to last stage

                # Weight = stage nutrient percentage (use N as proxy)
                weight = float(matched_stage.get("n_pct", 10)) / 100
                app_weights.append((app, matched_stage, weight))
                total_weight += weight

            # Distribute nutrients proportionally
            if total_weight > 0:
                for app, stage, weight in app_weights:
                    fraction = weight / total_weight
                    item = {
                        "stage_name": stage.get("stage_name", ""),
                        "month_target": app.month,
                        "method": app.method,
                        "available_methods": [],
                    }
                    for nut, total_val in total_nutrients.items():
                        item[f"{nut}_kg_ha"] = round(total_val * fraction, 2)
                    items.append(item)

            bp["items"] = items

        # Regroup after redistribution
        from app.services.programme_engine import _group_blocks_by_npk
        margin = 0.15
        try:
            dm = sb.table("default_materials").select("variability_margin").execute()
            if dm.data and dm.data[0].get("variability_margin"):
                margin = dm.data[0]["variability_margin"] / 100
        except Exception:
            pass

        groups = _group_blocks_by_npk(result["block_plans"], margin=margin)
        for group_letter, group_blocks in groups.items():
            for bpp in group_blocks:
                bpp["block"]["blend_group"] = group_letter

        # Rebuild blend_groups in result
        result["blend_groups"] = {}
        for group_letter, group_blocks in groups.items():
            crops_list = list(set(bpp["block"]["crop"] for bpp in group_blocks))
            block_names = [bpp["block"]["name"] for bpp in group_blocks]
            total_area = sum(bpp["block"].get("area_ha", 0) or 0 for bpp in group_blocks)
            template_items = group_blocks[0]["items"] if group_blocks else []
            result["blend_groups"][group_letter] = {
                "group": group_letter,
                "crops": crops_list,
                "block_names": block_names,
                "total_area_ha": round(total_area, 2),
                "num_applications": len(template_items),
                "template_items": template_items,
            }

    # Update blocks with blend groups
    for bp in result["block_plans"]:
        block = bp["block"]
        if block.get("blend_group"):
            sb.table("programme_blocks").update({
                "blend_group": block["blend_group"],
            }).eq("id", block["id"]).execute()

    # Clear old programme blends and save new ones
    # First unlink any applications referencing these blends (FK constraint)
    sb.table("programme_applications").update({
        "planned_blend_id": None,
    }).eq("programme_id", programme_id).execute()
    sb.table("programme_blends").delete().eq("programme_id", programme_id).execute()

    # Load materials for blend optimization
    from app.services.material_loader import load_materials_df, load_default_materials, find_compost_index
    from app.services.programme_engine import (
        FOLIAR_METHODS,
        filter_materials_for_method,
        optimize_blend_for_application,
    )

    _, min_compost = load_default_materials()
    # Load ALL materials (not just defaults) so the optimizer has full
    # selection across both dry and liquid-compatible inputs.
    materials_df = load_materials_df()
    batch_size = 1000.0

    # Track optimizer outcomes so the UI can surface "no valid materials"
    # / "solver infeasible" warnings rather than silently returning an
    # empty recipe.
    infeasible_applications: list[dict] = []

    for group_letter, group_info in result["blend_groups"].items():
        template_items = group_info.get("template_items", [])

        # Per-application optimization: each stage has its own nutrient
        # demand and application method, so it gets its own recipe built
        # from the materials valid for that method. No more one-blend-
        # for-all.
        for item in template_items:
            method = item.get("method")
            nutrient_sum = sum(
                item.get(f"{n}_kg_ha", 0) or 0
                for n in ["n", "p", "k", "ca", "mg", "s"]
            )

            # Foliar: skip the dry/liquid LP entirely. These go through
            # the proprietary product catalog (liquid_products with
            # product_type='foliar') or the crop_foliar_protocol table;
            # neither is wired into programme-generate yet. Record the
            # nutrient demand so the UI can render "Foliar — configure
            # product" instead of a bogus dry blend.
            if method in FOLIAR_METHODS:
                blend_data = {
                    "programme_id": programme_id,
                    "blend_group": group_letter,
                    "stage_name": item.get("stage_name"),
                    "application_month": item.get("month_target"),
                    "method": method,
                    "rate_kg_ha": 0,
                    "total_kg": 0,
                    "sa_notation": "",
                    "blend_nutrients": {
                        n: round(item.get(f"{n}_kg_ha", 0) or 0, 2)
                        for n in ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]
                    },
                    "blend_recipe": None,
                    "blend_cost_per_ton": None,
                }
                sb.table("programme_blends").insert(blend_data).execute()
                continue

            # Filter material set to what's physically valid for the
            # chosen method (dry-only for broadcast/band/etc., liquid-
            # only for fertigation). Compost only applies to dry blends.
            filtered_df = filter_materials_for_method(materials_df, method)
            c_idx = find_compost_index(filtered_df) if method in {"broadcast", "band_place", "side_dress", "topdress"} else None

            opt_result = optimize_blend_for_application(
                item, filtered_df, batch_size, c_idx, min_compost,
            )

            if opt_result is None and nutrient_sum > 0.01:
                infeasible_applications.append({
                    "group": group_letter,
                    "stage": item.get("stage_name"),
                    "month": item.get("month_target"),
                    "method": method,
                    "reason": (
                        "no_materials_available" if filtered_df is None or len(filtered_df) == 0
                        else "solver_infeasible"
                    ),
                })

            rate = opt_result["rate_kg_ha"] if opt_result else (round(nutrient_sum / 0.25) if nutrient_sum > 0 else 0)

            blend_data = {
                "programme_id": programme_id,
                "blend_group": group_letter,
                "stage_name": item.get("stage_name"),
                "application_month": item.get("month_target"),
                "method": method,
                "rate_kg_ha": rate,
                "total_kg": rate * group_info.get("total_area_ha", 0),
                "sa_notation": opt_result["sa_notation"] if opt_result else "",
                "blend_nutrients": {
                    n: round(item.get(f"{n}_kg_ha", 0) or 0, 2)
                    for n in ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]
                },
                "blend_recipe": opt_result["recipe"] if opt_result else None,
                "blend_cost_per_ton": opt_result["cost_per_ton"] if opt_result else None,
            }
            sb.table("programme_blends").insert(blend_data).execute()

    # Collect the Level 2 heterogeneity report so the UI can surface a
    # per-group warning when blocks within a group have divergent nutrient
    # requirements (Wilding-derived thresholds). Not persisted yet —
    # regenerate to refresh.
    heterogeneity_by_group = {
        letter: g.get("heterogeneity") or {}
        for letter, g in result["blend_groups"].items()
    }
    any_heterogeneity_warn = any(h.get("any_warn") for h in heterogeneity_by_group.values())
    any_heterogeneity_split = any(h.get("any_split") for h in heterogeneity_by_group.values())

    _audit(sb, user, "programme_generate", programme_id, {
        "num_blocks": len(blocks),
        "num_groups": len(result["blend_groups"]),
        "num_skipped": len(skipped_blocks),
        "heterogeneity_warn": any_heterogeneity_warn,
        "heterogeneity_split": any_heterogeneity_split,
        "infeasible_applications": len(infeasible_applications),
    })

    # Return full programme state + any blocks skipped during generation
    prog_state = get_programme(programme_id, user)
    prog_state["skipped_blocks"] = skipped_blocks
    prog_state["heterogeneity_by_group"] = heterogeneity_by_group
    prog_state["infeasible_applications"] = infeasible_applications
    return prog_state


# ── Match field for Quick Analysis integration ───────────────────────────


@router.get("/match-field")
def match_field(field_id: str, user: CurrentUser = Depends(get_current_user)):
    """Find active programme blocks that match a given field.

    Used by Quick Analysis to prompt linking a new analysis to an active programme.
    """
    sb = get_supabase_admin()

    # Find blocks linked to this field's soil analyses
    # First get soil analyses for this field
    analyses = sb.table("soil_analyses").select("id").eq("field_id", field_id).execute()
    analysis_ids = [a["id"] for a in (analyses.data or [])]

    if not analysis_ids:
        return []

    # Find programme blocks using any of these analyses
    blocks = (
        sb.table("programme_blocks")
        .select("*, programmes!inner(id, name, status, agent_id)")
        .in_("soil_analysis_id", analysis_ids)
        .execute()
    )

    # Filter to active programmes owned by this agent (or admin)
    results = []
    for block in (blocks.data or []):
        prog = block.get("programmes", {})
        if prog.get("status") not in ("draft", "active"):
            continue
        if prog.get("agent_id") != user.id and user.role != "admin":
            continue
        results.append({
            "programme_id": prog["id"],
            "programme_name": prog["name"],
            "block_id": block["id"],
            "block_name": block["name"],
            "crop": block["crop"],
        })

    return results


# ── Season Tracker ───────────────────────────────────────────────────────


class RecordApplicationRequest(BaseModel):
    block_id: str
    planned_blend_id: str | None = None
    actual_date: str | None = None
    actual_rate_kg_ha: float | None = Field(None, ge=0)
    product_name: str | None = Field(None, max_length=200)
    product_type: str | None = Field(None, max_length=50)
    is_sapling_product: bool = True
    method: str | None = Field(None, max_length=50)
    weather_notes: str | None = None
    notes: str | None = None
    status: str = Field("applied", max_length=20)


@router.post("/{programme_id}/applications", status_code=201)
def record_application(
    programme_id: str,
    body: RecordApplicationRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Record an actual application event for a block."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    data = {
        "programme_id": programme_id,
        "block_id": body.block_id,
        "planned_blend_id": body.planned_blend_id,
        "actual_date": body.actual_date,
        "actual_rate_kg_ha": body.actual_rate_kg_ha,
        "product_name": body.product_name,
        "product_type": body.product_type,
        "is_sapling_product": body.is_sapling_product,
        "method": body.method,
        "weather_notes": body.weather_notes,
        "notes": body.notes,
        "status": body.status,
    }

    result = sb.table("programme_applications").insert(data).execute()
    _audit(sb, user, "application_record", programme_id, {"block_id": body.block_id, "status": body.status})
    app_row = result.data[0] if result.data else None

    # Competitor product alert
    if not body.is_sapling_product:
        _audit(sb, user, "competitor_product", programme_id, {
            "block_id": body.block_id,
            "product_name": body.product_name,
            "product_type": body.product_type,
        })

    # Off-programme / rate-deviation detector. Raises a 'suggested'
    # adjustment if the actual diverges from the plan. The agronomist
    # reviews via the same adjustments queue.
    if body.status == "applied" and app_row:
        try:
            from app.services.adjustment_detector import detect_off_programme_adjustment
            detect_off_programme_adjustment(
                sb,
                programme_id=programme_id,
                block_id=body.block_id,
                application_id=app_row["id"],
                created_by=user.id,
            )
        except Exception:
            pass  # Non-critical; application is saved regardless

    return app_row if app_row else data


@router.get("/{programme_id}/applications")
def list_applications(programme_id: str, user: CurrentUser = Depends(get_current_user)):
    """List all recorded applications for a programme."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)
    result = sb.table("programme_applications").select("*").eq("programme_id", programme_id).order("actual_date").execute()
    return result.data or []


@router.patch("/{programme_id}/applications/{app_id}")
def update_application(
    programme_id: str,
    app_id: str,
    body: RecordApplicationRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Update a recorded application."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)
    updates = body.model_dump(exclude_none=True)
    result = sb.table("programme_applications").update(updates).eq("id", app_id).execute()
    return result.data[0] if result.data else {"id": app_id}


class AdjustmentRequest(BaseModel):
    block_id: str | None = None
    trigger_type: str = Field(..., max_length=50)  # leaf_analysis, observation, weather, manual
    trigger_id: str | None = None
    trigger_data: dict | None = None
    adjustment_data: dict
    notes: str | None = None


@router.post("/{programme_id}/adjustments", status_code=201)
def create_adjustment(
    programme_id: str,
    body: AdjustmentRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Create a mid-season adjustment for a programme."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    data = {
        "programme_id": programme_id,
        "block_id": body.block_id,
        "trigger_type": body.trigger_type,
        "trigger_id": body.trigger_id,
        "trigger_data": body.trigger_data,
        "adjustment_data": body.adjustment_data,
        "notes": body.notes,
        "created_by": user.id,
    }

    result = sb.table("programme_adjustments").insert(data).execute()
    _audit(sb, user, "programme_adjust", programme_id, {"trigger_type": body.trigger_type})
    return result.data[0] if result.data else data


@router.get("/{programme_id}/adjustments")
def list_adjustments(
    programme_id: str,
    status: str | None = Query(None, description="Filter by status: suggested/approved/applied/rejected"),
    user: CurrentUser = Depends(get_current_user),
):
    """List adjustments for a programme. Filter by review status for
    the tracker's 'pending review' queue."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)
    q = sb.table("programme_adjustments").select("*").eq("programme_id", programme_id)
    if status:
        q = q.eq("status", status)
    result = q.order("created_at", desc=True).execute()
    return result.data or []


# ── Blend editing (phase B) ──────────────────────────────────────────────
# Once a programme exists, the agent can edit individual blends directly
# instead of regenerating. These endpoints cover that. Edits apply
# directly in both draft and active states — audit log records them so
# the plan-vs-baseline comparison view can attribute changes.
# The data-driven adjustment queue is reserved for triggers from new
# soil/leaf/off-programme data, not manual edits.


NUTRIENT_ALLOWED = {"n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"}


class BlendCreate(BaseModel):
    blend_group: str = Field(..., min_length=1, max_length=10)
    stage_name: str | None = Field(None, max_length=100)
    application_month: int | None = Field(None, ge=1, le=12)
    method: str | None = Field(None, max_length=50)
    rate_kg_ha: float | None = Field(None, ge=0, le=10_000)
    total_kg: float | None = Field(None, ge=0, le=1_000_000)
    sa_notation: str | None = Field(None, max_length=100)
    blend_nutrients: dict[str, float] | None = None
    blend_recipe: list[dict] | None = None
    notes: str | None = None


class BlendUpdate(BaseModel):
    blend_group: str | None = Field(None, min_length=1, max_length=10)
    stage_name: str | None = Field(None, max_length=100)
    application_month: int | None = Field(None, ge=1, le=12)
    method: str | None = Field(None, max_length=50)
    rate_kg_ha: float | None = Field(None, ge=0, le=10_000)
    total_kg: float | None = Field(None, ge=0, le=1_000_000)
    sa_notation: str | None = Field(None, max_length=100)
    blend_nutrients: dict[str, float] | None = None
    blend_recipe: list[dict] | None = None
    notes: str | None = None


def _sanitize_nutrients(nut: dict[str, float] | None) -> dict[str, float] | None:
    """Strip unknown keys, coerce to float, drop negatives. Ensures a
    consumer of blend_nutrients can rely on the shape."""
    if nut is None:
        return None
    out: dict[str, float] = {}
    for k, v in nut.items():
        key = k.lower().strip()
        if key not in NUTRIENT_ALLOWED:
            continue
        try:
            num = float(v)
        except (TypeError, ValueError):
            continue
        if num < 0:
            continue
        out[key] = round(num, 3)
    return out


@router.post("/{programme_id}/blends", status_code=201)
def create_blend(
    programme_id: str,
    body: BlendCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """Add a new application to a programme. Use for insertions the
    auto-generator didn't produce — e.g., a corrective foliar spray."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    data = body.model_dump(exclude_none=True)
    data["programme_id"] = programme_id
    if "blend_nutrients" in data:
        data["blend_nutrients"] = _sanitize_nutrients(data["blend_nutrients"])

    result = sb.table("programme_blends").insert(data).execute()
    if not result.data:
        raise HTTPException(500, "Failed to create blend")
    blend = result.data[0]
    _audit(sb, user, "blend_add", programme_id, {
        "blend_id": blend["id"],
        "blend_group": blend.get("blend_group"),
        "application_month": blend.get("application_month"),
    })
    return blend


@router.patch("/{programme_id}/blends/{blend_id}")
def update_blend(
    programme_id: str,
    blend_id: str,
    body: BlendUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Edit an existing blend — rate, nutrients, month, method, etc.
    Audit-logged so the comparison view can highlight manual edits
    against the baseline."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    if "blend_nutrients" in updates:
        updates["blend_nutrients"] = _sanitize_nutrients(updates["blend_nutrients"])

    # Capture before-state for audit
    before = (
        sb.table("programme_blends")
        .select("*")
        .eq("id", blend_id)
        .eq("programme_id", programme_id)
        .limit(1)
        .execute()
        .data
    )
    if not before:
        raise HTTPException(404, "Blend not found")

    result = (
        sb.table("programme_blends")
        .update(updates)
        .eq("id", blend_id)
        .eq("programme_id", programme_id)
        .execute()
    )
    _audit(sb, user, "blend_update", programme_id, {
        "blend_id": blend_id,
        "changed_fields": list(updates.keys()),
        # Capture the small, useful delta — full snapshots go in audit
        # only if the changed fields are numeric enough to matter.
        "before": {k: before[0].get(k) for k in updates.keys() if k in before[0]},
        "after": {k: updates[k] for k in updates.keys()},
    })
    return result.data[0] if result.data else {"id": blend_id}


@router.delete("/{programme_id}/blends/{blend_id}")
def delete_blend(
    programme_id: str,
    blend_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Remove an application from the programme. Hard delete —
    programme_blends is cache-only, derived from blocks + generate."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    before = (
        sb.table("programme_blends")
        .select("*")
        .eq("id", blend_id)
        .eq("programme_id", programme_id)
        .limit(1)
        .execute()
        .data
    )
    if not before:
        raise HTTPException(404, "Blend not found")

    # Break FK: any programme_applications referencing this blend get
    # their planned_blend_id nulled so the delete doesn't cascade-kill
    # actual application records.
    sb.table("programme_applications").update({"planned_blend_id": None}) \
        .eq("planned_blend_id", blend_id).execute()

    sb.table("programme_blends").delete() \
        .eq("id", blend_id).eq("programme_id", programme_id).execute()

    _audit(sb, user, "blend_delete", programme_id, {
        "blend_id": blend_id,
        "blend_group": before[0].get("blend_group"),
        "application_month": before[0].get("application_month"),
    })
    return {"deleted": True}


class ManualPlanRequest(BaseModel):
    """Bulk replace a programme's blends with a hand-built plan.

    The agent defines each application manually — no auto-generation,
    no soil-engine scaling. Soil/leaf data (if present) still flows
    into the validator so the agent gets feedback on their plan, but
    it doesn't *drive* the plan.
    """
    replace_existing: bool = False
    blends: list[BlendCreate] = Field(..., min_length=1)


@router.post("/{programme_id}/manual-plan", status_code=201)
def manual_plan(
    programme_id: str,
    body: ManualPlanRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Write a hand-built plan. Used by the 'start blank' wizard path.

    If replace_existing is True, existing programme_blends are
    deleted before the new list is inserted — safe because
    programme_blends is a cache layer derived from blocks + build
    decisions.
    """
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    if body.replace_existing:
        # Unlink actual applications from blends we're about to delete
        sb.table("programme_applications") \
            .update({"planned_blend_id": None}) \
            .eq("programme_id", programme_id).execute()
        sb.table("programme_blends").delete() \
            .eq("programme_id", programme_id).execute()

    rows = []
    for b in body.blends:
        data = b.model_dump(exclude_none=True)
        data["programme_id"] = programme_id
        if "blend_nutrients" in data:
            data["blend_nutrients"] = _sanitize_nutrients(data["blend_nutrients"])
        rows.append(data)

    inserted = sb.table("programme_blends").insert(rows).execute().data or []
    _audit(sb, user, "manual_plan", programme_id, {
        "inserted": len(inserted),
        "replace_existing": body.replace_existing,
    })
    return {"inserted": len(inserted), "blends": inserted}


class EditProposal(BaseModel):
    """A set of hypothetical edits to preview against the current plan."""
    updates: list[dict] = Field(default_factory=list)
    # Each dict: {id: str, ...BlendUpdate fields}
    deletes: list[str] = Field(default_factory=list)
    # List of blend IDs to treat as removed
    creates: list[dict] = Field(default_factory=list)
    # Each dict: BlendCreate fields; id is assigned '__new_N' for diffing


@router.post("/{programme_id}/preview-edit")
def preview_edit(
    programme_id: str,
    body: EditProposal,
    block_id: str | None = Query(None, description="Constrain preview to a specific block"),
    user: CurrentUser = Depends(get_current_user),
):
    """Apply a set of hypothetical edits in memory and run the validator
    against the resulting plan, per block. No persistence.

    Returns the same shape as /validate so the UI can render identical
    feedback panels for current state and proposed state.
    """
    from app.services.plan_validator import validate_plan
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    blocks_q = sb.table("programme_blocks").select("*").eq("programme_id", programme_id)
    if block_id:
        blocks_q = blocks_q.eq("id", block_id)
    blocks = blocks_q.execute().data or []
    if not blocks:
        raise HTTPException(404, "No blocks found")

    all_blends = (
        sb.table("programme_blends")
        .select("*")
        .eq("programme_id", programme_id)
        .execute()
        .data
    ) or []

    # Apply proposed edits to an in-memory copy
    deletes = set(body.deletes or [])
    updates_by_id = {u["id"]: u for u in (body.updates or []) if u.get("id")}

    edited_blends: list[dict] = []
    for b in all_blends:
        if b["id"] in deletes:
            continue
        if b["id"] in updates_by_id:
            merged = {**b, **{k: v for k, v in updates_by_id[b["id"]].items() if k != "id"}}
            if "blend_nutrients" in merged:
                merged["blend_nutrients"] = _sanitize_nutrients(merged["blend_nutrients"])
            edited_blends.append(merged)
        else:
            edited_blends.append(b)

    # Append creates with synthetic IDs for diff clarity
    for i, new_blend in enumerate(body.creates or []):
        merged = dict(new_blend)
        merged["id"] = f"__new_{i}"
        merged["programme_id"] = programme_id
        if "blend_nutrients" in merged:
            merged["blend_nutrients"] = _sanitize_nutrients(merged["blend_nutrients"])
        edited_blends.append(merged)

    apps = (
        sb.table("programme_applications")
        .select("*")
        .eq("programme_id", programme_id)
        .execute()
        .data
    ) or []

    results: dict = {}
    for b in blocks:
        group = b.get("blend_group")
        # For diff display: current state per block (unchanged), proposed per block (after edits)
        current_block_blends = [x for x in all_blends if x.get("blend_group") == group] if group else []
        proposed_block_blends = [x for x in edited_blends if x.get("blend_group") == group] if group else []
        block_apps = [a for a in apps if a.get("block_id") == b["id"]]

        leaf_classifications = None
        try:
            leaf = (
                sb.table("leaf_analyses")
                .select("classifications")
                .eq("programme_id", programme_id)
                .eq("block_id", b["id"])
                .is_("deleted_at", "null")
                .order("sample_date", desc=True)
                .limit(1)
                .execute()
                .data
            )
            if leaf and leaf[0].get("classifications"):
                leaf_classifications = leaf[0]["classifications"]
        except Exception:
            pass

        current_fb = validate_plan(
            plan_blends=current_block_blends,
            nutrient_targets=b.get("nutrient_targets"),
            applications_applied=block_apps,
            leaf_classifications=leaf_classifications,
        )
        proposed_fb = validate_plan(
            plan_blends=proposed_block_blends,
            nutrient_targets=b.get("nutrient_targets"),
            applications_applied=block_apps,
            leaf_classifications=leaf_classifications,
        )
        results[b["id"]] = {
            "block_name": b.get("name"),
            "crop": b.get("crop"),
            "blend_group": group,
            "current": current_fb,
            "proposed": proposed_fb,
            "net_change": _summarise_change(current_fb, proposed_fb),
        }

    if block_id:
        return results.get(block_id) or {}
    return {"blocks": results}


def _summarise_change(current_fb: dict, proposed_fb: dict) -> dict:
    """Highlight the nutrients that actually moved under the proposed edit."""
    changes = []
    cur_planned = (current_fb.get("season_totals") or {}).get("planned", {})
    new_planned = (proposed_fb.get("season_totals") or {}).get("planned", {})
    all_keys = set(cur_planned) | set(new_planned)
    for k in sorted(all_keys):
        before = float(cur_planned.get(k, 0.0))
        after = float(new_planned.get(k, 0.0))
        diff = round(after - before, 2)
        if abs(diff) >= 0.05:
            changes.append({
                "nutrient": k,
                "before": round(before, 2),
                "after": round(after, 2),
                "delta_kg_ha": diff,
            })
    # Warning-count delta signals whether the edit moves things closer
    # to agronomic sense or further from it.
    return {
        "changed_nutrients": changes,
        "warnings_before": len(current_fb.get("warnings") or []),
        "warnings_after": len(proposed_fb.get("warnings") or []),
        "status_change": {
            "under_before": current_fb["summary"].get("under_target_count"),
            "under_after": proposed_fb["summary"].get("under_target_count"),
            "over_before": current_fb["summary"].get("over_target_count"),
            "over_after": proposed_fb["summary"].get("over_target_count"),
        },
    }


# ── Baselines + plan validation ──────────────────────────────────────────


@router.get("/{programme_id}/baseline")
def get_baseline(programme_id: str, user: CurrentUser = Depends(get_current_user)):
    """Return the current baseline for this programme, or 404 if none
    exists (programme hasn't been activated yet)."""
    from app.services.baseline_manager import get_current_baseline
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)
    baseline = get_current_baseline(sb, programme_id)
    if not baseline:
        raise HTTPException(404, "No baseline yet — activate the programme to snapshot.")
    return baseline


@router.get("/{programme_id}/baselines")
def list_programme_baselines(
    programme_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """List all baselines (activation + any manual rebases) for audit."""
    from app.services.baseline_manager import list_baselines
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)
    return list_baselines(sb, programme_id)


class ManualRebaseRequest(BaseModel):
    notes: str | None = None


@router.post("/{programme_id}/baseline/rebase", status_code=201)
def rebase_programme(
    programme_id: str,
    body: ManualRebaseRequest | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    """Take a new baseline snapshot of the programme's current state,
    superseding the previous one. Use when the plan has drifted
    enough that 'what changed since activation' is no longer the
    useful comparison — e.g., after a big mid-season replan."""
    from app.services.baseline_manager import create_baseline
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    notes = body.notes if body else None
    baseline = create_baseline(
        sb,
        programme_id=programme_id,
        reason="manual_rebase",
        created_by=user.id,
        notes=notes,
    )
    if not baseline:
        raise HTTPException(400, "Nothing to snapshot — programme has no blocks.")
    _audit(sb, user, "programme_rebase", programme_id, {"baseline_id": baseline["id"]})
    return baseline


@router.get("/{programme_id}/compare")
def compare_programme(
    programme_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Three-way comparison per block:
      baseline (frozen at activation) vs current (live plan) vs
      applied (recorded actuals). Returns per-month diff rows with
      status (unchanged/edited/added/removed/applied_only) and the
      list of applied adjustments that attribute each divergence.
    """
    from app.services.plan_compare import compare_plan
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)
    return compare_plan(sb, programme_id)


@router.get("/{programme_id}/validate")
def validate_programme(
    programme_id: str,
    block_id: str | None = Query(None, description="Validate one block only"),
    user: CurrentUser = Depends(get_current_user),
):
    """Run the plan validator on the current programme state.

    Returns per-nutrient deltas vs the block's nutrient targets,
    season totals, structural warnings, and any leaf flags from a
    linked leaf analysis. Useful after an edit to see if the plan
    still makes agronomic sense.

    If block_id is given, validates just that block. Otherwise
    validates each block independently and returns a dict of
    block_id → feedback.
    """
    from app.services.plan_validator import validate_plan
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    blocks_q = sb.table("programme_blocks").select("*").eq("programme_id", programme_id)
    if block_id:
        blocks_q = blocks_q.eq("id", block_id)
    blocks = blocks_q.execute().data or []
    if not blocks:
        raise HTTPException(404, "No blocks found")

    # Pull all blends once, bucket by blend_group for per-block attribution
    all_blends = (
        sb.table("programme_blends")
        .select("*")
        .eq("programme_id", programme_id)
        .execute()
        .data
    ) or []

    # Recorded applications for this programme
    apps = (
        sb.table("programme_applications")
        .select("*")
        .eq("programme_id", programme_id)
        .execute()
        .data
    ) or []

    results: dict = {}
    for b in blocks:
        group = b.get("blend_group")
        if group:
            block_blends = [x for x in all_blends if x.get("blend_group") == group]
        else:
            block_blends = []
        block_apps = [a for a in apps if a.get("block_id") == b["id"]]

        # Best-effort leaf classifications for this block
        leaf_classifications = None
        try:
            leaf = (
                sb.table("leaf_analyses")
                .select("classifications, sample_date")
                .eq("programme_id", programme_id)
                .eq("block_id", b["id"])
                .is_("deleted_at", "null")
                .order("sample_date", desc=True)
                .limit(1)
                .execute()
                .data
            )
            if leaf and leaf[0].get("classifications"):
                leaf_classifications = leaf[0]["classifications"]
        except Exception:
            pass

        feedback = validate_plan(
            plan_blends=block_blends,
            nutrient_targets=b.get("nutrient_targets"),
            applications_applied=block_apps,
            leaf_classifications=leaf_classifications,
        )
        results[b["id"]] = {
            "block_name": b.get("name"),
            "crop": b.get("crop"),
            "blend_group": group,
            **feedback,
        }

    if block_id:
        return results.get(block_id) or {}
    return {"blocks": results}


@router.get("/{programme_id}/adjustments/{adj_id}/proposal")
def get_adjustment_proposal(
    programme_id: str,
    adj_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Compute a concrete proposal for a suggested adjustment without
    persisting. Returns per-blend diff + season-total comparison so the
    agronomist can review before apply (phase 3)."""
    from app.services.adjustment_proposer import propose_from_adjustment
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    # Verify adjustment belongs to this programme
    adj = (
        sb.table("programme_adjustments")
        .select("programme_id")
        .eq("id", adj_id)
        .limit(1)
        .execute()
    )
    if not adj.data or adj.data[0]["programme_id"] != programme_id:
        raise HTTPException(404, "Adjustment not found for this programme")

    return propose_from_adjustment(sb, adj_id)


class AdjustmentReview(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    notes: str | None = None


@router.post("/{programme_id}/adjustments/{adj_id}/review")
def review_adjustment(
    programme_id: str,
    adj_id: str,
    body: AdjustmentReview,
    user: CurrentUser = Depends(get_current_user),
):
    """Mark an adjustment approved or rejected. Approving does NOT
    automatically patch programme_blends — that's the explicit apply
    step (phase 3). This is the review gate."""
    from datetime import datetime, timezone
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    update = {
        "status": body.status,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_by": user.id,
    }
    if body.notes:
        update["notes"] = body.notes

    result = (
        sb.table("programme_adjustments")
        .update(update)
        .eq("id", adj_id)
        .eq("programme_id", programme_id)
        .execute()
    )
    _audit(sb, user, f"adjustment_{body.status}", programme_id, {"adjustment_id": adj_id})
    return result.data[0] if result.data else {"id": adj_id}


class AdjustmentApply(BaseModel):
    force: bool = False
    notes: str | None = None


@router.post("/{programme_id}/adjustments/{adj_id}/apply")
def apply_adjustment(
    programme_id: str,
    adj_id: str,
    body: AdjustmentApply | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    """Write the proposed blend changes into programme_blends and mark
    the adjustment as applied. Also syncs the block's nutrient_targets
    cache so subsequent /generate calls use the new baseline.

    Refuses to apply a 'suggested' adjustment unless body.force=True,
    so the review step is the default gate. 'approved' applies freely.
    Rejected or already-applied adjustments 400.
    """
    from datetime import datetime, timezone
    from app.services.adjustment_proposer import propose_from_adjustment

    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)
    force = bool(body and body.force)

    adj_r = (
        sb.table("programme_adjustments")
        .select("*")
        .eq("id", adj_id)
        .eq("programme_id", programme_id)
        .limit(1)
        .execute()
    )
    if not adj_r.data:
        raise HTTPException(404, "Adjustment not found for this programme")
    adj = adj_r.data[0]

    current_status = adj.get("status") or "suggested"
    if current_status in ("applied", "rejected"):
        raise HTTPException(400, f"Adjustment is already {current_status}")
    if current_status == "suggested" and not force:
        raise HTTPException(
            400,
            "Adjustment is still 'suggested' — review it first, or pass force=true to apply directly.",
        )

    # Recompute the proposal on fresh data — don't trust a stale client view
    proposal = propose_from_adjustment(sb, adj_id)
    affected = proposal.get("affected_blends") or []

    updated_count = 0
    errors: list[dict] = []
    for ab in affected:
        if not ab.get("changed"):
            continue
        new_nut = ab["new"]["nutrients"]
        new_rate = ab["new"]["rate_kg_ha"]
        update = {
            "blend_nutrients": {k: round(float(v), 3) for k, v in new_nut.items()},
            "rate_kg_ha": new_rate,
        }
        try:
            sb.table("programme_blends").update(update).eq("id", ab["id"]).execute()
            updated_count += 1
        except Exception as e:
            errors.append({"blend_id": ab["id"], "error": str(e)[:200]})

    # Sync the block's nutrient_targets cache from the triggering analysis,
    # so subsequent /generate calls rebuild from the new baseline.
    trigger_type = adj.get("trigger_type")
    trigger_id = adj.get("trigger_id")
    block_id = adj.get("block_id")
    if trigger_type == "soil_analysis" and trigger_id and block_id:
        try:
            sa = (
                sb.table("soil_analyses")
                .select("nutrient_targets")
                .eq("id", trigger_id)
                .limit(1)
                .execute()
            )
            if sa.data and sa.data[0].get("nutrient_targets"):
                sb.table("programme_blocks").update({
                    "nutrient_targets": sa.data[0]["nutrient_targets"],
                    "soil_analysis_id": trigger_id,
                }).eq("id", block_id).execute()
        except Exception as e:
            errors.append({"context": "sync_block_cache", "error": str(e)[:200]})

    # Mark adjustment as applied
    now = datetime.now(timezone.utc).isoformat()
    final_update = {
        "status": "applied",
        "applied_at": now,
        "applied_by": user.id,
    }
    if not adj.get("reviewed_at"):
        final_update["reviewed_at"] = now
        final_update["reviewed_by"] = user.id
    if body and body.notes:
        final_update["notes"] = body.notes
    sb.table("programme_adjustments").update(final_update).eq("id", adj_id).execute()

    _audit(sb, user, "adjustment_apply", programme_id, {
        "adjustment_id": adj_id,
        "blends_updated": updated_count,
        "errors": len(errors),
    })

    return {
        "adjustment_id": adj_id,
        "status": "applied",
        "blends_updated": updated_count,
        "errors": errors,
        "proposal_summary": proposal.get("summary", {}),
    }


@router.get("/{programme_id}/variance")
def get_variance(programme_id: str, user: CurrentUser = Depends(get_current_user)):
    """Get planned vs actual variance report."""
    from app.services.programme_tracker import calculate_variance
    _check_access(sb=get_supabase_admin(), programme_id=programme_id, user=user)
    return calculate_variance(programme_id)


@router.get("/{programme_id}/status")
def get_status(programme_id: str, user: CurrentUser = Depends(get_current_user)):
    """Get programme health status summary."""
    from app.services.programme_tracker import get_programme_status
    _check_access(sb=get_supabase_admin(), programme_id=programme_id, user=user)
    return get_programme_status(programme_id)


# ── Bulk Lab Results Upload ──────────────────────────────────────────────


class BulkAnalysisItem(BaseModel):
    block_id: str | None = None
    block_name: str | None = None
    crop: str | None = None
    cultivar: str | None = None
    sample_id: str | None = None
    analysis_type: str = "soil"  # soil or leaf
    values: dict[str, float | None]
    include: bool = True


class BulkAnalysisSave(BaseModel):
    lab_name: str | None = None
    analysis_date: str | None = None
    analyses: list[BulkAnalysisItem]
    average_same_block: bool = True


@router.post("/{programme_id}/bulk-analyses", status_code=201)
def save_bulk_analyses(
    programme_id: str,
    body: BulkAnalysisSave,
    user: CurrentUser = Depends(get_current_user),
):
    """Save multiple analyses at once, linked to programme blocks.

    If multiple analyses map to the same block and average_same_block is true,
    values are averaged (with outlier exclusion). Each block gets one saved analysis
    record with the averaged values and linked nutrient targets.
    """
    sb = get_supabase_admin()
    prog = _check_access(sb, programme_id, user)

    # Load programme blocks
    blocks_result = sb.table("programme_blocks").select("*").eq("programme_id", programme_id).execute()
    blocks = {b["id"]: b for b in (blocks_result.data or [])}

    # Filter to included analyses
    included = [a for a in body.analyses if a.include]
    if not included:
        raise HTTPException(400, "No analyses selected for saving")

    # Group by block_id (for averaging)
    from collections import defaultdict
    block_groups: dict[str, list[BulkAnalysisItem]] = defaultdict(list)
    unlinked = []

    for item in included:
        if item.block_id and item.block_id in blocks:
            block_groups[item.block_id].append(item)
        else:
            unlinked.append(item)

    saved_records = []

    # Process each block group
    for block_id, items in block_groups.items():
        block = blocks[block_id]

        analysis_type = items[0].analysis_type

        if body.average_same_block and len(items) > 1:
            # Non-destructive composite: keep every component sample on
            # the record so we can re-aggregate later (drop an outlier,
            # add a fourth sample, etc.) without re-entering lab values.
            component_samples = [
                {"values": {k: v for k, v in i.values.items() if v is not None}}
                for i in items
            ]
            agg = aggregate_samples(component_samples)
            avg_values = agg.values
            outliers = _format_outliers_for_response(agg, items)
            composition_method = agg.composition_method
            replicate_count = agg.replicate_count
            aggregation_stats = agg.stats_as_dict()
        else:
            avg_values = items[0].values
            outliers = []
            component_samples = None
            composition_method = "single"
            replicate_count = 1
            aggregation_stats = None

        if analysis_type == "leaf":
            # Save as leaf analysis. Leaf schema has no component retention
            # columns (yet) — Phase 2 only extended soil_analyses.
            record = sb.table("leaf_analyses").insert({
                "agent_id": user.id,
                "programme_id": programme_id,
                "block_id": block_id,
                "crop": block.get("crop") or items[0].crop,
                "lab_name": body.lab_name,
                "sample_date": body.analysis_date,
                "values": avg_values,
                "notes": f"Bulk upload — {replicate_count} sample(s) composited" if replicate_count > 1 else None,
            }).execute()
        else:
            # Save as soil analysis with component retention.
            numeric_values = {k: v for k, v in avg_values.items() if v is not None}
            soil_row: dict = {
                "agent_id": user.id,
                "crop": block.get("crop") or items[0].crop,
                "cultivar": items[0].cultivar,
                "lab_name": body.lab_name,
                "analysis_date": body.analysis_date,
                "soil_values": numeric_values,
                "status": "saved",
                "composition_method": composition_method,
                "replicate_count": replicate_count,
            }
            if component_samples is not None:
                soil_row["component_samples"] = component_samples
            if aggregation_stats is not None:
                soil_row["aggregation_stats"] = aggregation_stats
            record = sb.table("soil_analyses").insert(soil_row).execute()

            # Link to programme block + set nutrient targets
            if record.data:
                analysis_id = record.data[0]["id"]
                sb.table("programme_blocks").update({
                    "soil_analysis_id": analysis_id,
                }).eq("id", block_id).execute()

        if record.data:
            saved_records.append({
                "id": record.data[0]["id"],
                "block_id": block_id,
                "block_name": block.get("name"),
                "type": analysis_type,
                "num_samples": len(items),
                "outliers": outliers,
            })

    # Process unlinked analyses (save without block link)
    for item in unlinked:
        if item.analysis_type == "leaf":
            record = sb.table("leaf_analyses").insert({
                "agent_id": user.id,
                "programme_id": programme_id,
                "crop": item.crop,
                "lab_name": body.lab_name,
                "sample_date": body.analysis_date,
                "values": item.values,
            }).execute()
        else:
            numeric_values = {k: v for k, v in item.values.items() if v is not None}
            record = sb.table("soil_analyses").insert({
                "agent_id": user.id,
                "crop": item.crop,
                "cultivar": item.cultivar,
                "lab_name": body.lab_name,
                "analysis_date": body.analysis_date,
                "soil_values": numeric_values,
                "status": "saved",
            }).execute()

        if record.data:
            saved_records.append({
                "id": record.data[0]["id"],
                "block_id": None,
                "block_name": item.block_name,
                "type": item.analysis_type,
                "num_samples": 1,
                "outliers": [],
            })

    _audit(sb, user, "bulk_analyses_save", programme_id, {
        "num_saved": len(saved_records),
        "lab_name": body.lab_name,
    })

    return {
        "saved": len(saved_records),
        "records": saved_records,
    }


def _format_outliers_for_response(
    agg: AggregationResult,
    items: list,
) -> list[dict]:
    """Flatten aggregation outlier indices into the legacy response shape.

    The frontend expects {sample_idx, key, value, mean, std_dev} per
    flagged value. Shape predates the aggregation primitive — we keep it
    stable so this endpoint's callers don't have to migrate at the same
    time.
    """
    out: list[dict] = []
    for key, s in agg.stats.items():
        if not s.outlier_sample_indices:
            continue
        std_dev = s.variance ** 0.5
        for idx in s.outlier_sample_indices:
            raw = items[idx].values.get(key)
            if raw is None:
                continue
            out.append({
                "sample_idx": idx,
                "key": key,
                "value": float(raw),
                "mean": round(s.mean, 4),
                "std_dev": round(std_dev, 4),
            })
    return out
