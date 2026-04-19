"""Golden-case tests for the pure-function parts of adjustment_proposer.

Focuses on _nut_of, _rate_from_nutrients, and the full propose flow
with a mocked supabase. The real DB-dependent paths
(propose_from_adjustment → _propose_soil → _propose_leaf) use a
hand-rolled fake supabase so the tests don't need network.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.services.adjustment_proposer import (
    _nut_of,
    _rate_from_nutrients,
    propose_from_adjustment,
)


def test_nut_of_handles_missing_and_bad_values():
    assert _nut_of({}, "n") == 0.0
    assert _nut_of({"blend_nutrients": None}, "n") == 0.0
    assert _nut_of({"blend_nutrients": {"n": None}}, "n") == 0.0
    assert _nut_of({"blend_nutrients": {"n": "abc"}}, "n") == 0.0
    assert _nut_of({"blend_nutrients": {"n": 42.5}}, "n") == 42.5


def test_rate_from_nutrients_at_25pct_density():
    """25% density → rate = total / 0.25. A blend delivering 30 kg
    total nutrient applies at 120 kg/ha to deliver it."""
    rate = _rate_from_nutrients({"n": 20, "p": 5, "k": 5})
    assert rate == 120.0


def test_rate_from_nutrients_empty_returns_zero():
    assert _rate_from_nutrients({}) == 0.0
    assert _rate_from_nutrients({"n": 0, "p": 0}) == 0.0


def test_rate_from_nutrients_custom_density():
    """Higher density → less product needed."""
    rate = _rate_from_nutrients({"n": 40}, density_pct=40.0)
    assert rate == 100.0


# ── Fake supabase client used by proposer tests ────────────────────────

class FakeQuery:
    """Minimal chainable query builder that records filters and returns
    pre-seeded rows."""
    def __init__(self, rows: list[dict]):
        self._rows = rows
        self._filters: list[tuple] = []

    def select(self, *_, **__):
        return self

    def eq(self, col, val):
        self._filters.append(("eq", col, val))
        return self

    def limit(self, _n):
        return self

    def order(self, *_, **__):
        return self

    def execute(self):
        data = list(self._rows)
        for op, col, val in self._filters:
            if op == "eq":
                data = [r for r in data if r.get(col) == val]
        return MagicMock(data=data, count=len(data))


class FakeSupabase:
    def __init__(self, tables: dict[str, list[dict]]):
        self._tables = tables

    def table(self, name: str):
        return FakeQuery(self._tables.get(name, []))


# ── propose_from_adjustment ────────────────────────────────────────────

def _build_programme_fixture(current_month: int):
    """Avocado-ish programme with 5 remaining blends; N is 20 kg/ha
    per blend (100 total), K is 40 kg/ha per blend (200 total)."""
    blends = []
    for i, month in enumerate([max(1, current_month + 1), current_month + 2,
                                current_month + 3, current_month + 4,
                                current_month + 5]):
        blends.append({
            "id": f"blend-{i+1}",
            "programme_id": "prog-1",
            "blend_group": "A",
            "stage_name": f"Stage {i+1}",
            "application_month": month if month <= 12 else month - 12,
            "blend_nutrients": {"n": 20.0, "p": 5.0, "k": 40.0},
            "rate_kg_ha": 260.0,
        })

    return {
        "programme_adjustments": [{
            "id": "adj-1",
            "programme_id": "prog-1",
            "block_id": "block-1",
            "trigger_type": "soil_analysis",
            "trigger_id": "sa-new",
            "adjustment_data": {
                "action": "update_targets",
                "delta": [
                    # N was 100 total, now 140 total (+40%)
                    {"nutrient": "N", "old_kg_ha": 100.0, "new_kg_ha": 140.0,
                     "change_pct": 40.0, "direction": "increase"},
                    # K was 200 total, now 150 total (-25%)
                    {"nutrient": "K", "old_kg_ha": 200.0, "new_kg_ha": 150.0,
                     "change_pct": -25.0, "direction": "decrease"},
                ],
            },
        }],
        "programme_blends": blends,
        "programme_applications": [],
        "programme_blocks": [{"id": "block-1", "blend_group": "A"}],
    }


def test_proposer_scales_affected_nutrients_only():
    """N and K are in the delta; P should not move."""
    current = datetime.now(timezone.utc).month
    # Avoid clash with the past-month heuristic by using a month in the future
    # inside the fixture itself.
    tables = _build_programme_fixture(current)
    sb = FakeSupabase(tables)

    result = propose_from_adjustment(sb, "adj-1")
    affected = result["affected_blends"]
    summary = result["summary"]

    assert summary["affected_count"] == 5
    assert "n" in summary["scale_factors"]
    assert "k" in summary["scale_factors"]
    # +40% on N → factor 1.4. -25% on K → factor 0.75.
    assert abs(summary["scale_factors"]["n"] - 1.4) < 0.01
    assert abs(summary["scale_factors"]["k"] - 0.75) < 0.01

    # Spot check one blend: N 20 → 28, K 40 → 30, P unchanged at 5
    first = affected[0]
    assert first["new"]["nutrients"]["n"] == 28.0
    assert first["new"]["nutrients"]["k"] == 30.0
    assert first["new"]["nutrients"]["p"] == 5.0


def test_proposer_season_totals_match_new_targets():
    """Summed remaining N across 5 blends should equal the new target
    (140 kg/ha total) when nothing has been applied yet."""
    current = datetime.now(timezone.utc).month
    tables = _build_programme_fixture(current)
    sb = FakeSupabase(tables)

    result = propose_from_adjustment(sb, "adj-1")
    new_total = result["summary"]["season_totals"]["new"]

    assert abs(new_total["n"] - 140.0) < 0.5
    assert abs(new_total["k"] - 150.0) < 0.5


def test_proposer_returns_empty_if_adjustment_missing():
    sb = FakeSupabase({})
    result = propose_from_adjustment(sb, "does-not-exist")
    assert result == {"error": "adjustment_not_found"}


def test_proposer_leaf_trigger_returns_foliar_recommendation():
    tables = {
        "programme_adjustments": [{
            "id": "adj-leaf",
            "programme_id": "prog-1",
            "block_id": "block-1",
            "trigger_type": "leaf_analysis",
            "adjustment_data": {
                "action": "foliar_correction_recommended",
                "deficient_elements": ["Zn", "B"],
                "excess_elements": [],
                "foliar_recommendations": [{"product": "Zn-B tonic", "rate_l_ha": 2.0}],
            },
        }],
    }
    sb = FakeSupabase(tables)
    result = propose_from_adjustment(sb, "adj-leaf")

    assert result["summary"]["kind"] == "foliar_correction"
    assert result["summary"]["deficient_count"] == 2
    assert result["proposed_foliar"]["deficient_elements"] == ["Zn", "B"]
