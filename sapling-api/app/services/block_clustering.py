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


# Soil-state thresholds for cluster refinement. The auto-clusterer
# splits a group when the within-group spread on any of these crosses
# the listed bound — a single averaged programme over blocks at pH 4.5
# and pH 7.5 is the wrong recipe for both extremes regardless of
# whether the season-target CV is calm. pH has its own range-based
# rule because half-unit pH differences map to ~3× H+ ion concentration
# differences, which CV-on-absolute-pH-numbers underplays.
_PH_SPLIT_RANGE = 0.8  # pH range max-min above which a cluster should split
_SATURATION_SPLIT_CV_PCT = 30.0  # CV % on Ca/Mg/K saturation above which to split
_SOIL_HETERO_KEYS = (
    # absolute soil values used for CV-based check
    "K", "Ca", "Mg",
    # saturation % values when present
    "Ca Saturation", "Mg Saturation", "K Saturation",
)


def _soil_param_value(block: Any, key: str) -> Optional[float]:
    """Read a soil parameter from a block's `soil_parameters` dict,
    tolerating canonicalised + unit-suffixed keys both."""
    sp = getattr(block, "soil_parameters", None) or {}
    if not sp:
        return None
    # Try canonical key first, then unit-suffixed variants seen in the wild
    for candidate in (key, f"{key} (mg/kg)", f"{key} (%)", f"{key}_pct"):
        v = sp.get(candidate)
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def _ph_value(block: Any) -> Optional[float]:
    sp = getattr(block, "soil_parameters", None) or {}
    if not sp:
        return None
    for candidate in ("pH (KCl)", "pH (H2O)", "pH"):
        v = sp.get(candidate)
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def _cv_pct(values: list[float]) -> Optional[float]:
    """Coefficient of variation as a percentage, robust to small samples."""
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    if mean == 0:
        return None
    var = sum((v - mean) ** 2 for v in values) / len(values)
    sd = var ** 0.5
    return abs(sd / mean) * 100.0


def _soil_state_split_signal(
    group: list[Any],
) -> tuple[Optional[str], list[float]]:
    """Detect whether a group should be split on soil-state heterogeneity.

    Returns (split_key, sort_values) — split_key is the parameter to
    sort by ("pH", "Ca", etc.) and sort_values is the per-block value
    list aligned to the group order. Returns (None, []) when no
    split-level soil-state heterogeneity is present.
    """
    # 1. pH range check first — wide pH spread is the single most
    # actionable agronomic mismatch (acidic blocks need lime + ammonia
    # restraint, alkaline blocks need acidifiers + chelated micros).
    ph_values = [_ph_value(b) for b in group]
    ph_filtered = [v for v in ph_values if v is not None]
    if len(ph_filtered) >= 2:
        ph_range = max(ph_filtered) - min(ph_filtered)
        if ph_range >= _PH_SPLIT_RANGE:
            return "pH", [v if v is not None else 0.0 for v in ph_values]

    # 2. Cation / saturation CV check — same recipe shape but very
    # different absolute amounts means programmed kg/ha will overshoot
    # on rich blocks and undershoot on poor blocks.
    worst_key: Optional[str] = None
    worst_cv: float = -1.0
    worst_values: list[float] = []
    for key in _SOIL_HETERO_KEYS:
        values = [_soil_param_value(b, key) for b in group]
        present = [v for v in values if v is not None]
        if len(present) < 2:
            continue
        cv = _cv_pct(present)
        if cv is None:
            continue
        if cv > _SATURATION_SPLIT_CV_PCT and cv > worst_cv:
            worst_cv = cv
            worst_key = key
            worst_values = [v if v is not None else 0.0 for v in values]
    if worst_key is not None:
        return worst_key, worst_values
    return None, []


def _refine_group_by_heterogeneity(group: list[Any]) -> list[list[Any]]:
    """Recursively split a group whose target OR soil-state heterogeneity
    hits the split threshold.

    Two heterogeneity axes are checked, in priority order:

    1. **Soil state** (pH range or cation/saturation CV) — drives the
       agronomic decision. Lime vs acidifier, supplementation vs hold,
       drainage class. A cluster with pH 4.4 and pH 7.5 in the same
       group is wrong for both extremes regardless of what the season
       targets averaged out to.
    2. **Season targets** (per-nutrient CV) — the original check.
       Catches blocks with similar soil but very different yield/density
       leading to different removal targets.

    Strategy: identify the worst-offending dimension, sort blocks by
    that dimension's per-block value, median-split, recurse on each
    half. Stops when both axes are below threshold or the group is a
    singleton.
    """
    if len(group) <= 1:
        return [group]

    # Soil-state check first: pH spread / cation CV.
    soil_key, soil_values = _soil_state_split_signal(group)
    if soil_key is not None:
        order = sorted(range(len(group)), key=lambda i: soil_values[i])
        ordered = [group[i] for i in order]
        mid = len(ordered) // 2
        low, high = ordered[:mid], ordered[mid:]
        if low and high:
            return _refine_group_by_heterogeneity(low) + _refine_group_by_heterogeneity(high)

    # Season-target check (existing behaviour).
    agg = aggregate_cluster(group, cluster_id="_tmp")
    if not agg.heterogeneity.any_split:
        return [group]
    # Identify the nutrient with highest CV among those that crossed the
    # "split" threshold — that's the one driving the misfit.
    worst_nut: Optional[str] = None
    worst_cv: float = -1.0
    for nut, info in agg.heterogeneity.per_nutrient.items():
        if info.get("level") != "split":
            continue
        cv = info.get("cv_pct")
        if cv is None:
            continue
        if cv > worst_cv:
            worst_cv = float(cv)
            worst_nut = nut
    if worst_nut is None:
        return [group]
    # Median split on the worst nutrient. Sorted halves keep similar
    # absolute amounts together — what the agronomist wants for one
    # blend per group.
    def _key(b: Any) -> float:
        targets = getattr(b, "season_targets", None) or {}
        v = targets.get(worst_nut, 0)
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0
    sorted_blocks = sorted(group, key=_key)
    mid = len(sorted_blocks) // 2
    low, high = sorted_blocks[:mid], sorted_blocks[mid:]
    if not low or not high:
        return [group]
    return _refine_group_by_heterogeneity(low) + _refine_group_by_heterogeneity(high)


def _block_distance(a: Any, b: Any) -> float:
    """Combined target+soil distance between two blocks. Used by the
    agglomerative `target_clusters`-driven path so the user can pick
    "I want N groups" and get the agronomically tightest N-way split.

    Components:
      * NPK-ratio L1 distance (0–3) — "are these the same recipe shape?"
      * Magnitude difference (0–1) — "are the absolute amounts comparable?"
      * pH delta normalised to a 0.8-unit scale (capped at 1.0) —
        "are the soils similar enough that one programme fits both?"
    Equal-weighted sum so no single signal can dominate. The resulting
    metric is symmetric, non-negative, and zero only when two blocks are
    indistinguishable on all three axes.
    """
    a_targets = getattr(a, "season_targets", None) or {}
    b_targets = getattr(b, "season_targets", None) or {}
    a_n, a_p, a_k, a_total = _npk_ratio(a_targets)
    b_n, b_p, b_k, b_total = _npk_ratio(b_targets)

    if a_total < 0.01 or b_total < 0.01:
        # Degenerate target — can't compute ratio meaningfully. Treat
        # as maximally distant so degenerate blocks stay singletons.
        ratio_dist = 3.0
    else:
        ratio_dist = abs(a_n - b_n) + abs(a_p - b_p) + abs(a_k - b_k)

    if a_total > 0 and b_total > 0:
        mag_dist = abs(a_total - b_total) / max(a_total, b_total)
    else:
        mag_dist = 1.0

    a_ph = _ph_value(a)
    b_ph = _ph_value(b)
    if a_ph is not None and b_ph is not None:
        ph_dist = min(1.0, abs(a_ph - b_ph) / 0.8)
    else:
        ph_dist = 0.0

    return ratio_dist + mag_dist + ph_dist


def _agglomerative_to_k(
    blocks: list[Any], target_k: int, pinned_block_ids: set[str],
) -> list[list[Any]]:
    """Single-linkage agglomerative clustering that stops at exactly
    `target_k` clusters. Pinned blocks are seeded as one super-cluster
    per pinned cluster_id so the user's manual groupings always win.

    Returns a list of `target_k` groups (or fewer if the block count is
    smaller than k). Order: pinned groups first (in caller's order),
    then auto-merged groups by descending size.
    """
    if not blocks:
        return []
    target_k = max(1, target_k)

    # Seed each block as its own cluster, except where multiple blocks
    # share a pinned cluster_id (then they pre-merge into one).
    pinned_groups: dict[str, list[Any]] = {}
    auto_clusters: list[list[Any]] = []
    block_to_pinned: dict[str, str] = {}
    # Caller passes assignments separately — we need access. Walk
    # `pinned_block_ids` only as a fast membership check; the actual
    # cluster_id mapping lives on the block via getattr fallback.
    # (The orchestrator caller seeds this from `assignments`.)
    for block in blocks:
        bid = str(getattr(block, "block_id", ""))
        pinned_cid = block_to_pinned.get(bid)
        if bid in pinned_block_ids and pinned_cid:
            pinned_groups.setdefault(pinned_cid, []).append(block)
        else:
            auto_clusters.append([block])

    # If we already have at-or-below k, no merges needed.
    while len(pinned_groups) + len(auto_clusters) > target_k:
        # Find the closest pair across (pinned, auto) and (auto, auto).
        # Pinned-pinned merges aren't allowed — distinct pinned ids are
        # the user's intent.
        all_groups: list[tuple[str, list[Any]]] = []
        for cid, g in pinned_groups.items():
            all_groups.append((f"_pinned_{cid}", g))
        for i, g in enumerate(auto_clusters):
            all_groups.append((f"_auto_{i}", g))

        best: tuple[float, int, int] | None = None
        for i in range(len(all_groups)):
            for j in range(i + 1, len(all_groups)):
                lab_i, g_i = all_groups[i]
                lab_j, g_j = all_groups[j]
                if lab_i.startswith("_pinned_") and lab_j.startswith("_pinned_"):
                    continue  # never merge two distinct pinned groups
                # Single-linkage: distance between groups = min distance
                # between any pair across them.
                d = min(_block_distance(a, b) for a in g_i for b in g_j)
                if best is None or d < best[0]:
                    best = (d, i, j)
        if best is None:
            break  # only pinned groups remain — can't reduce further
        _, i, j = best
        lab_i, g_i = all_groups[i]
        lab_j, g_j = all_groups[j]
        merged = list(g_i) + list(g_j)
        # Remove the originals; add the merge result back.
        if lab_i.startswith("_pinned_"):
            cid_i = lab_i[len("_pinned_"):]
            pinned_groups[cid_i] = merged  # absorb auto into pinned
            # remove the auto half
            auto_idx = int(lab_j[len("_auto_"):])
            auto_clusters.pop(auto_idx)
        elif lab_j.startswith("_pinned_"):
            cid_j = lab_j[len("_pinned_"):]
            pinned_groups[cid_j] = merged
            auto_idx = int(lab_i[len("_auto_"):])
            auto_clusters.pop(auto_idx)
        else:
            # Both auto — drop them in reverse-index order to keep
            # earlier indices stable, then append the merged result.
            i_idx = int(lab_i[len("_auto_"):])
            j_idx = int(lab_j[len("_auto_"):])
            for idx in sorted([i_idx, j_idx], reverse=True):
                auto_clusters.pop(idx)
            auto_clusters.append(merged)

    # Output: pinned in caller order, then auto sorted by size desc so
    # the biggest group reads first ("Group A" = the dominant cluster).
    out: list[list[Any]] = []
    for cid, g in pinned_groups.items():
        out.append(g)
    out.extend(sorted(auto_clusters, key=len, reverse=True))
    return out


def cluster_and_aggregate(
    blocks: list[Any],
    margin: float = 0.25,
    assignments: Optional[dict[str, str]] = None,
    target_clusters: Optional[int] = None,
) -> list[ClusterAggregate]:
    """End-to-end: cluster by NPK ratio, auto-refine any "split"-level
    sub-groups by absolute amounts, then aggregate.

    `assignments` (block_id → cluster_id) pins specific blocks to named
    clusters; unassigned blocks fall through to first-fit. Pinned cluster
    IDs are preserved as-is in the output (e.g. "A", "B"); auto-clusters
    are numbered after them with the next available letter.

    `target_clusters` — when provided, switches the algorithm to
    agglomerative clustering that produces EXACTLY this many groups
    (or fewer if there aren't enough blocks). Lets the agronomist
    pick "I want N groups" instead of guessing a margin threshold.
    Pinned assignments still win — they form forced super-clusters
    that agglomerative cannot split apart.

    The refinement post-pass only runs on groups that don't contain any
    pinned blocks — once the user has manually assigned blocks, we treat
    that grouping as authoritative.
    """
    assignments = assignments or {}
    pinned_block_ids = set(assignments.keys())

    if target_clusters is not None and target_clusters >= 1:
        # Agglomerative: produce exactly k groups, no refinement post-pass.
        # Seed pinned super-clusters from `assignments` so the helper
        # can read them off the block via the block_to_pinned map it
        # builds internally.
        # We pre-tag blocks via assignments dict membership; the helper
        # looks at block.block_id only, so we can't actually communicate
        # the cluster_id from a dict. Easier: do the seeding here.
        seeded_pinned: dict[str, list[Any]] = {}
        seeded_auto: list[list[Any]] = []
        for block in blocks:
            bid = str(getattr(block, "block_id", ""))
            cid = assignments.get(bid)
            if cid:
                seeded_pinned.setdefault(cid, []).append(block)
            else:
                seeded_auto.append([block])

        all_groups: list[tuple[str | None, list[Any]]] = (
            [(cid, g) for cid, g in seeded_pinned.items()] + [(None, g) for g in seeded_auto]
        )
        # Merge until we hit target_k. Same single-linkage min-distance
        # rule as `_agglomerative_to_k` but with the seeded pinned ids.
        while len(all_groups) > target_clusters:
            best: tuple[float, int, int] | None = None
            for i in range(len(all_groups)):
                for j in range(i + 1, len(all_groups)):
                    cid_i = all_groups[i][0]
                    cid_j = all_groups[j][0]
                    if cid_i is not None and cid_j is not None:
                        continue  # never merge two distinct pinned groups
                    g_i = all_groups[i][1]
                    g_j = all_groups[j][1]
                    d = min(_block_distance(a, b) for a in g_i for b in g_j)
                    if best is None or d < best[0]:
                        best = (d, i, j)
            if best is None:
                break  # only pinned groups remain
            _, i, j = best
            cid_i, g_i = all_groups[i]
            cid_j, g_j = all_groups[j]
            merged_cid = cid_i if cid_i is not None else cid_j
            merged_g = list(g_i) + list(g_j)
            # Drop both, append the merge — order matters because
            # iterating indices.
            for idx in sorted([i, j], reverse=True):
                all_groups.pop(idx)
            all_groups.append((merged_cid, merged_g))

        # Order: pinned (in caller's order) first, then auto by size desc.
        pinned_order: list[str] = []
        seen_cids: set[str] = set()
        for cid in assignments.values():
            if cid not in seen_cids:
                pinned_order.append(cid)
                seen_cids.add(cid)
        pinned_groups_out: list[list[Any]] = []
        for cid in pinned_order:
            for tag, g in all_groups:
                if tag == cid:
                    pinned_groups_out.append(g)
                    break
        auto_groups_out = sorted(
            [g for tag, g in all_groups if tag is None],
            key=len,
            reverse=True,
        )
        refined_groups = pinned_groups_out + auto_groups_out
        pinned_count = len(pinned_groups_out)
    else:
        groups = cluster_blocks_by_npk(blocks, margin=margin, assignments=assignments)
        # Refinement: for each non-pinned group, recursively split if it
        # crossed the split threshold on any nutrient. Pinned groups stay
        # as the user wanted them.
        refined_groups = []
        pinned_count = 0
        for i, g in enumerate(groups):
            is_pinned_group = any(
                str(getattr(b, "block_id", "")) in pinned_block_ids for b in g
            )
            if is_pinned_group:
                refined_groups.append(g)
                pinned_count += 1
            else:
                refined_groups.extend(_refine_group_by_heterogeneity(g))

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
    next_auto_idx = 0
    for i, g in enumerate(refined_groups):
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
