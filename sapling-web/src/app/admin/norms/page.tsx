"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Save } from "lucide-react";

const TABS = [
  { key: "requirements", label: "Crop Requirements" },
  { key: "sufficiency", label: "Soil Sufficiency" },
  { key: "adjustment", label: "Adjustment Factors" },
  { key: "ratios", label: "Ideal Ratios" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

const NUTRIENT_COLS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"];

export default function NormsPage() {
  const { isAdmin, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabKey>("requirements");
  const [data, setData] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editedRows, setEditedRows] = useState<Map<number, Record<string, unknown>>>(new Map());
  const [saving, setSaving] = useState(false);

  const fetchTab = useCallback(async (tab: TabKey) => {
    setLoading(true);
    setEditedRows(new Map());
    setError(null);
    try {
      let path: string;
      switch (tab) {
        case "requirements":
          path = "/api/crop-norms/admin";
          break;
        case "sufficiency":
          path = "/api/crop-norms/sufficiency";
          break;
        case "adjustment":
          path = "/api/crop-norms/adjustment-factors";
          break;
        case "ratios":
          path = "/api/crop-norms/ratios";
          break;
      }
      const result = await api.get<Record<string, unknown>[]>(path);
      // Sort by primary column — adjustment factors grouped by nutrient_group then classification
      if (tab === "adjustment") {
        const groupOrder = ["N", "P", "cations", "micro"];
        const classOrder = ["Very Low", "Low", "Optimal", "High", "Very High"];
        result.sort((a, b) => {
          const gA = groupOrder.indexOf(String(a.nutrient_group || ""));
          const gB = groupOrder.indexOf(String(b.nutrient_group || ""));
          if (gA !== gB) return gA - gB;
          return classOrder.indexOf(String(a.classification || "")) - classOrder.indexOf(String(b.classification || ""));
        });
      } else {
        const sortKey = tab === "requirements" ? "crop" : tab === "sufficiency" ? "parameter" : "ratio";
        result.sort((a, b) => String(a[sortKey] || "").localeCompare(String(b[sortKey] || "")));
      }
      setData(result);
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
      fetchTab(activeTab);
    }
  }, [authLoading, isAdmin, router, activeTab, fetchTab]);

  function getColumns(): string[] {
    if (data.length === 0) return [];
    const allKeys = Object.keys(data[0]);
    // Filter out internal/id fields, keep them in a sensible order
    const skip = new Set(["id", "created_at", "updated_at"]);
    return allKeys.filter((k) => !skip.has(k));
  }

  function isNumericColumn(col: string): boolean {
    if (data.length === 0) return false;
    const val = data[0][col];
    return typeof val === "number";
  }

  function handleCellEdit(rowIdx: number, col: string, value: string) {
    setEditedRows((prev) => {
      const next = new Map(prev);
      const existing = next.get(rowIdx) ?? {};
      const numVal = parseFloat(value);
      existing[col] = isNaN(numVal) ? value : numVal;
      next.set(rowIdx, existing);
      return next;
    });
  }

  function getCellValue(rowIdx: number, col: string): unknown {
    const edited = editedRows.get(rowIdx);
    if (edited && col in edited) return edited[col];
    return data[rowIdx][col];
  }

  async function saveChanges() {
    if (activeTab !== "requirements") {
      toast.info("Editing is only supported for Crop Requirements");
      return;
    }
    setSaving(true);
    try {
      const promises: Promise<unknown>[] = [];
      editedRows.forEach((changes, rowIdx) => {
        const crop = data[rowIdx].crop as string;
        // Only send nutrient fields that were actually edited
        const nutrientChanges: Record<string, unknown> = {};
        for (const [key, val] of Object.entries(changes)) {
          if (NUTRIENT_COLS.includes(key) || key === "c") {
            nutrientChanges[key] = val;
          }
        }
        if (Object.keys(nutrientChanges).length > 0) {
          promises.push(
            api.patch(`/api/crop-norms/${encodeURIComponent(crop)}`, nutrientChanges)
          );
        }
      });
      await Promise.all(promises);
      toast.success("Crop requirements updated");
      setEditedRows(new Map());
      fetchTab(activeTab);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (authLoading) return null;

  const columns = getColumns();
  const hasEdits = editedRows.size > 0;

  return (
    <>
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Crop Norms</h1>
            <p className="mt-1 text-sm text-[var(--sapling-medium-grey)]">
              View and edit crop nutrient requirements and reference data
            </p>
          </div>
          {activeTab === "requirements" && (
            <Button onClick={saveChanges} disabled={!hasEdits || saving}>
              <Save className="size-4" data-icon="inline-start" />
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          )}
        </div>

        {/* Tabs */}
        <div className="mt-6 flex gap-1 rounded-lg bg-gray-100 p-1">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
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
          <div className="mt-4 overflow-x-auto rounded-xl border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  {columns.map((col) => (
                    <th key={col} className="px-3 py-3 whitespace-nowrap">
                      {col.replace(/_/g, " ")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((row, rowIdx) => (
                  <tr key={rowIdx} className="hover:bg-gray-50">
                    {columns.map((col) => {
                      const value = getCellValue(rowIdx, col);
                      const isEditable =
                        activeTab === "requirements" &&
                        (NUTRIENT_COLS.includes(col) || col === "c");
                      const isEdited = editedRows.get(rowIdx)?.[col] !== undefined;

                      if (isEditable) {
                        return (
                          <td key={col} className="px-2 py-1.5">
                            <Input
                              type="number"
                              step="0.01"
                              className={`w-20 text-right ${
                                isEdited ? "border-orange-300 bg-orange-50" : ""
                              }`}
                              value={value as number}
                              onChange={(e) =>
                                handleCellEdit(rowIdx, col, e.target.value)
                              }
                            />
                          </td>
                        );
                      }

                      return (
                        <td
                          key={col}
                          className="px-3 py-3 whitespace-nowrap text-gray-700"
                        >
                          {typeof value === "number"
                            ? value
                            : String(value ?? "-")}
                        </td>
                      );
                    })}
                  </tr>
                ))}
                {data.length === 0 && (
                  <tr>
                    <td
                      colSpan={columns.length || 1}
                      className="px-4 py-8 text-center text-gray-400"
                    >
                      No data found
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
