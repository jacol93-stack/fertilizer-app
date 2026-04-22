"""
Quality + confidence types.

Tier + DataCompleteness + ConfidenceBand together let the engine be honest
about input quality and output uncertainty without refusing to produce a
programme when data is incomplete.
"""
from __future__ import annotations

from enum import IntEnum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Tier(IntEnum):
    """Source tier from most authoritative to least.

    Used on every numeric recommendation + every default applied. Tier is
    propagated through engine output so the renderer can show the user
    what's handbook-published vs what's implementer convention.
    """

    SA_INDUSTRY_BODY = 1       # FERTASA / SASRI / SAMAC / SARC / DAFF
    PEER_REVIEWED_SA = 2       # ARC / SAJEV / NZAGA (for SA-applicable crops)
    INTERNATIONAL_EXT = 3      # WSU / CDFA / MSU / NCSU / ALGA / CTAHR / UF-IFAS
    COMMERCIAL_TIER_4 = 4      # commercial bulletins, supplier guides
    INFERRED_DERIVED = 5       # derived values where handbook math supports
    IMPLEMENTER_CONVENTION = 6 # heuristic / agronomist rule / fallback

    @property
    def label(self) -> str:
        return {
            1: "SA industry body",
            2: "Peer-reviewed SA",
            3: "International extension",
            4: "Commercial bulletin",
            5: "Inferred / derived",
            6: "Implementer convention",
        }[int(self)]


class DataCompleteness(BaseModel):
    """Tier of input data available to the engine.

    Drives confidence-band widths + which defaults apply + which Assumptions
    get surfaced in the output.
    """

    level: Literal["minimum", "standard", "high"]

    # Minimum viable: crop + area + rough yield + pH + texture
    has_crop_area_yield: bool = False
    has_ph_and_texture: bool = False

    # Standard: + full soil analysis
    has_full_soil_analysis: bool = False
    soil_analysis_age_months: Optional[int] = None

    # High-confidence: + leaf analysis + yield history
    has_leaf_analysis: bool = False
    leaf_analysis_age_months: Optional[int] = None
    has_yield_history: bool = False
    yield_history_seasons: int = 0

    # Method-availability completeness
    has_method_availability: bool = False

    @property
    def confidence_pct_band(self) -> tuple[float, float]:
        """Returns (low, high) pct bands for output confidence."""
        if self.level == "high":
            return (5.0, 10.0)
        if self.level == "standard":
            return (10.0, 15.0)
        return (20.0, 30.0)  # minimum


class ConfidenceBand(BaseModel):
    """Uncertainty band attached to a numeric recommendation.

    pct_low / pct_high express the ± range. Example: target = 155 kg N,
    pct_low=10, pct_high=15 → confidence range 139-178 kg N. The band
    itself carries a tier to distinguish "derived from Tier-1 rate table
    with complete soil data" (tight) from "heuristic fallback on sparse
    input" (loose).
    """

    pct_low: float = Field(..., ge=0.0, le=100.0)
    pct_high: float = Field(..., ge=0.0, le=100.0)
    tier: Tier
    driver: str = Field(..., description="What drove this band width: 'complete-tier-1-data', 'sparse-yield-default', etc.")
