# Programme Builder — Decision Process

The programme builder turns a set of farm blocks (each with a soil sample, crop, and yield target) into a season's worth of application events, then groups those events into blends an operator can actually mix. This doc walks the decisions in the order the engine makes them. File paths are canonical; line numbers rot — grep the symbol.

---

## 1. Target calculation per block

For each nutrient in `{N, P, K, Ca, Mg, S, Fe, B, Mn, Zn, Cu, Mo}` the builder picks one of two paths. Rate-table wins when a cell exists.

### 1a. FERTASA 2-D rate table (preferred path)

`soil_engine.lookup_rate_table()`

If `fertilizer_rate_tables` contains a row matching `(crop, nutrient)` and the lookup context (yield target, soil-test value, optional third-axis filters), the cell's `kg/ha` value is the target — heuristic is skipped for that nutrient.

Snap semantics (conservative, no interpolation):
- **Yield** snaps to the nearest published point; ties break upward (agronomist-conservative: don't under-fertilize). Rows with `yield_max IS NULL` (e.g., "2.5+ t/ha") win outright whenever yield ≥ their `yield_min`.
- **Soil test** falls into a half-open band `[min, max)`; `max IS NULL` = open upper bound.
- **Third-axis filters** (`water_regime`, `clay_pct`, `texture`, `rainfall_mm`, `region`, `prior_crop`): a row's `NULL` on a dimension means "no constraint"; non-NULL requires a context match. When multiple rows match, the most specific wins (highest count of non-NULL filters).

Every hit carries provenance (`FERTASA Handbook 5.4.3.1.2`, year, footnote) through to the programme summary.

Coverage today: wheat P (dryland, 16 cells). Queued: wheat K, potato N/P/K, canola N. Fallback (below) handles everything else.

### 1b. Heuristic: removal × yield × sufficiency factor (fallback)

`soil_engine.calculate_nutrient_targets()`

```
base_req      = crop_requirements.removal_per_t × yield_target
classification = classify_soil_value(lab_value, thresholds, crop_overrides)
factor        = adjustment_factors[classification, nutrient_group]
target        = base_req × factor
```

Thresholds come from `soil_sufficiency` with optional `crop_sufficiency_overrides`. Adjustment factors are currently unsourced heuristics (1.5/1.25/1.0/0.5/0.0) — flagged as a credibility gap; the FERTASA rate-table path is the long-term replacement where data exists.

### 1c. Ratio adjustments (layered on top of 1a or 1b)

`soil_engine.adjust_targets_for_ratios()`

After targets are set, soil-nutrient ratios are checked against `ideal_ratios`:
- **Ca:Mg, Ca:K, Mg:K** — prefer reducing the over-supplied cation; only increase the deficient one if it isn't already High/Very High.
- **P:Zn** — always boost Zn (physical uptake blockage, not a balance choice).
- **N:S** — never reduce N; boost S to match.
- **K:Na** — always boost K when Na is displacing it.
- **Base saturations (Ca / K / Mg)** — CEC-weighted top-ups.

N is never ratio-reduced (not bankable — excess leaches). Total reductions are capped at 50% of the sufficiency target as a safety net. Sufficiency-already-penalised nutrients aren't double-punished.

### 1d. Corrective build-up (linked soil analysis)

`soil_corrections.calculate_corrective_targets()`

For P/K/Ca/Mg that are *below* sufficiency, an annual build-up amount is added on top of maintenance. This runs once, using the soil analysis linked to the block.

---

## 2. Seasonal splitting per block

`feeding_engine.generate_feeding_plan()`

Takes the per-nutrient total and splits it across the crop's `crop_growth_stages` rows by the stage's `n_pct / p_pct / k_pct / …` columns. Each stage declares:
- month window (`month_start`, `month_end`),
- number of applications within the stage,
- default application method (broadcast, side-dress, fertigation, foliar).

**Perennial age factor** (if applicable): a tree below full production gets its N/P/K/general targets scaled by `perennial_age_factors` (e.g., year-1 mac at 0.3× adult).

**Application-method validation** — `feeding_engine.validate_methods()` filters the stage's proposed method down to what's actually permitted:
1. `crop_application_methods` — what methods are agronomically valid for this crop×nutrient×stage.
2. Field-level `accepted_methods` — what the farmer's kit can do.
3. Field-level `irrigation_type` + `fertigation_months` — fertigation only lands in months the infrastructure supports; otherwise falls back to broadcast.

**Foliar items** are enriched with product recommendations from the foliar protocol catalog (`foliar_engine`) — the LP doesn't formulate foliar, the product catalog does.

---

## 3. Multi-sample aggregation (when a block has multiple soil samples)

`aggregation.aggregate_samples()`

Samples within a block are aggregated to a single composite value using one of three strategies (`weight_strategy`): area-weighted, equal-weighted, or depth-weighted. The composite feeds the target-calc pipeline — all downstream logic sees one value per block.

**Heterogeneity flag** (`_classify_heterogeneity`) — per-nutrient coefficient of variation across samples is checked against Wilding (1985) bands:
- `ok` — below the warn threshold,
- `warn` — mild variance (e.g., P CV ≥ 35%),
- `split` — variance high enough to recommend splitting the block (e.g., P CV ≥ 50%).

This surfaces in the programme summary; it doesn't auto-split blocks.

---

## 4. Grouping blocks into blends

`programme_engine.build_programme()`

Each block now has a feeding-plan item list. The engine:
1. Sums the N/P/K per block (excluding foliar items — those use packaged products).
2. Builds an NPK profile tuple per block.
3. Groups blocks with similar profiles into `blend_groups` (letter-labelled A, B, …). Blocks with incompatible profiles get their own group.
4. Runs the blend optimizer **per group** using materials filtered by application method (dry methods require `liquid_compatible=False`; fertigation requires `liquid_compatible=True`).

One output blend per group per application event (e.g., "Group A pre-plant broadcast", "Group A topdress fertigation"). The operator mixes one blend and applies it across every block in the group.

---

## 5. What the builder explicitly does NOT consider (known gaps)

- **Leaf analysis feedback.** `fertasa_leaf_norms` grades leaf samples for display, but `programme_engine` doesn't read the classification to adjust next-season targets. Gap flagged in the project memory.
- **Temporal / phenological windows.** `crop_application_windows` schema exists (migration 046) but no seed data and no engine enforcement yet. Mac N at the wrong month, dry-bean N at flowering — currently allowed.
- **Prior season's actual applications.** The season tracker is orthogonal; it records what happened but doesn't feed into the next programme's target calc.
- **Weather / irrigation volume forecasting.** The builder assumes the stated yield target is achievable; it doesn't downgrade for drought years or adjust N for rainfall.
- **Cost optimization across groups.** Blends are optimized within a group for nutrient accuracy; there's no cross-group cost minimization.

---

## 6. Input contract summary

| Input | Source | Used for |
|---|---|---|
| Crop name | block | lookup into `crop_requirements`, `crop_growth_stages`, `crop_application_methods`, `fertilizer_rate_tables` |
| Yield target + unit | block | base-req multiplication or rate-table axis |
| Tree age | block | perennial age factor |
| Soil values | block's linked `soil_analyses` | classification, ratios, rate-table lookup, corrective build-up |
| Field area (ha) | block | cost totals |
| Field methods / irrigation | `fields` | method validation, fertigation gating |
| Farmer-accepted methods | `fields.accepted_methods` | method validation |
| Water regime | context default `dryland`; per-request override TBD | rate-table third-axis filter |

---

## 7. Output contract summary

| Output | Shape | Downstream consumer |
|---|---|---|
| `nutrient_targets` per block | `[{Nutrient, Target_kg_ha, Source, Rate_Table_Hit, Classification, Factor, ...}]` | programme summary, audit trail, next season's comparison |
| `feeding_plan` per block | `[{stage, month_target, method, n_kg_ha, p_kg_ha, k_kg_ha, method_note?, ...}]` | blend grouping, delivery calendar |
| `blend_groups` | `{A: {blocks, total_area, applications: [{method, month, blend_formula, ...}]}}` | operator mix sheet, cost quotation |
| `heterogeneity` | per-nutrient CV + warn/split flag | agronomist review |

---

## Key files

```
sapling-api/app/services/
  soil_engine.py          target calculation + rate-table lookup + ratio logic
  soil_corrections.py     corrective build-up for deficient soils
  feeding_engine.py       seasonal splitting, age factors, method validation
  foliar_engine.py        foliar product recommendations
  aggregation.py          multi-sample → composite
  programme_engine.py     orchestration, heterogeneity flag, blend grouping

sapling-api/app/routers/soil.py     API endpoints that assemble the inputs
```

## Data tables (reference)

```
crop_requirements              removal per tonne per nutrient + crop_type
crop_growth_stages             stage sequence + percent splits + method + months
crop_application_methods       valid (crop, nutrient, stage, method) combos
crop_sufficiency_overrides     crop-specific soil thresholds
soil_sufficiency               universal soil thresholds
adjustment_factors             sufficiency class → multiplier (heuristic, flagged)
ideal_ratios                   Ca:Mg / P:Zn / etc. bands
perennial_age_factors          tree-age scaling
fertasa_leaf_norms             leaf-sample grading (display only today)
fertilizer_rate_tables         2-D FERTASA cells (wheat P live; expanding)
crop_application_windows       temporal rules (schema only, not wired)
foliar_protocols / _products   foliar catalog
materials                      blend optimizer inputs
```
