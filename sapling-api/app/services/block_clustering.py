"""Phase 3 — Block clustering + area-weighted aggregation for v2.

Mirrors the legacy programme_engine behavior: blocks with similar NPK
ratios are grouped, and per-nutrient targets + soil parameters are
combined with area weights. A CV-based heterogeneity report flags
groups that span too-dissimilar blocks — in which case the agronomist
should consider splitting them.

Pure module — no DB, no FastAPI, no Pydantic dependencies beyond what
the shared `aggregation` primitive needs.

Thresholds are the same Wilding (1985) / Mulla & Schepers (1997) bands
the legacy engine uses, keyed by oxide form (P2O5, K2O) since v2
targets use oxide notation.

Design notes:
* First-fit clustering matches legacy — order-dependent but stable for a
  given block ordering, and the margin is small enough that pathological
  ordering effects are rare.
* Single-block clusters are valid. If len(clusters) == len(blocks),
  aggregation is a no-op and the orchestrator sees the same input it
  would have seen without clustering.
* Clusters are labelled 'A', 'B', 'C', … (26 max is fine; we're not
  handling thousand-block programmes here).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.services.aggregation import aggregate_samples


# Same bands as legacy programme_engine, translated to v2's oxide form.
# CV is a ratio — converting P → P2O5 scales both mean and std by 2.291,
# so the percentage thresholds port directly.
HETEROGENEITY_THRESHOLDS: dict[str, dict[str, float]] = {
    "P2O5": {"warn": 35.0, "split": 50.0},
    "K2O":  {"warn": 25.0, "split": 35.0},
    "N":    {"warn": 30.0, "split": 50.0},
    "Ca":   {"warn": 30.0, "split": 50.0},
    "Mg":   {"warn": 30.0, "split": 50.0},
    "S":    {"warn": 30.0, "split": 50.0},
}
_FALLBACK_THRESHOLD = {"warn": 30.0, "split": 50.0}
HETEROGENEITY_CITATION = "Wilding (1985) via Mulla & Schepers (1997)"


def classify_heterogeneity(nutrient: str, cv_pct: Optional[float]) -> str:
    """Return 'ok' | 'warn' | 'split' for a per-nutrient CV across blocks."""
    if cv_pct is None:
        return "ok"
    thresholds = HETEROGENEITY_THRESHOLDS.get(nutrient, _FALLBACK_THRESHOLD)
    if cv_pct >= thresholds["split"]:
        return "split"
    if cv_pct >= thresholds["warn"]:
        return "warn"
    return "ok"


@dataclass
class HeterogeneityWarning:
    nutrient: str
    cv_pct: Optional[float]
    level: str           # 'warn' | 'split'
    threshold_pct: float


@dataclass
class HeterogeneityReport:
    per_nutrient: dict[str, dict] = field(default_factory=dict)
    warnings: list[HeterogeneityWarning] = field(default_factory=list)
    any_warn: bool = False
    any_split: bool = False
    citation: str = HETEROGENEITY_CITATION


@dataclass
class ClusterAggregate:
    """One cluster's aggregated view — what the orchestrator sees instead
    of the raw blocks."""
    cluster_id: str                       # 'A', 'B', ...
    block_ids: list[str]
    block_names: list[str]
    total_area_ha: float
    aggregated_targets: dict[str, float]  # oxide form (N, P2O5, K2O, Ca, Mg, S)
    aggregated_soil_parameters: dict[str, float]
    weight_strategy: str                   # 'area_weighted' | 'equal'
    heterogeneity: HeterogeneityReport


def _npk_ratio(targets: dict[str, float]) -> tuple[float, float, float, float]:
    """Return (n_prop, p_prop, k_prop, total). Handles missing keys.

    Uses v2's oxide form (P2O5, K2O) since that's what compute_season_targets
    emits. Pure proportions, so it doesn't matter that the absolute scale
    differs from elemental form.
    """
    n = float(targets.get("N", 0.0) or 0.0)
    p = float(targets.get("P2O5", 0.0) or 0.0)
    k = float(targets.get("K2O", 0.0) or 0.0)
    total = n + p + k
    if total < 0.01:
        return 0.0, 0.0, 0.0, 0.0
    return n / total, p / total, k / total, total


def cluster_blocks_by_npk(
    blocks: list[Any],
    margin: float = 0.25,
    assignments: Optional[dict[str, str]] = None,
) -> list[list[Any]]:
    """First-fit grouping: blocks with total L1 NPK-ratio distance below
    `margin` share a cluster.

    `blocks` is any iterable of objects with `.season_targets: dict` —
    typed as `list[Any]` so this module doesn't import BlockInput
    (circular with the orchestrator).

    Default margin 0.25 — same recipe shared, per-block rates differ;
    farmer mixes one batch and applies different volumes per ha. Tighter
    margins fragment the programme into more recipes than a farmer can
    track. Caller can override (BuildProgrammeRequest.cluster_margin) when
    a particular farm needs tighter or looser grouping.

    `assignments` lets the caller pin specific blocks to a named cluster
    (block_id → cluster_id, e.g. {"Blok A4": "A", "Blok 788": "A"}).
    Pinned blocks are placed in their assigned cluster verbatim — the
    NPK-distance check is skipped for them. Unpinned blocks then run the
    normal first-fit against the existing groups (pinned + earlier
    unpinned). Cluster IDs in `assignments` are honored for downstream
    naming via `cluster_and_aggregate`.

    Blocks with degenerate totals (<0.01 kg/ha combined NPK) become
    their own singleton cluster — nothing useful to cluster on — unless
    they carry an explicit assignment.
    """
    if not blocks:
        return []

    assignments = assignments or {}

    # Pre-seed pinned groups in the order their first block appears.
    # Preserves the cluster-id ordering caller wanted.
    pinned_groups: dict[str, list[Any]] = {}
    pinned_order: list[str] = []
    auto_groups: list[list[Any]] = []

    for block in blocks:
        block_id = str(getattr(block, "block_id", ""))
        if block_id in assignments:
            cid = assignments[block_id]
            if cid not in pinned_groups:
                pinned_groups[cid] = []
                pinned_order.append(cid)
            pinned_groups[cid].append(block)
            continue

        # Unpinned — run normal first-fit across pinned + auto groups.
        targets = getattr(block, "season_targets", None) or {}
        n_prop, p_prop, k_prop, total = _npk_ratio(targets)
        if total < 0.01:
            auto_groups.append([block])
            continue

        placed = False
        # Try pinned first (caller's intent wins on ties), then auto.
        for g in list(pinned_groups.values()) + auto_groups:
            ref = next(
                (b for b in g if getattr(b, "season_targets", None)),
                None,
            )
            if ref is None:
                continue
            ref_targets = ref.season_targets or {}
            rn, rp, rk, rtotal = _npk_ratio(ref_targets)
            if rtotal < 0.01:
                continue
            diff = abs(n_prop - rn) + abs(p_prop - rp) + abs(k_prop - rk)
            if diff < margin:
                g.append(block)
                placed = True
                break
        if not placed:
            auto_groups.append([block])

    return [pinned_groups[cid] for cid in pinned_order] + auto_groups


def _build_samples_and_weights(
    cluster: list[Any],
    field_name: str,
) -> tuple[list[dict], list[Optional[float]]]:
    """Extract per-block `{parameter: value}` samples + `area_ha` weights
    for a named dict field on each block. Skips blocks whose field is
    missing or empty.
    """
    samples: list[dict] = []
    weights: list[Optional[float]] = []
    for block in cluster:
        vec = getattr(block, field_name, None) or {}
        if not vec:
            continue
        numeric = {
            k: float(v) for k, v in vec.items()
            if isinstance(v, (int, float))
        }
        if not numeric:
            continue
        samples.append({"values": numeric})
        weights.append(getattr(block, "block_area_ha", None))
    return samples, weights


def _resolve_use_area_weighting(weights: list[Optional[float]]) -> bool:
    return bool(weights) and all(w is not None and w > 0 for w in weights)


def aggregate_cluster(
    cluster: list[Any],
    cluster_id: str,
) -> ClusterAggregate:
    """Area-weighted aggregation across a cluster's blocks — targets and
    soil parameters both — plus heterogeneity report on targets.

    Blocks missing area_ha force equal-weight fallback for the whole
    cluster (we never mix modes within one call — same rule as legacy).
    """
    if not cluster:
        raise ValueError("aggregate_cluster requires at least one block")

    block_ids = [str(getattr(b, "block_id", "?")) for b in cluster]
    block_names = [str(getattr(b, "block_name", "?")) for b in cluster]
    total_area_ha = sum(
        float(getattr(b, "block_area_ha", 0.0) or 0.0) for b in cluster
    )

    # Targets
    target_samples, target_weights = _build_samples_and_weights(cluster, "season_targets")
    use_area_for_targets = _resolve_use_area_weighting(target_weights)
    if target_samples:
        target_agg = aggregate_samples(
            target_samples,
            weights=[float(w) for w in target_weights] if use_area_for_targets else None,
        )
        aggregated_targets = {k: float(v) for k, v in target_agg.values.items()}
        weight_strategy = target_agg.weight_strategy
    else:
        aggregated_targets = {}
        weight_strategy = "equal"
        target_agg = None

    # Soil parameters
    soil_samples, soil_weights = _build_samples_and_weights(cluster, "soil_parameters")
    use_area_for_soil = _resolve_use_area_weighting(soil_weights)
    if soil_samples:
        soil_agg = aggregate_samples(
            soil_samples,
            weights=[float(w) for w in soil_weights] if use_area_for_soil else None,
        )
        aggregated_soil_parameters = {k: float(v) for k, v in soil_agg.values.items()}
    else:
        aggregated_soil_parameters = {}

    # Heterogeneity — drives the "should we split?" decision. Only on
    # targets, not soil params, because the consequence the agronomist
    # acts on is "different target → different blend", not "different
    # soil → different story".
    report = HeterogeneityReport()
    if target_agg is not None:
        for nutrient, stats in target_agg.stats.items():
            level = classify_heterogeneity(nutrient, stats.cv_pct)
            report.per_nutrient[nutrient] = {
                "cv_pct": round(stats.cv_pct, 1) if stats.cv_pct is not None else None,
                "n": stats.n,
                "level": level,
            }
            if level in ("warn", "split"):
                thresholds = HETEROGENEITY_THRESHOLDS.get(nutrient, _FALLBACK_THRESHOLD)
                report.warnings.append(HeterogeneityWarning(
                    nutrient=nutrient,
                    cv_pct=round(stats.cv_pct, 1) if stats.cv_pct is not None else None,
                    level=level,
                    threshold_pct=thresholds[level],
                ))
                if level == "split":
                    report.any_split = True
                else:
                    report.any_warn = True
        # any_warn rolls up splits too — mirrors legacy behavior
        if report.any_split:
            report.any_warn = True

    return ClusterAggregate(
        cluster_id=cluster_id,
        block_ids=block_ids,
        block_names=block_names,
        total_area_ha=round(total_area_ha, 3),
        aggregated_targets=aggregated_targets,
        aggregated_soil_parameters=aggregated_soil_parameters,
        weight_strategy=weight_strategy,
        heterogeneity=report,
    )


def cluster_and_aggregate(
    blocks: list[Any],
    margin: float = 0.25,
    assignments: Optional[dict[str, str]] = None,
) -> list[ClusterAggregate]:
    """End-to-end: cluster by NPK ratio, then aggregate each cluster.

    `assignments` (block_id → cluster_id) pins specific blocks to named
    clusters; unassigned blocks fall through to first-fit. Pinned cluster
    IDs are preserved as-is in the output (e.g. "A", "B"); auto-clusters
    are numbered after them with the next available letter.
    """
    assignments = assignments or {}
    groups = cluster_blocks_by_npk(blocks, margin=margin, assignments=assignments)

    # Pinned cluster IDs come from assignments; auto-clusters get the
    # next letter that isn't already used.
    pinned_ids: list[str] = []
    seen: set[str] = set()
    for cid in assignments.values():
        if cid not in seen:
            pinned_ids.append(cid)
            seen.add(cid)

    used: set[str] = set(pinned_ids)
    out: list[ClusterAggregate] = []
    pinned_count = len(pinned_ids)
    next_auto_idx = 0
    for i, g in enumerate(groups):
        if i < pinned_count:
            cid = pinned_ids[i]
        else:
            # Skip letters already pinned
            while True:
                candidate = chr(65 + next_auto_idx)
                next_auto_idx += 1
                if candidate not in used:
                    cid = candidate
                    used.add(cid)
                    break
        out.append(aggregate_cluster(g, cluster_id=cid))
    return out
