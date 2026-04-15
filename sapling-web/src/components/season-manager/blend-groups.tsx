"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MONTH_NAMES } from "@/lib/season-constants";

const GROUP_COLORS = [
  "bg-blue-500", "bg-green-500", "bg-purple-500", "bg-amber-500",
  "bg-rose-500", "bg-cyan-500", "bg-indigo-500", "bg-emerald-500",
];

export interface BlendGroupData {
  group: string;
  crops: string[];
  block_names: string[];
  total_area_ha: number;
  sa_notation: string;
  international_notation?: string;
  rate_kg_ha: number;
  cost_per_ton?: number;
  exact?: boolean;
  recipe?: Array<{ material: string; type: string; kg: number; pct: number; cost: number }>;
  applications: Array<{
    stage_name: string;
    month: number;
    method: string;
  }>;
}

interface BlendGroupsProps {
  blendGroups: BlendGroupData[];
  isAdmin: boolean;
}

export function BlendGroups({ blendGroups, isAdmin }: BlendGroupsProps) {
  if (blendGroups.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        No blend groups generated
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-[var(--sapling-dark)]">Optimized Blends</h3>
        <p className="text-sm text-muted-foreground">
          {blendGroups.length} unique blend{blendGroups.length !== 1 ? "s" : ""} needed for this programme
        </p>
      </div>

      {blendGroups.map((group, idx) => (
        <Card key={group.group} className="overflow-hidden">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <span className={`flex size-8 items-center justify-center rounded-full text-sm font-bold text-white ${GROUP_COLORS[idx % GROUP_COLORS.length]}`}>
                  {group.group}
                </span>
                <div>
                  <CardTitle className="text-base">
                    {group.sa_notation || "Blend " + group.group}
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    {group.crops.join(", ")} &middot; {group.block_names.join(", ")} &middot; {group.total_area_ha} ha
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-[var(--sapling-dark)]">
                  {group.rate_kg_ha} kg/ha
                </p>
                {isAdmin && group.cost_per_ton != null && (
                  <p className="text-xs text-muted-foreground">
                    R{group.cost_per_ton.toLocaleString(undefined, { minimumFractionDigits: 2 })}/ton
                  </p>
                )}
                {!group.exact && (
                  <p className="text-[10px] text-amber-600">Approximate match</p>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Application schedule for this blend */}
            <div>
              <p className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">Applications</p>
              <div className="flex flex-wrap gap-2">
                {group.applications.map((app, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs"
                  >
                    <span className="font-medium">{MONTH_NAMES[app.month]}</span>
                    <span className="text-muted-foreground">{app.stage_name}</span>
                    <span className="rounded bg-gray-100 px-1 py-0.5 text-[10px]">{app.method}</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Recipe table (admin sees costs, agents don't) */}
            {group.recipe && group.recipe.length > 0 && isAdmin && (
              <div>
                <p className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">Recipe (per 1000kg batch)</p>
                <div className="overflow-x-auto rounded border">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b bg-gray-50 text-left">
                        <th className="px-2 py-1.5 font-medium">Material</th>
                        <th className="px-2 py-1.5 font-medium">Type</th>
                        <th className="px-2 py-1.5 text-right font-medium">kg</th>
                        <th className="px-2 py-1.5 text-right font-medium">%</th>
                        {isAdmin && <th className="px-2 py-1.5 text-right font-medium">Cost</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {group.recipe.map((r, i) => (
                        <tr key={i} className="border-b last:border-0">
                          <td className="px-2 py-1">{r.material}</td>
                          <td className="px-2 py-1 text-muted-foreground">{r.type}</td>
                          <td className="px-2 py-1 text-right tabular-nums">{r.kg.toFixed(1)}</td>
                          <td className="px-2 py-1 text-right tabular-nums">{r.pct.toFixed(1)}</td>
                          {isAdmin && <td className="px-2 py-1 text-right tabular-nums">R{r.cost.toFixed(0)}</td>}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Total for this group */}
            <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-xs">
              <span className="text-muted-foreground">
                Total: {group.rate_kg_ha} kg/ha × {group.total_area_ha} ha = {(group.rate_kg_ha * group.total_area_ha).toLocaleString()} kg
              </span>
              {isAdmin && group.cost_per_ton != null && (
                <span className="font-medium text-[var(--sapling-dark)]">
                  R{((group.cost_per_ton / 1000) * group.rate_kg_ha * group.total_area_ha).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} total
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
