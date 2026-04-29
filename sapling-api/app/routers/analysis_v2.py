"""Quick Analysis v2 router — interpretation-only soil + leaf reports.

Wraps `analysis_pipeline.analyse_blocks()` so /quick-analysis can produce
a ProgrammeArtifact-shaped report without any fertilizer recommendation.
The renderer (existing ArtifactView) renders the report — same visual
surface as full programmes minus the empty Blends / ShoppingList /
StageSchedules sections.

Endpoint:
    POST /analysis/v2/run — soil + leaf interpretation, returns artifact

Auth: same scoping as programmes_v2 (admin sees any; non-admin scoped
to their own clients via client_id resolution at the row level — but
the analysis itself is ephemeral so no row to scope).
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.models import ProgrammeArtifact
from app.services.analysis_pipeline import AnalysisBlockInput, analyse_blocks
from app.services.target_computation import SoilCatalog
from app.supabase_client import get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Request / response schemas
# ============================================================

class AnalysisBlockRequest(BaseModel):
    """Per-block interpretation input. Lighter than programmes_v2's
    BlockRequest — no method availability needed; no pre-season
    inputs (those are programme-build concerns)."""
    block_id: str
    block_name: str
    block_area_ha: float = Field(..., gt=0)
    soil_parameters: dict[str, float] = Field(default_factory=dict)
    leaf_values: Optional[dict[str, float]] = None
    # Optional — engine falls back to crop_requirements.default_yield
    # (full-bearing potential) when missing/0 and emits an Assumption.
    yield_target_per_ha: Optional[float] = Field(None, ge=0)
    # Perennial only — drives age + density scaling in target_computation
    tree_age: Optional[int] = Field(None, ge=0, le=200)
    pop_per_ha: Optional[float] = Field(None, gt=0)
    # Lab metadata for the soil snapshot
    lab_name: Optional[str] = None
    lab_method: Optional[str] = None
    sample_date: Optional[date] = None
    sample_id: Optional[str] = None


class AnalysisRequest(BaseModel):
    crop: str
    blocks: list[AnalysisBlockRequest] = Field(..., min_length=1)
    # Optional — when provided, current-stage detection runs against the
    # crop_growth_stages table. Without it the report is season-agnostic.
    planting_date: Optional[date] = None
    prepared_for: str = "Quick Analysis"
    client_name: Optional[str] = None
    farm_name: Optional[str] = None
    season: Optional[str] = None
    # Optional irrigation water analysis for water × soil compounding
    # rules in the soil-factor reasoner (sodic-water-on-trending-ESP, etc.)
    water_values: Optional[dict[str, float]] = None


class AnalysisResponse(BaseModel):
    artifact: dict


# ============================================================
# Endpoint
# ============================================================

@router.post("/run", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Run interpretation pipeline for soil + optional leaf data.

    Returns a ProgrammeArtifact (JSON) with empty blends/stage_schedules/
    shopping_list since this is interpretation-only. Same shape as the
    full programmes_v2 artifact so the existing ArtifactView component
    renders it.

    No persistence — analysis is ephemeral. Underlying soil/leaf records
    persist via the legacy /api/soil/ + /api/leaf/ endpoints which the
    UI already calls before running analysis.
    """
    supabase = get_supabase_admin()
    catalog = _load_soil_catalog(supabase)
    crop_growth_stage_rows = supabase.table("crop_growth_stages").select("*").execute().data or []

    blocks = [
        AnalysisBlockInput(
            block_id=b.block_id,
            block_name=b.block_name,
            block_area_ha=b.block_area_ha,
            soil_parameters=b.soil_parameters,
            leaf_values=b.leaf_values,
            yield_target_per_ha=b.yield_target_per_ha,
            tree_age=b.tree_age,
            pop_per_ha=b.pop_per_ha,
            lab_name=b.lab_name,
            lab_method=b.lab_method,
            sample_date=b.sample_date,
            sample_id=b.sample_id,
        )
        for b in request.blocks
    ]

    try:
        artifact = analyse_blocks(
            crop=request.crop,
            blocks=blocks,
            catalog=catalog,
            crop_growth_stage_rows=crop_growth_stage_rows,
            planting_date=request.planting_date,
            prepared_for=request.prepared_for,
            client_name=request.client_name or "",
            farm_name=request.farm_name or "",
            season=request.season,
            water_values=request.water_values,
        )
    except Exception as e:
        logger.exception("analysis_pipeline.analyse_blocks failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Analysis pipeline failed: {e}",
        )

    return AnalysisResponse(artifact=artifact.model_dump(mode="json"))


# ============================================================
# Catalog loader — mirrors programmes_v2._load_soil_catalog
# ============================================================

def _load_soil_catalog(supabase) -> SoilCatalog:
    """Load the same reference tables target_computation needs.

    Loaded once per call. For high traffic, consider a TTL cache;
    Quick Analysis is one-shot so re-loading per request is fine.
    """
    return SoilCatalog(
        crop_rows=supabase.table("crop_requirements").select("*").execute().data or [],
        sufficiency_rows=supabase.table("soil_sufficiency").select("*").execute().data or [],
        adjustment_rows=supabase.table("adjustment_factors").select("*").execute().data or [],
        param_map_rows=supabase.table("soil_parameter_map").select("*").execute().data or [],
        crop_override_rows=supabase.table("crop_sufficiency_overrides").select("*").execute().data or [],
        rate_table_rows=supabase.table("fertilizer_rate_tables").select("*").execute().data or [],
        ratio_rows=supabase.table("ideal_ratios").select("*").execute().data or [],
        crop_calc_flags_rows=supabase.table("crop_calc_flags").select("*").execute().data or [],
        removal_rows=supabase.table("fertasa_nutrient_removal").select("*").execute().data or [],
        age_factor_rows=supabase.table("perennial_age_factors").select("*").execute().data or [],
    )
