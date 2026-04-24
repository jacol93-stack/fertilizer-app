"""
Programme Artifact — the typed interface contract between producers
(Programme Builder engine + Manual-Entry UI) and consumers (Season
Tracker + Renderer family).

Stable, versioned, UI-populatable, engine-producible, tracker-consumable.
This is THE most important type in the Phase 1 engine contract.

Principles:
    - Every numeric field carries SourceCitation + Tier + optional
      ConfidenceBand. Never bare numbers.
    - Section inclusion is a POSITIVE decision. Sections present means
      engine decided "this section earns a place" based on inputs.
      Sections absent means a rule didn't fire. Absence is meaningful.
    - Versioned: bump ARTIFACT_VERSION when breaking changes happen.
    - Re-entry aware: carries its own ProgrammeState + ReplanReason so
      Season Tracker can distinguish first-pass from nth-revision.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .confidence import ConfidenceBand, DataCompleteness, Tier
from .methods import ApplicationMethod, MethodAvailability, MethodKind
from .variants import VariantKey


ARTIFACT_VERSION = "1.0.0"


# ============================================================
# Lifecycle state
# ============================================================

class ProgrammeState(str, Enum):
    """Programme Artifact lifecycle.

    Transitions:
        draft → approved → activated → in_progress → completed
                        ↓
                      archived (user-initiated at any post-draft state)
    """
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVATED = "activated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ReplanReason(str, Enum):
    """Why a re-plan was triggered (when state transitions back from
    in_progress). Populates the re-plan orchestrator's decision context."""
    FIRST_PASS = "first_pass"
    LEAF_ANALYSIS = "leaf_analysis"
    SOIL_ANALYSIS = "soil_analysis"
    OFF_PROGRAMME_APPLICATION = "off_programme_application"
    WEATHER_DEVIATION = "weather_deviation"
    YIELD_REVISION = "yield_revision"
    CULTIVAR_CHANGE = "cultivar_change"
    MANUAL = "manual"


# ============================================================
# Sources + citations
# ============================================================

class SourceCitation(BaseModel):
    """Lightweight citation embedded on every numeric field.

    Resolves against the SourceRegistry at render-time to produce the
    full reference. Stored inline so the artifact remains self-describing
    even if the registry changes.
    """
    source_id: str = Field(..., description="FK into SourceRegistry")
    section: Optional[str] = None
    note: Optional[str] = None
    tier: Tier


# ============================================================
# Programme header
# ============================================================

class ProgrammeHeader(BaseModel):
    """Customer / farm / crop / season meta."""
    artifact_version: str = ARTIFACT_VERSION
    programme_id: Optional[str] = None  # set when persisted
    client_name: str
    farm_name: str
    location: Optional[str] = None  # e.g. "Klein Overberg · Ngodwana, Mpumalanga"
    prepared_for: str
    prepared_by: str = "Sapling Fertilizer"
    prepared_date: date
    ref_number: Optional[str] = None  # e.g. WJ60421

    state: ProgrammeState = ProgrammeState.DRAFT
    replan_reason: ReplanReason = ReplanReason.FIRST_PASS

    crop: str  # canonical name in crop_requirements
    variant_key: VariantKey
    season: str  # e.g. "Autumn 2026"
    planting_date: date
    expected_harvest_date: Optional[date] = None

    data_completeness: DataCompleteness
    method_availability: MethodAvailability


# ============================================================
# Inputs / state
# ============================================================

class SoilSnapshot(BaseModel):
    """Per-block soil analysis snapshot with status-vs-target flags.

    The renderer produces the side-by-side table seen in Clivia §02.
    Status is a computed field (critical / low / ok / high / severe /
    target-not-set) — not stored bare, derived from the value + target
    at render time.
    """
    block_id: str
    block_name: str  # e.g. "Land A"
    block_area_ha: float

    lab_name: Optional[str] = None
    lab_method: Optional[str] = None  # Mehlich-3, Bray-1, Olsen, Truog, etc.
    sample_date: Optional[date] = None
    sample_id: Optional[str] = None
    sample_depth_cm: Optional[float] = 15.0

    # Raw parameter → value. Units come from the lab method + parameter name.
    parameters: dict[str, float] = Field(
        default_factory=dict,
        description="e.g. {'pH_H2O': 5.38, 'CEC': 13.14, 'P_Mehlich3': 2, 'K': 227, ...}"
    )

    # Computed ratios + derived metrics from SoilFactorReasoner.
    # Populated by the orchestrator from `SoilFactorReport.computed`.
    # Keys: 'Ca:Mg', '(Ca+Mg):K', 'SAR', 'soil_ESP_pct', 'P:Zn', 'Ca:B',
    # 'C:N', 'Al_saturation_pct', 'water_SAR', 'water_RSC_meq', etc.
    # Surfaced in the renderer's Ratios section.
    computed_ratios: dict[str, float] = Field(default_factory=dict)

    # "Three loudest signals" — agronomist narrative, engine-derived
    headline_signals: list[str] = Field(default_factory=list)


class PreSeasonInput(BaseModel):
    """Something already applied before the programme starts.

    Clivia example: Feb 2026 lime + Metabophos + Rescue. Engine subtracts
    residual contribution from season targets.
    """
    product: str
    rate: str  # e.g. "1 500 kg/ha"
    contribution_per_ha: str  # e.g. "~570 kg Ca + neutralising capacity"
    status_at_planting: str  # e.g. "50-70% reacted; pH lifted ~5.5-5.7"
    applied_date: Optional[date] = None
    # Engine-computed effective nutrient contribution at planting
    # (after reaction state + soil fixation)
    effective_n_kg_per_ha: float = 0.0
    effective_p2o5_kg_per_ha: float = 0.0
    effective_k2o_kg_per_ha: float = 0.0
    effective_ca_kg_per_ha: float = 0.0
    effective_mg_kg_per_ha: float = 0.0
    effective_s_kg_per_ha: float = 0.0


class PreSeasonRecommendation(BaseModel):
    """Engine recommendation for soil-improvement actions BEFORE planting.

    Fired when the programme is built far enough ahead of the planting
    date that there's lead time for slow-reacting soil amendments (lime,
    gypsum, P-rock, OM amendments) to do their work. Different from
    PreSeasonInput — that's already-applied; this is to-be-applied.

    Engine produces these in Mode A. If build_date is too close to
    planting (Mode C), engine produces RiskFlags + OutstandingItems
    instead, noting what could have been done with more lead time.
    """
    block_id: str
    material: str  # canonical materials.material name
    target_rate_per_ha: str  # e.g. "2 t/ha"
    purpose: str  # from materials.soil_improvement_purpose
    reason: str  # why this is recommended (which finding it addresses)
    recommended_apply_by_date: date  # latest date to apply for full reaction by planting
    reaction_time_months: float  # min reaction time at planting from today
    expected_status_at_planting: str  # e.g. "50-70% reacted; pH lifted ~0.3 units"
    source: SourceCitation


# ============================================================
# Programme shape (per block)
# ============================================================

class StageWindow(BaseModel):
    """One row in the 'programme shape at a glance' table."""
    stage_number: int  # 0 = planting / drench, 1..N = seasonal stages
    stage_name: str  # "Establishment + Veg I", "Bulb Initiation"
    week_start: int  # from planting date (1-indexed)
    week_end: int
    date_start: date
    date_end: date
    events: int  # how many irrigation/application events fall in this window
    blend_ref: Optional[str] = None  # "Blend 1"
    foliar_at_week: Optional[int] = None  # e.g. 6 = Foliar #1 at wk 6


class StageSchedule(BaseModel):
    """Per-block stage schedule (the timeline spine of the programme)."""
    block_id: str
    planting_date: date
    harvest_date: Optional[date] = None
    cadence: str = "weekly"  # weekly / twice-weekly / monthly
    stages: list[StageWindow]


# ============================================================
# Blends (method-agnostic representation; renderer branches)
# ============================================================

class BlendPart(BaseModel):
    """Raw-product line in a blend card.

    For fertigation blends this is one product in Part A or Part B.
    For dry blends this is one granular component. For foliar, one
    tank-mixed product.
    """
    product: str
    analysis: str  # e.g. "N 17.1%, Ca 24.4%"
    stream: Optional[str] = None  # "A" or "B" for fertigation; None for dry
    rate_per_event_per_ha: Optional[str] = None  # "42 kg"
    rate_per_stage_per_ha: Optional[str] = None  # "210 kg"
    batch_total: Optional[str] = None  # "233 kg"
    source: Optional[SourceCitation] = None


class Concentrate(BaseModel):
    """Manufactured fertigation concentrate (Part A or Part B)."""
    name: str  # "Part A (Calcium stream)"
    contains: str  # "Ca Nitrate"
    dry_weight_or_liquid: str  # "233 kg dry salts"
    strength_g_per_l: Optional[float] = 300.0
    volume_l: Optional[float] = None
    per_event_dose_l: Optional[float] = None  # injection dose per weekly event
    injection_notes: Optional[str] = None


class Blend(BaseModel):
    """One blend for one stage for one block.

    Method-agnostic: fertigation blends have concentrates; dry blends
    have no concentrates (just the raw_products list); foliar is a
    FoliarEvent not a Blend.
    """
    block_id: str
    stage_number: int
    stage_name: str
    weeks: str  # "Weeks 3-7"
    events: int
    dates_label: str  # "13 May - 16 Jun 2026"
    method: ApplicationMethod  # dispatches rendering

    raw_products: list[BlendPart]
    concentrates: list[Concentrate] = Field(default_factory=list)  # populated for fertigation only

    # What this stage delivers per ha
    nutrients_delivered: dict[str, float] = Field(
        default_factory=dict,
        description="e.g. {'N': 35.9, 'P2O5': 28.5, 'K2O': 33.7, 'Ca': 51.2, 'S': 5.4}"
    )
    sources: list[SourceCitation] = Field(default_factory=list)
    confidence: Optional[ConfidenceBand] = None


# ============================================================
# Foliar (standalone — NOT a Blend; fires from triggers)
# ============================================================

class FoliarEvent(BaseModel):
    """One foliar spray event.

    Fires from a POSITIVE trigger condition. Engine's foliar module
    only produces FoliarEvents when a rule fires. Crops with no triggers
    get no foliar events — honest, not filler.
    """
    block_id: str
    event_number: int  # "#1", "#2"
    week: int  # e.g. 6
    spray_date: date
    stage_name: str
    product: str
    analysis: str
    rate_per_ha: str
    total_for_block: str
    trigger_reason: str = Field(
        ...,
        description="Why this spray fires. e.g. 'Soil Zn 1.26 mg/kg below garlic-crit 5 mg/kg, pH 5.38 locks root uptake'"
    )
    trigger_kind: str = Field(
        ...,
        description="'soil_availability_gap' | 'stage_peak_demand' | 'quality_window' | 'leaf_correction' | 'cultivar_specific'"
    )
    source: SourceCitation
    confidence: Optional[ConfidenceBand] = None


# ============================================================
# Narrative / audit
# ============================================================

class RiskFlag(BaseModel):
    """Narrative risk-flag generated from rule-based reasoning over
    soil + method + crop + history state."""
    message: str
    severity: str = Field(..., description="'info' | 'watch' | 'warn' | 'critical'")
    source: Optional[SourceCitation] = None


class Assumption(BaseModel):
    """Default / inference the engine made when data was absent.

    Always surfaced in the output. Override-friendly (user can supply
    actual value and engine re-runs). Clivia §14.1 is the exact pattern.
    """
    field: str  # e.g. "cultivar", "irrigation_water_EC"
    assumed_value: str  # "standard SA white (Egyptian White / Germidour)"
    override_guidance: Optional[str] = None  # "For elephant garlic, push harvest..."
    source: Optional[SourceCitation] = None  # if default came from a registry
    tier: Tier = Tier.IMPLEMENTER_CONVENTION


class OutstandingItem(BaseModel):
    """Action item for the agronomist — missing data, pending decisions.

    Clivia §14.2 pattern. Engine surfaces these proactively so the user
    knows what would improve the programme.
    """
    item: str
    why_it_matters: str
    impact_if_skipped: Optional[str] = None


# ============================================================
# Shopping list + render hints
# ============================================================

class ShoppingListEntry(BaseModel):
    """One row in the factory / farm shopping list."""
    category: str  # 'drip' | 'drench' | 'foliar' | 'dry_blend'
    product: str
    analysis: str
    total_per_block: dict[str, float] = Field(default_factory=dict)  # block_id → quantity
    total_overall: float
    unit: str  # 'kg' | 'L'


class RenderHint(BaseModel):
    """Optional hint to the renderer about preferred output shape.

    Not prescriptive — renderer can override. Useful for 'please produce
    the dry-blend version even though drip is available'.
    """
    preferred_shape: Optional[str] = Field(None, description="'full_programme' | 'quote_only' | 'foliar_only' | 'correction_addendum'")
    include_sections: Optional[list[str]] = None
    exclude_sections: Optional[list[str]] = None


# ============================================================
# Root artifact
# ============================================================

class ProgrammeArtifact(BaseModel):
    """The complete typed programme object.

    Produced by:
        - Programme Builder orchestrator (engine-produced)
        - Manual-Entry UI (UI-populated for agents who didn't use builder)

    Consumed by:
        - Season Tracker (in-season re-plans, activation, tracking)
        - Renderer family (multiple output shapes)
        - Comparison view (plan vs actual)

    Storage: serialised to JSONB in a new programme_artifacts table
    (planned Phase 1.5 migration).
    """
    header: ProgrammeHeader
    soil_snapshots: list[SoilSnapshot]  # per block
    pre_season_inputs: list[PreSeasonInput] = Field(default_factory=list)
    pre_season_recommendations: list["PreSeasonRecommendation"] = Field(default_factory=list)
    stage_schedules: list[StageSchedule]  # per block

    blends: list[Blend] = Field(default_factory=list)  # cross-block
    foliar_events: list[FoliarEvent] = Field(default_factory=list)  # only if triggers fired

    # Per-block nutrient-delivered summaries
    block_totals: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="e.g. {'Land A': {'N': 155, 'P2O5': 86, 'K2O': 173, 'Ca': 176, 'S': 67}}"
    )

    risk_flags: list[RiskFlag] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    outstanding_items: list[OutstandingItem] = Field(default_factory=list)

    shopping_list: list[ShoppingListEntry] = Field(default_factory=list)

    # Every source cited anywhere in the artifact — for the "Sources"
    # section of the output
    sources_audit: list[SourceCitation] = Field(default_factory=list)

    # Overall programme confidence — summarises per-nutrient bands
    overall_confidence: Optional[ConfidenceBand] = None

    # Engine's decision audit trail — every orchestrator decision logged
    decision_trace: list[str] = Field(
        default_factory=list,
        description="Each entry: 'Module X fired because Y', 'Section Z excluded because no trigger'"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Render hint
    render_hint: Optional[RenderHint] = None
