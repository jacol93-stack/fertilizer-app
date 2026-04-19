"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Loader2,
  Upload,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from "lucide-react";
import type {
  ProgrammeAdjustment,
  AdjustmentProposal,
} from "@/lib/season-constants";
import { MONTH_NAMES } from "@/lib/season-constants";

interface AdjustmentsViewProps {
  programmeId: string;
}

const STATUS_COLORS: Record<string, string> = {
  suggested: "bg-amber-100 text-amber-800 border-amber-300",
  approved: "bg-blue-100 text-blue-800 border-blue-300",
  applied: "bg-green-100 text-green-800 border-green-300",
  rejected: "bg-gray-100 text-gray-600 border-gray-300",
};

const TRIGGER_LABEL: Record<string, string> = {
  soil_analysis: "Soil Analysis",
  leaf_analysis: "Leaf Analysis",
  observation: "Field Observation",
  weather: "Weather Event",
  manual: "Manual",
};

export function AdjustmentsView({ programmeId }: AdjustmentsViewProps) {
  const [adjustments, setAdjustments] = useState<ProgrammeAdjustment[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [proposals, setProposals] = useState<Record<string, AdjustmentProposal>>({});
  const [working, setWorking] = useState<string | null>(null);

  const loadAdjustments = useCallback(() => {
    setLoading(true);
    api.get<ProgrammeAdjustment[]>(`/api/programmes/${programmeId}/adjustments`)
      .then(setAdjustments)
      .catch(() => toast.error("Failed to load adjustments"))
      .finally(() => setLoading(false));
  }, [programmeId]);

  useEffect(() => {
    loadAdjustments();
  }, [loadAdjustments]);

  const togglePreview = async (adj: ProgrammeAdjustment) => {
    if (expanded === adj.id) {
      setExpanded(null);
      return;
    }
    setExpanded(adj.id);
    if (proposals[adj.id] || adj.status === "applied" || adj.status === "rejected") {
      return;
    }
    try {
      const p = await api.get<AdjustmentProposal>(
        `/api/programmes/${programmeId}/adjustments/${adj.id}/proposal`
      );
      setProposals((prev) => ({ ...prev, [adj.id]: p }));
    } catch {
      toast.error("Failed to load proposal");
    }
  };

  const review = async (adj: ProgrammeAdjustment, status: "approved" | "rejected") => {
    setWorking(adj.id);
    try {
      await api.post(`/api/programmes/${programmeId}/adjustments/${adj.id}/review`, { status });
      toast.success(status === "approved" ? "Adjustment approved" : "Adjustment rejected");
      loadAdjustments();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Review failed");
    } finally {
      setWorking(null);
    }
  };

  const apply = async (adj: ProgrammeAdjustment) => {
    const force = adj.status === "suggested";
    const msg = force
      ? "Apply this adjustment directly (skipping review)? The remaining programme blends will be updated."
      : "Apply this adjustment now? The remaining programme blends will be updated.";
    if (!confirm(msg)) return;

    setWorking(adj.id);
    try {
      const result = await api.post<{ blends_updated: number; errors: unknown[] }>(
        `/api/programmes/${programmeId}/adjustments/${adj.id}/apply`,
        { force }
      );
      toast.success(`Applied — ${result.blends_updated} blends updated`);
      loadAdjustments();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Apply failed");
    } finally {
      setWorking(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const pending = adjustments.filter((a) => a.status === "suggested" || a.status === "approved");
  const history = adjustments.filter((a) => a.status === "applied" || a.status === "rejected");

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Mid-Season Adjustments</h3>
          <p className="text-sm text-muted-foreground">
            Review and apply adjustments triggered by new soil or leaf data
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => window.location.href = `/season-manager/${programmeId}/upload`}
        >
          <Upload className="size-4" />
          Upload New Analysis
        </Button>
      </div>

      {adjustments.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Sparkles className="mx-auto mb-3 size-10 text-muted-foreground/30" />
            <p className="font-medium text-muted-foreground">No adjustments yet</p>
            <p className="mt-1 text-sm text-muted-foreground/70">
              Adjustments appear here when new soil or leaf data shows the programme needs shifting
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {pending.length > 0 && (
            <div>
              <h4 className="mb-3 text-sm font-semibold text-amber-700">
                Needs Review ({pending.length})
              </h4>
              <div className="space-y-3">
                {pending.map((adj) => (
                  <AdjustmentCard
                    key={adj.id}
                    adj={adj}
                    expanded={expanded === adj.id}
                    proposal={proposals[adj.id]}
                    working={working === adj.id}
                    onToggle={() => togglePreview(adj)}
                    onApprove={() => review(adj, "approved")}
                    onReject={() => review(adj, "rejected")}
                    onApply={() => apply(adj)}
                  />
                ))}
              </div>
            </div>
          )}

          {history.length > 0 && (
            <div>
              <h4 className="mb-3 text-sm font-semibold text-muted-foreground">
                History ({history.length})
              </h4>
              <div className="space-y-2">
                {history.map((adj) => (
                  <AdjustmentCard
                    key={adj.id}
                    adj={adj}
                    expanded={expanded === adj.id}
                    proposal={proposals[adj.id]}
                    working={working === adj.id}
                    onToggle={() => togglePreview(adj)}
                    onApprove={() => {}}
                    onReject={() => {}}
                    onApply={() => {}}
                    readOnly
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

interface AdjustmentCardProps {
  adj: ProgrammeAdjustment;
  expanded: boolean;
  proposal?: AdjustmentProposal;
  working: boolean;
  onToggle: () => void;
  onApprove: () => void;
  onReject: () => void;
  onApply: () => void;
  readOnly?: boolean;
}

function AdjustmentCard({
  adj, expanded, proposal, working,
  onToggle, onApprove, onReject, onApply, readOnly,
}: AdjustmentCardProps) {
  const status = adj.status || "applied";
  const triggerLabel = TRIGGER_LABEL[adj.trigger_type] || adj.trigger_type;
  const colorClass = STATUS_COLORS[status] || STATUS_COLORS.applied;

  return (
    <Card className={status === "suggested" ? "border-amber-200" : undefined}>
      <CardContent className="py-4">
        <div className="flex items-start gap-3">
          {status === "suggested" ? (
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-500" />
          ) : status === "applied" ? (
            <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-green-600" />
          ) : status === "rejected" ? (
            <XCircle className="mt-0.5 size-4 shrink-0 text-gray-400" />
          ) : (
            <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-blue-500" />
          )}

          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${colorClass}`}>
                {status}
              </span>
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                {triggerLabel}
              </span>
              <span className="text-xs text-muted-foreground">
                {new Date(adj.created_at).toLocaleDateString()}
              </span>
            </div>

            {adj.notes && (
              <p className="mt-1.5 text-sm font-medium text-[var(--sapling-dark)]">{adj.notes}</p>
            )}

            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="outline" size="sm" onClick={onToggle}>
                {expanded ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
                {expanded ? "Hide details" : "Show details"}
              </Button>
              {!readOnly && status === "suggested" && (
                <>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onApprove}
                    disabled={working}
                  >
                    {working ? <Loader2 className="size-3 animate-spin" /> : <CheckCircle2 className="size-3" />}
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onReject}
                    disabled={working}
                    className="text-red-600 hover:bg-red-50"
                  >
                    <XCircle className="size-3" />
                    Reject
                  </Button>
                </>
              )}
              {!readOnly && (status === "suggested" || status === "approved") && (
                <Button
                  size="sm"
                  onClick={onApply}
                  disabled={working}
                  className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                >
                  {working ? <Loader2 className="size-3 animate-spin" /> : <Sparkles className="size-3" />}
                  Apply to Programme
                </Button>
              )}
            </div>

            {expanded && proposal && (
              <ProposalDetail proposal={proposal} />
            )}
            {expanded && !proposal && status !== "applied" && status !== "rejected" && (
              <div className="mt-3 flex items-center gap-2 rounded border border-muted bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                <Loader2 className="size-3 animate-spin" />
                Loading proposal…
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ProposalDetail({ proposal }: { proposal: AdjustmentProposal }) {
  const s = proposal.summary;
  const affected = proposal.affected_blends.filter((b) => b.changed);

  // Foliar proposal (leaf trigger)
  if (proposal.proposed_foliar) {
    const f = proposal.proposed_foliar;
    return (
      <div className="mt-3 space-y-3 rounded-lg border bg-muted/20 p-3 text-sm">
        <div>
          <p className="font-medium">Proposed foliar application</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Target month: {MONTH_NAMES[f.target_month]}
          </p>
        </div>
        {f.deficient_elements.length > 0 && (
          <div>
            <p className="text-xs font-medium text-amber-700">Deficient elements</p>
            <p className="text-xs">{f.deficient_elements.join(", ")}</p>
          </div>
        )}
        {f.excess_elements.length > 0 && (
          <div>
            <p className="text-xs font-medium text-red-700">Excess elements</p>
            <p className="text-xs">{f.excess_elements.join(", ")}</p>
          </div>
        )}
      </div>
    );
  }

  // Soil proposal
  return (
    <div className="mt-3 space-y-3 rounded-lg border bg-muted/20 p-3 text-sm">
      {s.season_totals && (
        <div>
          <p className="text-xs font-semibold text-muted-foreground">Season totals (kg/ha)</p>
          <div className="mt-1 overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-muted-foreground">
                <tr>
                  <th className="py-1 pr-3 text-left">Nutrient</th>
                  <th className="py-1 pr-3 text-right">Old</th>
                  <th className="py-1 pr-3 text-right">New</th>
                  <th className="py-1 pr-3 text-right">Δ</th>
                </tr>
              </thead>
              <tbody>
                {Object.keys(s.season_totals.old).sort().map((nut) => {
                  const oldV = s.season_totals!.old[nut];
                  const newV = s.season_totals!.new[nut] ?? 0;
                  const d = newV - oldV;
                  if (Math.abs(d) < 0.05 && oldV < 0.05 && newV < 0.05) return null;
                  const changed = Math.abs(d) >= 0.05;
                  return (
                    <tr key={nut} className="border-t border-muted">
                      <td className="py-1 pr-3 font-medium uppercase">{nut}</td>
                      <td className="py-1 pr-3 text-right tabular-nums">{oldV.toFixed(1)}</td>
                      <td className="py-1 pr-3 text-right tabular-nums">{newV.toFixed(1)}</td>
                      <td className={`py-1 pr-3 text-right tabular-nums font-medium ${
                        changed && d > 0 ? "text-red-600" : changed && d < 0 ? "text-blue-600" : "text-muted-foreground"
                      }`}>
                        {d > 0 ? "+" : ""}{d.toFixed(1)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {affected.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-muted-foreground">
            {affected.length} application{affected.length !== 1 ? "s" : ""} will shift
          </p>
          <div className="mt-1 space-y-1">
            {affected.slice(0, 5).map((b) => (
              <div key={b.id} className="flex items-center justify-between rounded bg-white/50 px-2 py-1 text-xs">
                <span className="font-medium">
                  {MONTH_NAMES[b.application_month ?? 1]} · {b.stage_name || "Stage"}
                </span>
                <span className="text-muted-foreground">
                  {b.old.rate_kg_ha}kg → {b.new.rate_kg_ha}kg/ha
                </span>
              </div>
            ))}
            {affected.length > 5 && (
              <p className="text-xs text-muted-foreground/70">…and {affected.length - 5} more</p>
            )}
          </div>
        </div>
      )}

      {s.past_applications !== undefined && s.past_applications > 0 && (
        <p className="text-xs text-muted-foreground">
          {s.past_applications} past application{s.past_applications !== 1 ? "s" : ""} will not be modified
        </p>
      )}
      {s.reason && (
        <p className="text-xs text-amber-700">Note: {s.reason}</p>
      )}
    </div>
  );
}
