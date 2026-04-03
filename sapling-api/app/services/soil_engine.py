"""Soil analysis classification, adjustment, and nutrient target calculation."""

NUTRIENTS_SOIL = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Mo", "Cu"]

SOIL_CLASSIFICATIONS = ["Very Low", "Low", "Optimal", "High", "Very High"]


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


def get_adjustment_factor(classification, adjustment_rows):
    """Look up adjustment factor for a soil classification level.

    Args:
        classification: string like "Very Low", "Low", etc.
        adjustment_rows: list of dicts from adjustment_factors table
    """
    if not classification:
        return 1.0
    row = next((r for r in adjustment_rows if r["classification"] == classification), None)
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
        factor = get_adjustment_factor(classification, adjustment_rows)
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

    Uses a hybrid sufficiency + BCSR approach:
    - Start with sufficiency-based targets (already calculated)
    - Check each ratio against ideal ranges
    - If a ratio is off, increase the deficient nutrient's target

    Args:
        targets: list of dicts from calculate_nutrient_targets()
        ratio_results: list of dicts from evaluate_ratios()
        soil_values: dict of soil parameter values
        ratio_rows: list of dicts from ideal_ratios table

    Returns:
        Updated targets list with Ratio_Adjustment and Adjusted_Target_kg_ha fields added
    """
    # Build lookup: nutrient name -> target dict
    target_map = {t["Nutrient"]: t for t in targets}

    # Track adjustments: {nutrient: [(reason, extra_kg_ha), ...]}
    adjustments: dict[str, list[tuple[str, float]]] = {}

    def sv(key):
        v = soil_values.get(key)
        return float(v) if v is not None and v != "" else None

    cec = sv("CEC")
    ca = sv("Ca")
    mg = sv("Mg")
    k = sv("K")
    na = sv("Na")

    for rr in ratio_results:
        ratio_name = rr["Ratio"]
        actual = rr["Actual"]
        ideal_min = rr["Ideal_Min"]
        ideal_max = rr["Ideal_Max"]
        status = rr["Status"]

        if status == "Ideal":
            continue

        # Get the current target for the nutrient that needs correction
        # Strategy: if ratio A:B is below ideal, increase A; if above ideal, increase B

        if ratio_name == "Ca:Mg" and status == "Below ideal":
            # Ca too low relative to Mg — increase Ca target
            if "Ca" in target_map:
                current = target_map["Ca"]["Target_kg_ha"]
                # Aim for midpoint of ideal ratio
                ideal_mid = (ideal_min + ideal_max) / 2
                if mg and mg > 0 and actual > 0:
                    correction_factor = min(ideal_mid / actual, 2.0)  # Cap at 2x
                    extra = round(current * (correction_factor - 1), 2)
                    if extra > 0:
                        adjustments.setdefault("Ca", []).append(
                            (f"Ca:Mg ratio {actual:.1f} below ideal {ideal_min}-{ideal_max}", extra)
                        )

        elif ratio_name == "Ca:Mg" and status == "Above ideal":
            # Mg too low relative to Ca — increase Mg target
            if "Mg" in target_map:
                current = target_map["Mg"]["Target_kg_ha"]
                ideal_mid = (ideal_min + ideal_max) / 2
                if ca and ca > 0 and actual > 0:
                    correction_factor = min(actual / ideal_mid, 2.0)
                    extra = round(current * (correction_factor - 1), 2)
                    if extra > 0:
                        adjustments.setdefault("Mg", []).append(
                            (f"Ca:Mg ratio {actual:.1f} above ideal {ideal_min}-{ideal_max}", extra)
                        )

        elif ratio_name == "Ca:K" and status == "Below ideal":
            # Ca too low relative to K — increase Ca
            if "Ca" in target_map:
                current = target_map["Ca"]["Target_kg_ha"]
                extra = round(current * 0.25, 2)  # 25% boost
                adjustments.setdefault("Ca", []).append(
                    (f"Ca:K ratio {actual:.1f} below ideal {ideal_min}-{ideal_max}", extra)
                )

        elif ratio_name == "Mg:K" and status == "Below ideal":
            # Mg too low relative to K — increase Mg
            if "Mg" in target_map:
                current = target_map["Mg"]["Target_kg_ha"]
                extra = round(current * 0.25, 2)
                adjustments.setdefault("Mg", []).append(
                    (f"Mg:K ratio {actual:.1f} below ideal {ideal_min}-{ideal_max}", extra)
                )

        elif ratio_name == "P:Zn" and status == "Above ideal":
            # P too high relative to Zn — increase Zn (common in high-P soils)
            if "Zn" in target_map:
                current = target_map["Zn"]["Target_kg_ha"]
                extra = round(max(current * 0.5, 0.5), 2)  # At least 0.5 kg/ha extra Zn
                adjustments.setdefault("Zn", []).append(
                    (f"P:Zn ratio {actual:.1f} above ideal {ideal_min}-{ideal_max}", extra)
                )

        elif ratio_name == "N:S" and status == "Above ideal":
            # N too high relative to S — increase S
            if "S" in target_map:
                current = target_map["S"]["Target_kg_ha"]
                extra = round(max(current * 0.3, 2.0), 2)
                adjustments.setdefault("S", []).append(
                    (f"N:S ratio {actual:.1f} above ideal {ideal_min}-{ideal_max}", extra)
                )

        elif ratio_name == "K:Na" and status == "Below ideal":
            # K too low relative to Na — increase K to displace Na
            if "K" in target_map:
                current = target_map["K"]["Target_kg_ha"]
                extra = round(current * 0.3, 2)
                adjustments.setdefault("K", []).append(
                    (f"K:Na ratio {actual:.1f} below ideal {ideal_min}-{ideal_max}", extra)
                )

        # Base saturation corrections
        elif ratio_name == "Ca base sat." and status == "Below ideal":
            if "Ca" in target_map:
                current = target_map["Ca"]["Target_kg_ha"]
                shortfall_pct = ideal_min - actual
                # Roughly: each 1% base sat increase needs ~(CEC * 200.4 / 100) mg/kg Ca
                if cec and cec > 0:
                    extra_mg_kg = shortfall_pct * cec * 200.4 / 100
                    extra_kg_ha = round(extra_mg_kg * 2 / 1000, 2)  # ~2 million kg soil per ha top 20cm
                    extra_kg_ha = min(extra_kg_ha, current * 2)  # Cap
                    if extra_kg_ha > 0:
                        adjustments.setdefault("Ca", []).append(
                            (f"Ca base sat. {actual:.1f}% below ideal {ideal_min}%", extra_kg_ha)
                        )

        elif ratio_name == "K base sat." and status == "Below ideal":
            if "K" in target_map:
                current = target_map["K"]["Target_kg_ha"]
                extra = round(current * 0.3, 2)
                adjustments.setdefault("K", []).append(
                    (f"K base sat. {actual:.1f}% below ideal {ideal_min}%", extra)
                )

        elif ratio_name == "Mg base sat." and status == "Below ideal":
            if "Mg" in target_map:
                current = target_map["Mg"]["Target_kg_ha"]
                extra = round(current * 0.25, 2)
                adjustments.setdefault("Mg", []).append(
                    (f"Mg base sat. {actual:.1f}% below ideal {ideal_min}%", extra)
                )

    # Apply adjustments to targets
    updated = []
    for t in targets:
        nut = t["Nutrient"]
        new_t = dict(t)
        adj_list = adjustments.get(nut, [])
        total_extra = sum(extra for _, extra in adj_list)
        reasons = [reason for reason, _ in adj_list]

        new_t["Ratio_Adjustment_kg_ha"] = round(total_extra, 2)
        new_t["Ratio_Reasons"] = reasons
        new_t["Final_Target_kg_ha"] = round(t["Target_kg_ha"] + total_extra, 2)
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
