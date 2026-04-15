"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Sparkles } from "lucide-react";

const PRIMARY = ["N", "P", "K"];

interface NutrientPriorityPanelProps {
  /** Current nutrient targets {N: 5, P: 2, Ca: 4, ...} */
  targets: Record<string, number>;
  /** Missed targets from the initial optimize (optional) */
  missedTargets?: Array<{ nutrient: string; target: number; actual: number; shortfall: number }>;
  /** Called when user clicks re-optimize */
  onOptimize: (priorities: Record<string, "must_match" | "flexible">) => void;
  optimizing: boolean;
}

export function NutrientPriorityPanel({
  targets,
  missedTargets,
  onOptimize,
  optimizing,
}: NutrientPriorityPanelProps) {
  const nutrients = Object.entries(targets).filter(([, v]) => v > 0);

  const [priorities, setPriorities] = useState<Record<string, "must_match" | "flexible">>(() => {
    const p: Record<string, "must_match" | "flexible"> = {};
    for (const [nut] of nutrients) {
      p[nut] = PRIMARY.includes(nut) ? "must_match" : "flexible";
    }
    return p;
  });

  const missedMap = new Map(
    (missedTargets || []).map((m) => [m.nutrient, m])
  );

  return (
    <div className="rounded-xl border-2 border-amber-300 bg-amber-50 p-5">
      <h3 className="text-sm font-semibold text-amber-800">
        Set Nutrient Priorities
      </h3>
      <p className="mt-1 text-xs text-amber-700">
        The optimizer couldn&apos;t match all targets exactly. Choose which nutrients must be matched
        and which can be flexible — the optimizer will prioritise accordingly.
      </p>

      <div className="mt-4 space-y-2">
        {nutrients.map(([nut, target]) => {
          const missed = missedMap.get(nut);
          const isMust = priorities[nut] === "must_match";
          return (
            <div
              key={nut}
              className="flex items-center justify-between rounded-lg border bg-white px-3 py-2"
            >
              <div className="flex items-center gap-3">
                <span className="w-8 text-sm font-bold text-[var(--sapling-dark)]">{nut}</span>
                <span className="text-xs text-muted-foreground">Target: {target}%</span>
                {missed && (
                  <span className="text-xs text-red-600">
                    achieved {missed.actual.toFixed(2)}% (short {missed.shortfall.toFixed(2)}%)
                  </span>
                )}
              </div>
              <div className="flex rounded-md border">
                <button
                  type="button"
                  onClick={() => setPriorities((p) => ({ ...p, [nut]: "must_match" }))}
                  className={`px-3 py-1 text-xs font-medium transition-colors ${
                    isMust
                      ? "bg-green-600 text-white"
                      : "text-gray-500 hover:bg-gray-50"
                  }`}
                >
                  Must Match
                </button>
                <button
                  type="button"
                  onClick={() => setPriorities((p) => ({ ...p, [nut]: "flexible" }))}
                  className={`px-3 py-1 text-xs font-medium transition-colors ${
                    !isMust
                      ? "bg-amber-500 text-white"
                      : "text-gray-500 hover:bg-gray-50"
                  }`}
                >
                  Flexible
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <Button
        onClick={() => onOptimize(priorities)}
        disabled={optimizing}
        className="mt-4 w-full bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
      >
        {optimizing ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
        Re-optimize with Priorities
      </Button>
    </div>
  );
}
