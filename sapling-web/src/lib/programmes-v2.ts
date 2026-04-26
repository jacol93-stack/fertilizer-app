/**
 * Client for the /api/programmes/v2 endpoints.
 *
 * Thin wrappers around the shared api helper; keep business logic in
 * Server Components or route handlers, not here.
 */
import { api, API_URL, ApiError, buildAuthHeaders } from "./api";
import type {
  BuildProgrammeRequest,
  BuildProgrammeResponse,
  ProgrammeListItem,
  ProgrammeState,
} from "./types/programme-artifact";

const BASE = "/api/programmes/v2";

/** Run the programme builder orchestrator + persist the artifact. */
export async function buildProgramme(
  req: BuildProgrammeRequest,
): Promise<BuildProgrammeResponse> {
  return api.post<BuildProgrammeResponse>(`${BASE}/build`, req);
}

/** Wizard helper — resolve growth stages, methods, and corrections per
 * block without touching the DB. Drives the Schedule Review step. */
export interface PreviewBlockInput {
  block_id: string;
  block_name: string;
  crop: string;
  cultivar?: string | null;
  soil_analysis_id?: string | null;
  field_id?: string | null;
  area_ha?: number | null;
  yield_target?: number | null;
  yield_unit?: string | null;
  tree_age?: number | null;
  pop_per_ha?: number | null;
}

export interface HeterogeneityWarning {
  nutrient: string;
  cv_pct: number | null;
  level: "warn" | "split";
  threshold_pct: number;
}

export interface ClusterPreview {
  cluster_id: string;
  block_ids: string[];
  block_names: string[];
  total_area_ha: number;
  weight_strategy: string;
  aggregated_targets: Record<string, number>;
  heterogeneity: {
    per_nutrient: Record<string, { cv_pct: number | null; n: number; level: string }>;
    warnings: HeterogeneityWarning[];
    any_warn: boolean;
    any_split: boolean;
    citation: string;
  };
}

export interface PreviewScheduleResponse {
  block_info: Array<Record<string, unknown>>;
  unplanable_blocks: Array<{ block_id: string; block_name: string; reason: string; crop?: string }>;
  corrections: Array<Record<string, unknown>>;
  clusters: ClusterPreview[];
  cluster_margin: number;
}

export async function previewSchedule(
  blocks: PreviewBlockInput[],
  options?: { clusterMargin?: number },
): Promise<PreviewScheduleResponse> {
  return api.post<PreviewScheduleResponse>(`${BASE}/preview-schedule`, {
    blocks,
    cluster_margin: options?.clusterMargin ?? 0.25,
  });
}

/** Fetch one programme artifact by id. */
export async function getProgramme(
  id: string,
): Promise<BuildProgrammeResponse> {
  return api.get<BuildProgrammeResponse>(`${BASE}/${id}`);
}

/** List programmes with optional filters. */
export async function listProgrammes(params?: {
  state?: ProgrammeState;
  crop?: string;
  clientId?: string;
  limit?: number;
}): Promise<ProgrammeListItem[]> {
  const qs = new URLSearchParams();
  if (params?.state) qs.set("state", params.state);
  if (params?.crop) qs.set("crop", params.crop);
  if (params?.clientId) qs.set("client_id", params.clientId);
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));
  const query = qs.toString();
  return api.get<ProgrammeListItem[]>(
    query ? `${BASE}?${query}` : BASE,
  );
}

/** Transition a programme's lifecycle state. On draft→approved the
 * optional `reviewerNotes` are persisted alongside the reviewer id. */
export async function transitionProgrammeState(
  id: string,
  newState: ProgrammeState,
  reviewerNotes?: string,
): Promise<BuildProgrammeResponse> {
  return api.patch<BuildProgrammeResponse>(
    `${BASE}/${id}/state`,
    {
      new_state: newState,
      ...(reviewerNotes !== undefined ? { reviewer_notes: reviewerNotes } : {}),
    },
  );
}

/** Archive (soft delete) a programme. */
export async function archiveProgramme(id: string): Promise<void> {
  await api.delete(`${BASE}/${id}`);
}

/**
 * Download the Sapling-branded styled PDF for a programme. Triggers a
 * browser download via a transient anchor click; the filename suggested
 * by the server's Content-Disposition header is used by default, with
 * an optional `fallbackFilename` if the header parse fails.
 */
export async function downloadProgrammePdf(
  id: string,
  fallbackFilename = "programme.pdf",
): Promise<void> {
  const headers = await buildAuthHeaders();
  // The server returns application/pdf; remove the Content-Type header
  // that buildAuthHeaders sets (it's for JSON requests).
  delete (headers as Record<string, string>)["Content-Type"];

  const res = await fetch(`${API_URL}${BASE}/${id}/render-pdf`, {
    method: "GET",
    headers,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(
      `PDF download failed (${res.status})`,
      res.status,
      body,
    );
  }

  const filename = parseFilenameFromHeader(
    res.headers.get("content-disposition"),
  ) ?? fallbackFilename;

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function parseFilenameFromHeader(header: string | null): string | null {
  if (!header) return null;
  // Content-Disposition: attachment; filename="Sapling Programme.pdf"
  const m = /filename\*?=(?:UTF-8'')?["']?([^";\n]+)["']?/i.exec(header);
  if (!m) return null;
  try {
    return decodeURIComponent(m[1].trim());
  } catch {
    return m[1].trim();
  }
}
