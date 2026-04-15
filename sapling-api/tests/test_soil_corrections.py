"""Golden-case tests for soil_corrections.

Locks in lime/gypsum/organic matter corrective calculation behavior.

Audit issues deliberately encoded here:
  - _buffer_factor uses inclusive <= boundaries (clay=15 hits sandy tier)
  - Acidophilic-crop detection uses simple substring matching
  - Gypsum rate ignores drawdown offset from ongoing fertilizer inputs
"""

from __future__ import annotations

import pytest

from app.services.soil_corrections import (
    _buffer_factor,
    calculate_gypsum_requirement,
    calculate_lime_requirement,
    check_organic_carbon,
    get_nutrient_explanations,
)


class TestBufferFactor:
    @pytest.mark.golden
    def test_sandy(self):
        assert _buffer_factor(10) == 1.5

    @pytest.mark.golden
    def test_sandy_loam(self):
        assert _buffer_factor(20) == 2.5

    @pytest.mark.golden
    def test_loam(self):
        assert _buffer_factor(30) == 3.5

    @pytest.mark.golden
    def test_clay_loam(self):
        assert _buffer_factor(40) == 4.5

    @pytest.mark.golden
    def test_clay(self):
        assert _buffer_factor(55) == 5.5

    @pytest.mark.golden
    def test_boundary_15_is_sandy(self):
        """Audit quirk: clay=15 hits sandy tier (<=15), not sandy loam.
        Boundary is inclusive. Locking in so the future fix to strictly-less
        trips this test."""
        assert _buffer_factor(15) == 1.5
        assert _buffer_factor(15.01) == 2.5


class TestCalculateLimeRequirement:
    @pytest.mark.golden
    def test_no_ph_data_returns_none(self):
        assert calculate_lime_requirement({}, {}) is None

    @pytest.mark.golden
    def test_ph_already_high_enough(self):
        soil = {"pH (H2O)": 6.2, "Clay": 25}
        assert calculate_lime_requirement(soil, {}) is None

    @pytest.mark.golden
    def test_acidic_soil_recommends_lime(self):
        soil = {"pH (H2O)": 5.0, "Clay": 25, "Org C": 1.0}
        result = calculate_lime_requirement(soil, {})
        assert result is not None
        assert result["type"] == "lime"
        # ph_deficit = 6.0 - 5.0 = 1.0; clay 25 -> buffer 2.5; 1.0 * 2.5 = 2.5 t/ha
        assert "2.5 t/ha" in result["rate"]

    @pytest.mark.golden
    def test_dolomitic_chosen_when_mg_low(self):
        soil = {"pH (H2O)": 5.0, "Clay": 25}
        result = calculate_lime_requirement(soil, {"Mg": "Low"})
        assert "Dolomitic" in result["product"]

    @pytest.mark.golden
    def test_calcitic_when_mg_ok(self):
        soil = {"pH (H2O)": 5.0, "Clay": 25}
        result = calculate_lime_requirement(soil, {"Mg": "Optimal"})
        assert "Calcitic" in result["product"]

    @pytest.mark.golden
    def test_blueberry_target_ph_is_5(self):
        """Acidophilic crops have target pH 5.0 instead of 6.0."""
        soil = {"pH (H2O)": 5.2, "Clay": 25}
        # For blueberry: target=5.0, current=5.2, no lime needed
        result = calculate_lime_requirement(soil, {}, crop="Blueberry")
        assert result is None

    @pytest.mark.golden
    def test_org_c_bumps_buffer(self):
        """Org C > 2% adds 0.5 to the buffer factor."""
        # clay 25 -> buffer 2.5; org c 3 -> buffer 3.0
        # deficit 1.0 * 3.0 = 3.0 t/ha
        soil = {"pH (H2O)": 5.0, "Clay": 25, "Org C": 3.0}
        result = calculate_lime_requirement(soil, {})
        assert "3.0 t/ha" in result["rate"]


class TestCalculateGypsumRequirement:
    @pytest.mark.golden
    def test_no_na_returns_none(self):
        assert calculate_gypsum_requirement({}, {}) is None

    @pytest.mark.golden
    def test_na_optimal_no_gypsum(self):
        soil = {"Na": 40}
        assert calculate_gypsum_requirement(soil, {"Na": "Optimal"}) is None

    @pytest.mark.golden
    def test_na_high_recommends_gypsum(self):
        soil = {"Na": 150, "Clay": 20}
        result = calculate_gypsum_requirement(soil, {"Na": "High"})
        assert result is not None
        assert result["type"] == "gypsum"
        # na_excess = 100; factor = 4 + 20/20 = 5; 100 * 5 = 500 kg/ha
        assert "500 kg/ha" in result["rate"]

    @pytest.mark.golden
    def test_below_practical_threshold_returns_none(self):
        """If calculated gypsum rate < 100 kg/ha, skip."""
        soil = {"Na": 60, "Clay": 20}  # excess 10 * 5 = 50 kg/ha
        assert calculate_gypsum_requirement(soil, {"Na": "High"}) is None


class TestCheckOrganicCarbon:
    @pytest.mark.golden
    def test_optimal_returns_none(self):
        assert check_organic_carbon({"Org C": 2.5}, {"Org C": "Optimal"}) is None

    @pytest.mark.golden
    def test_very_low_critical(self):
        result = check_organic_carbon({"Org C": 0.3}, {"Org C": "Very Low"})
        assert result is not None
        assert result["min_compost_pct"] == 60
        assert "critical" in result["note"]

    @pytest.mark.golden
    def test_low_important(self):
        result = check_organic_carbon({"Org C": 0.8}, {"Org C": "Low"})
        assert result["min_compost_pct"] == 55
        assert "important" in result["note"]

    @pytest.mark.golden
    def test_missing_org_c_returns_none(self):
        assert check_organic_carbon({}, {}) is None


class TestGetNutrientExplanations:
    @pytest.mark.golden
    def test_factor_reduced_explanation(self):
        targets = [{
            "Nutrient": "K",
            "Base_Req_kg_ha": 100,
            "Final_Target_kg_ha": 50,
            "Target_kg_ha": 50,
            "Ratio_Adjustment_kg_ha": 0,
            "Ratio_Reasons": [],
            "Classification": "High",
            "Factor": 0.5,
        }]
        result = get_nutrient_explanations(targets)
        assert len(result) == 1
        assert result[0]["nutrient"] == "K"
        assert any("Reduced to 50%" in n for n in result[0]["notes"])

    @pytest.mark.golden
    def test_factor_zero_explanation(self):
        targets = [{
            "Nutrient": "K",
            "Base_Req_kg_ha": 100,
            "Final_Target_kg_ha": 0,
            "Target_kg_ha": 0,
            "Ratio_Adjustment_kg_ha": 0,
            "Ratio_Reasons": [],
            "Classification": "Very High",
            "Factor": 0.0,
        }]
        result = get_nutrient_explanations(targets)
        # factor == 0 with base > 0 emits "Not applied" note, but the final
        # filter requires final > 0 or ratio_warnings — so it's filtered out.
        # Lock this in: zero-final entries with no warnings don't surface.
        assert result == []

    @pytest.mark.golden
    def test_ratio_increase_explanation(self):
        targets = [{
            "Nutrient": "Zn",
            "Base_Req_kg_ha": 1.0,
            "Final_Target_kg_ha": 2.5,
            "Target_kg_ha": 1.0,
            "Ratio_Adjustment_kg_ha": 1.5,
            "Ratio_Reasons": ["P:Zn ratio too high"],
            "Classification": "Optimal",
            "Factor": 1.0,
        }]
        result = get_nutrient_explanations(targets)
        assert len(result) == 1
        assert any("Increased by 1.5" in n for n in result[0]["notes"])

    @pytest.mark.golden
    def test_no_adjustment_no_explanation(self):
        targets = [{
            "Nutrient": "N",
            "Base_Req_kg_ha": 100,
            "Final_Target_kg_ha": 100,
            "Target_kg_ha": 100,
            "Ratio_Adjustment_kg_ha": 0,
            "Ratio_Reasons": [],
            "Classification": "Optimal",
            "Factor": 1.0,
        }]
        assert get_nutrient_explanations(targets) == []

    @pytest.mark.golden
    def test_warning_surfaces_even_without_adjustment(self):
        targets = [{
            "Nutrient": "Ca",
            "Base_Req_kg_ha": 50,
            "Final_Target_kg_ha": 50,
            "Target_kg_ha": 50,
            "Ratio_Adjustment_kg_ha": 0,
            "Ratio_Reasons": [],
            "Ratio_Warnings": ["Ca base sat. below ideal — already High, monitor tissue"],
            "Classification": "High",
            "Factor": 0.5,
        }]
        result = get_nutrient_explanations(targets)
        assert len(result) == 1
        assert any("⚠" in n for n in result[0]["notes"])
