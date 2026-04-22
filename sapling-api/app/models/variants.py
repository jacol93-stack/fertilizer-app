"""
Crop variant model — crop × cultivar × region × cycle produces
modified targets, stage shapes, and harvest windows.

Examples:
    - Maize (parent) → Maize (dryland), Maize (irrigated) [cycle variant]
    - Citrus (parent) → Navel, Valencia, Soft Citrus, Lemon, Grapefruit [cultivar]
    - Tobacco (parent) → Flue-cured, Burley, Dark/Light air-cured [cultivar]
    - Wheat (parent) → SA Southern FS, NW FS, Central FS, Eastern FS,
      Limpopo [region]
    - Garlic → standard SA white (Germidour) vs elephant [cultivar — latter
      needs +20% K, later harvest per Clivia doc]
    - Barley → feed barley vs malting barley [cultivar — protein cap]
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class VariantKey(BaseModel):
    """A resolved crop-variant lookup key.

    Engine modules call `resolve_variant_key(crop, cultivar?, region?,
    cycle?)` and get back a VariantKey that tells them which DB rows to
    look up (variant-first, fallback to parent).
    """

    canonical_crop: str = Field(..., description="As in crop_requirements.crop")
    parent_crop: Optional[str] = Field(None, description="If canonical_crop is a variant")
    cultivar: Optional[str] = None
    region: Optional[str] = None
    cycle: Optional[str] = Field(None, description="dryland / irrigated / annual / ratoon etc.")

    def lookup_chain(self) -> list[str]:
        """Crop names to try, in order: most specific first, parent last."""
        chain = [self.canonical_crop]
        if self.parent_crop and self.parent_crop != self.canonical_crop:
            chain.append(self.parent_crop)
        return chain


class CropVariant(BaseModel):
    """A variant entry in the crop_requirements registry.

    Mirrors the DB row after migration 070 added parent_crop.
    """

    crop: str
    type: str  # "Perennial" or "Annual" (user-facing)
    crop_type: str  # "perennial" or "annual" (schema-validated)
    parent_crop: Optional[str] = None
    yield_unit: str
    default_yield: float
    pop_per_ha: Optional[float] = None
    years_to_bearing: Optional[int] = None
    years_to_full_bearing: Optional[int] = None
