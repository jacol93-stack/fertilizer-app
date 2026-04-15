"use client";

import { useState, useEffect } from "react";
import { api, API_URL } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft, ChevronDown, Download } from "lucide-react";
import type { ComparisonResult } from "./comparison-utils";
import { SideBySideTable } from "./SideBySideTable";
import { MultiFieldTable } from "./MultiFieldTable";
import { TrendCharts } from "./TrendCharts";
import { SnapshotCharts } from "./SnapshotCharts";
import { CropImpactPanel } from "./CropImpactPanel";
import { RecommendationsPanel } from "./RecommendationsPanel";

export function SoilComparisonView({
  analysisIds,
  onBack,
}: {
  analysisIds: string[];
  onBack: () => void;
}) {
  const [data, setData] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCharts, setShowCharts] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    async function fetchComparison() {
      setLoading(true);
      setError(null);
      try {
        const result = await api.post<ComparisonResult>("/api/soil/compare", {
          analysis_ids: analysisIds,
        });
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load comparison");
      } finally {
        setLoading(false);
      }
    }
    fetchComparison();
  }, [analysisIds]);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-3 py-8 text-center">
        <p className="text-sm text-red-600">{error || "No data"}</p>
        <Button variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="size-3.5" />
          Modify Selection
        </Button>
      </div>
    );
  }

  const isTimeline = data.comparison_type === "timeline";
  const count = data.analyses.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="size-3.5" />
          Modify Selection
        </Button>
        <div className="flex items-center gap-3">
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
            isTimeline
              ? "bg-green-100 text-green-700"
              : "bg-blue-100 text-blue-700"
          }`}>
            {isTimeline ? "Timeline" : "Snapshot"}
          </span>
          <p className="text-sm text-muted-foreground">
            Comparing {count} analyses
            {isTimeline ? " (same field over time)" : " (different fields)"}
          </p>
          <Button
            variant="outline"
            size="sm"
            disabled={downloading}
            onClick={async () => {
              setDownloading(true);
              try {
                const { createClient } = await import("@/lib/supabase");
                const supabase = createClient();
                const { data: { session } } = await supabase.auth.getSession();
                const res = await fetch(`${API_URL}/api/reports/soil/compare/pdf`, {
                  method: "POST",
                  headers: {
                    "Authorization": `Bearer ${session?.access_token}`,
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({ analysis_ids: analysisIds }),
                });
                if (!res.ok) throw new Error("PDF generation failed");
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "soil_comparison.pdf";
                a.click();
                URL.revokeObjectURL(url);
              } catch {} finally { setDownloading(false); }
            }}
          >
            {downloading ? <Loader2 className="size-3.5 animate-spin" /> : <Download className="size-3.5" />}
            PDF
          </Button>
        </div>
      </div>

      {/* Main table comparison */}
      {count === 2 ? (
        <SideBySideTable a1={data.analyses[0]} a2={data.analyses[1]} />
      ) : (
        <MultiFieldTable analyses={data.analyses} />
      )}

      {/* Charts — collapsible, secondary */}
      {count >= 3 && (
        <div>
          <button
            type="button"
            onClick={() => setShowCharts(!showCharts)}
            className="flex w-full items-center justify-between rounded-lg border bg-gray-50 px-4 py-3 text-sm font-medium text-[var(--sapling-dark)] hover:bg-gray-100"
          >
            <span>{isTimeline ? "Trend Charts" : "Comparison Charts"}</span>
            <ChevronDown className={`size-4 text-muted-foreground transition-transform ${showCharts ? "rotate-180" : ""}`} />
          </button>
          {showCharts && (
            <div className="mt-4">
              {isTimeline ? (
                <TrendCharts data={data} />
              ) : (
                <SnapshotCharts data={data} />
              )}
            </div>
          )}
        </div>
      )}

      {/* Crop Impact — timeline only */}
      {isTimeline && data.crop_impact.length > 0 && (
        <CropImpactPanel impacts={data.crop_impact} />
      )}

      {/* Recommendations */}
      {isTimeline && data.recommendations.length > 0 && (
        <RecommendationsPanel recommendations={data.recommendations} />
      )}
      {!isTimeline && data.recommendations.length > 0 && (
        <RecommendationsPanel
          recommendations={data.recommendations.filter(
            (r) => r.type === "success" || r.type === "info"
          )}
        />
      )}
    </div>
  );
}
