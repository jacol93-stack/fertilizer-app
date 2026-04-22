# Data Audit & Seed Plan (Track A)

The premise: the programme builder's structure is sound; its numbers are a mix of FERTASA-direct and unsourced heuristic. This plan orders the sourcing work by credibility-per-hour, names a specific source for every row, and keeps gaps explicit.

Every seeded row carries `source`, `source_section`, `source_year` — so an auditor can trace any recommendation back to the paper/handbook it came from.

---

## Source trust tiers

We cite against these. A number only graduates into the calculator when it's Tier 1-2. Tier 3-4 are corroborating; Tier 5-6 are for calibration/overrides explicitly marked as such.

| Tier | Source class | Examples | Use for |
|---|---|---|---|
| **1** | SA industry-body standard | FERTASA, SASRI FAS, CRI FertMap, Hortgro Science, Vinpro/Winetech, SAMAC, SAAGA, Grain SA, Potatoes SA | Primary citation — safe to present to an accredited agronomist |
| **2** | Peer-reviewed SA research | ARC (SGI, GCI, TSC, Infruitec-Nietvoorbij, ISCW, VOPI), Stellenbosch, UP, UFS, UKZN; SA Journal of Plant and Soil, SAJEV, SAJCS | Acceptable citation, especially where Tier 1 is silent |
| **3** | International reference (SA-applicable) | IPNI Better Crops, IPI, FAO commodity guides, Cornell / UC Davis / UF-IFAS, Australian GRDC | Acceptable with an "SA conditions not verified" note |
| **4** | Commercial technical bulletins | Omnia, Nulandis, Kynoch, Yara, Haifa, K+S | Corroborating only — never the sole citation |
| **5** | Lab interpretation guides | Bemlab, Elsenburg, Omnia Lab, NVIRO | Useful for soil-test / leaf interpretation thresholds |
| **6** | Agronomist rule capture | The user's own expertise, per-client regional calibrations | Explicit overrides, shown in the UI as "custom rule" |

---

## Status — what got seeded 2026-04-20 → 2026-04-22

**24 migrations (046-069), 935 cells across 32 crops / 87 nutrient slots.** 455/455 tests pass on every commit.

**2026-04-22 afternoon — "provenance + honest heuristic elimination" session:** four migrations shipped (066, 067, 068, 069) targeting the north-star goal of zero `Source = "removal × factor (heuristic)"` rows in calculator output. Net effect: Ca/Mg heuristic eliminated for ~35 mainstream crops; `adjustment_factors` and `ideal_ratios` now carry full provenance; wheat N + asparagus K + canola S + lucerne S seeded. Remaining heuristic-path rows are now mostly micros (task #13, migration 070+) and a few S crops without rate tables.

**2026-04-22 — migration 069** (6 cells): sulphur rate tables.
- Canola S (5.5.1.5): 3 soil-test bands with Ca-phosphate extraction (<6 / 7-12 / >12 mg/kg → 15-20 / 15 / 10 kg S/ha). Canola S demand ~4× wheat per handbook prose.
- Lucerne S (5.12.2.7): 3 yield bands (4-8 / 8-16 / 16+ t DM/ha → 25 / 30 / 40 kg S/ha/yr). Yield-band mapping from the lucerne P/K axis in migration 059; annual-maintenance mode; one-off sulphate-sulphur build-up option kept in source_note.
- Deferred: wheat S (5.4.3.2.3 image 484 — needs OCR), tobacco S (excess-S quality constraint, not a rate), dry bean / groundnut / soya S (carrier-handled, no distinct FERTASA recommendation).

**2026-04-22 — migration 068** (Ca/Mg cation-ratio engine path — **BIG LEVER**):
- New function `calculate_cation_ratio_target()` computes Ca/Mg targets from FERTASA 5.2.2 base-saturation math (shortfall × CEC × equivalent weight × 2000 t/ha soil mass) instead of heuristic `removal × factor`. Applies to ~35 mainstream crops; skipped for 5 acid-loving crops via the new `crop_calc_flags` table (Blueberry, Raspberry, Blackberry, Rooibos, Honeybush) and for CEC < 3 cmol/kg sandy soils.
- Preemption order per nutrient: rate-table > ratio-path (Ca/Mg only) > heuristic. Each target now carries a `Calc_Path` field so UI can distinguish FERTASA-direct from Tier-6 fallback.
- `ideal_ratios` gained provenance columns; 11 of 13 rows are Tier 1 (FERTASA 5.2.2 direct). `adjust_targets_for_ratios` skips base-sat corrections on Ca/Mg that already came from the ratio path to avoid double-counting.
- Defaults: 2000 t/ha soil mass (~15 cm × 1.33 g/cm³ — matches pre-existing convention in the same function); 2-season split correction; midpoint ideal base sat (Ca 65%, Mg 15%).

**2026-04-22 — migration 067** (adjustment_factors provenance):
- Added `source` / `source_section` / `source_year` / `source_note` / `tier` columns to `adjustment_factors`. Backfilled all 20 rows as **tier=6 (implementer convention)** with per-nutrient-group rationale notes. The 1.5 / 1.25 / 0.75 shape follows the FSSA/FERTASA drawdown principle from FERTASA 5.1 prose — but the specific numeric factors aren't handbook-published. This is now visibly labelled on every heuristic-path recommendation.
- Engine: heuristic-path results carry `Tier` + `Adjustment_Factor_Source` dict so UI can surface provenance per nutrient. No calc values change; the honesty is on the label only.

**2026-04-22 — migration 066** (cross-cutting texture work, 27 cells):
- Wheat N Western Cape (5.4.3.2.2): 15 cells = 5 yield bands × 3 texture bands (sandy / loam / clayey). FERTASA prose multipliers (±10-15%) applied to the published N1 at midpoint factors (1.125 / 0.875); full envelope noted in source_note for auditors.
- Asparagus K (5.6.3.3): 12 cells = 4 soil-K bands × (establishment sand + establishment clay + established-annual). Uses `crop_cycle` ('plant' / 'ratoon') per the convention established in migration 063 for blueberries.
- Engine: `Matched_Band` extended to include clay_pct_min/max, texture, region, water_regime, crop_cycle for richer audit trail in UI output.

**Prior sessions (2026-04-20):**

| Crop | Nutrients seeded | Source | Tier |
|---|---|---|:---:|
| Wheat | P, K | FERTASA 5.4.3 | 1 |
| Maize | N | ARC-GCI MIG 2017 | 2 |
| Sugarcane | N + leaf norms + S/Ca/Mg soil overrides | SASRI IS 7.2 / 7.6 / 7.7 / 7.15 | 1 |
| Potato | N, P | FERTASA 5.6.2 | 1 |
| Soybean | P, K | FERTASA 5.5.5 | 1 |
| Sunflower | N, P, K | FERTASA 5.5.6 | 1 |
| Canola | N | FERTASA 5.5.1 | 1 |
| Lucerne | P, K, B | FERTASA 5.12.2 | 1 |
| Cotton | N, P, K | FERTASA 5.9 | 1 |
| Bean (Dry) | N, P, K | FERTASA 5.5.2 | 1 |
| Groundnut | N (not-inoculated) | FERTASA 5.5.3 | 1 |
| Banana | N, P, K | FERTASA 5.7.2 | 1 |
| Sweetcorn | N, P, K | FERTASA 5.4.5 | 1 |
| Tobacco (flue-cured) | N, P, K | FERTASA 5.11 | 1 |
| Macadamia | N, P, K, Zn, B + K/mineral-N soil overrides | SAMAC Schoeman 2021 | 1 |
| Avocado | leaf norms deficient/excess bounds | NZAGA 2008 ("Avocado Book" lineage) | 1 |
| **16 vegetable crops** | N, P, K each | FERTASA 5.6.1 | 1 |

Vegetable crops in the 5.6.1 block: Beetroot, Brinjal, Cabbage crops, Carrot, Chillies, Garlic, Gem squash, Green beans, Green peas, Lettuce, Onion, Pumpkin crops, Red/green peppers, Strawberry, Sweet melon, Sweet potato.

**Tier split: 90% Tier 1, 10% Tier 2 (ARC-GCI maize).**

Plus schema extensions: `fertilizer_rate_tables` (migration 046), `crop_application_windows` (046, schema only), `crop_cycle` + `soil_organic_matter_pct_min/max` columns (052 for sugarcane). Plus liquid-optimizer MILP incompatibility fix (separate from the data work but shipped the same day).

---

## Key decisions made along the way

1. **FERTASA electronic handbook is accessible** via user's session cookie — a full re-scrape pulled all 26 crop sections plus 23 image-tables. The R850 physical handbook is **not** a priority, despite the initial audit (when we thought the electronic was gated). They contain the same content; no known edge cases worth R850 have surfaced.

2. **FERTASA 5.4.4 (Maize) is a dead link** in the electronic reader — it just points to an "OLD GUIDELINES" PDF. The authoritative SA maize source is the free **ARC-GCI Maize Information Guide 2017**, which traces to the same Bloem 2002 research FERTASA cites in its abbreviated subset. Seeded via image-OCR (PDF → PNG → tesseract → manual parse). Two cells flagged as possible OCR errors in the migration's source_note.

3. **SASRI P and K are threshold-based, not 2-D rate tables** — IS 7.4 and 7.5 prescribe "apply enough to raise soil test to the soil-type-specific target," with the target values living inside the paid FAS lab report. Seeded sugarcane S/Ca/Mg soil thresholds as `crop_sufficiency_overrides`; P/K remain on the heuristic path for that crop.

4. **Image-based OCR works for slide-format PDFs** where `pdftotext` fails (column collapse). Used successfully on ARC-GCI MIG 2017 (232 pages) and SAMAC Schoeman decks. Pipeline: `pdftoppm -r 250 -png` → `tesseract` → combined text.

5. **Copyright-aware data handling** — SASRI Information Sheets carry an explicit no-redistribution notice; numerical thresholds (facts, not expression) are seeded with citations, but the source PDFs are `.gitignore`'d. Same pattern applies to any future Raath 2021 content.

---

## Remaining paid-reference decision

**Only one purchase currently justified**:

- **Raath 2021 "Handbook for Fertilisation of Citrus in SA" — R250.** Citrus is a massive SA export industry with zero usable data in FERTASA (only young-tree per-tree rates, defers to leaf analysis for bearing). The Raath handbook is confirmed to contain leaf norms, soil/leaf/water interpretation, bearing vs non-bearing rates, and deficiency symptoms. One-time purchase, authoritative SA source. Buy.

**Skipped on reconsideration**:

- ~~FERTASA physical handbook (R850)~~ — electronic access makes this redundant.
- ~~SATI "Fertilisation Guidelines for the Table Grape Industry" (R280)~~ — the user elected to skip both wine grape and table grape work for now.

**Unchanged — do not subscribe**:
- CRI FertMap / CGA membership / Hortgro Production Guide / Vinpro membership / SAMAC Production Planner. Content either unverified behind the paywall OR duplicates free sources (NZAGA 2008, Schoeman decks, Beyers 1958 Stellenbosch thesis, avocadosource.com mirror).

---

## What's left after today

### Source-limited (needs external data)

| Crop | Status | Next step |
|---|---|---|
| **Citrus (all types)** | FERTASA has only per-tree young-tree rates; no 2-D rate tables | Buy Raath 2021 (R250); extract bearing-orchard data |
| **Apple / pear / stone fruit** | Beyers 1958 Stellenbosch thesis has SA leaf norms (free); Hortgro content mostly postharvest, not nutrition | Extract Beyers 1958 leaf norms manually (no paywall gate; just extraction work) |
| **Wine + table grape** | Skipped by decision (2026-04-20) | N/A |
| **Pecan** | FERTASA has per-tree rates only; SA Pecan Producers Assoc. is thin | Low priority; ARC-TSC fallback if demand exists |
| **Mango / litchi / guava** | No FERTASA; Subtrop publishes only training-level content | FERTASA-only, flagged in programme output |
| **Berries (blueberry/strawberry/raspberry)** | Strawberry seeded in veg block; others thin | IPI / IPNI Tier-3 overlay if pushed |
| **Olive** | No SA industry rate tables; UC Davis (Tier 3) transferable | Optional |
| **Rooibos / coffee / tea** | Niche; rooibos legume schema breaks n_pct=0 convention (already flagged) | Optional |

### Schema-limited (data is there; engine/schema needs work)

These are NOT source problems — the data is in our research folder or already cited. They need engine or schema changes to unblock:

| Item | Blocker |
|---|---|
| Macadamia cultivar-split leaf norms | Schoeman deck's 3-column comparison table had column headers cut in OCR; verify attribution before overwriting FERTASA rows |
| Macadamia P threshold by clay texture (SAMAC young-tree deck) | `crop_sufficiency_overrides` doesn't split on texture; small schema extension needed |
| Macadamia B foliar protocol | No foliar_protocol schema for nut crops yet |
| Tomato 5.6.4 rate tables | Scraper mangled column layout; re-scrape with colspan/rowspan handling OR image-OCR |
| Groundnut inoculation axis | No `inoculation` column in rate_table schema; currently seed not-inoculated case only |
| Tobacco air-cured / dark / burley | Removal table gives them different N requirements; no rate-table calibration in FERTASA though. May need `tobacco_variant` column or sub-crop entries |
| Lucerne K-%-of-CEC alternative table | No `cec_pct_min/max` columns; alternative K table deferred |
| Lucerne leaf norms by growth stage (EB / B / F) | Complex 5-band × 3-stage × 14-element structure; schema decision needed |
| Wheat S for Western Cape (FERTASA image 484) | Simple 3-row table; easy seed, just hasn't been done |

### Cross-cutting data (Track A residual)

Not per-crop; relevant to many crops:

- ~~**Soil-type responsiveness for the unsourced adjustment factors**~~ — **reframed and partially resolved 2026-04-22**. The 1.5/1.25/1.0/0.5/0.0 multipliers in `adjustment_factors` are classification (soil-test buildup/drawdown) multipliers, not texture multipliers — they compose with texture-aware rate tables rather than being replaced by them. FERTASA's texture adjustments are now handled in one of two ways:
  - **Tabular-by-texture** — encoded directly in `fertilizer_rate_tables` via the `clay_pct_min/max` / `texture` / `crop_cycle` columns (already in the 046 schema). Seeded for potato N (049), wheat K (048), banana K (060), dry bean N (058), lucerne P (059), tobacco N (060), and now wheat N + asparagus K (066).
  - **Prose multiplier** — applied to a base rate at migration time (wheat N, 066). Stored as three texture-banded rows (sandy / loam / clayey) against FERTASA's published N1, with the ±15% envelope in source_note.

  The remaining per-crop texture prose (conditional / absolute adjustments — groundnut +10-25 kg N/ha on very sandy, soya +10-20 kg N/ha on <10% clay, sweetcorn +10% on sandy under heavy rain, lucerne +100 kg K/ha on <15% clay establishment) is too conditional to encode mechanically. Deferred to per-crop UI flags rather than calc-engine logic.

- **Soil-N mineralization credit by texture** (cotton 5.9.3: sand 60 / loam 120 / clay 160 kg N/ha mineralized). FERTASA applies this as the explicit "A − (B+C+D)" N subtraction method at section 5.9. Most other FERTASA rate tables are already calibrated net of mineralization, so a universal N-supply credit would double-count. Needs a "crops-that-use-subtraction-method" flag before seeding — architectural decision, deferred.

- **Method efficiency multipliers** — band vs broadcast vs fertigation vs foliar efficiency factors. Data exists in FERTASA / IPNI 4R prose; schema extension needed.
- **Application windows seed** — schema already exists (migration 046 `crop_application_windows`); ~15 concrete rules ready to seed (SAMAC Mar-Oct N, dry bean no N at flowering, wheat N split windows, etc.).
- **Leaf → next-season feed-forward curves** — biggest logic+data hybrid. Design decision needed first (additive vs multiplicative) before sourcing makes sense.

---

## Recommended order from here

1. **Buy Raath 2021 (R250).** Only paid item worth pursuing. Unlocks the biggest single untouched commercial crop (citrus).
2. **Deciduous fruit leaf norms from Beyers 1958.** Free Stellenbosch thesis, zero gate, SA-specific data for apple/pear/peach/apricot/plum. Extraction work only.
3. **Cross-cutting data ahead of new crops.** Soil-type responsiveness + method efficiency + application windows enforcement unlocks every crop at once, rather than adding the 5th banana decimal place. This is where the credibility-per-hour ratio is highest going forward.
4. **Schema-limited items** in the table above, prioritised by how often the gap surfaces in real programmes.
5. **Specialty / perennial long tail** as demand warrants — not blocking anyone now.

---

## What not to do

- Don't synthesize a "SA-wide" number when regional tables exist. If FERTASA publishes Western Cape and Free State separately, seed both with region filters. (Applied today for wheat, not yet for potato.)
- Don't backfill a Tier-3 international number into a Tier-1 slot when the SA-specific source is just behind a paywall. The Raath handbook is worth R250; anything Tier-3 should stay labeled as Tier-3.
- Don't let commercial Tier-4 bulletins drive the primary recommendation — corroboration only.
- Don't mix researched-heuristic values into the same table as FERTASA-direct without a source-tier distinction in the row. Currently every seeded rate-table row carries full provenance; keep that discipline.
