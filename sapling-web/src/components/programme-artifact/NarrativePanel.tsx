"use client";

import { useEffect, useState } from "react";
import {
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Lock,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  generateProgrammeNarrative,
  getProgrammeNarrative,
  type NarrativeIssue,
  type NarrativeReport,
} from "@/lib/programmes-v2";
import { ProgrammeState } from "@/lib/types/programme-artifact";

/**
 * Opus narrative review panel for the artifact page.
 *
 * Lifecycle:
 *   - Empty state: "Generate Narrative" CTA (only shown while artifact
 *     is in draft).
 *   - Generating: live spinner. ~30-60s end-to-end. Single API call —
 *     the backend runs all sections sequentially because the prompt-
 *     cache is most effective in series.
 *   - Generated (not yet locked): verdict pill, cost line, issues list
 *     when verdict ≠ PASS, regenerate button.
 *   - Locked (artifact approved): same readout with a lock badge,
 *     regenerate hidden.
 *
 * The narrative is locked automatically on draft → approved transition
 * (see programmes_v2.transition_state). The user reverts to draft to
 * regenerate after approval — explicit intent, audit trail intact.
 */
export function NarrativePanel({
  artifactId,
  state,
  onNarrativeChange,
}: {
  artifactId: string;
  state: ProgrammeState;
  /** Fires after a successful generate or initial fetch. Lets the
   * parent page refresh sibling UI (e.g. the Download PDF button's
   * "AI prose included" indicator) without re-fetching narrative
   * state at every render. */
  onNarrativeChange?: () => void;
}) {
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [report, setReport] = useState<NarrativeReport | null>(null);
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);
  const [lockedAt, setLockedAt] = useState<string | null>(null);
  const [hasOverrides, setHasOverrides] = useState(false);

  // Fetch persisted narrative state on mount + after every regenerate.
  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        setLoading(true);
        const res = await getProgrammeNarrative(artifactId);
        if (ignore) return;
        setReport(res.narrative_report ?? null);
        setGeneratedAt(res.narrative_generated_at);
        setLockedAt(res.narrative_locked_at);
        setHasOverrides(
          !!res.narrative_overrides &&
            Object.keys(res.narrative_overrides).length > 0,
        );
        onNarrativeChange?.();
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        toast.error(`Failed to load narrative: ${msg}`);
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [artifactId, onNarrativeChange]);

  async function handleGenerate() {
    setGenerating(true);
    try {
      const res = await generateProgrammeNarrative(artifactId);
      setReport(res.narrative_report);
      setGeneratedAt(res.narrative_generated_at);
      setLockedAt(res.narrative_locked_at ?? null);
      setHasOverrides(
        !!res.narrative_overrides &&
          Object.keys(res.narrative_overrides).length > 0,
      );
      const verdictMsg =
        res.narrative_report.verdict === "PASS"
          ? "Narrative passed audit"
          : `Narrative ${res.narrative_report.verdict.toLowerCase()} — review issues below`;
      toast.success(verdictMsg);
      onNarrativeChange?.();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Generation failed: ${msg}`);
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return null; // Silent — page-level loader is already covering this
  }

  // No narrative yet, artifact still in draft → show CTA. Hide entirely
  // for non-draft states (post-approval the absence is permanent and
  // the engine baseline drives the PDF).
  if (!report && !generating) {
    if (state !== ProgrammeState.DRAFT) {
      return null;
    }
    return (
      <Card className="border-l-4 border-l-[var(--sapling-orange)]/60 bg-orange-50/40 print:hidden">
        <CardContent className="flex flex-wrap items-start gap-3 p-4">
          <div className="flex-1 text-sm">
            <div className="font-medium text-[var(--sapling-dark)]">
              Generate AI narrative
            </div>
            <div className="mt-1 text-muted-foreground">
              Run Opus over the engine output to add agronomist-voice prose
              to the report. Takes 30–60 s and ~$0.25 per programme. Three-
              layer audit (engine + fact validator + policeman) gates the
              prose against fabrication and disclosure breaches.
            </div>
          </div>
          <Button
            variant="default"
            size="sm"
            className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating && <Loader2 className="size-4 animate-spin" />}
            Generate narrative
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (generating && !report) {
    return (
      <Card className="border-l-4 border-l-[var(--sapling-orange)]/60 bg-orange-50/40 print:hidden">
        <CardContent className="flex items-center gap-3 p-4 text-sm">
          <Loader2 className="size-5 animate-spin text-[var(--sapling-orange)]" />
          <div>
            <div className="font-medium">Generating narrative…</div>
            <div className="text-muted-foreground">
              Running 4 Opus sections sequentially (cache-warmed). Audit
              passes after the prose lands. ~30–60 s.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!report) return null;

  const isLocked = !!lockedAt;
  const canRegenerate = !isLocked && state === ProgrammeState.DRAFT;
  const verdictPill = (() => {
    if (report.verdict === "PASS") {
      return {
        Icon: CheckCircle2,
        bg: "bg-green-100",
        text: "text-green-800",
        border: "border-l-green-600",
        label: "Passed",
      };
    }
    if (report.verdict === "FAIL") {
      return {
        Icon: XCircle,
        bg: "bg-red-100",
        text: "text-red-800",
        border: "border-l-red-600",
        label: "Failed audit — engine baseline used",
      };
    }
    return {
      Icon: AlertTriangle,
      bg: "bg-amber-100",
      text: "text-amber-800",
      border: "border-l-amber-600",
      label: "Passed with warnings",
    };
  })();

  const generatedDate = generatedAt
    ? new Date(generatedAt).toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  const cost = report.cost_usd?.toFixed(2) ?? "—";

  return (
    <Card className={`border-l-4 ${verdictPill.border} print:hidden`}>
      <CardContent className="space-y-3 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <verdictPill.Icon className={`mt-0.5 size-5 shrink-0 ${verdictPill.text}`} />
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-[var(--sapling-dark)]">
                  AI narrative
                </span>
                <span
                  className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${verdictPill.bg} ${verdictPill.text}`}
                >
                  {verdictPill.label}
                </span>
                {isLocked && (
                  <span className="inline-flex items-center gap-1 rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-bold uppercase text-slate-700">
                    <Lock className="size-3" />
                    Locked
                  </span>
                )}
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                {generatedDate && <>Generated {generatedDate} · </>}
                {report.section_count} section{report.section_count !== 1 ? "s" : ""}
                {" · "}~${cost}
                {" · "}
                {report.duration_seconds.toFixed(0)}s
                {hasOverrides ? " · prose applied to PDF" : " · engine baseline used"}
              </div>
            </div>
          </div>
          {canRegenerate && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerate}
              disabled={generating}
              title="Run Opus again (replaces the current narrative)"
            >
              {generating ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <RefreshCw className="size-4" />
              )}
              Regenerate
            </Button>
          )}
        </div>

        {report.issues.length > 0 && (
          <IssuesList issues={report.issues} />
        )}
      </CardContent>
    </Card>
  );
}

function IssuesList({ issues }: { issues: NarrativeIssue[] }) {
  // Group by severity so the user sees FAILs first, then WARNs, then INFOs.
  const order: Record<NarrativeIssue["severity"], number> = {
    fail: 0,
    warn: 1,
    info: 2,
  };
  const sorted = [...issues].sort((a, b) => order[a.severity] - order[b.severity]);

  return (
    <div className="space-y-2 border-t pt-3">
      <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
        Audit findings
      </div>
      {sorted.map((issue, i) => {
        const sevStyle =
          issue.severity === "fail"
            ? "border-red-300 bg-red-50 text-red-900"
            : issue.severity === "warn"
              ? "border-amber-300 bg-amber-50 text-amber-900"
              : "border-slate-200 bg-slate-50 text-slate-800";
        return (
          <div
            key={i}
            className={`rounded border px-3 py-2 text-xs ${sevStyle}`}
          >
            <div className="flex flex-wrap items-baseline gap-2">
              <span className="font-bold uppercase">[{issue.severity}]</span>
              <span className="font-medium">{issue.category}</span>
              <span className="text-muted-foreground">@ {issue.where}</span>
            </div>
            <div className="mt-1">{issue.what}</div>
            {issue.fix && (
              <div className="mt-1 italic text-muted-foreground">Fix: {issue.fix}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
