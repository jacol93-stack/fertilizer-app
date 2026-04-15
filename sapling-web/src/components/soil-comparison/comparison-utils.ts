export interface SoilAnalysisRecord {
  id: string;
  crop: string | null;
  cultivar: string | null;
  yield_target: number | null;
  yield_unit: string | null;
  lab_name: string | null;
  analysis_date: string | null;
  total_cost_ha: number | null;
  farm_id: string | null;
  field_id: string | null;
  farm: string | null;
  field: string | null;
  soil_values: Record<string, number | string | null> | null;
  classifications: Record<string, string> | null;
  ratio_results: RatioResult[] | null;
  nutrient_targets: NutrientTarget[] | null;
  created_at: string;
}

export interface RatioResult {
  Ratio?: string;
  ratio_name?: string;
  Actual?: number;
  actual?: number;
  Ideal_Min?: number;
  ideal_min?: number;
  Ideal_Max?: number;
  ideal_max?: number;
  Status?: string;
  status?: string;
}

export interface NutrientTarget {
  Nutrient: string;
  Target_kg_ha?: number;
  Classification?: string;
  classification?: string;
}

export interface CropImpactNutrient {
  nutrient: string;
  soil_param: string;
  expected_depletion_kg_ha: number;
  value_before: number | null;
  value_after: number | null;
  actual_change: number | null;
  interpretation: string;
}

export interface CropImpact {
  available: boolean;
  reason?: string;
  crop?: string;
  crops?: Array<{ crop: string; cultivar?: string; season?: string; yield_target?: number }>;
  crops_label?: string;
  yield_target?: number;
  date_from?: string;
  date_to?: string;
  field_from?: string;
  field_to?: string;
  nutrients?: CropImpactNutrient[];
}

export interface Recommendation {
  type: "info" | "warning" | "success";
  message: string;
  parameters: string[];
}

export interface ComparisonResult {
  analyses: SoilAnalysisRecord[];
  comparison_type: "timeline" | "snapshot";
  crop_impact: CropImpact[];
  recommendations: Recommendation[];
  sufficiency_thresholds: Record<
    string,
    { very_low_max: number; low_max: number; optimal_max: number; high_max: number }
  >;
}

// Classification ordering
const CLASSIFICATION_ORDER = ["Very Low", "Low", "Optimal", "High", "Very High"];

export function classIndex(cls: string): number {
  return CLASSIFICATION_ORDER.indexOf(cls);
}

export function optimalDistance(cls: string): number {
  const idx = classIndex(cls);
  if (idx < 0) return -1;
  return Math.abs(idx - 2); // Optimal is index 2
}

export function changeDirection(
  cls1: string,
  cls2: string
): "improved" | "worsened" | "same" | "unknown" {
  const d1 = optimalDistance(cls1);
  const d2 = optimalDistance(cls2);
  if (d1 < 0 || d2 < 0) return "unknown";
  if (d2 < d1) return "improved";
  if (d2 > d1) return "worsened";
  return "same";
}

export function changeColor(direction: "improved" | "worsened" | "same" | "unknown"): string {
  switch (direction) {
    case "improved":
      return "text-green-600";
    case "worsened":
      return "text-red-600";
    case "same":
      return "text-gray-500";
    default:
      return "text-gray-400";
  }
}

export function changeBg(direction: "improved" | "worsened" | "same" | "unknown"): string {
  switch (direction) {
    case "improved":
      return "bg-green-50";
    case "worsened":
      return "bg-red-50";
    default:
      return "";
  }
}

export function classColor(cls: string): string {
  const lower = (cls || "").toLowerCase();
  if (lower === "optimal" || lower === "ideal") return "bg-green-100 text-green-700";
  if (lower.includes("very low")) return "bg-red-100 text-red-700";
  if (lower === "low") return "bg-orange-100 text-orange-700";
  if (lower.includes("very high")) return "bg-purple-100 text-purple-700";
  if (lower === "high") return "bg-blue-100 text-blue-700";
  return "bg-gray-100 text-gray-700";
}

export function daysBetween(d1: string, d2: string): number {
  const t1 = new Date(d1).getTime();
  const t2 = new Date(d2).getTime();
  return Math.round(Math.abs(t2 - t1) / (1000 * 60 * 60 * 24));
}

export function formatDate(d: string | null): string {
  if (!d) return "-";
  return new Date(d).toLocaleDateString("en-ZA", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function getRatioName(r: RatioResult): string {
  return r.Ratio || r.ratio_name || "-";
}

export function getRatioActual(r: RatioResult): number | null {
  return r.Actual ?? r.actual ?? null;
}

export function getRatioStatus(r: RatioResult): string {
  return r.Status || r.status || "";
}
