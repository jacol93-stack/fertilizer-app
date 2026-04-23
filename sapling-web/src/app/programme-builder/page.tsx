"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Loader2, Plus, Leaf, ChevronRight } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { listProgrammes } from "@/lib/programmes-v2";
import type {
  ProgrammeListItem,
  ProgrammeState,
} from "@/lib/types/programme-artifact";

const STATE_LABEL: Record<string, string> = {
  draft: "Draft",
  approved: "Approved",
  activated: "Activated",
  in_progress: "In progress",
  completed: "Completed",
  archived: "Archived",
};

const STATE_CLASS: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  approved: "bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-100",
  activated: "bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-100",
  in_progress: "bg-orange-100 text-orange-900 dark:bg-orange-900/40 dark:text-orange-100",
  completed: "bg-purple-100 text-purple-900 dark:bg-purple-900/40 dark:text-purple-100",
  archived: "bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-400",
};

export default function ProgrammeBuilderListPage() {
  const router = useRouter();
  const [items, setItems] = useState<ProgrammeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [stateFilter, setStateFilter] = useState<ProgrammeState | "">("");

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        setLoading(true);
        const res = await listProgrammes(
          stateFilter ? { state: stateFilter } : undefined,
        );
        if (!ignore) setItems(res);
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
  }, [stateFilter]);

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
        <header className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Programme Builder
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Season programmes generated from soil analysis + crop + methods.
            </p>
          </div>
          <Button onClick={() => router.push("/programme-builder/new")}>
            <Plus className="h-4 w-4" />
            New programme
          </Button>
        </header>

        <StateFilterChips
          value={stateFilter}
          onChange={setStateFilter}
        />

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : items.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center space-y-3">
              <Leaf className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No programmes yet.
              </p>
              <Button onClick={() => router.push("/programme-builder/new")}>
                Build your first programme
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {items.map((it) => (
              <Card
                key={it.id}
                className="cursor-pointer hover:border-primary transition-colors"
                onClick={() => router.push(`/programme-builder/${it.id}`)}
              >
                <CardContent className="p-4 flex items-center gap-4">
                  <div className="flex-1 space-y-0.5">
                    <div className="flex items-baseline gap-2 flex-wrap">
                      <span className="font-medium">
                        {it.crop}
                      </span>
                      {it.farm_name && (
                        <span className="text-muted-foreground">
                          · {it.farm_name}
                        </span>
                      )}
                      {it.ref_number && (
                        <span className="text-xs text-muted-foreground font-mono">
                          · {it.ref_number}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground flex gap-3 flex-wrap">
                      <span>Planting {it.planting_date}</span>
                      <span>·</span>
                      <span>{it.blocks_count} block{it.blocks_count !== 1 ? "s" : ""}</span>
                      {it.foliar_events_count > 0 && (
                        <>
                          <span>·</span>
                          <span>
                            {it.foliar_events_count} foliar event
                            {it.foliar_events_count !== 1 ? "s" : ""}
                          </span>
                        </>
                      )}
                      {it.risk_flags_count > 0 && (
                        <>
                          <span>·</span>
                          <span className="text-orange-700 dark:text-orange-300">
                            {it.risk_flags_count} risk flag
                            {it.risk_flags_count !== 1 ? "s" : ""}
                          </span>
                        </>
                      )}
                      {it.confidence_level && (
                        <>
                          <span>·</span>
                          <span>Data: {it.confidence_level}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded text-xs font-medium uppercase tracking-wide ${
                      STATE_CLASS[it.state] || STATE_CLASS.draft
                    }`}
                  >
                    {STATE_LABEL[it.state] || it.state}
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

function StateFilterChips({
  value,
  onChange,
}: {
  value: ProgrammeState | "";
  onChange: (v: ProgrammeState | "") => void;
}) {
  const states: Array<{ value: ProgrammeState | ""; label: string }> = [
    { value: "", label: "All" },
    { value: "draft" as ProgrammeState, label: "Draft" },
    { value: "approved" as ProgrammeState, label: "Approved" },
    { value: "activated" as ProgrammeState, label: "Activated" },
    { value: "in_progress" as ProgrammeState, label: "In progress" },
    { value: "completed" as ProgrammeState, label: "Completed" },
    { value: "archived" as ProgrammeState, label: "Archived" },
  ];
  return (
    <div className="flex gap-2 flex-wrap">
      {states.map((s) => (
        <button
          key={s.value || "all"}
          onClick={() => onChange(s.value)}
          className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
            value === s.value
              ? "bg-foreground text-background"
              : "bg-muted text-muted-foreground hover:bg-muted/70"
          }`}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}
