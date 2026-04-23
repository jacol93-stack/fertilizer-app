"""
Pre-Season Module — Phase 2 reasoning module 2 of 10.

Three modes based on time-gap between programme build_date and
planting_date:

    MODE A — RECOMMEND (lead time available)
        Engine recommends soil-improvement actions with timing.
        For each soil-factor finding (Al toxicity, sodicity, low pH,
        deficient amendments), check: is there enough lead time for
        a relevant pre-season material to react? If yes, produce a
        PreSeasonRecommendation with apply-by date.

    MODE B — SUBTRACT RESIDUAL (already applied)
        Programme has PreSeasonInput entries. Engine computes effective
        nutrient contribution at planting (= applied × reaction_pct ×
        soil_fixation_factor) and subtracts from season targets.
        Mirrors the Clivia §03 "residual position" calculation.

    MODE C — LOST OPPORTUNITY (too late)
        Time gap insufficient for any pre-season amendment to react.
        Engine produces OutstandingItems noting what could have been
        done with more lead time, plus RiskFlags about the consequences
        of going ahead without amendment.

Modes are not mutually exclusive — a programme can both have residual
inputs (B) AND new recommendations (A) AND lost opportunities (C) for
amendments still missing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from app.models import (
    Assumption,
    OutstandingItem,
    PreSeasonInput,
    PreSeasonRecommendation,
    RiskFlag,
    SourceCitation,
    Tier,
)
from app.services.soil_factor_reasoner import SoilFactorReport


# ============================================================
# Default reaction-time profiles (Tier 6 — IFA + standard SA agronomy)
# Referenced when materials table doesn't have reaction_time set.
# ============================================================

DEFAULT_REACTION_PROFILES: dict[str, tuple[float, float, str]] = {
    # (min_months, max_months, purpose)
    "lime": (3.0, 6.0, "pH lift + Ca contribution + partial Al displacement"),
    "calcitic_lime": (3.0, 6.0, "pH lift + Ca contribution + partial Al displacement"),
    "dolomitic_lime": (4.0, 8.0, "pH lift + Ca + Mg contribution"),
    "gypsum": (0.5, 2.0, "Na displacement; subsoil Ca + S; pH-neutral"),
    "rock_phosphate": (12.0, 36.0, "Slow P release on acid soils; long-term P building"),
    "manure": (2.0, 12.0, "OM building + slow N release"),
    "compost": (3.0, 12.0, "OM building + slow nutrient release"),
    "elemental_sulphur": (3.0, 9.0, "pH reduction (acidification); slow conversion via bacteria"),
}

# Soil-fixation factors for residual contribution math (Tier 6)
# Drives the "effective nutrient available at planting" calc.
P_FIXATION_FACTOR_HIGH_AL = 0.5  # Clivia: "~50% P2O5 fixed by Al"
P_FIXATION_FACTOR_LOW_AL = 0.85  # mostly available
N_LEACHING_FACTOR_WET = 0.10  # Clivia: "N largely leached by summer rain"
N_LEACHING_FACTOR_DRY = 0.50  # winter-applied N retains better

PRE_SEASON_SOURCE = (
    "IMPLEMENTER_CONVENTION",
    "Standard SA agronomy + Foth-Ellis Soil Fertility 2nd ed. + IFA 1992",
    6,
)


# ============================================================
# Containers
# ============================================================

@dataclass
class PreSeasonReport:
    """Output of the pre-season module — three lists for the three modes."""
    recommendations: list[PreSeasonRecommendation]  # Mode A
    residual_subtraction: dict[str, float]  # Mode B: nutrient → kg/ha to subtract
    lost_opportunities: list[OutstandingItem]  # Mode C
    risk_flags: list[RiskFlag]  # Cross-mode warnings
    assumptions: list[Assumption]  # Defaults applied during reasoning


# ============================================================
# Mode A — Recommend
# ============================================================

def recommend_pre_season_actions(
    block_id: str,
    soil_factor_report: SoilFactorReport,
    build_date: date,
    planting_date: date,
    available_materials: Optional[list[dict]] = None,
) -> list[PreSeasonRecommendation]:
    """Mode A — produce recommendations IF time gap allows.

    Args:
        block_id: programme block id
        soil_factor_report: from SoilFactorReasoner
        build_date: when the programme is being built (today usually)
        planting_date: when the crop will be planted
        available_materials: list of material dicts {material, applicability,
                             reaction_time_months_min/max, soil_improvement_purpose,
                             ca, mg, s, ...}. If None, falls back to defaults.

    Returns:
        list of PreSeasonRecommendation, one per (finding × applicable material).
        Empty if no lead time or no relevant findings.
    """
    months_to_planting = _months_between(build_date, planting_date)
    if months_to_planting <= 0:
        return []

    recs: list[PreSeasonRecommendation] = []

    # ----- Al toxicity → recommend lime if lead time allows (3-6 mo) -----
    al_findings = [f for f in soil_factor_report.findings
                   if f.parameter == "Al_saturation_pct" and f.severity in ("warn", "critical")]
    for finding in al_findings:
        rec = _try_recommend_lime(
            block_id=block_id,
            finding_message=finding.message,
            build_date=build_date,
            planting_date=planting_date,
            months_to_planting=months_to_planting,
            available_materials=available_materials,
        )
        if rec:
            recs.append(rec)

    # ----- Sodicity → recommend gypsum (0.5-2 mo lead time) -----
    sar_findings = [f for f in soil_factor_report.findings
                    if f.parameter == "SAR" and f.severity in ("warn", "critical")]
    for finding in sar_findings:
        rec = _try_recommend_gypsum(
            block_id=block_id,
            finding_message=finding.message,
            build_date=build_date,
            planting_date=planting_date,
            months_to_planting=months_to_planting,
            available_materials=available_materials,
        )
        if rec:
            recs.append(rec)

    return recs


def _try_recommend_lime(
    block_id: str,
    finding_message: str,
    build_date: date,
    planting_date: date,
    months_to_planting: float,
    available_materials: Optional[list[dict]],
) -> Optional[PreSeasonRecommendation]:
    """Try to recommend lime IF months_to_planting >= reaction_time_min."""
    material_row = _find_material(available_materials, "Calcitic Lime")
    min_months = (material_row.get("reaction_time_months_min") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["calcitic_lime"][0]
    max_months = (material_row.get("reaction_time_months_max") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["calcitic_lime"][1]
    purpose = (material_row.get("soil_improvement_purpose") if material_row
               else None) or DEFAULT_REACTION_PROFILES["calcitic_lime"][2]

    if months_to_planting < float(min_months):
        return None  # Mode C — lost opportunity, handled separately

    apply_by = planting_date - timedelta(days=int(float(min_months) * 30))
    expected_pct = min(100, int((months_to_planting / float(max_months)) * 100))

    return PreSeasonRecommendation(
        block_id=block_id,
        material="Calcitic Lime",
        target_rate_per_ha="1 500-2 500 kg/ha (size to lime requirement test)",
        purpose=purpose,
        reason=f"Address: {finding_message}",
        recommended_apply_by_date=apply_by,
        reaction_time_months=float(min_months),
        expected_status_at_planting=(
            f"~{expected_pct}% reacted at planting if applied by {apply_by.isoformat()}"
        ),
        source=SourceCitation(
            source_id=PRE_SEASON_SOURCE[0],
            section=PRE_SEASON_SOURCE[1],
            tier=Tier(PRE_SEASON_SOURCE[2]),
        ),
    )


def _try_recommend_gypsum(
    block_id: str,
    finding_message: str,
    build_date: date,
    planting_date: date,
    months_to_planting: float,
    available_materials: Optional[list[dict]],
) -> Optional[PreSeasonRecommendation]:
    """Recommend gypsum if SAR active and lead time allows."""
    material_row = _find_material(available_materials, "Gypsum")
    min_months = (material_row.get("reaction_time_months_min") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["gypsum"][0]
    max_months = (material_row.get("reaction_time_months_max") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["gypsum"][1]
    purpose = (material_row.get("soil_improvement_purpose") if material_row
               else None) or DEFAULT_REACTION_PROFILES["gypsum"][2]

    if months_to_planting < float(min_months):
        return None

    apply_by = planting_date - timedelta(days=int(float(min_months) * 30))
    expected_pct = min(100, int((months_to_planting / float(max_months)) * 100))

    return PreSeasonRecommendation(
        block_id=block_id,
        material="Gypsum",
        target_rate_per_ha="2-4 t/ha (size to gypsum requirement from SAR + ESP)",
        purpose=purpose,
        reason=f"Address: {finding_message}",
        recommended_apply_by_date=apply_by,
        reaction_time_months=float(min_months),
        expected_status_at_planting=(
            f"~{expected_pct}% Na displacement at planting if applied by {apply_by.isoformat()}"
        ),
        source=SourceCitation(
            source_id=PRE_SEASON_SOURCE[0],
            section=PRE_SEASON_SOURCE[1],
            tier=Tier(PRE_SEASON_SOURCE[2]),
        ),
    )


# ============================================================
# Mode B — Compute residual subtraction
# ============================================================

def compute_residual_position(
    pre_season_inputs: list[PreSeasonInput],
    planting_date: date,
    high_al_soil: bool = False,
    wet_summer_between_apply_and_plant: bool = False,
    available_materials: Optional[list[dict]] = None,
) -> tuple[list[PreSeasonInput], dict[str, float]]:
    """Mode B — compute effective nutrient contribution from already-applied
    inputs and the residual subtraction to apply to season targets.

    Args:
        pre_season_inputs: list of PreSeasonInput with applied_date set
        planting_date: when the programme starts
        high_al_soil: if True, applies P-fixation factor (Clivia case)
        wet_summer_between_apply_and_plant: applies N-leaching factor
        available_materials: lookup for material composition

    Returns:
        Tuple of:
          - Updated PreSeasonInput list with effective_*_kg_per_ha populated
          - Residual subtraction dict {nutrient: kg/ha to subtract from targets}
            Keys: 'N', 'P2O5', 'K2O', 'Ca', 'Mg', 'S'
    """
    subtraction: dict[str, float] = {"N": 0, "P2O5": 0, "K2O": 0, "Ca": 0, "Mg": 0, "S": 0}
    updated_inputs = []

    for psi in pre_season_inputs:
        material_row = _find_material(available_materials, psi.product)
        rate_kg_ha = _parse_rate_kg_ha(psi.rate)
        if rate_kg_ha is None or material_row is None:
            updated_inputs.append(psi)
            continue

        # Reaction state at planting
        if psi.applied_date:
            months_since = _months_between(psi.applied_date, planting_date)
            min_rt = float(material_row.get("reaction_time_months_min") or 0)
            max_rt = float(material_row.get("reaction_time_months_max") or 1)
            reaction_pct = min(1.0, months_since / max(max_rt, 0.01))
        else:
            reaction_pct = 1.0  # assume fully reacted if no date

        # Per-nutrient contribution = rate × pct of element × reaction_pct × fixation
        # All material % columns are already in % of total mass
        n_pct = float(material_row.get("n") or 0) / 100.0
        p_pct = float(material_row.get("p") or 0) / 100.0  # Note: materials.p is P2O5 in this DB
        k_pct = float(material_row.get("k") or 0) / 100.0
        ca_pct = float(material_row.get("ca") or 0) / 100.0
        mg_pct = float(material_row.get("mg") or 0) / 100.0
        s_pct = float(material_row.get("s") or 0) / 100.0

        # Soil-modifier factors
        n_modifier = N_LEACHING_FACTOR_WET if wet_summer_between_apply_and_plant else N_LEACHING_FACTOR_DRY
        p_modifier = P_FIXATION_FACTOR_HIGH_AL if high_al_soil else P_FIXATION_FACTOR_LOW_AL

        eff_n = rate_kg_ha * n_pct * reaction_pct * n_modifier
        eff_p = rate_kg_ha * p_pct * reaction_pct * p_modifier
        eff_k = rate_kg_ha * k_pct * reaction_pct  # K mostly mobile, no fixation
        eff_ca = rate_kg_ha * ca_pct * reaction_pct
        eff_mg = rate_kg_ha * mg_pct * reaction_pct
        eff_s = rate_kg_ha * s_pct * reaction_pct

        subtraction["N"] += eff_n
        subtraction["P2O5"] += eff_p
        subtraction["K2O"] += eff_k
        subtraction["Ca"] += eff_ca
        subtraction["Mg"] += eff_mg
        subtraction["S"] += eff_s

        # Update PSI with effective contributions (round for display)
        updated = psi.model_copy(update={
            "effective_n_kg_per_ha": round(eff_n, 1),
            "effective_p2o5_kg_per_ha": round(eff_p, 1),
            "effective_k2o_kg_per_ha": round(eff_k, 1),
            "effective_ca_kg_per_ha": round(eff_ca, 1),
            "effective_mg_kg_per_ha": round(eff_mg, 1),
            "effective_s_kg_per_ha": round(eff_s, 1),
        })
        updated_inputs.append(updated)

    # Round subtraction totals
    subtraction = {k: round(v, 1) for k, v in subtraction.items()}
    return updated_inputs, subtraction


# ============================================================
# Mode C — Lost opportunity flagging
# ============================================================

def flag_lost_opportunities(
    soil_factor_report: SoilFactorReport,
    build_date: date,
    planting_date: date,
) -> tuple[list[OutstandingItem], list[RiskFlag]]:
    """Mode C — when programme is built too close to planting for amendments
    to react, flag what could have been done.
    """
    items: list[OutstandingItem] = []
    flags: list[RiskFlag] = []
    months = _months_between(build_date, planting_date)

    al_findings = [f for f in soil_factor_report.findings
                   if f.parameter == "Al_saturation_pct" and f.severity in ("warn", "critical")]
    if al_findings and months < DEFAULT_REACTION_PROFILES["calcitic_lime"][0]:
        items.append(OutstandingItem(
            item="Lime application — too late this season for full reaction",
            why_it_matters=(
                f"Al saturation needs lime to neutralise. Lime requires 3-6 months "
                f"to react fully. Build-to-plant gap is only {months:.1f} months — "
                f"insufficient for this season. Schedule lime for post-harvest of "
                f"this crop to set up the next season."
            ),
            impact_if_skipped="Al stress will persist into the following season",
        ))
        flags.append(RiskFlag(
            message=(
                f"Al active but no time to lime (gap {months:.1f} months, lime needs 3-6). "
                f"This season will run on existing soil chemistry — slower early growth + "
                f"P lockup. Use Ca-Nitrate as N source for partial Al antagonism."
            ),
            severity="warn",
            source=SourceCitation(
                source_id=PRE_SEASON_SOURCE[0],
                section=PRE_SEASON_SOURCE[1],
                tier=Tier(PRE_SEASON_SOURCE[2]),
            ),
        ))

    sar_findings = [f for f in soil_factor_report.findings
                    if f.parameter == "SAR" and f.severity in ("warn", "critical")]
    if sar_findings and months < DEFAULT_REACTION_PROFILES["gypsum"][0]:
        items.append(OutstandingItem(
            item="Gypsum application — too late this season for full Na displacement",
            why_it_matters=(
                f"Sodicity needs gypsum to displace Na. Gypsum requires ~0.5-2 months. "
                f"Build-to-plant gap is only {months:.1f} months — schedule for post-harvest."
            ),
            impact_if_skipped="Soil structure problems persist; Na toxicity continues",
        ))

    return items, flags


# ============================================================
# Helpers
# ============================================================

def _months_between(start: date, end: date) -> float:
    """Approximate months between two dates (30.44 days/month average)."""
    return (end - start).days / 30.44


def _find_material(available_materials: Optional[list[dict]], name: str) -> Optional[dict]:
    """Case-insensitive material lookup."""
    if not available_materials:
        return None
    for m in available_materials:
        if m.get("material", "").strip().lower() == name.strip().lower():
            return m
    return None


def _parse_rate_kg_ha(rate: str) -> Optional[float]:
    """Parse a rate string like '1 500 kg/ha' or '2 t/ha' to kg/ha."""
    if not rate:
        return None
    s = rate.replace(",", "").replace(" ", "").strip().lower()
    try:
        # 1 500 kg/ha → 1500 kg/ha
        if "t/ha" in s:
            num = float(s.replace("t/ha", ""))
            return num * 1000.0
        if "kg/ha" in s:
            return float(s.replace("kg/ha", ""))
    except ValueError:
        return None
    return None
