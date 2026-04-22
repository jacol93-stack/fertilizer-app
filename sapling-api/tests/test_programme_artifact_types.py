"""
Basic smoke tests for the Phase 1 Programme Artifact types.

Locks in that the models instantiate, serialize to JSON, round-trip,
and enforce their validation rules. Phase 2 builds real engine logic
against these types; these tests guard the interface contract.
"""
from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.models import (
    ApplicationMethod,
    Assumption,
    Blend,
    BlendPart,
    Concentrate,
    ConfidenceBand,
    CropVariant,
    DataCompleteness,
    FertigationMethod,
    FoliarEvent,
    FoliarMethod,
    MethodAvailability,
    MethodKind,
    OutstandingItem,
    PreSeasonInput,
    ProgrammeArtifact,
    ProgrammeHeader,
    ProgrammeState,
    ReplanReason,
    RiskFlag,
    ShoppingListEntry,
    SoilSnapshot,
    Source,
    SourceCitation,
    SourceRegistry,
    StageSchedule,
    StageWindow,
    Tier,
    VariantKey,
)


# ============================================================
# Tier + DataCompleteness
# ============================================================

def test_tier_labels():
    assert Tier.SA_INDUSTRY_BODY == 1
    assert Tier.SA_INDUSTRY_BODY.label == "SA industry body"
    assert Tier.IMPLEMENTER_CONVENTION == 6
    assert Tier.IMPLEMENTER_CONVENTION.label == "Implementer convention"


def test_data_completeness_bands():
    minimum = DataCompleteness(level="minimum")
    standard = DataCompleteness(level="standard")
    high = DataCompleteness(level="high")

    assert minimum.confidence_pct_band == (20.0, 30.0)
    assert standard.confidence_pct_band == (10.0, 15.0)
    assert high.confidence_pct_band == (5.0, 10.0)


def test_confidence_band_validation():
    band = ConfidenceBand(pct_low=10, pct_high=15, tier=Tier.SA_INDUSTRY_BODY,
                          driver="complete-tier-1-data")
    assert band.pct_low == 10
    assert band.tier == Tier.SA_INDUSTRY_BODY

    with pytest.raises(ValidationError):
        ConfidenceBand(pct_low=-5, pct_high=10, tier=Tier.SA_INDUSTRY_BODY, driver="x")


# ============================================================
# Source registry
# ============================================================

def test_source_registry_roundtrip():
    SourceRegistry.clear()
    s = Source(id="FERTASA_5_6_1", name="FERTASA", section="5.6.1",
               title="General Vegetables", year=2019, tier=1)
    SourceRegistry.register(s)

    got = SourceRegistry.get("FERTASA_5_6_1")
    assert got is not None
    assert got.tier == 1
    assert got.section == "5.6.1"
    assert SourceRegistry.get("nope") is None


def test_source_tier_range():
    with pytest.raises(ValidationError):
        Source(id="x", name="y", tier=7)  # tier must be 1-6


# ============================================================
# Method taxonomy
# ============================================================

def test_method_availability_kinds():
    avail = MethodAvailability(has_drip=True, has_foliar_sprayer=True)
    kinds = avail.available_kinds()
    assert MethodKind.LIQUID_DRIP in kinds
    assert MethodKind.FOLIAR in kinds
    assert MethodKind.DRY_BROADCAST in kinds  # default granular spreader
    # Dry fertigation requires injectors — not set
    assert MethodKind.DRY_FERTIGATION not in kinds


def test_fertigation_method():
    m = FertigationMethod(
        kind=MethodKind.LIQUID_DRIP,
        concentrate_strength_g_per_l=300.0,
        ec_target_ms_per_cm=(2.0, 2.5),
        ph_target=(5.5, 6.5),
        part_a_required=True,
        part_b_required=True,
    )
    assert m.kind == MethodKind.LIQUID_DRIP
    assert m.part_a_required is True


def test_foliar_method():
    m = FoliarMethod(
        spray_volume_l_per_ha=(200, 300),
        tank_mix_ph=(5.0, 6.0),
    )
    assert m.kind == MethodKind.FOLIAR
    assert m.adjuvant  # default non-ionic wetter


# ============================================================
# Variants
# ============================================================

def test_variant_key_lookup_chain():
    # Variant with parent
    vk = VariantKey(canonical_crop="Maize (dryland)", parent_crop="Maize", cycle="dryland")
    assert vk.lookup_chain() == ["Maize (dryland)", "Maize"]

    # Crop that's its own parent (no variant)
    vk2 = VariantKey(canonical_crop="Wheat")
    assert vk2.lookup_chain() == ["Wheat"]


def test_crop_variant_model():
    cv = CropVariant(
        crop="Maize (dryland)",
        type="Annual",
        crop_type="annual",
        parent_crop="Maize",
        yield_unit="t grain/ha",
        default_yield=5.0,
    )
    assert cv.parent_crop == "Maize"


# ============================================================
# Programme Artifact end-to-end
# ============================================================

def _minimal_artifact() -> ProgrammeArtifact:
    src = SourceCitation(source_id="FERTASA_5_6_1", section="5.6.1",
                         tier=Tier.SA_INDUSTRY_BODY)
    header = ProgrammeHeader(
        client_name="Clivia Boerdery",
        farm_name="Klein Overberg",
        prepared_for="Wieland Jordaan",
        prepared_date=date(2026, 4, 21),
        crop="Garlic",
        variant_key=VariantKey(canonical_crop="Garlic"),
        season="Autumn 2026",
        planting_date=date(2026, 4, 29),
        expected_harvest_date=date(2026, 10, 25),
        data_completeness=DataCompleteness(level="standard"),
        method_availability=MethodAvailability(has_drip=True, has_foliar_sprayer=True),
        ref_number="WJ60421",
    )
    return ProgrammeArtifact(
        header=header,
        soil_snapshots=[
            SoilSnapshot(
                block_id="land_a",
                block_name="Land A",
                block_area_ha=1.11,
                lab_name="NViroTek",
                lab_method="Mehlich-3",
                sample_date=date(2026, 2, 2),
                parameters={"pH_H2O": 5.38, "P": 2.0, "K": 227.0, "Al": 851.0},
                headline_signals=["Al saturation high", "P critical", "S low"],
            ),
        ],
        stage_schedules=[],
    )


def test_programme_artifact_instantiates():
    a = _minimal_artifact()
    assert a.header.crop == "Garlic"
    assert a.header.state == ProgrammeState.DRAFT
    assert a.header.replan_reason == ReplanReason.FIRST_PASS
    assert len(a.soil_snapshots) == 1
    assert a.soil_snapshots[0].parameters["P"] == 2.0


def test_programme_artifact_json_roundtrip():
    a = _minimal_artifact()
    j = a.model_dump_json()
    round_tripped = ProgrammeArtifact.model_validate_json(j)
    assert round_tripped.header.crop == a.header.crop
    assert round_tripped.header.planting_date == a.header.planting_date
    assert round_tripped.soil_snapshots[0].block_name == "Land A"


def test_foliar_event_requires_positive_trigger():
    """Foliar is CONTINGENT — every event must carry its trigger reason."""
    event = FoliarEvent(
        block_id="land_a",
        event_number=1,
        week=6,
        spray_date=date(2026, 6, 5),
        stage_name="Vegetative I",
        product="Zinc Sulphate",
        analysis="36% Zn",
        rate_per_ha="1 kg",
        total_for_block="1.1 kg",
        trigger_reason="Soil Zn 1.26 mg/kg below garlic-crit 5 mg/kg; pH 5.38 restricts root uptake",
        trigger_kind="soil_availability_gap",
        source=SourceCitation(source_id="SAMAC_FOLIAR", tier=Tier.SA_INDUSTRY_BODY),
    )
    assert event.trigger_reason  # must be non-empty by contract


def test_assumption_defaults_tier_6():
    a = Assumption(
        field="cultivar",
        assumed_value="standard SA white (Germidour)",
        override_guidance="For elephant garlic, raise K₂O by ~20%",
    )
    assert a.tier == Tier.IMPLEMENTER_CONVENTION


def test_outstanding_item():
    o = OutstandingItem(
        item="Irrigation water test",
        why_it_matters="EC, pH, Ca, Mg, Na, HCO₃, Cl — critical before first Part A injection",
        impact_if_skipped="Scale risk in drip lines when Ca-Nitrate meets dolomite water",
    )
    assert o.item


def test_programme_state_transitions():
    """State machine values exist for the lifecycle we described."""
    for s in [ProgrammeState.DRAFT, ProgrammeState.APPROVED,
              ProgrammeState.ACTIVATED, ProgrammeState.IN_PROGRESS,
              ProgrammeState.COMPLETED, ProgrammeState.ARCHIVED]:
        assert s.value


def test_replan_reason_enum():
    for r in [ReplanReason.FIRST_PASS, ReplanReason.LEAF_ANALYSIS,
              ReplanReason.OFF_PROGRAMME_APPLICATION]:
        assert r.value
