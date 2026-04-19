"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, GitCompare, ArrowRight } from "lucide-react";
import { MONTH_NAMES } from "@/lib/season-constants";

interface ComparisonViewProps {
  programmeId: string;
}

interface Attribution {
  kind: string;
  adjustment_id: string;
  at: string;
  actor: string | null;
  summary: string | null;
}

interface BlendSummary {
  id: string;
  stage_name: string | null;
  application_month: number | null;
  method: string | null;
  rate_kg_ha: number | null;
  sa_notation: string | null;
  nutrients: Record<string, number>;
}

interface ActualSummary {
  id: string;
  actual_date: string | null;
  actual_rate_kg_ha: number | null;
  product_name: string | null;
  is_sapling_product: boolean;
  method: string | null;
  status: string | null;
}

interface MonthDiff {
  month: number;
  baseline: BlendSummary | null;
  current: BlendSummary | null;
  actual: ActualSummary[];
  status: "unchanged" | "edited" | "added" | "removed" | "applied_only";
  nutrient_delta: Record<string, number>;
}

interface BlockComparison {
  block_id: string;
  block_name: string;
  crop: string;
  blend_group: string | null;
  baseline_blends: BlendSummary[];
  current_blends: BlendSummary[];
  applications: ActualSummary[];
  per_month_diff: MonthDiff[];
  season_totals: {
    baseline: Record<string, number>;
    current: Record<string, number>;
    applied: Record<string, number>;
  };
  attributions: Attribution[];
}

interface CompareResponse {
  has_baseline: boolean;
  baseline: { id: string; created_at: string; reason: string } | null;
  blocks: BlockComparison[];
}

const STATUS_STYLE: Record<MonthDiff["status"], string> = {
  unchanged: "bg-muted text-muted-foreground",
  edited: "bg-amber-100 text-amber-800",
  added: "bg-green-100 text-green-800",
  removed: "bg-red-100 text-red-800",
  applied_only: "bg-blue-100 text-blue-800",
};

const STATUS_LABEL: Record<MonthDiff["status"], string> = {
  unchanged: "No change",
  edited: "Edited",
  added: "Added",
  removed: "Removed",
  applied_only: "Actual only",
};

export function ComparisonView({ programmeId }: ComparisonViewProps) {
  const [data, setData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<CompareResponse>(`/api/programmes/${programmeId}/compare`)
      .then(setData)
      .catch(() => toast.error("Failed to load comparison"))
      .finally(() => setLoading(false));
  }, [programmeId]);

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) return null;

  if (!data.has_baseline) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <GitCompare className="mx-auto mb-3 size-10 text-muted-foreground/30" />
          <p className="font-medium text-muted-foreground">No baseline snapshot yet</p>
          <p className="mt-1 text-sm text-muted-foreground/70">
            Activate the programme to freeze the original plan for comparison.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold">Plan vs Actual</h3>
        <p className="text-sm text-muted-foreground">
          Original plan frozen {data.baseline?.created_at && new Date(data.baseline.created_at).toLocaleDateString()} · Side-by-side with what's currently planned and what's been done
        </p>
      </div>

      {data.blocks.map((block) => (
        <BlockCompareCard key={block.block_id} block={block} />
      ))}
    </div>
  );
}

function BlockCompareCard({ block }: { block: BlockComparison }) {
  const nutrientKeys = [
    ...new Set([
      ...Object.keys(block.season_totals.baseline),
      ...Object.keys(block.season_totals.current),
      ...Object.keys(block.season_totals.applied),
    ]),
  ].sort();

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          {block.block_name}
          {block.blend_group && (
            <span className="rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
              Group {block.blend_group}
            </span>
          )}
          <span className="text-xs font-normal text-muted-foreground">· {block.crop}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Season totals */}
        <div>
          <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">Season totals (kg/ha)</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr>
                  <th className="py-1.5 pr-3 text-left">Nutrient</th>
                  <th className="py-1.5 pr-3 text-right">Baseline</th>
                  <th className="py-1.5 pr-3 text-right">Current</th>
                  <th className="py-1.5 pr-3 text-right">Applied</th>
                  <th className="py-1.5 pr-3 text-right">Δ (current − baseline)</th>
                </tr>
              </thead>
              <tbody>
                {nutrientKeys.map((nut) => {
                  const base = block.season_totals.baseline[nut] || 0;
                  const curr = block.season_totals.current[nut] || 0;
                  const app = block.season_totals.applied[nut] || 0;
                  const delta = curr - base;
                  return (
                    <tr key={nut} className="border-t border-muted">
                      <td className="py-1.5 pr-3 font-medium uppercase">{nut}</td>
                      <td className="py-1.5 pr-3 text-right tabular-nums text-muted-foreground">{base.toFixed(1)}</td>
                      <td className="py-1.5 pr-3 text-right tabular-nums font-medium">{curr.toFixed(1)}</td>
                      <td className="py-1.5 pr-3 text-right tabular-nums text-blue-700">{app.toFixed(1)}</td>
                      <td className={`py-1.5 pr-3 text-right tabular-nums font-medium ${
                        Math.abs(delta) < 0.1 ? "text-muted-foreground" :
                        delta > 0 ? "text-green-700" : "text-red-700"
                      }`}>
                        {Math.abs(delta) < 0.1 ? "—" : (delta > 0 ? "+" : "") + delta.toFixed(1)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Per-month timeline */}
        {block.per_month_diff.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">Timeline</p>
            <div className="space-y-1.5">
              {block.per_month_diff.map((diff) => (
                <MonthRow key={diff.month} diff={diff} />
              ))}
            </div>
          </div>
        )}

        {/* Attributions */}
        {block.attributions.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
              Why the plan changed ({block.attributions.length})
            </p>
            <div className="space-y-1.5">
              {block.attributions.map((attr, i) => (
                <div key={i} className="flex items-start gap-2 rounded border bg-muted/20 px-3 py-2 text-sm">
                  <span className="rounded bg-white px-2 py-0.5 text-xs font-medium capitalize">
                    {attr.kind.replace(/_/g, " ")}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs">{attr.summary || "(no summary)"}</p>
                    {attr.at && (
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {new Date(attr.at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MonthRow({ diff }: { diff: MonthDiff }) {
  const month = MONTH_NAMES[diff.month] || `M${diff.month}`;
  const baselineRate = diff.baseline?.rate_kg_ha;
  const currentRate = diff.current?.rate_kg_ha;
  const appliedRate = diff.actual[0]?.actual_rate_kg_ha;
  const nutrientChanges = Object.entries(diff.nutrient_delta);

  return (
    <div className="flex items-center gap-3 rounded border bg-white px-3 py-2 text-sm">
      <div className="w-12 shrink-0 font-medium">{month}</div>
      <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[diff.status]}`}>
        {STATUS_LABEL[diff.status]}
      </span>
      <div className="flex items-center gap-2 text-xs">
        {diff.baseline ? (
          <span className="text-muted-foreground">{baselineRate?.toFixed(0) ?? "—"} kg</span>
        ) : (
          <span className="text-muted-foreground/50">—</span>
        )}
        <ArrowRight className="size-3 text-muted-foreground/50" />
        {diff.current ? (
          <span className="font-medium">{currentRate?.toFixed(0) ?? "—"} kg</span>
        ) : (
          <span className="text-muted-foreground/50">—</span>
        )}
        {diff.actual.length > 0 && (
          <>
            <span className="text-muted-foreground">·</span>
            <span className="text-blue-700">
              actual {appliedRate?.toFixed(0) ?? "—"} kg
              {diff.actual[0].product_name && ` (${diff.actual[0].product_name})`}
              {diff.actual[0].is_sapling_product === false && " ⚠"}
            </span>
          </>
        )}
      </div>
      {nutrientChanges.length > 0 && (
        <div className="ml-auto flex flex-wrap gap-1 text-xs">
          {nutrientChanges.slice(0, 4).map(([nut, delta]) => (
            <span
              key={nut}
              className={`rounded px-1.5 py-0.5 ${
                delta > 0
                  ? "bg-green-50 text-green-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {nut.toUpperCase()} {delta > 0 ? "+" : ""}{delta.toFixed(1)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
