# Sapling Blend Calculator — Data Flow & Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SUPABASE (PostgreSQL)                        │
│                                                                     │
│  Reference Data          Transactional Data         User Data       │
│  ─────────────           ──────────────────         ─────────       │
│  crop_requirements       soil_analyses              profiles        │
│  soil_sufficiency        blends                     clients         │
│  crop_sufficiency_       feeding_plans              farms           │
│    overrides             feeding_plan_items          fields          │
│  adjustment_factors      field_crop_history         agent_crop_     │
│  ideal_ratios                                         overrides     │
│  soil_parameter_map                                                 │
│  crop_growth_stages                                                 │
│  perennial_age_factors                                              │
│  materials                                                          │
│  material_markups                                                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │   FastAPI Backend    │
                    │   (Python)           │
                    │                     │
                    │  /api/soil/*        │
                    │  /api/blends/*      │
                    │  /api/feeding-plans/*│
                    │  /api/crop-norms/*  │
                    │  /api/clients/*     │
                    │  /api/materials/*   │
                    │  /api/reports/*     │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │  Next.js Frontend   │
                    │  (TypeScript/React) │
                    │                     │
                    │  /soil              │
                    │  /blends            │
                    │  /clients           │
                    │  /records           │
                    │  /profile           │
                    │  /admin/*           │
                    └─────────────────────┘
```

---

## 1. SOIL ANALYSIS — Full Data Flow

```
USER INPUT                    REFERENCE DATA USED              CALCULATION              OUTPUT
──────────                    ───────────────────              ───────────              ──────

Soil lab values ──────────┐
(pH, P, K, Ca, Mg, ...)   │
                           │
Crop selection ────────────┤
                           │
Yield target ──────────────┤
                           │
                           ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │  STEP 1: CLASSIFICATION  (POST /api/soil/classify)          │
                    │                                                             │
                    │  INPUTS:                                                    │
                    │    • soil_values (user input)                               │
                    │    • crop name (user input)                                 │
                    │                                                             │
                    │  REFERENCE DATA:                                            │
                    │    • soil_sufficiency table (universal thresholds)           │
                    │    • crop_sufficiency_overrides table (per-crop overrides)   │
                    │    • ideal_ratios table (Ca:Mg, Ca:K, P:Zn, etc.)          │
                    │                                                             │
                    │  CALCULATIONS:                                              │
                    │    1. Merge universal thresholds + crop overrides            │
                    │    2. For each soil param: compare value to thresholds       │
                    │       → classify as Very Low / Low / Optimal / High / V.High│
                    │    3. Compute ratios from soil values (Ca/Mg, Ca/K, etc.)   │
                    │    4. Compare ratios to ideal ranges → status               │
                    │                                                             │
                    │  OUTPUT:                                                    │
                    │    • classifications: {param: "Optimal", ...}               │
                    │    • ratios: [{Ratio, Actual, Ideal_Min, Ideal_Max, Status}]│
                    │    • thresholds: {param: {very_low_max, low_max, ...}}      │
                    │      (for frontend gauge rendering)                         │
                    └─────────────────────────┬───────────────────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │  STEP 2: NUTRIENT TARGETS  (POST /api/soil/targets)         │
                    │                                                             │
                    │  INPUTS:                                                    │
                    │    • crop_name, yield_target, soil_values                   │
                    │                                                             │
                    │  REFERENCE DATA:                                            │
                    │    • crop_requirements table (nutrient per yield unit)       │
                    │    • soil_sufficiency + crop_sufficiency_overrides           │
                    │    • adjustment_factors table (classification → multiplier) │
                    │    • soil_parameter_map table (nutrient → soil param name)  │
                    │    • ideal_ratios table                                     │
                    │    • agent_crop_overrides (if agent has custom norms)       │
                    │                                                             │
                    │  CALCULATIONS:                                              │
                    │    1. base_req = crop_req_per_unit × yield_target           │
                    │       e.g., Avocado N: 8 kg/t × 15 t = 120 kg/ha           │
                    │                                                             │
                    │    2. Classify each soil param (using crop overrides)       │
                    │       e.g., K = 180 mg/kg → "Optimal" for avocado          │
                    │                                                             │
                    │    3. Look up adjustment factor for classification          │
                    │       Very Low → 1.5x, Low → 1.25x, Optimal → 1.0x,       │
                    │       High → 0.5x, Very High → 0x                          │
                    │                                                             │
                    │    4. adjusted_target = base_req × factor                   │
                    │       e.g., K: 150 kg/ha × 1.0 = 150 kg/ha                │
                    │                                                             │
                    │    5. Evaluate soil ratios against ideal ranges             │
                    │    6. If ratios off-balance, increase deficient nutrient    │
                    │       e.g., Ca:Mg below ideal → boost Ca by up to 2x       │
                    │                                                             │
                    │    7. Final target = adjusted + ratio correction            │
                    │                                                             │
                    │  OUTPUT:                                                    │
                    │    • targets: [{Nutrient, Per_Unit, Base_Req, Classification│
                    │       Factor, Target_kg_ha, Ratio_Adjustment, Final_Target}]│
                    └─────────────────────────┬───────────────────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │  STEP 3: FEEDING PLAN  (POST /api/feeding-plans/generate)   │
                    │                                                             │
                    │  INPUTS:                                                    │
                    │    • nutrient_targets (from Step 2)                         │
                    │    • crop, crop_type, tree_age                              │
                    │                                                             │
                    │  REFERENCE DATA:                                            │
                    │    • crop_growth_stages table (nutrient % per stage)        │
                    │    • perennial_age_factors table (age scaling)              │
                    │                                                             │
                    │  CALCULATIONS:                                              │
                    │    1. If perennial + young tree:                             │
                    │       age_adjusted = target × age_factor                    │
                    │       e.g., 3-yr avo: N = 120 × 0.6 = 72 kg/ha           │
                    │                                                             │
                    │    2. For each growth stage:                                │
                    │       stage_N = total_N × n_pct / 100                      │
                    │       per_app_N = stage_N / num_applications               │
                    │       e.g., Bloom stage 20% of N, 2 apps = 7.2 kg/app     │
                    │                                                             │
                    │    3. Assign months from stage month_start/end              │
                    │                                                             │
                    │  OUTPUT:                                                    │
                    │    • feeding_items: [{stage, month, n_kg_ha, p_kg_ha, ...}] │
                    └─────────────────────────┬───────────────────────────────────┘
                                              │
                                              ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │  STEP 4: PRACTICAL PLAN  (POST /api/feeding-plans/practical)│
                    │                                                             │
                    │  INPUTS:                                                    │
                    │    • ideal feeding items (from Step 3)                      │
                    │    • selected months (user picks when to fertilise)         │
                    │    • selected materials                                     │
                    │                                                             │
                    │  REFERENCE DATA:                                            │
                    │    • materials table (nutrient %, cost per ton)             │
                    │    • material_markups table (agent-specific pricing)         │
                    │                                                             │
                    │  CALCULATIONS:                                              │
                    │    1. Group ideal items into chosen months                  │
                    │    2. For each month: sum NPK requirements                 │
                    │    3. Group by N:K ratio similarity → blend groups          │
                    │    4. For each group: run blend optimizer (scipy linprog)   │
                    │       → find cheapest material mix meeting targets          │
                    │    5. Calculate application rate to deliver exact N         │
                    │    6. Calculate cost per ha                                 │
                    │                                                             │
                    │  OUTPUT:                                                    │
                    │    • practical_apps: [{month, blend_recipe, nutrients,       │
                    │       application_rate, cost_per_ha, cost_per_ton}]         │
                    │    • summary: {total_cost_ha, total_cost_field}             │
                    └─────────────────────────────────────────────────────────────┘
```

---

## 2. BLEND CALCULATOR — Data Flow

```
USER INPUT                    REFERENCE DATA USED              OUTPUT
──────────                    ───────────────────              ──────

NPK targets (% or ratio) ─┐
Batch size ────────────────┤
Min compost % ─────────────┤
Selected materials ────────┤
Blend preferences ─────────┤
                           │
                           ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │  OPTIMIZE  (POST /api/blends/optimize)                      │
                    │                                                             │
                    │  REFERENCE DATA:                                            │
                    │    • materials table (nutrient %, cost per ton)             │
                    │    • material_markups (agent pricing — admin only sees raw) │
                    │                                                             │
                    │  CALCULATIONS (scipy.optimize.linprog):                     │
                    │    1. Build constraint matrix from material nutrient %      │
                    │    2. Objective: minimize compost while meeting NPK targets │
                    │    3. Constraints: min compost %, batch size, non-negative  │
                    │    4. If exact match fails: binary search for closest blend │
                    │    5. Calculate cost per ton from material costs             │
                    │    6. Generate SA notation (e.g., "3:2:1 (25)")             │
                    │    7. Pricing suggestion from comparable saved blends       │
                    │                                                             │
                    │  OUTPUT:                                                    │
                    │    • recipe: [{material, type, kg, pct, cost}]              │
                    │    • nutrients: [{nutrient, target, actual, diff, kg_per_ton}│
                    │    • cost_per_ton, sa_notation, pricing suggestion          │
                    │    • missed_targets (if any nutrients couldn't be met)       │
                    │                                                             │
                    │  VISIBILITY:                                                │
                    │    Admin: full recipe, costs, pricing                       │
                    │    Agent: nutrients only, no recipe/costs                   │
                    └─────────────────────────────────────────────────────────────┘

                    NOTE: Blend calculator does NOT use soil data,
                    classifications, or crop-specific thresholds.
                    It is purely a material optimization engine.
```

---

## 3. SOIL COMPARISON TOOL — Data Flow

```
USER INPUT                    REFERENCE DATA USED              OUTPUT
──────────                    ───────────────────              ──────

Select 2+ analyses ────────┐
                           │
                           ▼
                    ┌─────────────────────────────────────────────────────────────┐
                    │  COMPARE  (POST /api/soil/compare)                          │
                    │                                                             │
                    │  STEP 1: Detect comparison type                             │
                    │    • All same field_id → "timeline" (trends over time)      │
                    │    • Mixed field_ids → "snapshot" (cross-field comparison)  │
                    │                                                             │
                    │  STEP 2: Crop Impact (timeline only)                        │
                    │    REFERENCE DATA:                                          │
                    │      • field_crop_history table (what was planted when)     │
                    │      • crop_requirements table (nutrient per yield unit)    │
                    │      • soil_parameter_map table                            │
                    │    CALCULATION:                                             │
                    │      For each consecutive pair of analyses:                │
                    │      1. Find crops grown between the two dates              │
                    │      2. Sum expected depletion across all crops             │
                    │         depletion = crop_req × yield_target                │
                    │      3. Compare to actual soil value change                │
                    │      4. Interpret: leaching? residual fertiliser?          │
                    │                                                             │
                    │  STEP 3: Recommendations (rule-based)                       │
                    │    INPUTS: sorted analyses + crop impacts                  │
                    │    RULES:                                                  │
                    │      • 3+ declining readings → "declining trend" warning   │
                    │      • Classification improved → success                   │
                    │      • Classification worsened → warning                   │
                    │      • Ratio moved in/out of ideal → flag                  │
                    │      • >40% drop + low uptake → "check leaching"           │
                    │      • Stable within 10% → "program maintaining"           │
                    │                                                             │
                    │  OUTPUT:                                                    │
                    │    • analyses (sorted by date)                              │
                    │    • comparison_type: "timeline" | "snapshot"               │
                    │    • crop_impact: [{crops, nutrients, interpretations}]     │
                    │    • recommendations: [{type, message}]                     │
                    │    • sufficiency_thresholds (for chart rendering)           │
                    │                                                             │
                    │  UI RENDERING:                                              │
                    │    2 analyses → side-by-side table                          │
                    │    3+ timeline → multi-field table + trend line charts      │
                    │    3+ snapshot → multi-field table + grouped bar charts     │
                    └─────────────────────────────────────────────────────────────┘
```

---

## 4. REFERENCE DATA — Source & Usage Map

```
TABLE                          POPULATED BY             USED BY
─────                          ────────────             ───────

crop_requirements              Excel → seed script      • Nutrient targets (soil engine)
(57 crops, NPK per unit)                               • Crop impact (comparison engine)
                                                        • Growth stage calculations
                                                        • Profile crop norm overrides

crop_sufficiency_overrides     SQL seed script          • Classification (soil engine)
(25 crops, pH/P/K/Ca/B/Zn)    (this session)           • Nutrient target adjustment
                                                        • PDF gauge zones
                                                        • Norms snapshot on save

soil_sufficiency               Excel → seed script      • Classification (universal base)
(19 parameters)                                         • PDF gauge zones
                                                        • Comparison chart bands

adjustment_factors             Excel → seed script      • Nutrient target multiplier
(Very Low=1.5x → V.High=0x)                            • Soil engine core calc

ideal_ratios                   Excel → seed script      • Ratio evaluation
(13 ratios with ranges)                                 • Ratio-based target adjustment
                                                        • Comparison recommendations

soil_parameter_map             Excel → seed script      • Map crop nutrient → soil param
(N→"N (total)", P→"P (Bray-1)")                         • Used in targets + crop impact

crop_growth_stages             Python → seed script     • Feeding plan generation
(57 crops, 2-5 stages each)    (this session: +48)      • Seasonal nutrient distribution

perennial_age_factors          Python → seed script     • Young tree scaling
(30 entries, 5 crop groups)                             • Feeding plan generation

materials                      Admin UI                 • Blend optimizer
(raw materials + nutrient %)                            • Practical plan blending
                                                        • Cost calculations

material_markups               Admin UI                 • Agent-specific pricing
                                                        • Selling price suggestions

agent_crop_overrides           Profile page UI          • Per-agent nutrient targets
                                                        • Merged via SQL RPC function

field_crop_history             Client detail UI         • Crop impact calculations
(new this session)             (this session)           • Multi-crop depletion
```

---

## 5. UI PAGE — Feature Map

```
PAGE                    FEATURES                              DATA SOURCES
────                    ────────                              ────────────

/soil                   Soil analysis wizard                  soil_sufficiency
                        • Step 1: Input soil values            crop_sufficiency_overrides
                        • Step 2: Classification + gauges      crop_requirements
                        • Step 3: Nutrient targets             adjustment_factors
                        • Step 4: Feeding plan                 ideal_ratios
                        • Step 5: Practical applications       crop_growth_stages
                        • PDF reports                          perennial_age_factors
                                                               materials

/blends                 Blend calculator                      materials
                        • NPK target input                    material_markups
                        • Optimizer results                   saved blends (pricing)
                        • Recipe + nutrients
                        • Save + PDF

/clients                Client management                     clients, farms, fields
                        • Client list + search                soil_analyses (by client_id)
                        • Client detail (tabs):               blends (by client_id)
                          - Overview (farms/fields/counts)    feeding_plans
                          - Blends (list + detail sheet)      field_crop_history
                          - Soil Analyses (list + detail)
                          - Feeding Plans
                          - Compare (comparison tool)
                        • Field drill-down view
                        • Crop history management

/records                Agent record management               soil_analyses (own)
                        • Search + filter                     blends (own)
                        • Soft delete/restore
                        • PDF download

/profile                Agent profile                         profiles
                        • Contact info edit                   crop_requirements
                        • Crop norm overrides                 agent_crop_overrides

/admin/materials        Material management (admin)           materials
/admin/markups          Agent markup rules (admin)            material_markups
/admin/norms            Crop norms editor (admin)             crop_requirements
                        • Crop requirements                   soil_sufficiency
                        • Soil sufficiency                    adjustment_factors
                        • Adjustment factors                  ideal_ratios
                        • Ideal ratios
/admin/users            User management (admin)               profiles (Supabase Auth)
/admin/audit            Audit log viewer (admin)              audit_log
```

---

## 6. ROLE-BASED VISIBILITY

```
                        ADMIN                           AGENT
                        ─────                           ─────

Blend results           Full recipe + materials         Nutrients only
                        Cost per material               No recipe
                        Cost per ton                    No costs
                        Pricing suggestions             No pricing

Soil analysis           Full data                       Full data
                        Total cost/ha visible           Total cost/ha visible

PDF reports             Recipe table in PDF             No recipe in PDF
                        Price per ton column            Price per ha only
                        Pricing suggestion              No pricing

Client detail           All clients                     Own clients only
Blend detail sheet      Recipe + costs visible          Nutrients only
Records                 All records                     Own records only
Admin pages             Accessible                      Hidden from nav
Crop norms              Edit via admin page             Override via profile
```
