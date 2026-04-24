"""
Month allocator — maps a programme's stage-based nutrient allocation
to the farmer's operationally-allowed application months.

The farmer picks WHICH MONTHS they can physically apply fertilizer
(labour, machinery, contractor windows, weather, harvest activity —
a pure operational constraint). The engine owns WHAT goes into each
of those slots. This module does the mapping.

Inputs:
    - Stage splits (per-stage nutrient allocations from stage_splitter)
    - Stage schedule (per-stage date windows from stage_splitter)
    - `allowed_months: list[int]` — farmer's operational availability (1-12)
    - Programme planting date + crop for timing-wall lookup

Outputs:
    - list of `AllocatedApplication` — one per event the farmer will perform,
      each carrying the nutrients it must deliver + its target date +
      which stage(s) it covers + any timing walls applied.
    - list of `RiskFlag` / `OutstandingItem` messages when the
      operational windows miss critical stages or walls block nutrients.

Design principle: the farmer can never cause agronomic harm through
their operational choices. Walls always win. If a farmer's only
available November slot blocks macadamia N, the engine zeroes N in
that event (not the whole event) and surfaces a RiskFlag. If allowed
months miss a whole stage window entirely, the stage's allocation
shifts to the nearest allowed month + an OutstandingItem explains the
compromise.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from app.services.stage_splitter import StageSplit
from app.services.timing_walls import (
    TimingWall,
    nutrient_blocked_in_month,
    walls_for_crop,
)


# ============================================================
# Output types
# ============================================================

@dataclass
class AllocatedApplication:
    """One application event the farmer will perform in one allowed month.

    The downstream method_selector + consolidator treat this as a
    virtual "stage" — each application is one row of nutrient
    allocations to be methoded + consolidated into a blend.
    """
    event_index: int  # 1..N sequential
    event_date: date
    month: int  # 1-12
    year: int
    stage_number: int  # the real stage this event primarily covers
    stage_name: str
    week_from_planting: int
    # Fraction of this event relative to the original stage's allocation
    # (for rendering "applications 2-of-3 for this stage")
    event_of_stage_index: int = 1
    total_events_in_stage: int = 1
    nutrients: dict[str, float] = field(default_factory=dict)
    # Nutrients zeroed by timing walls (for RiskFlag narrative)
    walls_applied: list[TimingWall] = field(default_factory=list)


@dataclass
class AllocationResult:
    applications: list[AllocatedApplication]
    # Warnings to surface through the orchestrator's RiskFlag / OutstandingItem pipeline
    risk_messages: list[str] = field(default_factory=list)
    outstanding_messages: list[str] = field(default_factory=list)


# ============================================================
# Helpers
# ============================================================

def _months_to_dates(
    allowed_months: list[int],
    planting_date: date,
    season_end: Optional[date] = None,
) -> list[date]:
    """Convert month numbers (1-12) to concrete dates on/after planting_date.

    Each month's event is centred on the 15th (arbitrary but consistent
    midpoint — adjust if you prefer early/late in the month).
    """
    if season_end is None:
        season_end = date(planting_date.year + 2, planting_date.month, planting_date.day)
    results: list[date] = []
    for m in sorted(set(allowed_months)):
        if not (1 <= m <= 12):
            continue
        candidate = date(planting_date.year, m, 15)
        if candidate < planting_date:
            candidate = candidate.replace(year=planting_date.year + 1)
        if candidate <= season_end:
            results.append(candidate)
    return sorted(results)


def _weeks_from_planting(planting_date: date, event_date: date) -> int:
    return max(1, (event_date - planting_date).days // 7 + 1)


def _find_stage_for_date(
    event_date: date,
    stage_schedule: list,  # list of StageWindow
) -> Optional[object]:
    """Find the StageWindow whose date range contains event_date. None if
    the date falls outside all stage windows."""
    for window in stage_schedule:
        if window.date_start <= event_date <= window.date_end:
            return window
    return None


def _nearest_stage_for_date(
    event_date: date,
    stage_schedule: list,
) -> Optional[object]:
    """For events that don't fall in any window, find the closest one by
    midpoint distance. Used to decide which stage's allocation should
    shift to this event."""
    if not stage_schedule:
        return None
    def _dist(w):
        mid = w.date_start + (w.date_end - w.date_start) / 2
        return abs((event_date - mid).days)
    return min(stage_schedule, key=_dist)


# ============================================================
# Main allocator
# ============================================================

def allocate_to_months(
    crop: str,
    stage_splits: list[StageSplit],
    stage_schedule: list,  # list[StageWindow] from stage_splitter
    allowed_months: list[int],
    planting_date: date,
    season_end: Optional[date] = None,
) -> AllocationResult:
    """Map stage-based nutrient allocation to farmer-allowed application months.

    The farmer can never cause agronomic harm — timing walls always win:
      - A nutrient blocked in an allowed month is zeroed in that event
        (re-distributed to other events in the same stage if possible),
        and a RiskFlag explains what was blocked.
      - Stages with no allowed month inside them have their allocation
        shifted to the nearest allowed month, with an OutstandingItem
        noting the compromise.

    If `allowed_months` is empty, falls back to one application per
    stage (legacy behaviour).
    """
    # Empty-input fallback: one virtual event per stage, dated at its window midpoint
    if not allowed_months:
        apps: list[AllocatedApplication] = []
        for idx, split in enumerate(stage_splits):
            window = stage_schedule[idx] if idx < len(stage_schedule) else None
            event_date = (
                window.date_start + (window.date_end - window.date_start) / 2
                if window else planting_date + timedelta(weeks=idx * 8)
            )
            apps.append(AllocatedApplication(
                event_index=idx + 1,
                event_date=event_date,
                month=event_date.month,
                year=event_date.year,
                stage_number=split.stage_number,
                stage_name=split.stage_name,
                week_from_planting=_weeks_from_planting(planting_date, event_date),
                nutrients=dict(split.nutrients),
            ))
        return AllocationResult(applications=apps)

    # Convert allowed months to concrete dates post-planting
    event_dates = _months_to_dates(allowed_months, planting_date, season_end)
    if not event_dates:
        return AllocationResult(
            applications=[],
            outstanding_messages=[
                "No allowed application months fall within the programme season. "
                "Review the application_months input against the planting date."
            ],
        )

    # Group event dates by which stage window contains them
    stage_to_dates: dict[int, list[date]] = {}
    stage_by_num = {s.stage_number: s for s in stage_splits}
    window_by_num = {w.stage_number: w for w in stage_schedule}
    risk_messages: list[str] = []
    outstanding_messages: list[str] = []
    orphan_dates: list[date] = []

    for d in event_dates:
        window = _find_stage_for_date(d, stage_schedule)
        if window is None:
            orphan_dates.append(d)
            continue
        stage_to_dates.setdefault(window.stage_number, []).append(d)

    # Shift orphan events to their nearest stage
    for d in orphan_dates:
        window = _nearest_stage_for_date(d, stage_schedule)
        if window is None:
            continue
        stage_to_dates.setdefault(window.stage_number, []).append(d)
        outstanding_messages.append(
            f"Allowed month {d.strftime('%B %Y')} fell outside any stage window — "
            f"shifted to the nearest stage ({window.stage_name}). "
            f"Consider adding an application closer to this stage for tighter timing."
        )

    # Build applications — split each stage's allocation across its events
    applications: list[AllocatedApplication] = []
    event_index = 0
    for stage_num in sorted(stage_to_dates.keys()):
        split = stage_by_num.get(stage_num)
        if split is None:
            continue
        dates_in_stage = sorted(stage_to_dates[stage_num])
        n_events = len(dates_in_stage)
        # Equal split across events in the same stage; walls may re-distribute later
        per_event_nutrients = {
            nut: (amount / n_events) for nut, amount in split.nutrients.items()
        }
        # Pass 1: build raw per-event allocations (before walls)
        raw_events = []
        for i, d in enumerate(dates_in_stage):
            raw_events.append({
                "date": d,
                "nutrients": dict(per_event_nutrients),
                "stage_num": stage_num,
                "stage_name": split.stage_name,
                "event_of_stage": i + 1,
            })
        # Pass 2: apply nutrient cutoff walls — zero blocked nutrients per event
        # and accumulate the blocked amounts for re-distribution.
        blocked_amounts: dict[str, float] = {}  # nutrient → total kg blocked
        blocked_walls: list[TimingWall] = []
        for ev in raw_events:
            walls_here: list[TimingWall] = []
            for nut in list(ev["nutrients"].keys()):
                wall = nutrient_blocked_in_month(crop, nut, ev["date"].month)
                if wall is not None:
                    blocked_amounts[nut] = blocked_amounts.get(nut, 0) + ev["nutrients"][nut]
                    ev["nutrients"][nut] = 0.0
                    if wall not in blocked_walls:
                        blocked_walls.append(wall)
                    walls_here.append(wall)
            ev["walls"] = walls_here
        # Re-distribute blocked amounts to unblocked events in the same stage
        # where the wall doesn't apply
        for nut, total_blocked in blocked_amounts.items():
            unblocked_events = [
                e for e in raw_events
                if nutrient_blocked_in_month(crop, nut, e["date"].month) is None
            ]
            if unblocked_events:
                per_event_extra = total_blocked / len(unblocked_events)
                for e in unblocked_events:
                    e["nutrients"][nut] = e["nutrients"].get(nut, 0) + per_event_extra
            else:
                # No unblocked event in this stage — the nutrient simply
                # cannot be applied in this stage's window. Emit RiskFlag.
                risk_messages.append(
                    f"{nut} cannot be applied in any of the stage-{stage_num} "
                    f"({split.stage_name}) events because every available month "
                    f"is blocked by timing wall. {total_blocked:.1f} kg/ha of "
                    f"{nut} remains unallocated. Consider adjusting "
                    f"application_months or accept the stage's {nut} shortfall."
                )
        # Pass 3: materialise AllocatedApplication objects
        for ev in raw_events:
            event_index += 1
            applications.append(AllocatedApplication(
                event_index=event_index,
                event_date=ev["date"],
                month=ev["date"].month,
                year=ev["date"].year,
                stage_number=ev["stage_num"],
                stage_name=ev["stage_name"],
                week_from_planting=_weeks_from_planting(planting_date, ev["date"]),
                event_of_stage_index=ev["event_of_stage"],
                total_events_in_stage=n_events,
                nutrients=ev["nutrients"],
                walls_applied=ev["walls"],
            ))

    # Check: stages with no events at all (farmer missed the window entirely)
    covered_stages = {a.stage_number for a in applications}
    for split in stage_splits:
        if split.stage_number in covered_stages:
            continue
        # Stage got no application → flag as outstanding
        window = window_by_num.get(split.stage_number)
        window_str = ""
        if window:
            window_str = f" ({window.date_start.strftime('%b')}–{window.date_end.strftime('%b')})"
        outstanding_messages.append(
            f"Stage {split.stage_number} '{split.stage_name}'{window_str} has no "
            f"allowed application month inside its window. Nutrients for this "
            f"stage were not delivered. Consider adding a month within this window."
        )

    # Sort applications by date for downstream ordering stability
    applications.sort(key=lambda a: a.event_date)
    for new_idx, app in enumerate(applications, start=1):
        app.event_index = new_idx

    return AllocationResult(
        applications=applications,
        risk_messages=risk_messages,
        outstanding_messages=outstanding_messages,
    )
