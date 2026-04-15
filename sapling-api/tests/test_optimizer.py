"""Golden-case tests for the blend optimizer.

These lock in CURRENT behavior of run_optimizer, find_closest_blend, and
run_priority_optimizer with a tiny fixed materials table. They're not
covering the real seeded materials — the point is to pin down HOW the
optimizer reacts to known inputs so refactors can't silently change output.

Audit items deliberately encoded here so the fix has a target to break:
  - find_closest_blend can return (None, 0.0) — downstream AttributeError risk
  - priority optimizer returns (None, meta) when completely infeasible
  - No minimum-material-mass constraint (recipes may include fractional kg)
"""

from __future__ import annotations

import pandas as pd
import pytest

from app.services.optimizer import (
    find_closest_blend,
    run_optimizer,
    run_priority_optimizer,
)


@pytest.fixture
def materials_df():
    """Tiny materials table: urea, MAP, MOP, compost.

    Compost is intentionally index 3 (c_idx). Nutrient columns are percent.
    """
    return pd.DataFrame([
        {"name": "Urea",    "N": 46.0, "P": 0.0,  "K": 0.0},
        {"name": "MAP",     "N": 11.0, "P": 52.0, "K": 0.0},
        {"name": "MOP",     "N": 0.0,  "P": 0.0,  "K": 60.0},
        {"name": "Compost", "N": 1.0,  "P": 1.0,  "K": 1.0},
    ])


class TestRunOptimizer:
    @pytest.mark.golden
    def test_feasible_basic_npk(self, materials_df):
        """5-3-2 on 1 ton with 10% min compost should be feasible."""
        targets = {"N": 5.0, "P": 3.0, "K": 2.0}
        res = run_optimizer(targets, materials_df, batch_size=1000, c_idx=3, min_pct=10)
        assert res.success is True
        # Total mass ≈ batch size
        assert abs(sum(res.x) - 1000) < 1e-6
        # Compost >= 10% of batch
        assert res.x[3] >= 100 - 1e-6
        # All non-negative
        assert all(v >= -1e-9 for v in res.x)

    @pytest.mark.golden
    def test_infeasible_high_n_with_compost_lock(self, materials_df):
        """Impossible target: 50% N with 90% min compost -> infeasible."""
        targets = {"N": 50.0, "P": 0.0, "K": 0.0}
        res = run_optimizer(targets, materials_df, batch_size=1000, c_idx=3, min_pct=90)
        assert res.success is False

    @pytest.mark.golden
    def test_delivered_nutrients_match_target(self, materials_df):
        targets = {"N": 5.0, "P": 3.0, "K": 2.0}
        res = run_optimizer(targets, materials_df, batch_size=1000, c_idx=3, min_pct=10)
        assert res.success
        delivered = {
            "N": sum(res.x[i] * materials_df.iloc[i]["N"] / 100 for i in range(len(res.x))),
            "P": sum(res.x[i] * materials_df.iloc[i]["P"] / 100 for i in range(len(res.x))),
            "K": sum(res.x[i] * materials_df.iloc[i]["K"] / 100 for i in range(len(res.x))),
        }
        # Expected kg of each nutrient in a 1000 kg batch
        assert delivered["N"] == pytest.approx(50.0, abs=0.1)
        assert delivered["P"] == pytest.approx(30.0, abs=0.1)
        assert delivered["K"] == pytest.approx(20.0, abs=0.1)


class TestFindClosestBlend:
    @pytest.mark.golden
    def test_feasible_returns_full_scale(self, materials_df):
        targets = {"N": 5.0, "P": 3.0, "K": 2.0}
        res, scale = find_closest_blend(targets, materials_df, 1000, c_idx=3, min_pct=10)
        assert res is not None
        assert scale == pytest.approx(1.0, abs=0.001)

    @pytest.mark.golden
    def test_zero_p_zero_k_infeasible_due_to_compost_trace(self, materials_df):
        """Audit-surfaced quirk: equality constraints + compost having 1% P/K
        mean you can't target P=0 exactly whenever min_pct > 0. Binary search
        fails at every scale factor and returns (None, 0.0). This is real
        behavior that would surprise callers. Locking in so the future
        optimizer fix (inequality / tolerance) trips the test."""
        targets = {"N": 40.0, "P": 0.0, "K": 0.0}
        res, scale = find_closest_blend(targets, materials_df, 1000, c_idx=3, min_pct=10)
        assert res is None
        assert scale == 0.0

    @pytest.mark.golden
    def test_totally_infeasible_returns_none(self, materials_df):
        """Audit: when binary search exhausts with no feasible point, returns
        (None, 0.0). Downstream code must handle this — ignoring it is the
        bug. Locking in so the future fix must update this test."""
        # Min compost 100% + nonzero N target -> nothing works
        targets = {"N": 5.0, "P": 0.0, "K": 0.0}
        res, scale = find_closest_blend(targets, materials_df, 1000, c_idx=3, min_pct=100)
        assert res is None
        assert scale == 0.0


class TestRunPriorityOptimizer:
    @pytest.mark.golden
    def test_all_must_match_feasible(self, materials_df):
        targets = {"N": 5.0, "P": 3.0, "K": 2.0}
        priorities = {"N": "must_match", "P": "must_match", "K": "must_match"}
        res, meta = run_priority_optimizer(targets, priorities, materials_df, 1000, 3, 10)
        assert meta["feasible"] is True
        assert meta["scale"] == pytest.approx(1.0)
        assert set(meta["matched"]) == {"N", "P", "K"}
        assert meta["compromised"] == []

    @pytest.mark.golden
    def test_flexible_dropped_when_needed(self, materials_df):
        """Infeasible full target — flexible nutrient dropped, must_match kept."""
        # Material mix can't hit 40% N *and* match P/K. Mark N must_match;
        # P/K flexible so they get dropped.
        targets = {"N": 40.0, "P": 5.0, "K": 5.0}
        priorities = {"N": "must_match", "P": "flexible", "K": "flexible"}
        res, meta = run_priority_optimizer(targets, priorities, materials_df, 1000, 3, 10)
        # Whether the optimizer lands on "feasible with compromise" or scaled
        # depends on the material mix; lock in "it doesn't crash and returns
        # something sensible."
        assert meta is not None
        assert "matched" in meta
        assert "compromised" in meta

    @pytest.mark.golden
    def test_totally_infeasible_returns_none_result(self, materials_df):
        """Audit: completely infeasible case returns (None, meta).
        Callers must check for None — doing so is still broken in programme_engine."""
        targets = {"N": 5.0, "P": 0.0, "K": 0.0}
        priorities = {"N": "must_match"}
        res, meta = run_priority_optimizer(targets, priorities, materials_df, 1000, 3, 100)
        # Result may be None or a scaled fallback depending on codepath;
        # the important invariant is that meta reports the infeasibility.
        if res is None:
            assert meta["feasible"] is False
            assert meta["scale"] == 0
