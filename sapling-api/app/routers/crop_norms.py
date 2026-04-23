"""Crop norms, overrides, and reference-data router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import CurrentUser, get_current_user, require_admin
from app.supabase_client import get_supabase_admin, run_sb

router = APIRouter(tags=["crop_norms"])


# ── Pydantic models ──────────────────────────────────────────────────────

class CropRequirementUpdate(BaseModel):
    """Fields that can be patched on the admin crop_requirements row."""
    n: float | None = None
    p: float | None = None
    k: float | None = None
    ca: float | None = None
    mg: float | None = None
    s: float | None = None
    fe: float | None = None
    b: float | None = None
    mn: float | None = None
    zn: float | None = None
    mo: float | None = None
    cu: float | None = None
    c: float | None = None


class CropOverrideIn(BaseModel):
    """Agent-level override values. Only non-null values are stored."""
    n: float | None = None
    p: float | None = None
    k: float | None = None
    ca: float | None = None
    mg: float | None = None
    s: float | None = None
    fe: float | None = None
    b: float | None = None
    mn: float | None = None
    zn: float | None = None
    mo: float | None = None
    cu: float | None = None
    c: float | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.get("/")
def get_effective_crop_requirements(user: CurrentUser = Depends(get_current_user)):
    """Get effective crop requirements (admin defaults merged with agent overrides)."""
    sb = get_supabase_admin()
    try:
        result = run_sb(lambda: sb.rpc(
            "get_effective_crop_requirements",
            {"p_agent_id": user.id},
        ).execute())
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin")
def get_admin_crop_requirements(user: CurrentUser = Depends(require_admin)):
    """Admin only — raw crop_requirements table."""
    sb = get_supabase_admin()
    try:
        result = run_sb(lambda: sb.table("crop_requirements").select("*").execute())
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{crop}")
def update_crop_requirement(
    crop: str,
    body: CropRequirementUpdate,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only — update a crop's default requirements."""
    sb = get_supabase_admin()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        result = (
            sb.table("crop_requirements")
            .update(updates)
            .eq("crop", crop)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Crop '{crop}' not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overrides")
def get_agent_overrides(user: CurrentUser = Depends(get_current_user)):
    """Get current agent's crop overrides."""
    sb = get_supabase_admin()
    try:
        result = (
            sb.table("agent_crop_overrides")
            .select("*")
            .eq("agent_id", user.id)
            .execute()
        )
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/overrides/{crop}")
def set_agent_override(
    crop: str,
    body: CropOverrideIn,
    user: CurrentUser = Depends(get_current_user),
):
    """Set (upsert) an agent override for a specific crop. Only non-null values stored."""
    sb = get_supabase_admin()
    overrides = body.model_dump(exclude_none=True)
    if not overrides:
        raise HTTPException(status_code=400, detail="No override values provided")
    row = {"agent_id": user.id, "crop": crop, **overrides}
    try:
        result = (
            sb.table("agent_crop_overrides")
            .upsert(row, on_conflict="agent_id,crop")
            .execute()
        )
        return result.data[0] if result.data else row
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/overrides/{crop}")
def delete_agent_override(
    crop: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Delete an agent's override for a crop (resets to admin default)."""
    sb = get_supabase_admin()
    try:
        result = (
            sb.table("agent_crop_overrides")
            .delete()
            .eq("agent_id", user.id)
            .eq("crop", crop)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Override not found")
        return {"detail": "Override deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sufficiency")
def get_sufficiency(user: CurrentUser = Depends(get_current_user)):
    """Get soil_sufficiency reference table."""
    sb = get_supabase_admin()
    try:
        result = sb.table("soil_sufficiency").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adjustment-factors")
def get_adjustment_factors(user: CurrentUser = Depends(get_current_user)):
    """Get adjustment_factors reference table."""
    sb = get_supabase_admin()
    try:
        result = sb.table("adjustment_factors").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ratios")
def get_ratios(user: CurrentUser = Depends(get_current_user)):
    """Get ideal_ratios reference table."""
    sb = get_supabase_admin()
    try:
        result = sb.table("ideal_ratios").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parameter-map")
def get_parameter_map(user: CurrentUser = Depends(get_current_user)):
    """Get soil_parameter_map reference table."""
    sb = get_supabase_admin()
    try:
        result = sb.table("soil_parameter_map").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Growth Stages & Seasonal Feeding Data ────────────────────


@router.get("/{crop}/growth-stages")
def get_growth_stages(crop: str, user: CurrentUser = Depends(get_current_user)):
    """Get growth stages for a specific crop."""
    sb = get_supabase_admin()
    result = (
        sb.table("crop_growth_stages")
        .select("*")
        .eq("crop", crop)
        .order("stage_order")
        .execute()
    )
    return result.data


@router.get("/{crop}/age-factors")
def get_age_factors(crop: str, user: CurrentUser = Depends(get_current_user)):
    """Get perennial age factors for a specific crop."""
    sb = get_supabase_admin()
    result = (
        sb.table("perennial_age_factors")
        .select("*")
        .eq("crop", crop)
        .order("age_min")
        .execute()
    )
    return result.data


@router.get("/{crop}/methods")
def get_application_methods(crop: str, user: CurrentUser = Depends(get_current_user)):
    """Get application methods for a specific crop."""
    sb = get_supabase_admin()
    result = (
        sb.table("crop_application_methods")
        .select("*")
        .eq("crop", crop)
        .execute()
    )
    return result.data


@router.get("/{crop}/valid-methods")
def get_valid_methods(
    crop: str,
    stage: str | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    """Get valid application methods for a crop, optionally filtered by growth stage.

    Returns methods from crop_application_methods. If a stage is specified,
    also includes the default_method from that growth stage and filters
    methods suited to nutrients dominant in that stage.
    """
    sb = get_supabase_admin()

    # Get all methods for this crop
    methods_result = (
        sb.table("crop_application_methods")
        .select("*")
        .eq("crop", crop)
        .execute()
    )
    methods = methods_result.data or []

    # If no methods defined, return common defaults
    if not methods:
        methods = [
            {"crop": crop, "method": "broadcast", "is_default": True, "nutrients_suited": None, "timing_notes": None},
            {"crop": crop, "method": "banding", "is_default": False, "nutrients_suited": None, "timing_notes": None},
            {"crop": crop, "method": "fertigation", "is_default": False, "nutrients_suited": None, "timing_notes": None},
        ]

    stage_info = None
    if stage:
        stage_result = (
            sb.table("crop_growth_stages")
            .select("*")
            .eq("crop", crop)
            .eq("stage_name", stage)
            .limit(1)
            .execute()
        )
        if stage_result.data:
            stage_info = stage_result.data[0]

    return {
        "crop": crop,
        "stage": stage,
        "stage_default_method": stage_info.get("default_method") if stage_info else None,
        "methods": methods,
    }


@router.get("/{crop}/micronutrients")
def get_micronutrient_schedule(crop: str, user: CurrentUser = Depends(get_current_user)):
    """Get micronutrient spray schedule for a specific crop."""
    sb = get_supabase_admin()
    result = (
        sb.table("crop_micronutrient_schedule")
        .select("*")
        .eq("crop", crop)
        .execute()
    )
    return result.data
