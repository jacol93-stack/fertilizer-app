"""Adjustment proposer — phase 2 of the season tracker.

Turns a 'suggested' programme_adjustments row into a concrete proposal:
for each remaining application in the programme's block(s), what the
nutrient amounts should become if we honour the new targets.

This module ONLY proposes. It does not persist. The agronomist reviews
the proposal, then the apply step (phase 3) writes it into
programme_blends.

Proposal algorithm — soil delta:
  1. Determine "remaining" applications: blends whose application_month
     is in the future relative to today, or whose matching
     programme_applications row is not yet 'applied'.
  2. For each affected nutrient in the delta, compute a scale factor:
        scale = new_remaining_target / old_remaining_total
     where old_remaining_total is the sum of that nutrient across
     remaining blends, and new_remaining_target is what still needs to
     be delivered after subtracting already-applied amounts.
  3. For each remaining blend, multiply its per-nutrient kg/ha by the
     scale factor for that nutrient. Recalculate rate_kg_ha from the
     new total nutrient sum, keeping the same density assumption as
     the original build (25%).

Proposal algorithm — leaf delta:
  Not scaling; instead attaching a recommended foliar application to
  the nearest upcoming month. The agronomist approves and Phase 3 adds
  it as a new programme_blends row with blend_group='F' (foliar).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("sapling.adjustment_proposer")

NUTRIENT_KEYS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]


def propose_from_adjustment(sb, adjustment_id: str) -> dict:
    """Compute a concrete proposal for a suggested adjustment.

    Returns:
        {
            adjustment: {...},
            affected_blends: [
                {
                    id, blend_group, stage_name, application_month,
                    is_past, is_applied,
                    old: {rate_kg_ha, nutrients: {n,p,k,...}},
                    new: {rate_kg_ha, nutrients: {...}},
                    delta: {n: "+12.5 kg/ha", ...},
                }
            ],
            summary: {
                affected_count, unchanged_count,
                season_totals: {
                    old: {n, p, k, ...},
                    new: {n, p, k, ...},
                }
            }
        }
    """
    adj_r = (
        sb.table("programme_adjustments")
        .select("*")
        .eq("id", adjustment_id)
        .limit(1)
        .execute()
    )
    if not adj_r.data:
        return {"error": "adjustment_not_found"}
    adj = adj_r.data[0]

    trigger_type = adj.get("trigger_type")
    if trigger_type in ("soil_analysis",):
        return _propose_soil(sb, adj)
    if trigger_type in ("leaf_analysis",):
        return _propose_leaf(sb, adj)
    return {
        "adjustment": adj,
        "affected_blends": [],
        "summary": {
            "affected_count": 0,
            "unchanged_count": 0,
            "reason": f"no proposer for trigger_type={trigger_type!r}",
        },
    }


def _propose_soil(sb, adj: dict) -> dict:
    """Scale remaining programme_blends by per-nutrient factors
    derived from the delta."""
    programme_id = adj["programme_id"]
    block_id = adj.get("block_id")
    delta = (adj.get("adjustment_data") or {}).get("delta") or []

    if not delta:
        return _empty_proposal(adj, "no delta in adjustment_data")

    # All planned blends for this programme
    blends_query = sb.table("programme_blends").select("*").eq("programme_id", programme_id)
    blends = blends_query.execute().data or []
    if not blends:
        return _empty_proposal(adj, "programme has no blends")

    # If this adjustment is for a specific block, filter to its blend group.
    # (blend_group is shared across blocks with similar NPK profiles; if the
    # block is in group 'A', scaling should apply to group 'A' only, not
    # the whole programme.)
    group_filter: str | None = None
    if block_id:
        block_r = (
            sb.table("programme_blocks")
            .select("blend_group")
            .eq("id", block_id)
            .limit(1)
            .execute()
        )
        if block_r.data and block_r.data[0].get("blend_group"):
            group_filter = block_r.data[0]["blend_group"]

    relevant = [b for b in blends if (group_filter is None or b.get("blend_group") == group_filter)]
    if not relevant:
        return _empty_proposal(adj, f"no blends for group {group_filter!r}")

    # Split past vs remaining by application_month.
    # Southern Hemisphere: fertigation months cycle Jan-Dec; we need a
    # fiscal-season comparison rather than calendar. For the first pass
    # we use: "remaining = blend month >= current month OR blend is
    # explicitly not yet applied".
    current_month = datetime.now(timezone.utc).month
    applications = (
        sb.table("programme_applications")
        .select("planned_blend_id, status")
        .eq("programme_id", programme_id)
        .execute()
        .data or []
    )
    applied_blend_ids = {
        a["planned_blend_id"] for a in applications
        if a.get("status") == "applied" and a.get("planned_blend_id")
    }

    past_blends: list[dict] = []
    remaining_blends: list[dict] = []
    for b in relevant:
        is_applied = b["id"] in applied_blend_ids
        month = b.get("application_month") or 1
        is_past = month < current_month  # crude SH-fiscal heuristic
        if is_applied or is_past:
            past_blends.append(b)
        else:
            remaining_blends.append(b)

    if not remaining_blends:
        return _empty_proposal(adj, "no remaining blends (all past or applied)")

    # Build per-nutrient scaling factors.
    # For each nutrient in delta: factor = (new_target - already_applied) / old_remaining
    delta_by_nut = {d["nutrient"].lower(): d for d in delta}

    scale_factors: dict[str, float] = {}
    old_remaining_totals: dict[str, float] = {}
    past_applied_totals: dict[str, float] = {}

    for nut in NUTRIENT_KEYS:
        old_remaining_totals[nut] = sum(
            _nut_of(b, nut) for b in remaining_blends
        )
        past_applied_totals[nut] = sum(
            _nut_of(b, nut) for b in past_blends
        )

    for nut, d in delta_by_nut.items():
        new_target = float(d.get("new_kg_ha") or 0)
        old_remaining = old_remaining_totals.get(nut, 0.0)
        already_applied = past_applied_totals.get(nut, 0.0)

        # Remaining under new plan
        new_remaining = max(new_target - already_applied, 0.0)
        if old_remaining < 0.01:
            # Nothing was planned for this nutrient in remaining apps;
            # introducing requires new application (handled in phase 3)
            scale_factors[nut] = None  # flag introduced
            continue
        # Clamp scale factor to [0, 5] — an extreme scale should flag,
        # not silently over-feed.
        raw = new_remaining / old_remaining
        scale_factors[nut] = max(0.0, min(raw, 5.0))

    # Build per-blend proposals
    affected: list[dict] = []
    old_season_totals = {k: 0.0 for k in NUTRIENT_KEYS}
    new_season_totals = {k: 0.0 for k in NUTRIENT_KEYS}

    for b in relevant:
        month = b.get("application_month") or 1
        is_applied = b["id"] in applied_blend_ids
        is_past = month < current_month
        old_nut = {k: _nut_of(b, k) for k in NUTRIENT_KEYS}
        for k, v in old_nut.items():
            old_season_totals[k] += v

        if is_applied or is_past:
            # Don't propose changes to past applications; they already happened
            for k, v in old_nut.items():
                new_season_totals[k] += v
            continue

        new_nut = {}
        for k, v in old_nut.items():
            factor = scale_factors.get(k)
            if factor is None and k in delta_by_nut:
                # Introduced nutrient — leave 0 here; phase 3 can add a
                # dedicated application. Flag in diff.
                new_nut[k] = v  # don't back-compute here
            elif factor is None:
                new_nut[k] = v  # nutrient not in delta, unchanged
            else:
                new_nut[k] = round(v * factor, 3)
            new_season_totals[k] += new_nut[k]

        new_rate = _rate_from_nutrients(new_nut)
        old_rate = b.get("rate_kg_ha") or _rate_from_nutrients(old_nut)

        affected.append({
            "id": b["id"],
            "blend_group": b.get("blend_group"),
            "stage_name": b.get("stage_name"),
            "application_month": month,
            "method": b.get("method"),
            "is_past": is_past,
            "is_applied": is_applied,
            "old": {
                "rate_kg_ha": round(old_rate, 1) if old_rate else None,
                "nutrients": {k: round(v, 2) for k, v in old_nut.items() if v > 0.001},
            },
            "new": {
                "rate_kg_ha": round(new_rate, 1) if new_rate else None,
                "nutrients": {k: round(v, 2) for k, v in new_nut.items() if v > 0.001},
            },
            "changed": any(
                abs(new_nut[k] - old_nut[k]) > 0.01 for k in NUTRIENT_KEYS
            ),
        })

    return {
        "adjustment": adj,
        "affected_blends": affected,
        "summary": {
            "affected_count": sum(1 for a in affected if a["changed"]),
            "unchanged_count": sum(1 for a in affected if not a["changed"]),
            "past_applications": len(past_blends),
            "scale_factors": {k: round(v, 3) for k, v in scale_factors.items() if v is not None},
            "introduced_nutrients": [k for k, v in scale_factors.items() if v is None],
            "season_totals": {
                "old": {k: round(v, 2) for k, v in old_season_totals.items() if v > 0.001},
                "new": {k: round(v, 2) for k, v in new_season_totals.items() if v > 0.001},
            },
        },
    }


def _propose_leaf(sb, adj: dict) -> dict:
    """Leaf-trigger proposals don't scale the dry plan — they attach a
    foliar correction for deficient elements. Phase 3 writes this as a
    new programme_blends row with method='foliar'."""
    data = adj.get("adjustment_data") or {}
    deficient = data.get("deficient_elements") or []
    foliar_recs = data.get("foliar_recommendations") or []
    if not deficient and not data.get("excess_elements"):
        return _empty_proposal(adj, "leaf analysis has no deficient or excess elements")

    current_month = datetime.now(timezone.utc).month
    return {
        "adjustment": adj,
        "affected_blends": [],
        "proposed_foliar": {
            "target_month": current_month,
            "deficient_elements": deficient,
            "excess_elements": data.get("excess_elements") or [],
            "recommendations": foliar_recs,
        },
        "summary": {
            "kind": "foliar_correction",
            "deficient_count": len(deficient),
            "excess_count": len(data.get("excess_elements") or []),
        },
    }


def _nut_of(blend: dict, key: str) -> float:
    """Pull a nutrient kg/ha from a blend_nutrients dict, defaulting to 0."""
    n = blend.get("blend_nutrients") or {}
    v = n.get(key)
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _rate_from_nutrients(nutrients: dict[str, float], density_pct: float = 25.0) -> float:
    """Back-compute rate_kg_ha assuming 25% nutrient density (the same
    assumption used in programme_engine.optimize_blend_for_group)."""
    total = sum(v for v in nutrients.values() if v)
    if total < 0.01:
        return 0.0
    return total / (density_pct / 100.0)


def _empty_proposal(adj: dict, reason: str) -> dict:
    return {
        "adjustment": adj,
        "affected_blends": [],
        "summary": {
            "affected_count": 0,
            "unchanged_count": 0,
            "reason": reason,
        },
    }
