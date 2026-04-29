"""Soil Reports router — API surface for the new soil-report feature.

Mirrors the programmes_v2 router shape so the frontend can reuse the
same lifecycle pattern (build → generate-narrative → approve → download
PDF). Lifecycle states: draft → approved → archived. Narrative locks on
draft → approved transition.

Endpoints:
    POST   /soil-reports/build                      build + persist
    GET    /soil-reports                            list (with kind-grouped UI)
    GET    /soil-reports/{id}                       fetch one
    POST   /soil-reports/{id}/generate-narrative    fire Opus, persist draft prose
    GET    /soil-reports/{id}/narrative             fetch persisted narrative state
    GET    /soil-reports/{id}/render-pdf            stream Sapling-branded PDF
    PATCH  /soil-reports/{id}/state                 transition state (locks narrative on approve)
    DELETE /soil-reports/{id}                       archive (soft delete)
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.services.pdf_renderer import render_soil_report_pdf
from app.services.soil_report_builder import (
    AnalysisInput,
    BlockAnalysesInput,
    SoilReportBuilderInputs,
    build_soil_report,
)
from app.supabase_client import get_supabase_admin, run_sb


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/soil-reports", tags=["soil-reports"])


# Hard cost cap per Opus narrative run — same as programmes (see
# programmes_v2.NARRATIVE_COST_CAP_USD). Soil report narratives are
# typically smaller (1-2 sections vs 4) but the safety net is the same.
NARRATIVE_COST_CAP_USD = 5.0


# ============================================================
# Request / response shapes
# ============================================================


class SoilReportBuildRequest(BaseModel):
    title: Optional[str] = None
    block_ids: list[UUID] = Field(..., min_length=1)
    # Optional explicit list. When omitted, the builder pulls every
    # active analysis the user has access to for these blocks.
    analysis_ids: Optional[list[UUID]] = None
    # When True, all analyses for each block are included (history
    # mode). When False, only the latest analysis per block.
    include_history: bool = True


class SoilReportListItem(BaseModel):
    id: UUID
    title: Optional[str]
    scope_kind: str
    block_count: int
    analysis_count: int
    state: str
    created_at: datetime
    updated_at: datetime
    farm_name: Optional[str] = None
    narrative_locked: bool = False


class SoilReportResponse(BaseModel):
    id: UUID
    title: Optional[str]
    scope_kind: str
    state: str
    block_ids: list[UUID]
    analysis_ids: list[UUID]
    farm_id: Optional[UUID] = None
    farm_name: Optional[str] = None
    report_payload: dict
    created_at: datetime
    updated_at: datetime
    narrative_locked_at: Optional[datetime] = None


# ============================================================
# Build
# ============================================================


@router.post("/build", response_model=SoilReportResponse, status_code=status.HTTP_201_CREATED)
async def build_report(
    request: SoilReportBuildRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Compose a SoilReportArtifact from the requested block(s) +
    analyses, and persist it as a draft. The frontend can then preview,
    optionally generate a narrative, and approve to lock."""
    sb = get_supabase_admin()

    # Load fields (blocks). RLS scopes to the user; admin sees all.
    # NOTE: fields uses `size_ha` (not `area_ha`); farms has no own `name`
    # → wait, farms DOES have name. The fields ↔ farms ↔ clients join is
    # PostgREST-style with the `farm_id` and `client_id` FK relationships.
    field_q = sb.table("fields").select(
        "id, name, size_ha, crop, farm_id, farms(id, name, client_id, clients(id, name))"
    ).in_("id", [str(b) for b in request.block_ids])
    if user.role != "admin":
        # Field RLS handles access; no explicit user filter on fields.
        pass
    fields_res = run_sb(lambda: field_q.execute())
    fields_data = fields_res.data or []
    if not fields_data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No accessible blocks for the provided IDs")

    found_block_ids = {f["id"] for f in fields_data}
    requested = {str(b) for b in request.block_ids}
    missing = requested - found_block_ids
    if missing:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Some blocks could not be loaded: {sorted(missing)}",
        )

    # Resolve client + farm metadata. We assume all blocks share one
    # farm — if not, we use the first block's farm for the header and
    # log a warning (cross-farm reports are unusual but legal).
    primary = fields_data[0]
    farm = primary.get("farms") or {}
    client = farm.get("clients") or {}

    # Load analyses scoped to these blocks. When request.analysis_ids
    # is set, filter to that subset; else when include_history is True,
    # load every analysis on every block; else just the latest per block.
    analysis_query = sb.table("soil_analyses").select(
        "id, field_id, lab_name, analysis_date, soil_values, deleted_at"
    ).in_("field_id", list(found_block_ids)).is_("deleted_at", "null")
    if request.analysis_ids:
        analysis_query = analysis_query.in_("id", [str(a) for a in request.analysis_ids])
    analyses_res = run_sb(lambda: analysis_query.execute())
    analyses_data = analyses_res.data or []
    if not analyses_data:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No active soil analyses found for the requested blocks. "
            "Upload an analysis or pick a different selection.",
        )

    # Group analyses by block, sorted ascending by date.
    analyses_by_block: dict[str, list[dict]] = {}
    for a in analyses_data:
        analyses_by_block.setdefault(a["field_id"], []).append(a)
    for fid, lst in analyses_by_block.items():
        lst.sort(key=lambda x: x.get("analysis_date") or "")

    # Apply include_history flag: when False, keep only latest per block.
    if not request.include_history:
        for fid, lst in list(analyses_by_block.items()):
            analyses_by_block[fid] = lst[-1:]

    # Build the BlockAnalysesInput list, dropping blocks with no
    # analyses (shouldn't happen with our query but defensive).
    block_inputs: list[BlockAnalysesInput] = []
    for f in fields_data:
        fid = f["id"]
        block_analyses = analyses_by_block.get(fid) or []
        if not block_analyses:
            continue
        block_inputs.append(BlockAnalysesInput(
            block_id=fid,
            block_name=f.get("name") or "",
            block_area_ha=f.get("size_ha"),
            crop=f.get("crop") or "",
            analyses=[
                AnalysisInput(
                    analysis_id=a["id"],
                    sample_date=date.fromisoformat(a["analysis_date"]) if a.get("analysis_date") else None,
                    lab_name=a.get("lab_name"),
                    lab_method=None,  # Lab method not stored on soil_analyses today
                    soil_parameters=a.get("soil_values") or {},
                )
                for a in block_analyses
            ],
        ))

    if not block_inputs:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No analyses survived filtering — pick a different selection.",
        )

    # Load sufficiency + param_map (per-crop fallback to global). All
    # blocks share one crop in practice; if they don't, sufficiency
    # rows for the FIRST block's crop are used as the comparison band
    # for the whole report. This is a known soft-edge — a multi-crop
    # report is unusual but legal; the per-block sections still surface
    # crop-specific findings via soil_factor_reasoner.
    crop = block_inputs[0].crop
    sufficiency_rows = _load_sufficiency_rows(sb, crop)
    param_map_rows = _load_param_map_rows(sb)

    # Compose the title if not provided.
    title = request.title or _default_title(client, farm, block_inputs)

    inputs = SoilReportBuilderInputs(
        title=title,
        client_name=client.get("name"),
        farm_name=farm.get("name"),
        blocks=block_inputs,
        sufficiency_rows=sufficiency_rows,
        param_map_rows=param_map_rows,
    )
    artifact = build_soil_report(inputs)

    # Persist to soil_reports
    insert = {
        "user_id": user.id,
        "client_id": client.get("id"),
        "farm_id": farm.get("id"),
        "farm_name": farm.get("name"),
        "title": title,
        "scope_kind": artifact.header.scope_kind,
        "block_ids": [str(b.block_id) for b in block_inputs],
        "analysis_ids": artifact.analysis_ids,
        "state": "draft",
        "report_payload": artifact.to_dict(),
    }
    saved = run_sb(lambda: sb.table("soil_reports").insert(insert).execute())
    if not saved.data:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to persist soil report")
    row = saved.data[0]

    return SoilReportResponse(
        id=UUID(row["id"]),
        title=row.get("title"),
        scope_kind=row["scope_kind"],
        state=row["state"],
        block_ids=[UUID(b) for b in row.get("block_ids") or []],
        analysis_ids=[UUID(a) for a in row.get("analysis_ids") or []],
        farm_id=UUID(row["farm_id"]) if row.get("farm_id") else None,
        farm_name=row.get("farm_name"),
        report_payload=row.get("report_payload") or {},
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        narrative_locked_at=row.get("narrative_locked_at"),
    )


# ============================================================
# List + fetch
# ============================================================


@router.get("", response_model=list[SoilReportListItem])
async def list_reports(
    client_id: Optional[UUID] = Query(None),
    state: Optional[str] = Query(None, pattern=r"^(draft|approved|archived)$"),
    user: CurrentUser = Depends(get_current_user),
):
    sb = get_supabase_admin()
    q = sb.table("soil_reports").select(
        "id, title, scope_kind, block_ids, analysis_ids, state, created_at, updated_at, "
        "farm_name, narrative_locked_at"
    ).is_("deleted_at", "null").order("created_at", desc=True)
    if user.role != "admin":
        q = q.eq("user_id", user.id)
    if client_id:
        q = q.eq("client_id", str(client_id))
    if state:
        q = q.eq("state", state)
    res = run_sb(lambda: q.execute())
    items: list[SoilReportListItem] = []
    for row in res.data or []:
        items.append(SoilReportListItem(
            id=UUID(row["id"]),
            title=row.get("title"),
            scope_kind=row["scope_kind"],
            block_count=len(row.get("block_ids") or []),
            analysis_count=len(row.get("analysis_ids") or []),
            state=row["state"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            farm_name=row.get("farm_name"),
            narrative_locked=bool(row.get("narrative_locked_at")),
        ))
    return items


@router.get("/{report_id}", response_model=SoilReportResponse)
async def fetch_report(
    report_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    sb = get_supabase_admin()
    q = sb.table("soil_reports").select("*").eq("id", str(report_id)).is_("deleted_at", "null")
    if user.role != "admin":
        q = q.eq("user_id", user.id)
    res = run_sb(lambda: q.limit(1).execute())
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Soil report not found")
    row = res.data[0]
    return SoilReportResponse(
        id=UUID(row["id"]),
        title=row.get("title"),
        scope_kind=row["scope_kind"],
        state=row["state"],
        block_ids=[UUID(b) for b in row.get("block_ids") or []],
        analysis_ids=[UUID(a) for a in row.get("analysis_ids") or []],
        farm_id=UUID(row["farm_id"]) if row.get("farm_id") else None,
        farm_name=row.get("farm_name"),
        report_payload=row.get("report_payload") or {},
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        narrative_locked_at=row.get("narrative_locked_at"),
    )


# ============================================================
# Narrative — generate / fetch
# ============================================================


class GenerateSoilNarrativeResponse(BaseModel):
    soil_report_id: UUID
    narrative_overrides: dict
    raw_prose: dict
    narrative_report: dict
    narrative_generated_at: datetime
    narrative_locked_at: Optional[datetime] = None


@router.post(
    "/{report_id}/generate-narrative",
    response_model=GenerateSoilNarrativeResponse,
)
async def generate_narrative(
    report_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Run Opus over the soil report's payload. Persists the prose +
    audit verdict on the row. Refuses if the narrative is locked."""
    from app.services.narrative.opus_renderer import enhance_soil_report_prose

    sb = get_supabase_admin()
    q = sb.table("soil_reports").select(
        "id, user_id, state, report_payload, narrative_locked_at",
    ).eq("id", str(report_id)).is_("deleted_at", "null")
    if user.role != "admin":
        q = q.eq("user_id", user.id)
    res = run_sb(lambda: q.limit(1).execute())
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Soil report not found")
    row = res.data[0]
    if row.get("narrative_locked_at"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Narrative is locked — soil report has been approved. "
            "Move back to draft before regenerating.",
        )

    try:
        result = enhance_soil_report_prose(row["report_payload"])
    except RuntimeError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"Narrative pipeline not configured: {exc}",
        )

    cost_usd = round(
        result.input_tokens * 15 / 1_000_000
        + result.output_tokens * 75 / 1_000_000
        + result.cache_read_tokens * 1.5 / 1_000_000
        + result.cache_write_tokens * 18.75 / 1_000_000,
        4,
    )

    # Telemetry → ai_usage
    try:
        sb.table("ai_usage").insert({
            "user_id": user.id,
            "operation": "generate_soil_report_narrative",
            "model": "claude-opus-4-7",
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cost_usd": cost_usd,
            "metadata": {
                "soil_report_id": str(report_id),
                "verdict": result.verdict,
                "section_count": result.section_count,
                "duration_seconds": round(result.duration_seconds, 1),
                "cache_read_tokens": result.cache_read_tokens,
                "cache_write_tokens": result.cache_write_tokens,
                "issue_count": len(result.issues),
            },
        }).execute()
    except Exception as exc:
        logger.warning("ai_usage insert failed: %s", exc)

    if cost_usd > NARRATIVE_COST_CAP_USD:
        raise HTTPException(
            status.HTTP_507_INSUFFICIENT_STORAGE,
            f"Narrative generation exceeded cost cap (${cost_usd:.2f} > "
            f"${NARRATIVE_COST_CAP_USD:.2f}). Tokens recorded in ai_usage.",
        )

    narrative_report = {
        "verdict": result.verdict,
        "issues": result.issues,
        "section_count": result.section_count,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "cache_read_tokens": result.cache_read_tokens,
        "cache_write_tokens": result.cache_write_tokens,
        "duration_seconds": round(result.duration_seconds, 1),
        "cost_usd": cost_usd,
        "used_opus_prose": result.used_opus_prose,
    }
    generated_at = datetime.utcnow()

    update = {
        "narrative_overrides": result.overrides,
        "narrative_report": narrative_report,
        "narrative_generated_at": generated_at.isoformat(),
    }
    upd_q = sb.table("soil_reports").update(update).eq("id", str(report_id))
    if user.role != "admin":
        upd_q = upd_q.eq("user_id", user.id)
    upd_q.execute()

    return GenerateSoilNarrativeResponse(
        soil_report_id=report_id,
        narrative_overrides=result.overrides,
        raw_prose=result.raw_prose,
        narrative_report=narrative_report,
        narrative_generated_at=generated_at,
        narrative_locked_at=None,
    )


class SoilNarrativeFetchResponse(BaseModel):
    soil_report_id: UUID
    narrative_overrides: Optional[dict] = None
    narrative_report: Optional[dict] = None
    narrative_generated_at: Optional[datetime] = None
    narrative_locked_at: Optional[datetime] = None


@router.get("/{report_id}/narrative", response_model=SoilNarrativeFetchResponse)
async def fetch_narrative(
    report_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    sb = get_supabase_admin()
    q = sb.table("soil_reports").select(
        "id, user_id, narrative_overrides, narrative_report, "
        "narrative_generated_at, narrative_locked_at",
    ).eq("id", str(report_id)).is_("deleted_at", "null")
    if user.role != "admin":
        q = q.eq("user_id", user.id)
    res = run_sb(lambda: q.limit(1).execute())
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Soil report not found")
    row = res.data[0]
    return SoilNarrativeFetchResponse(
        soil_report_id=report_id,
        narrative_overrides=row.get("narrative_overrides"),
        narrative_report=row.get("narrative_report"),
        narrative_generated_at=row.get("narrative_generated_at"),
        narrative_locked_at=row.get("narrative_locked_at"),
    )


# ============================================================
# Lifecycle — state transitions + archive
# ============================================================


class SoilReportStateTransitionRequest(BaseModel):
    new_state: str = Field(..., pattern=r"^(draft|approved|archived)$")
    reviewer_notes: Optional[str] = Field(None, max_length=4000)


@router.patch("/{report_id}/state", response_model=SoilReportResponse)
async def transition_state(
    report_id: UUID,
    request: SoilReportStateTransitionRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Move a soil report between lifecycle states. draft → approved
    locks the narrative; approved → draft un-locks for regeneration."""
    sb = get_supabase_admin()
    q = sb.table("soil_reports").select(
        "state, narrative_overrides"
    ).eq("id", str(report_id)).is_("deleted_at", "null")
    if user.role != "admin":
        q = q.eq("user_id", user.id)
    res = run_sb(lambda: q.limit(1).execute())
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Soil report not found")

    curr_state = res.data[0]["state"]
    new_state = request.new_state
    allowed = {
        "draft":    {"approved", "archived"},
        "approved": {"draft", "archived"},
        "archived": set(),
    }
    if new_state not in allowed.get(curr_state, set()):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Invalid state transition: {curr_state} → {new_state}",
        )

    update: dict[str, Any] = {"state": new_state}
    if curr_state == "draft" and new_state == "approved":
        update["reviewer_id"] = user.id
        update["reviewed_at"] = datetime.utcnow().isoformat()
        if request.reviewer_notes is not None:
            update["reviewer_notes"] = request.reviewer_notes
        # Lock narrative if any was generated.
        if res.data[0].get("narrative_overrides"):
            update["narrative_locked_at"] = datetime.utcnow().isoformat()
    if curr_state == "approved" and new_state == "draft":
        update["narrative_locked_at"] = None

    uq = sb.table("soil_reports").update(update).eq("id", str(report_id))
    if user.role != "admin":
        uq = uq.eq("user_id", user.id)
    saved = run_sb(lambda: uq.execute())
    if not saved.data:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Update failed")
    row = saved.data[0]

    # Re-fetch with full payload (the update return excludes JSONB cols).
    full = run_sb(lambda: sb.table("soil_reports").select("*").eq("id", str(report_id)).limit(1).execute())
    if not full.data:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Re-fetch failed")
    full_row = full.data[0]

    return SoilReportResponse(
        id=UUID(full_row["id"]),
        title=full_row.get("title"),
        scope_kind=full_row["scope_kind"],
        state=full_row["state"],
        block_ids=[UUID(b) for b in full_row.get("block_ids") or []],
        analysis_ids=[UUID(a) for a in full_row.get("analysis_ids") or []],
        farm_id=UUID(full_row["farm_id"]) if full_row.get("farm_id") else None,
        farm_name=full_row.get("farm_name"),
        report_payload=full_row.get("report_payload") or {},
        created_at=full_row["created_at"],
        updated_at=full_row["updated_at"],
        narrative_locked_at=full_row.get("narrative_locked_at"),
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_report(
    report_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    sb = get_supabase_admin()
    q = sb.table("soil_reports").update({
        "state": "archived",
        "deleted_at": datetime.utcnow().isoformat(),
    }).eq("id", str(report_id))
    if user.role != "admin":
        q = q.eq("user_id", user.id)
    res = run_sb(lambda: q.execute())
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Soil report not found")
    return None


# ============================================================
# PDF render
# ============================================================


@router.get("/{report_id}/render-pdf")
async def render_pdf(
    report_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Stream the Sapling-branded soil report PDF. Uses persisted
    narrative_overrides when present so downloads are reproducible
    after approval."""
    sb = get_supabase_admin()
    q = sb.table("soil_reports").select(
        "title, report_payload, narrative_overrides, farm_name"
    ).eq("id", str(report_id)).is_("deleted_at", "null")
    if user.role != "admin":
        q = q.eq("user_id", user.id)
    res = run_sb(lambda: q.limit(1).execute())
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Soil report not found")
    row = res.data[0]

    # Load the ideal_ratios reference table fresh each render — it's
    # small (~13 rows), changes rarely, and feeds the cation balance +
    # ratio tables on each per-block view.
    ideal_ratios_rows = run_sb(
        lambda: sb.table("ideal_ratios").select("*").execute()
    ).data or []

    pdf_bytes = render_soil_report_pdf(
        row["report_payload"],
        narrative_overrides=row.get("narrative_overrides") or None,
        ideal_ratios=ideal_ratios_rows,
    )

    filename = _suggest_filename(row.get("title"), row.get("farm_name"))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


# ============================================================
# Helpers
# ============================================================


def _default_title(client: dict, farm: dict, blocks: list[BlockAnalysesInput]) -> str:
    parts: list[str] = []
    if client.get("name"):
        parts.append(client["name"])
    if farm.get("name"):
        parts.append(farm["name"])
    if len(blocks) == 1:
        parts.append(blocks[0].block_name)
        if len(blocks[0].analyses) > 1:
            parts.append("history")
    else:
        parts.append(f"{len(blocks)} blocks")
    parts.append(date.today().strftime("%Y-%m-%d"))
    return " — ".join(parts)


def _suggest_filename(title: Optional[str], farm_name: Optional[str]) -> str:
    """ASCII-safe filename from the title (Content-Disposition is latin-1)."""
    base = (title or "Soil Report").strip()
    if farm_name and farm_name not in base:
        base = f"{base} — {farm_name}"
    base = base.encode("ascii", errors="ignore").decode("ascii")
    base = base.replace("/", "-").replace("\\", "-").replace(",", "")
    base = "".join(c for c in base if c.isprintable())
    if not base:
        base = "Soil Report"
    return f"{base}.pdf"


def _load_sufficiency_rows(sb, crop: str) -> list[dict]:
    """Soil sufficiency thresholds for the crop.

    Strategy mirrors the orchestrator's catalog loader:
      1. Start with the generic `soil_sufficiency` table — covers pH,
         Ca, Mg, P, S, Na and all the parameters that don't vary by
         crop. This is the base layer.
      2. Layer crop-specific rows from `crop_sufficiency_overrides` on
         top — for Macadamia, that's B / K / N / Zn with crop-tuned
         optimal bands. Override-row values replace the generic values
         for the same `parameter`.
      3. If the cultivar variant has no overrides of its own, fall
         back to the parent-genus crop name (mirrors the orchestrator's
         parent-variant fallback for "Citrus (Valencia)" → "Citrus").

    Without the generic base layer the soil report rendered K-only on
    Macadamia analyses (the override table only has 4 macadamia rows).
    """
    base_crop = crop.split("(")[0].strip() if "(" in crop else crop

    generic = sb.table("soil_sufficiency").select("*").execute().data or []

    overrides = sb.table("crop_sufficiency_overrides").select("*").eq("crop", crop).execute().data or []
    if not overrides and base_crop != crop:
        overrides = sb.table("crop_sufficiency_overrides").select("*").eq("crop", base_crop).execute().data or []

    by_param: dict[str, dict] = {}
    for r in generic:
        p = r.get("parameter")
        if p:
            by_param[p] = dict(r)
    for r in overrides:
        p = r.get("parameter")
        if p:
            existing = by_param.get(p, {})
            existing.update({k: v for k, v in r.items() if v is not None})
            by_param[p] = existing
    return list(by_param.values())


def _load_param_map_rows(sb) -> list[dict]:
    """Load the soil_parameter_map (crop_nutrient → soil_parameter mapping).
    Used when a soil column doesn't directly match a sufficiency row's
    parameter. Same lookup pattern the orchestrator uses."""
    res = sb.table("soil_parameter_map").select("*").execute()
    return res.data or []
