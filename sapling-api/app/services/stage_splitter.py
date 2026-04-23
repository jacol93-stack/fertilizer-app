"""
Stage Splitter — Phase 2 reasoning module 5 of 10.

Apportions residual-adjusted season nutrient targets across crop stages
using crop-family stage-shape weights. Drives WHEN nutrients land during
the season, which (per Clivia doc) is "the clever bit — stage shape is
robust, absolute numbers ±15%".

Weights are published per crop family (bulb / cereal / oilseed / legume /
fruit_tree / vine / tuber / leafy_veg / fodder) with crop-specific
overrides where SA Tier-1 data exists (FERTASA 5.4.3 wheat N splits,
SASRI IS 7.2 sugarcane, etc.).

Design principles:
  * Weights sum to 1.0 per nutrient per stage set
  * Match stages by semantic name (establishment / vegetative /
    reproductive / fill / maturation) — stage-count tolerant
  * Handle crop_family fallback if crop not individually profiled
  * Return per-stage, per-nutrient kg/ha + source provenance

Stage names are normalised:
  'establishment' = planting → first true leaves / emergence
  'vegetative'    = leafy growth / tillering / stem elongation
  'reproductive'  = flowering / bulb init / stem heading / pre-bloom
  'fill'          = grain fill / fruit fill / bulb fill / pod fill
  'maturation'    = senescence / tapering → harvest
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# Crop family taxonomy
# ============================================================

# Maps canonical crop names (post-migration 070) to families
CROP_FAMILY_MAP: dict[str, str] = {
    # bulbs
    "Garlic": "bulb", "Onion": "bulb",
    # cereals (C3 + C4)
    "Wheat": "cereal", "Barley": "cereal", "Oat": "cereal", "Rye": "cereal",
    "Maize": "cereal", "Maize (dryland)": "cereal", "Maize (irrigated)": "cereal",
    "Sorghum": "cereal", "Sweetcorn": "cereal",
    # oilseeds
    "Canola": "oilseed", "Sunflower": "oilseed",
    # legumes (N-fixing)
    "Soybean": "legume", "Groundnut": "legume", "Bean (Dry)": "legume",
    "Bean (Green)": "legume", "Pea": "legume", "Pea (Green)": "legume",
    "Lentils": "legume", "Lucerne": "legume",
    # fruit-trees (deciduous + evergreen perennials)
    "Apple": "fruit_tree", "Pear": "fruit_tree", "Cherry": "fruit_tree",
    "Peach": "fruit_tree", "Nectarine": "fruit_tree", "Apricot": "fruit_tree",
    "Plum": "fruit_tree", "Persimmon": "fruit_tree", "Fig": "fruit_tree",
    "Olive": "fruit_tree", "Pomegranate": "fruit_tree",
    "Litchi": "fruit_tree", "Mango": "fruit_tree", "Guava": "fruit_tree",
    "Avocado": "fruit_tree", "Macadamia": "fruit_tree", "Pecan": "fruit_tree",
    "Citrus": "fruit_tree",
    "Citrus (Grapefruit)": "fruit_tree", "Citrus (Lemon)": "fruit_tree",
    "Citrus (Navel)": "fruit_tree", "Citrus (Soft Citrus)": "fruit_tree",
    "Citrus (Valencia)": "fruit_tree",
    # vines + cane-style
    "Wine Grape": "vine", "Table Grape": "vine", "Passion Fruit": "vine",
    "Blueberry": "bush_fruit", "Blackberry": "bush_fruit",
    "Raspberry": "bush_fruit", "Strawberry": "bush_fruit",
    # tubers
    "Potato": "tuber", "Sweet Potato": "tuber", "Cassava": "tuber",
    # leafy + cole
    "Lettuce": "leafy_veg", "Spinach": "leafy_veg", "Cabbage": "leafy_veg",
    # fruit-vegetables (annual fruit crops)
    "Tomato": "fruit_veg", "Pepper (Bell)": "fruit_veg",
    "Brinjal": "fruit_veg", "Chillies": "fruit_veg",
    "Cucumber": "fruit_veg", "Sweet Melon": "fruit_veg",
    "Watermelon": "fruit_veg", "Pumpkin": "fruit_veg",
    "Butternut": "fruit_veg", "Gem Squash": "fruit_veg",
    # root
    "Beetroot": "root", "Carrot": "root",
    # specialty perennials
    "Banana": "monocot_perennial", "Pineapple": "monocot_perennial",
    "Sugarcane": "monocot_perennial", "Asparagus": "monocot_perennial",
    # fibre + stimulant
    "Cotton": "fibre", "Tobacco": "leaf_stimulant",
    "Tobacco (Flue-cured)": "leaf_stimulant", "Tobacco (Burley)": "leaf_stimulant",
    "Tobacco (Dark air-cured)": "leaf_stimulant",
    "Tobacco (Light air-cured)": "leaf_stimulant",
    "Coffee": "leaf_stimulant", "Tea": "leaf_stimulant",
    # specialty SA crops
    "Rooibos": "specialty_sa", "Honeybush": "specialty_sa",
}


def get_family(crop: str) -> str:
    """Resolve crop → family. Unknown crops default to 'cereal' (broad average).

    Tolerates leading/trailing whitespace. Case-sensitive (matches
    crop_requirements canonical).
    """
    return CROP_FAMILY_MAP.get(crop.strip(), "cereal")


# ============================================================
# Stage names (normalised 5-stage template)
# ============================================================

NORMALISED_STAGES = ["establishment", "vegetative", "reproductive", "fill", "maturation"]


# ============================================================
# Family stage-shape templates
# ============================================================
# Fractions of season total per nutrient per stage.
# Each list sums to 1.0 (within rounding).
#
# Sources:
#   * bulb — per Clivia reference workflow + FERTASA 5.6.1 general
#     vegetables prose. Tier 6 implementer convention (no FERTASA
#     stage-split table for bulb crops).
#   * cereal — FERTASA 5.4.3 wheat Table 5.4.3.3.5 N-splitting
#     (planting-to-tillering / early-tillering / late-tillering /
#     flag-leaf-to-flowering); generalised to C3+C4 cereals.
#     Tier 2 — derived from FERTASA wheat table + standard cereal
#     physiology.
#   * oilseed — Canola FERTASA 5.5.1 prose + international canola
#     research. S peaks at bolting-flowering. Tier 3.
#   * legume — FERTASA 5.5.5 soya + Foth-Ellis legume N-fixation curve.
#     Low early N (inoculation), peak P at flowering-pod set. Tier 3.
#   * fruit_tree — deciduous cycle: pre-bloom / bloom / fruit set /
#     fruit dev / post-harvest (budbuild). SAMAC for mac, FERTASA 5.7
#     prose. Tier 3.
#   * vine — SAJEV Conradie grape curve + FERTASA 5.8 prose. Tier 2.
#   * bush_fruit — MSU E2011 + Tier 6 SA adaptation.
#   * tuber — FERTASA 5.6.2 potato tuber-initiation/fill K dominance +
#     Cornell potato. Tier 2.
#   * leafy_veg — Starke Ayres commercial guide + FERTASA 5.6.1.
#     Leaf N 50-70% of season during rapid growth. Tier 3.
#   * fruit_veg — Hort Innovation tomato + FERTASA 5.6.4 prose. Tier 3.
#   * root — similar to tuber but with earlier K peak.
#   * monocot_perennial — SASRI sugarcane IS 7.2 + banana Turner. Tier 1
#     for sugarcane; Tier 3 others.
#   * fibre — FERTASA 5.9 cotton boll-fill K surge. Tier 1.
#   * leaf_stimulant — FERTASA 5.11 tobacco + general leaf-stimulant
#     tea/coffee research. Tier 2.
#   * specialty_sa — SARC rooibos/honeybush minimal external fert.
#     Tier 1.

@dataclass(frozen=True)
class StageShape:
    """Fractions per nutrient per stage for a crop family."""
    N: list[float]
    P: list[float]
    K: list[float]
    Ca: list[float]
    Mg: list[float]
    S: list[float]
    # provenance
    source_id: str
    source_section: str
    tier: int


FAMILY_STAGE_SHAPES: dict[str, StageShape] = {
    # Stages:                establish  vegetative  reproductive  fill  maturation
    "bulb": StageShape(
        N=[0.15, 0.30, 0.30, 0.20, 0.05],
        P=[0.20, 0.25, 0.25, 0.25, 0.05],
        K=[0.10, 0.20, 0.25, 0.35, 0.10],  # K peaks at bulb fill
        Ca=[0.15, 0.25, 0.30, 0.25, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.25, 0.05],
        S=[0.10, 0.20, 0.25, 0.35, 0.10],  # S mobile; peaks with K
        source_id="IMPLEMENTER_CONVENTION",
        source_section="Clivia reference + FERTASA 5.6.1 general veg prose",
        tier=6,
    ),
    "cereal": StageShape(
        # FERTASA 5.4.3 wheat Table 5.4.3.3.5 N-split pattern generalised
        # Planting→early till 55%; early→late till 25%; flag→flowering 20%
        N=[0.15, 0.35, 0.30, 0.15, 0.05],  # tillering N dominance
        P=[0.35, 0.30, 0.20, 0.10, 0.05],  # P front-loaded (seedling root)
        K=[0.15, 0.25, 0.25, 0.30, 0.05],  # K grain-fill dominance
        Ca=[0.20, 0.30, 0.30, 0.15, 0.05],
        Mg=[0.15, 0.30, 0.30, 0.20, 0.05],
        S=[0.20, 0.30, 0.30, 0.15, 0.05],
        source_id="FERTASA_5_4_3",
        source_section="Wheat Table 5.4.3.3.5 N splits (generalised to cereals)",
        tier=2,
    ),
    "oilseed": StageShape(
        N=[0.15, 0.30, 0.30, 0.20, 0.05],
        P=[0.25, 0.30, 0.25, 0.15, 0.05],
        K=[0.15, 0.25, 0.25, 0.30, 0.05],
        Ca=[0.20, 0.25, 0.30, 0.20, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.25, 0.05],
        S=[0.10, 0.25, 0.35, 0.25, 0.05],  # Canola S peaks bolting/flower
        source_id="FERTASA_5_5_1",
        source_section="Canola 5.5.1 prose + oilseed S curve",
        tier=3,
    ),
    "legume": StageShape(
        N=[0.30, 0.20, 0.30, 0.15, 0.05],  # Starter N only; rest N-fixation
        P=[0.25, 0.20, 0.30, 0.20, 0.05],  # P peaks at flowering/pod set
        K=[0.15, 0.25, 0.30, 0.25, 0.05],
        Ca=[0.20, 0.25, 0.30, 0.20, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.25, 0.05],
        S=[0.15, 0.25, 0.30, 0.25, 0.05],
        source_id="FERTASA_5_5_5",
        source_section="Soya 5.5.5 + legume N-fixation curve",
        tier=3,
    ),
    "fruit_tree": StageShape(
        # Pre-bloom / bloom + fruit set / fruit dev / harvest / post-harvest budbuild
        N=[0.15, 0.25, 0.35, 0.15, 0.10],
        P=[0.20, 0.25, 0.30, 0.15, 0.10],
        K=[0.15, 0.20, 0.40, 0.20, 0.05],  # Fruit fill K-dominant
        Ca=[0.20, 0.30, 0.30, 0.15, 0.05],  # Xylem-mobile only during cell div
        Mg=[0.15, 0.25, 0.30, 0.20, 0.10],
        S=[0.20, 0.25, 0.30, 0.15, 0.10],
        source_id="IMPLEMENTER_CONVENTION",
        source_section="FERTASA 5.7 prose + SAMAC + deciduous cycle standard",
        tier=3,
    ),
    "vine": StageShape(
        # Budbreak / flowering / véraison / ripening / post-harvest
        N=[0.20, 0.30, 0.25, 0.15, 0.10],
        P=[0.25, 0.30, 0.25, 0.15, 0.05],
        K=[0.10, 0.20, 0.40, 0.25, 0.05],  # K massive at véraison/ripening
        Ca=[0.20, 0.30, 0.30, 0.15, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.20, 0.10],
        S=[0.20, 0.25, 0.30, 0.20, 0.05],
        source_id="CONRADIE_SAJEV",
        source_section="Conradie vine N/K curve; FERTASA 5.8",
        tier=2,
    ),
    "bush_fruit": StageShape(
        N=[0.20, 0.30, 0.30, 0.15, 0.05],
        P=[0.25, 0.25, 0.25, 0.20, 0.05],
        K=[0.15, 0.25, 0.30, 0.25, 0.05],
        Ca=[0.20, 0.30, 0.25, 0.20, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.25, 0.05],
        S=[0.20, 0.25, 0.30, 0.20, 0.05],
        source_id="MSU_E2011",
        source_section="Blueberry production + bush-fruit generalisation",
        tier=3,
    ),
    "tuber": StageShape(
        N=[0.15, 0.30, 0.25, 0.25, 0.05],
        P=[0.20, 0.30, 0.25, 0.20, 0.05],
        K=[0.10, 0.20, 0.30, 0.35, 0.05],  # K very strong at tuber fill
        Ca=[0.20, 0.30, 0.25, 0.20, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.25, 0.05],
        S=[0.15, 0.25, 0.30, 0.25, 0.05],
        source_id="FERTASA_5_6_2",
        source_section="Potato 5.6.2 tuber-fill K dominance",
        tier=2,
    ),
    "leafy_veg": StageShape(
        N=[0.15, 0.50, 0.25, 0.10, 0.00],  # N dumps into rapid leaf growth
        P=[0.30, 0.35, 0.20, 0.15, 0.00],
        K=[0.10, 0.40, 0.30, 0.20, 0.00],
        Ca=[0.20, 0.40, 0.25, 0.15, 0.00],
        Mg=[0.15, 0.35, 0.30, 0.20, 0.00],
        S=[0.15, 0.40, 0.25, 0.20, 0.00],
        source_id="STARKE_AYRES_COMMERCIAL",
        source_section="Leafy-veg rapid-growth N/K curve; FERTASA 5.6.1",
        tier=3,
    ),
    "fruit_veg": StageShape(
        N=[0.15, 0.25, 0.25, 0.30, 0.05],
        P=[0.25, 0.25, 0.25, 0.20, 0.05],
        K=[0.10, 0.20, 0.30, 0.35, 0.05],  # Fruit fill K-dominant
        Ca=[0.15, 0.25, 0.30, 0.25, 0.05],  # Blossom-end-rot window
        Mg=[0.15, 0.25, 0.30, 0.25, 0.05],
        S=[0.15, 0.25, 0.30, 0.25, 0.05],
        source_id="FERTASA_5_6_4",
        source_section="Tomato 5.6.4 + fruit-veg generalisation",
        tier=3,
    ),
    "root": StageShape(
        N=[0.15, 0.30, 0.30, 0.20, 0.05],
        P=[0.25, 0.30, 0.25, 0.15, 0.05],
        K=[0.10, 0.25, 0.35, 0.25, 0.05],
        Ca=[0.20, 0.30, 0.25, 0.20, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.25, 0.05],
        S=[0.15, 0.25, 0.30, 0.25, 0.05],
        source_id="IMPLEMENTER_CONVENTION",
        source_section="Root-crop general; FERTASA 5.6.1 prose",
        tier=6,
    ),
    "monocot_perennial": StageShape(
        # Varies widely by crop; use generic perennial. Sugarcane, banana,
        # pineapple all have specific curves — override at crop level.
        N=[0.15, 0.30, 0.30, 0.20, 0.05],
        P=[0.25, 0.30, 0.25, 0.15, 0.05],
        K=[0.15, 0.25, 0.30, 0.25, 0.05],
        Ca=[0.20, 0.30, 0.25, 0.20, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.25, 0.05],
        S=[0.15, 0.25, 0.30, 0.25, 0.05],
        source_id="IMPLEMENTER_CONVENTION",
        source_section="Monocot perennial generic (override per crop)",
        tier=6,
    ),
    "fibre": StageShape(
        # Cotton: FERTASA 5.9 — boll-fill K surge
        N=[0.15, 0.30, 0.35, 0.15, 0.05],
        P=[0.20, 0.30, 0.25, 0.20, 0.05],
        K=[0.10, 0.20, 0.30, 0.35, 0.05],  # K very strong at boll fill
        Ca=[0.20, 0.30, 0.25, 0.20, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.25, 0.05],
        S=[0.15, 0.30, 0.30, 0.20, 0.05],
        source_id="FERTASA_5_9",
        source_section="Cotton 5.9 boll-fill K surge",
        tier=1,
    ),
    "leaf_stimulant": StageShape(
        # Tobacco: FERTASA 5.11 — mid-season N cutoff to manage leaf quality
        N=[0.25, 0.40, 0.25, 0.10, 0.00],  # N tapers hard for leaf quality
        P=[0.35, 0.30, 0.20, 0.15, 0.00],
        K=[0.15, 0.30, 0.30, 0.25, 0.00],
        Ca=[0.25, 0.35, 0.25, 0.15, 0.00],
        Mg=[0.20, 0.30, 0.30, 0.20, 0.00],
        S=[0.20, 0.30, 0.30, 0.20, 0.00],
        source_id="FERTASA_5_11",
        source_section="Tobacco 5.11 leaf-quality N cutoff",
        tier=1,
    ),
    "specialty_sa": StageShape(
        # Rooibos / Honeybush: SARC guidance — minimal external fert needed
        # Flat distribution when any is applied
        N=[0.20, 0.20, 0.20, 0.20, 0.20],
        P=[0.20, 0.20, 0.20, 0.20, 0.20],
        K=[0.20, 0.20, 0.20, 0.20, 0.20],
        Ca=[0.20, 0.20, 0.20, 0.20, 0.20],
        Mg=[0.20, 0.20, 0.20, 0.20, 0.20],
        S=[0.20, 0.20, 0.20, 0.20, 0.20],
        source_id="SARC_ROOIBOS",
        source_section="SARC minimal-fertilization guidance",
        tier=1,
    ),
}


# Crop-specific overrides (higher priority than family shape).
# Only populate with SA Tier-1 data where published; otherwise
# the family default is fine.
CROP_SPECIFIC_OVERRIDES: dict[str, StageShape] = {
    # Sugarcane (SASRI Information Sheet 7.2): N into early growth
    # then tapered aggressively to avoid delayed ripening
    "Sugarcane": StageShape(
        N=[0.25, 0.45, 0.20, 0.10, 0.00],  # SASRI: front-load N
        P=[0.60, 0.20, 0.10, 0.10, 0.00],  # Pre-plant P bulk
        K=[0.20, 0.30, 0.25, 0.20, 0.05],
        Ca=[0.30, 0.30, 0.20, 0.15, 0.05],
        Mg=[0.20, 0.30, 0.25, 0.20, 0.05],
        S=[0.20, 0.30, 0.25, 0.20, 0.05],
        source_id="SASRI_IS_7_2",
        source_section="SASRI IS 7.2 sugarcane fertilisation",
        tier=1,
    ),
    # Wheat (FERTASA 5.4.3.3.5 explicit N-splitting table)
    "Wheat": StageShape(
        N=[0.15, 0.40, 0.25, 0.15, 0.05],  # Tillering N peak per FERTASA
        P=[0.40, 0.30, 0.20, 0.05, 0.05],  # P front-loaded at planting
        K=[0.20, 0.25, 0.25, 0.25, 0.05],
        Ca=[0.20, 0.30, 0.30, 0.15, 0.05],
        Mg=[0.15, 0.30, 0.30, 0.20, 0.05],
        S=[0.20, 0.30, 0.30, 0.15, 0.05],
        source_id="FERTASA_5_4_3_3_5",
        source_section="Wheat N-splitting Table 5.4.3.3.5",
        tier=1,
    ),
    # Macadamia (SAMAC Schoeman 2021): heavy post-flowering, lighter dormant
    "Macadamia": StageShape(
        N=[0.10, 0.20, 0.30, 0.25, 0.15],  # Post-harvest budbuild significant
        P=[0.15, 0.25, 0.30, 0.20, 0.10],
        K=[0.10, 0.15, 0.40, 0.30, 0.05],
        Ca=[0.15, 0.30, 0.30, 0.20, 0.05],
        Mg=[0.15, 0.25, 0.30, 0.20, 0.10],
        S=[0.15, 0.25, 0.30, 0.20, 0.10],
        source_id="SAMAC_SCHOEMAN_2021",
        source_section="Schoeman 2021 annual N/K/Zn/B schedule",
        tier=1,
    ),
}


# ============================================================
# Main splitter
# ============================================================

@dataclass
class StageSplit:
    """One output row: stage → nutrient → kg/ha."""
    stage_number: int
    stage_name: str
    nutrients: dict[str, float] = field(default_factory=dict)
    source_id: str = ""
    source_section: str = ""
    tier: int = 6


def split_season_targets(
    crop: str,
    season_targets: dict[str, float],
    stage_count: int = 5,
    stage_names: Optional[list[str]] = None,
) -> list[StageSplit]:
    """Apportion season nutrient targets across stages.

    Args:
        crop: canonical crop name
        season_targets: {nutrient: kg/ha} e.g. {'N': 155, 'P2O5': 86, 'K2O': 173,
                        'Ca': 176, 'S': 67}. Expected nutrients: N, P/P2O5, K/K2O,
                        Ca, Mg, S. Unknown nutrients pass through as-is (flat split).
        stage_count: number of stages in the programme (3-6). Template is
                     5-stage; non-5 is re-sampled proportionally.
        stage_names: optional explicit stage names; falls back to NORMALISED_STAGES
                     truncated/padded to stage_count.

    Returns:
        list of StageSplit, one per stage. Sum across stages ≈ season_targets.
    """
    # Resolve shape: crop-specific override > family default > cereal fallback
    shape = CROP_SPECIFIC_OVERRIDES.get(crop)
    if shape is None:
        family = get_family(crop)
        shape = FAMILY_STAGE_SHAPES.get(family) or FAMILY_STAGE_SHAPES["cereal"]

    # Resolve stage names
    if stage_names is None:
        stage_names = _default_stage_names(stage_count)
    elif len(stage_names) != stage_count:
        stage_names = (stage_names + NORMALISED_STAGES[len(stage_names):])[:stage_count]

    # Re-sample the 5-stage template to stage_count
    nutrient_fractions = {
        "N": _resample(shape.N, stage_count),
        "P2O5": _resample(shape.P, stage_count),
        "P": _resample(shape.P, stage_count),
        "K2O": _resample(shape.K, stage_count),
        "K": _resample(shape.K, stage_count),
        "Ca": _resample(shape.Ca, stage_count),
        "Mg": _resample(shape.Mg, stage_count),
        "S": _resample(shape.S, stage_count),
    }

    results: list[StageSplit] = []
    for idx in range(stage_count):
        split = StageSplit(
            stage_number=idx + 1,
            stage_name=stage_names[idx] if idx < len(stage_names) else NORMALISED_STAGES[idx],
            source_id=shape.source_id,
            source_section=shape.source_section,
            tier=shape.tier,
        )
        for nutrient, total in season_targets.items():
            fractions = nutrient_fractions.get(nutrient)
            if fractions is None:
                # Unknown nutrient — flat split
                split.nutrients[nutrient] = round(total / stage_count, 2)
            else:
                split.nutrients[nutrient] = round(total * fractions[idx], 2)
        results.append(split)

    return results


# ============================================================
# Helpers
# ============================================================

def _default_stage_names(stage_count: int) -> list[str]:
    """Pick stage names for a given count, mapped from the 5-stage template."""
    if stage_count == 5:
        return list(NORMALISED_STAGES)
    if stage_count == 4:
        # collapse maturation into fill
        return ["establishment", "vegetative", "reproductive", "fill"]
    if stage_count == 3:
        return ["establishment", "vegetative+reproductive", "fill"]
    if stage_count == 6:
        return ["establishment", "vegetative", "reproductive",
                "fill", "late_fill", "maturation"]
    # fallback: pad with generic numbered stages
    return [f"stage_{i+1}" for i in range(stage_count)]


def _resample(fractions: list[float], target_count: int) -> list[float]:
    """Re-sample a fraction list to target_count. Preserves sum ≈ 1.0.

    For target_count < len(fractions): collapse adjacent stages proportionally.
    For target_count > len(fractions): split evenly across padding stages
    (additional stages taken from the last weight).
    """
    if target_count == len(fractions):
        return list(fractions)
    total = sum(fractions)
    if target_count < len(fractions):
        # Collapse by evenly aggregating
        result = []
        chunk = len(fractions) / target_count
        for i in range(target_count):
            start = int(i * chunk)
            end = int((i + 1) * chunk) if i < target_count - 1 else len(fractions)
            result.append(sum(fractions[start:end]))
        # Re-normalise to match original sum
        current_sum = sum(result)
        if current_sum > 0:
            result = [r * total / current_sum for r in result]
        return result
    # target_count > len(fractions): distribute last stage weight
    result = list(fractions)
    last_weight = result.pop()
    n_new = target_count - len(result)
    per = last_weight / n_new
    result.extend([per] * n_new)
    return result


def get_stage_shape_provenance(crop: str) -> tuple[str, str, int]:
    """Return (source_id, source_section, tier) for a crop's stage shape."""
    shape = CROP_SPECIFIC_OVERRIDES.get(crop)
    if shape is None:
        family = get_family(crop)
        shape = FAMILY_STAGE_SHAPES.get(family) or FAMILY_STAGE_SHAPES["cereal"]
    return (shape.source_id, shape.source_section, shape.tier)
