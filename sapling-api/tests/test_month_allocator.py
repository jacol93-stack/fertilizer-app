"""Tests for the month allocator — the engine's bridge between
the farmer's operational availability and the agronomic stage
calendar."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

import pytest

from app.services.month_allocator import (
    AllocatedApplication,
    AllocationResult,
    allocate_to_months,
)
from app.services.stage_splitter import StageSplit


# ============================================================
# Minimal StageWindow-shaped test double
# ============================================================

@dataclass
class _StageWindowStub:
    stage_number: int
    stage_name: str
    week_start: int
    week_end: int
    date_start: date
    date_end: date
    events: int = 1
    blend_ref: Optional[str] = None
    foliar_at_week: Optional[int] = None


def _mac_4stage_schedule(planting: date = date(2026, 7, 1)) -> tuple[list[StageSplit], list[_StageWindowStub]]:
    """A 4-stage macadamia programme starting July 2026, roughly
    aligned to FERTASA 5.8.1 windows (post-harvest / pre-flower /
    nut set / nut growth)."""
    splits = [
        StageSplit(stage_number=1, stage_name="Post-harvest + flower initiation",
                   nutrients={"N": 30, "P2O5": 15, "K2O": 20, "Ca": 5, "Mg": 0.5, "S": 1.5}),
        StageSplit(stage_number=2, stage_name="Pre-flowering + flowering",
                   nutrients={"N": 30, "P2O5": 15, "K2O": 40, "Ca": 3, "Mg": 0.5, "S": 1.5}),
        StageSplit(stage_number=3, stage_name="Nut set",
                   nutrients={"N": 30, "P2O5": 15, "K2O": 60, "Ca": 2, "Mg": 0.5, "S": 1.5}),
        StageSplit(stage_number=4, stage_name="Nut growth + oil",
                   nutrients={"N": 20, "P2O5": 15, "K2O": 50, "Ca": 2, "Mg": 0.5, "S": 1.5}),
    ]
    schedule = [
        _StageWindowStub(1, "Post-harvest + flower initiation", 1, 10,
                         date(2026, 7, 1), date(2026, 9, 15), events=3),
        _StageWindowStub(2, "Pre-flowering + flowering", 11, 22,
                         date(2026, 9, 16), date(2026, 11, 30), events=3),
        _StageWindowStub(3, "Nut set", 23, 30,
                         date(2026, 12, 1), date(2027, 2, 15), events=2),
        _StageWindowStub(4, "Nut growth + oil", 31, 48,
                         date(2027, 2, 16), date(2027, 6, 30), events=4),
    ]
    return splits, schedule


# ============================================================
# Empty allowed_months → fallback
# ============================================================

def test_empty_allowed_months_falls_back_to_stage_midpoints():
    splits, schedule = _mac_4stage_schedule()
    result = allocate_to_months(
        crop="Macadamia",
        stage_splits=splits,
        stage_schedule=schedule,
        allowed_months=[],
        planting_date=date(2026, 7, 1),
    )
    # One application per stage
    assert len(result.applications) == 4
    for i, app in enumerate(result.applications, start=1):
        assert app.stage_number == i
        assert app.nutrients == splits[i - 1].nutrients


# ============================================================
# Basic allocation — 4 allowed months, 4 stages
# ============================================================

def test_four_allowed_months_across_four_stages_one_app_each():
    """Aug, Oct, Dec, Mar — each stage gets one event, no splitting."""
    splits, schedule = _mac_4stage_schedule()
    result = allocate_to_months(
        crop="Macadamia",
        stage_splits=splits,
        stage_schedule=schedule,
        allowed_months=[8, 10, 12, 3],
        planting_date=date(2026, 7, 1),
    )
    assert len(result.applications) == 4
    # Applications in chronological order
    dates = [a.event_date for a in result.applications]
    assert dates == sorted(dates)
    # Each allocates to a different stage
    stages = {a.stage_number for a in result.applications}
    assert stages == {1, 2, 3, 4}


def test_two_allowed_months_in_same_stage_split_allocation():
    """Aug + Sep both fall in stage 1 → allocation splits equally."""
    splits, schedule = _mac_4stage_schedule()
    result = allocate_to_months(
        crop="Macadamia",
        stage_splits=splits,
        stage_schedule=schedule,
        allowed_months=[8, 9],
        planting_date=date(2026, 7, 1),
    )
    # Two applications, both in stage 1
    assert len(result.applications) == 2
    assert all(a.stage_number == 1 for a in result.applications)
    # Each carries half of stage-1 allocation
    for app in result.applications:
        assert app.nutrients["N"] == pytest.approx(15.0)  # 30 / 2
        assert app.nutrients["P2O5"] == pytest.approx(7.5)


# ============================================================
# Timing walls — nutrient cutoff must fire
# ============================================================

def test_mac_n_zeroed_in_december_per_fertasa_5_8_1():
    """FERTASA 5.8.1 Nov-Feb N cutoff — December event must have N=0,
    N redistributed to other events in the same stage."""
    splits, schedule = _mac_4stage_schedule()
    result = allocate_to_months(
        crop="Macadamia",
        stage_splits=splits,
        stage_schedule=schedule,
        allowed_months=[9, 12],  # Sep → stage 1; Dec → stage 2 or 3 (Nov-Feb)
        planting_date=date(2026, 7, 1),
    )
    # Find the December event
    dec_apps = [a for a in result.applications if a.month == 12]
    assert len(dec_apps) >= 1
    # All December events must have N = 0 per the wall
    for a in dec_apps:
        assert a.nutrients.get("N", 0) == 0, "December N must be zeroed by FERTASA 5.8.1 wall"
        # And the wall itself should be attached for downstream narrative
        assert any(w.kind == "nutrient_cutoff" for w in a.walls_applied)


def test_mac_n_blocked_in_all_events_surfaces_risk():
    """If every allowed month within a stage is N-blocked, the N
    allocation cannot be delivered → RiskFlag message."""
    splits, schedule = _mac_4stage_schedule()
    result = allocate_to_months(
        crop="Macadamia",
        stage_splits=splits,
        stage_schedule=schedule,
        allowed_months=[12, 1, 2],  # all Nov-Feb N-blocked
        planting_date=date(2026, 7, 1),
    )
    # Risk message must flag the undeliverable N
    assert any("N" in msg and "unallocated" in msg for msg in result.risk_messages), (
        f"Expected N-undeliverable risk message, got: {result.risk_messages}"
    )


def test_k_flows_through_mac_november_since_not_blocked():
    """Only N is walled Nov-Feb for mac — K peak is Oct-Dec per FERTASA,
    so K in a December event is fine."""
    splits, schedule = _mac_4stage_schedule()
    result = allocate_to_months(
        crop="Macadamia",
        stage_splits=splits,
        stage_schedule=schedule,
        allowed_months=[12],
        planting_date=date(2026, 7, 1),
    )
    dec_apps = [a for a in result.applications if a.month == 12]
    assert len(dec_apps) >= 1
    assert dec_apps[0].nutrients["K2O"] > 0


# ============================================================
# Stage-miss outstanding flags
# ============================================================

def test_stage_missed_entirely_emits_outstanding():
    """If allowed months skip stage 2 entirely, outstanding item fires."""
    splits, schedule = _mac_4stage_schedule()
    result = allocate_to_months(
        crop="Macadamia",
        stage_splits=splits,
        stage_schedule=schedule,
        allowed_months=[8, 3],  # stage 1 + stage 4 only; 2+3 missed
        planting_date=date(2026, 7, 1),
    )
    msgs = " ".join(result.outstanding_messages)
    assert "Pre-flowering" in msgs or "stage 2" in msgs.lower() or "Nut set" in msgs


# ============================================================
# Citrus parent-variant walls
# ============================================================

def test_citrus_variant_inherits_walls():
    """A wall defined on 'Citrus' parent still fires for 'Citrus (Valencia)'.
    This test is a smoke check — the N+K antagonism is enforced at blend-
    merger time, not allocator time, so here we just confirm no crash."""
    splits = [
        StageSplit(stage_number=1, stage_name="Post-harvest",
                   nutrients={"N": 30, "K2O": 40}),
    ]
    schedule = [
        _StageWindowStub(1, "Post-harvest", 1, 10,
                         date(2026, 8, 1), date(2026, 10, 31)),
    ]
    result = allocate_to_months(
        crop="Citrus (Valencia)",
        stage_splits=splits,
        stage_schedule=schedule,
        allowed_months=[9],
        planting_date=date(2026, 8, 1),
    )
    assert len(result.applications) == 1
    assert result.applications[0].nutrients["N"] > 0
    assert result.applications[0].nutrients["K2O"] > 0
