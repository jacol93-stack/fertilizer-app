"use client";

import { useEffect, useState, Suspense } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  ChevronDown,
  ChevronRight,
  FileBarChart,
  CheckCircle2,
  Calendar,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { buildSoilReport } from "@/lib/soil-reports";
import type { Field } from "@/lib/season-constants";

interface Client {
  id: string;
  name: string;
}

interface Farm {
  id: string;
  name: string;
}

interface SoilAnalysis {
  id: string;
  field_id: string | null;
  analysis_date: string | null;
  lab_name: string | null;
  deleted_at?: string | null;
}

interface BlockOption {
  field: Field;
  farmName: string;
  analyses: SoilAnalysis[];
}

export default function NewSoilReportPageWrapper() {
  return (
    <Suspense>
      <NewSoilReportPage />
    </Suspense>
  );
}

function NewSoilReportPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const clientId = params.id;

  const [client, setClient] = useState<Client | null>(null);
  const [blocks, setBlocks] = useState<BlockOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);
  // Selection state — block-id → set of selected analysis-ids. Block
  // is included in the report when at least one analysis is selected.
  const [selectedAnalysesByBlock, setSelectedAnalysesByBlock] = useState<
    Record<string, Set<string>>
  >({});
  const [expandedBlocks, setExpandedBlocks] = useState<Set<string>>(new Set());
  const [title, setTitle] = useState("");

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        setLoading(true);
        // The clients router has no GET /api/clients/{id} endpoint —
        // it only exposes the list at /api/clients/. Match the existing
        // pattern used by the documents page: list + find-by-id in JS.
        const [allClients, farms] = await Promise.all([
          api.getAll<Client>("/api/clients"),
          api.getAll<Farm>(`/api/clients/${clientId}/farms`),
        ]);
        if (ignore) return;
        const clientRow = allClients.find((c) => c.id === clientId) || null;
        setClient(clientRow);

        // Fetch fields per farm + soil analyses for this client.
        const fieldArrays = await Promise.all(
          farms.map((farm) =>
            api.getAll<Field>(`/api/clients/farms/${farm.id}/fields`),
          ),
        );
        const allAnalyses = await api.getAll<SoilAnalysis>(
          `/api/soil?client_id=${clientId}`,
        );
        const activeAnalyses = allAnalyses.filter((a) => !a.deleted_at);
        const analysesByField = new Map<string, SoilAnalysis[]>();
        for (const a of activeAnalyses) {
          if (!a.field_id) continue;
          if (!analysesByField.has(a.field_id)) analysesByField.set(a.field_id, []);
          analysesByField.get(a.field_id)!.push(a);
        }
        // Sort each block's analyses ascending by date so the latest
        // is at the bottom of the per-block list.
        for (const arr of analysesByField.values()) {
          arr.sort((x, y) => (x.analysis_date || "").localeCompare(y.analysis_date || ""));
        }
        const opts: BlockOption[] = [];
        farms.forEach((farm, i) => {
          (fieldArrays[i] || []).forEach((field) => {
            const analyses = analysesByField.get(field.id || "") || [];
            if (analyses.length === 0) return;
            opts.push({ field, farmName: farm.name, analyses });
          });
        });
        // Stable order: farm name, then field name.
        opts.sort((a, b) =>
          a.farmName.localeCompare(b.farmName) ||
          (a.field.name || "").localeCompare(b.field.name || ""),
        );
        setBlocks(opts);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        toast.error(`Failed to load: ${msg}`);
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [clientId]);

  function toggleBlockExpansion(blockId: string) {
    setExpandedBlocks((prev) => {
      const next = new Set(prev);
      if (next.has(blockId)) next.delete(blockId);
      else next.add(blockId);
      return next;
    });
  }

  function toggleBlockAllAnalyses(block: BlockOption) {
    setSelectedAnalysesByBlock((prev) => {
      const next = { ...prev };
      const blockId = block.field.id || "";
      const current = next[blockId];
      const allIds = block.analyses.map((a) => a.id);
      if (current && current.size === allIds.length) {
        // Deselect block
        delete next[blockId];
      } else {
        next[blockId] = new Set(allIds);
      }
      return next;
    });
  }

  function toggleAnalysis(blockId: string, analysisId: string) {
    setSelectedAnalysesByBlock((prev) => {
      const next = { ...prev };
      const current = new Set(next[blockId] || []);
      if (current.has(analysisId)) current.delete(analysisId);
      else current.add(analysisId);
      if (current.size === 0) delete next[blockId];
      else next[blockId] = current;
      return next;
    });
  }

  // Aggregate selection state for the build summary.
  const selectedBlockIds = Object.keys(selectedAnalysesByBlock);
  const totalSelectedAnalyses = Object.values(selectedAnalysesByBlock).reduce(
    (sum, set) => sum + set.size,
    0,
  );
  const scopeKind: "single_block" | "block_with_history" | "multi_block" = (() => {
    if (selectedBlockIds.length === 0) return "single_block";
    if (selectedBlockIds.length === 1) {
      const set = selectedAnalysesByBlock[selectedBlockIds[0]] || new Set();
      return set.size > 1 ? "block_with_history" : "single_block";
    }
    return "multi_block";
  })();
  const scopeLabel = {
    single_block: "Single block snapshot",
    block_with_history: "Block with history",
    multi_block: "Multi-block snapshot",
  }[scopeKind];

  async function handleBuild() {
    if (selectedBlockIds.length === 0) {
      toast.error("Select at least one block + analysis to build a report.");
      return;
    }
    setBuilding(true);
    try {
      const allAnalysisIds = selectedBlockIds.flatMap((bid) =>
        Array.from(selectedAnalysesByBlock[bid] || []),
      );
      const res = await buildSoilReport({
        title: title.trim() || undefined,
        block_ids: selectedBlockIds,
        analysis_ids: allAnalysisIds,
        // include_history is implicit in the explicit analysis_ids list,
        // but pass true so any analyses we forgot to enumerate get
        // included as a safety net (no harm — caller already filtered).
        include_history: true,
      });
      toast.success("Soil report built");
      router.push(`/clients/${clientId}/soil-reports/${res.id}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Build failed: ${msg}`);
    } finally {
      setBuilding(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto flex max-w-4xl items-center justify-center px-4 py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/clients/${clientId}`)}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to client
          </Button>
        </div>

        <div className="flex items-start gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
            <FileBarChart className="size-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">
              New Soil Report
            </h1>
            <p className="text-sm text-muted-foreground">
              {client?.name} · pick the blocks + analyses to interpret
            </p>
          </div>
        </div>

        {/* Scope summary card */}
        <Card>
          <CardContent className="space-y-3 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  Selection
                </p>
                <p className="text-sm font-medium text-[var(--sapling-dark)]">
                  {selectedBlockIds.length === 0
                    ? "No blocks selected"
                    : `${selectedBlockIds.length} block${selectedBlockIds.length !== 1 ? "s" : ""} · ${totalSelectedAnalyses} analys${totalSelectedAnalyses === 1 ? "is" : "es"}`}
                </p>
              </div>
              <span className="rounded bg-orange-100 px-2 py-1 text-[10px] font-bold uppercase text-[var(--sapling-orange)]">
                {scopeLabel}
              </span>
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Title (optional)
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Anton Muller — Laborie macadamia 2026"
                className="w-full rounded-md border px-3 py-2 text-sm outline-none focus:border-[var(--sapling-orange)]"
              />
            </div>
          </CardContent>
        </Card>

        {/* Block + analysis selection */}
        {blocks.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-sm text-muted-foreground">
              No blocks with soil analyses yet. Upload an analysis on the
              client page first, then come back here.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {blocks.map((block) => {
              const blockId = block.field.id || "";
              const selectedAnalyses = selectedAnalysesByBlock[blockId] || new Set();
              const allSelected = selectedAnalyses.size === block.analyses.length;
              const isExpanded = expandedBlocks.has(blockId);
              return (
                <Card key={blockId} className={selectedAnalyses.size > 0 ? "border-[var(--sapling-orange)]/40" : ""}>
                  <CardContent className="space-y-2 p-3">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={allSelected}
                        onChange={() => toggleBlockAllAnalyses(block)}
                        aria-label={`Toggle all analyses on ${block.field.name}`}
                        className="size-4 cursor-pointer rounded border accent-[var(--sapling-orange)]"
                      />
                      <button
                        type="button"
                        onClick={() => toggleBlockExpansion(blockId)}
                        className="flex flex-1 items-center gap-2 text-left"
                      >
                        {isExpanded ? (
                          <ChevronDown className="size-4 text-muted-foreground" />
                        ) : (
                          <ChevronRight className="size-4 text-muted-foreground" />
                        )}
                        <span className="font-medium text-[var(--sapling-dark)]">
                          {block.field.name}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {block.farmName} · {block.field.crop || "—"} · {block.field.size_ha ? `${block.field.size_ha} ha` : "—"}
                        </span>
                        <span className="ml-auto text-xs text-muted-foreground">
                          {selectedAnalyses.size > 0
                            ? `${selectedAnalyses.size} of ${block.analyses.length} selected`
                            : `${block.analyses.length} analys${block.analyses.length === 1 ? "is" : "es"}`}
                        </span>
                      </button>
                    </div>

                    {isExpanded && (
                      <ul className="ml-6 space-y-1 border-l border-muted/40 pl-4">
                        {block.analyses.map((a) => {
                          const isSelected = selectedAnalyses.has(a.id);
                          return (
                            <li key={a.id} className="flex items-center gap-3 py-1 text-sm">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleAnalysis(blockId, a.id)}
                                aria-label={`Select analysis ${a.id}`}
                                className="size-4 cursor-pointer rounded border accent-[var(--sapling-orange)]"
                              />
                              <Calendar className="size-3.5 text-muted-foreground" />
                              <span className="font-medium">
                                {a.analysis_date || "Undated"}
                              </span>
                              {a.lab_name && (
                                <span className="text-xs text-muted-foreground">· {a.lab_name}</span>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={() => router.push(`/clients/${clientId}`)}
          >
            Cancel
          </Button>
          <Button
            variant="default"
            onClick={handleBuild}
            disabled={selectedBlockIds.length === 0 || building}
            className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
          >
            {building ? <Loader2 className="size-4 animate-spin" /> : <CheckCircle2 className="size-4" />}
            Build report
          </Button>
        </div>
    </div>
  );
}
