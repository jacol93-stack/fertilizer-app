"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Loader2,
  ArrowLeft,
  CheckCircle2,
  Archive,
  Printer,
  ShieldCheck,
  Download,
  FileCheck,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { ArtifactView } from "@/components/programme-artifact/ArtifactView";
import { NarrativePanel } from "@/components/programme-artifact/NarrativePanel";
import { SeasonTracker } from "@/components/season-tracker/SeasonTracker";
import {
  archiveProgramme,
  downloadProgrammePdf,
  generateProgrammeNarrative,
  getProgramme,
  getProgrammeNarrative,
  transitionProgrammeState,
} from "@/lib/programmes-v2";
import { useEffectiveAdmin } from "@/lib/use-effective-role";
import type {
  BuildProgrammeResponse,
  ProgrammeState,
  ReviewInfo,
} from "@/lib/types/programme-artifact";
import { ProgrammeState as State } from "@/lib/types/programme-artifact";

export default function ProgrammeArtifactPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const isAdmin = useEffectiveAdmin();
  const [data, setData] = useState<BuildProgrammeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [transitioning, setTransitioning] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  // Tracks whether persisted Opus prose is on this artifact. Used to
  // surface an AI label on the Download button so the user knows
  // their click will produce the AI-prose PDF, not the engine-
  // baseline one.
  const [hasOpusProse, setHasOpusProse] = useState(false);
  const [narrativeLocked, setNarrativeLocked] = useState(false);
  // Auto-generate state for non-admin flow.
  const [autoGenAttempted, setAutoGenAttempted] = useState(false);
  const [autoGenerating, setAutoGenerating] = useState(false);
  const [narrativeRefresh, setNarrativeRefresh] = useState(0);

  async function handleDownloadPdf() {
    if (!data) return;
    setDownloadingPdf(true);
    try {
      await downloadProgrammePdf(params.id);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`PDF download failed: ${msg}`);
    } finally {
      setDownloadingPdf(false);
    }
  }

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        setLoading(true);
        const res = await getProgramme(params.id);
        if (!ignore) setData(res);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        toast.error(`Failed to load programme: ${msg}`);
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [params.id]);

  // Narrative state — refetched whenever the NarrativePanel reports a
  // regenerate or a lock change. Drives the Download button indicator.
  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const n = await getProgrammeNarrative(params.id);
        if (ignore) return;
        const present = !!(
          n.narrative_overrides &&
          Object.keys(n.narrative_overrides).length > 0
        );
        setHasOpusProse(present);
        setNarrativeLocked(!!n.narrative_locked_at);
      } catch {
        // Silent — the panel itself surfaces narrative errors. The
        // Download indicator just stays in its no-prose state.
      }
    })();
    return () => {
      ignore = true;
    };
  }, [params.id, narrativeRefresh]);

  // Non-admin auto-generate. Same flow as the soil report page: every
  // client-facing programme view auto-fires Opus on first visit when
  // the artifact is still in draft and no narrative exists yet. The
  // Download CTA below lights up as soon as the prose lands. Admins
  // keep the manual Generate / Regenerate panel for debugging.
  useEffect(() => {
    if (loading || isAdmin || autoGenAttempted) return;
    if (!data) return;
    if (hasOpusProse) return; // already have one
    if (data.state !== "draft") return; // won't accept a generate
    setAutoGenAttempted(true);
    (async () => {
      setAutoGenerating(true);
      try {
        const res = await generateProgrammeNarrative(params.id);
        // Apply hasOpusProse SYNCHRONOUSLY from the generate response.
        // Previously we only bumped narrativeRefresh and let the async
        // narrative-fetch effect update hasOpusProse — that left a
        // brief window where autoGenerating=false AND hasOpusProse=false,
        // which the DownloadHero rendered as the "engine baseline"
        // state. The flicker was the hero card swapping between
        // "Generating…" → "engine baseline" → "Programme ready" in
        // ~50-200 ms. Setting hasOpusProse directly from the response
        // closes that window.
        const present = !!(
          res.narrative_overrides &&
          Object.keys(res.narrative_overrides).length > 0
        );
        setHasOpusProse(present);
        setNarrativeLocked(!!res.narrative_locked_at);
        // Still bump refresh so other effects (e.g. NarrativePanel for
        // admins) re-fetch the persisted state.
        setNarrativeRefresh((n) => n + 1);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        toast.error(`AI narrative failed: ${msg}`);
      } finally {
        setAutoGenerating(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, isAdmin, autoGenAttempted, data, hasOpusProse, params.id]);

  const onTransition = async (newState: ProgrammeState, notes?: string) => {
    setTransitioning(true);
    try {
      const res = await transitionProgrammeState(params.id, newState, notes);
      setData(res);
      toast.success(`Programme ${newState}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Transition failed: ${msg}`);
    } finally {
      setTransitioning(false);
    }
  };

  const onArchive = async () => {
    if (!confirm("Archive this programme?")) return;
    setTransitioning(true);
    try {
      await archiveProgramme(params.id);
      toast.success("Programme archived");
      router.push("/season-manager");
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Archive failed: ${msg}`);
    } finally {
      setTransitioning(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="mx-auto flex max-w-5xl items-center justify-center px-4 py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </AppShell>
    );
  }
  if (!data) {
    return (
      <AppShell>
        <div className="mx-auto max-w-5xl px-4 py-8">
          <Card>
            <CardContent className="p-6">
              Programme not found.
              <Button
                variant="link"
                onClick={() => router.push("/season-manager")}
              >
                Back to Season Manager
              </Button>
            </CardContent>
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        <div className="flex flex-wrap items-center justify-between gap-4 print:hidden">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/season-manager")}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Season Manager
          </Button>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="default"
              size="sm"
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              title={
                hasOpusProse
                  ? `Download the Sapling-branded styled PDF — includes Opus AI narrative${narrativeLocked ? " (locked)" : ""}`
                  : "Download the Sapling-branded styled PDF — engine baseline prose"
              }
            >
              {downloadingPdf ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Download PDF
              {hasOpusProse && (
                <span
                  className="ml-1 inline-flex items-center rounded bg-white/20 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide"
                  aria-label={narrativeLocked ? "AI narrative locked" : "AI narrative included"}
                >
                  AI
                </span>
              )}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              title="Print this view via the browser"
            >
              <Printer className="h-4 w-4" />
              Print this view
            </Button>
            <StateActions
              state={data.state as ProgrammeState}
              onTransition={onTransition}
              onArchive={onArchive}
              disabled={transitioning}
            />
          </div>
        </div>
        <ReviewPanel
          state={data.state as ProgrammeState}
          review={data.review ?? null}
          disabled={transitioning}
          onApprove={(notes) => onTransition(State.APPROVED, notes)}
        />
        {/* Prominent download CTA — visible to every user the moment
            the AI report is ready. Hidden on print. */}
        <ProgrammeDownloadHero
          generating={autoGenerating}
          hasOpusProse={hasOpusProse}
          downloadingPdf={downloadingPdf}
          onDownload={handleDownloadPdf}
        />
        {/* NarrativePanel is admin-only — non-admins get the Opus
            version automatically and never see the verdict / audit /
            regenerate controls. */}
        {isAdmin && (
          <NarrativePanel
            artifactId={params.id}
            state={data.state as ProgrammeState}
            onNarrativeChange={() => setNarrativeRefresh((n) => n + 1)}
          />
        )}
        <ArtifactView artifact={data.artifact} />
        <SeasonTracker artifactId={data.id} artifact={data.artifact} />
      </div>
    </AppShell>
  );
}

function ProgrammeDownloadHero({
  generating,
  hasOpusProse,
  downloadingPdf,
  onDownload,
}: {
  generating: boolean;
  hasOpusProse: boolean;
  downloadingPdf: boolean;
  onDownload: () => void;
}) {
  if (generating) {
    return (
      <Card className="border-l-4 border-l-[var(--sapling-orange)] bg-orange-50/40 print:hidden">
        <CardContent className="flex items-center gap-4 p-5">
          <Loader2 className="size-6 animate-spin text-[var(--sapling-orange)]" />
          <div className="flex-1">
            <div className="text-base font-semibold text-[var(--sapling-dark)]">
              Generating AI programme…
            </div>
            <div className="mt-0.5 text-sm text-muted-foreground">
              Opus is reading the artifact and writing the agronomist
              narrative. Usually 30-60 seconds.
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
  if (hasOpusProse) {
    return (
      <Card className="border-l-4 border-l-green-600 bg-green-50/40 print:hidden">
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5">
          <div className="flex items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-green-100">
              <FileCheck className="size-5 text-green-700" />
            </div>
            <div>
              <div className="text-base font-semibold text-[var(--sapling-dark)]">
                Programme ready
              </div>
              <div className="mt-0.5 text-sm text-muted-foreground">
                Fertilizer programme — Sapling-branded PDF, ready to download.
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
  return (
    <Card className="border-l-4 border-l-slate-300 bg-slate-50/60 print:hidden">
      <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5">
        <div>
          <div className="text-base font-semibold text-[var(--sapling-dark)]">
            Engine baseline ready
          </div>
          <div className="mt-0.5 text-sm text-muted-foreground">
            Programme without AI narrative — download as-is.
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


function ReviewPanel({
  state,
  review,
  disabled,
  onApprove,
}: {
  state: ProgrammeState;
  review: ReviewInfo | null;
  disabled: boolean;
  onApprove: (notes: string) => void;
}) {
  const [notes, setNotes] = useState("");

  // Approved / activated / etc. — show reviewer attribution. Prints too.
  const reviewedStates = new Set<ProgrammeState>([
    State.APPROVED, State.ACTIVATED, State.IN_PROGRESS,
    State.COMPLETED, State.ARCHIVED,
  ]);
  if (reviewedStates.has(state) && review?.reviewer_id) {
    const displayName = review.reviewer_name || review.reviewer_email || "agronomist";
    const reviewedDate = review.reviewed_at
      ? new Date(review.reviewed_at).toLocaleDateString(undefined, {
          year: "numeric", month: "short", day: "numeric",
        })
      : null;
    return (
      <Card className="border-l-4 border-l-green-600 bg-green-50/50 print:bg-transparent">
        <CardContent className="flex items-start gap-3 p-4">
          <ShieldCheck className="mt-0.5 size-5 shrink-0 text-green-700" />
          <div className="flex-1 text-sm">
            <div className="font-medium text-green-900">
              Reviewed & approved by {displayName}
              {reviewedDate && <> · {reviewedDate}</>}
            </div>
            {review.reviewer_notes && (
              <div className="mt-1 whitespace-pre-wrap text-green-900/80">
                {review.reviewer_notes}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Draft — show the approve panel. Hidden from print (draft should
  // never reach a farmer anyway).
  if (state === State.DRAFT) {
    return (
      <Card className="border-dashed print:hidden">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-start gap-2">
            <ShieldCheck className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
            <div>
              <Label className="text-sm font-medium">Agronomist review</Label>
              <p className="text-xs text-muted-foreground">
                Approve this programme to add your name + optional notes
                (e.g. "K reduced 15% — leaf norms already adequate").
                Approved programmes carry your attribution to the farmer.
              </p>
            </div>
          </div>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional notes — any adjustments, caveats, or follow-ups you want the farmer to see…"
            className="min-h-20 w-full rounded-md border bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--sapling-orange)]"
            rows={3}
          />
          <div className="flex justify-end">
            <Button
              size="sm"
              disabled={disabled}
              onClick={() => onApprove(notes.trim())}
              className="bg-green-600 text-white hover:bg-green-700"
            >
              <CheckCircle2 className="size-4" />
              Approve as reviewer
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
}

function StateActions({
  state,
  onTransition,
  onArchive,
  disabled,
}: {
  state: ProgrammeState;
  onTransition: (s: ProgrammeState) => void;
  onArchive: () => void;
  disabled: boolean;
}) {
  // Draft → approved runs through the ReviewPanel (captures reviewer
  // notes); every other transition stays as a lightweight StateActions
  // button. The `approved` entry is intentionally absent under draft.
  const allowed: Record<ProgrammeState, ProgrammeState[]> = {
    [State.DRAFT]: [],
    [State.APPROVED]: [State.ACTIVATED, State.DRAFT],
    [State.ACTIVATED]: [State.IN_PROGRESS],
    [State.IN_PROGRESS]: [State.COMPLETED],
    [State.COMPLETED]: [],
    [State.ARCHIVED]: [],
  };
  const nexts = allowed[state] || [];
  return (
    <div className="flex flex-wrap gap-2">
      {nexts.map((n) => (
        <Button
          key={n}
          size="sm"
          variant={n === State.ACTIVATED ? "default" : "secondary"}
          disabled={disabled}
          onClick={() => onTransition(n)}
        >
          <CheckCircle2 className="h-4 w-4" />
          {n === State.APPROVED
            ? "Approve"
            : n === State.ACTIVATED
              ? "Activate"
              : n === State.IN_PROGRESS
                ? "Mark in progress"
                : n === State.COMPLETED
                  ? "Mark completed"
                  : n === State.DRAFT
                    ? "Revert to draft"
                    : n}
        </Button>
      ))}
      {state !== State.ARCHIVED && (
        <Button
          size="sm"
          variant="ghost"
          disabled={disabled}
          onClick={onArchive}
        >
          <Archive className="h-4 w-4" />
          Archive
        </Button>
      )}
    </div>
  );
}
