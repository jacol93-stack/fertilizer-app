"""Tests for the FERTASA 5.2.2 base-saturation target path (migration 068).

These lock in the contract that calculate_cation_ratio_target() computes
Ca/Mg fertilizer targets from measured exchangeable-cation shortfall —
and that calculate_nutrient_targets() prefers the ratio path over the
heuristic for Ca/Mg when CEC is measured and the crop isn't flagged.

Reference math (FERTASA 5.2.2 + existing adjust_targets_for_ratios):
  shortfall_cmol = (ideal_min_sat_pct - current_sat_pct) / 100 * CEC
  delta_mg_kg    = shortfall_cmol * equivalent_weight
  full_kg_ha     = delta_mg_kg * 2000 t-soil/ha / 1e3
  per_season     = full_kg_ha / seasons_to_spread   (default 2)

Equivalent weights (mg/kg per cmol_c/kg):
  Ca = 200.4   Mg = 121.56   K = 390.98
"""
from __future__ import annotations

import pytest

from app.services.soil_engine import (
    CATION_EQUIVALENT_WEIGHT_MG_PER_CMOL,
    CATION_RATIO_MIN_CEC,
    CATION_SOIL_MASS_KG_PER_HA,
    calculate_cation_ratio_target,
    calculate_nutrient_targets,
)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def ideal_ratios_with_provenance():
    """Post-068 ideal_ratios rows with tier + provenance fields."""
    return [
        {"ratio": "Ca base sat.", "ideal_min": 60.0, "ideal_max": 70.0,
         "unit": "%", "source": "FERTASA Handbook", "source_section": "5.2.2",
         "source_year": 2019, "tier": 1, "source_note": None},
        {"ratio": "Mg base sat.", "ideal_min": 12.0, "ideal_max": 18.0,
         "unit": "%", "source": "FERTASA Handbook", "source_section": "5.2.2",
         "source_year": 2019, "tier": 1, "source_note": None},
        {"ratio": "K base sat.", "ideal_min": 3.0, "ideal_max": 5.0,
         "unit": "%", "source": "FERTASA Handbook", "source_section": "5.2.2",
         "source_year": 2019, "tier": 1, "source_note": None},
        {"ratio": "Ca:Mg", "ideal_min": 3.0, "ideal_max": 5.0, "unit": "ratio",
         "source": "FERTASA Handbook", "source_section": "5.2.2",
         "source_year": 2019, "tier": 1, "source_note": None},
    ]


@pytest.fixture
def deficient_soil():
    """A mineral soil where Ca and Mg are visibly below FERTASA targets.
    CEC = 10, Ca = 1000 mg/kg (→ 5 cmol_c/kg = 50% sat, below 60% target),
    Mg = 60 mg/kg (→ 0.49 cmol_c/kg = 4.9% sat, below 12% target)."""
    return {
        "pH (H2O)": 5.8, "P (Bray-1)": 25, "K": 120, "Ca": 1000, "Mg": 60,
        "S": 12, "N (total)": 25, "Zn": 1.5, "B": 0.8, "Mn": 18, "Fe": 15,
        "Cu": 0.8, "Mo": 0.15, "CEC": 10.0, "Na": 25,
    }


@pytest.fixture
def crop_calc_flags_rows():
    """Post-068 seeded rows — acid-loving crops flagged to skip."""
    return [
        {"crop": "Blueberry",  "skip_cation_ratio_path": True,
         "source": "MSU Extension + SA", "source_section": "Table 4",
         "source_year": 2012, "tier": 1,
         "source_note": "Blueberry prefers low Ca saturation."},
        {"crop": "Rooibos",    "skip_cation_ratio_path": True,
         "source": "SARC", "source_section": None, "source_year": 2020, "tier": 1,
         "source_note": "Native to acidic fynbos soils."},
    ]


# ── calculate_cation_ratio_target: math + edge cases ───────────────────────


class TestCationRatioMath:
    def test_ca_shortfall_produces_expected_kg_ha(
        self, ideal_ratios_with_provenance, deficient_soil,
    ):
        """Ca = 1000 mg/kg / 200.4 = 4.990 cmol_c, sat = 49.9%.
        Target 60%. Shortfall 10.1%. shortfall_cmol ≈ 1.010.
        delta_mg_kg ≈ 202.4. full_kg_ha ≈ 404.8. Per season ≈ 202.4."""
        hit = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=10.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Ca",
        )
        assert hit is not None
        assert hit["Target_kg_ha"] == pytest.approx(202.4, abs=0.5)
        assert hit["Current_Base_Sat_Pct"] == pytest.approx(49.9, abs=0.1)
        assert hit["Target_Base_Sat_Pct"] == 60.0
        assert hit["Shortfall_Pct"] == pytest.approx(10.1, abs=0.1)
        assert hit["Tier"] == 1
        assert hit["Source_Section"] == "5.2.2"
        assert hit["Seasons_To_Spread"] == 2

    def test_mg_shortfall_uses_mg_equivalent_weight(
        self, ideal_ratios_with_provenance, deficient_soil,
    ):
        """Mg = 60 mg/kg, CEC = 10 → 0.4935 cmol_c/kg = 4.9% sat.
        Target 12%. Shortfall 7.07%. shortfall_cmol = 0.707.
        delta_mg_kg = 0.707 × 121.56 = 85.96 mg/kg.
        full_kg_ha ≈ 171.9. Per season ≈ 85.96."""
        hit = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=10.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Mg",
        )
        assert hit is not None
        assert hit["Target_kg_ha"] == pytest.approx(85.9, abs=1.0)
        assert hit["Target_Base_Sat_Pct"] == 12.0

    def test_already_at_target_returns_none(
        self, ideal_ratios_with_provenance,
    ):
        """Ca = 1500 mg/kg, CEC = 10 → 7.49 cmol_c = 74.9% sat, above
        60% ideal_min. No addition needed → ratio path returns None so
        caller falls through to heuristic (which will compute zero or
        low-factor add for the already-adequate case)."""
        soil = {"Ca": 1500, "Mg": 200, "CEC": 10.0}
        hit = calculate_cation_ratio_target(
            soil_values=soil, cec=10.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Ca",
        )
        assert hit is None

    def test_low_cec_skips_ratio_path(
        self, ideal_ratios_with_provenance,
    ):
        """CEC 2 < CATION_RATIO_MIN_CEC (3) — sandy soil, math unstable,
        skip the ratio path entirely."""
        soil = {"Ca": 100, "Mg": 20, "CEC": 2.0}
        hit = calculate_cation_ratio_target(
            soil_values=soil, cec=2.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Ca",
        )
        assert hit is None

    def test_missing_cec_skips(self, ideal_ratios_with_provenance, deficient_soil):
        hit = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=None,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Ca",
        )
        assert hit is None

    def test_k_always_returns_none(self, ideal_ratios_with_provenance, deficient_soil):
        """K is handled by rate tables + heuristic — the ratio path is
        intentionally scoped to Ca/Mg. K base sat. row exists but we
        don't fire on it."""
        hit = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=10.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="K",
        )
        assert hit is None

    def test_non_cation_nutrient_returns_none(
        self, ideal_ratios_with_provenance, deficient_soil,
    ):
        for nut in ("N", "P", "S", "Zn", "B"):
            assert calculate_cation_ratio_target(
                soil_values=deficient_soil, cec=10.0,
                ratio_rows=ideal_ratios_with_provenance, nutrient=nut,
            ) is None

    def test_no_ratio_row_returns_none(self, deficient_soil):
        """Ratio table missing the Ca base sat. row — nothing to target
        against, skip the path. Caller falls through to heuristic."""
        ratios_without_ca = [
            {"ratio": "Ca:Mg", "ideal_min": 3.0, "ideal_max": 5.0, "unit": "ratio",
             "source": "FERTASA", "source_section": "5.2.2", "tier": 1},
        ]
        hit = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=10.0,
            ratio_rows=ratios_without_ca, nutrient="Ca",
        )
        assert hit is None

    def test_skip_flag_overrides_soil(
        self, ideal_ratios_with_provenance, deficient_soil, crop_calc_flags_rows,
    ):
        """Blueberry has skip_cation_ratio_path=TRUE. Even with deficient
        Ca and valid CEC, the ratio path skips → None."""
        hit = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=10.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Ca",
            crop_name="Blueberry", crop_calc_flags_rows=crop_calc_flags_rows,
        )
        assert hit is None

    def test_unflagged_crop_with_flag_rows_still_fires(
        self, ideal_ratios_with_provenance, deficient_soil, crop_calc_flags_rows,
    ):
        """Maize isn't in crop_calc_flags → ratio path fires normally."""
        hit = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=10.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Ca",
            crop_name="Maize", crop_calc_flags_rows=crop_calc_flags_rows,
        )
        assert hit is not None
        assert hit["Target_kg_ha"] > 0

    def test_spread_seasons_divides_full_correction(
        self, ideal_ratios_with_provenance, deficient_soil,
    ):
        """Default 2 seasons; setting 1 doubles the per-season value,
        setting 3 returns a third."""
        one = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=10.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Ca",
            seasons_to_spread=1,
        )
        two = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=10.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Ca",
            seasons_to_spread=2,
        )
        three = calculate_cation_ratio_target(
            soil_values=deficient_soil, cec=10.0,
            ratio_rows=ideal_ratios_with_provenance, nutrient="Ca",
            seasons_to_spread=3,
        )
        assert one["Target_kg_ha"] == pytest.approx(two["Target_kg_ha"] * 2, abs=0.5)
        assert three["Target_kg_ha"] == pytest.approx(two["Target_kg_ha"] * 2 / 3, abs=0.5)


class TestConversionConstants:
    """Sanity-check the FERTASA 5.2.2 equivalent-weight constants — if
    someone changes them, these fail loudly."""

    def test_equivalent_weights_match_fertasa_5_2_2(self):
        assert CATION_EQUIVALENT_WEIGHT_MG_PER_CMOL["Ca"] == 200.4
        assert CATION_EQUIVALENT_WEIGHT_MG_PER_CMOL["Mg"] == 121.56
        assert CATION_EQUIVALENT_WEIGHT_MG_PER_CMOL["K"] == 390.98

    def test_soil_mass_matches_existing_convention(self):
        """2,000,000 kg/ha = 2000 t/ha ≈ 15 cm × 1.33 g/cm³. The existing
        adjust_targets_for_ratios uses the same constant (via ×2/1000
        literal); if this drifts, the two code paths disagree silently."""
        assert CATION_SOIL_MASS_KG_PER_HA == 2_000_000

    def test_min_cec_gate_is_3(self):
        assert CATION_RATIO_MIN_CEC == 3.0


# ── Integration via calculate_nutrient_targets ─────────────────────────────


@pytest.fixture
def maize_crop_row():
    return {
        "crop": "Maize",
        "n": 22.0, "p": 4.0, "k": 18.0, "ca": 3.0, "mg": 2.0, "s": 2.5,
        "fe": 0.15, "b": 0.02, "mn": 0.1, "zn": 0.08, "mo": 0.001, "cu": 0.015,
    }


@pytest.fixture
def blueberry_crop_row():
    return {
        "crop": "Blueberry",
        "n": 8.0, "p": 2.0, "k": 10.0, "ca": 2.0, "mg": 0.8, "s": 1.0,
        "fe": 0.1, "b": 0.03, "mn": 0.1, "zn": 0.05, "mo": 0.001, "cu": 0.02,
    }


class TestCalculateNutrientTargetsWithRatioPath:
    def test_ratio_path_wins_for_ca_mg_when_rows_provided(
        self, sufficiency_rows, adjustment_rows_grouped, param_map_rows,
        maize_crop_row, ideal_ratios_with_provenance, deficient_soil,
    ):
        """Maize + deficient soil → Ca/Mg come from FERTASA 5.2.2 path,
        not removal × factor. N/P/K/S still use heuristic (no rate table
        provided in this test)."""
        targets = calculate_nutrient_targets(
            crop_name="Maize", yield_target=6.0, soil_values=deficient_soil,
            crop_rows=[maize_crop_row], sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows_grouped, param_map_rows=param_map_rows,
            ratio_rows=ideal_ratios_with_provenance,
        )
        ca = next(t for t in targets if t["Nutrient"] == "Ca")
        mg = next(t for t in targets if t["Nutrient"] == "Mg")
        n  = next(t for t in targets if t["Nutrient"] == "N")

        assert ca["Calc_Path"] == "cation_ratio"
        assert ca["Tier"] == 1
        assert "5.2.2" in ca["Source"]
        assert ca["Cation_Ratio_Hit"] is not None
        assert ca["Target_kg_ha"] == pytest.approx(202.4, abs=0.5)

        assert mg["Calc_Path"] == "cation_ratio"
        assert mg["Target_kg_ha"] > 0

        assert n["Calc_Path"] == "heuristic"

    def test_ratio_path_skipped_without_ratio_rows(
        self, sufficiency_rows, adjustment_rows_grouped, param_map_rows,
        maize_crop_row, deficient_soil,
    ):
        """If the caller doesn't pass ratio_rows, Ca/Mg fall through to
        heuristic — backward-compatible with pre-068 callers."""
        targets = calculate_nutrient_targets(
            crop_name="Maize", yield_target=6.0, soil_values=deficient_soil,
            crop_rows=[maize_crop_row], sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows_grouped, param_map_rows=param_map_rows,
        )
        ca = next(t for t in targets if t["Nutrient"] == "Ca")
        assert ca["Calc_Path"] == "heuristic"
        assert ca["Cation_Ratio_Hit"] is None

    def test_blueberry_flag_falls_back_to_heuristic(
        self, sufficiency_rows, adjustment_rows_grouped, param_map_rows,
        blueberry_crop_row, ideal_ratios_with_provenance, deficient_soil,
        crop_calc_flags_rows,
    ):
        """Blueberry flagged skip_cation_ratio_path=TRUE. Ca/Mg fall
        through to heuristic so the universal 60-70% Ca target doesn't
        damage the acid-loving crop."""
        targets = calculate_nutrient_targets(
            crop_name="Blueberry", yield_target=5.0, soil_values=deficient_soil,
            crop_rows=[blueberry_crop_row], sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows_grouped, param_map_rows=param_map_rows,
            ratio_rows=ideal_ratios_with_provenance,
            crop_calc_flags_rows=crop_calc_flags_rows,
        )
        ca = next(t for t in targets if t["Nutrient"] == "Ca")
        assert ca["Calc_Path"] == "heuristic"
        assert ca["Cation_Ratio_Hit"] is None

    def test_low_cec_falls_back_to_heuristic(
        self, sufficiency_rows, adjustment_rows_grouped, param_map_rows,
        maize_crop_row, ideal_ratios_with_provenance,
    ):
        """Sandy soil, CEC = 2 (< CATION_RATIO_MIN_CEC). Ratio path
        skips; Ca/Mg use heuristic."""
        sandy_soil = {
            "pH (H2O)": 5.5, "P (Bray-1)": 15, "K": 80, "Ca": 200, "Mg": 30,
            "S": 8, "N (total)": 20, "Zn": 1.0, "B": 0.5, "Mn": 10, "Fe": 10,
            "Cu": 0.5, "Mo": 0.1, "CEC": 2.0, "Na": 15,
        }
        targets = calculate_nutrient_targets(
            crop_name="Maize", yield_target=4.0, soil_values=sandy_soil,
            crop_rows=[maize_crop_row], sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows_grouped, param_map_rows=param_map_rows,
            ratio_rows=ideal_ratios_with_provenance,
        )
        ca = next(t for t in targets if t["Nutrient"] == "Ca")
        assert ca["Calc_Path"] == "heuristic"

    def test_k_still_uses_heuristic_when_no_rate_table(
        self, sufficiency_rows, adjustment_rows_grouped, param_map_rows,
        maize_crop_row, ideal_ratios_with_provenance, deficient_soil,
    ):
        """K is NOT in the ratio path even when a K base sat. row exists.
        Without a rate table, K falls through to heuristic."""
        targets = calculate_nutrient_targets(
            crop_name="Maize", yield_target=6.0, soil_values=deficient_soil,
            crop_rows=[maize_crop_row], sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows_grouped, param_map_rows=param_map_rows,
            ratio_rows=ideal_ratios_with_provenance,
        )
        k = next(t for t in targets if t["Nutrient"] == "K")
        assert k["Calc_Path"] == "heuristic"


class TestRatioPathInteractionsWithAdjust:
    """When adjust_targets_for_ratios runs after the ratio path produced
    a Ca/Mg base target, it must NOT stack a base-sat correction on top
    (double-counting the same shortfall)."""

    def test_adjust_targets_skips_ca_base_sat_when_ratio_path_used(
        self, sufficiency_rows, adjustment_rows_grouped, param_map_rows,
        maize_crop_row, ideal_ratios_with_provenance, deficient_soil,
        ratio_rows,
    ):
        from app.services.soil_engine import (
            adjust_targets_for_ratios, evaluate_ratios,
        )
        targets = calculate_nutrient_targets(
            crop_name="Maize", yield_target=6.0, soil_values=deficient_soil,
            crop_rows=[maize_crop_row], sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows_grouped, param_map_rows=param_map_rows,
            ratio_rows=ideal_ratios_with_provenance,
        )
        ca_before = next(t for t in targets if t["Nutrient"] == "Ca")["Target_kg_ha"]

        ratios = evaluate_ratios(deficient_soil, ratio_rows)
        adjusted = adjust_targets_for_ratios(
            targets, ratios, deficient_soil, ratio_rows,
        )
        ca_after = next(t for t in adjusted if t["Nutrient"] == "Ca")["Target_kg_ha"]

        # No base-sat stacking on top of the ratio path.
        assert ca_after == ca_before