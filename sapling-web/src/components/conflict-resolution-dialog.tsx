"use client";

import { Button } from "@/components/ui/button";
import type { FieldAnalysisConflict } from "@/lib/api";
import { AlertTriangle, Layers, Replace, History, ArrowRightLeft } from "lucide-react";

export type ConflictResolutionChoice =
  | "replace"
  | "merge_as_composite"
  | "keep_both_new_latest"
  | "keep_both_old_latest";

interface Props {
  open: boolean;
  conflicts: FieldAnalysisConflict[];
  onResolve: (choice: ConflictResolutionChoice) => void;
  onCancel: () => void;
}

/**
 * Four-choice modal that handles the 409 field_analysis_conflict response.
 *
 * The agronomist picks one of:
 *   - replace               → overwrite latest (previous record is orphaned but retained)
 *   - merge_as_composite    → fold the new sample into the existing record as an extra zone
 *   - keep_both_new_latest  → save as a separate record, repoint field to new
 *   - keep_both_old_latest  → save as a separate record, keep field on old
 *
 * Two things to note:
 *   1. Merge-as-composite is the safest, non-destructive default — usually
 *      the right choice when both lab reports describe the same block.
 *   2. Replace is called out as "previous record orphaned" so the agronomist
 *      understands what it really does. Keeps the audit trail honest.
 */
export function ConflictResolutionDialog({ open, conflicts, onResolve, onCancel }: Props) {
  if (!open || conflicts.length === 0) return null;

  const fieldList = conflicts.map((c) => c.field_name || c.field_id).join(", ");
  const windowDays = conflicts[0]?.window_days ?? 7;
  const multiple = conflicts.length > 1;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onCancel}
    >
      <div
        className="w-full max-w-xl rounded-xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-3 border-b p-5">
          <AlertTriangle className="mt-0.5 size-5 shrink-0 text-amber-600" />
          <div>
            <h2 className="text-base font-semibold text-[var(--sapling-dark)]">
              {multiple ? "Fields already have a recent analysis" : "Field already has a recent analysis"}
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {fieldList} {multiple ? "each have" : "has"} an analysis within the last {windowDays} days.
              Choose how to handle the overlap.
            </p>
          </div>
        </div>

        <div className="grid gap-2 p-4">
          <ChoiceButton
            icon={<Layers className="size-4" />}
            label="Merge as composite"
            description="Add the new sample as an extra zone on the existing record. Area-weighted if weights supplied — nothing is lost."
            recommended
            onClick={() => onResolve("merge_as_composite")}
          />
          <ChoiceButton
            icon={<ArrowRightLeft className="size-4" />}
            label="Keep both — new as latest"
            description="Save a separate record and repoint the field to the new one. Previous record stays in the database."
            onClick={() => onResolve("keep_both_new_latest")}
          />
          <ChoiceButton
            icon={<History className="size-4" />}
            label="Keep both — old stays latest"
            description="Save a separate record but the field keeps its current analysis. Use for historical uploads."
            onClick={() => onResolve("keep_both_old_latest")}
          />
          <ChoiceButton
            icon={<Replace className="size-4" />}
            label="Replace existing"
            description="The new analysis becomes the linked one. The previous record is orphaned but not deleted."
            destructive
            onClick={() => onResolve("replace")}
          />
        </div>

        <div className="flex items-center justify-end gap-2 border-t bg-gray-50 p-3">
          <Button variant="outline" size="sm" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}

function ChoiceButton({
  icon,
  label,
  description,
  recommended,
  destructive,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  description: string;
  recommended?: boolean;
  destructive?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group flex items-start gap-3 rounded-lg border p-3 text-left transition-colors ${
        recommended
          ? "border-[var(--sapling-orange)]/40 bg-orange-50/30 hover:bg-orange-50"
          : destructive
            ? "border-gray-200 hover:border-red-300 hover:bg-red-50"
            : "border-gray-200 hover:bg-gray-50"
      }`}
    >
      <div className={`mt-0.5 shrink-0 ${
        recommended ? "text-[var(--sapling-orange)]" : destructive ? "text-red-600 group-hover:text-red-700" : "text-muted-foreground"
      }`}>
        {icon}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-[var(--sapling-dark)]">{label}</span>
          {recommended && (
            <span className="rounded-full bg-[var(--sapling-orange)]/10 px-1.5 py-0.5 text-[10px] font-medium text-[var(--sapling-orange)]">
              Recommended
            </span>
          )}
        </div>
        <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
      </div>
    </button>
  );
}
