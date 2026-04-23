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
    DataCompleteness,
    FoliarEvent,
    MethodAvailability,
    OutstandingItem,
    PreSeasonInput,
    PreSeasonRecommendation,
    ProgrammeArtifact,
    ProgrammeHeader,
    ProgrammeState,
    ReplanReason,
    RiskFlag,
    SoilSnapshot,
    SourceCitation,
    StageSchedule,
    StageWindow,
    Tier,
    VariantKey,
)
from app.services.foliar_trigger_engine import trigger_foliar_events
from app.services.method_selector import aggregate_by_method, select_methods
from app.services.pre_season_module import (
    compute_residual_position,
    flag_lost_opportunities,
    recommend_pre_season_actions,
)
from app.services.risk_flag_generator import generate_outstanding_items, generate_risk_flags
from app.services.soil_factor_reasoner import reason_soil_factors
from app.services.stage_splitter import (
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
    assumptions: list[Assumption] = []
    all_risk_flags: list[RiskFlag] = []
    all_outstanding: list[OutstandingItem] = []
    all_foliar_events: list[FoliarEvent] = []
    all_pre_season_recs: list[PreSeasonRecommendation] = []

    # Auto-detect high Al soil across blocks if not overridden
    high_al_soil = inputs.high_al_soil
    soil_factor_reports = {}

    # --------------------------------------------------------
    # Per-block reasoning
    # --------------------------------------------------------
    block_totals: dict[str, dict[str, float]] = {}
    stage_schedules: list[StageSchedule] = []
    updated_pre_season_inputs: list[PreSeasonInput] = []
    soil_snapshots_out: list[SoilSnapshot] = []

    for block in inputs.blocks:
        decision_trace.append(f"Block {block.block_id}: start reasoning")

        # 1. Soil factor reasoner — always runs
        sf_report = reason_soil_factors(
            soil_values=block.soil_parameters,
            crop=inputs.crop,
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

        # 2. Pre-season module — three modes
        months_to_planting = (inputs.planting_date - inputs.build_date).days / 30.44

        # Mode A — recommend
        recs = recommend_pre_season_actions(
            block_id=block.block_id,
            soil_factor_report=sf_report,
            build_date=inputs.build_date,
            planting_date=inputs.planting_date,
            available_materials=inputs.available_materials,
        )
        all_pre_season_recs.extend(recs)
        if recs:
            decision_trace.append(
                f"Block {block.block_id}: Pre-season Mode A — "
                f"{len(recs)} recommendations ({months_to_planting:.1f} mo lead time)"
            )

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

        # 5. Method selector
        method_assignments = select_methods(
            stage_splits=stage_splits,
            method_availability=inputs.method_availability,
            soil_factor_report=sf_report,
            crop_family=get_family(inputs.crop),
        )
        decision_trace.append(
            f"Block {block.block_id}: MethodSelector — {len(method_assignments)} routings"
        )

        # 6. Foliar trigger engine
        foliar_events = trigger_foliar_events(
            block_id=block.block_id,
            crop=inputs.crop,
            planting_date=inputs.planting_date,
            soil_factor_report=sf_report,
            leaf_deficiencies=block.leaf_deficiencies,
            block_area_ha=block.block_area_ha,
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

        # 8. Stage schedule (basic timeline from planting)
        stage_names = [s.stage_name for s in stage_splits]
        schedule = _build_stage_schedule(
            block_id=block.block_id,
            planting_date=inputs.planting_date,
            harvest_date=inputs.expected_harvest_date,
            stage_count=inputs.stage_count,
            stage_names=stage_names,
        )
        stage_schedules.append(schedule)

        # 9. Block totals — assemble from adjusted_targets
        block_totals[block.block_id] = adjusted_targets

        # 10. Soil snapshot for output
        headline = [f.message for f in sf_report.by_severity_at_least("warn")[:3]]
        soil_snapshots_out.append(SoilSnapshot(
            block_id=block.block_id,
            block_name=block.block_name,
            block_area_ha=block.block_area_ha,
            lab_name=block.lab_name,
            lab_method=block.lab_method,
            sample_date=block.sample_date,
            sample_id=block.sample_id,
            parameters=block.soil_parameters,
            headline_signals=headline,
        ))

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

    # Note unimplemented sections transparently
    unshipped_modules = (
        "Blend + Concentrate + ShoppingList sections empty — consolidator, "
        "two-stream packaging, and target-compute-with-provenance modules "
        "not yet shipped (Phase 2 modules 7-10). Downstream renderer should "
        "surface this as 'blend assembly pending' not produce fake numbers."
    )
    decision_trace.append(f"Orchestrator: {unshipped_modules}")

    # Dedup sources_audit by source_id+section
    deduped_sources = _dedup_sources(sources_audit)

    return ProgrammeArtifact(
        header=header,
        soil_snapshots=soil_snapshots_out,
        pre_season_inputs=updated_pre_season_inputs,
        pre_season_recommendations=all_pre_season_recs,
        stage_schedules=stage_schedules,
        blends=[],  # module 8 pending
        foliar_events=all_foliar_events,
        block_totals=block_totals,
        risk_flags=all_risk_flags,
        assumptions=assumptions,
        outstanding_items=all_outstanding,
        shopping_list=[],  # module 8 pending
        sources_audit=deduped_sources,
        decision_trace=decision_trace,
    )


# ============================================================
# Helpers
# ============================================================

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
