"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { AlertTriangle } from "lucide-react";

interface LeafResultsProps {
  result: Record<string, unknown>;
}

export function LeafResults({ result }: LeafResultsProps) {
  const deficiencies: Array<{ element: string; shortfall_pct?: number }> =
    (result.deficiencies as Array<{ element: string; shortfall_pct?: number }>) || [];
  const foliarRecs = result.foliar_recommendations as Record<string, unknown> | undefined;
  const recommendations: Array<{ severity?: string; action?: string }> =
    (result.recommendations as Array<{ severity?: string; action?: string }>) || [];

  return (
    <div className="space-y-6">
      {/* Classifications */}
      <Card>
        <CardHeader>
          <CardTitle>Leaf Classifications</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {Object.entries(
              (result.classifications || {}) as Record<string, string>
            ).map(([elem, cls]) => (
              <div
                key={elem}
                className="flex items-center justify-between rounded-md border px-3 py-2"
              >
                <span className="text-sm font-medium">{elem}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    cls === "Deficient"
                      ? "bg-red-100 text-red-700"
                      : cls === "Low"
                        ? "bg-orange-100 text-orange-700"
                        : cls === "Sufficient"
                          ? "bg-green-100 text-green-700"
                          : cls === "High"
                            ? "bg-blue-100 text-blue-700"
                            : cls === "Excess"
                              ? "bg-purple-100 text-purple-700"
                              : "bg-gray-100 text-gray-700"
                  }`}
                >
                  {cls}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {deficiencies.length > 0 ? (
        <Card className="border-amber-200">
          <CardHeader>
            <CardTitle className="text-amber-800">Deficiencies Detected</CardTitle>
          </CardHeader>
          <CardContent>
            {deficiencies.map((d, i) => (
              <div
                key={i}
                className="flex items-center justify-between border-b border-muted py-2 last:border-0"
              >
                <span className="font-medium text-amber-800">
                  {d.element}
                </span>
                <span className="text-sm text-amber-700">
                  {d.shortfall_pct?.toFixed(0)}% below sufficient
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {foliarRecs?.recommendations ? (
        <Card className="border-2 border-[var(--sapling-orange)]">
          <CardHeader>
            <CardTitle>Recommended Foliar Sprays</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {(foliarRecs.recommendations as Array<Record<string, unknown>>)?.map((rec, i) => (
              <div key={i} className="rounded-lg border p-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium">{rec.product_name as string}</p>
                  <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                    {rec.coverage_pct as number}% coverage
                  </span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  Apply {(rec.application_rate_kg_ha as number)?.toFixed(1)} kg/ha
                  {rec.dilution ? ` — ${String(rec.dilution)}` : ""}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {recommendations.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent>
            {recommendations.map((rec, i) => (
              <div
                key={i}
                className="flex items-start gap-2 border-b border-muted py-2 last:border-0"
              >
                <AlertTriangle
                  className={`mt-0.5 size-4 shrink-0 ${
                    rec.severity === "critical" ? "text-red-500" : "text-amber-500"
                  }`}
                />
                <p className="text-sm">{rec.action}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
