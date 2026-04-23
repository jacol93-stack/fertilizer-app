"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { Loader2, ArrowLeft, CheckCircle2, Archive } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArtifactView } from "@/components/programme-artifact/ArtifactView";
import {
  archiveProgramme,
  getProgramme,
  transitionProgrammeState,
} from "@/lib/programmes-v2";
import type {
  BuildProgrammeResponse,
  ProgrammeState,
} from "@/lib/types/programme-artifact";
import { ProgrammeState as State } from "@/lib/types/programme-artifact";

export default function ProgrammeArtifactPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<BuildProgrammeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [transitioning, setTransitioning] = useState(false);

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

  const onTransition = async (newState: ProgrammeState) => {
    setTransitioning(true);
    try {
      const res = await transitionProgrammeState(params.id, newState);
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
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/season-manager")}
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Season Manager
          </Button>
          <StateActions
            state={data.state as ProgrammeState}
            onTransition={onTransition}
            onArchive={onArchive}
            disabled={transitioning}
          />
        </div>
        <ArtifactView artifact={data.artifact} />
      </div>
    </AppShell>
  );
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
  const allowed: Record<ProgrammeState, ProgrammeState[]> = {
    [State.DRAFT]: [State.APPROVED],
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
