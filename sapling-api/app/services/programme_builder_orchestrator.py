"""
Programme Builder Orchestrator — Phase 2 module 7 of 10 (the composer).

Chains the 6 reasoning modules into a real ProgrammeArtifact:

    soil_factor_reasoner   ─┐
    pre_season_module      ─┤
    stage_splitter         ─┤──►  [Orchestrator]  ──►  ProgrammeArtifact
    method_selector        ─┤
    foliar_trigger_engine  ─┤
    risk_flag_generator    ─┘

The orchestrator owns:
  * Sequencing (target_compute first, then residual adjust, then stage
    split, then method select, then foliar triggers)
  * Section-applicability decisions (no PreSeasonRecommendations section
    if no lead time; no FoliarEvents if no triggers fire)
  * Decision audit trail (every module invocation or skip logged)
  * Source-citation aggregation (deduped across all modules)
  * Assumption aggregation (all defaults applied, surfaced in output)

Not yet composed: target_computation (module 7 of 10, uses existing
soil_engine.calculate_nutrient_targets), consolidator (module 8 — groups
per-stage method assignments into blends), two-stream packaging (module
9 — wraps liquid_optimizer with Part A/B constraint), complementarity
(module 10 — foliar+fertigation+basal co-design).

Until those land, Blend + Concentrate + ShoppingList sections of the
artifact stay empty (fail transparent — we don't fake them).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from app.models import (
    Assumption,
    Blend,
    DataCompleteness,
    FactorFindingOut,
    FoliarEvent,
    MethodAvailability,
    NutrientStatusEntry,
    OutstandingItem,
    PreSeasonInput,
    PreSeasonRecommendation,
    ProgrammeArtifact,
    ProgrammeHeader,
    ProgrammeState,
    ReplanReason,
    RiskFlag,
    ShoppingListEntry,
    SoilSnapshot,
    SourceCitation,
    StageSchedule,
    StageWindow,
    Tier,
    VariantKey,
)
from app.services.blend_validator import validate_blends
from app.services.consolidator import consolidate_blends
from app.services.month_allocator import allocate_to_months
from app.services.foliar_trigger_engine import trigger_foliar_events
from app.services.method_selector import aggregate_by_method, select_methods
from app.services.pre_season_module import (
    compute_residual_position,
    flag_lost_opportunities,
    recommend_pre_season_actions,
)
from app.services.risk_flag_generator import generate_outstanding_items, generate_risk_flags
from app.services.similarity_merger import merge_compatible_within_stage, merge_similar_blends
from app.services.soil_factor_reasoner import reason_soil_factors
from app.services.stage_splitter import (
    StageSplit,
    get_family,
    get_stage_shape_provenance,
    split_season_targets,
)


# ============================================================
# Input container
# ============================================================

@dataclass
class BlockInput:
    """One block's inputs to the orchestrator."""
    block_id: str
    block_name: str
    block_area_ha: float
    soil_parameters: dict[str, float]
    season_targets: dict[str, float]  # {'N': 155, 'P2O5': 86, ...}
    lab_name: Optional[str] = None
    lab_method: Optional[str] = None
    sample_date: Optional[date] = None
    sample_id: Optional[str] = None
    pre_season_inputs: list[PreSeasonInput] = field(default_factory=list)
    leaf_deficiencies: Optional[dict[str, float]] = None  # Season Tracker re-entry
    # For perennials, target_computation scales by density
    # (block_pop_per_ha / crop_requirements.pop_per_ha).
    pop_per_ha: Optional[float] = None
    # For perennials, target_computation scales N/P/K by the bracket
    # in perennial_age_factors. None / annuals → factor 1.0.
    tree_age: Optional[int] = None


@dataclass
class OrchestratorInput:
    """Top-level inputs — mirrors the ProgrammeBuilderInputs protocol."""
    client_name: str
    farm_name: str
    prepared_for: str
    crop: str
    planting_date: date
    build_date: date  # typically date.today()
    method_availability: MethodAvailability
    blocks: list[BlockInput]
    season: str = ""  # e.g. "Autumn 2026"
    location: Optional[str] = None
    ref_number: Optional[str] = None
    expected_harvest_date: Optional[date] = None
    stage_count: int = 5
    high_al_soil: Optional[bool] = None  # override auto-detection
    wet_summer_between_apply_and_plant: bool = False
    has_gypsum_in_plan: bool = False
    has_irrigation_water_test: bool = False
    has_recent_leaf_analysis: bool = False
    planned_n_fertilizers: Optional[list[str]] = None
    available_materials: Optional[list[dict]] = None
    # Irrigation water analysis applied to every block unless per-block
    # override exists. Keys: EC (dS/m), Na/Ca/Mg/HCO3 (mg/L), pH, etc.
    water_values: Optional[dict] = None
    # Farmer's operational availability — months (1-12) when fertilizer
    # application is physically possible (labour, machinery, irrigation
    # schedule, harvest activity). When supplied, the engine maps stage
    # allocations onto these slots with timing walls enforced. When None,
    # engine uses the default stage-count-aligned calendar.
    application_months: Optional[list[int]] = None
    # Sufficiency catalog rows (soil_sufficiency, soil_parameter_map) —
    # used to populate per-block NutrientStatusEntry on the output
    # snapshot so the UI can render 'value vs ideal' range bars without
    # re-fetching from the DB.
    #
    # `crop_override_rows` carries the full crop_sufficiency_overrides
    # table; the orchestrator merges it with `sufficiency_rows` per-crop
    # via `merge_sufficiency_for_crop` so the visible "ideal" bands
    # actually reflect crop-specific bands (e.g. Macadamia K 85-145
    # tighter than the generic 80-150). Without this the report shows
    # universal generic bands for every crop.
    sufficiency_rows: Optional[list[dict]] = None
    crop_override_rows: Optional[list[dict]] = None
    param_map_rows: Optional[list[dict]] = None
    # cluster_id → list of source BlockInputs that fed the aggregate.
    # When supplied, the orchestrator runs soil-side reasoning (factor
    # findings, pre-season recommendations, soil snapshots) on each
    # SOURCE block individually rather than on the cluster aggregate
    # — block-specific signals like Blok 100's 22% Al-saturation
    # otherwise get averaged out in a multi-block cluster and miss
    # the lime-priority window. Blend production still runs on the
    # cluster aggregate from `blocks`. Singleton clusters are fine
    # either way (source == effective).
    cluster_sources: Optional[dict[str, list]] = None
    # Assumptions pre-computed upstream (typically by compute_season_targets
    # in the router) — yield-target defaults, density scaling, N-min
    # credit, etc. Merged into the orchestrator's own assumptions list
    # so they flow to the artifact's Assumptions section. Without this
    # bridge any assumption emitted before the orchestrator runs is
    # silently dropped.
    pre_computed_assumptions: list[Assumption] = field(default_factory=list)
    # Per-cluster method overrides set by the agronomist on the cluster
    # board. Keys are cluster_ids (e.g. "A", "B"). When a cluster_id
    # appears here, the engine uses its MethodAvailability instead of
    # the global `method_availability` for that group's blends. Lets
    # the user say "Group A drip-only this season, Group B broadcast
    # only" without changing the underlying field capability.
    method_availability_per_cluster: dict[str, MethodAvailability] = field(default_factory=dict)


# ============================================================
# Main orchestrator
# ============================================================

def build_programme(inputs: OrchestratorInput) -> ProgrammeArtifact:
    """Compose reasoning modules into a ProgrammeArtifact.

    Returns an artifact with populated sections for every module that
    produced output. Modules not yet shipped (blends, concentrates,
    shopping list) remain empty — renderer is responsible for showing
    "not yet computed" markers to the user.
    """
    decision_trace: list[str] = []
    sources_audit: list[SourceCitation] = []
    assumptions: list[Assumption] = list(inputs.pre_computed_assumptions or [])
    all_risk_flags: list[RiskFlag] = []
    all_outstanding: list[OutstandingItem] = []
    all_foliar_events: list[FoliarEvent] = []
    all_pre_season_recs: list[PreSeasonRecommendation] = []

    # Auto-detect high Al soil across blocks if not overridden
    high_al_soil = inputs.high_al_soil
    soil_factor_reports = {}

    # --------------------------------------------------------
    # Per-SOURCE soil pass (snapshots + pre-season)
    # --------------------------------------------------------
    # Soil reasoning + pre-season recommendations run per SOURCE block,
    # not per cluster aggregate. Block-specific signals (e.g. Blok 100's
    # 22% Al-saturation while Blok 101 sits at 8%) get averaged out in
    # a multi-block cluster — running per source preserves the lime-
    # priority signal that drives pre-season scheduling and the visual
    # range bars in the per-block soil report.
    source_blocks: list[BlockInput] = []
    if inputs.cluster_sources:
        seen_ids: set[str] = set()
        for sources in inputs.cluster_sources.values():
            for src in sources:
                if src.block_id in seen_ids:
                    continue
                seen_ids.add(src.block_id)
                source_blocks.append(src)
    else:
        # No clustering metadata — treat the input list as the source
        # set (singleton clusters case).
        source_blocks = list(inputs.blocks)

    # Build a block_id → cluster_id resolver. Singleton clusters keep
    # their original block_id (the orchestrator never rewrites it to
    # `cluster_<letter>`), so the per-cluster method-availability
    # override lookup needs an explicit map. Without this, single-block
    # programmes silently drop their cluster overrides — the agronomist
    # excludes fertigation + foliar on the cluster board, the engine
    # falls back to global method_availability, and uses fertigation
    # + foliar anyway. This map fixes that.
    block_to_cluster: dict[str, str] = {}
    if inputs.cluster_sources:
        for cluster_id, sources in inputs.cluster_sources.items():
            for src in sources:
                block_to_cluster[src.block_id] = cluster_id

    soil_snapshots_out: list[SoilSnapshot] = []
    for src in source_blocks:
        src_sf_report = reason_soil_factors(
            soil_values=src.soil_parameters,
            crop=inputs.crop,
            water_values=inputs.water_values,
        )
        # Promote per-source Al-critical detection to the high_al_soil
        # flag so blend production downstream picks up the toxicity
        # context even when the cluster aggregate looks benign.
        if high_al_soil is None:
            for f in src_sf_report.findings:
                if f.parameter == "Al_saturation_pct" and f.severity == "critical":
                    high_al_soil = True
                    break
        # Mode A pre-season — per source, so per-block lime / gypsum /
        # dolomite recommendations land with the right rate.
        recs = recommend_pre_season_actions(
            block_id=src.block_id,
            soil_factor_report=src_sf_report,
            build_date=inputs.build_date,
            planting_date=inputs.planting_date,
            available_materials=inputs.available_materials,
        )
        all_pre_season_recs.extend(recs)
        if recs:
            decision_trace.append(
                f"Block {src.block_id}: pre-season — {len(recs)} recommendation"
                f"{'s' if len(recs) != 1 else ''} from soil findings"
            )
        # SoilSnapshot with full structured data (per-source).
        headline = [f.message for f in src_sf_report.by_severity_at_least("warn")[:3]]
        computed_ratios = {
            k: float(v) for k, v in (src_sf_report.computed or {}).items()
            if isinstance(v, (int, float))
        }
        factor_findings = [
            FactorFindingOut(
                kind=f.kind,
                severity=f.severity,
                parameter=f.parameter,
                value=float(f.value),
                threshold=float(f.threshold) if f.threshold is not None else None,
                message=f.message,
                recommended_action=f.recommended_action,
                source_id=f.source_id,
                source_section=f.source_section,
                tier=f.tier,
            )
            for f in src_sf_report.findings
        ]
        # Normalise unit-suffixed keys ("K (mg/kg)" → "K") before the
        # sufficiency lookup. Without this the soil-report shows only
        # parameters whose labels happen to match the sufficiency table
        # exactly — usually just pH (KCl) — and every other lab
        # parameter (K / Ca / Mg / P / S / saturations) silently drops
        # out, leaving the agronomist staring at "no NPK, no ratios".
        from app.services.soil_engine import normalise_soil_values, merge_sufficiency_for_crop
        normalised_params = normalise_soil_values(src.soil_parameters)
        # Layer crop overrides on the universal sufficiency rows so the
        # range bars show crop-tuned ideal bands (e.g. Macadamia K 85-145)
        # rather than the generic-for-all-crops fallback. Per-block crop
        # in case the programme spans mixed crops (rare today, but the
        # data model allows it).
        merged_sufficiency = merge_sufficiency_for_crop(
            inputs.sufficiency_rows or [],
            inputs.crop_override_rows or [],
            inputs.crop,
        )
        nutrient_status = _build_nutrient_status(
            soil_parameters=normalised_params,
            sufficiency_rows=merged_sufficiency,
            param_map_rows=inputs.param_map_rows or [],
            lab_method=src.lab_method,
        )
        # Smart ratio-by-ratio interpretation — every relevant ratio gets
        # an interpretation row (in-band or out-of-band) explaining what
        # the value means agronomically and which nutrients are bound.
        # Plus a holistic 2-3 sentence summary collapsing all ratios.
        from app.services.ratio_interpreter import (
            interpret_all_ratios,
            summarise_ratios,
        )
        ratio_interps_dc = interpret_all_ratios(
            soil_values=src.soil_parameters or {},
            computed_ratios=computed_ratios,
        )
        ratio_summary_dc = summarise_ratios(ratio_interps_dc)
        # Convert dataclasses → Pydantic for the artifact.
        from app.models.programme_artifact import (
            RatioInterpretationOut,
            RatioHolisticSummaryOut,
        )
        ratio_interpretations_out = [
            RatioInterpretationOut(
                name=i.name, value=i.value,
                ideal_low=i.ideal_low, ideal_high=i.ideal_high,
                unit=i.unit, state=i.state, severity=i.severity,
                what_it_measures=i.what_it_measures,
                direct_effect=i.direct_effect,
                bound_nutrients=list(i.bound_nutrients),
                recommended_action=i.recommended_action,
                source_citation=i.source_citation,
            )
            for i in ratio_interps_dc
        ]
        ratio_summary_out = RatioHolisticSummaryOut(
            summary=ratio_summary_dc.summary,
            key_concerns=list(ratio_summary_dc.key_concerns),
            nutrients_at_risk=list(ratio_summary_dc.nutrients_at_risk),
        )

        # Crop-specific qualitative notes (Cl-sensitive, S-critical, etc.)
        # — feeds renderer's Notes section + future product selector
        # filters. Looks up from hardcoded knowledge base + live
        # crop_calc_flags row when available.
        from app.services.crop_notes_generator import generate_crop_notes
        from app.models.programme_artifact import CropNote
        crop_calc_row = None  # caller can pass via inputs in future
        crop_notes_dc = generate_crop_notes(inputs.crop, crop_calc_row)
        crop_notes_out = [
            CropNote(
                kind=n.kind, headline=n.headline, detail=n.detail,
                severity=n.severity, source_citation=n.source_citation,
            )
            for n in crop_notes_dc
        ]

        soil_snapshots_out.append(SoilSnapshot(
            block_id=src.block_id,
            block_name=src.block_name,
            block_area_ha=src.block_area_ha,
            lab_name=src.lab_name,
            lab_method=src.lab_method,
            sample_date=src.sample_date,
            sample_id=src.sample_id,
            parameters=src.soil_parameters,
            computed_ratios=computed_ratios,
            factor_findings=factor_findings,
            nutrient_status=nutrient_status,
            ratio_interpretations=ratio_interpretations_out,
            ratio_summary=ratio_summary_out,
            crop_notes=crop_notes_out,
            headline_signals=headline,
        ))

    # --------------------------------------------------------
    # Per-EFFECTIVE-block reasoning (blend production)
    # --------------------------------------------------------
    block_totals: dict[str, dict[str, float]] = {}
    stage_schedules: list[StageSchedule] = []
    updated_pre_season_inputs: list[PreSeasonInput] = []
    all_blends = []  # populated by consolidator per block

    # Multi-block clusters need a "directory" snapshot so the walkthrough
    # group-lookup keyed on cluster_X has somewhere to read the member
    # list + total area from. Filtered out of the Soil Report by the
    # renderer (it skips cluster_-prefixed snapshots) — purely a lookup
    # entry, no parameters / findings on it.
    if inputs.cluster_sources:
        for cluster_id, sources in inputs.cluster_sources.items():
            if len(sources) <= 1:
                continue
            soil_snapshots_out.append(SoilSnapshot(
                block_id=f"cluster_{cluster_id}",
                block_name=", ".join(s.block_name for s in sources),
                block_area_ha=sum(s.block_area_ha for s in sources),
                parameters={},
                computed_ratios={},
                factor_findings=[],
                nutrient_status=[],
                headline_signals=[],
            ))

    for block in inputs.blocks:
        decision_trace.append(f"Block {block.block_id}: start reasoning")

        # 1. Soil factor reasoner — always runs
        sf_report = reason_soil_factors(
            soil_values=block.soil_parameters,
            crop=inputs.crop,
            water_values=inputs.water_values,
        )
        soil_factor_reports[block.block_id] = sf_report
        decision_trace.append(
            f"Block {block.block_id}: SoilFactorReasoner produced "
            f"{len(sf_report.findings)} findings"
        )

        # Auto-detect high Al if not set
        if high_al_soil is None:
            block_has_critical_al = any(
                f.parameter == "Al_saturation_pct" and f.severity == "critical"
                for f in sf_report.findings
            )
            if block_has_critical_al:
                high_al_soil = True

        # 2. Pre-season — Mode A recommendations (lime / gypsum etc.)
        # are produced per SOURCE block in the upstream per-source pass,
        # not here on the cluster aggregate (averaging would dilute the
        # block-specific signals that drive pre-season scheduling).
        # Mode B (residual computation) stays in-loop because pre-season
        # INPUTS are already-applied amendments tracked at the cluster
        # level via the BlockInput's pre_season_inputs field.
        months_to_planting = (inputs.planting_date - inputs.build_date).days / 30.44

        # Mode B — compute residual
        residual_subtraction: dict[str, float] = {}
        if block.pre_season_inputs:
            updated_psi, residual_subtraction = compute_residual_position(
                pre_season_inputs=block.pre_season_inputs,
                planting_date=inputs.planting_date,
                high_al_soil=high_al_soil or False,
                wet_summer_between_apply_and_plant=inputs.wet_summer_between_apply_and_plant,
                available_materials=inputs.available_materials,
            )
            updated_pre_season_inputs.extend(updated_psi)
            decision_trace.append(
                f"Block {block.block_id}: Pre-season Mode B — residual subtraction "
                f"{residual_subtraction}"
            )

        # Mode C — lost opportunities
        lost_items, lost_flags = flag_lost_opportunities(
            soil_factor_report=sf_report,
            build_date=inputs.build_date,
            planting_date=inputs.planting_date,
        )
        all_outstanding.extend(lost_items)
        all_risk_flags.extend(lost_flags)
        if lost_items:
            decision_trace.append(
                f"Block {block.block_id}: Pre-season Mode C — "
                f"{len(lost_items)} lost opportunities"
            )

        # 3. Apply residual subtraction to season targets
        adjusted_targets = {}
        for nutrient, kg in block.season_targets.items():
            subtracted = residual_subtraction.get(nutrient, 0)
            adjusted = max(0, kg - subtracted)
            adjusted_targets[nutrient] = adjusted

        if residual_subtraction:
            assumptions.append(Assumption(
                field=f"block.{block.block_id}.residual_subtraction",
                assumed_value=str(residual_subtraction),
                override_guidance="Override via high_al_soil + wet_summer flags if conditions differ",
                tier=Tier.IMPLEMENTER_CONVENTION,
            ))

        # 4. Stage splitter
        stage_splits = split_season_targets(
            crop=inputs.crop,
            season_targets=adjusted_targets,
            stage_count=inputs.stage_count,
        )
        stage_src, stage_section, stage_tier = get_stage_shape_provenance(inputs.crop)
        sources_audit.append(SourceCitation(
            source_id=stage_src,
            section=stage_section,
            tier=Tier(stage_tier),
        ))
        decision_trace.append(
            f"Block {block.block_id}: StageSplitter — {len(stage_splits)} stages "
            f"using {get_family(inputs.crop)} family shape (tier {stage_tier})"
        )

        # 4b. Month allocator — when the farmer has supplied their
        # operational application months, reshape the stage-based
        # allocation onto those specific slots. Timing walls are enforced
        # here: any nutrient blocked in a given month is zeroed in that
        # event (redistributed to unblocked events in the same stage if
        # possible). When application_months is None, falls through with
        # a 1-event-per-stage schedule — identical to legacy behaviour.
        #
        # The allocator's per-event nutrient totals are summed back to
        # real-stage totals so method_selector + consolidator operate at
        # real-stage granularity (one Blend per real stage × method).
        # Per-event timing is preserved on the Blend's applications[] list
        # (see F3 — ApplicationEvent model).
        month_allocation = None
        if inputs.application_months:
            initial_schedule = _build_stage_schedule(
                block_id=block.block_id,
                planting_date=inputs.planting_date,
                harvest_date=inputs.expected_harvest_date,
                stage_count=inputs.stage_count,
                stage_names=[s.stage_name for s in stage_splits],
            )
            allocation = allocate_to_months(
                crop=inputs.crop,
                stage_splits=stage_splits,
                stage_schedule=initial_schedule.stages,
                allowed_months=inputs.application_months,
                planting_date=inputs.planting_date,
                season_end=inputs.expected_harvest_date,
            )
            month_allocation = allocation
            # Sum per-event nutrients back to real-stage totals. Walls may
            # have zeroed some per-event amounts (redistributed within the
            # stage where possible); the summed total reflects the true
            # deliverable amount per real stage.
            real_stage_nutrients: dict[int, dict[str, float]] = {}
            for app in allocation.applications:
                bucket = real_stage_nutrients.setdefault(app.stage_number, {})
                for nut, kg in app.nutrients.items():
                    bucket[nut] = bucket.get(nut, 0.0) + kg
            stage_splits = [
                StageSplit(
                    stage_number=split.stage_number,
                    stage_name=split.stage_name,
                    nutrients=real_stage_nutrients.get(split.stage_number, {}),
                    source_id=stage_src,
                    source_section=stage_section,
                    tier=stage_tier,
                )
                for split in stage_splits
                if split.stage_number in real_stage_nutrients
            ]
            decision_trace.append(
                f"Block {block.block_id}: MonthAllocator — {len(allocation.applications)} "
                f"application events mapped from {len(inputs.application_months)} allowed months"
            )
            # Surface allocator risk + outstanding messages into the artifact
            for msg in allocation.risk_messages:
                all_risk_flags.append(RiskFlag(
                    message=msg, severity="warn",
                    source=SourceCitation(
                        source_id="FERTASA_TIMING_WALL", section="month_allocator",
                        tier=Tier.SA_INDUSTRY_BODY,
                    ),
                ))
            for msg in allocation.outstanding_messages:
                all_outstanding.append(OutstandingItem(
                    item="Application-month coverage gap",
                    why_it_matters=msg,
                ))
            # Removed: the "no allowed application month inside its
            # window" warning was deliberately killed (see month_allocator
            # comment + memory:project_application_timing_and_blend_count).
            # Agronomist owns timing; engine doesn't bark.

        # 5. Method selector — uses per-cluster availability when the
        # agronomist set an override on the cluster board, falls back
        # to the global method_availability otherwise.
        # Resolve cluster_id with three fallbacks (in priority order):
        #   1. The `cluster_` prefix on multi-block synthetic blocks
        #   2. The block_to_cluster map (singletons keep their original id)
        #   3. The block_id itself (no clustering at all)
        if block.block_id.startswith("cluster_"):
            cluster_id = block.block_id[len("cluster_"):]
        elif block.block_id in block_to_cluster:
            cluster_id = block_to_cluster[block.block_id]
        else:
            cluster_id = block.block_id
        block_method_availability = (
            inputs.method_availability_per_cluster.get(cluster_id)
            or inputs.method_availability
        )
        method_assignments = select_methods(
            stage_splits=stage_splits,
            method_availability=block_method_availability,
            soil_factor_report=sf_report,
            crop_family=get_family(inputs.crop),
        )
        decision_trace.append(
            f"Block {block.block_id}: MethodSelector — {len(method_assignments)} routings"
        )

        # 6. Foliar trigger engine — gated on the same per-cluster
        # availability the method selector uses. Previously this fired
        # unconditionally, so a cluster override that turned foliar OFF
        # still produced foliar events (the user excluded foliar but
        # the report had foliar passes anyway). Honour the agronomist's
        # call: if foliar isn't on the equipment list for this cluster,
        # don't trigger any foliar events for it.
        if block_method_availability.has_foliar_sprayer:
            foliar_events = trigger_foliar_events(
                block_id=block.block_id,
                crop=inputs.crop,
                planting_date=inputs.planting_date,
                soil_factor_report=sf_report,
                leaf_deficiencies=block.leaf_deficiencies,
                block_area_ha=block.block_area_ha,
            )
        else:
            foliar_events = []
            decision_trace.append(
                f"Block {block.block_id}: FoliarTriggerEngine SKIPPED — "
                f"cluster override excluded foliar"
            )
        all_foliar_events.extend(foliar_events)
        if foliar_events:
            decision_trace.append(
                f"Block {block.block_id}: FoliarTriggerEngine — "
                f"{len(foliar_events)} events ({_trigger_kind_summary(foliar_events)})"
            )
        else:
            decision_trace.append(
                f"Block {block.block_id}: FoliarTriggerEngine — no triggers fired, no events"
            )

        # 7. Risk flags + outstanding items
        risk_flags = generate_risk_flags(
            soil_factor_report=sf_report,
            crop=inputs.crop,
            planned_n_fertilizers=inputs.planned_n_fertilizers,
            has_gypsum_in_plan=inputs.has_gypsum_in_plan,
            has_irrigation_water_test=inputs.has_irrigation_water_test,
            uses_fertigation=_uses_fertigation(inputs.method_availability),
        )
        all_risk_flags.extend(risk_flags)

        season_weeks = None
        if inputs.expected_harvest_date:
            season_weeks = (inputs.expected_harvest_date - inputs.planting_date).days // 7
        outstanding = generate_outstanding_items(
            soil_factor_report=sf_report,
            crop=inputs.crop,
            has_irrigation_water_test=inputs.has_irrigation_water_test,
            has_recent_leaf_analysis=inputs.has_recent_leaf_analysis,
            uses_fertigation=_uses_fertigation(inputs.method_availability),
            season_weeks=season_weeks,
        )
        all_outstanding.extend(outstanding)

        # 8. Stage schedule — per-event StageWindows when the allocator
        # ran (so the timeline surface shows each concrete application
        # date), otherwise the default per-real-stage timeline from
        # planting. The consolidator receives the real-stage schedule
        # plus the allocator's events separately (see step 9).
        if month_allocation is not None:
            # One StageWindow per application event for the timeline. The
            # stage_number on the window carries the global event index
            # so the renderer can order them; event-of-stage metadata is
            # preserved on the Blend's ApplicationEvents.
            schedule_windows: list[StageWindow] = []
            for app in month_allocation.applications:
                display_name = app.stage_name
                if app.total_events_in_stage > 1:
                    display_name = (
                        f"{app.stage_name} ({app.event_of_stage_index} of "
                        f"{app.total_events_in_stage})"
                    )
                schedule_windows.append(StageWindow(
                    stage_number=app.event_index,
                    stage_name=display_name,
                    week_start=app.week_from_planting,
                    week_end=app.week_from_planting,
                    date_start=app.event_date,
                    date_end=app.event_date,
                    events=1,
                ))
            schedule = StageSchedule(
                block_id=block.block_id,
                planting_date=inputs.planting_date,
                harvest_date=inputs.expected_harvest_date,
                cadence="per-application",
                stages=schedule_windows,
            )
            # Real-stage schedule for the consolidator fallback path.
            # (When allocations is provided the consolidator uses those
            # directly; this stays as a safety net.)
            consolidator_schedule = _build_stage_schedule(
                block_id=block.block_id,
                planting_date=inputs.planting_date,
                harvest_date=inputs.expected_harvest_date,
                stage_count=inputs.stage_count,
                stage_names=[s.stage_name for s in stage_splits],
            ).stages
        else:
            stage_names = [s.stage_name for s in stage_splits]
            schedule = _build_stage_schedule(
                block_id=block.block_id,
                planting_date=inputs.planting_date,
                harvest_date=inputs.expected_harvest_date,
                stage_count=inputs.stage_count,
                stage_names=stage_names,
            )
            consolidator_schedule = schedule.stages
        stage_schedules.append(schedule)

        # 9. Consolidator — group method_assignments into typed Blends
        #    (populates ProgrammeArtifact.blends[], producing real
        #    Blend / BlendPart / Concentrate objects for the renderer).
        if inputs.available_materials:
            block_blends = consolidate_blends(
                assignments=method_assignments,
                available_materials=inputs.available_materials,
                block_id=block.block_id,
                block_area_ha=block.block_area_ha,
                stage_schedule=consolidator_schedule,
                allocations=(
                    month_allocation.applications if month_allocation else None
                ),
                planting_date=inputs.planting_date,
                crop=inputs.crop,
            )
            pre_merge_count = len(block_blends)

            # First pass: merge different-product DRY blends within the
            # same (block, stage, method) when chemistry allows. Bias
            # toward fewer bags — agronomists prefer one combined
            # broadcast over a basal + starter split when it's safe.
            block_blends = merge_compatible_within_stage(
                block_blends, block_area_ha=block.block_area_ha,
            )
            after_within_stage = len(block_blends)

            # Second pass: F4 — merge identical-product blends across
            # adjacent stages.
            block_blends = merge_similar_blends(
                block_blends, crop=inputs.crop, block_area_ha=block.block_area_ha,
            )
            all_blends.extend(block_blends)

            within_stage_collapsed = pre_merge_count - after_within_stage
            similarity_collapsed = after_within_stage - len(block_blends)
            note_parts: list[str] = []
            if within_stage_collapsed > 0:
                note_parts.append(
                    f"WithinStageMerger collapsed {within_stage_collapsed} dry blend(s) "
                    f"(same stage, no chemistry conflict)"
                )
            if similarity_collapsed > 0:
                note_parts.append(
                    f"SimilarityMerger collapsed {similarity_collapsed} adjacent pair(s) "
                    f"(same recipe, ±10% rate tolerance, no timing wall in gap)"
                )
            if note_parts:
                decision_trace.append(
                    f"Block {block.block_id}: Consolidator — {pre_merge_count} blends → "
                    f"{len(block_blends)} blends (" + "; ".join(note_parts) + ")"
                )
            else:
                decision_trace.append(
                    f"Block {block.block_id}: Consolidator — {len(block_blends)} blends "
                    f"(no merges applied)"
                )
        else:
            decision_trace.append(
                f"Block {block.block_id}: Consolidator skipped — "
                f"no materials catalog provided (Blend section stays empty)"
            )

        # 10. Block totals — assemble from adjusted_targets
        block_totals[block.block_id] = adjusted_targets

        # SoilSnapshot generation is handled in the upstream per-source
        # pass — the cluster aggregate's snapshot would just duplicate
        # what the per-source snapshots already cover for the soil
        # report, and the renderer's per-block visualisations want the
        # per-source granularity.

    # --------------------------------------------------------
    # Build the header
    # --------------------------------------------------------
    header = ProgrammeHeader(
        client_name=inputs.client_name,
        farm_name=inputs.farm_name,
        location=inputs.location,
        prepared_for=inputs.prepared_for,
        prepared_date=inputs.build_date,
        ref_number=inputs.ref_number,
        state=ProgrammeState.DRAFT,
        replan_reason=ReplanReason.FIRST_PASS,
        crop=inputs.crop,
        variant_key=VariantKey(canonical_crop=inputs.crop),
        season=inputs.season or _default_season_label(inputs.planting_date),
        planting_date=inputs.planting_date,
        expected_harvest_date=inputs.expected_harvest_date,
        data_completeness=_infer_data_completeness(inputs),
        method_availability=inputs.method_availability,
    )

    decision_trace.append(
        f"Orchestrator: produced artifact with {len(soil_snapshots_out)} blocks, "
        f"{len(all_pre_season_recs)} recommendations, {len(all_foliar_events)} foliar events, "
        f"{len(all_risk_flags)} risk flags"
    )

    # Note truly-empty section transparently
    if not all_blends:
        decision_trace.append(
            "Orchestrator: Blend section empty — either no materials "
            "catalog provided OR method assignments produced no groupable "
            "events. Shopping list will be empty too."
        )

    # Run blend validator over all blends (module 9) — catches stream purity,
    # known incompat pairs, missing sources. Surfaces warnings as RiskFlags.
    if all_blends and inputs.available_materials:
        _validations, validation_flags = validate_blends(
            blends=all_blends,
            available_materials=inputs.available_materials,
            compatibility_rules=None,  # caller can pass from materials_compatibility table
        )
        all_risk_flags.extend(validation_flags)
        decision_trace.append(
            f"Orchestrator: BlendValidator — {len(_validations)} blends validated, "
            f"{len(validation_flags)} warnings/errors surfaced"
        )

    # Dedup all list fields where the orchestrator fan-out produces
    # identical per-block entries (e.g. cluster A and cluster B both
    # emit the same "irrigation water test" OutstandingItem).
    deduped_sources = _dedup_sources(sources_audit)
    deduped_outstanding = _dedup_outstanding(all_outstanding)
    deduped_risk_flags = _dedup_risk_flags(all_risk_flags)
    deduped_assumptions = _dedup_assumptions(assumptions)

    # Roll up per-product totals across all blends + foliar events
    # into a shopping list. Categorises by method so the doc can
    # show separate drip / foliar / dry_blend tables.
    shopping_list = _build_shopping_list(all_blends, all_foliar_events)

    return ProgrammeArtifact(
        header=header,
        soil_snapshots=soil_snapshots_out,
        pre_season_inputs=updated_pre_season_inputs,
        pre_season_recommendations=all_pre_season_recs,
        stage_schedules=stage_schedules,
        blends=all_blends,
        foliar_events=all_foliar_events,
        block_totals=block_totals,
        risk_flags=deduped_risk_flags,
        assumptions=deduped_assumptions,
        outstanding_items=deduped_outstanding,
        shopping_list=shopping_list,
        sources_audit=deduped_sources,
        decision_trace=decision_trace,
    )


# ============================================================
# Helpers
# ============================================================

# Display labels + units per soil parameter — used by the per-block
# 'nutrients vs ideal' visual on the artifact view. Keys must match
# the soil_values column names emitted by the lab (parameters dict on
# SoilSnapshot). Anything not in this map still renders, but with the
# bare key as the label.
_NUTRIENT_DISPLAY: dict[str, tuple[str, str]] = {
    "pH_H2O": ("pH (H₂O)", ""),
    "pH_KCl": ("pH (KCl)", ""),
    "Org_C_pct": ("Organic carbon", "%"),
    "Total_N_pct": ("Total N", "%"),
    "P_Mehlich3": ("Phosphorus (P)", "mg/kg"),
    "P_Bray1": ("Phosphorus (P)", "mg/kg"),
    "P_Olsen": ("Phosphorus (P)", "mg/kg"),
    "P_Truog": ("Phosphorus (P)", "mg/kg"),
    "P_Ambic": ("Phosphorus (P)", "mg/kg"),
    "K": ("Potassium (K)", "mg/kg"),
    "Ca": ("Calcium (Ca)", "mg/kg"),
    "Mg": ("Magnesium (Mg)", "mg/kg"),
    "Na": ("Sodium (Na)", "mg/kg"),
    "S": ("Sulphur (S)", "mg/kg"),
    "Zn": ("Zinc (Zn)", "mg/kg"),
    "B": ("Boron (B)", "mg/kg"),
    "Mn": ("Manganese (Mn)", "mg/kg"),
    "Fe": ("Iron (Fe)", "mg/kg"),
    "Cu": ("Copper (Cu)", "mg/kg"),
    "CEC": ("CEC", "cmol/kg"),
    "Ca_pct_BS": ("Ca base saturation", "%"),
    "Mg_pct_BS": ("Mg base saturation", "%"),
    "K_pct_BS": ("K base saturation", "%"),
    "Na_pct_BS": ("Na base saturation", "%"),
}


def _classify_status(value: float, low_max: float, optimal_max: float) -> str:
    """Bucket a parameter into low / ok / high relative to the
    sufficiency band. low_max is the upper bound of 'low' (i.e. the
    start of the optimal range), optimal_max is the upper bound of the
    optimal range. Anything below low_max is low; above optimal_max is
    high; in between is ok."""
    if value < low_max:
        return "low"
    if value > optimal_max:
        return "high"
    return "ok"


# SASRI / FAS Truog extraction reports nutrient concentrations in mg/L
# (volumetric extract) rather than the mass-based mg/kg used by Mehlich-
# 3, Bray-1, Olsen, Bemlab Ambic etc. The threshold tables are stored
# without unit annotations because within a method they're internally
# consistent — what changes is the LABEL on the rendered report. This
# pattern matches lab_method strings that come from FAS / SASRI reports
# so the renderer prints "mg/L" for Truog samples.
_TRUOG_LAB_PATTERNS = ("truog", "sasri", "fas")


def _is_truog_method(lab_method: Optional[str]) -> bool:
    if not lab_method:
        return False
    method = lab_method.lower()
    return any(p in method for p in _TRUOG_LAB_PATTERNS)


def _unit_for_parameter(param: str, lab_method: Optional[str]) -> str:
    """Return the display unit for a soil parameter given the lab
    method. SASRI / FAS Truog samples report soil-extractable mg/L;
    everyone else reports mg/kg. Structural parameters (CEC,
    base-saturation %) keep their own units regardless of method.
    """
    label_unit = _NUTRIENT_DISPLAY.get(param, (param, ""))[1]
    if not label_unit or label_unit == "%" or label_unit == "cmol/kg":
        return label_unit
    # mg/kg-class units flip to mg/L on a SASRI/FAS Truog report.
    if label_unit == "mg/kg" and _is_truog_method(lab_method):
        return "mg/L"
    return label_unit


def _build_nutrient_status(
    soil_parameters: dict[str, float],
    sufficiency_rows: list[dict],
    param_map_rows: list[dict],
    lab_method: Optional[str] = None,
) -> list[NutrientStatusEntry]:
    """Build the 'nutrients vs ideal' rows for one block's snapshot.

    Iterates the block's soil_parameters and emits one entry per
    parameter that has a sufficiency band in the catalog. Skips
    parameters without bands (e.g. ratio columns, anything purely
    diagnostic) — those surface via factor_findings instead.

    param_map_rows is consulted as a fallback when a soil column name
    doesn't directly match a sufficiency row's parameter (e.g. when
    the lab names it `P_Mehlich3` but sufficiency keys it as `P`).

    `lab_method` drives the display unit. SASRI / FAS Truog reports use
    mg/L for soil extracts (volumetric method); everyone else uses
    mg/kg. Numbers stay as the lab reported them — no conversion
    between methods because the extraction efficiencies aren't
    interchangeable.
    """
    if not soil_parameters or not sufficiency_rows:
        return []

    from app.services.soil_canonicaliser import canonicalise_parameter_name

    # Index by canonical name on both sides so labels that differ in
    # unit suffix or wording ("K", "K (exchangeable)", "Potassium")
    # collapse to the same key — otherwise an override row keyed
    # differently from its lab counterpart silently fails to match.
    suff_by_param: dict[str, dict] = {}
    for r in sufficiency_rows:
        key = r.get("parameter")
        if isinstance(key, str):
            suff_by_param[canonicalise_parameter_name(key)] = r
    nutrient_by_soil_param: dict[str, str] = {}
    for r in param_map_rows:
        sp = r.get("soil_parameter") or r.get("parameter")
        nut = r.get("nutrient")
        if isinstance(sp, str) and isinstance(nut, str):
            nutrient_by_soil_param[canonicalise_parameter_name(sp)] = canonicalise_parameter_name(nut)

    entries: list[NutrientStatusEntry] = []
    seen_keys: set[str] = set()
    for soil_param, raw_value in soil_parameters.items():
        if raw_value is None or not isinstance(raw_value, (int, float)):
            continue
        value = float(raw_value)
        canonical_param = canonicalise_parameter_name(soil_param)
        # Direct match → use the soil parameter's own row. Otherwise
        # try the catalog mapping (e.g. P_Mehlich3 → P).
        suff = suff_by_param.get(canonical_param)
        if not suff:
            mapped = nutrient_by_soil_param.get(canonical_param)
            if mapped:
                suff = suff_by_param.get(mapped)
        if not suff:
            continue
        try:
            low_max = float(suff["low_max"])
            optimal_max = float(suff["optimal_max"])
        except (KeyError, TypeError, ValueError):
            continue
        # Avoid emitting two rows for the same nutrient (e.g. when both
        # the soil column and its mapped nutrient match — the soil
        # column wins because it's what the lab actually reported).
        key = f"{soil_param}|{low_max}|{optimal_max}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        label, _ = _NUTRIENT_DISPLAY.get(soil_param, (soil_param, ""))
        unit = _unit_for_parameter(soil_param, lab_method)
        chart_min, chart_max = _resolve_chart_bounds(suff, value, low_max, optimal_max)
        entries.append(NutrientStatusEntry(
            parameter=soil_param,
            nutrient_label=label,
            value=round(value, 2),
            optimal_low=low_max,
            optimal_high=optimal_max,
            unit=unit or None,
            status=_classify_status(value, low_max, optimal_max),
            chart_min=chart_min,
            chart_max=chart_max,
        ))
    # Stable ordering — macros first, then secondary, then micros, then
    # everything else. Mirrors how an agronomist scans a soil report.
    macro_order = [
        "pH_H2O", "pH_KCl",
        "P_Mehlich3", "P_Bray1", "P_Olsen", "P_Truog", "P_Ambic",
        "K", "Ca", "Mg",
        "S", "Na",
        "Zn", "B", "Mn", "Fe", "Cu",
        "Org_C_pct", "Total_N_pct", "CEC",
        "Ca_pct_BS", "Mg_pct_BS", "K_pct_BS", "Na_pct_BS",
    ]
    rank = {p: i for i, p in enumerate(macro_order)}
    entries.sort(key=lambda e: rank.get(e.parameter, len(rank) + 1))
    return entries


def _resolve_chart_bounds(
    suff_row: dict,
    value: float,
    low_max: float,
    optimal_max: float,
) -> tuple[Optional[float], Optional[float]]:
    """Decide the bar's min/max so the optimal band reads as a
    proportional slice rather than a hairline. Prefer explicit
    display_min/display_max columns when present; otherwise pad the
    optimal range by 25% on either side, but always include the
    block's actual value so a critical-low or critical-high reading
    is visible on the bar.
    """
    explicit_min = suff_row.get("display_min")
    explicit_max = suff_row.get("display_max")
    try:
        cmin = float(explicit_min) if explicit_min is not None else None
    except (TypeError, ValueError):
        cmin = None
    try:
        cmax = float(explicit_max) if explicit_max is not None else None
    except (TypeError, ValueError):
        cmax = None
    if cmin is None or cmax is None:
        span = max(optimal_max - low_max, 1.0)
        if cmin is None:
            cmin = max(0.0, low_max - span * 0.5)
        if cmax is None:
            cmax = optimal_max + span * 0.5
    if value < cmin:
        cmin = max(0.0, value - max(value * 0.1, 1.0))
    if value > cmax:
        cmax = value + max(value * 0.1, 1.0)
    return cmin, cmax


def _uses_fertigation(avail: MethodAvailability) -> bool:
    return any(k.name.startswith("LIQUID_") for k in avail.available_kinds())


def _trigger_kind_summary(events: list[FoliarEvent]) -> str:
    kinds: dict[str, int] = {}
    for e in events:
        kinds[e.trigger_kind] = kinds.get(e.trigger_kind, 0) + 1
    return ", ".join(f"{v} {k}" for k, v in kinds.items())


def _build_stage_schedule(
    block_id: str, planting_date: date, harvest_date: Optional[date],
    stage_count: int, stage_names: list[str],
) -> StageSchedule:
    """Even-split timeline from planting to harvest."""
    total_days = 180  # default 6 months
    if harvest_date:
        total_days = (harvest_date - planting_date).days
    per_stage_days = max(7, total_days // stage_count)

    windows: list[StageWindow] = []
    for idx in range(stage_count):
        week_start = (idx * per_stage_days) // 7 + 1
        week_end = ((idx + 1) * per_stage_days) // 7
        date_start = planting_date + timedelta(days=idx * per_stage_days)
        date_end = planting_date + timedelta(days=(idx + 1) * per_stage_days - 1)
        windows.append(StageWindow(
            stage_number=idx + 1,
            stage_name=stage_names[idx] if idx < len(stage_names) else f"stage_{idx+1}",
            week_start=week_start,
            week_end=week_end,
            date_start=date_start,
            date_end=date_end,
            events=max(1, per_stage_days // 7),  # ~weekly
        ))

    return StageSchedule(
        block_id=block_id,
        planting_date=planting_date,
        harvest_date=harvest_date,
        stages=windows,
    )


def _default_season_label(planting_date: date) -> str:
    """Autumn/Winter/Spring/Summer SA label from planting date."""
    m = planting_date.month
    if m in (3, 4, 5):
        season = "Autumn"
    elif m in (6, 7, 8):
        season = "Winter"
    elif m in (9, 10, 11):
        season = "Spring"
    else:
        season = "Summer"
    return f"{season} {planting_date.year}"


def _infer_data_completeness(inputs: OrchestratorInput) -> DataCompleteness:
    # Cheap heuristic — can be refined in later Phase 2 iteration
    has_full_soil = any(
        len(b.soil_parameters) >= 10 for b in inputs.blocks
    )
    if inputs.has_recent_leaf_analysis and has_full_soil:
        level = "high"
    elif has_full_soil:
        level = "standard"
    else:
        level = "minimum"
    return DataCompleteness(
        level=level,
        has_crop_area_yield=True,
        has_ph_and_texture=any("pH" in str(k) for b in inputs.blocks for k in b.soil_parameters),
        has_full_soil_analysis=has_full_soil,
        has_leaf_analysis=inputs.has_recent_leaf_analysis,
        has_method_availability=True,
    )


def _dedup_sources(sources: list[SourceCitation]) -> list[SourceCitation]:
    seen = set()
    result = []
    for s in sources:
        key = (s.source_id, s.section or "")
        if key not in seen:
            seen.add(key)
            result.append(s)
    return result


def _dedup_outstanding(items: list[OutstandingItem]) -> list[OutstandingItem]:
    """Cluster A and cluster B often emit the same OutstandingItem (e.g.
    'irrigation water test' fires per-fertigation-block). De-dup by the
    item + why_it_matters tuple so the agronomist sees each unique
    action once. Preserve first-seen order.
    """
    seen = set()
    result = []
    for item in items:
        key = (item.item, item.why_it_matters)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _dedup_risk_flags(flags: list[RiskFlag]) -> list[RiskFlag]:
    """Same rationale as OutstandingItem dedup — per-block fan-out
    produces identical RiskFlags. Dedup by (message, severity).
    """
    seen = set()
    result = []
    for f in flags:
        key = (f.message, f.severity)
        if key not in seen:
            seen.add(key)
            result.append(f)
    return result


def _dedup_assumptions(assumptions: list[Assumption]) -> list[Assumption]:
    """Dedup per-block duplicates by (field, assumed_value). Keep the
    first occurrence to preserve the most-specific provenance."""
    seen = set()
    result = []
    for a in assumptions:
        key = (a.field, a.assumed_value)
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result


def _parse_quantity(raw: Optional[str]) -> tuple[float, str]:
    """Parse a quantity string like '233 kg' or '976380 L' → (233.0, 'kg').

    Returns (0.0, 'kg') on anything it can't parse cleanly — the caller
    then drops the row from the shopping list, which is safer than
    bogus totals.
    """
    if not raw:
        return 0.0, "kg"
    # Strip any thousands separators or spaces before the unit
    s = raw.strip().replace(",", "")
    # Find where the unit starts — first non-digit/non-dot after a digit
    num = ""
    i = 0
    while i < len(s) and (s[i].isdigit() or s[i] == "." or s[i] == "-"):
        num += s[i]
        i += 1
    unit = s[i:].strip() or "kg"
    # Normalise common unit forms
    unit_lower = unit.lower()
    if unit_lower in {"l", "litres", "litre", "liters", "liter"}:
        unit = "L"
    elif unit_lower in {"kg", "kgs", "kilograms", "kilogram"}:
        unit = "kg"
    try:
        return float(num), unit
    except ValueError:
        return 0.0, unit or "kg"


def _blend_category(blend: Blend) -> str:
    """Map the blend's method to a shopping-list category label.

    Matches ShoppingListEntry.category docstring values:
    'drip' | 'drench' | 'foliar' | 'dry_blend'.
    """
    kind = str(getattr(blend.method, "kind", "")).lower()
    if "liquid" in kind or "fertigation" in kind:
        return "drip"
    if "drench" in kind:
        return "drench"
    if "dry" in kind or "broadcast" in kind or "band" in kind or "side_dress" in kind:
        return "dry_blend"
    return "dry_blend"  # safe default for unknown dry kinds


def _build_shopping_list(
    blends: list[Blend],
    foliar_events: list[FoliarEvent],
) -> list[ShoppingListEntry]:
    """Roll per-product quantities across all blends + foliar events
    into a season-total shopping list, keyed per block.

    Grouping key: (category, product, analysis) so a product used by
    both fertigation and dry applications stays distinct.
    """
    buckets: dict[tuple[str, str, str], dict] = {}

    for blend in blends:
        category = _blend_category(blend)
        for part in blend.raw_products:
            qty, unit = _parse_quantity(part.batch_total)
            if qty <= 0:
                continue
            key = (category, part.product, part.analysis)
            row = buckets.setdefault(key, {
                "unit": unit,
                "per_block": {},
                "total": 0.0,
            })
            row["total"] += qty
            row["per_block"][blend.block_id] = (
                row["per_block"].get(blend.block_id, 0.0) + qty
            )

    for ev in foliar_events:
        qty, unit = _parse_quantity(ev.total_for_block)
        if qty <= 0:
            continue
        key = ("foliar", ev.product, ev.analysis)
        row = buckets.setdefault(key, {
            "unit": unit,
            "per_block": {},
            "total": 0.0,
        })
        row["total"] += qty
        row["per_block"][ev.block_id] = (
            row["per_block"].get(ev.block_id, 0.0) + qty
        )

    return [
        ShoppingListEntry(
            category=cat,
            product=product,
            analysis=analysis,
            total_per_block={bid: round(q, 1) for bid, q in row["per_block"].items()},
            total_overall=round(row["total"], 1),
            unit=row["unit"],
        )
        for (cat, product, analysis), row in buckets.items()
    ]
