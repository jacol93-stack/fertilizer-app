# Data Audit & Seed Plan (Track A)

The premise: the programme builder's structure is sound; its numbers are a mix of FERTASA-direct and unsourced heuristic. This plan orders the sourcing work by credibility-per-hour, names a specific source for every row, and keeps gaps explicit.

Every seeded row should carry `source`, `source_section`, `source_year`, `source_tier` — so an auditor can trace any recommendation back to the paper/handbook it came from.

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

## Phase 0 — This weekend (hours)

All data already in `sapling-api/data/fertasa_handbook/*.json`. Zero-research, pure transposition.

| Crop | Data | Source (Tier 1) | Effort | Nutrient impact |
|---|---|---|---|---|
| Wheat | K table (yield × K-status × texture filter clay ≥35%) | FERTASA 5.4.3.1.3 | 1 hr | Covers WC + Free State K |
| Potato | N dryland (clay × yield), N irrigation (clay × yield), P (6 soil-P × 8 yield), K | FERTASA 5.6.2 | 3 hr | All four NPK matrices |
| Canola | N by region × rainfall × prior_crop | FERTASA 5.5.1 image 501 | 1 hr | 7 regional rows |
| Maize | Re-scrape section 5.4.4 (current capture is OLD GUIDELINES placeholder) | FERTASA 5.4.4 or newer edition | 2-4 hr | Fixes the single biggest SA field crop |

**Delivery**: migrations 048-051, similar pattern to 047.

---

## Phase 1 — Field crops full coverage (2-3 days)

FERTASA covers the basics. Grain SA production manuals (freely downloadable, industry-standard) fill yield-target × region × tillage splits that FERTASA glosses.

| Crop | Primary source | Secondary source | Data needed | Notes |
|---|---|---|---|---|
| Maize | Grain SA "Maize Producers' Manual" (T1) | ARC-GCI Maize Information Guide (T2) | N × texture × yield, P × soil-P × yield, K × soil-K, Zn/S guidelines | Grain SA publishes per-region tables; ARC-GCI publishes physiological curves |
| Wheat | FERTASA 5.4.3 (have) + ARC-SGI manuals (T1) | Grain SA Wheat Handbook (T1) | Validate FERTASA Free State tables; seed the Western Cape table (5.4.3.2.5) separately with `region='Western Cape'` | Winter- vs summer-rainfall split matters |
| Sorghum | Grain SA Sorghum Handbook (T1) | FERTASA 5.4.2 (have), ARC-GCI | Verify N removal + P/K calibration | SA sorghum area is small but trades at protein premium |
| Barley | Grain SA malting barley protocol (T1) | FERTASA 5.4.1 (have) | **Malting barley ≠ feed barley**: low-protein target caps late N | Flagged in research memo |
| Sunflower | Grain SA Sunflower Manual (T1) | FERTASA 5.5.6 (have), ARC-GCI | B deficiency critical — seed foliar protocol | |
| Soybean | Grain SA Soybean Handbook (T1) | FERTASA 5.5.5 (have) | Inoculation reduces applied N to near zero — logic already in 042 | Validate P/K recommendations for SA clay soils |
| Groundnut | Grain SA Groundnut Handbook (T1) | FERTASA 5.5.3 (have), ARC-GCI | Ca (gypsum at pegging) is the critical intervention | Not in removal × factor model today |
| Dry bean | Dry Bean Producers' Organisation (T1) | FERTASA 5.5.2 (have) | "No N at flowering" window — seed `crop_application_windows` | |
| Lucerne | FERTASA 5.12.2 (have) | ARC-Animal Production | Established stands = zero N; Ca/Mg/S matter more | 043 updated |
| Cotton | Cotton SA technical docs (T1) | FERTASA 5.9 (have), ARC-IIC | N cutoff at week 13 (in 042) | Validate K timing |
| Tobacco | FERTASA 5.11 (have) | Limpopo Tobacco Cooperative tech docs | Flue-cured vs oriental vs burley are different — need 4 variants | Currently only flue-cured seeded |
| **Sugarcane** | **SASRI FAS** (T1) — per-mill-area recommendations | SASRI Information Sheets; *South African Sugarcane Research Institute Info Sheets* | N × rainfall/irrigation × soil, P × soil-P, K × soil-K, filter-mud residual, ripener N-cut-off | **Gold standard — SASRI publishes defensible rate tables for every mill area.** High priority. |

**Delivery**: migrations 052-060 range; ~9 crops × ~15-30 cells each = ~200 seeded cells.

---

## Phase 2 — Perennials (1-2 weeks)

This is where the effort is. FERTASA rate tables effectively don't exist for perennials; Tier 1 industry bodies are the only defensible source.

| Crop | Primary source (Tier 1) | What they publish | Access | Effort |
|---|---|---|---|---|
| Citrus (all types) | **CRI FertMap** — citrus fertilizer recommendation tool | Soil-test × leaf × yield-target → per-nutrient rec, by cultivar and rootstock | Member-gated; R500-ish annual; *Citrus Research International Technical Circulars* | 2 days |
| Citrus | **CGA** newsletters + *Citrus Academy* | Seasonal application calendars | Mostly free | — |
| Apple / Pear | **Hortgro Science "Pome Fruit Production Guide"** | Age-factor × leaf → N, orchard P/K rebuilds | Member/subscription; *Hortgro Production Guide* | 2 days |
| Peach / Nectarine / Apricot / Plum | **Hortgro Science "Stone Fruit Production Guide"** | Similar to pome; cultivar-specific | Member | 1-2 days |
| Wine grape | **Vinpro / Winetech** research portal | Conradie's SAJEV papers (canonical in research memo); cultivar-split targets | Partly free via Winetech; SAJEV behind DOI | 2-3 days |
| Table grape | **SATI** Technical Bulletins | Smaller body than Vinpro; less published | Member portal | 1 day |
| Blueberry / Strawberry / Raspberry / Blackberry | **SA Berry Producers' Association** | Limited local publishing | Partial | 1 day + IPI/IPNI Tier 3 top-up |
| Macadamia | **SAMAC Technical Programme** (T1) | Leaf-based feed-forward; Mar-Oct N window | Member portal; partial free via Farmer's Weekly | 1 day |
| Avocado | **SAAGA "Avocado Growers' Manual"** (T1) | Cultivar-split leaf norms (Hass / Fuerte / Pinkerton / Edranol / Ryan) | Member; some free via SAAGA Yearbook | 1 day |
| Pecan | SA Pecan Producers' Assoc. (small); ARC-TSC; UGA Extension (Tier 3) | Limited SA data; US pecan research transfers | Mixed | 1-2 days |
| Banana | ARC-TSC banana production guide (T2) + Subtrop | Soil-K heavy; leaf norms | Some free | 0.5 day |
| Mango / Guava / Litchi | **Subtrop** + ARC-TSC | Sparse tables; often only removal figures | Member portal | 2 days combined |
| Olive | SA Olive Growers' Assoc. + UC Davis (Tier 3) | SA publishing is thin; UC Davis transfers well | Member + open access | 1 day |
| Fig / Pomegranate | ARC-Infruitec, Stellenbosch academic | Very thin | Academic search | 0.5 day (likely document-and-leave gaps) |

**Delivery**: migrations 061+ as sources confirm. Expect ~15 crops × fewer cells (perennials are more prose-heavy than table-heavy) + leaf-norm extensions.

---

## Phase 3 — Specialty / small crops (as-needed)

| Crop | Source | Notes |
|---|---|---|
| Vegetables (tomato, onion, cabbage, carrot, pumpkin, etc.) | FERTASA 5.6.1 (have) + **Starke Ayres variety guides** (T4) + ARC-VOPI (T2) | 041 already has decent research data; validate against Starke Ayres which quantifies weekly fertigation splits |
| Sweet potato | ARC-VOPI, UKZN research | Thin |
| Asparagus | FERTASA 5.6.3 (have, seeded in 042) | Done |
| Rooibos | **SA Rooibos Council** + Stellenbosch research | Legume — `n_pct=0` breaks our schema assumption, flagged in research memos |
| Coffee / Tea | ARC-TSC; KZN academic | SA-grown but small volumes |

---

## Phase 4 — Cross-cutting data (not per-crop)

These fill the calculator's structural gaps after per-crop data is in.

### 4a. Soil-type responsiveness (replaces the unsourced adjustment factors)

The 1.5/1.25/1.0/0.5/0.0 multiplier is the single biggest credibility gap. Replace with published responsiveness curves where they exist.

| Nutrient | Best source | Data shape |
|---|---|---|
| N | FERTASA 5.4.3.2 (wheat prose: "+10-15% for sandy, −10-15% for clayey"); ARC-ISCW soil-texture classification | `adjustment_factors_by_texture` — (nutrient, classification, texture, factor) |
| P | FERTASA rate tables implicitly handle this via 2-D lookup; for non-FERTASA crops, use IPNI 4R texture guidance (T3) | Same table |
| K | FERTASA wheat K table: "no K on soils < 35% clay" is an exemplar rule | Texture filter on rate-table lookup (already supported in schema 046) |

### 4b. Method efficiency multipliers

| Method | Efficiency relative to broadcast | Source |
|---|---|---|
| Broadcast | 1.00 (baseline) | Reference |
| Band-place | 1.3-1.5 (P) | FERTASA 5.4.3; IPNI 4R |
| Side-dress | 1.2 (N) | IPNI 4R |
| Fertigation | 1.15-1.25 (N, K) | SASRI FAS; IPI fertigation monographs (Tier 3) |
| Foliar | Nutrient-specific; typically 5-20% of soil-equivalent for macros, effective-enough for micros | Haifa / Yara bulletins (Tier 4); CRI + SAMAC for perennials |

Schema addition: `method_efficiency` table — (method, nutrient, multiplier, source).

### 4c. Application windows (seeds for the 046 `crop_application_windows` table)

Start with the 10-15 most obvious rules across SA crops:

| Crop | Nutrient | Rule | Source |
|---|---|---|---|
| Macadamia | N | Mar-Oct only | SAMAC Technical |
| Dry bean | N | None at flowering | FERTASA 5.5.2 |
| Lucerne (established) | N | Zero | FERTASA 5.12.2 |
| Wheat | N | Split at planting / tillering / flag-leaf (irrigation only) | FERTASA 5.4.3.3.2 |
| Citrus | N | Avoid immediately pre-flowering (Aug-Sep) | CRI |
| Avocado | N | Jan-Feb peak (flowering/fruit set) | SAAGA |
| Wine grape | N | Budbreak to bunch-closure, not after veraison | Conradie SAJEV |
| Apple | Ca | Pre-harvest foliar sprays for bitter-pit control | Hortgro; Cheng 2013 Cornell |
| Potato | N | Not after tuber bulking | FERTASA 5.6.2 |
| Groundnut | Ca | At pegging (gypsum) | Grain SA |

### 4d. Leaf → next-season feed-forward curves

This is the big logic+data hybrid. For each crop with reliable leaf norms (we already have from 043 + FERTASA 5.3), decide:
- Adjustment shape: additive (`+25% on deficient`) or multiplicative (`×1.25`)?
- Does low leaf bump the soil-derived target, or replace the sufficiency factor?
- Time horizon: one season, or decay across 2-3?

Source for the curves:
- Hortgro (pome fruit — boron, zinc, calcium)
- CRI (citrus — the FertMap tool is literally this curve)
- SAMAC (macadamia — boron primarily)
- SAAGA (avocado)
- Vinpro (wine grape)

No single source publishes curves as neat tables; we'll likely synthesize from prose and flag the resulting numbers as Tier 6 (agronomist-captured) until industry-body data comes in.

### 4e. N / S form awareness

| Nutrient form | Behaviour | Data to add |
|---|---|---|
| Urea | Volatilization risk above 20°C + no rain | Flag on material; warn if broadcast without incorporation |
| Ammonium | Soil acidification; lower leaching than nitrate | Material flag |
| Nitrate | High leaching on sandy soils | Material flag |
| Elemental S | Requires oxidation (weeks-months) | Material flag; reduce effective S availability for short-season crops |
| Sulphate S | Immediately plant-available | Baseline |

Source: Haifa / Yara technical bulletins (Tier 4) corroborated by IFA / IPNI (Tier 3). Add `n_form`, `s_form` columns to materials.

---

## Provenance tracking (apply everywhere)

Every numeric row we seed gets these columns. Retrofit existing data where cheap.

| Column | What it records |
|---|---|
| `source` | Short label — "FERTASA Handbook", "SASRI FAS 2024", "CRI FertMap" |
| `source_section` | Handbook section, manual page, DOI, URL |
| `source_year` | Year the source was published |
| `source_tier` | 1-6 per the table above |
| `notes` | Footnotes, caveats, "applies only to cv. Valencia", etc. |

The existing `fertilizer_rate_tables` already has the first four under slightly different names. Standardize others (`crop_requirements`, `fertasa_leaf_norms`, `crop_growth_stages`, `adjustment_factors`) to match.

---

## Recommended execution order

1. **This weekend** — Phase 0 (pure transposition, already scraped).
2. **Next week** — Phase 1 field crops. SASRI sugarcane first (highest revenue × tier-1 source × well-structured tables).
3. **Weeks 2-3** — Phase 2 perennials. CRI + Hortgro in parallel (subscription admin blocks nothing else); SAMAC/SAAGA concurrent.
4. **Week 3-4** — Phase 4a (soil-type responsiveness) — unblocks *every* non-FERTASA crop by replacing the unsourced factor.
5. **Week 4+** — Phase 4b-e in parallel tracks as Tier-1 sources arrive.
6. **Ongoing** — Phase 3 specialty crops whenever a relevant user request arrives.

**Pragmatic guardrail**: don't start Phase 2 perennials without at least one Tier-1 subscription (CRI or Hortgro). Trying to assemble perennial data from academic papers alone will burn time and still leave an auditor asking "why didn't you use the industry body?"

---

## What not to do

- Don't synthesize a "SA-wide" number when regional tables exist. If FERTASA publishes Western Cape and Free State separately, seed both with region filters.
- Don't backfill a Tier-3 international number into a Tier-1 slot when the SA-specific source is just behind a paywall. Either pay for it or mark the crop as "partial coverage".
- Don't let commercial Tier-4 bulletins drive the primary recommendation — use for corroboration only.
- Don't mix researched-heuristic values into the same table as FERTASA-direct without a `source_tier` column to distinguish them.
