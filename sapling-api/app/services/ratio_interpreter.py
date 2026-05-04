"""Smart ratio-by-ratio interpretation engine.

Given a block's soil_values + computed_ratios, produces a list of
`RatioInterpretation` entries — one per agronomically-meaningful ratio
or saturation parameter — explaining:
  * the current value vs the ideal band
  * the direct effect (what does this state cause?)
  * which nutrients become bound / unavailable as a result
  * a recommended action (qualitative — no specific products, since
    blend prescription has moved to the product selector layer)

Plus a holistic summary that collapses all interpretations into a 2-3
sentence narrative + nutrients-at-risk list.

Sources (T1 SA-canonical):
  * FERTASA Handbook 5.2.2 (cation balance principles)
  * Manson & Sheard 2007 KZN (Ca:Mg 2.5-5.4 band)
  * Conradie 1986/2022 SAJEV (cation balance + grape-specific overrides)
  * IPNI 4R Better Crops cation interactions
  * Du Plessis & Koen 1992 SAJPS (avocado leaf K minimum)

Design rule: every interpretation row must be deterministic — no calls
out to LLMs or external services. Used by both the programme builder
and the soil-report renderer; both surfaces produce identical text for
the same input.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RatioInterpretation:
    """One row in the per-block ratio-by-ratio interpretation table.

    Designed to render as a self-contained 'card' in both the programme
    artifact and the soil report — caller doesn't need to compose
    additional prose.
    """
    name: str  # "Ca:Mg", "Mg:K", "K base sat.", "Acid saturation", etc.
    value: Optional[float]
    ideal_low: Optional[float]
    ideal_high: Optional[float]
    unit: str  # "ratio", "%"
    state: str  # 'unknown' | 'low' | 'in_range' | 'high'
    severity: str  # 'info' | 'watch' | 'warn' | 'critical'

    what_it_measures: str
    """One sentence of plain-English context about what the ratio captures."""

    direct_effect: str
    """What is happening agronomically given the current value."""

    bound_nutrients: list[str] = field(default_factory=list)
    """Which nutrients lose availability under this state. e.g. ['K', 'Mg']
    when Ca:Mg is too high."""

    recommended_action: Optional[str] = None
    """Qualitative action — no product names. e.g. 'Apply gypsum to raise
    Ca without lifting pH; foliar Mg at flowering to bridge leaf demand'."""

    source_citation: Optional[str] = None


@dataclass
class RatioHolisticSummary:
    """Collapses all ratio interpretations into a single agronomic summary.

    Designed for the renderer's 'Cation Balance — Summary' block. The
    summary should explicitly name the nutrients-at-risk so the next
    section (per-stage targets) makes sense to a reader who skipped
    the table.
    """
    summary: str
    """2-3 sentence agronomic narrative."""

    key_concerns: list[str] = field(default_factory=list)
    """Top 1-3 ratio-driven concerns by severity."""

    nutrients_at_risk: list[str] = field(default_factory=list)
    """Nutrients likely under-available given the cumulative ratio profile.
    Drives the renderer's 'consider foliar X' badges and feeds the
    product selector's filter for 'must include foliar X' constraints."""


# ── Ratio rule definitions ─────────────────────────────────────────


@dataclass(frozen=True)
class RatioRule:
    """Reference data + interpretation templates for one ratio.

    Templates use `{value}`, `{low}`, `{high}` placeholders that are
    f-string substituted at render time. Sources are tier-tagged.
    """
    name: str
    unit: str  # "ratio" or "%"
    ideal_low: float
    ideal_high: float
    what_it_measures: str
    source: str  # "FERTASA 5.2.2", "Manson & Sheard 2007 KZN", etc.

    # State templates — populated at interpretation time
    low_effect: str
    low_bound: list[str]  # nutrients bound when ratio is below band
    low_action: str
    low_severity: str  # 'watch' | 'warn' | 'critical'

    high_effect: str
    high_bound: list[str]
    high_action: str
    high_severity: str

    in_range_effect: str = "Within the published band — no ratio-driven antagonism expected for this pair."


# Rule set — keys are the canonical ratio/saturation parameter names
# matching what `soil_factor_reasoner` writes to `report.computed`
# and what the lab reports verbatim.
RATIO_RULES: dict[str, RatioRule] = {
    "Ca:Mg": RatioRule(
        name="Ca:Mg",
        unit="ratio",
        ideal_low=3.0,
        ideal_high=7.0,
        what_it_measures="Balance between calcium and magnesium on the exchange complex.",
        source="FERTASA 5.2.2 + Manson & Sheard 2007 KZN Table 8",
        low_effect=(
            "Ca is under-represented relative to Mg. Magnesium dominance in this state "
            "drives potassium (K) antagonism — leaf K runs low even when soil-test K reads "
            "sufficient — and Ca uptake into fruit/cell walls is restricted, raising the "
            "risk of Ca-quality disorders (bitter pit, blossom-end rot, tip burn)."
        ),
        low_bound=["Ca", "K"],
        low_action=(
            "Apply gypsum (CaSO4) to raise Ca without lifting pH. Avoid dolomitic lime "
            "until Ca:Mg is corrected. Consider foliar Ca during fruit-quality stages."
        ),
        low_severity="warn",
        high_effect=(
            "Ca is dominant relative to Mg, common on over-limed or naturally calcareous "
            "soils. Magnesium becomes functionally deficient in the leaf despite adequate "
            "soil-test Mg — Mg gets locked into the soil exchange and outcompeted for "
            "uptake. Look for interveinal chlorosis on older leaves."
        ),
        high_bound=["Mg"],
        high_action=(
            "Apply Mg-bearing materials at planting (Epsom salt or kieserite) and side-"
            "dress through the season. Avoid further Ca application until ratio recovers."
        ),
        high_severity="warn",
    ),

    "Mg:K": RatioRule(
        name="Mg:K",
        unit="ratio",
        ideal_low=2.0,
        ideal_high=4.0,
        what_it_measures="Balance between magnesium and potassium on the exchange complex.",
        source="FERTASA 5.2.2",
        low_effect=(
            "K is in excess relative to Mg — luxury K consumption is locking Mg out of "
            "the leaf. Symptoms: interveinal chlorosis on older leaves, especially during "
            "fruit fill. Even adequate soil-Mg won't reach the leaf at this ratio."
        ),
        low_bound=["Mg"],
        low_action=(
            "Reduce K input until Mg comes back into balance. Foliar Mg at flowering "
            "and fruit set to bridge leaf demand."
        ),
        low_severity="warn",
        high_effect=(
            "Mg is in excess relative to K — Mg dominance is restricting K uptake. Leaf "
            "K runs low despite optimal soil-test K. Symptoms: leaf-margin scorch, weak "
            "fruit colour, low brix."
        ),
        high_bound=["K"],
        high_action=(
            "Increase K supply during fruit-fill stage. Foliar K (KNO3 or K-sulphate) at "
            "veraison / fruit fill bypasses soil-Mg lockup."
        ),
        high_severity="warn",
    ),

    "Ca:K": RatioRule(
        name="Ca:K",
        unit="ratio",
        ideal_low=10.0,
        ideal_high=20.0,
        what_it_measures="Balance between calcium and potassium on the exchange complex.",
        source="FERTASA 5.2.2",
        low_effect=(
            "K dominant relative to Ca — luxury K consumption restricts Ca uptake. "
            "Bitter pit / blossom-end rot risk rises sharply on apples, tomatoes, peppers."
        ),
        low_bound=["Ca"],
        low_action="Reduce K, prioritise Ca foliars at fruit-quality stages.",
        low_severity="watch",
        high_effect=(
            "Ca dominant relative to K — K is locked by Ca on the exchange. Leaf K runs "
            "low even with adequate soil-K. Common on over-limed or calcareous soils."
        ),
        high_bound=["K"],
        high_action="Foliar K at fruit fill; avoid further liming until ratio recovers.",
        high_severity="warn",
    ),

    "(Ca+Mg):K": RatioRule(
        name="(Ca+Mg):K",
        unit="ratio",
        ideal_low=15.0,
        ideal_high=30.0,
        what_it_measures="Combined cation pressure on K availability — composite of Ca:K and Mg:K.",
        source="FERTASA 5.2.2",
        low_effect=(
            "Both Ca and Mg are under-represented relative to K. Soil is "
            "K-luxury — uptake of Ca and Mg into vegetation will be restricted, "
            "fruit-quality issues likely."
        ),
        low_bound=["Ca", "Mg"],
        low_action="Apply Ca + Mg sources (dolomitic lime, gypsum-MgO blend); reduce K.",
        low_severity="warn",
        high_effect=(
            "Combined Ca + Mg pressure is excessive — K uptake into the plant will be "
            "restricted regardless of soil-test K. Leaf K low; fruit colour, brix, "
            "and shelf-life all suffer."
        ),
        high_bound=["K"],
        high_action="Increase K supply; foliar K at peak fruit-fill stages.",
        high_severity="warn",
    ),

    "K:Na": RatioRule(
        name="K:Na",
        unit="ratio",
        ideal_low=5.0,
        ideal_high=999.0,  # No upper limit; higher K:Na is always safer
        what_it_measures="Plant's ability to discriminate K from Na on the root surface. Lower ratios indicate sodic stress.",
        source="FERTASA 5.2.2 + Maas & Hoffman 1977 ASCE salinity guide",
        low_effect=(
            "Na is competing with K for uptake — sodic stress. Plants substitute Na "
            "for K in the leaf, weakening cell-wall integrity, fruit quality, and "
            "drought tolerance. On Cl-sensitive crops (avocado, kiwi) this is a "
            "compound risk."
        ),
        low_bound=["K"],
        low_action=(
            "Apply gypsum to displace Na from the exchange. Maintain high K supply via "
            "fertigation. Verify irrigation water EC + Na content."
        ),
        low_severity="warn",
        high_effect=(
            "K is well in excess of Na — no sodic-stress concern from this ratio."
        ),
        high_bound=[],
        high_action="No action required.",
        high_severity="info",
    ),

    "P:Zn": RatioRule(
        name="P:Zn",
        unit="ratio",
        ideal_low=0.0,  # No lower concern
        ideal_high=150.0,  # Above this, P locks Zn
        what_it_measures="High soil P can lock Zn — measured in mg/kg basis.",
        source="IPNI 4R Better Crops + FERTASA 5.4.4 maize chapter",
        low_effect="No P-induced Zn lockup at this ratio.",
        low_bound=[],
        low_action="No action.",
        low_severity="info",
        high_effect=(
            "Soil P is high enough to suppress Zn availability — Zn uptake will be "
            "inadequate regardless of soil-test Zn level. Zn-sensitive crops (mac, "
            "pecan, maize) show interveinal chlorosis on young leaves."
        ),
        high_bound=["Zn"],
        high_action=(
            "Apply foliar Zn (ZnSO4 or Zn-EDTA) to bypass soil P lockup. Reduce P "
            "input until ratio recovers."
        ),
        high_severity="warn",
    ),

    # ── Saturation parameters (% of CEC) ───────────────────────────

    "Ca Saturation": RatioRule(
        name="Ca base saturation",
        unit="%",
        ideal_low=60.0,
        ideal_high=70.0,
        what_it_measures="Share of the cation exchange capacity occupied by Ca²⁺.",
        source="FERTASA 5.2.2",
        low_effect=(
            "Ca-deficient exchange — soil acidity dominant; Al toxicity risk on acid-"
            "sensitive crops. Cation balance skewed toward H+, Al, Mg, K."
        ),
        low_bound=["Ca"],
        low_action="Apply lime (CaCO3 or dolomitic) according to acid-saturation level.",
        low_severity="warn",
        high_effect=(
            "Ca-dominant exchange — Mg and K saturation will be suppressed. Common on "
            "over-limed or naturally calcareous soils. Expect Mg and K antagonism."
        ),
        high_bound=["Mg", "K"],
        high_action=(
            "Halt liming. Compensate with Mg + K applications and foliars during "
            "high-demand stages."
        ),
        high_severity="warn",
    ),

    "Mg Saturation": RatioRule(
        name="Mg base saturation",
        unit="%",
        ideal_low=12.0,
        ideal_high=18.0,
        what_it_measures="Share of the cation exchange capacity occupied by Mg²⁺.",
        source="FERTASA 5.2.2",
        low_effect=(
            "Mg saturation low — leaf Mg deficiency likely even when soil-test Mg "
            "reads sufficient. Older-leaf chlorosis at fruit fill is the canonical "
            "symptom."
        ),
        low_bound=["Mg"],
        low_action="Apply Epsom salt or kieserite; foliar Mg at flowering.",
        low_severity="warn",
        high_effect=(
            "Mg-dominant exchange — K antagonism is the primary effect. Even adequate "
            "soil-K will not translate to leaf K at this saturation."
        ),
        high_bound=["K"],
        high_action="Increase K supply; foliar K at fruit-fill stages.",
        high_severity="warn",
    ),

    "K Saturation": RatioRule(
        name="K base saturation",
        unit="%",
        ideal_low=3.0,
        ideal_high=5.0,
        what_it_measures="Share of the cation exchange capacity occupied by K⁺.",
        source="FERTASA 5.2.2",
        low_effect=(
            "K-deficient exchange — leaf K will run low and fruit quality (colour, "
            "brix, firmness) will suffer regardless of yield."
        ),
        low_bound=["K"],
        low_action="Build K supply via fertigation or fertilizer K applications.",
        low_severity="warn",
        high_effect=(
            "Luxury K consumption — K is dominant on the exchange and will antagonise "
            "Ca and Mg uptake. On wine grapes especially, excess K raises juice pH "
            "and damages wine quality."
        ),
        high_bound=["Ca", "Mg"],
        high_action=(
            "Reduce K applications until Ca:K and Mg:K return to band. Foliar Ca/Mg "
            "to bridge leaf demand."
        ),
        high_severity="watch",
    ),

    "Na Saturation": RatioRule(
        name="Na base saturation (ESP)",
        unit="%",
        ideal_low=0.0,
        ideal_high=3.0,
        what_it_measures=(
            "Exchangeable sodium percentage — fraction of CEC occupied by Na⁺. "
            "High ESP causes structure breakdown + dispersion."
        ),
        source="FERTASA 5.2.2 + Sumner & Naidu 1998 sodic-soil framework",
        low_effect="No sodic-stress concern at this ESP.",
        low_bound=[],
        low_action="No action required.",
        low_severity="info",
        high_effect=(
            "Sodic stress — soil structure dispersion, infiltration loss, Na competing "
            "with K for uptake. On Cl-sensitive crops (avocado, kiwi) sodic stress "
            "compounds with chloride toxicity. Fruit storage life and quality both "
            "suffer."
        ),
        high_bound=["K", "Ca"],
        high_action=(
            "Apply gypsum to displace Na from exchange. Verify irrigation water Na + Cl. "
            "Switch to K-sulphate if KCl is in use."
        ),
        high_severity="warn",
    ),

    "Acid Saturation": RatioRule(
        name="Acid saturation",
        unit="%",
        ideal_low=0.0,
        ideal_high=5.0,
        what_it_measures="Fraction of CEC occupied by acidic cations (H⁺, Al³⁺). Drives Al toxicity risk on acid-sensitive crops.",
        source="FERTASA 5.2.2 + 5.8.1 macadamia chapter",
        low_effect="No acid-related stress; Al is not present in toxic concentrations.",
        low_bound=[],
        low_action="No action.",
        low_severity="info",
        high_effect=(
            "Acid saturation high — Al is mobilised onto the exchange. Acid-sensitive "
            "crops (most fruit, vegetables, cereals) show root-tip damage, restricted "
            "P uptake, and Ca/Mg antagonism. Acid-tolerant crops (blueberry, pineapple, "
            "rooibos) are unaffected."
        ),
        high_bound=["P", "Ca", "Mg"],
        high_action=(
            "Apply lime according to acid-saturation level (calculated lime "
            "requirement). For sub-soil Al, use gypsum to leach Ca below the topsoil."
        ),
        high_severity="critical",
    ),
}


# ── Interpretation engine ──────────────────────────────────────────


def _classify_state(value: Optional[float], rule: RatioRule) -> str:
    """Map a numeric value to a state ('low' | 'in_range' | 'high' | 'unknown')."""
    if value is None:
        return "unknown"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if v < rule.ideal_low:
        return "low"
    if v > rule.ideal_high:
        return "high"
    return "in_range"


def interpret_ratio(name: str, value: Optional[float]) -> Optional[RatioInterpretation]:
    """Build a RatioInterpretation for one ratio + value, or None if no
    rule defined for that ratio name."""
    rule = RATIO_RULES.get(name)
    if rule is None:
        return None

    state = _classify_state(value, rule)

    if state == "low":
        effect = rule.low_effect
        bound = list(rule.low_bound)
        action = rule.low_action
        severity = rule.low_severity
    elif state == "high":
        effect = rule.high_effect
        bound = list(rule.high_bound)
        action = rule.high_action
        severity = rule.high_severity
    elif state == "in_range":
        effect = rule.in_range_effect
        bound = []
        action = None
        severity = "info"
    else:  # unknown
        effect = "Value not available — interpretation skipped."
        bound = []
        action = None
        severity = "info"

    return RatioInterpretation(
        name=rule.name,
        value=value if isinstance(value, (int, float)) else None,
        ideal_low=rule.ideal_low,
        ideal_high=rule.ideal_high,
        unit=rule.unit,
        state=state,
        severity=severity,
        what_it_measures=rule.what_it_measures,
        direct_effect=effect,
        bound_nutrients=bound,
        recommended_action=action,
        source_citation=rule.source,
    )


def interpret_all_ratios(
    soil_values: dict,
    computed_ratios: Optional[dict] = None,
) -> list[RatioInterpretation]:
    """Produce one RatioInterpretation per agronomically-relevant ratio.

    Looks up the value from `computed_ratios` first (orchestrator's
    canonical computed dict), then falls back to `soil_values` (lab
    direct readings of saturations + sometimes ratios).

    Skips ratios where neither source has a value — output is variable-
    length depending on what the lab reported and what the reasoner
    computed.
    """
    computed_ratios = computed_ratios or {}
    interpretations: list[RatioInterpretation] = []

    for ratio_name in RATIO_RULES:
        # Prefer reasoner-computed value; lab-reported overrides nothing
        # because the canonicaliser already aliased lab keys upstream.
        value: Optional[float] = computed_ratios.get(ratio_name)
        if value is None:
            value = soil_values.get(ratio_name)
        if value is None:
            # Try lab key variants for saturations
            if ratio_name == "Ca Saturation":
                value = soil_values.get("Ca Saturation") or soil_values.get("Ca%")
            elif ratio_name == "Mg Saturation":
                value = soil_values.get("Mg Saturation") or soil_values.get("Mg%")
            elif ratio_name == "K Saturation":
                value = soil_values.get("K Saturation") or soil_values.get("K%")
            elif ratio_name == "Na Saturation":
                value = soil_values.get("Na Saturation") or soil_values.get("Na%")
            elif ratio_name == "Acid Saturation":
                value = soil_values.get("Acid Saturation")

        interp = interpret_ratio(ratio_name, value)
        if interp is None:
            continue
        # Only surface in-band entries that have a value — skip "unknown"
        # ones to keep the table tight (caller can still iterate the full
        # rule set if a verbose view is wanted).
        if interp.state == "unknown":
            continue
        interpretations.append(interp)

    return interpretations


def summarise_ratios(interpretations: list[RatioInterpretation]) -> RatioHolisticSummary:
    """Collapse all ratio interpretations into a 2-3 sentence summary +
    nutrients-at-risk list.

    Logic:
      * Collect every nutrient flagged as 'bound' across all out-of-band
        ratios — the union becomes 'nutrients_at_risk'
      * Pick the top 1-3 concerns by severity (critical > warn > watch)
      * Compose the summary from the patterns observed
    """
    if not interpretations:
        return RatioHolisticSummary(
            summary="No ratio data available for this block.",
            key_concerns=[],
            nutrients_at_risk=[],
        )

    # Severity rank
    severity_rank = {"critical": 4, "warn": 3, "watch": 2, "info": 1}

    out_of_band = [i for i in interpretations if i.state in ("low", "high")]
    nutrients_at_risk: list[str] = []
    seen = set()
    for interp in sorted(out_of_band, key=lambda i: -severity_rank.get(i.severity, 0)):
        for nut in interp.bound_nutrients:
            if nut not in seen:
                nutrients_at_risk.append(nut)
                seen.add(nut)

    # Top 3 concerns by severity
    key_concerns = [
        f"{i.name} {i.value:g}{(' ' + i.unit) if i.unit != 'ratio' else ''} "
        f"({i.state.replace('_', ' ')})"
        for i in sorted(out_of_band, key=lambda i: -severity_rank.get(i.severity, 0))[:3]
    ]

    # Compose narrative
    if not out_of_band:
        summary = (
            "All measured cation ratios are within their published bands. "
            "No ratio-driven antagonism or bound-nutrient concerns expected; "
            "absolute soil-test values can be read at face value."
        )
    elif len(out_of_band) == 1:
        i = out_of_band[0]
        risks = ", ".join(nutrients_at_risk) if nutrients_at_risk else "none"
        summary = (
            f"One ratio is outside its published band — {i.name} at {i.value:g} "
            f"({i.state.replace('_', ' ')}). Likely under-available nutrients given "
            f"this pattern: {risks}. The per-stage targets below take this into "
            f"account where the engine has cited corrections."
        )
    else:
        risks = ", ".join(nutrients_at_risk) if nutrients_at_risk else "none"
        n_warn_or_worse = sum(1 for i in out_of_band if severity_rank.get(i.severity, 0) >= 3)
        summary = (
            f"{len(out_of_band)} ratios are outside their published bands "
            f"({n_warn_or_worse} flagged warn/critical). Cumulative effect is that "
            f"the following nutrients will be functionally less available than "
            f"their soil-test values suggest: {risks}. The per-stage nutrient targets "
            f"below assume soil-test face values; consider foliar supplementation for "
            f"the bound nutrients during peak-demand stages."
        )

    return RatioHolisticSummary(
        summary=summary,
        key_concerns=key_concerns,
        nutrients_at_risk=nutrients_at_risk,
    )
