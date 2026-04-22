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

# FERTASA 5.2.2: equivalent weights for mg/kg ↔ cmol_c/kg conversion.
# 1 cmol_c/kg of the ion equals this many mg/kg.
CATION_EQUIVALENT_WEIGHT_MG_PER_CMOL = {
    "Ca": 200.4,   # atomic mass 40.08, charge 2 → eq wt 20.04 → 200.4 mg/kg per cmol_c/kg
    "Mg": 121.56,  # atomic mass 24.31, charge 2
    "K":  390.98,  # atomic mass 39.10, charge 1
    "Na": 229.90,  # atomic mass 22.99, charge 1
}

# Soil-mass assumption for mg/kg → kg/ha conversion. Matches the
# existing convention used in adjust_targets_for_ratios: ~15 cm topsoil
# depth × 1.33 g/cm³ bulk density = 2,000,000 kg/ha = 2000 t/ha.
# Hardcoded until per-field sample depth + bulk density are captured.
CATION_SOIL_MASS_KG_PER_HA = 2_000_000

# Below this measured CEC the base-saturation calculation becomes
# numerically unstable (a small absolute Ca gives a misleadingly high
# %), so we skip the ratio path. FERTASA doesn't publish this cut
# explicitly — 3 cmol_c/kg is SA lab-interpretation convention for
# "sandy soil, treat cautiously."
CATION_RATIO_MIN_CEC = 3.0


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


def get_adjustment_factor_row(classification, adjustment_rows, nutrient=None):
    """Resolve the adjustment_factors row for a (classification, nutrient) pair.

    Returns the full row dict so callers can read not only the numeric
    factor but also provenance (source, source_section, source_note,
    tier) — the UI surfaces these so agronomists can distinguish a
    FERTASA-rate-table-driven target from a Tier-6 implementer-convention
    fallback. Returns None when no row matches and the calculator
    should treat the factor as 1.0.

    Args:
        classification: string like "Very Low", "Low", etc.
        adjustment_rows: list of dicts from adjustment_factors table
        nutrient: optional nutrient name to look up group-specific factor
    """
    if not classification:
        return None

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
                return row

    # Fallback: match by classification only (backward compat with
    # ungrouped fixtures and legacy callers).
    return next(
        (r for r in adjustment_rows if r["classification"] == classification),
        None,
    )


def get_adjustment_factor(classification, adjustment_rows, nutrient=None):
    """Numeric factor for (classification, nutrient). Thin wrapper over
    get_adjustment_factor_row that returns only the factor and defaults
    to 1.0 on miss. Retained for callers that don't need provenance."""
    row = get_adjustment_factor_row(classification, adjustment_rows, nutrient)
    if row is None:
        return 1.0
    return float(row["factor"])


def lookup_rate_table(crop, nutrient, yield_target, soil_value, rate_table_rows,
                       context=None):
    """Look up a FERTASA-style 2-D rate table cell for (crop, nutrient).

    Snap semantics (conservative, faithful to published cell):
      * Yield: rows with yield_max IS NULL are open-top bands — they
        apply iff yield_target >= yield_min. Rows where min == max
        are discrete points; snap to the nearest. Tie-break: prefer
        higher yield_min (agronomist-conservative).
      * Soil test: rows with a soil-test axis use half-open bands
        [soil_test_min, soil_test_max); NULL max = open upper bound.
        Rows where ALL soil_test_* cols are NULL mean the table has
        no soil-test axis (e.g. canola N) — always applicable.
      * Third-axis filters (clay_pct, texture, rainfall, region,
        prior_crop, water_regime): NULL in the row means "no
        constraint on that dimension". Non-NULL means the context
        must match.
      * Specificity: when multiple rows pass all filters, pick the
        one with the most non-NULL third-axis columns (the most
        specific match wins over the generic fallback).

    Args:
        crop: crop name (matches fertilizer_rate_tables.crop).
        nutrient: 'N', 'P', 'K', etc.
        yield_target: numeric, the user's yield target (crop's yield unit).
        soil_value: numeric soil-test reading, or None if not applicable.
        rate_table_rows: full list of dicts from fertilizer_rate_tables.
        context: optional dict with keys — clay_pct, texture, rainfall_mm,
                 region, prior_crop, water_regime. NULL/missing keys mean
                 the caller doesn't know the value; rows requiring that
                 dimension are skipped.

    Returns:
        dict with keys Rate_Min, Rate_Max, Rate_Mid, Is_Range, Source,
        Source_Section, Source_Note, Matched_Band — or None on miss.
    """
    if not rate_table_rows:
        return None

    ctx = context or {}

    # Narrow by crop + nutrient
    candidates = [
        r for r in rate_table_rows
        if r.get("crop") == crop and r.get("nutrient") == nutrient
    ]
    if not candidates:
        return None

    # Apply third-axis filters (row requires a match only if its column is non-NULL)
    def _passes_third_axis(row):
        # Clay-% range
        cmin, cmax = row.get("clay_pct_min"), row.get("clay_pct_max")
        if cmin is not None or cmax is not None:
            clay = ctx.get("clay_pct")
            if clay is None:
                return False
            clay = float(clay)
            if cmin is not None and clay < float(cmin):
                return False
            if cmax is not None and clay >= float(cmax):
                return False
        # Texture
        if row.get("texture") is not None and ctx.get("texture") != row.get("texture"):
            return False
        # Rainfall range
        rmin, rmax = row.get("rainfall_mm_min"), row.get("rainfall_mm_max")
        if rmin is not None or rmax is not None:
            rain = ctx.get("rainfall_mm")
            if rain is None:
                return False
            rain = float(rain)
            if rmin is not None and rain < float(rmin):
                return False
            if rmax is not None and rain >= float(rmax):
                return False
        # Soil organic matter %
        smin, smax = (row.get("soil_organic_matter_pct_min"),
                       row.get("soil_organic_matter_pct_max"))
        if smin is not None or smax is not None:
            som = ctx.get("som_pct")
            if som is None:
                return False
            som = float(som)
            if smin is not None and som < float(smin):
                return False
            if smax is not None and som >= float(smax):
                return False
        # Region / prior_crop / water_regime / crop_cycle: discrete equality
        for field in ("region", "prior_crop", "water_regime", "crop_cycle"):
            if row.get(field) is not None and ctx.get(field) != row.get(field):
                return False
        return True

    candidates = [r for r in candidates if _passes_third_axis(r)]
    if not candidates:
        return None

    # Soil-test axis filter: row has a soil-test axis iff soil_test_min or
    # soil_test_max is non-NULL. If the row has an axis, soil_value must
    # fall in its band. If the row has no axis, it's always applicable.
    def _passes_soil_axis(row):
        smin, smax = row.get("soil_test_min"), row.get("soil_test_max")
        has_axis = smin is not None or smax is not None
        if not has_axis:
            return True
        if soil_value is None:
            return False
        sv = float(soil_value)
        if smin is not None and sv < float(smin):
            return False
        if smax is not None and sv >= float(smax):
            return False
        return True

    candidates = [r for r in candidates if _passes_soil_axis(r)]
    if not candidates:
        return None

    # Yield-axis match: three row shapes are possible.
    #   1. Open-top  (yield_max IS NULL, e.g. "2.5+"): applies iff yield ≥ yield_min.
    #   2. Point     (yield_min == yield_max, e.g. "1.0"): snap to nearest.
    #   3. Band      (yield_min < yield_max, e.g. "1-2"): applies iff yield
    #                 falls in half-open interval [yield_min, yield_max).
    #
    # Precedence when multiple shapes apply:
    #   band ∋ yield  →  beats open-top, beats point-snap.
    #   open-top ∋ yield (no band matched)  →  beats point-snap.
    #   no membership match  →  snap to nearest point.
    # Rationale: explicit membership (yield literally IN the published
    # interval) is a stronger match than snapping to a nearby point.
    yt = float(yield_target)

    bands = [
        r for r in candidates
        if r.get("yield_max_t_ha") is not None
        and float(r["yield_min_t_ha"]) < float(r["yield_max_t_ha"])
    ]
    applicable_bands = [
        r for r in bands
        if float(r["yield_min_t_ha"]) <= yt < float(r["yield_max_t_ha"])
    ]

    open_top = [r for r in candidates if r.get("yield_max_t_ha") is None]
    applicable_open = [
        r for r in open_top
        if float(r["yield_min_t_ha"]) <= yt
    ]

    if applicable_bands:
        # Prefer the narrowest matching band (highest min when they overlap).
        applicable_bands.sort(
            key=lambda r: float(r["yield_min_t_ha"]), reverse=True
        )
        chosen = applicable_bands[0]
    elif applicable_open:
        applicable_open.sort(
            key=lambda r: float(r["yield_min_t_ha"]), reverse=True
        )
        chosen = applicable_open[0]
    else:
        # Snap to nearest discrete point
        discrete = [
            r for r in candidates
            if r.get("yield_max_t_ha") is not None
            and float(r["yield_min_t_ha"]) == float(r["yield_max_t_ha"])
        ]
        if not discrete:
            return None
        # Tie-break: closer wins; on exact tie, prefer higher yield_min.
        discrete.sort(key=lambda r: (
            abs(float(r["yield_min_t_ha"]) - yt),
            -float(r["yield_min_t_ha"]),
        ))
        chosen = discrete[0]

    # Specificity: among rows that match the same yield AND soil band,
    # prefer the one with the most non-NULL third-axis columns.
    third_axis_cols = ("clay_pct_min", "texture", "rainfall_mm_min",
                        "region", "prior_crop", "water_regime",
                        "crop_cycle", "soil_organic_matter_pct_min")
    same_band = [
        r for r in candidates
        if r.get("yield_min_t_ha") == chosen.get("yield_min_t_ha")
        and r.get("yield_max_t_ha") == chosen.get("yield_max_t_ha")
        and r.get("soil_test_min") == chosen.get("soil_test_min")
        and r.get("soil_test_max") == chosen.get("soil_test_max")
    ]
    if len(same_band) > 1:
        same_band.sort(
            key=lambda r: sum(1 for c in third_axis_cols if r.get(c) is not None),
            reverse=True,
        )
        chosen = same_band[0]

    rate_min = float(chosen["rate_min_kg_ha"])
    rate_max = float(chosen["rate_max_kg_ha"])
    return {
        "Rate_Min": rate_min,
        "Rate_Max": rate_max,
        "Rate_Mid": round((rate_min + rate_max) / 2, 2),
        "Is_Range": rate_max > rate_min,
        "Source": chosen.get("source"),
        "Source_Section": chosen.get("source_section"),
        "Source_Note": chosen.get("source_note"),
        "Matched_Band": {
            "yield_min": chosen.get("yield_min_t_ha"),
            "yield_max": chosen.get("yield_max_t_ha"),
            "soil_test_min": chosen.get("soil_test_min"),
            "soil_test_max": chosen.get("soil_test_max"),
            "soil_test_method": chosen.get("soil_test_method"),
            "clay_pct_min": chosen.get("clay_pct_min"),
            "clay_pct_max": chosen.get("clay_pct_max"),
            "texture": chosen.get("texture"),
            "region": chosen.get("region"),
            "water_regime": chosen.get("water_regime"),
            "crop_cycle": chosen.get("crop_cycle"),
        },
    }


def calculate_cation_ratio_target(soil_values, cec, ratio_rows, nutrient,
                                   crop_name=None, crop_calc_flags_rows=None,
                                   seasons_to_spread=2):
    """FERTASA 5.2.2 base-saturation target for Ca or Mg.

    For normal mineral soils with measured CEC, this produces a
    physically-grounded fertilizer recommendation by computing the
    exchangeable-cation shortfall relative to target base saturation
    and converting back to kg/ha using the FERTASA equivalent-weight
    factors. It replaces the Tier-6 heuristic path for Ca/Mg.

    Returns None (→ caller falls through to the next path) when:
      * nutrient is not 'Ca' or 'Mg' (K handled by rate tables where
        available; base-saturation targeting is less appropriate for
        mobile K)
      * CEC is missing, non-numeric, or below CATION_RATIO_MIN_CEC
      * the crop is flagged skip_cation_ratio_path in crop_calc_flags
        (acid-loving crops — blueberry, rooibos, etc.)
      * no 'Ca base sat.' / 'Mg base sat.' row in ratio_rows
      * the measured cation is already at or above the ideal-band lower
        bound (no addition needed — existing adjust_targets_for_ratios
        still surfaces the "already sufficient" state in diagnostics)

    Otherwise returns a dict:
      {
        "Target_kg_ha": float,
        "Source": "FERTASA Handbook",
        "Source_Section": "5.2.2",
        "Tier": 1,
        "Source_Note": <diagnostic note incl. current/target sat + spread>,
        "Current_Base_Sat_Pct": float,
        "Target_Base_Sat_Pct": float,
        "Shortfall_Pct": float,
        "CEC": float,
        "Seasons_To_Spread": int,
      }

    Args:
        soil_values: dict {soil_parameter: value}
        cec: measured CEC (cmol_c/kg). Pass None if not measured.
        ratio_rows: list of dicts from ideal_ratios table
        nutrient: 'Ca' or 'Mg'
        crop_name: optional crop for flag lookup
        crop_calc_flags_rows: optional list of dicts from crop_calc_flags
        seasons_to_spread: default 2 — FERTASA convention is to spread
            a full Ca/Mg correction over 2-3 seasons. Returns half of
            the full shortfall to apply in one season.
    """
    if nutrient not in ("Ca", "Mg"):
        return None

    # Skip flag: acid-loving crops whose universal targets would damage.
    if crop_name and crop_calc_flags_rows:
        flag_row = next(
            (r for r in crop_calc_flags_rows if r.get("crop") == crop_name),
            None,
        )
        if flag_row and flag_row.get("skip_cation_ratio_path"):
            return None

    # CEC gate.
    if cec is None:
        return None
    try:
        cec_f = float(cec)
    except (TypeError, ValueError):
        return None
    if cec_f < CATION_RATIO_MIN_CEC:
        return None

    # Measured cation in cmol_c/kg.
    measured_mg_kg = soil_values.get(nutrient)
    if measured_mg_kg is None:
        return None
    try:
        measured_mg_kg_f = float(measured_mg_kg)
    except (TypeError, ValueError):
        return None
    eq_wt = CATION_EQUIVALENT_WEIGHT_MG_PER_CMOL[nutrient]
    current_cmol = measured_mg_kg_f / eq_wt
    current_sat_pct = (current_cmol / cec_f) * 100 if cec_f > 0 else 0

    # Target from ideal_ratios. Use ideal_min (conservative — only
    # recommend addition if below the published-low-end target, matching
    # the existing adjust_targets_for_ratios convention).
    ratio_name = f"{nutrient} base sat."
    ratio_row = next(
        (r for r in ratio_rows if r.get("ratio") == ratio_name),
        None,
    )
    if not ratio_row:
        return None
    ideal_min = float(ratio_row["ideal_min"])
    ideal_max = float(ratio_row["ideal_max"])

    if current_sat_pct >= ideal_min:
        return None  # already adequate; no addition

    shortfall_pct = ideal_min - current_sat_pct
    shortfall_cmol = (shortfall_pct / 100) * cec_f
    delta_mg_kg = shortfall_cmol * eq_wt
    full_correction_kg_ha = delta_mg_kg * CATION_SOIL_MASS_KG_PER_HA / 1_000_000
    # Spread over seasons_to_spread (conservative default 2).
    per_season_kg_ha = round(full_correction_kg_ha / max(1, seasons_to_spread), 2)

    return {
        "Target_kg_ha": per_season_kg_ha,
        "Source": ratio_row.get("source") or "FERTASA Handbook",
        "Source_Section": ratio_row.get("source_section") or "5.2.2",
        "Tier": ratio_row.get("tier") or 1,
        "Source_Note": (
            f"Base-saturation target: {nutrient} currently "
            f"{current_sat_pct:.1f}% of CEC (ideal {ideal_min:.0f}-{ideal_max:.0f}%). "
            f"Full correction {full_correction_kg_ha:.0f} kg {nutrient}/ha; "
            f"split over {seasons_to_spread} seasons per FERTASA convention."
        ),
        "Current_Base_Sat_Pct": round(current_sat_pct, 1),
        "Target_Base_Sat_Pct": ideal_min,
        "Shortfall_Pct": round(shortfall_pct, 1),
        "CEC": cec_f,
        "Seasons_To_Spread": seasons_to_spread,
    }


def calculate_nutrient_targets(crop_name, yield_target, soil_values,
                                crop_rows, sufficiency_rows, adjustment_rows, param_map_rows,
                                crop_override_rows=None, rate_table_rows=None,
                                rate_table_context=None, ratio_rows=None,
                                crop_calc_flags_rows=None):
    """Calculate adjusted nutrient targets (kg/ha) for a crop.

    Preemption order per nutrient:
      1. FERTASA (or equivalent) rate-table row — if a cell exists for
         the (crop, nutrient, yield, soil) combination, it wins.
      2. For Ca/Mg only: FERTASA 5.2.2 base-saturation ratio path
         (skipped on low-CEC soils and acid-loving crops).
      3. Heuristic: removal × yield × adjustment-factor (Tier 6).

    The result dict's `Source` and `Tier` fields indicate which path
    was taken so the UI can surface the provenance of each number.

    Args:
        crop_name: crop name matching crop_requirements table
        yield_target: expected yield in the crop's yield unit
        soil_values: dict of {soil_parameter: value} from lab results
        crop_rows: list of dicts from crop_requirements table
        sufficiency_rows: list of dicts from soil_sufficiency table
        adjustment_rows: list of dicts from adjustment_factors table
        param_map_rows: list of dicts from soil_parameter_map table
        crop_override_rows: optional crop-specific sufficiency overrides
        rate_table_rows: optional list of dicts from fertilizer_rate_tables.
            When provided, a table hit replaces the removal × factor
            calculation for that nutrient.
        rate_table_context: optional dict passed to lookup_rate_table()
            for third-axis filtering (clay_pct, texture, rainfall_mm,
            region, prior_crop, water_regime).
        ratio_rows: optional list of dicts from ideal_ratios — when
            provided, enables the Ca/Mg base-saturation path (FERTASA
            5.2.2) as the preferred source for those two nutrients.
        crop_calc_flags_rows: optional list of dicts from crop_calc_flags
            — used to skip the ratio path for acid-loving crops.
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
        adj_row = get_adjustment_factor_row(classification, adjustment_rows, nutrient=nut)
        factor = float(adj_row["factor"]) if adj_row else 1.0
        adjusted = round(base_req * factor, 2)

        # Path 1: rate-table override takes precedence when a matching cell exists.
        rate_hit = lookup_rate_table(
            crop=crop_name,
            nutrient=nut,
            yield_target=yield_target,
            soil_value=soil_val,
            rate_table_rows=rate_table_rows,
            context=rate_table_context,
        ) if rate_table_rows else None

        # Path 2: Ca/Mg base-saturation (FERTASA 5.2.2) when no rate-table hit.
        ratio_hit = None
        if rate_hit is None and nut in ("Ca", "Mg") and ratio_rows:
            cec_value = soil_values.get("CEC")
            ratio_hit = calculate_cation_ratio_target(
                soil_values=soil_values,
                cec=cec_value,
                ratio_rows=ratio_rows,
                nutrient=nut,
                crop_name=crop_name,
                crop_calc_flags_rows=crop_calc_flags_rows,
            )

        if rate_hit is not None:
            target_kg_ha = rate_hit["Rate_Mid"]
            source_label = f"{rate_hit['Source']} ({rate_hit['Source_Section']})"
            # Rate-table rows carry their own provenance; inferring a
            # numeric Tier from source strings is a separate follow-up.
            tier = None
            adj_provenance = None
            calc_path = "rate_table"
        elif ratio_hit is not None:
            target_kg_ha = ratio_hit["Target_kg_ha"]
            source_label = f"{ratio_hit['Source']} ({ratio_hit['Source_Section']})"
            tier = ratio_hit["Tier"]
            adj_provenance = None
            calc_path = "cation_ratio"
        else:
            target_kg_ha = adjusted
            source_label = "removal × factor (heuristic)"
            tier = adj_row.get("tier") if adj_row else None
            adj_provenance = {
                "source": adj_row.get("source"),
                "source_section": adj_row.get("source_section"),
                "source_note": adj_row.get("source_note"),
            } if adj_row else None
            calc_path = "heuristic"

        results.append({
            "Nutrient": nut,
            "Per_Unit": per_unit,
            "Base_Req_kg_ha": base_req,
            "Soil_Value": soil_val if soil_val is not None else "",
            "Classification": classification,
            "Factor": factor,
            "Target_kg_ha": target_kg_ha,
            "Source": source_label,
            "Tier": tier,
            "Calc_Path": calc_path,
            "Adjustment_Factor_Source": adj_provenance,
            "Rate_Table_Hit": rate_hit,
            "Cation_Ratio_Hit": ratio_hit,
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

        Sufficiency-first principle:
        - If sufficiency already penalised a nutrient (factor < 1), don't
          reduce it further via ratios — sufficiency handled the oversupply.
        - Only reduce a nutrient that sufficiency scored as Optimal (factor 1).
        - Only increase a nutrient if it is NOT already High/Very High.
        - If neither action is possible, warn instead.

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

        def _sufficiency_already_reduced(nutrient):
            """True if sufficiency already penalised this nutrient (factor < 1)."""
            t = target_map.get(nutrient)
            return t is not None and t.get("Factor", 1) < 1

        # Strategy 1: reduce the over-supplied nutrient
        # BUT only if sufficiency hasn't already reduced it — don't double-punish
        if (reduce_nut in target_map
                and not _sufficiency_already_reduced(reduce_nut)):
            current = target_map[reduce_nut]["Target_kg_ha"]
            if current > 0:
                other = target_map.get(increase_nut, {}).get("Target_kg_ha", 0)
                if other > 0:
                    if reduce_nut == denominator_nut:
                        ideal_reduce = other / ideal_mid
                    else:
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
                    ideal_increase = other * ideal_mid
                else:
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
                pzn_mid = (ideal_min + ideal_max) / 2
                if current_p > 0 and pzn_mid > 0:
                    ideal_zn = current_p / pzn_mid
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
            ns_mid = (ideal_min + ideal_max) / 2
            if not is_high("S") and "S" in target_map and n_target > 0:
                current_s = target_map["S"]["Target_kg_ha"]
                ideal_s = n_target / ns_mid
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
            kna_mid = (ideal_min + ideal_max) / 2
            if "K" in target_map and na and na > 0:
                current_k = target_map["K"]["Target_kg_ha"]
                ideal_k = na * kna_mid  # K needed relative to soil Na
                extra = round(ideal_k - current_k, 2)
                extra = min(extra, max(current_k, 5.0))  # Cap
                if extra > 0:
                    adjustments.setdefault("K", []).append(
                        (f"K:Na ratio {actual:.1f} below ideal {ideal_min}-{ideal_max}", extra)
                    )

        # Base saturation corrections — these already use exact calculations.
        # Skipped for Ca/Mg targets already computed via the cation_ratio
        # base-target path (calculate_cation_ratio_target), since the ratio
        # path already internalises the same shortfall formula. Double-
        # applying would stack a full correction on top of itself.
        elif ratio_name == "Ca base sat." and status == "Below ideal":
            ca_target = target_map.get("Ca", {})
            if ca_target.get("Calc_Path") == "cation_ratio":
                pass  # already handled by base-target path
            elif "Ca" in target_map and not is_high("Ca"):
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
            mg_target = target_map.get("Mg", {})
            if mg_target.get("Calc_Path") == "cation_ratio":
                pass  # already handled by base-target path
            elif "Mg" in target_map and not is_high("Mg"):
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

        # Safety net: cap total stacked reductions at 50% of base target.
        # This should rarely trigger now that _ratio_adjust_pair skips
        # nutrients already penalised by sufficiency, but prevents edge cases.
        base = t["Target_kg_ha"]
        if total_extra < 0 and base > 0:
            max_reduction = base * 0.5
            if abs(total_extra) > max_reduction:
                total_extra = -max_reduction
                warn_list = list(warn_list)  # copy
                warn_list.append(
                    f"Ratio adjustments capped — {nut} kept at "
                    f"{round(base - max_reduction, 1)} kg/ha (50% of sufficiency target)"
                )

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
