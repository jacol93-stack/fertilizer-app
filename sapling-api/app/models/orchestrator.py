"""
Orchestrator interfaces for Programme Builder + Season Tracker.

The Programme Builder's orchestrator decides — given inputs — which
reasoning modules to run, in what order, and which output sections earn
a place in the final ProgrammeArtifact.

The Season Tracker's orchestrator is parallel but consumes an already-
activated ProgrammeArtifact + new in-season data, producing a re-plan
decision (spot-correct / bump remaining / full re-plan / advise-only).

These are Protocol definitions (PEP 544 structural typing) — concrete
implementations live in app/services/ (Phase 2 work).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Optional, Protocol

from .confidence import DataCompleteness
from .methods import MethodAvailability
from .programme_artifact import ProgrammeArtifact, ReplanReason
from .variants import VariantKey


# ============================================================
# Programme Builder orchestrator (pre-plant)
# ============================================================

class ProgrammeBuilderInputs(Protocol):
    """Structural input contract to the Programme Builder orchestrator."""

    # Client / farm
    client_name: str
    farm_name: str

    # Crop + season
    crop: str
    variant_key: VariantKey
    planting_date: date
    expected_harvest_date: Optional[date]
    yield_target_per_ha: Optional[float]

    # Blocks (one or more)
    blocks: list[Any]  # BlockInput — soil snapshot + area + pre-season inputs

    # Constraints
    method_availability: MethodAvailability
    data_completeness: DataCompleteness
    fertigation_start_week: Optional[int]  # Clivia: wk 3 per client request
    water_off_date: Optional[date]


class ProgrammeBuilderOrchestrator(ABC):
    """Produces a Programme Artifact from inputs.

    Responsibility:
        1. Decide which reasoning modules to invoke based on inputs +
           method availability + data completeness
        2. Sequence module calls correctly (targets → stage-split →
           method-select → foliar-trigger → consolidation → risk-flags)
        3. Decide which output sections earn a place (no foliar section
           if no trigger fired, no Part A/B procedure if not fertigation)
        4. Carry the decision audit trail in the artifact
        5. Populate Assumptions + OutstandingItems from defaults applied
    """

    @abstractmethod
    def build(self, inputs: ProgrammeBuilderInputs) -> ProgrammeArtifact:
        """Main entry — produce an Artifact from inputs."""
        ...


# ============================================================
# Season Tracker orchestrator (in-season)
# ============================================================

class InSeasonEvent(Protocol):
    """Something that happened since the Artifact was activated."""

    event_date: date
    event_kind: str  # 'leaf_analysis' | 'soil_analysis' | 'off_programme' | 'weather' | ...
    payload: dict[str, Any]


class ReplanDecision(Protocol):
    """What the Season Tracker decides to do given an event."""

    action: str  # 'advise_only' | 'spot_correct' | 'bump_remaining' | 'full_replan'
    reason: ReplanReason
    modified_artifact: Optional[ProgrammeArtifact]  # None for advise-only
    new_foliar_events: list[Any]  # for spot-correct
    narrative: str  # what the UI shows the agronomist


class SeasonTrackerOrchestrator(ABC):
    """Consumes an activated Artifact + in-season events, produces
    re-plan decisions.

    Responsibility:
        1. Classify events (benign / informational / corrective / re-plan)
        2. For corrective: compute spot-correction (e.g. immediate foliar)
        3. For re-plan: re-run reasoning modules over (today → harvest)
           window only, preserving already-applied history
        4. Feed forward to next-season pre-plant sizing (post-harvest mode)
    """

    @abstractmethod
    def react_to_event(
        self,
        artifact: ProgrammeArtifact,
        event: InSeasonEvent,
    ) -> ReplanDecision:
        """Entry point for mid-season decisions."""
        ...

    @abstractmethod
    def close_season(
        self,
        artifact: ProgrammeArtifact,
        actual_yield_per_ha: Optional[float],
        post_harvest_soil: Optional[Any],
        post_harvest_leaf: Optional[Any],
    ) -> dict[str, Any]:
        """Post-harvest review. Produces next-season feed-forward guidance."""
        ...
