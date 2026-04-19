"""Unit tests for the field-analysis conflict helper in soil router.

Uses a tiny fake Supabase client that answers the two queries the helper
makes: `fields` by id (for latest_analysis_id, name) and `soil_analyses`
by id (for dates + crop). No DB required.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.routers.soil import _check_field_analysis_conflict


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, table: str, store: dict):
        self._table = table
        self._store = store
        self._filters: list[tuple[str, object]] = []

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, col: str, val):
        self._filters.append((col, val))
        return self

    def execute(self):
        rows = self._store.get(self._table, [])
        out = [r for r in rows if all(r.get(c) == v for c, v in self._filters)]
        return _FakeResult(out)


class _FakeSupabase:
    def __init__(self, store: dict):
        self._store = store

    def table(self, name: str):
        return _FakeQuery(name, self._store)


def _iso(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def test_returns_none_when_field_has_no_latest():
    sb = _FakeSupabase({
        "fields": [{"id": "F1", "name": "Block A", "latest_analysis_id": None}],
        "soil_analyses": [],
    })
    assert _check_field_analysis_conflict(sb, "F1") is None


def test_returns_none_when_field_unknown():
    sb = _FakeSupabase({"fields": [], "soil_analyses": []})
    assert _check_field_analysis_conflict(sb, "F1") is None


def test_returns_none_when_empty_field_id():
    sb = _FakeSupabase({"fields": [], "soil_analyses": []})
    assert _check_field_analysis_conflict(sb, "") is None


def test_returns_none_when_latest_is_old():
    sb = _FakeSupabase({
        "fields": [{"id": "F1", "name": "Block A", "latest_analysis_id": "A1"}],
        "soil_analyses": [{
            "id": "A1",
            "analysis_date": None,
            "created_at": _iso(days_ago=30),
            "crop": "maize",
        }],
    })
    assert _check_field_analysis_conflict(sb, "F1", window_days=7) is None


def test_returns_conflict_when_latest_is_recent():
    sb = _FakeSupabase({
        "fields": [{"id": "F1", "name": "Block A", "latest_analysis_id": "A1"}],
        "soil_analyses": [{
            "id": "A1",
            "analysis_date": None,
            "created_at": _iso(days_ago=2),
            "crop": "maize",
        }],
    })
    conflict = _check_field_analysis_conflict(sb, "F1", window_days=7)
    assert conflict is not None
    assert conflict["field_id"] == "F1"
    assert conflict["field_name"] == "Block A"
    assert conflict["existing"]["id"] == "A1"
    assert conflict["existing"]["crop"] == "maize"
    assert conflict["window_days"] == 7


def test_prefers_analysis_date_over_created_at():
    """If both dates are set, analysis_date wins (what the agronomist recorded)."""
    recent = datetime.now(timezone.utc).date().isoformat()
    sb = _FakeSupabase({
        "fields": [{"id": "F1", "name": "Block A", "latest_analysis_id": "A1"}],
        "soil_analyses": [{
            "id": "A1",
            "analysis_date": recent,
            "created_at": _iso(days_ago=90),
            "crop": "maize",
        }],
    })
    assert _check_field_analysis_conflict(sb, "F1", window_days=7) is not None


def test_respects_window_days_override():
    sb = _FakeSupabase({
        "fields": [{"id": "F1", "name": "Block A", "latest_analysis_id": "A1"}],
        "soil_analyses": [{
            "id": "A1",
            "analysis_date": None,
            "created_at": _iso(days_ago=14),
            "crop": "maize",
        }],
    })
    # Default 7d window: 14 days ago is out
    assert _check_field_analysis_conflict(sb, "F1", window_days=7) is None
    # Wider 30d window: same analysis now counts as a conflict
    assert _check_field_analysis_conflict(sb, "F1", window_days=30) is not None
