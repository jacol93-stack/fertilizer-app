"""
Similarity merger — Phase 2 module 8.5 (post-consolidator).

Scans the consolidator's output for adjacent Blends that can be safely
combined into one recipe delivered across multiple stage spans. The
consolidator produces one Blend per real stage × method; this module
recognises when two stages (same block, same method) use the same
physical recipe and fuses them so the factory mixes one batch instead
of two.

Criteria (all must hold to merge a pair):
    1. Same block_id.
    2. Same ApplicationMethod kind.
    3. Same set of raw product names (exact match, case-insensitive).
    4. Per-event rate per product matches within ±10 %.
    5. No nutrient-cutoff timing wall fires in any month strictly
       between the two blends' event spans, on any nutrient the
       combined recipe delivers.

Conservative: any criterion failing leaves the two blends separate.
Merging iterates — after a successful merge, the algorithm re-scans
in case the new larger Blend is now mergeable with its next
neighbour.
"""
from __future__ import annotations

import re
from collections import OrderedDict
from datetime import date
from typing import Optional

from app.models import (
    ApplicationEvent,
    Blend,
    BlendPart,
    Concentrate,
    FertigationMethod,
    MethodKind,
    SourceCitation,
)
from app.services.timing_walls import nutrient_blocked_in_month


RATE_TOLERANCE = 0.10  # ±10 % on per-event rate per product


# ============================================================
# Public entry point
# ============================================================

def merge_similar_blends(
    blends: list[Blend],
    crop: str,
    block_area_ha: float,
) -> list[Blend]:
    """Return a post-merge copy of the block's blend list.

    Input blends may come from any one block. For safety the merger
    only fuses blends sharing the same block_id, so passing cross-block
    blends is tolerated (they stay separate).

    Iterates until no further merges are possible. Stable: on ties the
    earlier-stage blend wins the primary stage_number.
    """
    if not blends or len(blends) == 1:
        return list(blends)

    working = list(blends)

    # Group by (block_id, method_kind) so only mergeable candidates
    # compare against each other. Other blends pass through unchanged.
    groups: "OrderedDict[tuple[str, MethodKind], list[Blend]]" = OrderedDict()
    for b in working:
        key = (b.block_id, b.method.kind)
        groups.setdefault(key, []).append(b)

    merged: list[Blend] = []
    for key, group in groups.items():
        merged.extend(_merge_within_group(group, crop, block_area_ha))
    return merged


# ============================================================
# Per-group merge loop
# ============================================================

def _merge_within_group(
    group: list[Blend],
    crop: str,
    block_area_ha: float,
) -> list[Blend]:
    """Iteratively merge any mergeable pairs in `group` until stable.

    Group members share block_id + method_kind by construction.
    """
    # Sort by first event date so "adjacent" has a clear meaning.
    sorted_group = sorted(group, key=lambda b: _earliest_event(b))
    if len(sorted_group) <= 1:
        return sorted_group

    changed = True
    current = sorted_group
    while changed:
        changed = False
        next_pass: list[Blend] = []
        i = 0
        while i < len(current):
            if i + 1 < len(current) and _can_merge(current[i], current[i + 1], crop):
                merged = _merge_pair(current[i], current[i + 1], block_area_ha)
                next_pass.append(merged)
                i += 2
                changed = True
            else:
                next_pass.append(current[i])
                i += 1
        current = next_pass
    return current


# ============================================================
# Merge eligibility
# ============================================================

def _can_merge(a: Blend, b: Blend, crop: str) -> bool:
    """All F4 criteria in one boolean."""
    if a.block_id != b.block_id:
        return False
    if a.method.kind != b.method.kind:
        return False

    # Same product set (case-insensitive)
    products_a = {p.product.strip().lower() for p in a.raw_products}
    products_b = {p.product.strip().lower() for p in b.raw_products}
    if products_a != products_b or not products_a:
        return False

    # Per-event rate per product within ±10 %
    by_name_a = {p.product.strip().lower(): p for p in a.raw_products}
    by_name_b = {p.product.strip().lower(): p for p in b.raw_products}
    for name in products_a:
        rate_a = _parse_kg(by_name_a[name].rate_per_event_per_ha)
        rate_b = _parse_kg(by_name_b[name].rate_per_event_per_ha)
        if not _within_tolerance(rate_a, rate_b, RATE_TOLERANCE):
            return False

    # No timing wall between the two blends' event spans
    if _wall_fires_between(a, b, crop):
        return False

    return True


def _wall_fires_between(a: Blend, b: Blend, crop: str) -> bool:
    """Returns True if any nutrient_cutoff wall fires in a month that
    falls strictly between a's last event and b's first event (or vice
    versa if b precedes a). Overlapping spans yield no gap → no wall
    check."""
    a_last = _latest_event(a)
    b_first = _earliest_event(b)
    b_last = _latest_event(b)
    a_first = _earliest_event(a)

    if a_last < b_first:
        gap_start, gap_end = a_last, b_first
    elif b_last < a_first:
        gap_start, gap_end = b_last, a_first
    else:
        return False  # overlap → no gap months to check

    gap_months = _months_strictly_between(gap_start, gap_end)
    if not gap_months:
        return False

    nutrients = set(a.nutrients_delivered.keys()) | set(b.nutrients_delivered.keys())
    for (year, month) in gap_months:
        for nut in nutrients:
            if nutrient_blocked_in_month(crop, nut, month) is not None:
                return True
    return False


def _months_strictly_between(start: date, end: date) -> list[tuple[int, int]]:
    """List of (year, month) tuples falling strictly between start and
    end (excluding both endpoint months)."""
    if start >= end:
        return []
    months: list[tuple[int, int]] = []
    # Start from the month AFTER start's month
    year = start.year
    month = start.month + 1
    if month > 12:
        month = 1
        year += 1
    while (year, month) < (end.year, end.month):
        months.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


# ============================================================
# Pair merge
# ============================================================

def _merge_pair(a: Blend, b: Blend, block_area_ha: float) -> Blend:
    """Fuse two Blends known to satisfy _can_merge. Stage_number =
    earliest; stage_name = " + ".join of the two spans."""
    # Canonicalise order: earliest event wins primary stage slot
    if _earliest_event(a) > _earliest_event(b):
        a, b = b, a

    # Applications: union, sorted, event_of_stage_index/total relabelled
    union_apps = sorted(
        list(a.applications) + list(b.applications),
        key=lambda e: e.event_date,
    )
    n_events = len(union_apps)
    relabelled_apps = [
        ApplicationEvent(
            event_index=orig.event_index,
            event_date=orig.event_date,
            week_from_planting=orig.week_from_planting,
            event_of_stage_index=i + 1,
            total_events_in_stage=n_events,
        )
        for i, orig in enumerate(union_apps)
    ]

    # Combined stage name: dedup to keep strings like "Veg I + Veg II"
    # stable when one side is already merged.
    stage_names = _split_stage_name(a.stage_name) + _split_stage_name(b.stage_name)
    combined_stage_name = " + ".join(_dedup_preserve_order(stage_names))

    # Merge raw_products — same product set by construction. Average
    # per-event rates (they're within ±10 %), recompute stage + batch
    # from the averaged per-event rate × new event count.
    merged_products = _merge_products(
        a.raw_products, b.raw_products, n_events, block_area_ha
    )

    # Nutrients delivered sum across both
    nutrients_delivered: dict[str, float] = {}
    for key, val in a.nutrients_delivered.items():
        nutrients_delivered[key] = nutrients_delivered.get(key, 0.0) + val
    for key, val in b.nutrients_delivered.items():
        nutrients_delivered[key] = nutrients_delivered.get(key, 0.0) + val
    nutrients_delivered = {k: round(v, 1) for k, v in nutrients_delivered.items()}

    # Recompute concentrates for fertigation from the merged products
    concentrates: list[Concentrate] = []
    if isinstance(a.method, FertigationMethod) or isinstance(b.method, FertigationMethod):
        from app.services.consolidator import _build_fertigation_concentrates  # local import to avoid cycle on module load
        concentrates = _build_fertigation_concentrates(
            raw_products=merged_products,
            block_area_ha=block_area_ha,
        )

    # Merge sources (dedup by source_id + section)
    merged_sources = _dedup_sources(a.sources + b.sources)

    # Confidence: when both set, pick the wider band (weaker confidence
    # wins — merged recipe inherits the looser uncertainty of its parts)
    merged_confidence = a.confidence or b.confidence
    if a.confidence and b.confidence:
        a_span = a.confidence.pct_low + a.confidence.pct_high
        b_span = b.confidence.pct_low + b.confidence.pct_high
        merged_confidence = a.confidence if a_span >= b_span else b.confidence

    return Blend(
        block_id=a.block_id,
        stage_number=a.stage_number,
        stage_name=combined_stage_name,
        applications=relabelled_apps,
        method=a.method,  # identical kind on both by precondition
        raw_products=merged_products,
        concentrates=concentrates,
        nutrients_delivered=nutrients_delivered,
        sources=merged_sources,
        confidence=merged_confidence,
    )


def _merge_products(
    parts_a: list[BlendPart],
    parts_b: list[BlendPart],
    n_events: int,
    block_area_ha: float,
) -> list[BlendPart]:
    """Return one averaged BlendPart per shared product name, in the
    order from parts_a."""
    by_name_b = {p.product.strip().lower(): p for p in parts_b}
    out: list[BlendPart] = []
    for pa in parts_a:
        pb = by_name_b[pa.product.strip().lower()]
        rate_a = _parse_kg(pa.rate_per_event_per_ha)
        rate_b = _parse_kg(pb.rate_per_event_per_ha)
        avg_event = (rate_a + rate_b) / 2.0 if (rate_a or rate_b) else 0.0
        new_stage = avg_event * n_events if n_events else 0.0
        new_batch = new_stage * block_area_ha
        out.append(BlendPart(
            product=pa.product,
            analysis=pa.analysis,
            stream=pa.stream,
            rate_per_event_per_ha=_fmt_kg(avg_event) if avg_event else pa.rate_per_event_per_ha,
            rate_per_stage_per_ha=_fmt_kg(new_stage) if new_stage else pa.rate_per_stage_per_ha,
            batch_total=_fmt_kg(new_batch) if new_batch else pa.batch_total,
            source=pa.source or pb.source,
        ))
    return out


def _dedup_sources(sources: list[SourceCitation]) -> list[SourceCitation]:
    seen: set[tuple[str, Optional[str]]] = set()
    out: list[SourceCitation] = []
    for s in sources:
        key = (s.source_id, s.section)
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


# ============================================================
# Small helpers
# ============================================================

def _earliest_event(b: Blend) -> date:
    return min(a.event_date for a in b.applications)


def _latest_event(b: Blend) -> date:
    return max(a.event_date for a in b.applications)


def _within_tolerance(a: float, b: float, tol: float) -> bool:
    """True if |a - b| / max(|a|, |b|, eps) <= tol. If both are 0, True."""
    if a == 0 and b == 0:
        return True
    denom = max(abs(a), abs(b), 1e-9)
    return abs(a - b) / denom <= tol


_KG_RE = re.compile(r"^\s*([\d\s,\.]+)\s*kg\s*$", re.IGNORECASE)


def _parse_kg(text: Optional[str]) -> float:
    """Parse '42 kg' / '42.5 kg' / '1 200 kg' (SA notation). Returns 0.0
    for None / unparseable."""
    if text is None:
        return 0.0
    match = _KG_RE.match(text)
    if not match:
        return 0.0
    raw = match.group(1).replace(" ", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _fmt_kg(v: float) -> str:
    if v >= 10:
        return f"{v:.0f} kg"
    return f"{v:.1f} kg"


def _split_stage_name(name: str) -> list[str]:
    """Handle stage names that may already be " + "-joined from a prior
    merge, so repeated merges stay flat."""
    return [part.strip() for part in name.split(" + ") if part.strip()]


def _dedup_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
