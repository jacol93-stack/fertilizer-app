"use client";

import { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Leaf, AlertTriangle, Info } from "lucide-react";
import type { CropImpact } from "./comparison-utils";

export function CropImpactPanel({
  impacts,
}: {
  impacts: CropImpact[];
}) {
  const [enabledPairs, setEnabledPairs] = useState<Set<number>>(
    new Set(impacts.map((_, i) => i))
  );

  function togglePair(idx: number) {
    const next = new Set(enabledPairs);
    if (next.has(idx)) {
      next.delete(idx);
    } else {
      next.add(idx);
    }
    setEnabledPairs(next);
  }

  if (impacts.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Leaf className="size-4 text-[var(--sapling-orange)]" />
          Crop Impact Analysis
        </CardTitle>
        <CardDescription>
          Expected nutrient depletion vs actual soil changes between analyses
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {impacts.map((impact, idx) => (
            <div key={idx} className="rounded-lg border">
              <div className="flex items-center justify-between border-b bg-gray-50 px-4 py-2.5">
                <div className="text-sm">
                  <span className="font-medium text-[var(--sapling-dark)]">
                    {impact.date_from} → {impact.date_to}
                  </span>
                  {impact.available && (impact.crops_label || impact.crop) && (
                    <span className="ml-3 text-muted-foreground">
                      Crops: {impact.crops_label || impact.crop}
                    </span>
                  )}
                </div>
                <label className="flex cursor-pointer items-center gap-2 text-xs">
                  <input
                    type="checkbox"
                    checked={enabledPairs.has(idx)}
                    onChange={() => togglePair(idx)}
                    className="size-3.5 rounded border-gray-300 accent-[var(--sapling-orange)]"
                  />
                  Include
                </label>
              </div>

              {!impact.available && (
                <div className="flex items-center gap-2 px-4 py-3 text-sm text-muted-foreground">
                  <Info className="size-4 shrink-0" />
                  {impact.reason || "Crop impact data unavailable"}
                </div>
              )}

              {impact.available && enabledPairs.has(idx) && impact.nutrients && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        <th className="px-4 py-2">Nutrient</th>
                        <th className="px-4 py-2 text-right">Before</th>
                        <th className="px-4 py-2 text-right">After</th>
                        <th className="px-4 py-2 text-right">Change</th>
                        <th className="px-4 py-2 text-right">Expected Depletion</th>
                        <th className="px-4 py-2">Interpretation</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {impact.nutrients
                        .filter((n) => n.expected_depletion_kg_ha > 0 || n.actual_change !== null)
                        .map((n) => {
                          const isWarning =
                            n.interpretation.toLowerCase().includes("leaching") ||
                            n.interpretation.toLowerCase().includes("erosion") ||
                            n.interpretation.toLowerCase().includes("significant");

                          return (
                            <tr key={n.nutrient} className="hover:bg-gray-50">
                              <td className="px-4 py-2 font-medium">{n.nutrient}</td>
                              <td className="px-4 py-2 text-right tabular-nums">
                                {n.value_before != null ? Number(n.value_before).toFixed(1) : "-"}
                              </td>
                              <td className="px-4 py-2 text-right tabular-nums">
                                {n.value_after != null ? Number(n.value_after).toFixed(1) : "-"}
                              </td>
                              <td
                                className={`px-4 py-2 text-right tabular-nums ${
                                  n.actual_change != null && n.actual_change < 0
                                    ? "text-red-600"
                                    : n.actual_change != null && n.actual_change > 0
                                      ? "text-green-600"
                                      : ""
                                }`}
                              >
                                {n.actual_change != null
                                  ? `${n.actual_change > 0 ? "+" : ""}${n.actual_change.toFixed(1)}`
                                  : "-"}
                              </td>
                              <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">
                                {n.expected_depletion_kg_ha > 0
                                  ? `${n.expected_depletion_kg_ha.toFixed(1)} kg/ha`
                                  : "-"}
                              </td>
                              <td className="px-4 py-2">
                                <span className="flex items-center gap-1.5 text-xs">
                                  {isWarning && (
                                    <AlertTriangle className="size-3.5 shrink-0 text-orange-500" />
                                  )}
                                  <span className={isWarning ? "text-orange-700" : "text-muted-foreground"}>
                                    {n.interpretation}
                                  </span>
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              )}

              {impact.available && !enabledPairs.has(idx) && (
                <div className="px-4 py-3 text-sm text-muted-foreground italic">
                  Crop impact excluded — toggle to include
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
