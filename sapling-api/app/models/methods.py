"""
Method taxonomy — application methods are first-class, not labels.

Each method carries its own constraint set + procedure template. Engine's
method-selector module decides which method delivers which nutrient at
which stage, given farmer's available methods.

Design note: these types are discriminated unions over MethodKind. The
orchestrator + reasoning modules pattern-match on MethodKind to dispatch
method-specific logic (e.g. Part A/B packaging only applies to fertigation;
granule-compat matrix only applies to dry blend).
"""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class MethodKind(str, Enum):
    """Discriminator for the ApplicationMethod union."""

    LIQUID_DRIP = "liquid_drip"
    LIQUID_PIVOT = "liquid_pivot"
    LIQUID_SPRINKLER = "liquid_sprinkler"
    FOLIAR = "foliar"
    DRY_BROADCAST = "dry_broadcast"
    DRY_BAND = "dry_band"
    DRY_SIDE_DRESS = "dry_side_dress"
    DRY_FERTIGATION = "dry_fertigation"  # water-soluble dry dissolved then injected
    SEED_TREAT = "seed_treat"
    DRENCH = "drench"  # one-off planting drench


class FertigationMethod(BaseModel):
    """Liquid delivery via irrigation system.

    Constraints:
        - Water-solubility ceiling per product at ambient temperature
        - Part A / Part B packaging (Ca ↔ SO₄ / PO₄ incompatibility)
        - EC target in drip line: typically 2.0-2.5 mS/cm
        - pH target in drip line: typically 5.5-6.5
        - Injector flow math (L/min per part)
    """

    kind: Literal[MethodKind.LIQUID_DRIP, MethodKind.LIQUID_PIVOT, MethodKind.LIQUID_SPRINKLER]
    concentrate_strength_g_per_l: Optional[float] = Field(
        None, description="Target manufactured strength, e.g. 300 g/L Part A"
    )
    ec_target_ms_per_cm: Optional[tuple[float, float]] = None
    ph_target: Optional[tuple[float, float]] = None
    part_a_required: bool = False
    part_b_required: bool = False


class FoliarMethod(BaseModel):
    """Spray-applied micronutrient or corrective.

    Constraints:
        - Tank-mix compatibility + spray-pH rules
        - Time-of-day (avoid > 28°C, early/late only)
        - Leaf-wetness + rain-fastness (re-spray within 4h of rain)
        - Adjuvant (non-ionic wetter ~50 mL/100 L)
        - Phytotoxicity caps per element (on label, not here)
    """

    kind: Literal[MethodKind.FOLIAR] = MethodKind.FOLIAR
    spray_volume_l_per_ha: Optional[tuple[int, int]] = Field(None, description="e.g. (200, 300)")
    adjuvant: Optional[str] = "Non-ionic wetter ~50 mL/100 L"
    tank_mix_ph: Optional[tuple[float, float]] = None


class DryBlendMethod(BaseModel):
    """Dry granular fertiliser blend.

    Constraints:
        - Granule physical compatibility (AN + urea = slurry)
        - Particle-size segregation in spreader
        - Hygroscopicity / storage
        - Spreader calibration (bulk density drives rate)
        - Placement: broadcast / banded / side-dress / in-furrow
        - Incorporation requirement (till-in or surface)
    """

    kind: Literal[MethodKind.DRY_BROADCAST, MethodKind.DRY_BAND, MethodKind.DRY_SIDE_DRESS]
    incorporate: bool = False
    placement_depth_cm: Optional[float] = None


class SeedTreatMethod(BaseModel):
    """Per-seed dose — inoculants, Mo on groundnut, Zn coating.

    Constraints:
        - Per-seed dose (g/100kg seed or similar)
        - Coating compatibility
        - Inoculant live-count maintenance
    """

    kind: Literal[MethodKind.SEED_TREAT] = MethodKind.SEED_TREAT
    dose_per_kg_seed_mg: Optional[float] = None


class SoilBasalMethod(BaseModel):
    """At-planting soil application (lime, gypsum, phosphate rock).

    Usually dry but may be a drench. Differs from dry_broadcast by timing
    (pre-plant) and typical product classes (amendments, not NPK).
    """

    kind: Literal[MethodKind.DRY_BROADCAST, MethodKind.DRENCH] = MethodKind.DRY_BROADCAST
    pre_plant: bool = True


# Discriminated union. Consumers use method.kind to dispatch.
ApplicationMethod = Union[
    FertigationMethod,
    FoliarMethod,
    DryBlendMethod,
    SeedTreatMethod,
    SoilBasalMethod,
]


class MethodAvailability(BaseModel):
    """What equipment / methods the farmer can actually use.

    Drives the method-selector module's decision space. A farmer with
    drip + boom sprayer has very different options from one with only
    a granular spreader. Captured per block (might differ across blocks).
    """

    has_drip: bool = False
    has_pivot: bool = False
    has_sprinkler: bool = False
    has_foliar_sprayer: bool = False
    has_granular_spreader: bool = True  # common default
    has_fertigation_injectors: bool = False
    has_seed_treatment: bool = True  # cheap / universal

    def available_kinds(self) -> set[MethodKind]:
        kinds: set[MethodKind] = set()
        if self.has_drip:
            kinds.add(MethodKind.LIQUID_DRIP)
        if self.has_pivot:
            kinds.add(MethodKind.LIQUID_PIVOT)
        if self.has_sprinkler:
            kinds.add(MethodKind.LIQUID_SPRINKLER)
        if self.has_foliar_sprayer:
            kinds.add(MethodKind.FOLIAR)
        if self.has_granular_spreader:
            kinds.add(MethodKind.DRY_BROADCAST)
            kinds.add(MethodKind.DRY_BAND)
            kinds.add(MethodKind.DRY_SIDE_DRESS)
        if self.has_fertigation_injectors:
            kinds.add(MethodKind.DRY_FERTIGATION)
        if self.has_seed_treatment:
            kinds.add(MethodKind.SEED_TREAT)
        return kinds
