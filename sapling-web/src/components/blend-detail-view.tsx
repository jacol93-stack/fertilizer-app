"use client";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Download, Loader2 } from "lucide-react";
import { useState } from "react";

interface RecipeRow {
  material: string;
  type: string | null;
  kg: number;
  pct: number;
  cost: number;
}

interface NutrientRow {
  nutrient: string;
  target: number;
  actual: number;
  diff: number;
  kg_per_ton: number;
}

interface BlendData {
  id: string;
  blend_name: string | null;
  targets: Record<string, number> | null;
  batch_size: number | null;
  min_compost_pct: number | null;
  cost_per_ton: number | null;
  selling_price: number | null;
  recipe: RecipeRow[] | null;
  nutrients: NutrientRow[] | null;
  farm: string | null;
  client: string | null;
  created_at: string | null;
}

export function BlendDetailView({
  blend,
  isAdmin,
}: {
  blend: BlendData;
  isAdmin: boolean;
}) {
  const [downloading, setDownloading] = useState(false);

  async function downloadPdf() {
    setDownloading(true);
    try {
      const blob = await api.getPdf(`/api/reports/blend/${blend.id}/pdf`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `blend_${blend.blend_name || blend.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // silently fail
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-[var(--sapling-dark)]">
          {blend.blend_name || "Unnamed Blend"}
        </h3>
        {blend.targets && (
          <p className="mt-0.5 text-sm font-medium text-[var(--sapling-orange)]">
            {Math.round(blend.targets.N || 0)}:{Math.round(blend.targets.P || 0)}:{Math.round(blend.targets.K || 0)}
          </p>
        )}
        {blend.created_at && (
          <p className="mt-1 text-xs text-muted-foreground">
            {new Date(blend.created_at).toLocaleDateString()}
          </p>
        )}
      </div>

      {/* Summary — admin sees all, agent sees batch + compost only */}
      <div className={`grid gap-3 ${isAdmin ? "grid-cols-2 sm:grid-cols-4" : "grid-cols-2"}`}>
        <div className="rounded-lg bg-muted px-3 py-2">
          <p className="text-xs text-muted-foreground">Batch</p>
          <p className="font-semibold">{blend.batch_size ?? "-"} kg</p>
        </div>
        {isAdmin && (
          <div className="rounded-lg bg-muted px-3 py-2">
            <p className="text-xs text-muted-foreground">Cost/ton</p>
            <p className="font-semibold">
              {blend.cost_per_ton != null ? `R${blend.cost_per_ton.toFixed(0)}` : "-"}
            </p>
          </div>
        )}
        {isAdmin && (
          <div className="rounded-lg bg-muted px-3 py-2">
            <p className="text-xs text-muted-foreground">Selling Price</p>
            <p className="font-semibold">
              {blend.selling_price ? `R${blend.selling_price.toFixed(0)}` : "-"}
            </p>
          </div>
        )}
        <div className="rounded-lg bg-muted px-3 py-2">
          <p className="text-xs text-muted-foreground">Compost</p>
          <p className="font-semibold">{blend.min_compost_pct ?? 0}%</p>
        </div>
      </div>

      {/* Recipe Table — admin only */}
      {isAdmin && blend.recipe && blend.recipe.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-[var(--sapling-dark)]">
            Recipe
          </h4>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-3 py-2">Material</th>
                  <th className="px-3 py-2 text-right">kg</th>
                  <th className="px-3 py-2 text-right">%</th>
                  <th className="px-3 py-2 text-right">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {blend.recipe.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium">{row.material}</td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {row.kg.toFixed(1)}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {row.pct.toFixed(1)}%
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      R{row.cost.toFixed(0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Nutrient Breakdown — visible to all */}
      {blend.nutrients && blend.nutrients.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold text-[var(--sapling-dark)]">
            Nutrient Breakdown
          </h4>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-3 py-2">Nutrient</th>
                  <th className="px-3 py-2 text-right">Target</th>
                  <th className="px-3 py-2 text-right">Actual</th>
                  <th className="px-3 py-2 text-right">Diff</th>
                  <th className="px-3 py-2 text-right">kg/ton</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {blend.nutrients.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium">{row.nutrient}</td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {row.target.toFixed(2)}%
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {row.actual.toFixed(2)}%
                    </td>
                    <td
                      className={`px-3 py-2 text-right tabular-nums ${
                        row.diff < 0 ? "text-red-600" : "text-green-600"
                      }`}
                    >
                      {row.diff > 0 ? "+" : ""}
                      {row.diff.toFixed(2)}%
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {row.kg_per_ton.toFixed(1)}
                    </td>
                  </tr>
                ))}
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
