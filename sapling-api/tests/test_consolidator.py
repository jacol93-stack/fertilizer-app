"""Tests for the Phase 2 Consolidator — groups method_selector
assignments into typed Blend objects with material selection + Part A/B
split for fertigation."""
from __future__ import annotations

from datetime import date

import pytest

from app.models import (
    Blend,
    BlendPart,
    Concentrate,
    FertigationMethod,
    MethodAvailability,
    MethodKind,
    StageWindow,
)
from app.services.consolidator import (
    MAX_PRODUCTS_PER_BLEND,
    _classify_stream,
    consolidate_blends,
)
from app.services.method_selector import MethodAssignment, select_methods
from app.services.stage_splitter import split_season_targets


# ============================================================
# Fixtures
# ============================================================

LIQUID_MATERIALS = [
    {"material": "Calcium Nitrate", "type": "Nitrogen Source",
     "n": 17.1, "p": 0, "k": 0, "ca": 24.4, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": True, "foliar_compatible": False},
    {"material": "Potassium Nitrate", "type": "Nitrogen Source",
     "n": 14, "p": 0, "k": 46, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": True, "foliar_compatible": False},
    {"material": "MKP", "type": "Phosphate Source",
     "n": 0, "p": 51.8, "k": 33.8, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": True, "foliar_compatible": False},
    {"material": "SOP (Potassium Sulphate)", "type": "Potassium",
     "n": 0, "p": 0, "k": 50.4, "ca": 0, "mg": 0, "s": 18,
     "form": "solid", "liquid_compatible": True, "foliar_compatible": False},
    {"material": "Ammonium Sulphate", "type": "Nitrogen Source",
     "n": 21, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 24,
     "form": "solid", "liquid_compatible": True, "foliar_compatible": False},
    {"material": "MAP 33%", "type": "Phosphate Source",
     "n": 11, "p": 50.4, "k": 0, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": True, "foliar_compatible": False},
]

DRY_MATERIALS = [
    {"material": "Urea", "type": "Nitrogen Source",
     "n": 46, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": False, "foliar_compatible": False},
    {"material": "MAP (granular)", "type": "Phosphate Source",
     "n": 11, "p": 50.4, "k": 0, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": False, "foliar_compatible": False},
    {"material": "KCl", "type": "Potassium Source",
     "n": 0, "p": 0, "k": 60, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": False, "foliar_compatible": False},
    {"material": "Ammonium Sulphate (granular)", "type": "Nitrogen Source",
     "n": 21, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 24,
     "form": "solid", "liquid_compatible": False, "foliar_compatible": False},
]

FOLIAR_MATERIALS = [
    {"material": "Zinc Sulphate", "type": "Zinc Source",
     "n": 0, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 17.5,
     "zn": 36, "form": "solid", "liquid_compatible": False, "foliar_compatible": True},
    {"material": "Solubor", "type": "Boron Source",
     "n": 0, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 0,
     "b": 20.5, "form": "solid", "liquid_compatible": False, "foliar_compatible": True},
]


# ============================================================
# Stream classification
# ============================================================

def test_calcium_nitrate_goes_part_a():
    mat = {"ca": 24.4, "s": 0, "p": 0}
    assert _classify_stream(mat) == "A"


def test_sop_goes_part_b():
    mat = {"ca": 0, "s": 18, "p": 0}
    assert _classify_stream(mat) == "B"


def test_metabophos_ca_with_s_goes_part_b():
    """Metabophos has Ca 19% AND S 11% — SO₄ dominates, routes Part B."""
    mat = {"ca": 19, "s": 11, "p": 19}
    assert _classify_stream(mat) == "B"


# ============================================================
# Liquid consolidation (Clivia-style)
# ============================================================

def test_consolidate_produces_blends_per_stage():
    """5 stages × liquid method → 5 Blend objects."""
    targets = {"N": 100, "P2O5": 40, "K2O": 80, "Ca": 60, "S": 20}
    splits = split_season_targets("Garlic", targets, stage_count=5)
    avail = MethodAvailability(has_drip=True, has_foliar_sprayer=False)
    assignments = select_methods(splits, avail)

    blends = consolidate_blends(
        assignments=assignments,
        available_materials=LIQUID_MATERIALS,
        block_id="land_a",
        block_area_ha=1.11,
    )
    # At least one blend per stage
    stages_covered = {b.stage_number for b in blends}
    assert len(stages_covered) == 5


def test_consolidate_produces_fertigation_concentrates():
    targets = {"N": 100, "P2O5": 40, "K2O": 80, "Ca": 60, "S": 20}
    splits = split_season_targets("Garlic", targets, stage_count=5)
    avail = MethodAvailability(has_drip=True)
    assignments = select_methods(splits, avail)

    blends = consolidate_blends(
        assignments=assignments, available_materials=LIQUID_MATERIALS,
        block_id="land_a", block_area_ha=1.11,
    )
    for b in blends:
        if _is_fertigation_blend(b):
            # Part A + Part B concentrates should exist
            conc_names = {c.name for c in b.concentrates}
            assert any("Part A" in n for n in conc_names)
            assert any("Part B" in n for n in conc_names)


def test_consolidate_respects_max_products_per_blend():
    """No blend should have more than MAX_PRODUCTS_PER_BLEND raw products."""
    targets = {"N": 100, "P2O5": 40, "K2O": 80, "Ca": 60, "S": 20, "Mg": 5}
    splits = split_season_targets("Garlic", targets, stage_count=5)
    avail = MethodAvailability(has_drip=True)
    assignments = select_methods(splits, avail)

    blends = consolidate_blends(
        assignments=assignments, available_materials=LIQUID_MATERIALS,
        block_id="land_a", block_area_ha=1.11,
    )
    for b in blends:
        assert len(b.raw_products) <= MAX_PRODUCTS_PER_BLEND


def test_consolidate_nutrients_delivered_populated():
    targets = {"N": 100, "P2O5": 40, "K2O": 80}
    splits = split_season_targets("Garlic", targets, stage_count=5)
    avail = MethodAvailability(has_drip=True)
    assignments = select_methods(splits, avail)

    blends = consolidate_blends(
        assignments=assignments, available_materials=LIQUID_MATERIALS,
        block_id="land_a", block_area_ha=1.11,
    )
    # At least one blend should deliver meaningful N
    assert any(b.nutrients_delivered.get("N", 0) > 1 for b in blends)


# ============================================================
# Dry consolidation (dryland maize)
# ============================================================

def test_dry_blends_have_no_concentrates():
    targets = {"N": 90, "P2O5": 45, "K2O": 30}
    splits = split_season_targets("Maize (dryland)", targets, stage_count=4)
    avail = MethodAvailability(
        has_drip=False, has_foliar_sprayer=False, has_granular_spreader=True,
    )
    assignments = select_methods(splits, avail)

    blends = consolidate_blends(
        assignments=assignments, available_materials=DRY_MATERIALS,
        block_id="fs", block_area_ha=80,
    )
    for b in blends:
        # Dry blends have no Part A/B concentrates
        assert b.concentrates == []


def test_dry_blend_uses_dry_materials():
    targets = {"N": 90, "P2O5": 45, "K2O": 30}
    splits = split_season_targets("Maize (dryland)", targets, stage_count=4)
    avail = MethodAvailability(
        has_drip=False, has_foliar_sprayer=False, has_granular_spreader=True,
    )
    assignments = select_methods(splits, avail)

    blends = consolidate_blends(
        assignments=assignments, available_materials=DRY_MATERIALS,
        block_id="fs", block_area_ha=80,
    )
    dry_product_names = {m["material"] for m in DRY_MATERIALS}
    for b in blends:
        for part in b.raw_products:
            assert part.product in dry_product_names


def test_dry_blend_parts_have_no_stream():
    targets = {"N": 90, "P2O5": 45, "K2O": 30}
    splits = split_season_targets("Maize (dryland)", targets, stage_count=4)
    avail = MethodAvailability(has_granular_spreader=True, has_drip=False)
    assignments = select_methods(splits, avail)
    blends = consolidate_blends(
        assignments=assignments, available_materials=DRY_MATERIALS,
        block_id="fs", block_area_ha=80,
    )
    for b in blends:
        for part in b.raw_products:
            assert part.stream is None


# ============================================================
# Stage schedule integration
# ============================================================

def test_events_and_dates_populated_from_schedule():
    """When StageSchedule provided, blend events + weeks labels populate."""
    targets = {"N": 100, "K2O": 80}
    splits = split_season_targets("Garlic", targets, stage_count=5)
    avail = MethodAvailability(has_drip=True)
    assignments = select_methods(splits, avail)

    schedule = [
        StageWindow(stage_number=1, stage_name="establishment",
                    week_start=3, week_end=7,
                    date_start=date(2026, 5, 13), date_end=date(2026, 6, 16),
                    events=5),
        StageWindow(stage_number=2, stage_name="vegetative",
                    week_start=8, week_end=15,
                    date_start=date(2026, 6, 17), date_end=date(2026, 8, 11),
                    events=8),
        StageWindow(stage_number=3, stage_name="reproductive",
                    week_start=16, week_end=19,
                    date_start=date(2026, 8, 12), date_end=date(2026, 9, 8),
                    events=4),
        StageWindow(stage_number=4, stage_name="fill",
                    week_start=20, week_end=23,
                    date_start=date(2026, 9, 9), date_end=date(2026, 10, 6),
                    events=4),
        StageWindow(stage_number=5, stage_name="maturation",
                    week_start=24, week_end=25,
                    date_start=date(2026, 10, 7), date_end=date(2026, 10, 20),
                    events=2),
    ]

    blends = consolidate_blends(
        assignments=assignments, available_materials=LIQUID_MATERIALS,
        block_id="land_a", block_area_ha=1.11,
        stage_schedule=schedule,
    )

    # Each blend should have events + weeks populated
    stage_1 = next((b for b in blends if b.stage_number == 1), None)
    assert stage_1 is not None
    assert stage_1.events == 5
    assert "3" in stage_1.weeks or "7" in stage_1.weeks
    assert "May" in stage_1.dates_label or "Jun" in stage_1.dates_label


# ============================================================
# Greedy algorithm correctness
# ============================================================

def test_empty_assignments_produce_no_blends():
    blends = consolidate_blends(
        assignments=[], available_materials=LIQUID_MATERIALS,
        block_id="b1", block_area_ha=1.0,
    )
    assert blends == []


def test_no_liquid_compatible_materials_still_returns_blends_for_dry():
    """If only dry materials provided but assignments are dry → works fine."""
    targets = {"N": 50}
    splits = split_season_targets("Maize (dryland)", targets, stage_count=3)
    avail = MethodAvailability(has_drip=False, has_granular_spreader=True)
    assignments = select_methods(splits, avail)

    blends = consolidate_blends(
        assignments=assignments, available_materials=DRY_MATERIALS,
        block_id="fs", block_area_ha=50,
    )
    # Should produce blends (dry materials available)
    assert len(blends) > 0


def test_blend_typed_method_matches_method_kind():
    """Liquid assignments → FertigationMethod; dry → DryBlendMethod."""
    targets = {"N": 100}
    splits = split_season_targets("Garlic", targets, stage_count=3)
    liquid_avail = MethodAvailability(has_drip=True)
    dry_avail = MethodAvailability(has_drip=False, has_granular_spreader=True)

    liquid_assignments = select_methods(splits, liquid_avail)
    dry_assignments = select_methods(splits, dry_avail)

    liquid_blends = consolidate_blends(
        liquid_assignments, LIQUID_MATERIALS, "b1", 1.0,
    )
    dry_blends = consolidate_blends(
        dry_assignments, DRY_MATERIALS, "b1", 1.0,
    )

    assert any(isinstance(b.method, FertigationMethod) for b in liquid_blends)
    assert all(b.method.kind.name.startswith("DRY_") for b in dry_blends)


# ============================================================
# Helpers
# ============================================================

def _is_fertigation_blend(b: Blend) -> bool:
    return b.method.kind in (
        MethodKind.LIQUID_DRIP,
        MethodKind.LIQUID_PIVOT,
        MethodKind.LIQUID_SPRINKLER,
    )
