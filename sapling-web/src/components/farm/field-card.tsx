"use client";

import type { Field } from "@/lib/season-constants";
import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, CheckCircle, Droplets, Sprout, TreeDeciduous, CheckCircle2, Pencil, Layers } from "lucide-react";

interface FieldCardProps {
  field: Field;
  selected?: boolean;
  selectable?: boolean;
  onToggle?: (fieldId: string) => void;
  onClick?: (fieldId: string) => void;
}

const irrigationIcons: Record<string, string> = {
  drip: "Drip",
  pivot: "Pivot",
  micro: "Micro",
  flood: "Flood",
  none: "None",
};

// Friendly labels for the health-issue keys returned by the API.
// Keys mirror what _compute_field_health emits in clients.py.
const HEALTH_LABELS: Record<string, string> = {
  size: "size (ha)",
  crop: "crop",
  soil_analysis: "soil analysis link",
  soil_macros_missing: "soil macros (K/Ca/Mg/P)",
  tree_age: "tree age",
  planting_date: "planting date",
  yield_target: "yield target",
  irrigation_type: "irrigation type",
  accepted_methods: "application methods",
  pop_per_ha: "trees / ha",
  soil_pH_missing: "soil pH",
  soil_CEC_missing: "soil CEC",
};

function humanise(keys: string[]): string {
  return keys.map((k) => HEALTH_LABELS[k] ?? k).join(", ");
}

function HealthPill({ health }: { health: NonNullable<Field["health"]> }) {
  if (health.level === "ok") {
    return (
      <span
        className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700"
        title="All engine-relevant inputs present"
      >
        <CheckCircle className="size-3" />
        Ready
      </span>
    );
  }
  if (health.level === "critical") {
    return (
      <span
        className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-semibold text-red-700"
        title={`Engine can't build a programme until you set: ${humanise(health.critical)}`}
      >
        <AlertTriangle className="size-3" />
        Missing: {humanise(health.critical)}
      </span>
    );
  }
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700"
      title={`Programme will build with assumptions on: ${humanise(health.warnings)}`}
    >
      <AlertTriangle className="size-3" />
      Assumes: {humanise(health.warnings.slice(0, 2))}
      {health.warnings.length > 2 && ` +${health.warnings.length - 2}`}
    </span>
  );
}

export function FieldCard({ field, selected, selectable, onToggle, onClick }: FieldCardProps) {
  const isPerennial = field.crop_type?.toLowerCase() === "perennial";

  return (
    <Card
      className={`relative cursor-pointer transition-all hover:shadow-md ${
        selected ? "ring-2 ring-[var(--sapling-orange)]" : ""
      }`}
      onClick={() => {
        if (selectable && onToggle) {
          onToggle(field.id);
        } else if (onClick) {
          onClick(field.id);
        }
      }}
    >
      {/* Selection checkbox */}
      {selectable && (
        <div className="absolute right-3 top-3">
          <div
            className={`flex size-5 items-center justify-center rounded-full border-2 transition-colors ${
              selected
                ? "border-[var(--sapling-orange)] bg-[var(--sapling-orange)]"
                : "border-gray-300 bg-white"
            }`}
          >
            {selected && <CheckCircle2 className="size-3.5 text-white" />}
          </div>
        </div>
      )}

      <CardContent className="p-4">
        {/* Header: name + area + edit */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-[var(--sapling-dark)]">{field.name}</h3>
          <div className="flex items-center gap-1.5 shrink-0">
            {field.size_ha && (
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                {field.size_ha} ha
              </span>
            )}
            {!selectable && (
              <span className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-[var(--sapling-orange)]">
                <Pencil className="size-3.5" />
              </span>
            )}
          </div>
        </div>

        {/* Crop info */}
        {field.crop ? (
          <div className="mt-2 flex items-center gap-2">
            {isPerennial ? (
              <TreeDeciduous className="size-3.5 text-green-600" />
            ) : (
              <Sprout className="size-3.5 text-blue-600" />
            )}
            <span className="text-sm font-medium text-[var(--sapling-dark)]">
              {field.crop}
              {field.cultivar && <span className="text-[var(--sapling-medium-grey)]"> ({field.cultivar})</span>}
            </span>
            <span
              className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase ${
                isPerennial
                  ? "bg-green-50 text-green-700"
                  : "bg-blue-50 text-blue-700"
              }`}
            >
              {field.crop_type}
            </span>
          </div>
        ) : (
          <p className="mt-2 text-xs italic text-gray-400">No crop set</p>
        )}

        {/* Age / planting date */}
        {field.crop && (
          <p className="mt-1 text-xs text-[var(--sapling-medium-grey)]">
            {isPerennial && field.tree_age != null && `${field.tree_age} years old`}
            {!isPerennial && field.planting_date && `Planted: ${field.planting_date}`}
            {field.yield_target && ` · Target: ${field.yield_target} ${field.yield_unit || ""}`}
          </p>
        )}

        {/* Irrigation + methods */}
        <div className="mt-3 flex flex-wrap gap-1.5">
          {field.irrigation_type && field.irrigation_type !== "none" && (
            <span className="inline-flex items-center gap-1 rounded-full bg-cyan-50 px-2 py-0.5 text-[10px] font-semibold text-cyan-700">
              <Droplets className="size-3" />
              {irrigationIcons[field.irrigation_type] || field.irrigation_type}
            </span>
          )}
          {field.accepted_methods?.map((m) => (
            <span
              key={m}
              className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600"
            >
              {m}
            </span>
          ))}
        </div>

        {/* Analysis status + data-completeness pill */}
        <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-2">
          {field.latest_analysis_id ? (
            <span
              className="inline-flex items-center gap-1 text-[10px] font-medium text-green-600"
              title={
                field.latest_analysis_date
                  ? `Sampled ${new Date(field.latest_analysis_date).toLocaleDateString()}`
                  : "Linked"
              }
            >
              <span className="size-1.5 rounded-full bg-green-500" />
              {field.latest_analysis_date
                ? `Soil ${field.latest_analysis_date}`
                : "Analysis linked"}
            </span>
          ) : (
            <span className="text-[10px] text-gray-400">No analysis</span>
          )}
          {field.latest_analysis_composite && field.latest_analysis_composite.replicate_count > 1 && (
            <span
              className="inline-flex items-center gap-0.5 rounded-full bg-orange-100 px-1.5 py-0.5 text-[10px] font-medium text-orange-700"
              title={`Composite of ${field.latest_analysis_composite.replicate_count} zone samples (${field.latest_analysis_composite.composition_method.replace("composite_", "").replace("_", " ")})`}
            >
              <Layers className="size-2.5" />
              {field.latest_analysis_composite.replicate_count} samples
            </span>
          )}
          {field.health && <HealthPill health={field.health} />}
        </div>
      </CardContent>
    </Card>
  );
}
