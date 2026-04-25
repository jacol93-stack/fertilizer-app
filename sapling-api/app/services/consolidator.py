"""
Consolidator — Phase 2 module 8 of 10.

Groups method_selector assignments into a small number of physical Blend
events per block. Enforces the "no 10s of products per crop per farm"
constraint: target is 3-6 blends per (block × method), not one blend per
weekly event.

Key responsibilities:
  1. Aggregate per (stage, method) — all nutrients for that combo flow
     into one blend
  2. Material selection — pick a small set of products whose combined
     composition supplies the stage's nutrient targets
  3. Part A/B split for fertigation — Ca-containing products in Part A
     stream; sulphate + phosphate + acid-compatible in Part B (prevents
     CaSO₄ precipitation)
  4. Produce typed Blend + BlendPart + Concentrate objects for the
     ProgrammeArtifact

Material selection is currently a **greedy cover algorithm** (Tier 6):
  * Rank materials by their contribution to the remaining deficit
  * Pick the best; subtract what it supplies; repeat
  * Stop when targets met (within tolerance) or products exhausted

A future module (not in this session) will delegate to the existing
liquid_optimizer (MILP) + optimizer (dry) for proper constrained
optimisation with incompatibility handling + cost minimisation.
For now, the Blend is produced with a Tier-6 source note + can be
refined by the user or by the downstream optimiser.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from datetime import date, timedelta

from app.models import (
    ApplicationEvent,
    ApplicationMethod,
    Blend,
    BlendPart,
    Concentrate,
    DryBlendMethod,
    FertigationMethod,
    FoliarMethod,
    MethodKind,
    SourceCitation,
    Tier,
)
from app.services.method_selector import MethodAssignment
from app.services.month_allocator import AllocatedApplication
from app.services.timing_walls import walls_for_crop


# ============================================================
# Configuration
# ============================================================

# Target max distinct products per blend (soft constraint — greedy
# algorithm stops when hit)
MAX_PRODUCTS_PER_BLEND = 6

# Tolerance for "nutrient target met" — stop adding products when deficit
# is below this fraction of original target
DEFICIT_STOP_TOLERANCE = 0.05  # within 5% of target = done

# ============================================================
# Organic-carrier policy (Sapling house rule)
# ============================================================
# Every dry-blend Sapling produces is anchored by an organic carrier at
# ≥ 50 % of blend mass. The carrier (manure compost / pellet) delivers
# organic carbon, slow-release N, micronutrients, and gives the
# programme its multi-year soil-health trajectory. Synthetic products
# layer on top to close remaining nutrient gaps.
#
# This policy applies only to dry blends — fertigation and foliar
# blends are liquid pipelines and use different materials.

MIN_ORGANIC_FRACTION_DRY = 0.5  # 50 % of blend mass = organic carrier

# Starter organic-carrier rate (kg/ha) when no stronger signal drives it.
# A post-check bumps this if synthetic mass ends up requiring more organic
# to satisfy the 50 % rule.
ORGANIC_CARRIER_STARTER_KG_HA = 500.0

# Year-1 plant-available fractions for organic carrier nutrients. The
# remainder mineralises across Y2-Y4 as soil biology works on the
# organic fraction (see feedback_visibility_over_fabrication memory —
# these are conservative SA norms, not farm-specific).
ORGANIC_Y1_AVAILABILITY = {
    "N":  0.25,   # FERTASA §5.5.2: 20-30 % Y1 typical for SA composts
    "P":  0.50,   # slower than synthetic but much faster than N
    "K":  0.80,   # mostly mineral in manure ash, rapidly available
    "Ca": 0.90,
    "Mg": 0.90,
    "S":  0.60,
    "B":  0.70,
    "Zn": 0.70,
    "Mn": 0.70,
    "Cu": 0.70,
    "Fe": 0.70,
    "Mo": 0.70,
}


def _is_organic_carrier(material: dict) -> bool:
    """Identify a bulk organic carrier: solid manure-compost-class product
    carrying carbon + nitrogen in meaningful quantities.

    Keeps liquid organics (molasses, humic acid) and acid bio-stimulants
    (propionic) out of the dry-blend 50 %-rule pool.
    """
    if material.get("type") != "Organic":
        return False
    if material.get("form") != "solid":
        return False
    try:
        n_pct = float(material.get("n") or 0)
        c_pct = float(material.get("c") or 0)
    except (ValueError, TypeError):
        return False
    return n_pct >= 0.5 and c_pct >= 10.0


def _find_organic_carrier(materials: list[dict]) -> Optional[dict]:
    """Pick the single best organic carrier from the catalog. Prefer the
    one with highest carbon content — that's the metric the multi-year
    soil-building narrative leans on."""
    candidates = [m for m in materials if _is_organic_carrier(m)]
    if not candidates:
        return None
    return max(candidates, key=lambda m: float(m.get("c") or 0))


def _is_dry_blend_method(method_kind: MethodKind) -> bool:
    """The 50 %-organic rule applies only to dry blends. Fertigation +
    foliar are liquid pipelines; the organic pellet can't participate
    there."""
    return method_kind.name.startswith("DRY_")


def _material_total_mass(selected: list[tuple[dict, float]]) -> float:
    """Sum of rates across selected (material, rate) pairs."""
    return sum(rate for _, rate in selected)

# ============================================================
# Part A / Part B stream classification (liquid only)
# ============================================================
# Ca ↔ SO₄ / PO₄ incompatibility means Part A (Calcium stream) must not
# meet Part B (sulphate/phosphate stream) in concentrate. They join only
# in the diluted drip line downstream of injection.

def _classify_stream(material: dict) -> str:
    """Returns 'A' (calcium stream) or 'B' (sulphate/phosphate stream).

    Rule: if material carries a dominant cation (Ca OR Mg ≥ 5%) and is
    NOT dominated by S or P2O5 (< 2% of each) → Part A. Everything
    else → Part B.

    Why both Ca AND Mg: both go in the "calcium stream" in FERTASA §11
    fertigation compatibility. Mg Nitrate (N 11%, Mg 15%, S 0%) is a
    Part A product; missing the Mg limb classifies it B and it ends
    up in the sulphate/phosphate stock tank, which is wrong.

    Borderline cases (Ca-containing sulphate/phosphate like
    Metabophos) stay Part B because the SO₄/PO₄ dominates
    compatibility behavior — MgSO4 stays B because S ≥ 2.
    """
    ca = float(material.get("ca") or 0)
    mg = float(material.get("mg") or 0)
    s = float(material.get("s") or 0)
    # materials.p column in this DB is P2O5 equivalent
    p = float(material.get("p") or 0)
    if (ca >= 5 or mg >= 5) and s < 2 and p < 2:
        return "A"
    return "B"


# ============================================================
# Main consolidator
# ============================================================

def consolidate_blends(
    assignments: list[MethodAssignment],
    available_materials: list[dict],
    block_id: str,
    block_area_ha: float,
    stage_schedule: Optional[list] = None,  # list of StageWindow for per-event math
    allocations: Optional[list[AllocatedApplication]] = None,
    planting_date: Optional[date] = None,
    crop: Optional[str] = None,
) -> list[Blend]:
    """Group method assignments into typed Blend objects.

    Args:
        assignments: from method_selector.select_methods()
        available_materials: material catalog (dicts matching materials row)
        block_id: programme block identifier
        block_area_ha: for per-block totals
        stage_schedule: optional StageWindow list — provides events per stage
                        for fertigation per-event dose math
        allocations: optional AllocatedApplication list from the month
                     allocator. When present, populates each Blend's
                     applications[] with one ApplicationEvent per allocator
                     event falling in the Blend's real stage. When absent,
                     falls back to one synthesised ApplicationEvent per
                     stage derived from stage_schedule.
        planting_date: used to compute week_from_planting for synthesised
                       events when allocations is None.
        crop: canonical crop name. When supplied, fertigation material
              selection consults the crop's nutrient_antagonism walls
              from timing_walls so two single-nutrient salts that the
              wall flags as together-forbidden (e.g. Citrus N + K per
              FERTASA 5.7.3) are not co-applied in one event. Compound
              salts that carry both nutrients in a single molecule
              (e.g. KNO3) are still allowed — the rule targets only
              separate-salt pairs.

    Returns:
        list of Blend objects. One blend per (stage × method) that has
        non-zero assignments. Blends already empty-nutrient are skipped.
    """
    # Aggregate assignments by (stage_number, method)
    grouped: dict[tuple[int, MethodKind, str], dict] = {}
    for a in assignments:
        key = (a.stage_number, a.method, a.stage_name)
        if key not in grouped:
            grouped[key] = {"nutrients": {}, "reasons": []}
        grouped[key]["nutrients"][a.nutrient] = grouped[key]["nutrients"].get(a.nutrient, 0) + a.kg_per_ha
        grouped[key]["reasons"].append(a.reason)

    # Build events-per-stage lookup from stage_schedule
    events_lookup = {}
    if stage_schedule:
        for sw in stage_schedule:
            events_lookup[sw.stage_number] = (sw.events, sw.week_start, sw.week_end, sw.date_start, sw.date_end)

    # Index allocations by real stage_number for per-Blend ApplicationEvent population
    allocations_by_stage: dict[int, list[AllocatedApplication]] = {}
    if allocations:
        for app in allocations:
            allocations_by_stage.setdefault(app.stage_number, []).append(app)

    blends: list[Blend] = []
    for (stage_num, method_kind, stage_name), data in sorted(grouped.items()):
        nutrient_targets = data["nutrients"]
        if not nutrient_targets or all(v <= 0 for v in nutrient_targets.values()):
            continue

        events_info = events_lookup.get(stage_num)

        # Build ApplicationEvents — one per allocator event in this stage,
        # or one synthesised event from stage_schedule when allocator didn't run.
        application_events = _build_application_events(
            stage_num=stage_num,
            stage_allocations=allocations_by_stage.get(stage_num, []),
            stage_window=_first_stage_window(stage_schedule, stage_num),
            planting_date=planting_date,
        )
        events_count = len(application_events)

        # Greedy material selection for this (stage, method)
        selected = _select_materials_greedy(
            nutrient_targets=nutrient_targets,
            available_materials=available_materials,
            method_kind=method_kind,
            crop=crop,
        )

        # Build BlendParts from selected materials
        raw_products, delivered = _build_blend_parts(
            selected=selected,
            nutrient_targets=nutrient_targets,
            block_area_ha=block_area_ha,
            events_count=events_count,
            method_kind=method_kind,
        )

        # Part A / Part B concentrates for fertigation only
        concentrates: list[Concentrate] = []
        if _is_fertigation(method_kind):
            concentrates = _build_fertigation_concentrates(
                raw_products=raw_products,
                block_area_ha=block_area_ha,
            )

        # Construct the method-specific ApplicationMethod instance
        method_obj = _build_application_method(method_kind)

        blends.append(Blend(
            block_id=block_id,
            stage_number=stage_num,
            stage_name=stage_name,
            applications=application_events,
            method=method_obj,
            raw_products=raw_products,
            concentrates=concentrates,
            nutrients_delivered=delivered,
            sources=[SourceCitation(
                source_id="IMPLEMENTER_CONVENTION",
                section="Greedy material-cover algorithm v1 (Phase 2 module 8)",
                tier=Tier.IMPLEMENTER_CONVENTION,
            )],
        ))

    return blends


def _first_stage_window(stage_schedule: Optional[list], stage_num: int):
    if not stage_schedule:
        return None
    for sw in stage_schedule:
        if sw.stage_number == stage_num:
            return sw
    return None


def _build_application_events(
    stage_num: int,
    stage_allocations: list[AllocatedApplication],
    stage_window,
    planting_date: Optional[date],
) -> list[ApplicationEvent]:
    """Produce the ApplicationEvent list for one Blend.

    When the month allocator ran, every allocator event in this real stage
    becomes one ApplicationEvent — dates, week offsets, and 1-of-N counters
    all flow through.

    When the allocator did not run (no application_months input), we
    synthesise a single ApplicationEvent anchored to the stage window's
    midpoint — preserving the legacy single-event-per-stage semantics.
    """
    if stage_allocations:
        return [
            ApplicationEvent(
                event_index=a.event_index,
                event_date=a.event_date,
                week_from_planting=a.week_from_planting,
                event_of_stage_index=a.event_of_stage_index,
                total_events_in_stage=a.total_events_in_stage,
            )
            for a in sorted(stage_allocations, key=lambda x: x.event_date)
        ]

    if stage_window is not None:
        # Spread the stage's annotated event count evenly across its window.
        n_events = max(1, int(getattr(stage_window, "events", 1) or 1))
        span_days = (stage_window.date_end - stage_window.date_start).days
        span_weeks = stage_window.week_end - stage_window.week_start
        events_list: list[ApplicationEvent] = []
        for i in range(n_events):
            # Spacing: at n_events=1 → midpoint; at n_events>1 → evenly
            # distributed between date_start and date_end.
            if n_events == 1:
                frac = 0.5
            else:
                frac = i / (n_events - 1)
            day_offset = int(round(span_days * frac))
            wk_offset = int(round(span_weeks * frac))
            events_list.append(ApplicationEvent(
                event_index=stage_num * 100 + i + 1,  # unique-ish within programme
                event_date=stage_window.date_start + timedelta(days=day_offset),
                week_from_planting=stage_window.week_start + wk_offset,
                event_of_stage_index=i + 1,
                total_events_in_stage=n_events,
            ))
        return events_list

    # No schedule, no allocations — build a placeholder anchored at planting
    anchor = planting_date or date.today()
    return [ApplicationEvent(
        event_index=stage_num,
        event_date=anchor + timedelta(weeks=max(0, stage_num - 1) * 4),
        week_from_planting=max(1, (stage_num - 1) * 4 + 1),
        event_of_stage_index=1,
        total_events_in_stage=1,
    )]


# ============================================================
# Greedy material-cover selection
# ============================================================

def _select_materials_greedy(
    nutrient_targets: dict[str, float],
    available_materials: list[dict],
    method_kind: MethodKind,
    crop: Optional[str] = None,
) -> list[tuple[dict, float]]:
    """Pick materials iteratively — best deficit-coverage first.

    For dry blends, anchors the blend with an organic carrier at ≥ 50 %
    of blend mass per Sapling's house rule. The carrier's Y1-available
    nutrients reduce the deficit before the synthetic greedy pass; if
    the post-synthetic mass balance would drop organic below 50 %, the
    organic rate is bumped to restore it.

    For fertigation, when `crop` is supplied and the crop has a
    `nutrient_antagonism` timing wall (e.g. Citrus N+K per FERTASA
    5.7.3), the greedy filter rejects candidates that would create a
    separate single-nutrient-salt co-application of a forbidden pair.
    Compound salts that carry both nutrients in one molecule (e.g. KNO3)
    pass through unchanged — the rule targets only separate-salt pairs.

    Returns: list of (material_dict, kg_per_ha_to_apply) tuples.
    """
    # Filter materials by method compatibility
    candidates = _filter_materials_for_method(available_materials, method_kind)
    if not candidates:
        return []

    # Resolve nutrient-antagonism pairs from the crop's timing walls.
    # Only fertigation triggers the per-event antagonism check — dry
    # blending is a separate physical regime (granule-mix incompat is
    # already handled by blend_validator's known-bad-pair list).
    forbidden_pairs: list[tuple[str, str]] = []
    if crop and _is_fertigation(method_kind):
        for wall in walls_for_crop(crop):
            if wall.kind == "nutrient_antagonism":
                forbidden_pairs.append(wall.together_forbidden)

    # Normalise nutrient keys to material columns
    deficit = _normalise_nutrients(nutrient_targets)

    selected: list[tuple[dict, float]] = []
    picked_names: set[str] = set()

    # ── Organic carrier anchor (dry blends only) ───────────────────
    # Seed the blend with an organic carrier before the synthetic pass.
    # Its Y1-available nutrients reduce the deficit; its full mass is
    # locked in as the ≥ 50 % foundation.
    organic_carrier = None
    if _is_dry_blend_method(method_kind):
        organic_carrier = _find_organic_carrier(candidates)
        if organic_carrier is not None:
            organic_rate = ORGANIC_CARRIER_STARTER_KG_HA
            _subtract_organic_contribution(deficit, organic_carrier, organic_rate)
            selected.append((organic_carrier, organic_rate))
            picked_names.add(organic_carrier["material"])

    while len([n for n in deficit.values() if n > 0.01]) > 0 and len(selected) < MAX_PRODUCTS_PER_BLEND:
        best_material = None
        best_rate = 0.0
        best_score = 0.0

        for mat in candidates:
            if mat.get("material") in picked_names:
                continue
            # Antagonism filter — skip candidates that would create a
            # separate-salt co-application of a forbidden nutrient pair
            # against any already-selected material.
            if forbidden_pairs and _antagonism_violates(
                mat, [m for m, _ in selected], forbidden_pairs,
            ):
                continue
            rate, score = _evaluate_material(mat, deficit)
            if score > best_score:
                best_score = score
                best_material = mat
                best_rate = rate

        if best_material is None or best_score <= 0:
            break

        # Subtract this material's contribution from deficit
        _subtract_contribution(deficit, best_material, best_rate)
        selected.append((best_material, best_rate))
        picked_names.add(best_material["material"])

        # Stop if all deficits within tolerance
        if all(
            abs(d) < DEFICIT_STOP_TOLERANCE * _original_target(nutrient_targets, k)
            for k, d in deficit.items()
        ):
            break

    # ── Post-check: enforce organic ≥ 50 % of blend mass ──────────
    # If the synthetic products ended up weighing more than the organic
    # carrier, bump the carrier rate so organic mass equals synthetic
    # mass (= 50 % exactly). This preserves nutrient coverage while
    # honouring Sapling's house rule that every dry blend is carrier-
    # anchored.
    if organic_carrier is not None and len(selected) > 1:
        synthetic_mass = sum(
            rate for mat, rate in selected if mat is not organic_carrier
        )
        organic_idx, organic_rate = next(
            (i, rate) for i, (mat, rate) in enumerate(selected) if mat is organic_carrier
        )
        if synthetic_mass > organic_rate:
            selected[organic_idx] = (organic_carrier, synthetic_mass)

    return selected


def _is_single_source_for(material: dict, nutrient: str, antagonist: str) -> bool:
    """True if `material` carries significant `nutrient` (≥ 5 % m/m) but
    NOT `antagonist` (< 1 % m/m). Used to flag separate-salt pairs that
    a `nutrient_antagonism` timing wall forbids from co-application.

    A material that carries both nutrients in one molecule (e.g. KNO3
    = N + K) is NOT single-source for either — it's a compound salt and
    FERTASA-style co-application rules do not apply to it.
    """
    own_pct = _material_pct_for(material, nutrient)
    other_pct = _material_pct_for(material, antagonist)
    return own_pct >= 0.05 and other_pct < 0.01


def _antagonism_violates(
    candidate: dict,
    already_selected: list[dict],
    forbidden_pairs: list[tuple[str, str]],
) -> bool:
    """True if adding `candidate` to the blend would create a separate-
    salt co-application of any (a, b) nutrient pair the crop's timing
    walls forbid from co-application.

    Logic per pair (a, b):
      * candidate single-source-a + any selected single-source-b → violation
      * candidate single-source-b + any selected single-source-a → violation
    Compound salts on either side don't trigger the rule.
    """
    if not already_selected:
        return False
    for (a, b) in forbidden_pairs:
        cand_is_a = _is_single_source_for(candidate, a, b)
        cand_is_b = _is_single_source_for(candidate, b, a)
        if not (cand_is_a or cand_is_b):
            continue
        for prior in already_selected:
            prior_is_a = _is_single_source_for(prior, a, b)
            prior_is_b = _is_single_source_for(prior, b, a)
            if cand_is_a and prior_is_b:
                return True
            if cand_is_b and prior_is_a:
                return True
    return False


def _subtract_organic_contribution(
    deficit: dict[str, float], organic: dict, rate: float,
) -> None:
    """Subtract the Y1-plant-available portion of an organic carrier's
    delivery from the deficit. The full mass is applied, but only the
    fraction that mineralises in the current season counts against the
    deficit — the remainder is the multi-year soil-building investment.
    """
    for nutrient in list(deficit.keys()):
        pct = _material_pct_for(organic, nutrient)
        if pct <= 0:
            continue
        y1_frac = ORGANIC_Y1_AVAILABILITY.get(nutrient, 0.7)
        available = rate * pct * y1_frac
        deficit[nutrient] = max(0.0, deficit[nutrient] - available)


def _evaluate_material(material: dict, deficit: dict[str, float]) -> tuple[float, float]:
    """Given deficit, compute optimal rate of this material + its score.

    Rate = smallest rate that fills the limiting deficit without overshoot.
    Score = total deficit reduction achievable at that rate.
    """
    # For each nutrient, compute rate that exactly fills it
    rates_to_fill = []
    for nutrient, def_kg in deficit.items():
        if def_kg <= 0:
            continue
        pct = _material_pct_for(material, nutrient)
        if pct <= 0:
            continue
        # rate (kg material / ha) × pct (kg nut / kg mat) = def_kg
        # rate = def_kg / pct
        rates_to_fill.append(def_kg / pct)

    if not rates_to_fill:
        return (0.0, 0.0)

    # Pick the smallest rate (no overshoot on any nutrient)
    rate = min(rates_to_fill)
    # Score = sum of deficits actually reduced
    score = 0.0
    for nutrient, def_kg in deficit.items():
        if def_kg <= 0:
            continue
        pct = _material_pct_for(material, nutrient)
        if pct <= 0:
            continue
        score += min(def_kg, rate * pct)
    return (rate, score)


def _subtract_contribution(deficit: dict[str, float], material: dict, rate: float) -> None:
    """Mutate deficit by subtracting this material × rate."""
    for nutrient in list(deficit.keys()):
        pct = _material_pct_for(material, nutrient)
        deficit[nutrient] = max(0.0, deficit[nutrient] - rate * pct)


def _material_pct_for(material: dict, nutrient: str) -> float:
    """Map normalised nutrient key → material column fraction (0-1)."""
    col = {
        "N": "n", "P2O5": "p", "P": "p", "K2O": "k", "K": "k",
        "Ca": "ca", "Mg": "mg", "S": "s",
        "Fe": "fe", "B": "b", "Mn": "mn", "Zn": "zn", "Mo": "mo", "Cu": "cu",
    }.get(nutrient)
    if col is None:
        return 0.0
    return float(material.get(col) or 0) / 100.0


def _filter_materials_for_method(
    materials: list[dict], method_kind: MethodKind,
) -> list[dict]:
    """Only keep materials compatible with this method."""
    if _is_fertigation(method_kind):
        # Liquid-compatible required
        return [m for m in materials if m.get("liquid_compatible", False)
                or m.get("form") == "liquid"]
    if method_kind == MethodKind.FOLIAR:
        return [m for m in materials if m.get("foliar_compatible", False)]
    if method_kind.name.startswith("DRY_"):
        # Exclude pre-season-only for in-season dry stages (except
        # establishment — but method_selector already routed pre-plant P
        # to DRY_BROADCAST, so lime/gypsum reach here only in
        # establishment blends, which is correct)
        return [m for m in materials if m.get("form") != "liquid"]
    return list(materials)


# ============================================================
# Blend assembly helpers
# ============================================================

def _normalise_nutrients(targets: dict[str, float]) -> dict[str, float]:
    """Build a working copy for deficit tracking."""
    return {k: v for k, v in targets.items() if v > 0}


def _original_target(targets: dict[str, float], key: str) -> float:
    """Max-tolerance anchor for each nutrient (min 1.0 to avoid div-by-zero)."""
    return max(1.0, targets.get(key, 0.0))


def _build_blend_parts(
    selected: list[tuple[dict, float]],
    nutrient_targets: dict[str, float],
    block_area_ha: float,
    events_count: int,
    method_kind: MethodKind,
) -> tuple[list[BlendPart], dict[str, float]]:
    """Build BlendParts + compute delivered-nutrients."""
    parts: list[BlendPart] = []
    delivered: dict[str, float] = {k: 0.0 for k in nutrient_targets}

    for material, rate_kg_ha in selected:
        per_event = rate_kg_ha / events_count if events_count else rate_kg_ha
        per_stage = rate_kg_ha
        batch_total = rate_kg_ha * block_area_ha

        stream = None
        if _is_fertigation(method_kind):
            stream = _classify_stream(material)

        parts.append(BlendPart(
            product=material.get("material", "Unknown"),
            analysis=_analysis_label(material),
            stream=stream,
            rate_per_event_per_ha=_fmt_kg(per_event),
            rate_per_stage_per_ha=_fmt_kg(per_stage),
            batch_total=_fmt_kg(batch_total),
        ))

        # Accumulate delivered nutrients
        for nut in delivered:
            pct = _material_pct_for(material, nut)
            delivered[nut] += rate_kg_ha * pct

    # Round delivered for display
    delivered = {k: round(v, 1) for k, v in delivered.items()}
    return parts, delivered


def _build_fertigation_concentrates(
    raw_products: list[BlendPart],
    block_area_ha: float,
) -> list[Concentrate]:
    """Split raw products into Part A and Part B concentrates."""
    part_a_products = [p for p in raw_products if p.stream == "A"]
    part_b_products = [p for p in raw_products if p.stream == "B"]

    concs: list[Concentrate] = []
    if part_a_products:
        names = " + ".join(p.product for p in part_a_products)
        dry_weight = _sum_batch_totals(part_a_products)
        concs.append(Concentrate(
            name="Part A (Calcium stream)",
            contains=names,
            dry_weight_or_liquid=f"{dry_weight:.0f} kg dry salts",
            strength_g_per_l=300.0,
            volume_l=round(dry_weight * 1000 / 300, 0) if dry_weight > 0 else None,
            injection_notes="Inject via dedicated stock-tank line (never mix with Part B)",
        ))
    if part_b_products:
        names = " + ".join(p.product for p in part_b_products)
        dry_weight = _sum_batch_totals(part_b_products)
        concs.append(Concentrate(
            name="Part B (Sulphate + phosphate stream)",
            contains=names,
            dry_weight_or_liquid=f"{dry_weight:.0f} kg dry salts",
            strength_g_per_l=100.0,
            volume_l=round(dry_weight * 1000 / 100, 0) if dry_weight > 0 else None,
            injection_notes="Inject via second stock-tank line, parallel or sequential",
        ))
    return concs


def _sum_batch_totals(parts: list[BlendPart]) -> float:
    total = 0.0
    for p in parts:
        if p.batch_total:
            try:
                total += float(p.batch_total.split()[0])
            except (ValueError, IndexError):
                pass
    return total


def _build_application_method(method_kind: MethodKind) -> ApplicationMethod:
    """Build the correct typed ApplicationMethod discriminated-union member."""
    if _is_fertigation(method_kind):
        return FertigationMethod(
            kind=method_kind,  # type: ignore
            concentrate_strength_g_per_l=300.0,
            ec_target_ms_per_cm=(2.0, 2.5),
            ph_target=(5.5, 6.5),
            part_a_required=True,
            part_b_required=True,
        )
    if method_kind == MethodKind.FOLIAR:
        return FoliarMethod(
            spray_volume_l_per_ha=(200, 300),
            tank_mix_ph=(5.0, 6.0),
        )
    # Dry variants
    return DryBlendMethod(
        kind=method_kind,  # type: ignore
        incorporate=(method_kind == MethodKind.DRY_BAND),
    )


def _is_fertigation(method_kind: MethodKind) -> bool:
    return method_kind in (
        MethodKind.LIQUID_DRIP,
        MethodKind.LIQUID_PIVOT,
        MethodKind.LIQUID_SPRINKLER,
    )


def _analysis_label(material: dict) -> str:
    """Build the 'N 17.1%, Ca 24.4%' style label Clivia doc uses."""
    parts = []
    for code, col in [("N", "n"), ("P₂O₅", "p"), ("K₂O", "k"),
                       ("Ca", "ca"), ("Mg", "mg"), ("S", "s")]:
        v = material.get(col)
        if v and float(v) > 0.5:
            parts.append(f"{code} {float(v):.1f}%")
    return ", ".join(parts) if parts else "composition not specified"


def _fmt_kg(v: float) -> str:
    if v >= 10:
        return f"{v:.0f} kg"
    return f"{v:.1f} kg"


