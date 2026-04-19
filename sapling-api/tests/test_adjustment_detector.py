"""Golden-case tests for adjustment_detector.

The detector's job is narrow: given old targets + new targets (or a
classifications dict for leaf), decide whether to raise a 'suggested'
adjustment, and what the delta snapshot looks like.

The pure functions (_compute_soil_delta, _targets_by_nutrient,
_summarise_soil_delta) don't touch Supabase — test them directly.
The router-level detect_soil_adjustment / detect_leaf_adjustment
integration tests need a live DB and live HTTP, deferred to the
integration pass.
"""

from __future__ import annotations

import pytest

from app.services.adjustment_detector import (
    _compute_soil_delta,
    _summarise_soil_delta,
    _targets_by_nutrient,
)


# ── _targets_by_nutrient ────────────────────────────────────────────────

def test_targets_by_nutrient_prefers_final_over_target():
    """Ratio-adjusted Final_Target_kg_ha should win over Target_kg_ha."""
    targets = [
        {"Nutrient": "N", "Target_kg_ha": 100.0, "Final_Target_kg_ha": 120.0},
        {"Nutrient": "K", "Target_kg_ha": 150.0},
    ]
    out = _targets_by_nutrient(targets)
    assert out == {"N": 120.0, "K": 150.0}


def test_targets_by_nutrient_accepts_lowercase_keys():
    """The cache can use either casing; handle both."""
    targets = [
        {"nutrient": "N", "target_kg_ha": 100.0},
    ]
    assert _targets_by_nutrient(targets) == {"N": 100.0}


def test_targets_by_nutrient_handles_none_and_bad_values():
    targets = [
        {"Nutrient": "N", "Target_kg_ha": 100.0},
        {"Nutrient": "P", "Target_kg_ha": None},
        {"Nutrient": "K", "Target_kg_ha": "not a number"},
        {"Nutrient": None, "Target_kg_ha": 50.0},  # nutrient missing
    ]
    out = _targets_by_nutrient(targets)
    assert out == {"N": 100.0}


def test_targets_by_nutrient_empty_cases():
    assert _targets_by_nutrient(None) == {}
    assert _targets_by_nutrient([]) == {}


# ── _compute_soil_delta ────────────────────────────────────────────────

def test_compute_delta_flags_above_margin():
    """N moved +25% (above 15% margin) → flag. P moved 10% → noise."""
    old = {"N": 100.0, "P": 20.0, "K": 150.0}
    new = {"N": 125.0, "P": 22.0, "K": 150.0}
    delta = _compute_soil_delta(old, new, margin_pct=15.0)
    assert len(delta) == 1
    assert delta[0]["nutrient"] == "N"
    assert delta[0]["direction"] == "increase"
    assert delta[0]["change_pct"] == 25.0


def test_compute_delta_flags_decrease():
    old = {"K": 200.0}
    new = {"K": 150.0}  # -25%
    delta = _compute_soil_delta(old, new, margin_pct=15.0)
    assert len(delta) == 1
    assert delta[0]["direction"] == "decrease"
    assert delta[0]["change_pct"] == -25.0


def test_compute_delta_exactly_at_margin_triggers():
    """Exactly at margin should trigger (>= comparison) — prevents a
    boundary case where the detector silently ignores a move exactly
    at the threshold."""
    old = {"N": 100.0}
    new = {"N": 115.0}  # exactly +15%
    delta = _compute_soil_delta(old, new, margin_pct=15.0)
    assert len(delta) == 1
    assert delta[0]["change_pct"] == 15.0


def test_compute_delta_new_nutrient_introduced():
    """Old=0 new>0 is a new requirement — flag as 'introduced'."""
    old = {"N": 100.0}
    new = {"N": 100.0, "Zn": 2.5}
    delta = _compute_soil_delta(old, new, margin_pct=15.0)
    zn_entry = next(d for d in delta if d["nutrient"] == "Zn")
    assert zn_entry["direction"] == "introduced"
    assert zn_entry["change_pct"] is None


def test_compute_delta_nutrient_removed():
    """Old>0 new=0 means this nutrient no longer needed — flag as 'removed'."""
    old = {"N": 100.0, "Zn": 2.5}
    new = {"N": 100.0}
    delta = _compute_soil_delta(old, new, margin_pct=15.0)
    zn_entry = next(d for d in delta if d["nutrient"] == "Zn")
    assert zn_entry["direction"] == "removed"
    assert zn_entry["new_kg_ha"] == 0.0


def test_compute_delta_ignores_zero_to_zero():
    """Micros often not required — don't spuriously flag 0 → 0."""
    old = {"Mo": 0.0, "Cu": 0.0}
    new = {"Mo": 0.0, "Cu": 0.0}
    assert _compute_soil_delta(old, new, margin_pct=15.0) == []


def test_compute_delta_empty_inputs():
    assert _compute_soil_delta({}, {}, margin_pct=15.0) == []
    assert _compute_soil_delta({"N": 100.0}, {}, margin_pct=15.0)[0]["direction"] == "removed"


def test_compute_delta_custom_margin():
    """A stricter 5% margin catches smaller moves that 15% ignores."""
    old = {"N": 100.0, "P": 20.0}
    new = {"N": 108.0, "P": 22.0}  # N +8%, P +10%
    strict = _compute_soil_delta(old, new, margin_pct=5.0)
    loose = _compute_soil_delta(old, new, margin_pct=15.0)
    assert len(strict) == 2
    assert len(loose) == 0


# ── _summarise_soil_delta ────────────────────────────────────────────────

def test_summary_renders_increases_and_decreases():
    delta = [
        {"nutrient": "N", "direction": "increase", "change_pct": 25.0, "old_kg_ha": 100, "new_kg_ha": 125},
        {"nutrient": "K", "direction": "decrease", "change_pct": -30.0, "old_kg_ha": 200, "new_kg_ha": 140},
    ]
    s = _summarise_soil_delta(delta)
    assert "N +25.0%" in s
    assert "K -30.0%" in s


def test_summary_handles_introduced_and_removed():
    delta = [
        {"nutrient": "Zn", "direction": "introduced", "change_pct": None, "old_kg_ha": 0, "new_kg_ha": 2.5},
        {"nutrient": "B", "direction": "removed", "change_pct": -100.0, "old_kg_ha": 1.5, "new_kg_ha": 0},
    ]
    s = _summarise_soil_delta(delta)
    assert "newly required: Zn" in s
    assert "no longer needed: B" in s


def test_summary_empty_delta():
    assert _summarise_soil_delta([]) == "No meaningful change"
