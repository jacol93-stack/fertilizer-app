"""Tests for the Phase 2 Pre-Season Module — three modes:
A (recommend), B (subtract residual), C (lost opportunity)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models import OutstandingItem, PreSeasonInput, PreSeasonRecommendation, RiskFlag
from app.services.pre_season_module import (
    DEFAULT_REACTION_PROFILES,
    compute_residual_position,
    flag_lost_opportunities,
    recommend_pre_season_actions,
)
from app.services.soil_factor_reasoner import reason_soil_factors


# Sample materials catalog for tests (mirrors post-073 DB)
SAMPLE_MATERIALS = [
    {
        "material": "Calcitic Lime", "type": "Chemical",
        "n": 0, "p": 0, "k": 0, "ca": 40, "mg": 2, "s": 0,
        "applicability": "pre_season_only",
        "reaction_time_months_min": 3, "reaction_time_months_max": 6,
        "soil_improvement_purpose": "pH lift via CaCO3 + Ca contribution + partial Al displacement",
    },
    {
        "material": "Gypsum", "type": "Chemical",
        "n": 0, "p": 0, "k": 0, "ca": 23, "mg": 0, "s": 18,
        "applicability": "both",
        "reaction_time_months_min": 0.5, "reaction_time_months_max": 2,
        "soil_improvement_purpose": "Na displacement; subsoil Ca + S",
    },
    {
        "material": "Manure Compost", "type": "Organic",
        "n": 2.13, "p": 1.01, "k": 1.64, "ca": 2.2, "mg": 1.0, "s": 0.7,
        "applicability": "both",
        "reaction_time_months_min": 2, "reaction_time_months_max": 12,
        "soil_improvement_purpose": "OM building + slow N release",
    },
    {
        "material": "Metabophos",
        "n": 0, "p": 19, "k": 0, "ca": 19, "mg": 0, "s": 11,
        "applicability": "in_season_only",
        "reaction_time_months_min": None, "reaction_time_months_max": None,
        "soil_improvement_purpose": None,
    },
]


# ============================================================
# Mode A — Recommend
# ============================================================

def test_recommend_lime_when_al_active_and_lead_time_sufficient():
    """6 months lead time, Al critical → recommend lime."""
    soil = {"Al": 851, "Ca": 1025, "Mg": 242, "K": 227, "Na": 10}
    report = reason_soil_factors(soil, crop="Garlic")
    build = date(2026, 1, 1)
    plant = date(2026, 7, 1)  # 6 months out

    recs = recommend_pre_season_actions(
        block_id="b1",
        soil_factor_report=report,
        build_date=build,
        planting_date=plant,
        available_materials=SAMPLE_MATERIALS,
    )
    lime_recs = [r for r in recs if r.material == "Calcitic Lime"]
    assert len(lime_recs) == 1
    rec = lime_recs[0]
    assert isinstance(rec, PreSeasonRecommendation)
    # Apply-by date should be 3 months before planting at minimum
    assert rec.recommended_apply_by_date <= plant - timedelta(days=80)
    assert "Al" in rec.reason or "saturation" in rec.reason


def test_no_lime_recommendation_if_no_lead_time():
    """1 month lead time with Al active → NO recommendation (lime needs 3+)."""
    soil = {"Al": 851, "Ca": 1025, "Mg": 242, "K": 227, "Na": 10}
    report = reason_soil_factors(soil, crop="Garlic")
    build = date(2026, 4, 1)
    plant = date(2026, 5, 1)  # only 1 month

    recs = recommend_pre_season_actions(
        block_id="b1",
        soil_factor_report=report,
        build_date=build,
        planting_date=plant,
        available_materials=SAMPLE_MATERIALS,
    )
    assert not any(r.material == "Calcitic Lime" for r in recs)


def test_recommend_gypsum_for_sodicity():
    """SAR critical + 2 months lead time → recommend gypsum (needs only 0.5-2)."""
    soil = {"Ca": 100, "Mg": 50, "Na": 5000}  # SAR > 20
    report = reason_soil_factors(soil, crop="Maize (dryland)")
    build = date(2026, 5, 1)
    plant = date(2026, 7, 1)  # 2 months

    recs = recommend_pre_season_actions(
        block_id="b1",
        soil_factor_report=report,
        build_date=build,
        planting_date=plant,
        available_materials=SAMPLE_MATERIALS,
    )
    gypsum_recs = [r for r in recs if r.material == "Gypsum"]
    assert len(gypsum_recs) == 1


def test_no_recommendations_if_no_findings():
    """Healthy soil + plenty of lead time → no pre-season recommendations."""
    soil = {"pH (H2O)": 6.5, "Ca": 1500, "Mg": 250, "K": 200,
            "Al": 5, "Na": 10, "P (Bray-1)": 30, "Zn": 4.0}
    report = reason_soil_factors(soil, crop="Maize (dryland)")
    recs = recommend_pre_season_actions(
        block_id="b1",
        soil_factor_report=report,
        build_date=date(2026, 1, 1),
        planting_date=date(2026, 12, 1),
        available_materials=SAMPLE_MATERIALS,
    )
    assert recs == []


# ============================================================
# Mode B — Compute residual subtraction (Clivia case)
# ============================================================

def test_clivia_residual_position():
    """Clivia: lime 1500 kg/ha + Metabophos 125 kg/ha + Manure 2 t/ha
    applied 3 months before planting on high-Al soil with wet summer."""
    inputs = [
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
            product="Manure Compost", rate="2000 kg/ha",  # 2 t/ha
            contribution_per_ha="~8 kg N, 5 kg P2O5, 10 kg K2O",
            status_at_planting="N largely leached; OM benefit retained",
            applied_date=date(2026, 2, 1),
        ),
    ]
    planting = date(2026, 4, 29)

    updated, subtraction = compute_residual_position(
        pre_season_inputs=inputs,
        planting_date=planting,
        high_al_soil=True,
        wet_summer_between_apply_and_plant=True,
        available_materials=SAMPLE_MATERIALS,
    )

    # Should produce real subtraction
    assert subtraction["Ca"] > 0  # Lime + Metabophos contributions
    assert subtraction["P2O5"] > 0  # Metabophos
    assert subtraction["S"] > 0  # Metabophos S

    # N from manure should be discounted (wet summer leaching)
    # Manure n=2.13%, 2000 kg = 42.6 kg total N. Discounted to ~10% (wet) × reaction_pct
    assert subtraction["N"] < 10  # most leached

    # Updated inputs carry effective_*_kg_per_ha
    lime = next(i for i in updated if i.product == "Calcitic Lime")
    assert lime.effective_ca_kg_per_ha > 0


def test_residual_zero_if_no_inputs():
    updated, subtraction = compute_residual_position([], date(2026, 4, 29))
    assert updated == []
    assert all(v == 0 for v in subtraction.values())


def test_residual_handles_unknown_material():
    """Unknown material in PSI → preserved in output without subtraction."""
    inputs = [PreSeasonInput(
        product="UnobtainiumPhos 99", rate="100 kg/ha",
        contribution_per_ha="?", status_at_planting="?",
    )]
    updated, subtraction = compute_residual_position(
        inputs, date(2026, 4, 29), available_materials=SAMPLE_MATERIALS,
    )
    assert len(updated) == 1
    assert all(v == 0 for v in subtraction.values())


def test_p_fixation_factor_lower_on_high_al_soil():
    """Same Metabophos input, high-Al soil halves P availability."""
    inputs = [PreSeasonInput(
        product="Metabophos", rate="125 kg/ha",
        contribution_per_ha="?", status_at_planting="?",
        applied_date=date(2026, 1, 1),
    )]
    plant = date(2026, 4, 29)

    _, sub_high_al = compute_residual_position(
        inputs, plant, high_al_soil=True,
        available_materials=SAMPLE_MATERIALS,
    )
    _, sub_low_al = compute_residual_position(
        inputs, plant, high_al_soil=False,
        available_materials=SAMPLE_MATERIALS,
    )
    assert sub_low_al["P2O5"] > sub_high_al["P2O5"]


# ============================================================
# Mode C — Lost opportunity
# ============================================================

def test_lost_opportunity_lime_when_al_active_no_time(clivia_al_soil_factor_report=None):
    """Al active + 1 month gap → lost-opportunity item + risk flag."""
    soil = {"Al": 851, "Ca": 1025, "Mg": 242, "K": 227, "Na": 10}
    report = reason_soil_factors(soil, crop="Garlic")
    items, flags = flag_lost_opportunities(
        soil_factor_report=report,
        build_date=date(2026, 4, 1),
        planting_date=date(2026, 5, 1),  # 1 month
    )
    lime_items = [i for i in items if "Lime" in i.item]
    assert len(lime_items) == 1
    al_flags = [f for f in flags if "Al active" in f.message]
    assert len(al_flags) == 1
    assert al_flags[0].severity == "warn"


def test_no_lost_opportunity_when_lead_time_sufficient():
    """Al active + 6 months gap → no lost-opportunity (Mode A handles)."""
    soil = {"Al": 851, "Ca": 1025, "Mg": 242, "K": 227, "Na": 10}
    report = reason_soil_factors(soil, crop="Garlic")
    items, flags = flag_lost_opportunities(
        soil_factor_report=report,
        build_date=date(2026, 1, 1),
        planting_date=date(2026, 7, 1),  # 6 months
    )
    assert not any("Lime" in i.item for i in items)


# ============================================================
# Reaction profiles
# ============================================================

def test_reaction_profiles_ordered_correctly():
    """Lime should react slower than gypsum, faster than rock phosphate."""
    gypsum_min = DEFAULT_REACTION_PROFILES["gypsum"][0]
    lime_min = DEFAULT_REACTION_PROFILES["calcitic_lime"][0]
    rock_p_min = DEFAULT_REACTION_PROFILES["rock_phosphate"][0]
    assert gypsum_min < lime_min < rock_p_min
