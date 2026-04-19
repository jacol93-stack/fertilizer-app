"""Plan comparison — Phase E.

For a given programme, produces a three-way view per block:

  baseline  → the snapshot taken at activation (programme_baselines)
  current   → the live programme_blends state
  applied   → what was actually recorded as happening

Each divergence between baseline and current carries a reason derived
from the audit log or the programme_adjustments row that caused it.
The tracker UI reads this and highlights changes with attribution —
"what must now be done vs the original plan, and why".

Pure-ish: takes supabase client to read, returns a structured payload.
No writes.
"""

from __future__ import annotations

from typing import Any

NUTRIENT_KEYS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]


def compare_plan(sb, programme_id: str) -> dict:
    """Return the comparison payload for a programme.

    Shape:
    {
        has_baseline: bool,
        baseline: {...frozen snapshot...} | None,
        blocks: [
            {
                block_id, block_name, crop, blend_group,
                baseline_blends: [...],
                current_blends: [...],
                applications: [...],
                per_month_diff: [
                    {month, baseline, current, actual,
                     status: 'unchanged'|'edited'|'added'|'removed'|'applied',
                     nutrient_delta: {...}}
                ],
                season_totals: {
                    baseline: {n, p, k, ...},
                    current: {...},
                    applied: {...},
                },
                attributions: [
                    {kind: 'adjustment'|'manual_edit'|'off_programme',
                     at, actor, reference, summary}
                ],
            }
        ]
    }
    """
    # Fetch everything upfront so we don't round-trip per block
    baselines = (
        sb.table("programme_baselines").select("*")
        .eq("programme_id", programme_id).eq("is_current", True)
        .limit(1).execute().data
    )
    baseline = baselines[0] if baselines else None

    blocks = (
        sb.table("programme_blocks").select("*")
        .eq("programme_id", programme_id).execute().data
    ) or []
    current_blends = (
        sb.table("programme_blends").select("*")
        .eq("programme_id", programme_id).execute().data
    ) or []
    applications = (
        sb.table("programme_applications").select("*")
        .eq("programme_id", programme_id).execute().data
    ) or []
    adjustments = (
        sb.table("programme_adjustments").select("*")
        .eq("programme_id", programme_id).eq("status", "applied")
        .execute().data
    ) or []

    baseline_blocks_by_id = {}
    baseline_blends_by_group: dict[str, list[dict]] = {}
    if baseline:
        for b in baseline.get("blocks") or []:
            baseline_blocks_by_id[b["id"]] = b
        for bl in baseline.get("blends") or []:
            baseline_blends_by_group.setdefault(bl.get("blend_group") or "_", []).append(bl)

    current_blends_by_group: dict[str, list[dict]] = {}
    for bl in current_blends:
        current_blends_by_group.setdefault(bl.get("blend_group") or "_", []).append(bl)

    apps_by_block: dict[str, list[dict]] = {}
    for a in applications:
        if a.get("block_id"):
            apps_by_block.setdefault(a["block_id"], []).append(a)

    out_blocks: list[dict] = []
    for block in blocks:
        block_id = block["id"]
        group = block.get("blend_group") or "_"
        baseline_blends = baseline_blends_by_group.get(group, [])
        live_blends = current_blends_by_group.get(group, [])
        block_apps = apps_by_block.get(block_id, [])
        block_adj = [a for a in adjustments if a.get("block_id") == block_id]

        per_month = _per_month_diff(baseline_blends, live_blends, block_apps)
        totals = _season_totals(baseline_blends, live_blends, block_apps)
        attributions = _build_attributions(block_adj)

        out_blocks.append({
            "block_id": block_id,
            "block_name": block.get("name"),
            "crop": block.get("crop"),
            "blend_group": block.get("blend_group"),
            "baseline_blends": baseline_blends,
            "current_blends": live_blends,
            "applications": block_apps,
            "per_month_diff": per_month,
            "season_totals": totals,
            "attributions": attributions,
        })

    return {
        "has_baseline": baseline is not None,
        "baseline": {
            "id": baseline.get("id"),
            "created_at": baseline.get("created_at"),
            "reason": baseline.get("reason"),
        } if baseline else None,
        "blocks": out_blocks,
    }


def _per_month_diff(
    baseline_blends: list[dict],
    current_blends: list[dict],
    applications: list[dict],
) -> list[dict]:
    """One row per month that appears in any of the three sources.
    Status indicates how current compares to baseline for that month."""
    baseline_by_month: dict[int, dict] = {
        (b.get("application_month") or 0): b for b in baseline_blends
    }
    current_by_month: dict[int, dict] = {
        (b.get("application_month") or 0): b for b in current_blends
    }
    applied_by_month: dict[int, list[dict]] = {}
    for a in applications:
        # Derive month from actual_date if present
        month = _month_of_application(a)
        if month:
            applied_by_month.setdefault(month, []).append(a)

    months = sorted(set(baseline_by_month) | set(current_by_month) | set(applied_by_month))
    rows: list[dict] = []
    for m in months:
        if m == 0:
            continue
        b = baseline_by_month.get(m)
        c = current_by_month.get(m)
        a_list = applied_by_month.get(m) or []

        if b and c:
            b_nut = _nuts(b)
            c_nut = _nuts(c)
            status = "unchanged" if _nut_equal(b_nut, c_nut) and _rates_equal(b, c) else "edited"
            delta = {k: round(c_nut.get(k, 0) - b_nut.get(k, 0), 2)
                     for k in set(b_nut) | set(c_nut)
                     if abs(c_nut.get(k, 0) - b_nut.get(k, 0)) >= 0.05}
        elif b and not c:
            status = "removed"
            delta = {k: -round(v, 2) for k, v in _nuts(b).items() if v > 0.01}
        elif c and not b:
            status = "added"
            delta = {k: round(v, 2) for k, v in _nuts(c).items() if v > 0.01}
        else:
            status = "applied_only"
            delta = {}

        rows.append({
            "month": m,
            "baseline": _summarise_blend(b) if b else None,
            "current": _summarise_blend(c) if c else None,
            "actual": [_summarise_app(a) for a in a_list],
            "status": status,
            "nutrient_delta": delta,
        })
    return rows


def _season_totals(
    baseline_blends: list[dict],
    current_blends: list[dict],
    applications: list[dict],
) -> dict:
    baseline_tot = {k: 0.0 for k in NUTRIENT_KEYS}
    current_tot = {k: 0.0 for k in NUTRIENT_KEYS}
    applied_tot = {k: 0.0 for k in NUTRIENT_KEYS}

    for b in baseline_blends:
        for k, v in _nuts(b).items():
            baseline_tot[k] = baseline_tot.get(k, 0.0) + v
    for b in current_blends:
        for k, v in _nuts(b).items():
            current_tot[k] = current_tot.get(k, 0.0) + v

    blend_by_id = {b["id"]: b for b in current_blends if b.get("id")}
    for app in applications:
        if (app.get("status") or "").lower() != "applied":
            continue
        delivered = _applied_nutrients(app, blend_by_id)
        for k, v in delivered.items():
            applied_tot[k] = applied_tot.get(k, 0.0) + v

    return {
        "baseline": {k: round(v, 2) for k, v in baseline_tot.items() if v > 0.001},
        "current": {k: round(v, 2) for k, v in current_tot.items() if v > 0.001},
        "applied": {k: round(v, 2) for k, v in applied_tot.items() if v > 0.001},
    }


def _build_attributions(adjustments: list[dict]) -> list[dict]:
    """Human-readable list of what drove divergence between baseline
    and current. Each row is an applied adjustment."""
    out = []
    for a in adjustments:
        out.append({
            "kind": a.get("trigger_type") or "adjustment",
            "adjustment_id": a.get("id"),
            "at": a.get("applied_at") or a.get("created_at"),
            "actor": a.get("applied_by") or a.get("created_by"),
            "summary": a.get("notes") or (a.get("adjustment_data") or {}).get("summary"),
        })
    return out


# ── small helpers ──────────────────────────────────────────────────────


def _nuts(blend: dict | None) -> dict[str, float]:
    if not blend:
        return {}
    raw = blend.get("blend_nutrients") or {}
    if not isinstance(raw, dict):
        return {}
    out = {}
    for k, v in raw.items():
        key = k.lower()
        if key in NUTRIENT_KEYS:
            try:
                out[key] = float(v or 0)
            except (TypeError, ValueError):
                pass
    return out


def _nut_equal(a: dict, b: dict) -> bool:
    keys = set(a) | set(b)
    return all(abs(a.get(k, 0) - b.get(k, 0)) < 0.05 for k in keys)


def _rates_equal(a: dict, b: dict) -> bool:
    return abs((a.get("rate_kg_ha") or 0) - (b.get("rate_kg_ha") or 0)) < 0.5


def _summarise_blend(b: dict) -> dict:
    return {
        "id": b.get("id"),
        "stage_name": b.get("stage_name"),
        "application_month": b.get("application_month"),
        "method": b.get("method"),
        "rate_kg_ha": b.get("rate_kg_ha"),
        "sa_notation": b.get("sa_notation"),
        "nutrients": _nuts(b),
    }


def _summarise_app(a: dict) -> dict:
    return {
        "id": a.get("id"),
        "actual_date": a.get("actual_date"),
        "actual_rate_kg_ha": a.get("actual_rate_kg_ha"),
        "product_name": a.get("product_name"),
        "is_sapling_product": a.get("is_sapling_product"),
        "method": a.get("method"),
        "status": a.get("status"),
    }


def _month_of_application(a: dict) -> int | None:
    date = a.get("actual_date")
    if not date:
        return None
    try:
        return int(str(date).split("-")[1])
    except (IndexError, ValueError):
        return None


def _applied_nutrients(app: dict, blend_by_id: dict) -> dict[str, float]:
    """Same contract as in plan_validator — attribute an application's
    nutrient delivery via explicit delivery or recipe × rate scaling."""
    explicit = app.get("nutrients_delivered")
    if isinstance(explicit, dict) and explicit:
        out = {}
        for k, v in explicit.items():
            key = k.lower()
            if key in NUTRIENT_KEYS:
                try:
                    out[key] = float(v or 0)
                except (TypeError, ValueError):
                    pass
        return out

    planned_id = app.get("planned_blend_id")
    planned = blend_by_id.get(planned_id) if planned_id else None
    if not planned:
        return {}
    planned_nut = _nuts(planned)
    planned_rate = float(planned.get("rate_kg_ha") or 0)
    actual_rate = float(app.get("actual_rate_kg_ha") or 0)
    if planned_rate < 0.01 or actual_rate < 0.01:
        return planned_nut
    scale = actual_rate / planned_rate
    return {k: v * scale for k, v in planned_nut.items()}
