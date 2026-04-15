"use client";

import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { Classification, RatioResult } from "../types";

interface DiagnosticSummaryProps {
  classifications: Classification;
  ratios: RatioResult[];
  leafResult?: Record<string, unknown> | null;
}

export function DiagnosticSummary({ classifications, ratios, leafResult }: DiagnosticSummaryProps) {
  // Count soil classification levels
  const entries = Object.entries(classifications);
  const concerns: string[] = [];
  const healthy: string[] = [];

  for (const [param, cls] of entries) {
    const lower = cls.toLowerCase();
    if (lower.includes("very low") || lower.includes("very high")) {
      concerns.push(`${param} is ${cls}`);
    } else if (lower.includes("low") || lower.includes("high")) {
      concerns.push(`${param} is ${cls}`);
    } else {
      healthy.push(param);
    }
  }

  // Ratio imbalances
  const ratioIssues: string[] = [];
  for (const r of ratios) {
    const status = String(r.Status || r.status || "").toLowerCase();
    const name = String(r.Ratio || r.ratio_name || "");
    if (status && status !== "ideal" && status !== "optimal" && status !== "ok") {
      ratioIssues.push(`${name} ${status}`);
    }
  }

  // Leaf deficiencies
  const leafDeficiencies = (leafResult?.deficiencies as Array<Record<string, unknown>> | undefined) || [];

  // Cross-reference soil + leaf
  const crossIssues: string[] = [];
  if (leafResult?.classifications) {
    const leafCls = leafResult.classifications as Record<string, string>;
    for (const [elem, cls] of Object.entries(leafCls)) {
      if (cls === "Deficient" || cls === "Low") {
        // Check if soil also shows this element as low
        const soilCls = classifications[elem]?.toLowerCase() || "";
        if (soilCls.includes("low") || soilCls.includes("very low")) {
          crossIssues.push(`${elem} low in both soil and leaf — priority correction`);
        }
      }
    }
  }

  const criticalConcerns = Object.entries(classifications).filter(([, cls]) => {
    const l = cls.toLowerCase();
    return l.includes("very low") || l.includes("very high");
  });

  const totalChecked = entries.length + (leafResult ? Object.keys((leafResult.classifications || {}) as Record<string, string>).length : 0);
  const totalOk = healthy.length + (leafResult
    ? Object.values((leafResult.classifications || {}) as Record<string, string>).filter(
        (c) => c === "Sufficient"
      ).length
    : 0);

  return (
    <Card className={criticalConcerns.length > 0 ? "border-amber-200 bg-amber-50/50" : "border-green-200 bg-green-50/50"}>
      <CardContent className="pt-6">
        <div className="flex items-start gap-3">
          {criticalConcerns.length > 0 ? (
            <AlertTriangle className="mt-0.5 size-5 shrink-0 text-amber-600" />
          ) : (
            <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-green-600" />
          )}
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold">
                {concerns.length} concern{concerns.length !== 1 ? "s" : ""} found
              </span>
              <span className="text-sm text-muted-foreground">
                {totalOk}/{totalChecked} parameters OK
              </span>
            </div>

            {/* Cross-reference issues (highest priority) */}
            {crossIssues.length > 0 && (
              <div className="space-y-1">
                {crossIssues.map((issue, i) => (
                  <p key={i} className="text-sm font-medium text-red-700">{issue}</p>
                ))}
              </div>
            )}

            {/* Critical soil concerns */}
            {criticalConcerns.length > 0 && (
              <div className="space-y-0.5">
                {criticalConcerns.map(([param, cls]) => (
                  <p key={param} className="text-sm text-amber-800">
                    <span className="font-medium">{param}</span> is {cls}
                  </p>
                ))}
              </div>
            )}

            {/* Ratio imbalances */}
            {ratioIssues.length > 0 && (
              <p className="text-sm text-muted-foreground">
                Ratio imbalances: {ratioIssues.join(", ")}
              </p>
            )}

            {/* Leaf deficiencies */}
            {leafDeficiencies.length > 0 && (
              <p className="text-sm text-muted-foreground">
                Leaf deficiencies: {leafDeficiencies.map((d) => d.element as string).join(", ")}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
