"""Tests for Phase 2 module 10: target computation with provenance.

Wraps calculate_nutrient_targets with typed provenance output + P↔P2O5
and K↔K2O conversions + harvested-removal subtraction.
"""
from __future__ import annotations

import pytest

from app.models import Tier
from app.services.target_computation import (
    K_TO_K2O,
    P_TO_P2O5,
    SoilCatalog,
    TargetComputationResult,
    _compute_removal_subtraction,
    _infer_harvest_mode,
    compute_season_targets,
)


# ============================================================
# Fixtures — minimal catalog for Maize + Wheat
# ============================================================

CROP_ROWS = [
    {"crop": "Maize (dryland)", "type": "Annual", "crop_type": "annual",
     "yield_unit": "t grain/ha", "default_yield": 5.0,
     "n": 25.0, "p": 4.5, "k": 20.0, "ca": 1.0, "mg": 2.0, "s": 1.5,
     "fe": 0.1, "b": 0.05, "mn": 0.1, "zn": 0.05, "mo": 0.01, "cu": 0.03,
     "pop_per_ha": 60000},
    {"crop": "Wheat", "type": "Annual", "crop_type": "annual",
     "yield_unit": "t grain/ha", "default_yield": 5.0,
     "n": 22.5, "p": 3.8, "k": 4.3, "ca": 0.5, "mg": 1.0, "s": 2.5,
     "fe": 0.1, "b": 0.03, "mn": 0.05, "zn": 0.05, "mo": 0.01, "cu": 0.02,
     "pop_per_ha": 3000000},
]

SUFFICIENCY_ROWS = [
    {"parameter": "pH (H2O)", "very_low_max": 4.5, "low_max": 5.5, "optimal_max": 7.0, "high_max": 8.0},
    {"parameter": "P (Bray-1)", "very_low_max": 10, "low_max": 20, "optimal_max": 40, "high_max": 60},
    {"parameter": "K", "very_low_max": 50, "low_max": 100, "optimal_max": 200, "high_max": 350},
    {"parameter": "Ca", "very_low_max": 200, "low_max": 400, "optimal_max": 1000, "high_max": 2000},
    {"parameter": "Mg", "very_low_max": 40, "low_max": 80, "optimal_max": 200, "high_max": 400},
    {"parameter": "S", "very_low_max": 5, "low_max": 10, "optimal_max": 20, "high_max": 40},
    {"parameter": "N (total)", "very_low_max": 10, "low_max": 20, "optimal_max": 40, "high_max": 60},
]

ADJUSTMENT_ROWS = [
    {"classification": "Very Low",  "factor": 1.5,  "nutrient_group": None,
     "source": "Implementer convention", "source_section": "5.1", "tier": 6},
    {"classification": "Low",       "factor": 1.25, "nutrient_group": None,
     "source": "Implementer convention", "source_section": "5.1", "tier": 6},
    {"classification": "Optimal",   "factor": 1.0,  "nutrient_group": None,
     "source": "Implementer convention", "source_section": "5.1", "tier": 6},
    {"classification": "High",      "factor": 0.5,  "nutrient_group": None,
     "source": "Implementer convention", "source_section": "5.1", "tier": 6},
    {"classification": "Very High", "factor": 0.0,  "nutrient_group": None,
     "source": "Implementer convention", "source_section": "5.1", "tier": 6},
]

PARAM_MAP_ROWS = [
    {"crop_nutrient": "N", "soil_parameter": "N (total)"},
    {"crop_nutrient": "P", "soil_parameter": "P (Bray-1)"},
    {"crop_nutrient": "K", "soil_parameter": "K"},
    {"crop_nutrient": "Ca", "soil_parameter": "Ca"},
    {"crop_nutrient": "Mg", "soil_parameter": "Mg"},
    {"crop_nutrient": "S", "soil_parameter": "S"},
]


@pytest.fixture
def minimal_catalog():
    return SoilCatalog(
        crop_rows=CROP_ROWS,
        sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS,
        param_map_rows=PARAM_MAP_ROWS,
    )


# ============================================================
# Basic smoke
# ============================================================

def test_returns_target_computation_result(minimal_catalog):
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150,
            "Ca": 1000, "Mg": 150, "S": 15, "N (total)": 30}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    assert isinstance(result, TargetComputationResult)
    assert result.targets
    assert result.sources
    assert result.calc_path_by_nutrient


def test_macros_and_secondaries_by_default_excludes_micros(minimal_catalog):
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000, "Mg": 150, "S": 15}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    # N, P2O5, K2O, Ca, Mg, S present — no Fe/B/Mn/Zn/Mo/Cu
    for nut in ("N", "P2O5", "K2O", "Ca", "Mg", "S"):
        assert nut in result.targets
    for micro in ("Fe", "B", "Mn", "Zn", "Mo", "Cu"):
        assert micro not in result.targets


def test_include_micros_returns_them(minimal_catalog):
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000,
            "Mg": 150, "S": 15, "B": 0.5, "Zn": 1.5, "Mn": 15, "Fe": 30}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=minimal_catalog,
        include_micros=True,
    )
    # At least some micros present
    assert "Zn" in result.targets or "B" in result.targets


# ============================================================
# Oxide conversion
# ============================================================

def test_p_converted_to_p2o5():
    """crop_requirements P=4.5 → yield 5 → base 22.5 kg P; P2O5 = 22.5 × 2.291."""
    catalog = SoilCatalog(
        crop_rows=CROP_ROWS, sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS, param_map_rows=PARAM_MAP_ROWS,
    )
    soil = {"P (Bray-1)": 25}  # Optimal → factor 1.0
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=catalog,
    )
    # P2O5 present, P not (converted)
    assert "P2O5" in result.targets
    assert "P" not in result.targets
    # Expected: 4.5 × 5 × 1.0 × 2.291 ≈ 51.5
    assert 50 <= result.targets["P2O5"] <= 53


def test_k_converted_to_k2o():
    catalog = SoilCatalog(
        crop_rows=CROP_ROWS, sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS, param_map_rows=PARAM_MAP_ROWS,
    )
    soil = {"K": 150}  # Optimal
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=catalog,
    )
    # K2O present, K not
    assert "K2O" in result.targets
    assert "K" not in result.targets
    # Expected: 20.0 × 5 × 1.0 × 1.205 ≈ 120.5
    assert 118 <= result.targets["K2O"] <= 123


def test_conversion_constants_accurate():
    """P_TO_P2O5 × P = P2O5. Standard oxide conversions."""
    # 1 kg P = 2.291 kg P₂O₅ (atomic: P2O5 has 2×31 P / (2×31 + 5×16) = 62/142)
    assert abs(P_TO_P2O5 - 62 / 30.974) < 0.01 or P_TO_P2O5 == 2.291
    # 1 kg K = 1.205 kg K₂O
    assert 1.20 <= K_TO_K2O <= 1.21


# ============================================================
# Provenance
# ============================================================

def test_sources_populated_per_nutrient(minimal_catalog):
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000, "Mg": 150, "S": 15}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    for nut in result.targets:
        assert nut in result.sources
        source = result.sources[nut]
        assert source.source_id
        assert source.tier is not None


def test_worst_tier_rollup_reflects_least_authoritative(minimal_catalog):
    """Heuristic path returns Tier 6 — worst_tier should be 6 in this catalog."""
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000, "Mg": 150, "S": 15}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    assert result.worst_tier == Tier.IMPLEMENTER_CONVENTION


def test_calc_path_populated(minimal_catalog):
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000, "Mg": 150, "S": 15}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    for nut in result.targets:
        assert result.calc_path_by_nutrient[nut] in (
            "rate_table", "cation_ratio", "heuristic", "unadjusted",
        )


def test_unadjusted_path_when_soil_missing(minimal_catalog):
    """Nutrients with no soil test land on the 'unadjusted' path and
    surface via unadjusted_nutrients so callers can emit warnings."""
    # N (total) absent from soil_values → N falls through to unadjusted
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150,
            "Ca": 1000, "Mg": 150, "S": 15}  # no N (total) key
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    assert "N" in result.unadjusted_nutrients
    assert result.calc_path_by_nutrient.get("N") == "unadjusted"
    assert any(a.field == "unadjusted_removal_nutrients" for a in result.assumptions)


def test_no_unadjusted_when_all_soil_present(minimal_catalog):
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150,
            "Ca": 1000, "Mg": 150, "S": 15, "N (total)": 30}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    assert result.unadjusted_nutrients == []
    assert all(p != "unadjusted" for p in result.calc_path_by_nutrient.values())


# ============================================================
# Rate-table hit path
# ============================================================

def test_rate_table_hit_overrides_heuristic(minimal_catalog):
    """A rate-table hit should beat the removal×factor heuristic."""
    rate_rows = [
        {"crop": "Maize (dryland)", "nutrient": "N",
         "yield_min_t_ha": 4, "yield_max_t_ha": 8,
         "soil_test_method": "N (total)", "soil_test_min": 20, "soil_test_max": 40,
         "rate_min_kg_ha": 100, "rate_max_kg_ha": 120,
         "source": "ARC_GCI_MIG_2017", "source_section": "Table 2",
         "water_regime": "dryland"},
    ]
    catalog = SoilCatalog(
        crop_rows=CROP_ROWS, sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS, param_map_rows=PARAM_MAP_ROWS,
        rate_table_rows=rate_rows,
    )
    soil = {"N (total)": 30}  # in the 20-40 band
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values=soil, catalog=catalog,
        rate_table_context={"water_regime": "dryland"},
    )
    # Rate-table midpoint = (100 + 120) / 2 = 110
    assert 108 <= result.targets["N"] <= 112
    assert result.calc_path_by_nutrient["N"] == "rate_table"


# ============================================================
# Harvested-removal subtraction
# ============================================================

def test_harvested_removal_subtracts_from_targets():
    """When subtract_harvested_removal=True, totals reflect off-farm export."""
    removal_rows = [
        {"crop": "Maize (dryland)", "plant_part": "total",
         "yield_unit": "kg/t grain",
         "n": 18.0, "p": 3.0, "k": 5.0, "ca": 0.5, "mg": 1.5, "s": 1.5},
    ]
    catalog = SoilCatalog(
        crop_rows=CROP_ROWS, sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS, param_map_rows=PARAM_MAP_ROWS,
        removal_rows=removal_rows,
    )
    soil = {"P (Bray-1)": 25, "K": 150}

    no_removal = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0,
        soil_values=soil, catalog=catalog,
        subtract_harvested_removal=False,
    )
    with_removal = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0,
        soil_values=soil, catalog=catalog,
        subtract_harvested_removal=True,
        expected_yield_harvested=8.0,
    )

    # N should be lower after removal subtraction
    assert with_removal.targets["N"] < no_removal.targets["N"]
    # Assumption added
    assert any(a.field == "harvested_removal" for a in with_removal.assumptions)


def test_removal_without_expected_yield_noop():
    """If subtract flag but no yield → no-op, no error."""
    removal_rows = [
        {"crop": "Maize (dryland)", "plant_part": "total",
         "yield_unit": "kg/t grain",
         "n": 18.0, "p": 3.0, "k": 5.0},
    ]
    catalog = SoilCatalog(
        crop_rows=CROP_ROWS, sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS, param_map_rows=PARAM_MAP_ROWS,
        removal_rows=removal_rows,
    )
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=5.0,
        soil_values={}, catalog=catalog,
        subtract_harvested_removal=True,
        # intentionally omit expected_yield_harvested
    )
    # Should not error; no removal assumption added
    assert not any(a.field == "harvested_removal" for a in result.assumptions)


# ============================================================
# Perennial density scaling (pop/ha)
# ============================================================

MAC_CROP_ROW = {
    "crop": "Macadamia", "type": "Perennial", "crop_type": "perennial",
    "yield_unit": "t NIS/ha", "default_yield": 4.0,
    "n": 20.0, "p": 2.5, "k": 15.0, "ca": 3.0, "mg": 1.5, "s": 1.0,
    "fe": 0.1, "b": 0.05, "mn": 0.1, "zn": 0.05, "mo": 0.01, "cu": 0.03,
    "pop_per_ha": 300,  # SAMAC reference
}


def _mac_catalog():
    return SoilCatalog(
        crop_rows=[MAC_CROP_ROW],
        sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS,
        param_map_rows=PARAM_MAP_ROWS,
    )


def test_perennial_higher_density_scales_targets_up():
    """Mac orchard at 600 trees/ha (2× reference) → ~2× the per-ha target."""
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150,
            "Ca": 1000, "Mg": 150, "S": 15, "N (total)": 30}
    catalog = _mac_catalog()
    base = compute_season_targets(
        crop="Macadamia", yield_target=5.0, soil_values=soil, catalog=catalog,
    )
    scaled = compute_season_targets(
        crop="Macadamia", yield_target=5.0, soil_values=soil, catalog=catalog,
        block_pop_per_ha=600,
    )
    for nut in ("N", "P2O5", "K2O"):
        if nut in base.targets and base.targets[nut] > 0:
            ratio = scaled.targets[nut] / base.targets[nut]
            assert 1.95 <= ratio <= 2.05, f"{nut} expected ~2x, got {ratio}"


def test_perennial_lower_density_scales_targets_down():
    """Mac orchard at 150 trees/ha (0.5× reference) → ~half the target."""
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150,
            "Ca": 1000, "Mg": 150, "S": 15, "N (total)": 30}
    catalog = _mac_catalog()
    base = compute_season_targets(
        crop="Macadamia", yield_target=5.0, soil_values=soil, catalog=catalog,
    )
    scaled = compute_season_targets(
        crop="Macadamia", yield_target=5.0, soil_values=soil, catalog=catalog,
        block_pop_per_ha=150,
    )
    for nut in ("N", "P2O5", "K2O"):
        if nut in base.targets and base.targets[nut] > 0:
            ratio = scaled.targets[nut] / base.targets[nut]
            assert 0.48 <= ratio <= 0.52, f"{nut} expected ~0.5x, got {ratio}"


def test_perennial_scaling_adds_assumption():
    """The scale factor + reference density must be surfaced for audit."""
    result = compute_season_targets(
        crop="Macadamia", yield_target=5.0,
        soil_values={"N (total)": 30}, catalog=_mac_catalog(),
        block_pop_per_ha=450,
    )
    dens = next((a for a in result.assumptions if a.field == "perennial_density_scale"), None)
    assert dens is not None
    assert "1.5" in dens.assumed_value  # 450 / 300
    assert "450" in dens.assumed_value
    assert "300" in dens.assumed_value


def test_annual_pop_per_ha_ignored():
    """Annual crops already capture stand density in yield target;
    pop_per_ha must NOT rescale their kg/ha."""
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150,
            "Ca": 1000, "Mg": 150, "S": 15, "N (total)": 30}
    catalog = SoilCatalog(
        crop_rows=CROP_ROWS, sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS, param_map_rows=PARAM_MAP_ROWS,
    )
    base = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0, soil_values=soil, catalog=catalog,
    )
    with_pop = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0, soil_values=soil, catalog=catalog,
        block_pop_per_ha=90000,  # 50% more than the 60000 reference
    )
    # Targets unchanged — annuals don't scale
    for nut in base.targets:
        assert base.targets[nut] == with_pop.targets[nut], f"{nut} scaled for annual"
    assert not any(a.field == "perennial_density_scale" for a in with_pop.assumptions)


def test_perennial_no_reference_density_no_scaling():
    """If crop_requirements has no pop_per_ha reference, no scaling applied
    (and no assumption surfaced — we don't guess)."""
    row = dict(MAC_CROP_ROW)
    row["pop_per_ha"] = None
    catalog = SoilCatalog(
        crop_rows=[row], sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS, param_map_rows=PARAM_MAP_ROWS,
    )
    result = compute_season_targets(
        crop="Macadamia", yield_target=5.0,
        soil_values={"N (total)": 30}, catalog=catalog,
        block_pop_per_ha=600,
    )
    assert not any(a.field == "perennial_density_scale" for a in result.assumptions)


# ============================================================
# Unknown crop graceful handling
# ============================================================

def test_unknown_crop_returns_empty_targets(minimal_catalog):
    """calculate_nutrient_targets returns [] for unknown crops → we pass through."""
    result = compute_season_targets(
        crop="UnobtainiumPlant",
        yield_target=5.0,
        soil_values={}, catalog=minimal_catalog,
    )
    assert result.targets == {}


# ============================================================
# Harvest mode parametrisation (grain / hay / silage / fruit)
# ============================================================

# Barley-like removal fixture with grain, straw, total rows — mirrors
# the post-migration-078 DB shape.
BARLEY_REMOVAL_ROWS = [
    {"crop": "Barley", "plant_part": "grain", "yield_unit": "kg/t grain",
     "n": 22.0, "p": 3.5, "k": 5.0, "ca": 0.5, "mg": 1.2, "s": 2.0},
    {"crop": "Barley", "plant_part": "straw", "yield_unit": "kg/t grain",
     "n": 7.0, "p": 1.0, "k": 16.0, "ca": 3.5, "mg": 1.3, "s": 1.8},
    {"crop": "Barley", "plant_part": "total", "yield_unit": "kg/t grain",
     "n": 29.0, "p": 4.5, "k": 21.0, "ca": 4.0, "mg": 2.5, "s": 3.8},
]

# Crop row needed so harvest_mode inference from yield_unit works.
BARLEY_CROP_ROW = {
    "crop": "Barley", "type": "Annual", "crop_type": "annual",
    "yield_unit": "t grain/ha", "default_yield": 4.0,
    "n": 22.0, "p": 3.5, "k": 5.0, "ca": 2.5, "mg": 2.0, "s": 2.0,
    "fe": 0.1, "b": 0.02, "mn": 0.04, "zn": 0.04, "mo": 0.004, "cu": 0.008,
    "pop_per_ha": 2000000,
}


def test_harvest_mode_grain_picks_grain_row():
    """Grain mode pulls the grain row directly — 5 kg K/t removal."""
    removal = _compute_removal_subtraction(
        crop="Barley", yield_harvested=4.0,
        removal_rows=BARLEY_REMOVAL_ROWS, harvest_mode="grain",
    )
    # 4 t × 5.0 kg K/t × 1.205 (K→K2O) ≈ 24.1
    assert abs(removal["K2O"] - 24.1) < 0.5
    # 4 t × 22.0 kg N/t = 88
    assert abs(removal["N"] - 88.0) < 0.5


def test_harvest_mode_hay_falls_through_to_total():
    """Hay mode has no 'hay' plant_part for Barley — falls through to
    the 'total' row per preference order. Total K off-take is 21 kg/t,
    ~4× the grain mode."""
    removal = _compute_removal_subtraction(
        crop="Barley", yield_harvested=4.0,
        removal_rows=BARLEY_REMOVAL_ROWS, harvest_mode="hay",
    )
    # 4 t × 21.0 kg K/t × 1.205 ≈ 101.2
    assert abs(removal["K2O"] - 101.2) < 0.5
    # 4 t × 29.0 kg N/t = 116
    assert abs(removal["N"] - 116.0) < 0.5


def test_harvest_mode_grain_vs_hay_k_delta():
    """Anchor check: hay-mode K removal is materially larger than grain-mode.
    This is the whole point of splitting the harvest modes — cereal hay
    cuts draw soil K down ~4× faster than grain harvests."""
    grain = _compute_removal_subtraction(
        crop="Barley", yield_harvested=4.0,
        removal_rows=BARLEY_REMOVAL_ROWS, harvest_mode="grain",
    )
    hay = _compute_removal_subtraction(
        crop="Barley", yield_harvested=4.0,
        removal_rows=BARLEY_REMOVAL_ROWS, harvest_mode="hay",
    )
    assert hay["K2O"] > grain["K2O"] * 3.5


def test_harvest_mode_inferred_from_yield_unit():
    """_infer_harvest_mode maps yield_unit strings to plant_part names."""
    assert _infer_harvest_mode("t grain/ha") == "grain"
    assert _infer_harvest_mode("t hay/ha") == "hay"
    assert _infer_harvest_mode("t fruit/ha") == "fruit"
    assert _infer_harvest_mode("t NIS/ha") == "nuts"
    assert _infer_harvest_mode("t bulb/ha") == "total"
    assert _infer_harvest_mode("t tuber/ha") == "total"
    assert _infer_harvest_mode("t seed/ha") == "grain"
    assert _infer_harvest_mode("t cane/ha") == "total"
    assert _infer_harvest_mode(None) is None
    assert _infer_harvest_mode("unknown unit") is None


def test_harvest_mode_note_in_assumption():
    """The harvested_removal Assumption should note which harvest mode
    was applied — agronomist needs to see whether grain or hay math ran."""
    catalog = SoilCatalog(
        crop_rows=[BARLEY_CROP_ROW], sufficiency_rows=SUFFICIENCY_ROWS,
        adjustment_rows=ADJUSTMENT_ROWS, param_map_rows=PARAM_MAP_ROWS,
        removal_rows=BARLEY_REMOVAL_ROWS,
    )
    result = compute_season_targets(
        crop="Barley", yield_target=4.0,
        soil_values={"P (Bray-1)": 25, "K": 150}, catalog=catalog,
        subtract_harvested_removal=True,
        expected_yield_harvested=4.0,
        harvest_mode="hay",
    )
    assumption = next((a for a in result.assumptions if a.field == "harvested_removal"), None)
    assert assumption is not None
    assert "hay" in assumption.override_guidance.lower()


# ============================================================
# N-mineralisation assessment (FERTASA §5.5.2)
# ============================================================

def test_n_min_assumption_fires_on_high_oc(minimal_catalog):
    """Org C ≥ 1.5% surfaces an N-mineralisation credit range as an
    Assumption, with source cited to FERTASA §5.5.2. The range is the
    only thing emitted — we don't auto-subtract from N."""
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000,
            "Mg": 150, "S": 15, "N (total)": 30, "Org C": 2.5}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    n_min = next((a for a in result.assumptions if a.field == "n_mineralisation_credit"), None)
    assert n_min is not None
    # OC 2.5% → 1.5% above baseline → 30-45 kg N/ha (20-30 × 1.5, rounded to 5)
    assert "30-45 kg N/ha" in n_min.assumed_value
    assert n_min.source.source_id == "FERTASA_5_5_2"
    assert n_min.tier == Tier.SA_INDUSTRY_BODY


def test_n_min_assumption_silent_when_oc_below_baseline(minimal_catalog):
    """Org C < 1.5% doesn't surface a credit — typical sandy SA soils
    aren't meaningfully above the 1% baseline."""
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000,
            "Mg": 150, "S": 15, "N (total)": 30, "Org C": 1.0}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    assert not any(a.field == "n_mineralisation_credit" for a in result.assumptions)


def test_n_min_assumption_silent_when_oc_missing(minimal_catalog):
    """No OC in soil_values → no credit Assumption. Avoids noise on
    labs that don't report OM/OC."""
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000,
            "Mg": 150, "S": 15, "N (total)": 30}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    assert not any(a.field == "n_mineralisation_credit" for a in result.assumptions)


def test_n_min_falls_back_to_om_via_van_bemmelen(minimal_catalog):
    """When only OM is reported, convert via OM/1.724 (Van Bemmelen).
    OM 5.17% ≈ 3% OC → 2% above baseline → 40-60 kg N/ha credit."""
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000,
            "Mg": 150, "S": 15, "N (total)": 30, "Organic Matter": 5.17}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    n_min = next((a for a in result.assumptions if a.field == "n_mineralisation_credit"), None)
    assert n_min is not None
    assert "40-60 kg N/ha" in n_min.assumed_value


def test_n_min_caps_credit_at_4pct_oc(minimal_catalog):
    """Above 4% OC the credit is harder to predict — we cap the band at
    3% above baseline (60-90 kg N/ha) so it doesn't grow unboundedly."""
    soil = {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 150, "Ca": 1000,
            "Mg": 150, "S": 15, "N (total)": 30, "Org C": 8.0}
    result = compute_season_targets(
        crop="Maize (dryland)", yield_target=8.0,
        soil_values=soil, catalog=minimal_catalog,
    )
    n_min = next((a for a in result.assumptions if a.field == "n_mineralisation_credit"), None)
    assert n_min is not None
    assert "60-90 kg N/ha" in n_min.assumed_value
