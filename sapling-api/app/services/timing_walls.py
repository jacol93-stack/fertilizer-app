"""
Per-crop timing-wall rules — hard agronomic constraints that cannot
be violated by the allocator or the similarity-merge.

A TimingWall represents a prohibition: either
  - a nutrient cannot be applied in a given month range ("nutrient cutoff"),
  - or two nutrients cannot land in the same application event
    ("nutrient antagonism"), or
  - a stage must be delivered as its own isolated application regardless
    of similarity to neighbours ("isolated stage").

These are the non-negotiable rules the engine enforces no matter what
the farmer's operational windows say or what the similarity merger
would otherwise prefer. Sourced from FERTASA, SAMAC, SASRI, UF-IFAS,
WSU and other published SA/international extension literature.

If a rule here fires for a farmer-chosen month, the allocator either
shifts the affected nutrient to a compliant month or zeros it in that
month's allocation and emits a RiskFlag. Rules here are NEVER silently
violated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


Wallkind = Literal[
    "nutrient_cutoff",       # nutrient X prohibited in months [start..end]
    "nutrient_antagonism",   # nutrients X and Y cannot share an event
    "isolated_stage",        # a stage cannot merge with any neighbour
]


@dataclass
class TimingWall:
    """A single agronomic hard rule for a crop.

    Attributes:
        kind: which pattern this wall represents.
        nutrients: the nutrient(s) the rule applies to (N, P, K, Ca, Mg, S, etc.).
        forbidden_months: for 'nutrient_cutoff' — months (1-12) where the
            nutrient(s) cannot be applied.
        together_forbidden: for 'nutrient_antagonism' — pair of nutrients
            that cannot land in the same application event.
        stage_name: for 'isolated_stage' — the stage_name from the stage
            splitter that must stand alone.
        reason: short human-readable rationale.
        source_id, source_section, tier: provenance for the rule, surfaced
            in RiskFlag output when the rule fires.
    """
    kind: Wallkind
    nutrients: tuple[str, ...] = ()
    forbidden_months: tuple[int, ...] = ()
    together_forbidden: tuple[str, str] = ("", "")
    stage_name: str = ""
    reason: str = ""
    source_id: str = ""
    source_section: str = ""
    tier: int = 1


# ============================================================
# Per-crop rules
# ============================================================
# Keyed by canonical crop name. Variants (Citrus (Valencia), etc.) fall
# through to the parent if an exact key isn't found — see `walls_for_crop`.

CROP_TIMING_WALLS: dict[str, list[TimingWall]] = {
    "Macadamia": [
        TimingWall(
            kind="nutrient_cutoff",
            nutrients=("N",),
            forbidden_months=(11, 12, 1, 2),
            reason=(
                "FERTASA 5.8.1 explicit: Nov-Feb has NO applied N. "
                "Vegetative growth hampers nut growth and oil accumulation."
            ),
            source_id="FERTASA_5_8_1",
            source_section="5.8.1",
            tier=1,
        ),
    ],
    "Citrus": [
        TimingWall(
            kind="nutrient_antagonism",
            together_forbidden=("N", "K"),
            reason=(
                "FERTASA 5.7.3: N and K must not be applied in the same "
                "fertigation event — combined salinity spike stresses feeder "
                "roots. Separate by at least 2 irrigations."
            ),
            source_id="FERTASA_5_7_3",
            source_section="5.7.3",
            tier=1,
        ),
    ],
    "Apple": [
        TimingWall(
            kind="isolated_stage",
            stage_name="Cell-division window",
            nutrients=("Ca",),
            reason=(
                "WSU bitter-pit research (Cheng 2013): Ca foliar during the "
                "cell-division window is xylem-mobile only at that stage. "
                "Cannot merge with neighbouring applications."
            ),
            source_id="WSU_BITTER_PIT",
            source_section="Cheng 2013",
            tier=3,
        ),
    ],
    "Lucerne": [
        TimingWall(
            kind="isolated_stage",
            stage_name="establishment",
            nutrients=("N",),
            reason=(
                "Lucerne N at establishment is deliberately modest (<30 kg N/ha) "
                "to allow rhizobial nodulation. Cannot merge with in-season "
                "applications where N demand is higher."
            ),
            source_id="FERTASA_5_12_2",
            source_section="5.12.2",
            tier=1,
        ),
    ],
    # Avocado: cultivar-specific (Fuerte sensitive to early N causing
    # fruit drop vs. Hass tolerant). Captured per FERTASA 5.7.1 note.
    "Avocado": [
        TimingWall(
            kind="nutrient_cutoff",
            nutrients=("N",),
            forbidden_months=(6, 7),  # Fuerte pre-bloom — blocked for safety
            reason=(
                "FERTASA 5.7.1: Fuerte sensitive to early N causing fruit drop. "
                "June-July N is blocked by default; override if cultivar is Hass."
            ),
            source_id="FERTASA_5_7_1",
            source_section="5.7.1",
            tier=1,
        ),
    ],
}


def walls_for_crop(crop: str) -> list[TimingWall]:
    """Return the timing walls applicable to this crop.

    Variants fall through to parent: 'Citrus (Valencia)' picks up
    'Citrus' rules. Exact-match preferred if defined.
    """
    if crop in CROP_TIMING_WALLS:
        return CROP_TIMING_WALLS[crop]
    # Parent-variant fallback — strip " (variant)" suffix if present
    if " (" in crop and crop.endswith(")"):
        parent = crop.split(" (")[0]
        return CROP_TIMING_WALLS.get(parent, [])
    return []


# ============================================================
# Wall-check helpers — used by month_allocator + similarity_merger
# ============================================================

def nutrient_blocked_in_month(crop: str, nutrient: str, month: int) -> Optional[TimingWall]:
    """If a nutrient_cutoff wall prohibits this nutrient in this month,
    return the wall. Otherwise None."""
    for wall in walls_for_crop(crop):
        if wall.kind != "nutrient_cutoff":
            continue
        if nutrient in wall.nutrients and month in wall.forbidden_months:
            return wall
    return None


def nutrients_may_coapply(crop: str, nutrients_in_event: set[str]) -> Optional[TimingWall]:
    """If any nutrient_antagonism wall fires for this combination of
    nutrients in a single event, return the first offending wall.
    Returns None if the combination is fine."""
    nutrients_set = {n.upper() for n in nutrients_in_event}
    for wall in walls_for_crop(crop):
        if wall.kind != "nutrient_antagonism":
            continue
        a, b = wall.together_forbidden
        if a.upper() in nutrients_set and b.upper() in nutrients_set:
            return wall
    return None


def stage_must_stand_alone(crop: str, stage_name: str) -> Optional[TimingWall]:
    """If an isolated_stage wall names this stage, return it."""
    stage_lc = stage_name.lower()
    for wall in walls_for_crop(crop):
        if wall.kind != "isolated_stage":
            continue
        if wall.stage_name.lower() in stage_lc or stage_lc in wall.stage_name.lower():
            return wall
    return None
