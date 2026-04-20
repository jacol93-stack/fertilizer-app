"""Soil analysis endpoints: classification, targets, and CRUD."""

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field

# Conflict resolution values accepted on write endpoints when a field already
# has a recent analysis. Phase 1 supports "replace" only; the other values are
# reserved for later phases (merge-as-composite UX).
ConflictResolution = Literal[
    "replace",
    "merge_as_composite",
    "keep_both_new_latest",
    "keep_both_old_latest",
]
FIELD_ANALYSIS_CONFLICT_WINDOW_DAYS = 7

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
from app.services.aggregation import aggregate_samples
from app.services.soil_engine import (
    classify_soil_value,
    evaluate_ratios,
    calculate_nutrient_targets,
    adjust_targets_for_ratios,
)
from app.services.comparison_engine import calculate_crop_impact, generate_recommendations
from app.supabase_client import get_supabase_admin

router = APIRouter(tags=["Soil"])


def _rate_table_context(obj) -> dict:
    """Build the context dict passed to lookup_rate_table() from a request.

    Dimensions the FERTASA rate tables can filter on: water_regime,
    clay_pct, texture, rainfall_mm, region, prior_crop. Request models
    don't carry all of these today; anything absent is left out of the
    context and the lookup treats it as "caller doesn't know" (rows that
    require that dimension are skipped, generic rows still match).

    water_regime defaults to 'dryland': SA field-crop production is
    overwhelmingly dryland, and the seeded FERTASA wheat/potato/canola
    tables are all dryland-specific. Irrigation-specific tables (seeded
    in later migrations) will require an explicit override from a
    request field that doesn't yet exist — add it when that context
    becomes available.
    """
    ctx: dict = {"water_regime": "dryland"}
    for key in ("clay_pct", "texture", "rainfall_mm", "region",
                "prior_crop", "water_regime"):
        val = getattr(obj, key, None)
        if val is not None:
            ctx[key] = val
    return ctx


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


class ComponentSampleIn(BaseModel):
    """One physical sample contributing to a composite soil analysis.

    When two or more of these are supplied on a create call, the server
    aggregates them (area-weighted if every sample carries `weight_ha`,
    otherwise equal-weighted) and retains the raw components on the
    stored record. A caller supplying exactly one component, or none at
    all, is treated as a single-sample record.
    """
    values: dict[str, float | None]
    weight_ha: float | None = Field(None, gt=0, le=100_000)
    location_label: str | None = Field(None, max_length=200)
    depth_cm: float | None = Field(None, ge=0, le=500)


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
    source_document_url: str | None = Field(None, max_length=500)
    status: str = Field("saved", max_length=20)
    conflict_resolution: ConflictResolution | None = None
    # Multi-sample composite: supply ≥2 to build one composite record
    # with non-destructive retention of the raw samples. Composite's
    # weighted mean overrides `soil_values` if both are supplied.
    component_samples: list[ComponentSampleIn] | None = None


class SoilAnalysisOut(BaseModel):
    model_config = {"extra": "allow"}
    id: str


# ── Helper ────────────────────────────────────────────────────────────────────


def _check_field_analysis_conflict(
    sb,
    field_id: str,
    window_days: int = FIELD_ANALYSIS_CONFLICT_WINDOW_DAYS,
) -> dict | None:
    """Return a conflict payload if `field_id` has a recent analysis, else None.

    A conflict means the field's `latest_analysis_id` points at a soil analysis
    whose `analysis_date` (or `created_at` fallback) is within `window_days` of
    now. The client must pass `conflict_resolution` to proceed — otherwise the
    save endpoint returns HTTP 409 so the UI can confirm instead of silently
    overwriting the previous analysis.
    """
    if not field_id:
        return None
    try:
        f = sb.table("fields").select(
            "id, name, latest_analysis_id"
        ).eq("id", field_id).execute()
        if not f.data or not f.data[0].get("latest_analysis_id"):
            return None
        latest_id = f.data[0]["latest_analysis_id"]
        field_name = f.data[0].get("name") or ""

        a = sb.table("soil_analyses").select(
            "id, analysis_date, created_at, crop"
        ).eq("id", latest_id).execute()
        if not a.data:
            return None
        existing = a.data[0]

        ref_str = existing.get("analysis_date") or existing.get("created_at")
        if not ref_str:
            return None
        try:
            ref = datetime.fromisoformat(ref_str.replace("Z", "+00:00"))
        except ValueError:
            return None
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - ref).days
        if age_days > window_days:
            return None

        return {
            "field_id": field_id,
            "field_name": field_name,
            "existing": {
                "id": existing["id"],
                "analysis_date": existing.get("analysis_date"),
                "created_at": existing.get("created_at"),
                "crop": existing.get("crop"),
            },
            "window_days": window_days,
        }
    except Exception:
        return None


def _validate_conflict_resolution(value: ConflictResolution | None) -> None:
    """All four resolutions are supported after Phase 7."""
    if value is None:
        return
    if value in ("replace", "merge_as_composite", "keep_both_new_latest", "keep_both_old_latest"):
        return
    raise HTTPException(
        status_code=422,
        detail=f"Unknown conflict_resolution '{value}'.",
    )


def _merge_incoming_into_existing(
    sb,
    existing_analysis_id: str,
    incoming_soil_values: dict,
    incoming_components: list | None,
    *,
    default_weight_ha: float | None = None,
    default_location_label: str | None = None,
    default_depth_cm: float | None = None,
) -> dict:
    """Non-destructive merge: absorb the incoming sample(s) into an existing
    analysis as additional components, re-aggregate, and UPDATE the row in
    place. Returns the updated analysis record.

    If the existing row has no `component_samples` retained (legacy /
    single-sample), its `soil_values` are treated as one component so no
    data is lost.
    """
    existing_result = sb.table("soil_analyses").select(
        "id, soil_values, component_samples, composition_method"
    ).eq("id", existing_analysis_id).execute()
    if not existing_result.data:
        raise HTTPException(status_code=404, detail="Existing analysis not found for merge")
    existing = existing_result.data[0]

    existing_components = existing.get("component_samples") or []
    if not existing_components:
        # Promote the legacy single-sample row into a component list with
        # one entry so we don't lose its values when aggregating.
        existing_components = [{
            "values": {k: v for k, v in (existing.get("soil_values") or {}).items() if v is not None},
        }]

    incoming_as_components: list[dict] = []
    if incoming_components:
        incoming_as_components = list(incoming_components)
    elif incoming_soil_values:
        incoming_as_components = [{
            "values": {k: v for k, v in incoming_soil_values.items() if v is not None},
            **({"weight_ha": default_weight_ha} if default_weight_ha is not None else {}),
            **({"location_label": default_location_label} if default_location_label else {}),
            **({"depth_cm": default_depth_cm} if default_depth_cm is not None else {}),
        }]

    combined = existing_components + incoming_as_components
    weights: list[float] | None = None
    if all(c.get("weight_ha") is not None and c.get("weight_ha") > 0 for c in combined):
        weights = [float(c["weight_ha"]) for c in combined]

    agg = aggregate_samples(combined, weights=weights)

    update_row: dict = {
        "soil_values": agg.values,
        "component_samples": combined,
        "composition_method": agg.composition_method,
        "replicate_count": agg.replicate_count,
        "aggregation_stats": agg.stats_as_dict(),
    }
    result = sb.table("soil_analyses").update(update_row).eq("id", existing_analysis_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to merge analyses")
    return result.data[0]


def _build_composite_fields(components) -> dict | None:
    """Aggregate ≥2 component samples into the DB field set for soil_analyses.

    Returns None if fewer than two components are supplied (the caller
    should treat the data as a single-sample record and proceed with
    its existing `soil_values`).
    """
    if not components or len(components) < 2:
        return None
    payload = [
        {
            "values": {k: v for k, v in c.values.items() if v is not None},
            **({"weight_ha": c.weight_ha} if c.weight_ha is not None else {}),
            **({"location_label": c.location_label} if c.location_label else {}),
            **({"depth_cm": c.depth_cm} if c.depth_cm is not None else {}),
        }
        for c in components
    ]
    weights: list[float] | None = None
    if all(c.weight_ha is not None and c.weight_ha > 0 for c in components):
        weights = [float(c.weight_ha) for c in components]
    agg = aggregate_samples(payload, weights=weights)
    return {
        "soil_values": agg.values,
        "component_samples": payload,
        "composition_method": agg.composition_method,
        "replicate_count": agg.replicate_count,
        "aggregation_stats": agg.stats_as_dict(),
    }


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
    rate_tables = sb.table("fertilizer_rate_tables").select("*").eq("crop", body.crop_name).execute().data or []

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
        rate_table_rows=rate_tables,
        rate_table_context=_rate_table_context(body),
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
        rate_tables = sb.table("fertilizer_rate_tables").select("*").eq("crop", body.crop_name).execute().data or []

        targets = calculate_nutrient_targets(
            crop_name=body.crop_name,
            yield_target=body.yield_target,
            soil_values=body.soil_values,
            crop_rows=crop_rows,
            sufficiency_rows=sufficiency,
            adjustment_rows=adjustment,
            param_map_rows=param_map,
            crop_override_rows=crop_overrides,
            rate_table_rows=rate_tables,
            rate_table_context=_rate_table_context(body),
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
    client_id: str | None = Form(None),
    user: CurrentUser = Depends(get_current_user),
):
    """Extract soil analysis values from an uploaded lab report (PDF or photo).

    Uses Claude vision API to read the document. If a lab template exists for
    the detected lab, learned field mappings improve accuracy.
    """
    from app.services.lab_extractor import extract_from_document
    import hashlib

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

    # Store original document for agent retrieval
    source_document_url = None
    try:
        ext = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(file.content_type, "bin")
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(contents).hexdigest()[:8]
        owner = client_id or user.id
        storage_path = f"clients/{owner}/{ts}_{file_hash}.{ext}"
        sb.storage.from_("lab-reports").upload(
            path=storage_path,
            file=contents,
            file_options={"content-type": file.content_type},
        )
        source_document_url = storage_path
    except Exception:
        pass  # Non-critical — extraction still works without storage

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

    if source_document_url:
        result["source_document_url"] = source_document_url

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

    _validate_conflict_resolution(body.conflict_resolution)

    data = body.model_dump(exclude_none=False)
    data.pop("conflict_resolution", None)
    # component_samples are turned into server-side columns via
    # _build_composite_fields below; drop the raw input shape from the
    # insert payload so Supabase doesn't receive a list of Pydantic dicts
    # that don't match the JSONB layout we actually store.
    data.pop("component_samples", None)
    data["agent_id"] = user.id

    composite = _build_composite_fields(body.component_samples)
    if composite is not None:
        data.update(composite)

    # Guard: if the target field already has a recent analysis, require the
    # caller to acknowledge. Prevents silent orphaning of the previous record.
    existing_conflict: dict | None = None
    if data.get("field_id"):
        existing_conflict = _check_field_analysis_conflict(sb, data["field_id"])
        if existing_conflict and body.conflict_resolution is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "field_analysis_conflict",
                    "conflicts": [existing_conflict],
                },
            )

    # Merge-as-composite short-circuits the whole insert path: instead of a
    # new row, we fold the incoming sample(s) into the existing analysis.
    if body.conflict_resolution == "merge_as_composite" and existing_conflict:
        incoming_components_raw = [c.model_dump() for c in (body.component_samples or [])]
        merged = _merge_incoming_into_existing(
            sb,
            existing_conflict["existing"]["id"],
            incoming_soil_values=data.get("soil_values") or {},
            incoming_components=incoming_components_raw or None,
        )
        _audit(
            sb, user, "merge", "soil_analyses", merged["id"],
            detail={"conflict_resolution": "merge_as_composite"},
        )
        return merged

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

    # Auto-populate field/farm/customer text names from IDs if missing
    if data.get("field_id") and not data.get("field"):
        try:
            f = sb.table("fields").select("name").eq("id", data["field_id"]).execute()
            if f.data:
                data["field"] = f.data[0]["name"]
        except Exception:
            pass
    if data.get("farm_id") and not data.get("farm"):
        try:
            f = sb.table("farms").select("name").eq("id", data["farm_id"]).execute()
            if f.data:
                data["farm"] = f.data[0]["name"]
        except Exception:
            pass
    if data.get("client_id") and not data.get("customer"):
        try:
            c = sb.table("clients").select("name").eq("id", data["client_id"]).execute()
            if c.data:
                data["customer"] = c.data[0]["name"]
        except Exception:
            pass

    result = sb.table("soil_analyses").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save soil analysis")

    record = result.data[0]

    # Update field's latest_analysis_id if this analysis is linked to a field.
    # `keep_both_old_latest` is the one resolution that skips this update —
    # the new row is stored but the field keeps pointing at the earlier
    # analysis, per the agronomist's choice.
    should_set_latest = record.get("field_id") and body.conflict_resolution != "keep_both_old_latest"
    if should_set_latest:
        try:
            sb.table("fields").update({
                "latest_analysis_id": record["id"],
            }).eq("id", record["field_id"]).execute()
        except Exception:
            pass  # Non-critical

        # Season tracker: fan out adjustment detection to every active
        # programme block using this field. Detector handles its own errors.
        try:
            from app.services.adjustment_detector import (
                detect_soil_adjustment,
                find_programme_blocks_for_analysis,
            )
            for link in find_programme_blocks_for_analysis(sb, record["id"]):
                detect_soil_adjustment(
                    sb,
                    programme_id=link["programme_id"],
                    block_id=link["block_id"],
                    new_analysis_id=record["id"],
                    created_by=user.id,
                )
        except Exception:
            pass  # Non-critical; save succeeds regardless

    _audit(
        sb, user, "create", "soil_analyses", record["id"],
        detail={"conflict_resolution": body.conflict_resolution} if body.conflict_resolution else None,
    )
    return record


# ── Batch save (multi-block from client page) ─────────────────────────────────


class BatchAnalysisItem(BaseModel):
    field_id: str | None = None
    field_name: str | None = None
    crop: str | None = Field(None, max_length=200)
    cultivar: str | None = Field(None, max_length=200)
    yield_target: float | None = Field(None, gt=0, le=1_000_000)
    yield_unit: str | None = Field(None, max_length=50)
    analysis_type: str = Field("soil", pattern="^(soil|leaf)$")
    soil_values: dict[str, float | None] = Field(default_factory=dict)
    component_samples: list[ComponentSampleIn] | None = None


class BatchSaveRequest(BaseModel):
    client_id: str
    farm_id: str | None = None
    lab_name: str | None = Field(None, max_length=200)
    analysis_date: str | None = Field(None, max_length=20)
    source_document_url: str | None = Field(None, max_length=500)
    items: list[BatchAnalysisItem] = Field(..., min_length=1)
    conflict_resolution: ConflictResolution | None = None


@router.post("/batch", status_code=201)
def batch_save_analyses(body: BatchSaveRequest, user: CurrentUser = Depends(get_current_user)):
    """Save multiple soil/leaf analyses in one call, each linked to a field.

    Runs classification + targets for each item, saves to soil_analyses table,
    and updates each field's latest_analysis_id.

    Returns list of saved analysis records with their IDs.
    """
    sb = get_supabase_admin()

    _validate_conflict_resolution(body.conflict_resolution)

    # Guard: collect every field whose latest analysis is recent enough to
    # count as a conflict. If any exist and the caller has not acknowledged,
    # return 409 with the full list so the UI can show one confirmation.
    # If they have, we also keep the conflict map around so the merge /
    # keep-both paths know which existing analyses to target.
    conflict_by_field: dict[str, dict] = {}
    for item in body.items:
        if item.field_id:
            c = _check_field_analysis_conflict(sb, item.field_id)
            if c:
                conflict_by_field[item.field_id] = c
    if conflict_by_field and body.conflict_resolution is None:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "field_analysis_conflict",
                "conflicts": list(conflict_by_field.values()),
            },
        )

    # Load reference data once
    sufficiency = sb.table("soil_sufficiency").select("*").execute().data or []
    ratio_rows = sb.table("ideal_ratios").select("*").execute().data or []
    adjustment_rows = sb.table("adjustment_factors").select("*").execute().data or []
    param_map_rows = sb.table("soil_parameter_map").select("*").execute().data or []
    rate_table_rows_all = sb.table("fertilizer_rate_tables").select("*").execute().data or []

    # Lookup client name
    customer_name = ""
    try:
        c = sb.table("clients").select("name").eq("id", body.client_id).execute()
        if c.data:
            customer_name = c.data[0]["name"]
    except Exception:
        pass

    # Lookup farm name
    farm_name = ""
    if body.farm_id:
        try:
            f = sb.table("farms").select("name").eq("id", body.farm_id).execute()
            if f.data:
                farm_name = f.data[0]["name"]
        except Exception:
            pass

    # Build norms snapshot once
    norms_snapshot = {"sufficiency": sufficiency, "ratios": ratio_rows}

    # Cache farm names by ID
    farm_name_cache = {}
    if body.farm_id and farm_name:
        farm_name_cache[body.farm_id] = farm_name

    def _get_farm_name(fid):
        if not fid:
            return ""
        if fid in farm_name_cache:
            return farm_name_cache[fid]
        try:
            r = sb.table("farms").select("name").eq("id", fid).execute()
            name = r.data[0]["name"] if r.data else ""
            farm_name_cache[fid] = name
            return name
        except Exception:
            return ""

    saved = []
    for item in body.items:
        # Resolve field name and farm from field record
        field_name = item.field_name or ""
        field_farm_id = body.farm_id
        if item.field_id:
            try:
                fld = sb.table("fields").select("name, farm_id").eq("id", item.field_id).execute()
                if fld.data:
                    if not field_name:
                        field_name = fld.data[0].get("name", "")
                    if fld.data[0].get("farm_id"):
                        field_farm_id = fld.data[0]["farm_id"]
            except Exception:
                pass

        item_farm_name = _get_farm_name(field_farm_id)

        # ── LEAF analysis → leaf_analyses table ──
        if item.analysis_type == "leaf":
            # Classify leaf values
            leaf_classifications = {}
            try:
                from app.services.leaf_engine import classify_leaf_values
                leaf_result = classify_leaf_values(item.crop, {
                    k: v for k, v in item.soil_values.items() if v is not None
                })
                leaf_classifications = leaf_result.get("classifications", {})
            except Exception:
                pass

            leaf_data = {
                "agent_id": user.id,
                "client_id": body.client_id,
                "farm_id": field_farm_id,
                "field_id": item.field_id,
                "crop": item.crop or "",
                "cultivar": item.cultivar,
                "lab_name": body.lab_name,
                "sample_date": body.analysis_date,
                "values": {k: v for k, v in item.soil_values.items() if v is not None},
                "classifications": leaf_classifications,
                **({"source_document_url": body.source_document_url} if body.source_document_url else {}),
            }
            result = sb.table("leaf_analyses").insert(leaf_data).execute()
            if result.data:
                record = result.data[0]
                saved.append({**record, "_type": "leaf"})
                _audit(sb, user, "batch_create_leaf", "leaf_analyses", record["id"])
            continue

        # ── SOIL analysis → soil_analyses table ──
        # If the item carries ≥2 components, aggregate them now so the
        # downstream classifier, ratios, and nutrient-target calc all
        # operate on the composite values.
        composite = _build_composite_fields(item.component_samples)
        effective_values = composite["soil_values"] if composite else item.soil_values

        # Get crop-specific overrides
        crop_overrides = None
        if item.crop:
            try:
                ovr = sb.table("crop_sufficiency_overrides").select("*").eq("crop", item.crop).execute()
                crop_overrides = ovr.data or None
            except Exception:
                pass

        # Classify soil values
        classifications = {}
        for param, value in effective_values.items():
            if value is not None:
                classifications[param] = classify_soil_value(
                    value, param, sufficiency, crop_overrides
                )

        # Evaluate ratios
        ratios = evaluate_ratios(effective_values, ratio_rows)

        # Calculate nutrient targets if crop + yield provided
        nutrient_targets = None
        if item.crop and item.yield_target:
            crop_rows = sb.table("crop_requirements").select("*").execute().data or []
            item_rate_tables = [r for r in rate_table_rows_all if r.get("crop") == item.crop]
            targets = calculate_nutrient_targets(
                item.crop, item.yield_target, effective_values,
                crop_rows, sufficiency, adjustment_rows, param_map_rows,
                crop_overrides,
                rate_table_rows=item_rate_tables,
                rate_table_context=_rate_table_context(item),
            )
            if targets:
                nutrient_targets = adjust_targets_for_ratios(
                    targets, ratios, effective_values, ratio_rows
                )

        # Merge crop overrides into norms snapshot for this item
        item_snapshot = dict(norms_snapshot)
        if crop_overrides:
            item_snapshot["crop_overrides"] = crop_overrides

        data = {
            "agent_id": user.id,
            "client_id": body.client_id,
            "farm_id": field_farm_id,
            "field_id": item.field_id,
            "customer": customer_name,
            "farm": item_farm_name,
            "field": field_name,
            "crop": item.crop,
            "cultivar": item.cultivar,
            "yield_target": item.yield_target,
            "yield_unit": item.yield_unit,
            "lab_name": body.lab_name,
            "analysis_date": body.analysis_date,
            "soil_values": effective_values,
            "classifications": classifications,
            "ratio_results": [dict(r) for r in ratios],
            "nutrient_targets": nutrient_targets,
            "norms_snapshot": item_snapshot,
            "status": "saved",
            **({"source_document_url": body.source_document_url} if body.source_document_url else {}),
        }
        if composite is not None:
            # Overwrite soil_values with the composite (already identical)
            # and attach component retention columns.
            data["soil_values"] = composite["soil_values"]
            data["component_samples"] = composite["component_samples"]
            data["composition_method"] = composite["composition_method"]
            data["replicate_count"] = composite["replicate_count"]
            data["aggregation_stats"] = composite["aggregation_stats"]

        # Merge-as-composite short-circuits: fold this item's values into the
        # existing analysis instead of inserting a new row.
        item_conflict = conflict_by_field.get(item.field_id) if item.field_id else None
        if body.conflict_resolution == "merge_as_composite" and item_conflict:
            incoming_components_raw = [c.model_dump() for c in (item.component_samples or [])]
            merged = _merge_incoming_into_existing(
                sb,
                item_conflict["existing"]["id"],
                incoming_soil_values=data.get("soil_values") or {},
                incoming_components=incoming_components_raw or None,
            )
            saved.append(merged)
            _audit(
                sb, user, "merge", "soil_analyses", merged["id"],
                detail={"conflict_resolution": "merge_as_composite"},
            )
            continue

        result = sb.table("soil_analyses").insert(data).execute()
        if result.data:
            record = result.data[0]
            saved.append(record)

            # Update field's latest_analysis_id. `keep_both_old_latest`
            # keeps the existing analysis as latest when a conflict was
            # resolved; everything else repoints to the new row.
            skip_latest = (
                body.conflict_resolution == "keep_both_old_latest"
                and item.field_id in conflict_by_field
            )
            if item.field_id and not skip_latest:
                try:
                    sb.table("fields").update({
                        "latest_analysis_id": record["id"],
                    }).eq("id", item.field_id).execute()
                except Exception:
                    pass

            _audit(
                sb, user, "batch_create", "soil_analyses", record["id"],
                detail={"conflict_resolution": body.conflict_resolution} if body.conflict_resolution else None,
            )

    return {"saved": len(saved), "analyses": saved}


# ── Link analysis to field ─────────────────────────────────────────────────


class LinkFieldRequest(BaseModel):
    field_id: str


@router.post("/{analysis_id}/link-field")
def link_analysis_to_field(
    analysis_id: str,
    body: LinkFieldRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Link a soil analysis to a field, updating field name and latest_analysis_id."""
    sb = get_supabase_admin()

    # Check analysis exists and user has access
    result = sb.table("soil_analyses").select("id, agent_id").eq("id", analysis_id).execute()
    if not result.data:
        raise HTTPException(404, "Analysis not found")
    if user.role != "admin" and result.data[0].get("agent_id") != user.id:
        raise HTTPException(403, "Access denied")

    # Get field info
    field_result = sb.table("fields").select("name, farm_id").eq("id", body.field_id).execute()
    if not field_result.data:
        raise HTTPException(404, "Field not found")

    field_name = field_result.data[0].get("name", "")
    farm_id = field_result.data[0].get("farm_id")

    # Get farm name
    farm_name = ""
    if farm_id:
        try:
            fr = sb.table("farms").select("name").eq("id", farm_id).execute()
            if fr.data:
                farm_name = fr.data[0]["name"]
        except Exception:
            pass

    # Update analysis
    sb.table("soil_analyses").update({
        "field_id": body.field_id,
        "farm_id": farm_id,
        "field": field_name,
        "farm": farm_name,
    }).eq("id", analysis_id).execute()

    # Update field's latest_analysis_id
    sb.table("fields").update({
        "latest_analysis_id": analysis_id,
    }).eq("id", body.field_id).execute()

    # Fan out adjustment detection to any programme using this field
    try:
        from app.services.adjustment_detector import (
            detect_soil_adjustment,
            find_programme_blocks_for_analysis,
        )
        for link in find_programme_blocks_for_analysis(sb, analysis_id):
            detect_soil_adjustment(
                sb,
                programme_id=link["programme_id"],
                block_id=link["block_id"],
                new_analysis_id=analysis_id,
                created_by=user.id,
            )
    except Exception:
        pass

    _audit(sb, user, "link_field", "soil_analyses", analysis_id, {"field_id": body.field_id})

    return {"ok": True}


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
    page: PageParams = Depends(PageParams.as_query),
    search: Optional[str] = Query(None, description="Search by client, farm, or crop"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    farm_id: Optional[str] = Query(None, description="Filter by farm ID"),
    field_id: Optional[str] = Query(None, description="Filter by field ID"),
    user: CurrentUser = Depends(get_current_user),
):
    """List soil analyses. Agents see their own; admins see all."""
    sb = get_supabase_admin()

    query = sb.table("soil_analyses").select("*", count="exact")

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

    query = apply_page(query, page, default_order="created_at")
    result = query.execute()
    return Page.from_result(result, page)


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


@router.get("/{analysis_id}/components")
def get_soil_analysis_components(
    analysis_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Return the component samples that produced a composite analysis.

    For single-sample records (or rows pre-dating migration 040), returns
    `components: []` and `composition_method: 'single'`. The field drawer
    uses this endpoint to render the "N samples composited" panel.
    """
    sb = get_supabase_admin()

    result = sb.table("soil_analyses").select(
        "id, agent_id, composition_method, replicate_count, "
        "component_samples, aggregation_stats"
    ).eq("id", analysis_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Soil analysis not found")

    record = result.data[0]
    if user.role != "admin" and record.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "analysis_id": analysis_id,
        "composition_method": record.get("composition_method") or "single",
        "replicate_count": record.get("replicate_count") or 1,
        "components": record.get("component_samples") or [],
        "stats": record.get("aggregation_stats") or {},
    }


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


@router.get("/{analysis_id}/document")
def get_analysis_document(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    """Get a signed URL for the original lab report document."""
    sb = get_supabase_admin()

    result = sb.table("soil_analyses").select("source_document_url, agent_id").eq("id", analysis_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Soil analysis not found")

    record = result.data[0]
    if user.role != "admin" and record.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    doc_url = record.get("source_document_url")
    if not doc_url:
        raise HTTPException(status_code=404, detail="No document attached to this analysis")

    signed = sb.storage.from_("lab-reports").create_signed_url(doc_url, 300)
    return {"url": signed.get("signedURL") or signed.get("signedUrl", "")}


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
