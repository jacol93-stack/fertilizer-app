"""Unit tests for app/pagination.py.

Covers the helpers that wrap Supabase query builders into a Page[T]
envelope. The Supabase client is stubbed with a tiny fake that records
calls — no network dependency.
"""

from __future__ import annotations

import pytest

from app.pagination import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    Page,
    PageParams,
    apply_page,
)


# ── PageParams ────────────────────────────────────────────────────────────

class TestPageParams:
    @pytest.mark.golden
    def test_defaults(self):
        p = PageParams()
        assert p.skip == 0
        assert p.limit == DEFAULT_LIMIT
        assert p.order_by is None
        assert p.order_desc is True

    @pytest.mark.golden
    def test_as_query_constructor(self):
        p = PageParams.as_query(skip=40, limit=50, order_by="name", order_desc=False)
        assert p.skip == 40
        assert p.limit == 50
        assert p.order_by == "name"
        assert p.order_desc is False

    @pytest.mark.golden
    def test_limit_cap_enforced_on_model(self):
        """Pydantic Field(le=MAX_LIMIT) rejects over-cap inputs."""
        with pytest.raises(ValueError):
            PageParams(limit=MAX_LIMIT + 1)

    @pytest.mark.golden
    def test_negative_skip_rejected(self):
        with pytest.raises(ValueError):
            PageParams(skip=-1)


# ── Page envelope ─────────────────────────────────────────────────────────

class _FakeResult:
    """Mimics the supabase-py result object (has .data and .count)."""

    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class TestPageFromResult:
    @pytest.mark.golden
    def test_uses_count_when_present(self):
        result = _FakeResult([{"id": 1}, {"id": 2}], count=847)
        p = Page.from_result(result, PageParams(skip=0, limit=20))
        assert p.items == [{"id": 1}, {"id": 2}]
        assert p.total == 847
        assert p.skip == 0
        assert p.limit == 20

    @pytest.mark.golden
    def test_falls_back_to_len_when_count_missing(self):
        result = _FakeResult([{"id": 1}], count=None)
        p = Page.from_result(result, PageParams())
        assert p.total == 1

    @pytest.mark.golden
    def test_empty_data_is_safe(self):
        result = _FakeResult([], count=0)
        p = Page.from_result(result, PageParams())
        assert p.items == []
        assert p.total == 0


class TestPageFromList:
    @pytest.mark.golden
    def test_default_total_is_items_length(self):
        p = Page.from_list([1, 2, 3], PageParams())
        assert p.total == 3

    @pytest.mark.golden
    def test_explicit_total_overrides_len(self):
        p = Page.from_list([1, 2], PageParams(skip=10, limit=2), total=100)
        assert p.total == 100
        assert p.skip == 10


# ── apply_page ────────────────────────────────────────────────────────────

class _FakeQuery:
    """Records the chain of .order/.offset/.limit calls."""

    def __init__(self):
        self.calls: list[tuple] = []

    def order(self, col, desc=True):
        self.calls.append(("order", col, desc))
        return self

    def offset(self, n):
        self.calls.append(("offset", n))
        return self

    def limit(self, n):
        self.calls.append(("limit", n))
        return self


class TestApplyPage:
    @pytest.mark.golden
    def test_applies_default_order_when_no_override(self):
        q = _FakeQuery()
        apply_page(q, PageParams(), default_order="created_at")
        assert q.calls[0] == ("order", "created_at", True)

    @pytest.mark.golden
    def test_override_order_by(self):
        q = _FakeQuery()
        apply_page(q, PageParams(order_by="name", order_desc=False), default_order="created_at")
        assert q.calls[0] == ("order", "name", False)

    @pytest.mark.golden
    def test_offset_skipped_when_zero(self):
        q = _FakeQuery()
        apply_page(q, PageParams(skip=0, limit=20))
        assert not any(c[0] == "offset" for c in q.calls)
        assert ("limit", 20) in q.calls

    @pytest.mark.golden
    def test_offset_applied_when_nonzero(self):
        q = _FakeQuery()
        apply_page(q, PageParams(skip=40, limit=20))
        assert ("offset", 40) in q.calls
        assert ("limit", 20) in q.calls

    @pytest.mark.golden
    def test_returns_same_builder_for_chaining(self):
        q = _FakeQuery()
        result = apply_page(q, PageParams())
        assert result is q
