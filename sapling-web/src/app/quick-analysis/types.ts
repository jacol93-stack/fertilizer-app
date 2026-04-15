// ── Quick Analysis Types & Constants ──────────────────────────────────

export interface CropNorm {
  id: string;
  crop: string;
  yield_unit: string;
  pop_per_ha?: number;
  type?: string;
  default_yield?: number;
  is_overridden?: boolean;
  [key: string]: unknown;
}

export interface Classification {
  [param: string]: string;
}

export interface RatioResult {
  [key: string]: unknown;
  ratio_name?: string;
  Ratio?: string;
  actual?: number;
  Actual?: number;
  ideal_low?: number;
  ideal_high?: number;
  Ideal_Min?: number;
  Ideal_Max?: number;
  ideal_min?: number;
  ideal_max?: number;
  status?: string;
  Status?: string;
}

export interface NutrientTarget {
  [key: string]: unknown;
  Nutrient: string;
  Per_Unit?: number;
  per_unit?: number;
  Base_Req_kg_ha?: number;
  base_req?: number;
  Soil_Value?: number | string;
  soil_value?: number | string;
  Classification?: string;
  classification?: string;
  Factor?: number;
  factor?: number;
  Target_kg_ha?: number;
  Ratio_Adjustment_kg_ha?: number;
  Final_Target_kg_ha?: number;
  Ratio_Reasons?: string[];
  Ratio_Warnings?: string[];
}

export interface ExtractedSample {
  sample_id?: string;
  block_name?: string;
  crop?: string;
  cultivar?: string;
  values: Record<string, number>;
}

export interface SampleGroup {
  crop: string | null;
  samples: ExtractedSample[];
  averaged: Record<string, number>;
  selected: boolean;
}

// ── Constants ─────────────────────────────────────────────────────────

// Keys MUST match what the soil engine expects (soil_sufficiency.parameter + evaluate_ratios lookups)
export const SOIL_PARAMS: Record<string, string[]> = {
  pH: ["pH (H2O)", "pH (KCl)"],
  Organic: ["Org C", "CEC", "Clay"],
  Macros: ["N (total)", "P (Bray-1)", "K", "Ca", "Mg", "S"],
  Micros: ["Fe", "B", "Mn", "Zn", "Mo", "Cu", "Na"],
};

export const PARAM_LABELS: Record<string, string> = {
  "pH (H2O)": "pH (H2O)",
  "pH (KCl)": "pH (KCl)",
  "Org C": "Org C (%)",
  CEC: "CEC (cmol/kg)",
  Clay: "Clay %",
  "N (total)": "N (mg/kg)",
  "P (Bray-1)": "P Bray-1 (mg/kg)",
  K: "K (mg/kg)",
  Ca: "Ca (mg/kg)",
  Mg: "Mg (mg/kg)",
  S: "S (mg/kg)",
  Fe: "Fe (mg/kg)",
  B: "B (mg/kg)",
  Mn: "Mn (mg/kg)",
  Zn: "Zn (mg/kg)",
  Mo: "Mo (mg/kg)",
  Cu: "Cu (mg/kg)",
  Na: "Na (mg/kg)",
};

export const LEAF_ELEMENTS = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "Mn", "Zn", "Cu", "B", "Mo"];

// ── Style Helpers ─────────────────────────────────────────────────────

export function classificationColor(c: string): string {
  const lower = c.toLowerCase();
  if (lower.includes("very low")) return "bg-red-100 text-red-700";
  if (lower.includes("low")) return "bg-orange-100 text-orange-700";
  if (lower.includes("optimal") || lower.includes("adequate"))
    return "bg-green-100 text-green-700";
  if (lower.includes("very high")) return "bg-purple-100 text-purple-700";
  if (lower.includes("high")) return "bg-blue-100 text-blue-700";
  return "bg-gray-100 text-gray-700";
}

export function ratioStatusColor(s: string | undefined): string {
  if (!s) return "bg-gray-100 text-gray-700";
  const lower = s.toLowerCase();
  if (lower === "ideal" || lower === "optimal" || lower === "ok") return "bg-green-100 text-green-700";
  if (lower.includes("below") || lower === "low") return "bg-orange-100 text-orange-700";
  if (lower.includes("above") || lower === "high") return "bg-blue-100 text-blue-700";
  return "bg-gray-100 text-gray-700";
}
