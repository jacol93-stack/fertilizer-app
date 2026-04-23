"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Loader2, Plus, Trash2, Sprout, Beaker, Tractor, Info } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { ClientSelector } from "@/components/client-selector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { buildProgramme } from "@/lib/programmes-v2";
import type {
  BlockRequest,
  BuildProgrammeRequest,
  MethodAvailability,
  PreSeasonInput,
} from "@/lib/types/programme-artifact";

// ------------------------------------------------------------
// Form state + validation
// ------------------------------------------------------------

interface FormState {
  clientId: string;
  clientName: string;
  farmId: string;
  farmName: string;
  preparedFor: string;
  crop: string;
  plantingDate: string;
  expectedHarvestDate: string;
  refNumber: string;
  stageCount: number;
  methods: MethodAvailability;
  blocks: BlockFormState[];
  highAlSoil: boolean | null;
  wetSummerBetweenApplyAndPlant: boolean;
  hasGypsumInPlan: boolean;
  hasIrrigationWaterTest: boolean;
  hasRecentLeafAnalysis: boolean;
  plannedNFertilizers: string;
  subtractHarvestedRemoval: boolean;
}

interface BlockFormState {
  blockId: string;
  blockName: string;
  blockAreaHa: string;
  yieldTargetPerHa: string;
  labName: string;
  labMethod: string;
  sampleDate: string;
  sampleId: string;
  // Soil parameters as key/value pairs for flexible entry
  soilParameters: Array<{ key: string; value: string }>;
  preSeasonInputs: PreSeasonFormState[];
}

interface PreSeasonFormState {
  product: string;
  rate: string;
  appliedDate: string;
}

const DEFAULT_SOIL_KEYS = [
  "CEC", "pH (H2O)", "P (Bray-1)", "K", "Ca", "Mg", "Al",
  "Na", "S", "B", "Zn", "Mn", "Fe", "Cu",
];

function emptyBlock(index: number): BlockFormState {
  return {
    blockId: `block_${index + 1}`,
    blockName: `Block ${index + 1}`,
    blockAreaHa: "",
    yieldTargetPerHa: "",
    labName: "",
    labMethod: "",
    sampleDate: "",
    sampleId: "",
    soilParameters: DEFAULT_SOIL_KEYS.map((k) => ({ key: k, value: "" })),
    preSeasonInputs: [],
  };
}

function emptyMethods(): MethodAvailability {
  return {
    has_drip: false,
    has_pivot: false,
    has_sprinkler: false,
    has_foliar_sprayer: true,
    has_granular_spreader: true,
    has_fertigation_injectors: false,
    has_seed_treatment: true,
  };
}

function initialState(): FormState {
  return {
    clientId: "",
    clientName: "",
    farmId: "",
    farmName: "",
    preparedFor: "",
    crop: "",
    plantingDate: "",
    expectedHarvestDate: "",
    refNumber: "",
    stageCount: 5,
    methods: emptyMethods(),
    blocks: [emptyBlock(0)],
    highAlSoil: null,
    wetSummerBetweenApplyAndPlant: false,
    hasGypsumInPlan: false,
    hasIrrigationWaterTest: false,
    hasRecentLeafAnalysis: false,
    plannedNFertilizers: "",
    subtractHarvestedRemoval: false,
  };
}

// ------------------------------------------------------------
// Page
// ------------------------------------------------------------

export default function ProgrammeBuilderNewPage() {
  const router = useRouter();
  const [state, setState] = useState<FormState>(initialState);
  const [generating, setGenerating] = useState(false);

  const updateMethod = <K extends keyof MethodAvailability>(
    key: K,
    value: MethodAvailability[K],
  ) => {
    setState((s) => ({ ...s, methods: { ...s.methods, [key]: value } }));
  };

  const addBlock = () => {
    setState((s) => ({ ...s, blocks: [...s.blocks, emptyBlock(s.blocks.length)] }));
  };

  const removeBlock = (idx: number) => {
    setState((s) => ({ ...s, blocks: s.blocks.filter((_, i) => i !== idx) }));
  };

  const updateBlock = <K extends keyof BlockFormState>(
    idx: number,
    key: K,
    value: BlockFormState[K],
  ) => {
    setState((s) => ({
      ...s,
      blocks: s.blocks.map((b, i) => (i === idx ? { ...b, [key]: value } : b)),
    }));
  };

  const updateSoilParam = (blockIdx: number, paramIdx: number, value: string) => {
    setState((s) => ({
      ...s,
      blocks: s.blocks.map((b, i) =>
        i !== blockIdx
          ? b
          : {
              ...b,
              soilParameters: b.soilParameters.map((p, j) =>
                j === paramIdx ? { ...p, value } : p,
              ),
            },
      ),
    }));
  };

  const addPreSeasonInput = (blockIdx: number) => {
    setState((s) => ({
      ...s,
      blocks: s.blocks.map((b, i) =>
        i !== blockIdx
          ? b
          : {
              ...b,
              preSeasonInputs: [
                ...b.preSeasonInputs,
                { product: "", rate: "", appliedDate: "" },
              ],
            },
      ),
    }));
  };

  const removePreSeasonInput = (blockIdx: number, psIdx: number) => {
    setState((s) => ({
      ...s,
      blocks: s.blocks.map((b, i) =>
        i !== blockIdx
          ? b
          : {
              ...b,
              preSeasonInputs: b.preSeasonInputs.filter((_, j) => j !== psIdx),
            },
      ),
    }));
  };

  const updatePreSeasonInput = (
    blockIdx: number,
    psIdx: number,
    key: keyof PreSeasonFormState,
    value: string,
  ) => {
    setState((s) => ({
      ...s,
      blocks: s.blocks.map((b, i) =>
        i !== blockIdx
          ? b
          : {
              ...b,
              preSeasonInputs: b.preSeasonInputs.map((p, j) =>
                j === psIdx ? { ...p, [key]: value } : p,
              ),
            },
      ),
    }));
  };

  const validate = (): string | null => {
    if (!state.clientName) return "Client is required";
    if (!state.farmName) return "Farm is required";
    if (!state.crop) return "Crop is required";
    if (!state.plantingDate) return "Planting date is required";
    if (!state.preparedFor) return "Prepared for is required";
    if (state.blocks.length === 0) return "At least one block is required";
    for (const [i, b] of state.blocks.entries()) {
      if (!b.blockName) return `Block ${i + 1}: name is required`;
      const area = parseFloat(b.blockAreaHa);
      if (!area || area <= 0)
        return `Block ${i + 1}: area (ha) must be > 0`;
      const yld = parseFloat(b.yieldTargetPerHa);
      if (!yld || yld <= 0)
        return `Block ${i + 1}: yield target must be > 0`;
    }
    return null;
  };

  const onGenerate = async () => {
    const err = validate();
    if (err) {
      toast.error(err);
      return;
    }
    setGenerating(true);
    try {
      const blocks: BlockRequest[] = state.blocks.map((b) => {
        const soil: Record<string, number> = {};
        for (const { key, value } of b.soilParameters) {
          if (key && value.trim() !== "") {
            const n = parseFloat(value);
            if (!Number.isNaN(n)) soil[key] = n;
          }
        }
        const preSeason: PreSeasonInput[] = b.preSeasonInputs
          .filter((p) => p.product && p.rate)
          .map((p) => ({
            product: p.product,
            rate: p.rate,
            contribution_per_ha: "",
            status_at_planting: "",
            applied_date: p.appliedDate || null,
            effective_n_kg_per_ha: 0,
            effective_p2o5_kg_per_ha: 0,
            effective_k2o_kg_per_ha: 0,
            effective_ca_kg_per_ha: 0,
            effective_mg_kg_per_ha: 0,
            effective_s_kg_per_ha: 0,
          }));
        return {
          block_id: b.blockId,
          block_name: b.blockName,
          block_area_ha: parseFloat(b.blockAreaHa),
          yield_target_per_ha: parseFloat(b.yieldTargetPerHa),
          soil_parameters: soil,
          lab_name: b.labName || null,
          lab_method: b.labMethod || null,
          sample_date: b.sampleDate || null,
          sample_id: b.sampleId || null,
          pre_season_inputs: preSeason,
        };
      });

      const plannedN = state.plannedNFertilizers
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);

      const req: BuildProgrammeRequest = {
        client_name: state.clientName,
        farm_name: state.farmName,
        prepared_for: state.preparedFor,
        crop: state.crop,
        planting_date: state.plantingDate,
        expected_harvest_date: state.expectedHarvestDate || null,
        ref_number: state.refNumber || null,
        stage_count: state.stageCount,
        blocks,
        method_availability: state.methods,
        high_al_soil: state.highAlSoil,
        wet_summer_between_apply_and_plant: state.wetSummerBetweenApplyAndPlant,
        has_gypsum_in_plan: state.hasGypsumInPlan,
        has_irrigation_water_test: state.hasIrrigationWaterTest,
        has_recent_leaf_analysis: state.hasRecentLeafAnalysis,
        planned_n_fertilizers: plannedN.length ? plannedN : null,
        subtract_harvested_removal: state.subtractHarvestedRemoval,
        client_id: state.clientId || null,
      };

      const res = await buildProgramme(req);
      toast.success("Programme generated");
      router.push(`/programme-builder/${res.id}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(`Build failed: ${msg}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl px-4 py-8 space-y-6">
        <header className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Programme Builder
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Generate a season programme from soil analysis + crop + methods
              available. All numbers carry source + tier provenance.
            </p>
          </div>
          <Button onClick={onGenerate} disabled={generating} size="lg">
            {generating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              "Generate Programme"
            )}
          </Button>
        </header>

        {/* Section: Client + Farm + Crop */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <SectionHeader icon={<Sprout className="h-4 w-4" />} title="Client, farm, crop" />
            <ClientSelector
              onSelect={(sel) =>
                setState((s) => ({
                  ...s,
                  clientId: sel.client_id || "",
                  clientName: sel.client_name,
                  farmId: sel.farm_id || "",
                  farmName: sel.farm_name,
                }))
              }
              showField={false}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <LabeledInput
                label="Prepared for"
                value={state.preparedFor}
                onChange={(v) => setState((s) => ({ ...s, preparedFor: v }))}
                placeholder="e.g. Wieland Jordaan"
              />
              <LabeledInput
                label="Crop (canonical name)"
                value={state.crop}
                onChange={(v) => setState((s) => ({ ...s, crop: v }))}
                placeholder="e.g. Garlic, Maize (dryland), Wheat"
              />
              <LabeledInput
                label="Planting date"
                type="date"
                value={state.plantingDate}
                onChange={(v) => setState((s) => ({ ...s, plantingDate: v }))}
              />
              <LabeledInput
                label="Expected harvest date (optional)"
                type="date"
                value={state.expectedHarvestDate}
                onChange={(v) => setState((s) => ({ ...s, expectedHarvestDate: v }))}
              />
              <LabeledInput
                label="Reference number (optional)"
                value={state.refNumber}
                onChange={(v) => setState((s) => ({ ...s, refNumber: v }))}
                placeholder="e.g. WJ60421"
              />
              <LabeledInput
                label="Stage count"
                type="number"
                min={3}
                max={6}
                value={String(state.stageCount)}
                onChange={(v) =>
                  setState((s) => ({
                    ...s,
                    stageCount: Math.max(3, Math.min(6, parseInt(v) || 5)),
                  }))
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Section: Method availability */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <SectionHeader
              icon={<Tractor className="h-4 w-4" />}
              title="Method availability — what equipment is on the farm?"
            />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <CheckboxItem
                label="Drip"
                checked={state.methods.has_drip}
                onChange={(v) => updateMethod("has_drip", v)}
              />
              <CheckboxItem
                label="Pivot"
                checked={state.methods.has_pivot}
                onChange={(v) => updateMethod("has_pivot", v)}
              />
              <CheckboxItem
                label="Sprinkler"
                checked={state.methods.has_sprinkler}
                onChange={(v) => updateMethod("has_sprinkler", v)}
              />
              <CheckboxItem
                label="Foliar sprayer"
                checked={state.methods.has_foliar_sprayer}
                onChange={(v) => updateMethod("has_foliar_sprayer", v)}
              />
              <CheckboxItem
                label="Granular spreader"
                checked={state.methods.has_granular_spreader}
                onChange={(v) => updateMethod("has_granular_spreader", v)}
              />
              <CheckboxItem
                label="Fertigation injectors"
                checked={state.methods.has_fertigation_injectors}
                onChange={(v) => updateMethod("has_fertigation_injectors", v)}
              />
              <CheckboxItem
                label="Seed treatment"
                checked={state.methods.has_seed_treatment}
                onChange={(v) => updateMethod("has_seed_treatment", v)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Section: Blocks */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <SectionHeader
                icon={<Beaker className="h-4 w-4" />}
                title="Blocks"
              />
              <Button onClick={addBlock} variant="outline" size="sm">
                <Plus className="h-4 w-4" />
                Add block
              </Button>
            </div>
            <div className="space-y-6">
              {state.blocks.map((b, i) => (
                <BlockEditor
                  key={i}
                  block={b}
                  index={i}
                  canRemove={state.blocks.length > 1}
                  onRemove={() => removeBlock(i)}
                  onUpdate={(key, value) => updateBlock(i, key, value)}
                  onSoilParamChange={(pIdx, v) => updateSoilParam(i, pIdx, v)}
                  onAddPreSeason={() => addPreSeasonInput(i)}
                  onRemovePreSeason={(idx) => removePreSeasonInput(i, idx)}
                  onUpdatePreSeason={(idx, key, value) =>
                    updatePreSeasonInput(i, idx, key, value)
                  }
                />
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Section: Context flags */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <SectionHeader
              icon={<Info className="h-4 w-4" />}
              title="Context flags (optional)"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <CheckboxItem
                label="Wet summer between pre-season apply and planting"
                checked={state.wetSummerBetweenApplyAndPlant}
                onChange={(v) =>
                  setState((s) => ({ ...s, wetSummerBetweenApplyAndPlant: v }))
                }
              />
              <CheckboxItem
                label="Gypsum is in the plan"
                checked={state.hasGypsumInPlan}
                onChange={(v) => setState((s) => ({ ...s, hasGypsumInPlan: v }))}
              />
              <CheckboxItem
                label="Recent irrigation water test available"
                checked={state.hasIrrigationWaterTest}
                onChange={(v) =>
                  setState((s) => ({ ...s, hasIrrigationWaterTest: v }))
                }
              />
              <CheckboxItem
                label="Recent leaf analysis available"
                checked={state.hasRecentLeafAnalysis}
                onChange={(v) =>
                  setState((s) => ({ ...s, hasRecentLeafAnalysis: v }))
                }
              />
              <CheckboxItem
                label="Subtract harvested removal from targets"
                checked={state.subtractHarvestedRemoval}
                onChange={(v) =>
                  setState((s) => ({ ...s, subtractHarvestedRemoval: v }))
                }
              />
            </div>
            <LabeledInput
              label="Planned N fertilizers (comma-separated, e.g. 'calcium_ammonium_nitrate, urea')"
              value={state.plannedNFertilizers}
              onChange={(v) =>
                setState((s) => ({ ...s, plannedNFertilizers: v }))
              }
            />
          </CardContent>
        </Card>

        <div className="flex justify-end pt-2">
          <Button onClick={onGenerate} disabled={generating} size="lg">
            {generating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              "Generate Programme"
            )}
          </Button>
        </div>
      </div>
    </AppShell>
  );
}

// ------------------------------------------------------------
// Block editor subcomponent
// ------------------------------------------------------------

interface BlockEditorProps {
  block: BlockFormState;
  index: number;
  canRemove: boolean;
  onRemove: () => void;
  onUpdate: <K extends keyof BlockFormState>(key: K, value: BlockFormState[K]) => void;
  onSoilParamChange: (paramIdx: number, value: string) => void;
  onAddPreSeason: () => void;
  onRemovePreSeason: (idx: number) => void;
  onUpdatePreSeason: (idx: number, key: keyof PreSeasonFormState, value: string) => void;
}

function BlockEditor({
  block,
  index,
  canRemove,
  onRemove,
  onUpdate,
  onSoilParamChange,
  onAddPreSeason,
  onRemovePreSeason,
  onUpdatePreSeason,
}: BlockEditorProps) {
  return (
    <div className="border border-border rounded-md p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Block {index + 1}</h3>
        {canRemove && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRemove}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
            Remove
          </Button>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <LabeledInput
          label="Block name"
          value={block.blockName}
          onChange={(v) => onUpdate("blockName", v)}
        />
        <LabeledInput
          label="Area (ha)"
          type="number"
          step="0.01"
          value={block.blockAreaHa}
          onChange={(v) => onUpdate("blockAreaHa", v)}
        />
        <LabeledInput
          label="Yield target (per ha)"
          type="number"
          step="0.1"
          value={block.yieldTargetPerHa}
          onChange={(v) => onUpdate("yieldTargetPerHa", v)}
        />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <LabeledInput
          label="Lab name"
          value={block.labName}
          onChange={(v) => onUpdate("labName", v)}
          placeholder="e.g. NViroTek"
        />
        <LabeledInput
          label="Lab method"
          value={block.labMethod}
          onChange={(v) => onUpdate("labMethod", v)}
          placeholder="Mehlich-3 / Bray-1"
        />
        <LabeledInput
          label="Sample date"
          type="date"
          value={block.sampleDate}
          onChange={(v) => onUpdate("sampleDate", v)}
        />
        <LabeledInput
          label="Sample ID"
          value={block.sampleId}
          onChange={(v) => onUpdate("sampleId", v)}
        />
      </div>

      <div>
        <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-2">
          Soil parameters
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {block.soilParameters.map((p, pIdx) => (
            <div key={p.key} className="space-y-1">
              <Label className="text-xs">{p.key}</Label>
              <Input
                type="number"
                step="0.01"
                value={p.value}
                onChange={(e) => onSoilParamChange(pIdx, e.target.value)}
                placeholder="—"
                className="h-8 text-sm"
              />
            </div>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Pre-season inputs (already applied, optional)
          </h4>
          <Button variant="ghost" size="sm" onClick={onAddPreSeason}>
            <Plus className="h-4 w-4" />
            Add input
          </Button>
        </div>
        {block.preSeasonInputs.length === 0 ? (
          <p className="text-xs text-muted-foreground italic">
            None — add if lime / gypsum / manure was applied before the programme
            starts. Engine will compute residual contribution at planting.
          </p>
        ) : (
          <div className="space-y-2">
            {block.preSeasonInputs.map((ps, psIdx) => (
              <div
                key={psIdx}
                className="grid grid-cols-1 md:grid-cols-4 gap-2 items-end"
              >
                <LabeledInput
                  label="Product"
                  value={ps.product}
                  onChange={(v) => onUpdatePreSeason(psIdx, "product", v)}
                  placeholder="e.g. Calcitic Lime"
                />
                <LabeledInput
                  label="Rate (e.g. 1500 kg/ha)"
                  value={ps.rate}
                  onChange={(v) => onUpdatePreSeason(psIdx, "rate", v)}
                />
                <LabeledInput
                  label="Applied date"
                  type="date"
                  value={ps.appliedDate}
                  onChange={(v) => onUpdatePreSeason(psIdx, "appliedDate", v)}
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemovePreSeason(psIdx)}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ------------------------------------------------------------
// Small primitives
// ------------------------------------------------------------

function SectionHeader({
  icon,
  title,
}: {
  icon: React.ReactNode;
  title: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-muted-foreground">{icon}</span>
      <h2 className="text-sm font-semibold">{title}</h2>
    </div>
  );
}

interface LabeledInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  min?: number;
  max?: number;
  step?: string;
}

function LabeledInput({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  min,
  max,
  step,
}: LabeledInputProps) {
  return (
    <div className="space-y-1">
      <Label className="text-xs">{label}</Label>
      <Input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
      />
    </div>
  );
}

function CheckboxItem({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2 cursor-pointer select-none text-sm">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="rounded border-input h-4 w-4 text-primary focus:ring-primary"
      />
      <span>{label}</span>
    </label>
  );
}
