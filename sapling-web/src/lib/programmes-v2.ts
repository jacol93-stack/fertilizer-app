/**
 * Client for the /api/programmes/v2 endpoints.
 *
 * Thin wrappers around the shared api helper; keep business logic in
 * Server Components or route handlers, not here.
 */
import { api } from "./api";
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
  limit?: number;
}): Promise<ProgrammeListItem[]> {
  const qs = new URLSearchParams();
  if (params?.state) qs.set("state", params.state);
  if (params?.crop) qs.set("crop", params.crop);
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
