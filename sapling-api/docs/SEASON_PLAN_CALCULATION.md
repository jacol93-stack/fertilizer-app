# Season Plan Calculation — How It Works

This document describes how Sapling calculates fertilizer recommendations, from raw soil analysis through to corrective action timelines.

---

## Overview

The calculation pipeline has four layers, each building on the previous:

```
1. Sufficiency Assessment     → What does the crop need? What does the soil already have?
2. Ratio Adjustments          → Are nutrients in balance? Adjust within sufficiency constraints
3. Pre-season Soil Treatment  → pH correction, Na displacement, organic matter
4. Corrective Action Plan     → Long-term soil improvement timelines
```

---

## 1. Sufficiency Assessment

**File:** `soil_engine.py` → `calculate_nutrient_targets()`

### Step 1: Base Requirement
For each of the 12 nutrients (N, P, K, Ca, Mg, S, Fe, B, Mn, Zn, Mo, Cu):

```
base_req = per_unit_requirement × yield_target
```

Example: Maize N at 0.022 kg/kg × 8000 kg/ha yield = 176 kg N/ha

### Step 2: Soil Classification
Each soil test value is classified against sufficiency thresholds (from the `soil_sufficiency` table, with optional crop-specific overrides from `crop_sufficiency_overrides`):

| Range | Classification |
|---|---|
| 0 → very_low_max | Very Low |
| very_low_max → low_max | Low |
| low_max → optimal_max | Optimal |
| optimal_max → high_max | High |
| above high_max | Very High |

### Step 3: Adjustment Factor (Nutrient-Group-Specific)
The base requirement is multiplied by a factor from the `adjustment_factors` table. Factors are now **nutrient-group-specific**:

| Group | Nutrients | Very Low | Low | Optimal | High | Very High | Rationale |
|---|---|---|---|---|---|---|---|
| **N** | N | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | Not bankable — always supply full crop demand |
| **P** | P | 1.5 | 1.25 | 1.0 | 0.75 | 0.5 | Draws down very slowly, conservative cuts only |
| **cations** | K, Ca, Mg, S | 1.5 | 1.25 | 1.0 | 0.5 | 0.25 | Standard response to soil levels |
| **micro** | Fe, B, Mn, Zn, Mo, Cu | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | Tiny quantities, not worth cutting |

```
target_kg_ha = base_req × factor
```

### Why N is never reduced
Soil N tests do not reliably predict plant-available N during the growing season. N is mobile, transforms rapidly (mineralisation, nitrification, denitrification, leaching), and crops need it supplied fresh every season regardless of soil test levels. Cutting N based on a soil test risks yield loss with no meaningful soil draw-down benefit.

### Why P is conservative
P draws down very slowly in soil — typically 2-4 mg/kg per year under crop removal. Aggressive cuts (e.g., factor = 0 at Very High) would deny the crop P for many seasons while the soil test barely moves. A factor of 0.5 at Very High still supplies half the crop's need while allowing gradual draw-down.

---

## 2. Ratio Adjustments

**File:** `soil_engine.py` → `adjust_targets_for_ratios()`

After sufficiency targets are calculated, the engine checks nutrient ratios against ideal ranges (from the `ideal_ratios` table). The approach is **sufficiency-first**:

### Principles
1. **Prefer reducing the over-supplied nutrient** rather than increasing the deficient one
2. **Never increase a nutrient already classified as High/Very High** (except P:Zn — see below)
3. **Never reduce N** — it's not bankable, always needs full supply
4. If neither action is possible, generate a **warning** for the agronomist

### Ratio Handlers

| Ratio | When Off | Primary Action | Fallback |
|---|---|---|---|
| **Ca:Mg** | Below ideal | Reduce Mg | Increase Ca (if not High) |
| **Ca:Mg** | Above ideal | Reduce Ca | Increase Mg (if not High) |
| **Ca:K** | Below ideal | Reduce K | Increase Ca (if not High) |
| **Mg:K** | Below ideal | Reduce K | Increase Mg (if not High) |
| **P:Zn** | Above ideal | **Always boost Zn** | — |
| **N:S** | Above ideal | Increase S | Warn (never reduce N) |
| **K:Na** | Below ideal | Always increase K | — (Na displacement) |
| **Ca base sat.** | Below ideal | Increase Ca (if not High) | Warn + suggest lime |
| **K base sat.** | Below ideal | Increase K (if not High) | — |
| **Mg base sat.** | Below ideal | Increase Mg (if not High) | — |

### Why P:Zn is an exception
High soil P physically blocks Zn uptake at the root level — it's a direct physiological antagonism, not just a ratio on paper. Even if soil Zn tests as "sufficient," the plant may not access it when P is very high. This is the one case where boosting the "low" side of a ratio is justified regardless of sufficiency status.

### Exact Calculations
Ratio adjustments calculate the exact kg/ha change needed to move the application ratio toward the ideal midpoint, rather than using arbitrary percentages. All adjustments are capped (never reduce by more than 50%, never increase by more than 2x) to prevent extreme swings.

---

## 3. Pre-season Soil Treatment

**File:** `soil_corrections.py`

Three pre-season corrections are evaluated independently of the nutrient targets:

### 3a. Lime (pH Correction)

**Trigger:** pH (H2O) more than 0.2 units below target

| Crop Type | Target pH |
|---|---|
| Standard crops | 6.0 |
| Acid-loving (blueberry, tea, pineapple, rooibos) | 5.0 |

**Calculation:**
```
lime_t_ha = pH_deficit × buffer_factor
```

Buffer factor is based on clay %:

| Clay % | Buffer (t lime per pH unit) |
|---|---|
| <15% (sandy) | 1.5 |
| 15-25% (sandy loam) | 2.5 |
| 25-35% (loam) | 3.5 |
| 35-45% (clay loam) | 4.5 |
| >45% (clay) | 5.5 |

Additional +0.5 if organic carbon > 2% (higher buffer capacity).

**Lime type selection:**
- Dolomitic lime if Mg is also Low/Very Low (supplies Mg as well)
- Calcitic lime otherwise

### 3b. Gypsum (Na Displacement)

**Trigger:** Na classification is High or Very High

```
gypsum_kg_ha = Na_excess × gypsum_factor
where Na_excess = Na_mg_kg - 50 (target)
      gypsum_factor = 4 + (clay% / 20)
```

Not recommended if calculated rate < 100 kg/ha (below practical threshold).

### 3c. Organic Carbon

**Trigger:** Org C classification is Low or Very Low

| Classification | Minimum compost % in blend | Severity |
|---|---|---|
| Very Low | 60% | Critical |
| Low | 55% | Important |

This is a flag/recommendation, not a calculated rate — it informs the blend optimizer to include compost.

---

## 4. Corrective Action Plan (Soil Improvement)

**File:** `soil_corrections.py` → `calculate_corrective_targets()`

This is a **separate output** from the season recommendation. It shows how long it will take to bring soil levels to optimal, given the current recommendation strategy.

### Required Data
- CEC (cmol/kg) — determines build-up efficiency
- Clay % — already used for lime calculation
- If either is missing, the system shows a banner: *"Soil correction plan unavailable — missing CEC, Clay from soil analysis"*

### Build-up (nutrients below optimal)

Target: midpoint of optimal range

```
total_kg_needed = gap_mg_kg × buildup_factor
seasons = ceil(total_kg_needed / max_per_season)
annual_rate = total_kg_needed / seasons
```

Build-up factors (kg element per ha per 1 mg/kg soil test rise):

| Nutrient | Sandy (CEC <6) | Medium (CEC 6-15) | Clay (CEC >15) |
|---|---|---|---|
| P (Bray-1) | 5 | 8 | 15 |
| K | 2.5 | 4 | 6.5 |
| Ca | 7 | 10 | 16 |
| Mg | 2.5 | 4 | 6.5 |

Per-season caps (to prevent fixation losses and luxury consumption):
- P: 50 kg/ha
- K: 120 kg/ha
- Ca: 200 kg/ha
- Mg: 60 kg/ha

### Draw-down (nutrients above optimal)

Target: top of optimal range. No extra fertilizer needed — the reduced application rate (from sufficiency factors) allows crop removal to draw down the soil bank.

Approximate draw-down rates (mg/kg decline per season):
- P: ~3 mg/kg/season (very slow — strongly buffered)
- K: ~8 mg/kg/season (moderate)
- Ca: ~5 mg/kg/season (moderate)
- Mg: ~5 mg/kg/season (moderate)

### What this means for the user
The correction plan tells the agronomist: "At current application rates, here's how long it will take for this soil to reach optimal." It's informational — the system calculates the timeline, the user doesn't choose it.

---

## Calculation Flow Summary

```
Soil Lab Values + Crop + Yield Target
         │
         ▼
┌─────────────────────────────┐
│  1. SUFFICIENCY ASSESSMENT  │
│  base_req × group_factor    │
│  (N=1.0, P=conservative,   │
│   cations=standard,         │
│   micro=1.0)                │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│  2. RATIO ADJUSTMENTS       │
│  Sufficiency-first:         │
│  - Reduce oversupplied      │
│  - Never increase if High   │
│  - Never reduce N           │
│  - P:Zn always boosts Zn    │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│  3. PRE-SEASON TREATMENT    │
│  - Lime (pH → 6.0)          │
│  - Gypsum (Na displacement) │
│  - Org C flag (compost %)   │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│  4. CORRECTIVE PLAN         │
│  - Build-up timelines       │
│  - Draw-down estimates      │
│  - Missing data banner      │
│  (informational, not        │
│   user-selectable)          │
└─────────────────────────────┘
```

---

## Key Design Decisions

1. **Sufficiency drives the recommendation.** Ratios are secondary flags, not prescriptive targets. Research (Kopittke & Menzies 2007, FSSA Handbook) shows correcting ratios when individual nutrients are sufficient produces no yield benefit.

2. **N is sacred.** Never reduced by any mechanism — sufficiency factors, ratio adjustments, or draw-down. Always supply full crop demand.

3. **P is treated conservatively.** Slow soil draw-down (years to decades) means aggressive cuts deny the crop without meaningfully improving soil levels.

4. **The system decides timelines, not the user.** Soil properties (CEC, clay, fixation capacity) and per-season caps determine how long correction takes. This removes guesswork and prevents agronomically unsound acceleration.

5. **Missing data is flagged, not assumed.** When CEC or Clay% is absent, the system says so rather than guessing — corrective plans require these parameters.
