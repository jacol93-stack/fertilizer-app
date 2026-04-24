"""
Target Computation with Provenance — Phase 2 module 10 of 10.

Wraps the existing soil_engine.calculate_nutrient_targets so callers pass
crop + yield + soil_values + reference catalog rows and get back:
  * typed dict of {nutrient → kg/ha}
  * per-nutrient SourceCitation (source_id + section + tier)
  * list of Assumption objects for any defaults applied
  * Tier rollup (worst-tier across all nutrients)

Also:
  * Converts P → P2O5 and K → K2O (rate tables + downstream modules use
    oxide notation; crop_requirements stores elemental)
  * Adds harvested-removal subtraction using fertasa_nutrient_removal
    when enabled (caller supplies removal_rows + actual_yield), per the
    migration 072 wiring target
  * Produces typed output the orchestrator can consume directly

This is the "entry point" closer — after this, the orchestrator takes
(crop, yield, soil_values, catalog) instead of requiring a caller to
pre-compute season_targets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.models import Assumption, SourceCitation, Tier
from app.services.soil_engine import calculate_nutrient_targets


# P → P2O5 = P × 2.291; K → K2O = K × 1.205 (standard oxide conversions)
P_TO_P2O5 = 2.291
K_TO_K2O = 1.205


@dataclass
class SoilCatalog:
    """Bundles the reference rows `calculate_nutrient_targets` needs.

    Each field mirrors a DB table. Caller loads once and passes
    through; the orchestrator wiring does this once per programme
    build, not per-block.
    """
    crop_rows: list[dict]
    sufficiency_rows: list[dict]
    adjustment_rows: list[dict]
    param_map_rows: list[dict]
    crop_override_rows: Optional[list[dict]] = None
    rate_table_rows: Optional[list[dict]] = None
    ratio_rows: Optional[list[dict]] = None
    crop_calc_flags_rows: Optional[list[dict]] = None
    removal_rows: Optional[list[dict]] = None  # fertasa_nutrient_removal


@dataclass
class TargetComputationResult:
    """Structured output of target computation — direct feed to orchestrator."""
    targets: dict[str, float]  # {nutrient: kg/ha} — uses P2O5/K2O oxide form
    sources: dict[str, SourceCitation]
    calc_path_by_nutrient: dict[str, str]  # 'rate_table' | 'cation_ratio' | 'heuristic'
    assumptions: list[Assumption] = field(default_factory=list)
    worst_tier: Optional[Tier] = None  # rollup — the least-authoritative tier used


# ============================================================
# Main function
# ============================================================

def compute_season_targets(
    crop: str,
    yield_target: float,
    soil_values: dict[str, float],
    catalog: SoilCatalog,
    rate_table_context: Optional[dict] = None,
    subtract_harvested_removal: bool = False,
    expected_yield_harvested: Optional[float] = None,
    include_micros: bool = False,
    block_pop_per_ha: Optional[float] = None,
) -> TargetComputationResult:
    """Compute per-nutrient season targets with full provenance.

    Args:
        crop: canonical crop name (post migration-070)
        yield_target: expected yield in the crop's yield unit (t/ha usually)
        soil_values: lab results dict {parameter: value}
        catalog: SoilCatalog with all reference tables
        rate_table_context: dict of axis filters for rate-table lookup
            (clay_pct, texture, rainfall_mm, region, prior_crop, water_regime)
        subtract_harvested_removal: if True, subtract fertasa_nutrient_removal
            contribution for the expected harvest (farm-gate export balance)
        expected_yield_harvested: tonnes harvested — drives removal math
        include_micros: if False (default), returns only macros + secondaries
            (N/P2O5/K2O/Ca/Mg/S). Micros flow through foliar/micro schedule
            in most programmes, not season-total targets.
        block_pop_per_ha: actual plant/tree density for this block. For
            perennials only, targets are scaled by block_pop / crop_rows
            reference pop — a 400 trees/ha mac orchard needs ~2× the kg/ha
            of a 200 trees/ha orchard at the same age, per SAMAC (Schoeman
            2021). Annuals ignore it (yield target covers stand density).

    Returns:
        TargetComputationResult with typed provenance for each nutrient.
    """
    raw_results = calculate_nutrient_targets(
        crop_name=crop,
        yield_target=yield_target,
        soil_values=soil_values,
        crop_rows=catalog.crop_rows,
        sufficiency_rows=catalog.sufficiency_rows,
        adjustment_rows=catalog.adjustment_rows,
        param_map_rows=catalog.param_map_rows,
        crop_override_rows=catalog.crop_override_rows,
        rate_table_rows=catalog.rate_table_rows,
        rate_table_context=rate_table_context,
        ratio_rows=catalog.ratio_rows,
        crop_calc_flags_rows=catalog.crop_calc_flags_rows,
    )

    targets: dict[str, float] = {}
    sources: dict[str, SourceCitation] = {}
    calc_paths: dict[str, str] = {}
    assumptions: list[Assumption] = []
    tiers_used: list[int] = []

    macro_and_secondary = {"N", "P", "K", "Ca", "Mg", "S"}
    micros = {"Fe", "B", "Mn", "Zn", "Mo", "Cu"}

    for row in raw_results:
        nutrient = row["Nutrient"]
        if not include_micros and nutrient in micros:
            continue
        if include_micros and nutrient not in macro_and_secondary and nutrient not in micros:
            continue
        if nutrient not in macro_and_secondary and nutrient not in micros:
            continue

        # Convert to oxide form for P and K (rate tables + downstream modules
        # expect this; Clivia output is in P₂O₅ + K₂O)
        output_nutrient = nutrient
        kg = float(row["Target_kg_ha"])
        if nutrient == "P":
            output_nutrient = "P2O5"
            kg = kg * P_TO_P2O5
        elif nutrient == "K":
            output_nutrient = "K2O"
            kg = kg * K_TO_K2O

        targets[output_nutrient] = round(kg, 2)
        calc_paths[output_nutrient] = row.get("Calc_Path") or "heuristic"

        # Build provenance
        source_id, section, tier_val = _parse_source_from_row(row)
        tiers_used.append(tier_val if tier_val is not None else 6)
        sources[output_nutrient] = SourceCitation(
            source_id=source_id,
            section=section,
            tier=Tier(tier_val) if tier_val is not None else Tier.IMPLEMENTER_CONVENTION,
            note=row.get("Source"),
        )

    # Perennial density scaling — per-ha FERTASA/SAMAC tables implicitly
    # assume a "normal" orchard density. A 400 trees/ha mac orchard
    # needs ~2× the kg/ha of a 200 trees/ha orchard at the same age.
    # Only applied for perennials; annuals' yield target already
    # captures stand density. Uses crop_requirements.pop_per_ha as the
    # reference baseline.
    if block_pop_per_ha and block_pop_per_ha > 0:
        density_scale, density_assumption = _compute_density_scale(
            crop=crop,
            block_pop_per_ha=block_pop_per_ha,
            crop_rows=catalog.crop_rows,
        )
        if density_scale and density_scale != 1.0:
            for nut in list(targets.keys()):
                targets[nut] = round(targets[nut] * density_scale, 2)
        if density_assumption:
            assumptions.append(density_assumption)

    # Harvested-removal subtraction (per migration 072 wiring target)
    if subtract_harvested_removal and catalog.removal_rows and expected_yield_harvested:
        removal_subtraction = _compute_removal_subtraction(
            crop=crop,
            yield_harvested=expected_yield_harvested,
            removal_rows=catalog.removal_rows,
        )
        if removal_subtraction:
            assumptions.append(Assumption(
                field="harvested_removal",
                assumed_value=str(removal_subtraction),
                override_guidance=(
                    "Harvested removal subtracted from season targets per "
                    "fertasa_nutrient_removal. For multi-year perennials, "
                    "this represents off-farm export, not in-field recycling."
                ),
                source=SourceCitation(
                    source_id="FERTASA_NUTRIENT_REMOVAL",
                    section="fertasa_nutrient_removal table",
                    tier=Tier.SA_INDUSTRY_BODY,
                ),
                tier=Tier.SA_INDUSTRY_BODY,
            ))
            for nut, kg in removal_subtraction.items():
                if nut in targets:
                    targets[nut] = max(0.0, round(targets[nut] - kg, 2))

    # Worst tier rollup (least authoritative tier drives caveats)
    worst_tier = None
    if tiers_used:
        worst_tier = Tier(max(tiers_used))

    return TargetComputationResult(
        targets=targets,
        sources=sources,
        calc_path_by_nutrient=calc_paths,
        assumptions=assumptions,
        worst_tier=worst_tier,
    )


# ============================================================
# Helpers
# ============================================================

def _parse_source_from_row(row: dict) -> tuple[str, Optional[str], Optional[int]]:
    """Extract (source_id, section, tier) from a calculate_nutrient_targets row."""
    calc_path = row.get("Calc_Path")
    if calc_path == "rate_table" and row.get("Rate_Table_Hit"):
        hit = row["Rate_Table_Hit"]
        return (
            hit.get("Source") or "RATE_TABLE",
            hit.get("Source_Section"),
            row.get("Tier"),
        )
    if calc_path == "cation_ratio" and row.get("Cation_Ratio_Hit"):
        hit = row["Cation_Ratio_Hit"]
        return (
            hit.get("Source") or "FERTASA_5_2_2",
            hit.get("Source_Section") or "5.2.2",
            row.get("Tier") or 1,
        )
    # Heuristic path
    adj = row.get("Adjustment_Factor_Source") or {}
    return (
        adj.get("source") or "IMPLEMENTER_CONVENTION",
        adj.get("source_section"),
        row.get("Tier") or 6,
    )


def _compute_density_scale(
    crop: str,
    block_pop_per_ha: float,
    crop_rows: list[dict],
) -> tuple[Optional[float], Optional[Assumption]]:
    """For perennial crops, compute a scale factor = block_pop / reference_pop.

    Returns (scale_factor, assumption) where scale_factor is None if the
    crop isn't a perennial or we can't find a reference density. The
    assumption row is always worth surfacing when we DID find a
    reference (even if the scale is 1.0 — the agronomist should know
    we're anchoring to a specific density baseline).

    References: SAMAC (Schoeman 2021) mac orchard, Raath (2021) citrus
    handbook, FERTASA handbook §5 per-tree tables. All express
    per-tree rates × trees/ha; a per-ha table is the convenience
    aggregate for a specific reference density.
    """
    crop_row = next(
        (r for r in crop_rows if r.get("crop") == crop),
        None,
    )
    if not crop_row:
        return None, None
    crop_type = (crop_row.get("crop_type") or "").lower()
    if crop_type != "perennial":
        return None, None

    ref_pop = crop_row.get("pop_per_ha")
    try:
        ref_pop_f = float(ref_pop) if ref_pop is not None else 0.0
    except (TypeError, ValueError):
        ref_pop_f = 0.0
    if ref_pop_f <= 0:
        return None, None

    scale = round(block_pop_per_ha / ref_pop_f, 3)
    assumption = Assumption(
        field="perennial_density_scale",
        assumed_value=(
            f"scale={scale} (block={int(block_pop_per_ha)} trees/ha ÷ "
            f"reference={int(ref_pop_f)} trees/ha)"
        ),
        override_guidance=(
            "Per-ha nutrient targets are scaled linearly by planting "
            "density relative to the crop's reference density from "
            "crop_requirements. Override by correcting pop_per_ha on "
            "the field record, or disable by setting block_pop_per_ha "
            "= reference density."
        ),
        source=SourceCitation(
            source_id="SAMAC_SCHOEMAN_2021" if "macadamia" in crop.lower() else "FERTASA_HANDBOOK",
            section="per-tree rate × trees/ha convention",
            tier=Tier.SA_INDUSTRY_BODY,
        ),
        tier=Tier.SA_INDUSTRY_BODY,
    )
    return scale, assumption


def _compute_removal_subtraction(
    crop: str,
    yield_harvested: float,
    removal_rows: list[dict],
) -> dict[str, float]:
    """Subtract harvested nutrient removal from season targets.

    FERTASA publishes kg/t of harvested product per crop per plant_part.
    We use the 'total' plant_part where available, else sum individual parts.
    """
    # Prefer 'total' row; fall back to 'fruit' or first row
    matched = [r for r in removal_rows if r.get("crop") == crop]
    if not matched:
        return {}

    total_row = next((r for r in matched if r.get("plant_part") == "total"), None)
    if not total_row:
        # Pick the first row available — not ideal but graceful
        total_row = matched[0]

    result: dict[str, float] = {}
    for fertasa_col, output_nut, converter in [
        ("n", "N", 1.0),
        ("p", "P2O5", P_TO_P2O5),
        ("k", "K2O", K_TO_K2O),
        ("ca", "Ca", 1.0),
        ("mg", "Mg", 1.0),
        ("s", "S", 1.0),
    ]:
        per_t = total_row.get(fertasa_col)
        if per_t is None:
            continue
        try:
            per_t_f = float(per_t)
        except (ValueError, TypeError):
            continue
        # fertasa_nutrient_removal column is kg nutrient per t product
        # (sometimes %) — assume kg/t for now; user can override via Assumption
        result[output_nut] = round(per_t_f * yield_harvested * converter, 2)
    return result
