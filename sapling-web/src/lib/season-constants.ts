// ── Season Manager Shared Constants ───────────────────────────────────

export const PRODUCT_TYPES = [
  "pelletised",
  "liquid",
  "foliar",
  "granular",
  "suspension",
  "fertigation concentrate",
  "lime",
  "gypsum",
  "compost-manure",
  "other",
] as const;

export type ProductType = (typeof PRODUCT_TYPES)[number];

export const APPLICATION_METHODS = [
  "broadcast",
  "banded",
  "foliar spray",
  "drip/fertigation",
  "topdress",
  "incorporation",
  "other",
] as const;

// Backend method enums → human-readable labels for UI selects.
// Engine emits these raw strings (programme_engine.DRY_METHODS,
// MethodAvailability flags, accepted_methods on fields, the v2
// orchestrator's MethodKind enum). Anywhere the agronomist sees a
// method choice, render the label not the enum.
export const METHOD_LABELS: Record<string, string> = {
  // Legacy / accepted_methods enum
  broadcast: "Broadcast",
  band_place: "Band placement",
  side_dress: "Side-dressing",
  topdress: "Top-dressing",
  foliar: "Foliar spray",
  drip: "Drip / fertigation",
  fertigation: "Drip / fertigation",
  drench: "Drench",
  dry_blend: "Dry blend / broadcast",
  dry_side_dress: "Dry side-dressing",
  // v2 MethodKind enum (programme_artifact.ts)
  liquid_drip: "Liquid · drip",
  liquid_pivot: "Liquid · pivot",
  liquid_sprinkler: "Liquid · sprinkler",
  dry_broadcast: "Dry · broadcast",
  dry_band: "Dry · band placement",
  dry_fertigation: "Dry · fertigation",
  seed_treat: "Seed treatment",
};

export function methodLabel(method: string): string {
  return METHOD_LABELS[method] ?? method;
}

export const MONTH_NAMES = [
  "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  completed: "bg-blue-100 text-blue-700",
  archived: "bg-gray-100 text-gray-500",
};

export const GROUP_COLORS = [
  "bg-orange-100 text-orange-700 border-orange-300",
  "bg-blue-100 text-blue-700 border-blue-300",
  "bg-green-100 text-green-700 border-green-300",
  "bg-purple-100 text-purple-700 border-purple-300",
  "bg-amber-100 text-amber-700 border-amber-300",
];

// ── Types ─────────────────────────────────────────────────────────────

export interface Field {
  id: string;
  farm_id: string;
  name: string;
  size_ha: number | null;
  soil_type: string | null;
  crop: string | null;
  cultivar: string | null;
  crop_type: string | null;
  planting_date: string | null;
  tree_age: number | null;
  pop_per_ha: number | null;
  yield_target: number | null;
  yield_unit: string | null;
  irrigation_type: string | null;
  /** Distinct from irrigation_type — a drip block may or may not have
   * fertilizer-injection infrastructure. NULL = unknown. */
  fertigation_capable: boolean | null;
  accepted_methods: string[];
  fertigation_months: number[];
  latest_analysis_id: string | null;
  latest_analysis_composite?: {
    composition_method: string;
    replicate_count: number;
  } | null;
  gps_lat: number | null;
  gps_lng: number | null;
  created_at?: string;
}

export const IRRIGATION_TYPES = ["drip", "pivot", "micro", "flood", "none"] as const;

export interface Block {
  id?: string;
  field_id?: string | null;
  name: string;
  area_ha: number | null;
  crop: string;
  cultivar: string;
  yield_target: number | null;
  yield_unit: string;
  tree_age: number | null;
  pop_per_ha: number | null;
  soil_analysis_id: string | null;
  feeding_plan_id?: string | null;
  blend_group?: string;
  nutrient_targets?: unknown[];
  notes: string;
}

export interface ProgrammeBlend {
  id: string;
  blend_group: string;
  stage_name: string;
  application_month: number;
  blend_recipe: unknown;
  blend_nutrients: unknown;
  blend_cost_per_ton: number | null;
  sa_notation: string | null;
  rate_kg_ha: number | null;
  total_kg: number | null;
}

export interface Programme {
  id: string;
  name: string;
  season: string | null;
  status: string;
  created_at: string;
  updated_at?: string;
  client_id: string | null;
  farm_id: string | null;
  notes: string | null;
  programme_blocks?: Block[];
  blocks?: Block[];
  blends?: ProgrammeBlend[];
}

export interface ProgrammeApplication {
  id: string;
  programme_id: string;
  block_id: string;
  planned_blend_id: string | null;
  actual_date: string | null;
  actual_rate_kg_ha: number | null;
  product_name: string | null;
  product_type: string | null;
  is_sapling_product: boolean;
  method: string | null;
  weather_notes: string | null;
  notes: string | null;
  status: string;
  created_at: string;
}

export interface ProgrammeAdjustment {
  id: string;
  programme_id: string;
  block_id: string | null;
  trigger_type: string;
  trigger_id: string | null;
  trigger_data: unknown;
  adjustment_data: unknown;
  notes: string | null;
  created_at: string;
  status?: "suggested" | "approved" | "applied" | "rejected";
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  applied_at?: string | null;
  applied_by?: string | null;
}

export interface AdjustmentProposal {
  adjustment: ProgrammeAdjustment;
  affected_blends: Array<{
    id: string;
    blend_group: string | null;
    stage_name: string | null;
    application_month: number | null;
    method: string | null;
    is_past: boolean;
    is_applied: boolean;
    changed: boolean;
    old: {
      rate_kg_ha: number | null;
      nutrients: Record<string, number>;
    };
    new: {
      rate_kg_ha: number | null;
      nutrients: Record<string, number>;
    };
  }>;
  summary: {
    affected_count: number;
    unchanged_count: number;
    past_applications?: number;
    scale_factors?: Record<string, number>;
    introduced_nutrients?: string[];
    season_totals?: {
      old: Record<string, number>;
      new: Record<string, number>;
    };
    reason?: string;
    kind?: string;
  };
  proposed_foliar?: {
    target_month: number;
    deficient_elements: string[];
    excess_elements: string[];
    recommendations: unknown;
  };
}

export interface CropNorm {
  crop: string;
  yield_unit: string;
  crop_type?: string;
  [key: string]: unknown;
}

export interface SoilAnalysis {
  id: string;
  crop: string | null;
  cultivar: string | null;
  field: string | null;
  field_id: string | null;
  lab_name: string | null;
  analysis_date: string | null;
  yield_target: number | null;
  yield_unit: string | null;
  created_at: string;
  nutrient_targets: unknown[] | null;
}

export function emptyBlock(): Omit<Block, "id"> {
  return {
    name: "",
    area_ha: null,
    crop: "",
    cultivar: "",
    yield_target: null,
    yield_unit: "",
    tree_age: null,
    pop_per_ha: null,
    soil_analysis_id: null,
    notes: "",
  };
}
