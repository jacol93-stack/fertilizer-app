"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface UsageData {
  period_days: number;
  total_calls: number;
  total_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  by_user: Array<{ user_id: string; name: string; calls: number; cost_usd: number }>;
  by_operation: Array<{ operation: string; calls: number; cost_usd: number }>;
  recent: Array<{
    id: string;
    created_at: string;
    user_id: string;
    operation: string;
    model: string;
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    metadata: Record<string, unknown>;
  }>;
}

export default function AiUsagePage() {
  const [data, setData] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<UsageData>("/api/admin/ai-usage?days=30")
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <>
        <div className="flex justify-center py-20">
          <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
        </div>
      </>
    );
  }

  if (!data) return null;

  return (
    <>
      <div className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="mb-6 text-2xl font-bold text-[var(--sapling-dark)]">AI Usage</h1>

        {/* Summary cards */}
        <div className="mb-6 grid gap-4 sm:grid-cols-4">
          <Card>
            <CardContent className="py-4 text-center">
              <p className="text-xs font-medium uppercase text-muted-foreground">Total Cost (30d)</p>
              <p className="mt-1 text-2xl font-bold text-[var(--sapling-dark)]">
                ${data.total_cost_usd.toFixed(2)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4 text-center">
              <p className="text-xs font-medium uppercase text-muted-foreground">API Calls</p>
              <p className="mt-1 text-2xl font-bold text-[var(--sapling-dark)]">{data.total_calls}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4 text-center">
              <p className="text-xs font-medium uppercase text-muted-foreground">Input Tokens</p>
              <p className="mt-1 text-2xl font-bold text-[var(--sapling-dark)]">
                {(data.total_input_tokens / 1000).toFixed(1)}k
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4 text-center">
              <p className="text-xs font-medium uppercase text-muted-foreground">Output Tokens</p>
              <p className="mt-1 text-2xl font-bold text-[var(--sapling-dark)]">
                {(data.total_output_tokens / 1000).toFixed(1)}k
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* By user */}
          <Card>
            <CardHeader><CardTitle className="text-base">Cost by User</CardTitle></CardHeader>
            <CardContent>
              {data.by_user.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">No usage yet</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="pb-2 font-medium text-muted-foreground">User</th>
                      <th className="pb-2 text-right font-medium text-muted-foreground">Calls</th>
                      <th className="pb-2 text-right font-medium text-muted-foreground">Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.by_user.map((u) => (
                      <tr key={u.user_id} className="border-b border-muted last:border-0">
                        <td className="py-2 font-medium">{u.name}</td>
                        <td className="py-2 text-right tabular-nums">{u.calls}</td>
                        <td className="py-2 text-right tabular-nums">${u.cost_usd.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>

          {/* By operation */}
          <Card>
            <CardHeader><CardTitle className="text-base">Cost by Operation</CardTitle></CardHeader>
            <CardContent>
              {data.by_operation.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">No usage yet</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="pb-2 font-medium text-muted-foreground">Operation</th>
                      <th className="pb-2 text-right font-medium text-muted-foreground">Calls</th>
                      <th className="pb-2 text-right font-medium text-muted-foreground">Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.by_operation.map((o) => (
                      <tr key={o.operation} className="border-b border-muted last:border-0">
                        <td className="py-2 font-medium">{o.operation}</td>
                        <td className="py-2 text-right tabular-nums">{o.calls}</td>
                        <td className="py-2 text-right tabular-nums">${o.cost_usd.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recent calls */}
        <Card className="mt-6">
          <CardHeader><CardTitle className="text-base">Recent API Calls</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-2 pr-4 font-medium text-muted-foreground">Time</th>
                    <th className="pb-2 pr-4 font-medium text-muted-foreground">Operation</th>
                    <th className="pb-2 pr-4 font-medium text-muted-foreground">Details</th>
                    <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">Tokens</th>
                    <th className="pb-2 text-right font-medium text-muted-foreground">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent.map((r) => (
                    <tr key={r.id} className="border-b border-muted last:border-0">
                      <td className="py-2 pr-4 text-xs text-muted-foreground">
                        {new Date(r.created_at).toLocaleString()}
                      </td>
                      <td className="py-2 pr-4">{r.operation}</td>
                      <td className="py-2 pr-4 text-xs text-muted-foreground">
                        {r.metadata?.lab_name ? `${r.metadata.lab_name}` : ""}
                        {r.metadata?.num_samples ? ` (${r.metadata.num_samples} samples)` : ""}
                      </td>
                      <td className="py-2 pr-4 text-right tabular-nums text-xs">
                        {r.input_tokens + r.output_tokens}
                      </td>
                      <td className="py-2 text-right tabular-nums">${Number(r.cost_usd).toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
