"use client";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Download, Loader2 } from "lucide-react";
import { useState } from "react";

interface RatioResult {
  ratio_name?: string;
  Ratio?: string;
  actual?: number;
  Actual?: number;
  ideal_min?: number;
  ideal_max?: number;
  Ideal_Min?: number;
  Ideal_Max?: number;
  status?: string;
  Status?: string;
}

interface NutrientTarget {
  Nutrient: string;
  Per_Unit?: number;
  per_unit?: number;
  Base_Req_kg_ha?: number;
  base_req?: number;
  Classification?: string;
  classification?: string;
  Factor?: number;
  factor?: number;
  Target_kg_ha?: number;
}

interface SoilData {
  id: string;
  crop: string | null;
  cultivar: string | null;
  yield_target: number | null;
  yield_unit: string | null;
  lab_name: string | null;
  analysis_date: string | null;
  total_cost_ha: number | null;
  soil_values: Record<string, number | string | null> | null;
  classifications: Record<string, string> | null;
  ratio_results: RatioResult[] | null;
  nutrient_targets: NutrientTarget[] | null;
  farm: string | null;
  field: string | null;
  created_at: string | null;
}

function classColor(c: string): string {
  const lower = (c || "").toLowerCase();
  if (lower === "ideal" || lower === "optimal" || lower === "ok")
    return "bg-green-100 text-green-700";
  if (lower.includes("very low")) return "bg-red-100 text-red-700";
  if (lower.includes("below") || lower === "low")
    return "bg-orange-100 text-orange-700";
  if (lower.includes("very high")) return "bg-purple-100 text-purple-700";
  if (lower.includes("above") || lower === "high")
    return "bg-blue-100 text-blue-700";
  return "bg-gray-100 text-gray-700";
}

function ratioStatusColor(s: string): string {
  const lower = (s || "").toLowerCase();
  if (lower === "ideal" || lower === "within range") return "text-green-600";
  if (lower.includes("below")) return "text-orange-600";
  if (lower.includes("above")) return "text-blue-600";
  return "text-gray-600";
}

export function SoilDetailView({ soil }: { soil: SoilData }) {
  const [downloading, setDownloading] = useState(false);

  async function downloadPdf() {
    setDownloading(true);
    try {
      const blob = await api.getPdf(`/api/reports/soil/${soil.id}/pdf`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `soil_analysis_${soil.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently fail
    } finally {
      setDownloading(false);
    }
  }

  const soilEntries = soil.soil_values
    ? Object.entries(soil.soil_values).filter(
        ([, v]) => v !== null && v !== ""
      )
    : [];

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-[var(--sapling-dark)]">
          {soil.crop || "Unknown Crop"}
          {soil.cultivar ? ` — ${soil.cultivar}` : ""}
        </h3>
        <div className="mt-1 flex flex-wrap gap-3 text-sm text-muted-foreground">
          {soil.yield_target && (
            <span>
              Yield: {soil.yield_target} {soil.yield_unit || "t/ha"}
            </span>
          )}
          {soil.lab_name && <span>Lab: {soil.lab_name}</span>}
          {soil.analysis_date && <span>Date: {soil.analysis_date}</span>}
          {soil.farm && <span>Farm: {soil.farm}</span>}
          {soil.field && <span>Field: {soil.field}</span>}
        </div>
        {soil.total_cost_ha != null && (
          <p className="mt-1 text-sm font-medium text-[var(--sapling-orange)]">
            Total cost: R{soil.total_cost_ha.toFixed(0)}/ha
          </p>
        )}
      </div>

      {/* Soil Values + Classifications */}
      {soilEntries.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-[var(--sapling-dark)]">
            Soil Values
          </h4>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-3 py-2">Parameter</th>
                  <th className="px-3 py-2 text-right">Value</th>
                  {soil.classifications && (
                    <th className="px-3 py-2 text-center">Classification</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {soilEntries.map(([param, val]) => (
                  <tr key={param} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium">{param}</td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {val}
                    </td>
                    {soil.classifications && (
                      <td className="px-3 py-2 text-center">
                        {soil.classifications[param] && (
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${classColor(
                              soil.classifications[param]
                            )}`}
                          >
                            {soil.classifications[param]}
                          </span>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Ratio Results */}
      {soil.ratio_results && soil.ratio_results.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-[var(--sapling-dark)]">
            Nutrient Ratios
          </h4>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-3 py-2">Ratio</th>
                  <th className="px-3 py-2 text-right">Actual</th>
                  <th className="px-3 py-2 text-right">Ideal Range</th>
                  <th className="px-3 py-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {soil.ratio_results.map((r, i) => {
                  const name = r.ratio_name || r.Ratio || "-";
                  const actual = r.actual ?? r.Actual;
                  const min = r.ideal_min ?? r.Ideal_Min;
                  const max = r.ideal_max ?? r.Ideal_Max;
                  const status = r.status || r.Status || "";
                  return (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-medium">{name}</td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {actual != null ? Number(actual).toFixed(2) : "-"}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {min != null && max != null
                          ? `${Number(min).toFixed(1)} – ${Number(max).toFixed(1)}`
                          : "-"}
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span
                          className={`text-xs font-medium ${ratioStatusColor(status)}`}
                        >
                          {status || "-"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Nutrient Targets */}
      {soil.nutrient_targets && soil.nutrient_targets.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-[var(--sapling-dark)]">
            Nutrient Targets
          </h4>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-3 py-2">Nutrient</th>
                  <th className="px-3 py-2 text-right">Base (kg/ha)</th>
                  <th className="px-3 py-2 text-center">Classification</th>
                  <th className="px-3 py-2 text-right">Factor</th>
                  <th className="px-3 py-2 text-right">Target (kg/ha)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {soil.nutrient_targets.map((t, i) => {
                  const baseReq = t.Base_Req_kg_ha ?? t.base_req;
                  const cls = t.Classification || t.classification || "";
                  const factor = t.Factor ?? t.factor;
                  return (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-medium">{t.Nutrient}</td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {baseReq != null ? Number(baseReq).toFixed(1) : "-"}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {cls && (
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${classColor(cls)}`}
                          >
                            {cls}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {factor != null ? Number(factor).toFixed(2) : "-"}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums font-medium">
                        {t.Target_kg_ha != null
                          ? Number(t.Target_kg_ha).toFixed(1)
                          : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Download PDF */}
      <Button variant="outline" onClick={downloadPdf} disabled={downloading}>
        {downloading ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Download className="size-4" />
        )}
        Download PDF
      </Button>
    </div>
  );
}
