"use client";

/**
 * SelectionToolbar — generic multi-select bar for any list view.
 *
 * Two modes:
 *   • idle      — just shows a "Select" button to enter selection mode
 *   • selecting — shows checkbox-all, count, Cancel, and Delete buttons
 *
 * Wiring contract:
 *   1. Parent owns `selected: Set<string>` state and toggles on row click
 *      when `selectionMode` is true.
 *   2. Parent fires `onDelete(ids)` after the user confirms; the parent
 *      runs the per-row API calls and refreshes its list.
 *
 * Used on Clients, Farms, Fields, and per-block data lists. Same UX
 * everywhere so the agronomist learns it once.
 */

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Trash2, X, CheckSquare, Square, Loader2 } from "lucide-react";

export interface SelectionToolbarProps {
  /** Whether the parent list is currently in selection mode. */
  selectionMode: boolean;
  /** Toggle selection mode. */
  onToggleMode: (next: boolean) => void;
  /** Total number of rows currently visible. Used for "all selected"
   * detection and the "Select all" button label. */
  totalCount: number;
  /** Number currently selected. */
  selectedCount: number;
  /** Toggle "select all" — when called, parent should select every
   * visible row id (or clear, depending on current state). */
  onSelectAll: (selectAll: boolean) => void;
  /** Fired after the user confirms the destructive action. The parent
   * is responsible for the per-row API calls + list refresh. */
  onDelete: () => Promise<void> | void;
  /** Singular/plural noun for the item type, e.g. "client" / "farm" /
   * "field" / "soil analysis". Drives copy on the toolbar + confirm
   * dialog. */
  itemLabel: { singular: string; plural: string };
  /** Disable when an outer save is in flight. */
  disabled?: boolean;
}

export function SelectionToolbar(props: SelectionToolbarProps) {
  const {
    selectionMode, onToggleMode, totalCount, selectedCount,
    onSelectAll, onDelete, itemLabel, disabled,
  } = props;
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const allSelected = totalCount > 0 && selectedCount === totalCount;

  if (!selectionMode) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => onToggleMode(true)}
        disabled={disabled || totalCount === 0}
        className="h-8 text-xs"
      >
        <CheckSquare className="size-3.5" />
        Select
      </Button>
    );
  }

  const noun = selectedCount === 1 ? itemLabel.singular : itemLabel.plural;

  return (
    <>
      <div className="flex items-center gap-2 rounded-md border border-[var(--sapling-orange)]/40 bg-orange-50/50 px-2 py-1">
        <button
          type="button"
          onClick={() => onSelectAll(!allSelected)}
          className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium text-[var(--sapling-dark)] hover:bg-white"
          disabled={disabled || totalCount === 0}
        >
          {allSelected ? <CheckSquare className="size-3.5" /> : <Square className="size-3.5" />}
          {allSelected ? "Clear all" : `Select all ${totalCount}`}
        </button>
        <span className="text-xs text-muted-foreground">
          {selectedCount} {selectedCount === 1 ? "selected" : "selected"}
        </span>
        <div className="ml-auto flex items-center gap-1">
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setConfirming(true)}
            disabled={disabled || selectedCount === 0}
            className="h-7 text-xs"
          >
            <Trash2 className="size-3.5" />
            Delete{selectedCount > 0 ? ` ${selectedCount}` : ""}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onToggleMode(false)}
            disabled={deleting}
            className="h-7 text-xs"
          >
            <X className="size-3.5" />
            Cancel
          </Button>
        </div>
      </div>

      {confirming && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => !deleting && setConfirming(false)}
        >
          <div
            className="w-full max-w-md rounded-lg bg-white shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="border-b px-5 py-4">
              <h3 className="text-base font-semibold text-[var(--sapling-dark)]">
                Delete {selectedCount} {noun}?
              </h3>
            </div>
            <div className="px-5 py-4 text-sm text-muted-foreground">
              <p>
                This soft-deletes the selected {noun} and everything below
                ({itemLabel.singular === "client" && "farms, fields, soil analyses, programmes"}
                {itemLabel.singular === "farm" && "fields, soil analyses, programmes for those fields"}
                {itemLabel.singular === "field" && "soil + leaf analyses, yield records, applications, events"}
                {itemLabel.singular !== "client" && itemLabel.singular !== "farm" && itemLabel.singular !== "field" && "all attached records"})
                . Admins can restore from the Trash tab.
              </p>
            </div>
            <div className="flex justify-end gap-2 border-t px-5 py-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConfirming(false)}
                disabled={deleting}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                disabled={deleting}
                onClick={async () => {
                  setDeleting(true);
                  try {
                    await onDelete();
                    setConfirming(false);
                    onToggleMode(false);
                  } finally {
                    setDeleting(false);
                  }
                }}
              >
                {deleting ? <Loader2 className="size-3.5 animate-spin" /> : <Trash2 className="size-3.5" />}
                Delete {selectedCount} {noun}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
