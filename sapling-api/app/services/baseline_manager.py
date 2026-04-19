"""Programme baseline snapshots.

A baseline is a frozen copy of the programme's blocks + blends at a
specific moment, used as the anchor for comparison over the season.

Created when:
  - Programme transitions draft → active (automatic, reason='activation')
  - Agent explicitly rebases mid-season (reason='manual_rebase')

Only one baseline per programme carries is_current=TRUE. Old baselines
stay in the table for audit — nothing is ever deleted on rebase.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("sapling.baseline_manager")

# Fields we snapshot from programme_blocks. Derived/transient columns
# (created_at, updated_at, id tracking) are stripped.
_BLOCK_FIELDS = (
    "id", "name", "area_ha", "crop", "cultivar",
    "yield_target", "yield_unit", "tree_age", "pop_per_ha",
    "soil_analysis_id", "feeding_plan_id", "blend_group",
    "nutrient_targets", "notes", "field_id",
)

_BLEND_FIELDS = (
    "id", "blend_group", "stage_name", "application_month",
    "blend_id", "blend_recipe", "blend_nutrients",
    "blend_cost_per_ton", "sa_notation", "rate_kg_ha",
    "total_kg", "notes", "method",
)


def _pick(d: dict, fields: tuple[str, ...]) -> dict:
    return {k: d.get(k) for k in fields}


def create_baseline(
    sb,
    programme_id: str,
    reason: str = "activation",
    created_by: str | None = None,
    notes: str | None = None,
) -> dict | None:
    """Snapshot the programme's current state and store it as the new
    current baseline. Flips any prior current baseline to is_current=False.

    Returns the created baseline row, or None if the programme has
    nothing worth snapshotting (no blocks).
    """
    try:
        blocks = (
            sb.table("programme_blocks")
            .select("*")
            .eq("programme_id", programme_id)
            .execute()
            .data
        ) or []
        if not blocks:
            logger.info("baseline skipped — no blocks on programme %s", programme_id)
            return None

        blends = (
            sb.table("programme_blends")
            .select("*")
            .eq("programme_id", programme_id)
            .execute()
            .data
        ) or []

        # Convenience side-map: nutrient targets keyed by block id.
        # Saves lookups later when validator wants to compare plans
        # against the original soil-derived targets.
        targets_by_block = {}
        for b in blocks:
            nt = b.get("nutrient_targets")
            if nt:
                targets_by_block[b["id"]] = nt

        # Flip any existing current baseline off
        sb.table("programme_baselines").update({"is_current": False}) \
            .eq("programme_id", programme_id) \
            .eq("is_current", True) \
            .execute()

        row = {
            "programme_id": programme_id,
            "reason": reason,
            "is_current": True,
            "blocks": [_pick(b, _BLOCK_FIELDS) for b in blocks],
            "blends": [_pick(b, _BLEND_FIELDS) for b in blends],
            "nutrient_targets_by_block": targets_by_block,
            "created_by": created_by,
            "notes": notes,
        }
        result = sb.table("programme_baselines").insert(row).execute()
        if result.data:
            logger.info(
                "baseline created: programme=%s reason=%s blocks=%d blends=%d",
                programme_id, reason, len(blocks), len(blends),
            )
            return result.data[0]
    except Exception as e:
        logger.warning(
            "create_baseline failed: programme=%s reason=%s error=%s",
            programme_id, reason, e, exc_info=True,
        )
    return None


def get_current_baseline(sb, programme_id: str) -> dict | None:
    """Return the active baseline for a programme, or None."""
    r = (
        sb.table("programme_baselines")
        .select("*")
        .eq("programme_id", programme_id)
        .eq("is_current", True)
        .limit(1)
        .execute()
    )
    return r.data[0] if r.data else None


def list_baselines(sb, programme_id: str) -> list[dict]:
    """All baselines for a programme, most recent first."""
    r = (
        sb.table("programme_baselines")
        .select("id, created_at, created_by, reason, is_current, notes")
        .eq("programme_id", programme_id)
        .order("created_at", desc=True)
        .execute()
    )
    return r.data or []
