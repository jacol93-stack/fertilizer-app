"""
End-to-end vertical-slice tests for Phase 2 reasoning modules:
SoilFactorReasoner → FoliarTriggerEngine + RiskFlagGenerator.

Demonstrates the orchestrator pattern: chain modules to populate
ProgrammeArtifact sub-objects from real soil analysis input.

Clivia Land A is the golden test fixture.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.models import FoliarEvent, OutstandingItem, RiskFlag, Tier
from app.services.foliar_trigger_engine import (
    STAGE_PEAK_RULES,
    trigger_foliar_events,
)
from app.services.risk_flag_generator import (
    generate_outstanding_items,
    generate_risk_flags,
)
from app.services.soil_factor_reasoner import reason_soil_factors


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def clivia_land_a_soil():
    """NViroTek Mehlich-3 results, Clivia Land A, Feb 2026."""
    return {
        "CEC": 13.14,
        "pH (H2O)": 5.38,
        "P (Mehlich-3)": 2,
        "K": 227,
        "Ca": 1025,
        "Mg": 242,
        "Al": 851,
        "Na": 10,
        "S": 10,
        "B": 0.36,
        "Zn": 1.26,
        "Mn": 75,
        "Fe": 106,
        "Cu": 6.27,
    }


@pytest.fixture
def clivia_planting_date():
    return date(2026, 4, 29)


# ============================================================
# Foliar Trigger Engine
# ============================================================

def test_no_foliar_when_no_triggers_fire():
    """Healthy soil + crop with no stage-peak rules → no foliar events.

    Ca:B must be < 1000 to avoid antagonism trigger (Ca 1500/B 2.0 = 750)."""
    healthy_soil = {"CEC": 12, "pH (H2O)": 6.5, "P (Bray-1)": 30, "K": 200,
                    "Ca": 1500, "Mg": 250, "Al": 5, "S": 25, "B": 2.0,
                    "Zn": 4.0, "Mn": 25, "Fe": 30, "Cu": 1.5}
    report = reason_soil_factors(healthy_soil, crop="Sweetcorn")
    events = trigger_foliar_events(
        block_id="b1", crop="Sweetcorn",
        planting_date=date(2026, 4, 29),
        soil_factor_report=report,
    )
    # Sweetcorn has no STAGE_PEAK_RULES; healthy soil → no triggers
    assert events == []


def test_clivia_land_a_fires_garlic_b_at_bulb_init(clivia_land_a_soil, clivia_planting_date):
    """Clivia Garlic Land A: stage-peak B at week 16 should fire regardless of soil."""
    report = reason_soil_factors(clivia_land_a_soil, crop="Garlic")
    events = trigger_foliar_events(
        block_id="land_a", crop="Garlic",
        planting_date=clivia_planting_date,
        soil_factor_report=report,
        block_area_ha=1.11,
    )
    b_events = [e for e in events if "B" in e.product or "Solubor" in e.product]
    assert len(b_events) >= 1
    # At least one B event at bulb init (week 16)
    bulb_init_b = [e for e in b_events if e.week == 16]
    assert len(bulb_init_b) == 1
    # Trigger kind should be quality-window (B is in QUALITY_WINDOW_NUTRIENTS)
    assert bulb_init_b[0].trigger_kind == "quality_window"
    # Date math: planting (2026-04-29) + 16 weeks = 2026-08-19
    from datetime import timedelta
    assert bulb_init_b[0].spray_date == clivia_planting_date + timedelta(weeks=16)


def test_stage_peak_rules_carry_provenance():
    """Every STAGE_PEAK_RULE must have source_id + section + tier."""
    for rule in STAGE_PEAK_RULES:
        assert rule.source_id
        assert rule.source_section
        assert 1 <= rule.tier <= 6


def test_leaf_correction_trigger_fires():
    """Mid-season leaf showed K deficiency → leaf_correction event."""
    healthy_soil = {"pH (H2O)": 6.0, "P (Bray-1)": 30, "K": 150}
    report = reason_soil_factors(healthy_soil, crop="Maize (dryland)")
    events = trigger_foliar_events(
        block_id="b1", crop="Maize (dryland)",
        planting_date=date(2026, 4, 29),
        soil_factor_report=report,
        leaf_deficiencies={"Zn": 12.0},  # leaf Zn below 15-20 norm
    )
    leaf_events = [e for e in events if e.trigger_kind == "leaf_correction"]
    assert len(leaf_events) == 1
    # Default Zn product is "Zinc Sulphate" with analysis "36% Zn"
    assert "Zinc" in leaf_events[0].product or "Zn" in leaf_events[0].analysis


def test_block_area_scales_total():
    """A 2-ha block applying 1 kg/ha → 2 kg total."""
    soil = {"P (Bray-1)": 100, "Zn": 0.5}  # P:Zn 200, fires antagonism
    report = reason_soil_factors(soil, crop="Maize (dryland)")
    events = trigger_foliar_events(
        block_id="b1", crop="Maize (dryland)",
        planting_date=date(2026, 4, 29),
        soil_factor_report=report,
        block_area_ha=2.0,
    )
    soil_gap = [e for e in events if e.trigger_kind == "soil_availability_gap"]
    assert len(soil_gap) >= 1
    # Default Zn rate is "1 kg" → for 2 ha → "2.0 kg"
    assert "2.0 kg" in soil_gap[0].total_for_block


# ============================================================
# Citrus parent-variant foliar rule matching
# ============================================================

def test_citrus_parent_rule_fires_for_valencia():
    """A STAGE_PEAK_RULE defined for 'Citrus' parent must fire when the
    actual crop is 'Citrus (Valencia)' — parent-variant matching."""
    soil = {"pH": 6.2, "K": 200}
    report = reason_soil_factors(soil, crop="Citrus (Valencia)")
    events = trigger_foliar_events(
        block_id="b1", crop="Citrus (Valencia)",
        planting_date=date(2026, 8, 1),
        soil_factor_report=report,
    )
    b_events = [e for e in events if "B" in e.analysis and "Pre-bloom" in e.stage_name]
    zn_events = [e for e in events if "Zn" in e.analysis and "Pre-bloom" in e.stage_name]
    assert len(b_events) >= 1, "Citrus B pre-bloom foliar must fire for Valencia"
    assert len(zn_events) >= 1, "Citrus Zn pre-bloom foliar must fire for Valencia"


def test_citrus_parent_rule_fires_for_navel():
    soil = {"pH": 6.5, "K": 250}
    report = reason_soil_factors(soil, crop="Citrus (Navel)")
    events = trigger_foliar_events(
        block_id="b1", crop="Citrus (Navel)",
        planting_date=date(2026, 7, 15),
        soil_factor_report=report,
    )
    b_events = [e for e in events if "B" in e.analysis and "Pre-bloom" in e.stage_name]
    assert len(b_events) >= 1


def test_citrus_parent_rule_does_not_fire_for_apple():
    """Parent-variant matching must not over-match unrelated crops."""
    soil = {"pH": 6.0, "K": 180}
    report = reason_soil_factors(soil, crop="Apple")
    events = trigger_foliar_events(
        block_id="b1", crop="Apple",
        planting_date=date(2026, 8, 1),
        soil_factor_report=report,
    )
    citrus_b = [e for e in events if "Pre-bloom" in e.stage_name and "B" in e.analysis]
    # Apple has its own Ca quality-window rule, but no Citrus B rule should fire
    assert not any(
        "Citrus" in (e.trigger_reason or "") or "FERTASA 5.7.3" in (e.source.section or "")
        for e in events
    )


def test_citrus_parent_rule_fires_for_exact_citrus():
    """Rule defined as 'Citrus' also matches exactly 'Citrus'."""
    soil = {"pH": 6.0, "K": 180}
    report = reason_soil_factors(soil, crop="Citrus")
    events = trigger_foliar_events(
        block_id="b1", crop="Citrus",
        planting_date=date(2026, 8, 1),
        soil_factor_report=report,
    )
    b_events = [e for e in events if "B" in e.analysis and "Pre-bloom" in e.stage_name]
    assert len(b_events) >= 1


# ============================================================
# Risk Flag Generator
# ============================================================

def test_clivia_land_a_produces_critical_al_flag(clivia_land_a_soil):
    """Clivia Land A → critical Al toxicity must surface as RiskFlag."""
    report = reason_soil_factors(clivia_land_a_soil, crop="Garlic")
    flags = generate_risk_flags(soil_factor_report=report, crop="Garlic")
    al_critical = [f for f in flags if "Al saturation" in f.message and f.severity == "critical"]
    assert len(al_critical) >= 1


def test_no_gypsum_with_active_al_fires_warn(clivia_land_a_soil):
    """Active Al + no gypsum in plan → programme-level warning."""
    report = reason_soil_factors(clivia_land_a_soil, crop="Garlic")
    flags = generate_risk_flags(
        soil_factor_report=report, crop="Garlic",
        has_gypsum_in_plan=False,
    )
    no_gypsum = [f for f in flags if "no gypsum" in f.message.lower()]
    assert len(no_gypsum) >= 1
    assert no_gypsum[0].severity == "warn"


def test_gypsum_in_plan_suppresses_no_gypsum_flag(clivia_land_a_soil):
    """If gypsum IS in the plan, the no-gypsum flag should not fire."""
    report = reason_soil_factors(clivia_land_a_soil, crop="Garlic")
    flags = generate_risk_flags(
        soil_factor_report=report, crop="Garlic",
        has_gypsum_in_plan=True,
    )
    no_gypsum = [f for f in flags if "no gypsum" in f.message.lower()]
    assert len(no_gypsum) == 0


def test_ams_on_acid_soil_fires_warn(clivia_land_a_soil):
    """Plan includes ammonium sulphate on already-acid soil → warn."""
    report = reason_soil_factors(clivia_land_a_soil, crop="Garlic")
    flags = generate_risk_flags(
        soil_factor_report=report, crop="Garlic",
        planned_n_fertilizers=["ammonium_sulphate", "urea"],
    )
    ams_flags = [f for f in flags if "Ammonium Sulphate" in f.message]
    assert len(ams_flags) >= 1
    # Cites IFA
    assert ams_flags[0].source.source_id == "IFA_WFM_1992"


def test_ca_nitrate_advisory_fires_with_critical_al(clivia_land_a_soil):
    """Critical Al + fertigation → don't-substitute-the-Ca-stream advisory.
    Reference is by analysis ('15.5 % N + 19 % Ca source') not raw name,
    per client-disclosure boundary."""
    report = reason_soil_factors(clivia_land_a_soil, crop="Garlic")
    flags = generate_risk_flags(
        soil_factor_report=report, crop="Garlic",
        uses_fertigation=True,
    )
    advisories = [
        f for f in flags
        if "substitute" in f.message and "Al-antagonism" in f.message
    ]
    assert len(advisories) >= 1
    # Disclosure boundary — message must NOT name raw materials
    assert "Calcium Nitrate" not in advisories[0].message
    assert "Ca-Nit" not in advisories[0].message


def test_outstanding_items_water_test_when_fertigation():
    flags = generate_outstanding_items(
        soil_factor_report=reason_soil_factors({}, crop="Garlic"),
        uses_fertigation=True,
        has_irrigation_water_test=False,
    )
    water = [i for i in flags if "water test" in i.item.lower()]
    assert len(water) == 1
    assert "Part A" in water[0].why_it_matters


def test_outstanding_items_post_harvest_soil_when_al_critical(clivia_land_a_soil):
    report = reason_soil_factors(clivia_land_a_soil, crop="Garlic")
    items = generate_outstanding_items(soil_factor_report=report, crop="Garlic")
    post_harvest = [i for i in items if "Post-harvest" in i.item]
    assert len(post_harvest) == 1


# ============================================================
# Vertical slice — Clivia Land A end-to-end
# ============================================================

def test_clivia_land_a_full_vertical_slice(clivia_land_a_soil, clivia_planting_date):
    """Soil → SoilFactorReasoner → FoliarTriggers + RiskFlags + Outstanding.

    Demonstrates the orchestrator pattern: chain modules and produce real
    Programme Artifact sub-objects from real soil input. This is the
    template Phase 2 main orchestrator will follow.
    """
    # 1. Run soil-factor reasoning
    report = reason_soil_factors(clivia_land_a_soil, crop="Garlic")
    assert "Al_saturation_pct" in report.computed
    assert report.computed["Al_saturation_pct"] > 50  # severe per Clivia

    # 2. Generate foliar events from triggers
    foliar_events = trigger_foliar_events(
        block_id="land_a", crop="Garlic",
        planting_date=clivia_planting_date,
        soil_factor_report=report,
        block_area_ha=1.11,
    )
    # At minimum: B event at bulb-init wk 16
    assert any(e.week == 16 for e in foliar_events)
    # All events typed FoliarEvent
    assert all(isinstance(e, FoliarEvent) for e in foliar_events)
    # All events carry source citation
    assert all(e.source.source_id for e in foliar_events)

    # 3. Generate risk flags
    risk_flags = generate_risk_flags(
        soil_factor_report=report, crop="Garlic",
        planned_n_fertilizers=["calcium_ammonium_nitrate"],  # Clivia uses Ca-Nit
        has_gypsum_in_plan=False,  # Clivia explicitly skipped gypsum
        uses_fertigation=True,
    )
    assert all(isinstance(f, RiskFlag) for f in risk_flags)
    # Should have multiple flags: critical Al, no-gypsum, Ca-Nit-don't-substitute, etc.
    assert len(risk_flags) >= 3

    # 4. Generate outstanding items
    items = generate_outstanding_items(
        soil_factor_report=report, crop="Garlic",
        uses_fertigation=True,
        has_irrigation_water_test=False,
        has_recent_leaf_analysis=False,
        season_weeks=26,
    )
    assert all(isinstance(i, OutstandingItem) for i in items)
    # Water test required + leaf analysis suggestion + post-harvest soil
    assert len(items) >= 2
