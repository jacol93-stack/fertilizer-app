"""
Programmes v2 router — API surface for the new programme_builder_orchestrator.

Separate from the legacy `programmes.py` which drives Season Tracker
Phase A-E foundations via the old programme_engine. Both coexist during
the UI migration window; the legacy routes stay intact, new UI calls
these v2 endpoints exclusively.

Endpoints:
    POST   /programmes/v2/build           — run orchestrator + persist
    GET    /programmes/v2/{id}            — fetch one artifact
    GET    /programmes/v2                 — list user's artifacts
    PATCH  /programmes/v2/{id}/state      — transition lifecycle state
    DELETE /programmes/v2/{id}            — archive (soft delete)

Request shape (BuildProgrammeRequest) is lighter than OrchestratorInput —
the catalog (crop_requirements, sufficiency, adjustment_factors,
rate_tables, ideal_ratios, crop_calc_flags, fertasa_nutrient_removal,
materials) is loaded server-side. Frontend only supplies farm/block
data + crop + dates + method availability.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.models import MethodAvailability, PreSeasonInput
from app.services.programme_builder_orchestrator import (
    BlockInput,
    OrchestratorInput,
    build_programme,
)
from app.services.target_computation import SoilCatalog, compute_season_targets
from app.supabase_client import get_supabase_admin


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/programmes/v2", tags=["programmes-v2"])


# ============================================================
# Request / response types
# ============================================================

class BlockRequest(BaseModel):
    """Per-block input from frontend."""
    block_id: str
    block_name: str
    block_area_ha: float = Field(..., gt=0)
    soil_parameters: dict[str, float] = Field(default_factory=dict)
    yield_target_per_ha: float = Field(..., gt=0)
    # Optional pre-computed targets; when omitted, the server uses target_computation
    season_targets: Optional[dict[str, float]] = None
    lab_name: Optional[str] = None
    lab_method: Optional[str] = None
    sample_date: Optional[date] = None
    sample_id: Optional[str] = None
    pre_season_inputs: list[PreSeasonInput] = Field(default_factory=list)
    leaf_deficiencies: Optional[dict[str, float]] = None


class BuildProgrammeRequest(BaseModel):
    """Lightweight API surface — server loads the full catalog."""
    client_name: str
    farm_name: str
    prepared_for: str
    crop: str
    planting_date: date
    build_date: Optional[date] = None  # defaults to today on server
    expected_harvest_date: Optional[date] = None
    season: Optional[str] = None
    location: Optional[str] = None
    ref_number: Optional[str] = None
    stage_count: int = Field(default=5, ge=3, le=6)
    blocks: list[BlockRequest]
    method_availability: MethodAvailability
    high_al_soil: Optional[bool] = None
    wet_summer_between_apply_and_plant: bool = False
    has_gypsum_in_plan: bool = False
    has_irrigation_water_test: bool = False
    has_recent_leaf_analysis: bool = False
    planned_n_fertilizers: Optional[list[str]] = None
    subtract_harvested_removal: bool = False
    client_id: Optional[UUID] = None


class BuildProgrammeResponse(BaseModel):
    id: UUID
    state: str
    artifact: dict  # full ProgrammeArtifact as dict — TS type matches Pydantic model


# ============================================================
# Endpoints
# ============================================================

@router.post("/build", response_model=BuildProgrammeResponse, status_code=status.HTTP_201_CREATED)
async def build_programme_endpoint(
    request: BuildProgrammeRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Run the programme builder orchestrator and persist the resulting artifact."""
    supabase = get_supabase_admin()

    # Load catalog rows (one batch of queries)
    catalog = _load_soil_catalog(supabase)
    materials = _load_materials(supabase)

    # Build per-block inputs, computing targets server-side if not provided
    block_inputs: list[BlockInput] = []
    for b in request.blocks:
        targets = b.season_targets
        if targets is None:
            # Compute via target_computation module
            result = compute_season_targets(
                crop=request.crop,
                yield_target=b.yield_target_per_ha,
                soil_values=b.soil_parameters,
                catalog=catalog,
                subtract_harvested_removal=request.subtract_harvested_removal,
                expected_yield_harvested=b.yield_target_per_ha,
            )
            targets = result.targets
        block_inputs.append(BlockInput(
            block_id=b.block_id,
            block_name=b.block_name,
            block_area_ha=b.block_area_ha,
            soil_parameters=b.soil_parameters,
            season_targets=targets,
            lab_name=b.lab_name,
            lab_method=b.lab_method,
            sample_date=b.sample_date,
            sample_id=b.sample_id,
            pre_season_inputs=b.pre_season_inputs,
            leaf_deficiencies=b.leaf_deficiencies,
        ))

    build_date = request.build_date or date.today()

    orchestrator_input = OrchestratorInput(
        client_name=request.client_name,
        farm_name=request.farm_name,
        prepared_for=request.prepared_for,
        crop=request.crop,
        planting_date=request.planting_date,
        build_date=build_date,
        expected_harvest_date=request.expected_harvest_date,
        season=request.season or "",
        location=request.location,
        ref_number=request.ref_number,
        stage_count=request.stage_count,
        method_availability=request.method_availability,
        blocks=block_inputs,
        high_al_soil=request.high_al_soil,
        wet_summer_between_apply_and_plant=request.wet_summer_between_apply_and_plant,
        has_gypsum_in_plan=request.has_gypsum_in_plan,
        has_irrigation_water_test=request.has_irrigation_water_test,
        has_recent_leaf_analysis=request.has_recent_leaf_analysis,
        planned_n_fertilizers=request.planned_n_fertilizers,
        available_materials=materials,
    )

    try:
        artifact = build_programme(orchestrator_input)
    except Exception as exc:
        logger.exception("build_programme failed for user %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Programme build failed: {exc}",
        )

    # Persist
    artifact_json = artifact.model_dump(mode="json")
    row = {
        "user_id": user.id,
        "client_id": str(request.client_id) if request.client_id else None,
        "farm_name": request.farm_name,
        "crop": request.crop,
        "planting_date": request.planting_date.isoformat(),
        "build_date": build_date.isoformat(),
        "expected_harvest_date": request.expected_harvest_date.isoformat() if request.expected_harvest_date else None,
        "season": request.season,
        "ref_number": request.ref_number,
        "prepared_for": request.prepared_for,
        "state": artifact.header.state.value,
        "replan_reason": artifact.header.replan_reason.value,
        "worst_tier": artifact.overall_confidence.tier.value if artifact.overall_confidence else None,
        "confidence_level": artifact.header.data_completeness.level,
        "blocks_count": len(artifact.soil_snapshots),
        "foliar_events_count": len(artifact.foliar_events),
        "risk_flags_count": len(artifact.risk_flags),
        "artifact": artifact_json,
        "artifact_version": artifact.header.artifact_version,
        "inputs": request.model_dump(mode="json"),
    }
    insert_result = supabase.table("programme_artifacts").insert(row).execute()
    if not insert_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist programme artifact",
        )
    saved = insert_result.data[0]

    return BuildProgrammeResponse(
        id=UUID(saved["id"]),
        state=saved["state"],
        artifact=artifact_json,
    )


@router.get("/{artifact_id}", response_model=BuildProgrammeResponse)
async def get_programme_artifact(
    artifact_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    query = (
        supabase.table("programme_artifacts")
        .select("*")
        .eq("id", str(artifact_id))
    )
    # Admin sees any; non-admin scoped to their own rows (admin client bypasses
    # RLS so we enforce the scope explicitly)
    if user.role != "admin":
        query = query.eq("user_id", user.id)
    result = query.limit(1).execute()
    if not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programme not found")
    row = result.data[0]
    return BuildProgrammeResponse(
        id=UUID(row["id"]),
        state=row["state"],
        artifact=row["artifact"],
    )


@router.get("", response_model=list[dict])
async def list_programmes(
    state: Optional[str] = Query(None),
    crop: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
):
    """List user's programmes with summary fields only (not full artifact JSON)."""
    supabase = get_supabase_admin()
    query = (
        supabase.table("programme_artifacts")
        .select(
            "id,created_at,updated_at,client_id,farm_name,crop,planting_date,"
            "build_date,expected_harvest_date,state,ref_number,worst_tier,"
            "confidence_level,blocks_count,foliar_events_count,risk_flags_count"
        )
        .order("created_at", desc=True)
        .limit(limit)
    )
    if user.role != "admin":
        query = query.eq("user_id", user.id)
    if state:
        query = query.eq("state", state)
    if crop:
        query = query.eq("crop", crop)
    result = query.execute()
    return result.data or []


class StateTransitionRequest(BaseModel):
    new_state: str = Field(
        ...,
        pattern=r"^(draft|approved|activated|in_progress|completed|archived)$",
    )


@router.patch("/{artifact_id}/state", response_model=BuildProgrammeResponse)
async def transition_state(
    artifact_id: UUID,
    request: StateTransitionRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Transition a programme's lifecycle state.

    Allowed transitions:
        draft → approved, archived
        approved → activated, draft, archived
        activated → in_progress, archived
        in_progress → completed, archived
        completed → archived
    """
    supabase = get_supabase_admin()
    select_query = (
        supabase.table("programme_artifacts")
        .select("state,artifact")
        .eq("id", str(artifact_id))
    )
    if user.role != "admin":
        select_query = select_query.eq("user_id", user.id)
    current = select_query.limit(1).execute()
    if not current.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programme not found")

    curr_state = current.data[0]["state"]
    new_state = request.new_state

    allowed = {
        "draft":        {"approved", "archived"},
        "approved":     {"activated", "draft", "archived"},
        "activated":    {"in_progress", "archived"},
        "in_progress":  {"completed", "archived"},
        "completed":    {"archived"},
        "archived":     set(),
    }
    if new_state not in allowed.get(curr_state, set()):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Invalid state transition: {curr_state} → {new_state}",
        )

    update = {"state": new_state}
    if new_state == "activated":
        update["activated_at"] = datetime.utcnow().isoformat()
    elif new_state == "completed":
        update["completed_at"] = datetime.utcnow().isoformat()

    update_query = (
        supabase.table("programme_artifacts")
        .update(update)
        .eq("id", str(artifact_id))
    )
    if user.role != "admin":
        update_query = update_query.eq("user_id", user.id)
    updated = update_query.execute()
    if not updated.data:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Update failed")
    row = updated.data[0]
    return BuildProgrammeResponse(
        id=UUID(row["id"]),
        state=row["state"],
        artifact=row["artifact"],
    )


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_programme(
    artifact_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Archive (soft delete) — sets state='archived'. Row is retained."""
    supabase = get_supabase_admin()
    query = (
        supabase.table("programme_artifacts")
        .update({"state": "archived"})
        .eq("id", str(artifact_id))
    )
    if user.role != "admin":
        query = query.eq("user_id", user.id)
    result = query.execute()
    if not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programme not found")
    return None


# ============================================================
# Catalog loading (server-side — the frontend doesn't know this schema)
# ============================================================

def _load_soil_catalog(supabase) -> SoilCatalog:
    """Load all reference tables the orchestrator + target_computation need.

    Loaded once per build call. For heavy traffic, consider caching with TTL;
    for now this is 8 small queries.
    """
    crop_rows = supabase.table("crop_requirements").select("*").execute().data or []
    sufficiency_rows = supabase.table("soil_sufficiency").select("*").execute().data or []
    adjustment_rows = supabase.table("adjustment_factors").select("*").execute().data or []
    param_map_rows = supabase.table("soil_parameter_map").select("*").execute().data or []
    override_rows = supabase.table("crop_sufficiency_overrides").select("*").execute().data or []
    rate_table_rows = supabase.table("fertilizer_rate_tables").select("*").execute().data or []
    ratio_rows = supabase.table("ideal_ratios").select("*").execute().data or []
    flags_rows = supabase.table("crop_calc_flags").select("*").execute().data or []
    removal_rows = supabase.table("fertasa_nutrient_removal").select("*").execute().data or []
    return SoilCatalog(
        crop_rows=crop_rows,
        sufficiency_rows=sufficiency_rows,
        adjustment_rows=adjustment_rows,
        param_map_rows=param_map_rows,
        crop_override_rows=override_rows,
        rate_table_rows=rate_table_rows,
        ratio_rows=ratio_rows,
        crop_calc_flags_rows=flags_rows,
        removal_rows=removal_rows,
    )


def _load_materials(supabase) -> list[dict]:
    result = supabase.table("materials").select("*").execute()
    return result.data or []
