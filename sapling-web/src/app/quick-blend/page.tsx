"use client";

import { useCallback, useEffect, useRef, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useSessionState, clearSessionGroup } from "@/lib/use-session-state";
import { useAuth } from "@/lib/auth-context";
import { useEffectiveAdmin } from "@/lib/use-effective-role";
import { api, API_URL } from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { ClientSelector } from "@/components/client-selector";
import { QuoteRequestDialog } from "@/components/quote-request-dialog";
import { CreateQuoteDialog } from "@/components/create-quote-dialog";
import { NutrientPriorityPanel } from "@/components/nutrient-priority-panel";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import {
  FlaskConical,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Download,
  Save,
  Loader2,
  Check,
  RotateCcw,
  Send,
  Droplets,
  Leaf,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

interface Material {
  id: number;
  material: string;
  type: string | null;
  cost_per_ton: number;
}

interface RecipeRow {
  material: string;
  type: string | null;
  kg: number;
  pct: number;
  cost: number;
}

interface NutrientRow {
  nutrient: string;
  target: number;
  actual: number;
  diff: number;
  kg_per_ton: number;
}

interface PricingComparable {
  blend_name: string;
  sa_notation?: string;
  selling_price?: number;
  price?: number;
  client?: string;
  date?: string;
  status?: string;
  quote_number?: string;
  source?: string;
  [key: string]: unknown;
}

interface PricingSuggestion {
  low: number;
  mid: number;
  high: number;
  method: string;
  comparables?: PricingComparable[];
  quote_comparables?: PricingComparable[];
}

interface OptimizeResult {
  success: boolean;
  exact: boolean;
  scale: number;
  recipe: RecipeRow[];
  nutrients: NutrientRow[];
  cost_per_ton: number;
  sa_notation: string;
  international_notation: string;
  pricing: PricingSuggestion | null;
  batch_size: number;
  min_compost_pct: number;
  missed_targets?: Array<{
    nutrient: string;
    target: number;
    actual: number;
    shortfall: number;
    suggested_materials: string[];
  }>;
  priority_result?: Record<string, unknown> | null;
  contact_sapling?: boolean;
}

interface Client {
  id: string;
  name: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

// Fallback safe limits — overridden by DB values when loaded
const FALLBACK_LIQUID_LIMITS: Record<string, number> = {
  N: 20, P: 15, K: 20, Ca: 15, Mg: 10, S: 15,
  Fe: 2, B: 0.5, Mn: 3, Zn: 3, Mo: 0.3, Cu: 1,
};

const PRIMARY_NUTRIENTS = ["N", "P", "K"] as const;
const SECONDARY_NUTRIENTS = [
  "Ca",
  "Mg",
  "S",
  "Fe",
  "B",
  "Mn",
  "Zn",
  "Mo",
  "Cu",
] as const;

// ── Agent blend preferences → material exclusions ─────────────────────
const BLEND_PREFERENCES = [
  {
    id: "chloride_free",
    label: "Chloride-free",
    description: "For chloride-sensitive crops like avocado, litchi, macadamia",
    excludes: ["KCL (Potassium Chloride)"],
  },
  {
    id: "low_salt",
    label: "Low salt index",
    description: "Reduce salt damage risk on sensitive soils or young trees",
    excludes: ["KCL (Potassium Chloride)", "KNO3", "Potassium Nitrate"],
  },
];

function saRatioToPercent(
  n: number,
  p: number,
  k: number,
  totalPct: number
): { N: number; P: number; K: number } {
  const sum = n + p + k;
  if (sum === 0) return { N: 0, P: 0, K: 0 };
  return {
    N: (n / sum) * totalPct,
    P: (p / sum) * totalPct,
    K: (k / sum) * totalPct,
  };
}

// ── Component ──────────────────────────────────────────────────────────────

export default function BlendsPageWrapper() {
  return (
    <Suspense>
      <BlendsPage />
    </Suspense>
  );
}

function BlendsPage() {
  const { isAdmin: _isAdmin, isLoading: authLoading, profile } = useAuth();
  const isAdmin = useEffectiveAdmin();
  const searchParams = useSearchParams();
  const SESSION_KEY = "blends";

  // ── Blend type toggle ────────────────────────────────────────
  const [blendType, setBlendType] = useSessionState<"dry" | "liquid" | "foliar">(SESSION_KEY, "blendType", "dry");

  // ── Liquid mode state ────────────────────────────────────────
  const [liquidMaterials, setLiquidMaterials] = useState<Material[]>([]);
  const [selectedLiquidMaterials, setSelectedLiquidMaterials] = useState<Set<string>>(new Set());
  const [tankVolume, setTankVolume] = useSessionState(SESSION_KEY, "tankVolume", "1000");
  const [liquidTargets, setLiquidTargets] = useSessionState<Record<string, string>>(SESSION_KEY, "liquidTargets", {});
  const [liquidResult, setLiquidResult] = useState<Record<string, unknown> | null>(null);
  const [liquidOptimizing, setLiquidOptimizing] = useState(false);
  const [showLiquidPriorityPanel, setShowLiquidPriorityPanel] = useState(false);
  const [liquidContactSapling, setLiquidContactSapling] = useState(false);

  // ── Application rate inputs ──────────────────────────────────
  const [appMethod, setAppMethod] = useSessionState<"fertigation" | "foliar">(SESSION_KEY, "appMethod", "fertigation");
  const [appTargetNutrient, setAppTargetNutrient] = useSessionState(SESSION_KEY, "appTargetNutrient", "N");
  const [appTargetKgHa, setAppTargetKgHa] = useSessionState(SESSION_KEY, "appTargetKgHa", "");
  const [appDilution, setAppDilution] = useSessionState(SESSION_KEY, "appDilution", "");
  const [appSprayVolume, setAppSprayVolume] = useSessionState(SESSION_KEY, "appSprayVolume", "");
  const [appPlantsHa, setAppPlantsHa] = useSessionState(SESSION_KEY, "appPlantsHa", "");

  // ── Nutrient safety limits (loaded from DB) ──────────────────
  const [liquidSafeLimits, setLiquidSafeLimits] = useState<Record<string, number>>(FALLBACK_LIQUID_LIMITS);

  // ── Foliar mode state ────────────────────────────────────────
  const [foliarNutrients, setFoliarNutrients] = useSessionState<string[]>(SESSION_KEY, "foliarNutrients", []);
  const [foliarProducts, setFoliarProducts] = useState<Array<Record<string, unknown>>>([]);
  const [foliarLoading, setFoliarLoading] = useState(false);
  const [selectedFoliar, setSelectedFoliar] = useState<Record<string, unknown> | null>(null);
  const [foliarHectares, setFoliarHectares] = useState("10");
  const foliarDetailRef = useRef<HTMLDivElement>(null);

  // ── Input state ────────────────────────────────────────────
  const [mode, setMode] = useSessionState<"international" | "sa">(SESSION_KEY, "mode", "international");
  const [intTargets, setIntTargets] = useSessionState(SESSION_KEY, "intTargets", { N: "", P: "", K: "" });
  const [saRatio, setSaRatio] = useSessionState(SESSION_KEY, "saRatio", { N: "", P: "", K: "" });
  const [saTotalPct, setSaTotalPct] = useSessionState(SESSION_KEY, "saTotalPct", "");
  const [secondaryTargets, setSecondaryTargets] = useSessionState<
    Record<string, string>
  >(SESSION_KEY, "secondaryTargets", {});
  const [showSecondary, setShowSecondary] = useState(false);

  const [batchSize, setBatchSize] = useSessionState(SESSION_KEY, "batchSize", "1000");
  const [minCompost, setMinCompost] = useSessionState(SESSION_KEY, "minCompost", 50);
  const [blendMode, setBlendMode] = useSessionState<"compost" | "chemical">(SESSION_KEY, "blendMode", "compost");
  // Force compost mode for agents
  if (!isAdmin && blendMode === "chemical") setBlendMode("compost");
  const [agentMinCompost, setAgentMinCompost] = useState(50);

  const [materials, setMaterials] = useState<Material[]>([]);
  const [savedMaterialSelection, setSavedMaterialSelection] = useSessionState<string[]>(SESSION_KEY, "selectedMaterials", []);
  const [selectedMaterials, setSelectedMaterialsRaw] = useState<Set<string>>(new Set(savedMaterialSelection));
  // Wrap setter to also persist to session
  const setSelectedMaterials = (val: Set<string> | ((prev: Set<string>) => Set<string>)) => {
    setSelectedMaterialsRaw((prev) => {
      const next = typeof val === "function" ? val(prev) : val;
      setSavedMaterialSelection([...next]);
      return next;
    });
  };
  const [materialsLoading, setMaterialsLoading] = useState(true);

  const [clients, setClients] = useState<Client[]>([]);
  const [clientName, setClientName] = useSessionState(SESSION_KEY, "clientName", "");
  const [farmName, setFarmName] = useSessionState(SESSION_KEY, "farmName", "");
  const [clientId, setClientId] = useSessionState<string | undefined>(SESSION_KEY, "clientId", undefined);
  const [farmId, setFarmId] = useSessionState<string | undefined>(SESSION_KEY, "farmId", undefined);
  const [fieldId, setFieldId] = useSessionState<string | undefined>(SESSION_KEY, "fieldId", undefined);
  const [fieldName, setFieldName] = useSessionState(SESSION_KEY, "fieldName", "");
  const [customBlendName, setCustomBlendName] = useSessionState(SESSION_KEY, "customBlendName", "");
  const [sellingPrice, setSellingPrice] = useSessionState(SESSION_KEY, "sellingPrice", "");
  const [activePrefsArray, setActivePrefsArray] = useSessionState<string[]>(SESSION_KEY, "activePrefs", []);
  const activePrefs = new Set(activePrefsArray);
  const setActivePrefs = (val: Set<string> | ((prev: Set<string>) => Set<string>)) => {
    if (typeof val === "function") {
      setActivePrefsArray((prev) => [...val(new Set(prev))]);
    } else {
      setActivePrefsArray([...val]);
    }
  };

  // ── Result state ───────────────────────────────────────────
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [quoteDialogOpen, setQuoteDialogOpen] = useState(false);
  const [showPriorityPanel, setShowPriorityPanel] = useState(false);
  const [contactSapling, setContactSapling] = useState(false);
  const [blendAssistDialogOpen, setBlendAssistDialogOpen] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedBlendId, setSavedBlendId] = useState<string | null>(null);
  const [quoteSheetOpen, setQuoteSheetOpen] = useState(false);

  // ── Pre-fill from URL params (overrides session state) ──────
  useEffect(() => {
    const c = searchParams.get("client");
    const cId = searchParams.get("client_id");
    const f = searchParams.get("farm");
    const fId = searchParams.get("farm_id");
    const fl = searchParams.get("field");
    const flId = searchParams.get("field_id");
    if (cId) {
      // Clear all blend session state so we start completely fresh
      clearSessionGroup(SESSION_KEY);
      setBlendType("dry");
      if (c) { sessionStorage.setItem(`${SESSION_KEY}:clientName`, JSON.stringify(c)); setClientName(c); }
      sessionStorage.setItem(`${SESSION_KEY}:clientId`, JSON.stringify(cId)); setClientId(cId);
      if (f) { sessionStorage.setItem(`${SESSION_KEY}:farmName`, JSON.stringify(f)); setFarmName(f); }
      if (fId) { sessionStorage.setItem(`${SESSION_KEY}:farmId`, JSON.stringify(fId)); setFarmId(fId); }
      if (fl) { sessionStorage.setItem(`${SESSION_KEY}:fieldName`, JSON.stringify(fl)); setFieldName(fl); }
      if (flId) { sessionStorage.setItem(`${SESSION_KEY}:fieldId`, JSON.stringify(flId)); setFieldId(flId); }
    }
    // Switch blend type tab if specified in URL
    const bt = searchParams.get("blend_type");
    if (bt === "liquid" || bt === "foliar") {
      setBlendType(bt);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Load materials & defaults ──────────────────────────────
  useEffect(() => {
    if (authLoading) return;
    async function load() {
      try {
        const [mats, defaults, clientsList] = await Promise.all([
          api.get<Material[]>("/api/materials"),
          api.get<{ materials: string[]; agent_min_compost_pct: number }>("/api/materials/defaults"),
          api.getAll<Client>("/api/clients").catch(() => [] as Client[]),
        ]);
        setMaterials(mats.sort((a, b) => a.material.localeCompare(b.material)));
        // Only use defaults if no session-persisted selection with actual values
        const hasSaved = sessionStorage.getItem(`${SESSION_KEY}:selectedMaterials`);
        let savedArr: string[] = [];
        try { savedArr = hasSaved ? JSON.parse(hasSaved) : []; } catch { /* ignore */ }
        if (!savedArr || savedArr.length === 0) {
          setSelectedMaterials(new Set(defaults.materials));
        }
        setAgentMinCompost(defaults.agent_min_compost_pct ?? 50);
        if (!isAdmin && !sessionStorage.getItem(`${SESSION_KEY}:minCompost`)) {
          setMinCompost(defaults.agent_min_compost_pct ?? 50);
        }
        setClients(Array.isArray(clientsList) ? clientsList : []);
      } catch (err) {
        toast.error(
          "Failed to load materials: " +
            (err instanceof Error ? err.message : "Unknown error")
        );
      } finally {
        setMaterialsLoading(false);
      }
    }
    load();
  }, [authLoading]);

  // Load liquid materials and foliar products
  useEffect(() => {
    if (blendType === "liquid" && liquidMaterials.length === 0) {
      // Load nutrient limits from DB
      api.get<Record<string, { liquid_max: number | null }>>("/api/blends/nutrient-limits")
        .then((limits) => {
          const parsed: Record<string, number> = {};
          for (const [nut, val] of Object.entries(limits)) {
            // Normalize key: "ca" → "Ca", "fe" → "Fe", "n" → "N"
            const key = nut.length === 1 ? nut.toUpperCase() : nut.charAt(0).toUpperCase() + nut.slice(1).toLowerCase();
            if (val.liquid_max != null) parsed[key] = val.liquid_max;
          }
          if (Object.keys(parsed).length > 0) setLiquidSafeLimits(parsed);
        })
        .catch(() => {});

      Promise.all([
        api.get<Material[]>("/api/blends/liquid-materials"),
        api.get<{ liquid_materials: string[] }>("/api/materials/defaults"),
      ]).then(([data, defaults]) => {
        setLiquidMaterials(data.sort((a, b) => a.material.localeCompare(b.material)));
        const liquidDefaults = defaults.liquid_materials || [];
        if (!isAdmin && liquidDefaults.length > 0) {
          // Agents use admin-configured defaults
          setSelectedLiquidMaterials(new Set(liquidDefaults));
        } else {
          // Admin or no defaults configured — select all
          setSelectedLiquidMaterials(new Set(data.map((m) => m.material)));
        }
      }).catch(() => {});
    }
    if (blendType === "foliar" && foliarProducts.length === 0) {
      handleFoliarLookup([]);
    }
  }, [blendType]);

  // Liquid blend optimizer
  async function handleLiquidOptimize() {
    const targets: Record<string, number> = {};
    for (const [k, v] of Object.entries(liquidTargets)) {
      const n = parseFloat(v);
      if (n > 0) targets[k.toLowerCase()] = n;
    }
    if (Object.keys(targets).length === 0) {
      toast.error("Enter at least one nutrient target (g/L)");
      return;
    }
    setLiquidOptimizing(true);
    setLiquidResult(null);
    setSavedLiquidBlendId(null);
    setLiquidContactSapling(false);
    try {
      const res = await api.post<Record<string, unknown>>("/api/blends/optimize-liquid", {
        targets,
        selected_materials: [...selectedLiquidMaterials],
        tank_volume_l: parseFloat(tankVolume) || 1000,
      });
      setLiquidResult(res);
      if (!res.exact) {
        setShowLiquidPriorityPanel(true);
        toast.info("Exact blend not possible — set nutrient priorities to find the best match.");
      } else {
        setShowLiquidPriorityPanel(false);
        toast.success("Liquid blend optimized!");
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Optimization failed");
    } finally {
      setLiquidOptimizing(false);
    }
  }

  // ── Re-optimize liquid with priorities ─────────────────────
  async function handleLiquidPriorityOptimize(priorities: Record<string, "must_match" | "flexible">) {
    setLiquidOptimizing(true);
    try {
      const targets: Record<string, number> = {};
      for (const [k, v] of Object.entries(liquidTargets)) {
        const n = parseFloat(v);
        if (n > 0) targets[k.toLowerCase()] = n;
      }

      const res = await api.post<Record<string, unknown>>("/api/blends/optimize-liquid", {
        targets,
        selected_materials: [...selectedLiquidMaterials],
        tank_volume_l: parseFloat(tankVolume) || 1000,
        priorities,
      });
      setLiquidResult(res);

      if (res.contact_sapling) {
        setLiquidContactSapling(true);
        setShowLiquidPriorityPanel(false);
        toast.warning("Even with priorities, this blend can't be fully achieved.");
      } else {
        setLiquidContactSapling(false);
        const compromised = (res.priority_result as Record<string, unknown>)?.compromised;
        if (Array.isArray(compromised) && compromised.length > 0) {
          setShowLiquidPriorityPanel(true);
          toast.success(`Blend optimized! ${compromised.length} nutrient(s) adjusted — reshuffle priorities if needed.`);
        } else {
          setShowLiquidPriorityPanel(false);
          toast.success("Blend optimized with all priorities met!");
        }
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      toast.error("Re-optimization failed: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setLiquidOptimizing(false);
    }
  }

  // Foliar product lookup
  async function handleFoliarLookup(selected?: string[]) {
    const nuts = selected ?? foliarNutrients;
    setFoliarLoading(true);
    setFoliarProducts([]);
    try {
      const params = nuts.length > 0 ? `?nutrients=${nuts.join(",")}` : "";
      const res = await api.get<Array<Record<string, unknown>>>(`/api/blends/foliar-products${params}`);
      setFoliarProducts(res);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to load products");
    } finally {
      setFoliarLoading(false);
    }
  }

  // ── Save liquid blend ──────────────────────────────────────
  const [liquidSaving, setLiquidSaving] = useState(false);
  const [savedLiquidBlendId, setSavedLiquidBlendId] = useState<string | null>(null);

  async function handleLiquidSave() {
    if (!liquidResult) return;
    if (!isAdmin && (!clientId || !farmId)) {
      toast.error("Please select a client and farm before saving");
      return;
    }
    if (savedLiquidBlendId) {
      if (!confirm("This blend has already been saved. Save again as a new blend?")) {
        return;
      }
      setSavedLiquidBlendId(null);
    }
    setLiquidSaving(true);
    try {
      const liquidFormula = Object.entries(liquidTargets)
        .filter(([, v]) => parseFloat(v) > 0)
        .map(([k, v]) => `${k} ${v}g/L`)
        .join(", ") || "Liquid Blend";
      const blendName = customBlendName.trim()
        ? `${customBlendName.trim()} - ${liquidFormula}`
        : liquidFormula + (clientName ? ` - ${clientName}` : "");
      const saved = await api.post<{ id: string; blend_name: string }>(
        "/api/blends",
        {
          blend_name: blendName,
          blend_type: "liquid",
          client_id: clientId || null,
          farm_id: farmId || null,
          field_id: fieldId || null,
          client: clientName || null,
          farm: farmName || null,
          field: fieldName || null,
          batch_size: parseFloat(tankVolume) || 1000,
          targets: Object.fromEntries(
            Object.entries(liquidTargets)
              .filter(([, v]) => parseFloat(v) > 0)
              .map(([k, v]) => [k, parseFloat(v)])
          ),
          recipe: liquidResult.recipe as Array<Record<string, unknown>>,
          nutrients: liquidResult.nutrients as Array<Record<string, unknown>>,
          selected_materials: [...selectedLiquidMaterials],
          tank_volume_l: liquidResult.tank_volume_l as number,
          sg_estimate: liquidResult.sg_estimate as number,
          mixing_instructions: liquidResult.mixing_instructions as string[],
        }
      );
      setSavedLiquidBlendId(saved.id);
      toast.success(`Blend "${saved.blend_name}" saved successfully!`);
    } catch (err) {
      toast.error(
        "Failed to save blend: " +
          (err instanceof Error ? err.message : "Unknown error")
      );
    } finally {
      setLiquidSaving(false);
    }
  }

  // ── Download liquid PDF ───────────────────────────────────
  async function handleLiquidDownloadPdf() {
    if (!liquidResult) return;
    try {
      const headers = {
        Authorization: `Bearer ${(await (await import("@/lib/supabase")).createClient().auth.getSession()).data.session?.access_token}`,
        "Content-Type": "application/json",
      };
      const liquidFormula = Object.entries(liquidTargets)
        .filter(([, v]) => parseFloat(v) > 0)
        .map(([k, v]) => `${k} ${v}g/L`)
        .join(", ") || "Liquid Blend";
      const blendName = customBlendName.trim()
        ? `${customBlendName.trim()} - ${liquidFormula}`
        : liquidFormula + (clientName ? ` - ${clientName}` : "");
      const warnings = (liquidResult.compatibility_warnings as Array<Record<string, string>>)?.map(
        (w) => `${w.material_a} + ${w.material_b}: ${w.reason}`
      ) || [];
      const res = await fetch(
        `${API_URL}/api/reports/blend/liquid/pdf`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({
            blend_name: blendName,
            client: clientName,
            farm: farmName,
            tank_volume_l: liquidResult.tank_volume_l,
            total_dissolved_kg: liquidResult.total_dissolved_kg,
            sg_estimate: liquidResult.sg_estimate,
            exact: liquidResult.success,
            scale: liquidResult.scale ?? 1.0,
            recipe: liquidResult.recipe,
            nutrients: liquidResult.nutrients,
            mixing_instructions: liquidResult.mixing_instructions || [],
            compatibility_warnings: warnings,
          }),
        }
      );
      if (!res.ok) throw new Error(`PDF error ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `liquid_blend_${blendName}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(
        "Failed to download PDF: " +
          (err instanceof Error ? err.message : "Unknown error")
      );
    }
  }

  // Check for quote prefill data from admin quotes page
  const [quoteRef, setQuoteRef] = useState<{ id: string; number: string } | null>(null);
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("quote_prefill");
      if (raw) {
        sessionStorage.removeItem("quote_prefill");
        const data = JSON.parse(raw);
        // Prefill the form
        // Option 1: targets object (from nutrient_request: {N: 4, P: 3, K: 1, Ca: 4})
        if (data.targets && typeof data.targets === "object") {
          setMode("international");
          setIntTargets({
            N: String(data.targets.N || ""),
            P: String(data.targets.P || ""),
            K: String(data.targets.K || ""),
          });
          // Secondary nutrients
          const secondaries: Record<string, string> = {};
          for (const [k, v] of Object.entries(data.targets)) {
            if (!["N", "P", "K"].includes(k) && Number(v) > 0) {
              secondaries[k] = String(v);
            }
          }
          if (Object.keys(secondaries).length > 0) {
            setSecondaryTargets(secondaries);
            setShowSecondary(true);
          }
        }
        // Option 2: SA notation string
        else if (data.sa_notation) {
          const match = String(data.sa_notation).match(/(\d+):(\d+):(\d+)\s*\((\d+)\)/);
          if (match) {
            setMode("sa");
            setSaRatio({ N: match[1], P: match[2], K: match[3] });
            setSaTotalPct(match[4]);
          }
        }
        // Option 3: International notation string
        else if (data.international_notation) {
          const intMatch = String(data.international_notation).match(/N\s*([\d.]+)%\s*P\s*([\d.]+)%\s*K\s*([\d.]+)%/);
          if (intMatch) {
            setMode("international");
            setIntTargets({ N: intMatch[1], P: intMatch[2], K: intMatch[3] });
          }
        }
        if (data.batch_size) setBatchSize(String(data.batch_size));
        if (data.min_compost_pct != null) setMinCompost(Number(data.min_compost_pct));
        if (data.client_name) setClientName(data.client_name);
        if (data.farm_name) setFarmName(data.farm_name);
        if (data.quote_id) setQuoteRef({ id: data.quote_id, number: data.quote_number || "" });

        toast.info(`Loaded quote ${data.quote_number || ""} — run the optimizer then send the quote back`);
      }
    } catch {}
  }, []);

  // ── Build targets from inputs ──────────────────────────────
  const buildTargets = useCallback((): Record<string, number> => {
    const targets: Record<string, number> = {};

    if (mode === "international") {
      for (const key of PRIMARY_NUTRIENTS) {
        const v = parseFloat(intTargets[key]);
        if (v > 0) targets[key] = v;
      }
    } else {
      const n = parseInt(saRatio.N) || 0;
      const p = parseInt(saRatio.P) || 0;
      const k = parseInt(saRatio.K) || 0;
      const total = parseFloat(saTotalPct) || 0;
      const pcts = saRatioToPercent(n, p, k, total);
      if (pcts.N > 0) targets.N = pcts.N;
      if (pcts.P > 0) targets.P = pcts.P;
      if (pcts.K > 0) targets.K = pcts.K;
    }

    for (const key of SECONDARY_NUTRIENTS) {
      const v = parseFloat(secondaryTargets[key] || "");
      if (v > 0) targets[key] = v;
    }

    return targets;
  }, [mode, intTargets, saRatio, saTotalPct, secondaryTargets]);

  // ── Optimize ───────────────────────────────────────────────
  async function handleOptimize() {
    const targets = buildTargets();
    if (Object.keys(targets).length === 0) {
      toast.error("Please enter at least one nutrient target.");
      return;
    }
    if (selectedMaterials.size === 0) {
      toast.error("Please select at least one material.");
      return;
    }

    setOptimizing(true);
    setResult(null);
    setSavedBlendId(null);

    try {
      // Auto-include compost or filler based on mode
      // Apply agent blend preferences — exclude materials
      const prefExcludes = new Set<string>();
      for (const pref of BLEND_PREFERENCES) {
        if (activePrefs.has(pref.id)) {
          for (const mat of pref.excludes) prefExcludes.add(mat);
        }
      }
      const matList = Array.from(selectedMaterials)
        .filter((m) => m !== "Manure Compost" && m !== "Dolomitic Lime (Filler)" && !prefExcludes.has(m));
      if (blendMode === "compost") {
        matList.push("Manure Compost");
      }
      // Chemical mode: API auto-adds the filler

      const res = await api.post<OptimizeResult>("/api/blends/optimize", {
        targets,
        selected_materials: matList,
        batch_size: parseFloat(batchSize) || 1000,
        min_compost_pct: blendMode === "chemical" ? 0 : minCompost,
        blend_mode: blendMode,
      });
      setResult(res);
      setContactSapling(false);
      if (!res.exact) {
        setShowPriorityPanel(true);
        toast.info("Exact blend not possible — set nutrient priorities to find the best match.");
      } else {
        setShowPriorityPanel(false);
        toast.success("Blend optimized successfully!");
      }
      // Scroll to top so user sees results / priority panel
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      if (!isAdmin && (msg.includes("cannot be achieved") || msg.includes("priorities"))) {
        toast.info("This blend can't be achieved with the available materials. Contact Sapling Fertilizer for assistance.");
        setContactSapling(true);
        setShowPriorityPanel(false);
      } else {
        toast.error("Optimization failed: " + msg);
      }
    } finally {
      setOptimizing(false);
    }
  }

  // ── Re-optimize with priorities ────────────────────────────
  async function handlePriorityOptimize(priorities: Record<string, "must_match" | "flexible">) {
    setOptimizing(true);
    try {
      const targets = buildTargets();
      const matList = Array.from(selectedMaterials)
        .filter((m) => m !== "Manure Compost" && m !== "Dolomitic Lime (Filler)");
      if (blendMode === "compost") matList.push("Manure Compost");

      const res = await api.post<OptimizeResult>("/api/blends/optimize", {
        targets,
        selected_materials: matList,
        batch_size: parseFloat(batchSize) || 1000,
        min_compost_pct: blendMode === "chemical" ? 0 : minCompost,
        blend_mode: blendMode,
        priorities,
      });
      setResult(res);
      if (res.contact_sapling) {
        setContactSapling(true);
        setShowPriorityPanel(false);
        toast.warning("Even with priorities, this blend can't be fully achieved.");
      } else {
        setContactSapling(false);
        const compromised = (res.priority_result as Record<string, unknown>)?.compromised;
        if (Array.isArray(compromised) && compromised.length > 0) {
          // Still not perfect — keep priority panel open for another try
          setShowPriorityPanel(true);
          toast.success(`Blend optimized! ${compromised.length} nutrient(s) adjusted — reshuffle priorities if needed.`);
        } else {
          setShowPriorityPanel(false);
          toast.success("Blend optimized with all priorities met!");
        }
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      toast.error("Re-optimization failed: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setOptimizing(false);
    }
  }

  // ── Save blend ─────────────────────────────────────────────
  async function handleSave() {
    if (!result) return;
    if (!isAdmin && (!clientId || !farmId)) {
      toast.error("Please select a client and farm before saving");
      return;
    }
    // Prevent duplicate saves
    if (savedBlendId) {
      if (!confirm("This blend has already been saved. Save again as a new blend?")) {
        return;
      }
      setSavedBlendId(null);
    }
    setSaving(true);
    try {
      const formula = result.sa_notation;
      const blendName = customBlendName.trim()
        ? `${customBlendName.trim()} - ${formula}`
        : formula + (clientName ? ` - ${clientName}` : "");
      const saved = await api.post<{ id: string; blend_name: string }>(
        "/api/blends",
        {
          blend_name: blendName,
          client_id: clientId || null,
          farm_id: farmId || null,
          field_id: fieldId || null,
          client: clientName || null,
          farm: farmName || null,
          field: fieldName || null,
          batch_size: result.batch_size,
          min_compost_pct: result.min_compost_pct,
          cost_per_ton: result.cost_per_ton ?? 0,
          selling_price: parseFloat(sellingPrice) || 0,
          targets: buildTargets(),
          recipe: result.recipe,
          nutrients: result.nutrients,
          selected_materials: Array.from(selectedMaterials),
        }
      );
      setSavedBlendId(saved.id);
      toast.success(`Blend "${saved.blend_name}" saved successfully!`);
    } catch (err) {
      toast.error(
        "Failed to save blend: " +
          (err instanceof Error ? err.message : "Unknown error")
      );
    } finally {
      setSaving(false);
    }
  }

  // ── Download PDF ───────────────────────────────────────────
  async function handleDownloadPdf() {
    if (!result) return;
    try {
      const headers = {
        Authorization: `Bearer ${(await (await import("@/lib/supabase")).createClient().auth.getSession()).data.session?.access_token}`,
        "Content-Type": "application/json",
      };
      const pdfFormula = result.sa_notation;
      const blendName = customBlendName.trim()
        ? `${customBlendName.trim()} - ${pdfFormula}`
        : pdfFormula + (clientName ? ` - ${clientName}` : "");
      const res = await fetch(
        `${API_URL}/api/reports/blend/pdf`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({
            blend_name: blendName,
            client: clientName,
            farm: farmName,
            batch_size: result.batch_size ?? 1000,
            cost_per_ton: result.cost_per_ton ?? 0,
            selling_price: parseFloat(sellingPrice) || 0,
            sa_notation: result.sa_notation ?? "",
            exact: result.exact ?? true,
            scale: result.scale ?? 1.0,
            recipe: result.recipe ?? [],
            nutrients: result.nutrients ?? [],
            pricing: result.pricing ?? null,
          }),
        }
      );
      if (!res.ok) throw new Error(`PDF error ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `blend_${blendName}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(
        "Failed to download PDF: " +
          (err instanceof Error ? err.message : "Unknown error")
      );
    }
  }

  // ── Toggle material selection ──────────────────────────────
  function toggleMaterial(name: string) {
    setSelectedMaterials((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  // ── Computed NPK for display ───────────────────────────────
  const displayNpk =
    result?.nutrients
      .filter((n) => ["N", "P", "K"].includes(n.nutrient))
      .map((n) => `${n.nutrient}: ${n.actual.toFixed(2)}%`)
      .join(", ") ?? "";

  // ── Render ─────────────────────────────────────────────────
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl px-4 py-8">
        {/* Page header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-orange-50 text-[var(--sapling-orange)]">
              <FlaskConical className="size-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-[var(--sapling-dark)]">
                Quick Blend
              </h1>
              <p className="text-sm text-[var(--sapling-medium-grey)]">
                Design custom fertilizer blends with optimized formulations
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (!confirm("Clear all form data and start fresh?")) return;
              clearSessionGroup(SESSION_KEY);
              window.location.reload();
            }}
          >
            <RotateCcw className="size-3.5" data-icon="inline-start" />
            Reset
          </Button>
        </div>

        {/* Blend type toggle */}
        <div className="mb-6 flex rounded-lg bg-muted p-1">
          {([
            { key: "dry" as const, label: "Pelletised Blend", icon: FlaskConical },
            { key: "liquid" as const, label: "Liquid Blend", icon: Droplets },
            { key: "foliar" as const, label: "Foliar Spray", icon: Leaf },
          ]).map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setBlendType(t.key)}
              className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                blendType === t.key
                  ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <t.icon className="size-4" />
              {t.label}
            </button>
          ))}
        </div>

        {/* ═══════════ LIQUID BLEND MODE ═══════════ */}
        {blendType === "liquid" && (
          <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
            <div className="flex flex-col gap-6">
              {/* Nutrient targets (g/L) */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-[var(--sapling-dark)]">Nutrient Targets (g/L)</CardTitle>
                  <CardDescription>Target concentration per litre of final solution</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-3">
                    {["N", "P", "K", "Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Mo", "Cu"].map((nut) => {
                      const val = parseFloat(liquidTargets[nut] || "0");
                      const limit = liquidSafeLimits[nut] || 999;
                      const overLimit = val > 0 && val > limit;
                      return (
                        <div key={nut} className="space-y-1">
                          <Label htmlFor={`liq-${nut}`}>{nut} g/L</Label>
                          <Input
                            id={`liq-${nut}`}
                            type="number"
                            step="0.1"
                            placeholder="0"
                            value={liquidTargets[nut] || ""}
                            onChange={(e) => setLiquidTargets((prev) => ({ ...prev, [nut]: e.target.value }))}
                            className={overLimit ? "border-red-400 focus-visible:ring-red-400" : ""}
                          />
                          {overLimit && (
                            <p className="text-[10px] text-red-600">Max safe: {limit} g/L</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Tank size */}
              <Card>
                <CardHeader><CardTitle className="text-[var(--sapling-dark)]">Batch Settings</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-1.5">
                    <Label>Batch Volume (L)</Label>
                    <Input type="number" value={tankVolume} onChange={(e) => setTankVolume(e.target.value)} />
                  </div>
                </CardContent>
              </Card>

              {/* Material selection — admin only */}
              {isAdmin && <Card>
                <CardHeader>
                  <CardTitle className="text-[var(--sapling-dark)]">Materials</CardTitle>
                  <CardDescription>Select available liquid-compatible materials</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="max-h-64 space-y-1 overflow-y-auto">
                    {liquidMaterials.map((mat) => (
                      <label key={mat.material} className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-1.5 transition-colors hover:bg-muted">
                        <input
                          type="checkbox"
                          checked={selectedLiquidMaterials.has(mat.material)}
                          onChange={() => {
                            setSelectedLiquidMaterials((prev) => {
                              const next = new Set(prev);
                              if (next.has(mat.material)) next.delete(mat.material);
                              else next.add(mat.material);
                              return next;
                            });
                          }}
                          className="size-4 rounded border-gray-300 accent-[var(--sapling-orange)]"
                        />
                        <span className="flex-1 text-sm">{mat.material}</span>
                        {mat.type && <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">{mat.type}</span>}
                      </label>
                    ))}
                  </div>
                </CardContent>
              </Card>}

              {/* ── Client Info ── */}
              <Card className="overflow-visible">
                <CardHeader>
                  <CardTitle className="text-[var(--sapling-dark)]">
                    Blend Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-1.5">
                    <Label>Blend Name</Label>
                    <Input
                      placeholder="e.g. Mac Fertigation Mix A"
                      value={customBlendName}
                      onChange={(e) => setCustomBlendName(e.target.value)}
                    />
                  </div>
                  <ClientSelector
                    onSelect={(sel) => {
                      setClientName(sel.client_name);
                      setFarmName(sel.farm_name);
                      setFieldName(sel.field_name);
                      setClientId(sel.client_id);
                      setFarmId(sel.farm_id);
                      setFieldId(sel.field_id);
                    }}
                    initialClient={clientName}
                    initialFarm={farmName}
                    initialField={fieldName}
                  />
                </CardContent>
              </Card>

              {/* ── Client required warning (agent) ── */}
              {!isAdmin && !clientName && (
                <div className="flex items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-800">
                  Please select a client and farm before calculating a blend.
                </div>
              )}

              <Button
                size="lg"
                onClick={handleLiquidOptimize}
                disabled={liquidOptimizing || (!isAdmin && !clientName)}
                className="h-12 w-full bg-[var(--sapling-orange)] text-base font-semibold text-white hover:bg-[var(--sapling-orange)]/90"
              >
                {liquidOptimizing ? <Loader2 className="size-5 animate-spin" /> : <Droplets className="size-5" />}
                {liquidOptimizing ? "Optimizing..." : "Calculate Liquid Blend"}
              </Button>
            </div>

            {/* Results */}
            <div className="flex flex-col gap-6">
              {!liquidResult && !liquidOptimizing && (
                <Card className="flex min-h-[300px] flex-col items-center justify-center text-center">
                  <CardContent>
                    <Droplets className="mx-auto mb-4 size-12 text-muted-foreground/30" />
                    <p className="text-lg font-medium text-muted-foreground">Configure your liquid blend</p>
                    <p className="mt-1 text-sm text-muted-foreground/70">Mixing instructions will appear here</p>
                  </CardContent>
                </Card>
              )}

              {liquidResult && (
                <>
                  {/* Compatibility warnings — admin sees details, agent sees contact prompt */}
                  {(liquidResult.compatibility_warnings as Array<Record<string, string>>)?.length > 0 && (
                    isAdmin ? (
                      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                        <p className="font-medium text-red-800">Compatibility Warning</p>
                        {(liquidResult.compatibility_warnings as Array<Record<string, string>>).map((w, i) => (
                          <p key={i} className="mt-1 text-sm text-red-700">{w.material_a} + {w.material_b}: {w.reason}</p>
                        ))}
                      </div>
                    ) : (
                      <Card className="border-2 border-red-300 bg-red-50">
                        <CardContent className="py-6 text-center">
                          <AlertTriangle className="mx-auto size-8 text-red-500" />
                          <p className="mt-3 font-medium text-red-800">
                            This blend has compatibility limitations
                          </p>
                          <p className="mt-1 text-sm text-red-600">
                            Some of the selected materials cannot be mixed together. Please contact Sapling Fertilizer for assistance.
                          </p>
                        </CardContent>
                      </Card>
                    )
                  )}

                  {/* Relaxed warning banner */}
                  {!liquidResult.exact && (liquidResult.scale as number) < 0.999 && !showLiquidPriorityPanel && (
                    <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4">
                      <AlertTriangle className="mt-0.5 size-5 shrink-0 text-amber-600" />
                      <div>
                        <p className="font-medium text-amber-800">Relaxed Blend</p>
                        <p className="mt-0.5 text-sm text-amber-700">
                          An exact match was not possible. The optimizer found the closest blend at{" "}
                          <strong>{Math.round((liquidResult.scale as number) * 100)}%</strong> of your targets.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Priority panel — shown when blend is imperfect */}
                  {showLiquidPriorityPanel && !liquidContactSapling && (
                    <NutrientPriorityPanel
                      targets={Object.fromEntries(
                        Object.entries(liquidTargets)
                          .filter(([, v]) => parseFloat(v) > 0)
                          .map(([k, v]) => [k, parseFloat(v)])
                      )}
                      onOptimize={handleLiquidPriorityOptimize}
                      optimizing={liquidOptimizing}
                    />
                  )}

                  {/* Priority result summary */}
                  {(liquidResult.priority_result as Record<string, unknown>) && !liquidContactSapling && (
                    <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                      <p className="text-sm font-medium text-green-800">Priority Optimization Result</p>
                      <div className="mt-2 space-y-1">
                        {((liquidResult.priority_result as Record<string, unknown>).matched as string[] || []).map((n: string) => (
                          <div key={n} className="flex items-center gap-2 text-xs text-green-700">
                            <span className="size-1.5 rounded-full bg-green-500" />
                            {n} — matched
                          </div>
                        ))}
                        {((liquidResult.priority_result as Record<string, unknown>).compromised as Array<Record<string, unknown>> || []).map((c: Record<string, unknown>) => (
                          <div key={String(c.nutrient)} className="flex items-center gap-2 text-xs text-amber-700">
                            <span className="size-1.5 rounded-full bg-amber-500" />
                            {String(c.nutrient)} — target {String(c.target)} g/L, achieved {String(c.actual)} g/L
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Contact Sapling card */}
                  {liquidContactSapling && (
                    <Card className="border-2 border-red-300 bg-red-50">
                      <CardContent className="py-6 text-center">
                        <AlertTriangle className="mx-auto size-8 text-red-500" />
                        <p className="mt-3 font-medium text-red-800">
                          This blend cannot be achieved with the available materials
                        </p>
                        <p className="mt-1 text-sm text-red-600">
                          Contact Sapling Fertilizer for assistance with this formulation.
                        </p>
                      </CardContent>
                    </Card>
                  )}

                  {/* Safety warnings */}
                  {(liquidResult.warnings as string[])?.length > 0 && (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                      <p className="font-medium text-amber-800">Safety Notes</p>
                      {(liquidResult.warnings as string[]).map((w, i) => (
                        <p key={i} className="mt-1 text-sm text-amber-700">{w}</p>
                      ))}
                    </div>
                  )}

                  {/* Summary */}
                  <Card>
                    <CardHeader><CardTitle>Liquid Blend Summary</CardTitle></CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Batch Volume</p>
                          <p className="mt-1 text-lg font-bold">{liquidResult.tank_volume_l as number} L</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Total Dissolved</p>
                          <p className="mt-1 text-lg font-bold">{liquidResult.total_dissolved_kg as number} kg</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase text-muted-foreground">Est. SG</p>
                          <p className="mt-1 text-lg font-bold">{liquidResult.sg_estimate as number}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Mixing Instructions — admin only */}
                  {isAdmin && (
                    <Card>
                      <CardHeader><CardTitle>Mixing Instructions</CardTitle></CardHeader>
                      <CardContent>
                        <ol className="space-y-2">
                          {(liquidResult.mixing_instructions as string[])?.map((step, i) => (
                            <li key={i} className="flex gap-3 text-sm">
                              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--sapling-orange)] text-xs font-bold text-white">{i + 1}</span>
                              <span>{step}</span>
                            </li>
                          ))}
                        </ol>
                      </CardContent>
                    </Card>
                  )}

                  {/* Recipe Table — admin only */}
                  {isAdmin && (
                    <Card>
                      <CardHeader><CardTitle>Recipe</CardTitle></CardHeader>
                      <CardContent>
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b text-left">
                              <th className="pb-2 pr-4 font-medium text-muted-foreground">Material</th>
                              <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">kg/tank</th>
                              <th className="pb-2 text-right font-medium text-muted-foreground">g/L</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(liquidResult.recipe as Array<Record<string, unknown>>)?.map((row) => (
                              <tr key={row.material as string} className="border-b border-muted last:border-0">
                                <td className="py-2 pr-4 font-medium">{row.material as string}</td>
                                <td className="py-2 pr-4 text-right tabular-nums">{(row.kg_per_tank as number)?.toFixed(2)}</td>
                                <td className="py-2 text-right tabular-nums">{(row.g_per_l as number)?.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </CardContent>
                    </Card>
                  )}

                  {/* Nutrient Analysis */}
                  <Card>
                    <CardHeader><CardTitle>Nutrient Analysis</CardTitle></CardHeader>
                    <CardContent>
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b text-left">
                            <th className="pb-2 pr-4 font-medium text-muted-foreground">Nutrient</th>
                            <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">Target g/L</th>
                            <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">Actual g/L</th>
                            <th className="pb-2 text-right font-medium text-muted-foreground">Diff</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(liquidResult.nutrients as Array<Record<string, unknown>>)
                            ?.filter((n) => (n.target_g_l as number) > 0 || (n.actual_g_l as number) > 0.001)
                            .map((row) => (
                              <tr key={row.nutrient as string} className="border-b border-muted last:border-0">
                                <td className="py-2 pr-4 font-medium">{row.nutrient as string}</td>
                                <td className="py-2 pr-4 text-right tabular-nums">{(row.target_g_l as number)?.toFixed(3)}</td>
                                <td className="py-2 pr-4 text-right tabular-nums">{(row.actual_g_l as number)?.toFixed(3)}</td>
                                <td className={`py-2 text-right tabular-nums ${(row.diff_g_l as number) < -0.01 ? "text-red-600" : (row.diff_g_l as number) > 0.01 ? "text-green-600" : ""}`}>
                                  {(row.diff_g_l as number) >= 0 ? "+" : ""}{(row.diff_g_l as number)?.toFixed(3)}
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </CardContent>
                  </Card>

                  {/* ── Application Rates ── */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Application Rates</CardTitle>
                      <CardDescription>Calculate how much to apply per hectare or per tree</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Method toggle */}
                      <div className="flex rounded-lg bg-muted p-1">
                        {([
                          { key: "fertigation" as const, label: "Fertigation / Drench" },
                          { key: "foliar" as const, label: "Foliar Spray" },
                        ]).map((m) => (
                          <button
                            key={m.key}
                            type="button"
                            onClick={() => setAppMethod(m.key)}
                            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                              appMethod === m.key
                                ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                          >
                            {m.label}
                          </button>
                        ))}
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1.5">
                          <Label>Target nutrient</Label>
                          <select
                            value={appTargetNutrient}
                            onChange={(e) => setAppTargetNutrient(e.target.value)}
                            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
                          >
                            {(liquidResult.nutrients as Array<Record<string, unknown>>)
                              ?.filter((n) => (n.actual_g_l as number) > 0.001)
                              .map((n) => (
                                <option key={n.nutrient as string} value={n.nutrient as string}>
                                  {n.nutrient as string} ({(n.actual_g_l as number)?.toFixed(2)} g/L)
                                </option>
                              ))}
                          </select>
                        </div>
                        <div className="space-y-1.5">
                          <Label>Deliver (kg/ha)</Label>
                          <Input
                            type="number"
                            step="0.1"
                            placeholder={appMethod === "foliar" ? "e.g. 0.5" : "e.g. 5"}
                            value={appTargetKgHa}
                            onChange={(e) => setAppTargetKgHa(e.target.value)}
                          />
                        </div>
                        {appMethod === "fertigation" && (
                          <div className="space-y-1.5">
                            <Label>Dilution ratio (1:X)</Label>
                            <Input
                              type="number"
                              step="1"
                              placeholder="e.g. 100 for 1:100"
                              value={appDilution}
                              onChange={(e) => setAppDilution(e.target.value)}
                            />
                          </div>
                        )}
                        {appMethod === "foliar" && (
                          <div className="space-y-1.5">
                            <Label>Spray volume (L/ha)</Label>
                            <Input
                              type="number"
                              step="10"
                              placeholder="e.g. 500"
                              value={appSprayVolume}
                              onChange={(e) => setAppSprayVolume(e.target.value)}
                            />
                          </div>
                        )}
                        <div className="space-y-1.5">
                          <Label>Plants per ha (optional)</Label>
                          <Input
                            type="number"
                            step="1"
                            placeholder="e.g. 400"
                            value={appPlantsHa}
                            onChange={(e) => setAppPlantsHa(e.target.value)}
                          />
                        </div>
                      </div>

                      {/* Calculated rates */}
                      {(() => {
                        const kgHa = parseFloat(appTargetKgHa);
                        const nutRow = (liquidResult.nutrients as Array<Record<string, unknown>>)
                          ?.find((n) => n.nutrient === appTargetNutrient);
                        const gPerL = nutRow ? (nutRow.actual_g_l as number) : 0;
                        const sg = (liquidResult.sg_estimate as number) || 1.0;
                        const plants = parseFloat(appPlantsHa) || 0;

                        if (!kgHa || kgHa <= 0 || gPerL <= 0) return null;

                        // Concentrate needed: kg/ha target → L/ha of concentrate
                        const concentrateL = (kgHa * 1000) / gPerL;
                        const concentrateKg = concentrateL * sg;
                        const tankVol = (liquidResult.tank_volume_l as number) || 1000;
                        const tanksPerHa = concentrateL / tankVol;

                        // Dilution / spray volume
                        let totalSprayL = 0;
                        let dilutionDisplay = "";
                        if (appMethod === "fertigation") {
                          const dilution = parseFloat(appDilution) || 0;
                          if (dilution > 0) {
                            totalSprayL = concentrateL * (1 + dilution);
                            dilutionDisplay = `1:${dilution}`;
                          }
                        } else {
                          // Foliar: user specifies total spray volume, we calculate dilution
                          const sprayVol = parseFloat(appSprayVolume) || 0;
                          if (sprayVol > 0) {
                            totalSprayL = sprayVol;
                            const effectiveDilution = Math.round(sprayVol / concentrateL);
                            dilutionDisplay = `1:${effectiveDilution}`;
                          }
                        }

                        // Per tree
                        const perTreeMl = plants > 0 ? (concentrateL * 1000) / plants : 0;
                        const perTreeSprayMl = plants > 0 && totalSprayL > 0 ? (totalSprayL * 1000) / plants : 0;

                        // All nutrients delivered
                        const allNutrients = (liquidResult.nutrients as Array<Record<string, unknown>>)
                          ?.filter((n) => (n.actual_g_l as number) > 0.001)
                          .map((n) => ({
                            nutrient: n.nutrient as string,
                            kg_ha: ((n.actual_g_l as number) * concentrateL / 1000),
                          }));

                        // Foliar burn check: concentration in spray tank
                        let burnWarning = "";
                        if (appMethod === "foliar" && totalSprayL > 0) {
                          const sprayConcentrationPct = (concentrateL / totalSprayL) * 100;
                          if (sprayConcentrationPct > 2) {
                            burnWarning = `Spray concentration is ${sprayConcentrationPct.toFixed(1)}% — risk of leaf burn. Keep below 1-2% for most crops.`;
                          }
                        }

                        return (
                          <div className="space-y-3 rounded-lg border bg-muted/30 p-4">
                            {burnWarning && (
                              <div className="flex items-start gap-2 rounded-md bg-red-50 p-2 text-xs text-red-700">
                                <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
                                {burnWarning}
                              </div>
                            )}
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-xs font-medium uppercase text-muted-foreground">Concentrate</p>
                                <p className="mt-1 text-lg font-bold">{concentrateL.toFixed(1)} L/ha</p>
                                <p className="text-xs text-muted-foreground">{concentrateKg.toFixed(1)} kg/ha</p>
                              </div>
                              <div>
                                <p className="text-xs font-medium uppercase text-muted-foreground">Batches per ha</p>
                                <p className="mt-1 text-lg font-bold">{tanksPerHa.toFixed(2)}</p>
                              </div>
                              {totalSprayL > 0 && (
                                <div>
                                  <p className="text-xs font-medium uppercase text-muted-foreground">
                                    {appMethod === "foliar" ? "Total spray volume" : "Diluted volume"}
                                  </p>
                                  <p className="mt-1 text-lg font-bold">{totalSprayL.toFixed(0)} L/ha</p>
                                  {dilutionDisplay && (
                                    <p className="text-xs text-muted-foreground">Dilution {dilutionDisplay}</p>
                                  )}
                                </div>
                              )}
                              {perTreeMl > 0 && (
                                <div>
                                  <p className="text-xs font-medium uppercase text-muted-foreground">Per tree (concentrate)</p>
                                  <p className="mt-1 text-lg font-bold">{perTreeMl.toFixed(0)} mL</p>
                                  {perTreeSprayMl > 0 && (
                                    <p className="text-xs text-muted-foreground">{perTreeSprayMl.toFixed(0)} mL diluted</p>
                                  )}
                                </div>
                              )}
                            </div>

                            {/* All nutrients delivered */}
                            {allNutrients && allNutrients.length > 0 && (
                              <div>
                                <p className="mb-1 text-xs font-medium uppercase text-muted-foreground">All nutrients delivered at this rate</p>
                                <div className="flex flex-wrap gap-2">
                                  {allNutrients.map((n) => (
                                    <span key={n.nutrient} className="rounded-full bg-white px-2 py-0.5 text-xs font-medium">
                                      {n.nutrient}: {n.kg_ha.toFixed(2)} kg/ha
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })()}
                    </CardContent>
                  </Card>

                  {/* ── Action Buttons ── */}
                  <div className="flex flex-wrap gap-3">
                    <Button
                      size="lg"
                      onClick={handleLiquidSave}
                      disabled={liquidSaving}
                      className={`flex-1 ${
                        savedLiquidBlendId
                          ? "bg-green-600 text-white hover:bg-green-700"
                          : "bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                      }`}
                    >
                      {liquidSaving ? (
                        <>
                          <Loader2 className="size-4 animate-spin" />
                          Saving...
                        </>
                      ) : savedLiquidBlendId ? (
                        <>
                          <Check className="size-4" />
                          Saved
                        </>
                      ) : (
                        <>
                          <Save className="size-4" />
                          Save Blend
                        </>
                      )}
                    </Button>
                    <Button
                      size="lg"
                      variant="outline"
                      onClick={handleLiquidDownloadPdf}
                      disabled={!liquidResult}
                      className="flex-1"
                    >
                      <Download className="size-4" />
                      Download PDF
                    </Button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* ═══════════ FOLIAR SPRAY MODE ═══════════ */}
        {blendType === "foliar" && (
          <div className="space-y-6">
            {/* Client / Farm / Field — required for agents */}
            <Card>
              <CardHeader>
                <CardTitle className="text-[var(--sapling-dark)]">Client Details</CardTitle>
                <CardDescription>Select the client and farm this foliar application is for</CardDescription>
              </CardHeader>
              <CardContent>
                <ClientSelector
                  onSelect={(sel) => {
                    setClientName(sel.client_name);
                    setFarmName(sel.farm_name);
                    setFieldName(sel.field_name);
                    setClientId(sel.client_id);
                    setFarmId(sel.farm_id);
                    setFieldId(sel.field_id);
                  }}
                  initialClient={clientName}
                  initialFarm={farmName}
                  initialField={fieldName}
                />
              </CardContent>
            </Card>

            {!isAdmin && !clientId && (
              <div className="flex items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-800">
                Please select a client and farm to browse foliar products.
              </div>
            )}

            {(isAdmin || !!clientId) && (<>
            {/* Nutrient filter */}
            <Card>
              <CardHeader>
                <CardTitle className="text-[var(--sapling-dark)]">Which deficiencies do you want to correct?</CardTitle>
                <CardDescription>Select one or more nutrients to find products that address them</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {["N", "P", "K", "Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Mo", "Cu"].map((nut) => {
                    const active = foliarNutrients.includes(nut.toLowerCase());
                    return (
                      <Button
                        key={nut}
                        size="sm"
                        variant={active ? "default" : "outline"}
                        className={active ? "bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90" : ""}
                        onClick={() => {
                          const next = active
                            ? foliarNutrients.filter((n) => n !== nut.toLowerCase())
                            : [...foliarNutrients, nut.toLowerCase()];
                          setFoliarNutrients(next);
                          handleFoliarLookup(next);
                        }}
                      >
                        {nut}
                      </Button>
                    );
                  })}
                </div>
                {foliarNutrients.length > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-xs text-muted-foreground"
                    onClick={() => { setFoliarNutrients([]); handleFoliarLookup([]); }}
                  >
                    Clear selection — show all products
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Product list */}
            {foliarLoading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="size-6 animate-spin text-muted-foreground" />
              </div>
            )}

            {!foliarLoading && foliarProducts.length === 0 && foliarNutrients.length > 0 && (
              <Card className="flex min-h-[200px] flex-col items-center justify-center text-center">
                <CardContent>
                  <Leaf className="mx-auto mb-4 size-12 text-muted-foreground/30" />
                  <p className="text-lg font-medium text-muted-foreground">No products match {foliarNutrients.map(n => n.toUpperCase()).join(", ")}</p>
                  <p className="mt-1 text-sm text-muted-foreground/70">Try different nutrients or clear the selection</p>
                </CardContent>
              </Card>
            )}

            {!foliarLoading && foliarProducts.length > 0 && (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {foliarProducts.map((prod, i) => {
                  const nutrients = prod.nutrients as Record<string, number> || {};
                  const unit = (prod.analysis_unit as string) || "g/kg";
                  const targetCrops = (prod.target_crops as string[]) || [];
                  const covers = (prod.covers as string[]) || [];
                  const isTopMatch = i === 0 && foliarNutrients.length > 0;
                  const isSelected = selectedFoliar?.name === prod.name;
                  return (
                    <Card
                      key={i}
                      className={`cursor-pointer transition-shadow hover:shadow-md ${isSelected ? "border-2 border-[var(--sapling-orange)] ring-2 ring-[var(--sapling-orange)]/20" : isTopMatch ? "border-2 border-[var(--sapling-orange)]" : ""}`}
                      onClick={() => {
                        if (isSelected) { setSelectedFoliar(null); return; }
                        setSelectedFoliar(prod);
                        setTimeout(() => foliarDetailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
                      }}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-base">{prod.name as string}</CardTitle>
                          {isTopMatch && (
                            <span className="rounded-full bg-[var(--sapling-orange)]/10 px-2 py-0.5 text-xs font-medium text-[var(--sapling-orange)]">
                              Best match
                            </span>
                          )}
                        </div>
                        {covers.length > 0 && (
                          <div className="flex items-center gap-1.5 pt-1">
                            <span className="text-xs text-muted-foreground">Covers:</span>
                            {covers.map((c) => (
                              <span key={c} className="rounded-full bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-700">{c}</span>
                            ))}
                          </div>
                        )}
                        {targetCrops.length > 0 && (
                          <CardDescription>{targetCrops.join(", ")}</CardDescription>
                        )}
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {/* Nutrient breakdown */}
                        <div>
                          <p className="mb-2 text-xs font-medium uppercase text-muted-foreground">Nutrient Breakdown ({unit})</p>
                          <div className="flex flex-wrap gap-1.5">
                            {Object.entries(nutrients).map(([nut, val]) => (
                              <span
                                key={nut}
                                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                  foliarNutrients.includes(nut.toLowerCase())
                                    ? "bg-[var(--sapling-orange)]/15 text-[var(--sapling-orange)] ring-1 ring-[var(--sapling-orange)]/30"
                                    : "bg-muted text-muted-foreground"
                                }`}
                              >
                                {nut} {val}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Application info */}
                        {(prod.spray_volume_l_ha || prod.dilution_rate) ? (
                          <div className="flex gap-4 text-sm">
                            {prod.spray_volume_l_ha ? (
                              <div>
                                <span className="text-xs text-muted-foreground">Spray volume: </span>
                                <span className="font-medium">{String(prod.spray_volume_l_ha)} L/ha</span>
                              </div>
                            ) : null}
                            {prod.dilution_rate ? (
                              <div>
                                <span className="text-xs text-muted-foreground">Dilution: </span>
                                <span className="font-medium">{String(prod.dilution_rate)}</span>
                              </div>
                            ) : null}
                          </div>
                        ) : null}

                        {prod.notes ? (
                          <p className="text-xs text-muted-foreground">{String(prod.notes)}</p>
                        ) : null}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}

            {/* Selected product detail panel */}
            {selectedFoliar && (() => {
              const nutrients = selectedFoliar.nutrients as Record<string, number> || {};
              const unit = (selectedFoliar.analysis_unit as string) || "g/kg";
              const targetCrops = (selectedFoliar.target_crops as string[]) || [];
              const sprayVol = Number(selectedFoliar.spray_volume_l_ha) || 500;
              const hectares = parseFloat(foliarHectares) || 0;
              const defaultRate = 10; // kg/ha
              const totalProduct = hectares * defaultRate;
              const totalWater = hectares * sprayVol;

              return (
                <div ref={foliarDetailRef}>
                <Card className="border-2 border-[var(--sapling-orange)]">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{String(selectedFoliar.name)}</CardTitle>
                      <Button size="sm" variant="ghost" onClick={() => setSelectedFoliar(null)}>Close</Button>
                    </div>
                    {targetCrops.length > 0 && (
                      <CardDescription>Recommended for: {targetCrops.join(", ")}</CardDescription>
                    )}
                  </CardHeader>
                  <CardContent className="space-y-5">
                    {/* Full nutrient breakdown */}
                    <div>
                      <p className="mb-2 text-sm font-semibold text-[var(--sapling-dark)]">Nutrient Analysis ({unit})</p>
                      <div className="grid grid-cols-4 gap-2 sm:grid-cols-6">
                        {Object.entries(nutrients).map(([nut, val]) => (
                          <div key={nut} className={`rounded-lg p-2 text-center ${
                            foliarNutrients.includes(nut.toLowerCase())
                              ? "bg-[var(--sapling-orange)]/10 ring-1 ring-[var(--sapling-orange)]/30"
                              : "bg-muted/50"
                          }`}>
                            <p className="text-lg font-bold text-[var(--sapling-dark)]">{val}</p>
                            <p className="text-xs text-muted-foreground">{nut}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Application details */}
                    <div>
                      <p className="mb-2 text-sm font-semibold text-[var(--sapling-dark)]">Application Details</p>
                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                        <div className="rounded-lg bg-muted/50 p-3">
                          <p className="text-xs text-muted-foreground">Spray Volume</p>
                          <p className="text-sm font-medium">{sprayVol} L/ha</p>
                        </div>
                        {selectedFoliar.dilution_rate ? (
                          <div className="rounded-lg bg-muted/50 p-3">
                            <p className="text-xs text-muted-foreground">Dilution Rate</p>
                            <p className="text-sm font-medium">{String(selectedFoliar.dilution_rate)}</p>
                          </div>
                        ) : null}
                        {selectedFoliar.notes ? (
                          <div className="rounded-lg bg-muted/50 p-3 sm:col-span-2">
                            <p className="text-xs text-muted-foreground">Notes</p>
                            <p className="text-sm font-medium">{String(selectedFoliar.notes)}</p>
                          </div>
                        ) : null}
                      </div>
                    </div>

                    {/* Quantity calculator */}
                    <div className="rounded-lg border bg-gray-50 p-4">
                      <p className="mb-3 text-sm font-semibold text-[var(--sapling-dark)]">Quantity Calculator</p>
                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <Label className="text-xs">Hectares to treat</Label>
                          <Input
                            type="number"
                            step="1"
                            value={foliarHectares}
                            onChange={(e) => setFoliarHectares(e.target.value)}
                            className="mt-1"
                          />
                        </div>
                        <div className="flex flex-col justify-end">
                          <p className="text-xs text-muted-foreground">Product needed</p>
                          <p className="text-lg font-bold text-[var(--sapling-dark)]">{totalProduct > 0 ? `${totalProduct.toFixed(0)} kg` : "—"}</p>
                          <p className="text-xs text-muted-foreground">@ {defaultRate} kg/ha</p>
                        </div>
                        <div className="flex flex-col justify-end">
                          <p className="text-xs text-muted-foreground">Water needed</p>
                          <p className="text-lg font-bold text-[var(--sapling-dark)]">{totalWater > 0 ? `${(totalWater / 1000).toFixed(1)} kL` : "—"}</p>
                          <p className="text-xs text-muted-foreground">@ {sprayVol} L/ha</p>
                        </div>
                      </div>
                    </div>

                    {/* Request Quote */}
                    {clientName && (
                      <div className="rounded-lg bg-muted/50 p-3">
                        <p className="text-xs text-muted-foreground">Quoting for</p>
                        <p className="text-sm font-medium">{clientName}{farmName ? ` — ${farmName}` : ""}{fieldName ? ` / ${fieldName}` : ""}</p>
                      </div>
                    )}
                    <Button
                      className="w-full bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                      onClick={() => {
                        const msg = `Foliar quote request: ${String(selectedFoliar.name)}, ${totalProduct > 0 ? totalProduct.toFixed(0) + " kg" : "qty TBD"} for ${hectares > 0 ? hectares + " ha" : "TBD ha"}${clientName ? ` — ${clientName}` : ""}`;
                        toast.success(msg + " — contact Sapling to finalise pricing");
                      }}
                    >
                      <Send className="mr-2 size-4" />
                      Request Quote — {totalProduct > 0 ? `${totalProduct.toFixed(0)} kg` : "Select hectares"}
                    </Button>
                  </CardContent>
                </Card>
                </div>
              );
            })()}
            </>)}
          </div>
        )}

        {/* ═══════════ PELLETISED BLEND MODE ═══════════ */}
        {blendType === "dry" && <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          {/* ═══════════ LEFT COLUMN — INPUTS ═══════════ */}
          <div className="flex flex-col gap-6">
            {/* ── Nutrient Targets ── */}
            <Card>
              <CardHeader>
                <CardTitle className="text-[var(--sapling-dark)]">
                  Nutrient Targets
                </CardTitle>
                <CardDescription>
                  Set your desired NPK concentration
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Mode toggle */}
                <div className="flex rounded-lg bg-muted p-1">
                  <button
                    type="button"
                    onClick={() => setMode("international")}
                    className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                      mode === "international"
                        ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    International (%)
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode("sa")}
                    className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                      mode === "sa"
                        ? "bg-white text-[var(--sapling-dark)] shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    SA Local (ratio)
                  </button>
                </div>

                {mode === "international" ? (
                  <div className="grid grid-cols-3 gap-3">
                    {PRIMARY_NUTRIENTS.map((key) => (
                      <div key={key} className="space-y-1.5">
                        <Label htmlFor={`int-${key}`}>{key} %</Label>
                        <Input
                          id={`int-${key}`}
                          type="number"
                          min="0"
                          step="0.1"
                          placeholder="0.0"
                          value={intTargets[key]}
                          onChange={(e) =>
                            setIntTargets((prev) => ({
                              ...prev,
                              [key]: e.target.value,
                            }))
                          }
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="grid grid-cols-4 gap-2">
                      {PRIMARY_NUTRIENTS.map((key) => (
                        <div key={key} className="space-y-1.5">
                          <Label htmlFor={`sa-${key}`}>{key}</Label>
                          <Input
                            id={`sa-${key}`}
                            type="number"
                            min="0"
                            step="1"
                            placeholder="0"
                            value={saRatio[key]}
                            onChange={(e) =>
                              setSaRatio((prev) => ({
                                ...prev,
                                [key]: e.target.value,
                              }))
                            }
                          />
                        </div>
                      ))}
                      <div className="space-y-1.5">
                        <Label htmlFor="sa-total">Total %</Label>
                        <Input
                          id="sa-total"
                          type="number"
                          min="0"
                          step="0.5"
                          placeholder="0"
                          value={saTotalPct}
                          onChange={(e) => setSaTotalPct(e.target.value)}
                        />
                      </div>
                    </div>
                    {/* Live preview */}
                    {(() => {
                      const n = parseInt(saRatio.N) || 0;
                      const p = parseInt(saRatio.P) || 0;
                      const k = parseInt(saRatio.K) || 0;
                      const total = parseFloat(saTotalPct) || 0;
                      if (n + p + k === 0) return null;
                      const pcts = saRatioToPercent(n, p, k, total);
                      return (
                        <p className="text-xs text-muted-foreground">
                          Converts to: N {pcts.N.toFixed(2)}%, P{" "}
                          {pcts.P.toFixed(2)}%, K {pcts.K.toFixed(2)}%
                        </p>
                      );
                    })()}
                  </div>
                )}

                {/* Secondary nutrients collapsible */}
                <button
                  type="button"
                  onClick={() => setShowSecondary(!showSecondary)}
                  className="flex w-full items-center gap-2 text-sm font-medium text-[var(--sapling-medium-grey)] hover:text-[var(--sapling-dark)]"
                >
                  {showSecondary ? (
                    <ChevronUp className="size-4" />
                  ) : (
                    <ChevronDown className="size-4" />
                  )}
                  Secondary nutrients
                </button>

                {showSecondary && (
                  <div className="grid grid-cols-3 gap-3">
                    {SECONDARY_NUTRIENTS.map((key) => (
                      <div key={key} className="space-y-1.5">
                        <Label htmlFor={`sec-${key}`}>{key} %</Label>
                        <Input
                          id={`sec-${key}`}
                          type="number"
                          min="0"
                          step="0.01"
                          placeholder="0.0"
                          value={secondaryTargets[key] || ""}
                          onChange={(e) =>
                            setSecondaryTargets((prev) => ({
                              ...prev,
                              [key]: e.target.value,
                            }))
                          }
                        />
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* ── Blend Settings ── */}
            <Card>
              <CardHeader>
                <CardTitle className="text-[var(--sapling-dark)]">
                  Blend Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Blend Mode Toggle — admin only */}
                {isAdmin && (
                  <div className="space-y-1.5">
                    <Label>Blend Mode</Label>
                    <div className="flex gap-2">
                      {(["compost", "chemical"] as const).map((mode) => (
                        <button
                          key={mode}
                          type="button"
                          onClick={() => setBlendMode(mode)}
                          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                            blendMode === mode
                              ? "bg-[var(--sapling-orange)] text-white"
                              : "bg-muted text-muted-foreground hover:bg-muted/80"
                          }`}
                        >
                          {mode === "compost" ? "Compost Blend" : "Chemical Blend"}
                        </button>
                      ))}
                    </div>
                    {blendMode === "chemical" && (
                      <p className="text-xs text-muted-foreground">
                        Uses Dolomitic Lime as filler/carrier instead of compost
                      </p>
                    )}
                  </div>
                )}

                <div className="space-y-1.5">
                  <Label htmlFor="batch-size">Batch Size (kg)</Label>
                  <Input
                    id="batch-size"
                    type="number"
                    min="1"
                    step="100"
                    value={batchSize}
                    onChange={(e) => setBatchSize(e.target.value)}
                  />
                </div>

                {/* Compost slider — hidden in chemical mode */}
                {blendMode === "compost" && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="min-compost">Minimum Compost %</Label>
                    <span className="text-sm font-medium text-[var(--sapling-orange)]">
                      {minCompost}%
                    </span>
                  </div>
                  <input
                    id="min-compost"
                    type="range"
                    min={isAdmin ? 0 : agentMinCompost}
                    max="95"
                    step="5"
                    value={minCompost}
                    onChange={(e) => setMinCompost(parseInt(e.target.value))}
                    className="h-2 w-full cursor-pointer appearance-none rounded-full bg-gray-200 accent-[var(--sapling-orange)]"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{isAdmin ? "0%" : `${agentMinCompost}% (min)`}</span>
                    <span>95%</span>
                  </div>
                </div>
                )}
              </CardContent>
            </Card>

            {/* ── Blend Preferences (agent) ── */}
            {!isAdmin && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-[var(--sapling-dark)]">
                    Blend Preferences
                  </CardTitle>
                  <CardDescription>
                    Adjust blend properties for this calculation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {BLEND_PREFERENCES.map((pref) => (
                      <label
                        key={pref.id}
                        className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-muted"
                      >
                        <input
                          type="checkbox"
                          checked={activePrefs.has(pref.id)}
                          onChange={() => {
                            setActivePrefs((prev) => {
                              const next = new Set(prev);
                              if (next.has(pref.id)) next.delete(pref.id);
                              else next.add(pref.id);
                              return next;
                            });
                          }}
                          className="size-4 rounded border-gray-300 accent-[var(--sapling-orange)]"
                        />
                        <div>
                          <span className="text-sm font-medium text-[var(--sapling-dark)]">
                            {pref.label}
                          </span>
                          <p className="text-xs text-muted-foreground">{pref.description}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ── Material Selection (admin only) ── */}
            {isAdmin && <Card>
              <CardHeader>
                <CardTitle className="text-[var(--sapling-dark)]">
                  Materials
                </CardTitle>
                <CardDescription>
                  Select materials to include in the blend
                </CardDescription>
              </CardHeader>
              <CardContent>
                {materialsLoading ? (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 className="size-5 animate-spin text-[var(--sapling-orange)]" />
                  </div>
                ) : isAdmin ? (
                  /* Admin: full control over material selection */
                  <div className="max-h-64 space-y-1 overflow-y-auto">
                    {materials.filter((m) => m.material !== "Manure Compost" && m.material !== "Dolomitic Lime (Filler)").map((mat) => (
                      <label
                        key={mat.id || mat.material}
                        className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-1.5 transition-colors hover:bg-muted"
                      >
                        <input
                          type="checkbox"
                          checked={selectedMaterials.has(mat.material)}
                          onChange={() => toggleMaterial(mat.material)}
                          className="size-4 rounded border-gray-300 accent-[var(--sapling-orange)]"
                        />
                        <span className="flex-1 text-sm text-[var(--sapling-dark)]">
                          {mat.material}
                        </span>
                        {mat.type && (
                          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                            {mat.type}
                          </span>
                        )}
                      </label>
                    ))}
                  </div>
                ) : (
                  /* Agent: show default materials only, no editing */
                  <div className="space-y-1">
                    {materials
                      .filter((m) => selectedMaterials.has(m.material) && m.material !== "Manure Compost" && m.material !== "Dolomitic Lime (Filler)")
                      .map((mat) => (
                        <div
                          key={mat.id || mat.material}
                          className="flex items-center gap-3 rounded-md px-2 py-1.5"
                        >
                          <div className="size-2 rounded-full bg-[var(--sapling-orange)]" />
                          <span className="flex-1 text-sm text-[var(--sapling-dark)]">
                            {mat.material}
                          </span>
                          {mat.type && (
                            <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                              {mat.type}
                            </span>
                          )}
                        </div>
                      ))}
                    <p className="pt-1 text-xs text-muted-foreground">
                      Materials set by admin
                    </p>
                  </div>
                )}
              </CardContent>
              <CardFooter>
                <div className="flex w-full items-center justify-between text-xs text-muted-foreground">
                  <span>{selectedMaterials.size} selected</span>
                  {isAdmin && <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() =>
                        setSelectedMaterials(
                          new Set(materials.map((m) => m.material))
                        )
                      }
                      className="text-[var(--sapling-orange)] hover:underline"
                    >
                      Select all
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedMaterials(new Set())}
                      className="text-[var(--sapling-orange)] hover:underline"
                    >
                      Clear
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        api.get<{ materials: string[] }>("/api/materials/defaults").then((d) => {
                          setSelectedMaterials(new Set(d.materials));
                          toast.success("Synced with system defaults");
                        })
                      }
                      className="text-[var(--sapling-orange)] hover:underline"
                    >
                      Sync with Defaults
                    </button>
                  </div>}
                </div>
              </CardFooter>
            </Card>}

            {/* ── Blend Details ── */}
            <Card className="overflow-visible">
              <CardHeader>
                <CardTitle className="text-[var(--sapling-dark)]">
                  Blend Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label>Blend Name</Label>
                  <Input
                    placeholder="e.g. Maize Starter 2:3:2"
                    value={customBlendName}
                    onChange={(e) => setCustomBlendName(e.target.value)}
                  />
                </div>
                <ClientSelector
                  onSelect={(sel) => {
                    setClientName(sel.client_name);
                    setFarmName(sel.farm_name);
                    setFieldName(sel.field_name);
                    setClientId(sel.client_id);
                    setFarmId(sel.farm_id);
                    setFieldId(sel.field_id);
                  }}
                  initialClient={clientName}
                  initialFarm={farmName}
                  initialField={fieldName}
                />
              </CardContent>
            </Card>

            {/* ── Calculate Button ── */}
            {!isAdmin && !clientName && (
              <div className="flex items-center gap-2 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-800">
                Please select a client and farm before calculating a blend.
              </div>
            )}
            <Button
              size="lg"
              onClick={handleOptimize}
              disabled={optimizing || (!isAdmin && !clientName)}
              className="h-12 w-full bg-[var(--sapling-orange)] text-base font-semibold text-white hover:bg-[var(--sapling-orange)]/90"
            >
              {optimizing ? (
                <>
                  <Loader2 className="size-5 animate-spin" />
                  Optimizing...
                </>
              ) : (
                <>
                  <FlaskConical className="size-5" />
                  Calculate Blend
                </>
              )}
            </Button>
          </div>

          {/* ═══════════ RIGHT COLUMN — RESULTS ═══════════ */}
          <div className="flex flex-col gap-6">
            {!result && !optimizing && (
              <Card className="flex min-h-[300px] flex-col items-center justify-center text-center">
                <CardContent>
                  <FlaskConical className="mx-auto mb-4 size-12 text-muted-foreground/30" />
                  <p className="text-lg font-medium text-muted-foreground">
                    Configure your blend and click Calculate
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground/70">
                    Results will appear here
                  </p>
                </CardContent>
              </Card>
            )}

            {optimizing && (
              <Card className="flex min-h-[300px] flex-col items-center justify-center">
                <CardContent className="text-center">
                  <Loader2 className="mx-auto mb-4 size-10 animate-spin text-[var(--sapling-orange)]" />
                  <p className="text-lg font-medium text-[var(--sapling-dark)]">
                    Optimizing blend...
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Finding the best formulation for your targets
                  </p>
                </CardContent>
              </Card>
            )}

            {result && (
              <>
                {/* Relaxed warning banner */}
                {!result.exact && result.scale < 0.999 && (
                  <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4">
                    <AlertTriangle className="mt-0.5 size-5 shrink-0 text-amber-600" />
                    <div>
                      <p className="font-medium text-amber-800">
                        Relaxed Blend
                      </p>
                      <p className="mt-0.5 text-sm text-amber-700">
                        An exact match was not possible with the selected
                        materials. The optimizer found the closest blend at{" "}
                        <strong>{Math.round(result.scale * 100)}%</strong> of
                        your original targets.
                      </p>
                    </div>
                  </div>
                )}

                {/* Priority panel — shown when blend is imperfect */}
                {showPriorityPanel && !contactSapling && (
                  <NutrientPriorityPanel
                    targets={buildTargets()}
                    missedTargets={result.missed_targets}
                    onOptimize={handlePriorityOptimize}
                    optimizing={optimizing}
                  />
                )}

                {/* Priority result summary */}
                {result.priority_result && !contactSapling && (
                  <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                    <p className="text-sm font-medium text-green-800">Priority Optimization Result</p>
                    <div className="mt-2 space-y-1">
                      {((result.priority_result as Record<string, unknown>).matched as string[] || []).map((n: string) => (
                        <div key={n} className="flex items-center gap-2 text-xs text-green-700">
                          <span className="size-1.5 rounded-full bg-green-500" />
                          {n} — matched exactly
                        </div>
                      ))}
                      {((result.priority_result as Record<string, unknown>).compromised as Array<Record<string, unknown>> || []).map((c: Record<string, unknown>) => (
                        <div key={String(c.nutrient)} className="flex items-center gap-2 text-xs text-amber-700">
                          <span className="size-1.5 rounded-full bg-amber-500" />
                          {String(c.nutrient)} — target {String(c.target)}%, achieved {String(c.actual)}%
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Contact Sapling card */}
                {contactSapling && (
                  <Card className="border-2 border-red-300 bg-red-50">
                    <CardContent className="py-6 text-center">
                      <AlertTriangle className="mx-auto size-8 text-red-500" />
                      <p className="mt-3 font-medium text-red-800">
                        This blend cannot be achieved with the available materials
                      </p>
                      <p className="mt-1 text-sm text-red-600">
                        Our team can help find a solution. We&apos;ll review your targets and suggest alternatives.
                      </p>
                      <Button
                        onClick={() => setBlendAssistDialogOpen(true)}
                        className="mt-4 bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                      >
                        <Send className="size-4" />
                        Contact Sapling Fertilizer
                      </Button>
                    </CardContent>
                  </Card>
                )}

                {/* Quote Response Banner — only when opened from admin quotes */}
                {quoteRef && (
                  <Card className="border-2 border-purple-300 bg-purple-50">
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wider text-purple-600">
                            Responding to Quote
                          </p>
                          <p className="text-sm font-bold text-purple-800">{quoteRef.number}</p>
                          <p className="text-xs text-purple-600">{clientName}{farmName ? ` / ${farmName}` : ""}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="text-right">
                            <label className="text-xs text-purple-600">Price (R)</label>
                            <Input
                              type="number"
                              step="0.01"
                              value={sellingPrice}
                              onChange={(e) => setSellingPrice(e.target.value)}
                              placeholder="0.00"
                              className="h-8 w-32 text-right font-bold"
                            />
                          </div>
                          <Button
                            disabled={!sellingPrice || parseFloat(sellingPrice) <= 0}
                            className="bg-purple-600 text-white hover:bg-purple-700"
                            onClick={async () => {
                              if (!confirm(`Send quote at R${parseFloat(sellingPrice).toLocaleString("en-ZA", {minimumFractionDigits: 2})} per ton to the agent?`)) return;
                              try {
                                await api.post(`/api/quotes/admin/${quoteRef.id}/quote`, {
                                  quoted_price: parseFloat(sellingPrice),
                                  price_unit: "per_ton",
                                  admin_notes: `Blend: ${result.sa_notation} | Batch: ${result.batch_size}kg`,
                                });
                                toast.success("Quote sent to agent!");
                                setQuoteRef(null);
                              } catch (err) {
                                toast.error(err instanceof Error ? err.message : "Failed to send quote");
                              }
                            }}
                          >
                            <Send className="size-3.5" />
                            Send Quote
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Missed targets info */}
                {result.missed_targets && result.missed_targets.length > 0 && (
                  <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                    <p className="font-medium text-blue-800">
                      Some nutrient targets could not be met exactly
                    </p>
                    <div className="mt-2 space-y-2">
                      {result.missed_targets.map((m) => (
                        <div key={m.nutrient} className="text-sm text-blue-700">
                          <span className="font-medium">{m.nutrient}</span>: target {m.target}% — achieved {m.actual}% (short by {m.shortfall}%)
                          {isAdmin && m.suggested_materials.length > 0 && (
                            <p className="mt-0.5 text-xs text-blue-600">
                              Try adding: {m.suggested_materials.join(", ")}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* ── Summary Card ── */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-[var(--sapling-dark)]">
                      Blend Summary
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                          SA Notation
                        </p>
                        <p className="mt-1 text-xl font-bold text-[var(--sapling-dark)]">
                          {result.sa_notation}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                          International
                        </p>
                        <p className="mt-1 text-sm font-medium text-[var(--sapling-dark)]">
                          {result.international_notation || displayNpk}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                          Batch Size
                        </p>
                        <p className="mt-1 text-sm font-medium text-[var(--sapling-dark)]">
                          {result.batch_size.toLocaleString()} kg
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                          {blendMode === "chemical" ? "Filler %" : "Compost %"}
                        </p>
                        <p className="mt-1 text-sm font-medium text-[var(--sapling-dark)]">
                          {(() => {
                            const carrier = blendMode === "chemical" ? "Dolomitic Lime (Filler)" : "Manure Compost";
                            const carrierRow = result.recipe.find((r) => r.material === carrier);
                            return carrierRow ? `${carrierRow.pct.toFixed(1)}%` : "0%";
                          })()}
                        </p>
                      </div>
                      {isAdmin && (<>
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                            Cost per Ton
                          </p>
                          <p className="mt-1 text-lg font-bold text-[var(--sapling-dark)]">
                            R {result.cost_per_ton.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                            Selling Price
                          </p>
                          <div className="mt-1 flex items-center gap-1">
                            <span className="text-sm text-muted-foreground">R</span>
                            <Input
                              type="number"
                              min="0"
                              step="100"
                              placeholder="0"
                              value={sellingPrice}
                              onChange={(e) => setSellingPrice(e.target.value)}
                              className="h-8 w-28 text-right font-bold"
                            />
                          </div>
                          {sellingPrice && parseFloat(sellingPrice) > 0 && (
                            <p className={`mt-0.5 text-xs font-medium ${
                              parseFloat(sellingPrice) >= result.cost_per_ton ? "text-green-600" : "text-red-600"
                            }`}>
                              Margin: R {(parseFloat(sellingPrice) - result.cost_per_ton).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                          )}
                        </div>
                      </>)}
                    </div>
                  </CardContent>
                </Card>

                {/* ── Request Quote (agent only) ── */}
                {!isAdmin && (
                  <Card className="border-2 border-[var(--sapling-orange)]">
                    <CardContent className="py-6 text-center">
                      <p className="mb-3 text-sm text-muted-foreground">
                        Ready to get a price for this blend?
                      </p>
                      <Button
                        onClick={() => setQuoteDialogOpen(true)}
                        className="bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                      >
                        <Send className="size-4" />
                        Request Quote
                      </Button>
                    </CardContent>
                  </Card>
                )}

                {/* ── Recipe Table (admin only) ── */}
                {isAdmin && result.recipe.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-[var(--sapling-dark)]">
                        Recipe
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b text-left">
                              <th className="pb-2 pr-4 font-medium text-muted-foreground">
                                Material
                              </th>
                              <th className="pb-2 pr-4 font-medium text-muted-foreground">
                                Type
                              </th>
                              <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">
                                kg
                              </th>
                              <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">
                                % of Blend
                              </th>
                              <th className="pb-2 text-right font-medium text-muted-foreground">
                                Cost (R)
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {result.recipe.map((row) => (
                              <tr
                                key={row.material}
                                className="border-b border-muted last:border-0"
                              >
                                <td className="py-2 pr-4 font-medium text-[var(--sapling-dark)]">
                                  {row.material}
                                </td>
                                <td className="py-2 pr-4 text-muted-foreground">
                                  {row.type || "-"}
                                </td>
                                <td className="py-2 pr-4 text-right tabular-nums">
                                  {row.kg.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </td>
                                <td className="py-2 pr-4 text-right tabular-nums">
                                  {row.pct.toFixed(2)}%
                                </td>
                                <td className="py-2 text-right tabular-nums">
                                  R {row.cost.toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* ── Nutrient Analysis Table ── */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-[var(--sapling-dark)]">
                      Nutrient Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b text-left">
                            <th className="pb-2 pr-4 font-medium text-muted-foreground">
                              Nutrient
                            </th>
                            <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">
                              Target %
                            </th>
                            <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">
                              Actual %
                            </th>
                            <th className="pb-2 pr-4 text-right font-medium text-muted-foreground">
                              Diff
                            </th>
                            <th className="pb-2 text-right font-medium text-muted-foreground">
                              kg/ton
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.nutrients
                            .filter(
                              (n) => n.target > 0 || n.actual > 0.001
                            )
                            .map((row) => (
                              <tr
                                key={row.nutrient}
                                className="border-b border-muted last:border-0"
                              >
                                <td className="py-2 pr-4 font-medium text-[var(--sapling-dark)]">
                                  {row.nutrient}
                                </td>
                                <td className="py-2 pr-4 text-right tabular-nums">
                                  {row.target.toFixed(3)}
                                </td>
                                <td className="py-2 pr-4 text-right tabular-nums">
                                  {row.actual.toFixed(3)}
                                </td>
                                <td
                                  className={`py-2 pr-4 text-right tabular-nums ${
                                    row.diff < -0.01
                                      ? "text-red-600"
                                      : row.diff > 0.01
                                        ? "text-green-600"
                                        : ""
                                  }`}
                                >
                                  {row.diff >= 0 ? "+" : ""}
                                  {row.diff.toFixed(3)}
                                </td>
                                <td className="py-2 text-right tabular-nums">
                                  {row.kg_per_ton.toFixed(2)}
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>

                {/* ── Pricing Suggestion (admin only) ── */}
                {isAdmin && result.pricing && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-[var(--sapling-dark)]">
                        Pricing Suggestion
                      </CardTitle>
                      <CardDescription>
                        Method: {result.pricing.method}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-3 gap-3">
                        {(
                          [
                            {
                              label: "Low",
                              value: result.pricing.low,
                              color: "bg-green-50 text-green-700 border-green-200",
                            },
                            {
                              label: "Mid",
                              value: result.pricing.mid,
                              color: "bg-orange-50 text-orange-700 border-orange-200",
                            },
                            {
                              label: "High",
                              value: result.pricing.high,
                              color: "bg-red-50 text-red-700 border-red-200",
                            },
                          ] as const
                        ).map((tier) => (
                          <div
                            key={tier.label}
                            className={`rounded-lg border p-3 text-center ${tier.color}`}
                          >
                            <p className="text-xs font-medium uppercase tracking-wider opacity-70">
                              {tier.label}
                            </p>
                            <p className="mt-1 text-lg font-bold">
                              R{" "}
                              {tier.value.toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}
                            </p>
                          </div>
                        ))}
                      </div>

                      {/* Comparable blends */}
                      {result.pricing.comparables &&
                        result.pricing.comparables.length > 0 && (
                          <div>
                            <p className="mb-2 text-sm font-medium text-muted-foreground">
                              Comparable Blends
                            </p>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="border-b text-left">
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">
                                      Blend
                                    </th>
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">
                                      SA Notation
                                    </th>
                                    <th className="pb-2 text-right font-medium text-muted-foreground">
                                      Price (R/ton)
                                    </th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {result.pricing.comparables.map(
                                    (comp, idx) => (
                                      <tr
                                        key={idx}
                                        className="border-b border-muted last:border-0"
                                      >
                                        <td className="py-1.5 pr-4">
                                          {comp.blend_name}
                                        </td>
                                        <td className="py-1.5 pr-4 text-muted-foreground">
                                          {comp.sa_notation}
                                        </td>
                                        <td className="py-1.5 text-right tabular-nums">
                                          R{" "}
                                          {(comp.selling_price ?? comp.price ?? 0).toLocaleString(
                                            undefined,
                                            {
                                              minimumFractionDigits: 2,
                                              maximumFractionDigits: 2,
                                            }
                                          )}
                                        </td>
                                      </tr>
                                    )
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                      {/* Past quotes */}
                      {result.pricing.quote_comparables &&
                        result.pricing.quote_comparables.length > 0 && (
                          <div>
                            <p className="mb-2 text-sm font-medium text-muted-foreground">
                              Past Quotes
                            </p>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="border-b text-left">
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">Quote</th>
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">Client</th>
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">Date</th>
                                    <th className="pb-2 pr-4 font-medium text-muted-foreground">Status</th>
                                    <th className="pb-2 text-right font-medium text-muted-foreground">Price (R/ton)</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {result.pricing.quote_comparables.map(
                                    (q, idx) => (
                                      <tr key={idx} className="border-b border-muted last:border-0">
                                        <td className="py-1.5 pr-4">{q.blend_name || q.quote_number || ""}</td>
                                        <td className="py-1.5 pr-4 text-muted-foreground">{q.client || ""}</td>
                                        <td className="py-1.5 pr-4 text-muted-foreground">{q.date || ""}</td>
                                        <td className="py-1.5 pr-4">
                                          <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                                            q.status === "accepted" ? "bg-green-100 text-green-700" :
                                            q.status === "pending" ? "bg-yellow-100 text-yellow-700" :
                                            q.status === "quoted" ? "bg-purple-100 text-purple-700" :
                                            q.status === "declined" ? "bg-red-100 text-red-700" :
                                            "bg-gray-100 text-gray-500"
                                          }`}>
                                            {q.status || ""}
                                          </span>
                                        </td>
                                        <td className="py-1.5 text-right tabular-nums">
                                          R {(q.price ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </td>
                                      </tr>
                                    )
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                    </CardContent>
                  </Card>
                )}

                {/* ── Action Buttons ── */}
                <div className="flex flex-wrap gap-3">
                  <Button
                    size="lg"
                    onClick={handleSave}
                    disabled={saving}
                    className={`flex-1 ${
                      savedBlendId
                        ? "bg-green-600 text-white hover:bg-green-700"
                        : "bg-[var(--sapling-orange)] text-white hover:bg-[var(--sapling-orange)]/90"
                    }`}
                  >
                    {saving ? (
                      <>
                        <Loader2 className="size-4 animate-spin" />
                        Saving...
                      </>
                    ) : savedBlendId ? (
                      <>
                        <Check className="size-4" />
                        Saved
                      </>
                    ) : (
                      <>
                        <Save className="size-4" />
                        Save Blend
                      </>
                    )}
                  </Button>
                  <Button
                    size="lg"
                    variant="outline"
                    onClick={handleDownloadPdf}
                    disabled={!result}
                    className="flex-1"
                  >
                    <Download className="size-4" />
                    Download PDF
                  </Button>
                  {isAdmin && (
                    <Button
                      size="lg"
                      variant="outline"
                      onClick={() => setQuoteSheetOpen(true)}
                      disabled={!result}
                      className="flex-1 border-purple-300 text-purple-700 hover:bg-purple-50"
                    >
                      <Send className="size-4" />
                      Create Quote
                    </Button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>}
      </div>
      {/* Quote Request Dialog */}
      {result && (
        <QuoteRequestDialog
          open={quoteDialogOpen}
          onClose={() => setQuoteDialogOpen(false)}
          quoteType="blend"
          requestData={{
            sa_notation: result.sa_notation,
            international_notation: result.international_notation,
            batch_size: result.batch_size,
            min_compost_pct: result.min_compost_pct,
            blend_mode: blendMode,
            preferences: [...activePrefs],
            nutrients: result.nutrients,
          }}
          clientName={clientName}
          farmName={farmName}
          summary={`${result.sa_notation} - Batch: ${result.batch_size}kg`}
        />
      )}
      {/* Admin Create Quote Dialog */}
      {result && isAdmin && (
        <CreateQuoteDialog
          open={quoteSheetOpen}
          onClose={() => setQuoteSheetOpen(false)}
          profile={profile}
          clientName={clientName}
          clientId={clientId}
          farmName={farmName}
          sellingPrice={parseFloat(sellingPrice) || 0}
          savedBlendId={savedBlendId}
          blendData={{
            sa_notation: result.sa_notation,
            international_notation: result.international_notation,
            batch_size: result.batch_size,
            min_compost_pct: result.min_compost_pct,
            blend_mode: blendMode,
            preferences: [...activePrefs],
            nutrients: result.nutrients,
            recipe: result.recipe,
            cost_per_ton: result.cost_per_ton,
          }}
        />
      )}
      {/* Blend Assist Dialog (Contact Sapling) */}
      {contactSapling && (
        <QuoteRequestDialog
          open={blendAssistDialogOpen}
          onClose={() => setBlendAssistDialogOpen(false)}
          quoteType="blend_assist"
          requestData={{
            targets: buildTargets(),
            selected_materials: [...selectedMaterials],
            batch_size: parseFloat(batchSize) || 1000,
            blend_mode: blendMode,
            achievable_result: result ? {
              sa_notation: result.sa_notation,
              nutrients: result.nutrients,
              scale: result.scale,
              priority_result: result.priority_result,
            } : null,
            reason: "Optimizer could not find a feasible blend matching the priority constraints.",
          }}
          clientName={clientName}
          farmName={farmName}
          summary={`Blend assist — ${Object.entries(buildTargets()).filter(([,v]) => v > 0).map(([k,v]) => `${k}:${v}%`).join(", ")}`}
        />
      )}
    </AppShell>
  );
}
