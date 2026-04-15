"""Golden-case tests for feeding_engine.

Locks in behavior of generate_feeding_plan, build_practical_plan,
get_age_factor, and validate_methods. These intentionally cover the
audit-flagged quirks so fixing them is a deliberate act.

Known audit issues encoded here:
  - Age beyond table range silently returns default 1.0 (no warning)
  - Rounding accumulates across apps within a stage
  - Mo/Cu divided by len(stages_sorted) — crashes on empty stages
  - Month wrapping computed but no validation of 1-12 range
"""

from __future__ import annotations

import pytest

from app.services.feeding_engine import (
    build_practical_plan,
    generate_feeding_plan,
    get_age_factor,
    validate_methods,
)


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def nutrient_targets():
    """Representative output of calculate_nutrient_targets()."""
    return [
        {"Nutrient": "N",  "Final_Target_kg_ha": 120.0, "Target_kg_ha": 120.0},
        {"Nutrient": "P",  "Final_Target_kg_ha": 22.5,  "Target_kg_ha": 22.5},
        {"Nutrient": "K",  "Final_Target_kg_ha": 150.0, "Target_kg_ha": 150.0},
        {"Nutrient": "Ca", "Final_Target_kg_ha": 45.0,  "Target_kg_ha": 45.0},
        {"Nutrient": "Mg", "Final_Target_kg_ha": 15.0,  "Target_kg_ha": 15.0},
        {"Nutrient": "S",  "Final_Target_kg_ha": 15.0,  "Target_kg_ha": 15.0},
        {"Nutrient": "Zn", "Final_Target_kg_ha": 0.75,  "Target_kg_ha": 0.75},
        {"Nutrient": "B",  "Final_Target_kg_ha": 0.5,   "Target_kg_ha": 0.5},
        {"Nutrient": "Mn", "Final_Target_kg_ha": 1.2,   "Target_kg_ha": 1.2},
        {"Nutrient": "Fe", "Final_Target_kg_ha": 1.5,   "Target_kg_ha": 1.5},
        {"Nutrient": "Mo", "Final_Target_kg_ha": 0.05,  "Target_kg_ha": 0.05},
        {"Nutrient": "Cu", "Final_Target_kg_ha": 0.3,   "Target_kg_ha": 0.3},
    ]


@pytest.fixture
def avocado_growth_stages():
    """Three-stage avocado schedule summing to 100% per nutrient."""
    return [
        {
            "stage_name": "Pre-bloom",
            "stage_order": 1,
            "month_start": 7, "month_end": 8,
            "num_applications": 1,
            "n_pct": 20, "p_pct": 30, "k_pct": 10,
            "ca_pct": 20, "mg_pct": 20, "s_pct": 20,
            "fe_pct": 33, "b_pct": 33, "mn_pct": 33, "zn_pct": 33,
            "default_method": "broadcast",
        },
        {
            "stage_name": "Fruit set",
            "stage_order": 2,
            "month_start": 10, "month_end": 12,
            "num_applications": 2,
            "n_pct": 50, "p_pct": 40, "k_pct": 50,
            "ca_pct": 40, "mg_pct": 40, "s_pct": 40,
            "fe_pct": 34, "b_pct": 34, "mn_pct": 34, "zn_pct": 34,
            "default_method": "broadcast",
        },
        {
            "stage_name": "Fruit fill",
            "stage_order": 3,
            "month_start": 1, "month_end": 3,
            "num_applications": 2,
            "n_pct": 30, "p_pct": 30, "k_pct": 40,
            "ca_pct": 40, "mg_pct": 40, "s_pct": 40,
            "fe_pct": 33, "b_pct": 33, "mn_pct": 33, "zn_pct": 33,
            "default_method": "fertigation",
        },
    ]


@pytest.fixture
def age_factors():
    return [
        {"age_min": 1, "age_max": 2, "n_factor": 0.3, "p_factor": 0.4, "k_factor": 0.3, "general_factor": 0.3},
        {"age_min": 3, "age_max": 5, "n_factor": 0.6, "p_factor": 0.7, "k_factor": 0.6, "general_factor": 0.6},
        {"age_min": 6, "age_max": 20, "n_factor": 1.0, "p_factor": 1.0, "k_factor": 1.0, "general_factor": 1.0},
    ]


# ── get_age_factor ─────────────────────────────────────────────────────────

class TestGetAgeFactor:
    @pytest.mark.golden
    def test_within_range(self, age_factors):
        af = get_age_factor(4, age_factors)
        assert af["n_factor"] == 0.6

    @pytest.mark.golden
    def test_boundary_inclusive(self, age_factors):
        assert get_age_factor(2, age_factors)["n_factor"] == 0.3
        assert get_age_factor(3, age_factors)["n_factor"] == 0.6

    @pytest.mark.golden
    def test_none_age_returns_default(self, age_factors):
        af = get_age_factor(None, age_factors)
        assert af == {"n_factor": 1.0, "p_factor": 1.0, "k_factor": 1.0, "general_factor": 1.0}

    @pytest.mark.golden
    def test_empty_factors_returns_default(self):
        af = get_age_factor(5, [])
        assert af["n_factor"] == 1.0

    @pytest.mark.golden
    def test_age_beyond_table_returns_default_silently(self, age_factors):
        """Audit issue: age 25 with max 20 returns neutral 1.0 factors with no
        warning. Locking in so the future 'warn above max' fix trips this test."""
        af = get_age_factor(25, age_factors)
        assert af == {"n_factor": 1.0, "p_factor": 1.0, "k_factor": 1.0, "general_factor": 1.0}


# ── generate_feeding_plan ──────────────────────────────────────────────────

class TestGenerateFeedingPlan:
    @pytest.mark.golden
    def test_total_items_matches_applications(self, nutrient_targets, avocado_growth_stages):
        items = generate_feeding_plan(
            nutrient_targets=nutrient_targets,
            growth_stages=avocado_growth_stages,
            crop_type="perennial",
            tree_age=8,
            age_factors=None,
        )
        # Stage 1 = 1 app, stage 2 = 2 apps, stage 3 = 2 apps  => 5 items
        assert len(items) == 5

    @pytest.mark.golden
    def test_stage_nutrients_sum_close_to_total(self, nutrient_targets, avocado_growth_stages):
        """Sum of n_kg_ha across items should round-trip close to total N target.

        Audit: rounding accumulates per-app so sums can drift below target.
        Current tolerance: within 1 kg of total. If the fix tightens this,
        update the assertion."""
        items = generate_feeding_plan(
            nutrient_targets=nutrient_targets,
            growth_stages=avocado_growth_stages,
            crop_type="annual",
            tree_age=None,
        )
        n_sum = sum(i["n_kg_ha"] for i in items)
        assert n_sum == pytest.approx(120.0, abs=1.0)

    @pytest.mark.golden
    def test_perennial_age_factor_applied(self, nutrient_targets, avocado_growth_stages, age_factors):
        items_mature = generate_feeding_plan(
            nutrient_targets=nutrient_targets,
            growth_stages=avocado_growth_stages,
            crop_type="perennial",
            tree_age=8,  # mature, factor 1.0
            age_factors=age_factors,
        )
        items_young = generate_feeding_plan(
            nutrient_targets=nutrient_targets,
            growth_stages=avocado_growth_stages,
            crop_type="perennial",
            tree_age=4,  # young, factor 0.6 for N
            age_factors=age_factors,
        )
        n_mature = sum(i["n_kg_ha"] for i in items_mature)
        n_young = sum(i["n_kg_ha"] for i in items_young)
        assert n_young < n_mature
        assert n_young == pytest.approx(n_mature * 0.6, abs=1.0)

    @pytest.mark.golden
    def test_annual_ignores_age_factor(self, nutrient_targets, avocado_growth_stages, age_factors):
        items = generate_feeding_plan(
            nutrient_targets=nutrient_targets,
            growth_stages=avocado_growth_stages,
            crop_type="annual",
            tree_age=4,
            age_factors=age_factors,
        )
        # Annual crops don't apply age factor even when one is passed
        n_sum = sum(i["n_kg_ha"] for i in items)
        assert n_sum == pytest.approx(120.0, abs=1.0)

    @pytest.mark.golden
    def test_mo_cu_distributed_across_stages(self, nutrient_targets, avocado_growth_stages):
        items = generate_feeding_plan(
            nutrient_targets=nutrient_targets,
            growth_stages=avocado_growth_stages,
            crop_type="annual",
        )
        mo_sum = sum(i["mo_kg_ha"] for i in items)
        # Mo target 0.05; distributed evenly across 3 stages then divided by apps
        # per stage. Rounding may drop it to ~0.04 or ~0.05.
        assert 0 < mo_sum <= 0.10

    @pytest.mark.golden
    def test_corrective_items_add_to_totals(self, nutrient_targets, avocado_growth_stages):
        corrective = [{"nutrient": "K", "annual_corrective_kg_ha": 60.0, "direction": "build-up"}]
        items = generate_feeding_plan(
            nutrient_targets=nutrient_targets,
            growth_stages=avocado_growth_stages,
            crop_type="annual",
            corrective_items=corrective,
        )
        k_sum = sum(i["k_kg_ha"] for i in items)
        # Base K 150 + corrective 60 = 210
        assert k_sum == pytest.approx(210.0, abs=1.5)

    @pytest.mark.golden
    def test_corrective_drawdown_does_not_subtract(self, nutrient_targets, avocado_growth_stages):
        """Audit quirk: corrective items with direction != 'build-up' are ignored."""
        corrective = [{"nutrient": "K", "annual_corrective_kg_ha": 60.0, "direction": "draw-down"}]
        items = generate_feeding_plan(
            nutrient_targets=nutrient_targets,
            growth_stages=avocado_growth_stages,
            crop_type="annual",
            corrective_items=corrective,
        )
        k_sum = sum(i["k_kg_ha"] for i in items)
        assert k_sum == pytest.approx(150.0, abs=1.0)

    @pytest.mark.golden
    def test_month_wrap_is_handled(self, nutrient_targets):
        """Stage crossing year boundary (Nov -> Feb) should still emit items."""
        wrap_stages = [{
            "stage_name": "Winter",
            "stage_order": 1,
            "month_start": 11, "month_end": 2,
            "num_applications": 2,
            "n_pct": 100, "p_pct": 100, "k_pct": 100,
            "ca_pct": 100, "mg_pct": 100, "s_pct": 100,
            "fe_pct": 100, "b_pct": 100, "mn_pct": 100, "zn_pct": 100,
            "default_method": "broadcast",
        }]
        items = generate_feeding_plan(
            nutrient_targets=nutrient_targets,
            growth_stages=wrap_stages,
            crop_type="annual",
        )
        assert len(items) == 2
        assert all(1 <= i["month_target"] <= 12 for i in items)


# ── build_practical_plan ───────────────────────────────────────────────────

class TestBuildPracticalPlan:
    @pytest.mark.golden
    def test_empty_months_returns_empty(self, nutrient_targets, avocado_growth_stages):
        items = generate_feeding_plan(nutrient_targets, avocado_growth_stages, crop_type="annual")
        assert build_practical_plan(items, application_months=[]) == []

    @pytest.mark.golden
    def test_groups_ideal_items_into_nearest_month(self, nutrient_targets, avocado_growth_stages):
        items = generate_feeding_plan(nutrient_targets, avocado_growth_stages, crop_type="annual")
        practical = build_practical_plan(items, application_months=[3, 6, 9, 12])
        # Total N delivered should match ideal N within rounding
        n_total = sum(p["n_kg_ha"] for p in practical)
        assert n_total == pytest.approx(120.0, abs=2.0)
        for p in practical:
            assert p["month"] in {3, 6, 9, 12}
            assert "npk_ratio" in p
            assert "blend_group" in p

    @pytest.mark.golden
    def test_single_month_collapses_all_nutrients(self, nutrient_targets, avocado_growth_stages):
        items = generate_feeding_plan(nutrient_targets, avocado_growth_stages, crop_type="annual")
        practical = build_practical_plan(items, application_months=[6])
        assert len(practical) == 1
        assert practical[0]["month"] == 6
        assert practical[0]["n_kg_ha"] == pytest.approx(120.0, abs=1.5)

    @pytest.mark.golden
    def test_blend_grouping_uses_letters(self, nutrient_targets, avocado_growth_stages):
        items = generate_feeding_plan(nutrient_targets, avocado_growth_stages, crop_type="annual")
        practical = build_practical_plan(items, application_months=[2, 5, 8, 11])
        letters = {p["blend_group"] for p in practical}
        assert all(len(L) == 1 and "A" <= L <= "Z" for L in letters)


# ── validate_methods ───────────────────────────────────────────────────────

class TestValidateMethods:
    @pytest.mark.golden
    def test_empty_crop_methods_returns_unchanged(self):
        items = [{"method": "broadcast"}]
        result = validate_methods(items, crop_methods=[])
        assert result == items

    @pytest.mark.golden
    def test_invalid_method_falls_back_to_default(self):
        items = [{"method": "spaceship"}]
        crop_methods = [
            {"method": "broadcast", "is_default": True},
            {"method": "fertigation", "is_default": False},
        ]
        result = validate_methods(items, crop_methods)
        assert result[0]["method"] == "broadcast"
        assert set(result[0]["available_methods"]) == {"broadcast", "fertigation"}

    @pytest.mark.golden
    def test_infrastructure_blocks_fertigation(self):
        items = [{"method": "fertigation"}]
        crop_methods = [
            {"method": "broadcast", "is_default": True},
            {"method": "fertigation", "is_default": False},
        ]
        result = validate_methods(items, crop_methods, infrastructure=[])
        assert result[0]["method"] == "broadcast"
        assert "fertigation" not in result[0]["available_methods"]

    @pytest.mark.golden
    def test_infrastructure_permits_fertigation_with_drip(self):
        items = [{"method": "fertigation"}]
        crop_methods = [
            {"method": "broadcast", "is_default": True},
            {"method": "fertigation", "is_default": False},
        ]
        result = validate_methods(items, crop_methods, infrastructure=["drip"])
        assert "fertigation" in result[0]["available_methods"]
        assert result[0]["method"] == "fertigation"
