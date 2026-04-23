"""
Foliar Trigger Engine — Phase 2 reasoning module 3 of 10.

Foliar is CONTINGENT — only fires when at least one of four trigger
conditions is positively true:

    1. soil_availability_gap — soil micro is locked up by pH, Al, P, Ca,
       or otherwise unavailable to roots even though soil-test reads ok
       (consumed from SoilFactorReport.findings where trigger_kind set)

    2. stage_peak_demand — a critical crop stage has nutrient demand
       higher than fertigation/basal can deliver in time (e.g. B at
       bulb initiation for alliums; Ca during rapid fruit enlargement)

    3. quality_window — quality-critical timing where leaf application
       outperforms root uptake (e.g. Ca for bitter-pit, B for pollen
       viability + fruit set)

    4. leaf_correction — mid-season leaf analysis showed a deficiency
       that needs immediate correction (Season Tracker re-entry path)

If no trigger fires → no foliar events in the artifact. Honest, not
filler.

Outputs typed FoliarEvent objects (from app.models.programme_artifact)
that the orchestrator embeds in the ProgrammeArtifact.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from app.models import FoliarEvent, SourceCitation, Tier
from app.services.soil_factor_reasoner import SoilFactorReport


# ============================================================
# Trigger 2 — stage-peak crop rules
# ============================================================
# Per-crop, per-stage, micros where stage-peak demand justifies foliar
# regardless of soil status. Sourced where possible; Tier-6 implementer
# convention where literature only gives qualitative guidance.

@dataclass(frozen=True)
class StagePeakRule:
    crop: str
    nutrient: str
    week_offset_from_planting: int
    stage_label: str
    rate_per_ha: str
    product: str
    analysis: str
    reason: str
    source_id: str
    source_section: str
    tier: int


STAGE_PEAK_RULES: list[StagePeakRule] = [
    # Garlic — bulb crop. Standard SA timing per Clivia reference workflow
    # (FERTASA 5.6.1 + international garlic agronomy assumptions, Tier 6).
    StagePeakRule(
        crop="Garlic", nutrient="B",
        week_offset_from_planting=16, stage_label="Bulb Initiation",
        rate_per_ha="1.5 kg",
        product="Solubor", analysis="20.5% B",
        reason="Bulb initiation — B critical for cell division in scape + clove development",
        source_id="IMPLEMENTER_CONVENTION",
        source_section="Bulb-crop standard SA practice; FERTASA 5.6.1 prose",
        tier=6,
    ),
    # Macadamia — SAMAC Schoeman 2021 calendar foliar (per memory
    # reference_foliar_protocols_sa.md)
    StagePeakRule(
        crop="Macadamia", nutrient="B",
        week_offset_from_planting=28, stage_label="Pre-flowering",
        rate_per_ha="0.1% Solubor",
        product="Solubor", analysis="20.5% B",
        reason="Critical for flower set + nut formation; B mobile in xylem only",
        source_id="SAMAC_SCHOEMAN_2021",
        source_section="Schoeman 2021 §3.2",
        tier=1,
    ),
    StagePeakRule(
        crop="Macadamia", nutrient="Zn",
        week_offset_from_planting=32, stage_label="Vegetative flush",
        rate_per_ha="0.5% ZnSO4",
        product="Zinc Sulphate", analysis="36% Zn",
        reason="Leaf expansion + enzyme activation; soil Zn often unavailable",
        source_id="SAMAC_SCHOEMAN_2021",
        source_section="Schoeman 2021 §3.2",
        tier=1,
    ),
    # Avocado — NZAGA "Avocado Book" + standard SA practice
    StagePeakRule(
        crop="Avocado", nutrient="B",
        week_offset_from_planting=24, stage_label="Pre-bloom",
        rate_per_ha="0.1% Solubor",
        product="Solubor", analysis="20.5% B",
        reason="Pollen tube viability + flower quality; xylem-mobile only",
        source_id="NZAGA_AVOCADO_BOOK",
        source_section="Goodall 2008",
        tier=2,
    ),
    # Apple — bitter-pit Ca quality window (per reference_foliar_protocols_sa)
    StagePeakRule(
        crop="Apple", nutrient="Ca",
        week_offset_from_planting=18, stage_label="Cell-division window",
        rate_per_ha="500 g Ca",
        product="Calcium Nitrate (foliar grade)", analysis="19% Ca",
        reason="Bitter-pit prevention — Ca xylem-mobile only during cell division",
        source_id="WSU_BITTER_PIT",
        source_section="Cheng 2013",
        tier=3,
    ),
]


# ============================================================
# Trigger 3 — quality-window rules (subset overlaps trigger 2)
# ============================================================

QUALITY_WINDOW_NUTRIENTS = {"Ca", "B"}  # the most common quality-window candidates


# ============================================================
# Engine
# ============================================================

def trigger_foliar_events(
    block_id: str,
    crop: str,
    planting_date: date,
    soil_factor_report: SoilFactorReport,
    leaf_deficiencies: Optional[dict[str, float]] = None,
    block_area_ha: Optional[float] = None,
) -> list[FoliarEvent]:
    """Produce foliar events for one block from all four trigger sources.

    Args:
        block_id: stable block identifier
        crop: canonical crop name
        planting_date: programme planting date (used to compute spray dates)
        soil_factor_report: from soil_factor_reasoner.reason_soil_factors()
        leaf_deficiencies: optional {nutrient: leaf_value_below_norm}
                           — populated only on Season Tracker re-entry
        block_area_ha: used to scale rate_per_ha → total_for_block

    Returns:
        list of FoliarEvent objects. Empty list if no triggers fire.
    """
    events: list[FoliarEvent] = []
    event_num = 0

    def _next_event_num() -> int:
        nonlocal event_num
        event_num += 1
        return event_num

    def _scale(rate_per_ha: str) -> str:
        """Cheap scale-by-area for total_for_block. Only handles the
        common 'X kg' / 'X.X kg' format. Free-form rates pass through
        unchanged (renderer + UI handle nuance)."""
        if block_area_ha is None:
            return rate_per_ha
        try:
            tokens = rate_per_ha.strip().split()
            qty = float(tokens[0])
            unit = " ".join(tokens[1:])
            return f"{qty * block_area_ha:.1f} {unit}"
        except (ValueError, IndexError):
            return rate_per_ha

    # ----- Trigger 1: soil_availability_gap (from SoilFactorReport) -----
    for finding in soil_factor_report.findings:
        if finding.trigger_kind != "soil_availability_gap":
            continue
        # The reasoner already identified the antagonism + recommended foliar
        # of a given nutrient. Map P:Zn → foliar Zn, Ca:B → foliar B.
        nutrient = _antagonism_to_target_nutrient(finding.parameter)
        if not nutrient:
            continue
        product, analysis, default_rate = _foliar_default_for_nutrient(nutrient)
        spray_week = 6  # early vegetative — first practical foliar window
        events.append(FoliarEvent(
            block_id=block_id,
            event_number=_next_event_num(),
            week=spray_week,
            spray_date=planting_date + timedelta(weeks=spray_week),
            stage_name="Vegetative I",
            product=product,
            analysis=analysis,
            rate_per_ha=default_rate,
            total_for_block=_scale(default_rate),
            trigger_reason=finding.message,
            trigger_kind="soil_availability_gap",
            source=SourceCitation(
                source_id=finding.source_id,
                section=finding.source_section,
                tier=Tier(finding.tier),
            ),
        ))

    # ----- Trigger 2 + 3: stage-peak crop rules + quality-window -----
    for rule in STAGE_PEAK_RULES:
        if rule.crop != crop:
            continue
        spray_date = planting_date + timedelta(weeks=rule.week_offset_from_planting)
        trigger_kind = (
            "quality_window" if rule.nutrient in QUALITY_WINDOW_NUTRIENTS
            else "stage_peak_demand"
        )
        events.append(FoliarEvent(
            block_id=block_id,
            event_number=_next_event_num(),
            week=rule.week_offset_from_planting,
            spray_date=spray_date,
            stage_name=rule.stage_label,
            product=rule.product,
            analysis=rule.analysis,
            rate_per_ha=rule.rate_per_ha,
            total_for_block=_scale(rule.rate_per_ha),
            trigger_reason=rule.reason,
            trigger_kind=trigger_kind,
            source=SourceCitation(
                source_id=rule.source_id,
                section=rule.source_section,
                tier=Tier(rule.tier),
            ),
        ))

    # ----- Trigger 4: leaf_correction (Season Tracker re-entry) -----
    if leaf_deficiencies:
        for nutrient, value in leaf_deficiencies.items():
            product, analysis, default_rate = _foliar_default_for_nutrient(nutrient)
            spray_week = 0  # immediate (relative to leaf event date — orchestrator handles)
            events.append(FoliarEvent(
                block_id=block_id,
                event_number=_next_event_num(),
                week=spray_week,
                spray_date=date.today(),  # placeholder — orchestrator overwrites
                stage_name="Mid-season correction",
                product=product,
                analysis=analysis,
                rate_per_ha=default_rate,
                total_for_block=_scale(default_rate),
                trigger_reason=f"Leaf {nutrient} {value} below norm — immediate corrective spray",
                trigger_kind="leaf_correction",
                source=SourceCitation(
                    source_id="IMPLEMENTER_CONVENTION",
                    section="Standard SA mid-season corrective practice",
                    tier=Tier.IMPLEMENTER_CONVENTION,
                ),
            ))

    return events


def _antagonism_to_target_nutrient(parameter: str) -> Optional[str]:
    """Map antagonism-finding parameter → foliar nutrient to apply."""
    return {
        "P:Zn": "Zn",
        "Ca:B": "B",
        "Fe:Mn": "Mn",
        "Cu:Mo": "Mo",
    }.get(parameter)


def _foliar_default_for_nutrient(nutrient: str) -> tuple[str, str, str]:
    """Default product + analysis + rate for a foliar nutrient.

    Conservative SA defaults — Phase 6 may extend per-crop variants.
    Returns (product_name, analysis, rate_per_ha).
    """
    defaults = {
        "Zn": ("Zinc Sulphate", "36% Zn", "1 kg"),
        "B":  ("Solubor", "20.5% B", "1.5 kg"),
        "Mn": ("Manganese Sulphate", "24.13% Mn", "1.5 kg"),
        "Fe": ("Iron Chelate (Fe-EDDHA)", "6% Fe", "1 kg"),
        "Cu": ("Copper Sulphate", "25% Cu", "0.5 kg"),
        "Mo": ("Sodium Molybdate", "39% Mo", "100 g"),
        "Ca": ("Calcium Nitrate (foliar)", "19% Ca", "500 g Ca"),
    }
    return defaults.get(nutrient, ("Generic foliar", f"{nutrient} source", "see label"))
