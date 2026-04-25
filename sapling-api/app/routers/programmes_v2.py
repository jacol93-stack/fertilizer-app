"""
Programmes v2 router — API surface for the new programme_builder_orchestrator.

Separate from the legacy `programmes.py` which drives Season Tracker
Phase A-E foundations via the old programme_engine. Both coexist during
the UI migration window; the legacy routes stay intact, new UI calls
these v2 endpoints exclusively.

Endpoints:
    POST   /programmes/v2/build           — run orchestrator + persist
    GET    /programmes/v2/{id}            — fetch one artifact
    GET    /programmes/v2/{id}/render-pdf — Sapling-branded styled PDF
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

import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.models import (
    MethodAvailability,
    OutstandingItem,
    PreSeasonInput,
    ProgrammeArtifact,
    RiskFlag,
    SoilSnapshot,
)
from app.services.pdf_renderer import render_programme_pdf
from app.services.block_clustering import (
    ClusterAggregate,
    cluster_and_aggregate,
)
from app.services.programme_builder_orchestrator import (
    BlockInput,
    OrchestratorInput,
    build_programme,
)
from app.services.target_computation import SoilCatalog, compute_season_targets
from app.supabase_client import get_supabase_admin, run_sb


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
    # Perennial only — trees/vines per hectare for density scaling
    pop_per_ha: Optional[float] = Field(None, gt=0)


class SkippedBlockRequest(BaseModel):
    """Block the caller couldn't plan (e.g. no soil analysis linked).

    Appended to artifact.outstanding_items so the agronomist sees what
    remains to complete, instead of the UI silently dropping them.
    """
    block_name: str
    reason: str


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
    harvest_mode: Optional[str] = None  # 'grain' | 'hay' | 'silage' | 'fruit' | 'nuts' | ...
    water_values: Optional[dict] = None  # {'EC': dS/m, 'Na': mg/L, 'Ca': mg/L, 'Mg': mg/L, 'HCO3': mg/L, 'pH': ...}
    # Farmer's operational application windows (month numbers 1-12).
    # Engine maps agronomic stages onto these slots with timing walls enforced.
    application_months: Optional[list[int]] = None
    client_id: Optional[UUID] = None
    skipped_blocks: list[SkippedBlockRequest] = Field(default_factory=list)


class ReviewInfo(BaseModel):
    """Reviewer attribution surfaced alongside an artifact. Populated
    once a draft is approved."""
    reviewer_id: Optional[UUID] = None
    reviewer_email: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class BuildProgrammeResponse(BaseModel):
    id: UUID
    state: str
    artifact: dict  # full ProgrammeArtifact as dict — TS type matches Pydantic model
    review: Optional[ReviewInfo] = None


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
    materials = _load_materials_for_user(supabase, user)

    # Build per-block inputs, computing targets server-side if not provided
    block_inputs: list[BlockInput] = []
    # Collected target-computation metadata (calc_path mix + unadjusted
    # nutrients per block) for post-build narrative rendering.
    calc_path_tally: dict[str, int] = {}
    unadjusted_by_block: list[tuple[str, list[str]]] = []
    for b in request.blocks:
        targets = b.season_targets
        if targets is None:
            # Compute via target_computation module. pop_per_ha drives
            # the perennial-density scaling — annual crops ignore it
            # server-side.
            result = compute_season_targets(
                crop=request.crop,
                yield_target=b.yield_target_per_ha,
                soil_values=b.soil_parameters,
                catalog=catalog,
                subtract_harvested_removal=request.subtract_harvested_removal,
                expected_yield_harvested=b.yield_target_per_ha,
                block_pop_per_ha=b.pop_per_ha,
                harvest_mode=request.harvest_mode,
            )
            targets = result.targets
            for path in result.calc_path_by_nutrient.values():
                calc_path_tally[path] = calc_path_tally.get(path, 0) + 1
            if result.unadjusted_nutrients:
                unadjusted_by_block.append((b.block_name, list(result.unadjusted_nutrients)))
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
            pop_per_ha=b.pop_per_ha,
        ))

    # Phase 3 — block aggregation. Blocks with similar NPK ratios share
    # a cluster; per-nutrient targets + soil parameters are combined
    # area-weighted (equal-weight fallback if any block lacks area_ha).
    # Blocks carrying pre_season_inputs are kept as singletons — those
    # inputs are per-block history, not safely aggregatable here.
    effective_blocks, cluster_aggs, cluster_sources = _cluster_block_inputs(block_inputs)

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
        blocks=effective_blocks,
        high_al_soil=request.high_al_soil,
        wet_summer_between_apply_and_plant=request.wet_summer_between_apply_and_plant,
        has_gypsum_in_plan=request.has_gypsum_in_plan,
        has_irrigation_water_test=request.has_irrigation_water_test,
        has_recent_leaf_analysis=request.has_recent_leaf_analysis,
        planned_n_fertilizers=request.planned_n_fertilizers,
        available_materials=materials,
        water_values=request.water_values,
        application_months=request.application_months,
    )

    try:
        artifact = build_programme(orchestrator_input)
    except Exception as exc:
        logger.exception("build_programme failed for user %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Programme build failed: {exc}",
        )

    # Caller-supplied skipped blocks (e.g. no soil analysis linked) are
    # surfaced as outstanding items so the agronomist sees what's still
    # pending. Keeps the artifact honest about which blocks it covers.
    _append_skipped_block_items(artifact, request.skipped_blocks)

    # Phase 3 — emit a RiskFlag per cluster whose nutrient CV breached
    # the Wilding thresholds. Also append cluster-mapping notes to the
    # decision trace.
    _append_cluster_narrative(artifact, cluster_aggs)

    # Per-block soil snapshots under multi-block clusters, so the
    # agronomist still sees each block's raw soil data alongside the
    # cluster's aggregated view.
    _append_per_block_soil_snapshots(artifact, cluster_sources)

    # Provenance + blind-spot narrative: calc-path mix in the decision
    # trace (so the Sources Audit section shows how many nutrients
    # came from rate-table vs cation-ratio vs heuristic vs unadjusted),
    # plus an OutstandingItem per block that had unadjusted fallbacks
    # (missing soil test for that nutrient).
    _append_calc_path_narrative(
        artifact, calc_path_tally, unadjusted_by_block,
    )

    # Sanity-cap guardrail: catch yield-target typos (a mistyped 100 t/ha
    # maize produces ~500 kg N/ha, well beyond anything physically
    # reasonable). Not crop-specific yet — universal thresholds derived
    # from the highest plausible SA programmes (sugarcane ~240, maize
    # ~300, heavy-feeder veg ~250). 500 is a red flag in every crop.
    _append_n_cap_flags(artifact)

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
        # Source blocks the agronomist ticked. Cluster-aggregate
        # snapshots (block_id="cluster_A", etc.) are engine-internal —
        # excluding them keeps the listing count consistent with what
        # the wizard input.
        "blocks_count": sum(
            1 for s in artifact.soil_snapshots
            if not s.block_id.startswith("cluster_")
        ),
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
    result = run_sb(lambda: query.limit(1).execute())
    if not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programme not found")
    row = result.data[0]
    return BuildProgrammeResponse(
        id=UUID(row["id"]),
        state=row["state"],
        artifact=row["artifact"],
        review=_build_review_info(supabase, row),
    )


@router.get("/{artifact_id}/render-pdf")
async def render_programme_artifact_pdf(
    artifact_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Render the artifact as a Sapling-branded styled PDF.

    Same access scope as the get-artifact endpoint: admin sees any,
    non-admin sees only their own. Strips all source citations + raw
    material names per the client-disclosure boundary.
    """
    supabase = get_supabase_admin()
    query = (
        supabase.table("programme_artifacts")
        .select("artifact, state")
        .eq("id", str(artifact_id))
    )
    if user.role != "admin":
        query = query.eq("user_id", user.id)
    result = run_sb(lambda: query.limit(1).execute())
    if not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programme not found")

    artifact_dict = result.data[0]["artifact"]
    artifact = ProgrammeArtifact.model_validate(artifact_dict)
    pdf_bytes = render_programme_pdf(artifact, mode="client")

    filename = _suggest_pdf_filename(artifact)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


def _suggest_pdf_filename(artifact: ProgrammeArtifact) -> str:
    """Build a sensible ASCII-safe filename from the artifact header.

    HTTP Content-Disposition headers are latin-1 encoded by default, so
    em-dashes / non-ASCII characters break the response. We use plain
    hyphens between parts and strip any non-ASCII characters.
    """
    h = artifact.header
    parts: list[str] = []
    if h.client_name:
        parts.append(h.client_name)
    if h.crop:
        parts.append(h.crop)
    if h.season:
        parts.append(h.season)
    if not parts and h.ref_number:
        parts.append(h.ref_number)
    if not parts:
        parts.append("Sapling Programme")
    base = " - ".join(parts)
    # Date-style separators: convert "2026/2027" → "2026-2027" rather
    # than collapse to "20262027". Then drop other filesystem-unsafe chars.
    safe = base.replace("/", "-")
    safe = re.sub(r'[\\:*?"<>|]+', "", safe)
    safe = safe.encode("ascii", errors="ignore").decode("ascii")
    safe = re.sub(r"\s+", " ", safe).strip()
    if not safe:
        safe = "Sapling Programme"
    return f"{safe}.pdf"


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
    # Optional reviewer notes — recorded on draft→approved transition.
    # For other transitions, ignored server-side.
    reviewer_notes: Optional[str] = Field(None, max_length=4000)


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

    On draft → approved: records user.id as reviewer_id, sets
    reviewed_at=now(), and stores optional reviewer_notes. The
    agronomist review workflow uses this to attach a signature +
    comments before the programme reaches the farmer.
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
    # Agronomist review: capture reviewer + notes + timestamp on the
    # draft→approved transition. Other transitions ignore notes.
    if curr_state == "draft" and new_state == "approved":
        update["reviewer_id"] = user.id
        update["reviewed_at"] = datetime.utcnow().isoformat()
        if request.reviewer_notes is not None:
            update["reviewer_notes"] = request.reviewer_notes

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
        review=_build_review_info(supabase, row),
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
# Helpers
# ============================================================

def _cluster_block_inputs(
    block_inputs: list[BlockInput],
) -> tuple[list[BlockInput], list[ClusterAggregate], dict[str, list[BlockInput]]]:
    """Group similar blocks into clusters + build the effective block
    list the orchestrator sees.

    Returns (effective_blocks, cluster_aggregates, cluster_sources):
      * effective_blocks: what the orchestrator processes. For singleton
        clusters this is the original BlockInput untouched. For multi-
        block clusters it's a synthetic BlockInput built from the
        cluster aggregate.
      * cluster_aggregates: kept so the caller can emit per-cluster
        RiskFlags + decision-trace notes after the build.
      * cluster_sources: map cluster_id → the original BlockInputs that
        went into it. Used post-build to emit per-original-block
        SoilSnapshots under multi-block clusters so the agronomist
        keeps per-block drill-down.

    Blocks with non-empty pre_season_inputs are excluded from clustering
    (kept as singletons) — those inputs are per-block history and
    combining them across blocks would risk double-counting in the
    pre-season residual subtraction.
    """
    clusterable = [b for b in block_inputs if not b.pre_season_inputs]
    non_clusterable = [b for b in block_inputs if b.pre_season_inputs]

    cluster_aggs = cluster_and_aggregate(clusterable)

    effective: list[BlockInput] = []
    by_id = {b.block_id: b for b in clusterable}
    cluster_sources: dict[str, list[BlockInput]] = {}

    for agg in cluster_aggs:
        cluster_sources[agg.cluster_id] = [by_id[bid] for bid in agg.block_ids]

        if len(agg.block_ids) == 1:
            # Singleton — pass the original through so lab metadata +
            # any other per-block detail survive untouched.
            original = by_id[agg.block_ids[0]]
            effective.append(original)
            continue

        # Multi-block cluster — build a synthetic BlockInput. No lab
        # metadata because it'd be misleading (mix of source analyses);
        # the cluster_aggs list is the provenance record.
        effective.append(BlockInput(
            block_id=f"cluster_{agg.cluster_id}",
            block_name=f"Cluster {agg.cluster_id}: {', '.join(agg.block_names)}",
            block_area_ha=agg.total_area_ha,
            soil_parameters=agg.aggregated_soil_parameters,
            season_targets=agg.aggregated_targets,
            lab_name=None,
            lab_method=None,
            sample_date=None,
            sample_id=None,
            pre_season_inputs=[],
            leaf_deficiencies=None,
        ))

    # Non-clusterable blocks (those with pre_season_inputs) always run
    # as singletons through the orchestrator.
    effective.extend(non_clusterable)
    return effective, cluster_aggs, cluster_sources


def _append_per_block_soil_snapshots(
    artifact,
    cluster_sources: dict[str, list[BlockInput]],
) -> None:
    """Add per-original-block SoilSnapshots under each multi-block
    cluster so the agronomist keeps per-block drill-down even when
    aggregation happens. The cluster-level snapshot already carries
    headline_signals; these per-block additions are raw data only.

    Singleton clusters produce nothing — the orchestrator already emits
    one snapshot per input, and for singletons the input is the real
    block.
    """
    for cluster_id, sources in cluster_sources.items():
        if len(sources) <= 1:
            continue
        for b in sources:
            artifact.soil_snapshots.append(SoilSnapshot(
                block_id=b.block_id,
                block_name=f"{b.block_name} (in Cluster {cluster_id})",
                block_area_ha=b.block_area_ha,
                lab_name=b.lab_name,
                lab_method=b.lab_method,
                sample_date=b.sample_date,
                sample_id=b.sample_id,
                parameters=b.soil_parameters,
                headline_signals=[],
            ))


def _append_cluster_narrative(artifact, cluster_aggs: list[ClusterAggregate]) -> None:
    """Emit heterogeneity RiskFlags + decision-trace notes for each
    multi-block cluster. Singleton clusters produce nothing."""
    for agg in cluster_aggs:
        if len(agg.block_ids) > 1:
            artifact.decision_trace.append(
                f"Clustered blocks [{', '.join(agg.block_names)}] into "
                f"'{agg.cluster_id}' ({agg.total_area_ha} ha, "
                f"{agg.weight_strategy} weighting)."
            )
        if agg.heterogeneity.any_warn or agg.heterogeneity.any_split:
            warnings_text = ", ".join(
                f"{w.nutrient} CV {w.cv_pct}% "
                f"(≥{w.threshold_pct}% {w.level})"
                for w in agg.heterogeneity.warnings
            )
            severity = "critical" if agg.heterogeneity.any_split else "warn"
            action = (
                "Consider splitting this cluster into per-block plans."
                if agg.heterogeneity.any_split
                else "Review whether one blend fits both blocks."
            )
            artifact.risk_flags.append(RiskFlag(
                message=(
                    f"Cluster {agg.cluster_id} "
                    f"({len(agg.block_ids)} blocks: "
                    f"{', '.join(agg.block_names)}) spans high nutrient "
                    f"variation: {warnings_text}. {action} "
                    f"[{agg.heterogeneity.citation}]"
                ),
                severity=severity,
            ))


N_CAP_CRITICAL_KG_HA = 500.0  # impossible in any SA crop — almost certainly yield typo
N_CAP_WARN_KG_HA = 350.0      # unusually high — worth double-checking


def _build_review_info(supabase, row: dict) -> Optional["ReviewInfo"]:
    """Pull reviewer attribution off a programme_artifacts row and
    hydrate with the reviewer's email + name from profiles.

    Returns None when the artifact hasn't been reviewed yet. One
    extra query per GET — acceptable; could denormalise into the
    artifact row if it becomes hot.
    """
    reviewer_id = row.get("reviewer_id")
    if not reviewer_id:
        return None
    email = None
    name = None
    try:
        prof = run_sb(lambda: supabase.table("profiles").select(
            "email,name"
        ).eq("id", reviewer_id).limit(1).execute())
        if prof.data:
            email = prof.data[0].get("email")
            name = prof.data[0].get("name")
    except Exception as e:
        logger.warning("reviewer profile lookup failed for %s: %s", reviewer_id, e)
    return ReviewInfo(
        reviewer_id=UUID(reviewer_id),
        reviewer_email=email,
        reviewer_name=name,
        reviewer_notes=row.get("reviewer_notes"),
        reviewed_at=row.get("reviewed_at"),
    )


def _append_n_cap_flags(artifact) -> None:
    """Scan soil_snapshots + block_totals for N targets beyond plausible
    SA ceilings and emit a RiskFlag.

    Heavy feeders (maize at 15 t/ha, sugarcane, potato) top out around
    250-300 kg N/ha total. Anything above 500 kg N/ha is almost
    certainly a yield-target typo (e.g. user typed "100 t/ha" for
    a maize block they meant to be "10 t/ha"). Between 350 and 500
    is unusual but possible for specific high-demand systems —
    flagged as warn so the agronomist double-checks.

    Future refinement: per-crop FERTASA-cited ceiling on
    crop_requirements.max_n_kg_ha, checked here with crop-specific
    messaging. Today's thresholds are universal and conservative.
    """
    for block_id, totals in (artifact.block_totals or {}).items():
        n_total = float(totals.get("N", 0) or 0)
        if n_total >= N_CAP_CRITICAL_KG_HA:
            artifact.risk_flags.append(RiskFlag(
                message=(
                    f"Block '{block_id}': total N target {n_total:.0f} kg/ha "
                    f"exceeds the {int(N_CAP_CRITICAL_KG_HA)} kg/ha sanity "
                    f"cap for any SA crop. Almost always a yield-target typo "
                    f"— verify the yield value (e.g. 10 t/ha not 100 t/ha) "
                    f"before activating the programme."
                ),
                severity="critical",
            ))
        elif n_total >= N_CAP_WARN_KG_HA:
            artifact.risk_flags.append(RiskFlag(
                message=(
                    f"Block '{block_id}': total N target {n_total:.0f} kg/ha "
                    f"is above {int(N_CAP_WARN_KG_HA)} kg/ha — unusual for "
                    f"most SA crops. Double-check the yield target if this "
                    f"isn't an intentional high-demand system."
                ),
                severity="warn",
            ))


def _append_calc_path_narrative(
    artifact,
    calc_path_tally: dict[str, int],
    unadjusted_by_block: list[tuple[str, list[str]]],
) -> None:
    """Surface target-computation provenance + blind spots on the artifact.

    Two outputs:
      * decision_trace line tallying how many nutrient-target cells
        came from each calc path — rate_table / cation_ratio /
        heuristic / unadjusted. Gives the agronomist an honest
        read on how data-driven the programme is.
      * OutstandingItem per block that hit 'unadjusted' on any
        nutrient (soil test missing for the mapped parameter). Target
        is raw removal × yield with factor=1.0 for those, which may
        over- or under-fertilize the actual soil. Uploading the
        missing parameter refines the target.
    """
    if calc_path_tally:
        path_order = ["rate_table", "cation_ratio", "heuristic", "unadjusted"]
        parts = []
        for p in path_order:
            n = calc_path_tally.get(p, 0)
            if n:
                parts.append(f"{n} {p}")
        # Append any non-standard paths we haven't listed above
        for p, n in calc_path_tally.items():
            if p not in path_order:
                parts.append(f"{n} {p}")
        if parts:
            artifact.decision_trace.append(
                "Target-computation path mix: " + ", ".join(parts)
            )

    for block_name, nutrients in unadjusted_by_block:
        nutrient_list = ", ".join(nutrients)
        artifact.outstanding_items.append(OutstandingItem(
            item=(
                f"Block '{block_name}': {nutrient_list} computed from "
                f"unadjusted removal (no soil test for that parameter)"
            ),
            why_it_matters=(
                "When the soil test is missing for a nutrient, the engine "
                "falls back to base removal × yield with no soil-state "
                "adjustment factor. The target is a reasonable starting "
                "point but is not informed by the actual soil reserve, so "
                "it may over- or under-fertilize vs what the soil really "
                "needs."
            ),
            impact_if_skipped=(
                "Upload a complete soil analysis including this parameter "
                "to get a soil-state-adjusted target. Safe to proceed with "
                "the current target, but expect variance from a refined "
                "target after the next soil test."
            ),
        ))


def _append_skipped_block_items(artifact, skipped_blocks: list[SkippedBlockRequest]) -> None:
    """Append one OutstandingItem per skipped block to the artifact.

    Kept separate from the endpoint so it's unit-testable without
    spinning up FastAPI + Supabase.
    """
    for sb in skipped_blocks:
        artifact.outstanding_items.append(OutstandingItem(
            item=f"Block '{sb.block_name}' not planned ({sb.reason})",
            why_it_matters=(
                "This block is on the farm but wasn't included in the "
                "programme build — no per-block plan, no shopping list "
                "contribution, no foliar schedule."
            ),
            impact_if_skipped=(
                "Link a soil analysis and rebuild, or record applications "
                "manually; otherwise the block has no programme guidance."
            ),
        ))


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


def _load_materials_for_user(supabase, user: CurrentUser) -> list[dict]:
    """Return the materials list the orchestrator should plan against.

    Admins get everything — the full catalog is theirs to curate.
    Agents get the admin-approved subset from `default_materials.materials`
    + `default_materials.liquid_materials`, with "Manure Compost" always
    included (matches the legacy auto-blend flow's behavior).

    If no default_materials row exists yet (fresh install), agents fall
    back to the full catalog with a warning logged — safer than
    blocking the build.
    """
    all_mats = supabase.table("materials").select("*").execute().data or []
    if getattr(user, "role", None) == "admin":
        return all_mats

    defaults_res = supabase.table("default_materials").select("*").execute()
    if not defaults_res.data:
        logger.warning(
            "No default_materials row found — agent user %s falling back "
            "to full materials catalog. Admin should configure defaults.",
            user.id,
        )
        return all_mats
    row = defaults_res.data[0]
    approved = set(row.get("materials") or [])
    approved.update(row.get("liquid_materials") or [])
    approved.add("Manure Compost")  # compost always available
    filtered = [m for m in all_mats if m.get("material") in approved]
    if not filtered:
        # Defaults row exists but empty — don't silently cripple the
        # build. Log and return the full catalog.
        logger.warning(
            "default_materials for agent %s resolves to zero matches — "
            "falling back to full catalog.",
            user.id,
        )
        return all_mats
    return filtered
