"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Save } from "lucide-react";

interface Material {
  id: number;
  material: string;
  type: string | null;
  cost_per_ton: number;
}

interface Markup {
  material: string;
  markup_pct: number;
}

interface RowState {
  materialId: number;
  materialName: string;
  type: string | null;
  rawCost: number;
  markupPct: number;
  dirty: boolean;
  saving: boolean;
}

export default function MarkupsPage() {
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [rows, setRows] = useState<RowState[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [materials, markups] = await Promise.all([
        api.get<Material[]>("/api/materials"),
        api.get<Markup[]>("/api/materials/markups"),
      ]);
      const markupMap = new Map(markups.map((m) => [m.material, m.markup_pct]));
      setRows(
        materials.map((mat) => ({
          materialId: mat.id,
          materialName: mat.material,
          type: mat.type,
          rawCost: mat.cost_per_ton,
          markupPct: markupMap.get(mat.material) ?? 0,
          dirty: false,
          saving: false,
        }))
      );
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading && !isAdmin) {
      router.replace("/");
      return;
    }
    if (!authLoading && isAdmin) {
      fetchData();
    }
  }, [authLoading, isAdmin, router, fetchData]);

  function updateMarkup(idx: number, value: number) {
    setRows((prev) =>
      prev.map((r, i) => (i === idx ? { ...r, markupPct: value, dirty: true } : r))
    );
  }

  async function saveRow(idx: number) {
    const row = rows[idx];
    setRows((prev) =>
      prev.map((r, i) => (i === idx ? { ...r, saving: true } : r))
    );
    try {
      const matId = row.materialId || row.materialName;
      await api.put(`/api/materials/${encodeURIComponent(matId)}/markup`, {
        markup_pct: row.markupPct,
      });
      setRows((prev) =>
        prev.map((r, i) =>
          i === idx ? { ...r, saving: false, dirty: false } : r
        )
      );
      toast.success(`Markup updated for ${row.materialName}`);
    } catch (err) {
      setRows((prev) =>
        prev.map((r, i) => (i === idx ? { ...r, saving: false } : r))
      );
      toast.error(err instanceof Error ? err.message : "Save failed");
    }
  }

  const [bulkPct, setBulkPct] = useState("");

  async function saveAll() {
    // If bulk value is set, apply it to all rows first
    const val = parseFloat(bulkPct);
    let toSave = rows;
    if (!isNaN(val) && val >= 0 && bulkPct !== "") {
      toSave = rows.map((r) => ({ ...r, markupPct: val, dirty: true }));
      setRows(toSave);
    }

    const dirtyIndices = toSave
      .map((r, i) => (r.dirty ? i : -1))
      .filter((i) => i !== -1);

    // If nothing dirty but bulk was set, save all
    const indices = dirtyIndices.length > 0 ? dirtyIndices :
      (!isNaN(val) && val >= 0 && bulkPct !== "" ? toSave.map((_, i) => i) : []);

    if (indices.length === 0) {
      toast.info("No changes to save");
      return;
    }

    try {
      const items = indices.map((i) => ({
        material: toSave[i].materialName,
        markup_pct: toSave[i].markupPct,
      }));
      await api.post("/api/materials/markups/bulk", items);
      setRows((prev) => prev.map((r) => ({ ...r, dirty: false, saving: false })));
      toast.success(`Markups saved for ${indices.length} materials`);
      setBulkPct("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    }
  }

  if (authLoading) return null;

  return (
    <>
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Markups</h1>
            <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
              Set markup percentages on raw material costs for agent pricing
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 rounded-lg border px-2 py-1">
              <span className="text-xs text-muted-foreground whitespace-nowrap">Set all to</span>
              <Input
                type="number"
                min="0"
                step="5"
                placeholder="%"
                value={bulkPct}
                onChange={(e) => setBulkPct(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") saveAll(); }}
                className="h-7 w-16 text-center text-sm"
              />
            </div>
            <Button onClick={saveAll}>
              <Save className="size-4" />
              Save All
            </Button>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="mt-8 flex justify-center">
            <div className="size-8 animate-spin rounded-full border-4 border-gray-200 border-t-[var(--sapling-orange)]" />
          </div>
        ) : (
          <div className="mt-6 overflow-x-auto rounded-xl border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Material</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3 text-right">Raw Cost/ton</th>
                  <th className="px-4 py-3 text-right">Markup %</th>
                  <th className="px-4 py-3 text-right">Agent Price</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map((row, idx) => {
                  const agentPrice = row.rawCost * (1 + row.markupPct / 100);
                  return (
                    <tr
                      key={row.materialId || row.materialName}
                      className={row.dirty ? "bg-orange-50/50" : ""}
                    >
                      <td className="px-4 py-3 font-medium text-[var(--sapling-dark)]">
                        {row.materialName}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{row.type ?? "-"}</td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        R{row.rawCost.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Input
                          type="number"
                          step="0.5"
                          min="0"
                          className="ml-auto w-24 text-right"
                          value={row.markupPct}
                          onChange={(e) =>
                            updateMarkup(idx, parseFloat(e.target.value) || 0)
                          }
                        />
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums font-medium text-[var(--sapling-orange)]">
                        R{agentPrice.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => saveRow(idx)}
                          disabled={!row.dirty || row.saving}
                        >
                          {row.saving ? "..." : "Save"}
                        </Button>
                      </td>
                    </tr>
                  );
                })}
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                      No materials found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
