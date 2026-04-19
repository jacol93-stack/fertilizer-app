"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MONTH_NAMES } from "@/lib/season-constants";

const GROUP_COLORS = [
  "bg-blue-500", "bg-green-500", "bg-purple-500", "bg-amber-500",
  "bg-rose-500", "bg-cyan-500", "bg-indigo-500", "bg-emerald-500",
];

export interface ApplicationBlendData {
  stage_name: string;
  month: number;
  method: string;
  // Each application now carries its own recipe — the programme engine
  // runs the LP per-application with method-filtered materials, so a
  // broadcast in Feb and a fertigation in Nov don't share the same
  // blend any more.
  sa_notation: string;
  rate_kg_ha: number;
  cost_per_ton?: number;
  exact?: boolean;
  recipe?: Array<{ material: string; type: string; kg: number; pct: number; cost: number }>;
  // Foliar applications skip the dry/liquid LP — the rate is 0 and
  // recipe empty. UI renders a "configure foliar product" hint instead.
  is_foliar?: boolean;
}

export interface BlendGroupData {
  group: string;
  crops: string[];
  block_names: string[];
  total_area_ha: number;
  applications: ApplicationBlendData[];
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

  const totalApplications = blendGroups.reduce((n, g) => n + g.applications.length, 0);

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-[var(--sapling-dark)]">Optimized Blends</h3>
        <p className="text-sm text-muted-foreground">
          {totalApplications} application{totalApplications !== 1 ? "s" : ""} across {blendGroups.length} blend group{blendGroups.length !== 1 ? "s" : ""} — each stage gets its own recipe.
        </p>
      </div>

      {blendGroups.map((group, idx) => {
        const groupTotalKg = group.applications.reduce(
          (s, a) => s + (a.is_foliar ? 0 : a.rate_kg_ha * group.total_area_ha),
          0,
        );
        const groupCost = group.applications.reduce(
          (s, a) => s + (a.is_foliar || a.cost_per_ton == null
            ? 0
            : (a.cost_per_ton / 1000) * a.rate_kg_ha * group.total_area_ha),
          0,
        );
        return (
          <Card key={group.group} className="overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex items-start gap-3">
                <span className={`flex size-8 items-center justify-center rounded-full text-sm font-bold text-white ${GROUP_COLORS[idx % GROUP_COLORS.length]}`}>
                  {group.group}
                </span>
                <div className="flex-1">
                  <CardTitle className="text-base">
                    Group {group.group} — {group.applications.length} application{group.applications.length !== 1 ? "s" : ""}
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    {group.crops.join(", ")} &middot; {group.block_names.join(", ")} &middot; {group.total_area_ha} ha
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {group.applications
                .slice()
                .sort((a, b) => a.month - b.month)
                .map((app, i) => (
                  <div key={i} className={`rounded-lg border ${app.is_foliar ? "border-violet-200 bg-violet-50/40" : "bg-white"}`}>
                    <div className="flex flex-wrap items-start justify-between gap-3 px-3 py-2">
                      <div className="flex items-start gap-2">
                        <div>
                          <p className="text-sm font-medium text-[var(--sapling-dark)]">
                            {MONTH_NAMES[app.month]} &middot; {app.stage_name || "Untitled stage"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {app.is_foliar ? (
                              <>Foliar &mdash; product selection happens via the catalog; not in this LP.</>
                            ) : (
                              <>{app.sa_notation || "(no recipe)"} via <span className="font-medium">{app.method}</span></>
                            )}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        {app.is_foliar ? (
                          <span className="inline-flex items-center rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-medium text-violet-800">
                            foliar (configure separately)
                          </span>
                        ) : (
                          <>
                            <p className="text-sm font-bold text-[var(--sapling-dark)]">
                              {app.rate_kg_ha ? `${app.rate_kg_ha} kg/ha` : "—"}
                            </p>
                            {isAdmin && app.cost_per_ton != null && (
                              <p className="text-[10px] text-muted-foreground">
                                R{app.cost_per_ton.toLocaleString(undefined, { minimumFractionDigits: 2 })}/ton
                              </p>
                            )}
                            {app.exact === false && (
                              <p className="text-[10px] text-amber-600">Approximate match</p>
                            )}
                          </>
                        )}
                      </div>
                    </div>

                    {app.recipe && app.recipe.length > 0 && isAdmin && !app.is_foliar && (
                      <div className="overflow-x-auto border-t">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b bg-gray-50 text-left">
                              <th className="px-2 py-1.5 font-medium">Material</th>
                              <th className="px-2 py-1.5 font-medium">Type</th>
                              <th className="px-2 py-1.5 text-right font-medium">kg</th>
                              <th className="px-2 py-1.5 text-right font-medium">%</th>
                              <th className="px-2 py-1.5 text-right font-medium">Cost</th>
                            </tr>
                          </thead>
                          <tbody>
                            {app.recipe.map((r, ri) => (
                              <tr key={ri} className="border-b last:border-0">
                                <td className="px-2 py-1">{r.material}</td>
                                <td className="px-2 py-1 text-muted-foreground">{r.type}</td>
                                <td className="px-2 py-1 text-right tabular-nums">{r.kg.toFixed(1)}</td>
                                <td className="px-2 py-1 text-right tabular-nums">{r.pct.toFixed(1)}</td>
                                <td className="px-2 py-1 text-right tabular-nums">R{r.cost.toFixed(0)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                ))}

              {/* Total for this group (excludes foliar rows since they're
                  not yet costed) */}
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-gray-50 px-3 py-2 text-xs">
                <span className="text-muted-foreground">
                  Non-foliar total: {groupTotalKg.toLocaleString(undefined, { maximumFractionDigits: 0 })} kg across {group.applications.filter((a) => !a.is_foliar).length} application{group.applications.filter((a) => !a.is_foliar).length !== 1 ? "s" : ""}
                </span>
                {isAdmin && groupCost > 0 && (
                  <span className="font-medium text-[var(--sapling-dark)]">
                    R{groupCost.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} total
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
