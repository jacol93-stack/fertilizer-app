/**
 * Client for the /api/soil-reports endpoints.
 *
 * Same lifecycle pattern as programmes-v2: build → optionally generate
 * narrative → approve to lock → download PDF. Sapling-branded soil
 * report renders against the same WeasyPrint pipeline + style.css.
 */
import { api, API_URL, ApiError, buildAuthHeaders } from "./api";
import type { NarrativeIssue, NarrativeReport } from "./programmes-v2";

const BASE = "/api/soil-reports";

export type SoilReportScope =
  | "single_block"
  | "block_with_history"
  | "multi_block";

export type SoilReportState = "draft" | "approved" | "archived";

export interface SoilReportListItem {
  id: string;
  title: string | null;
  scope_kind: SoilReportScope;
  block_count: number;
  analysis_count: number;
  state: SoilReportState;
  created_at: string;
  updated_at: string;
  farm_name: string | null;
  narrative_locked: boolean;
}

export interface SoilReportResponse {
  id: string;
  title: string | null;
  scope_kind: SoilReportScope;
  state: SoilReportState;
  block_ids: string[];
  analysis_ids: string[];
  farm_id: string | null;
  farm_name: string | null;
  report_payload: SoilReportPayload;
  created_at: string;
  updated_at: string;
  narrative_locked_at: string | null;
}

/**
 * Shape of report_payload — JSON-serialised SoilReportArtifact. Mirrors
 * `app/services/soil_report_builder.SoilReportArtifact.to_dict()`.
 */
export interface SoilReportPayload {
  header: {
    title: string;
    scope_kind: SoilReportScope;
    client_name: string | null;
    farm_name: string | null;
    generated_on: string | null;
    block_count: number;
    analysis_count: number;
    earliest_sample_date: string | null;
    latest_sample_date: string | null;
  };
  soil_snapshots: Array<Record<string, unknown>>;
  trend_reports: Array<Record<string, unknown>>;
  holistic_signals: string[];
  headline_signals: string[];
  block_ids: string[];
  analysis_ids: string[];
  decision_trace: string[];
}

export interface BuildSoilReportRequest {
  title?: string;
  block_ids: string[];
  analysis_ids?: string[];
  include_history?: boolean;
}

export async function buildSoilReport(
  req: BuildSoilReportRequest,
): Promise<SoilReportResponse> {
  return api.post<SoilReportResponse>(`${BASE}/build`, req);
}

export async function listSoilReports(params?: {
  clientId?: string;
  state?: SoilReportState;
}): Promise<SoilReportListItem[]> {
  const qs = new URLSearchParams();
  if (params?.clientId) qs.set("client_id", params.clientId);
  if (params?.state) qs.set("state", params.state);
  const query = qs.toString();
  return api.getAll<SoilReportListItem>(query ? `${BASE}?${query}` : BASE);
}

export async function getSoilReport(id: string): Promise<SoilReportResponse> {
  return api.get<SoilReportResponse>(`${BASE}/${id}`);
}

export async function transitionSoilReportState(
  id: string,
  newState: SoilReportState,
  reviewerNotes?: string,
): Promise<SoilReportResponse> {
  return api.patch<SoilReportResponse>(`${BASE}/${id}/state`, {
    new_state: newState,
    ...(reviewerNotes !== undefined ? { reviewer_notes: reviewerNotes } : {}),
  });
}

export async function archiveSoilReport(id: string): Promise<void> {
  await api.delete(`${BASE}/${id}`);
}

// ============================================================
// Narrative
// ============================================================

export interface GenerateSoilNarrativeResponse {
  soil_report_id: string;
  narrative_overrides: Record<string, unknown>;
  raw_prose: Record<string, unknown>;
  narrative_report: NarrativeReport;
  narrative_generated_at: string;
  narrative_locked_at: string | null;
}

export interface SoilNarrativeFetchResponse {
  soil_report_id: string;
  narrative_overrides: Record<string, unknown> | null;
  narrative_report: NarrativeReport | null;
  narrative_generated_at: string | null;
  narrative_locked_at: string | null;
}

export async function generateSoilReportNarrative(
  id: string,
): Promise<GenerateSoilNarrativeResponse> {
  return api.post<GenerateSoilNarrativeResponse>(
    `${BASE}/${id}/generate-narrative`,
    {},
  );
}

export async function getSoilReportNarrative(
  id: string,
): Promise<SoilNarrativeFetchResponse> {
  return api.get<SoilNarrativeFetchResponse>(`${BASE}/${id}/narrative`);
}

// Re-export the issue type so callers don't have to dual-import.
export type { NarrativeIssue, NarrativeReport };

// ============================================================
// PDF download
// ============================================================

export async function downloadSoilReportPdf(
  id: string,
  fallbackFilename = "soil-report.pdf",
): Promise<void> {
  const headers = await buildAuthHeaders();
  delete (headers as Record<string, string>)["Content-Type"];
  const res = await fetch(`${API_URL}${BASE}/${id}/render-pdf`, {
    method: "GET",
    headers,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(
      `Soil report PDF download failed (${res.status})`,
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
  const m = /filename\*?=(?:UTF-8'')?["']?([^";\n]+)["']?/i.exec(header);
  if (!m) return null;
  try {
    return decodeURIComponent(m[1].trim());
  } catch {
    return m[1].trim();
  }
}
