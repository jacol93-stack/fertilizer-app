"use client";

/**
 * Client hook that drives a paginated list page.
 *
 * Responsibilities:
 *  1. Hold PageParams state (skip / limit / order / search / filters)
 *  2. Sync that state to the URL query string via next/navigation so deep
 *     links work and browser back/forward restores the view
 *  3. Fetch the Page<T> envelope from the API whenever params change
 *  4. Expose helpers the UI uses: setPage, setPageSize, setSearch, setFilter
 *
 * The hook is deliberately dumb — no caching, no optimistic updates. If
 * those become useful we can wrap it in SWR/React Query later. For now
 * every call is a fresh fetch.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { api } from "./api";
import {
  DEFAULT_LIMIT,
  Page,
  PageParams,
  defaultPageParams,
  paramsFromSearchParams,
  paramsToQueryString,
} from "./pagination";

export interface UsePaginationOptions {
  /** API path without query string, e.g. "/api/blends/". */
  basePath: string;
  /** Filter query-string keys the hook should read from URL and pass to API. */
  filterKeys?: string[];
  /** Override the initial limit on first mount (if URL doesn't set one). */
  initialLimit?: number;
  /** Debounce for the search input in ms (default 300). */
  searchDebounceMs?: number;
  /** Whether to read/write the browser URL. Disable for embedded lists. */
  syncUrl?: boolean;
}

export interface UsePaginationResult<T> {
  page: Page<T> | null;
  params: PageParams;
  loading: boolean;
  error: string | null;
  /** Re-run the current query (e.g. after a mutation). */
  refetch: () => void;
  setSkip: (skip: number) => void;
  setLimit: (limit: number) => void;
  setPage: (pageNumber: number) => void;
  setOrder: (order_by: string, order_desc?: boolean) => void;
  setSearch: (search: string) => void;
  setFilter: (key: string, value: string | undefined) => void;
  clearFilters: () => void;
}

export function usePagination<T>(
  options: UsePaginationOptions,
): UsePaginationResult<T> {
  const {
    basePath,
    filterKeys = [],
    initialLimit,
    searchDebounceMs = 300,
    syncUrl = true,
  } = options;

  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Derive initial params from the URL on first mount.
  const initialRef = useRef<PageParams | null>(null);
  if (initialRef.current === null) {
    const parsed = syncUrl
      ? paramsFromSearchParams(
          new URLSearchParams(searchParams?.toString() ?? ""),
          filterKeys,
        )
      : defaultPageParams();
    if (initialLimit && !searchParams?.get("limit")) parsed.limit = initialLimit;
    initialRef.current = parsed;
  }

  const [params, setParams] = useState<PageParams>(initialRef.current);
  const [page, setPage] = useState<Page<T> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Debounced search — the text field updates `searchInput` synchronously
  // but the API call only fires when the debounce settles.
  const [searchInput, setSearchInput] = useState(params.search ?? "");
  useEffect(() => {
    const t = setTimeout(() => {
      setParams((p) => (p.search === searchInput ? p : { ...p, search: searchInput || undefined, skip: 0 }));
    }, searchDebounceMs);
    return () => clearTimeout(t);
  }, [searchInput, searchDebounceMs]);

  // Sync params → URL. Skipped in non-sync mode so embedded lists don't
  // fight the host page's URL.
  useEffect(() => {
    if (!syncUrl) return;
    const qs = paramsToQueryString(params);
    const current = searchParams?.toString() ?? "";
    const target = qs.startsWith("?") ? qs.slice(1) : qs;
    if (current !== target) {
      router.replace(`${pathname}${qs}`, { scroll: false });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, syncUrl, pathname]);

  // Build the API URL: basePath + query string
  const fetchUrl = useMemo(() => `${basePath}${paramsToQueryString(params)}`, [basePath, params]);

  const [fetchToken, setFetchToken] = useState(0);
  const refetch = useCallback(() => setFetchToken((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .get<Page<T>>(fetchUrl)
      .then((res) => {
        if (cancelled) return;
        setPage(res);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [fetchUrl, fetchToken]);

  // ── Public setters ─────────────────────────────────────────────────
  const setSkip = useCallback((skip: number) => {
    setParams((p) => ({ ...p, skip: Math.max(0, skip) }));
  }, []);

  const setLimit = useCallback((limit: number) => {
    setParams((p) => ({ ...p, limit, skip: 0 }));
  }, []);

  const setPageNumber = useCallback((pageNumber: number) => {
    setParams((p) => ({ ...p, skip: Math.max(0, (pageNumber - 1) * p.limit) }));
  }, []);

  const setOrder = useCallback((order_by: string, order_desc?: boolean) => {
    setParams((p) => ({
      ...p,
      order_by,
      order_desc: order_desc ?? p.order_desc,
      skip: 0,
    }));
  }, []);

  const setSearch = useCallback((search: string) => {
    setSearchInput(search);
  }, []);

  const setFilter = useCallback((key: string, value: string | undefined) => {
    setParams((p) => {
      const nextFilters = { ...(p.filters ?? {}) };
      if (value == null || value === "") {
        delete nextFilters[key];
      } else {
        nextFilters[key] = value;
      }
      return {
        ...p,
        filters: Object.keys(nextFilters).length ? nextFilters : undefined,
        skip: 0,
      };
    });
  }, []);

  const clearFilters = useCallback(() => {
    setParams((p) => ({ ...p, filters: undefined, search: undefined, skip: 0 }));
    setSearchInput("");
  }, []);

  return {
    page,
    params: { ...params, search: searchInput || undefined },
    loading,
    error,
    refetch,
    setSkip,
    setLimit,
    setPage: setPageNumber,
    setOrder,
    setSearch,
    setFilter,
    clearFilters,
  };
}

// Re-export commonly used types so consumers import from one place.
export type { Page, PageParams };
export { DEFAULT_LIMIT };
