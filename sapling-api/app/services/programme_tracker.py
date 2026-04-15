"""Programme tracker: record applications, calculate variance, adjust plans."""

from app.supabase_client import get_supabase_admin

NUTRIENTS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]


def calculate_variance(programme_id: str) -> dict:
    """Compare planned vs actual nutrient delivery across all blocks.

    Returns per-block and overall variance summary.
    """
    sb = get_supabase_admin()

    blocks = sb.table("programme_blocks").select("id, name, crop, area_ha").eq("programme_id", programme_id).execute()
    apps = sb.table("programme_applications").select("*").eq("programme_id", programme_id).execute()
    blends = sb.table("programme_blends").select("*").eq("programme_id", programme_id).execute()

    blocks_data = blocks.data or []
    apps_data = apps.data or []
    blends_data = blends.data or []

    block_variance = []
    for block in blocks_data:
        block_id = block["id"]

        # Planned: sum from programme_blends (all planned applications for this block's group)
        block_group = None
        for b in blocks_data:
            if b["id"] == block_id:
                # Need to get blend_group from programme_blocks
                full_block = sb.table("programme_blocks").select("blend_group").eq("id", block_id).limit(1).execute()
                block_group = full_block.data[0].get("blend_group") if full_block.data else None
                break

        planned = {f"{n}_kg_ha": 0.0 for n in NUTRIENTS}
        for blend in blends_data:
            if blend.get("blend_group") == block_group:
                rate = float(blend.get("rate_kg_ha") or 0)
                # We'd need the blend recipe to calculate nutrients, but for now use rate as proxy
                planned["total_rate_kg_ha"] = planned.get("total_rate_kg_ha", 0) + rate

        # Actual: sum from programme_applications for this block
        actual = {"total_rate_kg_ha": 0.0}
        applied_count = 0
        pending_count = 0
        for app in apps_data:
            if app.get("block_id") == block_id:
                if app.get("status") == "applied":
                    actual["total_rate_kg_ha"] += float(app.get("actual_rate_kg_ha") or 0)
                    applied_count += 1
                elif app.get("status") == "pending":
                    pending_count += 1

        block_variance.append({
            "block_id": block_id,
            "block_name": block["name"],
            "crop": block["crop"],
            "planned_applications": len([b for b in blends_data if b.get("blend_group") == block_group]),
            "applied": applied_count,
            "pending": pending_count,
            "planned_total_rate": planned.get("total_rate_kg_ha", 0),
            "actual_total_rate": actual["total_rate_kg_ha"],
            "completion_pct": round(
                (applied_count / max(len([b for b in blends_data if b.get("blend_group") == block_group]), 1)) * 100, 1
            ),
        })

    # Overall status
    total_planned = sum(bv["planned_applications"] for bv in block_variance)
    total_applied = sum(bv["applied"] for bv in block_variance)
    total_pending = sum(bv["pending"] for bv in block_variance)

    return {
        "programme_id": programme_id,
        "blocks": block_variance,
        "overall": {
            "total_planned": total_planned,
            "total_applied": total_applied,
            "total_pending": total_pending,
            "completion_pct": round((total_applied / max(total_planned, 1)) * 100, 1),
            "status": "on_track" if total_applied >= total_planned * 0.8 else "behind" if total_applied > 0 else "not_started",
        },
    }


def get_programme_status(programme_id: str) -> dict:
    """Quick status summary for a programme."""
    sb = get_supabase_admin()

    blocks = sb.table("programme_blocks").select("id").eq("programme_id", programme_id).execute()
    apps = sb.table("programme_applications").select("status").eq("programme_id", programme_id).execute()
    adjustments = sb.table("programme_adjustments").select("id").eq("programme_id", programme_id).execute()

    apps_data = apps.data or []
    applied = sum(1 for a in apps_data if a["status"] == "applied")
    pending = sum(1 for a in apps_data if a["status"] == "pending")
    skipped = sum(1 for a in apps_data if a["status"] == "skipped")

    return {
        "num_blocks": len(blocks.data or []),
        "applications_applied": applied,
        "applications_pending": pending,
        "applications_skipped": skipped,
        "adjustments_made": len(adjustments.data or []),
    }
