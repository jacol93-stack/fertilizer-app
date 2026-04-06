"""Soil analysis classification, adjustment, and nutrient target calculation."""

NUTRIENTS_SOIL = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Mo", "Cu"]

SOIL_CLASSIFICATIONS = ["Very Low", "Low", "Optimal", "High", "Very High"]

NUTRIENT_GROUP_MAP = {
    "N":  "N",
    "P":  "P",
    "K":  "cations",
    "Ca": "cations",
    "Mg": "cations",
    "S":  "cations",
    "Fe": "micro",
    "B":  "micro",
    "Mn": "micro",
    "Zn": "micro",
    "Mo": "micro",
    "Cu": "micro",
}


def classify_soil_value(value, param_name, sufficiency_rows, crop_override_rows=None):
    """Classify a soil analysis value against sufficiency thresholds.

    Uses crop-specific overrides when available, falling back to universal thresholds.

    Args:
        value: soil test value (float or None)
        param_name: parameter name matching sufficiency table
        sufficiency_rows: list of dicts from soil_sufficiency table (universal)
        crop_override_rows: optional list of dicts from crop_sufficiency_overrides table
    """
    if value is None:
        return ""

    # Start with universal thresholds
    row = next((r for r in sufficiency_rows if r["parameter"] == param_name), None)
    if not row:
        return ""

    # Merge with crop-specific overrides if available
    thresholds = {
        "very_low_max": float(row["very_low_max"]),
        "low_max": float(row["low_max"]),
        "optimal_max": float(row["optimal_max"]),
        "high_max": float(row["high_max"]),
    }

    if crop_override_rows:
        override = next(
            (r for r in crop_override_rows if r["parameter"] == param_name),
            None,
        )
        if override:
            for key in thresholds:
                if override.get(key) is not None:
                    thresholds[key] = float(override[key])

    if value <= thresholds["very_low_max"]:
        return "Very Low"
    elif value <= thresholds["low_max"]:
        return "Low"
    elif value <= thresholds["optimal_max"]:
        return "Optimal"
    elif value <= thresholds["high_max"]:
        return "High"
    else:
        return "Very High"


def get_adjustment_factor(classification, adjustment_rows, nutrient=None):
    """Look up adjustment factor for a soil classification level.

    Args:
        classification: string like "Very Low", "Low", etc.
        adjustment_rows: list of dicts from adjustment_factors table
        nutrient: optional nutrient name to look up group-specific factor
    """
    if not classification:
        return 1.0

    # Try group-specific lookup first
    if nutrient:
        group = NUTRIENT_GROUP_MAP.get(nutrient)
        if group:
            row = next(
                (r for r in adjustment_rows
                 if r["classification"] == classification
                 and r.get("nutrient_group") == group),
                None,
            )
            if row:
                return float(row["factor"])

    # Fallback: match by classification only (backward compat)
    row = next(
        (r for r in adjustment_rows if r["classification"] == classification),
        None,
    )
    if not row:
        return 1.0
    return float(row["factor"])


def calculate_nutrient_targets(crop_name, yield_target, soil_values,
                                crop_rows, sufficiency_rows, adjustment_rows, param_map_rows,
                                crop_override_rows=None):
    """Calculate adjusted nutrient targets (kg/ha) for a crop.

    Args:
        crop_name: crop name matching crop_requirements table
        yield_target: expected yield in the crop's yield unit
        soil_values: dict of {soil_parameter: value} from lab results
        crop_rows: list of dicts from crop_requirements table
        sufficiency_rows: list of dicts from soil_sufficiency table
        adjustment_rows: list of dicts from adjustment_factors table
        param_map_rows: list of dicts from soil_parameter_map table
    """
    crop_row = next((r for r in crop_rows if r["crop"] == crop_name), None)
    if not crop_row:
        return []

    results = []
    for nut in NUTRIENTS_SOIL:
        per_unit = float(crop_row.get(nut.lower(), 0) or 0)
        base_req = round(per_unit * yield_target, 2)

        # Find the soil parameter mapped to this crop nutrient
        map_row = next((r for r in param_map_rows if r["crop_nutrient"] == nut), None)
        soil_param = map_row["soil_parameter"] if map_row else nut
        soil_val = soil_values.get(soil_param)
        # Fallback: try the short nutrient name (e.g. "N" when map says "N (total)")
        if soil_val is None and soil_param != nut:
            soil_val = soil_values.get(nut)

        classification = classify_soil_value(soil_val, soil_param, sufficiency_rows, crop_override_rows)
        factor = get_adjustment_factor(classification, adjustment_rows, nutrient=nut)
        adjusted = round(base_req * factor, 2)

        results.append({
            "Nutrient": nut,
            "Per_Unit": per_unit,
            "Base_Req_kg_ha": base_req,
            "Soil_Value": soil_val if soil_val is not None else "",
            "Classification": classification,
            "Factor": factor,
            "Target_kg_ha": adjusted,
        })

    return results


def adjust_targets_for_ratios(targets, ratio_results, soil_values, ratio_rows):
    """Adjust nutrient targets to correct imbalanced soil ratios.

    Sufficiency-first approach:
    - Start with sufficiency-based targets (already calculated)
    - Check each ratio against ideal ranges
    - If a ratio is off, prefer reducing the over-supplied nutrient
    - Only increase a nutrient if it is NOT already High/Very High
    - Exception: P:Zn — always boost Zn because high P blocks Zn uptake

    Args:
        targets: list of dicts from calculate_nutrient_targets()
        ratio_results: list of dicts from evaluate_ratios()
        soil_values: dict of soil parameter values
        ratio_rows: list of dicts from ideal_ratios table

    Returns:
        Updated targets list with ratio adjustment fields added
    """
    # Build lookup: nutrient name -> target dict
    target_map = {t["Nutrient"]: t for t in targets}

    HIGH_CLASSIFICATIONS = {"High", "Very High"}

    def is_high(nutrient):
        """Check if a nutrient's soil classification is High or Very High."""
        t = target_map.get(nutrient)
        return t is not None and t.get("Classification") in HIGH_CLASSIFICATIONS

    # Track adjustments: {nutrient: [(reason, extra_kg_ha), ...]}
    # Positive extra = increase, negative extra = reduction
    adjustments: dict[str, list[tuple[str, float]]] = {}
    # Track ratio warnings when we can't correct via fertilizer
    warnings: dict[str, list[str]] = {}

    def sv(key):
        v = soil_values.get(key)
        return float(v) if v is not None and v != "" else None

    cec = sv("CEC")
    ca = sv("Ca")
    mg = sv("Mg")
    k = sv("K")
    na = sv("Na")

    def _ratio_adjust_pair(ratio_name, actual, ideal_min, ideal_max,
                           numerator_nut, denominator_nut):
        """Handle a ratio imbalance between two nutrients (A:B ratio).

        Calculates the exact kg/ha adjustment needed to move the fertilizer
        application ratio toward the ideal midpoint.

        Prefers reducing the over-supplied nutrient. Only increases a nutrient
        if it is NOT already High/Very High. If neither is possible, warns.

        For A:B below ideal: either reduce B or increase A.
        For A:B above ideal: either reduce A or increase B.
        """
        ideal_mid = (ideal_min + ideal_max) / 2
        below = actual < ideal_min
        reason_dir = "below" if below else "above"
        reason = f"{ratio_name} {actual:.1f} {reason_dir} ideal {ideal_min}-{ideal_max}"

        # Determine which to increase/reduce based on direction
        if below:
            increase_nut, reduce_nut = numerator_nut, denominator_nut
        else:
            increase_nut, reduce_nut = denominator_nut, numerator_nut

        # Calculate exact adjustment needed
        # Current applied: num_target / denom_target = actual ratio of application
        num_t = target_map.get(numerator_nut, {}).get("Target_kg_ha", 0)
        den_t = target_map.get(denominator_nut, {}).get("Target_kg_ha", 0)

        # Strategy 1: reduce the over-supplied nutrient
        if reduce_nut in target_map:
            current = target_map[reduce_nut]["Target_kg_ha"]
            if current > 0:
                # Calculate what reduce_nut target should be to hit ideal_mid
                other = target_map.get(increase_nut, {}).get("Target_kg_ha", 0)
                if other > 0:
                    if reduce_nut == denominator_nut:
                        # A:B ratio — reduce B so A/B = ideal_mid → B = A / ideal_mid
                        ideal_reduce = other / ideal_mid
                    else:
                        # A:B ratio — reduce A so A/B = ideal_mid → A = B * ideal_mid
                        ideal_reduce = other * ideal_mid
                    reduction = round(current - ideal_reduce, 2)
                    # Cap: never reduce by more than 50% of current target
                    reduction = min(reduction, current * 0.5)
                    if reduction > 0:
                        adjustments.setdefault(reduce_nut, []).append(
                            (f"{reason} — reducing {reduce_nut}", -reduction)
                        )
                        return

        # Strategy 2: increase the deficient nutrient (only if not already high)
        if not is_high(increase_nut) and increase_nut in target_map:
            current = target_map[increase_nut]["Target_kg_ha"]
            other = target_map.get(reduce_nut, {}).get("Target_kg_ha", 0)
            if current >= 0 and other > 0:
                if increase_nut == numerator_nut:
                    # A:B ratio — increase A so A/B = ideal_mid → A = B * ideal_mid
                    ideal_increase = other * ideal_mid
                else:
                    # A:B ratio — increase B so A/B = ideal_mid → B = A / ideal_mid
                    ideal_increase = other / ideal_mid
                extra = round(ideal_increase - current, 2)
                # Cap: never more than double current target
                extra = min(extra, max(current, 1.0))
                if extra > 0:
                    adjustments.setdefault(increase_nut, []).append(
                        (reason, extra)
                    )
                    return

        # Neither action possible — warn
        warnings.setdefault(increase_nut, []).append(
            f"{reason} — soil {increase_nut} already {target_map.get(increase_nut, {}).get('Classification', 'High')}, monitor via tissue testing"
        )

    for rr in ratio_results:
        ratio_name = rr["Ratio"]
        actual = rr["Actual"]
        ideal_min = rr["Ideal_Min"]
        ideal_max = rr["Ideal_Max"]
        status = rr["Status"]

        if status == "Ideal":
            continue

        if ratio_name == "Ca:Mg" and status in ("Below ideal", "Above ideal"):
            _ratio_adjust_pair("Ca:Mg", actual, ideal_min, ideal_max,
                               numerator_nut="Ca", denominator_nut="Mg")

        elif ratio_name == "Ca:K" and status == "Below ideal":
            _ratio_adjust_pair("Ca:K", actual, ideal_min, ideal_max,
                               numerator_nut="Ca", denominator_nut="K")

        elif ratio_name == "Mg:K" and status == "Below ideal":
            _ratio_adjust_pair("Mg:K", actual, ideal_min, ideal_max,
                               numerator_nut="Mg", denominator_nut="K")

        elif ratio_name == "P:Zn" and status == "Above ideal":
            # Exception: always boost Zn — high P physically blocks Zn uptake
            if "Zn" in target_map:
                current_zn = target_map["Zn"]["Target_kg_ha"]
                current_p = target_map.get("P", {}).get("Target_kg_ha", 0)
                if current_p > 0 and ideal_mid > 0:
                    ideal_zn = current_p / ideal_mid
                    extra = round(max(ideal_zn - current_zn, 0.5), 2)
                else:
                    extra = round(max(current_zn * 0.5, 0.5), 2)
                adjustments.setdefault("Zn", []).append(
                    (f"P:Zn ratio {actual:.1f} above ideal {ideal_min}-{ideal_max} — high P blocks Zn uptake", extra)
                )

        elif ratio_name == "N:S" and status == "Above ideal":
            # N:S high — increase S to match N. Never reduce N (not bankable).
            reason = f"N:S ratio {actual:.1f} above ideal {ideal_min}-{ideal_max}"
            n_target = target_map.get("N", {}).get("Target_kg_ha", 0)
            if not is_high("S") and "S" in target_map and n_target > 0:
                current_s = target_map["S"]["Target_kg_ha"]
                ideal_s = n_target / ideal_mid
                extra = round(ideal_s - current_s, 2)
                extra = min(extra, max(current_s, 2.0))  # Cap
                if extra > 0:
                    adjustments.setdefault("S", []).append((reason, extra))
            else:
                warnings.setdefault("S", []).append(
                    f"{reason} — soil S already {target_map.get('S', {}).get('Classification', 'High')}, monitor via tissue testing"
                )

        elif ratio_name == "K:Na" and status == "Below ideal":
            # K too low relative to Na — always increase K (Na displacement)
            if "K" in target_map and na and na > 0:
                current_k = target_map["K"]["Target_kg_ha"]
                ideal_k = na * ideal_mid  # K needed relative to soil Na
                extra = round(ideal_k - current_k, 2)
                extra = min(extra, max(current_k, 5.0))  # Cap
                if extra > 0:
                    adjustments.setdefault("K", []).append(
                        (f"K:Na ratio {actual:.1f} below ideal {ideal_min}-{ideal_max}", extra)
                    )

        # Base saturation corrections — these already use exact calculations
        elif ratio_name == "Ca base sat." and status == "Below ideal":
            if "Ca" in target_map and not is_high("Ca"):
                current = target_map["Ca"]["Target_kg_ha"]
                shortfall_pct = ideal_min - actual
                if cec and cec > 0:
                    extra_mg_kg = shortfall_pct * cec * 200.4 / 100
                    extra_kg_ha = round(extra_mg_kg * 2 / 1000, 2)
                    extra_kg_ha = min(extra_kg_ha, current * 2)
                    if extra_kg_ha > 0:
                        adjustments.setdefault("Ca", []).append(
                            (f"Ca base sat. {actual:.1f}% below ideal {ideal_min}%", extra_kg_ha)
                        )
            elif is_high("Ca"):
                warnings.setdefault("Ca", []).append(
                    f"Ca base sat. {actual:.1f}% below ideal {ideal_min}% — soil Ca already High, lime may help"
                )

        elif ratio_name == "K base sat." and status == "Below ideal":
            if "K" in target_map and not is_high("K"):
                current = target_map["K"]["Target_kg_ha"]
                shortfall_pct = ideal_min - actual
                if cec and cec > 0:
                    extra_mg_kg = shortfall_pct * cec * 390.98 / 100  # K equivalent weight
                    extra_kg_ha = round(extra_mg_kg * 2 / 1000, 2)
                    extra_kg_ha = min(extra_kg_ha, current * 2)
                    if extra_kg_ha > 0:
                        adjustments.setdefault("K", []).append(
                            (f"K base sat. {actual:.1f}% below ideal {ideal_min}%", extra_kg_ha)
                        )

        elif ratio_name == "Mg base sat." and status == "Below ideal":
            if "Mg" in target_map and not is_high("Mg"):
                current = target_map["Mg"]["Target_kg_ha"]
                shortfall_pct = ideal_min - actual
                if cec and cec > 0:
                    extra_mg_kg = shortfall_pct * cec * 121.56 / 100  # Mg equivalent weight
                    extra_kg_ha = round(extra_mg_kg * 2 / 1000, 2)
                    extra_kg_ha = min(extra_kg_ha, current * 2)
                    if extra_kg_ha > 0:
                        adjustments.setdefault("Mg", []).append(
                            (f"Mg base sat. {actual:.1f}% below ideal {ideal_min}%", extra_kg_ha)
                        )

    # Apply adjustments to targets
    updated = []
    for t in targets:
        nut = t["Nutrient"]
        new_t = dict(t)
        adj_list = adjustments.get(nut, [])
        total_extra = sum(extra for _, extra in adj_list)
        reasons = [reason for reason, _ in adj_list]
        warn_list = warnings.get(nut, [])

        # N must never be reduced by ratio adjustments — it's not bankable
        if nut == "N" and total_extra < 0:
            total_extra = 0
            reasons = []

        new_t["Ratio_Adjustment_kg_ha"] = round(total_extra, 2)
        new_t["Ratio_Reasons"] = reasons
        new_t["Ratio_Warnings"] = warn_list
        final = round(t["Target_kg_ha"] + total_extra, 2)
        new_t["Final_Target_kg_ha"] = max(final, 0)  # Never go negative
        updated.append(new_t)

    return updated


def evaluate_ratios(soil_values, ratio_rows):
    """Evaluate soil nutrient ratios against ideal ranges.

    Args:
        soil_values: dict of {soil_parameter: value}
        ratio_rows: list of dicts from ideal_ratios table
    """
    results = []

    def sv(key):
        v = soil_values.get(key)
        if v is not None and v > 0:
            return v
        return None

    ca = sv("Ca")
    mg = sv("Mg")
    k = sv("K")
    na = sv("Na")
    fe = sv("Fe")
    mn = sv("Mn")
    p = sv("P (Bray-1)") or sv("P (Citric acid)")
    zn = sv("Zn")
    n = sv("N (total)")
    s = sv("S")
    cec = sv("CEC")

    computed = {}
    if ca and mg:
        computed["Ca:Mg"] = round(ca / mg, 2)
    if ca and k:
        computed["Ca:K"] = round(ca / k, 2)
    if mg and k:
        computed["Mg:K"] = round(mg / k, 2)
    if ca and mg and k:
        computed["(Ca+Mg):K"] = round((ca + mg) / k, 2)
    if p and zn:
        computed["P:Zn"] = round(p / zn, 2)
    if fe and mn:
        computed["Fe:Mn"] = round(fe / mn, 2)
    if n and s:
        computed["N:S"] = round(n / s, 2)
    if k and na:
        computed["K:Na"] = round(k / na, 2)

    # Base saturation
    if cec and cec > 0:
        ca_cmol = (ca / 200.4) if ca else 0
        mg_cmol = (mg / 121.6) if mg else 0
        k_cmol = (k / 390.96) if k else 0
        na_cmol = (na / 230.0) if na else 0
        computed["Ca base sat."] = round(ca_cmol / cec * 100, 1)
        computed["Mg base sat."] = round(mg_cmol / cec * 100, 1)
        computed["K base sat."] = round(k_cmol / cec * 100, 1)
        computed["Na base sat."] = round(na_cmol / cec * 100, 1)
        total_bases = ca_cmol + mg_cmol + k_cmol + na_cmol
        computed["H+Al base sat."] = round(max((cec - total_bases) / cec * 100, 0), 1)

    for row in ratio_rows:
        name = row["ratio"]
        actual = computed.get(name)
        if actual is None:
            continue
        ideal_min = float(row["ideal_min"])
        ideal_max = float(row["ideal_max"])
        if actual < ideal_min:
            status = "Below ideal"
        elif actual > ideal_max:
            status = "Above ideal"
        else:
            status = "Ideal"

        results.append({
            "Ratio": name,
            "Actual": actual,
            "Ideal_Min": ideal_min,
            "Ideal_Max": ideal_max,
            "Unit": row["unit"],
            "Status": status,
        })

    return results
