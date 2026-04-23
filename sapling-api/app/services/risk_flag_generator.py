"""
Risk Flag Generator — Phase 2 reasoning module 4 of 10.

Translates structured findings (from SoilFactorReasoner + other reasoning
modules) + situational rules into typed RiskFlag narratives that go into
the ProgrammeArtifact.risk_flags[] for the renderer to surface in the
"Items to watch" section (Clivia §13 pattern).

Rules categorised:
  * Direct from SoilFactorReport (Al toxicity, SAR, EC, antagonisms,
    C:N) — already carry severity + message + recommended_action; this
    module just translates SoilFactorFinding → RiskFlag with provenance.
  * Programme-level rules — observed from the planned blends + pre-season
    inputs + crop choice. E.g. "no gypsum this season but Al active",
    "ammonium-sulphate-heavy plan + already-low pH", "Ca-Nitrate is
    workhorse — don't substitute urea".
  * Cultivar / data-completeness gaps — "leaf tissue analysis at wk 7
    would steer mid-season decisions", "irrigation water EC test required
    before first Part A injection".

Output goes into ProgrammeArtifact.risk_flags + a subset becomes
OutstandingItem entries (gaps that the agronomist can act on).
"""
from __future__ import annotations

from typing import Optional

from app.models import OutstandingItem, RiskFlag, SourceCitation, Tier
from app.services.soil_factor_reasoner import SoilFactorReport


def generate_risk_flags(
    soil_factor_report: SoilFactorReport,
    crop: Optional[str] = None,
    planned_n_fertilizers: Optional[list[str]] = None,
    has_gypsum_in_plan: bool = False,
    has_irrigation_water_test: bool = False,
    uses_fertigation: bool = False,
) -> list[RiskFlag]:
    """Translate findings + programme context into RiskFlag list.

    Args:
        soil_factor_report: from soil_factor_reasoner.reason_soil_factors()
        crop: canonical crop name (for crop-specific rules)
        planned_n_fertilizers: list of N fertilizer types in the plan
                               (e.g. ['ammonium_sulphate', 'urea'])
        has_gypsum_in_plan: whether gypsum is in the basal/pre-season plan
        has_irrigation_water_test: whether the agronomist has a recent
                                   irrigation-water EC/Ca/HCO3 test
        uses_fertigation: whether the programme uses any liquid drip path

    Returns:
        list of RiskFlag objects. Empty if nothing fires.
    """
    flags: list[RiskFlag] = []

    # ----- Translate every SoilFactorFinding into a RiskFlag -----
    for finding in soil_factor_report.findings:
        message = finding.message
        if finding.recommended_action:
            message = f"{message} — Action: {finding.recommended_action}"
        flags.append(RiskFlag(
            message=message,
            severity=finding.severity,
            source=SourceCitation(
                source_id=finding.source_id,
                section=finding.source_section,
                tier=Tier(finding.tier),
            ),
        ))

    # ----- Programme-level rule: Al active but no gypsum -----
    al_findings = [f for f in soil_factor_report.findings
                   if f.parameter == "Al_saturation_pct" and f.severity in ("warn", "critical")]
    if al_findings and not has_gypsum_in_plan:
        flags.append(RiskFlag(
            message=(
                "Al saturation is active but no gypsum in the pre-season plan — "
                "exchangeable Al stays in solution through early season. "
                "Slower early growth expected. Don't over-irrigate trying to "
                "compensate; the constraint is chemical, not water-related."
            ),
            severity="warn",
            source=SourceCitation(
                source_id="IMPLEMENTER_CONVENTION",
                section="Standard SA acid-soil management",
                tier=Tier.IMPLEMENTER_CONVENTION,
            ),
        ))

    # ----- Programme-level rule: ammonium-sulphate-heavy + low pH -----
    if planned_n_fertilizers:
        ams_present = any("ammonium_sulphate" in f.lower() or "ams" in f.lower()
                          for f in planned_n_fertilizers)
        ph_low = any(f.parameter in ("pH_H2O", "pH_KCl")
                     and (f.value or 99) < 5.5
                     for f in soil_factor_report.findings)
        if ams_present and (ph_low or al_findings):
            flags.append(RiskFlag(
                message=(
                    "Plan includes Ammonium Sulphate on an already-acid soil. "
                    "AmS is the most acidifying common N source (3 kg CaO per kg N "
                    "to neutralise, IFA Table 1). Lift the lime budget proportionally "
                    "or substitute Calcium Ammonium Nitrate (0.6 kg CaO per kg N)."
                ),
                severity="warn",
                source=SourceCitation(
                    source_id="IFA_WFM_1992",
                    section="World Fertilizer Use Manual Table 1",
                    tier=Tier.INTERNATIONAL_EXT,
                ),
            ))

    # ----- Programme-level rule: Ca-Nitrate as Al antagonist -----
    if al_findings and uses_fertigation:
        # If Al is critical and we're fertigating, advise against substituting Ca-Nit
        critical_al = any(f.severity == "critical" for f in al_findings)
        if critical_al:
            flags.append(RiskFlag(
                message=(
                    "Calcium Nitrate is the Al-antagonism workhorse for this soil. "
                    "Do not substitute with urea or UAN without recalculating — "
                    "you lose both the Ca contribution to base saturation AND "
                    "the avoidance of further acidification."
                ),
                severity="watch",
                source=SourceCitation(
                    source_id="IMPLEMENTER_CONVENTION",
                    section="Acid-soil fertigation practice",
                    tier=Tier.IMPLEMENTER_CONVENTION,
                ),
            ))

    return flags


def generate_outstanding_items(
    soil_factor_report: SoilFactorReport,
    crop: Optional[str] = None,
    has_irrigation_water_test: bool = False,
    has_recent_leaf_analysis: bool = False,
    uses_fertigation: bool = False,
    season_weeks: Optional[int] = None,
) -> list[OutstandingItem]:
    """Surface action items for the agronomist — missing data, follow-ups.

    Mirrors the Clivia §14.2 pattern.
    """
    items: list[OutstandingItem] = []

    # Irrigation water test if fertigation planned
    if uses_fertigation and not has_irrigation_water_test:
        items.append(OutstandingItem(
            item="Irrigation water test (EC, pH, Ca, Mg, Na, HCO₃, Cl)",
            why_it_matters=(
                "Required before first Part A (Calcium Nitrate) injection. "
                "Dolomite-country water can produce scale when Ca-Nitrate is "
                "injected. Borehole water EC + bicarb level affect drip-line pH."
            ),
            impact_if_skipped="Risk of emitter blockage from CaCO₃ precipitate",
        ))

    # Leaf analysis at decision points
    if not has_recent_leaf_analysis and season_weeks and season_weeks > 16:
        items.append(OutstandingItem(
            item="Mid-season leaf tissue analysis at tillering and at bulb-init/flowering",
            why_it_matters=(
                "Two natural decision points where the programme can still be "
                "steered. Catches deficiencies the soil test missed and validates "
                "actual uptake against plan."
            ),
            impact_if_skipped="Mid-season corrections become reactive, not anticipatory",
        ))

    # Post-harvest soil test if Al was active (need to size next-season lime)
    al_critical = any(f.parameter == "Al_saturation_pct" and f.severity == "critical"
                      for f in soil_factor_report.findings)
    if al_critical:
        items.append(OutstandingItem(
            item="Post-harvest soil test to size next-season basal lime application",
            why_it_matters=(
                "Al saturation was critical this season — track residual after "
                "lime + N reactions. Drives the next pre-plant lime budget."
            ),
            impact_if_skipped="Lime under-applied → Al active in subsequent seasons",
        ))

    return items
