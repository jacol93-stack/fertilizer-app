"""Soil Report Builder — composes a SoilReportArtifact from blocks + analyses.

Three scope kinds:
  * single_block        — 1 block, 1 analysis — deepest single-snapshot dive
  * block_with_history  — 1 block, N analyses — adds trend report
  * multi_block         — N blocks (each with 1 or N analyses) — adds
                          per-block trends (where applicable) + holistic
                          summary across blocks

Reuses every existing engine path:
  - soil_factor_reasoner.reason_soil_factors  → factor_findings
  - programme_builder_orchestrator._build_nutrient_status → range-bar rows
  - soil_canonicaliser.normalise_soil_values  → unit-stripped keys
  - soil_trend_analyzer.analyse_block_trends  → per-block trend verdicts

Output mirrors ProgrammeArtifact's soil section closely so the PDF
renderer reuses the same templates / CSS / context-building helpers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional

from app.models import FactorFindingOut, NutrientStatusEntry, SoilSnapshot
from app.services.soil_engine import normalise_soil_values
from app.services.soil_factor_reasoner import reason_soil_factors
from app.services.soil_trend_analyzer import (
    BlockTrendReport,
    analyse_block_trends,
)


# ============================================================
# Artifact shape — persisted as JSONB on soil_reports.report_payload
# ============================================================


@dataclass
class SoilReportHeader:
    title: str
    scope_kind: str
    client_name: Optional[str] = None
    farm_name: Optional[str] = None
    generated_on: Optional[date] = None
    block_count: int = 0
    analysis_count: int = 0
    earliest_sample_date: Optional[date] = None
    latest_sample_date: Optional[date] = None


@dataclass
class SoilReportArtifact:
    """Complete per-block + cross-block soil report."""
    header: SoilReportHeader
    # Latest analysis per block — the "current" snapshot the render shows
    # alongside any trend section.
    soil_snapshots: list[SoilSnapshot] = field(default_factory=list)
    # Per-block trend reports — only blocks with ≥ 2 analyses contribute.
    trend_reports: list[BlockTrendReport] = field(default_factory=list)
    # Cross-block patterns. Populated for scope_kind == 'multi_block'.
    holistic_signals: list[str] = field(default_factory=list)
    # Top three loudest signals across the whole report.
    headline_signals: list[str] = field(default_factory=list)
    # Audit trail.
    block_ids: list[str] = field(default_factory=list)
    analysis_ids: list[str] = field(default_factory=list)
    decision_trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSONB-friendly dict."""
        return {
            "header": _dataclass_to_dict(self.header),
            "soil_snapshots": [s.model_dump(mode="json") for s in self.soil_snapshots],
            "trend_reports": [_dataclass_to_dict(t) for t in self.trend_reports],
            "holistic_signals": list(self.holistic_signals),
            "headline_signals": list(self.headline_signals),
            "block_ids": list(self.block_ids),
            "analysis_ids": list(self.analysis_ids),
            "decision_trace": list(self.decision_trace),
        }


def _dataclass_to_dict(obj: Any) -> Any:
    """Recursive dataclass → dict serialiser; handles dates and nested
    dataclasses without depending on dataclasses.asdict (which doesn't
    handle nested non-dataclass objects gracefully)."""
    from dataclasses import is_dataclass, fields
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_dataclass_to_dict(v) for v in obj]
    if is_dataclass(obj):
        return {f.name: _dataclass_to_dict(getattr(obj, f.name)) for f in fields(obj)}
    return str(obj)


# ============================================================
# Inputs
# ============================================================


@dataclass
class BlockAnalysesInput:
    """One block + its chronological list of analyses to include.

    The builder picks the LAST entry as the "current" snapshot and uses
    the full list (when len > 1) for trend analysis.
    """
    block_id: str
    block_name: str
    block_area_ha: Optional[float]
    crop: str
    analyses: list["AnalysisInput"]


@dataclass
class AnalysisInput:
    analysis_id: str
    sample_date: Optional[date]
    lab_name: Optional[str]
    lab_method: Optional[str]
    soil_parameters: dict[str, float]


@dataclass
class SoilReportBuilderInputs:
    """Top-level inputs to the builder."""
    title: str
    client_name: Optional[str]
    farm_name: Optional[str]
    blocks: list[BlockAnalysesInput]
    sufficiency_rows: list[dict] = field(default_factory=list)
    param_map_rows: list[dict] = field(default_factory=list)
    water_values: Optional[dict] = None


# ============================================================
# Public entry point
# ============================================================


def build_soil_report(inputs: SoilReportBuilderInputs) -> SoilReportArtifact:
    """Compose a SoilReportArtifact from the blocks + analyses passed in.

    Detects scope_kind automatically:
      - 1 block, 1 analysis  → 'single_block'
      - 1 block, N analyses  → 'block_with_history'
      - N blocks (any count) → 'multi_block'
    """
    if not inputs.blocks:
        raise ValueError("Cannot build soil report with no blocks")
    for block in inputs.blocks:
        if not block.analyses:
            raise ValueError(
                f"Block {block.block_name} has no analyses — every block "
                f"in the input must have ≥ 1 analysis."
            )

    n_blocks = len(inputs.blocks)
    max_analyses_per_block = max(len(b.analyses) for b in inputs.blocks)
    if n_blocks == 1 and max_analyses_per_block == 1:
        scope_kind = "single_block"
    elif n_blocks == 1 and max_analyses_per_block > 1:
        scope_kind = "block_with_history"
    else:
        scope_kind = "multi_block"

    decision_trace: list[str] = [
        f"SoilReportBuilder: scope={scope_kind}, blocks={n_blocks}, "
        f"max analyses/block={max_analyses_per_block}",
    ]

    # ----- Per-block: latest snapshot + (optional) trend ---------------
    snapshots: list[SoilSnapshot] = []
    trend_reports: list[BlockTrendReport] = []
    optimal_bands = _bands_from_sufficiency(inputs.sufficiency_rows)
    earliest = None
    latest = None
    all_analysis_ids: list[str] = []

    for block in inputs.blocks:
        # Sort the block's analyses by sample_date ascending. Analyses
        # without a date go to the front; this preserves stability.
        sorted_analyses = sorted(
            block.analyses,
            key=lambda a: a.sample_date or date.min,
        )
        latest_analysis = sorted_analyses[-1]
        all_analysis_ids.extend(a.analysis_id for a in sorted_analyses)
        if sorted_analyses[0].sample_date:
            earliest = (
                sorted_analyses[0].sample_date if earliest is None
                else min(earliest, sorted_analyses[0].sample_date)
            )
        if latest_analysis.sample_date:
            latest = (
                latest_analysis.sample_date if latest is None
                else max(latest, latest_analysis.sample_date)
            )

        # Emit one snapshot per analysis on the block. Earlier passes
        # only persisted the latest snapshot, so a 4-analysis history
        # report only showed full data for one date even though all 4
        # were on the timeline. The trend section (deltas / direction
        # of travel) handles the cross-time comparison; per-snapshot
        # detail tables let the agronomist see the actual lab numbers
        # at each point. Block_id is suffixed with the analysis date
        # so renderer dedupe keys remain unique across snapshots of
        # the same block.
        for analysis in sorted_analyses:
            sample_label = (
                analysis.sample_date.isoformat()
                if analysis.sample_date else analysis.analysis_id[:8]
            )
            # Single-analysis blocks keep their original block_id
            # (preserves backwards-compat). Multi-analysis blocks get a
            # composite id so cluster/block lookups still work but each
            # snapshot is uniquely keyed for the renderer.
            if len(sorted_analyses) > 1:
                snapshot_block_id = f"{block.block_id}__{sample_label}"
            else:
                snapshot_block_id = block.block_id
            snapshot = _build_snapshot_for_analysis(
                block_id=snapshot_block_id,
                block_name=block.block_name,
                block_area_ha=block.block_area_ha,
                crop=block.crop,
                analysis=analysis,
                sufficiency_rows=inputs.sufficiency_rows,
                param_map_rows=inputs.param_map_rows,
                water_values=inputs.water_values,
            )
            snapshots.append(snapshot)
            decision_trace.append(
                f"Block {block.block_name}: snapshot built from {analysis.analysis_id} "
                f"({len(snapshot.factor_findings)} findings)"
            )

        # 2. Trend report when ≥ 2 analyses
        if len(sorted_analyses) >= 2:
            timeline: list[tuple[date, dict[str, float]]] = []
            for a in sorted_analyses:
                if a.sample_date is None:
                    continue
                normalised = normalise_soil_values(a.soil_parameters or {})
                timeline.append((a.sample_date, normalised))
            if len(timeline) >= 2:
                trend = analyse_block_trends(
                    block_id=block.block_id,
                    block_name=block.block_name,
                    timeline=timeline,
                    optimal_bands=optimal_bands,
                )
                trend_reports.append(trend)
                decision_trace.append(
                    f"Block {block.block_name}: trend report built from "
                    f"{trend.n_analyses} analyses spanning {trend.span_days} days, "
                    f"{len(trend.parameters)} parameters traced, "
                    f"{len(trend.headline_signals)} headline signals"
                )

    # ----- Holistic summary (multi-block only) -------------------------
    holistic_signals: list[str] = []
    if scope_kind == "multi_block":
        holistic_signals = _build_holistic_signals(snapshots, trend_reports)
        decision_trace.append(
            f"Holistic summary: {len(holistic_signals)} cross-block signals"
        )

    # ----- Headline signals — top of the report ------------------------
    headline_signals = _select_headline_signals(
        snapshots=snapshots,
        trend_reports=trend_reports,
        holistic_signals=holistic_signals,
    )

    header = SoilReportHeader(
        title=inputs.title,
        scope_kind=scope_kind,
        client_name=inputs.client_name,
        farm_name=inputs.farm_name,
        generated_on=date.today(),
        block_count=n_blocks,
        analysis_count=len(all_analysis_ids),
        earliest_sample_date=earliest,
        latest_sample_date=latest,
    )

    return SoilReportArtifact(
        header=header,
        soil_snapshots=snapshots,
        trend_reports=trend_reports,
        holistic_signals=holistic_signals,
        headline_signals=headline_signals,
        block_ids=[b.block_id for b in inputs.blocks],
        analysis_ids=all_analysis_ids,
        decision_trace=decision_trace,
    )


# ============================================================
# Per-block snapshot
# ============================================================


def _build_snapshot_for_analysis(
    *,
    block_id: str,
    block_name: str,
    block_area_ha: Optional[float],
    crop: str,
    analysis: AnalysisInput,
    sufficiency_rows: list[dict],
    param_map_rows: list[dict],
    water_values: Optional[dict],
) -> SoilSnapshot:
    """Run the soil-factor reasoner + nutrient-status builder against
    one analysis. Returns a SoilSnapshot identical in shape to what the
    programme builder produces, so the same renderer code reads it.
    """
    sf_report = reason_soil_factors(
        soil_values=analysis.soil_parameters or {},
        crop=crop,
        water_values=water_values,
    )
    headline = [f.message for f in sf_report.by_severity_at_least("warn")[:3]]
    computed_ratios = {
        k: float(v) for k, v in (sf_report.computed or {}).items()
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
        for f in sf_report.findings
    ]
    # Build the range-bar rows. Reuse the orchestrator's helper instead
    # of duplicating logic — it's the single source of truth for the
    # "nutrients vs ideal" visual.
    from app.services.programme_builder_orchestrator import _build_nutrient_status
    normalised = normalise_soil_values(analysis.soil_parameters or {})
    nutrient_status = _build_nutrient_status(
        soil_parameters=normalised,
        sufficiency_rows=sufficiency_rows or [],
        param_map_rows=param_map_rows or [],
        lab_method=analysis.lab_method,
    )
    return SoilSnapshot(
        block_id=block_id,
        block_name=block_name,
        block_area_ha=block_area_ha or 0.0,
        lab_name=analysis.lab_name,
        lab_method=analysis.lab_method,
        sample_date=analysis.sample_date,
        sample_id=analysis.analysis_id,
        parameters=analysis.soil_parameters or {},
        computed_ratios=computed_ratios,
        factor_findings=factor_findings,
        nutrient_status=nutrient_status,
        headline_signals=headline,
    )


# ============================================================
# Cross-block holistic summary
# ============================================================


def _build_holistic_signals(
    snapshots: list[SoilSnapshot],
    trend_reports: list[BlockTrendReport],
) -> list[str]:
    """Surface cross-block patterns in plain prose. Examples:
       'Five of seven blocks read acid (pH (KCl) below 5.0) — lime
        priority across the farm.'
       'Three blocks trending Mg-deficient against the band over the
        last two seasons; rest stable.'

    Heuristics scan factor_findings + range-bar statuses + trend
    verdicts. Output is short, agronomic, prose. Used as both renderer
    bullets and Opus prompt context.
    """
    signals: list[str] = []
    n = len(snapshots)
    if n < 2:
        return signals

    # ----- pH-low pattern across blocks -----
    ph_low_blocks = [
        s.block_name for s in snapshots
        if any(
            f.parameter == "pH (KCl)" and f.severity in ("warn", "critical")
            for f in (s.factor_findings or [])
        )
    ]
    if len(ph_low_blocks) >= 2:
        signals.append(
            f"{_count_phrase(len(ph_low_blocks), n)} of the blocks read acid "
            f"on pH — {_join_with_ellipsis(ph_low_blocks)}. Lime is a farm-wide "
            f"action, not a one-block correction."
        )

    # ----- pH-high pattern across blocks -----
    ph_high_blocks = [
        s.block_name for s in snapshots
        if any(
            f.parameter == "pH (KCl)_high" and f.severity in ("warn", "critical")
            for f in (s.factor_findings or [])
        )
    ]
    if len(ph_high_blocks) >= 2:
        signals.append(
            f"{_count_phrase(len(ph_high_blocks), n)} of the blocks read alkaline — "
            f"{_join_with_ellipsis(ph_high_blocks)}. Sulphur or acidifying N "
            f"sources are the farm-wide lever."
        )

    # ----- Ca:Mg-low pattern -----
    ca_mg_blocks = [
        s.block_name for s in snapshots
        if any(
            f.parameter == "Ca:Mg" and f.severity in ("warn", "critical")
            for f in (s.factor_findings or [])
        )
    ]
    if len(ca_mg_blocks) >= 2:
        signals.append(
            f"{_count_phrase(len(ca_mg_blocks), n)} of the blocks "
            f"({_join_with_ellipsis(ca_mg_blocks)}) carry Ca:Mg below the 3:1 "
            f"target with pH already in band — a gypsum call across those blocks."
        )

    # ----- Sodicity (SAR / soil_ESP_pct) cluster -----
    sodic_blocks = [
        s.block_name for s in snapshots
        if any(
            f.parameter in ("SAR", "soil_ESP_pct")
            and f.severity in ("warn", "critical")
            for f in (s.factor_findings or [])
        )
    ]
    if len(sodic_blocks) >= 2:
        signals.append(
            f"Sodicity flagged on {_count_phrase(len(sodic_blocks), n)} of the blocks "
            f"({_join_with_ellipsis(sodic_blocks)}). Worth re-checking irrigation "
            f"water source — soil-side gypsum alone may not hold the line."
        )

    # ----- Aggregate trend direction across blocks -----
    if trend_reports:
        improving = sum(
            1 for t in trend_reports
            if any(p.direction == "improving" and p.significance != "none" for p in t.parameters)
        )
        declining = sum(
            1 for t in trend_reports
            if any(p.direction == "declining" and p.significance != "none" for p in t.parameters)
        )
        if improving > 0 and improving > declining * 2:
            signals.append(
                f"{_count_phrase(improving, len(trend_reports))} of the blocks with "
                f"history are trending in the right direction — last cycle's corrections "
                f"are reflecting in the soil."
            )
        if declining > 0 and declining > improving * 2:
            signals.append(
                f"{_count_phrase(declining, len(trend_reports))} of the blocks with "
                f"history are trending out of band on at least one parameter — worth a "
                f"closer look at the per-block trend section."
            )

    return signals


def _count_phrase(n: int, total: int) -> str:
    """Render '5 of 7' etc. Plural-friendly."""
    return f"{n} of {total}"


def _join_with_ellipsis(names: list[str], cap: int = 5) -> str:
    """Format a list of block names: 'A, B, C' or 'A, B, C and 4 more'."""
    if len(names) <= cap:
        if len(names) <= 1:
            return ", ".join(names)
        return ", ".join(names[:-1]) + " and " + names[-1]
    head = ", ".join(names[:cap])
    rest = len(names) - cap
    return f"{head} and {rest} more"


# ============================================================
# Headline signals (top of the report)
# ============================================================


def _select_headline_signals(
    *,
    snapshots: list[SoilSnapshot],
    trend_reports: list[BlockTrendReport],
    holistic_signals: list[str],
) -> list[str]:
    """Pick three signals to surface at the report cover. Priority:
       1. Holistic cross-block patterns (most informative when present)
       2. Highest-severity factor findings across all snapshots
       3. Major-significance trend headlines
    """
    out: list[str] = []
    if holistic_signals:
        out.extend(holistic_signals[:2])

    severity_rank = {"critical": 0, "warn": 1, "watch": 2, "info": 3, "fyi": 4}
    findings_with_severity: list[tuple[int, str]] = []
    for s in snapshots:
        for f in (s.factor_findings or []):
            findings_with_severity.append((
                severity_rank.get(f.severity, 99),
                f"{s.block_name}: {f.message}",
            ))
    findings_with_severity.sort(key=lambda x: x[0])
    for _, msg in findings_with_severity:
        if msg not in out:
            out.append(msg)
        if len(out) >= 3:
            break

    if len(out) < 3:
        for t in trend_reports:
            for p in t.parameters:
                if p.significance == "major":
                    line = f"{t.block_name}: {p.headline}"
                    if line not in out:
                        out.append(line)
                if len(out) >= 3:
                    break
            if len(out) >= 3:
                break

    return out[:3]


# ============================================================
# Helpers
# ============================================================


def _bands_from_sufficiency(rows: list[dict]) -> dict[str, tuple[float, float]]:
    """Convert sufficiency rows ({parameter, low_max, optimal_max, ...})
    into the {param: (low, high)} shape the trend analyzer wants."""
    out: dict[str, tuple[float, float]] = {}
    for r in rows or []:
        param = r.get("parameter")
        low = r.get("low_max")
        high = r.get("optimal_max")
        if not param or low is None or high is None:
            continue
        try:
            out[param] = (float(low), float(high))
        except (TypeError, ValueError):
            continue
    return out
