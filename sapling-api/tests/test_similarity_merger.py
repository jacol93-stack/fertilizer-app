"""Tests for Phase 2 module 8.5 — similarity merger.

Covers the F4 criteria:
  1. same block + method
  2. same product set
  3. per-event rate within ±10 %
  4. no timing wall fires in the gap between the two blends' event spans

Conservative — any failing criterion leaves both blends separate.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.models import (
    ApplicationEvent,
    Blend,
    BlendPart,
    DryBlendMethod,
    FertigationMethod,
    FoliarMethod,
    MethodKind,
)
from app.services.similarity_merger import merge_similar_blends


# ============================================================
# Fixtures
# ============================================================

def _event(dt: date, idx: int = 1, weeks: int = 1) -> ApplicationEvent:
    return ApplicationEvent(
        event_index=idx,
        event_date=dt,
        week_from_planting=weeks,
    )


def _drip_blend(
    *,
    stage_num: int,
    stage_name: str,
    events: list[ApplicationEvent],
    rate_can: str = "42 kg",
    rate_mkp: str = "15 kg",
    block_id: str = "b1",
) -> Blend:
    return Blend(
        block_id=block_id,
        stage_number=stage_num,
        stage_name=stage_name,
        applications=events,
        method=FertigationMethod(kind=MethodKind.LIQUID_DRIP),
        raw_products=[
            BlendPart(product="Calcium Nitrate", analysis="N 17.1%, Ca 24.4%",
                      stream="A", rate_per_event_per_ha=rate_can,
                      rate_per_stage_per_ha=f"{_parse(rate_can) * len(events):.0f} kg"),
            BlendPart(product="MKP", analysis="P 51.8%, K 33.8%",
                      stream="B", rate_per_event_per_ha=rate_mkp,
                      rate_per_stage_per_ha=f"{_parse(rate_mkp) * len(events):.0f} kg"),
        ],
        nutrients_delivered={"N": 35.9 * len(events), "Ca": 51.2 * len(events),
                             "P2O5": 28.5 * len(events), "K2O": 33.7 * len(events)},
    )


def _dry_blend(
    *,
    stage_num: int,
    stage_name: str,
    events: list[ApplicationEvent],
    rate_urea: str = "30 kg",
    block_id: str = "b1",
) -> Blend:
    return Blend(
        block_id=block_id,
        stage_number=stage_num,
        stage_name=stage_name,
        applications=events,
        method=DryBlendMethod(kind=MethodKind.DRY_BROADCAST),
        raw_products=[
            BlendPart(product="Urea", analysis="N 46%",
                      rate_per_event_per_ha=rate_urea,
                      rate_per_stage_per_ha=rate_urea),
        ],
        nutrients_delivered={"N": 13.8 * len(events)},
    )


def _parse(rate: str) -> float:
    return float(rate.replace(" kg", "").strip())


# ============================================================
# Degenerate inputs
# ============================================================

def test_empty_returns_empty():
    assert merge_similar_blends([], crop="Macadamia", block_area_ha=10.0) == []


def test_single_blend_passthrough():
    b = _drip_blend(
        stage_num=1, stage_name="Veg I",
        events=[_event(date(2026, 3, 15))],
    )
    out = merge_similar_blends([b], crop="Macadamia", block_area_ha=10.0)
    assert len(out) == 1
    assert out[0].stage_name == "Veg I"


# ============================================================
# Happy path — two mergeable
# ============================================================

def test_two_identical_blends_no_wall_between_merge():
    """Lucerne has no timing walls — two adjacent drip stages with the
    same recipe should merge."""
    a = _drip_blend(
        stage_num=1, stage_name="Veg I",
        events=[_event(date(2026, 3, 5), idx=1, weeks=1),
                _event(date(2026, 3, 19), idx=2, weeks=3)],
    )
    b = _drip_blend(
        stage_num=2, stage_name="Veg II",
        events=[_event(date(2026, 4, 5), idx=3, weeks=5),
                _event(date(2026, 4, 19), idx=4, weeks=7)],
    )
    out = merge_similar_blends([a, b], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 1
    merged = out[0]
    assert merged.stage_name == "Veg I + Veg II"
    assert len(merged.applications) == 4
    # Nutrients summed across both blends
    assert merged.nutrients_delivered["N"] == pytest.approx(35.9 * 4, rel=0.01)
    # applications re-labelled 1-of-4 .. 4-of-4
    indices = [a.event_of_stage_index for a in merged.applications]
    assert indices == [1, 2, 3, 4]
    totals = {a.total_events_in_stage for a in merged.applications}
    assert totals == {4}


def test_three_adjacent_collapse_to_one():
    a = _drip_blend(stage_num=1, stage_name="Veg I",
                    events=[_event(date(2026, 3, 10))])
    b = _drip_blend(stage_num=2, stage_name="Veg II",
                    events=[_event(date(2026, 4, 10))])
    c = _drip_blend(stage_num=3, stage_name="Veg III",
                    events=[_event(date(2026, 5, 10))])
    out = merge_similar_blends([a, b, c], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 1
    assert out[0].stage_name == "Veg I + Veg II + Veg III"
    assert len(out[0].applications) == 3


# ============================================================
# Criterion failures — no merge
# ============================================================

def test_rates_differ_beyond_tolerance_no_merge():
    """Per-event rate difference >10% → blends stay separate."""
    a = _drip_blend(stage_num=1, stage_name="Veg I",
                    events=[_event(date(2026, 3, 15))],
                    rate_can="42 kg")
    b = _drip_blend(stage_num=2, stage_name="Veg II",
                    events=[_event(date(2026, 4, 15))],
                    rate_can="60 kg")   # 42.8% higher
    out = merge_similar_blends([a, b], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 2
    assert {b.stage_name for b in out} == {"Veg I", "Veg II"}


def test_rates_within_tolerance_still_merge():
    """Per-event rate difference <10% → merges, averaged."""
    a = _drip_blend(stage_num=1, stage_name="Veg I",
                    events=[_event(date(2026, 3, 15))],
                    rate_can="40 kg")
    b = _drip_blend(stage_num=2, stage_name="Veg II",
                    events=[_event(date(2026, 4, 15))],
                    rate_can="42 kg")   # 5% higher
    out = merge_similar_blends([a, b], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 1
    # Averaged per-event rate = 41 kg (rounded — formatter emits whole kg when ≥10)
    can = next(p for p in out[0].raw_products if p.product == "Calcium Nitrate")
    assert can.rate_per_event_per_ha == "41 kg"


def test_different_methods_no_merge():
    """Drip vs dry broadcast → different method kinds, no merge."""
    a = _drip_blend(stage_num=1, stage_name="Veg I",
                    events=[_event(date(2026, 3, 15))])
    b = _dry_blend(stage_num=2, stage_name="Veg II",
                   events=[_event(date(2026, 4, 15))])
    out = merge_similar_blends([a, b], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 2


def test_different_product_sets_no_merge():
    """Same method, different products → no merge."""
    a = _drip_blend(stage_num=1, stage_name="Veg I",
                    events=[_event(date(2026, 3, 15))])
    # b uses a different product set (SOP replacing MKP)
    b = Blend(
        block_id="b1", stage_number=2, stage_name="Veg II",
        applications=[_event(date(2026, 4, 15))],
        method=FertigationMethod(kind=MethodKind.LIQUID_DRIP),
        raw_products=[
            BlendPart(product="Calcium Nitrate", analysis="N 17.1%, Ca 24.4%",
                      stream="A", rate_per_event_per_ha="42 kg",
                      rate_per_stage_per_ha="42 kg"),
            BlendPart(product="SOP", analysis="K 50.4%, S 18%",
                      stream="B", rate_per_event_per_ha="20 kg",
                      rate_per_stage_per_ha="20 kg"),
        ],
        nutrients_delivered={"N": 20, "K2O": 30},
    )
    out = merge_similar_blends([a, b], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 2


def test_different_block_ids_no_merge():
    """Defensive — blends from different blocks never merge."""
    a = _drip_blend(stage_num=1, stage_name="Veg I",
                    events=[_event(date(2026, 3, 15))],
                    block_id="b1")
    b = _drip_blend(stage_num=1, stage_name="Veg I",
                    events=[_event(date(2026, 4, 15))],
                    block_id="b2")
    out = merge_similar_blends([a, b], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 2


# ============================================================
# Wall-in-gap
# ============================================================

def test_timing_wall_in_gap_blocks_merge():
    """Macadamia N-cutoff (Nov-Feb). Two N-delivering drip blends,
    one in Oct, one in Mar — the gap contains the blocked months, so
    they must NOT merge even though the blends themselves are outside
    the cutoff."""
    a = _drip_blend(
        stage_num=1, stage_name="Pre-cutoff",
        events=[_event(date(2026, 10, 15))],
    )
    b = _drip_blend(
        stage_num=2, stage_name="Post-cutoff",
        events=[_event(date(2027, 3, 15))],
    )
    out = merge_similar_blends([a, b], crop="Macadamia", block_area_ha=10.0)
    assert len(out) == 2
    assert {b.stage_name for b in out} == {"Pre-cutoff", "Post-cutoff"}


def test_timing_wall_outside_gap_allows_merge():
    """Same macadamia crop. Two blends both in Mar-Apr (fully outside
    the Nov-Feb cutoff) — the wall is not active in the gap, so they
    may merge."""
    a = _drip_blend(
        stage_num=1, stage_name="Mar",
        events=[_event(date(2026, 3, 15))],
    )
    b = _drip_blend(
        stage_num=2, stage_name="Apr",
        events=[_event(date(2026, 4, 15))],
    )
    out = merge_similar_blends([a, b], crop="Macadamia", block_area_ha=10.0)
    assert len(out) == 1
    assert out[0].stage_name == "Mar + Apr"


# ============================================================
# Post-merge shape checks
# ============================================================

def test_merged_fertigation_rebuilds_concentrates():
    """After merging, Part A + Part B concentrates are recomputed from
    the merged raw_products (important because batch totals changed)."""
    a = _drip_blend(stage_num=1, stage_name="Veg I",
                    events=[_event(date(2026, 3, 5)),
                            _event(date(2026, 3, 19))])
    b = _drip_blend(stage_num=2, stage_name="Veg II",
                    events=[_event(date(2026, 4, 5)),
                            _event(date(2026, 4, 19))])
    out = merge_similar_blends([a, b], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 1
    merged = out[0]
    # Fertigation recipe → two concentrates (Part A Ca-stream + Part B PO4-stream)
    names = [c.name for c in merged.concentrates]
    assert any("Part A" in n for n in names)
    assert any("Part B" in n for n in names)


def test_merged_blend_stage_number_is_lowest():
    a = _drip_blend(stage_num=5, stage_name="Later",
                    events=[_event(date(2026, 4, 15))])
    b = _drip_blend(stage_num=2, stage_name="Earlier",
                    events=[_event(date(2026, 3, 15))])
    out = merge_similar_blends([a, b], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 1
    # Blends were sorted earliest-first before merging, so stage_number = 2
    assert out[0].stage_number == 2
    assert out[0].stage_name == "Earlier + Later"


def test_already_merged_name_stays_flat_on_further_merges():
    """Don't produce 'A + B + A + C' when one side is already a merged
    label."""
    a = _drip_blend(stage_num=1, stage_name="Veg I + Veg II",
                    events=[_event(date(2026, 3, 5)),
                            _event(date(2026, 3, 19))])
    b = _drip_blend(stage_num=3, stage_name="Veg III",
                    events=[_event(date(2026, 4, 5))])
    out = merge_similar_blends([a, b], crop="Lucerne", block_area_ha=10.0)
    assert len(out) == 1
    assert out[0].stage_name == "Veg I + Veg II + Veg III"
