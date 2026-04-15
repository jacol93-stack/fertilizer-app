"use client";

import { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { ChevronDown } from "lucide-react";
import type { SoilAnalysisRecord } from "./comparison-utils";
import { classColor, formatDate, getRatioName, getRatioActual, getRatioStatus } from "./comparison-utils";

function getLabel(a: SoilAnalysisRecord): string {
  const parts = [a.field || a.farm || "Unknown"];
  if (a.crop) parts.push(a.crop);
  return parts.join(" — ");
}

export function MultiFieldTable({ analyses }: { analyses: SoilAnalysisRecord[] }) {
  // Collect all parameters across all analyses
  const allParams = Array.from(
    new Set(analyses.flatMap((a) => Object.keys(a.soil_values || {})))
  ).sort();

  // Collect all ratios
  const allRatios = Array.from(
    new Set(analyses.flatMap((a) => (a.ratio_results || []).map(getRatioName)))
  );

  const labels = analyses.map(getLabel);
  const dates = analyses.map((a) => formatDate(a.analysis_date || a.created_at));

  // Find min/max for each parameter to highlight extremes
  function getParamValues(param: string): (number | null)[] {
    return analyses.map((a) => {
      const v = a.soil_values?.[param];
      if (v == null) return null;
      const n = Number(v);
      return isNaN(n) ? null : n;
    });
  }

  return (
    <div className="space-y-4">
      {/* Header cards */}
      <div className="grid gap-2" style={{ gridTemplateColumns: `160px repeat(${analyses.length}, 1fr)` }}>
        <div />
        {analyses.map((a, i) => (
          <div key={a.id} className="rounded-lg border bg-gray-50 p-2.5 text-center">
            <p className="text-xs font-semibold text-[var(--sapling-dark)]">{labels[i]}</p>
            <p className="text-xs text-muted-foreground">{dates[i]}</p>
            {a.cultivar && <p className="text-xs text-muted-foreground">{a.cultivar}</p>}
            {a.lab_name && <p className="text-xs text-muted-foreground">Lab: {a.lab_name}</p>}
          </div>
        ))}
      </div>

      {/* Soil Values Table */}
      <Card>
        <CardHeader>
          <CardTitle>Soil Values</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-3 py-2 w-36">Parameter</th>
                  {labels.map((label, i) => (
                    <th key={i} className="px-3 py-2 text-center">{label}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {allParams.map((param) => {
                  const values = getParamValues(param);
                  const numericValues = values.filter((v): v is number => v !== null);
                  const min = numericValues.length > 0 ? Math.min(...numericValues) : null;
                  const max = numericValues.length > 0 ? Math.max(...numericValues) : null;

                  return (
                    <tr key={param} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-medium text-[var(--sapling-dark)]">{param}</td>
                      {analyses.map((a, i) => {
                        const v = a.soil_values?.[param];
                        const cls = a.classifications?.[param] || "";
                        const numVal = values[i];
                        const isMin = numVal !== null && numVal === min && min !== max;
                        const isMax = numVal !== null && numVal === max && min !== max;

                        return (
                          <td key={i} className="px-3 py-2 text-center">
                            <span className={`tabular-nums ${isMin ? "text-red-600 font-medium" : isMax ? "text-green-600 font-medium" : ""}`}>
                              {v != null ? String(v) : "-"}
                            </span>
                            {cls && (
                              <span className={`ml-1.5 inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-medium ${classColor(cls)}`}>
                                {cls}
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Ratio Table */}
      {allRatios.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Nutrient Ratios</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    <th className="px-3 py-2 w-36">Ratio</th>
                    {labels.map((label, i) => (
                      <th key={i} className="px-3 py-2 text-center">{label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {allRatios.map((name) => (
                    <tr key={name} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-medium text-[var(--sapling-dark)]">{name}</td>
                      {analyses.map((a, i) => {
                        const r = (a.ratio_results || []).find((r) => getRatioName(r) === name);
                        const val = r ? getRatioActual(r) : null;
                        const status = r ? getRatioStatus(r) : "";
                        const statusColor =
                          status === "Ideal" ? "text-green-600" :
                          status.includes("Below") ? "text-orange-600" :
                          status.includes("Above") ? "text-blue-600" : "";

                        return (
                          <td key={i} className="px-3 py-2 text-center">
                            <span className="tabular-nums">{val != null ? val.toFixed(2) : "-"}</span>
                            {status && (
                              <span className={`ml-1.5 text-[10px] font-medium ${statusColor}`}>
                                {status}
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
