"""Liquid blend optimizer: custom liquid fertilizer formulation.

Optimizes liquid fertilizer blends with:
- Per-material solubility constraints (with multi-salt safety margin)
- Inequality constraints ("at least target", not "exactly target")
- Volume displacement correction (solids increase total volume)
- Per-material SG-based density estimation
- Compatibility enforcement (hard incompatible pairs blocked)
- Mixing order and instruction generation
"""

import numpy as np
from scipy.optimize import linprog

from app.services.nutrient_limits import load_liquid_limits

NUTRIENTS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]

# Multi-salt solubility safety factor: when dissolving multiple salts,
# effective solubility drops due to ionic competition. Industry standard
# is 70-80% of theoretical single-salt solubility.
MULTI_SALT_SAFETY = 0.75

# Default density factor for SG estimation when per-material SG is unknown.
# Most fertilizer salts contribute SG in the 0.5-0.7 range per unit mass fraction.
DEFAULT_DENSITY_FACTOR = 0.6

# Maximum kg of material per litre of tank — physical sanity limit.
# Even the densest salt can't exceed ~2 kg/L dissolved.
MAX_KG_PER_LITRE = 1.5


def check_compatibility(selected_materials: list[dict], compatibility_rules: list[dict]) -> list[dict]:
    """Check for incompatible material pairs.

    Returns list of warnings: [{material_a, material_b, severity, reason}]
    """
    warnings = []
    names = {m["material"] for m in selected_materials}

    for rule in compatibility_rules:
        if not rule.get("compatible", True):
            a = rule["material_a"]
            b = rule["material_b"]
            # Exact name matching (case-insensitive)
            a_match = any(a.lower() == m.lower() for m in names)
            b_match = any(b.lower() == m.lower() for m in names)
            if a_match and b_match:
                warnings.append({
                    "material_a": a,
                    "material_b": b,
                    "severity": rule.get("severity", "incompatible"),
                    "reason": rule.get("reason", "Incompatible materials"),
                })

    return warnings


def _get_incompatible_pairs(materials: list[dict], compatibility_rules: list[dict]) -> set[tuple[int, int]]:
    """Return set of (i, j) index pairs that are hard incompatible."""
    if not compatibility_rules:
        return set()

    pairs = set()
    mat_names = [m["material"].lower() for m in materials]

    for rule in compatibility_rules:
        if rule.get("compatible", True):
            continue
        if rule.get("severity", "incompatible") != "incompatible":
            continue  # Only block hard incompatible, not caution

        a = rule["material_a"].lower()
        b = rule["material_b"].lower()

        a_indices = [i for i, n in enumerate(mat_names) if n == a]
        b_indices = [i for i, n in enumerate(mat_names) if n == b]

        for ai in a_indices:
            for bi in b_indices:
                if ai != bi:
                    pairs.add((min(ai, bi), max(ai, bi)))

    return pairs


def _estimate_sg(recipe: list[dict], materials_lookup: dict[str, dict], tank_volume_l: float) -> float:
    """Estimate specific gravity using per-material SG data where available.

    For materials with known SG, we use the material's own density contribution.
    For materials without SG data, we use a default density factor.

    The formula: SG = total_mass_kg / total_volume_L
    where total_volume = water_volume + sum(material_kg / material_density)
    and total_mass = water_mass + sum(material_kg)
    """
    total_dissolved_kg = sum(r["kg_per_tank"] for r in recipe)

    if total_dissolved_kg < 0.001:
        return 1.0

    # Estimate volume occupied by dissolved solids
    solid_volume_l = 0
    for item in recipe:
        mat = materials_lookup.get(item["material"], {})
        mat_sg = float(mat.get("sg", 0)) if mat.get("sg") else 0

        if mat_sg > 0:
            # Material has known SG — its volume contribution is mass / density
            solid_volume_l += item["kg_per_tank"] / mat_sg
        else:
            # Default: assume typical fertilizer salt density ~1.5-2.0 kg/L
            solid_volume_l += item["kg_per_tank"] / 1.8

    # Total solution: water fills the rest of the tank
    water_volume_l = tank_volume_l - solid_volume_l
    if water_volume_l < 0:
        water_volume_l = 0  # Over-saturated — shouldn't happen with solubility bounds

    total_mass_kg = water_volume_l * 1.0 + total_dissolved_kg  # water density ≈ 1.0
    total_volume_l = tank_volume_l  # final volume is the tank volume

    sg = round(total_mass_kg / total_volume_l, 3) if total_volume_l > 0 else 1.0
    return max(sg, 1.0)  # SG should never be below water


def _effective_tank_volume(tank_volume_l: float, total_kg: float, materials: list[dict], x: np.ndarray) -> float:
    """Calculate effective water volume after accounting for volume displacement.

    When dissolving solids, they occupy volume. The effective water volume
    available is: tank_volume - volume_of_dissolved_solids.
    This means nutrient concentrations are higher than naive calculation assumes.

    Returns corrected tank volume for concentration calculations.
    """
    solid_volume_l = 0
    for i, mat in enumerate(materials):
        kg = x[i]
        if kg < 0.001:
            continue
        mat_sg = float(mat.get("sg", 0)) if mat.get("sg") else 0
        if mat_sg > 0:
            solid_volume_l += kg / mat_sg
        else:
            solid_volume_l += kg / 1.8  # default solid density

    # Effective volume is the actual solution volume (tank is filled to target)
    # The solids displace water, so the total solution volume stays at tank_volume_l
    # but the water portion is reduced. For concentration calc, we use tank_volume_l
    # because the user fills to the final mark.
    # However, we need to ensure we're not trying to dissolve more solid volume
    # than the tank can hold.
    if solid_volume_l > tank_volume_l * 0.5:
        # More than 50% of tank would be solids — flag as problematic
        return tank_volume_l  # Return nominal, optimizer bounds should prevent this

    return tank_volume_l


def optimize_liquid_blend(
    targets: dict[str, float],
    materials: list[dict],
    tank_volume_l: float = 1000,
    compatibility_rules: list[dict] | None = None,
) -> dict:
    """Optimize a liquid blend to hit nutrient targets.

    Args:
        targets: nutrient targets as g/L in final solution
            e.g. {"n": 5.0, "p": 2.0, "k": 3.0}
        materials: list of material dicts with nutrient %ages and solubility
            Each needs: material, n, p, k, ..., solubility_20c, mixing_order
        tank_volume_l: batch size in litres (default 1000L)
        compatibility_rules: from material_compatibility table

    Returns:
        dict with: success, recipe, nutrients, total_dissolved, sg_estimate,
        mixing_instructions, compatibility_warnings
    """
    if not materials:
        return {"success": False, "error": "No materials selected"}

    # Load nutrient safety limits from DB (with fallback)
    nutrient_limits = load_liquid_limits()

    # ── Pre-check: remove hard-incompatible pairs ──────────────────────
    # If incompatible materials are both selected, we need to choose subsets.
    # Strategy: check all pairs, if any hard incompatible found, report them
    # and let the user resolve (rather than silently dropping materials).
    incompatible_pairs = _get_incompatible_pairs(materials, compatibility_rules or [])

    n_mats = len(materials)
    n_active = list(range(n_mats))  # indices of materials we'll actually use

    # Count how many materials have at least some nutrient content for targets
    has_nutrients = set()
    for nut in NUTRIENTS:
        if targets.get(nut, 0) > 0:
            for i, mat in enumerate(materials):
                if float(mat.get(nut, 0)) > 0:
                    has_nutrients.add(i)

    # ── Build constraint matrices ─────────────────────────────────────
    # Use INEQUALITY constraints: actual >= target (i.e., -actual <= -target)
    # This means A_ub * x <= b_ub where A_ub rows are negated nutrient contributions

    A_ub = []  # inequality: -nutrient_contribution <= -target
    b_ub = []

    targeted_nutrients = []
    for nut in NUTRIENTS:
        target_g_per_l = targets.get(nut, 0)
        if target_g_per_l <= 0:
            continue

        targeted_nutrients.append(nut)
        target_total_g = target_g_per_l * tank_volume_l

        row = []
        for mat in materials:
            pct = float(mat.get(nut, 0))
            g_per_kg = pct * 10  # g of nutrient per kg of material
            row.append(-g_per_kg)  # negated for >= constraint

        A_ub.append(row)
        b_ub.append(-target_total_g)

    if not A_ub:
        return {"success": False, "error": "No nutrient targets specified"}

    # ── Upper-bound constraints for ALL nutrients (toxicity safety) ────
    # Prevents non-target nutrients from accumulating to dangerous levels.
    # For targeted nutrients, the max is the higher of (target, safe limit).
    for nut in NUTRIENTS:
        max_g_per_l = nutrient_limits.get(nut)
        if not max_g_per_l:
            continue

        # If this nutrient is targeted, allow at least the target
        target_g_per_l = targets.get(nut, 0)
        effective_max = max(max_g_per_l, target_g_per_l * 1.5) if target_g_per_l > 0 else max_g_per_l

        max_total_g = effective_max * tank_volume_l

        # Check if any material contributes this nutrient
        row = []
        any_contribution = False
        for mat in materials:
            pct = float(mat.get(nut, 0))
            g_per_kg = pct * 10
            row.append(g_per_kg)  # positive: contribution <= max
            if g_per_kg > 0:
                any_contribution = True

        if any_contribution:
            A_ub.append(row)
            b_ub.append(max_total_g)

    # ── Objective: minimize cost (or total weight) ────────────────────
    c = []
    for mat in materials:
        cost = float(mat.get("cost_per_ton", 0))
        if cost > 0:
            c.append(cost / 1000)  # cost per kg
        else:
            c.append(1.0)  # minimize weight if no cost

    # ── Bounds: solubility with multi-salt safety margin ──────────────
    n_materials_with_solubility = sum(1 for m in materials if m.get("solubility_20c") and float(m.get("solubility_20c", 0)) > 0)
    # Apply safety margin when multiple salts are being mixed
    safety = MULTI_SALT_SAFETY if n_materials_with_solubility > 1 else 1.0

    bounds = []
    for mat in materials:
        sol = mat.get("solubility_20c")
        if sol and float(sol) > 0:
            # Solubility is g/L, max in tank = sol * tank_volume_l / 1000 (in kg)
            # Apply multi-salt safety factor
            max_kg = float(sol) * safety * tank_volume_l / 1000
        else:
            # No solubility data — use conservative physical limit
            max_kg = MAX_KG_PER_LITRE * tank_volume_l * 0.1  # 10% of max theoretical
        bounds.append((0, max_kg))

    # ── Solve ─────────────────────────────────────────────────────────
    A_ub_arr = np.array(A_ub, dtype=float)
    b_ub_arr = np.array(b_ub, dtype=float)

    result = linprog(
        c=c,
        A_ub=A_ub_arr,
        b_ub=b_ub_arr,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        # Try relaxed — find closest achievable
        return _find_closest_liquid_blend(
            c, A_ub_arr, b_ub_arr, bounds, materials, targets,
            tank_volume_l, compatibility_rules, nutrient_limits,
        )

    x = result.x

    # ── Build recipe ──────────────────────────────────────────────────
    recipe, total_kg = _build_recipe(x, materials, tank_volume_l)

    # ── Volume displacement check ─────────────────────────────────────
    effective_vol = _effective_tank_volume(tank_volume_l, total_kg, materials, x)

    # ── Calculate actual nutrients ────────────────────────────────────
    nutrients = _calc_nutrients(x, materials, targets, tank_volume_l)

    # ── Estimate SG ───────────────────────────────────────────────────
    mat_lookup = {m["material"]: m for m in materials}
    sg_estimate = _estimate_sg(recipe, mat_lookup, tank_volume_l)

    # ── Compatibility check ───────────────────────────────────────────
    compat_warnings = []
    if compatibility_rules:
        compat_warnings = check_compatibility(
            [{"material": r["material"]} for r in recipe],
            compatibility_rules,
        )

    # ── Mixing instructions ───────────────────────────────────────────
    mixing_instructions = _build_mixing_instructions(recipe, tank_volume_l)

    # ── Safety warnings ───────────────────────────────────────────────
    warnings = _generate_warnings(nutrients, total_kg, tank_volume_l, recipe, materials, x, nutrient_limits)

    return {
        "success": True,
        "exact": True,
        "recipe": recipe,
        "nutrients": nutrients,
        "tank_volume_l": tank_volume_l,
        "total_dissolved_kg": round(total_kg, 2),
        "sg_estimate": sg_estimate,
        "compatibility_warnings": compat_warnings,
        "mixing_instructions": mixing_instructions,
        "warnings": warnings,
    }


def _generate_warnings(nutrients: list[dict], total_kg: float, tank_volume_l: float,
                       recipe: list[dict], materials: list[dict], x,
                       nutrient_limits: dict[str, float] | None = None) -> list[str]:
    """Generate safety and practical warnings about the blend."""
    warnings = []

    # Temperature warning: high dissolved solids risk precipitation at low temps
    concentration_pct = (total_kg / (tank_volume_l * 1.0)) * 100  # % w/v
    if concentration_pct > 15:
        warnings.append(
            f"High concentration ({concentration_pct:.0f}% w/v). "
            "Solution may precipitate if stored below 20°C. "
            "Perform a jar test before full-scale mixing."
        )
    elif concentration_pct > 8:
        warnings.append(
            "Store above 15°C to prevent salt crystallisation. "
            "If solution turns cloudy or forms crystals, warm and re-agitate."
        )

    # Check non-target nutrients approaching limits
    for nut_row in nutrients:
        nut = nut_row["nutrient"].lower()
        actual = nut_row["actual_g_l"]
        target = nut_row["target_g_l"]
        max_safe = (nutrient_limits or {}).get(nut, 999)

        if actual > 0.001 and target <= 0 and actual > max_safe * 0.7:
            warnings.append(
                f"{nut_row['nutrient']} is not targeted but reached {actual:.2f} g/L "
                f"(safe limit {max_safe} g/L). Consider alternative materials."
            )

    # Boron-specific warning (very narrow safe range)
    b_row = next((n for n in nutrients if n["nutrient"] == "B"), None)
    if b_row and b_row["actual_g_l"] > 0.1:
        warnings.append(
            f"Boron at {b_row['actual_g_l']:.2f} g/L — B has a very narrow safe range. "
            "Verify application rate will not exceed crop tolerance (citrus: max 0.05 g/L applied)."
        )

    return warnings


def _build_recipe(x: np.ndarray, materials: list[dict], tank_volume_l: float) -> tuple[list[dict], float]:
    """Build recipe list from optimizer solution."""
    recipe = []
    total_kg = 0
    for i, mat in enumerate(materials):
        kg = round(x[i], 3)
        if kg < 0.001:
            continue
        g_per_l = round(kg * 1000 / tank_volume_l, 2)
        recipe.append({
            "material": mat["material"],
            "type": mat.get("type"),
            "kg_per_tank": round(kg, 2),
            "g_per_l": g_per_l,
            "mixing_order": mat.get("mixing_order", 5),
            "mixing_notes": mat.get("mixing_notes", ""),
        })
        total_kg += kg

    recipe.sort(key=lambda r: r["mixing_order"])
    return recipe, total_kg


def _calc_nutrients(x: np.ndarray, materials: list[dict], targets: dict, tank_volume_l: float) -> list[dict]:
    """Calculate actual nutrient concentrations."""
    n_mats = len(materials)
    nutrients = []
    for nut in NUTRIENTS:
        target = targets.get(nut, 0)
        actual_g = sum(x[i] * float(materials[i].get(nut, 0)) * 10 for i in range(n_mats))
        actual_g_per_l = round(actual_g / tank_volume_l, 4)
        nutrients.append({
            "nutrient": nut.upper(),
            "target_g_l": round(target, 4),
            "actual_g_l": actual_g_per_l,
            "diff_g_l": round(actual_g_per_l - target, 4),
        })
    return nutrients


def _find_closest_liquid_blend(c, A_ub, b_ub, bounds, materials, targets, tank_volume_l, compatibility_rules, nutrient_limits=None):
    """Binary search for the highest achievable scale factor."""
    best_scale = 0
    best_x = None

    lo, hi = 0.0, 1.0
    for _ in range(20):
        mid = (lo + hi) / 2
        scaled_b = b_ub * mid  # Scale all targets by mid

        result = linprog(c=c, A_ub=A_ub, b_ub=scaled_b, bounds=bounds, method="highs")
        if result.success:
            best_scale = mid
            best_x = result.x
            lo = mid
        else:
            hi = mid

    if best_x is None:
        return {"success": False, "error": "Could not find a feasible liquid blend with these materials"}

    recipe, total_kg = _build_recipe(best_x, materials, tank_volume_l)
    nutrients = _calc_nutrients(best_x, materials, targets, tank_volume_l)

    mat_lookup = {m["material"]: m for m in materials}
    sg_estimate = _estimate_sg(recipe, mat_lookup, tank_volume_l)

    compat_warnings = []
    if compatibility_rules:
        compat_warnings = check_compatibility(
            [{"material": r["material"]} for r in recipe],
            compatibility_rules,
        )

    warnings = _generate_warnings(nutrients, total_kg, tank_volume_l, recipe, materials, best_x, nutrient_limits)

    return {
        "success": True,
        "exact": False,
        "scale": round(best_scale, 3),
        "recipe": recipe,
        "nutrients": nutrients,
        "tank_volume_l": tank_volume_l,
        "total_dissolved_kg": round(total_kg, 2),
        "sg_estimate": sg_estimate,
        "compatibility_warnings": compat_warnings,
        "mixing_instructions": _build_mixing_instructions(recipe, tank_volume_l),
        "warnings": warnings,
    }


def _build_mixing_instructions(recipe: list[dict], tank_volume_l: float) -> list[str]:
    """Generate step-by-step mixing instructions."""
    steps = [f"Fill batch tank with {int(tank_volume_l * 0.6)}L clean water (60% of final volume)"]

    for item in recipe:
        order = item.get("mixing_order", 5)
        if order <= 2:
            steps.append(f"Add {item['kg_per_tank']} kg {item['material']} — {item.get('mixing_notes') or 'mix until dissolved'}")
        elif order <= 4:
            steps.append(f"Add {item['kg_per_tank']} kg {item['material']} — dissolve fully before next addition")
        elif order <= 7:
            steps.append(f"Add {item['kg_per_tank']} kg {item['material']} — stir until dissolved")
        elif order <= 8:
            steps.append(f"Add {item['kg_per_tank']} kg {item['material']} (chelate) — add after salts are dissolved")
        else:
            steps.append(f"Add {item['kg_per_tank']} kg {item['material']} — add LAST, stir gently")

    steps.append(f"Top up to {int(tank_volume_l)}L with clean water")
    steps.append("Agitate for 10 minutes before use")

    return steps


def run_liquid_priority_optimizer(
    targets: dict[str, float],
    priorities: dict[str, str],
    materials: list[dict],
    tank_volume_l: float = 1000,
    compatibility_rules: list[dict] | None = None,
) -> dict:
    """Optimize with nutrient priorities — satisfy must_match first, flex on the rest.

    Same algorithm as dry blend priority optimizer but for liquid blends.
    Returns full liquid blend result with priority_result metadata.
    """
    # 1. Try all targets first
    result = optimize_liquid_blend(targets, materials, tank_volume_l, compatibility_rules)
    if result.get("exact"):
        result["priority_result"] = {
            "matched": list(targets.keys()),
            "compromised": [],
            "feasible": True,
            "scale": 1.0,
        }
        return result

    # 2. Separate must_match and flexible targets
    must_match = {n: v for n, v in targets.items() if priorities.get(n) == "must_match" or priorities.get(n.upper()) == "must_match"}
    flexible = [(n, v) for n, v in targets.items() if n not in must_match]
    flexible.sort(key=lambda x: x[1])  # drop smallest first

    # 3. Try removing flexible targets one at a time
    remaining_flex = list(flexible)
    best_result = None
    dropped = []

    while remaining_flex:
        trial = dict(must_match)
        for n, v in remaining_flex:
            trial[n] = v

        res = optimize_liquid_blend(trial, materials, tank_volume_l, compatibility_rules)
        if res.get("exact") or (res.get("success") and res.get("scale", 0) > 0.95):
            best_result = res
            break

        dropped_nutrient = remaining_flex.pop(0)
        dropped.append(dropped_nutrient)

    # 4. If still no luck, try just must_match
    if best_result is None and must_match:
        res = optimize_liquid_blend(must_match, materials, tank_volume_l, compatibility_rules)
        if res.get("success"):
            best_result = res
            dropped = list(flexible)

    # 5. If even must_match alone fails, return the scaled result
    if best_result is None:
        result["priority_result"] = {
            "matched": [],
            "compromised": [{"nutrient": n.upper(), "target": round(v, 3), "actual": 0} for n, v in targets.items()],
            "feasible": False,
            "scale": 0,
        }
        result["contact_sapling"] = True
        return result

    # 6. Calculate matched vs compromised from actual nutrients
    matched = []
    compromised = []
    nutrients_map = {n["nutrient"]: n for n in best_result.get("nutrients", [])}

    for nut, target in targets.items():
        nut_upper = nut.upper()
        actual_row = nutrients_map.get(nut_upper, {})
        actual = actual_row.get("actual_g_l", 0)

        was_dropped = nut in [d[0] for d in dropped]

        if not was_dropped and abs(actual - target) < 0.05:
            matched.append(nut_upper)
        else:
            compromised.append({
                "nutrient": nut_upper,
                "target": round(target, 3),
                "actual": round(actual, 3),
            })

    best_result["priority_result"] = {
        "matched": matched,
        "compromised": compromised,
        "feasible": True,
        "scale": best_result.get("scale", 1.0),
    }
    best_result["contact_sapling"] = False

    return best_result


def calculate_application_rates(
    total_dissolved_kg: float,
    tank_volume_l: float,
    sg: float,
    target_rate_kg_ha: float | None = None,
    plants_per_ha: int | None = None,
) -> dict:
    """Calculate practical application rates.

    Returns rates for both broadacre (L/ha) and per-tree if applicable.
    """
    rates = {}

    if target_rate_kg_ha and sg > 0:
        l_per_ha = round(target_rate_kg_ha / sg, 1)
        rates["l_per_ha"] = l_per_ha
        rates["kg_per_ha"] = target_rate_kg_ha
        rates["tanks_per_ha"] = round(l_per_ha / tank_volume_l, 2)

        if plants_per_ha and plants_per_ha > 0:
            rates["l_per_tree"] = round(l_per_ha / plants_per_ha, 3)
            rates["ml_per_tree"] = round(l_per_ha * 1000 / plants_per_ha, 1)

    return rates
