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
    MIN_ORGANIC_FRACTION_DRY,
    ORGANIC_CARRIER_STARTER_KG_HA,
    _classify_stream,
    _find_organic_carrier,
    _is_organic_carrier,
    _select_materials_greedy,
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
# Organic carrier policy (A3) — ≥ 50 % organic on dry blends
# ============================================================

# Mirrors the production Manure Compost row: type Organic, solid, with
# carbon and macros bundled. The defining product for Sapling's house
# rule.
ORGANIC_CARRIER = {
    "material": "Manure Compost",
    "type": "Organic",
    "form": "solid",
    "n": 2.13, "p": 1.01, "k": 1.64,
    "ca": 2.2, "mg": 1.0, "s": 0.7,
    "b": 0.065, "zn": 0.053, "mn": 0.048, "cu": 0.053, "fe": 0.0, "mo": 0.0,
    "c": 35.0,
    "liquid_compatible": False, "foliar_compatible": False,
}

# Liquid organic — must NOT be picked up as the dry-blend carrier.
LIQUID_ORGANIC = {
    "material": "Liquid Molasses",
    "type": "Organic",
    "form": "liquid",
    "n": 0.0, "p": 0.0, "k": 0.0,
    "ca": 0.0, "mg": 0.0, "s": 0.0,
    "b": 4.3, "zn": 4.1, "mn": 1.2, "cu": 1.0,
    "c": 40.0,
    "liquid_compatible": True, "foliar_compatible": False,
}


def test_is_organic_carrier_identifies_solid_manure():
    assert _is_organic_carrier(ORGANIC_CARRIER) is True


def test_is_organic_carrier_rejects_liquid_organics():
    """Liquid molasses is Organic but liquid — not a bulk dry carrier."""
    assert _is_organic_carrier(LIQUID_ORGANIC) is False


def test_is_organic_carrier_rejects_synthetic():
    assert _is_organic_carrier(DRY_MATERIALS[0]) is False  # Urea


def test_is_organic_carrier_rejects_organic_without_carbon():
    """A bio-stimulant acid with no carbon isn't a carrier."""
    mat = {"type": "Organic", "form": "solid", "n": 0.0, "c": 0.0}
    assert _is_organic_carrier(mat) is False


def test_find_organic_carrier_prefers_highest_carbon():
    """When multiple carriers exist, pick the one with the most carbon
    (best multi-year soil-building return)."""
    low_c = {**ORGANIC_CARRIER, "material": "Low-C Compost", "c": 15.0}
    high_c = {**ORGANIC_CARRIER, "material": "High-C Compost", "c": 40.0}
    picked = _find_organic_carrier([low_c, high_c, DRY_MATERIALS[0]])
    assert picked is not None
    assert picked["material"] == "High-C Compost"


def test_find_organic_carrier_returns_none_when_absent():
    assert _find_organic_carrier(DRY_MATERIALS) is None


def test_dry_blend_anchors_with_organic_carrier():
    """Dry blend with an organic carrier in the pool seeds it at the
    starter rate and uses its Y1-available nutrients to reduce deficit."""
    materials = DRY_MATERIALS + [ORGANIC_CARRIER]
    selected = _select_materials_greedy(
        nutrient_targets={"N": 60, "P2O5": 30, "K2O": 50},
        available_materials=materials,
        method_kind=MethodKind.DRY_BROADCAST,
    )
    # Organic must be in the selection
    organic = next(
        ((m, r) for m, r in selected if m["material"] == "Manure Compost"),
        None,
    )
    assert organic is not None, "Organic carrier must anchor the dry blend"
    # Rate must be at least the starter (may be bumped higher)
    _, organic_rate = organic
    assert organic_rate >= ORGANIC_CARRIER_STARTER_KG_HA


def test_dry_blend_organic_fraction_at_or_above_50pct():
    """After the full greedy pass, organic mass ≥ 50 % of total blend mass."""
    materials = DRY_MATERIALS + [ORGANIC_CARRIER]
    selected = _select_materials_greedy(
        nutrient_targets={"N": 120, "P2O5": 40, "K2O": 80},
        available_materials=materials,
        method_kind=MethodKind.DRY_BROADCAST,
    )
    total_mass = sum(rate for _, rate in selected)
    organic_mass = sum(
        rate for mat, rate in selected
        if mat["material"] == "Manure Compost"
    )
    assert organic_mass >= total_mass * MIN_ORGANIC_FRACTION_DRY - 0.01, (
        f"Organic fraction {organic_mass/total_mass:.1%} below 50 % floor"
    )


def test_dry_blend_organic_bumps_when_synthetic_exceeds_starter():
    """When synthetic mass ends up > starter organic rate, organic rate
    bumps to match so the 50 % rule is preserved exactly."""
    # High N demand → lots of synthetic → synthetic mass will exceed 500 kg
    materials = DRY_MATERIALS + [ORGANIC_CARRIER]
    selected = _select_materials_greedy(
        nutrient_targets={"N": 300, "P2O5": 150, "K2O": 200},
        available_materials=materials,
        method_kind=MethodKind.DRY_BROADCAST,
    )
    synthetic_mass = sum(
        rate for mat, rate in selected
        if mat["material"] != "Manure Compost"
    )
    organic_mass = sum(
        rate for mat, rate in selected
        if mat["material"] == "Manure Compost"
    )
    # Organic should be bumped to >= synthetic mass
    assert organic_mass >= synthetic_mass - 0.01


def test_fertigation_blend_does_NOT_anchor_organic():
    """50 % rule applies only to dry blends. Fertigation is a liquid
    pipeline — solid carrier can't go in the stock tank."""
    materials = LIQUID_MATERIALS + [ORGANIC_CARRIER]
    selected = _select_materials_greedy(
        nutrient_targets={"N": 100, "K2O": 80},
        available_materials=materials,
        method_kind=MethodKind.LIQUID_DRIP,
    )
    # Liquid-compat filter would already drop the solid organic; this
    # doubly confirms — organic must not appear in a fertigation blend
    organic_picked = any(m["material"] == "Manure Compost" for m, _ in selected)
    assert organic_picked is False


def test_foliar_blend_does_NOT_anchor_organic():
    """Foliar is not a dry blend either."""
    materials = FOLIAR_MATERIALS + [ORGANIC_CARRIER]
    selected = _select_materials_greedy(
        nutrient_targets={"B": 0.4, "Zn": 1.0},
        available_materials=materials,
        method_kind=MethodKind.FOLIAR,
    )
    organic_picked = any(m["material"] == "Manure Compost" for m, _ in selected)
    assert organic_picked is False


def test_dry_blend_with_no_organic_available_falls_back_to_synthetic():
    """When no organic carrier is in the pool, the dry blend still
    produces a valid synthetic-only cover — no hard failure."""
    selected = _select_materials_greedy(
        nutrient_targets={"N": 100, "P2O5": 40, "K2O": 60},
        available_materials=DRY_MATERIALS,  # no organic
        method_kind=MethodKind.DRY_BROADCAST,
    )
    assert len(selected) > 0
    assert all(m["type"] != "Organic" for m, _ in selected)


# ============================================================
# Helpers
# ============================================================

def _is_fertigation_blend(b: Blend) -> bool:
    return b.method.kind in (
        MethodKind.LIQUID_DRIP,
        MethodKind.LIQUID_PIVOT,
        MethodKind.LIQUID_SPRINKLER,
    )
