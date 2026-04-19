"use client";

import { useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { ClientSelector } from "@/components/client-selector";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, ChevronLeft, PencilRuler } from "lucide-react";

export default function BlankProgrammeWrapper() {
  return (
    <Suspense>
      <BlankProgrammePage />
    </Suspense>
  );
}

function BlankProgrammePage() {
  const router = useRouter();
  const [clientId, setClientId] = useState("");
  const [farmId, setFarmId] = useState("");
  const [clientName, setClientName] = useState("");
  const [farmName, setFarmName] = useState("");
  const [programmeName, setProgrammeName] = useState("");
  const [season, setSeason] = useState(() => {
    const y = new Date().getFullYear();
    return `${y}/${y + 1}`;
  });
  const [blockName, setBlockName] = useState("Block 1");
  const [crop, setCrop] = useState("");
  const [areaHa, setAreaHa] = useState("");
  const [creating, setCreating] = useState(false);

  const canCreate = Boolean(programmeName && crop);

  const create = async () => {
    setCreating(true);
    try {
      const programme = await api.post<{ id: string }>("/api/programmes", {
        client_id: clientId || null,
        farm_id: farmId || null,
        name: programmeName,
        season,
        status: "draft",
        blocks: [
          {
            name: blockName || "Block 1",
            area_ha: areaHa ? parseFloat(areaHa) : null,
            crop,
          },
        ],
      });
      toast.success("Draft programme created — fill in the plan manually");
      router.push(`/season-manager/${programme.id}?tab=edit`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to create");
      setCreating(false);
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-3xl px-4 py-8">
        <Button variant="ghost" size="sm" onClick={() => router.push("/season-manager")} className="mb-3">
          <ChevronLeft className="size-4" />
          Back to Season Manager
        </Button>
        <div className="mb-6 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
            <PencilRuler className="size-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">Start Blank Programme</h1>
            <p className="text-sm text-[var(--sapling-medium-grey)]">
              Build the plan entirely by hand — no auto-generation. Soil / leaf data (if linked to the block) will still drive validation feedback.
            </p>
          </div>
        </div>

        <Card>
          <CardContent className="space-y-5 py-6">
            <ClientSelector
              onSelect={(sel) => {
                setClientName(sel.client_name);
                setFarmName(sel.farm_name);
                setClientId(sel.client_id || "");
                setFarmId(sel.farm_id || "");
                if (!programmeName && sel.client_name) {
                  const y = new Date().getFullYear();
                  setProgrammeName(`${sel.client_name} ${sel.farm_name ? `- ${sel.farm_name} ` : ""}${y}/${y + 1}`);
                }
              }}
              initialClient={clientName}
              initialFarm={farmName}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Programme Name *</Label>
                <Input
                  value={programmeName}
                  onChange={(e) => setProgrammeName(e.target.value)}
                  placeholder="e.g. Farm ABC 2026/2027"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Season</Label>
                <Input value={season} onChange={(e) => setSeason(e.target.value)} />
              </div>
            </div>

            <div className="rounded-lg border bg-muted/20 p-4">
              <p className="mb-3 text-sm font-medium">First block</p>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="space-y-1.5">
                  <Label>Block name</Label>
                  <Input value={blockName} onChange={(e) => setBlockName(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label>Crop *</Label>
                  <Input
                    value={crop}
                    onChange={(e) => setCrop(e.target.value)}
                    placeholder="e.g. Macadamia"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Area (ha)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={areaHa}
                    onChange={(e) => setAreaHa(e.target.value)}
                  />
                </div>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                You can add more blocks from the programme detail page after creating.
              </p>
            </div>

            <div className="flex justify-end">
              <Button
                onClick={create}
                disabled={!canCreate || creating}
                className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {creating ? <Loader2 className="size-4 animate-spin" /> : <PencilRuler className="size-4" />}
                Create and start editing
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
