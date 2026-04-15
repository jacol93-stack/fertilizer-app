"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface VarianceBlock {
  block_id: string;
  block_name: string;
  crop: string;
  planned_applications: number;
  applied: number;
  pending: number;
  planned_total_rate: number;
  actual_total_rate: number;
  completion_pct: number;
}

interface VarianceData {
  blocks: VarianceBlock[];
  overall: {
    total_planned: number;
    total_applied: number;
    total_pending: number;
    completion_pct: number;
    status: string;
  };
}

interface VarianceViewProps {
  programmeId: string;
}

export function VarianceView({ programmeId }: VarianceViewProps) {
  const [data, setData] = useState<VarianceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<VarianceData>(`/api/programmes/${programmeId}/variance`)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load variance"))
      .finally(() => setLoading(false));
  }, [programmeId]);

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-red-600">{error}</CardContent>
      </Card>
    );
  }

  if (!data || data.blocks.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          No variance data available — record applications to see planned vs actual
        </CardContent>
      </Card>
    );
  }

  const statusColor = (pct: number) => {
    if (pct >= 80) return "text-green-700 bg-green-100";
    if (pct >= 50) return "text-amber-700 bg-amber-100";
    return "text-red-700 bg-red-100";
  };

  return (
    <div className="space-y-6">
      {/* Overall */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Progress</CardTitle>
          <CardDescription>
            {data.overall.total_applied} of {data.overall.total_planned} applications completed
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="h-3 flex-1 overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full rounded-full bg-[var(--sapling-orange)] transition-all"
                style={{ width: `${Math.min(data.overall.completion_pct, 100)}%` }}
              />
            </div>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${statusColor(data.overall.completion_pct)}`}>
              {data.overall.completion_pct.toFixed(0)}%
            </span>
          </div>
          <p className="mt-2 text-xs text-muted-foreground capitalize">
            Status: {data.overall.status.replace("_", " ")}
            {data.overall.total_pending > 0 && ` · ${data.overall.total_pending} pending`}
          </p>
        </CardContent>
      </Card>

      {/* Per-block variance */}
      <Card>
        <CardHeader>
          <CardTitle>Block Variance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 pr-3 font-medium">Block</th>
                  <th className="pb-2 pr-3 font-medium">Crop</th>
                  <th className="pb-2 pr-3 font-medium text-right">Planned Rate</th>
                  <th className="pb-2 pr-3 font-medium text-right">Actual Rate</th>
                  <th className="pb-2 pr-3 font-medium text-right">Variance</th>
                  <th className="pb-2 font-medium text-right">Progress</th>
                </tr>
              </thead>
              <tbody>
                {data.blocks.map((b) => {
                  const variance = b.planned_total_rate > 0
                    ? ((b.actual_total_rate - b.planned_total_rate) / b.planned_total_rate) * 100
                    : 0;
                  return (
                    <tr key={b.block_id} className="border-b last:border-0">
                      <td className="py-2 pr-3 font-medium">{b.block_name}</td>
                      <td className="py-2 pr-3">{b.crop}</td>
                      <td className="py-2 pr-3 text-right tabular-nums">{b.planned_total_rate.toFixed(0)} kg/ha</td>
                      <td className="py-2 pr-3 text-right tabular-nums">{b.actual_total_rate.toFixed(0)} kg/ha</td>
                      <td className={`py-2 pr-3 text-right tabular-nums font-medium ${
                        Math.abs(variance) < 10 ? "text-green-700" : Math.abs(variance) < 25 ? "text-amber-700" : "text-red-700"
                      }`}>
                        {variance > 0 ? "+" : ""}{variance.toFixed(1)}%
                      </td>
                      <td className="py-2 text-right">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColor(b.completion_pct)}`}>
                          {b.applied}/{b.planned_applications}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
