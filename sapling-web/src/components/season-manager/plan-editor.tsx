"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Loader2,
  Plus,
  Trash2,
  Eye,
  Save,
  X,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { MONTH_NAMES } from "@/lib/season-constants";

interface PlanEditorProps {
  programmeId: string;
  onAfterSave?: () => void;
}

type Nutrients = Record<string, number>;

interface BlendRow {
  id: string;
  blend_group: string | null;
  stage_name: string | null;
  application_month: number | null;
  method: string | null;
  rate_kg_ha: number | null;
  sa_notation: string | null;
  blend_nutrients: Nutrients | null;
  notes: string | null;
  _dirty?: boolean;
  _new?: boolean;
  _deleted?: boolean;
}

interface Block {
  id: string;
  name: string;
  crop: string;
  blend_group: string | null;
  nutrient_targets?: unknown;
}

interface Validation {
  summary: {
    on_target_count: number;
    under_target_count: number;
    over_target_count: number;
    unaddressed_leaf_count: number;
    total_warnings: number;
    has_targets: boolean;
  };
  per_nutrient: Array<{
    nutrient: string;
    target_kg_ha: number | null;
    planned_kg_ha: number;
    delivered_kg_ha: number;
    status: string;
  }>;
  warnings: Array<{ kind: string; severity: string; message: string }>;
  leaf_flags: Array<{ element: string; addressed: boolean; classification: string }>;
}

interface PreviewResponse {
  blocks: Record<string, {
    block_name: string;
    current: Validation;
    proposed: Validation;
    net_change: {
      changed_nutrients: Array<{ nutrient: string; before: number; after: number; delta_kg_ha: number }>;
      warnings_before: number;
      warnings_after: number;
    };
  }>;
}

const NUTRIENT_KEYS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"] as const;
const METHOD_OPTIONS = ["broadcast", "band_place", "side_dress", "topdress", "fertigation", "foliar"];

export function PlanEditor({ programmeId, onAfterSave }: PlanEditorProps) {
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [blends, setBlends] = useState<BlendRow[]>([]);
  const [originalBlends, setOriginalBlends] = useState<BlendRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [validations, setValidations] = useState<Record<string, Validation>>({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const prog = await api.get<{ blocks: Block[]; blends: BlendRow[] }>(
        `/api/programmes/${programmeId}`
      );
      setBlocks(prog.blocks || []);
      const fresh = (prog.blends || []).map((b) => ({ ...b, _dirty: false, _new: false }));
      setBlends(fresh);
      setOriginalBlends(fresh.map((b) => ({ ...b })));
      setPreview(null);

      // Fetch current validation to show initial state
      const v = await api.get<{ blocks: Record<string, Validation> }>(
        `/api/programmes/${programmeId}/validate`
      );
      setValidations(v.blocks || {});
    } catch {
      toast.error("Failed to load plan");
    } finally {
      setLoading(false);
    }
  }, [programmeId]);

  useEffect(() => { load(); }, [load]);

  const updateField = (id: string, field: keyof BlendRow, value: unknown) => {
    setBlends((prev) =>
      prev.map((b) => (b.id === id ? { ...b, [field]: value, _dirty: true } : b))
    );
  };

  const updateNutrient = (id: string, nut: string, value: number) => {
    setBlends((prev) =>
      prev.map((b) => {
        if (b.id !== id) return b;
        const next = { ...(b.blend_nutrients || {}), [nut]: value };
        if (!Number.isFinite(value) || value <= 0) delete next[nut];
        return { ...b, blend_nutrients: next, _dirty: true };
      })
    );
  };

  const addBlend = (block: Block) => {
    const tempId = `__new_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    const row: BlendRow = {
      id: tempId,
      blend_group: block.blend_group,
      stage_name: "Stage",
      application_month: 1,
      method: "broadcast",
      rate_kg_ha: 0,
      sa_notation: null,
      blend_nutrients: {},
      notes: null,
      _dirty: true,
      _new: true,
    };
    setBlends((prev) => [...prev, row]);
  };

  const removeBlend = (id: string) => {
    setBlends((prev) => {
      const row = prev.find((b) => b.id === id);
      if (!row) return prev;
      if (row._new) return prev.filter((b) => b.id !== id);
      return prev.map((b) => (b.id === id ? { ...b, _deleted: true, _dirty: true } : b));
    });
  };

  const restoreBlend = (id: string) => {
    setBlends((prev) =>
      prev.map((b) => (b.id === id ? { ...b, _deleted: false } : b))
    );
  };

  const dirtyCount = blends.filter((b) => b._dirty).length;

  const buildProposal = () => {
    const creates = blends
      .filter((b) => b._new && !b._deleted)
      .map((b) => {
        // id is synthetic — don't forward to server
        const { id: _id, _dirty, _new, _deleted, ...rest } = b;
        return { ...rest, blend_group: rest.blend_group || "A" };
      });
    const updates = blends
      .filter((b) => b._dirty && !b._new && !b._deleted)
      .map((b) => {
        const { _dirty, _new, _deleted, ...rest } = b;
        return rest;
      });
    const deletes = blends.filter((b) => b._deleted && !b._new).map((b) => b.id);
    return { creates, updates, deletes };
  };

  const previewChanges = async () => {
    setPreviewing(true);
    try {
      const result = await api.post<PreviewResponse>(
        `/api/programmes/${programmeId}/preview-edit`,
        buildProposal()
      );
      setPreview(result);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Preview failed");
    } finally {
      setPreviewing(false);
    }
  };

  const saveChanges = async () => {
    if (dirtyCount === 0) return;
    setSaving(true);
    try {
      const { creates, updates, deletes } = buildProposal();

      // Deletes first so re-creates with same month don't clash
      for (const id of deletes) {
        await api.delete(`/api/programmes/${programmeId}/blends/${id}`);
      }
      for (const u of updates) {
        await api.patch(`/api/programmes/${programmeId}/blends/${u.id}`, u);
      }
      for (const c of creates) {
        await api.post(`/api/programmes/${programmeId}/blends`, c);
      }

      toast.success(`Saved ${creates.length + updates.length + deletes.length} change(s)`);
      setPreview(null);
      await load();
      onAfterSave?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const discardChanges = () => {
    setBlends(originalBlends.map((b) => ({ ...b })));
    setPreview(null);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">Edit Plan</h3>
          <p className="text-sm text-muted-foreground">
            Add, edit, or remove applications. Preview impact against targets before saving.
          </p>
        </div>
        <div className="flex gap-2">
          {dirtyCount > 0 && (
            <>
              <Button variant="outline" size="sm" onClick={discardChanges} disabled={saving}>
                <X className="size-4" />
                Discard
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={previewChanges}
                disabled={previewing || saving}
              >
                {previewing ? <Loader2 className="size-4 animate-spin" /> : <Eye className="size-4" />}
                Preview impact
              </Button>
              <Button
                size="sm"
                onClick={saveChanges}
                disabled={saving}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                Save {dirtyCount} change{dirtyCount !== 1 ? "s" : ""}
              </Button>
            </>
          )}
        </div>
      </div>

      {blocks.map((block) => {
        const blockBlends = blends.filter((b) => b.blend_group === block.blend_group);
        const validation = validations[block.id];
        const previewForBlock = preview?.blocks[block.id];
        return (
          <Card key={block.id}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                {block.name}
                {block.blend_group && (
                  <span className="rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
                    Group {block.blend_group}
                  </span>
                )}
                <span className="text-xs font-normal text-muted-foreground">· {block.crop}</span>
              </CardTitle>
              {validation && !previewForBlock && <ValidationSummary v={validation} />}
              {previewForBlock && <PreviewSummary p={previewForBlock} />}
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-xs font-medium text-muted-foreground">
                    <tr className="border-b">
                      <th className="py-2 pr-2 text-left">Month</th>
                      <th className="py-2 pr-2 text-left">Stage</th>
                      <th className="py-2 pr-2 text-left">Method</th>
                      <th className="py-2 pr-2 text-right">Rate (kg/ha)</th>
                      <th className="py-2 pr-2 text-left">N / P / K</th>
                      <th className="py-2 pr-2 text-left">Micros</th>
                      <th className="py-2 pr-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {blockBlends
                      .sort((a, b) => (a.application_month || 0) - (b.application_month || 0))
                      .map((bl) => (
                        <BlendEditorRow
                          key={bl.id}
                          blend={bl}
                          onField={(f, v) => updateField(bl.id, f, v)}
                          onNutrient={(n, v) => updateNutrient(bl.id, n, v)}
                          onRemove={() => removeBlend(bl.id)}
                          onRestore={() => restoreBlend(bl.id)}
                        />
                      ))}
                  </tbody>
                </table>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={() => addBlend(block)}
              >
                <Plus className="size-3" />
                Add application
              </Button>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function BlendEditorRow({
  blend, onField, onNutrient, onRemove, onRestore,
}: {
  blend: BlendRow;
  onField: (field: keyof BlendRow, value: unknown) => void;
  onNutrient: (nut: string, value: number) => void;
  onRemove: () => void;
  onRestore: () => void;
}) {
  const n = blend.blend_nutrients || {};
  const micros = NUTRIENT_KEYS.filter((k) => !["n", "p", "k"].includes(k));
  const anyMicros = micros.filter((k) => (n[k] ?? 0) > 0);

  const rowClass = blend._deleted
    ? "opacity-40 line-through"
    : blend._new
      ? "bg-green-50/30"
      : blend._dirty
        ? "bg-amber-50/30"
        : "";

  return (
    <tr className={`border-b ${rowClass}`}>
      <td className="py-2 pr-2">
        <select
          className="w-20 rounded border px-1.5 py-1 text-sm"
          value={blend.application_month || 1}
          onChange={(e) => onField("application_month", parseInt(e.target.value))}
          disabled={blend._deleted}
        >
          {Array.from({ length: 12 }, (_, i) => (
            <option key={i + 1} value={i + 1}>
              {MONTH_NAMES[i + 1]}
            </option>
          ))}
        </select>
      </td>
      <td className="py-2 pr-2">
        <Input
          className="h-7 text-sm"
          value={blend.stage_name || ""}
          onChange={(e) => onField("stage_name", e.target.value)}
          disabled={blend._deleted}
        />
      </td>
      <td className="py-2 pr-2">
        <select
          className="rounded border px-1.5 py-1 text-sm"
          value={blend.method || "broadcast"}
          onChange={(e) => onField("method", e.target.value)}
          disabled={blend._deleted}
        >
          {METHOD_OPTIONS.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </td>
      <td className="py-2 pr-2 text-right">
        <Input
          type="number"
          step="1"
          min="0"
          className="h-7 w-20 text-right text-sm tabular-nums"
          value={blend.rate_kg_ha ?? 0}
          onChange={(e) => onField("rate_kg_ha", parseFloat(e.target.value) || 0)}
          disabled={blend._deleted}
        />
      </td>
      <td className="py-2 pr-2">
        <div className="flex gap-1">
          {(["n", "p", "k"] as const).map((nut) => (
            <div key={nut} className="flex items-center gap-0.5">
              <span className="w-3 text-xs font-medium uppercase text-muted-foreground">{nut}</span>
              <Input
                type="number"
                step="0.1"
                min="0"
                className="h-7 w-14 text-right text-xs tabular-nums"
                value={n[nut] ?? 0}
                onChange={(e) => onNutrient(nut, parseFloat(e.target.value) || 0)}
                disabled={blend._deleted}
              />
            </div>
          ))}
        </div>
      </td>
      <td className="py-2 pr-2">
        <div className="flex flex-wrap gap-1 text-xs">
          {micros.map((nut) => {
            const val = n[nut] ?? 0;
            const active = val > 0;
            return (
              <details key={nut} className="inline-block">
                <summary className={`cursor-pointer rounded px-1.5 py-0.5 ${active ? "bg-blue-100 text-blue-800" : "bg-muted text-muted-foreground"}`}>
                  {nut.toUpperCase()}{active ? ` ${val}` : ""}
                </summary>
                <div className="absolute z-10 mt-1 rounded border bg-white p-2 shadow">
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    className="h-7 w-20 text-right text-xs"
                    value={val}
                    onChange={(e) => onNutrient(nut, parseFloat(e.target.value) || 0)}
                    disabled={blend._deleted}
                  />
                </div>
              </details>
            );
          })}
          {anyMicros.length === 0 && <span className="text-muted-foreground/50">none</span>}
        </div>
      </td>
      <td className="py-2 pr-2 text-right">
        {blend._deleted ? (
          <Button size="sm" variant="ghost" onClick={onRestore}>Undo</Button>
        ) : (
          <Button size="sm" variant="ghost" onClick={onRemove}>
            <Trash2 className="size-3 text-red-500" />
          </Button>
        )}
      </td>
    </tr>
  );
}

function ValidationSummary({ v }: { v: Validation }) {
  if (!v.summary.has_targets) {
    return (
      <p className="mt-1 text-xs text-muted-foreground">
        No soil targets — validation not available
      </p>
    );
  }
  const under = v.summary.under_target_count;
  const over = v.summary.over_target_count;
  const leaf = v.summary.unaddressed_leaf_count;
  return (
    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
      {under === 0 && over === 0 && leaf === 0 ? (
        <span className="flex items-center gap-1 text-green-700">
          <CheckCircle2 className="size-3" />
          Plan meets targets
        </span>
      ) : (
        <>
          {under > 0 && (
            <span className="flex items-center gap-1 text-red-700">
              <TrendingDown className="size-3" />
              {under} nutrient{under !== 1 ? "s" : ""} under target
            </span>
          )}
          {over > 0 && (
            <span className="flex items-center gap-1 text-amber-700">
              <TrendingUp className="size-3" />
              {over} over target
            </span>
          )}
          {leaf > 0 && (
            <span className="flex items-center gap-1 text-orange-700">
              <AlertTriangle className="size-3" />
              {leaf} leaf deficiency unaddressed
            </span>
          )}
        </>
      )}
    </div>
  );
}

function PreviewSummary({ p }: {
  p: {
    current: Validation;
    proposed: Validation;
    net_change: {
      changed_nutrients: Array<{ nutrient: string; before: number; after: number; delta_kg_ha: number }>;
      warnings_before: number;
      warnings_after: number;
    };
  };
}) {
  const nc = p.net_change;
  const betterWarnings = nc.warnings_after < nc.warnings_before;
  const worseWarnings = nc.warnings_after > nc.warnings_before;

  return (
    <div className="mt-2 rounded-lg border bg-muted/20 p-2.5 text-xs">
      <p className="mb-1 font-semibold">Proposed impact</p>
      <div className="flex flex-wrap gap-2">
        {nc.changed_nutrients.map((c) => (
          <span
            key={c.nutrient}
            className={`rounded px-1.5 py-0.5 font-medium ${
              c.delta_kg_ha > 0 ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
            }`}
          >
            {c.nutrient.toUpperCase()} {c.before.toFixed(1)} → {c.after.toFixed(1)}
            ({c.delta_kg_ha > 0 ? "+" : ""}{c.delta_kg_ha.toFixed(1)})
          </span>
        ))}
        {nc.changed_nutrients.length === 0 && (
          <span className="text-muted-foreground">No net nutrient change</span>
        )}
        <span className={
          betterWarnings ? "text-green-700" :
          worseWarnings ? "text-red-700" :
          "text-muted-foreground"
        }>
          Warnings: {nc.warnings_before} → {nc.warnings_after}
        </span>
      </div>
    </div>
  );
}
