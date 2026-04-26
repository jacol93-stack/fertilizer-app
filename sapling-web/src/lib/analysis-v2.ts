/**
 * Client for the /api/analysis/v2 endpoint.
 *
 * Quick Analysis runs the soil + leaf interpretation pipeline (target
 * computation + soil-factor reasoning + foliar trigger detection +
 * current-stage detection) and returns a ProgrammeArtifact-shaped
 * report with empty blends/stage_schedules/shopping_list.
 *
 * The renderer is the existing `ArtifactView` component with the
 * `mode="analysis"` prop, which hides the Programme-only sections.
 *
 * No persistence — analysis is ephemeral. Underlying soil + leaf
 * records persist via the legacy /api/soil/ and /api/leaf/ endpoints.
 */
import { api } from "./api";
import type { ProgrammeArtifact } from "./types/programme-artifact";

const BASE = "/api/analysis/v2";

export interface AnalysisBlockRequest {
  block_id: string;
  block_name: string;
  block_area_ha: number;
  soil_parameters: Record<string, number>;
  leaf_values?: Record<string, number> | null;
  yield_target_per_ha?: number | null;
  /** Perennial only. Drives age-factor + density scaling. */
  tree_age?: number | null;
  pop_per_ha?: number | null;
  lab_name?: string | null;
  lab_method?: string | null;
  /** ISO yyyy-mm-dd */
  sample_date?: string | null;
  sample_id?: string | null;
}

export interface AnalysisRequest {
  crop: string;
  blocks: AnalysisBlockRequest[];
  /** ISO yyyy-mm-dd. When provided, current-stage detection runs. */
  planting_date?: string | null;
  prepared_for?: string;
  client_name?: string | null;
  farm_name?: string | null;
  season?: string | null;
  water_values?: Record<string, number> | null;
}

export interface AnalysisResponse {
  artifact: ProgrammeArtifact;
}

/** Run the interpretation pipeline. Returns the artifact. */
export async function runAnalysis(req: AnalysisRequest): Promise<AnalysisResponse> {
  return api.post<AnalysisResponse>(`${BASE}/run`, req);
}
