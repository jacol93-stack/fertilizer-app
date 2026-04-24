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
  4. Lime-need from N-fertilizer acidification — compute_lime_needed_for_n()
     using IFA 1992 CaO equivalents per kg N per fertilizer type.

Returns structured SoilFactorFindings that the orchestrator converts
into RiskFlags + FoliarEvent triggers + risk-flag narratives.

Provenance discipline:
  - Thresholds sourced to FERTASA / SASRI / ICAR / Foth-Ellis / IFA where
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

# ── Soil ESP (Exchangeable Sodium Percentage) ────────────────────────
# ESP = Na_cmol_per_kg / CEC_cmol_per_kg × 100. Classification per USSL
# + FERTASA: ≥ 15 % = sodic soil; 10-15 % = trending sodic (early
# intervention); < 10 % = non-sodic. The 10 % threshold is the point
# where irrigation-water sodium additions can push the system into
# structural trouble within a season or two.
ESP_TRENDING_THRESHOLD = 10.0
ESP_SODIC_THRESHOLD = 15.0

# ── Irrigation water quality (FAO Irrigation & Drainage Paper 29,
#    Ayers & Westcot 1985, adopted by SA guidelines) ─────────────────
# All thresholds assume water values reported in SA-standard units:
#   EC in dS/m (= mS/cm), ions (Na, Ca, Mg, HCO3) in mg/L
# Water SAR uses the same formula as soil SAR but on water chemistry.
WATER_EC_MODERATE_DS_M = 0.7    # Ayers & Westcot: slight-to-moderate restriction
WATER_EC_SEVERE_DS_M = 3.0      # severe restriction
WATER_SAR_MODERATE = 3.0
WATER_SAR_SEVERE = 9.0
WATER_RSC_MODERATE_MEQ = 1.25   # residual sodium carbonate
WATER_RSC_SEVERE_MEQ = 2.5
WATER_HCO3_MODERATE_MG_L = 90.0
WATER_HCO3_SEVERE_MG_L = 520.0
WATER_QUALITY_SOURCE = ("FAO_IRRIGATION_29", "FAO Ayers & Westcot 1985", 3)

# Ion equivalent weights for mg/L ↔ meq/L conversion
# (atomic weight ÷ charge)
_EQ_WEIGHT_MG_PER_MEQ = {
    "Na": 22.99,
    "Ca": 20.04,
    "Mg": 12.15,
    "HCO3": 61.02,
    "CO3": 30.00,
}

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

# ------------------------------------------------------------
# N-fertilizer soil acidification (IFA World Fertilizer Use Manual
# 1992 Table 1 — "Soil acidification by nitrogen fertilizers").
# Values = kg CaO needed to neutralise the acidification from 1 kg N
# at 50% N utilization rate. Tier 3 (international industry body).
#
# Use: when a programme applies X kg N of a given fertilizer type, the
# lime budget should include X * CAO_PER_KG_N_BY_N_TYPE[fert_type]
# additional CaO to keep pH stable over time.
# ------------------------------------------------------------
CAO_PER_KG_N_BY_N_TYPE: dict[str, float] = {
    # Calcium ammonium nitrate — mildly acidifying (intrinsic Ca offsets some)
    "calcium_ammonium_nitrate": 0.6,  # 27% N blends
    "can": 0.6,  # alias
    # Ammonia / urea / ammonium nitrate — standard 1.0 acidification
    "ammonia": 1.0,
    "urea": 1.0,
    "ammonium_nitrate": 1.0,
    # Diammonium phosphate / ammonium sulphate nitrate
    "dap": 2.0,
    "diammonium_phosphate": 2.0,
    "ammonium_sulphate_nitrate": 2.0,
    "asn": 2.0,  # alias
    # Ammonium sulphate — most acidifying (SO₄ oxidation adds to NH₄ nitrification)
    "ammonium_sulphate": 3.0,
    "ams": 3.0,  # alias
}
IFA_N_ACIDIFICATION_SOURCE = (
    "IFA_WFM_1992",
    "World Fertilizer Use Manual Table 1, intro chapter by Prof. A. Finck",
    3,
)

# Typical first-year N utilization rate (IFA 1992: "mostly 50-70%")
N_UTILIZATION_RATE_FIRST_YEAR = (0.50, 0.70)
N_UTILIZATION_DEFAULT = 0.60  # midpoint for budget calc

# P utilization year 1 (IFA 1992: ~15% in year 1, 1-2% per year after)
P_UTILIZATION_YEAR_1 = 0.15
P_UTILIZATION_PER_YEAR_AFTER = 0.015


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


def compute_lime_needed_for_n(
    n_applied_kg_per_ha: float,
    fertilizer_type: str,
) -> Optional[dict]:
    """CaO required to offset soil acidification from an N application.

    Per IFA 1992 Table 1 (Finck intro, tier 3). Assumes 50% N utilization
    rate — the rest converts to nitrate, drives H⁺ release + base cation
    leaching.

    Args:
        n_applied_kg_per_ha: kg N/ha applied as the given fertilizer
        fertilizer_type: key into CAO_PER_KG_N_BY_N_TYPE (case-insensitive,
            underscore-tolerant). Unknown types return None.

    Returns:
        dict with CaO (kg/ha), citation info. None if fertilizer_type
        is unrecognised.

    Example:
        compute_lime_needed_for_n(150, "urea")
        → {"cao_kg_per_ha": 150.0, "factor": 1.0, ...}
    """
    if n_applied_kg_per_ha <= 0:
        return None
    key = fertilizer_type.strip().lower().replace(" ", "_").replace("-", "_")
    factor = CAO_PER_KG_N_BY_N_TYPE.get(key)
    if factor is None:
        return None
    return {
        "cao_kg_per_ha": round(n_applied_kg_per_ha * factor, 1),
        "factor": factor,
        "fertilizer_type": key,
        "basis": "50% N utilization rate",
        "source_id": IFA_N_ACIDIFICATION_SOURCE[0],
        "source_section": IFA_N_ACIDIFICATION_SOURCE[1],
        "tier": IFA_N_ACIDIFICATION_SOURCE[2],
    }


def compute_soil_esp_pct(soil_values: dict) -> Optional[float]:
    """Soil Exchangeable Sodium Percentage. Preferred path: read from
    base-saturation Na %. Fallback: Na (cmol/kg) / CEC × 100.

    Returns None when neither path is resolvable.
    """
    # Some labs report Na base-sat % directly
    for key in ("Na_base_sat_pct", "Na base sat %", "ESP"):
        val = soil_values.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
    na = _sv(soil_values, "Na")
    cec = _sv(soil_values, "CEC", "T Value", "T-value")
    if na is None or cec is None or cec <= 0:
        return None
    return round(na / cec * 100.0, 1)


def _mg_per_l_to_meq_per_l(mg_per_l: float, ion: str) -> Optional[float]:
    """Convert ion concentration mg/L → meq/L using equivalent weight."""
    eq = _EQ_WEIGHT_MG_PER_MEQ.get(ion)
    if not eq or not mg_per_l:
        return None
    return mg_per_l / eq


def compute_water_sar(water_values: dict) -> Optional[float]:
    """Irrigation water SAR = Na / sqrt((Ca + Mg) / 2), all in meq/L.
    Accepts mg/L inputs and converts internally. Returns None if any
    of Na/Ca/Mg missing."""
    if not water_values:
        return None
    na_mg = water_values.get("Na")
    ca_mg = water_values.get("Ca")
    mg_mg = water_values.get("Mg")
    if na_mg is None or ca_mg is None or mg_mg is None:
        return None
    try:
        na_meq = _mg_per_l_to_meq_per_l(float(na_mg), "Na")
        ca_meq = _mg_per_l_to_meq_per_l(float(ca_mg), "Ca")
        mg_meq = _mg_per_l_to_meq_per_l(float(mg_mg), "Mg")
    except (ValueError, TypeError):
        return None
    if na_meq is None or ca_meq is None or mg_meq is None:
        return None
    denom = ((ca_meq + mg_meq) / 2.0) ** 0.5
    if denom <= 0:
        return None
    return round(na_meq / denom, 2)


def compute_water_rsc_meq(water_values: dict) -> Optional[float]:
    """Residual Sodium Carbonate (meq/L) = (CO3 + HCO3) - (Ca + Mg),
    all in meq/L. Accepts mg/L input. High RSC means bicarbonate
    exceeds Ca + Mg, driving Na onto the exchange after irrigation
    precipitates Ca/Mg carbonates — a slow sodification mechanism
    invisible to soil SAR alone."""
    if not water_values:
        return None
    hco3_mg = water_values.get("HCO3", 0)
    co3_mg = water_values.get("CO3", 0)
    ca_mg = water_values.get("Ca")
    mg_mg = water_values.get("Mg")
    if ca_mg is None or mg_mg is None:
        return None
    try:
        hco3_meq = _mg_per_l_to_meq_per_l(float(hco3_mg), "HCO3") or 0
        co3_meq = _mg_per_l_to_meq_per_l(float(co3_mg), "CO3") or 0
        ca_meq = _mg_per_l_to_meq_per_l(float(ca_mg), "Ca") or 0
        mg_meq = _mg_per_l_to_meq_per_l(float(mg_mg), "Mg") or 0
    except (ValueError, TypeError):
        return None
    return round((hco3_meq + co3_meq) - (ca_meq + mg_meq), 2)


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
    water_values: Optional[dict] = None,
) -> SoilFactorReport:
    """Run all soil-factor reasoning rules.

    Args:
        soil_values: raw lab parameters as dict of {name: value}
        crop: canonical crop name (for crop-specific thresholds)
        crop_calc_flags: optional dict of flags for this crop
        water_values: optional irrigation water analysis (EC dS/m, Na/Ca/Mg/HCO3
            in mg/L). When provided, water × soil compounding rules fire —
            especially the sodic-water-on-trending-ESP-soil escalation.

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

    # ----- Soil ESP + irrigation water compounding ----------------
    # The sodium story has two limbs:
    #   (a) Soil ESP on its own tells us the current state.
    #   (b) Irrigation water SAR / RSC tells us whether every cycle
    #       makes it worse or better.
    # The combination matters far more than either alone — a soil ESP
    # of 12 % is recoverable with gypsum if water is benign, but is
    # heading for structural failure if water SAR is high.
    esp = compute_soil_esp_pct(soil_values)
    if esp is not None:
        report.computed["soil_ESP_pct"] = esp
        if esp >= ESP_SODIC_THRESHOLD:
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="critical",
                parameter="soil_ESP_pct",
                value=esp,
                threshold=ESP_SODIC_THRESHOLD,
                message=f"Soil ESP {esp:.1f} % — sodic (≥ 15 % threshold). "
                        f"Structural breakdown + Na toxicity risk.",
                recommended_action="Gypsum amelioration campaign; verify irrigation water is not re-adding Na",
                trigger_kind="toxicity",
                source_id="USSL_1954",
                source_section="USDA Ag Handbook 60",
                tier=3,
            ))
        elif esp >= ESP_TRENDING_THRESHOLD:
            report.findings.append(SoilFactorFinding(
                kind="balance",
                severity="warn",
                parameter="soil_ESP_pct",
                value=esp,
                threshold=ESP_TRENDING_THRESHOLD,
                message=f"Soil ESP {esp:.1f} % — trending toward sodic (10–15 % band). "
                        f"Early intervention prevents structural damage.",
                recommended_action="Start gypsum programme; confirm irrigation water is not Na-loaded",
                trigger_kind=None,
                source_id="USSL_1954",
                source_section="USDA Ag Handbook 60",
                tier=3,
            ))

    # Irrigation water quality findings (when water_values supplied)
    if water_values:
        water_sar = compute_water_sar(water_values)
        water_rsc = compute_water_rsc_meq(water_values)
        water_ec = None
        ec_raw = water_values.get("EC")
        if ec_raw is not None:
            try:
                water_ec = float(ec_raw)
            except (ValueError, TypeError):
                pass
        hco3_raw = water_values.get("HCO3")
        water_hco3 = None
        if hco3_raw is not None:
            try:
                water_hco3 = float(hco3_raw)
            except (ValueError, TypeError):
                pass

        if water_sar is not None:
            report.computed["water_SAR"] = water_sar
        if water_rsc is not None:
            report.computed["water_RSC_meq"] = water_rsc
        if water_ec is not None:
            report.computed["water_EC_dS_m"] = water_ec

        # Water SAR on its own
        if water_sar is not None:
            if water_sar > WATER_SAR_SEVERE:
                report.findings.append(SoilFactorFinding(
                    kind="toxicity",
                    severity="warn",
                    parameter="water_SAR",
                    value=water_sar,
                    threshold=WATER_SAR_SEVERE,
                    message=f"Irrigation water SAR {water_sar:.1f} — severe sodium hazard on water. "
                            f"Every cycle is adding Na to the exchange.",
                    recommended_action="Gypsum programme sized against water-delivered Na; investigate alternative water source",
                    trigger_kind="toxicity",
                    source_id=WATER_QUALITY_SOURCE[0],
                    source_section=WATER_QUALITY_SOURCE[1],
                    tier=WATER_QUALITY_SOURCE[2],
                ))
            elif water_sar > WATER_SAR_MODERATE:
                report.findings.append(SoilFactorFinding(
                    kind="balance",
                    severity="watch",
                    parameter="water_SAR",
                    value=water_sar,
                    threshold=WATER_SAR_MODERATE,
                    message=f"Irrigation water SAR {water_sar:.1f} — moderate sodium hazard. "
                            f"Monitor soil ESP annually.",
                    recommended_action="Maintenance gypsum; track soil ESP trend each season",
                    trigger_kind=None,
                    source_id=WATER_QUALITY_SOURCE[0],
                    source_section=WATER_QUALITY_SOURCE[1],
                    tier=WATER_QUALITY_SOURCE[2],
                ))

        # RSC on its own
        if water_rsc is not None and water_rsc > WATER_RSC_SEVERE_MEQ:
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="warn",
                parameter="water_RSC_meq",
                value=water_rsc,
                threshold=WATER_RSC_SEVERE_MEQ,
                message=f"Irrigation water RSC {water_rsc:.2f} meq/L — severe. "
                        f"Bicarbonate precipitates Ca/Mg as carbonates, "
                        f"concentrating Na on the exchange.",
                recommended_action="Acidify water (sulphuric acid injection) or blend with cleaner source; "
                                   "gypsum alone does not solve bicarbonate-driven sodification",
                trigger_kind="toxicity",
                source_id=WATER_QUALITY_SOURCE[0],
                source_section=WATER_QUALITY_SOURCE[1],
                tier=WATER_QUALITY_SOURCE[2],
            ))

        # Water EC on its own
        if water_ec is not None and water_ec > WATER_EC_SEVERE_DS_M:
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="warn",
                parameter="water_EC_dS_m",
                value=water_ec,
                threshold=WATER_EC_SEVERE_DS_M,
                message=f"Irrigation water EC {water_ec:.2f} dS/m — severe salinity. "
                        f"Crop yield penalty without leaching fraction.",
                recommended_action="Apply 15-25 % leaching fraction; avoid salt-carrier fertilisers; "
                                   "crop choice reconsidered for salt-sensitive species",
                trigger_kind="toxicity",
                source_id=WATER_QUALITY_SOURCE[0],
                source_section=WATER_QUALITY_SOURCE[1],
                tier=WATER_QUALITY_SOURCE[2],
            ))

        # Compounding: sodic water × trending-to-sodic soil. This is the
        # Karoo-Prince-Albert pattern — gypsum alone treads water unless
        # water is simultaneously addressed.
        if (esp is not None and water_sar is not None
                and esp >= ESP_TRENDING_THRESHOLD
                and water_sar > WATER_SAR_MODERATE):
            report.findings.append(SoilFactorFinding(
                kind="toxicity",
                severity="critical",
                parameter="soil_ESP_x_water_SAR",
                value=water_sar,
                threshold=WATER_SAR_MODERATE,
                message=(
                    f"Compounding sodium hazard: soil ESP {esp:.1f} % "
                    f"(already trending/sodic) + irrigation water SAR {water_sar:.1f}. "
                    f"Gypsum at conventional rates will tread water — every "
                    f"irrigation cycle re-adds Na as fast as gypsum displaces it."
                ),
                recommended_action=(
                    "Escalate gypsum rate materially (2-3× standard), investigate alternative water source, "
                    "and plan multi-season remediation. Get an irrigation water test if not already done."
                ),
                trigger_kind="toxicity",
                source_id=WATER_QUALITY_SOURCE[0],
                source_section=WATER_QUALITY_SOURCE[1],
                tier=WATER_QUALITY_SOURCE[2],
            ))

    return report
