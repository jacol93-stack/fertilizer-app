"""Quick Analysis pipeline — interpretation-only, no fertilizer recommendation.

Runs the upper half of the v2 orchestrator (target computation, soil
factor reasoning, foliar trigger detection) and emits a ProgrammeArtifact
with empty blends/shopping_list/stage_schedules. The agronomist gets a
read of "where the soil/leaf is, what's at risk, what stage you're in
right now, what foliars would address current gaps" without any blend
recommendation. Per the user's framing: programme builder minus the
fertilizer recommendation.

This is the engine half of /quick-analysis, replacing the legacy
/api/soil/run + /api/leaf/classify pair which only ran
calculate_nutrient_targets and missed: tree-age scaling, soil-factor
reasoning, stage-peak foliar triggers, and current-stage detection.

Reuses the same modules the v2 programme builder uses, so any future
seed migration / engine improvement automatically improves both
surfaces. No code duplication.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from app.models.confidence import DataCompleteness, Tier
from app.models.programme_artifact import (
    Assumption,
    FoliarEvent,
    MethodAvailability,
    ProgrammeArtifact,
    ProgrammeHeader,
    ReplanReason,
    RiskFlag,
    SoilSnapshot,
    SourceCitation,
)
from app.models.variants import VariantKey
from app.services.foliar_trigger_engine import trigger_foliar_events
from app.services.soil_factor_reasoner import reason_soil_factors
from app.services.target_computation import (
    SoilCatalog,
    compute_season_targets,
)


# ============================================================
# Per-block input + output
# ============================================================

class AnalysisBlockInput:
    """One block's interpretation input. Lighter than orchestrator's
    BlockInput — no pre_season_inputs, no method_availability needed."""

    def __init__(
        self,
        *,
        block_id: str,
        block_name: str,
        block_area_ha: float,
        soil_parameters: dict[str, float],
        leaf_values: Optional[dict[str, float]] = None,
        yield_target_per_ha: Optional[float] = None,
        tree_age: Optional[int] = None,
        pop_per_ha: Optional[float] = None,
        lab_name: Optional[str] = None,
        lab_method: Optional[str] = None,
        sample_date: Optional[date] = None,
        sample_id: Optional[str] = None,
    ):
        self.block_id = block_id
        self.block_name = block_name
        self.block_area_ha = block_area_ha
        self.soil_parameters = soil_parameters or {}
        self.leaf_values = leaf_values
        self.yield_target_per_ha = yield_target_per_ha
        self.tree_age = tree_age
        self.pop_per_ha = pop_per_ha
        self.lab_name = lab_name
        self.lab_method = lab_method
        self.sample_date = sample_date
        self.sample_id = sample_id


# ============================================================
# Stage-now detection
# ============================================================

def _detect_current_stage(
    crop_growth_stage_rows: list[dict],
    crop: str,
    planting_date: Optional[date],
    today: date,
) -> Optional[dict]:
    """Find which crop_growth_stages row covers `today` for this crop.

    Looks up the crop (with parent-variant fallback) and matches today's
    month against the stage's [month_start, month_end] window. Returns
    the row dict (so caller can read stage_name + n_pct/p_pct/k_pct
    peak demands) or None if no match.

    Wrap-around windows (e.g. month_start=11, month_end=2) are handled
    so a Jan reading correctly maps to a Nov-Feb stage.
    """
    if not crop_growth_stage_rows or not planting_date:
        return None

    rows = [r for r in crop_growth_stage_rows if (r.get("crop") or "") == crop]
    if not rows and "(" in crop:
        # Variant fallback — Citrus (Valencia) → Citrus
        parent = crop.split("(")[0].strip()
        rows = [r for r in crop_growth_stage_rows if (r.get("crop") or "") == parent]
    if not rows:
        return None

    m = today.month
    for r in rows:
        try:
            ms = int(r.get("month_start") or 0)
            me = int(r.get("month_end") or 0)
        except (TypeError, ValueError):
            continue
        if ms <= me:
            in_window = ms <= m <= me
        else:
            # Wraps year boundary, e.g. Nov-Feb (11-2)
            in_window = m >= ms or m <= me
        if in_window:
            return r
    return None


# ============================================================
# Main pipeline
# ============================================================

def analyse_blocks(
    *,
    crop: str,
    blocks: list[AnalysisBlockInput],
    catalog: SoilCatalog,
    crop_growth_stage_rows: Optional[list[dict]] = None,
    planting_date: Optional[date] = None,
    prepared_for: str,
    client_name: str = "",
    farm_name: str = "",
    season: Optional[str] = None,
    water_values: Optional[dict] = None,
    today: Optional[date] = None,
) -> ProgrammeArtifact:
    """Build an interpretation-only ProgrammeArtifact.

    Runs target_computation + soil_factor_reasoner + foliar_trigger_engine
    per block, plus current-stage detection if planting_date + crop_growth
    rows are provided. Emits a ProgrammeArtifact with empty blends /
    shopping_list / stage_schedules so the existing ArtifactView component
    renders an interpretation-only report.

    `today` is parameterised so tests can pin it; defaults to date.today().
    """
    today = today or date.today()
    # Default planting_date to today when caller didn't supply one — this
    # makes the report season-agnostic (no stage timing computed) but
    # keeps the artifact's required field populated.
    eff_planting_date = planting_date or today

    decision_trace: list[str] = []
    soil_snapshots: list[SoilSnapshot] = []
    all_foliar_events: list[FoliarEvent] = []
    all_risk_flags: list[RiskFlag] = []
    all_assumptions: list[Assumption] = []
    block_totals: dict[str, dict[str, float]] = {}
    tiers_seen: list[int] = []

    # ─── Per-block reasoning ─────────────────────────────────────────
    for block in blocks:
        decision_trace.append(f"Block {block.block_id}: start analysis")

        # 1. Soil-factor reasoning — produces findings + computed ratios
        sf_report = reason_soil_factors(
            soil_values=block.soil_parameters,
            crop=crop,
            water_values=water_values,
        )
        decision_trace.append(
            f"Block {block.block_id}: SoilFactorReasoner — "
            f"{len(sf_report.findings)} findings"
        )

        # 2. Season targets (with age + density scaling baked in by
        #    target_computation since Phase A 2026-04-26). When no
        #    yield_target is supplied, target_computation falls back to
        #    crop_requirements.default_yield (full-bearing potential)
        #    and emits an Assumption — combined with tree_age +
        #    perennial_age_factors this gives the right rates for young
        #    perennials without forcing the agronomist to supply a yield.
        tc_result = compute_season_targets(
            crop=crop,
            yield_target=block.yield_target_per_ha,
            soil_values=block.soil_parameters,
            catalog=catalog,
            block_pop_per_ha=block.pop_per_ha,
            tree_age=block.tree_age,
            block_name=block.block_name,
        )
        targets = tc_result.targets
        target_assumptions = list(tc_result.assumptions)
        block_totals[block.block_id] = targets
        if tc_result.worst_tier is not None:
            tiers_seen.append(tc_result.worst_tier.value)
        decision_trace.append(
            f"Block {block.block_id}: target_computation — "
            f"{len(targets)} nutrients, worst tier {tc_result.worst_tier}"
        )

        # 3. Foliar triggers — stage-peak demand + soil availability gaps
        foliar = trigger_foliar_events(
            block_id=block.block_id,
            crop=crop,
            planting_date=eff_planting_date,
            soil_factor_report=sf_report,
            leaf_deficiencies=block.leaf_values,
            block_area_ha=block.block_area_ha,
        )
        all_foliar_events.extend(foliar)
        if foliar:
            decision_trace.append(
                f"Block {block.block_id}: foliar_trigger_engine — "
                f"{len(foliar)} events"
            )

        # 4. Soil-factor findings → RiskFlags (warn + critical only).
        # RiskFlag.severity is a plain string field accepting
        # 'info'|'watch'|'warn'|'critical'.
        for finding in sf_report.by_severity_at_least("warn"):
            all_risk_flags.append(RiskFlag(
                kind=finding.kind,
                severity=finding.severity,
                affected_block_ids=[block.block_id],
                message=finding.message,
                action=finding.recommended_action,
                source=SourceCitation(
                    source_id=finding.source_id,
                    section=finding.source_section,
                    tier=Tier(finding.tier) if isinstance(finding.tier, int) else Tier.IMPLEMENTER_CONVENTION,
                ),
            ))
        all_assumptions.extend(target_assumptions)

        # 5. Snapshot — engine-derived ratios + headline signals
        headline = [f.message for f in sf_report.by_severity_at_least("warn")[:3]]
        computed_ratios = {
            k: float(v) for k, v in (sf_report.computed or {}).items()
            if isinstance(v, (int, float))
        }
        soil_snapshots.append(SoilSnapshot(
            block_id=block.block_id,
            block_name=block.block_name,
            block_area_ha=block.block_area_ha,
            lab_name=block.lab_name,
            lab_method=block.lab_method,
            sample_date=block.sample_date,
            sample_id=block.sample_id,
            parameters=block.soil_parameters,
            computed_ratios=computed_ratios,
            headline_signals=headline,
        ))

    # ─── Stage-now detection (one shot for the whole report) ─────────
    current_stage_row = _detect_current_stage(
        crop_growth_stage_rows or [],
        crop=crop,
        planting_date=planting_date,
        today=today,
    )
    if current_stage_row:
        all_assumptions.append(Assumption(
            field="current_growth_stage",
            assumed_value=current_stage_row.get("stage_name") or "?",
            override_guidance=(
                f"Today ({today.isoformat()}) falls inside the "
                f"'{current_stage_row.get('stage_name')}' stage window "
                f"for {crop} (months {current_stage_row.get('month_start')}–"
                f"{current_stage_row.get('month_end')}). Stage-peak demand "
                f"split: N {current_stage_row.get('n_pct', 0)}%, "
                f"P {current_stage_row.get('p_pct', 0)}%, "
                f"K {current_stage_row.get('k_pct', 0)}%."
            ),
            source=SourceCitation(
                source_id="CROP_GROWTH_STAGES",
                section="crop_growth_stages table",
                tier=Tier.SA_INDUSTRY_BODY,
            ),
            tier=Tier.SA_INDUSTRY_BODY,
        ))
        decision_trace.append(
            f"Current stage detected: {current_stage_row.get('stage_name')} "
            f"(today month {today.month})"
        )
    elif planting_date:
        decision_trace.append(
            f"No growth_stages row matched current month {today.month} "
            f"for {crop} — stage-now detection skipped"
        )

    # ─── Confidence + tier roll-up ───────────────────────────────────
    worst_tier = Tier(max(tiers_seen)) if tiers_seen else None
    # Heuristic: HIGH if we got soil + leaf + targets; MEDIUM if soil-only
    # with targets; MINIMUM otherwise.
    has_targets = any(s.block_id in block_totals for s in soil_snapshots)
    has_leaf = any(b.leaf_values for b in blocks)
    if has_targets and has_leaf:
        completeness_level = "high"
    elif has_targets:
        completeness_level = "standard"
    else:
        completeness_level = "minimum"

    # ─── Header — minimal for an analysis report ─────────────────────
    header = ProgrammeHeader(
        client_name=client_name or prepared_for,
        farm_name=farm_name,
        prepared_for=prepared_for,
        prepared_date=today,
        crop=crop,
        variant_key=VariantKey(canonical_crop=crop),
        season=season or f"Analysis · {today.isoformat()}",
        planting_date=eff_planting_date,
        data_completeness=DataCompleteness(
            level=completeness_level,
            has_full_soil_analysis=any(s.parameters for s in soil_snapshots),
            has_leaf_analysis=has_leaf,
        ),
        method_availability=MethodAvailability(),  # all-defaults — interpretation-only doesn't pick methods
        replan_reason=ReplanReason.FIRST_PASS,
    )

    # ─── Compose artifact (blends / stage_schedules / shopping_list
    #    intentionally empty — this is interpretation-only) ──────────
    artifact = ProgrammeArtifact(
        header=header,
        soil_snapshots=soil_snapshots,
        pre_season_inputs=[],
        pre_season_recommendations=[],
        stage_schedules=[],     # empty — no nutrient distribution computed
        blends=[],              # empty — no fertilizer recommendation
        foliar_events=all_foliar_events,
        block_totals=block_totals,
        risk_flags=_dedup_risk_flags(all_risk_flags),
        assumptions=_dedup_assumptions(all_assumptions),
        outstanding_items=[],
        shopping_list=[],       # empty — derived from blends
        sources_audit=[],       # populated by renderer via traversal
        overall_confidence=None,
        decision_trace=decision_trace,
        created_at=today.isoformat(),
        updated_at=today.isoformat(),
    )
    # worst_tier is captured in the assumptions/source_audit traversal
    # the renderer does at display time; no header field for it.
    return artifact


# ============================================================
# Helpers — match orchestrator's dedup pattern
# ============================================================

def _dedup_risk_flags(items: list[RiskFlag]) -> list[RiskFlag]:
    seen: set[tuple] = set()
    out: list[RiskFlag] = []
    for r in items:
        key = (r.kind, r.severity, r.message, tuple(sorted(r.affected_block_ids)))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _dedup_assumptions(items: list[Assumption]) -> list[Assumption]:
    seen: set[tuple] = set()
    out: list[Assumption] = []
    for a in items:
        key = (a.field, a.assumed_value)
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out
