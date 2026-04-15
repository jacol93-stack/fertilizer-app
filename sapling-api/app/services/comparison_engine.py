"""Soil comparison engine — crop impact calculations and rule-based recommendations."""

from __future__ import annotations

CLASSIFICATION_ORDER = ["Very Low", "Low", "Optimal", "High", "Very High"]

NUTRIENTS = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Mo", "Cu"]


def _class_index(cls: str) -> int:
    """Return ordered index of a classification, or -1 if unknown."""
    try:
        return CLASSIFICATION_ORDER.index(cls)
    except ValueError:
        return -1


def _optimal_distance(cls: str) -> int:
    """Distance from Optimal (0 = Optimal, 1 = Low/High, 2 = Very Low/Very High)."""
    idx = _class_index(cls)
    if idx < 0:
        return -1
    return abs(idx - 2)  # Optimal is index 2


def _calc_single_crop_depletion(
    crop_name: str,
    yield_target: float,
    crop_rows: list[dict],
    param_map_rows: list[dict],
) -> list[dict]:
    """Calculate expected depletion for a single crop."""
    crop_row = next((r for r in crop_rows if r["crop"] == crop_name), None)
    if not crop_row:
        return []

    results = []
    for nut in NUTRIENTS:
        per_unit = float(crop_row.get(nut.lower(), 0) or 0)
        depletion = round(per_unit * yield_target, 2)
        map_row = next((r for r in param_map_rows if r["crop_nutrient"] == nut), None)
        soil_param = map_row["soil_parameter"] if map_row else nut
        results.append({"nutrient": nut, "soil_param": soil_param, "depletion_kg_ha": depletion})
    return results


def calculate_crop_impact(
    a1: dict,
    a2: dict,
    crop_rows: list[dict],
    param_map_rows: list[dict],
    crop_history: list[dict] | None = None,
) -> dict:
    """Calculate expected vs actual nutrient changes between two consecutive analyses.

    Args:
        a1: earlier analysis record
        a2: later analysis record
        crop_rows: list of dicts from crop_requirements table
        param_map_rows: list of dicts from soil_parameter_map table
        crop_history: optional list of field_crop_history entries between the two dates

    Returns:
        dict with keys: available, reason, crops, nutrients
    """
    # Check if analyses are from different fields
    f1 = a1.get("field_id")
    f2 = a2.get("field_id")
    if f1 and f2 and f1 != f2:
        return {"available": False, "reason": "Different fields — crop impact not applicable for snapshot comparisons"}

    date1 = a1.get("analysis_date") or a1.get("created_at", "")[:10]
    date2 = a2.get("analysis_date") or a2.get("created_at", "")[:10]

    # Build list of crops to account for
    crops_in_period: list[dict] = []

    if crop_history:
        for entry in crop_history:
            crop_name = entry.get("crop")
            est_yield = entry.get("estimated_yield")
            if crop_name and est_yield:
                crops_in_period.append({
                    "crop": crop_name,
                    "cultivar": entry.get("cultivar", ""),
                    "season": entry.get("season", ""),
                    "yield_target": float(est_yield),
                    "yield_unit": entry.get("yield_unit", ""),
                })

    # Fallback to analysis record crop if no crop history
    if not crops_in_period:
        crop = a2.get("crop") or a1.get("crop")
        yield_target = a2.get("yield_target") or a1.get("yield_target")
        if crop and yield_target:
            crops_in_period.append({
                "crop": crop,
                "cultivar": a2.get("cultivar") or a1.get("cultivar", ""),
                "season": "",
                "yield_target": float(yield_target),
                "yield_unit": a2.get("yield_unit") or a1.get("yield_unit", ""),
            })

    if not crops_in_period:
        return {"available": False, "reason": "No crop data available for this period"}

    # Sum expected depletion across all crops in the period
    sv1 = a1.get("soil_values") or {}
    sv2 = a2.get("soil_values") or {}

    # Build cumulative depletion per nutrient
    cumulative: dict[str, dict] = {}
    unresolved_crops = []

    for crop_info in crops_in_period:
        depletions = _calc_single_crop_depletion(
            crop_info["crop"], crop_info["yield_target"], crop_rows, param_map_rows
        )
        if not depletions:
            unresolved_crops.append(crop_info["crop"])
            continue
        for d in depletions:
            key = d["nutrient"]
            if key not in cumulative:
                cumulative[key] = {"nutrient": key, "soil_param": d["soil_param"], "total_depletion": 0}
            cumulative[key]["total_depletion"] += d["depletion_kg_ha"]

    nutrients = []
    for nut in NUTRIENTS:
        entry = cumulative.get(nut)
        soil_param = entry["soil_param"] if entry else nut
        expected_depletion = round(entry["total_depletion"], 2) if entry else 0

        v1 = sv1.get(soil_param)
        v2 = sv2.get(soil_param)

        if v1 is None or v2 is None:
            nutrients.append({
                "nutrient": nut,
                "soil_param": soil_param,
                "expected_depletion_kg_ha": expected_depletion,
                "value_before": v1,
                "value_after": v2,
                "actual_change": None,
                "interpretation": "Insufficient data — parameter missing from one or both analyses",
            })
            continue

        v1f = float(v1)
        v2f = float(v2)
        actual_change = round(v2f - v1f, 2)

        if expected_depletion == 0:
            if abs(actual_change) > 0.1 * max(abs(v1f), 1):
                interpretation = f"No crop uptake expected but soil changed by {actual_change:+.1f}"
            else:
                interpretation = "Stable — no significant uptake or change"
        else:
            if actual_change < 0:
                pct_change = abs(actual_change / v1f * 100) if v1f != 0 else 0
                if pct_change > 25:
                    interpretation = f"Significant decline ({pct_change:.0f}%) — may exceed crop uptake alone. Possible leaching, erosion, or fixation."
                elif pct_change > 10:
                    interpretation = f"Moderate decline ({pct_change:.0f}%) — consistent with expected crop uptake."
                else:
                    interpretation = f"Slight decline ({pct_change:.0f}%) — less than expected. Possible residual fertilizer effect."
            elif actual_change > 0:
                interpretation = "Increased despite crop uptake — likely fertilizer accumulation or amendment effect."
            else:
                interpretation = "No change — uptake may be offset by fertilizer application."

        nutrients.append({
            "nutrient": nut,
            "soil_param": soil_param,
            "expected_depletion_kg_ha": expected_depletion,
            "value_before": v1f,
            "value_after": v2f,
            "actual_change": actual_change,
            "interpretation": interpretation,
        })

    crops_label = " + ".join(
        f"{c['crop']}" + (f" ({c['season']})" if c.get("season") else "")
        for c in crops_in_period
    )

    return {
        "available": True,
        "crops": crops_in_period,
        "crops_label": crops_label,
        "unresolved_crops": unresolved_crops,
        "date_from": date1,
        "date_to": date2,
        "field_from": a1.get("field", ""),
        "field_to": a2.get("field", ""),
        "nutrients": nutrients,
    }


def generate_recommendations(
    analyses: list[dict],
    crop_impacts: list[dict],
    comparison_type: str = "timeline",
) -> list[dict]:
    """Generate rule-based observations from a set of soil analyses.

    Args:
        analyses: list of analysis records sorted by date (earliest first)
        crop_impacts: list of crop impact results from calculate_crop_impact
        comparison_type: "timeline" (same field) or "snapshot" (different fields)

    Returns:
        list of {type, message, parameters} dicts
    """
    recommendations = []

    if len(analyses) < 2:
        return recommendations

    # Collect all soil parameters across all analyses
    all_params = set()
    for a in analyses:
        sv = a.get("soil_values") or {}
        all_params.update(sv.keys())

    # ── Trend rules (3+ analyses, timeline only) ───────────────────

    if len(analyses) >= 3 and comparison_type == "timeline":
        for param in sorted(all_params):
            values = []
            for a in analyses:
                sv = a.get("soil_values") or {}
                v = sv.get(param)
                if v is not None:
                    try:
                        values.append(float(v))
                    except (ValueError, TypeError):
                        pass

            if len(values) < 3:
                continue

            # Check for consistent decline
            declines = sum(1 for i in range(1, len(values)) if values[i] < values[i - 1])
            increases = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1])

            if declines == len(values) - 1:
                total_drop = ((values[0] - values[-1]) / values[0] * 100) if values[0] != 0 else 0
                msg = f"{param} has declined across all {len(values)} analyses (total change: {total_drop:.0f}%)"
                if "ph" in param.lower():
                    msg += " — consider liming to correct soil acidity"
                recommendations.append({
                    "type": "warning",
                    "message": msg,
                    "parameters": [param],
                })
            elif increases == len(values) - 1:
                total_rise = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                recommendations.append({
                    "type": "info",
                    "message": f"{param} has increased across all {len(values)} analyses (total change: +{total_rise:.0f}%)",
                    "parameters": [param],
                })
            else:
                # Check stability (within 10% range)
                avg = sum(values) / len(values)
                if avg != 0 and all(abs(v - avg) / abs(avg) < 0.10 for v in values):
                    recommendations.append({
                        "type": "success",
                        "message": f"{param} has remained stable across {len(values)} analyses — current management is maintaining levels",
                        "parameters": [param],
                    })

    # ── Classification transition rules (any 2 consecutive) ──────

    first = analyses[0]
    last = analyses[-1]
    cls1 = first.get("classifications") or {}
    cls2 = last.get("classifications") or {}

    for param in sorted(all_params):
        c1 = cls1.get(param, "")
        c2 = cls2.get(param, "")
        if not c1 or not c2 or c1 == c2:
            continue

        d1 = _optimal_distance(c1)
        d2 = _optimal_distance(c2)
        if d1 < 0 or d2 < 0:
            continue

        if d2 < d1:
            # Moved closer to optimal
            recommendations.append({
                "type": "success",
                "message": f"{param} improved from '{c1}' to '{c2}'",
                "parameters": [param],
            })
        elif d2 > d1:
            # Moved away from optimal
            if c2 in ("Very Low", "Very High"):
                rtype = "warning"
            else:
                rtype = "info"
            recommendations.append({
                "type": rtype,
                "message": f"{param} moved from '{c1}' to '{c2}' — monitor and adjust fertilizer program",
                "parameters": [param],
            })

    # ── Ratio rules ──────────────────────────────────────────────

    ratios1 = {r.get("Ratio") or r.get("ratio_name", ""): r for r in (first.get("ratio_results") or [])}
    ratios2 = {r.get("Ratio") or r.get("ratio_name", ""): r for r in (last.get("ratio_results") or [])}

    for ratio_name in set(ratios1.keys()) | set(ratios2.keys()):
        r1 = ratios1.get(ratio_name)
        r2 = ratios2.get(ratio_name)
        if not r1 or not r2:
            continue

        s1 = r1.get("Status") or r1.get("status", "")
        s2 = r2.get("Status") or r2.get("status", "")
        a1_val = r1.get("Actual") or r1.get("actual")
        a2_val = r2.get("Actual") or r2.get("actual")

        if s1 == s2:
            continue

        if s1 != "Ideal" and s2 == "Ideal":
            recommendations.append({
                "type": "success",
                "message": f"{ratio_name} ratio improved to ideal range ({a1_val:.2f} → {a2_val:.2f})",
                "parameters": [ratio_name],
            })
        elif s1 == "Ideal" and s2 != "Ideal":
            recommendations.append({
                "type": "warning",
                "message": f"{ratio_name} ratio moved out of ideal range ({a1_val:.2f} → {a2_val:.2f}) — correction needed",
                "parameters": [ratio_name],
            })

    # ── Crop impact flags (timeline only) ────────────────────────

    if comparison_type != "timeline":
        return recommendations

    for ci in crop_impacts:
        if not ci.get("available"):
            continue
        for n in ci.get("nutrients", []):
            change = n.get("actual_change")
            if change is None:
                continue
            v_before = n.get("value_before")
            if v_before and v_before != 0:
                pct = abs(change / v_before * 100)
                if pct > 40 and change < 0:
                    recommendations.append({
                        "type": "warning",
                        "message": f"{n['nutrient']} ({n['soil_param']}) dropped {pct:.0f}% between {ci['date_from']} and {ci['date_to']} — investigate possible leaching or erosion",
                        "parameters": [n["soil_param"]],
                    })

    return recommendations
