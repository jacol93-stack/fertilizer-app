"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { Loader2, ArrowLeft, Sparkles, Info } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArtifactView } from "@/components/programme-artifact/ArtifactView";
import { getProgramme } from "@/lib/programmes-v2";
import type { BuildProgrammeResponse } from "@/lib/types/programme-artifact";

/**
 * Season Tracker — per-programme in-season view.
 *
 * Stub scope: shows the programme artifact (reuses ArtifactView from
 * /programme-builder) + placeholder for in-season event entry.
 *
 * Future iterations will add:
 *   * Leaf analysis entry → triggers re-plan orchestrator
 *   * Weather deviation log
 *   * Actual application tracking vs planned
 *   * Re-plan decision surface (spot-correct / bump remaining /
 *     full re-plan / advise-only)
 *   * Comparison view (baseline vs current vs applied)
 */
export default function SeasonTrackerDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<BuildProgrammeResponse | null>(null);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return (
      <AppShell>
        <div className="mx-auto max-w-5xl px-4 py-8 flex items-center justify-center">
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
            </CardContent>
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/season-tracker")}
        >
          <ArrowLeft className="h-4 w-4" />
          All active programmes
        </Button>

        {/* In-season event entry — stub for next iteration */}
        <Card className="border-dashed">
          <CardContent className="p-6 space-y-3">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <div className="flex-1 space-y-2">
                <h2 className="text-sm font-semibold">
                  In-season events
                </h2>
                <p className="text-sm text-muted-foreground">
                  Leaf analysis, weather events, and actual applications
                  entered here trigger the re-plan orchestrator. Events
                  feed into the decision flow:{" "}
                  <span className="italic">
                    advise only / spot-correct / bump remaining stages /
                    full re-plan remainder
                  </span>
                  .
                </p>
                <div className="flex gap-2 flex-wrap pt-2">
                  <Button disabled size="sm" variant="outline">
                    Log leaf analysis
                  </Button>
                  <Button disabled size="sm" variant="outline">
                    Log application
                  </Button>
                  <Button disabled size="sm" variant="outline">
                    Log weather deviation
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground italic flex items-center gap-1.5 pt-1">
                  <Info className="h-3 w-3" />
                  In-season event UI ships in the next iteration. For
                  now, this view shows the activated programme artifact
                  read-only.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <ArtifactView artifact={data.artifact} />
      </div>
    </AppShell>
  );
}
