"""Soil correction calculators — lime, gypsum, organic matter recommendations.

These generate pre-season correction applications for the programme builder
based on the full soil analysis context (not just nutrient targets).
"""

from __future__ import annotations

import math

# Acidophilic crops that prefer lower pH
ACID_LOVING_CROPS = {"blueberry", "tea", "pineapple", "rooibos"}

# Buffer factor: tonnes of lime per pH unit per hectare, based on clay %
# Source: SA Fertasa guidelines (approximate)
BUFFER_TABLE = [
    (15, 1.5),    # Sandy: <15% clay
    (25, 2.5),    # Sandy loam: 15-25%
    (35, 3.5),    # Loam: 25-35%
    (45, 4.5),    # Clay loam: 35-45%
    (100, 5.5),   # Clay: >45%
]


def _buffer_factor(clay_pct: float) -> float:
    """Get lime buffer factor from clay percentage."""
    for max_clay, factor in BUFFER_TABLE:
        if clay_pct <= max_clay:
            return factor
    return 5.5


def calculate_lime_requirement(
    soil_values: dict,
    classifications: dict,
    crop: str = "",
) -> dict | None:
    """Calculate lime requirement for pH correction.

    Args:
        soil_values: raw soil analysis values (pH (H2O), pH (KCl), Clay, Org C, etc.)
        classifications: {parameter: classification} from soil analysis
        crop: crop name (to check if acidophilic)

    Returns:
        dict with type, product, rate_t_ha, reason — or None if no lime needed.
    """
    # Get current pH
    ph_h2o = soil_values.get("pH (H2O)")
    ph_kcl = soil_values.get("pH (KCl)")

    if ph_h2o is None and ph_kcl is None:
        return None

    current_ph = float(ph_h2o) if ph_h2o else float(ph_kcl) + 1.0

    # Target pH based on crop
    base_crop = crop.split("(")[0].strip().lower() if crop else ""
    if base_crop in ACID_LOVING_CROPS:
        target_ph = 5.0
    else:
        target_ph = 6.0  # Standard SA target for most crops

    # Only lime if pH is below target
    ph_deficit = target_ph - current_ph
    if ph_deficit <= 0.2:  # Within acceptable range
        return None

    # Get clay % for buffer factor
    clay = float(soil_values.get("Clay", 20) or 20)
    org_c = float(soil_values.get("Org C", 0) or 0)

    buffer = _buffer_factor(clay)

    # Org C adjustment: high organic matter increases buffer capacity
    if org_c > 2.0:
        buffer += 0.5

    lime_t_ha = round(ph_deficit * buffer, 1)

    # Choose lime type: dolomitic if Mg is also low, calcitic otherwise
    mg_class = classifications.get("Mg", "")
    if mg_class in ("Very Low", "Low"):
        product = "Dolomitic Lime"
        product_note = "Dolomitic chosen — Mg also low"
    else:
        product = "Calcitic Lime"
        product_note = ""

    reason = f"pH (H2O) {current_ph:.1f} → target {target_ph:.1f}"
    if product_note:
        reason += f" ({product_note})"

    return {
        "type": "lime",
        "product": product,
        "rate": f"{lime_t_ha} t/ha",
        "rate_value": lime_t_ha * 1000,  # kg/ha for calculations
        "timing": "Pre-season",
        "reason": reason,
    }


def calculate_gypsum_requirement(
    soil_values: dict,
    classifications: dict,
    ratio_results: list[dict] | None = None,
) -> dict | None:
    """Calculate gypsum requirement for Na displacement.

    Args:
        soil_values: raw soil analysis values
        classifications: {parameter: classification}
        ratio_results: ratio evaluation results from soil analysis

    Returns:
        dict with type, product, rate_kg_ha, reason — or None if not needed.
    """
    na_value = soil_values.get("Na")
    na_class = classifications.get("Na", "")

    if na_value is None:
        return None

    na_val = float(na_value)

    # Only recommend gypsum if Na is High or Very High
    if na_class not in ("High", "Very High"):
        return None

    # Check K:Na ratio
    k_na_info = ""
    if ratio_results:
        for r in ratio_results:
            name = r.get("ratio", r.get("name", ""))
            if "K" in name and "Na" in name:
                actual = r.get("actual", 0)
                status = r.get("status", "")
                ideal = r.get("ideal_range", "")
                if status in ("Below", "below"):
                    k_na_info = f"K:Na ratio {actual} below ideal {ideal}"
                break

    # Simplified gypsum calculation
    # Target: reduce Na to "Optimal" level (~50 mg/kg for most soils)
    target_na = 50
    na_excess = max(0, na_val - target_na)

    # Gypsum rate: approximately 5-6 kg gypsum per mg/kg Na to displace
    # This is a simplified SA guideline — actual rate depends on CEC and clay
    clay = float(soil_values.get("Clay", 20) or 20)
    gypsum_factor = 4 + (clay / 20)  # Higher clay = more gypsum needed
    gypsum_kg_ha = round(na_excess * gypsum_factor)

    if gypsum_kg_ha < 100:  # Below practical application threshold
        return None

    reason = f"Na {na_val:.0f} mg/kg ({na_class})"
    if k_na_info:
        reason += f", {k_na_info}"

    return {
        "type": "gypsum",
        "product": "Gypsum",
        "rate": f"{gypsum_kg_ha} kg/ha",
        "rate_value": gypsum_kg_ha,
        "timing": "Pre-season",
        "reason": reason,
    }


def check_organic_carbon(
    soil_values: dict,
    classifications: dict,
) -> dict | None:
    """Flag low organic carbon and recommend increased compost.

    Returns dict with type, note, min_compost_pct — or None if OK.
    """
    org_c = soil_values.get("Org C")
    org_c_class = classifications.get("Org C", "")

    if org_c is None or org_c_class not in ("Very Low", "Low"):
        return None

    org_c_val = float(org_c)

    if org_c_class == "Very Low":
        min_compost = 60
        severity = "critical"
    else:
        min_compost = 55
        severity = "important"

    return {
        "type": "organic_matter",
        "note": f"Org C {org_c_val:.2f}% ({org_c_class}) — compost is {severity} for soil health",
        "min_compost_pct": min_compost,
        "timing": "With blend applications",
        "reason": f"Organic carbon {org_c_val:.2f}% classified as {org_c_class}",
    }


def get_nutrient_explanations(nutrient_targets: list[dict]) -> list[dict]:
    """Extract explanations for nutrients that were adjusted above base requirement.

    Returns list of {nutrient, base_req, final_target, adjustment, reasons}.
    """
    explanations = []
    for t in nutrient_targets:
        nut = t.get("Nutrient", t.get("nutrient", ""))
        base = float(t.get("Base_Req_kg_ha", 0))
        final = float(t.get("Final_Target_kg_ha", t.get("Target_kg_ha", 0)))
        adjustment = float(t.get("Ratio_Adjustment_kg_ha", 0))
        reasons = t.get("Ratio_Reasons", [])
        classification = t.get("Classification", "")
        factor = float(t.get("Factor", 1))

        notes = []
        factored = round(base * factor, 1) if factor < 1 and factor > 0 else None
        ratio_warnings = t.get("Ratio_Warnings", [])

        # Factor adjustment (soil classification)
        if factor < 1 and factor > 0:
            notes.append(f"Reduced to {int(factor*100)}% — soil {nut} is {classification} → {factored} kg/ha")
        elif factor == 0 and base > 0:
            notes.append(f"Not applied — soil {nut} is {classification}")

        # Ratio adjustments (can be positive or negative)
        if adjustment > 0 and reasons:
            notes.append(f"Increased by {adjustment:.1f} kg/ha — {'; '.join(reasons)} → {final} kg/ha")
        elif adjustment < 0 and reasons:
            notes.append(f"Reduced by {abs(adjustment):.1f} kg/ha — {'; '.join(reasons)} → {final} kg/ha")

        # Ratio warnings (no action taken, flagged for agronomist)
        for warn in ratio_warnings:
            notes.append(f"⚠ {warn}")

        if notes and (final > 0 or ratio_warnings):
            explanations.append({
                "nutrient": nut,
                "base_req": round(base, 1),
                "final_target": round(final, 1),
                "notes": notes,
            })

    return explanations


def calculate_all_corrections(
    soil_values: dict,
    classifications: dict,
    ratio_results: list[dict] | None,
    nutrient_targets: list[dict],
    crop: str = "",
) -> dict:
    """Run all correction calculators and return combined result.

    Returns:
        {
            corrections: [lime, gypsum, organic_matter items],
            nutrient_explanations: [{nutrient, base_req, final_target, notes}],
        }
    """
    corrections = []

    lime = calculate_lime_requirement(soil_values, classifications, crop)
    if lime:
        corrections.append(lime)

    gypsum = calculate_gypsum_requirement(soil_values, classifications, ratio_results)
    if gypsum:
        corrections.append(gypsum)

    org_c = check_organic_carbon(soil_values, classifications)
    if org_c:
        corrections.append(org_c)

    explanations = get_nutrient_explanations(nutrient_targets)

    return {
        "corrections": corrections,
        "nutrient_explanations": explanations,
    }


# ── Corrective action calculator ──────────────────────────────────────────

# Build-up factors: kg element per ha needed to raise soil test by 1 mg/kg
# Indexed by CEC category: sandy (<6), medium (6-15), clay (>15)
_BUILDUP_FACTORS = {
    "P":  {"sandy": 5,   "medium": 8,   "clay": 15},
    "K":  {"sandy": 2.5, "medium": 4,   "clay": 6.5},
    "Ca": {"sandy": 7,   "medium": 10,  "clay": 16},
    "Mg": {"sandy": 2.5, "medium": 4,   "clay": 6.5},
}

# Max corrective application per season (kg element/ha), on top of maintenance
_MAX_PER_SEASON = {
    "P":  50,
    "K":  120,
    "Ca": 200,
    "Mg": 60,
}

# Draw-down rates: approximate mg/kg soil test decline per season when
# applying zero fertilizer and cropping at typical removal rates
_DRAWDOWN_RATES = {
    "P":  3,    # Very slow — strongly buffered
    "K":  8,    # Moderate
    "Ca": 5,    # Moderate — also affected by liming
    "Mg": 5,    # Moderate
}

# Nutrients eligible for corrective action (N and micros excluded)
_CORRECTIVE_NUTRIENTS = {"P", "K", "Ca", "Mg"}


def _cec_category(cec: float) -> str:
    if cec < 6:
        return "sandy"
    elif cec <= 15:
        return "medium"
    return "clay"


def calculate_corrective_targets(
    soil_values: dict,
    nutrient_targets: list[dict],
    sufficiency_rows: list[dict],
    param_map_rows: list[dict],
    crop_override_rows: list[dict] | None = None,
) -> dict:
    """Calculate soil correction timelines for nutrients outside optimal range.

    Returns:
        {
            "corrective_items": [
                {
                    "nutrient": "P",
                    "current_mg_kg": 12,
                    "optimal_range": "20-40",
                    "target_mg_kg": 30,
                    "direction": "build-up" | "draw-down",
                    "gap_mg_kg": 18,
                    "annual_corrective_kg_ha": 15,
                    "estimated_seasons": 4,
                    "note": "P: 12 → 30 mg/kg — ~4 seasons at 15 kg/ha above maintenance"
                },
                ...
            ],
            "missing_data": ["CEC", "Clay"]  # empty list if all present
        }
    """
    cec_val = soil_values.get("CEC")
    clay_val = soil_values.get("Clay")

    # Check for missing data
    missing = []
    if cec_val is None or cec_val == "":
        missing.append("CEC")
    if clay_val is None or clay_val == "":
        missing.append("Clay")

    if missing:
        return {"corrective_items": [], "missing_data": missing}

    cec = float(cec_val)
    cec_cat = _cec_category(cec)

    # Build nutrient target lookup
    target_map = {t.get("Nutrient", t.get("nutrient", "")): t for t in nutrient_targets}

    # Build param map lookup (crop_nutrient → soil_parameter)
    param_lookup = {}
    for m in param_map_rows:
        param_lookup[m["crop_nutrient"]] = m["soil_parameter"]

    items = []
    for nut in _CORRECTIVE_NUTRIENTS:
        # Get current soil value
        soil_param = param_lookup.get(nut, nut)
        soil_val = soil_values.get(soil_param)
        if soil_val is None or soil_val == "":
            soil_val = soil_values.get(nut)
        if soil_val is None or soil_val == "":
            continue

        current = float(soil_val)

        # Get optimal range from sufficiency thresholds
        suff_row = next((r for r in sufficiency_rows if r["parameter"] == soil_param), None)
        if not suff_row:
            suff_row = next((r for r in sufficiency_rows if r["parameter"] == nut), None)
        if not suff_row:
            continue

        thresholds = {
            "low_max": float(suff_row["low_max"]),
            "optimal_max": float(suff_row["optimal_max"]),
        }

        # Apply crop overrides if available
        if crop_override_rows:
            override = next(
                (r for r in crop_override_rows if r["parameter"] == soil_param),
                None,
            )
            if override:
                for key in thresholds:
                    if override.get(key) is not None:
                        thresholds[key] = float(override[key])

        opt_low = thresholds["low_max"]
        opt_high = thresholds["optimal_max"]
        opt_mid = round((opt_low + opt_high) / 2, 1)

        classification = target_map.get(nut, {}).get("Classification", "")

        if classification in ("Very Low", "Low"):
            # Build-up needed — target midpoint of optimal
            target = opt_mid
            gap = round(target - current, 1)
            if gap <= 0:
                continue

            buildup_factor = _BUILDUP_FACTORS.get(nut, {}).get(cec_cat, 8)
            total_kg = gap * buildup_factor
            max_season = _MAX_PER_SEASON.get(nut, 100)
            seasons = max(1, math.ceil(total_kg / max_season))
            annual = round(total_kg / seasons, 1)

            items.append({
                "nutrient": nut,
                "current_mg_kg": round(current, 1),
                "optimal_range": f"{opt_low}-{opt_high}",
                "target_mg_kg": target,
                "direction": "build-up",
                "gap_mg_kg": gap,
                "annual_corrective_kg_ha": annual,
                "estimated_seasons": seasons,
                "note": f"{nut}: {current:.0f} → {target:.0f} mg/kg — ~{seasons} season{'s' if seasons != 1 else ''} at {annual:.0f} kg/ha above maintenance",
            })

        elif classification in ("High", "Very High"):
            # Draw-down — target top of optimal range
            target = opt_high
            gap = round(current - target, 1)
            if gap <= 0:
                continue

            drawdown_rate = _DRAWDOWN_RATES.get(nut, 5)
            seasons = max(1, math.ceil(gap / drawdown_rate))

            # Crop removal per season (from nutrient targets base req)
            base_req = float(target_map.get(nut, {}).get("Base_Req_kg_ha", 0))

            items.append({
                "nutrient": nut,
                "current_mg_kg": round(current, 1),
                "optimal_range": f"{opt_low}-{opt_high}",
                "target_mg_kg": target,
                "direction": "draw-down",
                "gap_mg_kg": gap,
                "annual_corrective_kg_ha": 0,  # No extra application needed
                "estimated_seasons": seasons,
                "note": f"{nut}: {current:.0f} → {target:.0f} mg/kg — ~{seasons} season{'s' if seasons != 1 else ''} at reduced application",
            })

    return {"corrective_items": items, "missing_data": []}
