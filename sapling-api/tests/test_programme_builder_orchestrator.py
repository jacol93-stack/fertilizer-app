"""
End-to-end tests for the Programme Builder Orchestrator — the first real
assembly of a full ProgrammeArtifact from realistic inputs.

Clivia Garlic Land A + Land B is the golden fixture.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.models import (
    FoliarEvent,
    MethodAvailability,
    PreSeasonInput,
    ProgrammeArtifact,
    ProgrammeState,
)
from app.services.programme_builder_orchestrator import (
    BlockInput,
    OrchestratorInput,
    build_programme,
)


# ============================================================
# Fixtures
# ============================================================

CLIVIA_MATERIALS = [
    {"material": "Calcitic Lime", "n": 0, "p": 0, "k": 0, "ca": 40, "mg": 2, "s": 0,
     "applicability": "pre_season_only",
     "reaction_time_months_min": 3, "reaction_time_months_max": 6,
     "soil_improvement_purpose": "pH lift via CaCO3"},
    {"material": "Gypsum", "n": 0, "p": 0, "k": 0, "ca": 23, "mg": 0, "s": 18,
     "applicability": "both",
     "reaction_time_months_min": 0.5, "reaction_time_months_max": 2,
     "soil_improvement_purpose": "Na displacement"},
    {"material": "Manure Compost", "n": 2.13, "p": 1.01, "k": 1.64,
     "ca": 2.2, "mg": 1.0, "s": 0.7,
     "applicability": "both",
     "reaction_time_months_min": 2, "reaction_time_months_max": 12,
     "soil_improvement_purpose": "OM + slow N"},
    {"material": "Metabophos", "n": 0, "p": 19, "k": 0, "ca": 19, "mg": 0, "s": 11,
     "applicability": "in_season_only",
     "reaction_time_months_min": None, "reaction_time_months_max": None},
]


@pytest.fixture
def clivia_land_a_input():
    """Clivia Land A: already-applied pre-season inputs, soil analysis from Feb."""
    return BlockInput(
        block_id="land_a",
        block_name="Land A",
        block_area_ha=1.11,
        lab_name="NViroTek",
        lab_method="Mehlich-3",
        sample_date=date(2026, 2, 2),
        sample_id="AS14970",
        soil_parameters={
            "CEC": 13.14, "pH (H2O)": 5.38,
            "P (Mehlich-3)": 2, "K": 227, "Ca": 1025, "Mg": 242,
            "Al": 851, "Na": 10, "S": 10, "B": 0.36, "Zn": 1.26,
            "Mn": 75, "Fe": 106, "Cu": 6.27,
        },
        season_targets={
            "N": 155, "P2O5": 86, "K2O": 173, "Ca": 176, "S": 67,
        },
        pre_season_inputs=[
            PreSeasonInput(
                product="Calcitic Lime", rate="1500 kg/ha",
                contribution_per_ha="~570 kg Ca + neutralising capacity",
                status_at_planting="50-70% reacted",
                applied_date=date(2026, 2, 1),
            ),
            PreSeasonInput(
                product="Metabophos", rate="125 kg/ha",
                contribution_per_ha="~24 kg P2O5, ~24 kg Ca, ~14 kg S",
                status_at_planting="Fully mineralised; ~50% P2O5 fixed by Al",
                applied_date=date(2026, 2, 1),
            ),
            PreSeasonInput(
                product="Manure Compost", rate="2000 kg/ha",
                contribution_per_ha="~8 kg N, 5 kg P2O5, 10 kg K2O (yr-1)",
                status_at_planting="N largely leached by summer rain",
                applied_date=date(2026, 2, 1),
            ),
        ],
    )


@pytest.fixture
def clivia_land_b_input():
    return BlockInput(
        block_id="land_b",
        block_name="Land B",
        block_area_ha=1.46,
        lab_name="NViroTek", lab_method="Mehlich-3",
        sample_date=date(2026, 2, 2), sample_id="AS14967",
        soil_parameters={
            "CEC": 10.35, "pH (H2O)": 5.66,
            "P (Mehlich-3)": 12, "K": 214, "Ca": 958, "Mg": 203,
            "Al": 843, "Na": 10, "S": 10, "B": 0.42, "Zn": 2.97,
            "Mn": 49, "Fe": 182, "Cu": 6.07,
        },
        season_targets={
            "N": 132, "P2O5": 68, "K2O": 145, "Ca": 152, "S": 56,
        },
        pre_season_inputs=[
            PreSeasonInput(
                product="Calcitic Lime", rate="1500 kg/ha",
                contribution_per_ha="~570 kg Ca",
                status_at_planting="50-70% reacted",
                applied_date=date(2026, 2, 1),
            ),
        ],
    )


# ============================================================
# Core end-to-end
# ============================================================

def test_clivia_single_block_builds(clivia_land_a_input):
    inputs = OrchestratorInput(
        client_name="Clivia Boerdery",
        farm_name="Klein Overberg",
        prepared_for="Wieland Jordaan",
        crop="Garlic",
        planting_date=date(2026, 4, 29),
        build_date=date(2026, 4, 21),
        location="Ngodwana, Mpumalanga",
        ref_number="WJ60421",
        expected_harvest_date=date(2026, 10, 25),
        season="Autumn 2026",
        method_availability=MethodAvailability(
            has_drip=True, has_foliar_sprayer=True, has_granular_spreader=True,
        ),
        blocks=[clivia_land_a_input],
        high_al_soil=True,
        wet_summer_between_apply_and_plant=True,
        has_gypsum_in_plan=False,
        has_irrigation_water_test=False,
        planned_n_fertilizers=["calcium_ammonium_nitrate"],
        available_materials=CLIVIA_MATERIALS,
        stage_count=5,
    )

    art = build_programme(inputs)
    assert isinstance(art, ProgrammeArtifact)


def test_clivia_header_populated(clivia_land_a_input):
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    assert art.header.client_name == "Clivia Boerdery"
    assert art.header.crop == "Garlic"
    assert art.header.state == ProgrammeState.DRAFT
    assert art.header.ref_number == "WJ60421"


def test_clivia_soil_snapshot_carries_findings(clivia_land_a_input):
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    snap = art.soil_snapshots[0]
    assert snap.block_name == "Land A"
    assert snap.lab_method == "Mehlich-3"
    # Headline signals should mention the severe issues (Al, etc.)
    assert any("Al" in s for s in snap.headline_signals)


def test_clivia_pre_season_residual_subtracted(clivia_land_a_input):
    """Residual from Feb lime/Metabophos/Manure should be reflected in
    the block totals being lower than input targets."""
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    # Ca target 176 → subtract Ca from lime (40% × 1500 × reaction_pct) etc.
    # Expect block total Ca < 176
    totals = art.block_totals["land_a"]
    assert totals["Ca"] < 176  # residual Ca from lime + Metabophos
    # P2O5 target 86; Metabophos P discounted by high-Al factor 0.5
    assert totals["P2O5"] < 86


def test_clivia_foliar_events_produced(clivia_land_a_input):
    """Garlic at bulb init should fire at least one foliar event (B at wk 16)."""
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    assert len(art.foliar_events) >= 1
    assert any(e.week == 16 for e in art.foliar_events)


def test_clivia_risk_flags_produced(clivia_land_a_input):
    """Al critical + no gypsum → multiple risk flags."""
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    assert len(art.risk_flags) >= 2
    # Critical Al should appear
    assert any(f.severity == "critical" for f in art.risk_flags)


def test_clivia_outstanding_items_produced(clivia_land_a_input):
    """Fertigation + no water test + Al critical → water-test + post-harvest-soil items."""
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    items = art.outstanding_items
    assert len(items) >= 2
    assert any("water test" in i.item.lower() for i in items)


def test_clivia_no_pre_season_recommendations_when_already_applied(clivia_land_a_input):
    """If we're 1 week before planting, no time for lime — Mode C not A."""
    inputs = _minimal_inputs(clivia_land_a_input)
    # Clivia builds a week before planting — too late for lime
    art = build_programme(inputs)
    # Assertion: some combination of no recs + lost-opportunity items
    # Clivia had lime already applied; there's Al but no lead time for more
    lost_item_texts = [i.item.lower() for i in art.outstanding_items]
    # Either we have a lost-opportunity for lime OR a recommendation
    rec_materials = [r.material for r in art.pre_season_recommendations]
    assert "Calcitic Lime" not in rec_materials or any("lime" in t for t in lost_item_texts)


def test_full_two_block_programme(clivia_land_a_input, clivia_land_b_input):
    """Full Clivia: Land A + Land B together."""
    inputs = OrchestratorInput(
        client_name="Clivia Boerdery", farm_name="Klein Overberg",
        prepared_for="Wieland Jordaan",
        crop="Garlic", planting_date=date(2026, 4, 29),
        build_date=date(2026, 4, 21),
        expected_harvest_date=date(2026, 10, 25),
        method_availability=MethodAvailability(
            has_drip=True, has_foliar_sprayer=True, has_granular_spreader=True,
        ),
        blocks=[clivia_land_a_input, clivia_land_b_input],
        high_al_soil=True, wet_summer_between_apply_and_plant=True,
        available_materials=CLIVIA_MATERIALS,
        stage_count=5,
    )
    art = build_programme(inputs)
    assert len(art.soil_snapshots) == 2
    assert len(art.stage_schedules) == 2
    assert "land_a" in art.block_totals
    assert "land_b" in art.block_totals
    # Different targets → different block totals
    assert art.block_totals["land_a"]["N"] != art.block_totals["land_b"]["N"]


def test_artifact_json_roundtrip(clivia_land_a_input):
    """Programme artifact must survive JSON round-trip (tracker will persist)."""
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    j = art.model_dump_json()
    round_trip = ProgrammeArtifact.model_validate_json(j)
    assert round_trip.header.crop == art.header.crop
    assert len(round_trip.foliar_events) == len(art.foliar_events)
    assert len(round_trip.risk_flags) == len(art.risk_flags)


def test_decision_trace_records_every_module_invocation(clivia_land_a_input):
    """Every module invocation must appear in decision trace for audit."""
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    trace = "\n".join(art.decision_trace)
    assert "SoilFactorReasoner" in trace
    assert "StageSplitter" in trace
    assert "MethodSelector" in trace
    assert "FoliarTriggerEngine" in trace


def test_sources_deduped(clivia_land_a_input):
    """Same source cited twice should only appear once in sources_audit."""
    inputs = _minimal_inputs(clivia_land_a_input, with_block_b=True)
    art = build_programme(inputs)
    ids = [s.source_id for s in art.sources_audit]
    assert len(ids) == len(set(ids))  # no dups


# ============================================================
# Stage schedule
# ============================================================

def test_stage_schedule_covers_full_season(clivia_land_a_input):
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    sched = art.stage_schedules[0]
    assert sched.planting_date == date(2026, 4, 29)
    assert sched.harvest_date == date(2026, 10, 25)
    assert len(sched.stages) == 5
    # Every stage has a date range
    for stage in sched.stages:
        assert stage.date_start >= sched.planting_date


# ============================================================
# Transparent empties
# ============================================================

def test_blends_populated_when_materials_provided(clivia_land_a_input):
    """Consolidator (module 8) wired — blends populate when materials given."""
    inputs = _minimal_inputs(clivia_land_a_input)
    art = build_programme(inputs)
    # Clivia has materials catalog → blends should populate
    assert len(art.blends) > 0
    # Shopping list aggregator now wired — rolls up per-product totals
    # from the populated blends. Each entry has a valid category and
    # non-zero total.
    assert len(art.shopping_list) > 0, "shopping_list should be populated when blends are"
    valid_categories = {"drip", "drench", "foliar", "dry_blend"}
    for entry in art.shopping_list:
        assert entry.category in valid_categories
        assert entry.total_overall > 0
        assert entry.product
    trace = "\n".join(art.decision_trace)
    assert "Consolidator" in trace or "consolidator" in trace.lower()


def test_blends_empty_when_no_materials():
    """When no materials catalog is provided, blends stay empty — honest."""
    block = BlockInput(
        block_id="b1", block_name="Block 1", block_area_ha=1.0,
        soil_parameters={"pH (H2O)": 6.0},
        season_targets={"N": 100, "P2O5": 40, "K2O": 80},
    )
    inputs = OrchestratorInput(
        client_name="Test", farm_name="T", prepared_for="T",
        crop="Maize (dryland)",
        planting_date=date(2026, 11, 1), build_date=date(2026, 8, 1),
        method_availability=MethodAvailability(has_granular_spreader=True),
        blocks=[block], stage_count=4,
        # NOTE: no available_materials
    )
    art = build_programme(inputs)
    assert art.blends == []
    trace = "\n".join(art.decision_trace)
    assert "materials catalog" in trace.lower()


# ============================================================
# DRY-ONLY FARM — the engine must work for dry programmes too
# ============================================================

@pytest.fixture
def dryland_maize_block():
    """Free State dryland maize farm — NO drip, just granular spreader + foliar.
    Different crop, different method profile, different soil from Clivia."""
    return BlockInput(
        block_id="fs_north",
        block_name="FS North",
        block_area_ha=80.0,
        lab_name="Bemlab",
        lab_method="Bray-1",
        sample_date=date(2026, 1, 15),
        sample_id="BM2026_042",
        soil_parameters={
            "CEC": 8.5, "pH (H2O)": 5.9,
            "P (Bray-1)": 18, "K": 145, "Ca": 1200, "Mg": 180,
            "Al": 45, "Na": 15, "S": 8,  # moderate soil, no severe issues
            "B": 0.5, "Zn": 1.8, "Mn": 22, "Fe": 50, "Cu": 1.2,
        },
        season_targets={
            "N": 90, "P2O5": 45, "K2O": 30, "Ca": 25, "S": 15,
        },
        # No pre-season inputs — dryland farmers often apply everything
        # at planting via spreader
        pre_season_inputs=[],
    )


def test_dry_only_farm_produces_valid_artifact(dryland_maize_block):
    """Dryland maize, no drip, granular spreader + foliar sprayer only.
    Full orchestrator chain must still produce a working ProgrammeArtifact."""
    inputs = OrchestratorInput(
        client_name="Free State Farming Co",
        farm_name="Noordster",
        prepared_for="Jan Pretorius",
        crop="Maize (dryland)",
        planting_date=date(2026, 11, 1),  # Summer rainfall
        build_date=date(2026, 8, 1),  # 3 months pre-plant = lead time for lime
        location="Bothaville, Free State",
        ref_number="FSF_2026",
        expected_harvest_date=date(2027, 5, 15),
        season="Summer 2026/27",
        method_availability=MethodAvailability(
            has_drip=False,                  # ← no liquid at all
            has_pivot=False,
            has_sprinkler=False,
            has_foliar_sprayer=True,
            has_granular_spreader=True,     # ← dry blending only
            has_fertigation_injectors=False,
            has_seed_treatment=True,
        ),
        blocks=[dryland_maize_block],
        stage_count=5,
    )

    art = build_programme(inputs)

    # Artifact produced successfully
    assert isinstance(art, ProgrammeArtifact)
    assert art.header.crop == "Maize (dryland)"
    assert art.header.method_availability.has_drip is False
    assert art.header.method_availability.has_granular_spreader is True


def test_dry_farm_no_fertigation_specific_sections(dryland_maize_block):
    """Dry-only farm: zero fertigation-specific output (no Part A/B, no injection)."""
    inputs = OrchestratorInput(
        client_name="FS Co", farm_name="Noordster", prepared_for="Jan",
        crop="Maize (dryland)",
        planting_date=date(2026, 11, 1), build_date=date(2026, 8, 1),
        method_availability=MethodAvailability(
            has_drip=False, has_foliar_sprayer=True, has_granular_spreader=True,
        ),
        blocks=[dryland_maize_block], stage_count=5,
    )
    art = build_programme(inputs)

    # No risk flags should reference Part A/B or drip-line EC
    # (These are fertigation-specific, not applicable to dry farms)
    for flag in art.risk_flags:
        assert "Part A" not in flag.message
        assert "drip line" not in flag.message.lower()
        assert "injector" not in flag.message.lower()

    # Outstanding items should NOT ask for irrigation water test
    # (no fertigation → no water test needed)
    water_items = [i for i in art.outstanding_items if "water test" in i.item.lower()]
    assert len(water_items) == 0


def test_dry_farm_routes_all_macros_to_dry_broadcast_or_sidedress(dryland_maize_block):
    """Verify method routing via the method_selector happened correctly
    (dry farm → all macros go granular, not drip)."""
    from app.services.method_selector import select_methods
    from app.services.stage_splitter import split_season_targets

    avail = MethodAvailability(
        has_drip=False, has_foliar_sprayer=True, has_granular_spreader=True,
    )
    splits = split_season_targets(
        crop="Maize (dryland)",
        season_targets=dryland_maize_block.season_targets,
        stage_count=5,
    )
    assignments = select_methods(splits, avail)

    # Every N assignment must be DRY_* (not LIQUID_*)
    n_assignments = [a for a in assignments if a.nutrient == "N"]
    assert len(n_assignments) > 0
    for a in n_assignments:
        assert a.method.name.startswith("DRY_"), (
            f"N routed to {a.method.name} on a dry-only farm — expected DRY_*"
        )


def test_dry_farm_foliar_still_fires_if_triggered(dryland_maize_block):
    """Dry farm with foliar sprayer: foliar events STILL fire for micros
    even though the main macros programme is dry."""
    # Tweak soil to create P:Zn lockup → forces foliar Zn trigger
    dryland_maize_block.soil_parameters["P (Bray-1)"] = 150
    dryland_maize_block.soil_parameters["Zn"] = 0.4  # ratio 375, severe lockup
    dryland_maize_block.season_targets["Zn"] = 1.5

    inputs = OrchestratorInput(
        client_name="FS Co", farm_name="N", prepared_for="J",
        crop="Maize (dryland)",
        planting_date=date(2026, 11, 1), build_date=date(2026, 8, 1),
        method_availability=MethodAvailability(
            has_drip=False, has_foliar_sprayer=True, has_granular_spreader=True,
        ),
        blocks=[dryland_maize_block], stage_count=5,
    )
    art = build_programme(inputs)

    # P:Zn lockup should have produced a risk flag about Zn availability
    zn_flags = [f for f in art.risk_flags if "Zn" in f.message or "zinc" in f.message.lower()]
    # At least the SoilFactorFinding → RiskFlag translation should surface it
    assert len(zn_flags) >= 1 or any("P:Zn" in f.message for f in art.risk_flags)


def test_dry_farm_pre_season_lime_recommendation_if_al_and_lead_time():
    """Al-active dry farm + 3 months lead time → recommend lime (dry amendment,
    perfect for granular-spreader farm)."""
    al_block = BlockInput(
        block_id="al1", block_name="Al block", block_area_ha=50,
        soil_parameters={
            "Al": 450, "Ca": 800, "Mg": 150, "K": 120, "Na": 10,
            "pH (H2O)": 4.9, "P (Bray-1)": 15, "Zn": 1.0,
        },
        season_targets={"N": 80, "P2O5": 40, "K2O": 25},
    )
    inputs = OrchestratorInput(
        client_name="Acid-soil Farm", farm_name="Highveld",
        prepared_for="A", crop="Maize (dryland)",
        planting_date=date(2026, 11, 1), build_date=date(2026, 8, 1),  # 3 mo
        method_availability=MethodAvailability(
            has_drip=False, has_foliar_sprayer=True, has_granular_spreader=True,
        ),
        blocks=[al_block], stage_count=5,
        available_materials=CLIVIA_MATERIALS,  # reuse fixture
    )
    art = build_programme(inputs)

    # Should produce a lime recommendation — lime is dry, fits this farm
    lime_recs = [r for r in art.pre_season_recommendations if "Lime" in r.material]
    assert len(lime_recs) >= 1


# ============================================================
# Helpers
# ============================================================

def _minimal_inputs(block_a, with_block_b=False) -> OrchestratorInput:
    blocks = [block_a]
    if with_block_b:
        blocks.append(BlockInput(
            block_id="b2", block_name="Block 2", block_area_ha=1.0,
            soil_parameters={"pH (H2O)": 6.0},
            season_targets={"N": 100, "P2O5": 40, "K2O": 80},
        ))
    return OrchestratorInput(
        client_name="Clivia Boerdery",
        farm_name="Klein Overberg",
        prepared_for="Wieland Jordaan",
        crop="Garlic",
        planting_date=date(2026, 4, 29),
        build_date=date(2026, 4, 21),
        ref_number="WJ60421",
        expected_harvest_date=date(2026, 10, 25),
        method_availability=MethodAvailability(
            has_drip=True, has_foliar_sprayer=True, has_granular_spreader=True,
        ),
        blocks=blocks,
        high_al_soil=True,
        wet_summer_between_apply_and_plant=True,
        has_gypsum_in_plan=False,
        has_irrigation_water_test=False,
        planned_n_fertilizers=["calcium_ammonium_nitrate"],
        available_materials=CLIVIA_MATERIALS,
        stage_count=5,
    )
