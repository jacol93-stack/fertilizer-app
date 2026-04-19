"""Unit tests for the plan-compare pure helpers.

Full compare_plan is integration-tested against live Supabase in the
development scripts; these cover the diffing logic end users see in
the comparison UI.
"""

from __future__ import annotations

import pytest

from app.services.plan_compare import (
    _applied_nutrients,
    _build_attributions,
    _nut_equal,
    _nuts,
    _per_month_diff,
    _rates_equal,
    _season_totals,
)


# ── _nuts ──────────────────────────────────────────────────────────────


def test_nuts_extracts_lowercase_keys():
    b = {"blend_nutrients": {"N": 20, "K": 40, "Zn": 1.5, "garbage": 10}}
    assert _nuts(b) == {"n": 20.0, "k": 40.0, "zn": 1.5}


def test_nuts_empty_cases():
    assert _nuts(None) == {}
    assert _nuts({}) == {}
    assert _nuts({"blend_nutrients": None}) == {}
    assert _nuts({"blend_nutrients": {}}) == {}


# ── _nut_equal / _rates_equal ──────────────────────────────────────────


def test_nut_equal_within_tolerance():
    assert _nut_equal({"n": 20}, {"n": 20.04})
    assert not _nut_equal({"n": 20}, {"n": 21})


def test_nut_equal_different_key_sets():
    """If the current plan added a new nutrient not in baseline, they
    should compare as different."""
    assert not _nut_equal({"n": 20}, {"n": 20, "zn": 1})


def test_rates_equal_tolerance():
    assert _rates_equal({"rate_kg_ha": 100}, {"rate_kg_ha": 100.3})
    assert not _rates_equal({"rate_kg_ha": 100}, {"rate_kg_ha": 105})


# ── _per_month_diff ─────────────────────────────────────────────────────


def _blend(month: int, n: float, k: float, rate: float = 100, bid: str = "x"):
    return {
        "id": bid,
        "application_month": month,
        "rate_kg_ha": rate,
        "blend_nutrients": {"n": n, "k": k},
        "stage_name": f"m{month}",
    }


def test_per_month_unchanged_when_baseline_matches_current():
    baseline = [_blend(5, 20, 40, bid="b1")]
    current = [_blend(5, 20, 40, bid="b1")]
    rows = _per_month_diff(baseline, current, [])
    assert len(rows) == 1
    assert rows[0]["status"] == "unchanged"
    assert rows[0]["nutrient_delta"] == {}


def test_per_month_edited_when_nutrients_differ():
    baseline = [_blend(5, 20, 40, bid="b1")]
    current = [_blend(5, 30, 40, bid="b1")]
    rows = _per_month_diff(baseline, current, [])
    assert rows[0]["status"] == "edited"
    assert rows[0]["nutrient_delta"]["n"] == pytest.approx(10.0)


def test_per_month_added_and_removed():
    baseline = [_blend(5, 20, 40)]
    current = [_blend(7, 30, 50)]
    rows = _per_month_diff(baseline, current, [])
    by_month = {r["month"]: r for r in rows}
    assert by_month[5]["status"] == "removed"
    assert by_month[5]["nutrient_delta"]["n"] == pytest.approx(-20.0)
    assert by_month[7]["status"] == "added"
    assert by_month[7]["nutrient_delta"]["n"] == pytest.approx(30.0)


def test_per_month_applied_only_shows_with_no_plan_entry():
    """An actual in month 6 with neither a baseline nor a current entry
    for that month (eg a purely off-plan application) still appears."""
    baseline = [_blend(5, 20, 40)]
    current = [_blend(5, 20, 40)]
    apps = [{
        "id": "a1", "actual_date": "2026-06-14",
        "actual_rate_kg_ha": 150, "product_name": "LAN",
        "status": "applied", "planned_blend_id": None,
    }]
    rows = _per_month_diff(baseline, current, apps)
    by_month = {r["month"]: r for r in rows}
    assert by_month[6]["status"] == "applied_only"
    assert len(by_month[6]["actual"]) == 1


# ── _season_totals ────────────────────────────────────────────────────


def test_season_totals_sums_each_source():
    baseline = [_blend(5, 20, 40), _blend(7, 30, 50)]
    current = [_blend(5, 25, 40), _blend(7, 30, 50)]
    apps = [{
        "status": "applied",
        "nutrients_delivered": {"n": 10, "k": 15},
    }]
    out = _season_totals(baseline, current, apps)
    assert out["baseline"]["n"] == 50.0
    assert out["current"]["n"] == 55.0
    assert out["applied"]["n"] == 10.0


def test_season_totals_skips_non_applied_actuals():
    """Pending / skipped applications shouldn't count toward applied."""
    apps = [
        {"status": "pending", "nutrients_delivered": {"n": 100}},
        {"status": "skipped", "nutrients_delivered": {"n": 100}},
    ]
    out = _season_totals([], [], apps)
    assert out["applied"] == {}


# ── _applied_nutrients ────────────────────────────────────────────────


def test_applied_nutrients_explicit_preferred():
    app = {"nutrients_delivered": {"N": 25, "K": 30}}
    assert _applied_nutrients(app, {}) == {"n": 25.0, "k": 30.0}


def test_applied_nutrients_scales_via_linked_blend():
    blend = {"id": "b1", "blend_nutrients": {"n": 20}, "rate_kg_ha": 100}
    app = {"planned_blend_id": "b1", "actual_rate_kg_ha": 150}
    out = _applied_nutrients(app, {"b1": blend})
    assert out["n"] == pytest.approx(30.0)


# ── _build_attributions ───────────────────────────────────────────────


def test_build_attributions_picks_applied_adjustments():
    adj = [{
        "id": "adj-1", "trigger_type": "soil_analysis",
        "applied_at": "2026-06-01T00:00:00Z",
        "applied_by": "user-1",
        "notes": "Soil delta bumped N +30%",
    }]
    out = _build_attributions(adj)
    assert len(out) == 1
    assert out[0]["kind"] == "soil_analysis"
    assert out[0]["summary"] == "Soil delta bumped N +30%"
    assert out[0]["actor"] == "user-1"
