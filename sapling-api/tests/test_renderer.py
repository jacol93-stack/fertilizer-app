"""
Tests for the Phase B deterministic renderer.

Exercises `render_programme_document(artifact)` against representative
ProgrammeArtifact shapes and asserts:

1. Output is non-empty, well-formed markdown
2. Client-mode disclosure boundary holds — no raw material names,
   factory procedures, QC, SOPs, recipe-style content leaks
3. Sections included / dropped match artifact content
4. Multi-block, single-block, fertigation, dry-only, foliar branches
   render correctly
5. Operator mode raises — Phase E scope
"""
from __future__ import annotations

from datetime import date

import pytest

from app.models.confidence import DataCompleteness
from app.models.methods import (
    DryBlendMethod,
    FertigationMethod,
    FoliarMethod,
    MethodAvailability,
    MethodKind,
)
from app.models.programme_artifact import (
    Assumption,
    Blend,
    BlendPart,
    FoliarEvent,
    OutstandingItem,
    ProgrammeArtifact,
    ProgrammeHeader,
    ProgrammeState,
    RiskFlag,
    SoilSnapshot,
    SourceCitation,
    StageSchedule,
)
from app.models.confidence import Tier
from app.models.variants import VariantKey
from app.services.renderer import (
    RenderOptions,
    render_programme_document,
)


# ============================================================
# Minimal artifact factory
# ============================================================

def _minimal_header(**overrides) -> ProgrammeHeader:
    defaults = dict(
        client_name="Test Client",
        farm_name="Test Farm",
        prepared_for="Test Client",
        prepared_date=date(2026, 4, 28),
        crop="Barley",
        variant_key=VariantKey(canonical_crop="Barley"),
        season="2026",
        planting_date=date(2026, 5, 1),
        data_completeness=DataCompleteness(level="standard"),
        method_availability=MethodAvailability(has_granular_spreader=True),
        state=ProgrammeState.DRAFT,
    )
    defaults.update(overrides)
    return ProgrammeHeader(**defaults)


def _minimal_soil(**overrides) -> SoilSnapshot:
    defaults = dict(
        block_id="B1",
        block_name="Land A",
        block_area_ha=10.0,
        parameters={"pH (KCl)": 7.6, "P (Olsen)": 5.5, "K": 147},
        headline_signals=["pH trending alkaline", "P (Olsen) Low"],
    )
    defaults.update(overrides)
    return SoilSnapshot(**defaults)


def _minimal_stage_schedule(block_id: str = "B1") -> StageSchedule:
    return StageSchedule(
        block_id=block_id,
        planting_date=date(2026, 5, 1),
        stages=[],
    )


def _dry_blend(block_id: str = "B1", stage: int = 1) -> Blend:
    return Blend(
        block_id=block_id,
        stage_number=stage,
        stage_name="Planting",
        weeks=f"Week {stage}",
        events=1,
        dates_label="1 May 2026",
        method=DryBlendMethod(kind=MethodKind.DRY_BROADCAST),
        raw_products=[
            BlendPart(
                product="Ammonium Sulphate",           # <-- MUST NOT leak
                analysis="N 21%, S 24%",
                rate_per_stage_per_ha="100 kg",
            ),
            BlendPart(
                product="Calcitic Lime",               # <-- MUST NOT leak
                analysis="Ca 40%",
                rate_per_stage_per_ha="500 kg",
            ),
        ],
        nutrients_delivered={"N": 21.0, "S": 24.0, "Ca": 200.0},
    )


def _fertigation_blend(block_id: str = "B1") -> Blend:
    return Blend(
        block_id=block_id,
        stage_number=2,
        stage_name="Vegetative",
        weeks="Weeks 3-7",
        events=5,
        dates_label="20 May – 25 Jun 2026",
        method=FertigationMethod(kind=MethodKind.LIQUID_DRIP),
        raw_products=[
            BlendPart(
                product="Calcium Nitrate",             # <-- MUST NOT leak
                analysis="N 17.1%, Ca 24.4%",
                stream="A",
                rate_per_event_per_ha="42 kg",
                rate_per_stage_per_ha="210 kg",
            ),
            BlendPart(
                product="MKP",                         # <-- MUST NOT leak
                analysis="P 51.8%, K 33.8%",
                stream="B",
                rate_per_event_per_ha="15 kg",
                rate_per_stage_per_ha="75 kg",
            ),
        ],
        nutrients_delivered={"N": 35.9, "P2O5": 28.5, "K2O": 33.7, "Ca": 51.2},
    )


def _foliar_event(block_id: str = "B1", num: int = 1) -> FoliarEvent:
    return FoliarEvent(
        block_id=block_id,
        event_number=num,
        week=6,
        spray_date=date(2026, 6, 12),
        stage_name="Bulb initiation",
        product="Solubor",                            # <-- MUST NOT leak
        analysis="B 20.5%",
        rate_per_ha="2.5 kg",
        total_for_block="25 kg",
        trigger_reason="Soil B 0.45 mg/kg below garlic critical 0.8 mg/kg",
        trigger_kind="soil_availability_gap",
        source=SourceCitation(source_id="FERTASA_5_6", tier=Tier.SA_INDUSTRY_BODY),
    )


def _artifact(**kwargs) -> ProgrammeArtifact:
    defaults = dict(
        header=_minimal_header(),
        soil_snapshots=[_minimal_soil()],
        stage_schedules=[_minimal_stage_schedule()],
        blends=[],
        foliar_events=[],
        block_totals={},
        risk_flags=[],
        assumptions=[],
        outstanding_items=[],
    )
    defaults.update(kwargs)
    return ProgrammeArtifact(**defaults)


# ============================================================
# The disclosure-boundary denylist
# ============================================================

# Raw material names that MUST NEVER appear in client-mode output.
# Pulled from the test fixtures above — if these strings show up in the
# rendered markdown the disclosure boundary has been breached.
RAW_MATERIAL_DENYLIST = [
    "Ammonium Sulphate",
    "Calcitic Lime",
    "Calcium Nitrate",
    "MKP",
    "Solubor",
    "Urea",
    "KCl",
    "SOP",
    "Potassium Sulphate",
    "MAP",
    "DAP",
    "Potassium Nitrate",
]


def _assert_no_raw_material_leak(output: str):
    """Client-mode docs must not leak raw material names."""
    for name in RAW_MATERIAL_DENYLIST:
        assert name not in output, (
            f"Disclosure boundary breach: '{name}' leaked into client-mode output"
        )


# ============================================================
# Smoke tests
# ============================================================

def test_render_minimal_artifact_produces_markdown():
    """Smallest viable artifact renders to non-empty markdown."""
    output = render_programme_document(_artifact())
    assert output
    assert output.startswith("# Fertilizer Programme")
    assert "Test Client" in output
    assert "Test Farm" in output
    assert "Barley" in output


def test_render_includes_soil_headline_signals():
    output = render_programme_document(_artifact())
    assert "pH trending alkaline" in output
    assert "P (Olsen) Low" in output


def test_render_empty_artifact_still_renders_header_and_background():
    """Even with no blends, no flags, no assumptions — the doc produces
    a header + background section and drops the empty ones."""
    artifact = _artifact(soil_snapshots=[])
    output = render_programme_document(artifact)
    assert output
    assert "# Fertilizer Programme" in output
    assert "## Background" in output
    # Dropped sections should not appear as empty headers
    assert "## Reading of the Soil" not in output
    assert "## Applications" not in output
    assert "## Assumptions" not in output


# ============================================================
# Client-mode disclosure boundary
# ============================================================

def test_dry_blend_no_raw_material_name_leak():
    artifact = _artifact(
        blends=[_dry_blend()],
        block_totals={"B1": {"N": 21.0, "S": 24.0, "Ca": 200.0}},
    )
    output = render_programme_document(artifact)
    _assert_no_raw_material_leak(output)
    # But nutrient analysis IS in the output
    assert "21%" in output or "24%" in output


def test_fertigation_blend_no_raw_material_name_leak():
    artifact = _artifact(
        blends=[_fertigation_blend()],
        block_totals={"B1": {"N": 35.9, "P2O5": 28.5, "K2O": 33.7, "Ca": 51.2}},
    )
    output = render_programme_document(artifact)
    _assert_no_raw_material_leak(output)
    assert "Part A" in output
    assert "Part B" in output


def test_foliar_event_no_raw_material_name_leak():
    artifact = _artifact(foliar_events=[_foliar_event()])
    output = render_programme_document(artifact)
    _assert_no_raw_material_leak(output)
    # Foliar analysis shown
    assert "B 20.5%" in output
    assert "Bulb initiation" in output


def test_no_factory_or_qc_or_sop_content_in_output():
    """Client-mode renderer must not produce factory/QC/SOP strings
    even if downstream data somehow carried them."""
    artifact = _artifact(blends=[_fertigation_blend()])
    output = render_programme_document(artifact).lower()
    for forbidden in ["stock tank", "batch number", "shelf life", "mixing order",
                      "qc check", "operator", "factory procedure", "assay"]:
        assert forbidden not in output, f"Forbidden factory/operator content: '{forbidden}'"


# ============================================================
# Structural checks
# ============================================================

def test_multi_block_programme_renders_per_block_sections():
    artifact = _artifact(
        soil_snapshots=[
            _minimal_soil(block_id="B1", block_name="Land A"),
            _minimal_soil(block_id="B2", block_name="Land B", headline_signals=["Low K"]),
        ],
        stage_schedules=[
            _minimal_stage_schedule("B1"),
            _minimal_stage_schedule("B2"),
        ],
    )
    output = render_programme_document(artifact)
    assert "Land A" in output
    assert "Land B" in output
    assert "### Land A" in output  # multi-block subheader format
    assert "### Land B" in output


def test_assumptions_render_when_present():
    artifact = _artifact(
        assumptions=[
            Assumption(
                field="cultivar",
                assumed_value="standard SA white",
                override_guidance="For elephant garlic, shift harvest 3-4 weeks later.",
            ),
        ],
    )
    output = render_programme_document(artifact)
    assert "Assumptions" in output
    assert "cultivar" in output
    assert "standard SA white" in output
    assert "elephant garlic" in output


def test_risk_flags_render_sorted_by_severity():
    artifact = _artifact(
        risk_flags=[
            RiskFlag(message="Info note", severity="info"),
            RiskFlag(message="CRITICAL finding", severity="critical"),
            RiskFlag(message="Watch item", severity="watch"),
        ],
    )
    output = render_programme_document(artifact)
    # Critical should come before Info in the output
    assert output.index("CRITICAL finding") < output.index("Info note")


def test_outstanding_items_render():
    artifact = _artifact(
        outstanding_items=[
            OutstandingItem(
                item="Irrigation water test",
                why_it_matters="Gypsum rate depends on water Na loading.",
                impact_if_skipped="Remediation rate may be under-specified.",
            ),
        ],
    )
    output = render_programme_document(artifact)
    assert "Irrigation water test" in output
    assert "Gypsum rate" in output


def test_nutrient_balance_single_block():
    artifact = _artifact(
        block_totals={"Land A": {"N": 120, "P2O5": 40, "K2O": 80, "Ca": 160}},
    )
    output = render_programme_document(artifact)
    assert "Nutrient Balance" in output
    assert "120" in output
    assert "160" in output


def test_nutrient_balance_multi_block_renders_horizontal_table():
    artifact = _artifact(
        block_totals={
            "Land A": {"N": 120, "K2O": 80},
            "Land B": {"N": 80, "K2O": 100},
        },
    )
    output = render_programme_document(artifact)
    assert "Land A" in output
    assert "Land B" in output


# ============================================================
# Mode safety
# ============================================================

def test_operator_mode_not_implemented():
    """Operator mode is deferred to Phase E; it must raise a clear error."""
    with pytest.raises(NotImplementedError, match="(?i)operator"):
        render_programme_document(_artifact(), RenderOptions(mode="operator"))


def test_default_mode_is_client():
    """No options supplied → client-mode by default."""
    output = render_programme_document(_artifact())
    # Would raise on operator mode — reaching here means client default worked
    assert output
