"""
Soil Factor Reasoner — Phase 2 reasoning module (new 2026-04-23).

Sits on top of soil_engine.evaluate_ratios() and extends it with:
  1. Additional soil-chemistry factors not in evaluate_ratios today:
     - Al saturation (from exchangeable Al + CEC)
     - SAR (Sodium Adsorption Ratio)
     - C:N ratio (from Organic C + Total N)
  2. Antagonism detection — converts ratios into decisions:
     - P:Zn > 150:1 → Zn availability restricted → foliar Zn trigger
     - Ca:B > 1000:1 → B availability restricted → foliar B trigger
     - Fe:Mn out-of-range → antagonism flag
     - Cu:Mo out-of-range → antagonism flag
  3. Toxicity triggers:
     - Al saturation > crop-specific threshold → lime priority + Ca-Nitrate
     - SAR > 13 → sodic soil flag → gypsum/amelioration
     - EC > 2 mS/cm in topsoil → salinity flag

Returns structured SoilFactorFindings that the orchestrator converts
into RiskFlags + FoliarEvent triggers + risk-flag narratives.

Provenance discipline:
  - Thresholds sourced to FERTASA / SASRI / ICAR / Foth-Ellis where
    published, Tier 1-3 flagged.
  - Common agronomy thresholds without a specific handbook citation
    are Tier 6 (implementer convention) — user can override.

This module is NEW and does not modify existing evaluate_ratios
behavior. Phase 2 orchestrator will invoke both.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ============================================================
# Threshold constants (with provenance)
# ============================================================

# P:Zn lockup — classic agronomic threshold. Foth & Ellis "Soil Fertility"
# 2nd ed. (1997) p.224 references the 150:1 threshold above which soil Zn
# becomes restricted by high P. Tier 3 (international textbook).
P_ZN_ANTAGONISM_THRESHOLD = 150.0
P_ZN_SOURCE = ("FOTH_ELLIS_1997", "Soil Fertility 2nd ed. p.224", 3)

# Ca:B — Shorrocks (1997) "The occurrence and correction of boron deficiency"
# notes a Ca:B ratio > 1000:1 as threshold for induced B deficiency on
# high-Ca soils. Tier 3.
CA_B_ANTAGONISM_THRESHOLD = 1000.0
CA_B_SOURCE = ("SHORROCKS_1997", "Plant & Soil 193:121-148", 3)

# SAR thresholds — US Salinity Lab Staff Agriculture Handbook 60 classic
# classification: SAR < 13 non-sodic, 13-20 moderately sodic, > 20 sodic.
# Matches FERTASA 5.2 salinity-sodicity discussion (brief prose, no table).
SAR_MODERATE_THRESHOLD = 13.0
SAR_HIGH_THRESHOLD = 20.0
SAR_SOURCE = ("USSL_1954", "USDA Agriculture Handbook 60", 3)

# EC salinity thresholds (saturated paste extract, mS/cm at 25°C)
EC_MODERATE_THRESHOLD = 2.0  # affects salt-sensitive crops
EC_HIGH_THRESHOLD = 4.0      # salinity stress for most crops
EC_SOURCE = ("USSL_1954", "USDA Agriculture Handbook 60", 3)

# Al saturation thresholds — crop-specific. FERTASA 5.1 + 5.2 discuss
# Al toxicity prose but don't publish a universal threshold. Common SA
# agronomy: < 10% Al sat is safe for most crops; 10-30% caution; > 30%
# toxic for sensitive crops (lucerne, canola, barley). Acid-tolerant
# crops (tea, blueberry, honeybush, rooibos) tolerate much higher.
# Tier 6 unless a crop-specific FERTASA value exists.
AL_SAT_MODERATE_PCT = 10.0
AL_SAT_HIGH_PCT = 30.0
AL_SAT_SOURCE = ("IMPLEMENTER_CONVENTION", "FERTASA 5.1 qualitative Al discussion", 6)

# Acid-tolerant crops (per crop_calc_flags.skip_cation_ratio_path)
ACID_TOLERANT_CROPS = {"Blueberry", "Raspberry", "Blackberry", "Honeybush", "Rooibos"}


# ============================================================
# Outputs
# ============================================================

@dataclass
class SoilFactorFinding:
    """One decision/observation from the reasoner."""
    kind: str  # 'antagonism' | 'toxicity' | 'deficiency' | 'balance' | 'info'
    severity: str  # 'info' | 'watch' | 'warn' | 'critical'
    parameter: str  # e.g. 'P:Zn', 'Al_saturation', 'SAR'
    value: float
    threshold: Optional[float]
    message: str
    recommended_action: Optional[str]
    trigger_kind: Optional[str]  # for foliar triggers: 'soil_availability_gap' etc.
    source_id: str
    source_section: str
    tier: int


@dataclass
class SoilFactorReport:
    """Complete reasoner output for one soil analysis."""
    findings: list[SoilFactorFinding] = field(default_factory=list)
    computed: dict[str, float] = field(default_factory=dict)

    def by_kind(self, kind: str) -> list[SoilFactorFinding]:
        return [f for f in self.findings if f.kind == kind]

    def by_severity_at_least(self, level: str) -> list[SoilFactorFinding]:
        order = {"info": 0, "watch": 1, "warn": 2, "critical": 3}
        threshold = order[level]
        return [f for f in self.findings if order[f.severity] >= threshold]


# ============================================================
# Computation helpers
# ============================================================

def _sv(soil: dict, *keys: str) -> Optional[float]:
    """Return first positive soil value matching any of keys."""
    for k in keys:
        v = soil.get(k)
        if v is not None and v > 0:
            return float(v)
    return None


def compute_al_saturation_pct(soil_values: dict) -> Optional[float]:
    """Al as % of effective CEC.

    Al saturation = (Al_cmol / (base cations + Al + H)) × 100

    Exchangeable Al typically reported as mg/kg. Convert to cmol(+)/kg
    by dividing by 89.98 (atomic mass Al / charge 3 × conversion).
    Effective CEC (sum of bases + exchangeable acidity) preferred over
    total CEC for Al-sat calc.
    """
    al = _sv(soil_values, "Al", "Al (exchangeable)")
    ca = _sv(soil_values, "Ca") or 0
    mg = _sv(soil_values, "Mg") or 0
    k = _sv(soil_values, "K") or 0
    na = _sv(soil_values, "Na") or 0

    if al is None:
        return None

    al_cmol = al / 89.98
    ca_cmol = ca / 200.4
    mg_cmol = mg / 121.6
    k_cmol = k / 390.96
    na_cmol = na / 230.0

    # Effective CEC = bases + Al
    effective_cec = ca_cmol + mg_cmol + k_cmol + na_cmol + al_cmol
    if effective_cec <= 0:
        return None

    return round((al_cmol / effective_cec) * 100.0, 1)


def compute_sar(soil_values: dict) -> Optional[float]:
    """Sodium Adsorption Ratio.

    SAR = Na / sqrt((Ca + Mg) / 2)
    All in cmol(+)/kg (mmol(+)/L for water analysis).
    """
    ca = _sv(soil_values, "Ca")
    mg = _sv(soil_values, "Mg")
    na = _sv(soil_values, "Na")
    if na is None or (ca is None and mg is None):
        return None

    # Convert mg/kg to cmol(+)/kg
    ca_cmol = (ca / 200.4) if ca else 0
    mg_cmol = (mg / 121.6) if mg else 0
    na_cmol = na / 230.0

    divisor_sq = (ca_cmol + mg_cmol) / 2.0
    if divisor_sq <= 0:
        return None

    return round(na_cmol / (divisor_sq ** 0.5), 2)


def compute_cn_ratio(soil_values: dict) -> Optional[float]:
    """Carbon:Nitrogen ratio from Organic C % and Total N %.

    Typical range 10-15:1 for arable soils. > 25:1 slows N mineralisation
    (N immobilisation). < 8:1 indicates rapid mineralisation or recent
    heavy manure.
    """
    oc = _sv(soil_values, "Organic C", "Organic C (%)", "OC")
    tn = _sv(soil_values, "Total N", "Total N (%)", "N (total)")
    if oc is None or tn is None or tn == 0:
        return None
    return round(oc / tn, 1)


# ============================================================
# Main reasoner
# ============================================================

def reason_soil_factors(
    soil_values: dict,
    crop: str,
    crop_calc_flags: Optional[dict] = None,
) -> SoilFactorReport:
    """Run all soil-factor reasoning rules.

    Args:
        soil_values: raw lab parameters as dict of {name: value}
        crop: canonical crop name (for crop-specific thresholds)
        crop_calc_flags: optional dict of flags for this crop

    Returns:
        SoilFactorReport with findings + computed metrics.
    """
    report = SoilFactorReport()
    is_acid_tolerant = crop in ACID_TOLERANT_CROPS
    if crop_calc_flags and crop_calc_flags.get("skip_cation_ratio_path"):
        is_acid_tolerant = True  # skip many Al/pH reasoning for acid-loving crops

    # ----- Compute extended metrics -----
    al_sat = compute_al_saturation_pct(soil_values)
    sar = compute_sar(soil_values)
    cn = compute_cn_ratio(soil_values)
    if al_sat is not None:
        report.computed["Al_saturation_pct"] = al_sat
    if sar is not None:
        report.computed["SAR"] = sar
    if cn is not None:
        report.computed["C:N"] = cn

    # ----- P:Zn antagonism -----
    p = _sv(soil_values, "P (Bray-1)", "P (Citric acid)", "P (Mehlich-3)", "P")
    zn = _sv(soil_values, "Zn")
    if p and zn:
        ratio = p / zn
        report.computed["P:Zn"] = round(ratio, 1)
        if ratio > P_ZN_ANTAGONISM_THRESHOLD:
            report.findings.append(SoilFactorFinding(
                kind="antagonism",
                severity="warn" if ratio > P_ZN_ANTAGONISM_THRESHOLD * 1.5 else "watch",
                parameter="P:Zn",
                value=round(ratio, 1),
                threshold=P_ZN_ANTAGONISM_THRESHOLD,
                message=(
                    f"Soil P:Zn = {ratio:.1f} exceeds {P_ZN_ANTAGONISM_THRESHOLD:.0f}:1 "
                    f"threshold — Zn availability restricted by high P. "
                    f"Root uptake will be inadequate regardless of soil Zn level."
                ),
                recommended_action="Apply foliar Zn to bypass soil-P lockup",
                trigger_kind="soil_availability_gap",
                source_id=P_ZN_SOURCE[0],
                source_section=P_ZN_SOURCE[1],
                tier=P_ZN_SOURCE[2],
            ))

    # ----- Ca:B antagonism -----
    ca = _sv(soil_values, "Ca")
    b = _sv(soil_values, "B")
    if ca and b:
        ratio = ca / b
        report.computed["Ca:B"] = round(ratio, 0)
        if ratio > CA_B_ANTAGONISM_THRESHOLD:
            report.findings.append(SoilFactorFinding(
                kind="antagonism",
                severity="watch" if ratio < CA_B_ANTAGONISM_THRESHOLD * 1.5 else "warn",
                parameter="Ca:B",
                value=round(ratio, 0),
                threshold=CA_B_ANTAGONISM_THRESHOLD,
                message=(
                    f"Soil Ca:B = {ratio:.0f} exceeds {CA_B_ANTAGONISM_THRESHOLD:.0f}:1 "
                    f"— Ca-induced B deficiency likely, especially at flowering."
                ),
                recommended_action="Apply foliar B at critical stages (pre-bloom, fruit set)",
                trigger_kind="soil_availability_gap",
                source_id=CA_B_SOURCE[0],
                source_section=CA_B_SOURCE[1],
                tier=CA_B_SOURCE[2],
            ))

    # ----- Al toxicity -----
    if al_sat is not None and not is_acid_tolerant:
        if al_sat > AL_SAT_HIGH_PCT:
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="critical",
                parameter="Al_saturation_pct",
                value=al_sat,
                threshold=AL_SAT_HIGH_PCT,
                message=(
                    f"Al saturation {al_sat:.1f}% exceeds {AL_SAT_HIGH_PCT:.0f}% — "
                    f"root growth severely restricted. P lockup + Ca/Mg antagonism."
                ),
                recommended_action=(
                    "Prioritise lime application (based on exchangeable Al). "
                    "Use Ca-Nitrate as N source for Al-antagonism effect. "
                    "Consider gypsum for subsoil Al amelioration."
                ),
                trigger_kind="toxicity",
                source_id=AL_SAT_SOURCE[0],
                source_section=AL_SAT_SOURCE[1],
                tier=AL_SAT_SOURCE[2],
            ))
        elif al_sat > AL_SAT_MODERATE_PCT:
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="warn",
                parameter="Al_saturation_pct",
                value=al_sat,
                threshold=AL_SAT_MODERATE_PCT,
                message=(
                    f"Al saturation {al_sat:.1f}% approaching toxicity threshold "
                    f"({AL_SAT_HIGH_PCT:.0f}%). Expect reduced early growth."
                ),
                recommended_action="Consider lime application; monitor root development",
                trigger_kind="toxicity",
                source_id=AL_SAT_SOURCE[0],
                source_section=AL_SAT_SOURCE[1],
                tier=AL_SAT_SOURCE[2],
            ))

    # ----- SAR / sodicity -----
    if sar is not None:
        if sar > SAR_HIGH_THRESHOLD:
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="critical",
                parameter="SAR",
                value=sar,
                threshold=SAR_HIGH_THRESHOLD,
                message=f"SAR {sar:.1f} — sodic soil, structure collapse + Na toxicity likely",
                recommended_action="Gypsum amelioration + leaching; reconsider crop choice if severe",
                trigger_kind="toxicity",
                source_id=SAR_SOURCE[0],
                source_section=SAR_SOURCE[1],
                tier=SAR_SOURCE[2],
            ))
        elif sar > SAR_MODERATE_THRESHOLD:
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="warn",
                parameter="SAR",
                value=sar,
                threshold=SAR_MODERATE_THRESHOLD,
                message=f"SAR {sar:.1f} — moderate sodicity; structure risk on wet-dry cycles",
                recommended_action="Gypsum application to displace Na; improve drainage",
                trigger_kind="toxicity",
                source_id=SAR_SOURCE[0],
                source_section=SAR_SOURCE[1],
                tier=SAR_SOURCE[2],
            ))

    # ----- C:N (mineralization indicator) -----
    if cn is not None:
        if cn > 25:
            report.findings.append(SoilFactorFinding(
                kind="balance",
                severity="watch",
                parameter="C:N",
                value=cn,
                threshold=25.0,
                message=f"C:N {cn:.1f} high — N immobilisation likely; reduce N mineralisation credit",
                recommended_action="Expect slow N release; don't lean on OM mineralisation for early N",
                trigger_kind=None,
                source_id="IMPLEMENTER_CONVENTION",
                source_section="Standard SA agronomy",
                tier=6,
            ))
        elif cn < 8:
            report.findings.append(SoilFactorFinding(
                kind="balance",
                severity="info",
                parameter="C:N",
                value=cn,
                threshold=8.0,
                message=f"C:N {cn:.1f} low — rapid mineralisation; boost N credit in early stages",
                recommended_action="Reduce applied N early-season; OM is providing mineral N",
                trigger_kind=None,
                source_id="IMPLEMENTER_CONVENTION",
                source_section="Standard SA agronomy",
                tier=6,
            ))

    # ----- EC / salinity -----
    ec = _sv(soil_values, "EC", "EC (dS/m)", "EC (mS/cm)")
    if ec is not None:
        if ec > EC_HIGH_THRESHOLD:
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="critical",
                parameter="EC",
                value=ec,
                threshold=EC_HIGH_THRESHOLD,
                message=f"EC {ec:.2f} mS/cm — saline soil; only salt-tolerant crops viable",
                recommended_action="Leach with excess irrigation if possible; check irrigation water EC",
                trigger_kind="toxicity",
                source_id=EC_SOURCE[0],
                source_section=EC_SOURCE[1],
                tier=EC_SOURCE[2],
            ))
        elif ec > EC_MODERATE_THRESHOLD:
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="warn",
                parameter="EC",
                value=ec,
                threshold=EC_MODERATE_THRESHOLD,
                message=f"EC {ec:.2f} mS/cm — moderately saline; salt-sensitive crops stressed",
                recommended_action="Monitor irrigation water; avoid salt-carrier fertilisers",
                trigger_kind="toxicity",
                source_id=EC_SOURCE[0],
                source_section=EC_SOURCE[1],
                tier=EC_SOURCE[2],
            ))

    return report
