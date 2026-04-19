"""Unit tests for plan_validator — the feedback engine.

Covers:
- Target normalisation (JSONB list shape + plain dict)
- Per-nutrient sum across plan_blends (blend_nutrients dict + feeding
  plan item shape)
- Applied-nutrient attribution (explicit, recipe-scaled, or empty)
- Status classification (under/on_target/over) with tolerance band
- Leaf flags (addressed vs not, element name variations)
- Structural warnings (empty plan, blend with no nutrients)
"""

from __future__ import annotations

import pytest

from app.services.plan_validator import (
    NUTRIENT_KEYS,
    _applied_nutrients,
    _leaf_flags,
    _normalise_targets,
    _nutrients_of,
    _status_for,
    validate_plan,
)


# ── _normalise_targets ─────────────────────────────────────────────────


def test_normalise_targets_accepts_jsonb_shape():
    targets = [
        {"Nutrient": "N", "Final_Target_kg_ha": 120.0, "Target_kg_ha": 100.0},
        {"Nutrient": "K", "Target_kg_ha": 150.0},
    ]
    out = _normalise_targets(targets)
    # Keys must be lowercased; Final_ preferred over Target_
    assert out == {"n": 120.0, "k": 150.0}


def test_normalise_targets_accepts_plain_dict():
    out = _normalise_targets({"N": 100, "K": 150, "Mg": 20})
    assert out == {"n": 100.0, "k": 150.0, "mg": 20.0}


def test_normalise_targets_handles_none_and_empty():
    assert _normalise_targets(None) == {}
    assert _normalise_targets([]) == {}
    assert _normalise_targets({}) == {}


# ── _nutrients_of ───────────────────────────────────────────────────────


def test_nutrients_of_blend_nutrients_dict():
    blend = {"blend_nutrients": {"n": 20, "p": 5, "K": 40}}
    out = _nutrients_of(blend)
    assert out == {"n": 20.0, "p": 5.0, "k": 40.0}


def test_nutrients_of_feeding_item_shape():
    blend = {"n_kg_ha": 30.0, "k_kg_ha": 50.0, "blend_nutrients": {}}
    out = _nutrients_of(blend)
    assert out["n"] == 30.0 and out["k"] == 50.0


def test_nutrients_of_empty_blend():
    assert _nutrients_of({}) == {}
    assert _nutrients_of({"blend_nutrients": None}) == {}


# ── _applied_nutrients ─────────────────────────────────────────────────


def test_applied_nutrients_explicit_wins():
    """If the app row has nutrients_delivered, use it verbatim."""
    app = {"nutrients_delivered": {"n": 25, "k": 30}}
    out = _applied_nutrients(app, blend_by_id={})
    assert out == {"n": 25.0, "k": 30.0}


def test_applied_nutrients_scales_recipe_by_rate_ratio():
    """actual_rate / planned_rate scales the recipe."""
    blend = {"id": "b1", "blend_nutrients": {"n": 20, "k": 40}, "rate_kg_ha": 100}
    app = {"planned_blend_id": "b1", "actual_rate_kg_ha": 150}  # 1.5x
    out = _applied_nutrients(app, blend_by_id={"b1": blend})
    assert out["n"] == pytest.approx(30.0)
    assert out["k"] == pytest.approx(60.0)


def test_applied_nutrients_falls_back_to_plan_intent_when_rate_missing():
    """No actual_rate on the app → fall back to what the plan intended."""
    blend = {"id": "b1", "blend_nutrients": {"n": 20}, "rate_kg_ha": 100}
    app = {"planned_blend_id": "b1"}
    out = _applied_nutrients(app, blend_by_id={"b1": blend})
    assert out["n"] == 20.0


def test_applied_nutrients_unattributable_returns_empty():
    """No explicit and no planned_blend link → empty (can't attribute)."""
    app = {"actual_rate_kg_ha": 100}
    assert _applied_nutrients(app, blend_by_id={}) == {}


# ── _status_for ────────────────────────────────────────────────────────


def test_status_within_tolerance_is_on_target():
    # 10% tolerance: target 100, delivered 95 → on_target (within -10%)
    assert _status_for(100, 95, tol_pct=10.0) == "on_target"
    assert _status_for(100, 105, tol_pct=10.0) == "on_target"


def test_status_outside_tolerance():
    assert _status_for(100, 85, tol_pct=10.0) == "under"
    assert _status_for(100, 120, tol_pct=10.0) == "over"


def test_status_tolerance_boundary():
    """Exactly at the tolerance edge counts as on_target."""
    assert _status_for(100, 90, tol_pct=10.0) == "on_target"
    assert _status_for(100, 110, tol_pct=10.0) == "on_target"


# ── _leaf_flags ────────────────────────────────────────────────────────


def test_leaf_flags_deficient_unaddressed_when_plan_delivers_zero():
    flags = _leaf_flags({"Zn": "Deficient"}, delivered={"zn": 0})
    assert len(flags) == 1
    assert flags[0]["nutrient_key"] == "zn"
    assert flags[0]["addressed"] is False
    assert flags[0]["suggested_action"] == "add_application"


def test_leaf_flags_deficient_addressed_when_plan_delivers_it():
    flags = _leaf_flags({"Zn": "Deficient"}, delivered={"zn": 2.0})
    assert flags[0]["addressed"] is True


def test_leaf_flags_excess_suggests_reducing():
    flags = _leaf_flags({"K": "Excess"}, delivered={"k": 100})
    assert flags[0]["suggested_action"] == "reduce_supply"


def test_leaf_flags_ignores_sufficient_classification():
    """Only Deficient / Low / Excess / Toxic are flagged."""
    flags = _leaf_flags({"N": "Sufficient", "K": "Optimal"}, delivered={})
    assert flags == []


def test_leaf_flags_accepts_full_element_names():
    """'Potassium' should map to 'k'."""
    flags = _leaf_flags({"Potassium": "Deficient", "Zinc": "Low"}, delivered={"k": 0, "zn": 1.0})
    keys = {f["nutrient_key"] for f in flags}
    assert keys == {"k", "zn"}
    k_flag = next(f for f in flags if f["nutrient_key"] == "k")
    zn_flag = next(f for f in flags if f["nutrient_key"] == "zn")
    assert k_flag["addressed"] is False
    assert zn_flag["addressed"] is True


# ── validate_plan end-to-end ────────────────────────────────────────────


@pytest.fixture
def citrus_plan():
    """Five applications delivering 100 N, 30 P, 150 K over the season."""
    return [
        {"id": f"b{i}", "application_month": m,
         "blend_nutrients": {"n": 20, "p": 6, "k": 30}, "rate_kg_ha": 224}
        for i, m in enumerate([5, 7, 9, 11, 2])
    ]


def test_validate_on_target_plan_has_no_under_over_warnings(citrus_plan):
    targets = {"N": 100, "P": 30, "K": 150}
    result = validate_plan(plan_blends=citrus_plan, nutrient_targets=targets)

    assert result["summary"]["under_target_count"] == 0
    assert result["summary"]["over_target_count"] == 0
    assert result["summary"]["on_target_count"] == 3

    under_warnings = [w for w in result["warnings"] if w["kind"] == "under_target"]
    assert under_warnings == []


def test_validate_under_target_flags_nutrient(citrus_plan):
    """Plan delivers 100N, target says 150 — 33% short, flag as high severity."""
    targets = {"N": 150, "P": 30, "K": 150}
    result = validate_plan(plan_blends=citrus_plan, nutrient_targets=targets)

    n_row = next(r for r in result["per_nutrient"] if r["nutrient"] == "n")
    assert n_row["status"] == "under"
    assert n_row["delta_kg_ha"] == pytest.approx(-50.0)
    assert n_row["pct_of_target"] == pytest.approx(66.7, abs=0.5)

    warn = next(w for w in result["warnings"] if w["kind"] == "under_target" and w["nutrient"] == "n")
    assert warn["severity"] == "high"


def test_validate_over_target_flags_nutrient(citrus_plan):
    """Plan delivers 150K, target 50 — 3x, flag as high severity."""
    targets = {"N": 100, "P": 30, "K": 50}
    result = validate_plan(plan_blends=citrus_plan, nutrient_targets=targets)
    k_row = next(r for r in result["per_nutrient"] if r["nutrient"] == "k")
    assert k_row["status"] == "over"
    assert k_row["delta_kg_ha"] == pytest.approx(100.0)


def test_validate_with_applied_actuals_counts_toward_delivered(citrus_plan):
    """Applied 50N from the first application → delivered should be
    100 (planned) regardless, but applied should reflect the 50."""
    targets = {"N": 100, "P": 30, "K": 150}
    applications = [
        {
            "status": "applied",
            "planned_blend_id": "b0",
            "actual_rate_kg_ha": 300,  # 1.34× the planned 224 — extra N
            "block_id": None,
        },
    ]
    result = validate_plan(
        plan_blends=citrus_plan,
        nutrient_targets=targets,
        applications_applied=applications,
    )
    # applied[n] should be roughly 20 * 300/224 ≈ 26.8 from the actual,
    # plus the 20 planned remains in planned. delivered ≈ planned + applied.
    season = result["season_totals"]
    assert season["applied"]["n"] > 26.0
    # delivered for N is sum of plan + applied — sanity check > plan alone
    assert season["delivered"]["n"] > season["planned"]["n"]


def test_validate_no_targets_skips_comparison(citrus_plan):
    """When no targets available (manual build with no soil data),
    still return structural info but no under/over warnings."""
    result = validate_plan(plan_blends=citrus_plan, nutrient_targets=None)

    assert result["summary"]["has_targets"] is False
    assert result["summary"]["under_target_count"] == 0
    assert result["summary"]["over_target_count"] == 0
    # All per_nutrient rows should have status='no_target'
    assert all(r["status"] == "no_target" for r in result["per_nutrient"])


def test_validate_empty_plan_warns():
    result = validate_plan(plan_blends=[], nutrient_targets={"N": 100})
    empty_w = [w for w in result["warnings"] if w["kind"] == "empty_plan"]
    assert len(empty_w) == 1
    assert empty_w[0]["severity"] == "high"


def test_validate_blend_with_no_nutrients_warns(citrus_plan):
    bad = [{"id": "empty", "application_month": 3, "blend_nutrients": {},
            "stage_name": "Stage X"}]
    result = validate_plan(plan_blends=bad, nutrient_targets=None)
    w = [w for w in result["warnings"] if w["kind"] == "blend_no_nutrients"]
    assert len(w) == 1
    assert "Stage X" in w[0]["message"]


def test_validate_leaf_deficiency_unaddressed_generates_high_warning(citrus_plan):
    """Plan doesn't deliver Zn; leaf says Zn Deficient → unaddressed flag."""
    result = validate_plan(
        plan_blends=citrus_plan,
        nutrient_targets=None,
        leaf_classifications={"Zn": "Deficient"},
    )
    assert result["summary"]["unaddressed_leaf_count"] == 1
    zn_flag = next(f for f in result["leaf_flags"] if f["nutrient_key"] == "zn")
    assert zn_flag["addressed"] is False
    assert any(w["kind"] == "unaddressed_leaf" for w in result["warnings"])


def test_validate_leaf_deficiency_addressed_not_warned(citrus_plan):
    """Plan delivers some Zn → deficiency considered addressed."""
    plan_with_zn = [
        dict(b, blend_nutrients={**b["blend_nutrients"], "zn": 1.0}) for b in citrus_plan
    ]
    result = validate_plan(
        plan_blends=plan_with_zn,
        nutrient_targets=None,
        leaf_classifications={"Zn": "Deficient"},
    )
    zn_flag = next(f for f in result["leaf_flags"] if f["nutrient_key"] == "zn")
    assert zn_flag["addressed"] is True
    assert result["summary"]["unaddressed_leaf_count"] == 0


def test_validate_custom_tolerance():
    """Strict 2% tolerance flags a plan that 10% would pass."""
    plan = [{"id": "b", "blend_nutrients": {"n": 95}}]
    targets = {"N": 100}
    loose = validate_plan(plan_blends=plan, nutrient_targets=targets, tolerance_pct=10.0)
    strict = validate_plan(plan_blends=plan, nutrient_targets=targets, tolerance_pct=2.0)

    assert loose["summary"]["on_target_count"] == 1
    assert strict["summary"]["under_target_count"] == 1
