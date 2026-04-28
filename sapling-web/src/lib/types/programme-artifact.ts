/**
 * Programme Artifact — TypeScript types matching the Pydantic
 * ProgrammeArtifact + sub-types in sapling-api/app/models/.
 *
 * Keep this file in sync when backend types change. Version bump
 * (ARTIFACT_VERSION) signals a breaking change.
 */

export const ARTIFACT_VERSION = "1.0.0";

// ============================================================
// Quality / confidence
// ============================================================

export enum Tier {
  SA_INDUSTRY_BODY = 1,
  PEER_REVIEWED_SA = 2,
  INTERNATIONAL_EXT = 3,
  COMMERCIAL_TIER_4 = 4,
  INFERRED_DERIVED = 5,
  IMPLEMENTER_CONVENTION = 6,
}

export const TIER_LABEL: Record<Tier, string> = {
  [Tier.SA_INDUSTRY_BODY]: "SA industry body",
  [Tier.PEER_REVIEWED_SA]: "Peer-reviewed SA",
  [Tier.INTERNATIONAL_EXT]: "International extension",
  [Tier.COMMERCIAL_TIER_4]: "Commercial bulletin",
  [Tier.INFERRED_DERIVED]: "Inferred / derived",
  [Tier.IMPLEMENTER_CONVENTION]: "Implementer convention",
};

export type DataCompletenessLevel = "minimum" | "standard" | "high";

export interface DataCompleteness {
  level: DataCompletenessLevel;
  has_crop_area_yield: boolean;
  has_ph_and_texture: boolean;
  has_full_soil_analysis: boolean;
  soil_analysis_age_months?: number | null;
  has_leaf_analysis: boolean;
  leaf_analysis_age_months?: number | null;
  has_yield_history: boolean;
  yield_history_seasons: number;
  has_method_availability: boolean;
}

export interface ConfidenceBand {
  pct_low: number;
  pct_high: number;
  tier: Tier;
  driver: string;
}

// ============================================================
// Methods
// ============================================================

export enum MethodKind {
  LIQUID_DRIP = "liquid_drip",
  LIQUID_PIVOT = "liquid_pivot",
  LIQUID_SPRINKLER = "liquid_sprinkler",
  FOLIAR = "foliar",
  DRY_BROADCAST = "dry_broadcast",
  DRY_BAND = "dry_band",
  DRY_SIDE_DRESS = "dry_side_dress",
  DRY_FERTIGATION = "dry_fertigation",
  SEED_TREAT = "seed_treat",
  DRENCH = "drench",
}

export interface MethodAvailability {
  has_drip: boolean;
  has_pivot: boolean;
  has_sprinkler: boolean;
  has_foliar_sprayer: boolean;
  has_granular_spreader: boolean;
  has_fertigation_injectors: boolean;
  has_seed_treatment: boolean;
}

// Discriminated union (matches Pydantic Union dispatch by `kind`)
export type ApplicationMethod =
  | FertigationMethod
  | FoliarMethod
  | DryBlendMethod
  | SeedTreatMethod
  | SoilBasalMethod;

export interface FertigationMethod {
  kind: MethodKind.LIQUID_DRIP | MethodKind.LIQUID_PIVOT | MethodKind.LIQUID_SPRINKLER;
  concentrate_strength_g_per_l?: number | null;
  ec_target_ms_per_cm?: [number, number] | null;
  ph_target?: [number, number] | null;
  part_a_required: boolean;
  part_b_required: boolean;
}

export interface FoliarMethod {
  kind: MethodKind.FOLIAR;
  spray_volume_l_per_ha?: [number, number] | null;
  adjuvant?: string | null;
  tank_mix_ph?: [number, number] | null;
}

export interface DryBlendMethod {
  kind: MethodKind.DRY_BROADCAST | MethodKind.DRY_BAND | MethodKind.DRY_SIDE_DRESS;
  incorporate: boolean;
  placement_depth_cm?: number | null;
}

export interface SeedTreatMethod {
  kind: MethodKind.SEED_TREAT;
  dose_per_kg_seed_mg?: number | null;
}

export interface SoilBasalMethod {
  kind: MethodKind.DRY_BROADCAST | MethodKind.DRENCH;
  pre_plant: boolean;
}

// ============================================================
// Variants
// ============================================================

export interface VariantKey {
  canonical_crop: string;
  parent_crop?: string | null;
  cultivar?: string | null;
  region?: string | null;
  cycle?: string | null;
}

// ============================================================
// Source registry
// ============================================================

export interface SourceCitation {
  source_id: string;
  section?: string | null;
  note?: string | null;
  tier: Tier;
}

// ============================================================
// Lifecycle
// ============================================================

export enum ProgrammeState {
  DRAFT = "draft",
  APPROVED = "approved",
  ACTIVATED = "activated",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  ARCHIVED = "archived",
}

export enum ReplanReason {
  FIRST_PASS = "first_pass",
  LEAF_ANALYSIS = "leaf_analysis",
  SOIL_ANALYSIS = "soil_analysis",
  OFF_PROGRAMME_APPLICATION = "off_programme_application",
  WEATHER_DEVIATION = "weather_deviation",
  YIELD_REVISION = "yield_revision",
  CULTIVAR_CHANGE = "cultivar_change",
  MANUAL = "manual",
}

// ============================================================
// Header + inputs/state
// ============================================================

export interface ProgrammeHeader {
  artifact_version: string;
  programme_id?: string | null;
  client_name: string;
  farm_name: string;
  location?: string | null;
  prepared_for: string;
  prepared_by: string;
  prepared_date: string; // ISO date
  ref_number?: string | null;
  state: ProgrammeState;
  replan_reason: ReplanReason;
  crop: string;
  variant_key: VariantKey;
  season: string;
  planting_date: string; // ISO date
  expected_harvest_date?: string | null;
  data_completeness: DataCompleteness;
  method_availability: MethodAvailability;
}

export interface FactorFinding {
  /** 'antagonism' | 'toxicity' | 'deficiency' | 'balance' | 'info' */
  kind: string;
  /** 'info' | 'watch' | 'warn' | 'critical' */
  severity: string;
  /** Identifier the engine used — e.g. 'Ca:Mg', 'Al_saturation_pct', 'P:Zn'. */
  parameter: string;
  value: number;
  threshold?: number | null;
  message: string;
  recommended_action?: string | null;
  source_id?: string | null;
  source_section?: string | null;
  tier?: number | null;
}

export interface NutrientStatus {
  parameter: string;
  nutrient_label: string;
  value: number;
  optimal_low: number;
  optimal_high: number;
  unit?: string | null;
  /** 'low' | 'ok' | 'high' — bucket relative to the optimal band. */
  status: string;
  /** Display-only — bar minimum / maximum so the optimal band reads as
   * a proportional slice. Engine includes the actual value within
   * these bounds even if it's outside the optimal range. */
  chart_min?: number | null;
  chart_max?: number | null;
}

export interface SoilSnapshot {
  block_id: string;
  block_name: string;
  block_area_ha: number;
  lab_name?: string | null;
  lab_method?: string | null;
  sample_date?: string | null;
  sample_id?: string | null;
  sample_depth_cm?: number | null;
  parameters: Record<string, number>;
  /** Engine-computed ratios (Ca:Mg, ESP, SAR, P:Zn, C:N, Al sat, …). */
  computed_ratios?: Record<string, number>;
  /** Structured findings from the soil-factor reasoner — drives the
   * ratio status pills + 'why was this flagged' explanations. Empty
   * for legacy artifacts built before the field was added. */
  factor_findings?: FactorFinding[];
  /** Per-parameter optimal-band data driving the 'value vs ideal'
   * visual. Only emitted for parameters with sufficiency thresholds in
   * the catalog; ratio columns and diagnostic-only readings stay out. */
  nutrient_status?: NutrientStatus[];
  headline_signals: string[];
}

export interface PreSeasonInput {
  product: string;
  rate: string;
  contribution_per_ha: string;
  status_at_planting: string;
  applied_date?: string | null;
  effective_n_kg_per_ha: number;
  effective_p2o5_kg_per_ha: number;
  effective_k2o_kg_per_ha: number;
  effective_ca_kg_per_ha: number;
  effective_mg_kg_per_ha: number;
  effective_s_kg_per_ha: number;
}

export interface PreSeasonRecommendation {
  block_id: string;
  material: string;
  target_rate_per_ha: string;
  purpose: string;
  reason: string;
  recommended_apply_by_date: string;
  reaction_time_months: number;
  expected_status_at_planting: string;
  source: SourceCitation;
}

// ============================================================
// Programme shape
// ============================================================

export interface StageWindow {
  stage_number: number;
  stage_name: string;
  week_start: number;
  week_end: number;
  date_start: string;
  date_end: string;
  events: number;
  blend_ref?: string | null;
  foliar_at_week?: number | null;
}

export interface StageSchedule {
  block_id: string;
  planting_date: string;
  harvest_date?: string | null;
  cadence: string;
  stages: StageWindow[];
}

// ============================================================
// Blends
// ============================================================

export interface BlendPart {
  product: string;
  analysis: string;
  stream?: string | null;
  rate_per_event_per_ha?: string | null;
  rate_per_stage_per_ha?: string | null;
  batch_total?: string | null;
  source?: SourceCitation | null;
}

export interface Concentrate {
  name: string;
  contains: string;
  dry_weight_or_liquid: string;
  strength_g_per_l?: number | null;
  volume_l?: number | null;
  per_event_dose_l?: number | null;
  injection_notes?: string | null;
}

/** One concrete application pass across the field. A Blend's
 * `applications` list enumerates every date on which the recipe runs. */
export interface ApplicationEvent {
  event_index: number;
  event_date: string; // ISO date
  week_from_planting: number;
  event_of_stage_index?: number;
  total_events_in_stage?: number;
}

export interface Blend {
  block_id: string;
  stage_number: number;
  stage_name: string;
  /** Optional for backwards-compat: legacy artifacts persisted before F3
   *  do not carry this field. UI must defensive-guard via `?? []`. */
  applications?: ApplicationEvent[];
  /** Computed by backend from applications (Pydantic @computed_field).
   *  May be a real persisted string on legacy artifacts. */
  weeks: string;
  /** Computed by backend from applications (= applications.length).
   *  May be a real persisted number on legacy artifacts. */
  events: number;
  /** Computed by backend from applications (first..last event_date).
   *  May be a real persisted string on legacy artifacts. */
  dates_label: string;
  method: ApplicationMethod;
  raw_products: BlendPart[];
  concentrates: Concentrate[];
  nutrients_delivered: Record<string, number>;
  sources: SourceCitation[];
  confidence?: ConfidenceBand | null;
}

// ============================================================
// Foliar (contingent)
// ============================================================

export type FoliarTriggerKind =
  | "soil_availability_gap"
  | "stage_peak_demand"
  | "quality_window"
  | "leaf_correction"
  | "cultivar_specific";

export interface FoliarEvent {
  block_id: string;
  event_number: number;
  week: number;
  spray_date: string;
  stage_name: string;
  product: string;
  analysis: string;
  rate_per_ha: string;
  total_for_block: string;
  trigger_reason: string;
  trigger_kind: FoliarTriggerKind | string;
  source: SourceCitation;
  confidence?: ConfidenceBand | null;
}

// ============================================================
// Narrative
// ============================================================

export type Severity = "info" | "watch" | "warn" | "critical";

export interface RiskFlag {
  message: string;
  severity: Severity;
  source?: SourceCitation | null;
}

export interface Assumption {
  field: string;
  assumed_value: string;
  override_guidance?: string | null;
  source?: SourceCitation | null;
  tier: Tier;
}

export interface OutstandingItem {
  item: string;
  why_it_matters: string;
  impact_if_skipped?: string | null;
}

// ============================================================
// Shopping list + hints
// ============================================================

export interface ShoppingListEntry {
  category: "drip" | "drench" | "foliar" | "dry_blend" | string;
  product: string;
  analysis: string;
  total_per_block: Record<string, number>;
  total_overall: number;
  unit: "kg" | "L" | string;
}

export interface RenderHint {
  preferred_shape?: string | null;
  include_sections?: string[] | null;
  exclude_sections?: string[] | null;
}

// ============================================================
// Root artifact
// ============================================================

export interface ProgrammeArtifact {
  header: ProgrammeHeader;
  soil_snapshots: SoilSnapshot[];
  pre_season_inputs: PreSeasonInput[];
  pre_season_recommendations: PreSeasonRecommendation[];
  stage_schedules: StageSchedule[];
  blends: Blend[];
  foliar_events: FoliarEvent[];
  block_totals: Record<string, Record<string, number>>;
  risk_flags: RiskFlag[];
  assumptions: Assumption[];
  outstanding_items: OutstandingItem[];
  shopping_list: ShoppingListEntry[];
  sources_audit: SourceCitation[];
  overall_confidence?: ConfidenceBand | null;
  decision_trace: string[];
  created_at: string;
  updated_at: string;
  render_hint?: RenderHint | null;
}

// ============================================================
// API request/response shapes (match sapling-api/app/routers/programmes_v2.py)
// ============================================================

export interface BlockRequest {
  block_id: string;
  block_name: string;
  block_area_ha: number;
  soil_parameters: Record<string, number>;
  yield_target_per_ha: number;
  season_targets?: Record<string, number> | null;
  lab_name?: string | null;
  lab_method?: string | null;
  sample_date?: string | null;
  sample_id?: string | null;
  pre_season_inputs?: PreSeasonInput[];
  leaf_deficiencies?: Record<string, number> | null;
  /** Perennial-only density for target scaling (trees/vines per ha). */
  pop_per_ha?: number | null;
  /** Perennial-only years since planting; drives age-factor scaling
   *  against perennial_age_factors. None / annuals → factor 1.0. */
  tree_age?: number | null;
}

export interface SkippedBlockRequest {
  block_name: string;
  reason: string;
  /** Optional: lets the engine attach this block to an existing cluster
   * using the cluster's averaged recipe + targets. Requires block_id +
   * block_area_ha to be set so the engine can scale per-block rates. */
  block_id?: string | null;
  block_area_ha?: number | null;
  attach_to_cluster?: string | null;
}

export interface BuildProgrammeRequest {
  client_name: string;
  farm_name: string;
  prepared_for: string;
  crop: string;
  planting_date: string;
  build_date?: string | null;
  expected_harvest_date?: string | null;
  season?: string | null;
  location?: string | null;
  ref_number?: string | null;
  stage_count?: number;
  blocks: BlockRequest[];
  method_availability: MethodAvailability;
  high_al_soil?: boolean | null;
  wet_summer_between_apply_and_plant?: boolean;
  has_gypsum_in_plan?: boolean;
  has_irrigation_water_test?: boolean;
  has_recent_leaf_analysis?: boolean;
  planned_n_fertilizers?: string[] | null;
  subtract_harvested_removal?: boolean;
  client_id?: string | null;
  /** Blocks the caller couldn't plan (e.g. no soil analysis) — backend
   * appends one OutstandingItem per entry to the resulting artifact. */
  skipped_blocks?: SkippedBlockRequest[];
  /** NPK-ratio L1 distance threshold for clustering blocks into shared
   * recipes. Default 0.25; range 0.05–0.5. Lower = more separate blends. */
  cluster_margin?: number;
  /** block_id → cluster_id overrides from the wizard's drag-drop
   * ClusterBoard. Pinned blocks honor this exactly; unpinned fall through
   * to auto-clustering. */
  cluster_assignments?: Record<string, string>;
  /** Operational application windows the agronomist picked in the
   * Schedule step (1-12). Engine maps growth stages onto these slots
   * with timing walls enforced. Omit to let the engine pick its own
   * cadence per stage. */
  application_months?: number[];
}

export interface ReviewInfo {
  reviewer_id?: string | null;
  reviewer_email?: string | null;
  reviewer_name?: string | null;
  reviewer_notes?: string | null;
  reviewed_at?: string | null;
}

export interface BuildProgrammeResponse {
  id: string;
  state: ProgrammeState;
  artifact: ProgrammeArtifact;
  review?: ReviewInfo | null;
}

export interface ProgrammeListItem {
  id: string;
  created_at: string;
  updated_at: string;
  client_id?: string | null;
  farm_name?: string | null;
  crop: string;
  planting_date: string;
  build_date: string;
  expected_harvest_date?: string | null;
  state: ProgrammeState;
  ref_number?: string | null;
  worst_tier?: Tier | null;
  confidence_level?: DataCompletenessLevel | null;
  blocks_count: number;
  foliar_events_count: number;
  risk_flags_count: number;
}
