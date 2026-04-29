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
        Empty only when there are no relevant soil findings — late builds
        still emit recommendations, just with adapted timing guidance
        (apply for full reaction by next cycle's window).
    """
    months_to_planting = _months_between(build_date, planting_date)

    recs: list[PreSeasonRecommendation] = []

    # Defensive: if the block already reads alkaline (KCl ≥ 7.0 or H2O
    # ≥ 7.5), skip Al-driven lime — Al saturation can co-exist with
    # high pH on mottled / variable soils, but liming further locks
    # out micros. Note the pH-low finding can never co-fire with this
    # guard (a pH-low reading is by definition not alkaline), so the
    # pH-driven lime path is unaffected.
    measured_ph_kcl = soil_factor_report.computed.get("pH (KCl)")
    measured_ph_h2o = soil_factor_report.computed.get("pH (H2O)")
    ph_is_already_alkaline = (
        (measured_ph_kcl is not None and measured_ph_kcl >= 7.0)
        or (measured_ph_h2o is not None and measured_ph_h2o >= 7.5)
    )

    # ----- Lime triggers (deduped): Al toxicity + pH-low -----
    # Both trigger lime; combine reasons into a single recommendation
    # so the agronomist doesn't see two near-identical lime entries
    # for the same block.
    lime_reasons: list[str] = []
    al_findings = [f for f in soil_factor_report.findings
                   if f.parameter == "Al_saturation_pct" and f.severity in ("warn", "critical")]
    if al_findings and not ph_is_already_alkaline:
        lime_reasons.extend(f.message for f in al_findings)
    ph_low_findings = [f for f in soil_factor_report.findings
                       if f.parameter == "pH (KCl)" and f.severity in ("warn", "critical")]
    lime_reasons.extend(f.message for f in ph_low_findings)
    if lime_reasons:
        recs.append(_recommend_lime(
            block_id=block_id,
            finding_message=" | ".join(lime_reasons),
            build_date=build_date,
            planting_date=planting_date,
            months_to_planting=months_to_planting,
            available_materials=available_materials,
        ))

    # ----- Sulphur trigger: pH above crop optimal -----
    # New 2026-04-28 path. Acidifying amendment for alkaline soils on
    # non-acid-loving crops. Slow conversion (3-9 months via Thiobacillus)
    # so always emit, with adaptive timing guidance.
    ph_high_findings = [f for f in soil_factor_report.findings
                        if f.parameter == "pH (KCl)_high" and f.severity in ("warn", "critical")]
    if ph_high_findings:
        recs.append(_recommend_sulphur(
            block_id=block_id,
            finding_message=" | ".join(f.message for f in ph_high_findings),
            build_date=build_date,
            planting_date=planting_date,
            months_to_planting=months_to_planting,
            available_materials=available_materials,
        ))

    # ----- Gypsum triggers (deduped): SAR + Ca:Mg-low at OK pH -----
    # SAR-driven (Na displacement) and Ca:Mg-driven (Ca shortage at
    # adequate pH) both call for gypsum — fold both reasons into one
    # recommendation. Ca:Mg path is gated by pH-in-band on the reasoner
    # side, so when it fires lime would over-shoot.
    gypsum_reasons: list[str] = []
    sar_findings = [f for f in soil_factor_report.findings
                    if f.parameter == "SAR" and f.severity in ("warn", "critical")]
    gypsum_reasons.extend(f.message for f in sar_findings)
    ca_mg_findings = [f for f in soil_factor_report.findings
                      if f.parameter == "Ca:Mg" and f.severity in ("warn", "critical")]
    gypsum_reasons.extend(f.message for f in ca_mg_findings)
    if gypsum_reasons:
        recs.append(_recommend_gypsum(
            block_id=block_id,
            finding_message=" | ".join(gypsum_reasons),
            build_date=build_date,
            planting_date=planting_date,
            months_to_planting=months_to_planting,
            available_materials=available_materials,
        ))

    return recs


def _recommend_lime(
    block_id: str,
    finding_message: str,
    build_date: date,
    planting_date: date,
    months_to_planting: float,
    available_materials: Optional[list[dict]],
) -> PreSeasonRecommendation:
    """Always emit a lime recommendation when an Al-saturation finding
    fires. Timing guidance adapts to the lead-time available — see
    `_adaptive_apply_by_and_status` for the four-window logic.
    """
    material_row = _find_material(available_materials, "Calcitic Lime")
    min_months = (material_row.get("reaction_time_months_min") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["calcitic_lime"][0]
    max_months = (material_row.get("reaction_time_months_max") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["calcitic_lime"][1]
    purpose = (material_row.get("soil_improvement_purpose") if material_row
               else None) or DEFAULT_REACTION_PROFILES["calcitic_lime"][2]

    apply_by, expected = _adaptive_apply_by_and_status(
        build_date=build_date,
        planting_date=planting_date,
        months_to_planting=months_to_planting,
        min_months=float(min_months),
        max_months=float(max_months),
        action_verb="reacted",
    )
    return PreSeasonRecommendation(
        block_id=block_id,
        material="Calcitic Lime",
        target_rate_per_ha="1 500-2 500 kg/ha (size to lime requirement test)",
        purpose=purpose,
        reason=f"Address: {finding_message}",
        recommended_apply_by_date=apply_by,
        reaction_time_months=float(min_months),
        expected_status_at_planting=expected,
        source=SourceCitation(
            source_id=PRE_SEASON_SOURCE[0],
            section=PRE_SEASON_SOURCE[1],
            tier=Tier(PRE_SEASON_SOURCE[2]),
        ),
    )


def _recommend_gypsum(
    block_id: str,
    finding_message: str,
    build_date: date,
    planting_date: date,
    months_to_planting: float,
    available_materials: Optional[list[dict]],
) -> PreSeasonRecommendation:
    """Always emit a gypsum recommendation when a sodicity finding
    fires. Timing guidance adapts the same way as the lime helper."""
    material_row = _find_material(available_materials, "Gypsum")
    min_months = (material_row.get("reaction_time_months_min") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["gypsum"][0]
    max_months = (material_row.get("reaction_time_months_max") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["gypsum"][1]
    purpose = (material_row.get("soil_improvement_purpose") if material_row
               else None) or DEFAULT_REACTION_PROFILES["gypsum"][2]

    apply_by, expected = _adaptive_apply_by_and_status(
        build_date=build_date,
        planting_date=planting_date,
        months_to_planting=months_to_planting,
        min_months=float(min_months),
        max_months=float(max_months),
        action_verb="Na displacement",
    )
    return PreSeasonRecommendation(
        block_id=block_id,
        material="Gypsum",
        target_rate_per_ha="2-4 t/ha (size to gypsum requirement from SAR + ESP)",
        purpose=purpose,
        reason=f"Address: {finding_message}",
        recommended_apply_by_date=apply_by,
        reaction_time_months=float(min_months),
        expected_status_at_planting=expected,
        source=SourceCitation(
            source_id=PRE_SEASON_SOURCE[0],
            section=PRE_SEASON_SOURCE[1],
            tier=Tier(PRE_SEASON_SOURCE[2]),
        ),
    )


def _recommend_sulphur(
    block_id: str,
    finding_message: str,
    build_date: date,
    planting_date: date,
    months_to_planting: float,
    available_materials: Optional[list[dict]],
) -> PreSeasonRecommendation:
    """Elemental sulphur recommendation for alkaline soils. Slow
    bacterial oxidation (3-9 months) means timing guidance matters more
    than for gypsum — apply early enough for Thiobacillus to convert S⁰
    to SO₄ + H⁺ before peak demand."""
    material_row = _find_material(available_materials, "Elemental Sulphur")
    min_months = (material_row.get("reaction_time_months_min") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["elemental_sulphur"][0]
    max_months = (material_row.get("reaction_time_months_max") if material_row
                  else None) or DEFAULT_REACTION_PROFILES["elemental_sulphur"][1]
    purpose = (material_row.get("soil_improvement_purpose") if material_row
               else None) or DEFAULT_REACTION_PROFILES["elemental_sulphur"][2]

    apply_by, expected = _adaptive_apply_by_and_status(
        build_date=build_date,
        planting_date=planting_date,
        months_to_planting=months_to_planting,
        min_months=float(min_months),
        max_months=float(max_months),
        action_verb="acidification",
    )
    return PreSeasonRecommendation(
        block_id=block_id,
        material="Elemental Sulphur",
        target_rate_per_ha="500-1 500 kg/ha (size to pH excess + soil buffer; "
                           "split applications on heavier rates)",
        purpose=purpose,
        reason=f"Address: {finding_message}",
        recommended_apply_by_date=apply_by,
        reaction_time_months=float(min_months),
        expected_status_at_planting=expected,
        source=SourceCitation(
            source_id=PRE_SEASON_SOURCE[0],
            section=PRE_SEASON_SOURCE[1],
            tier=Tier(PRE_SEASON_SOURCE[2]),
        ),
    )


def _adaptive_apply_by_and_status(
    *,
    build_date: date,
    planting_date: date,
    months_to_planting: float,
    min_months: float,
    max_months: float,
    action_verb: str,
) -> tuple[date, str]:
    """Compute (apply_by_date, expected_status_string) for any pre-
    season amendment, given the lead time available. Four windows:

      1. ON-TIME with full reaction
         (lead ≥ max_months): apply by season-cycle start − min_months,
         "fully reacted by season start".

      2. ON-TIME with partial reaction
         (min_months ≤ lead < max_months): apply by season-cycle start
         − min_months, "expected ~X% reacted by season start".

      3. LATE — limited reaction this cycle
         (0 < lead < min_months): apply as soon as possible (early
         build_date + 7 days), "limited reaction time this season —
         partial benefit this cycle, full benefit next".

      4. PAST — next cycle window
         (lead ≤ 0): build is at or after the cycle start. Pivot the
         apply-by to next cycle (planting_date + 12 months − min_months),
         "apply as soon as practical for full reaction by next cycle".

    For mature perennials there's no real "planting" event — the
    `planting_date` is the season-cycle start used as the timing anchor.
    Recommendations always emit so the agronomist sees the soil-side
    correction need regardless of when the programme is built.
    """
    if months_to_planting >= max_months:
        # Window 1 — on time, full reaction
        apply_by = planting_date - timedelta(days=int(min_months * 30))
        return apply_by, (
            f"Fully reacted by season start (~{int(max_months)}-month reaction "
            f"window covered)."
        )
    if months_to_planting >= min_months:
        # Window 2 — on time, partial reaction
        apply_by = planting_date - timedelta(days=int(min_months * 30))
        pct = max(0, min(100, int((months_to_planting / max_months) * 100)))
        return apply_by, (
            f"~{pct}% reacted by season start. Plan a top-up next cycle for "
            f"full benefit."
        )
    if months_to_planting > 0:
        # Window 3 — late but cycle hasn't started; apply now for partial
        apply_by = build_date + timedelta(days=7)
        return apply_by, (
            f"Limited reaction time this cycle ({months_to_planting:.1f} mo "
            f"available, {min_months:.0f} mo ideal). Apply at the earliest "
            f"opportunity — partial benefit this season, full benefit next."
        )
    # Window 4 — cycle already started, target next cycle
    next_cycle_start = date(planting_date.year + 1, planting_date.month, planting_date.day)
    apply_by = next_cycle_start - timedelta(days=int(min_months * 30))
    return apply_by, (
        f"Cycle already underway — apply at the earliest opportunity to set up "
        f"full {action_verb} for the next cycle (target reaction window: "
        f"~{int(min_months)} months before {next_cycle_start.isoformat()})."
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
    ph_low_findings = [f for f in soil_factor_report.findings
                       if f.parameter == "pH (KCl)" and f.severity in ("warn", "critical")]
    lime_too_late = (al_findings or ph_low_findings) and months < DEFAULT_REACTION_PROFILES["calcitic_lime"][0]
    if lime_too_late:
        items.append(OutstandingItem(
            item="Lime application — too late this season for full reaction",
            why_it_matters=(
                f"Soil acidity / Al saturation needs lime to correct. Lime requires "
                f"3-6 months to react fully. Build-to-plant gap is only "
                f"{months:.1f} months — insufficient for this season. Schedule lime "
                f"for post-harvest of this crop to set up the next season."
            ),
            impact_if_skipped=(
                "Acidity / Al stress persists into the following season; early-"
                "growth and P availability will under-perform"
            ),
        ))
    if al_findings and months < DEFAULT_REACTION_PROFILES["calcitic_lime"][0]:
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
    if ph_low_findings and not al_findings and months < DEFAULT_REACTION_PROFILES["calcitic_lime"][0]:
        flags.append(RiskFlag(
            message=(
                f"Acidic pH but no time to lime (gap {months:.1f} months, lime needs 3-6). "
                f"Ca / Mg / P availability will run below capacity this season; lean "
                f"on foliar Ca + Mg at critical stages and avoid acidifying N sources."
            ),
            severity="warn",
            source=SourceCitation(
                source_id=PRE_SEASON_SOURCE[0],
                section=PRE_SEASON_SOURCE[1],
                tier=Tier(PRE_SEASON_SOURCE[2]),
            ),
        ))

    ph_high_findings = [f for f in soil_factor_report.findings
                        if f.parameter == "pH (KCl)_high" and f.severity in ("warn", "critical")]
    if ph_high_findings and months < DEFAULT_REACTION_PROFILES["elemental_sulphur"][0]:
        items.append(OutstandingItem(
            item="Elemental sulphur application — too late this season for pH correction",
            why_it_matters=(
                f"Alkaline soil needs elemental sulphur to acidify. Bacterial "
                f"oxidation requires 3-9 months. Build-to-plant gap is only "
                f"{months:.1f} months — schedule sulphur for post-harvest."
            ),
            impact_if_skipped=(
                "Zn / Fe / Mn / B / P availability remain locked at current pH; "
                "expect micronutrient deficiencies despite soil-test sufficiency"
            ),
        ))
        flags.append(RiskFlag(
            message=(
                f"Alkaline pH but no time to acidify (gap {months:.1f} months, "
                f"sulphur needs 3-9). Lean on foliar Zn / Fe / Mn / B and "
                f"acidifying N sources (ammonium sulphate) this season."
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
    ca_mg_findings = [f for f in soil_factor_report.findings
                      if f.parameter == "Ca:Mg" and f.severity in ("warn", "critical")]
    if (sar_findings or ca_mg_findings) and months < DEFAULT_REACTION_PROFILES["gypsum"][0]:
        driver = "Sodicity" if sar_findings else "Low Ca:Mg ratio"
        items.append(OutstandingItem(
            item="Gypsum application — too late this season for full reaction",
            why_it_matters=(
                f"{driver} needs gypsum to correct. Gypsum requires ~0.5-2 months. "
                f"Build-to-plant gap is only {months:.1f} months — schedule for post-harvest."
            ),
            impact_if_skipped=(
                "Cation balance / Na issues persist; Ca-driven physiological "
                "disorders (BER, tip-burn) more likely on susceptible crops"
            ),
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
