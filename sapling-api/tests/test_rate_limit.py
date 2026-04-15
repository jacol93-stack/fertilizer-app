"""Unit tests for the path-classifying rate limiter.

Locks in rule routing (which path/method lands in which tier) and the
sliding-window counter. No FastAPI — tests the helpers directly.
"""

from __future__ import annotations

import time

import pytest

from app import rate_limit
from app.rate_limit import _check, _classify, DEFAULT_LIMITS, DEFAULT_NAME


@pytest.fixture(autouse=True)
def _reset_buckets():
    """Each test starts with empty in-memory buckets."""
    rate_limit._buckets.clear()
    yield
    rate_limit._buckets.clear()


# ── Path classification ───────────────────────────────────────────────────

class TestClassify:
    @pytest.mark.golden
    def test_engine_blend_optimize(self):
        name, _ = _classify("POST", "/api/blends/optimize")
        assert name == "engine"

    @pytest.mark.golden
    def test_engine_soil_classify(self):
        name, _ = _classify("POST", "/api/soil/classify")
        assert name == "engine"

    @pytest.mark.golden
    def test_engine_soil_targets(self):
        assert _classify("POST", "/api/soil/targets")[0] == "engine"

    @pytest.mark.golden
    def test_engine_feeding_generate(self):
        assert _classify("POST", "/api/feeding-plans/generate")[0] == "engine"

    @pytest.mark.golden
    def test_engine_does_not_match_get(self):
        # engine tier is POST/PUT only; GET falls through
        name, _ = _classify("GET", "/api/blends/optimize")
        assert name != "engine"

    @pytest.mark.golden
    def test_list_tier_blends_root(self):
        assert _classify("GET", "/api/blends")[0] == "list"
        assert _classify("GET", "/api/blends/")[0] == "list"

    @pytest.mark.golden
    def test_list_tier_workbench(self):
        assert _classify("GET", "/api/workbench/workbench")[0] == "list"

    @pytest.mark.golden
    def test_admin_tier_post(self):
        assert _classify("POST", "/api/admin/users")[0] == "admin"
        assert _classify("DELETE", "/api/admin/users/abc")[0] == "admin"
        assert _classify("PATCH", "/api/admin/users/abc")[0] == "admin"

    @pytest.mark.golden
    def test_admin_tier_get_falls_through(self):
        # Admin GETs are not rate-tiered specially; they hit default
        assert _classify("GET", "/api/admin/users")[0] == DEFAULT_NAME

    @pytest.mark.golden
    def test_ai_tier_lab_extract(self):
        assert _classify("POST", "/api/soil/extract")[0] == "ai"
        assert _classify("POST", "/api/leaf/extract")[0] == "ai"

    @pytest.mark.golden
    def test_session_tier(self):
        assert _classify("POST", "/api/sessions/start")[0] == "session"
        assert _classify("POST", "/api/sessions/heartbeat")[0] == "session"

    @pytest.mark.golden
    def test_default_for_unknown_paths(self):
        assert _classify("GET", "/api/random/thing")[0] == DEFAULT_NAME
        assert _classify("POST", "/api/whatever")[0] == DEFAULT_NAME


# ── Sliding-window counter ────────────────────────────────────────────────

class TestCheck:
    @pytest.mark.golden
    def test_allows_within_limit(self):
        limits = ((5, 60),)
        for _ in range(5):
            allowed, retry = _check("test", "key1", limits)
            assert allowed is True
            assert retry is None

    @pytest.mark.golden
    def test_blocks_over_limit(self):
        limits = ((3, 60),)
        for _ in range(3):
            assert _check("test", "k", limits)[0] is True
        allowed, retry = _check("test", "k", limits)
        assert allowed is False
        assert retry is not None and retry >= 1

    @pytest.mark.golden
    def test_different_keys_are_independent(self):
        limits = ((2, 60),)
        assert _check("test", "alice", limits)[0] is True
        assert _check("test", "alice", limits)[0] is True
        assert _check("test", "alice", limits)[0] is False
        # Bob still has full budget
        assert _check("test", "bob", limits)[0] is True
        assert _check("test", "bob", limits)[0] is True
        assert _check("test", "bob", limits)[0] is False

    @pytest.mark.golden
    def test_different_rules_are_independent(self):
        limits = ((2, 60),)
        assert _check("engine", "k", limits)[0] is True
        assert _check("engine", "k", limits)[0] is True
        assert _check("engine", "k", limits)[0] is False
        # Same key, different rule — fresh budget
        assert _check("list", "k", limits)[0] is True

    @pytest.mark.golden
    def test_stacked_limits_both_checked(self):
        """30/second AND 300/minute — both must pass."""
        limits = ((3, 1), (5, 60))  # 3/second, 5/minute
        # Burst 3 — allowed
        for _ in range(3):
            assert _check("test", "k", limits)[0] is True
        # 4th fails on the per-second limit
        assert _check("test", "k", limits)[0] is False

    @pytest.mark.golden
    def test_retry_after_is_positive(self):
        limits = ((1, 10),)
        assert _check("test", "k", limits)[0] is True
        allowed, retry = _check("test", "k", limits)
        assert allowed is False
        assert retry is not None
        assert retry >= 1
        assert retry <= 10


# ── Default limits ────────────────────────────────────────────────────────

class TestDefaultLimits:
    @pytest.mark.golden
    def test_default_cap_is_200_per_minute(self):
        assert DEFAULT_LIMITS == ((200, 60),)

    @pytest.mark.golden
    def test_unknown_path_hits_default(self):
        name, limits = _classify("GET", "/api/unknown/route")
        assert name == DEFAULT_NAME
        assert limits == DEFAULT_LIMITS
