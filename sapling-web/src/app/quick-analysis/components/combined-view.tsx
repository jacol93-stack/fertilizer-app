"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Save, Check, ChevronRight, Download, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { DiagnosticSummary } from "./diagnostic-summary";
import { SoilResults } from "./soil-results";
import { LeafResults } from "./leaf-results";
import type { Classification, RatioResult } from "../types";

interface CombinedViewProps {
  // Soil data
  hasSoil: boolean;
  classifications: Classification;
  soilValues: Record<string, string>;
  soilThresholds: Record<string, { very_low_max: number; low_max: number; optimal_max: number; high_max: number }>;
  ratios: RatioResult[];
  // Context for PDF
  customer?: string;
  farm?: string;
  field?: string;
  cropName?: string;
  cultivar?: string;
  yieldTarget?: string;
  yieldUnit?: string;
  labName?: string;
  analysisDate?: string;
  // Leaf data
  hasLeaf: boolean;
  leafResult: Record<string, unknown> | null;
  // Actions
  savedAnalysisId: string | null;
  saving: boolean;
  onSaveAnalysis: () => void;
  onBuildProgramme: () => void;
  onBack: () => void;
}

export function CombinedView({
  hasSoil,
  classifications,
  soilValues,
  soilThresholds,
  ratios,
  customer,
  farm,
  field,
  cropName,
  cultivar,
  yieldTarget,
  yieldUnit,
  labName,
  analysisDate,
  hasLeaf,
  leafResult,
  savedAnalysisId,
  saving,
  onSaveAnalysis,
  onBuildProgramme,
  onBack,
}: CombinedViewProps) {
  const [downloading, setDownloading] = useState(false);

  const handleDownloadPdf = async () => {
    setDownloading(true);
    try {
      let blob: Blob;
      if (savedAnalysisId) {
        blob = await api.getPdf(`/api/reports/soil/${savedAnalysisId}/pdf`);
      } else {
        // Build numeric soil values for the API
        const numericValues: Record<string, number> = {};
        for (const [k, v] of Object.entries(soilValues)) {
          const n = parseFloat(v);
          if (!isNaN(n)) numericValues[k] = n;
        }
        blob = await api.postPdf("/api/reports/soil/diagnostic/pdf", {
          customer: customer || "",
          farm: farm || "",
          field: field || "",
          crop_name: cropName || "",
          cultivar: cultivar || "",
          yield_target: yieldTarget ? parseFloat(yieldTarget) : null,
          yield_unit: yieldUnit || "",
          lab_name: labName || "",
          analysis_date: analysisDate || "",
          soil_values: numericValues,
          classifications,
          ratio_results: ratios,
          soil_thresholds: soilThresholds,
        });
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `soil_analysis_${customer || "report"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Failed to generate report");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Diagnostic Summary */}
      {hasSoil && (
        <DiagnosticSummary
          classifications={classifications}
          ratios={ratios}
          leafResult={hasLeaf ? leafResult : null}
        />
      )}

      {/* Soil + Leaf side by side on desktop, stacked on mobile */}
      {hasSoil && hasLeaf && leafResult ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <h3 className="mb-4 text-lg font-semibold">Soil Analysis</h3>
            <SoilResults
              classifications={classifications}
              soilValues={soilValues}
              soilThresholds={soilThresholds}
              ratios={ratios}
            />
          </div>
          <div>
            <h3 className="mb-4 text-lg font-semibold">Leaf Analysis</h3>
            <LeafResults result={leafResult} />
          </div>
        </div>
      ) : hasSoil ? (
        <SoilResults
          classifications={classifications}
          soilValues={soilValues}
          soilThresholds={soilThresholds}
          ratios={ratios}
        />
      ) : hasLeaf && leafResult ? (
        <LeafResults result={leafResult} />
      ) : null}

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        {hasSoil && (
          <Button variant="outline" onClick={handleDownloadPdf} disabled={downloading}>
            {downloading ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
            Download Report
          </Button>
        )}
        {savedAnalysisId ? (
          <Button variant="outline" disabled className="text-green-600">
            <Check className="size-4" />
            Analysis Saved
          </Button>
        ) : (
          <Button
            variant="outline"
            onClick={onSaveAnalysis}
            disabled={saving}
          >
            <Save className="size-4" />
            {saving ? "Saving..." : "Save to Client"}
          </Button>
        )}
        <Button
          onClick={onBuildProgramme}
          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
        >
          <ChevronRight className="size-4" />
          Build a Programme
        </Button>
      </div>
    </div>
  );
}
