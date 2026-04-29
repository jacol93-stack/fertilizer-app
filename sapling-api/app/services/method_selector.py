"""
Method Selector — Phase 2 reasoning module 6 of 10.

For each (stage, nutrient) pair in a split season target, decides which
application method delivers it, constrained by:
  * farmer's MethodAvailability (what equipment exists on the farm)
  * nutrient root-uptake efficiency (K mostly root; P mostly root-or-basal;
    micros often need foliar when soil availability is low)
  * soil-factor findings (P:Zn lockup pushes Zn to foliar; high-Al pushes
    N source to Ca-Nitrate)
  * stage (pre-plant basal vs in-season drip vs mid-season foliar)
  * crop family (tree-crops handle foliar at flowering differently
    than annuals)

Output: list of MethodAssignment dicts covering the full (stage × nutrient)
matrix with a dispatch plan the consolidator + blender modules consume.

Design principles:
  * DO NOT duplicate dose across methods (method-selector picks ONE primary
    method per nutrient per stage; complementarity module handles
    split-dose cases separately)
  * Foliar quantities stay agronomic (≤ label rates per-event); the Stage
    Splitter's kg/ha can be larger than a single foliar dose can deliver —
    method selector caps foliar contribution and routes the remainder
    to root uptake.
  * Always provide a reason so the orchestrator's audit trail is complete.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.models import MethodAvailability, MethodKind
from app.services.soil_factor_reasoner import SoilFactorReport
from app.services.stage_splitter import StageSplit


# ============================================================
# Foliar single-event capacity caps (kg/ha per single spray)
# ============================================================
# Not phytotoxicity (those belong on the product label). These are
# practical single-spray delivery limits — foliar can't realistically
# deliver 30 kg K/ha in one pass; it's a correction tool, not a bulk
# delivery mechanism for macros.
FOLIAR_SINGLE_EVENT_CAP_KG_HA: dict[str, float] = {
    "N":     5.0,   # foliar urea limited; biuret caveat
    "P2O5":  3.0,   # rarely foliar; leaf scorch risk
    "P":     1.5,
    "K2O":   3.0,   # emergency correction only
    "K":     2.5,
    "Ca":    1.0,   # quality-window only (bitter pit)
    "Mg":    1.5,   # Epsom-salt spray standard
    "S":     2.0,
    "Zn":    1.0,
    "B":     0.4,   # Solubor 1.5 kg/ha × 20.5% = 0.3 kg B
    "Mn":    0.4,
    "Fe":    0.3,
    "Cu":    0.15,
    "Mo":    0.05,
}


# ============================================================
# Output type
# ============================================================

@dataclass
class MethodAssignment:
    """One routed delivery: a (stage × nutrient × method × amount) row."""
    stage_number: int
    stage_name: str
    nutrient: str
    method: MethodKind
    kg_per_ha: float
    reason: str  # why this method was chosen
    tier: int = 6  # confidence in the routing rule (Tier 6 by default)


# ============================================================
# Selector
# ============================================================

def select_methods(
    stage_splits: list[StageSplit],
    method_availability: MethodAvailability,
    soil_factor_report: Optional[SoilFactorReport] = None,
    crop_family: Optional[str] = None,
) -> list[MethodAssignment]:
    """Route every (stage, nutrient) kg/ha to a method.

    Args:
        stage_splits: from stage_splitter.split_season_targets()
        method_availability: what the farmer has (drip, foliar, granular, etc.)
        soil_factor_report: for lockup-based redirects (P:Zn → foliar Zn)
        crop_family: tree-crops handle budbreak foliar differently

    Returns:
        list of MethodAssignment, one or more per (stage, nutrient).
        Split assignments possible when one method can't deliver full dose
        (e.g. B stage-demand 1 kg/ha but foliar cap is 0.4 → 0.4 foliar +
        0.6 to soil if available).
    """
    avail = method_availability.available_kinds()
    # Per-finding redirects — pre-compute which nutrients should prefer foliar
    foliar_priority_nutrients = _foliar_priority_from_findings(soil_factor_report)
    total_stages = len(stage_splits)

    assignments: list[MethodAssignment] = []

    for split in stage_splits:
        for nutrient, amount in split.nutrients.items():
            if amount <= 0:
                continue
            routed = _route_nutrient(
                nutrient=nutrient, amount=amount,
                stage_number=split.stage_number,
                stage_name=split.stage_name,
                total_stages=total_stages,
                avail=avail,
                foliar_priority=nutrient in foliar_priority_nutrients,
                crop_family=crop_family,
            )
            assignments.extend(routed)

    return assignments


# ============================================================
# Routing rules
# ============================================================

def _route_nutrient(
    nutrient: str,
    amount: float,
    stage_number: int,
    stage_name: str,
    total_stages: int,
    avail: set[MethodKind],
    foliar_priority: bool,
    crop_family: Optional[str],
) -> list[MethodAssignment]:
    """Decide method(s) for ONE (stage, nutrient, amount).

    Routing policy is keyed on **stage role**, not stage_name strings,
    so the same rule applies across crops (perennial trees, vines,
    annuals, vegetables, sugarcane). The roles:

      * **Basal** (stage_number == 1) — pre-plant / pre-flush /
        post-harvest compound. Heavy, slow-moving nutrients (P, K, Ca,
        Mg, S) go to dry broadcast for soil reaction time and Al
        protection; N goes to liquid when available so it's split-
        applied across the actual demand stages, otherwise a dry
        broadcast fallback gets it down before peak demand.
      * **In-season** (middle stages) — N + K + Mg + S go to liquid
        when available (efficient root uptake + demand-matched
        timing); fall back to dry side-dress, then foliar (capped).
      * **Maturation** (stage_number == total_stages) — same routing
        as in-season but the stage_splitter already allocates small
        amounts here, so the engine naturally tapers off.

    Micros (Zn / B / Mn / Fe / Cu / Mo) and soil-availability-gap
    redirects (P:Zn → foliar Zn) sit on top of this and route to
    foliar first regardless of stage role.

    Stage-role keying replaces the previous stage_name-string match
    (`("establishment", "pre-plant", "planting")`) which silently
    missed every crop whose stages had crop-specific names — that bug
    routed all of Anton's macadamia through fertigation because his
    Stage-1 was named "Post-harvest + flower initiation".
    """
    is_basal = stage_number == 1
    is_maturation = (total_stages > 1 and stage_number == total_stages)
    # is_in_season is everything that isn't basal or maturation; we
    # don't need to compute it explicitly because we route by has_dry
    # / has_liquid preference for non-basal stages.
    has_liquid = (MethodKind.LIQUID_DRIP in avail or
                  MethodKind.LIQUID_PIVOT in avail or
                  MethodKind.LIQUID_SPRINKLER in avail)
    has_foliar = MethodKind.FOLIAR in avail
    has_dry = MethodKind.DRY_BROADCAST in avail

    nutrient_base = nutrient.replace("2O5", "").replace("2O", "")  # P2O5→P, K2O→K

    # ----- Priority redirect: soil-availability gap → foliar first -----
    if foliar_priority and has_foliar:
        cap = FOLIAR_SINGLE_EVENT_CAP_KG_HA.get(nutrient,
              FOLIAR_SINGLE_EVENT_CAP_KG_HA.get(nutrient_base, 1.0))
        foliar_portion = min(amount, cap)
        rem = amount - foliar_portion
        out = [MethodAssignment(
            stage_number=stage_number, stage_name=stage_name,
            nutrient=nutrient, method=MethodKind.FOLIAR,
            kg_per_ha=round(foliar_portion, 3),
            reason=f"Soil availability gap detected — bypass root uptake for {nutrient}",
            tier=3,
        )]
        if rem > 0.001:
            # Route remainder to soil path (drip preferred, else dry)
            soil_method = (MethodKind.LIQUID_DRIP if has_liquid else
                           (MethodKind.DRY_BROADCAST if has_dry else MethodKind.FOLIAR))
            out.append(MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=soil_method,
                kg_per_ha=round(rem, 3),
                reason=f"Remainder after foliar cap of {cap} kg/ha",
                tier=6,
            ))
        return out

    # ----- Basal stage: heavy slow-moving nutrients go dry -----
    # P, K, Ca, Mg, S all benefit from being positioned in the soil
    # before peak demand. Dry broadcast is the standard SA basal
    # delivery; band placement (DRY_BAND) is preferred for annuals
    # close to seed but DRY_BROADCAST is the universal fallback.
    if is_basal and nutrient_base in ("P", "K", "Ca", "Mg", "S"):
        if has_dry:
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=MethodKind.DRY_BROADCAST,
                kg_per_ha=round(amount, 2),
                reason=(
                    f"Basal {nutrient} — dry broadcast positions the nutrient "
                    f"before peak demand. Slow soil mobility (P) / cation "
                    f"exchange dynamics (K, Ca, Mg) reward early placement."
                ),
                tier=2,
            )]
        if has_liquid:
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=MethodKind.LIQUID_DRIP,
                kg_per_ha=round(amount, 2),
                reason=(
                    f"Basal {nutrient} — no dry spreader available, routing "
                    f"via drip as fallback. Less ideal for slow-moving "
                    f"nutrients; agronomic outcome may be reduced."
                ),
                tier=6,
            )]
        # Last resort handled at end of function.

    # ----- Basal N: liquid preferred (split application), dry fallback -----
    # N at basal stage is different from P/K — it leaches and shouldn't
    # be front-loaded. Drip lets it be split across demand. If no
    # liquid available, broadcast is acceptable but a dry side-dress
    # closer to demand peak would be better; we use broadcast for the
    # consistency it gives the agronomist (one pass at planting / pre-
    # flush) and let timing walls do their job.
    if is_basal and nutrient_base == "N":
        if has_liquid:
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=MethodKind.LIQUID_DRIP,
                kg_per_ha=round(amount, 2),
                reason=(
                    "Basal N — drip routing splits the dose across the "
                    "actual demand stages instead of front-loading; "
                    "reduces leaching loss."
                ),
                tier=2,
            )]
        if has_dry:
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=MethodKind.DRY_BROADCAST,
                kg_per_ha=round(amount, 2),
                reason=(
                    "Basal N — no fertigation available, dry broadcast "
                    "with the basal pass. Timing walls enforce no-N "
                    "stages downstream."
                ),
                tier=3,
            )]

    # ----- In-season + maturation: liquid preferred, dry fallback ------
    # Every macro routes here for non-basal stages. Drip wins when
    # available because it matches root uptake to demand. Dry side-
    # dress is the next-best option (placed near the active root zone).
    # Foliar last (capped, used as a delivery mechanism only when the
    # other two are absent).
    if nutrient_base in ("N", "P", "K", "Ca", "Mg", "S"):
        if has_liquid:
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=MethodKind.LIQUID_DRIP,
                kg_per_ha=round(amount, 2),
                reason=(
                    f"In-season {nutrient} via drip — efficient root "
                    f"uptake + demand-matched timing."
                ),
                tier=3,
            )]
        if has_dry:
            method = (MethodKind.DRY_BROADCAST if is_maturation
                      else MethodKind.DRY_SIDE_DRESS)
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=method,
                kg_per_ha=round(amount, 2),
                reason=(
                    f"Dry {method.value.replace('_', ' ')} — no fertigation "
                    f"available, in-season delivery via spreader."
                ),
                tier=3,
            )]
        if has_foliar:
            cap = FOLIAR_SINGLE_EVENT_CAP_KG_HA.get(nutrient,
                  FOLIAR_SINGLE_EVENT_CAP_KG_HA.get(nutrient_base, 1.0))
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=MethodKind.FOLIAR,
                kg_per_ha=round(min(amount, cap), 3),
                reason=f"No soil/drip available — foliar only (capped at {cap} kg/ha)",
                tier=6,
            )]

    # ----- Micros: foliar preferred for precision, drip if available -----
    if nutrient_base in ("Zn", "B", "Mn", "Fe", "Cu", "Mo"):
        if has_foliar:
            cap = FOLIAR_SINGLE_EVENT_CAP_KG_HA.get(nutrient_base, 0.5)
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=MethodKind.FOLIAR,
                kg_per_ha=round(min(amount, cap), 3),
                reason=f"Foliar micro — precise delivery at demand peak",
                tier=2,
            )]
        if has_liquid:
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=MethodKind.LIQUID_DRIP,
                kg_per_ha=round(amount, 3),
                reason="Micro via drip (chelated form recommended)",
                tier=3,
            )]
        if has_dry:
            return [MethodAssignment(
                stage_number=stage_number, stage_name=stage_name,
                nutrient=nutrient, method=MethodKind.DRY_BROADCAST,
                kg_per_ha=round(amount, 3),
                reason="Micro via blended dry — less precise, early-season preferred",
                tier=3,
            )]

    # ----- Last resort: if nothing available, document the gap -----
    return [MethodAssignment(
        stage_number=stage_number, stage_name=stage_name,
        nutrient=nutrient, method=MethodKind.DRY_BROADCAST,  # placeholder
        kg_per_ha=round(amount, 2),
        reason=(f"No available method — assigned to dry_broadcast as placeholder; "
                f"UI should surface this as an outstanding method-capability gap"),
        tier=6,
    )]


# ============================================================
# Helpers
# ============================================================

def _foliar_priority_from_findings(
    report: Optional[SoilFactorReport]
) -> set[str]:
    """From soil-factor findings, which nutrients should be prioritised to foliar."""
    if not report:
        return set()
    priority: set[str] = set()
    for finding in report.findings:
        if finding.trigger_kind != "soil_availability_gap":
            continue
        # Map finding parameter to target nutrient
        target = {
            "P:Zn": "Zn",
            "Ca:B": "B",
            "Fe:Mn": "Mn",
            "Cu:Mo": "Mo",
        }.get(finding.parameter)
        if target:
            priority.add(target)
    return priority


def aggregate_by_method(
    assignments: list[MethodAssignment]
) -> dict[tuple[int, MethodKind], dict[str, float]]:
    """Aggregate assignments by (stage, method) for downstream consolidator.

    Returns:
        {(stage_num, method_kind): {nutrient: kg/ha}}
    """
    agg: dict[tuple[int, MethodKind], dict[str, float]] = {}
    for a in assignments:
        key = (a.stage_number, a.method)
        if key not in agg:
            agg[key] = {}
        agg[key][a.nutrient] = agg[key].get(a.nutrient, 0) + a.kg_per_ha
    return agg
