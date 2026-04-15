"""Programmes router: full-season fertilizer programme CRUD and generation."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
from app.supabase_client import get_supabase_admin

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
    """Load a programme and verify access. Returns the programme dict."""
    result = sb.table("programmes").select("*").eq("id", programme_id).is_("deleted_at", "null").execute()
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
    """Update programme metadata."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")

    result = sb.table("programmes").update(updates).eq("id", programme_id).execute()
    _audit(sb, user, "programme_update", programme_id, updates)
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

    # Check for missing nutrient targets
    missing_targets = [b["name"] for b in blocks if not b.get("nutrient_targets")]
    if missing_targets:
        raise HTTPException(400, f"Blocks missing nutrient targets: {', '.join(missing_targets)}")

    # Generate plans
    block_plans = generate_block_plans(blocks, sb)

    # Check for missing growth stages
    missing_stages = [bp["block"]["name"] for bp in block_plans if bp.get("missing_stages")]
    if missing_stages:
        crops = list(set(bp["block"]["crop"] for bp in block_plans if bp.get("missing_stages")))
        raise HTTPException(400, f"No growth stages configured for: {', '.join(crops)}. Contact admin to add growth stage data.")

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

    return {"schedule": schedule, "block_info": block_info, "corrections": all_corrections}


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
    blocks = blocks_result.data or []

    if not blocks:
        raise HTTPException(400, "Programme has no blocks. Add blocks first.")

    # Check blocks have targets
    blocks_without_targets = [b for b in blocks if not b.get("nutrient_targets")]
    if blocks_without_targets:
        names = ", ".join(b["name"] for b in blocks_without_targets)
        raise HTTPException(400, f"Blocks missing nutrient targets: {names}. Run soil analysis first.")

    # If user provided applications, distribute nutrients across their chosen months
    user_apps = body.applications if body else None

    # Generate base plans (for growth stage data + grouping)
    result = build_programme(
        programme_id=programme_id,
        blocks=blocks,
        agent_id=user.id,
    )

    # If user specified applications, redistribute nutrients across their months
    import logging
    logger = logging.getLogger("programmes")
    logger.warning(f"Generate called. user_apps={user_apps}, body={body}")

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
    from app.services.material_loader import load_materials_df, load_default_materials, find_compost_index, COMPOST_NAME
    from app.services.programme_engine import optimize_blend_for_group

    default_mats, min_compost = load_default_materials()
    # Load ALL materials (not just defaults) so optimizer has full selection
    materials_df = load_materials_df()

    # Ensure compost is in the material list
    c_idx_found = find_compost_index(materials_df)
    c_idx = c_idx_found if c_idx_found is not None else 0
    batch_size = 1000.0

    for group_letter, group_info in result["blend_groups"].items():
        template_items = group_info.get("template_items", [])

        # Run LP optimizer for this group
        opt_result = optimize_blend_for_group(
            template_items, materials_df, batch_size, c_idx, min_compost,
        )

        for item in template_items:
            nutrient_sum = sum(
                item.get(f"{n}_kg_ha", 0) or 0
                for n in ["n", "p", "k", "ca", "mg", "s"]
            )
            rate = opt_result["rate_kg_ha"] if opt_result else (round(nutrient_sum / 0.25) if nutrient_sum > 0 else 0)

            blend_data = {
                "programme_id": programme_id,
                "blend_group": group_letter,
                "stage_name": item.get("stage_name"),
                "application_month": item.get("month_target"),
                "method": item.get("method"),
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

    _audit(sb, user, "programme_generate", programme_id, {
        "num_blocks": len(blocks),
        "num_groups": len(result["blend_groups"]),
    })

    # Return full programme state
    return get_programme(programme_id, user)


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

    # Competitor product alert
    if not body.is_sapling_product:
        _audit(sb, user, "competitor_product", programme_id, {
            "block_id": body.block_id,
            "product_name": body.product_name,
            "product_type": body.product_type,
        })

    return result.data[0] if result.data else data


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
def list_adjustments(programme_id: str, user: CurrentUser = Depends(get_current_user)):
    """List all adjustments for a programme."""
    sb = get_supabase_admin()
    _check_access(sb, programme_id, user)
    result = sb.table("programme_adjustments").select("*").eq("programme_id", programme_id).order("created_at", desc=True).execute()
    return result.data or []


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

        if body.average_same_block and len(items) > 1:
            # Average values across samples for this block
            avg_values = _average_values([i.values for i in items])
            outliers = _detect_outliers([i.values for i in items])
        else:
            avg_values = items[0].values
            outliers = []

        analysis_type = items[0].analysis_type

        if analysis_type == "leaf":
            # Save as leaf analysis
            record = sb.table("leaf_analyses").insert({
                "agent_id": user.id,
                "programme_id": programme_id,
                "block_id": block_id,
                "crop": block.get("crop") or items[0].crop,
                "lab_name": body.lab_name,
                "sample_date": body.analysis_date,
                "values": avg_values,
                "notes": f"Bulk upload — {len(items)} sample(s) averaged" if len(items) > 1 else None,
            }).execute()
        else:
            # Save as soil analysis
            numeric_values = {k: v for k, v in avg_values.items() if v is not None}
            record = sb.table("soil_analyses").insert({
                "agent_id": user.id,
                "crop": block.get("crop") or items[0].crop,
                "cultivar": items[0].cultivar,
                "lab_name": body.lab_name,
                "analysis_date": body.analysis_date,
                "soil_values": numeric_values,
                "status": "saved",
            }).execute()

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


def _average_values(value_sets: list[dict]) -> dict:
    """Average multiple value dicts, ignoring None values."""
    if not value_sets:
        return {}
    if len(value_sets) == 1:
        return value_sets[0]

    all_keys = set()
    for vs in value_sets:
        all_keys.update(vs.keys())

    result = {}
    for key in all_keys:
        nums = [float(vs[key]) for vs in value_sets if vs.get(key) is not None]
        if nums:
            result[key] = round(sum(nums) / len(nums), 4)
        else:
            result[key] = None

    return result


def _detect_outliers(value_sets: list[dict], threshold: float = 2.0) -> list[dict]:
    """Detect values that are >threshold standard deviations from the mean.

    Returns list of {sample_idx, key, value, mean, std_dev} for outliers.
    """
    if len(value_sets) < 3:
        return []  # Need at least 3 samples for meaningful outlier detection

    import statistics

    all_keys = set()
    for vs in value_sets:
        all_keys.update(vs.keys())

    outliers = []
    for key in all_keys:
        nums = [(i, float(vs[key])) for i, vs in enumerate(value_sets) if vs.get(key) is not None]
        if len(nums) < 3:
            continue

        values = [n[1] for n in nums]
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        if std < 0.001:
            continue

        for idx, val in nums:
            if abs(val - mean) > threshold * std:
                outliers.append({
                    "sample_idx": idx,
                    "key": key,
                    "value": val,
                    "mean": round(mean, 4),
                    "std_dev": round(std, 4),
                })

    return outliers
