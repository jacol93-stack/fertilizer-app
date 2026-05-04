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

from pydantic import BaseModel, Field, computed_field, model_validator

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

class FactorFindingOut(BaseModel):
    """One reasoner finding exposed on the artifact for UI rendering.

    Mirrors `soil_factor_reasoner.SoilFactorFinding` minus internal
    plumbing (source_id/section/tier are kept for citation but the rest
    is what the visual needs to draw a labelled status row).
    """
    kind: str  # 'antagonism' | 'toxicity' | 'deficiency' | 'balance' | 'info'
    severity: str  # 'info' | 'watch' | 'warn' | 'critical'
    parameter: str  # e.g. 'Ca:Mg', 'Al_saturation_pct', 'P:Zn'
    value: float
    threshold: Optional[float] = None
    message: str
    recommended_action: Optional[str] = None
    source_id: Optional[str] = None
    source_section: Optional[str] = None
    tier: Optional[int] = None


class NutrientStatusEntry(BaseModel):
    """One row in the per-block 'nutrients vs ideal' visual.

    Range bars need (value, optimal_low, optimal_high) to draw the
    shaded band + position the marker. Status is pre-computed server-
    side so the UI doesn't re-derive thresholds.
    """
    parameter: str  # e.g. 'P_Mehlich3', 'K', 'pH_H2O'
    nutrient_label: str  # 'Phosphorus (P)'
    value: float
    optimal_low: float
    optimal_high: float
    unit: Optional[str] = None  # 'mg/kg', '%', etc.
    status: str  # 'low' | 'ok' | 'high'
    # Display-only chart bounds so the bar doesn't span [0, 1000]. Pulled
    # from sufficiency thresholds (display_min/display_max) when set,
    # otherwise the renderer falls back to a sensible auto-bound.
    chart_min: Optional[float] = None
    chart_max: Optional[float] = None


class RatioInterpretationOut(BaseModel):
    """One row in the per-block 'ratio-by-ratio' interpretation table.

    The interpretation goes one level deeper than `FactorFindingOut`:
    instead of only firing when a threshold is breached, every relevant
    ratio gets a row even when in-band — so the report tells the
    agronomist what the ratio MEANS, not just whether it breaks rules.

    Drives both the soil-report's expanded "Cation Balance — what does
    it cause?" section and the programme builder's per-block analysis.
    """
    name: str  # 'Ca:Mg', 'K base saturation', etc.
    value: Optional[float] = None
    ideal_low: Optional[float] = None
    ideal_high: Optional[float] = None
    unit: str  # 'ratio' | '%'
    state: str  # 'unknown' | 'low' | 'in_range' | 'high'
    severity: str  # 'info' | 'watch' | 'warn' | 'critical'
    what_it_measures: str
    direct_effect: str
    bound_nutrients: list[str] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    source_citation: Optional[str] = None


class RatioHolisticSummaryOut(BaseModel):
    """2-3 sentence collapse of all ratio interpretations + nutrients-at-risk.

    Designed for the renderer's 'Cation Balance — Summary' callout block.
    `nutrients_at_risk` also feeds the future product selector's filter
    for 'must include foliar X' constraints when bound-nutrient
    supplementation is required.
    """
    summary: str
    key_concerns: list[str] = Field(default_factory=list)
    nutrients_at_risk: list[str] = Field(default_factory=list)


class CropNote(BaseModel):
    """A qualitative agronomic note attached to a block, surfaced in the
    new-direction report (no blend prescription) so the agronomist sees
    the crop-specific behavioural rules without having to remember them.

    Sourced from `crop_calc_flags` + crop-specific knowledge. The
    product selector consumes the same notes as hard filters (e.g.
    `kind='no_chloride_fertilisers'` → drop KCl/MOP from candidates).
    """
    kind: str
    """Programmatic key: 'no_chloride_fertilisers' | 'sulfur_critical' |
    'acid_intolerant' | 'chloride_sensitive' | 'photoperiod_sensitive' |
    'high_ca_demand_for_quality' | 'n_protein_cap' | 'low_K_for_quality',
    etc."""
    headline: str
    """One-line summary suitable for a callout: 'Kiwi is acutely Cl-sensitive.'"""
    detail: str
    """1-3 sentence explanation including operational implication."""
    severity: str = "info"  # 'info' | 'watch' | 'warn'
    source_citation: Optional[str] = None


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

    # Structured ratio findings — the engine's "Ca:Mg above ideal" /
    # "P:Zn antagonism" verdicts with severity + threshold context. Lets
    # the UI render coloured ratio pills tied to citations rather than
    # re-classifying the bare numbers.
    factor_findings: list[FactorFindingOut] = Field(default_factory=list)

    # Per-parameter optimal-band data driving the 'nutrients vs ideal'
    # range-bar visual. One entry per surfacable soil parameter (only
    # those with sufficiency thresholds in the catalog appear here).
    nutrient_status: list[NutrientStatusEntry] = Field(default_factory=list)

    # Smart ratio-by-ratio interpretation — one entry per agronomically-
    # relevant ratio or saturation parameter, with state, direct effect,
    # bound nutrients, and recommended action. Populated from
    # `ratio_interpreter.interpret_all_ratios`. Replaces the bare numeric
    # ratio rendering that the old renderer surfaced — now every ratio
    # tells the agronomist WHAT IT MEANS, not just whether it breached
    # a threshold.
    ratio_interpretations: list[RatioInterpretationOut] = Field(default_factory=list)

    # 2-3 sentence collapse of all ratio interpretations + nutrients-at-risk
    # list. Drives the renderer's 'Cation Balance — Summary' callout and
    # feeds the future product selector's 'must include foliar X' filter
    # for bound nutrients.
    ratio_summary: Optional[RatioHolisticSummaryOut] = None

    # Crop-specific qualitative notes — Cl-sensitive, S-critical,
    # acid-intolerant, high-Ca-demand, etc. Sourced from `crop_calc_flags`
    # + the canonical crop knowledge base. Drives the new-direction
    # 'Notes' renderer section AND product selector filters.
    crop_notes: list[CropNote] = Field(default_factory=list)

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


class ApplicationEvent(BaseModel):
    """One concrete application pass across the field.

    A `Blend` carries a recipe; the Blend's `applications` list enumerates
    each concrete date on which that recipe is applied. One recipe can
    serve multiple application dates — e.g. a fertigation stage that runs
    across 3 weekly events, or a dry blend split across two broadcast
    passes.

    Timing is denormalised from the month allocator's output so the
    renderer can iterate without having to cross-reference the schedule.
    """
    event_index: int  # 1..N sequential across the programme
    event_date: date
    week_from_planting: int
    # 1-of-N within the parent stage (for "applications 2 of 3" labels)
    event_of_stage_index: int = 1
    total_events_in_stage: int = 1


class Blend(BaseModel):
    """One recipe applied to one block across one or more dates.

    Method-agnostic: fertigation blends have concentrates; dry blends
    have no concentrates (just the raw_products list); foliar is a
    FoliarEvent not a Blend.

    `applications` holds every date on which this recipe is applied.
    `weeks`, `events`, and `dates_label` are computed from the list.
    """
    block_id: str
    stage_number: int
    stage_name: str
    applications: list[ApplicationEvent] = Field(..., min_length=1)
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

    @model_validator(mode="before")
    @classmethod
    def _synthesize_applications_from_legacy(cls, data):
        """Backwards-compat for artifacts persisted before F3.

        Legacy Blend JSON has `weeks` / `events` / `dates_label` as real
        persisted strings/ints but no `applications` list. Synthesize a
        single-event ApplicationEvent so model_validate succeeds + the
        computed fields read back the persisted values via the
        applications list (best effort — exact dates may be approximated
        from the dates_label when present, else fall back to today).

        Once a legacy artifact is re-rendered through the F3+ engine,
        it'll be re-persisted with proper applications and this synthesis
        is a no-op.
        """
        if not isinstance(data, dict):
            return data
        apps = data.get("applications")
        if apps:  # already F3-shaped
            return data
        # Legacy shape — synthesise one ApplicationEvent.
        from datetime import date as _date_type
        legacy_events = data.get("events") or 1
        try:
            n_events = max(1, int(legacy_events))
        except (TypeError, ValueError):
            n_events = 1
        # Best-effort: place at today; the renderer will use the legacy
        # weeks / dates_label strings via the @computed_field properties
        # (because the persisted values are still in `data`, but Pydantic
        # discards them at validation time — so we lose the strings here.
        # The applications list provides a fallback for downstream code).
        synth = []
        for i in range(n_events):
            synth.append({
                "event_index": data.get("stage_number", 1) * 100 + i + 1,
                "event_date": _date_type.today().isoformat(),
                "week_from_planting": max(1, i + 1),
                "event_of_stage_index": i + 1,
                "total_events_in_stage": n_events,
            })
        # Drop the legacy persisted weeks/events/dates_label strings so
        # the @computed_field versions take effect (they read from the
        # synthesized applications list).
        data = {k: v for k, v in data.items() if k not in {"weeks", "events", "dates_label"}}
        data["applications"] = synth
        return data

    @computed_field  # type: ignore[misc]
    @property
    def events(self) -> int:
        return len(self.applications)

    @computed_field  # type: ignore[misc]
    @property
    def weeks(self) -> str:
        if not self.applications:
            return ""
        start = min(a.week_from_planting for a in self.applications)
        end = max(a.week_from_planting for a in self.applications)
        return f"Week {start}" if start == end else f"Weeks {start}-{end}"

    @computed_field  # type: ignore[misc]
    @property
    def dates_label(self) -> str:
        if not self.applications:
            return ""
        dates = sorted(a.event_date for a in self.applications)
        start = dates[0]
        end = dates[-1]
        if start == end:
            return start.strftime("%-d %b %Y")
        if start.year == end.year:
            return f"{start.strftime('%-d %b')} – {end.strftime('%-d %b %Y')}"
        return f"{start.strftime('%-d %b %Y')} – {end.strftime('%-d %b %Y')}"


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
