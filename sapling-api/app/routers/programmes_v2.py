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
from datetime import date, datetime, timedelta
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
    # Optional — when missing/0, target_computation falls back to
    # crop_requirements.default_yield (full-bearing potential) and
    # emits an Assumption. Combined with tree_age + perennial_age_factors,
    # this gives correct rates for young / non-bearing blocks without
    # forcing the agronomist to enter "mature potential" manually.
    yield_target_per_ha: Optional[float] = Field(None, ge=0)
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
    # Perennial only — years since planting. Drives age-factor scaling
    # against perennial_age_factors so young non-bearing blocks aren't
    # over-fertilised. None / annuals → factor 1.0.
    tree_age: Optional[int] = Field(None, ge=0, le=200)


class SkippedBlockRequest(BaseModel):
    """Block the caller couldn't plan (e.g. no soil analysis linked).

    Appended to artifact.outstanding_items so the agronomist sees what
    remains to complete, instead of the UI silently dropping them.

    If `attach_to_cluster` is set, the block is added to that cluster's
    plan using the cluster's averaged targets — a "rough plan" for the
    block while soil sampling is pending. Requires `block_id` +
    `block_area_ha` to be set so the engine can scale per-block rates.
    The OutstandingItem still flags the missing soil analysis.
    """
    block_name: str
    reason: str
    block_id: Optional[str] = None
    block_area_ha: Optional[float] = Field(None, gt=0)
    attach_to_cluster: Optional[str] = None


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
    # Per-cluster method override set by the agronomist on the cluster
    # board. cluster_id → MethodAvailability. When a cluster_id appears
    # here, the engine uses its availability for that group's blends
    # instead of the global `method_availability`. Lets the user say
    # "Group A drip-only this season, Group B broadcast only" without
    # changing the field's stored capability.
    method_availability_per_cluster: dict[str, MethodAvailability] = Field(default_factory=dict)
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
    # NPK-ratio L1 distance threshold for grouping blocks into shared
    # clusters. Same recipe shared across cluster, per-block rates differ.
    # Lower = more singleton blocks, more recipes; higher = fewer recipes
    # for the farmer to mix and stock. Default 0.25.
    cluster_margin: float = Field(default=0.25, ge=0.05, le=0.5)
    # Manual cluster assignments (block_id → cluster_id) override the
    # auto-clustering for specific blocks. Lets the agronomist drag
    # blocks between recipes when the auto-NPK fit isn't quite right.
    # Dataless blocks (no soil_analysis_id) MUST be listed here to be
    # included; they inherit the cluster's averaged recipe + targets.
    cluster_assignments: dict[str, str] = Field(default_factory=dict)


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
    pre_computed_assumptions: list = []
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
                tree_age=b.tree_age,
                block_name=b.block_name,
            )
            targets = result.targets
            for path in result.calc_path_by_nutrient.values():
                calc_path_tally[path] = calc_path_tally.get(path, 0) + 1
            if result.unadjusted_nutrients:
                unadjusted_by_block.append((b.block_name, list(result.unadjusted_nutrients)))
            # Forward any per-block assumptions (yield-target default,
            # density scaling, N-min credit, etc.) to the orchestrator
            # so they reach the artifact's Assumptions section.
            if result.assumptions:
                pre_computed_assumptions.extend(result.assumptions)
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
            tree_age=b.tree_age,
        ))

    # Phase 3 — block aggregation. Blocks with similar NPK ratios share
    # a cluster; per-nutrient targets + soil parameters are combined
    # area-weighted (equal-weight fallback if any block lacks area_ha).
    # Blocks carrying pre_season_inputs are kept as singletons — those
    # inputs are per-block history, not safely aggregatable here.
    effective_blocks, cluster_aggs, cluster_sources = _cluster_block_inputs(
        block_inputs,
        cluster_margin=request.cluster_margin,
        cluster_assignments=request.cluster_assignments,
    )

    # Dataless-block attachment: skipped blocks with attach_to_cluster set
    # become extra effective blocks using the cluster's averaged targets.
    # Their OutstandingItem still flags the missing soil analysis.
    _attach_dataless_blocks_to_clusters(
        effective_blocks, cluster_aggs, request.skipped_blocks,
    )

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
        method_availability_per_cluster=request.method_availability_per_cluster,
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
        sufficiency_rows=catalog.sufficiency_rows,
        crop_override_rows=catalog.crop_override_rows,
        param_map_rows=catalog.param_map_rows,
        cluster_sources=cluster_sources,
        pre_computed_assumptions=pre_computed_assumptions,
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

    # Per-block soil snapshots are now emitted by the orchestrator
    # itself (per-source pass) with full structured data — no longer
    # need to append them here.

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


# ============================================================
# Preview-schedule endpoint
# ============================================================
# Stateless wizard helper: takes the in-memory blocks the user has
# assembled in step 1 and returns growth_stages + accepted_methods +
# nutrient_targets + soil corrections per block, without writing
# anything to the DB. Replaces the legacy /api/programmes/{id}/preview-schedule
# which required a v1 programme row.

class PreviewBlockRequest(BaseModel):
    """Per-block input for the wizard's Schedule step. Lighter than
    BlockRequest — no method availability needed yet."""
    block_id: str
    block_name: str
    crop: str
    cultivar: Optional[str] = None
    soil_analysis_id: Optional[str] = None
    field_id: Optional[str] = None
    area_ha: Optional[float] = Field(None, gt=0)  # for cluster aggregation
    yield_target: Optional[float] = None
    yield_unit: Optional[str] = None
    tree_age: Optional[int] = Field(None, ge=0, le=200)
    pop_per_ha: Optional[int] = Field(None, gt=0)


class PreviewScheduleRequest(BaseModel):
    blocks: list[PreviewBlockRequest]
    # Mirror of BuildProgrammeRequest.cluster_margin so the preview shows
    # the same grouping the build will produce.
    cluster_margin: float = Field(default=0.25, ge=0.05, le=0.5)
    # Manual cluster assignments mirror of BuildProgrammeRequest.
    # Empty dict → pure auto-cluster (default UX).
    cluster_assignments: dict[str, str] = Field(default_factory=dict)
    # User-driven group count. When set, overrides `cluster_margin` and
    # uses agglomerative clustering to produce exactly this many groups.
    # The wizard's "Number of groups" picker sends this; passing None
    # falls back to the legacy threshold-driven path.
    target_clusters: Optional[int] = Field(default=None, ge=1, le=50)
    # Hooks for future build-input parity. Defaults match BuildProgrammeRequest.
    subtract_harvested_removal: bool = False
    harvest_mode: Optional[str] = None


class _ClusterStub:
    """Minimal block-shaped object the clustering helpers can consume.
    Avoids importing BlockInput here (would be a circular dep)."""
    __slots__ = ("block_id", "block_name", "block_area_ha", "season_targets", "soil_parameters")

    def __init__(self, block_id, block_name, block_area_ha, season_targets, soil_parameters):
        self.block_id = block_id
        self.block_name = block_name
        self.block_area_ha = block_area_ha
        self.season_targets = season_targets
        self.soil_parameters = soil_parameters


def _material_to_correction_type(material: str) -> str:
    """Map a pre-season material name onto the chip-type taxonomy the
    wizard renders (lime / gypsum / sulphur / organic_matter)."""
    name = (material or "").lower()
    if "lime" in name or "dolomit" in name:
        return "lime"
    if "gypsum" in name:
        return "gypsum"
    if "sulphur" in name or "sulfur" in name:
        return "sulphur"
    return "other"


@router.post("/preview-schedule")
async def preview_schedule(
    request: PreviewScheduleRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Resolve growth stages, accepted methods, nutrient targets, soil
    corrections, and the proposed block clustering for each block. Drives
    the wizard's Schedule Review step. No DB writes.

    Cluster grouping mirrors what the v2 build will produce so the
    agronomist can see "blocks A+B+C share recipe X; block D is its own
    recipe" before committing.
    """
    from app.services.soil_corrections import (
        calculate_corrective_targets,
        check_organic_carbon,
        get_nutrient_explanations,
    )
    from app.services.soil_factor_reasoner import reason_soil_factors
    from app.services.pre_season_module import recommend_pre_season_actions

    sb = get_supabase_admin()

    if not request.blocks:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No blocks provided")

    # Catalog drives target_computation. Same load as the build endpoint
    # so preview targets match what the build will produce.
    catalog = _load_soil_catalog(sb)

    # Pre-fetch soil analyses (one batched query is cheaper than N round-trips)
    analysis_ids = [b.soil_analysis_id for b in request.blocks if b.soil_analysis_id]
    analyses_by_id: dict[str, dict] = {}
    if analysis_ids:
        ar = (
            sb.table("soil_analyses")
            .select("id, soil_values, classifications, ratio_results, nutrient_targets, norms_snapshot")
            .in_("id", analysis_ids)
            .execute()
        )
        for row in ar.data or []:
            analyses_by_id[row["id"]] = row

    # Pre-fetch field accepted_methods + irrigation_type + fertigation_capable
    field_ids = [b.field_id for b in request.blocks if b.field_id]
    fields_by_id: dict[str, dict] = {}
    if field_ids:
        fr = (
            sb.table("fields")
            .select("id, accepted_methods, irrigation_type, fertigation_capable")
            .in_("id", field_ids)
            .execute()
        )
        for row in fr.data or []:
            fields_by_id[row["id"]] = row

    pm_rows = catalog.param_map_rows

    block_info: list[dict] = []
    unplanable_blocks: list[dict] = []
    all_corrections: list[dict] = []
    cluster_stubs: list[_ClusterStub] = []  # one per planable block

    for b in request.blocks:
        analysis = analyses_by_id.get(b.soil_analysis_id) if b.soil_analysis_id else None
        nutrient_targets = (analysis or {}).get("nutrient_targets") or []

        # Compute fresh v2 season targets so clustering uses the same
        # numbers the build will produce. Always attempt this — when the
        # linked analysis was created via bulk-import (no crop / yield at
        # the time of upload), nutrient_targets is empty but the block
        # itself carries crop + yield_target from the field record, so
        # we can still compute targets here from the analysis's
        # soil_values.
        v2_targets: dict[str, float] = {}
        soil_values_for_targets = (analysis or {}).get("soil_values") or {}
        if b.yield_target and soil_values_for_targets:
            try:
                tc_result = compute_season_targets(
                    crop=b.crop,
                    yield_target=float(b.yield_target),
                    soil_values=soil_values_for_targets,
                    catalog=catalog,
                    subtract_harvested_removal=request.subtract_harvested_removal,
                    expected_yield_harvested=float(b.yield_target),
                    block_pop_per_ha=b.pop_per_ha,
                    harvest_mode=request.harvest_mode,
                    tree_age=b.tree_age,
                )
                v2_targets = tc_result.targets
            except Exception:
                # Don't block the preview on a target-computation hiccup —
                # the block still gets growth-stage + correction info.
                v2_targets = {}

        # Block is unplanable only if BOTH pre-stored targets and
        # freshly-computed v2 targets came up empty — i.e. nothing the
        # programme builder can use.
        if not nutrient_targets and not v2_targets:
            unplanable_blocks.append({
                "block_id": b.block_id,
                "block_name": b.block_name,
                "reason": "missing_targets",
            })
            continue

        # Growth stages — try crop, fall back to base crop ("Citrus (Valencia)" → "Citrus")
        crop = b.crop
        base_crop = crop.split("(")[0].strip() if "(" in crop else crop
        stage_cols = "stage_name, stage_order, month_start, month_end, n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct"
        stages_result = sb.table("crop_growth_stages").select(stage_cols).eq("crop", crop).order("stage_order").execute()
        stages = stages_result.data or []
        if not stages and base_crop != crop:
            stages_result = sb.table("crop_growth_stages").select(stage_cols).eq("crop", base_crop).order("stage_order").execute()
            stages = stages_result.data or []
        if not stages:
            unplanable_blocks.append({
                "block_id": b.block_id,
                "block_name": b.block_name,
                "reason": "missing_growth_stages",
                "crop": crop,
            })
            continue

        # Accepted methods — block-level is authoritative.
        # Resolution order:
        #   1. `field.accepted_methods` array (the agronomist's stored
        #      per-block capability — what this orchard *can* do).
        #   2. `crop_application_methods` for the crop (fallback when
        #      the field record was created without methods set).
        #   3. Derive from irrigation_type when accepted_methods + crop
        #      methods both come up empty. Used to silently drop to
        #      `["broadcast"]` only — that lost fertigation routing on
        #      drip/micro orchards. Now: drip/micro/pivot → broadcast
        #      + fertigation; none → broadcast. Foliar always available
        #      (cheap, universal capability).
        field_row = fields_by_id.get(b.field_id) if b.field_id else None
        accepted_methods = (field_row or {}).get("accepted_methods") or []
        if not accepted_methods:
            try:
                cm = sb.table("crop_application_methods").select("method").eq("crop", crop).execute()
                accepted_methods = [m["method"] for m in (cm.data or [])]
            except Exception:
                accepted_methods = []
        if not accepted_methods:
            irr = (field_row or {}).get("irrigation_type")
            fert_capable = (field_row or {}).get("fertigation_capable")
            derived = ["broadcast", "foliar"]  # always available
            if irr in ("drip", "micro", "pivot", "sprinkler") and fert_capable:
                derived.append("fertigation")
            accepted_methods = derived

        # Soil corrections (uses linked analysis when present)
        # ─────────────────────────────────────────────────────────
        # Unified path: the wizard's grouping page now surfaces the
        # SAME pre-season recommendations the final artifact uses.
        # Previously the preview ran a parallel `calculate_all_corrections`
        # which only fired on legacy classifications-based triggers
        # (Al + SAR), so blocks with low pH / high pH / low Ca:Mg
        # showed up clean on the grouping page but flagged in the
        # final report. This now routes through soil_factor_reasoner
        # → recommend_pre_season_actions, the same code the artifact
        # build runs at orchestrator.py:237.
        #
        # Build/planting dates: the preview is interpretive — we only
        # need the *kind* of recommendation, not exact apply-by dates.
        # Anchor on today + 6 months so the timing copy reads sensibly;
        # final artifact uses the user's actual build/planting dates.
        corrections_payload: dict = {"corrections": [], "nutrient_explanations": []}
        corrective_payload = {"corrective_items": [], "missing_data": [], "assumptions": []}
        if analysis:
            soil_vals = analysis.get("soil_values") or {}
            preview_build = date.today()
            preview_plant = preview_build + timedelta(days=180)
            sf_report = reason_soil_factors(soil_vals, crop=crop)
            recs = recommend_pre_season_actions(
                block_id=b.block_id,
                soil_factor_report=sf_report,
                build_date=preview_build,
                planting_date=preview_plant,
            )
            unified_corrections: list[dict] = []
            for r in recs:
                unified_corrections.append({
                    "type": _material_to_correction_type(r.material),
                    "product": r.material,
                    "rate": r.target_rate_per_ha,
                    "timing": r.expected_status_at_planting or "Pre-season",
                    "reason": r.reason,
                    "block_id": b.block_id,
                    "block_name": b.block_name,
                })
            # Org C / OM check has no equivalent in the new module —
            # keep it as a parallel correction so we don't lose the
            # build-OM-up advice on low-carbon soils.
            org_c = check_organic_carbon(soil_vals, analysis.get("classifications") or {})
            if org_c:
                org_c["block_id"] = b.block_id
                org_c["block_name"] = b.block_name
                unified_corrections.append(org_c)

            corrections_payload = {
                "corrections": unified_corrections,
                "nutrient_explanations": get_nutrient_explanations(nutrient_targets),
            }
            all_corrections.extend(unified_corrections)

            snapshot = analysis.get("norms_snapshot") or {}
            suf_rows = snapshot.get("sufficiency") or []
            if suf_rows:
                corrective_payload = calculate_corrective_targets(
                    soil_values=soil_vals,
                    nutrient_targets=nutrient_targets,
                    sufficiency_rows=suf_rows,
                    param_map_rows=pm_rows,
                )

        # Crop type for the UI (annual / perennial)
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

        # Surface the freshest nutrient_targets we have. The persisted
        # `nutrient_targets` from the linked soil_analysis is often empty
        # for bulk-imported rows (lab files don't carry crop+yield, so
        # the upload-time computation skipped it). v2_targets is the
        # on-the-fly recompute we always do here — promote it into the
        # response under `nutrient_targets` when the persisted version
        # is empty so the wizard's Review table renders real numbers
        # instead of em-dashes.
        effective_targets = nutrient_targets
        if not effective_targets and v2_targets:
            effective_targets = [
                {"Nutrient": nut, "Target_kg_ha": float(kg)}
                for nut, kg in v2_targets.items()
            ]

        block_info.append({
            "block_id": b.block_id,
            "block_name": b.block_name,
            "crop": crop,
            "crop_type": crop_type,
            "growth_stages": stages,
            "nutrient_targets": effective_targets,
            "accepted_methods": accepted_methods,
            "irrigation_type": (field_row or {}).get("irrigation_type"),
            "fertigation_capable": (field_row or {}).get("fertigation_capable"),
            "corrections": corrections_payload["corrections"],
            "nutrient_explanations": corrections_payload["nutrient_explanations"],
            "corrective_targets": corrective_payload["corrective_items"],
            "missing_corrective_data": corrective_payload["missing_data"],
            "corrective_assumptions": corrective_payload.get("assumptions", []),
        })

        # Build a cluster stub if we have v2 targets to cluster on.
        # Area falls back to 1.0 ha for blocks missing area_ha — keeps
        # them in the cluster, just down-weights their aggregation share.
        if v2_targets:
            cluster_stubs.append(_ClusterStub(
                block_id=b.block_id,
                block_name=b.block_name,
                block_area_ha=float(b.area_ha) if b.area_ha else 1.0,
                season_targets=v2_targets,
                soil_parameters=soil_values_for_targets,
            ))
            # Surface per-block v2 targets so the wizard can recompute
            # heterogeneity locally on drag-drop.
            block_info[-1]["v2_season_targets"] = v2_targets
            block_info[-1]["block_area_ha"] = float(b.area_ha) if b.area_ha else None

    # Cluster the planable blocks with the user-chosen group count
    # (or threshold), respecting any manual assignments. When the
    # wizard sends `target_clusters`, agglomerative clustering produces
    # exactly that many groups; otherwise the legacy first-fit + refine
    # path runs against `cluster_margin`.
    clusters_payload: list[dict] = []
    if cluster_stubs:
        cluster_aggs = cluster_and_aggregate(
            cluster_stubs,
            margin=request.cluster_margin,
            assignments=request.cluster_assignments,
            target_clusters=request.target_clusters,
        )
        for agg in cluster_aggs:
            clusters_payload.append({
                "cluster_id": agg.cluster_id,
                "block_ids": agg.block_ids,
                "block_names": agg.block_names,
                "total_area_ha": agg.total_area_ha,
                "weight_strategy": agg.weight_strategy,
                "aggregated_targets": agg.aggregated_targets,
                "heterogeneity": {
                    "per_nutrient": agg.heterogeneity.per_nutrient,
                    "warnings": [
                        {
                            "nutrient": w.nutrient,
                            "cv_pct": w.cv_pct,
                            "level": w.level,
                            "threshold_pct": w.threshold_pct,
                        }
                        for w in agg.heterogeneity.warnings
                    ],
                    "any_warn": agg.heterogeneity.any_warn,
                    "any_split": agg.heterogeneity.any_split,
                    "citation": agg.heterogeneity.citation,
                },
            })

    return {
        "block_info": block_info,
        "unplanable_blocks": unplanable_blocks,
        "corrections": all_corrections,
        "clusters": clusters_payload,
        "cluster_margin": request.cluster_margin,
    }


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
        .select("artifact, state, narrative_overrides")
        .eq("id", str(artifact_id))
    )
    if user.role != "admin":
        query = query.eq("user_id", user.id)
    result = run_sb(lambda: query.limit(1).execute())
    if not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programme not found")

    row = result.data[0]
    artifact = ProgrammeArtifact.model_validate(row["artifact"])
    # When persisted Opus prose is available, render against it. Cheap
    # + deterministic. The narrative is lock-stable from approval, so
    # every re-download produces the same PDF.
    pdf_bytes = render_programme_pdf(
        artifact,
        mode="client",
        narrative_overrides=row.get("narrative_overrides") or None,
    )

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
    client_id: Optional[UUID] = Query(None),
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
    if client_id:
        query = query.eq("client_id", str(client_id))
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
        .select("state,artifact,narrative_overrides")
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
        # Lock the narrative if one has been generated. After this
        # point generate-narrative refuses with 409 and the PDF
        # renderer always uses the same prose for this artifact.
        # Re-check narrative_overrides on the row we already have so
        # we don't burn a round-trip.
        artifact_row = current.data[0]
        if artifact_row.get("narrative_overrides"):
            update["narrative_locked_at"] = datetime.utcnow().isoformat()
    # Reverse path: approved→draft un-locks narrative so the user can
    # regenerate after picking up a fault in the prose during review.
    if curr_state == "approved" and new_state == "draft":
        update["narrative_locked_at"] = None

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
# Opus narrative — generate / fetch / lock
# ============================================================
# Three-layer defense (engine + fact validator + policeman) lives
# inside enhance_artifact_prose. The endpoint just wraps persistence,
# cost capping, and lifecycle gating. Locked-once-approved is enforced
# in two places: here (refuse to regenerate) and on transition_state
# (sets narrative_locked_at on draft→approved).

# Hard cost ceiling per generation. List pricing as of 2026-04: input
# $15/MTok, output $75/MTok, cache reads $1.50/MTok, cache writes
# $18.75/MTok. A typical 4-section render lands ~$0.25; pathological
# runs could escalate. Anything above $5 is almost certainly a bug
# (loop, retry storm, runaway prompt) and we'd rather fail loudly.
NARRATIVE_COST_CAP_USD = 5.0


def _estimate_narrative_cost_usd(
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_write_tokens: int,
) -> float:
    return round(
        input_tokens * 15 / 1_000_000
        + output_tokens * 75 / 1_000_000
        + cache_read_tokens * 1.5 / 1_000_000
        + cache_write_tokens * 18.75 / 1_000_000,
        4,
    )


class GenerateNarrativeResponse(BaseModel):
    artifact_id: UUID
    narrative_overrides: dict
    raw_prose: dict
    narrative_report: dict
    narrative_generated_at: datetime
    narrative_locked_at: Optional[datetime] = None


@router.post(
    "/{artifact_id}/generate-narrative",
    response_model=GenerateNarrativeResponse,
)
async def generate_narrative(
    artifact_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Fire the Opus narrative pipeline against a draft artifact.

    Refuses if `narrative_locked_at IS NOT NULL` — once approved, the
    narrative is frozen with the engine artifact. Costs are estimated
    against list pricing and logged to ai_usage; renders above the
    NARRATIVE_COST_CAP_USD ceiling are aborted post-hoc (tokens already
    spent are recorded, prose is discarded).
    """
    from app.services.narrative.opus_renderer import enhance_artifact_prose
    from app.services.pdf_renderer import _baseline_for_narrative, _build_context

    supabase = get_supabase_admin()
    query = (
        supabase.table("programme_artifacts")
        .select("id, user_id, state, artifact, narrative_locked_at")
        .eq("id", str(artifact_id))
    )
    if user.role != "admin":
        query = query.eq("user_id", user.id)
    current = query.limit(1).execute()
    if not current.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programme not found")

    row = current.data[0]
    if row.get("narrative_locked_at"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Narrative is locked — programme has been approved. "
            "Move back to draft before regenerating.",
        )

    artifact = ProgrammeArtifact.model_validate(row["artifact"])
    context = _build_context(artifact)
    baseline = _baseline_for_narrative(context, artifact)

    try:
        result = enhance_artifact_prose(artifact, baseline=baseline, mode="client")
    except RuntimeError as exc:
        # Missing API key, etc. — surface clearly rather than burning
        # the user with a generic 500.
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"Narrative pipeline not configured: {exc}",
        )

    cost_usd = _estimate_narrative_cost_usd(
        result.input_tokens,
        result.output_tokens,
        result.cache_read_tokens,
        result.cache_write_tokens,
    )

    # Log to ai_usage regardless of outcome so cost telemetry captures
    # FAIL runs too (those still spend tokens on the audit layer).
    try:
        supabase.table("ai_usage").insert({
            "user_id": user.id,
            "operation": "generate_narrative",
            "model": "claude-opus-4-7",
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "cost_usd": cost_usd,
            "metadata": {
                "artifact_id": str(artifact_id),
                "verdict": result.verdict,
                "section_count": result.section_count,
                "duration_seconds": round(result.duration_seconds, 1),
                "cache_read_tokens": result.cache_read_tokens,
                "cache_write_tokens": result.cache_write_tokens,
                "issue_count": len(result.issues),
            },
        }).execute()
    except Exception as exc:
        logger.warning("ai_usage insert failed for generate_narrative: %s", exc)

    if cost_usd > NARRATIVE_COST_CAP_USD:
        raise HTTPException(
            status.HTTP_507_INSUFFICIENT_STORAGE,
            f"Narrative generation exceeded cost cap (${cost_usd:.2f} > "
            f"${NARRATIVE_COST_CAP_USD:.2f}). Tokens recorded in ai_usage; "
            "prose discarded. Investigate before retrying.",
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
    upd_query = (
        supabase.table("programme_artifacts")
        .update(update)
        .eq("id", str(artifact_id))
    )
    if user.role != "admin":
        upd_query = upd_query.eq("user_id", user.id)
    upd_query.execute()

    return GenerateNarrativeResponse(
        artifact_id=artifact_id,
        narrative_overrides=result.overrides,
        raw_prose=result.raw_prose,
        narrative_report=narrative_report,
        narrative_generated_at=generated_at,
        narrative_locked_at=None,
    )


class NarrativeFetchResponse(BaseModel):
    artifact_id: UUID
    narrative_overrides: Optional[dict] = None
    narrative_report: Optional[dict] = None
    narrative_generated_at: Optional[datetime] = None
    narrative_locked_at: Optional[datetime] = None


@router.get("/{artifact_id}/narrative", response_model=NarrativeFetchResponse)
async def fetch_narrative(
    artifact_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """Read the persisted narrative state for an artifact. Returns NULLs
    for every narrative field when no narrative has been generated yet."""
    supabase = get_supabase_admin()
    query = (
        supabase.table("programme_artifacts")
        .select(
            "id, user_id, narrative_overrides, narrative_report, "
            "narrative_generated_at, narrative_locked_at",
        )
        .eq("id", str(artifact_id))
    )
    if user.role != "admin":
        query = query.eq("user_id", user.id)
    current = query.limit(1).execute()
    if not current.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programme not found")

    row = current.data[0]
    return NarrativeFetchResponse(
        artifact_id=artifact_id,
        narrative_overrides=row.get("narrative_overrides"),
        narrative_report=row.get("narrative_report"),
        narrative_generated_at=row.get("narrative_generated_at"),
        narrative_locked_at=row.get("narrative_locked_at"),
    )


# ============================================================
# Season Tracker (artifact_applications + artifact_adjustments)
# ============================================================

class ApplicationRecord(BaseModel):
    block_id: str = Field(..., min_length=1, max_length=200)
    actual_date: date
    planned_blend_ref: Optional[str] = None
    product_label: Optional[str] = Field(None, max_length=300)
    rate_kg_ha: Optional[float] = Field(None, ge=0)
    rate_l_ha: Optional[float] = Field(None, ge=0)
    method: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


def _check_artifact_access(supabase, artifact_id: UUID, user: CurrentUser) -> dict:
    """Read artifact + enforce per-user scope. Returns the row dict."""
    query = supabase.table("programme_artifacts").select("*").eq("id", str(artifact_id))
    if user.role != "admin":
        query = query.eq("user_id", user.id)
    result = query.limit(1).execute()
    if not result.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Programme not found")
    return result.data[0]


def _classify_variance(
    artifact_row: dict, block_id: str, actual_date: date, rate: Optional[float],
) -> str:
    """Compare an actual application to the artifact's planned schedule.

    Returns:
      - 'on_plan'      — found a planned event within ±2 weeks of actual,
                         and (if rate given) within ±10% of planned rate
      - 'off_plan'     — date or rate diverges from the closest plan
      - 'unscheduled'  — no planned event for this block at this time of season
    """
    artifact = artifact_row.get("artifact") or {}
    blends = artifact.get("blends") or []
    closest_delta_days = None
    closest_rate_diff_pct = None
    for blend in blends:
        if blend.get("block_id") != block_id:
            continue
        for ev in (blend.get("applications") or []):
            ev_date_str = ev.get("event_date")
            if not ev_date_str:
                continue
            try:
                ev_date = date.fromisoformat(ev_date_str[:10])
            except ValueError:
                continue
            delta = abs((ev_date - actual_date).days)
            if closest_delta_days is None or delta < closest_delta_days:
                closest_delta_days = delta
                # Try to pull a rate from the blend's raw_products
                if rate is not None:
                    blend_rate = 0.0
                    for p in (blend.get("raw_products") or []):
                        rstr = p.get("rate_per_event_per_ha") or ""
                        try:
                            num = float(rstr.split()[0]) if rstr else 0.0
                            blend_rate += num
                        except ValueError:
                            pass
                    if blend_rate > 0:
                        closest_rate_diff_pct = abs(rate - blend_rate) / blend_rate * 100
    if closest_delta_days is None:
        return "unscheduled"
    if closest_delta_days <= 14 and (closest_rate_diff_pct is None or closest_rate_diff_pct <= 10):
        return "on_plan"
    return "off_plan"


@router.get("/{artifact_id}/applications")
async def list_applications(
    artifact_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    """All actual applications recorded against this programme, newest first."""
    supabase = get_supabase_admin()
    _check_artifact_access(supabase, artifact_id, user)
    result = (
        supabase.table("artifact_applications")
        .select("*")
        .eq("artifact_id", str(artifact_id))
        .order("actual_date", desc=True)
        .execute()
    )
    return result.data or []


@router.post("/{artifact_id}/applications", status_code=status.HTTP_201_CREATED)
async def record_application(
    artifact_id: UUID,
    body: ApplicationRecord,
    user: CurrentUser = Depends(get_current_user),
):
    """Record an actual application against a programme block.

    Variance is classified at insert time by comparing the actual_date
    + rate_kg_ha to the artifact's planned blends[].applications.
    """
    supabase = get_supabase_admin()
    artifact_row = _check_artifact_access(supabase, artifact_id, user)
    rate = body.rate_kg_ha if body.rate_kg_ha is not None else body.rate_l_ha
    variance = _classify_variance(artifact_row, body.block_id, body.actual_date, rate)
    payload = body.model_dump(exclude_none=True)
    payload["actual_date"] = body.actual_date.isoformat()
    payload["artifact_id"] = str(artifact_id)
    payload["variance_flag"] = variance
    payload["created_by"] = user.id
    result = supabase.table("artifact_applications").insert(payload).execute()
    if not result.data:
        raise HTTPException(500, "Failed to record application")
    return result.data[0]


@router.delete("/applications/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    record_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    row = supabase.table("artifact_applications").select("artifact_id").eq("id", str(record_id)).execute()
    if not row.data:
        raise HTTPException(404, "Application record not found")
    _check_artifact_access(supabase, UUID(row.data[0]["artifact_id"]), user)
    supabase.table("artifact_applications").delete().eq("id", str(record_id)).execute()
    return None


class AdjustmentCreate(BaseModel):
    block_id: Optional[str] = None
    trigger_type: str = Field(..., pattern=r"^(leaf_analysis|soil_analysis|off_programme|manual)$")
    trigger_ref: Optional[str] = None
    proposal: str = Field(..., min_length=1)
    severity: str = Field("info", pattern=r"^(info|warn|critical)$")


class AdjustmentReview(BaseModel):
    status: str = Field(..., pattern=r"^(approved|rejected|applied)$")
    reviewer_notes: Optional[str] = None


@router.get("/{artifact_id}/adjustments")
async def list_adjustments(
    artifact_id: UUID,
    user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    _check_artifact_access(supabase, artifact_id, user)
    result = (
        supabase.table("artifact_adjustments")
        .select("*")
        .eq("artifact_id", str(artifact_id))
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.post("/{artifact_id}/adjustments", status_code=status.HTTP_201_CREATED)
async def create_adjustment(
    artifact_id: UUID,
    body: AdjustmentCreate,
    user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    _check_artifact_access(supabase, artifact_id, user)
    payload = body.model_dump(exclude_none=True)
    payload["artifact_id"] = str(artifact_id)
    payload["created_by"] = user.id
    result = supabase.table("artifact_adjustments").insert(payload).execute()
    if not result.data:
        raise HTTPException(500, "Failed to create adjustment")
    return result.data[0]


@router.patch("/adjustments/{adjustment_id}/review")
async def review_adjustment(
    adjustment_id: UUID,
    body: AdjustmentReview,
    user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    row = supabase.table("artifact_adjustments").select("artifact_id").eq("id", str(adjustment_id)).execute()
    if not row.data:
        raise HTTPException(404, "Adjustment not found")
    _check_artifact_access(supabase, UUID(row.data[0]["artifact_id"]), user)
    update = {
        "status": body.status,
        "reviewed_by": user.id,
        "reviewed_at": datetime.utcnow().isoformat(),
    }
    if body.reviewer_notes is not None:
        update["reviewer_notes"] = body.reviewer_notes
    result = supabase.table("artifact_adjustments").update(update).eq("id", str(adjustment_id)).execute()
    if not result.data:
        raise HTTPException(500, "Failed to update adjustment")
    return result.data[0]


# ============================================================
# Helpers
# ============================================================

def _cluster_block_inputs(
    block_inputs: list[BlockInput],
    cluster_margin: float = 0.25,
    cluster_assignments: Optional[dict[str, str]] = None,
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

    cluster_aggs = cluster_and_aggregate(
        clusterable, margin=cluster_margin, assignments=cluster_assignments,
    )

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


def _attach_dataless_blocks_to_clusters(
    effective_blocks: list[BlockInput],
    cluster_aggs: list[ClusterAggregate],
    skipped_blocks: list[SkippedBlockRequest],
) -> None:
    """Mutate `effective_blocks` + `cluster_aggs` in place: each skipped
    block with `attach_to_cluster` set joins that cluster's existing
    effective block. Bumps area + adds to block_ids/block_names, so the
    cluster's recipe stays unchanged and the shopping list rolls forward.

    Singleton clusters get converted into synthetic clusters on first
    attachment so the orchestrator's per-block lab metadata doesn't
    misleadingly attach to multiple blocks.

    Skips silently when the named cluster doesn't exist or block_id /
    block_area_ha is missing — the block falls through to its
    OutstandingItem (already appended in build_programme_endpoint).
    """
    if not skipped_blocks:
        return
    aggs_by_id = {a.cluster_id: a for a in cluster_aggs}

    for sb in skipped_blocks:
        if not sb.attach_to_cluster:
            continue
        agg = aggs_by_id.get(sb.attach_to_cluster)
        if agg is None or not sb.block_id or not sb.block_area_ha:
            continue

        # Find the cluster's effective block. Synthetic clusters use
        # block_id = f"cluster_{cluster_id}"; singletons use the original
        # block's id.
        synthetic_id = f"cluster_{agg.cluster_id}"
        target_idx = next(
            (i for i, eb in enumerate(effective_blocks) if eb.block_id == synthetic_id),
            None,
        )
        if target_idx is None and len(agg.block_ids) == 1:
            # Singleton cluster — find the original block by id, convert to
            # a synthetic so multiple blocks can share it without misleading
            # lab metadata.
            singleton_id = agg.block_ids[0]
            target_idx = next(
                (i for i, eb in enumerate(effective_blocks) if eb.block_id == singleton_id),
                None,
            )
            if target_idx is None:
                continue
            original = effective_blocks[target_idx]
            effective_blocks[target_idx] = BlockInput(
                block_id=synthetic_id,
                block_name=f"Cluster {agg.cluster_id}: {', '.join(agg.block_names)}",
                block_area_ha=float(original.block_area_ha),
                soil_parameters=dict(agg.aggregated_soil_parameters),
                season_targets=dict(agg.aggregated_targets),
                lab_name=None,
                lab_method=None,
                sample_date=None,
                sample_id=None,
                pre_season_inputs=[],
                leaf_deficiencies=None,
            )

        if target_idx is None:
            continue

        # Append the dataless block to the cluster aggregate metadata.
        agg.block_ids.append(sb.block_id)
        agg.block_names.append(sb.block_name)
        agg.total_area_ha = round(agg.total_area_ha + float(sb.block_area_ha), 3)

        # Bump the effective block's area + refresh its display name.
        eb = effective_blocks[target_idx]
        effective_blocks[target_idx] = BlockInput(
            block_id=eb.block_id,
            block_name=f"Cluster {agg.cluster_id}: {', '.join(agg.block_names)}",
            block_area_ha=eb.block_area_ha + float(sb.block_area_ha),
            soil_parameters=eb.soil_parameters,
            season_targets=eb.season_targets,
            lab_name=eb.lab_name,
            lab_method=eb.lab_method,
            sample_date=eb.sample_date,
            sample_id=eb.sample_id,
            pre_season_inputs=eb.pre_season_inputs,
            leaf_deficiencies=eb.leaf_deficiencies,
        )


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

    Two flavors:
      * Block with `attach_to_cluster` set → rough plan emitted under that
        cluster's recipe; OutstandingItem flags "soil analysis still
        recommended for tighter targeting".
      * Block without attachment → not planned at all; OutstandingItem
        says rebuild after linking a soil analysis.

    Kept separate from the endpoint so it's unit-testable without
    spinning up FastAPI + Supabase.
    """
    for sb in skipped_blocks:
        if sb.attach_to_cluster:
            artifact.outstanding_items.append(OutstandingItem(
                item=f"Block '{sb.block_name}' on rough plan (Recipe {sb.attach_to_cluster})",
                why_it_matters=(
                    "This block has no soil analysis on file, so its targets "
                    f"are inherited from Recipe {sb.attach_to_cluster}'s averaged "
                    "values rather than computed from its own soil. The recipe "
                    "is a reasonable starting point; per-block tuning isn't possible."
                ),
                impact_if_skipped=(
                    "Sample the block and rebuild the programme to compute "
                    "block-specific targets — the rough plan may over- or "
                    "under-fertilize relative to actual demand."
                ),
            ))
        else:
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
    age_factor_rows = supabase.table("perennial_age_factors").select("*").execute().data or []
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
        age_factor_rows=age_factor_rows,
    )


def _load_materials_for_user(supabase, user: CurrentUser) -> list[dict]:
    """Return the materials list the orchestrator should plan against.

    Everyone — admin and agent alike — runs against the admin-approved
    subset from `default_materials.materials` + `.liquid_materials`,
    with "Manure Compost" always included. Defaults are meant as the
    real production material pool; in a one-man shop where the same
    person curates the catalogue and builds programmes, the previous
    admin escape hatch meant the defaults never applied to the
    programmes the admin actually built.

    If no default_materials row exists yet (fresh install), falls back
    to the full catalog with a warning logged — safer than blocking
    the build.
    """
    all_mats = supabase.table("materials").select("*").execute().data or []
    defaults_res = supabase.table("default_materials").select("*").execute()
    if not defaults_res.data:
        logger.warning(
            "No default_materials row found — user %s falling back "
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
            "default_materials for user %s resolves to zero matches — "
            "falling back to full catalog.",
            user.id,
        )
        return all_mats
    return filtered
