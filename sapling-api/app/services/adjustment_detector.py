"""Adjustment trigger detection.

When a new soil or leaf analysis is saved against a block that belongs
to an active programme, the tracker needs to detect whether the data
differs from the baseline enough to warrant a mid-season adjustment.

The detector writes a `programme_adjustments` row with status='suggested'.
The agronomist reviews and either approves (→ phase 3 apply) or rejects.

This module only detects and records. It does NOT modify
programme_blends. That's the apply step (phase 3), deliberately
separate so the agronomist is always in the loop.

Detection rules, documented so future audits trace where numbers come
from:

  Soil:
    A new analysis meaningfully differs from the block's baseline if
    any nutrient's target shifts by more than the programme-level
    variability_margin (default 15%). Smaller shifts are noise and
    don't warrant an alert.

  Leaf:
    Any nutrient classified as Deficient/Low/Excess/Toxic in the new
    analysis triggers a suggestion. The existing leaf_engine produces
    those classifications via FERTASA tissue thresholds
    (tissue_toxicity table).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("sapling.adjustment_detector")

# Fallback if default_materials.variability_margin is missing
DEFAULT_MARGIN_PCT = 15.0


def _targets_by_nutrient(targets: list[dict] | None) -> dict[str, float]:
    """Extract nutrient -> kg/ha from a nutrient_targets JSONB array.

    Handles both casings (Nutrient / nutrient) and the two target-field
    names (Final_Target_kg_ha preferred, Target_kg_ha fallback)."""
    out: dict[str, float] = {}
    for t in targets or []:
        nut = t.get("Nutrient") or t.get("nutrient")
        val = t.get("Final_Target_kg_ha")
        if val is None:
            val = t.get("Target_kg_ha")
        if val is None:
            val = t.get("target_kg_ha")
        if nut and val is not None:
            try:
                out[nut] = float(val)
            except (TypeError, ValueError):
                pass
    return out


def _compute_soil_delta(
    old_targets: dict[str, float],
    new_targets: dict[str, float],
    margin_pct: float,
) -> list[dict]:
    """Per-nutrient delta entries for any nutrient that moved by more
    than `margin_pct` (as a percentage of the old target)."""
    threshold = margin_pct / 100.0
    delta = []
    for nut, new_val in new_targets.items():
        old_val = old_targets.get(nut, 0.0)
        # Treat 0 -> non-zero as a "new requirement" — always flag
        if old_val <= 0.01 and new_val > 0.01:
            delta.append({
                "nutrient": nut,
                "old_kg_ha": round(old_val, 2),
                "new_kg_ha": round(new_val, 2),
                "change_pct": None,   # undefined when starting from zero
                "direction": "introduced",
            })
            continue
        if old_val <= 0.01:
            continue
        pct_change = (new_val - old_val) / old_val
        if abs(pct_change) >= threshold:
            delta.append({
                "nutrient": nut,
                "old_kg_ha": round(old_val, 2),
                "new_kg_ha": round(new_val, 2),
                "change_pct": round(pct_change * 100, 1),
                "direction": "increase" if pct_change > 0 else "decrease",
            })
    # Also flag nutrients that dropped out (old non-zero, new zero/missing)
    for nut, old_val in old_targets.items():
        if old_val > 0.01 and new_targets.get(nut, 0.0) <= 0.01:
            delta.append({
                "nutrient": nut,
                "old_kg_ha": round(old_val, 2),
                "new_kg_ha": 0.0,
                "change_pct": -100.0,
                "direction": "removed",
            })
    return delta


def _load_variability_margin(sb) -> float:
    """Pull the programme-level variability_margin from default_materials."""
    try:
        r = sb.table("default_materials").select("variability_margin").limit(1).execute()
        if r.data and r.data[0].get("variability_margin") is not None:
            return float(r.data[0]["variability_margin"])
    except Exception as e:
        logger.debug("variability_margin lookup failed: %s", e)
    return DEFAULT_MARGIN_PCT


def detect_soil_adjustment(
    sb,
    programme_id: str,
    block_id: str,
    new_analysis_id: str,
    created_by: str | None = None,
) -> dict | None:
    """Compare a new soil analysis's targets to the block's baseline and
    write a 'suggested' programme_adjustments row if they differ beyond
    the variability margin.

    Returns the created adjustment row, or None if nothing to suggest.
    Safe to call in a hot path — logs and swallows errors rather than
    blocking the save that triggered it.
    """
    try:
        # Baseline: what the block is currently operating from
        block_r = (
            sb.table("programme_blocks")
            .select("nutrient_targets, soil_analysis_id, crop, name")
            .eq("id", block_id)
            .limit(1)
            .execute()
        )
        if not block_r.data:
            return None
        block = block_r.data[0]

        # If the new analysis IS the block's current baseline, nothing to do
        if block.get("soil_analysis_id") == new_analysis_id:
            return None

        old_targets = _targets_by_nutrient(block.get("nutrient_targets"))

        # New analysis
        sa_r = (
            sb.table("soil_analyses")
            .select("nutrient_targets, crop, analysis_date")
            .eq("id", new_analysis_id)
            .limit(1)
            .execute()
        )
        if not sa_r.data:
            return None
        new_targets = _targets_by_nutrient(sa_r.data[0].get("nutrient_targets"))
        if not new_targets:
            # New analysis hasn't computed targets yet — can't compare
            return None

        margin = _load_variability_margin(sb)
        delta = _compute_soil_delta(old_targets, new_targets, margin)
        if not delta:
            return None

        summary = _summarise_soil_delta(delta)

        row = {
            "programme_id": programme_id,
            "block_id": block_id,
            "trigger_type": "soil_analysis",
            "trigger_id": new_analysis_id,
            "trigger_data": {
                "crop": block.get("crop"),
                "block_name": block.get("name"),
                "previous_analysis_id": block.get("soil_analysis_id"),
                "new_analysis_date": sa_r.data[0].get("analysis_date"),
                "margin_pct_used": margin,
            },
            "adjustment_data": {
                "action": "update_targets",
                "delta": delta,
                "summary": summary,
            },
            "notes": summary,
            "created_by": created_by,
            "status": "suggested",
        }
        result = sb.table("programme_adjustments").insert(row).execute()
        if result.data:
            logger.info(
                "soil adjustment suggested: programme=%s block=%s delta=%d nutrients",
                programme_id, block_id, len(delta),
            )
            return result.data[0]
    except Exception as e:
        logger.warning("detect_soil_adjustment failed: %s", e, exc_info=True)
    return None


def detect_off_programme_adjustment(
    sb,
    programme_id: str,
    block_id: str | None,
    application_id: str,
    created_by: str | None = None,
) -> dict | None:
    """Raise a suggested adjustment when an actual application was off-plan:

      * No planned_blend_id set (agent recorded something the plan didn't
        call for — a corrective spray, extra topdress, whatever).
      * OR actual_rate_kg_ha differs from the planned rate by more than
        the variability_margin, meaning the farmer delivered a very
        different dose than the programme prescribed.

    The proposer (adjustment_proposer) will consume the suggestion and
    propose how to rebalance the remaining plan — typically by scaling
    future blends down when nutrients were over-delivered or up when
    under-delivered.
    """
    try:
        app_r = (
            sb.table("programme_applications")
            .select("*")
            .eq("id", application_id)
            .limit(1)
            .execute()
        )
        if not app_r.data:
            return None
        app = app_r.data[0]

        if app.get("status") and app["status"] != "applied":
            return None

        actual_rate = float(app.get("actual_rate_kg_ha") or 0)
        planned_id = app.get("planned_blend_id")

        margin = _load_variability_margin(sb)
        threshold = margin / 100.0  # e.g. 0.15 for 15%

        off_plan_reason: str | None = None
        deviation_pct: float | None = None
        planned_blend: dict | None = None

        if not planned_id:
            # Truly unplanned action
            off_plan_reason = "unplanned_application"
        else:
            planned = (
                sb.table("programme_blends")
                .select("*")
                .eq("id", planned_id)
                .limit(1)
                .execute()
                .data
            )
            if planned:
                planned_blend = planned[0]
                planned_rate = float(planned_blend.get("rate_kg_ha") or 0)
                if planned_rate > 0.01 and actual_rate > 0.01:
                    deviation_pct = (actual_rate - planned_rate) / planned_rate
                    if abs(deviation_pct) >= threshold:
                        off_plan_reason = "rate_deviation"

        if not off_plan_reason:
            return None

        # Build the trigger snapshot
        trigger_data = {
            "application_id": application_id,
            "reason": off_plan_reason,
            "product_name": app.get("product_name"),
            "product_type": app.get("product_type"),
            "is_sapling_product": app.get("is_sapling_product"),
            "actual_rate_kg_ha": actual_rate,
            "method": app.get("method"),
            "actual_date": app.get("actual_date"),
        }
        if planned_blend:
            trigger_data["planned_blend_id"] = planned_blend["id"]
            trigger_data["planned_rate_kg_ha"] = planned_blend.get("rate_kg_ha")
            trigger_data["deviation_pct"] = (
                round(deviation_pct * 100, 1) if deviation_pct is not None else None
            )
            trigger_data["margin_pct_used"] = margin

        # Short human summary for the notes field
        if off_plan_reason == "unplanned_application":
            product = app.get("product_name") or "unlabelled product"
            summary = (
                f"Off-plan application: {product} at {actual_rate} kg/ha "
                f"(not in programme)"
            )
        else:
            direction = "over" if (deviation_pct or 0) > 0 else "under"
            summary = (
                f"Rate {direction} plan by "
                f"{abs(deviation_pct or 0) * 100:.0f}% — applied {actual_rate} "
                f"kg/ha vs planned {planned_blend.get('rate_kg_ha') if planned_blend else '?'}"
            )

        row = {
            "programme_id": programme_id,
            "block_id": block_id or app.get("block_id"),
            "trigger_type": "off_programme_action",
            "trigger_id": application_id,
            "trigger_data": trigger_data,
            "adjustment_data": {
                "action": "rebalance_remaining",
                "reason": off_plan_reason,
                "deviation_pct": (
                    round(deviation_pct * 100, 1) if deviation_pct is not None else None
                ),
                "summary": summary,
            },
            "notes": summary,
            "created_by": created_by,
            "status": "suggested",
        }
        result = sb.table("programme_adjustments").insert(row).execute()
        if result.data:
            logger.info(
                "off-programme adjustment suggested: programme=%s reason=%s",
                programme_id, off_plan_reason,
            )
            return result.data[0]
    except Exception as e:
        logger.warning("detect_off_programme_adjustment failed: %s", e, exc_info=True)
    return None


def detect_leaf_adjustment(
    sb,
    programme_id: str,
    block_id: str | None,
    new_leaf_id: str,
    created_by: str | None = None,
) -> dict | None:
    """Create a 'suggested' adjustment when a leaf analysis shows any
    nutrient outside the sufficiency range (Deficient/Low/Excess/Toxic).

    Returns the created row, or None if nothing triggered.
    """
    try:
        leaf_r = (
            sb.table("leaf_analyses")
            .select("classifications, crop, sample_date, foliar_recommendations")
            .eq("id", new_leaf_id)
            .limit(1)
            .execute()
        )
        if not leaf_r.data:
            return None
        rec = leaf_r.data[0]
        classifications = rec.get("classifications") or {}
        if not classifications:
            return None

        deficiencies = [k for k, v in classifications.items() if v in ("Deficient", "Low")]
        excesses = [k for k, v in classifications.items() if v in ("Excess", "Toxic")]

        if not deficiencies and not excesses:
            return None

        parts = []
        if deficiencies:
            parts.append(f"deficient: {', '.join(deficiencies)}")
        if excesses:
            parts.append(f"excess: {', '.join(excesses)}")
        summary = "Leaf analysis — " + "; ".join(parts)

        row = {
            "programme_id": programme_id,
            "block_id": block_id,
            "trigger_type": "leaf_analysis",
            "trigger_id": new_leaf_id,
            "trigger_data": {
                "crop": rec.get("crop"),
                "sample_date": rec.get("sample_date"),
                "classifications": classifications,
            },
            "adjustment_data": {
                "action": "foliar_correction_recommended" if deficiencies else "reduce_excess",
                "deficient_elements": deficiencies,
                "excess_elements": excesses,
                "foliar_recommendations": rec.get("foliar_recommendations"),
                "summary": summary,
            },
            "notes": summary,
            "created_by": created_by,
            "status": "suggested",
        }
        result = sb.table("programme_adjustments").insert(row).execute()
        if result.data:
            logger.info(
                "leaf adjustment suggested: programme=%s block=%s def=%d exc=%d",
                programme_id, block_id, len(deficiencies), len(excesses),
            )
            return result.data[0]
    except Exception as e:
        logger.warning("detect_leaf_adjustment failed: %s", e, exc_info=True)
    return None


def _summarise_soil_delta(delta: list[dict]) -> str:
    """Human-readable one-liner for the adjustment notes field."""
    if not delta:
        return "No meaningful change"
    increases = [d for d in delta if d["direction"] == "increase"]
    decreases = [d for d in delta if d["direction"] == "decrease"]
    introduced = [d for d in delta if d["direction"] == "introduced"]
    removed = [d for d in delta if d["direction"] == "removed"]
    parts = []
    if increases:
        names = ", ".join(f"{d['nutrient']} +{d['change_pct']}%" for d in increases)
        parts.append(f"↑ {names}")
    if decreases:
        names = ", ".join(f"{d['nutrient']} {d['change_pct']}%" for d in decreases)
        parts.append(f"↓ {names}")
    if introduced:
        names = ", ".join(d["nutrient"] for d in introduced)
        parts.append(f"newly required: {names}")
    if removed:
        names = ", ".join(d["nutrient"] for d in removed)
        parts.append(f"no longer needed: {names}")
    return " · ".join(parts)


def find_programme_blocks_for_analysis(sb, new_analysis_id: str) -> list[dict]:
    """Find all programme_blocks that should react to this new soil
    analysis. Two lookup paths, unioned:

      1. Blocks with matching field_id (blocks from the field-wizard
         flow have this set).
      2. Blocks whose soil_analysis_id references an earlier analysis
         on the same field. Legacy blocks created before the farm
         builder don't have field_id set but are still tied to a
         specific field via their baseline analysis.

    Returns a list of unique {programme_id, block_id} dicts,
    filtered to programmes that are alive and not already completed.
    """
    try:
        sa = (
            sb.table("soil_analyses")
            .select("field_id")
            .eq("id", new_analysis_id)
            .limit(1)
            .execute()
        )
        if not sa.data or not sa.data[0].get("field_id"):
            return []
        field_id = sa.data[0]["field_id"]

        # Path 2: all analyses on this field — used to reach legacy blocks
        field_analyses = (
            sb.table("soil_analyses")
            .select("id")
            .eq("field_id", field_id)
            .execute()
        )
        analysis_ids = [a["id"] for a in (field_analyses.data or [])]

        # Path 1: blocks with matching field_id
        by_field = (
            sb.table("programme_blocks")
            .select("id, programme_id, programmes!inner(id, deleted_at, status)")
            .eq("field_id", field_id)
            .execute()
        ).data or []

        # Path 2: blocks whose baseline analysis is one of the field's analyses
        by_analysis: list[dict] = []
        if analysis_ids:
            by_analysis = (
                sb.table("programme_blocks")
                .select("id, programme_id, programmes!inner(id, deleted_at, status)")
                .in_("soil_analysis_id", analysis_ids)
                .execute()
            ).data or []

        seen: set[str] = set()
        out: list[dict] = []
        for b in (*by_field, *by_analysis):
            if b["id"] in seen:
                continue
            seen.add(b["id"])
            prog = b.get("programmes") or {}
            if prog.get("deleted_at"):
                continue
            if prog.get("status") in ("archived", "completed"):
                continue
            out.append({"programme_id": b["programme_id"], "block_id": b["id"]})
        return out
    except Exception as e:
        logger.warning("find_programme_blocks_for_analysis failed: %s", e)
        return []
