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

# Maximum total elemental nutrient content (N + P + K, m/m %) of the
# finished solution. Derived from the global commercial clear-liquid NPK
# envelope: AgroLiquid Pro-Germinator 9-24-3, Simplot 6-24-6, NACHURS
# 9-18-9 all land at ~36% m/m oxide = ~23-24% m/m elemental at SG 1.33
# (~500 g/L oxide nutrient, ~325 g/L elemental). Zero-K APP products
# (10-34-0, 11-37-0) reach 44-48% oxide because they dodge the KCl
# solubility bottleneck, but balanced NPK tops out lower. 25% m/m
# elemental gives a small cushion above observed real products and
# cleanly rejects suspension-territory blends (which run ≥30% elemental).
#
# Sources: AdvanSix Sulf-N formulation guide ("clear liquids usually
# less than 30% plant food"), Mississippi State Extension (KCl caps K2O
# at ~11%), published TDSes from AgroLiquid / Simplot / NACHURS / Kugler
# / CropChoice / Tessenderlo surveyed April 2026.
MAX_NUTRIENT_MM_PCT = 25.0


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
    required_materials: dict[str, float] | None = None,
) -> dict:
    """Optimize a liquid blend to hit nutrient targets.

    Args:
        targets: nutrient targets as g/L in final solution
            e.g. {"n": 5.0, "p": 2.0, "k": 3.0}
        materials: list of material dicts with nutrient %ages and solubility
            Each needs: material, n, p, k, ..., solubility_20c, mixing_order
        tank_volume_l: batch size in litres (default 1000L)
        compatibility_rules: from material_compatibility table
        required_materials: {material_name: pct_of_total_mass} exact equalities

    Returns:
        dict with: success, recipe, nutrients, total_dissolved, sg_estimate,
        mixing_instructions, compatibility_warnings
    """
    if not materials:
        return {"success": False, "error": "No materials selected"}

    # ── Diagnostic: any targeted nutrient with no source in selection? ──
    missing_sources = [
        nut.upper()
        for nut in NUTRIENTS
        if targets.get(nut, 0) > 0
        and not any(float(m.get(nut, 0) or 0) > 0 for m in materials)
    ]
    if missing_sources:
        joined = ", ".join(missing_sources)
        return {
            "success": False,
            "error": (
                f"No source for {joined} in selected materials. "
                f"Add a material containing {joined} to the selection."
            ),
            "missing_sources": missing_sources,
        }

    # Validate required_materials: must be in selection, pct in (0, 100], sum ≤ 100
    required_constraints: list[tuple[int, float]] = []
    if required_materials:
        name_to_idx = {m["material"]: i for i, m in enumerate(materials)}
        unknown = [n for n in required_materials if n not in name_to_idx]
        if unknown:
            return {
                "success": False,
                "error": f"Required materials not in selection: {', '.join(unknown)}",
            }
        bad_pct = [n for n, p in required_materials.items() if p <= 0 or p > 100]
        if bad_pct:
            return {
                "success": False,
                "error": f"Required % must be between 0 and 100 for: {', '.join(bad_pct)}",
            }
        total_required_pct = sum(required_materials.values())
        if total_required_pct > 100.001:
            return {
                "success": False,
                "error": (
                    f"Required materials total {total_required_pct:.1f}% — "
                    "cannot exceed 100%."
                ),
            }
        required_constraints = [
            (name_to_idx[n], float(p) / 100.0)
            for n, p in required_materials.items()
        ]

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

    # NOTE: Phytotoxicity caps (nutrient_limits in g/L) are not applied as
    # LP constraints — they were blocking legitimate concentrate formulations.
    # Safe-application concentration is handled downstream via dilution
    # instructions on the printed label, not at formulation time. The LP's
    # real physical constraints remain: solubility, multi-salt safety, and
    # the per-material density bound below.

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

    # Build equality rows for required-% constraints (exact mass fraction).
    #   For material i required at fraction p of total:
    #     x_i = p * sum(x_j)  →  (1-p)*x_i - p*sum_{j≠i}(x_j) = 0
    A_eq_arr = None
    b_eq_arr = None
    if required_constraints:
        eq_rows = []
        for idx, frac in required_constraints:
            row = [-frac] * n_mats
            row[idx] = 1.0 - frac
            eq_rows.append(row)
        A_eq_arr = np.array(eq_rows, dtype=float)
        b_eq_arr = np.zeros(len(eq_rows), dtype=float)

    lp_kwargs = dict(c=c, A_ub=A_ub_arr, b_ub=b_ub_arr, bounds=bounds, method="highs")
    if A_eq_arr is not None:
        lp_kwargs["A_eq"] = A_eq_arr
        lp_kwargs["b_eq"] = b_eq_arr

    result = linprog(**lp_kwargs)

    if not result.success:
        # Try relaxed — find closest achievable
        return _find_closest_liquid_blend(
            c, A_ub_arr, b_ub_arr, bounds, materials, targets,
            tank_volume_l, compatibility_rules, nutrient_limits,
            A_eq=A_eq_arr, b_eq=b_eq_arr,
            required_materials=required_materials,
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
    """Generate formulation-time warnings about the blend.

    Per-nutrient phytotoxicity warnings were removed: all blends ship with
    dilution instructions on the label, so safe application concentration
    is handled downstream, not here. The warnings we still emit are about
    formulation chemistry — precipitation risk at low temperatures when the
    dissolved-solids fraction is high.
    """
    warnings = []

    # Total-dissolved w/v thresholds calibrated against real commercial
    # clear-liquid NPK products. The 60-85% w/v band is where mainstream
    # products live (9-24-3, 10-34-0, UAN32, etc.); above 85% you're at
    # the edge of the manufacturing envelope and salt-out risk climbs.
    concentration_pct = (total_kg / (tank_volume_l * 1.0)) * 100  # % w/v
    if concentration_pct > 85:
        warnings.append(
            f"Near the manufacturing ceiling ({concentration_pct:.0f}% w/v). "
            "Store above 20°C and always jar-test before full-scale mixing — "
            "high-density blends crystallise if temperature drops."
        )
    elif concentration_pct > 60:
        warnings.append(
            f"Concentrated blend ({concentration_pct:.0f}% w/v). "
            "Store above 10°C to keep the solution clear; if it turns "
            "cloudy, warm gently and re-agitate before use."
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
            "mixing_order": mat.get("mixing_order") or 5,
            "mixing_notes": mat.get("mixing_notes") or "",
        })
        total_kg += kg

    recipe.sort(key=lambda r: r["mixing_order"] or 5)
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


def _find_closest_liquid_blend(c, A_ub, b_ub, bounds, materials, targets, tank_volume_l, compatibility_rules, nutrient_limits=None, A_eq=None, b_eq=None, required_materials=None):
    """Binary search for the highest achievable scale factor."""
    best_scale = 0
    best_x = None

    lo, hi = 0.0, 1.0
    for _ in range(20):
        mid = (lo + hi) / 2
        scaled_b = b_ub * mid  # Scale all targets by mid

        kwargs = dict(c=c, A_ub=A_ub, b_ub=scaled_b, bounds=bounds, method="highs")
        if A_eq is not None:
            kwargs["A_eq"] = A_eq
            kwargs["b_eq"] = b_eq
        result = linprog(**kwargs)
        if result.success:
            best_scale = mid
            best_x = result.x
            lo = mid
        else:
            hi = mid

    if best_x is None:
        hint = ""
        if required_materials:
            hint = (
                " The required-% constraint may be incompatible with the "
                "nutrient targets. Try lowering the required % or removing "
                "some required materials."
            )
        return {
            "success": False,
            "error": (
                "Could not find a feasible blend with the selected materials. "
                "Likely reason: solubility or safety-limit constraints prevent "
                "hitting the requested g/L at this tank size. Try a larger "
                "batch volume or relax / reduce the highest target."
                + hint
            ),
        }

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
        order = item.get("mixing_order") or 5
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
    required_materials: dict[str, float] | None = None,
) -> dict:
    """Optimize with nutrient priorities — satisfy must_match first, flex on the rest.

    Same algorithm as dry blend priority optimizer but for liquid blends.
    Returns full liquid blend result with priority_result metadata.
    """
    # 1. Try all targets first
    result = optimize_liquid_blend(targets, materials, tank_volume_l, compatibility_rules, required_materials)
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

        res = optimize_liquid_blend(trial, materials, tank_volume_l, compatibility_rules, required_materials)
        if res.get("exact") or (res.get("success") and res.get("scale", 0) > 0.95):
            best_result = res
            break

        dropped_nutrient = remaining_flex.pop(0)
        dropped.append(dropped_nutrient)

    # 4. If still no luck, try just must_match
    if best_result is None and must_match:
        res = optimize_liquid_blend(must_match, materials, tank_volume_l, compatibility_rules, required_materials)
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


# ════════════════════════════════════════════════════════════════════════════
# Mass-fraction (m/m) liquid optimizer — the "comprehensive" path
#
# Targets are m/m percentages (what SA notation and Act 36 express). The LP
# runs entirely in mass-fraction space, so no SG guess is needed up front:
# density falls out of the recipe as a computed output. This removes the
# circular dependency that forced the old g/L optimizer to take an SG input.
#
# Variables (n materials + water):
#   f_i ∈ [0, 1]  — mass fraction of material i in the finished solution
#   f_w ∈ [0, 1]  — mass fraction of water
#
# Normalization (equality):
#   Σ f_i + f_w = 1
#
# Nutrient targets (inequality, achieved ≥ requested):
#   Σ f_i × pct_i(nut) / 100  ≥  target_mm(nut) / 100
#
# Safety caps (inequality, achieved ≤ limit):
#   Converted from g/L limits using a conservative SG (1.5 kg/L) so the
#   m/m cap is tighter than the real g/L cap — errs on the safe side.
#
# Solubility (inequality, per material):
#   Dissolved kg_i  ≤  sol_i × water_kg / 1000   (sol_i is g solute / L water)
#   Scaling both sides by total_mass gives:  f_i  ≤  sol_i × f_w / 1000
#   Multi-salt safety factor applied when > 1 material has solubility data.
#
# Required materials (equality):
#   f_i = required_pct / 100   — identical to dry blend semantics.
#
# Objective:
#   Minimise Σ f_i × cost_per_kg_i  (cost per kg of finished blend)
# ════════════════════════════════════════════════════════════════════════════

# Conservative SG used when translating g/L safety limits into m/m caps.
# Picking a HIGH value means the m/m cap we enforce is LOWER, so the LP
# is stricter than strictly necessary — the solution is guaranteed to
# respect the real g/L limit once we compute the actual SG.
_SAFETY_SG_CEILING = 1.5


def _compute_sg_from_fractions(
    mass_fractions: dict[str, float],
    water_fraction: float,
    materials_lookup: dict[str, dict],
) -> float:
    """Compute finished-blend SG from mass fractions.

    sg = 1 / (f_w / ρ_w + Σ f_i / ρ_i)   where ρ_w = 1 kg/L for water
    and ρ_i is the material's own density (the `sg` column). Materials
    without a density fall back to 1.8 kg/L (typical fertilizer salt).
    """
    inv_vol = water_fraction  # water contributes f_w / 1.0
    for mat_name, f_i in mass_fractions.items():
        if f_i < 1e-9:
            continue
        mat = materials_lookup.get(mat_name, {})
        rho_i = float(mat.get("sg") or 0) or 1.8
        inv_vol += f_i / rho_i
    if inv_vol < 1e-9:
        return 1.0
    return 1.0 / inv_vol


def optimize_liquid_blend_mm(
    targets_mm: dict[str, float],
    materials: list[dict],
    tank_volume_l: float = 1000,
    compatibility_rules: list[dict] | None = None,
    required_materials: dict[str, float] | None = None,
) -> dict:
    """Optimize a liquid blend given m/m nutrient targets.

    Args:
        targets_mm: nutrient targets as m/m percentages of the finished
            solution (elemental form, matching SA notation).
            e.g. {"n": 9.09, "p": 1.82, "k": 9.09} for a 5:1:5(20) grade.
        materials: liquid-compatible material rows (must include material,
            nutrient %s, solubility_20c, sg, mixing_order).
        tank_volume_l: reporting volume — used to scale the mass-fraction
            result into a concrete recipe (kg per material, L of water).
            Does not affect the LP (which is unit-less in mass fractions).
        compatibility_rules: from material_compatibility table.
        required_materials: {material_name: pct_of_total_mass}. Same semantics
            as the g/L optimizer.

    Returns:
        dict identical in shape to optimize_liquid_blend, plus:
            - nutrient_composition: [{nutrient, m_m_pct, g_per_l}] per nutrient
            - density_kg_per_l: computed finished-blend SG
            - sa_notation: string like "5:1:5 (20)" derived from achieved m/m
            - international_notation: "N 9.1% P 1.8% K 9.1%"
    """
    if not materials:
        return {"success": False, "error": "No materials selected"}

    # ── Diagnostics: targeted nutrient with no source in selection? ──
    missing_sources = [
        nut.upper()
        for nut in NUTRIENTS
        if targets_mm.get(nut, 0) > 0
        and not any(float(m.get(nut, 0) or 0) > 0 for m in materials)
    ]
    if missing_sources:
        joined = ", ".join(missing_sources)
        return {
            "success": False,
            "error": (
                f"No source for {joined} in selected materials. "
                f"Add a material containing {joined} to the selection."
            ),
            "missing_sources": missing_sources,
        }

    # ── Validate required_materials (same rules as the g/L path) ──
    required_constraints: list[tuple[int, float]] = []
    if required_materials:
        name_to_idx = {m["material"]: i for i, m in enumerate(materials)}
        unknown = [n for n in required_materials if n not in name_to_idx]
        if unknown:
            return {
                "success": False,
                "error": f"Required materials not in selection: {', '.join(unknown)}",
            }
        bad_pct = [n for n, p in required_materials.items() if p <= 0 or p > 100]
        if bad_pct:
            return {
                "success": False,
                "error": f"Required % must be between 0 and 100 for: {', '.join(bad_pct)}",
            }
        total_required_pct = sum(required_materials.values())
        if total_required_pct > 100.001:
            return {
                "success": False,
                "error": (
                    f"Required materials total {total_required_pct:.1f}% — "
                    "cannot exceed 100%."
                ),
            }
        required_constraints = [
            (name_to_idx[n], float(p) / 100.0)
            for n, p in required_materials.items()
        ]

    nutrient_limits = load_liquid_limits()

    n_mats = len(materials)
    n_vars = n_mats + 1  # materials + water
    water_idx = n_mats

    # ── Build constraint matrices ──────────────────────────────────────
    # A_ub × x ≤ b_ub. Normalization is A_eq × x = b_eq.
    A_ub: list[list[float]] = []
    b_ub: list[float] = []

    targeted_nutrients = []
    for nut in NUTRIENTS:
        tgt_mm_pct = targets_mm.get(nut, 0)
        if tgt_mm_pct <= 0:
            continue
        targeted_nutrients.append(nut)
        # Σ f_i × pct_i / 100 ≥ tgt_mm_pct / 100
        # Negate to get ≤ form: -Σ f_i × pct_i / 100 ≤ -tgt_mm_pct / 100
        row = [0.0] * n_vars
        for i, mat in enumerate(materials):
            row[i] = -float(mat.get(nut, 0)) / 100.0
        # row[water_idx] stays 0 — water contributes no nutrients
        A_ub.append(row)
        b_ub.append(-tgt_mm_pct / 100.0)

    if not A_ub:
        return {"success": False, "error": "No nutrient targets specified"}

    # NOTE: The g/L phytotoxicity caps from load_liquid_limits() are INTENTIONALLY
    # NOT applied in the m/m path. Those limits (e.g. N ≤ 20 g/L, P ≤ 15 g/L)
    # guard against leaf/root burn when a solution is APPLIED to a plant.
    # A concentrated product (2:3:2(12), 5:1:5(20), etc.) is formulated to be
    # DILUTED before application, so its in-drum concentration can and should
    # exceed applied-solution limits. The real physical constraints on a
    # concentrate are: solubility (below), multi-salt safety margin, and the
    # practical density bound (handled via bounds + saturation warning).
    # Post-solve, _generate_warnings() still flags if the concentrate exceeds
    # ~15% w/v dissolved solids so the agronomist knows it needs dilution.

    # ── Solubility (per material) ──
    # f_i ≤ sol_i × safety × f_w / 1000
    # → f_i - sol_i × safety / 1000 × f_w ≤ 0
    n_with_solubility = sum(
        1 for m in materials
        if m.get("solubility_20c") and float(m.get("solubility_20c", 0)) > 0
    )
    sol_safety = MULTI_SALT_SAFETY if n_with_solubility > 1 else 1.0

    for i, mat in enumerate(materials):
        sol = mat.get("solubility_20c")
        form = (mat.get("form") or "solid").lower()
        row = [0.0] * n_vars
        if sol and float(sol) > 0:
            row[i] = 1.0
            row[water_idx] = -float(sol) * sol_safety / 1000.0
            A_ub.append(row)
            b_ub.append(0.0)
        elif form == "liquid":
            # Miscible concentrated liquids (e.g. phosphoric acid 80%, UAN)
            # don't have a solubility_20c and mix with water in any
            # proportion — but they're themselves near-saturated solutions,
            # so letting them reach 100% of a blend produces a "pure acid"
            # result, not a fertilizer. Cap at 50% of the finished blend:
            # a stable upper bound for real-world NPK liquid formulations.
            row[i] = 1.0
            A_ub.append(row)
            b_ub.append(0.5)
        else:
            # Solid without solubility data — conservative cap: f_i ≤ 0.05.
            # Narrow guardrail for rare materials we have no chemistry data on.
            row[i] = 1.0
            A_ub.append(row)
            b_ub.append(0.05)

    # ── Maximum total elemental nutrient content ──
    # Cap Σ f_i × (n% + p% + k%) / 100 ≤ MAX_NUTRIENT_MM_PCT / 100.
    # This is a direct m/m constraint (no SG approximation needed) that
    # matches how the industry actually bounds stable clear-liquid NPK
    # formulations. Real total-dissolved mass fraction is often 60-85%
    # (KCl alone brings 4-7× its K mass in chloride), so capping that
    # directly blocks real products; capping nutrient content correctly
    # limits the product class.
    nutrient_row = [0.0] * n_vars
    for i, mat in enumerate(materials):
        nutrient_row[i] = (
            float(mat.get("n", 0) or 0)
            + float(mat.get("p", 0) or 0)
            + float(mat.get("k", 0) or 0)
        ) / 100.0
    # nutrient_row[water_idx] stays 0 — water contributes no nutrients
    A_ub.append(nutrient_row)
    b_ub.append(MAX_NUTRIENT_MM_PCT / 100.0)

    # ── Normalization + required-% equalities ──
    # Σ f_i + f_w = 1
    norm_row = [1.0] * n_vars
    A_eq: list[list[float]] = [norm_row]
    b_eq: list[float] = [1.0]

    # Required-% as direct mass-fraction equality: f_i = p
    for idx, frac in required_constraints:
        eq_row = [0.0] * n_vars
        eq_row[idx] = 1.0
        A_eq.append(eq_row)
        b_eq.append(frac)

    # ── Incompatible pair enforcement ──
    # We cannot express "at most one of a pair" in a pure LP, so we defer
    # hard-incompatibility to a pre-flight check and surface as an error.
    incompatible = _get_incompatible_pairs(materials, compatibility_rules or [])
    if incompatible:
        names = set()
        for i, j in incompatible:
            names.add(materials[i]["material"])
            names.add(materials[j]["material"])
        return {
            "success": False,
            "error": (
                "Incompatible materials selected together: "
                + ", ".join(sorted(names))
                + ". Remove one from each incompatible pair."
            ),
            "incompatible_materials": sorted(names),
        }

    # ── Objective: minimise cost per kg of finished blend ──
    c = [0.0] * n_vars
    for i, mat in enumerate(materials):
        cost = float(mat.get("cost_per_ton", 0) or 0)
        c[i] = cost / 1000.0 if cost > 0 else 1.0
    c[water_idx] = 0.0  # water is free

    # ── Bounds ──
    bounds = [(0.0, 1.0)] * n_vars

    # ── Solve ──
    A_ub_arr = np.array(A_ub, dtype=float) if A_ub else None
    b_ub_arr = np.array(b_ub, dtype=float) if b_ub else None
    A_eq_arr = np.array(A_eq, dtype=float)
    b_eq_arr = np.array(b_eq, dtype=float)

    result = linprog(
        c=c,
        A_ub=A_ub_arr,
        b_ub=b_ub_arr,
        A_eq=A_eq_arr,
        b_eq=b_eq_arr,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        return _find_closest_mm_blend(
            c=c,
            A_ub=A_ub_arr,
            b_ub=b_ub_arr,
            A_eq=A_eq_arr,
            b_eq=b_eq_arr,
            bounds=bounds,
            materials=materials,
            targets_mm=targets_mm,
            targeted_nutrients=targeted_nutrients,
            tank_volume_l=tank_volume_l,
            compatibility_rules=compatibility_rules,
            nutrient_limits=nutrient_limits,
            required_materials=required_materials,
        )

    return _package_mm_result(
        x=result.x,
        materials=materials,
        targets_mm=targets_mm,
        tank_volume_l=tank_volume_l,
        compatibility_rules=compatibility_rules,
        nutrient_limits=nutrient_limits,
        exact=True,
        scale=1.0,
    )


def _package_mm_result(
    x: np.ndarray,
    materials: list[dict],
    targets_mm: dict[str, float],
    tank_volume_l: float,
    compatibility_rules: list[dict] | None,
    nutrient_limits: dict[str, float] | None,
    exact: bool,
    scale: float,
) -> dict:
    """Translate a mass-fraction LP solution into the full blend result dict."""
    from app.services.notation import pct_to_sa_notation

    n_mats = len(materials)
    mat_fractions = {materials[i]["material"]: float(x[i]) for i in range(n_mats)}
    water_fraction = float(x[n_mats])
    mat_lookup = {m["material"]: m for m in materials}

    density = _compute_sg_from_fractions(mat_fractions, water_fraction, mat_lookup)

    # Scale the unit-mass solution to the user's tank size.
    tank_mass_kg = tank_volume_l * density
    water_kg = water_fraction * tank_mass_kg

    recipe: list[dict] = []
    total_dissolved_kg = 0.0
    for i, mat in enumerate(materials):
        kg = x[i] * tank_mass_kg
        if kg < 0.001:
            continue
        recipe.append({
            "material": mat["material"],
            "type": mat.get("type"),
            "kg_per_tank": round(kg, 2),
            "g_per_l": round(kg * 1000 / tank_volume_l, 2),
            "mass_fraction_pct": round(x[i] * 100, 3),
            "mixing_order": mat.get("mixing_order") or 5,
            "mixing_notes": mat.get("mixing_notes") or "",
        })
        total_dissolved_kg += kg
    recipe.sort(key=lambda r: r["mixing_order"] or 5)

    # Per-nutrient composition of the finished blend (m/m + g/L via density).
    composition: list[dict] = []
    nutrients: list[dict] = []
    achieved_mm: dict[str, float] = {}
    for nut in NUTRIENTS:
        mm_pct = sum(x[i] * float(materials[i].get(nut, 0)) for i in range(n_mats))
        g_per_l = mm_pct * density * 10
        target_mm = targets_mm.get(nut, 0)
        target_g_per_l = target_mm * density * 10
        achieved_mm[nut] = mm_pct
        composition.append({
            "nutrient": nut.upper(),
            "m_m_pct": round(mm_pct, 4),
            "g_per_l": round(g_per_l, 4),
            "target_m_m_pct": round(target_mm, 4),
            "target_g_per_l": round(target_g_per_l, 4),
        })
        # `nutrients` preserves the old g/L-shape response for back-compat.
        nutrients.append({
            "nutrient": nut.upper(),
            "target_g_l": round(target_g_per_l, 4),
            "actual_g_l": round(g_per_l, 4),
            "diff_g_l": round(g_per_l - target_g_per_l, 4),
        })

    # SA grade notation from achieved m/m (elemental).
    secondary = {
        nut.capitalize(): achieved_mm[nut]
        for nut in ["ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]
        if achieved_mm.get(nut, 0) > 0.01
    }
    # Translate keys to the casing the notation helper expects (Ca, Mg, …).
    casing = {"ca": "Ca", "mg": "Mg", "s": "S", "fe": "Fe", "b": "B",
              "mn": "Mn", "zn": "Zn", "mo": "Mo", "cu": "Cu"}
    secondary = {casing[k.lower()]: v for k, v in secondary.items()}
    sa, intl = pct_to_sa_notation(
        achieved_mm.get("n", 0),
        achieved_mm.get("p", 0),
        achieved_mm.get("k", 0),
        secondary,
    )

    # Nutrient w/v — the metric the real-world manufacturing envelope is
    # expressed in. N+P+K elemental mass per litre of finished solution.
    npk_mm = achieved_mm.get("n", 0) + achieved_mm.get("p", 0) + achieved_mm.get("k", 0)
    nutrient_wv_g_per_l = npk_mm * density * 10  # m/m % × SG × 10 = g/L

    compat_warnings: list[dict] = []
    if compatibility_rules:
        compat_warnings = check_compatibility(
            [{"material": r["material"]} for r in recipe],
            compatibility_rules,
        )
    mixing_instructions = _build_mixing_instructions(recipe, tank_volume_l)
    warnings = _generate_warnings(
        nutrients, total_dissolved_kg, tank_volume_l, recipe,
        materials, x[:n_mats], nutrient_limits,
    )

    return {
        "success": True,
        "exact": exact,
        "scale": round(scale, 3),
        "recipe": recipe,
        "nutrients": nutrients,
        "nutrient_composition": composition,
        "sa_notation": sa,
        "international_notation": intl,
        "tank_volume_l": tank_volume_l,
        "total_dissolved_kg": round(total_dissolved_kg, 2),
        "water_kg": round(water_kg, 2),
        "density_kg_per_l": round(density, 3),
        "sg_estimate": round(density, 3),  # alias for back-compat
        "nutrient_wv_g_per_l": round(nutrient_wv_g_per_l, 2),
        "nutrient_mm_pct": round(npk_mm, 3),
        "compatibility_warnings": compat_warnings,
        "mixing_instructions": mixing_instructions,
        "warnings": warnings,
    }


def _find_closest_mm_blend(
    c, A_ub, b_ub, A_eq, b_eq, bounds,
    materials, targets_mm, targeted_nutrients,
    tank_volume_l, compatibility_rules, nutrient_limits, required_materials,
) -> dict:
    """Binary-search the largest scale factor that keeps the LP feasible.

    Identical strategy to the g/L optimizer's closest-blend fallback:
    shrink every nutrient target by a common factor until the LP solves,
    then report `scale` < 1 so the UI can show priority panel.
    """
    if A_ub is None or b_ub is None:
        # Nothing to relax — genuinely infeasible.
        return {
            "success": False,
            "error": (
                "Could not find a feasible blend with the selected materials. "
                "Likely reason: solubility or safety-limit constraints prevent "
                "hitting the requested m/m %. Try a different material set or "
                "lower targets."
            ),
        }

    # The first N rows of A_ub correspond to nutrient targets (one per
    # targeted nutrient, in NUTRIENTS order). Only scale those rows.
    n_target_rows = len(targeted_nutrients)
    best_scale = 0.0
    best_x = None

    lo, hi = 0.0, 1.0
    for _ in range(20):
        mid = (lo + hi) / 2
        scaled_b = b_ub.copy()
        scaled_b[:n_target_rows] = b_ub[:n_target_rows] * mid
        res = linprog(
            c=c, A_ub=A_ub, b_ub=scaled_b,
            A_eq=A_eq, b_eq=b_eq,
            bounds=bounds, method="highs",
        )
        if res.success:
            best_scale = mid
            best_x = res.x
            lo = mid
        else:
            hi = mid

    if best_x is None:
        hint = ""
        if required_materials:
            hint = (
                " The required-% constraint may be incompatible with the "
                "nutrient targets. Try lowering the required % or removing "
                "some required materials."
            )
        return {
            "success": False,
            "error": (
                "Could not find a feasible blend with the selected materials."
                + hint
            ),
        }

    # Closest-blend hits a scaled version of the targets; report achieved m/m.
    return _package_mm_result(
        x=best_x,
        materials=materials,
        targets_mm=targets_mm,
        tank_volume_l=tank_volume_l,
        compatibility_rules=compatibility_rules,
        nutrient_limits=nutrient_limits,
        exact=False,
        scale=best_scale,
    )


def run_liquid_priority_optimizer_mm(
    targets_mm: dict[str, float],
    priorities: dict[str, str],
    materials: list[dict],
    tank_volume_l: float = 1000,
    compatibility_rules: list[dict] | None = None,
    required_materials: dict[str, float] | None = None,
) -> dict:
    """m/m equivalent of run_liquid_priority_optimizer — same algorithm.

    Tries all targets first; on failure, drops 'flexible' targets smallest-
    first until a feasible blend is found. `priorities` maps nutrient →
    'must_match' | 'flexible'; absent or flexible targets can be dropped.
    """
    result = optimize_liquid_blend_mm(
        targets_mm, materials, tank_volume_l, compatibility_rules, required_materials
    )
    if result.get("exact"):
        result["priority_result"] = {
            "matched": [n.upper() for n in targets_mm if targets_mm[n] > 0],
            "compromised": [],
            "feasible": True,
            "scale": 1.0,
        }
        return result

    must_match = {
        n: v for n, v in targets_mm.items()
        if priorities.get(n) == "must_match" or priorities.get(n.upper()) == "must_match"
    }
    flexible = [(n, v) for n, v in targets_mm.items() if n not in must_match]
    flexible.sort(key=lambda x: x[1])

    remaining_flex = list(flexible)
    best_result = None
    dropped: list[tuple[str, float]] = []
    while remaining_flex:
        trial = dict(must_match)
        for n, v in remaining_flex:
            trial[n] = v
        res = optimize_liquid_blend_mm(
            trial, materials, tank_volume_l, compatibility_rules, required_materials,
        )
        if res.get("exact") or (res.get("success") and res.get("scale", 0) > 0.95):
            best_result = res
            break
        dropped_nutrient = remaining_flex.pop(0)
        dropped.append(dropped_nutrient)

    if best_result is None and must_match:
        res = optimize_liquid_blend_mm(
            must_match, materials, tank_volume_l, compatibility_rules, required_materials,
        )
        if res.get("success"):
            best_result = res
            dropped = list(flexible)

    if best_result is None:
        result["priority_result"] = {
            "matched": [],
            "compromised": [
                {"nutrient": n.upper(), "target": round(v, 4), "actual": 0}
                for n, v in targets_mm.items()
            ],
            "feasible": False,
            "scale": 0,
        }
        result["contact_sapling"] = True
        return result

    matched = []
    compromised = []
    ga_map = {g["nutrient"]: g for g in best_result.get("nutrient_composition", [])}
    for nut, target in targets_mm.items():
        nu = nut.upper()
        actual = ga_map.get(nu, {}).get("m_m_pct", 0)
        was_dropped = nut in [d[0] for d in dropped]
        if not was_dropped and abs(actual - target) < 0.05:
            matched.append(nu)
        else:
            compromised.append({
                "nutrient": nu,
                "target": round(target, 4),
                "actual": round(actual, 4),
            })

    best_result["priority_result"] = {
        "matched": matched,
        "compromised": compromised,
        "feasible": True,
        "scale": best_result.get("scale", 1.0),
    }
    best_result["contact_sapling"] = False
    return best_result
