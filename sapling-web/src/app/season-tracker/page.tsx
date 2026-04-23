"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Loader2,
  Leaf,
  ChevronRight,
  Calendar,
  CircleAlert,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { listProgrammes } from "@/lib/programmes-v2";
import type { ProgrammeListItem } from "@/lib/types/programme-artifact";

/**
 * Season Tracker — list of programmes currently in-season.
 *
 * Scope: shows activated / in_progress programmes (draft/approved are
 * still in Programme Builder). From here, user drills into a programme
 * to enter in-season events (leaf analysis, weather, applications) and
 * trigger re-plans.
 *
 * This is a stub — the in-season decision flow ships in a follow-up.
 */
export default function SeasonTrackerListPage() {
  const router = useRouter();
  const [items, setItems] = useState<ProgrammeListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        setLoading(true);
        // Fetch activated + in_progress in parallel (no filter = all states,
        // then filter client-side; keeps the shape simple for a stub)
        const all = await listProgrammes({ limit: 200 });
        if (ignore) return;
        const active = all.filter(
          (p) => p.state === "activated" || p.state === "in_progress",
        );
        setItems(active);
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
  }, []);

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight">
            Season Tracker
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Activated programmes in their crop season. Enter in-season events
            (leaf analysis, weather, applications) and trigger re-plans.
          </p>
        </header>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : items.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center space-y-3">
              <Leaf className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No activated programmes. Build one in Programme Builder and
                activate it to start tracking.
              </p>
              <button
                onClick={() => router.push("/programme-builder")}
                className="text-sm text-primary underline"
              >
                Go to Programme Builder
              </button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {items.map((it) => (
              <Card
                key={it.id}
                className="cursor-pointer hover:border-primary transition-colors"
                onClick={() => router.push(`/season-tracker/${it.id}`)}
              >
                <CardContent className="p-4 flex items-center gap-4">
                  <Calendar className="h-5 w-5 text-muted-foreground shrink-0" />
                  <div className="flex-1 space-y-0.5">
                    <div className="flex items-baseline gap-2 flex-wrap">
                      <span className="font-medium">{it.crop}</span>
                      {it.farm_name && (
                        <span className="text-muted-foreground">
                          · {it.farm_name}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground flex gap-3 flex-wrap">
                      <span>Planted {it.planting_date}</span>
                      {it.expected_harvest_date && (
                        <>
                          <span>·</span>
                          <span>
                            Expected harvest {it.expected_harvest_date}
                          </span>
                        </>
                      )}
                      {it.risk_flags_count > 0 && (
                        <>
                          <span>·</span>
                          <span className="text-orange-700 dark:text-orange-300 inline-flex items-center gap-1">
                            <CircleAlert className="h-3 w-3" />
                            {it.risk_flags_count} flag
                            {it.risk_flags_count !== 1 ? "s" : ""}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded text-xs font-medium uppercase tracking-wide ${
                      it.state === "in_progress"
                        ? "bg-orange-100 text-orange-900 dark:bg-orange-900/40 dark:text-orange-100"
                        : "bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-100"
                    }`}
                  >
                    {it.state === "in_progress" ? "In progress" : "Activated"}
                  </span>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
