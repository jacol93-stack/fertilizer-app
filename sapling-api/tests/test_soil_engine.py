"""Golden-case tests for soil_engine.

These lock in CURRENT behavior of classify_soil_value,
calculate_nutrient_targets, and adjust_targets_for_ratios. If any of these
tests later start failing, treat them as a load-bearing decision point:
is the behavior change intentional, and is the audit item it unblocks worth
the regression risk? Update the test only after that question is answered.

Known issues these tests INTENTIONALLY encode (from the calc audit):
  - Boundary values are classified inclusively (value == low_max -> "Low")
  - CEC-missing silently skips base-saturation adjustments
  - Empty crop rows return [] rather than raising
Those behaviors are documented here so the future fix has a target to change.
"""

from __future__ import annotations

import pytest

from app.services.soil_engine import (
    _canonicalise_param_name,
    adjust_targets_for_ratios,
    calculate_nutrient_targets,
    classify_soil_value,
    evaluate_ratios,
    get_adjustment_factor,
    normalise_soil_values,
)


# ── classify_soil_value ────────────────────────────────────────────────────

class TestClassifySoilValue:
    @pytest.mark.golden
    def test_very_low(self, sufficiency_rows):
        assert classify_soil_value(5, "K", sufficiency_rows) == "Very Low"

    @pytest.mark.golden
    def test_low(self, sufficiency_rows):
        assert classify_soil_value(75, "K", sufficiency_rows) == "Low"

    @pytest.mark.golden
    def test_optimal(self, sufficiency_rows):
        assert classify_soil_value(150, "K", sufficiency_rows) == "Optimal"

    @pytest.mark.golden
    def test_high(self, sufficiency_rows):
        assert classify_soil_value(300, "K", sufficiency_rows) == "High"

    @pytest.mark.golden
    def test_very_high(self, sufficiency_rows):
        assert classify_soil_value(500, "K", sufficiency_rows) == "Very High"

    @pytest.mark.golden
    def test_none_value_returns_empty(self, sufficiency_rows):
        assert classify_soil_value(None, "K", sufficiency_rows) == ""

    @pytest.mark.golden
    def test_unknown_param_returns_empty(self, sufficiency_rows):
        assert classify_soil_value(100, "Unobtainium", sufficiency_rows) == ""

    @pytest.mark.golden
    def test_boundary_is_inclusive_low(self, sufficiency_rows):
        """Locks in the <= boundary behavior. Audit flags this as counter-intuitive
        (a value exactly at low_max classifies as Low, not Optimal). Keeping this
        test will force a conscious decision if/when the audit fix is applied."""
        # K low_max = 100 in fixture
        assert classify_soil_value(100, "K", sufficiency_rows) == "Low"

    @pytest.mark.golden
    def test_boundary_is_inclusive_optimal(self, sufficiency_rows):
        # K optimal_max = 200 -> still Optimal
        assert classify_soil_value(200, "K", sufficiency_rows) == "Optimal"
        # 200.01 falls into High
        assert classify_soil_value(200.01, "K", sufficiency_rows) == "High"

    @pytest.mark.golden
    def test_crop_override_merge(self, sufficiency_rows):
        overrides = [{
            "parameter": "K",
            "very_low_max": 80,
            "low_max": 150,
            "optimal_max": 250,
            "high_max": 400,
        }]
        assert classify_soil_value(150, "K", sufficiency_rows, overrides) == "Low"
        assert classify_soil_value(200, "K", sufficiency_rows, overrides) == "Optimal"

    @pytest.mark.golden
    def test_partial_crop_override_falls_back_to_universal(self, sufficiency_rows):
        # Only low_max is overridden; other thresholds come from universal rows.
        overrides = [{"parameter": "K", "low_max": 150}]
        # Universal optimal_max = 200 is still in play
        assert classify_soil_value(180, "K", sufficiency_rows, overrides) == "Optimal"


# ── get_adjustment_factor ──────────────────────────────────────────────────

class TestGetAdjustmentFactor:
    @pytest.mark.golden
    def test_universal_lookup(self, adjustment_rows):
        assert get_adjustment_factor("Very Low", adjustment_rows) == 1.5
        assert get_adjustment_factor("Low", adjustment_rows) == 1.25
        assert get_adjustment_factor("Optimal", adjustment_rows) == 1.0
        assert get_adjustment_factor("High", adjustment_rows) == 0.5
        assert get_adjustment_factor("Very High", adjustment_rows) == 0.0

    @pytest.mark.golden
    def test_empty_classification_returns_one(self, adjustment_rows):
        assert get_adjustment_factor("", adjustment_rows) == 1.0

    @pytest.mark.golden
    def test_group_specific_lookup(self, adjustment_rows_grouped):
        # K, Ca, Mg now resolve to distinct curves post migration 077.
        assert get_adjustment_factor("Low", adjustment_rows_grouped, nutrient="K") == 1.25

    @pytest.mark.golden
    def test_k_vs_ca_mg_split_at_high(self, adjustment_rows_grouped):
        """Migration 077: K drawdown is aggressive (0.5), Ca/Mg gentler (0.75),
        S flat (1.0). Previously all shared the cations curve."""
        assert get_adjustment_factor("High", adjustment_rows_grouped, nutrient="K") == 0.5
        assert get_adjustment_factor("High", adjustment_rows_grouped, nutrient="Ca") == 0.75
        assert get_adjustment_factor("High", adjustment_rows_grouped, nutrient="Mg") == 0.75
        assert get_adjustment_factor("High", adjustment_rows_grouped, nutrient="S") == 1.0

    @pytest.mark.golden
    def test_k_vs_ca_mg_split_at_very_high(self, adjustment_rows_grouped):
        """At Very High: K zeros out, Ca/Mg reduce to half (protect base
        saturation), S stays flat."""
        assert get_adjustment_factor("Very High", adjustment_rows_grouped, nutrient="K") == 0.0
        assert get_adjustment_factor("Very High", adjustment_rows_grouped, nutrient="Ca") == 0.5
        assert get_adjustment_factor("Very High", adjustment_rows_grouped, nutrient="Mg") == 0.5
        assert get_adjustment_factor("Very High", adjustment_rows_grouped, nutrient="S") == 1.0

    @pytest.mark.golden
    def test_group_fallback_to_universal(self, adjustment_rows):
        # No group-specific rows in this fixture — should still find a match
        assert get_adjustment_factor("Low", adjustment_rows, nutrient="K") == 1.25

    @pytest.mark.golden
    def test_unknown_classification_defaults_to_one(self, adjustment_rows):
        assert get_adjustment_factor("Nonsense", adjustment_rows) == 1.0


# ── calculate_nutrient_targets ─────────────────────────────────────────────

class TestCalculateNutrientTargets:
    @pytest.mark.golden
    def test_unknown_crop_returns_empty(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows, optimal_soil
    ):
        assert calculate_nutrient_targets(
            crop_name="Unobtainium",
            yield_target=10,
            soil_values=optimal_soil,
            crop_rows=crop_rows,
            sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows,
            param_map_rows=param_map_rows,
        ) == []

    @pytest.mark.golden
    def test_avocado_optimal_soil_base_requirement(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows, optimal_soil
    ):
        """Avocado at 15 t/ha on optimal soil: N = 8 * 15 * 1.0 = 120 kg/ha."""
        targets = calculate_nutrient_targets(
            crop_name="Avocado",
            yield_target=15,
            soil_values=optimal_soil,
            crop_rows=crop_rows,
            sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows,
            param_map_rows=param_map_rows,
        )
        by_nut = {t["Nutrient"]: t for t in targets}
        assert by_nut["N"]["Base_Req_kg_ha"] == 120.0
        assert by_nut["N"]["Factor"] == 1.0
        assert by_nut["N"]["Target_kg_ha"] == 120.0
        assert by_nut["N"]["Classification"] == "Optimal"

    @pytest.mark.golden
    def test_very_low_soil_boosts_target(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows
    ):
        """Very Low soil value triggers the 1.5x boost."""
        soil = {"K": 20, "P (Bray-1)": 30, "N (total)": 30}
        targets = calculate_nutrient_targets(
            crop_name="Avocado",
            yield_target=10,
            soil_values=soil,
            crop_rows=crop_rows,
            sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows,
            param_map_rows=param_map_rows,
        )
        k = next(t for t in targets if t["Nutrient"] == "K")
        # base = 10 * 10 = 100; factor 1.5 -> 150
        assert k["Classification"] == "Very Low"
        assert k["Factor"] == 1.5
        assert k["Target_kg_ha"] == 150.0

    @pytest.mark.golden
    def test_very_high_soil_zeros_target(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows
    ):
        soil = {"K": 500, "P (Bray-1)": 30, "N (total)": 30}
        targets = calculate_nutrient_targets(
            crop_name="Avocado",
            yield_target=10,
            soil_values=soil,
            crop_rows=crop_rows,
            sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows,
            param_map_rows=param_map_rows,
        )
        k = next(t for t in targets if t["Nutrient"] == "K")
        assert k["Classification"] == "Very High"
        assert k["Factor"] == 0.0
        assert k["Target_kg_ha"] == 0.0

    @pytest.mark.golden
    def test_missing_soil_value_defaults_to_factor_one(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows
    ):
        """Audit: missing soil values silently fall through to factor 1.0.
        Locking in current behavior — will surface as a warning after the fix."""
        targets = calculate_nutrient_targets(
            crop_name="Avocado",
            yield_target=10,
            soil_values={},  # no soil data at all
            crop_rows=crop_rows,
            sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows,
            param_map_rows=param_map_rows,
        )
        k = next(t for t in targets if t["Nutrient"] == "K")
        assert k["Classification"] == ""
        assert k["Factor"] == 1.0
        assert k["Target_kg_ha"] == 100.0  # 10 * 10 * 1.0

    @pytest.mark.golden
    def test_zero_yield_produces_zero_targets(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows, optimal_soil
    ):
        """Audit issue: zero yield silently produces zero targets with no error.
        Locking in behavior so a future fix (validation error) trips this test."""
        targets = calculate_nutrient_targets(
            crop_name="Avocado",
            yield_target=0,
            soil_values=optimal_soil,
            crop_rows=crop_rows,
            sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows,
            param_map_rows=param_map_rows,
        )
        assert all(t["Target_kg_ha"] == 0 for t in targets)


# ── evaluate_ratios ────────────────────────────────────────────────────────

class TestEvaluateRatios:
    @pytest.mark.golden
    def test_ideal_ca_mg(self, ratio_rows):
        # Ca=800, Mg=160 -> 5.0 (ideal 3-6)
        soil = {"Ca": 800, "Mg": 160}
        results = evaluate_ratios(soil, ratio_rows)
        cm = next(r for r in results if r["Ratio"] == "Ca:Mg")
        assert cm["Actual"] == 5.0
        assert cm["Status"] == "Ideal"

    @pytest.mark.golden
    def test_below_ideal_ca_mg(self, ratio_rows):
        soil = {"Ca": 300, "Mg": 200}  # 1.5
        results = evaluate_ratios(soil, ratio_rows)
        cm = next(r for r in results if r["Ratio"] == "Ca:Mg")
        assert cm["Status"] == "Below ideal"

    @pytest.mark.golden
    def test_missing_cec_omits_base_saturation(self, ratio_rows):
        """Audit item: base saturation silently skipped when CEC missing."""
        soil = {"Ca": 800, "Mg": 160, "K": 150}
        results = evaluate_ratios(soil, ratio_rows)
        assert not any(r["Ratio"].endswith("base sat.") for r in results)

    @pytest.mark.golden
    def test_base_saturation_present_with_cec(self, ratio_rows):
        soil = {"Ca": 800, "Mg": 160, "K": 150, "Na": 30, "CEC": 10.0}
        results = evaluate_ratios(soil, ratio_rows)
        ca_sat = next(r for r in results if r["Ratio"] == "Ca base sat.")
        # (800/200.4)/10 * 100 ~= 39.92
        assert ca_sat["Actual"] == pytest.approx(39.9, abs=0.2)


# ── adjust_targets_for_ratios ──────────────────────────────────────────────

class TestAdjustTargetsForRatios:
    @pytest.mark.golden
    def test_ideal_ratios_no_change(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows,
        ratio_rows, optimal_soil
    ):
        targets = calculate_nutrient_targets(
            "Avocado", 15, optimal_soil, crop_rows,
            sufficiency_rows, adjustment_rows, param_map_rows,
        )
        ratios = evaluate_ratios(optimal_soil, ratio_rows)
        adjusted = adjust_targets_for_ratios(targets, ratios, optimal_soil, ratio_rows)
        # N is never reduced by ratio logic
        n = next(t for t in adjusted if t["Nutrient"] == "N")
        assert n["Final_Target_kg_ha"] == n["Target_kg_ha"]

    @pytest.mark.golden
    def test_n_never_reduced_by_ratios(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows, ratio_rows
    ):
        """N is 'not bankable' — ratio logic may not reduce it."""
        # Construct a soil where N:S is wildly off in a way that would otherwise
        # want to reduce N (even though the current engine doesn't — lock it in).
        soil = {
            "N (total)": 30, "S": 2,  # N:S = 15 (above ideal 8-12)
            "K": 180, "Ca": 800, "Mg": 150, "P (Bray-1)": 30,
        }
        targets = calculate_nutrient_targets(
            "Avocado", 15, soil, crop_rows,
            sufficiency_rows, adjustment_rows, param_map_rows,
        )
        ratios = evaluate_ratios(soil, ratio_rows)
        adjusted = adjust_targets_for_ratios(targets, ratios, soil, ratio_rows)
        n = next(t for t in adjusted if t["Nutrient"] == "N")
        assert n["Ratio_Adjustment_kg_ha"] >= 0
        assert n["Final_Target_kg_ha"] >= n["Target_kg_ha"]

    @pytest.mark.golden
    def test_final_target_never_negative(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows, ratio_rows
    ):
        soil = {
            "K": 500, "Ca": 3000, "Mg": 500, "P (Bray-1)": 100, "N (total)": 30,
        }
        targets = calculate_nutrient_targets(
            "Avocado", 15, soil, crop_rows,
            sufficiency_rows, adjustment_rows, param_map_rows,
        )
        ratios = evaluate_ratios(soil, ratio_rows)
        adjusted = adjust_targets_for_ratios(targets, ratios, soil, ratio_rows)
        assert all(t["Final_Target_kg_ha"] >= 0 for t in adjusted)


# ── normalise_soil_values ──────────────────────────────────────────────────


class TestNormaliseSoilValues:
    """Lab files often label columns with units ("K (mg/kg)") but the engine's
    reference tables are unit-free ("K"). normalise_soil_values bridges the
    two, idempotently."""

    def test_strips_mg_per_kg_suffix(self):
        out = normalise_soil_values({"K (mg/kg)": 263, "Ca (mg/kg)": 944})
        assert out == {"K": 263, "Ca": 944}

    def test_strips_cmol_kg_suffix(self):
        out = normalise_soil_values({"CEC (cmol/kg)": 6.94})
        assert out == {"CEC": 6.94}

    def test_preserves_method_qualifier_inside_parens(self):
        out = normalise_soil_values({"P (Bray-1) (mg/kg)": 61, "pH (KCl)": 5.29})
        # (Bray-1) and (KCl) stay — they're qualifiers not units
        assert out == {"P (Bray-1)": 61, "pH (KCl)": 5.29}

    def test_strips_percent_marker(self):
        out = normalise_soil_values({"Acid Saturation (%)": 0.0, "K Saturation (%)": 9.7})
        assert out == {"Acid Saturation": 0.0, "K Saturation": 9.7}

    def test_already_canonical_passthrough(self):
        out = normalise_soil_values({"K": 263, "Ca": 944, "P (Bray-1)": 61})
        assert out == {"K": 263, "Ca": 944, "P (Bray-1)": 61}

    def test_idempotent(self):
        once = normalise_soil_values({"K (mg/kg)": 263})
        twice = normalise_soil_values(once)
        assert once == twice

    def test_canonical_wins_on_collision(self):
        # Both forms in the same dict — canonical takes precedence
        out = normalise_soil_values({"K (mg/kg)": 100, "K": 263})
        assert out["K"] == 263

    def test_handles_none_or_empty(self):
        assert normalise_soil_values(None) == {}
        assert normalise_soil_values({}) == {}

    def test_canonicalise_helper(self):
        assert _canonicalise_param_name("K (mg/kg)") == "K"
        assert _canonicalise_param_name("Bulk Density (g/ml)") == "Bulk Density"
        assert _canonicalise_param_name("pH (KCl)") == "pH (KCl)"
        assert _canonicalise_param_name("P (Bray-1) (mg/kg)") == "P (Bray-1)"


class TestEngineHandlesUnitSuffixedKeys:
    """Anton-style data: lab keys carry units. Engine should classify,
    compute targets, and evaluate ratios identically to canonical-key
    inputs."""

    def test_classify_via_calculate_nutrient_targets_with_unit_keys(
        self, sufficiency_rows, adjustment_rows, param_map_rows, crop_rows
    ):
        canonical = {"N (total)": 20, "P (Bray-1)": 30, "K": 200, "Ca": 800, "Mg": 150, "S": 12}
        unit_suffixed = {
            "N (total) (mg/kg)": 20,
            "P (Bray-1) (mg/kg)": 30,
            "K (mg/kg)": 200,
            "Ca (mg/kg)": 800,
            "Mg (mg/kg)": 150,
            "S (mg/kg)": 12,
        }
        canon_t = calculate_nutrient_targets(
            "Macadamia", 5, canonical, crop_rows,
            sufficiency_rows, adjustment_rows, param_map_rows,
        )
        unit_t = calculate_nutrient_targets(
            "Macadamia", 5, unit_suffixed, crop_rows,
            sufficiency_rows, adjustment_rows, param_map_rows,
        )
        # Same classifications driven by same soil values via different keys
        canon_by_nut = {t["Nutrient"]: t for t in canon_t}
        unit_by_nut = {t["Nutrient"]: t for t in unit_t}
        for nut in canon_by_nut:
            if nut not in unit_by_nut:
                continue
            assert canon_by_nut[nut].get("Classification") == unit_by_nut[nut].get("Classification"), (
                f"{nut} classification differs: canonical={canon_by_nut[nut].get('Classification')} "
                f"unit-suffixed={unit_by_nut[nut].get('Classification')}"
            )

    def test_evaluate_ratios_with_unit_keys(self, ratio_rows):
        unit_keyed = {
            "Ca (mg/kg)": 1000, "Mg (mg/kg)": 200, "K (mg/kg)": 250,
        }
        canonical = {"Ca": 1000, "Mg": 200, "K": 250}
        rs_unit = evaluate_ratios(unit_keyed, ratio_rows)
        rs_canon = evaluate_ratios(canonical, ratio_rows)
        assert len(rs_unit) == len(rs_canon)
