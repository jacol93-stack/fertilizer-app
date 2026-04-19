"""Unit tests for the merge-as-composite helper (Phase 7).

Uses a tiny fake Supabase client that captures reads + updates so we can
verify the merged shape without hitting a real DB.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.routers.soil import _merge_incoming_into_existing


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, table: str, store: dict, captured_updates: list):
        self._table = table
        self._store = store
        self._captured = captured_updates
        self._filters: list = []
        self._op: str | None = None
        self._payload: dict | None = None

    def select(self, *_args, **_kwargs):
        self._op = "select"
        return self

    def update(self, payload: dict):
        self._op = "update"
        self._payload = payload
        return self

    def eq(self, col: str, val):
        self._filters.append((col, val))
        return self

    def execute(self):
        if self._op == "select":
            rows = self._store.get(self._table, [])
            out = [r for r in rows if all(r.get(c) == v for c, v in self._filters)]
            return _FakeResult(out)
        if self._op == "update":
            rows = self._store.get(self._table, [])
            updated = []
            for r in rows:
                if all(r.get(c) == v for c, v in self._filters):
                    r.update(self._payload or {})
                    updated.append(r)
            self._captured.append({"table": self._table, "payload": self._payload})
            return _FakeResult(updated)
        return _FakeResult([])


class _FakeSupabase:
    def __init__(self, store: dict):
        self._store = store
        self.captured_updates: list = []

    def table(self, name: str):
        return _FakeQuery(name, self._store, self.captured_updates)


def test_merge_promotes_legacy_single_sample_into_components():
    """An analysis row predating migration 040 (no component_samples) should
    be promoted into a two-component composite when an incoming sample
    merges in. No data loss."""
    sb = _FakeSupabase({
        "soil_analyses": [{
            "id": "A1",
            "soil_values": {"pH": 6.5, "P": 20.0},
            "component_samples": None,
            "composition_method": "single",
        }],
    })
    merged = _merge_incoming_into_existing(
        sb,
        existing_analysis_id="A1",
        incoming_soil_values={"pH": 6.2, "P": 25.0},
        incoming_components=None,
    )
    # Two components now: existing values + incoming
    assert merged["replicate_count"] == 2
    assert len(merged["component_samples"]) == 2
    assert merged["composition_method"] in ("composite_mean", "composite_area_weighted")
    # Values are the arithmetic mean (no weights supplied)
    assert merged["soil_values"]["pH"] == pytest.approx(6.35)
    assert merged["soil_values"]["P"] == pytest.approx(22.5)


def test_merge_appends_to_existing_components():
    """If the row already has components, merging appends without losing any."""
    sb = _FakeSupabase({
        "soil_analyses": [{
            "id": "A1",
            "soil_values": {"P": 20.0},
            "component_samples": [
                {"values": {"P": 10.0}, "weight_ha": 2.0},
                {"values": {"P": 30.0}, "weight_ha": 8.0},
            ],
            "composition_method": "composite_area_weighted",
        }],
    })
    merged = _merge_incoming_into_existing(
        sb,
        existing_analysis_id="A1",
        incoming_soil_values={"P": 50.0},
        incoming_components=None,
        default_weight_ha=10.0,
    )
    assert merged["replicate_count"] == 3
    # Area-weighted mean: (10*2 + 30*8 + 50*10) / 20 = 760 / 20 = 38
    assert merged["soil_values"]["P"] == pytest.approx(38.0)
    assert merged["composition_method"] == "composite_area_weighted"


def test_merge_falls_back_to_equal_when_any_weight_missing():
    """If even one component lacks a positive weight, the whole aggregation
    falls back to equal weighting."""
    sb = _FakeSupabase({
        "soil_analyses": [{
            "id": "A1",
            "soil_values": {"P": 20.0},
            "component_samples": [
                {"values": {"P": 10.0}, "weight_ha": 2.0},  # has weight
                {"values": {"P": 30.0}},                    # missing weight
            ],
            "composition_method": "composite_mean",
        }],
    })
    merged = _merge_incoming_into_existing(
        sb,
        existing_analysis_id="A1",
        incoming_soil_values={"P": 50.0},
        incoming_components=None,
        default_weight_ha=10.0,
    )
    # Equal weights: (10 + 30 + 50) / 3 = 30
    assert merged["soil_values"]["P"] == pytest.approx(30.0)
    assert merged["composition_method"] == "composite_mean"


def test_merge_accepts_incoming_multi_sample_payload():
    """Incoming can itself be a multi-sample composite — all its components
    are added to the existing record's list."""
    sb = _FakeSupabase({
        "soil_analyses": [{
            "id": "A1",
            "soil_values": {"P": 20.0},
            "component_samples": [{"values": {"P": 20.0}}],
            "composition_method": "single",
        }],
    })
    merged = _merge_incoming_into_existing(
        sb,
        existing_analysis_id="A1",
        incoming_soil_values={},  # ignored when components supplied
        incoming_components=[
            {"values": {"P": 10.0}},
            {"values": {"P": 30.0}},
        ],
    )
    assert merged["replicate_count"] == 3
    assert merged["soil_values"]["P"] == pytest.approx(20.0)


def test_merge_raises_when_target_missing():
    sb = _FakeSupabase({"soil_analyses": []})
    with pytest.raises(Exception):
        _merge_incoming_into_existing(
            sb,
            existing_analysis_id="nope",
            incoming_soil_values={"P": 10.0},
            incoming_components=None,
        )
