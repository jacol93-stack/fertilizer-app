"""Plan validator — the orthogonal feedback engine.

Takes a plan (list of blends) and the available agronomic context
(targets, recorded actuals, optional leaf classifications) and returns
structured deltas + warnings.

Three callers share it:

  Edit preview (phase B): "if I change this blend, how does the season
      look against targets?"

  Off-programme review (phase C): "farmer applied something we didn't
      recommend — what does the rest of the season need to look like?"

  Manual/guided build (phase D): "agent built a plan by hand; if soil
      or leaf data exists, flag under-feeding, over-feeding, or
      untreated deficiencies."

The function is pure (no DB) so it's cheap to call on hypothetical
states during editing.
"""

from __future__ import annotations

NUTRIENT_KEYS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]


def validate_plan(
    *,
    plan_blends: list[dict],
    nutrient_targets: list[dict] | dict[str, float] | None = None,
    applications_applied: list[dict] | None = None,
    leaf_classifications: dict | None = None,
    tolerance_pct: float = 10.0,
) -> dict:
    """Compute feedback for a plan.

    Args:
        plan_blends: list of blend dicts with `blend_nutrients`
            (per-nutrient kg/ha) and optional `rate_kg_ha`.
        nutrient_targets: the target season totals, either as the
            nutrient_targets JSONB shape (list of dicts) or a plain
            {nutrient: kg_ha} dict. When None, comparisons against
            target are skipped and only structural warnings returned.
        applications_applied: list of recorded applications that have
            already been done. Each needs `actual_rate_kg_ha` and
            either a `nutrients_delivered` dict or a link to a
            planned_blend whose recipe we use.
        leaf_classifications: {element: classification} from a leaf
            analysis. Elements classified Deficient / Low that aren't
            addressed in the plan are surfaced as warnings.
        tolerance_pct: per-nutrient +/- band within which delta is
            treated as "on target" (no warning).

    Returns:
        {
            per_nutrient: [
                {nutrient, target_kg_ha, planned_kg_ha, applied_kg_ha,
                 delivered_kg_ha, delta_kg_ha, pct_of_target, status}
            ],
            season_totals: {target: {...}, planned: {...}, applied: {...},
                           delivered: {...}},
            warnings: [{kind, nutrient?, blend_id?, severity, message}],
            leaf_flags: [{element, classification, addressed: bool,
                         suggested_action}],
            summary: {
                on_target_count, under_target_count, over_target_count,
                unaddressed_leaf_count, total_warnings,
            },
        }
    """
    target_map = _normalise_targets(nutrient_targets)

    # Per-nutrient sums across the plan
    planned = {n: 0.0 for n in NUTRIENT_KEYS}
    for blend in plan_blends or []:
        for k, v in _nutrients_of(blend).items():
            if k in planned:
                planned[k] += v

    # Per-nutrient sums across recorded actuals. For actuals without
    # explicit per-nutrient breakdown, use the linked planned blend's
    # recipe * actual_rate / planned_rate ratio.
    applied = {n: 0.0 for n in NUTRIENT_KEYS}
    blend_by_id = {b.get("id"): b for b in (plan_blends or []) if b.get("id")}
    for app in applications_applied or []:
        if app.get("status") and app["status"] != "applied":
            continue
        delivered = _applied_nutrients(app, blend_by_id)
        for k, v in delivered.items():
            if k in applied:
                applied[k] += v

    # Plan as a whole: what's going to be delivered = already applied
    # + remaining planned. For a plan where nothing has been applied
    # yet, delivered == planned.
    delivered = {n: planned[n] + applied[n] for n in NUTRIENT_KEYS}
    # But "planned" alone still represents what the PLAN calls for
    # over the whole season regardless of actuals — we keep both so
    # callers can distinguish "plan says" from "total likely to land".

    # Build per-nutrient comparison rows
    per_nutrient = []
    on_target = under = over = 0
    warnings: list[dict] = []

    for n in NUTRIENT_KEYS:
        target = target_map.get(n, 0.0) if target_map else 0.0
        p = planned[n]
        a = applied[n]
        d = delivered[n]

        has_target = target > 0.01
        delta = d - target if has_target else 0.0
        pct = (d / target * 100.0) if has_target else None
        status = _status_for(target, d, tolerance_pct) if has_target else "no_target"

        if status == "under":
            under += 1
            severity = "high" if pct is not None and pct < (100 - 2 * tolerance_pct) else "medium"
            warnings.append({
                "kind": "under_target",
                "nutrient": n,
                "severity": severity,
                "message": (
                    f"{n.upper()}: plan delivers {d:.1f} vs {target:.1f} kg/ha target "
                    f"({pct:.0f}% of target, short {abs(delta):.1f} kg/ha)"
                ),
            })
        elif status == "over":
            over += 1
            severity = "high" if pct is not None and pct > (100 + 3 * tolerance_pct) else "medium"
            warnings.append({
                "kind": "over_target",
                "nutrient": n,
                "severity": severity,
                "message": (
                    f"{n.upper()}: plan delivers {d:.1f} vs {target:.1f} kg/ha target "
                    f"({pct:.0f}% of target, excess {delta:.1f} kg/ha)"
                ),
            })
        elif status == "on_target":
            on_target += 1

        per_nutrient.append({
            "nutrient": n,
            "target_kg_ha": round(target, 2) if has_target else None,
            "planned_kg_ha": round(p, 2),
            "applied_kg_ha": round(a, 2),
            "delivered_kg_ha": round(d, 2),
            "delta_kg_ha": round(delta, 2) if has_target else None,
            "pct_of_target": round(pct, 1) if pct is not None else None,
            "status": status,
        })

    # Plan-level structural warnings
    warnings.extend(_structural_warnings(plan_blends or []))

    # Leaf flags — elements flagged by a leaf analysis that aren't being
    # addressed in the plan (no nutrient mass delivered for them).
    leaf_flags = _leaf_flags(leaf_classifications, delivered)
    unaddressed_leaf = sum(1 for f in leaf_flags if not f["addressed"])
    if unaddressed_leaf:
        warnings.append({
            "kind": "unaddressed_leaf",
            "severity": "high",
            "message": (
                f"{unaddressed_leaf} leaf-flagged element(s) not addressed "
                "by the current plan"
            ),
        })

    return {
        "per_nutrient": per_nutrient,
        "season_totals": {
            "target": {k: round(v, 2) for k, v in target_map.items()} if target_map else {},
            "planned": {k: round(v, 2) for k, v in planned.items() if v > 0.001},
            "applied": {k: round(v, 2) for k, v in applied.items() if v > 0.001},
            "delivered": {k: round(v, 2) for k, v in delivered.items() if v > 0.001},
        },
        "warnings": warnings,
        "leaf_flags": leaf_flags,
        "summary": {
            "on_target_count": on_target,
            "under_target_count": under,
            "over_target_count": over,
            "unaddressed_leaf_count": unaddressed_leaf,
            "total_warnings": len(warnings),
            "has_targets": bool(target_map),
            "tolerance_pct": tolerance_pct,
        },
    }


# ── helpers ────────────────────────────────────────────────────────────


def _normalise_targets(targets) -> dict[str, float]:
    """Accept either the nutrient_targets JSONB list shape or a plain
    {n: float} dict. Returns lowercased single-letter keys."""
    if not targets:
        return {}
    if isinstance(targets, dict):
        return {k.lower(): float(v) for k, v in targets.items() if v is not None}

    out: dict[str, float] = {}
    for t in targets:
        nut = (t.get("Nutrient") or t.get("nutrient") or "").lower()
        val = t.get("Final_Target_kg_ha")
        if val is None:
            val = t.get("Target_kg_ha") or t.get("target_kg_ha")
        if nut and val is not None:
            try:
                out[nut] = float(val)
            except (TypeError, ValueError):
                pass
    return out


def _nutrients_of(blend: dict) -> dict[str, float]:
    """Extract per-nutrient kg/ha from a blend dict. Handles both the
    live programme_blends shape (blend_nutrients dict) and the feeding
    plan item shape (n_kg_ha/p_kg_ha/...)."""
    raw = blend.get("blend_nutrients") or {}
    out: dict[str, float] = {}
    if isinstance(raw, dict) and raw:
        for k, v in raw.items():
            if k.lower() in NUTRIENT_KEYS:
                try:
                    out[k.lower()] = float(v or 0)
                except (TypeError, ValueError):
                    pass
    # Feeding-plan item shape
    for n in NUTRIENT_KEYS:
        key = f"{n}_kg_ha"
        if key in blend and blend[key] is not None and n not in out:
            try:
                out[n] = float(blend[key])
            except (TypeError, ValueError):
                pass
    return out


def _applied_nutrients(app: dict, blend_by_id: dict) -> dict[str, float]:
    """Best-guess at what nutrients the recorded application delivered.

    Preference order:
      1. Explicit `nutrients_delivered` on the application
      2. Linked planned_blend's recipe × (actual_rate / planned_rate)
      3. Empty — caller can't attribute
    """
    explicit = app.get("nutrients_delivered")
    if isinstance(explicit, dict) and explicit:
        return {k.lower(): float(v or 0) for k, v in explicit.items() if k.lower() in NUTRIENT_KEYS}

    planned_id = app.get("planned_blend_id")
    planned = blend_by_id.get(planned_id) if planned_id else None
    if not planned:
        return {}

    planned_nut = _nutrients_of(planned)
    planned_rate = float(planned.get("rate_kg_ha") or 0)
    actual_rate = float(app.get("actual_rate_kg_ha") or 0)
    if planned_rate < 0.01 or actual_rate < 0.01:
        return planned_nut  # rate info missing — assume plan intent
    scale = actual_rate / planned_rate
    return {k: v * scale for k, v in planned_nut.items()}


def _status_for(target: float, delivered: float, tol_pct: float) -> str:
    lo = target * (1 - tol_pct / 100.0)
    hi = target * (1 + tol_pct / 100.0)
    if delivered < lo:
        return "under"
    if delivered > hi:
        return "over"
    return "on_target"


def _structural_warnings(blends: list[dict]) -> list[dict]:
    """Warnings about plan structure itself, independent of targets."""
    out: list[dict] = []
    if not blends:
        out.append({
            "kind": "empty_plan",
            "severity": "high",
            "message": "Plan has no applications",
        })
        return out

    # Check for blends with no nutrient content at all
    for b in blends:
        if not _nutrients_of(b):
            out.append({
                "kind": "blend_no_nutrients",
                "blend_id": b.get("id"),
                "severity": "medium",
                "message": (
                    f"Blend in month {b.get('application_month', '?')} "
                    f"({b.get('stage_name') or 'unnamed'}) has no "
                    f"nutrient content defined"
                ),
            })

    # Check for stale months (nothing planned in a wide calendar gap)
    months = sorted({b.get("application_month") for b in blends if b.get("application_month")})
    # No warning fired for gaps — legitimate for dormant periods.
    # Placeholder for future cadence heuristics.

    return out


def _leaf_flags(classifications: dict | None, delivered: dict[str, float]) -> list[dict]:
    """Convert leaf classifications into plan-aware flags.

    An element is "addressed" if the plan delivers any mass of that
    nutrient. We're not checking whether the amount is sufficient to
    correct the deficiency — that's downstream. Just: is it being
    supplied at all?
    """
    if not classifications:
        return []

    out = []
    for element, classification in classifications.items():
        cls = str(classification or "").strip()
        if cls not in ("Deficient", "Low", "Excess", "Toxic"):
            continue
        key = element.lower()
        # Handle common element name variations
        if key in {"nitrogen", "n"}:
            key = "n"
        elif key in {"phosphorus", "p"}:
            key = "p"
        elif key in {"potassium", "k"}:
            key = "k"
        elif key in {"calcium", "ca"}:
            key = "ca"
        elif key in {"magnesium", "mg"}:
            key = "mg"
        elif key in {"sulphur", "sulfur", "s"}:
            key = "s"
        elif key in {"iron", "fe"}:
            key = "fe"
        elif key in {"boron", "b"}:
            key = "b"
        elif key in {"manganese", "mn"}:
            key = "mn"
        elif key in {"zinc", "zn"}:
            key = "zn"
        elif key in {"molybdenum", "mo"}:
            key = "mo"
        elif key in {"copper", "cu"}:
            key = "cu"

        if key not in NUTRIENT_KEYS:
            continue

        addressed = delivered.get(key, 0.0) > 0.01
        action = (
            "reduce_supply" if cls in ("Excess", "Toxic")
            else "add_application"
        )
        out.append({
            "element": element,
            "nutrient_key": key,
            "classification": cls,
            "addressed": addressed,
            "suggested_action": action,
        })
    return out
