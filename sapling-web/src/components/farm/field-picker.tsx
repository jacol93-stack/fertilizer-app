"use client";

import type { Field } from "@/lib/season-constants";
import { FieldCard } from "./field-card";

interface FieldPickerProps {
  fields: Field[];
  selectedIds: Set<string>;
  onToggle: (fieldId: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
}

export function FieldPicker({
  fields,
  selectedIds,
  onToggle,
  onSelectAll,
  onDeselectAll,
}: FieldPickerProps) {
  const allSelected = fields.length > 0 && fields.every((f) => selectedIds.has(f.id));
  const fieldsWithCrop = fields.filter((f) => f.crop);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--sapling-medium-grey)]">
          {selectedIds.size} of {fieldsWithCrop.length} fields selected
        </p>
        <button
          type="button"
          onClick={allSelected ? onDeselectAll : onSelectAll}
          className="text-xs font-medium text-[var(--sapling-orange)] hover:underline"
        >
          {allSelected ? "Deselect All" : "Select All"}
        </button>
      </div>

      {fieldsWithCrop.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-400">
          No fields with crops configured. Set up fields on the farm page first.
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {fieldsWithCrop.map((field) => (
            <FieldCard
              key={field.id}
              field={field}
              selectable
              selected={selectedIds.has(field.id)}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}

      {fields.length > fieldsWithCrop.length && (
        <p className="text-xs text-gray-400">
          {fields.length - fieldsWithCrop.length} field(s) hidden — no crop configured
        </p>
      )}
    </div>
  );
}
