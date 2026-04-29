"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Loader2,
  ArrowLeft,
  Archive,
  Download,
  FileBarChart,
  FileCheck,
  ShieldCheck,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Lock,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  archiveSoilReport,
  downloadSoilReportPdf,
  generateSoilReportNarrative,
  getSoilReport,
  getSoilReportNarrative,
  transitionSoilReportState,
  type NarrativeIssue,
  type NarrativeReport,
  type SoilReportResponse,
  type SoilReportState,
} from "@/lib/soil-reports";
import { useEffectiveAdmin } from "@/lib/use-effective-role";

export default function SoilReportPage() {
  const params = useParams<{ id: string; reportId: string }>();
  const router = useRouter();
  const clientId = params.id;
  const reportId = params.reportId;
  const isAdmin = useEffectiveAdmin();

  const [data, setData] = useState<SoilReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [transitioning, setTransitioning] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  // Narrative state — fetched separately so the action panel can
  // surface verdict/issues without bloating the artifact response.
  const [narrativeReport, setNarrativeReport] = useState<NarrativeReport | null>(null);
  const [narrativeGeneratedAt, setNarrativeGeneratedAt] = useState<string | null>(null);
  const [narrativeLockedAt, setNarrativeLockedAt] = useState<string | null>(null);
  const [hasOverrides, setHasOverrides] = useState(false);
  const [generating, setGenerating] = useState(false);
  // Tracks whether we already kicked off the auto-generate for non-
  // admins so the effect doesn't re-fire on every state change.
  const [autoGenAttempted, setAutoGenAttempted] = useState(false);

  async function loadAll() {
    try {
      setLoading(true);
      const [report, narrative] = await Promise.all([
        getSoilReport(reportId),
        getSoilReportNarrative(reportId),
      ]);
      setData(report);
      setNarrativeReport(narrative.narrative_report);
      setNarrativeGeneratedAt(narrative.narrative_generated_at);
      setNarrativeLockedAt(narrative.narrative_locked_at);
      setHasOverrides(
        !!narrative.narrative_overrides &&
          Object.keys(narrative.narrative_overrides).length > 0,
      );
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Failed to load report: ${msg}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportId]);

  // Non-admin auto-generate. The client-facing flow always serves the
  // Opus-prose PDF — there's no "engine baseline" path for end users.
  // When the page mounts and no narrative exists yet, fire generate
  // immediately so the Download CTA below lights up as soon as Opus
  // returns. Admins keep the explicit Generate / Regenerate / audit
  // controls for debugging.
  useEffect(() => {
    if (loading || isAdmin || autoGenAttempted) return;
    if (!data) return;
    if (narrativeReport) return; // already have one (or already locked)
    if (data.state !== "draft") return; // won't accept a generate
    setAutoGenAttempted(true);
    void handleGenerateNarrative();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, isAdmin, autoGenAttempted, data, narrativeReport]);

  async function handleDownloadPdf() {
    setDownloadingPdf(true);
    try {
      await downloadSoilReportPdf(reportId);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`PDF download failed: ${msg}`);
    } finally {
      setDownloadingPdf(false);
    }
  }

  async function handleGenerateNarrative() {
    setGenerating(true);
    try {
      const res = await generateSoilReportNarrative(reportId);
      setNarrativeReport(res.narrative_report);
      setNarrativeGeneratedAt(res.narrative_generated_at);
      setNarrativeLockedAt(res.narrative_locked_at ?? null);
      setHasOverrides(
        !!res.narrative_overrides &&
          Object.keys(res.narrative_overrides).length > 0,
      );
      const verdictMsg =
        res.narrative_report.verdict === "PASS"
          ? "Narrative passed audit"
          : `Narrative ${res.narrative_report.verdict.toLowerCase()} — review issues below`;
      toast.success(verdictMsg);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Generation failed: ${msg}`);
    } finally {
      setGenerating(false);
    }
  }

  async function handleTransition(newState: SoilReportState) {
    setTransitioning(true);
    try {
      const res = await transitionSoilReportState(reportId, newState);
      setData(res);
      setNarrativeLockedAt(res.narrative_locked_at);
      toast.success(`Soil report ${newState}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Transition failed: ${msg}`);
    } finally {
      setTransitioning(false);
    }
  }

  async function handleArchive() {
    if (!confirm("Archive this soil report?")) return;
    setTransitioning(true);
    try {
      await archiveSoilReport(reportId);
      toast.success("Soil report archived");
      router.push(`/clients/${clientId}/documents`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Archive failed: ${msg}`);
    } finally {
      setTransitioning(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto flex max-w-5xl items-center justify-center px-4 py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  if (!data) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <Card>
          <CardContent className="p-6">
            Soil report not found.
            <Button
              variant="link"
              onClick={() => router.push(`/clients/${clientId}/documents`)}
            >
              Back to documents
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isDraft = data.state === "draft";
  const payload = data.report_payload;
  const header = payload.header;

  return (
    <>
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        {/* Top action bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 print:hidden">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/clients/${clientId}/documents`)}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to documents
          </Button>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="default"
              size="sm"
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              title={
                hasOverrides
                  ? `Download PDF — includes Opus AI narrative${narrativeLockedAt ? " (locked)" : ""}`
                  : "Download Sapling-branded soil report PDF"
              }
            >
              {downloadingPdf ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Download PDF
              {hasOverrides && (
                <span className="ml-1 inline-flex items-center rounded bg-white/20 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide">
                  AI
                </span>
              )}
            </Button>
            {data.state === "draft" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleTransition("approved")}
                disabled={transitioning}
              >
                <ShieldCheck className="size-4" />
                Approve
              </Button>
            )}
            {data.state === "approved" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleTransition("draft")}
                disabled={transitioning}
              >
                <RefreshCw className="size-4" />
                Re-open as draft
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleArchive}
              disabled={transitioning || data.state === "archived"}
              title="Archive this report"
            >
              <Archive className="size-4" />
              Archive
            </Button>
          </div>
        </div>

        {/* Header card */}
        <Card>
          <CardContent className="p-5">
            <div className="flex items-start gap-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
                <FileBarChart className="size-5" />
              </div>
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">
                  {data.title || "Soil Report"}
                </h1>
                <p className="mt-1 text-sm text-muted-foreground">
                  {[
                    header.farm_name,
                    header.client_name,
                    `${header.block_count} block${header.block_count !== 1 ? "s" : ""}`,
                    `${header.analysis_count} analys${header.analysis_count === 1 ? "is" : "es"}`,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <span className="rounded bg-orange-100 px-2 py-1 text-[10px] font-bold uppercase text-[var(--sapling-orange)]">
                    {scopeLabelFor(header.scope_kind)}
                  </span>
                  <span
                    className={`rounded px-2 py-1 text-[10px] font-bold uppercase ${
                      data.state === "draft"
                        ? "bg-slate-200 text-slate-800"
                        : data.state === "approved"
                          ? "bg-green-100 text-green-800"
                          : "bg-stone-200 text-stone-700"
                    }`}
                  >
                    {data.state}
                  </span>
                  {narrativeLockedAt && (
                    <span className="inline-flex items-center gap-1 rounded bg-slate-200 px-2 py-1 text-[10px] font-bold uppercase text-slate-700">
                      <Lock className="size-3" />
                      Narrative locked
                    </span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Download / progress hero — prominent CTA visible to every
            user the moment the AI report is ready. Hidden on print. */}
        <DownloadHero
          generating={generating}
          hasOverrides={hasOverrides}
          downloadingPdf={downloadingPdf}
          onDownload={handleDownloadPdf}
        />

        {/* Narrative panel — admin-only. Client-facing pages auto-fire
            the generate above and never surface the verdict / audit
            findings / regenerate controls. */}
        {isAdmin && (
          <NarrativePanel
            state={data.state as SoilReportState}
            report={narrativeReport}
            generatedAt={narrativeGeneratedAt}
            lockedAt={narrativeLockedAt}
            hasOverrides={hasOverrides}
            generating={generating}
            onGenerate={handleGenerateNarrative}
          />
        )}

        {/* Headline signals */}
        {payload.headline_signals && payload.headline_signals.length > 0 && (
          <Card>
            <CardContent className="space-y-2 p-4">
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Loudest signals
              </p>
              <ul className="space-y-1 text-sm">
                {payload.headline_signals.map((sig: string, i: number) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-[var(--sapling-orange)]">●</span>
                    {sig}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Per-block soil snapshots — engine baseline view. The PDF
            uses richer Sapling-branded visuals; this on-screen view
            is a simpler text breakdown so the agronomist can scan
            findings without rendering a PDF. */}
        {payload.soil_snapshots && payload.soil_snapshots.length > 0 && (
          <SnapshotList snapshots={payload.soil_snapshots} />
        )}

        {/* Trends section — only when ≥ 1 block has multi-analysis history */}
        {payload.trend_reports && payload.trend_reports.length > 0 && (
          <TrendsList trends={payload.trend_reports} />
        )}

        {/* Holistic signals (multi-block) */}
        {payload.holistic_signals && payload.holistic_signals.length > 0 && (
          <Card>
            <CardContent className="space-y-2 p-4">
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Across the farm
              </p>
              <ol className="space-y-2 text-sm">
                {payload.holistic_signals.map((sig: string, i: number) => (
                  <li key={i} className="flex gap-3">
                    <span className="font-mono text-xs text-muted-foreground">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span>{sig}</span>
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
}

function DownloadHero({
  generating,
  hasOverrides,
  downloadingPdf,
  onDownload,
}: {
  generating: boolean;
  hasOverrides: boolean;
  downloadingPdf: boolean;
  onDownload: () => void;
}) {
  // Three states drive the hero:
  //   1. AI prose is being generated → progress card
  //   2. AI prose ready (overrides present) → big download CTA
  //   3. AI prose absent + not generating → engine baseline still
  //      downloadable, but quieter card so the user knows the AI
  //      version isn't on this PDF.
  if (generating) {
    return (
      <Card className="border-l-4 border-l-[var(--sapling-orange)] bg-orange-50/40 print:hidden">
        <CardContent className="flex items-center gap-4 p-5">
          <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
          <div className="flex-1">
            <div className="text-base font-semibold text-[var(--sapling-dark)]">
              Generating AI report…
            </div>
            <div className="mt-0.5 text-sm text-muted-foreground">
              Opus is reading the analyses and writing the executive summary.
              Usually 15-30 seconds.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
  if (hasOverrides) {
    return (
      <Card className="border-l-4 border-l-green-600 bg-green-50/40 print:hidden">
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5">
          <div className="flex items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-green-100">
              <FileCheck className="size-5 text-green-700" />
            </div>
            <div>
              <div className="text-base font-semibold text-[var(--sapling-dark)]">
                Report ready
              </div>
              <div className="mt-0.5 text-sm text-muted-foreground">
                Soil report — Sapling-branded PDF, ready to download.
              </div>
            </div>
          </div>
          <Button
            variant="default"
            size="lg"
            onClick={onDownload}
            disabled={downloadingPdf}
            className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
          >
            {downloadingPdf ? (
              <Loader2 className="size-5 animate-spin" />
            ) : (
              <Download className="size-5" />
            )}
            Download PDF
          </Button>
        </CardContent>
      </Card>
    );
  }
  // No narrative, no generation in flight — engine baseline available.
  return (
    <Card className="border-l-4 border-l-slate-300 bg-slate-50/60 print:hidden">
      <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5">
        <div>
          <div className="text-base font-semibold text-[var(--sapling-dark)]">
            Engine baseline ready
          </div>
          <div className="mt-0.5 text-sm text-muted-foreground">
            Soil interpretation without AI narrative — download as-is.
          </div>
        </div>
        <Button
          variant="default"
          size="lg"
          onClick={onDownload}
          disabled={downloadingPdf}
          className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
        >
          {downloadingPdf ? (
            <Loader2 className="size-5 animate-spin" />
          ) : (
            <Download className="size-5" />
          )}
          Download PDF
        </Button>
      </CardContent>
    </Card>
  );
}


function scopeLabelFor(scope: string): string {
  return (
    {
      single_block: "Single block",
      block_with_history: "Block + history",
      multi_block: "Multi-block",
    }[scope] || scope
  );
}

function NarrativePanel({
  state,
  report,
  generatedAt,
  lockedAt,
  hasOverrides,
  generating,
  onGenerate,
}: {
  state: SoilReportState;
  report: NarrativeReport | null;
  generatedAt: string | null;
  lockedAt: string | null;
  hasOverrides: boolean;
  generating: boolean;
  onGenerate: () => void;
}) {
  // No narrative yet, draft state — show CTA. Hide entirely after
  // approval if no narrative was ever generated (the absence is
  // intentional; engine baseline carries the prose).
  if (!report && !generating) {
    if (state !== "draft") return null;
    return (
      <Card className="border-l-4 border-l-[var(--sapling-orange)]/60 bg-orange-50/40 print:hidden">
        <CardContent className="flex flex-wrap items-start gap-3 p-4">
          <div className="flex-1 text-sm">
            <div className="font-medium text-[var(--sapling-dark)]">
              Generate AI narrative
            </div>
            <div className="mt-1 text-muted-foreground">
              Run Opus over the report to add an agronomist-voice executive
              summary + (when multi-block) cross-farm framing. Three-layer
              audit gates the prose.
            </div>
          </div>
          <Button
            variant="default"
            size="sm"
            className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
            onClick={onGenerate}
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
            <div className="text-muted-foreground">~15-30 s.</div>
          </div>
        </CardContent>
      </Card>
    );
  }
  if (!report) return null;

  const verdictPill = (() => {
    if (report.verdict === "PASS") {
      return { Icon: CheckCircle2, bg: "bg-green-100", text: "text-green-800", border: "border-l-green-600", label: "Passed" };
    }
    if (report.verdict === "FAIL") {
      return { Icon: XCircle, bg: "bg-red-100", text: "text-red-800", border: "border-l-red-600", label: "Failed audit — engine baseline used" };
    }
    return { Icon: AlertTriangle, bg: "bg-amber-100", text: "text-amber-800", border: "border-l-amber-600", label: "Passed with warnings" };
  })();

  const generatedDate = generatedAt
    ? new Date(generatedAt).toLocaleString(undefined, {
        year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
      })
    : null;
  const cost = report.cost_usd?.toFixed(2) ?? "—";
  const canRegenerate = !lockedAt && state === "draft";

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
                <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${verdictPill.bg} ${verdictPill.text}`}>
                  {verdictPill.label}
                </span>
                {lockedAt && (
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
              onClick={onGenerate}
              disabled={generating}
            >
              {generating ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
              Regenerate
            </Button>
          )}
        </div>
        {report.issues.length > 0 && <IssuesList issues={report.issues} />}
      </CardContent>
    </Card>
  );
}

function IssuesList({ issues }: { issues: NarrativeIssue[] }) {
  const order: Record<NarrativeIssue["severity"], number> = { fail: 0, warn: 1, info: 2 };
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
          <div key={i} className={`rounded border px-3 py-2 text-xs ${sevStyle}`}>
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

function SnapshotList({ snapshots }: { snapshots: Array<Record<string, unknown>> }) {
  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
          Per-block detail
        </p>
        {snapshots.map((snap, i) => {
          const findings = (snap.factor_findings as Array<Record<string, unknown>> | null) || [];
          const headlines = (snap.headline_signals as string[] | null) || [];
          return (
            <div key={i} className="border-t pt-3 first:border-t-0 first:pt-0">
              <div className="flex items-baseline justify-between">
                <h3 className="font-semibold">{snap.block_name as string}</h3>
                <span className="text-xs text-muted-foreground">
                  {snap.block_area_ha ? `${(snap.block_area_ha as number).toFixed(2)} ha` : null}
                  {snap.sample_date ? ` · sampled ${snap.sample_date}` : null}
                </span>
              </div>
              {headlines.length > 0 && (
                <ul className="mt-2 space-y-1 text-sm">
                  {headlines.map((s, j) => (
                    <li key={j} className="flex gap-2">
                      <span className="text-[var(--sapling-orange)]">●</span>
                      {s}
                    </li>
                  ))}
                </ul>
              )}
              {findings.length > 0 && (
                <details className="mt-2 text-xs">
                  <summary className="cursor-pointer text-muted-foreground">
                    {findings.length} finding{findings.length !== 1 ? "s" : ""}
                  </summary>
                  <ul className="mt-1 space-y-1">
                    {findings.map((f, j) => (
                      <li key={j} className="ml-4 list-disc">
                        <span className="font-medium">[{f.severity as string}]</span>{" "}
                        {f.message as string}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

function TrendsList({ trends }: { trends: Array<Record<string, unknown>> }) {
  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
          Trends over time
        </p>
        {trends.map((trend, i) => {
          const params = (trend.parameters as Array<Record<string, unknown>> | null) || [];
          const headlines = (trend.headline_signals as string[] | null) || [];
          return (
            <div key={i} className="border-t pt-3 first:border-t-0 first:pt-0">
              <h3 className="font-semibold">{trend.block_name as string}</h3>
              <p className="text-xs text-muted-foreground">
                {trend.n_analyses as number} analyses · {trend.span_days as number} days
              </p>
              {headlines.length > 0 && (
                <ul className="mt-2 space-y-1 text-sm">
                  {headlines.map((s, j) => (
                    <li key={j}>{s}</li>
                  ))}
                </ul>
              )}
              {params.length > 0 && (
                <details className="mt-2 text-xs">
                  <summary className="cursor-pointer text-muted-foreground">
                    Parameter-by-parameter
                  </summary>
                  <table className="mt-2 w-full text-xs">
                    <thead className="bg-muted/30 text-left">
                      <tr>
                        <th className="px-2 py-1">Parameter</th>
                        <th className="px-2 py-1">Earliest → Latest</th>
                        <th className="px-2 py-1">Direction</th>
                        <th className="px-2 py-1">Significance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {params.map((p, j) => (
                        <tr key={j} className="border-b last:border-0">
                          <td className="px-2 py-1 font-medium">{p.parameter as string}</td>
                          <td className="px-2 py-1 tabular-nums">
                            {(p.earliest_value as number)?.toFixed(2)} →{" "}
                            {(p.latest_value as number)?.toFixed(2)}
                          </td>
                          <td className="px-2 py-1">
                            <span className="capitalize">{p.direction as string}</span>
                          </td>
                          <td className="px-2 py-1">
                            <span className="capitalize">{p.significance as string}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
