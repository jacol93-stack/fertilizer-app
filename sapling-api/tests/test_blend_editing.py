"""Unit tests for the blend-editing pure helpers in routers/programmes.

Exercises the sanitation + change-summary logic without hitting
Supabase. End-to-end coverage of the DB paths lives in the ad-hoc
integration scripts (see development notes); the router handlers are
thin wrappers around the sanitiser and the plan_validator, both of
which have their own tests.
"""

from __future__ import annotations

import pytest

from app.routers.programmes import _sanitize_nutrients, _summarise_change


# ── _sanitize_nutrients ────────────────────────────────────────────────


def test_sanitize_keeps_valid_lowercased_keys():
    out = _sanitize_nutrients({"N": 20, "K": 50, "Zn": 1.5})
    assert out == {"n": 20.0, "k": 50.0, "zn": 1.5}


def test_sanitize_drops_unknown_keys():
    """Only the 12 nutrients we track are accepted. Anything else is
    silently stripped to protect the downstream validator."""
    out = _sanitize_nutrients({"n": 10, "garbage": 5, "xx": 1})
    assert out == {"n": 10.0}


def test_sanitize_drops_negatives():
    out = _sanitize_nutrients({"n": -5, "k": 30})
    assert out == {"k": 30.0}


def test_sanitize_coerces_strings_and_drops_non_numeric():
    out = _sanitize_nutrients({"n": "20", "k": "abc"})
    assert out == {"n": 20.0}


def test_sanitize_returns_none_unchanged():
    assert _sanitize_nutrients(None) is None


def test_sanitize_empty_dict_returns_empty():
    assert _sanitize_nutrients({}) == {}


def test_sanitize_rounds_to_three_places():
    """Keep blend_nutrients tidy — JSONB storage doesn't need 15
    decimals."""
    out = _sanitize_nutrients({"n": 20.123456789})
    assert out == {"n": 20.123}


# ── _summarise_change ─────────────────────────────────────────────────


def _fb(planned_map: dict, warnings_count: int = 0, under=0, over=0) -> dict:
    """Minimal validator-output fixture."""
    return {
        "season_totals": {"planned": planned_map},
        "warnings": [None] * warnings_count,
        "summary": {"under_target_count": under, "over_target_count": over},
    }


def test_summarise_highlights_nutrients_that_moved():
    current = _fb({"n": 100, "p": 30, "k": 150})
    proposed = _fb({"n": 140, "p": 30, "k": 120})
    out = _summarise_change(current, proposed)

    movers = {c["nutrient"]: c for c in out["changed_nutrients"]}
    assert set(movers.keys()) == {"n", "k"}  # p didn't move
    assert movers["n"]["delta_kg_ha"] == pytest.approx(40.0)
    assert movers["k"]["delta_kg_ha"] == pytest.approx(-30.0)


def test_summarise_ignores_subkg_noise():
    """A 0.04 kg/ha wobble (below 0.05 threshold) shouldn't clutter
    the diff."""
    current = _fb({"n": 100.0})
    proposed = _fb({"n": 100.04})
    out = _summarise_change(current, proposed)
    assert out["changed_nutrients"] == []


def test_summarise_reports_warning_and_status_deltas():
    """Edit takes two nutrients out of under_target and introduces one
    over_target — the UI needs all three numbers to show the trade-off."""
    current = _fb({"n": 100}, warnings_count=3, under=2, over=0)
    proposed = _fb({"n": 140}, warnings_count=2, under=0, over=1)
    out = _summarise_change(current, proposed)

    assert out["warnings_before"] == 3
    assert out["warnings_after"] == 2
    assert out["status_change"]["under_before"] == 2
    assert out["status_change"]["under_after"] == 0
    assert out["status_change"]["over_before"] == 0
    assert out["status_change"]["over_after"] == 1


def test_summarise_handles_newly_appearing_nutrient():
    """A nutrient not in the current plan but added by the edit should
    appear in the diff with before=0."""
    current = _fb({"n": 100})
    proposed = _fb({"n": 100, "zn": 2.0})
    out = _summarise_change(current, proposed)
    zn = next(c for c in out["changed_nutrients"] if c["nutrient"] == "zn")
    assert zn["before"] == 0.0
    assert zn["after"] == 2.0
    assert zn["delta_kg_ha"] == 2.0


def test_summarise_handles_removed_nutrient():
    """A nutrient removed by the edit should show before>0, after=0."""
    current = _fb({"n": 100, "zn": 2.0})
    proposed = _fb({"n": 100})
    out = _summarise_change(current, proposed)
    zn = next(c for c in out["changed_nutrients"] if c["nutrient"] == "zn")
    assert zn["before"] == 2.0
    assert zn["after"] == 0.0
    assert zn["delta_kg_ha"] == -2.0
