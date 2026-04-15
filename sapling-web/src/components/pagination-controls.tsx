"use client";

/**
 * Reusable pagination controls for any paginated list page.
 *
 * Connect it to a usePagination() hook like this:
 *
 *   const pag = usePagination<Thing>({ basePath: "/api/things/" });
 *   return (
 *     <>
 *       {pag.page?.items.map(...)}
 *       <PaginationControls pagination={pag} />
 *     </>
 *   );
 *
 * The component is a dumb view — all state lives in the hook.
 */

import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  PAGE_SIZE_OPTIONS,
  pageCount,
  pageLabel,
  pageNumber,
} from "@/lib/pagination";
import type { UsePaginationResult } from "@/lib/use-pagination";

interface Props<T> {
  pagination: UsePaginationResult<T>;
  /** Hide the page-size picker if the caller wants fixed sizing. */
  hidePageSize?: boolean;
  /** Compact mode — no label, just prev/next. */
  compact?: boolean;
  className?: string;
}

export function PaginationControls<T>({
  pagination,
  hidePageSize,
  compact,
  className,
}: Props<T>) {
  const { page, params, loading, setPage, setLimit } = pagination;

  // Page may be null during initial load; render minimal skeleton.
  if (!page) {
    if (loading) {
      return (
        <div className={`flex items-center justify-center py-4 ${className ?? ""}`}>
          <Loader2 className="size-4 animate-spin text-[var(--sapling-medium-grey)]" />
        </div>
      );
    }
    return null;
  }

  const total = page.total ?? page.items.length;
  const currentPage = pageNumber(page);
  const totalPages = pageCount(page);
  const atFirst = currentPage <= 1;
  const atLast = currentPage >= totalPages;

  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-4 ${className ?? ""}`}
    >
      {/* Left: label */}
      {!compact && (
        <div className="text-xs text-[var(--sapling-medium-grey)]">
          {pageLabel(page)}
        </div>
      )}

      {/* Right: controls */}
      <div className="flex items-center gap-2">
        {!hidePageSize && !compact && total > 10 && (
          <label className="flex items-center gap-1 text-xs text-[var(--sapling-medium-grey)]">
            <span className="hidden sm:inline">Per page</span>
            <select
              value={params.limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-[var(--sapling-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--sapling-orange)]/40"
              disabled={loading}
            >
              {PAGE_SIZE_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
        )}

        <Button
          variant="outline"
          size="sm"
          className="h-8 px-2"
          disabled={atFirst || loading}
          onClick={() => setPage(currentPage - 1)}
          aria-label="Previous page"
        >
          <ChevronLeft className="size-4" />
        </Button>

        <span className="tabular-nums text-xs font-medium text-[var(--sapling-dark)]">
          {loading ? (
            <Loader2 className="inline size-3 animate-spin" />
          ) : (
            <>
              {currentPage}
              <span className="text-[var(--sapling-medium-grey)]"> / {totalPages}</span>
            </>
          )}
        </span>

        <Button
          variant="outline"
          size="sm"
          className="h-8 px-2"
          disabled={atLast || loading}
          onClick={() => setPage(currentPage + 1)}
          aria-label="Next page"
        >
          <ChevronRight className="size-4" />
        </Button>
      </div>
    </div>
  );
}
