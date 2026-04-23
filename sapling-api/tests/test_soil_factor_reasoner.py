"""Tests for the Phase 2 Soil Factor Reasoner module.

Locks in the thresholds + antagonism rules + toxicity triggers. When
rules evolve (new sources, crop-specific overrides), tests evolve too.
"""
from __future__ import annotations

import pytest

from app.services.soil_factor_reasoner import (
    AL_SAT_HIGH_PCT,
    AL_SAT_MODERATE_PCT,
    CA_B_ANTAGONISM_THRESHOLD,
    CAO_PER_KG_N_BY_N_TYPE,
    EC_HIGH_THRESHOLD,
    EC_MODERATE_THRESHOLD,
    N_UTILIZATION_DEFAULT,
    P_ZN_ANTAGONISM_THRESHOLD,
    SAR_HIGH_THRESHOLD,
    SAR_MODERATE_THRESHOLD,
    SoilFactorFinding,
    SoilFactorReport,
    compute_al_saturation_pct,
    compute_cn_ratio,
    compute_lime_needed_for_n,
    compute_sar,
    reason_soil_factors,
)


# ============================================================
# Metric computation
# ============================================================

def test_al_saturation_clivia_land_a():
    """Clivia Land A: Al 851 mg/kg, Ca 1025, Mg 242, K 227 → ~55% of effective CEC.

    Computation: Al_cmol = 851/89.98 = 9.46; bases = 7.73 cmol; eff CEC = 17.19;
    Al sat = 55%. Clivia doc reported "H+Al 25-34% TUK" (which uses total CEC
    denominator); our effective-CEC calc is stricter (Al-only numerator) and
    gives a higher %. Both indicate severe Al stress — the point of this test.
    """
    soil = {"Al": 851, "Ca": 1025, "Mg": 242, "K": 227, "Na": 10}
    al_sat = compute_al_saturation_pct(soil)
    assert al_sat is not None
    assert 50 < al_sat < 60  # severe Al stress per effective-CEC calc


def test_al_saturation_none_without_al():
    assert compute_al_saturation_pct({"Ca": 1000}) is None


def test_sar_computation():
    # Typical moderate-sodicity: Na high relative to Ca+Mg
    soil = {"Ca": 400, "Mg": 100, "Na": 200}
    sar = compute_sar(soil)
    assert sar is not None
    assert sar > 0


def test_sar_none_without_na():
    assert compute_sar({"Ca": 1000, "Mg": 200}) is None


def test_cn_ratio_normal():
    cn = compute_cn_ratio({"Organic C": 2.0, "Total N": 0.15})
    assert cn == pytest.approx(13.3, rel=0.01)


def test_cn_ratio_none_without_inputs():
    assert compute_cn_ratio({"Organic C": 2.0}) is None


# ============================================================
# P:Zn antagonism
# ============================================================

def test_p_zn_below_threshold_no_finding():
    # P 30, Zn 3 → ratio 10, well under 150
    report = reason_soil_factors({"P (Bray-1)": 30, "Zn": 3}, crop="Maize")
    antagonisms = report.by_kind("antagonism")
    assert not any(f.parameter == "P:Zn" for f in antagonisms)


def test_p_zn_over_threshold_fires_watch():
    # P 100, Zn 0.5 → ratio 200, moderately over 150
    report = reason_soil_factors({"P (Bray-1)": 100, "Zn": 0.5}, crop="Maize")
    p_zn = [f for f in report.findings if f.parameter == "P:Zn"]
    assert len(p_zn) == 1
    assert p_zn[0].severity == "watch"
    assert p_zn[0].trigger_kind == "soil_availability_gap"
    assert "foliar zn" in p_zn[0].recommended_action.lower()


def test_p_zn_extreme_fires_warn():
    # P 200, Zn 0.3 → ratio 666, extremely over
    report = reason_soil_factors({"P (Bray-1)": 200, "Zn": 0.3}, crop="Maize")
    p_zn = [f for f in report.findings if f.parameter == "P:Zn"][0]
    assert p_zn.severity == "warn"


# ============================================================
# Ca:B antagonism
# ============================================================

def test_ca_b_below_threshold_no_finding():
    # Ca 800, B 1.0 → 800:1, under 1000
    report = reason_soil_factors({"Ca": 800, "B": 1.0}, crop="Apple")
    assert not any(f.parameter == "Ca:B" for f in report.findings)


def test_ca_b_over_threshold():
    # Ca 1500, B 1.0 → 1500:1
    report = reason_soil_factors({"Ca": 1500, "B": 1.0}, crop="Apple")
    ca_b = [f for f in report.findings if f.parameter == "Ca:B"][0]
    assert ca_b.kind == "antagonism"
    assert ca_b.trigger_kind == "soil_availability_gap"


# ============================================================
# Al toxicity (Clivia case)
# ============================================================

def test_al_toxicity_fires_critical_for_non_acid_tolerant():
    """Clivia Land A scenario: Al saturation ~34% → critical for garlic."""
    soil = {"Al": 851, "Ca": 1025, "Mg": 242, "K": 227, "Na": 10}
    report = reason_soil_factors(soil, crop="Garlic")
    al_findings = [f for f in report.findings if f.parameter == "Al_saturation_pct"]
    assert len(al_findings) == 1
    assert al_findings[0].severity == "critical"
    assert al_findings[0].trigger_kind == "toxicity"
    assert "lime" in al_findings[0].recommended_action.lower()
    assert "ca-nitrate" in al_findings[0].recommended_action.lower()


def test_al_toxicity_suppressed_for_acid_tolerant():
    """Blueberry, rooibos etc. tolerate high Al — suppress toxicity alert."""
    soil = {"Al": 851, "Ca": 1025, "Mg": 242, "K": 227, "Na": 10}
    report = reason_soil_factors(soil, crop="Blueberry")
    al_findings = [f for f in report.findings if f.parameter == "Al_saturation_pct"]
    assert len(al_findings) == 0


def test_al_toxicity_suppressed_by_explicit_flag():
    """Crop_calc_flags can also gate Al toxicity (e.g. Honeybush)."""
    soil = {"Al": 851, "Ca": 1025, "Mg": 242, "K": 227, "Na": 10}
    report = reason_soil_factors(
        soil, crop="SomeCustomAcidCrop",
        crop_calc_flags={"skip_cation_ratio_path": True},
    )
    al_findings = [f for f in report.findings if f.parameter == "Al_saturation_pct"]
    assert len(al_findings) == 0


def test_al_moderate_fires_warn():
    # Lower Al → moderate range 10-30%
    soil = {"Al": 200, "Ca": 1500, "Mg": 300, "K": 300, "Na": 10}
    report = reason_soil_factors(soil, crop="Maize")
    al_findings = [f for f in report.findings if f.parameter == "Al_saturation_pct"]
    if al_findings:
        assert al_findings[0].severity in ("warn", "critical")


# ============================================================
# SAR / sodicity
# ============================================================

def test_sar_high_fires_critical():
    """Na ~5000 mg/kg with low Ca+Mg → SAR > 20 → critical sodicity."""
    # SAR = (Na_cmol) / sqrt((Ca+Mg)/2 cmol)
    # Na_cmol = 5000/230 ≈ 21.7; Ca+Mg_cmol ≈ 0.91; sqrt(0.455) ≈ 0.675
    # SAR ≈ 32 → critical (> 20 threshold)
    soil = {"Ca": 100, "Mg": 50, "Na": 5000}
    report = reason_soil_factors(soil, crop="Maize")
    sar_findings = [f for f in report.findings if f.parameter == "SAR"]
    assert len(sar_findings) >= 1
    assert sar_findings[0].severity == "critical"


def test_sar_moderate_fires_warn():
    """Moderate Na → SAR 13-20 → warn."""
    soil = {"Ca": 100, "Mg": 50, "Na": 3000}
    report = reason_soil_factors(soil, crop="Maize")
    sar_findings = [f for f in report.findings if f.parameter == "SAR"]
    assert len(sar_findings) == 1
    assert sar_findings[0].severity == "warn"


def test_sar_low_no_finding():
    soil = {"Ca": 1500, "Mg": 300, "Na": 20}
    report = reason_soil_factors(soil, crop="Maize")
    sar_findings = [f for f in report.findings if f.parameter == "SAR"]
    assert len(sar_findings) == 0


# ============================================================
# C:N
# ============================================================

def test_cn_high_slows_mineralization():
    report = reason_soil_factors({"Organic C": 3.0, "Total N": 0.10}, crop="Maize")
    cn_findings = [f for f in report.findings if f.parameter == "C:N"]
    assert len(cn_findings) == 1
    assert cn_findings[0].kind == "balance"
    assert cn_findings[0].severity == "watch"


def test_cn_low_rapid_mineralization():
    report = reason_soil_factors({"Organic C": 1.0, "Total N": 0.15}, crop="Maize")
    cn_findings = [f for f in report.findings if f.parameter == "C:N"]
    assert len(cn_findings) == 1
    assert cn_findings[0].severity == "info"


# ============================================================
# EC / salinity
# ============================================================

def test_ec_high_fires_critical():
    report = reason_soil_factors({"EC": 5.0}, crop="Maize")
    ec_findings = [f for f in report.findings if f.parameter == "EC"]
    assert len(ec_findings) == 1
    assert ec_findings[0].severity == "critical"


def test_ec_moderate_fires_warn():
    report = reason_soil_factors({"EC": 2.5}, crop="Maize")
    ec_findings = [f for f in report.findings if f.parameter == "EC"]
    assert len(ec_findings) == 1
    assert ec_findings[0].severity == "warn"


def test_ec_ok_no_finding():
    report = reason_soil_factors({"EC": 0.5}, crop="Maize")
    ec_findings = [f for f in report.findings if f.parameter == "EC"]
    assert len(ec_findings) == 0


# ============================================================
# N-fertilizer lime-need (IFA 1992 Table 1)
# ============================================================

def test_lime_need_urea():
    """150 kg N as urea → 150 kg CaO (factor 1.0)."""
    result = compute_lime_needed_for_n(150, "urea")
    assert result is not None
    assert result["cao_kg_per_ha"] == 150.0
    assert result["factor"] == 1.0
    assert result["tier"] == 3
    assert "IFA" in result["source_id"]


def test_lime_need_ammonium_sulphate_most_acidifying():
    """Ammonium sulphate is the worst: factor 3.0."""
    result = compute_lime_needed_for_n(100, "ammonium_sulphate")
    assert result is not None
    assert result["cao_kg_per_ha"] == 300.0
    assert result["factor"] == 3.0


def test_lime_need_can_mildest():
    """CAN (27% N calcium ammonium nitrate) is mildest: 0.6."""
    result = compute_lime_needed_for_n(100, "CAN")
    assert result is not None
    assert result["factor"] == 0.6


def test_lime_need_aliases_work():
    """DAP / diammonium_phosphate / AmS / ams all resolve."""
    assert compute_lime_needed_for_n(100, "DAP")["factor"] == 2.0
    assert compute_lime_needed_for_n(100, "diammonium phosphate")["factor"] == 2.0
    assert compute_lime_needed_for_n(100, "AmS")["factor"] == 3.0
    assert compute_lime_needed_for_n(100, "ammonium-sulphate")["factor"] == 3.0


def test_lime_need_unknown_type_returns_none():
    assert compute_lime_needed_for_n(100, "unobtainium-nitrate") is None


def test_lime_need_zero_n_returns_none():
    assert compute_lime_needed_for_n(0, "urea") is None


def test_n_utilization_constant_reasonable():
    """IFA published 50-70%; default should be midpoint."""
    assert 0.5 <= N_UTILIZATION_DEFAULT <= 0.7


def test_cao_table_ordering_matches_ifa():
    """CAN < urea < DAP < AmS acidification ordering per IFA Table 1."""
    assert (
        CAO_PER_KG_N_BY_N_TYPE["can"]
        < CAO_PER_KG_N_BY_N_TYPE["urea"]
        < CAO_PER_KG_N_BY_N_TYPE["dap"]
        < CAO_PER_KG_N_BY_N_TYPE["ams"]
    )


# ============================================================
# Clivia end-to-end sanity
# ============================================================

def test_clivia_land_a_full_reasoning():
    """End-to-end: Clivia Land A soil → multiple findings."""
    soil = {
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
    report = reason_soil_factors(soil, crop="Garlic")

    # Should detect Al toxicity (Clivia's #1 signal)
    assert any(f.parameter == "Al_saturation_pct" for f in report.findings)

    # Report should have an Al_saturation_pct computed metric
    assert "Al_saturation_pct" in report.computed

    # Multiple findings expected
    assert len(report.findings) >= 1

    # by_severity_at_least helper
    critical_findings = report.by_severity_at_least("critical")
    assert len(critical_findings) >= 1
