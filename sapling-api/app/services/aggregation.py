"""Shared aggregation primitive for multi-sample soil / leaf analyses.

One function, `aggregate_samples`, is used at two levels:

* Level 1 — combining several physical samples taken from one block into a
  single `soil_analyses` row (with component retention).
* Level 2 — combining per-block nutrient-requirement vectors across the
  blocks grouped into one programme blend.

The primitive is pure: no DB access, no side-effects. Callers decide how
to persist the result.

Design rules (see project_multi_sample_aggregation memory):

* Weighted mean is area-weighted when every sample supplies a positive
  weight; otherwise the primitive falls back to equal weights for the
  *whole* aggregation and records `weight_strategy='equal'` in the stats.
  We never mix modes inside one call — that produces subtle bias.
* Missing values (None, NaN) are ignored for that parameter only; they
  don't poison the whole aggregation.
* Outliers are flagged, never silently dropped. Agronomist judgement wins.
* CV (coefficient of variation) is reported in percent; None when the
  mean is zero or the sample count is too low to be meaningful.
* A single-sample input is valid and returns `composition_method='single'`
  with no outlier flags.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Iterable, Sequence


# Below this sample count, CV and outlier detection are not reported —
# statistics on n<3 are noise.
_MIN_N_FOR_VARIANCE_STATS = 3
_DEFAULT_OUTLIER_SIGMA = 2.0
# Consistent with normal-distribution conversion: σ ≈ 1.4826 * MAD.
_MAD_TO_SIGMA = 1.4826


def _detect_outliers_mad(
    values: list[float],
    sigma_threshold: float,
) -> list[int]:
    """Flag outliers using median absolute deviation (MAD), which is
    robust to the very points it's trying to detect. Naive z-score
    using the mean fails because the outlier itself pulls the mean and
    std toward itself.

    Returns indices into `values`. Returns [] if MAD is zero (all
    samples identical to the median, or tied; no meaningful spread).
    """
    if len(values) < _MIN_N_FOR_VARIANCE_STATS:
        return []
    median = statistics.median(values)
    deviations = [abs(x - median) for x in values]
    mad = statistics.median(deviations)
    if mad == 0:
        return []
    threshold = sigma_threshold * _MAD_TO_SIGMA * mad
    return [i for i, x in enumerate(values) if abs(x - median) > threshold]


@dataclass
class ParameterStats:
    n: int
    mean: float
    variance: float
    cv_pct: float | None
    outlier_sample_indices: list[int] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "mean": self.mean,
            "variance": self.variance,
            "cv_pct": self.cv_pct,
            "outlier_sample_indices": list(self.outlier_sample_indices),
        }


@dataclass
class AggregationResult:
    values: dict[str, float]
    stats: dict[str, ParameterStats]
    weight_strategy: str           # 'area_weighted' | 'equal'
    composition_method: str        # matches soil_analyses.composition_method values
    replicate_count: int

    def stats_as_dict(self) -> dict:
        """Return stats in the shape the DB column expects."""
        out: dict = {"weight_strategy": self.weight_strategy}
        for param, s in self.stats.items():
            out[param] = s.as_dict()
        return out


def _is_valid_number(x) -> bool:
    return x is not None and isinstance(x, (int, float)) and not math.isnan(x)


def _resolve_weights(
    samples: Sequence[dict],
    weights: Sequence[float] | None,
) -> tuple[list[float], str]:
    """Return (weights, strategy). Falls back to equal weights if any
    supplied weight is missing or non-positive, so the whole call uses
    one consistent weighting mode."""
    n = len(samples)
    if weights is None:
        return [1.0] * n, "equal"
    if len(weights) != n:
        raise ValueError(
            f"weights length {len(weights)} does not match samples length {n}"
        )
    if any(w is None or w <= 0 or (isinstance(w, float) and math.isnan(w)) for w in weights):
        return [1.0] * n, "equal"
    return [float(w) for w in weights], "area_weighted"


def _collect_parameters(samples: Iterable[dict]) -> list[str]:
    """Union of parameter keys across samples, stable order (first-seen)."""
    seen: dict[str, None] = {}
    for s in samples:
        values = s.get("values", s) if isinstance(s, dict) else {}
        for k in values.keys():
            if k not in seen:
                seen[k] = None
    return list(seen.keys())


def _sample_values(sample: dict) -> dict:
    """Support both {'values': {...}} and flat {...} shapes."""
    if "values" in sample and isinstance(sample["values"], dict):
        return sample["values"]
    return sample


def aggregate_samples(
    samples: Sequence[dict],
    weights: Sequence[float] | None = None,
    *,
    outlier_sigma: float = _DEFAULT_OUTLIER_SIGMA,
) -> AggregationResult:
    """Combine a set of samples into one composite record with stats.

    Args:
        samples: each either `{parameter: number}` or
            `{'values': {parameter: number}, ...}`. The second shape lets
            callers attach metadata (location, depth, weight) without
            polluting the values map.
        weights: optional per-sample weights (e.g. zone area in ha). Must
            be the same length as `samples`. If any weight is missing or
            non-positive, the whole aggregation falls back to equal
            weights — we never mix modes inside one call.
        outlier_sigma: z-score threshold for flagging a sample as an
            outlier on a given parameter.

    Returns:
        AggregationResult with weighted means, per-parameter stats,
        the weight strategy that was actually used, and a
        `composition_method` suitable for the `soil_analyses` column.
    """
    if not samples:
        raise ValueError("aggregate_samples requires at least one sample")

    n = len(samples)
    resolved_weights, weight_strategy = _resolve_weights(samples, weights)
    parameters = _collect_parameters(samples)

    values: dict[str, float] = {}
    stats: dict[str, ParameterStats] = {}

    for param in parameters:
        xs: list[float] = []
        ws: list[float] = []
        idx_map: list[int] = []   # sample indices that contributed
        for i, sample in enumerate(samples):
            raw = _sample_values(sample).get(param)
            if not _is_valid_number(raw):
                continue
            xs.append(float(raw))
            ws.append(resolved_weights[i])
            idx_map.append(i)

        if not xs:
            continue

        total_weight = sum(ws)
        if total_weight <= 0:
            continue
        mean = sum(x * w for x, w in zip(xs, ws)) / total_weight
        # Weighted population variance (n=len(xs)), bias-corrected would
        # need Σw/(Σw - Σw²/Σw), which is overkill for our n. Population
        # variance is what CV practitioners report.
        variance = sum(w * (x - mean) ** 2 for x, w in zip(xs, ws)) / total_weight

        cv_pct: float | None = None
        outliers: list[int] = []
        if len(xs) >= _MIN_N_FOR_VARIANCE_STATS and mean != 0:
            std = math.sqrt(variance)
            cv_pct = abs(std / mean) * 100.0
            # MAD-based outlier detection is robust to the outlier's own
            # distortion of mean/std. Map local indices back to the
            # caller's sample indices.
            local_flags = _detect_outliers_mad(xs, outlier_sigma)
            outliers = [idx_map[j] for j in local_flags]

        values[param] = mean
        stats[param] = ParameterStats(
            n=len(xs),
            mean=mean,
            variance=variance,
            cv_pct=cv_pct,
            outlier_sample_indices=outliers,
        )

    if n == 1:
        composition_method = "single"
    elif weight_strategy == "area_weighted":
        composition_method = "composite_area_weighted"
    else:
        composition_method = "composite_mean"

    return AggregationResult(
        values=values,
        stats=stats,
        weight_strategy=weight_strategy,
        composition_method=composition_method,
        replicate_count=n,
    )
