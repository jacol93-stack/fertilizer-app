"""Seasonal feeding plan generation engine.

Takes total nutrient requirements (from soil analysis) and splits them
across growth stages, applying perennial age factors where applicable.
"""


def get_age_factor(tree_age: int, age_factors: list[dict]) -> dict:
    """Find the matching age factor row for a given tree age.

    Returns dict with n_factor, p_factor, k_factor, general_factor.
    Defaults to 1.0 for all if no match found.
    """
    default = {"n_factor": 1.0, "p_factor": 1.0, "k_factor": 1.0, "general_factor": 1.0}
    if not age_factors or tree_age is None:
        return default
    for af in age_factors:
        if af["age_min"] <= tree_age <= af["age_max"]:
            return af
    return default


def generate_feeding_plan(
    nutrient_targets: list[dict],
    growth_stages: list[dict],
    crop_type: str = "perennial",
    tree_age: int | None = None,
    age_factors: list[dict] | None = None,
    field_area_ha: float | None = None,
    corrective_items: list[dict] | None = None,
) -> list[dict]:
    """Generate a seasonal feeding plan by splitting total requirements
    across growth stages.

    Args:
        nutrient_targets: list of dicts from calculate_nutrient_targets()
            Each has: Nutrient, Target_kg_ha, Final_Target_kg_ha, etc.
        growth_stages: list of dicts from crop_growth_stages table
            Each has: stage_name, stage_order, month_start, month_end,
            n_pct, p_pct, k_pct, ..., num_applications, default_method
        crop_type: "perennial" or "annual"
        tree_age: age in years (for perennials)
        age_factors: list of dicts from perennial_age_factors table
        field_area_ha: field size for total cost calculation
        corrective_items: list of dicts from calculate_corrective_targets()
            Each has: nutrient, annual_corrective_kg_ha, direction

    Returns:
        List of feeding plan item dicts, one per application event,
        sorted by feeding_order.
    """
    # Build total kg/ha lookup from nutrient targets.
    # Use Final_Target_kg_ha (ratio-adjusted) with fallback to Target_kg_ha.
    totals = {}
    for nt in nutrient_targets:
        nutrient = nt["Nutrient"]
        totals[nutrient] = float(
            nt.get("Final_Target_kg_ha",
                   nt.get("Target_kg_ha", 0))
        )

    # Add corrective build-up amounts on top of maintenance targets.
    # Only for nutrients that need building up (P, K, Ca, Mg).
    if corrective_items:
        for ci in corrective_items:
            nut = ci.get("nutrient", "")
            if ci.get("direction") == "build-up" and nut in totals:
                extra = float(ci.get("annual_corrective_kg_ha", 0))
                totals[nut] = round(totals[nut] + extra, 2)

    # Apply age factor for perennials
    af = {"n_factor": 1.0, "p_factor": 1.0, "k_factor": 1.0, "general_factor": 1.0}
    if crop_type == "perennial" and tree_age is not None and age_factors:
        af = get_age_factor(tree_age, age_factors)

    # Map nutrient names to their age factor
    factor_map = {
        "N": af["n_factor"],
        "P": af["p_factor"],
        "K": af["k_factor"],
    }
    # All other nutrients use general_factor
    for nut in totals:
        if nut not in factor_map:
            factor_map[nut] = af["general_factor"]

    # Apply age factors to totals
    adjusted_totals = {}
    for nut, kg in totals.items():
        adjusted_totals[nut] = round(kg * factor_map.get(nut, 1.0), 2)

    # Map growth stage nutrient pct column names to nutrient names
    pct_col_map = {
        "n_pct": "N", "p_pct": "P", "k_pct": "K",
        "ca_pct": "Ca", "mg_pct": "Mg", "s_pct": "S",
        "fe_pct": "Fe", "b_pct": "B", "mn_pct": "Mn", "zn_pct": "Zn",
    }

    # Generate plan items
    items = []
    feeding_order = 0
    stages_sorted = sorted(growth_stages, key=lambda s: s["stage_order"])

    for stage in stages_sorted:
        num_apps = max(stage.get("num_applications", 1), 1)

        # Calculate nutrients for this stage
        stage_nutrients = {}
        for col, nut in pct_col_map.items():
            pct = float(stage.get(col, 0))
            total = adjusted_totals.get(nut, 0)
            stage_nutrients[nut] = round(total * pct / 100, 2)

        # Also handle Mo and Cu which don't have stage pct columns
        # — distribute evenly across stages
        for nut in ["Mo", "Cu"]:
            if nut in adjusted_totals and adjusted_totals[nut] > 0:
                stage_nutrients[nut] = round(
                    adjusted_totals[nut] / len(stages_sorted), 2
                )

        # Split across applications within this stage
        for app_idx in range(num_apps):
            feeding_order += 1

            # Distribute stage months across applications
            m_start = stage["month_start"]
            m_end = stage["month_end"]
            # Handle wrapping (e.g. Nov-Jan = 11-1)
            if m_end >= m_start:
                months_in_stage = list(range(m_start, m_end + 1))
            else:
                months_in_stage = list(range(m_start, 13)) + list(range(1, m_end + 1))

            if months_in_stage:
                month_idx = min(app_idx, len(months_in_stage) - 1)
                # Spread apps across the stage months
                if num_apps > 1 and len(months_in_stage) > 1:
                    step = max(1, len(months_in_stage) // num_apps)
                    month_idx = min(app_idx * step, len(months_in_stage) - 1)
                target_month = months_in_stage[month_idx]
            else:
                target_month = m_start

            # Divide nutrients equally across applications in this stage
            item = {
                "stage_name": stage["stage_name"],
                "feeding_order": feeding_order,
                "month_target": target_month,
                "method": stage.get("default_method", "broadcast"),
                "n_kg_ha": round(stage_nutrients.get("N", 0) / num_apps, 2),
                "p_kg_ha": round(stage_nutrients.get("P", 0) / num_apps, 2),
                "k_kg_ha": round(stage_nutrients.get("K", 0) / num_apps, 2),
                "ca_kg_ha": round(stage_nutrients.get("Ca", 0) / num_apps, 2),
                "mg_kg_ha": round(stage_nutrients.get("Mg", 0) / num_apps, 2),
                "s_kg_ha": round(stage_nutrients.get("S", 0) / num_apps, 2),
                "fe_kg_ha": round(stage_nutrients.get("Fe", 0) / num_apps, 2),
                "b_kg_ha": round(stage_nutrients.get("B", 0) / num_apps, 2),
                "mn_kg_ha": round(stage_nutrients.get("Mn", 0) / num_apps, 2),
                "zn_kg_ha": round(stage_nutrients.get("Zn", 0) / num_apps, 2),
                "mo_kg_ha": round(stage_nutrients.get("Mo", 0) / num_apps, 2),
                "cu_kg_ha": round(stage_nutrients.get("Cu", 0) / num_apps, 2),
                "is_edited": False,
                "notes": stage.get("notes", ""),
            }
            items.append(item)

    return items


def validate_methods(
    items: list[dict],
    crop_methods: list[dict],
    infrastructure: list[str] | None = None,
    accepted_methods: list[str] | None = None,
) -> list[dict]:
    """Validate and constrain application methods in feeding plan items.

    For each item, ensures the method is valid for the crop. If the current
    method isn't in the allowed list, falls back to the default method.

    Args:
        items: feeding plan items from generate_feeding_plan()
        crop_methods: rows from crop_application_methods table for this crop
        infrastructure: optional list of available infrastructure
            (e.g., ["drip", "pivot", "sprinkler"]). If provided, filters
            out methods that require infrastructure the farmer doesn't have.
        accepted_methods: optional list of methods the farmer accepts.
            If provided, only these methods will be used (intersected with
            crop-valid methods).

    Returns:
        Updated items list with validated methods and available_methods per item.
    """
    if not crop_methods:
        return items

    # Build allowed methods set
    allowed = {m["method"] for m in crop_methods}
    default_method = next(
        (m["method"] for m in crop_methods if m.get("is_default")),
        crop_methods[0]["method"] if crop_methods else "broadcast",
    )

    # Filter by infrastructure if provided
    infra_restricted = set()
    if infrastructure is not None:
        infra_set = {i.lower() for i in infrastructure}
        # Fertigation requires drip, pivot, or sprinkler
        if "fertigation" in allowed and not infra_set.intersection({"drip", "pivot", "sprinkler", "micro"}):
            infra_restricted.add("fertigation")

    effective_methods = allowed - infra_restricted

    # Filter by farmer's accepted methods if provided
    if accepted_methods:
        farmer_set = set(accepted_methods)
        intersection = effective_methods & farmer_set
        # Use intersection if non-empty, otherwise trust the farmer's list
        effective_methods = intersection if intersection else farmer_set

    for item in items:
        current = item.get("method", "broadcast")
        item["available_methods"] = sorted(effective_methods)

        if current not in effective_methods:
            # Fall back to default, or first available
            if default_method in effective_methods:
                item["method"] = default_method
            elif effective_methods:
                item["method"] = sorted(effective_methods)[0]

    return items


MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

NUTRIENTS = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Mo", "Cu"]


def build_practical_plan(
    ideal_items: list[dict],
    application_months: list[int],
    plants_per_ha: int = 0,
) -> list[dict]:
    """Build a practical fertilizer plan from ideal items and farmer's chosen months.

    Groups the ideal nutrient requirements into the farmer's chosen application
    windows, assigning each ideal item to the nearest chosen month.

    Args:
        ideal_items: list of feeding items from generate_feeding_plan()
        application_months: list of months (1-12) the farmer will actually apply
        plants_per_ha: for per-tree calculations

    Returns:
        List of practical application dicts, one per chosen month, with:
        - month, stage_names (combined), nutrients (summed), method (most common)
        - npk_ratio: the N:P:K ratio for this application (for blend grouping)
    """
    if not application_months:
        return []

    app_months = sorted(set(application_months))

    # Assign each ideal item to nearest application month
    def nearest_month(item_month):
        # Handle wrapping (Dec → Jan)
        best = app_months[0]
        best_dist = 12
        for am in app_months:
            dist = min(abs(item_month - am), 12 - abs(item_month - am))
            if dist < best_dist:
                best_dist = dist
                best = am
        return best

    # Group ideal items by their assigned application month
    groups: dict[int, list[dict]] = {m: [] for m in app_months}
    for item in ideal_items:
        if item.get("skipped"):
            continue
        target_month = nearest_month(item.get("month_target", 1))
        groups[target_month].append(item)

    # Build practical applications
    nut_keys = [f"{n.lower()}_kg_ha" for n in NUTRIENTS]
    applications = []

    for month in app_months:
        items = groups[month]
        if not items:
            continue

        # Sum nutrients across all ideal items assigned to this month
        totals = {k: 0.0 for k in nut_keys}
        stage_names = []
        methods = []
        for item in items:
            for k in nut_keys:
                totals[k] += float(item.get(k, 0))
            if item.get("stage_name") and item["stage_name"] not in stage_names:
                stage_names.append(item["stage_name"])
            if item.get("method"):
                methods.append(item["method"])

        # Round totals
        for k in nut_keys:
            totals[k] = round(totals[k], 2)

        # Most common method
        method = max(set(methods), key=methods.count) if methods else "broadcast"

        # Calculate NPK ratio for blend grouping
        n = totals.get("n_kg_ha", 0)
        p = totals.get("p_kg_ha", 0)
        k_val = totals.get("k_kg_ha", 0)
        total_npk = n + p + k_val
        if total_npk > 0:
            # Normalize to smallest non-zero
            non_zero = [v for v in [n, p, k_val] if v > 0.01]
            divisor = min(non_zero) if non_zero else 1
            npk_ratio = f"{round(n/divisor)}:{round(p/divisor)}:{round(k_val/divisor)}"
        else:
            npk_ratio = "0:0:0"

        app = {
            "month": month,
            "month_name": MONTH_NAMES[month],
            "stage_names": stage_names,
            "method": method,
            "npk_ratio": npk_ratio,
            **totals,
        }

        # Per-tree values
        if plants_per_ha and plants_per_ha > 0:
            for k in nut_keys:
                tree_key = k.replace("_kg_ha", "_kg_tree")
                app[tree_key] = round(totals[k] / plants_per_ha, 4)

        applications.append(app)

    # Group applications by similar NPK ratio to minimize distinct blends
    # Two applications can share a blend if their NPK ratios are similar
    blend_groups = _group_by_blend(applications)
    for app in applications:
        app["blend_group"] = blend_groups.get(app["month"], "A")

    return applications


def _group_by_blend(applications: list[dict]) -> dict[int, str]:
    """Group applications that can use the same blend (very similar N:K ratios).

    Two applications share a blend ONLY if the N:K proportions are within 10%.
    A single blend has one fixed composition — different months use different
    application RATES of the same blend.

    Returns {month: blend_letter}
    """
    if not applications:
        return {}

    groups: list[list[dict]] = []

    for app in applications:
        n = app.get("n_kg_ha", 0)
        k = app.get("k_kg_ha", 0)
        total_nk = n + k
        if total_nk < 0.01:
            groups.append([app])
            continue

        # N:K proportion is what defines the blend composition
        n_prop = n / total_nk
        k_prop = k / total_nk

        # Try to place in existing group — very strict: within 10% proportional difference
        placed = False
        for g in groups:
            ref = g[0]
            ref_nk = ref.get("n_kg_ha", 0) + ref.get("k_kg_ha", 0)
            if ref_nk < 0.01:
                continue
            ref_n_prop = ref.get("n_kg_ha", 0) / ref_nk
            ref_k_prop = ref.get("k_kg_ha", 0) / ref_nk
            diff = abs(n_prop - ref_n_prop) + abs(k_prop - ref_k_prop)
            if diff < 0.10:  # Within 10% — genuinely the same blend
                g.append(app)
                placed = True
                break

        if not placed:
            groups.append([app])

    # Assign letters
    result = {}
    for i, g in enumerate(groups):
        letter = chr(65 + i)  # A, B, C...
        for app in g:
            result[app["month"]] = letter

    return result
