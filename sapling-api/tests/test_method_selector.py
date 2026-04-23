"""Tests for Phase 2 Method Selector — routing (stage × nutrient × kg/ha)
to a method given MethodAvailability + soil-factor findings."""
from __future__ import annotations

import pytest

from app.models import MethodAvailability, MethodKind
from app.services.method_selector import (
    FOLIAR_SINGLE_EVENT_CAP_KG_HA,
    MethodAssignment,
    aggregate_by_method,
    select_methods,
)
from app.services.soil_factor_reasoner import reason_soil_factors
from app.services.stage_splitter import split_season_targets


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def clivia_splits():
    targets = {"N": 155, "P2O5": 86, "K2O": 173, "Ca": 176, "S": 67}
    return split_season_targets(crop="Garlic", season_targets=targets, stage_count=5)


@pytest.fixture
def clivia_avail():
    """Clivia has drip + foliar + granular."""
    return MethodAvailability(
        has_drip=True, has_foliar_sprayer=True,
        has_granular_spreader=True,
    )


@pytest.fixture
def clivia_al_report():
    soil = {"Al": 851, "Ca": 1025, "Mg": 242, "K": 227, "Na": 10,
            "P (Mehlich-3)": 2, "Zn": 1.26, "B": 0.36}
    return reason_soil_factors(soil, crop="Garlic")


# ============================================================
# Basic routing
# ============================================================

def test_every_stage_nutrient_gets_at_least_one_method(clivia_splits, clivia_avail):
    assignments = select_methods(clivia_splits, clivia_avail)
    # Build (stage, nutrient) coverage set
    covered = {(a.stage_number, a.nutrient) for a in assignments}
    for split in clivia_splits:
        for nutrient, kg in split.nutrients.items():
            if kg > 0:
                assert (split.stage_number, nutrient) in covered


def test_every_assignment_has_reason(clivia_splits, clivia_avail):
    assignments = select_methods(clivia_splits, clivia_avail)
    for a in assignments:
        assert a.reason
        assert isinstance(a.method, MethodKind)


# ============================================================
# Method-availability logic
# ============================================================

def test_drip_only_farm_routes_macros_to_drip(clivia_splits):
    avail = MethodAvailability(has_drip=True, has_granular_spreader=False,
                                has_foliar_sprayer=False)
    assignments = select_methods(clivia_splits, avail)
    n_assignments = [a for a in assignments if a.nutrient == "N"]
    assert all(a.method == MethodKind.LIQUID_DRIP for a in n_assignments)


def test_dry_only_farm_routes_macros_to_dry(clivia_splits):
    avail = MethodAvailability(has_drip=False, has_granular_spreader=True,
                                has_foliar_sprayer=False)
    assignments = select_methods(clivia_splits, avail)
    n_assignments = [a for a in assignments if a.nutrient == "N"]
    # Establishment stage → broadcast; later stages → side-dress
    methods = {a.method for a in n_assignments}
    assert MethodKind.DRY_BROADCAST in methods or MethodKind.DRY_SIDE_DRESS in methods


def test_foliar_only_farm_caps_macros(clivia_splits):
    """Farm with only foliar — macros get capped at foliar single-event limit."""
    avail = MethodAvailability(has_drip=False, has_granular_spreader=False,
                                has_foliar_sprayer=True)
    assignments = select_methods(clivia_splits, avail)
    # N stage demand is often > 5 kg; foliar cap is 5 → we should see assignments
    # capped at 5 kg rather than 30+
    foliar_n = [a for a in assignments if a.nutrient == "N"
                and a.method == MethodKind.FOLIAR]
    for a in foliar_n:
        assert a.kg_per_ha <= FOLIAR_SINGLE_EVENT_CAP_KG_HA["N"] + 0.01


# ============================================================
# Soil-factor priority: P:Zn lockup → foliar Zn
# ============================================================

def test_p_zn_lockup_redirects_zn_to_foliar():
    """Soil with P:Zn > 150 — Zn should route to foliar first."""
    soil = {"P (Bray-1)": 120, "Zn": 0.5}  # ratio 240
    report = reason_soil_factors(soil, crop="Maize (dryland)")
    targets = {"Zn": 2.0}
    splits = split_season_targets(crop="Maize (dryland)", season_targets=targets, stage_count=5)
    avail = MethodAvailability(has_drip=True, has_foliar_sprayer=True,
                                has_granular_spreader=True)
    assignments = select_methods(splits, avail, soil_factor_report=report)
    zn_foliar = [a for a in assignments if a.nutrient == "Zn"
                 and a.method == MethodKind.FOLIAR]
    assert len(zn_foliar) > 0
    # Reason mentions soil availability
    assert any("availability" in a.reason.lower() for a in zn_foliar)


def test_no_p_zn_lockup_allows_non_foliar_zn():
    """Low P:Zn — Zn can go any route including drip."""
    soil = {"P (Bray-1)": 30, "Zn": 5}  # ratio 6, healthy
    report = reason_soil_factors(soil, crop="Maize (dryland)")
    targets = {"Zn": 2.0}
    splits = split_season_targets(crop="Maize (dryland)", season_targets=targets, stage_count=5)
    avail = MethodAvailability(has_drip=True, has_foliar_sprayer=True,
                                has_granular_spreader=True)
    assignments = select_methods(splits, avail, soil_factor_report=report)
    # Without lockup, Zn routes to foliar by default (micro), not forced
    # No "availability gap" reason in assignments
    for a in assignments:
        if a.nutrient == "Zn":
            assert "availability gap" not in a.reason.lower()


# ============================================================
# Pre-plant P preference for basal
# ============================================================

def test_preplant_p_prefers_broadcast_over_drip():
    """Pre-plant/establishment P should go DRY_BROADCAST if available."""
    targets = {"P2O5": 60}
    splits = split_season_targets(crop="Wheat", season_targets=targets, stage_count=5)
    avail = MethodAvailability(has_drip=True, has_foliar_sprayer=True,
                                has_granular_spreader=True)
    assignments = select_methods(splits, avail)
    # First stage = establishment
    stage1_p = [a for a in assignments if a.stage_number == 1 and a.nutrient == "P2O5"]
    assert len(stage1_p) >= 1
    assert stage1_p[0].method == MethodKind.DRY_BROADCAST
    assert "basal" in stage1_p[0].reason.lower() or "root uptake" in stage1_p[0].reason.lower()


def test_in_season_ca_prefers_drip_for_al_antagonism():
    """In-season Ca preferred via drip (Calcium Nitrate) — Al antagonism benefit."""
    targets = {"Ca": 100}
    splits = split_season_targets(crop="Garlic", season_targets=targets, stage_count=5)
    avail = MethodAvailability(has_drip=True, has_granular_spreader=True)
    assignments = select_methods(splits, avail)
    # Non-establishment stage Ca should go drip
    stage3_ca = [a for a in assignments if a.stage_number == 3 and a.nutrient == "Ca"]
    if stage3_ca:
        assert stage3_ca[0].method == MethodKind.LIQUID_DRIP


# ============================================================
# Foliar cap + remainder routing
# ============================================================

def test_foliar_micro_cap_routes_remainder():
    """If Zn lockup stage demand > foliar cap → foliar gets cap, rest to drip."""
    soil = {"P (Bray-1)": 120, "Zn": 0.5}  # lockup triggers foliar priority
    report = reason_soil_factors(soil, crop="Maize (dryland)")
    # Season Zn unusually high → stage-level demand exceeds foliar cap (1.0)
    targets = {"Zn": 20}
    splits = split_season_targets(crop="Maize (dryland)", season_targets=targets, stage_count=5)
    avail = MethodAvailability(has_drip=True, has_foliar_sprayer=True,
                                has_granular_spreader=True)
    assignments = select_methods(splits, avail, soil_factor_report=report)
    # Each stage should have BOTH foliar (capped) + remainder route
    for stage in range(1, 6):
        stage_zn = [a for a in assignments if a.stage_number == stage and a.nutrient == "Zn"]
        if sum(a.kg_per_ha for a in stage_zn) > 1.0:
            # Multiple methods expected
            methods = {a.method for a in stage_zn}
            assert len(methods) >= 2  # foliar + soil


# ============================================================
# Aggregation helper
# ============================================================

def test_aggregate_by_method_groups_correctly(clivia_splits, clivia_avail):
    assignments = select_methods(clivia_splits, clivia_avail)
    agg = aggregate_by_method(assignments)
    # Every key is (int stage_num, MethodKind)
    for key in agg:
        assert isinstance(key[0], int)
        assert isinstance(key[1], MethodKind)
    # Values are {nutrient: float}
    for nutrients in agg.values():
        for v in nutrients.values():
            assert isinstance(v, float)
            assert v >= 0


def test_clivia_vertical_slice_end_to_end(clivia_splits, clivia_avail, clivia_al_report):
    """Clivia Land A: soil → splitter → method-selector → full method plan."""
    assignments = select_methods(
        clivia_splits, clivia_avail,
        soil_factor_report=clivia_al_report,
        crop_family="bulb",
    )
    # Full coverage
    assert len(assignments) >= 10  # 5 stages × ~5 nutrients
    # Drip should be used for macros
    macro_assignments = [a for a in assignments if a.nutrient in ("N", "K2O")]
    drip_macro = [a for a in macro_assignments if a.method == MethodKind.LIQUID_DRIP]
    assert len(drip_macro) > 0
    # Every assignment has provenance
    assert all(a.reason and isinstance(a.tier, int) for a in assignments)
