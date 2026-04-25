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
    age_factor_rows: Optional[list[dict]] = None  # perennial_age_factors


@dataclass
class TargetComputationResult:
    """Structured output of target computation — direct feed to orchestrator."""
    targets: dict[str, float]  # {nutrient: kg/ha} — uses P2O5/K2O oxide form
    sources: dict[str, SourceCitation]
    calc_path_by_nutrient: dict[str, str]  # 'rate_table' | 'cation_ratio' | 'heuristic' | 'unadjusted'
    assumptions: list[Assumption] = field(default_factory=list)
    worst_tier: Optional[Tier] = None  # rollup — the least-authoritative tier used
    # Nutrients that fell all the way through to unadjusted removal
    # because the soil test was missing for that parameter. Caller
    # should surface these prominently — the target is uninformed by
    # soil state and may over- or under-fertilize for the actual soil.
    unadjusted_nutrients: list[str] = field(default_factory=list)


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
    harvest_mode: Optional[str] = None,
    tree_age: Optional[int] = None,
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
        harvest_mode: what leaves the field at harvest — 'grain', 'hay',
            'silage', 'fruit', 'nuts', 'tuber', 'total', etc. Controls
            which plant_part row is pulled from fertasa_nutrient_removal
            for the removal-subtraction math. If None, inferred from the
            crop's yield_unit (e.g. 't grain/ha' → 'grain'). Explicit
            override matters when a grain cereal is cut as hay: grain
            mode exports ~5 kg K/t; hay mode exports ~21 kg K/t.
        tree_age: years since planting for perennials. When supplied
            with a matching `perennial_age_factors` bracket, scales
            N / P / K / general by the bracket's factor (year-1
            establishment 0.15× → year-7+ full bearing 1.0× for citrus,
            etc.). Without this, a 3-year-old non-bearing block gets
            the same per-ha target as a 15-year-old full-bearing block.
            Annuals ignore this argument.

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
    unadjusted_nutrients: list[str] = []

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
        base_path = row.get("Calc_Path") or "heuristic"

        # Unadjusted detection: heuristic path + empty classification
        # means the soil test for this nutrient's mapped parameter was
        # missing, so factor defaulted to 1.0 and the target is raw
        # removal × yield. Promote to its own path label so the mix
        # tally surfaces it distinctly.
        classification = (row.get("Classification") or "").strip()
        if base_path == "heuristic" and not classification:
            calc_paths[output_nutrient] = "unadjusted"
            unadjusted_nutrients.append(output_nutrient)
        else:
            calc_paths[output_nutrient] = base_path

        # Build provenance
        source_id, section, tier_val = _parse_source_from_row(row)
        tiers_used.append(tier_val if tier_val is not None else 6)
        sources[output_nutrient] = SourceCitation(
            source_id=source_id,
            section=section,
            tier=Tier(tier_val) if tier_val is not None else Tier.IMPLEMENTER_CONVENTION,
            note=row.get("Source"),
        )

    # Perennial age scaling — per-ha tables assume a fully-bearing
    # tree. A 3-year-old non-bearing block needs ~15-30% of full-
    # bearing demand. Apply BEFORE density scaling so the two
    # multipliers compose cleanly (age × density × base). Annuals
    # ignore this — their yield target already encodes stand state.
    age_scale_n, age_scale_p, age_scale_k, age_scale_other, age_assumption = \
        _compute_age_scales(crop=crop, tree_age=tree_age, age_factor_rows=catalog.age_factor_rows)
    if any(s != 1.0 for s in (age_scale_n, age_scale_p, age_scale_k, age_scale_other)):
        for nut in list(targets.keys()):
            if nut == "N":
                targets[nut] = round(targets[nut] * age_scale_n, 2)
            elif nut == "P2O5":
                targets[nut] = round(targets[nut] * age_scale_p, 2)
            elif nut == "K2O":
                targets[nut] = round(targets[nut] * age_scale_k, 2)
            else:
                targets[nut] = round(targets[nut] * age_scale_other, 2)
    if age_assumption:
        assumptions.append(age_assumption)

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
        # Resolve harvest_mode: explicit override first, else infer from
        # the crop's yield_unit ('t grain/ha' → 'grain', 't hay/ha' → 'hay').
        effective_harvest_mode = harvest_mode
        if effective_harvest_mode is None:
            crop_row = next((r for r in catalog.crop_rows if r.get("crop") == crop), None)
            if crop_row:
                effective_harvest_mode = _infer_harvest_mode(crop_row.get("yield_unit"))

        removal_subtraction = _compute_removal_subtraction(
            crop=crop,
            yield_harvested=expected_yield_harvested,
            removal_rows=catalog.removal_rows,
            harvest_mode=effective_harvest_mode,
        )
        if removal_subtraction:
            mode_note = (
                f" ({effective_harvest_mode} mode)" if effective_harvest_mode else ""
            )
            assumptions.append(Assumption(
                field="harvested_removal",
                assumed_value=str(removal_subtraction),
                override_guidance=(
                    f"Harvested removal subtracted from season targets per "
                    f"fertasa_nutrient_removal{mode_note}. For multi-year "
                    f"perennials, this represents off-farm export, not "
                    f"in-field recycling. For cereals cut as hay, set "
                    f"harvest_mode='hay' — grain mode materially under-estimates K removal."
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

    # N-mineralisation assessment — surface when Org C is present so
    # the agronomist sees the credit range and can adjust the N target.
    # We don't auto-subtract because published SA mineralisation rates
    # are ranges (FERTASA §5.5.2 cites 20-30 kg N/ha per 1% OC above a
    # 1% baseline, but the actual value depends on temperature, moisture,
    # C:N ratio, prior cropping) and our worst-case rule would either
    # over- or under-credit. Visibility > silent adjustment.
    n_min_assumption = _assess_n_mineralisation(soil_values)
    if n_min_assumption:
        assumptions.append(n_min_assumption)

    # Unadjusted-removal assumption — surfaced on the artifact so the
    # agronomist knows which nutrients got a soil-state-blind target.
    if unadjusted_nutrients:
        assumptions.append(Assumption(
            field="unadjusted_removal_nutrients",
            assumed_value=", ".join(unadjusted_nutrients),
            override_guidance=(
                "These nutrients had no soil test for their mapped parameter, "
                "so the target is base removal × yield (no soil-state scaling). "
                "May over- or under-fertilize vs the actual soil. Upload a "
                "complete soil analysis to refine."
            ),
            source=None,
            tier=Tier.IMPLEMENTER_CONVENTION,
        ))

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
        unadjusted_nutrients=unadjusted_nutrients,
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


def _compute_age_scales(
    crop: str,
    tree_age: Optional[int],
    age_factor_rows: Optional[list[dict]],
) -> tuple[float, float, float, float, Optional[Assumption]]:
    """For perennial crops, look up per-bracket age factors and return
    (n_factor, p_factor, k_factor, general_factor, assumption).

    Per-ha agronomic tables (FERTASA, SAMAC, NZAGA) implicitly assume a
    fully-bearing tree. A 3-year-old non-bearing block actually wants
    ~15-30% of full-bearing demand — applying the full target over-
    fertilises the canopy 3-5× and risks salinity / nitrate leaching
    on young root systems. The `perennial_age_factors` table holds
    the published establishment → full-bearing curve per crop.

    Returns (1.0, 1.0, 1.0, 1.0, None) when:
    - tree_age is None (caller didn't provide it)
    - age_factor_rows is None / empty
    - no row matches the crop
    - no bracket covers tree_age (defensive default; doesn't raise)

    Otherwise returns the four factors + an Assumption row with the
    bracket label + factor values for traceability on the artifact.
    """
    if tree_age is None or not age_factor_rows:
        return 1.0, 1.0, 1.0, 1.0, None

    # Match by crop name first; fall back to parent-crop lookup so a
    # variant like "Citrus (Valencia)" picks up the parent-crop curve
    # if the variant itself has no rows seeded.
    crop_rows = [r for r in age_factor_rows if (r.get("crop") or "") == crop]
    if not crop_rows:
        # Strip variant suffix " (Variant)" and try parent.
        if "(" in crop:
            parent = crop.split("(")[0].strip()
            crop_rows = [r for r in age_factor_rows if (r.get("crop") or "") == parent]
    if not crop_rows:
        return 1.0, 1.0, 1.0, 1.0, None

    bracket = None
    for r in crop_rows:
        try:
            lo = int(r.get("age_min") or 0)
            hi = int(r.get("age_max") or 99)
        except (TypeError, ValueError):
            continue
        if lo <= tree_age <= hi:
            bracket = r
            break
    if not bracket:
        return 1.0, 1.0, 1.0, 1.0, None

    def _f(key: str) -> float:
        try:
            return float(bracket.get(key) or 1.0)
        except (TypeError, ValueError):
            return 1.0

    n_f = _f("n_factor")
    p_f = _f("p_factor")
    k_f = _f("k_factor")
    g_f = _f("general_factor")
    label = bracket.get("age_label") or f"age {tree_age}"
    notes = bracket.get("notes") or ""

    assumption = Assumption(
        field="perennial_age_scale",
        assumed_value=(
            f"{label} (age {tree_age} y) — N×{n_f}, P×{p_f}, K×{k_f}, "
            f"others×{g_f}"
        ),
        override_guidance=(
            f"Per-ha targets scaled by published establishment-curve "
            f"factors so a young block isn't over-fertilised. "
            f"{notes + '. ' if notes else ''}"
            f"Override by correcting tree_age on the block, or by "
            f"editing the `perennial_age_factors` row for this crop."
        ),
        source=SourceCitation(
            source_id=(
                "SAMAC_SCHOEMAN_2021" if "macadamia" in crop.lower()
                else "NZAGA_AVOCADO_BOOK" if "avocado" in crop.lower()
                else "CRI_CITRUS_GUIDE" if "citrus" in crop.lower()
                else "FERTASA_HANDBOOK"
            ),
            section="perennial_age_factors table",
            tier=Tier.SA_INDUSTRY_BODY,
        ),
        tier=Tier.SA_INDUSTRY_BODY,
    )
    return n_f, p_f, k_f, g_f, assumption


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


# ── Harvest-mode → plant_part resolution ─────────────────────────────
#
# Which plant_part row to pull from fertasa_nutrient_removal depends on
# what leaves the field at harvest:
#   - Grain harvest: only the grain is exported; straw returns as residue
#     → use the 'grain' row (smaller off-take, much less K)
#   - Hay / silage cut: whole plant is removed → use the 'total' row
#     (significantly more K; cereal hay draws soil K 3-4× faster than
#     grain harvest)
#   - Fruit / nut / tuber crops: those parts are the export
#
# When harvest_mode isn't explicitly provided, we infer it from the
# crop's yield_unit ("t grain/ha" → grain, "t hay/ha" → hay, etc.).
# Callers can override per programme.
_YIELD_UNIT_TO_HARVEST_MODE = {
    "grain": "grain",
    "seed": "grain",           # canola/sunflower/lentil seed → same removal convention as grain
    "hay": "hay",
    "fruit": "fruit",
    "pod": "pods",
    "shoots": "shoots",
    "leaf": "leaves",
    "leaves": "leaves",
    "made": "leaves",          # tea
    "nis": "nuts",             # NIS = Nut-In-Shell (macadamia/pecan)
    "cane": "total",           # sugarcane: whole stalk exported
    "tuber": "total",          # potato/sweet potato: map to total — no tuber row yet
    "root": "total",           # carrot/beetroot
    "bulb": "total",           # garlic/onion
    "head": "total",           # cabbage/lettuce
    "dry": "total",            # rooibos/honeybush
    "green": "fruit",          # coffee green bean
    "fresh": "total",          # sweetcorn
    "cobs": "total",
    "cotton": "total",
}

_PLANT_PART_PREFERENCE = ("total", "fruit", "grain", "hay")


def _infer_harvest_mode(yield_unit: Optional[str]) -> Optional[str]:
    """Pick a sensible default plant_part from a crop's yield unit string.

    e.g. 't grain/ha' → 'grain', 't hay/ha' → 'hay', 't NIS/ha' → 'nuts'.
    Returns None when the unit doesn't map clearly — caller falls back
    to the generic 'total > fruit > first' preference order.
    """
    if not yield_unit:
        return None
    unit_lc = yield_unit.lower()
    for token, mode in _YIELD_UNIT_TO_HARVEST_MODE.items():
        if token in unit_lc:
            return mode
    return None


def _compute_removal_subtraction(
    crop: str,
    yield_harvested: float,
    removal_rows: list[dict],
    harvest_mode: Optional[str] = None,
) -> dict[str, float]:
    """Subtract harvested nutrient removal from season targets.

    FERTASA publishes kg/t of harvested product per crop per plant_part.
    The right plant_part to pull depends on what leaves the field:
    grain harvest exports only grain (straw stays), hay/silage exports
    the whole plant, fruit crops export fruit. Pass `harvest_mode` to
    pick the matching plant_part; on miss, fall back through a
    preference order ('total' > 'fruit' > first available).
    """
    matched = [r for r in removal_rows if r.get("crop") == crop]
    if not matched:
        return {}

    # First try: exact plant_part match for the requested harvest mode
    chosen_row = None
    if harvest_mode:
        chosen_row = next(
            (r for r in matched if r.get("plant_part") == harvest_mode),
            None,
        )

    # Fallback preference order — 'total' is the safest default when no
    # harvest-mode-specific row exists (conservative over-estimate for
    # whole-plant removal; under-estimate for grain-harvest cereals).
    if chosen_row is None:
        for preferred in _PLANT_PART_PREFERENCE:
            chosen_row = next(
                (r for r in matched if r.get("plant_part") == preferred),
                None,
            )
            if chosen_row is not None:
                break

    # Last resort — any row
    if chosen_row is None:
        chosen_row = matched[0]

    total_row = chosen_row

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


# ============================================================
# N-mineralisation assessment
# ============================================================

# Common lab-report keys for soil organic-carbon / organic-matter.
# Labs aren't consistent; try all of these. Values are %.
_ORG_C_KEYS = ("Org C", "OC", "Organic Carbon", "C_org", "organic_carbon_pct", "Org_C_%")
_ORG_M_KEYS = ("OM", "Organic Matter", "Organic_Matter", "organic_matter_pct", "Humus")

# Conversion factor OM → OC (Van Bemmelen): OC ≈ OM / 1.724. Used only
# when OC isn't reported directly but OM is.
_OM_TO_OC = 1.0 / 1.724


def _extract_organic_carbon_pct(soil_values: dict) -> Optional[float]:
    """Find OC % in soil_values, tolerating lab naming variance and
    falling back to OM / 1.724 (Van Bemmelen) when only OM is reported.

    Returns None if nothing usable is present.
    """
    if not soil_values:
        return None
    for key in _ORG_C_KEYS:
        val = soil_values.get(key)
        if val is not None:
            try:
                f = float(val)
                if f >= 0:
                    return f
            except (ValueError, TypeError):
                continue
    for key in _ORG_M_KEYS:
        val = soil_values.get(key)
        if val is not None:
            try:
                f = float(val)
                if f >= 0:
                    return round(f * _OM_TO_OC, 3)
            except (ValueError, TypeError):
                continue
    return None


def _assess_n_mineralisation(soil_values: dict) -> Optional[Assumption]:
    """Surface an N-mineralisation consideration when OC is meaningfully
    above the 1% baseline.

    FERTASA §5.5.2 describes mineralisation of soil OM as a significant
    N contribution for SA summer-rainfall cropping — typical published
    range is 20-30 kg N/ha per 1% OC above ~1% baseline, capped around
    4% OC (above that the extra is harder to predict). The actual value
    swings with temperature, moisture, C:N ratio, and prior cropping;
    we surface the credit range as an Assumption rather than silently
    subtracting from the N target so the agronomist owns the call.

    Threshold: OC ≥ 1.5% is "meaningfully above baseline" worth flagging.
    Returns None if OC is absent or below the threshold.
    """
    oc_pct = _extract_organic_carbon_pct(soil_values)
    if oc_pct is None or oc_pct < 1.5:
        return None

    # Conservative credit band: 20 kg N/ha per 1% OC above 1%, capped
    # above 4% OC. Rounded to the nearest 5 kg for readability.
    oc_above_baseline = min(oc_pct, 4.0) - 1.0
    low_credit = int(round(oc_above_baseline * 20 / 5)) * 5
    high_credit = int(round(oc_above_baseline * 30 / 5)) * 5

    return Assumption(
        field="n_mineralisation_credit",
        assumed_value=f"{low_credit}-{high_credit} kg N/ha (OC {oc_pct:.2f}%)",
        override_guidance=(
            f"Org C {oc_pct:.2f}% is meaningfully above SA arable baseline (~1%). "
            f"FERTASA §5.5.2 convention: 20-30 kg N/ha per 1% OC above 1% for "
            f"summer-rainfall cropping. Consider reducing the N target by "
            f"{low_credit}-{high_credit} kg/ha if prior cropping, temperature, "
            f"and moisture support mineralisation (warm, moist, legume residue "
            f"→ upper end; cool, dry, cereal residue → lower end or none)."
        ),
        source=SourceCitation(
            source_id="FERTASA_5_5_2",
            section="5.5.2",
            tier=Tier.SA_INDUSTRY_BODY,
        ),
        tier=Tier.SA_INDUSTRY_BODY,
    )
