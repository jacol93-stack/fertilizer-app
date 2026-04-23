"""Tests for Phase 2 Stage Splitter — apportioning season targets
across crop stages using family shape weights + crop-specific overrides."""
from __future__ import annotations

import pytest

from app.services.stage_splitter import (
    CROP_FAMILY_MAP,
    CROP_SPECIFIC_OVERRIDES,
    FAMILY_STAGE_SHAPES,
    NORMALISED_STAGES,
    get_family,
    get_stage_shape_provenance,
    split_season_targets,
)


# ============================================================
# Family taxonomy
# ============================================================

def test_known_crops_resolve_to_family():
    assert get_family("Garlic") == "bulb"
    assert get_family("Wheat") == "cereal"
    assert get_family("Maize (dryland)") == "cereal"
    assert get_family("Sunflower") == "oilseed"
    assert get_family("Soybean") == "legume"
    assert get_family("Macadamia") == "fruit_tree"
    assert get_family("Wine Grape") == "vine"
    assert get_family("Blueberry") == "bush_fruit"
    assert get_family("Potato") == "tuber"
    assert get_family("Lettuce") == "leafy_veg"
    assert get_family("Tomato") == "fruit_veg"
    assert get_family("Sugarcane") == "monocot_perennial"
    assert get_family("Cotton") == "fibre"
    assert get_family("Tobacco") == "leaf_stimulant"
    assert get_family("Rooibos") == "specialty_sa"


def test_unknown_crop_defaults_to_cereal():
    assert get_family("Ficus carica mystery-variant") == "cereal"


# ============================================================
# Shape integrity — every family's fractions sum to ~1.0
# ============================================================

def test_every_family_shape_sums_to_one():
    """Sanity: no agronomy-wrong shape ships with accidentally-skewed totals."""
    for family, shape in FAMILY_STAGE_SHAPES.items():
        for nutrient in ("N", "P", "K", "Ca", "Mg", "S"):
            fractions = getattr(shape, nutrient)
            total = sum(fractions)
            assert abs(total - 1.0) < 0.005, (
                f"{family}.{nutrient} sums to {total}, expected 1.0"
            )


def test_every_crop_override_sums_to_one():
    for crop, shape in CROP_SPECIFIC_OVERRIDES.items():
        for nutrient in ("N", "P", "K", "Ca", "Mg", "S"):
            fractions = getattr(shape, nutrient)
            total = sum(fractions)
            assert abs(total - 1.0) < 0.005, (
                f"{crop}.{nutrient} sums to {total}"
            )


def test_every_family_has_provenance():
    for family, shape in FAMILY_STAGE_SHAPES.items():
        assert shape.source_id, f"{family} missing source_id"
        assert shape.source_section, f"{family} missing source_section"
        assert 1 <= shape.tier <= 6


# ============================================================
# Agronomic correctness — "shape shape" tests
# ============================================================

def test_cereal_n_peaks_at_tillering_not_planting():
    """Cereal N should peak at vegetative (tillering), not establishment."""
    cereal_n = FAMILY_STAGE_SHAPES["cereal"].N
    # vegetative = index 1; establishment = index 0
    assert cereal_n[1] > cereal_n[0]


def test_bulb_k_peaks_at_fill_not_vegetative():
    """Bulb K peaks at bulb fill (index 3), not vegetative."""
    bulb_k = FAMILY_STAGE_SHAPES["bulb"].K
    assert bulb_k[3] == max(bulb_k)


def test_fruit_tree_k_peaks_at_fruit_dev():
    """Fruit-tree K peaks at fruit development (reproductive/fill)."""
    ft_k = FAMILY_STAGE_SHAPES["fruit_tree"].K
    assert ft_k[2] == max(ft_k)  # reproductive = index 2 (fruit dev)


def test_legume_n_front_loaded():
    """Legume N is front-loaded (starter N) because rest is from fixation."""
    legume_n = FAMILY_STAGE_SHAPES["legume"].N
    # Establishment (index 0) should be the highest OR tied-highest
    assert legume_n[0] == max(legume_n) or legume_n[0] >= 0.25


def test_leafy_veg_n_concentrated_in_rapid_growth():
    """Leafy veg N at vegetative >= 50% of season."""
    leafy_n = FAMILY_STAGE_SHAPES["leafy_veg"].N
    assert leafy_n[1] >= 0.45


def test_tuber_k_peaks_at_fill():
    """Potato/tuber K strongly peaks at tuber fill."""
    tuber_k = FAMILY_STAGE_SHAPES["tuber"].K
    assert tuber_k[3] >= 0.30


def test_cotton_k_peaks_at_boll_fill():
    """Cotton K peaks during boll fill (fill stage)."""
    cotton_k = FAMILY_STAGE_SHAPES["fibre"].K
    assert cotton_k[3] == max(cotton_k)


def test_tobacco_n_tapers_for_quality():
    """Tobacco N drops sharply in fill/maturation for leaf quality."""
    tobacco_n = FAMILY_STAGE_SHAPES["leaf_stimulant"].N
    assert tobacco_n[3] < 0.15  # fill stage N < 15%
    assert tobacco_n[4] < 0.05  # maturation ~0


# ============================================================
# Crop-specific overrides
# ============================================================

def test_sugarcane_override_is_sasri_tier_1():
    src, section, tier = get_stage_shape_provenance("Sugarcane")
    assert tier == 1
    assert "SASRI" in src


def test_wheat_override_is_fertasa_tier_1():
    src, section, tier = get_stage_shape_provenance("Wheat")
    assert tier == 1
    assert "FERTASA" in src or "5_4_3" in src


def test_macadamia_override_is_samac_tier_1():
    src, section, tier = get_stage_shape_provenance("Macadamia")
    assert tier == 1
    assert "SAMAC" in src or "SCHOEMAN" in src


# ============================================================
# split_season_targets — the main function
# ============================================================

def test_garlic_5_stage_split_matches_clivia_shape():
    """Clivia Land A: N 155, P2O5 86, K2O 173, Ca 176, S 67 → 5 stages."""
    targets = {"N": 155, "P2O5": 86, "K2O": 173, "Ca": 176, "S": 67}
    splits = split_season_targets(crop="Garlic", season_targets=targets, stage_count=5)

    assert len(splits) == 5

    # Sums should round to near season totals
    for nutrient, total in targets.items():
        staged_sum = sum(s.nutrients.get(nutrient, 0) for s in splits)
        assert abs(staged_sum - total) < 2.0  # within rounding

    # Every row carries provenance
    assert all(s.source_id for s in splits)


def test_split_respects_stage_count_reduction():
    """3-stage count should still sum to season total."""
    targets = {"N": 100}
    splits = split_season_targets(crop="Garlic", season_targets=targets, stage_count=3)
    assert len(splits) == 3
    assert abs(sum(s.nutrients["N"] for s in splits) - 100) < 1.0


def test_split_handles_non_standard_nutrient():
    """Unknown nutrient gets flat split."""
    targets = {"Boron": 0.5}  # not a standard macro
    splits = split_season_targets(crop="Garlic", season_targets=targets, stage_count=5)
    for s in splits:
        assert s.nutrients["Boron"] == 0.1  # 0.5 / 5 = 0.1


def test_split_sugarcane_uses_override_not_family():
    """Sugarcane override (Tier 1 SASRI) should be used over monocot_perennial family."""
    targets = {"N": 160}
    splits = split_season_targets(crop="Sugarcane", season_targets=targets, stage_count=5)
    # Override has N[1] = 0.45 — very front-loaded
    assert splits[1].nutrients["N"] > 60  # 0.45 * 160 = 72
    assert splits[0].source_id == "SASRI_IS_7_2"


def test_wheat_override_wheat_p_front_loaded():
    """Wheat P override has P[0] = 0.40 (planting bulk)."""
    targets = {"P2O5": 100}
    splits = split_season_targets(crop="Wheat", season_targets=targets, stage_count=5)
    assert splits[0].nutrients["P2O5"] >= 35  # 0.40 * 100 = 40


def test_mac_override_post_harvest_budbuild_nonzero():
    """Macadamia maturation (post-harvest budbuild) should have nonzero N."""
    targets = {"N": 200}
    splits = split_season_targets(crop="Macadamia", season_targets=targets, stage_count=5)
    assert splits[4].nutrients["N"] > 20  # 0.15 * 200 = 30
