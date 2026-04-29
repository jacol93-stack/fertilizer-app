"use client";

/**
 * Season Tracker — in-season recording surface for a v2 ProgrammeArtifact.
 *
 * Two surfaces:
 *   - Applications recorded   (what the farmer actually did, vs the plan)
 *   - Adjustments              (proposed mid-season changes; agronomist
 *                              reviews + approves)
 *
 * Lives below the ArtifactView on /season-manager/artifact/[id]. Variance
 * classification (on_plan / off_plan / unscheduled) is computed by the
 * backend at insert time by comparing actual_date + rate against the
 * artifact's planned blends[].applications.
 */

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { AlertCircle, Check, ClipboardCheck, Plus, Trash2, X } from "lucide-react";
import type { ProgrammeArtifact } from "@/lib/types/programme-artifact";

interface ApplicationRecord {
  id: string;
  artifact_id: string;
  block_id: string;
  planned_blend_ref?: string | null;
  actual_date: string;
  product_label?: string | null;
  rate_kg_ha?: number | null;
  rate_l_ha?: number | null;
  method?: string | null;
  notes?: string | null;
  variance_flag?: "on_plan" | "off_plan" | "unscheduled" | null;
  created_at: string;
}

interface Adjustment {
  id: string;
  artifact_id: string;
  block_id?: string | null;
  trigger_type: string;
  trigger_ref?: string | null;
  proposal: string;
  severity: "info" | "warn" | "critical";
  status: "suggested" | "approved" | "rejected" | "applied";
  reviewer_notes?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

interface Props {
  artifactId: string;
  artifact: ProgrammeArtifact;
}

export function SeasonTracker({ artifactId, artifact }: Props) {
  const [tab, setTab] = useState<"applications" | "adjustments">("applications");
  const [apps, setApps] = useState<ApplicationRecord[]>([]);
  const [adjs, setAdjs] = useState<Adjustment[]>([]);
  const [loading, setLoading] = useState(true);

  const blockOptions = (artifact.soil_snapshots ?? []).map((s) => ({
    id: s.block_id,
    name: s.block_name || s.block_id,
  }));

  const reload = async () => {
    setLoading(true);
    try {
      const [a, j] = await Promise.all([
        api.get<ApplicationRecord[]>(`/api/programmes/v2/${artifactId}/applications`).catch(() => []),
        api.get<Adjustment[]>(`/api/programmes/v2/${artifactId}/adjustments`).catch(() => []),
      ]);
      setApps(a);
      setAdjs(j);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { reload(); }, [artifactId]);

  return (
    <Card className="mt-6">
      <CardContent className="py-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-semibold text-[var(--sapling-dark)]">
            <ClipboardCheck className="size-4" />
            Season tracker
          </h2>
          <div className="flex gap-1 rounded-md bg-muted p-0.5 text-xs">
            <button
              onClick={() => setTab("applications")}
              className={`rounded px-3 py-1 font-medium transition-colors ${
                tab === "applications"
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : "text-muted-foreground hover:text-[var(--sapling-dark)]"
              }`}
            >
              Applications · {apps.length}
            </button>
            <button
              onClick={() => setTab("adjustments")}
              className={`rounded px-3 py-1 font-medium transition-colors ${
                tab === "adjustments"
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : "text-muted-foreground hover:text-[var(--sapling-dark)]"
              }`}
            >
              Adjustments · {adjs.length}
            </button>
          </div>
        </div>

        {loading ? (
          <p className="py-4 text-center text-sm text-muted-foreground">Loading…</p>
        ) : tab === "applications" ? (
          <ApplicationsPanel
            artifactId={artifactId}
            blockOptions={blockOptions}
            apps={apps}
            onChange={reload}
          />
        ) : (
          <AdjustmentsPanel
            artifactId={artifactId}
            blockOptions={blockOptions}
            adjs={adjs}
            onChange={reload}
          />
        )}
      </CardContent>
    </Card>
  );
}

// ─── Applications panel ─────────────────────────────────────────────

function ApplicationsPanel({
  artifactId,
  blockOptions,
  apps,
  onChange,
}: {
  artifactId: string;
  blockOptions: Array<{ id: string; name: string }>;
  apps: ApplicationRecord[];
  onChange: () => void;
}) {
  const [adding, setAdding] = useState(false);
  return (
    <div>
      {!adding && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => setAdding(true)}
          className="mb-3"
        >
          <Plus className="size-3.5" />
          Record an application
        </Button>
      )}

      {adding && (
        <ApplicationForm
          artifactId={artifactId}
          blockOptions={blockOptions}
          onCancel={() => setAdding(false)}
          onSaved={() => { setAdding(false); onChange(); }}
        />
      )}

      {apps.length === 0 ? (
        <p className="py-4 text-center text-sm text-muted-foreground">
          No applications recorded yet.
        </p>
      ) : (
        <div className="space-y-2">
          {apps.map((a) => (
            <ApplicationRow key={a.id} app={a} blockOptions={blockOptions} onChange={onChange} />
          ))}
        </div>
      )}
    </div>
  );
}

function ApplicationForm({
  artifactId,
  blockOptions,
  onCancel,
  onSaved,
}: {
  artifactId: string;
  blockOptions: Array<{ id: string; name: string }>;
  onCancel: () => void;
  onSaved: () => void;
}) {
  const [blockId, setBlockId] = useState(blockOptions[0]?.id ?? "");
  const [actualDate, setActualDate] = useState(new Date().toISOString().slice(0, 10));
  const [product, setProduct] = useState("");
  const [rateKg, setRateKg] = useState("");
  const [rateL, setRateL] = useState("");
  const [method, setMethod] = useState("broadcast");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!blockId || !actualDate) {
      toast.error("Block + date are required");
      return;
    }
    setSaving(true);
    try {
      await api.post(`/api/programmes/v2/${artifactId}/applications`, {
        block_id: blockId,
        actual_date: actualDate,
        product_label: product || undefined,
        rate_kg_ha: rateKg ? parseFloat(rateKg) : undefined,
        rate_l_ha: rateL ? parseFloat(rateL) : undefined,
        method: method || undefined,
        notes: notes || undefined,
      });
      toast.success("Application recorded");
      onSaved();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to record");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mb-3 rounded-lg border bg-orange-50/30 p-3">
      <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
        New application
      </p>
      <div className="grid gap-2 sm:grid-cols-3">
        <div className="space-y-1">
          <Label className="text-xs">Block</Label>
          <select
            value={blockId}
            onChange={(e) => setBlockId(e.target.value)}
            className="w-full rounded border bg-white px-2 py-1.5 text-sm"
          >
            {blockOptions.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Date applied</Label>
          <Input
            type="date"
            value={actualDate}
            onChange={(e) => setActualDate(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Method</Label>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="w-full rounded border bg-white px-2 py-1.5 text-sm"
          >
            <option value="broadcast">Broadcast</option>
            <option value="band">Banded</option>
            <option value="side_dress">Banded ring</option>
            <option value="fertigation">Fertigation</option>
            <option value="foliar">Foliar</option>
          </select>
        </div>
        <div className="space-y-1 sm:col-span-3">
          <Label className="text-xs">Product / formula label</Label>
          <Input
            placeholder="e.g. 5:1:5 (17) + Ca 4.1%"
            value={product}
            onChange={(e) => setProduct(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Rate (kg/ha)</Label>
          <Input
            type="number"
            step="0.1"
            value={rateKg}
            onChange={(e) => setRateKg(e.target.value)}
            placeholder="optional"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Rate (L/ha — fertigation)</Label>
          <Input
            type="number"
            step="0.1"
            value={rateL}
            onChange={(e) => setRateL(e.target.value)}
            placeholder="optional"
          />
        </div>
        <div className="space-y-1 sm:col-span-3">
          <Label className="text-xs">Notes</Label>
          <Input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional context"
          />
        </div>
      </div>
      <div className="mt-3 flex justify-end gap-2">
        <Button variant="outline" size="sm" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={submit}
          disabled={saving}
          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
        >
          <Check className="size-3.5" />
          {saving ? "Saving…" : "Record"}
        </Button>
      </div>
    </div>
  );
}

function ApplicationRow({
  app,
  blockOptions,
  onChange,
}: {
  app: ApplicationRecord;
  blockOptions: Array<{ id: string; name: string }>;
  onChange: () => void;
}) {
  const blockName = blockOptions.find((b) => b.id === app.block_id)?.name ?? app.block_id;
  const variance = app.variance_flag ?? "unscheduled";
  const palette =
    variance === "on_plan"
      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
      : variance === "off_plan"
      ? "bg-amber-50 text-amber-800 border-amber-200"
      : "bg-red-50 text-red-800 border-red-200";

  const remove = async () => {
    if (!confirm("Remove this recorded application?")) return;
    try {
      await api.delete(`/api/programmes/v2/applications/${app.id}`);
      onChange();
      toast.success("Removed");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to remove");
    }
  };

  return (
    <div className="rounded-md border bg-white px-3 py-2 text-sm">
      <div className="flex items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <span className="font-medium text-[var(--sapling-dark)]">{blockName}</span>
          <span className="text-xs text-muted-foreground tabular-nums">{app.actual_date}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${palette}`}>
            {variance.replace("_", " ")}
          </span>
          <button
            onClick={remove}
            className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
            aria-label="Remove"
          >
            <Trash2 className="size-3.5" />
          </button>
        </div>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        {app.product_label ?? "(no product label)"}
        {" · "}
        {app.method ?? "method?"}
        {" · "}
        {app.rate_kg_ha != null && `${app.rate_kg_ha} kg/ha`}
        {app.rate_l_ha != null && ` · ${app.rate_l_ha} L/ha`}
      </p>
      {app.notes && <p className="mt-1 text-xs italic text-muted-foreground">{app.notes}</p>}
    </div>
  );
}

// ─── Adjustments panel ──────────────────────────────────────────────

function AdjustmentsPanel({
  artifactId,
  blockOptions,
  adjs,
  onChange,
}: {
  artifactId: string;
  blockOptions: Array<{ id: string; name: string }>;
  adjs: Adjustment[];
  onChange: () => void;
}) {
  const [adding, setAdding] = useState(false);
  return (
    <div>
      {!adding && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => setAdding(true)}
          className="mb-3"
        >
          <Plus className="size-3.5" />
          Propose an adjustment
        </Button>
      )}
      {adding && (
        <AdjustmentForm
          artifactId={artifactId}
          blockOptions={blockOptions}
          onCancel={() => setAdding(false)}
          onSaved={() => { setAdding(false); onChange(); }}
        />
      )}
      {adjs.length === 0 ? (
        <p className="py-4 text-center text-sm text-muted-foreground">
          No adjustments proposed.
        </p>
      ) : (
        <div className="space-y-2">
          {adjs.map((a) => (
            <AdjustmentRow key={a.id} adj={a} blockOptions={blockOptions} onChange={onChange} />
          ))}
        </div>
      )}
    </div>
  );
}

function AdjustmentForm({
  artifactId,
  blockOptions,
  onCancel,
  onSaved,
}: {
  artifactId: string;
  blockOptions: Array<{ id: string; name: string }>;
  onCancel: () => void;
  onSaved: () => void;
}) {
  const [blockId, setBlockId] = useState<string>("");
  const [trigger, setTrigger] = useState("manual");
  const [severity, setSeverity] = useState<"info" | "warn" | "critical">("info");
  const [proposal, setProposal] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!proposal.trim()) {
      toast.error("Proposal text is required");
      return;
    }
    setSaving(true);
    try {
      await api.post(`/api/programmes/v2/${artifactId}/adjustments`, {
        block_id: blockId || undefined,
        trigger_type: trigger,
        proposal,
        severity,
      });
      toast.success("Adjustment proposed");
      onSaved();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mb-3 rounded-lg border bg-orange-50/30 p-3">
      <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
        New adjustment proposal
      </p>
      <div className="grid gap-2 sm:grid-cols-3">
        <div className="space-y-1">
          <Label className="text-xs">Block (optional)</Label>
          <select
            value={blockId}
            onChange={(e) => setBlockId(e.target.value)}
            className="w-full rounded border bg-white px-2 py-1.5 text-sm"
          >
            <option value="">Whole programme</option>
            {blockOptions.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Trigger</Label>
          <select
            value={trigger}
            onChange={(e) => setTrigger(e.target.value)}
            className="w-full rounded border bg-white px-2 py-1.5 text-sm"
          >
            <option value="manual">Manual</option>
            <option value="leaf_analysis">Leaf analysis</option>
            <option value="soil_analysis">Soil analysis</option>
            <option value="off_programme">Off-programme application</option>
          </select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Severity</Label>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value as typeof severity)}
            className="w-full rounded border bg-white px-2 py-1.5 text-sm"
          >
            <option value="info">Info</option>
            <option value="warn">Warn</option>
            <option value="critical">Critical</option>
          </select>
        </div>
        <div className="space-y-1 sm:col-span-3">
          <Label className="text-xs">Proposal</Label>
          <textarea
            value={proposal}
            onChange={(e) => setProposal(e.target.value)}
            placeholder="e.g. Bring K fertigation forward 2 weeks; leaf K at 0.6% (low band)."
            rows={3}
            className="w-full rounded border bg-white px-2 py-1.5 text-sm"
          />
        </div>
      </div>
      <div className="mt-3 flex justify-end gap-2">
        <Button variant="outline" size="sm" onClick={onCancel} disabled={saving}>
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={submit}
          disabled={saving}
          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
        >
          <Check className="size-3.5" />
          {saving ? "Saving…" : "Propose"}
        </Button>
      </div>
    </div>
  );
}

function AdjustmentRow({
  adj,
  blockOptions,
  onChange,
}: {
  adj: Adjustment;
  blockOptions: Array<{ id: string; name: string }>;
  onChange: () => void;
}) {
  const blockName = adj.block_id
    ? (blockOptions.find((b) => b.id === adj.block_id)?.name ?? adj.block_id)
    : "Whole programme";
  const sevPalette =
    adj.severity === "critical"
      ? "bg-red-50 text-red-800 border-red-200"
      : adj.severity === "warn"
      ? "bg-amber-50 text-amber-800 border-amber-200"
      : "bg-blue-50 text-blue-800 border-blue-200";
  const statPalette =
    adj.status === "approved"
      ? "bg-emerald-100 text-emerald-800"
      : adj.status === "applied"
      ? "bg-emerald-100 text-emerald-800"
      : adj.status === "rejected"
      ? "bg-gray-100 text-gray-700"
      : "bg-orange-100 text-[var(--sapling-orange)]";

  const review = async (status: "approved" | "rejected" | "applied") => {
    try {
      await api.patch(`/api/programmes/v2/adjustments/${adj.id}/review`, { status });
      onChange();
      toast.success(`Marked ${status}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed");
    }
  };

  return (
    <div className="rounded-md border bg-white px-3 py-2 text-sm">
      <div className="flex items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <span className="font-medium text-[var(--sapling-dark)]">{blockName}</span>
          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${sevPalette}`}>
            {adj.severity}
          </span>
          <span className="text-xs text-muted-foreground">
            via {adj.trigger_type.replace("_", " ")}
          </span>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${statPalette}`}>
          {adj.status}
        </span>
      </div>
      <p className="mt-1 text-sm">{adj.proposal}</p>
      {adj.reviewer_notes && (
        <p className="mt-1 text-xs italic text-muted-foreground">Note: {adj.reviewer_notes}</p>
      )}
      {adj.status === "suggested" && (
        <div className="mt-2 flex gap-2">
          <button
            onClick={() => review("approved")}
            className="flex items-center gap-1 rounded-md bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-800 hover:bg-emerald-200"
          >
            <Check className="size-3" /> Approve
          </button>
          <button
            onClick={() => review("rejected")}
            className="flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-200"
          >
            <X className="size-3" /> Reject
          </button>
        </div>
      )}
      {adj.status === "approved" && (
        <button
          onClick={() => review("applied")}
          className="mt-2 flex items-center gap-1 rounded-md bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-800 hover:bg-emerald-200"
        >
          <AlertCircle className="size-3" /> Mark applied
        </button>
      )}
    </div>
  );
}
