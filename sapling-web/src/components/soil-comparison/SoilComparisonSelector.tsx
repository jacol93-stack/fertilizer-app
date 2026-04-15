"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { BarChart3, ChevronDown } from "lucide-react";
import { formatDate } from "./comparison-utils";

interface Analysis {
  id: string;
  crop: string | null;
  cultivar: string | null;
  yield_target: number | null;
  lab_name: string | null;
  analysis_date: string | null;
  farm_id: string | null;
  field_id: string | null;
  farm: string | null;
  field: string | null;
  created_at: string;
}

interface Farm {
  id: string;
  name: string;
}

interface Field {
  id: string;
  farm_id: string;
  name: string;
}

export function SoilComparisonSelector({
  analyses,
  farms,
  farmFields,
  selectedIds,
  onSelectionChange,
  onCompare,
}: {
  analyses: Analysis[];
  farms: Farm[];
  farmFields: Record<string, Field[]>;
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
  onCompare: () => void;
}) {
  const [filterFarm, setFilterFarm] = useState("all");

  const filtered =
    filterFarm === "all"
      ? analyses
      : analyses.filter((a) => a.farm_id === filterFarm);

  // Group by field
  const byField: Record<string, Analysis[]> = {};
  for (const a of filtered) {
    const key = a.field || a.farm || "Unknown";
    if (!byField[key]) byField[key] = [];
    byField[key].push(a);
  }

  function toggle(id: string) {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    onSelectionChange(next);
  }

  function toggleAll(ids: string[]) {
    const allSelected = ids.every((id) => selectedIds.has(id));
    const next = new Set(selectedIds);
    if (allSelected) {
      ids.forEach((id) => next.delete(id));
    } else {
      ids.forEach((id) => next.add(id));
    }
    onSelectionChange(next);
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="size-4 text-[var(--sapling-orange)]" />
              Select Analyses to Compare
            </CardTitle>
            <CardDescription>
              Choose 2 or more soil analyses to compare side-by-side or track trends
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            {farms.length > 0 && (
              <div className="relative">
                <select
                  value={filterFarm}
                  onChange={(e) => setFilterFarm(e.target.value)}
                  className="h-8 appearance-none rounded-md border border-input bg-white pl-3 pr-8 text-sm outline-none focus-visible:border-ring"
                >
                  <option value="all">All Farms</option>
                  {farms.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
              </div>
            )}
            <Button
              onClick={onCompare}
              disabled={selectedIds.size < 2}
            >
              Compare ({selectedIds.size})
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {Object.entries(byField).length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">
            No soil analyses found
          </p>
        ) : (
          <div className="space-y-4">
            {Object.entries(byField).map(([fieldName, fieldAnalyses]) => (
              <div key={fieldName} className="rounded-lg border">
                <div className="flex items-center justify-between border-b bg-gray-50 px-4 py-2">
                  <span className="text-sm font-medium text-[var(--sapling-dark)]">
                    {fieldName}
                  </span>
                  <button
                    type="button"
                    onClick={() =>
                      toggleAll(fieldAnalyses.map((a) => a.id))
                    }
                    className="text-xs text-[var(--sapling-orange)] hover:underline"
                  >
                    {fieldAnalyses.every((a) => selectedIds.has(a.id))
                      ? "Deselect all"
                      : "Select all"}
                  </button>
                </div>
                <div className="divide-y divide-gray-100">
                  {fieldAnalyses.map((a) => (
                    <label
                      key={a.id}
                      className="flex cursor-pointer items-center gap-3 px-4 py-2.5 hover:bg-gray-50"
                    >
                      <input
                        type="checkbox"
                        checked={selectedIds.has(a.id)}
                        onChange={() => toggle(a.id)}
                        className="size-4 rounded border-gray-300 text-[var(--sapling-orange)] accent-[var(--sapling-orange)]"
                      />
                      <div className="flex flex-1 items-center gap-4 text-sm">
                        <span className="w-24 font-medium">
                          {formatDate(a.analysis_date || a.created_at)}
                        </span>
                        <span className="w-24">{a.crop || "-"}</span>
                        <span className="w-20 text-muted-foreground">
                          {a.cultivar || "-"}
                        </span>
                        <span className="w-20 text-muted-foreground">
                          {a.lab_name || "-"}
                        </span>
                        <span className="text-muted-foreground tabular-nums">
                          {a.yield_target || "-"}
                        </span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
