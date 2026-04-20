"""Tests for the mass-fraction liquid optimizer (optimize_liquid_blend_mm).

These tests lock in the contract of the m/m optimizer — targets are expressed
as mass-fraction percentages and density falls out of the recipe as an output.
The LP is tested against straightforward NPK sets; failure-mode branches
(missing source, over-constrained required-%, infeasible targets) are
exercised directly.
"""

from __future__ import annotations

import os
import sys

import pytest

# Make `app` importable when running pytest from sapling-api/
_HERE = os.path.dirname(os.path.abspath(__file__))
_API_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _API_ROOT not in sys.path:
    sys.path.insert(0, _API_ROOT)

from app.services.liquid_optimizer import (  # noqa: E402
    _compute_sg_from_fractions,
    optimize_liquid_blend_mm,
    run_liquid_priority_optimizer_mm,
)


# ── Material builders ──────────────────────────────────────────────────────
# Simplified NPK sources with realistic percentages, high solubility, and
# known density. Keeping these small and explicit keeps failures readable.

def _urea(**overrides):
    base = {
        "material": "Urea",
        "type": "straight",
        "form": "liquid",
        "n": 46.0, "p": 0, "k": 0,
        "ca": 0, "mg": 0, "s": 0,
        "fe": 0, "b": 0, "mn": 0, "zn": 0, "mo": 0, "cu": 0,
        "solubility_20c": 1000.0,  # g/L — urea is extremely soluble
        "sg": 1.33,
        "mixing_order": 3,
    }
    base.update(overrides)
    return base


def _map(**overrides):
    # Mono-ammonium phosphate: ~12% N, ~22% P (elemental).
    # Test uses a pure-P source for clarity — zero out N to keep the math
    # on any single test isolated.
    base = {
        "material": "MAP",
        "type": "straight",
        "form": "liquid",
        "n": 0, "p": 22.0, "k": 0,
        "ca": 0, "mg": 0, "s": 0,
        "fe": 0, "b": 0, "mn": 0, "zn": 0, "mo": 0, "cu": 0,
        "solubility_20c": 400.0,
        "sg": 1.58,
        "mixing_order": 4,
    }
    base.update(overrides)
    return base


def _kcl(**overrides):
    # KCl: ~50% K (elemental ≈ 60% K2O × 0.83).
    base = {
        "material": "KCL",
        "type": "straight",
        "form": "liquid",
        "n": 0, "p": 0, "k": 50.0,
        "ca": 0, "mg": 0, "s": 0,
        "fe": 0, "b": 0, "mn": 0, "zn": 0, "mo": 0, "cu": 0,
        "solubility_20c": 340.0,
        "sg": 1.98,
        "mixing_order": 5,
    }
    base.update(overrides)
    return base


def _zinc_sulfate(**overrides):
    base = {
        "material": "ZincSulfate",
        "type": "micro",
        "form": "liquid",
        "n": 0, "p": 0, "k": 0,
        "ca": 0, "mg": 0, "s": 17.8,
        "fe": 0, "b": 0, "mn": 0, "zn": 22.7, "mo": 0, "cu": 0,
        "solubility_20c": 540.0,
        "sg": 1.96,
        "mixing_order": 7,
    }
    base.update(overrides)
    return base


def _basic_npk_materials():
    return [_urea(), _map(), _kcl()]


# ── Tests ───────────────────────────────────────────────────────────────────

def test_basic_npk_target_is_hit():
    """Simple NPK target should be achievable exactly."""
    materials = _basic_npk_materials()
    targets = {"n": 5.0, "p": 2.0, "k": 5.0}

    result = optimize_liquid_blend_mm(targets, materials, tank_volume_l=1000)

    assert result["success"] is True, result.get("error")
    assert result["exact"] is True

    ga = {g["nutrient"]: g for g in result["nutrient_composition"]}
    for nut in ("N", "P", "K"):
        target = targets[nut.lower()]
        assert ga[nut]["m_m_pct"] >= target - 0.01, (
            f"{nut}: achieved {ga[nut]['m_m_pct']} < target {target}"
        )


def test_density_falls_between_water_and_salt():
    """Density should lie between water (1.0) and a hard salt ceiling (1.8)."""
    materials = _basic_npk_materials()
    targets = {"n": 2.0, "p": 1.0, "k": 2.0}

    result = optimize_liquid_blend_mm(targets, materials, tank_volume_l=1000)

    assert result["success"] is True, result.get("error")
    density = result["density_kg_per_l"]
    assert 1.0 <= density <= 1.8, f"density={density} outside [1.0, 1.8]"


def test_sa_notation_is_produced():
    """A 5:1:5(20) m/m target should round-trip to its SA notation."""
    materials = _basic_npk_materials()
    # 5:1:5 (20) elemental → N 9.09%, P 1.82%, K 9.09%
    targets = {"n": 9.09, "p": 1.82, "k": 9.09}

    result = optimize_liquid_blend_mm(targets, materials, tank_volume_l=1000)

    assert result["success"] is True, result.get("error")
    assert "5:1:5" in result["sa_notation"], (
        f"Expected 5:1:5 in sa_notation, got {result['sa_notation']!r}"
    )
    assert result["international_notation"].startswith("N "), (
        f"Expected int'l notation to start with 'N ', got "
        f"{result['international_notation']!r}"
    )


def test_no_source_for_nutrient_returns_missing_sources():
    """Asking for P with only N materials should fail with missing_sources."""
    materials = [_urea()]  # N only, no P source
    targets = {"n": 5.0, "p": 2.0}

    result = optimize_liquid_blend_mm(targets, materials, tank_volume_l=1000)

    assert result["success"] is False
    assert "No source" in result["error"]
    assert "missing_sources" in result
    assert "P" in result["missing_sources"]


def test_required_material_is_exact_fraction():
    """required_materials should pin a material to its exact mass fraction."""
    materials = _basic_npk_materials()
    targets = {"n": 2.0, "p": 1.0, "k": 2.0}
    required = {"Urea": 30.0}

    result = optimize_liquid_blend_mm(
        targets, materials, tank_volume_l=1000, required_materials=required
    )

    assert result["success"] is True, result.get("error")
    urea_row = next(
        (r for r in result["recipe"] if r["material"] == "Urea"), None
    )
    assert urea_row is not None, "Urea missing from recipe"
    assert abs(urea_row["mass_fraction_pct"] - 30.0) < 0.5, (
        f"Urea mass_fraction_pct={urea_row['mass_fraction_pct']} not ~30.0"
    )


def test_required_materials_sum_over_100_rejected():
    """Sum of required fractions > 100% must be rejected."""
    materials = _basic_npk_materials()
    targets = {"n": 2.0, "p": 1.0, "k": 2.0}
    required = {"Urea": 60.0, "MAP": 60.0}

    result = optimize_liquid_blend_mm(
        targets, materials, tank_volume_l=1000, required_materials=required
    )

    assert result["success"] is False
    error = result["error"].lower()
    assert "100%" in result["error"] or "cannot exceed" in error, (
        f"Expected '100%' or 'cannot exceed' in error, got: {result['error']!r}"
    )


def test_infeasible_targets_return_closest():
    """Impossibly high m/m should either fail or return closest (scale<1)."""
    materials = _basic_npk_materials()
    # 50% m/m N is higher than any practical liquid fertilizer.
    targets = {"n": 50.0}

    result = optimize_liquid_blend_mm(targets, materials, tank_volume_l=1000)

    if result.get("success"):
        # Closest-blend path: exact must be False and scale must be < 1.
        assert result["exact"] is False, (
            "Expected exact=False for infeasible target, got exact=True"
        )
        assert result["scale"] < 1.0, (
            f"Expected scale<1 for infeasible, got {result['scale']}"
        )
    else:
        assert "error" in result


def test_water_kg_plus_dissolved_equals_tank_mass():
    """total_dissolved_kg + water_kg ≈ tank_volume_l × density."""
    materials = _basic_npk_materials()
    targets = {"n": 2.0, "p": 1.0, "k": 2.0}

    result = optimize_liquid_blend_mm(targets, materials, tank_volume_l=1000)

    assert result["success"] is True, result.get("error")
    tank_mass = result["tank_volume_l"] * result["density_kg_per_l"]
    total = result["total_dissolved_kg"] + result["water_kg"]
    assert abs(total - tank_mass) < 0.5, (
        f"dissolved+water={total} vs tank_mass={tank_mass} "
        f"(diff {abs(total - tank_mass):.3f} kg)"
    )


def test_priority_optimizer_matches_must_match():
    """When not all targets are feasible, must_match targets must be hit."""
    # Give a Zn source that can supply some Zn, but asking for 10% m/m Zn
    # is unrealistic — the priority optimizer should drop or compromise Zn
    # while keeping N and P satisfied (both easy to hit).
    materials = [_urea(), _map(), _zinc_sulfate()]
    targets = {"n": 5.0, "p": 2.0, "zn": 10.0}
    priorities = {"n": "must_match", "p": "must_match", "zn": "flexible"}

    result = run_liquid_priority_optimizer_mm(
        targets, priorities, materials, tank_volume_l=1000,
    )

    assert result.get("success"), result.get("error")
    assert "priority_result" in result
    pr = result["priority_result"]
    matched = pr.get("matched", [])
    compromised_nuts = {c["nutrient"] for c in pr.get("compromised", [])}

    assert "N" in matched, f"N should be matched, got matched={matched}"
    assert "P" in matched, f"P should be matched, got matched={matched}"
    # Zn is either in compromised (still in result) or dropped (not in matched).
    assert "ZN" not in matched, (
        f"ZN should not be fully matched; got matched={matched}"
    )
    # Either ZN appears in compromised list or it was dropped entirely.
    if "ZN" not in compromised_nuts:
        # Dropped — the priority run's targets don't include ZN anymore,
        # so the check above ("ZN" not in matched) already covers this.
        pass


# ── Incompatibility handling (MILP path) ───────────────────────────────────


def _calcium_nitrate(**overrides):
    base = {
        "material": "Calcium Nitrate",
        "type": "straight",
        "form": "liquid",
        "n": 15.5, "p": 0, "k": 0,
        "ca": 19.0, "mg": 0, "s": 0,
        "fe": 0, "b": 0, "mn": 0, "zn": 0, "mo": 0, "cu": 0,
        "solubility_20c": 1200.0,
        "sg": 1.82,
        "mixing_order": 2,
    }
    base.update(overrides)
    return base


def _ammonium_sulfate(**overrides):
    base = {
        "material": "Ammonium Sulphate",
        "type": "straight",
        "form": "liquid",
        "n": 21.0, "p": 0, "k": 0,
        "ca": 0, "mg": 0, "s": 24.0,
        "fe": 0, "b": 0, "mn": 0, "zn": 0, "mo": 0, "cu": 0,
        "solubility_20c": 760.0,
        "sg": 1.77,
        "mixing_order": 3,
    }
    base.update(overrides)
    return base


CA_SULFATE_INCOMPAT = [{
    "material_a": "Calcium Nitrate",
    "material_b": "Ammonium Sulphate",
    "compatible": False,
    "severity": "incompatible",
    "reason": "Ca + SO4 precipitates as gypsum",
}]


def test_incompatible_pair_is_resolved_by_optimizer():
    """User's reported bug: enabling raw materials that include a Ca source
    and a sulphate source used to hard-error. The optimizer should instead
    pick a compatible subset (drop one side of the incompatible edge)."""
    materials = [_calcium_nitrate(), _ammonium_sulfate(), _map(), _kcl()]
    # N can come from either Ca(NO3)2 or (NH4)2SO4. A low-Ca target lets
    # the optimizer pick the sulphate side and avoid the incompatibility.
    targets = {"n": 4.0, "p": 2.0, "k": 4.0}

    result = optimize_liquid_blend_mm(
        targets, materials, tank_volume_l=1000,
        compatibility_rules=CA_SULFATE_INCOMPAT,
    )

    assert result["success"] is True, result.get("error")
    recipe_names = {r["material"] for r in result["recipe"]}
    # At most one of the incompatible pair ends up in the recipe
    assert not ({"Calcium Nitrate", "Ammonium Sulphate"} <= recipe_names), (
        f"both incompatible materials in recipe: {recipe_names}"
    )


def test_incompatible_but_both_required_is_hard_error():
    """If the user explicitly required both halves of an incompatible pair,
    that IS a conflict — the optimizer can't honour both without dropping
    one. Surface it as a clear error."""
    materials = [_calcium_nitrate(), _ammonium_sulfate(), _map(), _kcl()]
    targets = {"n": 4.0, "p": 1.0, "k": 2.0}

    result = optimize_liquid_blend_mm(
        targets, materials, tank_volume_l=1000,
        compatibility_rules=CA_SULFATE_INCOMPAT,
        required_materials={
            "Calcium Nitrate": 20.0,
            "Ammonium Sulphate": 10.0,
        },
    )

    assert result["success"] is False
    assert "incompatible" in result["error"].lower()
    assert "Calcium Nitrate" in result["incompatible_materials"]
    assert "Ammonium Sulphate" in result["incompatible_materials"]


def test_required_material_on_compatible_side_is_kept():
    """If only ONE side of an incompatible pair is required, the optimizer
    pins that side and excludes the incompatible partner automatically."""
    materials = [_calcium_nitrate(), _ammonium_sulfate(), _map(), _kcl()]
    targets = {"n": 4.0, "p": 2.0, "k": 4.0}

    result = optimize_liquid_blend_mm(
        targets, materials, tank_volume_l=1000,
        compatibility_rules=CA_SULFATE_INCOMPAT,
        required_materials={"Calcium Nitrate": 15.0},
    )

    assert result["success"] is True, result.get("error")
    recipe_names = {r["material"] for r in result["recipe"]}
    assert "Calcium Nitrate" in recipe_names
    assert "Ammonium Sulphate" not in recipe_names


def test_no_incompatibility_path_unchanged():
    """Regression guard: with no incompatibility rules, the fast LP path
    should be taken and produce the same result as before this change."""
    materials = _basic_npk_materials()
    targets = {"n": 5.0, "p": 2.0, "k": 5.0}

    result = optimize_liquid_blend_mm(
        targets, materials, tank_volume_l=1000,
        compatibility_rules=None,
    )

    assert result["success"] is True
    assert result["exact"] is True


# ── Sanity check on the density helper ─────────────────────────────────────

def test_compute_sg_from_fractions_water_only_is_one():
    """Pure water: SG should round to 1.0."""
    assert _compute_sg_from_fractions({}, 1.0, {}) == pytest.approx(1.0)


def test_compute_sg_from_fractions_matches_hand_calc():
    """Check helper against a hand calculation."""
    mats = {"Urea": {"sg": 1.33}}
    # 10% urea, 90% water.
    # inv_vol = 0.9/1.0 + 0.1/1.33 = 0.9 + 0.07519 = 0.97519
    # sg = 1 / 0.97519 ≈ 1.0254
    sg = _compute_sg_from_fractions({"Urea": 0.1}, 0.9, mats)
    expected = 1.0 / (0.9 + 0.1 / 1.33)
    assert sg == pytest.approx(expected, abs=1e-4)
