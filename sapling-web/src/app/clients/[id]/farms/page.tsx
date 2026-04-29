"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  Loader2,
  Trees,
  Plus,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { SelectionToolbar } from "@/components/ui/selection-toolbar";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { BlockCard, type BlockCardData } from "@/components/client-portal/block-card";
import type { Field } from "@/lib/season-constants";

interface Farm {
  id: string;
  name: string;
  region?: string | null;
}

interface SoilAnalysis {
  id: string;
  field_id: string | null;
  analysis_date: string | null;
  created_at: string;
  soil_values?: Record<string, number> | null;
}

interface LeafAnalysis {
  id: string;
  field_id: string | null;
  sample_date: string | null;
  created_at: string;
  classifications?: Record<string, string> | null;
}

interface YieldRecord {
  id: string;
  field_id: string;
  season_year: number;
  yield_t_ha: number | null;
}

export default function FarmsAndBlocksPage() {
  const params = useParams<{ id: string }>();
  const clientId = params.id;

  const [loading, setLoading] = useState(true);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [farmFields, setFarmFields] = useState<Record<string, Field[]>>({});
  const [soils, setSoils] = useState<SoilAnalysis[]>([]);
  const [leaves, setLeaves] = useState<LeafAnalysis[]>([]);
  const [yields, setYields] = useState<YieldRecord[]>([]);

  // Bulk-select for farms (top-level toolbar) and per-farm fields
  // (toolbar inside each farm section).
  const [farmSelectMode, setFarmSelectMode] = useState(false);
  const [selectedFarmIds, setSelectedFarmIds] = useState<Set<string>>(new Set());
  const [fieldSelectFarmId, setFieldSelectFarmId] = useState<string | null>(null);
  const [selectedFieldIds, setSelectedFieldIds] = useState<Set<string>>(new Set());

  const refreshFarmsAndFields = async () => {
    const farmsData = await api.get<Farm[]>(`/api/clients/${clientId}/farms`);
    setFarms(farmsData);
    const fieldsByFarm: Record<string, Field[]> = {};
    await Promise.all(
      farmsData.map(async (f) => {
        const fields = await api
          .get<Field[]>(`/api/clients/farms/${f.id}/fields`)
          .catch(() => []);
        fieldsByFarm[f.id] = fields;
      }),
    );
    setFarmFields(fieldsByFarm);
  };

  const handleBulkDeleteFarms = async () => {
    const ids = Array.from(selectedFarmIds);
    let ok = 0;
    const failures: string[] = [];
    for (const id of ids) {
      try {
        await api.delete(`/api/clients/farms/${id}`);
        ok++;
      } catch {
        const f = farms.find((x) => x.id === id);
        failures.push(f?.name ?? id);
      }
    }
    if (failures.length === 0) {
      toast.success(`Deleted ${ok} farm${ok === 1 ? "" : "s"}`);
    } else {
      toast.warning(
        `${ok} deleted · ${failures.length} failed`,
        { description: failures.slice(0, 3).join(", ") },
      );
    }
    setSelectedFarmIds(new Set());
    await refreshFarmsAndFields();
  };

  const handleBulkDeleteFields = async (farmId: string) => {
    const ids = Array.from(selectedFieldIds);
    let ok = 0;
    const failures: string[] = [];
    for (const id of ids) {
      try {
        await api.post(`/api/clients/fields/${id}/delete`, {});
        ok++;
      } catch {
        const f = (farmFields[farmId] ?? []).find((x) => x.id === id);
        failures.push(f?.name ?? id);
      }
    }
    if (failures.length === 0) {
      toast.success(`Deleted ${ok} block${ok === 1 ? "" : "s"}`);
    } else {
      toast.warning(
        `${ok} deleted · ${failures.length} failed`,
        { description: failures.slice(0, 3).join(", ") },
      );
    }
    setSelectedFieldIds(new Set());
    setFieldSelectFarmId(null);
    await refreshFarmsAndFields();
  };

  const toggleFarm = (id: string) =>
    setSelectedFarmIds((p) => {
      const n = new Set(p);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  const toggleField = (id: string) =>
    setSelectedFieldIds((p) => {
      const n = new Set(p);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        const [farmsData, soilData, leafData] = await Promise.all([
          api.get<Farm[]>(`/api/clients/${clientId}/farms`),
          api.getAll<SoilAnalysis>(`/api/soil?client_id=${clientId}`).catch(() => []),
          api.getAll<LeafAnalysis>(`/api/leaf?client_id=${clientId}`).catch(() => []),
        ]);
        if (!alive) return;
        setFarms(farmsData);
        setSoils(soilData);
        setLeaves(leafData);

        const fieldsByFarm: Record<string, Field[]> = {};
        const allYields: YieldRecord[] = [];
        await Promise.all(
          farmsData.map(async (f) => {
            const fields = await api
              .get<Field[]>(`/api/clients/farms/${f.id}/fields`)
              .catch(() => []);
            fieldsByFarm[f.id] = fields;
            const yieldResults = await Promise.all(
              fields.map((field) =>
                api
                  .get<YieldRecord[]>(`/api/clients/fields/${field.id}/yields`)
                  .catch(() => []),
              ),
            );
            yieldResults.forEach((rs) => allYields.push(...rs));
          }),
        );
        if (!alive) return;
        setFarmFields(fieldsByFarm);
        setYields(allYields);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [clientId]);

  const cardDataByFieldId = useMemo(() => {
    const map = new Map<string, BlockCardData>();
    const allFields = Object.values(farmFields).flat();
    for (const field of allFields) {
      const fieldSoils = soils
        .filter((s) => s.field_id === field.id)
        .sort((a, b) =>
          (b.analysis_date ?? b.created_at).localeCompare(a.analysis_date ?? a.created_at),
        );
      const fieldLeaves = leaves
        .filter((l) => l.field_id === field.id)
        .sort((a, b) =>
          (b.sample_date ?? b.created_at).localeCompare(a.sample_date ?? a.created_at),
        );
      const fieldYields = yields
        .filter((y) => y.field_id === field.id)
        .sort((a, b) => b.season_year - a.season_year);

      const latestSoilRow = fieldSoils[0];
      const latestSoil = latestSoilRow
        ? {
          date: latestSoilRow.analysis_date ?? latestSoilRow.created_at,
          ph: pickNum(latestSoilRow.soil_values, "pH (H2O)", "pH"),
          oc: pickNum(latestSoilRow.soil_values, "Org C", "OC"),
          n: null,
        }
        : undefined;
      const soilHistory = fieldSoils
        .map((s) => pickNum(s.soil_values, "pH (H2O)", "pH"))
        .filter((v): v is number => typeof v === "number")
        .reverse()
        .slice(-6);

      const latestLeafRow = fieldLeaves[0];
      const latestLeaf = latestLeafRow
        ? {
          date: latestLeafRow.sample_date ?? latestLeafRow.created_at,
          summary: summariseLeaf(latestLeafRow.classifications),
        }
        : undefined;
      const leafHistory: number[] = []; // future: composite leaf health score per analysis

      const latestYieldRow = fieldYields[0];
      const latestYield = latestYieldRow?.yield_t_ha != null
        ? {
          season: String(latestYieldRow.season_year),
          tHa: latestYieldRow.yield_t_ha,
          benchmark: undefined,
        }
        : undefined;
      const yieldHistory = fieldYields
        .map((y) => y.yield_t_ha)
        .filter((v): v is number => typeof v === "number")
        .reverse()
        .slice(-6);

      map.set(field.id, {
        field,
        latestSoil,
        soilHistory,
        latestLeaf,
        leafHistory,
        latestYield,
        yieldHistory,
      });
    }
    return map;
  }, [farmFields, soils, leaves, yields]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-[var(--sapling-dark)]">Farms & Blocks</h1>
          <p className="text-sm text-muted-foreground">
            {farms.length} {farms.length === 1 ? "farm" : "farms"} ·{" "}
            {Object.values(farmFields).flat().length} blocks
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <SelectionToolbar
            selectionMode={farmSelectMode}
            onToggleMode={(next) => {
              setFarmSelectMode(next);
              if (!next) setSelectedFarmIds(new Set());
              // Selecting whole farms cancels block-level selection
              if (next) {
                setFieldSelectFarmId(null);
                setSelectedFieldIds(new Set());
              }
            }}
            totalCount={farms.length}
            selectedCount={selectedFarmIds.size}
            onSelectAll={(all) => {
              if (all) setSelectedFarmIds(new Set(farms.map((f) => f.id)));
              else setSelectedFarmIds(new Set());
            }}
            onDelete={handleBulkDeleteFarms}
            itemLabel={{ singular: "farm", plural: "farms" }}
          />
          <Link
            href={`/clients/${clientId}?action=add-farm`}
            className="inline-flex items-center gap-1.5 rounded-md bg-[var(--sapling-orange)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--sapling-orange)]/90"
          >
            <Plus className="size-3.5" />
            Add farm
          </Link>
          <Link
            href={`/clients/${clientId}/import`}
            className="inline-flex items-center gap-1.5 rounded-md border bg-white px-3 py-1.5 text-xs font-medium text-[var(--sapling-dark)] hover:bg-orange-50"
          >
            <Upload className="size-3.5" />
            Bulk import
          </Link>
        </div>
      </div>

      {farms.length === 0 ? (
        <div className="rounded-lg border border-dashed bg-white py-12 text-center">
          <Trees className="mx-auto size-8 text-muted-foreground/40" />
          <p className="mt-3 text-sm text-muted-foreground">No farms yet for this client.</p>
          <Link
            href={`/clients/${clientId}?action=add-farm`}
            className="mt-3 inline-flex items-center gap-1.5 text-xs text-[var(--sapling-orange)] hover:underline"
          >
            <Plus className="size-3" />
            Add the first farm
          </Link>
        </div>
      ) : (
        farms.map((farm) => {
          const fields = farmFields[farm.id] ?? [];
          const totalArea = fields.reduce((s, f) => s + (f.size_ha ?? 0), 0);
          const isFarmSelected = selectedFarmIds.has(farm.id);
          const blocksSelectable = fieldSelectFarmId === farm.id;
          return (
            <section
              key={farm.id}
              className={
                farmSelectMode && isFarmSelected
                  ? "rounded-lg ring-2 ring-[var(--sapling-orange)] p-2"
                  : ""
              }
            >
              <header className="mb-3 flex items-baseline justify-between">
                <div className="flex items-center gap-2">
                  {farmSelectMode && (
                    <button
                      type="button"
                      onClick={() => toggleFarm(farm.id)}
                      className={`flex size-4 items-center justify-center rounded border-2 ${
                        isFarmSelected
                          ? "border-[var(--sapling-orange)] bg-[var(--sapling-orange)]"
                          : "border-gray-300 bg-white"
                      }`}
                      title="Select for bulk delete"
                    >
                      {isFarmSelected && <span className="text-[8px] leading-none text-white">✓</span>}
                    </button>
                  )}
                  <div>
                    <h2 className="text-base font-semibold text-[var(--sapling-dark)]">
                      {farm.name}
                    </h2>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {farm.region && <>{farm.region} · </>}
                      {fields.length} {fields.length === 1 ? "block" : "blocks"} ·{" "}
                      {totalArea.toFixed(1)} ha
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  {!farmSelectMode && fields.length > 0 && (
                    <SelectionToolbar
                      selectionMode={blocksSelectable}
                      onToggleMode={(next) => {
                        if (next) {
                          setFieldSelectFarmId(farm.id);
                          setSelectedFieldIds(new Set());
                        } else {
                          setFieldSelectFarmId(null);
                          setSelectedFieldIds(new Set());
                        }
                      }}
                      totalCount={fields.length}
                      selectedCount={blocksSelectable ? selectedFieldIds.size : 0}
                      onSelectAll={(all) => {
                        if (all) setSelectedFieldIds(new Set(fields.map((f) => f.id)));
                        else setSelectedFieldIds(new Set());
                      }}
                      onDelete={() => handleBulkDeleteFields(farm.id)}
                      itemLabel={{ singular: "block", plural: "blocks" }}
                    />
                  )}
                  <Link
                    href={`/clients/${clientId}?addFieldFarm=${farm.id}`}
                    className="inline-flex items-center gap-1 rounded-md border bg-white px-2 py-1 text-[11px] text-[var(--sapling-dark)] hover:bg-orange-50"
                  >
                    <Plus className="size-3" />
                    Add block
                  </Link>
                </div>
              </header>

              {fields.length === 0 ? (
                <div className="rounded-lg border border-dashed bg-white py-6 text-center text-sm text-muted-foreground">
                  No blocks yet.{" "}
                  <Link
                    href={`/clients/${clientId}?addFieldFarm=${farm.id}`}
                    className="text-[var(--sapling-orange)] hover:underline"
                  >
                    Add one
                  </Link>
                </div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {fields.map((field) => {
                    const data = cardDataByFieldId.get(field.id);
                    if (!data) return null;
                    return (
                      <BlockCard
                        key={field.id}
                        clientId={clientId}
                        data={data}
                        selectable={blocksSelectable}
                        selected={selectedFieldIds.has(field.id)}
                        onToggleSelect={() => toggleField(field.id)}
                      />
                    );
                  })}
                </div>
              )}
            </section>
          );
        })
      )}
    </div>
  );
}

function pickNum(
  obj: Record<string, number> | null | undefined,
  ...keys: string[]
): number | null {
  if (!obj) return null;
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === "number" && !isNaN(v)) return v;
  }
  return null;
}

function summariseLeaf(
  classifications: Record<string, string> | null | undefined,
): string {
  if (!classifications) return "no class.";
  const items = Object.entries(classifications);
  const lows = items.filter(([, v]) => v === "low" || v === "deficient").map(([k]) => k);
  const highs = items.filter(([, v]) => v === "high" || v === "excess").map(([k]) => k);
  if (lows.length === 0 && highs.length === 0) return "Adequate";
  const parts: string[] = [];
  if (lows.length > 0) parts.push(`Low ${lows.slice(0, 2).join("/")}`);
  if (highs.length > 0) parts.push(`High ${highs.slice(0, 2).join("/")}`);
  return parts.join(" · ");
}

