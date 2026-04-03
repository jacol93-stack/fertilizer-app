"""Soil analysis endpoints: classification, targets, and CRUD."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.services.soil_engine import (
    classify_soil_value,
    evaluate_ratios,
    calculate_nutrient_targets,
    adjust_targets_for_ratios,
)
from app.services.comparison_engine import calculate_crop_impact, generate_recommendations
from app.supabase_client import get_supabase_admin

router = APIRouter(tags=["Soil"])


# ── Pydantic models ──────────────────────────────────────────────────────────


class ClassifyRequest(BaseModel):
    soil_values: dict[str, float | None] = Field(
        ..., description="Soil parameter names mapped to lab values"
    )


class ClassifyResponse(BaseModel):
    classifications: dict[str, str]
    ratios: list[dict]
    thresholds: dict[str, dict] | None = None


class TargetsRequest(BaseModel):
    crop_name: str = Field(..., min_length=1, max_length=200)
    yield_target: float = Field(..., gt=0, le=1_000_000)
    soil_values: dict[str, float | None]


class TargetsResponse(BaseModel):
    targets: list[dict]


class SoilAnalysisCreate(BaseModel):
    client_id: str | None = None
    farm_id: str | None = None
    field_id: str | None = None
    crop: str | None = Field(None, max_length=200)
    cultivar: str | None = Field(None, max_length=200)
    yield_target: float | None = Field(None, gt=0, le=1_000_000)
    yield_unit: str | None = Field(None, max_length=50)
    field_area_ha: float | None = Field(None, gt=0, le=100_000)
    pop_per_ha: int | None = Field(None, gt=0, le=1_000_000)
    lab_name: str | None = Field(None, max_length=200)
    analysis_date: str | None = Field(None, max_length=20)
    soil_values: dict | None = None
    nutrient_targets: list[dict] | None = None
    ratio_results: list[dict] | None = None
    classifications: dict | None = None
    products: list[dict] | None = None
    total_cost_ha: float | None = Field(0, ge=0, le=100_000_000)
    norms_snapshot: dict | None = None
    status: str = Field("saved", max_length=20)


class SoilAnalysisOut(BaseModel):
    model_config = {"extra": "allow"}
    id: str


# ── Helper ────────────────────────────────────────────────────────────────────


def _audit(sb, user: CurrentUser, action: str, table: str, record_id: str | None = None, detail: dict | None = None):
    """Fire-and-forget audit log via DB RPC."""
    try:
        sb.rpc(
            "log_audit_event",
            {
                "p_event_type": action,
                "p_entity_type": table,
                "p_entity_id": record_id,
                "p_metadata": detail or {},
                "p_user_id": user.id,
            },
        ).execute()
    except Exception:
        pass  # audit failure should never block the request


# ── Classification ────────────────────────────────────────────────────────────


@router.post("/classify", response_model=ClassifyResponse)
def classify_soil(
    body: ClassifyRequest,
    crop: Optional[str] = Query(None, description="Crop name for crop-specific thresholds"),
    user: CurrentUser = Depends(get_current_user),
):
    """Classify each soil parameter and evaluate nutrient ratios."""
    sb = get_supabase_admin()

    sufficiency = sb.table("soil_sufficiency").select("*").execute().data
    ratio_rows = sb.table("ideal_ratios").select("*").execute().data

    # Fetch crop-specific overrides if crop specified
    crop_overrides = None
    if crop:
        try:
            result = sb.table("crop_sufficiency_overrides").select("*").eq("crop", crop).execute()
            crop_overrides = result.data or None
        except Exception:
            pass

    classifications = {}
    for param, value in body.soil_values.items():
        classifications[param] = classify_soil_value(value, param, sufficiency, crop_overrides)

    ratios = evaluate_ratios(body.soil_values, ratio_rows)

    # Build merged thresholds for frontend gauge rendering
    threshold_map = {}
    for row in (sufficiency or []):
        t = {
            "very_low_max": float(row["very_low_max"]),
            "low_max": float(row["low_max"]),
            "optimal_max": float(row["optimal_max"]),
            "high_max": float(row["high_max"]),
        }
        if crop_overrides:
            ovr = next((o for o in crop_overrides if o["parameter"] == row["parameter"]), None)
            if ovr:
                for key in t:
                    if ovr.get(key) is not None:
                        t[key] = float(ovr[key])
        threshold_map[row["parameter"]] = t

    return ClassifyResponse(classifications=classifications, ratios=ratios, thresholds=threshold_map)


# ── Nutrient targets ─────────────────────────────────────────────────────────


@router.post("/targets", response_model=TargetsResponse)
def nutrient_targets(body: TargetsRequest, user: CurrentUser = Depends(get_current_user)):
    """Calculate adjusted nutrient targets for a crop + yield."""
    sb = get_supabase_admin()

    crop_rows = sb.table("crop_requirements").select("*").execute().data
    sufficiency = sb.table("soil_sufficiency").select("*").execute().data
    adjustment = sb.table("adjustment_factors").select("*").execute().data
    param_map = sb.table("soil_parameter_map").select("*").execute().data
    ratio_rows = sb.table("ideal_ratios").select("*").execute().data

    # Fetch crop-specific overrides
    crop_overrides = None
    try:
        result = sb.table("crop_sufficiency_overrides").select("*").eq("crop", body.crop_name).execute()
        crop_overrides = result.data or None
    except Exception:
        pass

    # Step 1: Sufficiency-based targets
    targets = calculate_nutrient_targets(
        crop_name=body.crop_name,
        yield_target=body.yield_target,
        soil_values=body.soil_values,
        crop_rows=crop_rows,
        sufficiency_rows=sufficiency,
        adjustment_rows=adjustment,
        param_map_rows=param_map,
        crop_override_rows=crop_overrides,
    )

    # Step 2: Evaluate ratios
    ratio_results = evaluate_ratios(body.soil_values, ratio_rows)

    # Step 3: Adjust targets based on ratio imbalances
    adjusted_targets = adjust_targets_for_ratios(
        targets=targets,
        ratio_results=ratio_results,
        soil_values=body.soil_values,
        ratio_rows=ratio_rows,
    )

    # Auto-save draft for audit trail (admin visibility only)
    try:
        draft_data = {
            "agent_id": user.id,
            "crop": body.crop_name,
            "yield_target": body.yield_target,
            "soil_values": body.soil_values,
            "nutrient_targets": adjusted_targets,
            "ratio_results": [dict(r) for r in ratio_results],
            "classifications": {},
            "status": "draft",
        }
        # Classify for the draft record
        for param, value in body.soil_values.items():
            if value is not None:
                draft_data["classifications"][param] = classify_soil_value(
                    value, param, sufficiency, crop_overrides
                )
        draft_result = sb.table("soil_analyses").insert(draft_data).execute()
        if draft_result.data:
            _audit(sb, user, "soil_draft", "soil_analyses", draft_result.data[0]["id"])
    except Exception:
        pass

    return TargetsResponse(targets=adjusted_targets)


# ── Combined run (ephemeral — no save) ───────────────────────────────────────


class RunAnalysisRequest(BaseModel):
    soil_values: dict[str, float | None]
    crop_name: str | None = Field(None, max_length=200)
    yield_target: float | None = Field(None, gt=0, le=1_000_000)


class RunAnalysisResponse(BaseModel):
    classifications: dict[str, str]
    ratios: list[dict]
    thresholds: dict[str, dict] | None = None
    targets: list[dict] | None = None


@router.post("/run", response_model=RunAnalysisResponse)
def run_analysis(body: RunAnalysisRequest, user: CurrentUser = Depends(get_current_user)):
    """Run a full analysis (classify + targets) without saving to the database.

    Audit-logged for usage tracking but no soil_analyses row is created.
    """
    sb = get_supabase_admin()

    sufficiency = sb.table("soil_sufficiency").select("*").execute().data
    ratio_rows = sb.table("ideal_ratios").select("*").execute().data

    # Fetch crop-specific overrides if crop specified
    crop_overrides = None
    if body.crop_name:
        try:
            result = sb.table("crop_sufficiency_overrides").select("*").eq("crop", body.crop_name).execute()
            crop_overrides = result.data or None
        except Exception:
            pass

    # Step 1: Classify
    classifications = {}
    for param, value in body.soil_values.items():
        classifications[param] = classify_soil_value(value, param, sufficiency, crop_overrides)

    ratios = evaluate_ratios(body.soil_values, ratio_rows)

    # Build thresholds for frontend
    threshold_map = {}
    for row in (sufficiency or []):
        t = {
            "very_low_max": float(row["very_low_max"]),
            "low_max": float(row["low_max"]),
            "optimal_max": float(row["optimal_max"]),
            "high_max": float(row["high_max"]),
        }
        if crop_overrides:
            ovr = next((o for o in crop_overrides if o["parameter"] == row["parameter"]), None)
            if ovr:
                for key in t:
                    if ovr.get(key) is not None:
                        t[key] = float(ovr[key])
        threshold_map[row["parameter"]] = t

    # Step 2: Calculate targets (if crop + yield provided)
    adjusted_targets = None
    if body.crop_name and body.yield_target:
        crop_rows = sb.table("crop_requirements").select("*").execute().data
        adjustment = sb.table("adjustment_factors").select("*").execute().data
        param_map = sb.table("soil_parameter_map").select("*").execute().data

        targets = calculate_nutrient_targets(
            crop_name=body.crop_name,
            yield_target=body.yield_target,
            soil_values=body.soil_values,
            crop_rows=crop_rows,
            sufficiency_rows=sufficiency,
            adjustment_rows=adjustment,
            param_map_rows=param_map,
            crop_override_rows=crop_overrides,
        )

        adjusted_targets = adjust_targets_for_ratios(
            targets=targets,
            ratio_results=ratios,
            soil_values=body.soil_values,
            ratio_rows=ratio_rows,
        )

    # Audit log the run (no DB record created)
    _audit(sb, user, "analysis_run", "soil_analyses", detail={
        "crop": body.crop_name,
        "yield_target": body.yield_target,
        "soil_params": list(body.soil_values.keys()),
    })

    return RunAnalysisResponse(
        classifications=classifications,
        ratios=ratios,
        thresholds=threshold_map,
        targets=adjusted_targets,
    )


# ── Lab report extraction ────────────────────────────────────────────────────


@router.post("/extract")
async def extract_lab_report(
    file: UploadFile = File(...),
    lab_name_hint: str | None = Form(None),
    user: CurrentUser = Depends(get_current_user),
):
    """Extract soil analysis values from an uploaded lab report (PDF or photo).

    Uses Claude vision API to read the document. If a lab template exists for
    the detected lab, learned field mappings improve accuracy.
    """
    from app.services.lab_extractor import extract_from_document

    allowed_types = {
        "application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}. Upload a PDF or image.")

    # 50 MB limit
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 50 MB.")

    try:
        result = extract_from_document(contents, file.content_type, lab_name_hint)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Extraction failed: {str(e)}")

    sb = get_supabase_admin()
    _audit(sb, user, "lab_extract", "soil_analyses", detail={
        "lab_name": result.get("lab_name"),
        "params_extracted": len(result.get("values", {})),
        "file_type": file.content_type,
    })

    # Log AI usage
    ai_usage = result.get("ai_usage")
    if ai_usage:
        try:
            sb.table("ai_usage").insert({
                "user_id": user.id,
                "operation": "extract_lab",
                "model": ai_usage.get("model", ""),
                "input_tokens": ai_usage.get("input_tokens", 0),
                "output_tokens": ai_usage.get("output_tokens", 0),
                "cost_usd": ai_usage.get("cost_usd", 0),
                "metadata": {
                    "lab_name": result.get("lab_name"),
                    "num_samples": result.get("num_samples", 0),
                    "file_type": file.content_type,
                },
            }).execute()
        except Exception:
            pass  # Never block for usage logging

    return result


class LearnCorrectionsRequest(BaseModel):
    lab_name: str = Field(..., min_length=1, max_length=200)
    original_values: dict[str, float | None]
    corrected_values: dict[str, float | None]


@router.post("/extract/learn")
def learn_lab_corrections(
    body: LearnCorrectionsRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Record user corrections to improve future extraction accuracy for this lab.

    Diffs original vs corrected values and updates the lab template mapping.
    """
    from app.services.lab_extractor import learn_from_corrections

    result = learn_from_corrections(
        lab_name=body.lab_name,
        original_values=body.original_values,
        corrected_values=body.corrected_values,
    )

    sb = get_supabase_admin()
    _audit(sb, user, "lab_learn", "lab_templates", detail={
        "lab_name": body.lab_name,
        "corrections": result.get("corrections_recorded", 0),
    })

    return result


# ── CRUD ──────────────────────────────────────────────────────────────────────


@router.post("/", status_code=201)
def create_soil_analysis(body: SoilAnalysisCreate, user: CurrentUser = Depends(get_current_user)):
    """Save a soil analysis record with norms snapshot for future PDF generation."""
    sb = get_supabase_admin()

    data = body.model_dump(exclude_none=False)
    data["agent_id"] = user.id

    # Snapshot current norms if not provided — merge crop-specific overrides
    if not data.get("norms_snapshot"):
        try:
            snapshot = {}
            suf = sb.table("soil_sufficiency").select("*").execute()
            suf_rows = suf.data or []

            # Merge crop-specific overrides into sufficiency snapshot
            crop_name = data.get("crop")
            if crop_name and suf_rows:
                try:
                    overrides = sb.table("crop_sufficiency_overrides").select("*").eq("crop", crop_name).execute()
                    if overrides.data:
                        override_map = {r["parameter"]: r for r in overrides.data}
                        merged = []
                        for row in suf_rows:
                            new_row = dict(row)
                            ovr = override_map.get(row["parameter"])
                            if ovr:
                                for key in ["very_low_max", "low_max", "optimal_max", "high_max"]:
                                    if ovr.get(key) is not None:
                                        new_row[key] = ovr[key]
                            merged.append(new_row)
                        suf_rows = merged
                except Exception:
                    pass

            snapshot["sufficiency"] = suf_rows
            ratios = sb.table("ideal_ratios").select("*").execute()
            if ratios.data:
                snapshot["ratios"] = ratios.data
            data["norms_snapshot"] = snapshot
        except Exception:
            pass

    result = sb.table("soil_analyses").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save soil analysis")

    record = result.data[0]
    _audit(sb, user, "create", "soil_analyses", record["id"])
    return record


class CompareRequest(BaseModel):
    analysis_ids: list[str] = Field(..., min_length=2)


@router.post("/compare")
def compare_soil_analyses(
    body: CompareRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Compare multiple soil analyses — returns side-by-side data, crop impact, and recommendations."""
    sb = get_supabase_admin()

    # Fetch all requested analyses
    result = sb.table("soil_analyses").select("*").in_("id", body.analysis_ids).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No analyses found")

    analyses = result.data

    # Access control: agents can only compare their own
    if user.role != "admin":
        for a in analyses:
            if a.get("agent_id") != user.id:
                raise HTTPException(status_code=403, detail="Access denied to one or more analyses")

    # Sort by analysis_date (or created_at as fallback)
    def sort_key(a):
        return a.get("analysis_date") or a.get("created_at", "")[:10]

    analyses.sort(key=sort_key)

    # Fetch reference data for crop impact (sequential to avoid connection exhaustion)
    import time
    try:
        crop_rows = sb.table("crop_requirements").select("*").execute().data or []
    except Exception:
        crop_rows = []
    try:
        param_map_rows = sb.table("soil_parameter_map").select("*").execute().data or []
    except Exception:
        param_map_rows = []
    try:
        sufficiency_rows = sb.table("soil_sufficiency").select("*").execute().data or []
    except Exception:
        sufficiency_rows = []

    # Detect same field vs different fields
    field_ids = set(a.get("field_id") for a in analyses if a.get("field_id"))
    is_same_field = len(field_ids) == 1
    comparison_type = "timeline" if is_same_field else "snapshot"

    # Calculate crop impact between each consecutive pair (only for same-field)
    crop_impacts = []
    if is_same_field:
        the_field_id = field_ids.pop() if field_ids else None
        for i in range(len(analyses) - 1):
            # Fetch crop history between the two analysis dates
            crop_history = []
            if the_field_id:
                d1 = analyses[i].get("analysis_date") or analyses[i].get("created_at", "")[:10]
                d2 = analyses[i + 1].get("analysis_date") or analyses[i + 1].get("created_at", "")[:10]
                try:
                    ch_result = (
                        sb.table("field_crop_history")
                        .select("*")
                        .eq("field_id", the_field_id)
                        .gte("date_planted", d1)
                        .lte("date_planted", d2)
                        .order("date_planted")
                        .execute()
                    )
                    crop_history = ch_result.data or []
                except Exception:
                    crop_history = []

            impact = calculate_crop_impact(
                analyses[i], analyses[i + 1], crop_rows, param_map_rows, crop_history
            )
            crop_impacts.append(impact)

    # Generate recommendations
    recommendations = generate_recommendations(analyses, crop_impacts, comparison_type)

    # Build sufficiency thresholds for chart rendering
    thresholds = {}
    for row in sufficiency_rows:
        thresholds[row["parameter"]] = {
            "very_low_max": float(row["very_low_max"]),
            "low_max": float(row["low_max"]),
            "optimal_max": float(row["optimal_max"]),
            "high_max": float(row["high_max"]),
        }

    return {
        "analyses": analyses,
        "comparison_type": comparison_type,
        "crop_impact": crop_impacts,
        "recommendations": recommendations,
        "sufficiency_thresholds": thresholds,
    }


@router.get("/")
def list_soil_analyses(
    search: Optional[str] = Query(None, description="Search by client, farm, or crop"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    farm_id: Optional[str] = Query(None, description="Filter by farm ID"),
    field_id: Optional[str] = Query(None, description="Filter by field ID"),
    user: CurrentUser = Depends(get_current_user),
):
    """List soil analyses. Agents see their own; admins see all."""
    sb = get_supabase_admin()

    query = sb.table("soil_analyses").select("*").order("created_at", desc=True)

    if user.role != "admin":
        query = query.eq("agent_id", user.id).eq("status", "saved").is_("deleted_at", "null")

    if search:
        query = query.or_(
            f"crop.ilike.%{search}%,"
            f"lab_name.ilike.%{search}%"
        )
    if client_id:
        query = query.eq("client_id", client_id)
    if farm_id:
        query = query.eq("farm_id", farm_id)
    if field_id:
        query = query.eq("field_id", field_id)

    result = query.execute()
    return result.data


@router.get("/{analysis_id}")
def get_soil_analysis(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    """Retrieve a single soil analysis."""
    sb = get_supabase_admin()

    result = sb.table("soil_analyses").select("*").eq("id", analysis_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Soil analysis not found")

    record = result.data[0]

    # Agents can only view their own
    if user.role != "admin" and record.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return record


@router.post("/{analysis_id}/delete", status_code=200)
def soft_delete_soil_analysis(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    """Soft-delete a soil analysis (mark as deleted)."""
    sb = get_supabase_admin()

    # Verify exists and user has access
    existing = sb.table("soil_analyses").select("id, agent_id").eq("id", analysis_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    if user.role != "admin" and existing.data[0].get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    now = datetime.now(timezone.utc).isoformat()
    sb.table("soil_analyses").update({
        "deleted_at": now,
        "deleted_by": user.id,
    }).eq("id", analysis_id).execute()

    _audit(sb, user, "soft_delete", "soil_analyses", analysis_id)
    return {"detail": "Soil analysis soft-deleted"}


@router.post("/{analysis_id}/restore", status_code=200)
def restore_soil_analysis(analysis_id: str, user: CurrentUser = Depends(require_admin)):
    """Admin only. Restore a soft-deleted soil analysis."""
    sb = get_supabase_admin()
    result = sb.table("soil_analyses").update({
        "deleted_at": None,
        "deleted_by": None,
    }).eq("id", analysis_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Soil analysis not found")

    _audit(sb, user, "restore", "soil_analyses", analysis_id)
    return {"detail": "Soil analysis restored"}


@router.delete("/{analysis_id}", status_code=200)
def hard_delete_soil_analysis(analysis_id: str, user: CurrentUser = Depends(require_admin)):
    """Hard-delete a soil analysis (admin only)."""
    sb = get_supabase_admin()

    existing = sb.table("soil_analyses").select("id").eq("id", analysis_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Soil analysis not found")

    sb.table("soil_analyses").delete().eq("id", analysis_id).execute()

    _audit(sb, user, "hard_delete", "soil_analyses", analysis_id)
    return {"detail": "Soil analysis permanently deleted"}
