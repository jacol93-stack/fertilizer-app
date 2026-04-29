"""Per-parameter trend analysis across multiple soil analyses for one block.

Used by the soil report builder when scope_kind == 'block_with_history'
or the multi-block path with N analyses on at least one block.

Inputs:
  - list of (sample_date, soil_values) tuples sorted ascending by date
  - per-parameter optimal_low / optimal_high band (for direction-of-
    travel: a value moving INTO the band counts as "improving")

Outputs:
  - per-parameter TrendVerdict: improving | stable | declining | uncertain
  - delta (latest − earliest), slope (mg/kg per day), n analyses, span
  - significance: 'significant' | 'minor' | 'none' based on relative
    delta + (when n ≥ 3) slope p-value approximation
  - human-readable headline ("pH (KCl) up from 4.4 → 4.9 over 14 months,
    moving into the 5.0–6.5 band but not yet there")

Significance heuristics (defaults — tune via constants):
  - relative delta ≥ 10 % → significant
  - relative delta 5–10 % → minor
  - relative delta < 5 %  → none
  - For n ≥ 3 with linear-regression p-value < 0.1, escalates one tier
    (so a small but consistent trend across 4+ analyses still surfaces
    as 'minor' rather than 'none').

Direction-of-travel:
  - "improving" when the value moves toward the optimal band
  - "declining" when it moves away
  - "stable" when |relative delta| below significance threshold
  - "uncertain" when no optimal band is known (rare — most params have
    sufficiency entries in the catalog)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# Significance thresholds — defaults, tunable per-call if needed.
SIGNIFICANCE_RELATIVE_DELTA_MAJOR = 0.10  # 10 %
SIGNIFICANCE_RELATIVE_DELTA_MINOR = 0.05  # 5 %
SIGNIFICANCE_LINEAR_P_VALUE = 0.10        # for n ≥ 3 trend escalation


@dataclass
class ParameterTrend:
    """One parameter's trajectory across N analyses."""
    parameter: str
    n_observations: int
    earliest_date: date
    latest_date: date
    earliest_value: float
    latest_value: float
    delta: float                        # latest − earliest
    relative_delta: float               # delta / abs(earliest), 0 when earliest=0
    slope_per_day: float                # linear regression slope (units / day)
    slope_p_value: Optional[float] = None  # only when n ≥ 3
    direction: str = "stable"           # improving | stable | declining | uncertain
    significance: str = "none"          # major | minor | none
    optimal_low: Optional[float] = None
    optimal_high: Optional[float] = None
    in_band_now: Optional[bool] = None  # latest value vs band
    headline: str = ""                  # human-readable one-liner


@dataclass
class BlockTrendReport:
    """Complete trend report for one block over N analyses."""
    block_id: str
    block_name: str
    n_analyses: int
    earliest_date: date
    latest_date: date
    span_days: int
    parameters: list[ParameterTrend] = field(default_factory=list)
    # Surfaces the loudest signals across the parameter list — used by
    # the renderer + Opus prompts. Top three by significance, breaking
    # ties on absolute relative_delta.
    headline_signals: list[str] = field(default_factory=list)


def analyse_block_trends(
    *,
    block_id: str,
    block_name: str,
    timeline: list[tuple[date, dict[str, float]]],
    optimal_bands: Optional[dict[str, tuple[float, float]]] = None,
) -> BlockTrendReport:
    """Compute trend verdicts for every parameter present in ≥ 2 analyses.

    Args:
        block_id: stable block identifier
        block_name: display name
        timeline: list of (sample_date, soil_values) — analyses ordered
            ascending by date. Caller is responsible for sorting + for
            keying soil_values consistently across analyses (the
            soil_canonicaliser handles this upstream of this module).
        optimal_bands: optional {parameter: (low, high)} for direction-
            of-travel verdicts. When absent, direction defaults to
            'uncertain' for parameters without a band.

    Returns:
        BlockTrendReport with one ParameterTrend per parameter that
        appears in ≥ 2 analyses. Parameters in < 2 are skipped (no
        trend possible).
    """
    if len(timeline) < 2:
        return BlockTrendReport(
            block_id=block_id,
            block_name=block_name,
            n_analyses=len(timeline),
            earliest_date=timeline[0][0] if timeline else date.today(),
            latest_date=timeline[-1][0] if timeline else date.today(),
            span_days=0,
        )

    earliest_date = timeline[0][0]
    latest_date = timeline[-1][0]
    span_days = (latest_date - earliest_date).days

    # Pivot: parameter → list of (date, value) observations.
    by_param: dict[str, list[tuple[date, float]]] = {}
    for sample_date, values in timeline:
        for param, value in (values or {}).items():
            if value is None:
                continue
            try:
                v = float(value)
            except (TypeError, ValueError):
                continue
            by_param.setdefault(param, []).append((sample_date, v))

    bands = optimal_bands or {}
    parameter_trends: list[ParameterTrend] = []
    for param, observations in by_param.items():
        if len(observations) < 2:
            continue
        observations.sort(key=lambda x: x[0])
        first_date, first_val = observations[0]
        last_date, last_val = observations[-1]
        delta = last_val - first_val
        rel_delta = delta / abs(first_val) if first_val != 0 else 0.0

        # Linear slope (per day). Use simple OLS — no need for scipy
        # for a 2-10-point series.
        slope = _ols_slope_per_day(observations)
        p_value = (
            _ols_p_value_approx(observations, slope)
            if len(observations) >= 3 else None
        )

        band = bands.get(param)
        opt_low = band[0] if band else None
        opt_high = band[1] if band else None
        in_band = (
            opt_low is not None and opt_high is not None
            and opt_low <= last_val <= opt_high
        )

        direction = _classify_direction(
            first_val=first_val,
            last_val=last_val,
            opt_low=opt_low,
            opt_high=opt_high,
            relative_delta=rel_delta,
        )
        significance = _classify_significance(
            relative_delta=rel_delta,
            p_value=p_value,
        )

        headline = _format_trend_headline(
            param=param,
            first_val=first_val,
            last_val=last_val,
            first_date=first_date,
            last_date=last_date,
            opt_low=opt_low,
            opt_high=opt_high,
            direction=direction,
            significance=significance,
        )

        parameter_trends.append(ParameterTrend(
            parameter=param,
            n_observations=len(observations),
            earliest_date=first_date,
            latest_date=last_date,
            earliest_value=first_val,
            latest_value=last_val,
            delta=round(delta, 3),
            relative_delta=round(rel_delta, 4),
            slope_per_day=round(slope, 6),
            slope_p_value=round(p_value, 4) if p_value is not None else None,
            direction=direction,
            significance=significance,
            optimal_low=opt_low,
            optimal_high=opt_high,
            in_band_now=in_band,
            headline=headline,
        ))

    # Headline signals — pick the loudest. Significance > minor counts;
    # break ties on absolute relative_delta.
    headline_order = {"major": 0, "minor": 1, "none": 2}
    parameter_trends.sort(
        key=lambda t: (
            headline_order.get(t.significance, 3),
            -abs(t.relative_delta),
        )
    )
    top_signals = [
        t.headline for t in parameter_trends
        if t.significance in ("major", "minor")
    ][:3]

    return BlockTrendReport(
        block_id=block_id,
        block_name=block_name,
        n_analyses=len(timeline),
        earliest_date=earliest_date,
        latest_date=latest_date,
        span_days=span_days,
        parameters=parameter_trends,
        headline_signals=top_signals,
    )


# ============================================================
# Helpers
# ============================================================


def _ols_slope_per_day(
    observations: list[tuple[date, float]],
) -> float:
    """Ordinary-least-squares slope of value vs days-from-first.

    Days-from-first chosen as the x-axis so slope reads as units / day,
    interpretable independent of which decade the analyses span.
    """
    if not observations:
        return 0.0
    base_date = observations[0][0]
    xs = [(d - base_date).days for d, _ in observations]
    ys = [v for _, v in observations]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return num / den


def _ols_p_value_approx(
    observations: list[tuple[date, float]],
    slope: float,
) -> Optional[float]:
    """Approximate two-sided p-value for the OLS slope coefficient.

    Uses a t-statistic against a Student-t distribution with (n-2) df.
    Pure-stdlib approximation — no scipy dependency. Good enough for
    "is this trend significant?" thresholding; not for publication.

    Returns None when n < 3 (no df) or when residual variance is zero
    (perfect fit — caller should treat as 'definitely significant').
    """
    n = len(observations)
    if n < 3:
        return None
    base_date = observations[0][0]
    xs = [(d - base_date).days for d, _ in observations]
    ys = [v for _, v in observations]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    intercept = mean_y - slope * mean_x
    residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
    rss = sum(r * r for r in residuals)
    if rss <= 0:
        # Perfect linear fit — slope is "definitely significant" in the
        # absence of noise. Return a tiny p-value as the signal.
        return 0.0
    df = n - 2
    sigma_sq = rss / df
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        return None
    se_slope = (sigma_sq / sxx) ** 0.5
    if se_slope == 0:
        return 0.0
    t_stat = abs(slope / se_slope)
    # Two-sided p-value via Student-t survival approximation. Use the
    # Wilson-Hilferty approximation: t-distribution CDF approximated by
    # a transformed normal. For small df this is loose but ranks
    # correctly, which is all we need for major / minor / none binning.
    # p ≈ 2 * (1 - Φ(t * sqrt(df / (df + t²)))) is a common rough form.
    z_equiv = t_stat * (df / (df + t_stat * t_stat)) ** 0.5
    p = 2.0 * (1.0 - _standard_normal_cdf(z_equiv))
    return max(0.0, min(1.0, p))


def _standard_normal_cdf(z: float) -> float:
    """Pure-stdlib N(0,1) CDF via the Abramowitz-Stegun approximation."""
    import math
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _classify_direction(
    *,
    first_val: float,
    last_val: float,
    opt_low: Optional[float],
    opt_high: Optional[float],
    relative_delta: float,
) -> str:
    """Improving / stable / declining / uncertain.

    With an optimal band:
      - inside-to-inside, significant change → direction by distance-
        from-midpoint (toward midpoint = improving, away = declining).
        Catches "still in band but drifting toward the edge" cases that
        agronomists treat as a decline-in-the-making.
      - outside-to-inside → improving
      - inside-to-outside → declining
      - both outside     → distance-to-band comparison
    Without a band we report 'uncertain' (UI surfaces this as
    "+/− X.X%, target unknown").
    """
    if abs(relative_delta) < SIGNIFICANCE_RELATIVE_DELTA_MINOR:
        return "stable"
    if opt_low is None or opt_high is None:
        return "uncertain"
    first_in = opt_low <= first_val <= opt_high
    last_in = opt_low <= last_val <= opt_high
    if first_in and last_in:
        midpoint = (opt_low + opt_high) / 2.0
        first_distance = abs(first_val - midpoint)
        last_distance = abs(last_val - midpoint)
        if last_distance < first_distance:
            return "improving"
        if last_distance > first_distance:
            return "declining"
        return "stable"
    if last_in and not first_in:
        return "improving"
    if first_in and not last_in:
        return "declining"
    # Both outside — direction depends on whether we moved closer or
    # further from the band.
    first_distance = (
        opt_low - first_val if first_val < opt_low
        else first_val - opt_high
    )
    last_distance = (
        opt_low - last_val if last_val < opt_low
        else last_val - opt_high
    )
    if last_distance < first_distance:
        return "improving"
    if last_distance > first_distance:
        return "declining"
    return "stable"


def _classify_significance(
    *,
    relative_delta: float,
    p_value: Optional[float],
) -> str:
    abs_delta = abs(relative_delta)
    if abs_delta >= SIGNIFICANCE_RELATIVE_DELTA_MAJOR:
        return "major"
    if abs_delta >= SIGNIFICANCE_RELATIVE_DELTA_MINOR:
        return "minor"
    # Sub-threshold relative delta — but n ≥ 3 trend with a small
    # p-value still merits surfacing as 'minor'. Catches consistent
    # small-step trends that single endpoint comparison would miss.
    if p_value is not None and p_value < SIGNIFICANCE_LINEAR_P_VALUE:
        return "minor"
    return "none"


def _format_trend_headline(
    *,
    param: str,
    first_val: float,
    last_val: float,
    first_date: date,
    last_date: date,
    opt_low: Optional[float],
    opt_high: Optional[float],
    direction: str,
    significance: str,
) -> str:
    """Produce a one-liner the renderer can drop into the trend report
    section. Uses agronomic phrasing — "up from X to Y, into the band"
    rather than "delta Δ = ...". The optimiser stays out of this string
    (no rates, no products, no recommendations)."""
    arrow = (
        "up from" if last_val > first_val
        else "down from" if last_val < first_val
        else "unchanged at"
    )
    span_months = max(1, (last_date - first_date).days // 30)
    direction_phrase = {
        "improving": ", trending into the optimal band",
        "declining": ", trending out of the optimal band",
        "stable": "",
        "uncertain": "",
    }.get(direction, "")
    band_phrase = ""
    if opt_low is not None and opt_high is not None:
        band_phrase = f" (target {opt_low:g}–{opt_high:g})"
    sig_phrase = "" if significance == "major" else (
        " (minor change)" if significance == "minor" else " (within noise)"
    )
    if last_val == first_val:
        return f"{param} unchanged at {first_val:g} over {span_months} months{band_phrase}."
    return (
        f"{param} {arrow} {first_val:g} to {last_val:g} over {span_months} months"
        f"{band_phrase}{direction_phrase}{sig_phrase}."
    )
