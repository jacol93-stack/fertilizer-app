/**
 * Shared pagination types + helpers for list endpoints.
 *
 * Every FastAPI list endpoint returns a Page<T> envelope instead of a
 * raw array — see sapling-api/app/pagination.py for the backend side.
 * Use this module to talk to those endpoints consistently.
 */

export const DEFAULT_LIMIT = 20;
export const MAX_LIMIT = 500;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const;

/** Server response shape for any paginated list endpoint. */
export interface Page<T> {
  items: T[];
  total: number | null;
  skip: number;
  limit: number;
}

/** Client-side pagination state. Mirrors the query-string params the API accepts. */
export interface PageParams {
  skip: number;
  limit: number;
  order_by?: string;
  order_desc: boolean;
  /** Free-text search. Forwarded only if the backend endpoint supports `?search=...`. */
  search?: string;
  /** Extra filter params (client_id, farm_id, field_id, status, etc.). */
  filters?: Record<string, string | undefined>;
}

/** Default starting state for a paginated list. */
export function defaultPageParams(overrides: Partial<PageParams> = {}): PageParams {
  return {
    skip: 0,
    limit: DEFAULT_LIMIT,
    order_desc: true,
    ...overrides,
  };
}

/** Turn PageParams into a query string suffix (includes leading `?` if non-empty). */
export function paramsToQueryString(params: PageParams): string {
  const q = new URLSearchParams();
  if (params.skip) q.set("skip", String(params.skip));
  if (params.limit !== DEFAULT_LIMIT) q.set("limit", String(params.limit));
  if (params.order_by) q.set("order_by", params.order_by);
  if (params.order_desc === false) q.set("order_desc", "false");
  if (params.search) q.set("search", params.search);
  if (params.filters) {
    for (const [k, v] of Object.entries(params.filters)) {
      if (v != null && v !== "") q.set(k, v);
    }
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

/** Parse URL search params back into PageParams. Used on mount so deep links work. */
export function paramsFromSearchParams(
  searchParams: URLSearchParams,
  knownFilterKeys: string[] = [],
): PageParams {
  const skip = Number(searchParams.get("skip") ?? 0);
  const limit = Number(searchParams.get("limit") ?? DEFAULT_LIMIT);
  const order_by = searchParams.get("order_by") ?? undefined;
  const order_desc = searchParams.get("order_desc") !== "false";
  const search = searchParams.get("search") ?? undefined;

  const filters: Record<string, string> = {};
  for (const key of knownFilterKeys) {
    const v = searchParams.get(key);
    if (v != null && v !== "") filters[key] = v;
  }

  return {
    skip: Number.isFinite(skip) && skip >= 0 ? skip : 0,
    limit: Number.isFinite(limit) && limit > 0 && limit <= MAX_LIMIT ? limit : DEFAULT_LIMIT,
    order_by,
    order_desc,
    search,
    filters: Object.keys(filters).length ? filters : undefined,
  };
}

/** Current page number (1-indexed) for a Page. */
export function pageNumber(page: Pick<Page<unknown>, "skip" | "limit">): number {
  if (!page.limit) return 1;
  return Math.floor(page.skip / page.limit) + 1;
}

/** Total page count for a Page. */
export function pageCount(page: Page<unknown>): number {
  if (!page.total || !page.limit) return 1;
  return Math.max(1, Math.ceil(page.total / page.limit));
}

/** "Showing 1–20 of 847" label. */
export function pageLabel(page: Page<unknown>): string {
  const total = page.total ?? page.items.length;
  if (total === 0) return "No results";
  const start = page.skip + 1;
  const end = Math.min(page.skip + page.items.length, total);
  return `Showing ${start.toLocaleString()}\u2013${end.toLocaleString()} of ${total.toLocaleString()}`;
}
