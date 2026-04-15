"use client";

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";
import type { SoilAnalysisRecord } from "./comparison-utils";
import {
  changeDirection,
  changeColor,
  changeBg,
  classColor,
  daysBetween,
  formatDate,
  getRatioName,
  getRatioActual,
  getRatioStatus,
} from "./comparison-utils";

export function SideBySideTable({
  a1,
  a2,
}: {
  a1: SoilAnalysisRecord;
  a2: SoilAnalysisRecord;
}) {
  const sv1 = a1.soil_values || {};
  const sv2 = a2.soil_values || {};
  const cls1 = a1.classifications || {};
  const cls2 = a2.classifications || {};

  const allParams = Array.from(
    new Set([...Object.keys(sv1), ...Object.keys(sv2)])
  ).sort();

  const date1 = a1.analysis_date || a1.created_at?.slice(0, 10) || "";
  const date2 = a2.analysis_date || a2.created_at?.slice(0, 10) || "";
  const gap = daysBetween(date1, date2);

  // Ratios
  const ratios1 = a1.ratio_results || [];
  const ratios2 = a2.ratio_results || [];
  const ratioNames = Array.from(
    new Set([
      ...ratios1.map(getRatioName),
      ...ratios2.map(getRatioName),
    ])
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardContent className="pt-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-lg bg-blue-50 p-3">
              <p className="font-semibold text-blue-800">
                {formatDate(date1)}
              </p>
              <p className="text-blue-600">
                {a1.field || a1.farm || "Unknown"} — {a1.crop || "No crop"}
                {a1.cultivar ? ` (${a1.cultivar})` : ""}
              </p>
              {a1.lab_name && (
                <p className="text-xs text-blue-500">Lab: {a1.lab_name}</p>
              )}
            </div>
            <div className="rounded-lg bg-orange-50 p-3">
              <p className="font-semibold text-orange-800">
                {formatDate(date2)}
              </p>
              <p className="text-orange-600">
                {a2.field || a2.farm || "Unknown"} — {a2.crop || "No crop"}
                {a2.cultivar ? ` (${a2.cultivar})` : ""}
              </p>
              {a2.lab_name && (
                <p className="text-xs text-orange-500">Lab: {a2.lab_name}</p>
              )}
            </div>
          </div>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            {gap} days between analyses
          </p>
        </CardContent>
      </Card>

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
                  <th className="px-3 py-2">Parameter</th>
                  <th className="px-3 py-2 text-right text-blue-600">
                    {formatDate(date1)}
                  </th>
                  <th className="px-3 py-2 text-center">Class</th>
                  <th className="px-3 py-2 text-right text-orange-600">
                    {formatDate(date2)}
                  </th>
                  <th className="px-3 py-2 text-center">Class</th>
                  <th className="px-3 py-2 text-right">Change</th>
                  <th className="px-3 py-2 text-center">Direction</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {allParams.map((param) => {
                  const v1 = sv1[param];
                  const v2 = sv2[param];
                  const c1 = cls1[param] || "";
                  const c2 = cls2[param] || "";
                  const dir = changeDirection(c1, c2);

                  let changeText = "-";
                  let changePct = "";
                  if (v1 != null && v2 != null) {
                    const n1 = Number(v1);
                    const n2 = Number(v2);
                    if (!isNaN(n1) && !isNaN(n2)) {
                      const diff = n2 - n1;
                      changeText = `${diff > 0 ? "+" : ""}${diff.toFixed(1)}`;
                      if (n1 !== 0) {
                        changePct = `(${diff > 0 ? "+" : ""}${((diff / n1) * 100).toFixed(0)}%)`;
                      }
                    }
                  }

                  return (
                    <tr
                      key={param}
                      className={`hover:bg-gray-50 ${changeBg(dir)}`}
                    >
                      <td className="px-3 py-2 font-medium">{param}</td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {v1 != null ? String(v1) : "-"}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {c1 && (
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${classColor(c1)}`}
                          >
                            {c1}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {v2 != null ? String(v2) : "-"}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {c2 && (
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${classColor(c2)}`}
                          >
                            {c2}
                          </span>
                        )}
                      </td>
                      <td className={`px-3 py-2 text-right tabular-nums ${changeColor(dir)}`}>
                        {changeText}{" "}
                        <span className="text-xs text-muted-foreground">
                          {changePct}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-center">
                        {dir === "improved" && (
                          <ArrowUp className="mx-auto size-4 text-green-600" />
                        )}
                        {dir === "worsened" && (
                          <ArrowDown className="mx-auto size-4 text-red-600" />
                        )}
                        {dir === "same" && (
                          <Minus className="mx-auto size-4 text-gray-400" />
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Ratio Comparison */}
      {ratioNames.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Nutrient Ratios</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    <th className="px-3 py-2">Ratio</th>
                    <th className="px-3 py-2 text-right text-blue-600">
                      {formatDate(date1)}
                    </th>
                    <th className="px-3 py-2 text-center">Status</th>
                    <th className="px-3 py-2 text-right text-orange-600">
                      {formatDate(date2)}
                    </th>
                    <th className="px-3 py-2 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {ratioNames.map((name) => {
                    const r1 = ratios1.find((r) => getRatioName(r) === name);
                    const r2 = ratios2.find((r) => getRatioName(r) === name);
                    const v1 = r1 ? getRatioActual(r1) : null;
                    const v2 = r2 ? getRatioActual(r2) : null;
                    const s1 = r1 ? getRatioStatus(r1) : "";
                    const s2 = r2 ? getRatioStatus(r2) : "";

                    const statusColor = (s: string) => {
                      if (s === "Ideal") return "text-green-600";
                      if (s.includes("Below")) return "text-orange-600";
                      if (s.includes("Above")) return "text-blue-600";
                      return "text-gray-500";
                    };

                    return (
                      <tr key={name} className="hover:bg-gray-50">
                        <td className="px-3 py-2 font-medium">{name}</td>
                        <td className="px-3 py-2 text-right tabular-nums">
                          {v1 != null ? v1.toFixed(2) : "-"}
                        </td>
                        <td className={`px-3 py-2 text-center text-xs font-medium ${statusColor(s1)}`}>
                          {s1 || "-"}
                        </td>
                        <td className="px-3 py-2 text-right tabular-nums">
                          {v2 != null ? v2.toFixed(2) : "-"}
                        </td>
                        <td className={`px-3 py-2 text-center text-xs font-medium ${statusColor(s2)}`}>
                          {s2 || "-"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
