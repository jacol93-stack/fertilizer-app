import { createClient } from "./supabase";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Impersonation state — set by admin, persisted in sessionStorage
let _impersonateUserId: string | null = null;

// Auto-load from sessionStorage on module init
if (typeof window !== "undefined") {
  try {
    const stored = sessionStorage.getItem("sapling_impersonate");
    if (stored) {
      const parsed = JSON.parse(stored);
      _impersonateUserId = parsed.id || null;
    }
  } catch {}
}

export function setImpersonateUser(userId: string | null) {
  _impersonateUserId = userId;
}

export function getImpersonateUser(): string | null {
  return _impersonateUserId;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const supabase = createClient();
  let session = (await supabase.auth.getSession()).data.session;

  // If session isn't ready yet, wait briefly for Supabase to hydrate
  if (!session?.access_token) {
    await new Promise((r) => setTimeout(r, 300));
    session = (await supabase.auth.getSession()).data.session;
  }

  if (!session?.access_token) {
    throw new Error("Not authenticated");
  }
  const headers: Record<string, string> = {
    Authorization: `Bearer ${session.access_token}`,
    "Content-Type": "application/json",
  };
  if (_impersonateUserId) {
    headers["X-Impersonate-User"] = _impersonateUserId;
  }
  return headers;
}

/**
 * Root list endpoints in FastAPI have trailing slashes (e.g. /api/clients/).
 * All other endpoints do not.
 * This set contains the paths that need a trailing slash.
 */
const TRAILING_SLASH_PATHS = new Set([
  "/api/blends",
  "/api/clients",
  "/api/soil",
  "/api/leaf",
  "/api/materials",
  "/api/feeding-plans",
  "/api/crop-norms",
  "/api/quotes",
  "/api/programmes",
]);

function normalizePath(path: string): string {
  const [base, query] = path.split("?");
  const needsSlash = TRAILING_SLASH_PATHS.has(base);
  const normalized = needsSlash && !base.endsWith("/") ? base + "/" : base;
  return query ? `${normalized}?${query}` : normalized;
}

async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
  _retry = 0
): Promise<T> {
  let headers: Record<string, string>;
  try {
    headers = await getAuthHeaders();
  } catch {
    // Session not ready yet — retry once after a delay
    if (_retry === 0) {
      await new Promise((r) => setTimeout(r, 500));
      return apiFetch<T>(path, options, 1);
    }
    throw new Error("Not authenticated");
  }
  const res = await fetch(`${API_URL}${normalizePath(path)}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  });
  // Retry once on 401 — the Supabase session may not be fully hydrated yet
  if (res.status === 401 && _retry === 0) {
    await new Promise((r) => setTimeout(r, 500));
    return apiFetch<T>(path, options, 1);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join("; ")
          : `API error ${res.status}`;
    throw new Error(message);
  }
  return res.json();
}

/**
 * For list endpoints that now return a Page<T> envelope but the caller
 * just wants the full array. Fetches with limit=500 (the backend max)
 * and returns the items. Use this in legacy sites that expected a raw
 * array; new code should use `usePagination()` from `@/lib/use-pagination`.
 *
 * If the response happens to still be a raw array (e.g. non-paginated
 * endpoint), the helper passes it through unchanged so this can be used
 * defensively.
 */
async function apiGetAll<T>(path: string): Promise<T[]> {
  const sep = path.includes("?") ? "&" : "?";
  const res = await apiFetch<T[] | { items: T[] }>(`${path}${sep}limit=500`);
  if (Array.isArray(res)) return res;
  if (res && typeof res === "object" && Array.isArray((res as { items?: T[] }).items)) {
    return (res as { items: T[] }).items;
  }
  return [];
}

export const api = {
  get: <T = unknown>(path: string) => apiFetch<T>(path),

  /** Fetches a list endpoint and unwraps the Page<T> envelope. */
  getAll: apiGetAll,

  post: <T = unknown>(path: string, body?: unknown) =>
    apiFetch<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T = unknown>(path: string, body: unknown) =>
    apiFetch<T>(path, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  put: <T = unknown>(path: string, body: unknown) =>
    apiFetch<T>(path, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  delete: <T = unknown>(path: string) =>
    apiFetch<T>(path, { method: "DELETE" }),

  getPdf: async (path: string): Promise<Blob> => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_URL}${normalizePath(path)}`, { headers });
    if (!res.ok) throw new Error(`PDF error ${res.status}`);
    return res.blob();
  },

  postPdf: async (path: string, body: unknown): Promise<Blob> => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_URL}${normalizePath(path)}`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`PDF error ${res.status}`);
    return res.blob();
  },
};
