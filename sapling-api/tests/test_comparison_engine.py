"""Golden-case tests for comparison_engine.

Locks in current behavior of calculate_crop_impact and generate_recommendations.
Known audit quirks encoded as tests:
  - v1f == 0 with non-zero change produces pct_change=0 (masks lab-zero edge case)
  - 25% threshold for "significant decline", 10% for "moderate" — hardcoded
  - Different-field pair always returns available=False regardless of crops
"""

from __future__ import annotations

import pytest

from app.services.comparison_engine import (
    _class_index,
    _optimal_distance,
    calculate_crop_impact,
    generate_recommendations,
)


# ── Internal helpers ──────────────────────────────────────────────────────

class TestClassIndex:
    @pytest.mark.golden
    def test_known_classes(self):
        assert _class_index("Very Low") == 0
        assert _class_index("Low") == 1
        assert _class_index("Optimal") == 2
        assert _class_index("High") == 3
        assert _class_index("Very High") == 4

    @pytest.mark.golden
    def test_unknown_returns_negative(self):
        assert _class_index("Nonsense") == -1
        assert _class_index("") == -1


class TestOptimalDistance:
    @pytest.mark.golden
    def test_optimal_is_zero(self):
        assert _optimal_distance("Optimal") == 0

    @pytest.mark.golden
    def test_symmetric(self):
        assert _optimal_distance("Low") == _optimal_distance("High") == 1
        assert _optimal_distance("Very Low") == _optimal_distance("Very High") == 2

    @pytest.mark.golden
    def test_unknown_returns_negative(self):
        assert _optimal_distance("Garbage") == -1


# ── calculate_crop_impact ─────────────────────────────────────────────────

@pytest.fixture
def impact_crop_rows():
    return [{
        "crop": "Maize",
        "n": 22.0, "p": 4.0, "k": 18.0, "ca": 3.0, "mg": 2.0, "s": 2.5,
        "fe": 0.15, "b": 0.02, "mn": 0.1, "zn": 0.08, "mo": 0.001, "cu": 0.015,
    }]


@pytest.fixture
def impact_param_map():
    return [
        {"crop_nutrient": "N", "soil_parameter": "N (total)"},
        {"crop_nutrient": "P", "soil_parameter": "P (Bray-1)"},
        {"crop_nutrient": "K", "soil_parameter": "K"},
    ]


class TestCalculateCropImpact:
    @pytest.mark.golden
    def test_different_fields_not_applicable(self, impact_crop_rows, impact_param_map):
        a1 = {"field_id": "f1", "soil_values": {"K": 200}, "crop": "Maize", "yield_target": 8}
        a2 = {"field_id": "f2", "soil_values": {"K": 150}, "crop": "Maize", "yield_target": 8}
        result = calculate_crop_impact(a1, a2, impact_crop_rows, impact_param_map)
        assert result["available"] is False
        assert "Different fields" in result["reason"]

    @pytest.mark.golden
    def test_same_field_with_crop_returns_nutrients(self, impact_crop_rows, impact_param_map):
        a1 = {
            "field_id": "f1",
            "soil_values": {"K": 200, "N (total)": 30, "P (Bray-1)": 25},
            "crop": "Maize", "yield_target": 8,
            "created_at": "2024-01-01T00:00:00Z",
        }
        a2 = {
            "field_id": "f1",
            "soil_values": {"K": 150, "N (total)": 25, "P (Bray-1)": 20},
            "crop": "Maize", "yield_target": 8,
            "created_at": "2025-01-01T00:00:00Z",
        }
        result = calculate_crop_impact(a1, a2, impact_crop_rows, impact_param_map)
        assert result["available"] is True
        assert len(result["nutrients"]) == 12  # all NUTRIENTS

        k = next(n for n in result["nutrients"] if n["nutrient"] == "K")
        assert k["expected_depletion_kg_ha"] == pytest.approx(144.0)  # 18 × 8
        assert k["actual_change"] == -50.0
        assert "decline" in k["interpretation"].lower()

    @pytest.mark.golden
    def test_no_crop_and_no_history_unavailable(self, impact_crop_rows, impact_param_map):
        a1 = {"field_id": "f1", "soil_values": {"K": 200}}
        a2 = {"field_id": "f1", "soil_values": {"K": 150}}
        result = calculate_crop_impact(a1, a2, impact_crop_rows, impact_param_map)
        assert result["available"] is False
        assert "No crop data" in result["reason"]

    @pytest.mark.golden
    def test_missing_soil_value_marked_insufficient(self, impact_crop_rows, impact_param_map):
        a1 = {
            "field_id": "f1",
            "soil_values": {"K": 200},
            "crop": "Maize", "yield_target": 8,
            "created_at": "2024-01-01T00:00:00Z",
        }
        a2 = {
            "field_id": "f1",
            "soil_values": {},  # missing
            "crop": "Maize", "yield_target": 8,
            "created_at": "2025-01-01T00:00:00Z",
        }
        result = calculate_crop_impact(a1, a2, impact_crop_rows, impact_param_map)
        k = next(n for n in result["nutrients"] if n["nutrient"] == "K")
        assert k["actual_change"] is None
        assert "Insufficient" in k["interpretation"]

    @pytest.mark.golden
    def test_crop_history_overrides_analysis_crop(self, impact_crop_rows, impact_param_map):
        a1 = {
            "field_id": "f1",
            "soil_values": {"K": 200, "N (total)": 30, "P (Bray-1)": 25},
            "crop": "Wheat", "yield_target": 5,  # should be ignored
            "created_at": "2024-01-01T00:00:00Z",
        }
        a2 = {
            "field_id": "f1",
            "soil_values": {"K": 150, "N (total)": 25, "P (Bray-1)": 20},
            "crop": "Wheat", "yield_target": 5,
            "created_at": "2025-01-01T00:00:00Z",
        }
        history = [{"crop": "Maize", "estimated_yield": 10, "season": "2024"}]
        result = calculate_crop_impact(
            a1, a2, impact_crop_rows, impact_param_map, crop_history=history
        )
        assert result["available"] is True
        assert result["crops_label"].startswith("Maize")
        k = next(n for n in result["nutrients"] if n["nutrient"] == "K")
        assert k["expected_depletion_kg_ha"] == pytest.approx(180.0)  # 18 × 10

    @pytest.mark.golden
    def test_unknown_crop_in_history_marked_unresolved(self, impact_crop_rows, impact_param_map):
        a1 = {
            "field_id": "f1",
            "soil_values": {"K": 200},
            "created_at": "2024-01-01T00:00:00Z",
        }
        a2 = {
            "field_id": "f1",
            "soil_values": {"K": 150},
            "created_at": "2025-01-01T00:00:00Z",
        }
        history = [{"crop": "Unobtainium", "estimated_yield": 10}]
        result = calculate_crop_impact(
            a1, a2, impact_crop_rows, impact_param_map, crop_history=history
        )
        assert result["available"] is True
        assert "Unobtainium" in result["unresolved_crops"]


# ── generate_recommendations ──────────────────────────────────────────────

class TestGenerateRecommendations:
    @pytest.mark.golden
    def test_fewer_than_two_returns_empty(self):
        assert generate_recommendations([{}], []) == []
        assert generate_recommendations([], []) == []

    @pytest.mark.golden
    def test_consistent_decline_three_analyses(self):
        analyses = [
            {"soil_values": {"K": 200}, "classifications": {"K": "High"}},
            {"soil_values": {"K": 150}, "classifications": {"K": "Optimal"}},
            {"soil_values": {"K": 100}, "classifications": {"K": "Low"}},
        ]
        recs = generate_recommendations(analyses, [], comparison_type="timeline")
        warnings = [r for r in recs if r["type"] == "warning"]
        assert any("K" in r["message"] and "declined" in r["message"] for r in warnings)

    @pytest.mark.golden
    def test_ph_decline_suggests_liming(self):
        analyses = [
            {"soil_values": {"pH (H2O)": 6.5}, "classifications": {"pH (H2O)": "Optimal"}},
            {"soil_values": {"pH (H2O)": 6.0}, "classifications": {"pH (H2O)": "Low"}},
            {"soil_values": {"pH (H2O)": 5.5}, "classifications": {"pH (H2O)": "Low"}},
        ]
        recs = generate_recommendations(analyses, [], comparison_type="timeline")
        ph_recs = [r for r in recs if "pH" in r["message"]]
        assert any("liming" in r["message"].lower() for r in ph_recs)

    @pytest.mark.golden
    def test_stable_values_marked_success(self):
        analyses = [
            {"soil_values": {"K": 200}},
            {"soil_values": {"K": 205}},
            {"soil_values": {"K": 195}},  # within 10%
        ]
        recs = generate_recommendations(analyses, [], comparison_type="timeline")
        assert any(r["type"] == "success" and "K" in r["message"] for r in recs)

    @pytest.mark.golden
    def test_classification_improvement_success(self):
        """Audit quirk: classification transition rules only fire for
        parameters that ALSO appear in soil_values, because all_params
        is built from soil_values keys. Passing both is required for
        the rule to trip — lock this in so the future fix (iterate
        classifications too) trips the test."""
        analyses = [
            {"soil_values": {"K": 100}, "classifications": {"K": "Low"}},
            {"soil_values": {"K": 180}, "classifications": {"K": "Optimal"}},
        ]
        recs = generate_recommendations(analyses, [], comparison_type="snapshot")
        assert any(r["type"] == "success" and "improved" in r["message"] for r in recs)

    @pytest.mark.golden
    def test_classification_worsening_warning(self):
        analyses = [
            {"soil_values": {"K": 200}, "classifications": {"K": "Optimal"}},
            {"soil_values": {"K": 20}, "classifications": {"K": "Very Low"}},
        ]
        recs = generate_recommendations(analyses, [], comparison_type="snapshot")
        warnings = [r for r in recs if r["type"] == "warning"]
        assert len(warnings) > 0

    @pytest.mark.golden
    def test_trend_rules_only_apply_to_timeline(self):
        analyses = [
            {"soil_values": {"K": 200}},
            {"soil_values": {"K": 150}},
            {"soil_values": {"K": 100}},
        ]
        recs_snapshot = generate_recommendations(analyses, [], comparison_type="snapshot")
        # Trend warnings (consistent decline) should not fire for snapshot
        trend_warnings = [r for r in recs_snapshot if "declined across" in r["message"]]
        assert trend_warnings == []
