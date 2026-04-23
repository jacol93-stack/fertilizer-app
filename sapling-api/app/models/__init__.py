"""
Programme-engine typed model layer (Phase 1 of 2026-04-23 rebaseline).

These types define the contract between the Programme Builder (producer),
Manual-Entry UI (alternate producer), and Season Tracker + Renderer family
(consumers).

Design principles:
    1. Method first-class (liquid-drip / dry-broadcast / foliar / etc.).
       Not a flat "applications" list.
    2. Foliar contingent, not default. Triggers must positively fire.
    3. Fail transparent. Defaults registry + confidence bands + explicit
       Assumptions. No silent refuse, no silent default.
    4. Provenance to output. Every numeric carries source + tier.
    5. Re-entry states: pre-plant / mid-season / post-harvest.
    6. Variant inheritance: crop × cultivar × region × cycle.

See memory/state_of_play.md + memory/project_programme_engine_architecture.md
for the full design.
"""

from .confidence import ConfidenceBand, DataCompleteness, Tier
from .methods import (
    ApplicationMethod,
    DryBlendMethod,
    FertigationMethod,
    FoliarMethod,
    MethodAvailability,
    MethodKind,
    SeedTreatMethod,
    SoilBasalMethod,
)
from .programme_artifact import (
    Assumption,
    Blend,
    BlendPart,
    Concentrate,
    FoliarEvent,
    OutstandingItem,
    PreSeasonInput,
    PreSeasonRecommendation,
    ProgrammeArtifact,
    ProgrammeHeader,
    ProgrammeState,
    RenderHint,
    ReplanReason,
    RiskFlag,
    ShoppingListEntry,
    SoilSnapshot,
    SourceCitation,
    StageSchedule,
    StageWindow,
)
from .sources import Source, SourceRegistry
from .variants import CropVariant, VariantKey

__all__ = [
    # programme artifact
    "ProgrammeArtifact",
    "ProgrammeHeader",
    "ProgrammeState",
    "ReplanReason",
    "SoilSnapshot",
    "PreSeasonInput",
    "StageSchedule",
    "StageWindow",
    "PreSeasonRecommendation",
    "Blend",
    "BlendPart",
    "Concentrate",
    "FoliarEvent",
    "RiskFlag",
    "Assumption",
    "OutstandingItem",
    "ShoppingListEntry",
    "SourceCitation",
    "RenderHint",
    # methods
    "ApplicationMethod",
    "MethodKind",
    "FertigationMethod",
    "FoliarMethod",
    "DryBlendMethod",
    "SoilBasalMethod",
    "SeedTreatMethod",
    "MethodAvailability",
    # sources
    "Source",
    "SourceRegistry",
    # variants
    "CropVariant",
    "VariantKey",
    # quality
    "Tier",
    "ConfidenceBand",
    "DataCompleteness",
]
