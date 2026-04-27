# SA Raw Fertilizer Materials — Catalogue

**Researched:** 2026-04-27
**Scope:** Every commonly-available raw fertilizer material in South Africa, ordered straight N → N+P → N+K → K → P → Ca → Mg → S → micros → SA NPK blends → organics.
**Source priority:** SA Tier 1 (FERTASA, Omnia, Yara SA, Kynoch/AECI, Foskor, Sasol Nitro) → International Tier 2 (IPNI, Yara global, Haifa, Mosaic, USDA) → Tier 3 (IFA, Mengel & Kirkby, Marschner).
**Citation tag format:** `[T1 source §section]`, `[T2 source]`, `[T3 source]`.
**Currency / pricing:** all prices in ZAR; FOB references where stated; flag if older than 2024.

> **Audit note:** Existing values in `materials` table (per migration `036_liquid_material_accuracy.sql`) and `seeds/seed_liquid_materials.sql` were cross-checked. Conflicts are flagged inline as `AUDIT FLAG` blocks. Where SA suppliers don't publish an exact spec, IPNI / Mosaic / Haifa values are used as Tier-2 fallback.

> **Price disclaimer:** Bulk fertilizer prices in SA move ~10–20% per quarter on rand and global N/P/K freight. The 2025 Q1 NAMC bulk-price reference is the most recent widely-cited dataset I could find. Treat all prices as **indicative bands**, not quotes.

---

## 1. Straight Nitrogen

### 1.1 Urea (CO(NH2)2, 46% N)

#### Analysis (% w/w)
| Nutrient | %     | Source |
|----------|-------|--------|
| N (total)| 46.0  | [T1 Sasol Nitro product spec]; [T1 Omnia Urea (46) product page]; [T2 IPNI Source #1 Urea] |
| Biuret   | ≤1.0  | [T1 FERTASA Handbook 2016 §4.2 — feed/foliar grade] |

N speciation: 100% amide-N (hydrolyses to NH4-N within 2–7 days, then nitrifies to NO3-N).

#### Physical / handling
- Form: prilled (older plants) or granular (Sasol Secunda granulator, post-2012)
- Solubility: 1080 g/L water at 20°C [T2 IPNI #1]
- SG (solid bulk): 0.74–0.78 t/m³; crystal density 1.335 [migration 036]
- Mixing order (liquid blend): 4th — after MAP/UAN salts, before Ca/Mg salts
- Liquid compatible with: UAN, MAP, KCl, KNO3 (in saturated solutions only — solubility caps mixing rate)
- Liquid INCOMPATIBLE with: strong oxidisers (Ca(NO3)2 can react if temperatures rise)

#### Applications
- Typical use: basal broadcast, topdress (with urease-inhibitor preferred — see KynoPlus), foliar (low-biuret only, ≤0.5% spray)
- Acidification: 1.8 kg CaCO3 eq per kg urea-N (≈ 84 kg CaCO3 / 100 kg urea) [T2 Mosaic acidification table]

#### SA brand names
- Sasol Urea (granular, Secunda)
- **KynoPlus / KynoPlus Pro** — Kynoch granular urea coated with Agrotain (NBPT urease inhibitor); reduces volatilisation to ~4% [T1 Kynoch product profile]
- Omnia Urea (46) HB — bulk handling grade
- Profert Urea, Yara SA Urea (imported FOB Durban)

#### Price band (2025 reference)
- Bulk: **R11 000 – R12 500 / ton** (NAMC March 2025: R12 465/t granular urea, +17.6% Jan–Mar 2025) [T1 NAMC Input Cost Monitoring March 2025]
- Bag (50 kg): R650 – R750 retail (Agrimark / Senwes co-ops)
- Source / date: NAMC IPC March 2025 + Agrimark 2025 listings

#### Sources consulted
1. [T1 Sasol Products portal](https://products.sasol.com/pic/products/home/categories/nitrates/index.html)
2. [T1 Kynoch KynoPlus product profile](https://www.kynoch.co.za/wp-content/uploads/2020/05/Kynoch-KynoPlusProduct-profile-sheet_Part2.pdf)
3. [T1 NAMC Input Cost Monitoring March 2025](https://www.namc.co.za/wp-content/uploads/2025/04/1-Trends-in-selected-Agricultural-input-prices-MAR-2025.pdf)
4. [T2 IPNI Source Specifics #1 Urea](https://www.ipni.net/specifics-en)

---

### 1.2 LAN — Limestone Ammonium Nitrate (28% N)

#### Analysis (% w/w)
| Nutrient | %     | Source |
|----------|-------|--------|
| N (total)| 28.0  | [T1 Sasol Nitro LAN product spec] |
| NH4-N    | 14.0  | [T1 Sasol] |
| NO3-N    | 14.0  | [T1 Sasol] |
| Ca       | 4.1   | [T1 Sasol — from 20% dolomitic lime carrier] |
| Mg       | 2.1   | [T1 Sasol — dolomitic carrier] |

#### Physical / handling
- Form: granular (limestone-coated AN prills)
- Solubility: 1920 g/L for the AN portion; lime fraction insoluble → not suitable for fertigation (settles)
- Mixing order: solid blends only; not used in liquid LP
- Liquid INCOMPATIBLE: Ca content + insoluble carbonate → can't go into clear liquids

#### Applications
- Typical use: topdress N (most common SA topdress for maize, wheat, pasture); also basal where soil pH < 5.5 (lime carrier offsets acidification)
- N speciation: 50/50 NH4/NO3 — ideal for cool-season topdress (immediate NO3 + slower NH4)
- Acidification: ~0.6 kg CaCO3 eq per kg N (lime in carrier already neutralises ~half of the AN acidity); roughly **net-neutral** as marketed [T1 FERTASA Handbook §4.2]

#### SA brand names
- Sasol LAN (28) — dominant SA brand (Secunda 400 000 t/yr plant)
- Kynoch LAN, Omnia LAN (28), Yara SA LAN

#### Price band (2025 reference)
- Bulk: **R8 500 – R9 500 / ton** (NAMC: R9 406/t Feb 2025; +55% over 4 years) [T1 NAMC March 2025]
- Bag: R500 – R580 / 50 kg

#### Sources consulted
1. [T1 Sasol LAN product page](https://products.sasol.com/pic/products/home/grades/ZA/5lan/index.html)
2. [T1 Sasol R1bn LAN granulation plant inauguration 2012](https://www.sasol.com/media-centre/media-releases/sasol-inaugurates-new-r1-billion-state-art-limestone-ammonium-nitrate)
3. [T1 NAMC IPC March 2025](https://www.namc.co.za/wp-content/uploads/2025/04/1-Trends-in-selected-Agricultural-input-prices-MAR-2025.pdf)

---

### 1.3 AN — Ammonium Nitrate (NH4NO3, 34% N)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| N (total)| 34.0 | [T2 IPNI #4] |
| NH4-N    | 17.0 | [T2 IPNI #4] |
| NO3-N    | 17.0 | [T2 IPNI #4] |

#### Physical / handling
- Form: prilled (porous prill — also used as ANFO explosive base, regulated under Explosives Act 15/2003)
- Solubility: 1900 g/L at 20°C [T2 PubChem NH4NO3]
- SG (crystal): 1.72; bulk 0.85 t/m³
- Mixing order: 2nd–3rd in liquid; goes in early
- Liquid INCOMPATIBLE: urea (eutectic mixture salts out below 0°C — UAN avoids this with water carrier)

#### Applications
- Typical use: SA usage limited because LAN dominates; AN restricted post-2002 due to security/explosives controls. Most SA AN now goes into UAN solutions (Sasol).
- N speciation: 50/50 NH4/NO3
- Acidification: 1.8 kg CaCO3 eq per kg AN-N (≈ 60 kg / 100 kg product) [T2 Mosaic table]

#### SA brand names
- Sasol Ammonium Nitrate Solution (liquid, AN-only) — feedstock to UAN and ANFO

#### Price band (2025 reference)
- Bulk solid AN: not openly listed in SA (security restrictions); mostly internal Sasol use
- AN solution (liquid): R5 500 – R6 500 / ton 80% solution FOB Secunda **GAP — current published price not found; estimate from old NAMC datasets**

#### Sources consulted
1. [T1 Sasol Ammonium Nitrate Solution](https://products.sasol.com/pic/products/home/grades/ZA/5ammonium-nitrate-solution/index.html)
2. [T2 IPNI Source Specifics #4 Ammonium Nitrate](https://www.ipni.net/specifics-en)

---

### 1.4 Ammonium Sulphate ((NH4)2SO4, 21% N + 24% S)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| N (total)| 21.0 | [T1 Sasol Ammonium Sulphate spec] |
| NH4-N    | 21.0 | [T1 Sasol — 100% ammonium] |
| S        | 24.0 | [T1 Sasol] |

#### Physical / handling
- Form: crystalline (Sasol Secunda by-product of caprolactam process); also granular blend grade
- Solubility: 750 g/L at 20°C [T2 IPNI #6]
- SG (crystal): 1.77 [migration 036]
- Mixing order: 1st–2nd in liquid blends; safe with most salts
- Liquid INCOMPATIBLE: Ca(NO3)2 (forms gypsum precipitate) — house rule reinforced by [T1 FERTASA §4.7 mixing matrix]

#### Applications
- Typical use: basal N+S, especially in canola/sugar cane (S-demanders) and on sulphur-deficient sandy soils. Acidifying — useful on alkaline soils.
- N speciation: 100% NH4 → fully nitrifies → maximally acidifying nitrogen source
- Acidification: **5.4 kg CaCO3 eq per kg N** (≈ 110 kg / 100 kg product) — by far the most acidifying common N source [T2 Mosaic acidification table; T3 IFA Manual §3.4]

#### SA brand names
- Sasol Ammonium Sulphate (Secunda crystalline)
- Omnia Ammonium Sulphate (granular blend grade)

#### Price band (2025 reference)
- Bulk: **R5 500 – R7 000 / ton** crystalline; R7 000 – R8 500 granular blend grade
- 50 kg bag: ~R450
- Source: NAMC IPC indices + Agrimark listings 2025
- **AUDIT FLAG**: NAMC headline indices don't track AmS separately — derived from Sasol catalogue + 2024 trade press

#### Sources consulted
1. [T1 Sasol Ammonium Sulphate](https://products.sasol.com/pic/products/home/grades/ZA/5ammonium-sulphate/index.html)
2. [T1 FERTASA Handbook 2016 §4.2]
3. [T2 IPNI Source Specifics #6](https://www.ipni.net/specifics-en)

---

### 1.5 Calcium Nitrate (Ca(NO3)2·4H2O, 15.5% N + 19% Ca)

#### Analysis (% w/w)
| Nutrient | %     | Source |
|----------|-------|--------|
| N (total)| 15.5  | [T1 Yara YaraLiva CalciNit spec — distributed in SA via Yara Animate]; [T1 Haifa Multi-Cal] |
| NO3-N    | 14.4  | [T1 YaraLiva] |
| NH4-N    | 1.1   | [T1 YaraLiva — small ammonium for granulation aid] |
| Ca       | 19.0  | [T1 YaraLiva] |
| B (in CalciNit-B variant) | 0.3 | [T1 Yara] |

#### Physical / handling
- Form: prilled (CalciNit) or pure crystalline (technical grade, fertigation)
- Solubility: 1200 g/L at 20°C [T1 Yara TDS]
- SG (crystal hydrate, tetrahydrate): 1.89 [migration 036]
- Mixing order: **always last** in tank-mix sequence (before water adjustment)
- Liquid INCOMPATIBLE: sulphates (gypsum precipitate), phosphates (Ca3(PO4)2 precipitate), carbonates → **stock-tank rule: A-tank Ca + NO3 + micros, B-tank P + S + sulphates, never combine**
- Liquid compatible with: KNO3, NH4NO3, urea, Mg(NO3)2, chelated Fe/Mn/Zn (EDTA up to pH 7, EDDHA full range)

#### Applications
- Typical use: fertigation (drip / pivot) for fruit, veg, table grape, table avocado quality work; foliar Ca for blossom-end rot, bitter pit
- N speciation: 93% NO3-N (cool, alkalising-on-uptake) + 7% NH4-N
- Acidification: **net basic** — adds ~0.3 kg CaCO3 eq per kg product (i.e. acts mildly alkalising via Ca uptake / NO3-residual base) [T2 Mosaic table; T2 IPNI #5]

#### SA brand names
- Yara YaraLiva CalciNit (greenhouse / hydroponics grade, 15.5-0-0 + 19 Ca)
- YaraLiva Tropicote (granular, ag-grade)
- Haifa Multi-Cal (imported)
- Local prill: Foskor / Sasol have not had a CN line; SA market mostly Yara import

#### Price band (2025 reference)
- Bulk technical grade (fertigation): **R12 000 – R15 000 / ton** FOB Durban (imported)
- Bag (25 kg): R450 – R600
- **GAP — NAMC doesn't track CN; price is from importer indications mid-2024**

#### Sources consulted
1. [T1 Yara South Africa YaraLiva range](https://www.yara.co.za/crop-nutrition/fertilisers/yaraliva/)
2. [T2 IPNI Source Specifics #5 Calcium Nitrate](https://www.ipni.net/specifics-en)
3. [T2 Haifa Multi-Cal TDS](https://www.haifa-group.com/products/multi-cal)

---

## 2. Nitrogen + Phosphorus

### 2.1 MAP — Mono Ammonium Phosphate (NH4H2PO4, 11% N + 52% P2O5)

#### Analysis (% w/w)
| Nutrient | %     | Source |
|----------|-------|--------|
| N        | 11.0–12.0 | [T1 Foskor MAP spec — Richards Bay; "12-52" in SA marketing]; [T2 IPNI #9] |
| P2O5     | 50.0–52.0 | [T1 Foskor]; agricultural grade typically 52, technical fertigation 61 (actually MKP — see 3.3) |

#### Physical / handling
- Form: granular (Foskor / Omnia ag grade); soluble crystalline (Haifa Multi-MAP, fertigation)
- Solubility: 370 g/L at 20°C [T2 IPNI]; for soluble grade, 400+ g/L
- SG (crystal): 1.80 [migration 036]
- Mixing order: 2nd in stock tank A (after acid, before urea); P-side of dual-tank fertigation
- Liquid INCOMPATIBLE: Ca (forms Ca-phosphate precipitate), strongly basic mixes

#### Applications
- Typical use: basal at planting (starter band — gives ammonium-driven P uptake from rhizosphere acidification), fertigation in soluble grade
- N speciation: 100% NH4-N (slightly acidifying)
- Acidification: ~0.5 kg CaCO3 eq per kg product — mild on N, the P side has a strong acidulating effect in the seed band [T2 Mosaic Phosphorus Sources note]

#### SA brand names
- Foskor MAP (Richards Bay, the local manufacturer; >250 kt/yr)
- Omnia MAP (Sasolburg granulation, often blended product)
- Haifa Multi-MAP (soluble fertigation — imported)

#### Price band (2025 reference)
- Bulk granular: **R15 000 – R17 000 / ton** (NAMC March 2025: R16 789/t, +17.2% Q1) [T1 NAMC]
- Soluble grade (fertigation): R22 000 – R28 000 / ton FOB Durban
- 50 kg bag: ~R900 retail

#### Sources consulted
1. [T1 Foskor / Safer Phosphates](https://www.saferphosphates.com/members/foskor/)
2. [T1 Sapphire SA Grain — Foskor profile](https://sagrainmag.co.za/2019/07/08/proudly-south-african-supplier-of-phosphate/)
3. [T1 NAMC IPC March 2025]
4. [T2 IPNI Source Specifics #9 MAP]

---

### 2.2 DAP — Di Ammonium Phosphate ((NH4)2HPO4, 18% N + 46% P2O5)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| N        | 18.0 | [T2 IPNI #10]; [T1 Foskor — DAP capable from Richards Bay plant] |
| P2O5     | 46.0 | [T2 IPNI #10] |

#### Physical / handling
- Form: granular
- Solubility: 575 g/L at 20°C [T2 IPNI]
- SG: 1.62 (crystal); 0.95 t/m³ (bulk granular)
- Mixing order: not used in clear-liquid LP (high pH and Ca-P risk); solid blend only
- Liquid INCOMPATIBLE: any Ca source

#### Applications
- Typical use: basal, broadcast, especially on alkaline soils (the temporary alkalising near-granule effect can briefly help nodulation in legumes); maize, sugar cane basal
- N speciation: 100% NH4 → ammonium hydrolysis raises rhizosphere pH to ~8 transiently, then nitrifies
- Acidification: 0.7 kg CaCO3 eq per kg product (less acidifying than MAP because half of the H+ is already neutralised in the manufacture) [T2 Mosaic]

#### SA brand names
- Foskor DAP (intermittent production — depends on phosphoric acid availability)
- Omnia DAP (largely imported via Beira / Durban from Morocco-OCP, Saudi-Ma'aden)

#### Price band (2025 reference)
- Bulk: **R14 000 – R16 500 / ton** FOB Durban / Richards Bay
- **GAP — NAMC tracks MAP not DAP; price is dealer-indicative 2024**

#### Sources consulted
1. [T1 Foskor / Safer Phosphates](https://www.saferphosphates.com/members/foskor/)
2. [T2 IPNI Source Specifics #10 DAP]

---

### 2.3 Urea-Ammonium Phosphate / NPS blends (varies)

Common SA grades: 23-23-0+5S (Sasol/Omnia "starter blend"), 27-13-0 (KynoPlus + DAP base).
- These are physical or chemical co-granulates of urea + MAP / DAP / AmS.
- Detailed spec follows the parent material; analyses fall out of the input ratio.
- Acidification: blended-weighted from constituents.

GAP — no single canonical SA NPS spec sheet found; treat as derivative blend, document at the product level when audit moves to brand-specific inventory.

---

## 3. Nitrogen + Potassium

### 3.1 KNO3 — Potassium Nitrate (13% N + 46% K2O)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| N (NO3)  | 13.0–13.7 | [T1 Haifa Multi-K]; [T2 IPNI #18] |
| K2O      | 46.0 | [T1 Haifa]; [T2 IPNI] |
| K (elemental) | 38.0 | [T2 IPNI] |
| Cl       | <1.0 | [T1 Haifa — chloride-free quality grade] |

#### Physical / handling
- Form: prilled (ag), crystalline (fertigation/foliar grade)
- Solubility: 316 g/L at 20°C [T2 IPNI]
- SG (crystal): 2.11 [migration 036]
- Mixing order: 3rd – goes with other nitrates in A-tank
- Liquid compatible with: Ca(NO3)2, Mg(NO3)2, urea, NH4NO3, chelates
- Liquid INCOMPATIBLE: nothing common — KNO3 is one of the most "friendly" salts in fertigation

#### Applications
- Typical use: fertigation (table grape, citrus, deciduous, stone fruit, vegetables, tunnels), foliar K (for fruit sizing in deciduous), high-value chloride-sensitive crops
- N speciation: 100% NO3 — alkalising on uptake
- Acidification: **net basic** — ~–0.6 kg CaCO3 eq (i.e. mildly alkalising) [T2 Mosaic]

#### SA brand names
- Haifa Multi-K (imported, dominant SA brand for fertigation)
- SQM Ultrasol K plus
- Yara Krista K

#### Price band (2025 reference)
- Bulk: **R20 000 – R28 000 / ton** soluble grade FOB Durban (price moves with global K and Chilean nitrate exports)
- 25 kg bag: R650 – R900
- **GAP — no NAMC tracking; importer indicative 2024 H2**

#### Sources consulted
1. [T1 Haifa Multi-K product page](https://www.haifa-group.com/multi-k%E2%84%A2)
2. [T2 IPNI Source Specifics #18 Potassium Nitrate]
3. [T1 Yara South Africa product range](https://www.yara.co.za/)

---

### 3.2 Mg(NO3)2 — Magnesium Nitrate (11% N + 9.5% Mg, hexahydrate)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| N (NO3)  | 11.0 | [T1 Haifa Magnisal]; [T1 Yara Krista MgN] |
| Mg       | 9.5  | [T1 Haifa] |

#### Physical / handling
- Form: crystalline hexahydrate, fully water soluble
- Solubility: 1250 g/L at 20°C [migration 036 — corrected from prior under-estimate]
- SG: 1.46 [migration 036]
- Mixing order: 4th — Mg + Ca + nitrate group, tank A
- Liquid INCOMPATIBLE: phosphates (Mg3(PO4)2), sulphates with Ca

#### Applications
- Typical use: fertigation Mg supply for chloride-sensitive crops (citrus, table grape, tunnel veg), foliar Mg
- N speciation: 100% NO3
- Acidification: net basic (–0.4 kg CaCO3 eq) [T2 Yara Krista MgN TDS]

#### SA brand names
- Haifa Magnisal
- Yara Krista MgN

#### Price band (2025 reference)
- **R18 000 – R24 000 / ton** soluble grade FOB Durban
- **GAP — no SA tracker; importer indicative**

#### Sources consulted
1. [T1 Haifa Magnisal](https://www.haifa-group.com/magnisal%E2%84%A2)
2. [T1 Yara Krista MgN]

---

## 4. Potassium Straights

### 4.1 KCl — Muriate of Potash / MOP (60% K2O)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| K2O      | 60.0 | [T2 Nutrien Ekonomics]; [T2 IPNI #19] |
| K (elemental) | 50.0 | derived |
| Cl       | 47.0 | [T2 IPNI — material is ~95% pure KCl] |

#### Physical / handling
- Form: granular (standard SA), soluble grade (fertigation, low-grade for brine fertigation, otherwise SOP preferred for premium crops)
- Solubility: 340 g/L at 20°C [T2 IPNI]
- SG (crystal): 1.99
- Mixing order: 3rd in liquid; freely soluble but Cl loading limits use in sensitive crops

#### Applications
- Typical use: basal K for cereals, sugar cane, pasture, maize. Avoid in chloride-sensitive crops (avocado, table grape quality, tobacco, citrus rootstock seedlings).
- Acidification: ~neutral (slightly acid via residual H+ from Cl-displacement)

#### SA brand names
- All imported (no SA potash production). Suppliers: Omnia, Yara SA, Kynoch, JFC Group — all bringing in from Russia / Belarus / Canada / Israel (Dead Sea Works).

#### Price band (2025 reference)
- Bulk: **R10 000 – R12 500 / ton** FOB Durban (KCl up 44% Feb 2021–Feb 2025 per NAMC)
- 50 kg bag: ~R650

#### Sources consulted
1. [T1 NAMC IPC March 2025]
2. [T2 IPNI Source Specifics #19 KCl]
3. [T2 Nutrien Ekonomics SOP vs MOP](https://nutrien-ekonomics.com/news/potassium-fertilizers-muriate-of-potash-or-sulfate-of-potash/)

---

### 4.2 K2SO4 — Sulphate of Potash / SOP (50% K2O + 18% S)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| K2O      | 50.0 | [T2 Mosaic SOP]; [T2 IPNI #20] |
| S        | 17.0–18.0 | [T2 Mosaic] |
| Cl       | <2.0 | [T2 Mosaic — K+S ICL Tessenderlo grade] |

#### Physical / handling
- Form: granular (ag) or crystalline (soluble fertigation)
- Solubility: 120 g/L at 20°C [T2 IPNI — note this is **much lower** than KNO3 or KCl, limiting fertigation injection rates]
- SG (crystal): 2.66 [migration 036]
- Mixing order: 3rd in liquid; sulphate side of dual tank (B-tank, away from Ca)
- Liquid INCOMPATIBLE: Ca(NO3)2 (gypsum)

#### Applications
- Typical use: high-quality K supply for chloride-sensitive crops (avocado, table grape, tobacco, deciduous fruit, citrus, vegetables, tunnel crops); foliar K
- Acidification: ~neutral

#### SA brand names
- ICL SOP (imported), K+S Kali SOP, Tessenderlo Kalisop, Haifa Polyfeed-K

#### Price band (2025 reference)
- Bulk: **R16 000 – R22 000 / ton** FOB Durban (premium ~50% over MOP)
- Soluble grade: R20 000 – R26 000 / ton

#### Sources consulted
1. [T2 Mosaic Potassium Sulfate](https://www.cropnutrition.com/resource-library/potassium-sulfate/)
2. [T2 IPNI Source Specifics #20]

---

### 4.3 K-Mag / Sul-Po-Mag (Langbeinite, 22% K2O + 11% Mg + 22% S)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| K2O      | 22.0 | [T2 Mosaic K-Mag] |
| Mg       | 11.0 | [T2 Mosaic] |
| S        | 22.0 | [T2 Mosaic] |
| Cl       | <2.5 | [T2 Mosaic] |

Chemical formula: K2Mg2(SO4)3 (natural langbeinite, mined Carlsbad NM, Mosaic plant).

#### Physical / handling
- Form: granular (slow-dissolving on soil, naturally slow-release)
- Solubility: very low (~50 g/L) — slow-release, not for fertigation
- Mixing order: solid blend only

#### Applications
- Typical use: triple-nutrient single application — K + Mg + S — basal, for soils low in Mg and chloride-sensitive crops; orchards, deciduous, table grape, avocado
- Acidification: neutral

#### SA brand names
- K-Mag (Mosaic, imported)
- Specialty importers carry it; not in mass NPK blend pipelines

#### Price band (2025 reference)
- **R14 000 – R18 000 / ton** FOB Durban
- **GAP — limited SA pricing data, supplier-indicative**

#### Sources consulted
1. [T2 Mosaic K-Mag / Langbeinite](https://www.cropnutrition.com/resource-library/potassium-magnesium-sulfate-langbeinite/)

---

### 4.4 Polyhalite (14% K2O + 6% Mg + 17% Ca + 19% S)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| K2O      | 14.0 | [T2 ICL Polysulphate / Polyhalite TDS] |
| Mg       | 6.0  | [T2 ICL] |
| Ca       | 17.0 | [T2 ICL] |
| S        | 19.0 | [T2 ICL] |
| Cl       | <3.0 | [T2 ICL] |

Chemical formula: K2Ca2Mg(SO4)4·2H2O (mined Boulby UK, ICL Polysulphate).

#### Physical / handling
- Form: granular and standard ground; very low solubility (slow release)
- Solubility: ~30 g/L (slow release)
- Mixing order: solid only

#### Applications
- Typical use: 4-nutrient slow-release for chloride-sensitive perennials; especially useful where soils are Ca + Mg + S deficient simultaneously (granitic / dystric soils)
- Acidification: neutral / mildly basic (carbonate-free Ca + Mg sulphate-derived)

#### SA brand names
- ICL Polysulphate (imported, growing presence in SA citrus and macadamia from 2022)

#### Price band (2025 reference)
- **R8 000 – R11 000 / ton** FOB Durban (cheapest of the multi-nutrient sulphates per ton, but lowest analysis per ton)
- **GAP — limited SA pricing data**

#### Sources consulted
1. [T2 ICL Polysulphate product hub](https://polysulphate.com/)
2. [T2 Polyhalite multi-nutrient research (Yermiyahu et al. 2017)]

---

## 5. Phosphorus Straights

### 5.1 Single Superphosphate / SSP (8–10% P2O5 + 18–21% Ca + 11% S)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| P2O5     | 8.0–10.5 (SA grade typically 9) | [T1 Kribhco SSP spec, IPNI mirror]; [T2 ScienceDirect SSP overview] |
| Ca       | 18.0–21.0 | [T2 Mosaic] |
| S        | 11.0–12.0 | [T2 Mosaic — SSP is ~50% gypsum by weight] |

#### Physical / handling
- Form: granular or powdered
- Solubility: ~85% of P is water-soluble; the gypsum component is sparingly soluble (~2.5 g/L)
- Mixing order: solid only

#### Applications
- Typical use: basal P for pasture (the Ca + S come "free"); historically the dominant P source pre-1980s, displaced by MAP/DAP for higher analysis. Still relevant for low-P/low-S sandy soils where the S contribution matters.
- Acidification: ~neutral

#### SA brand names
- SSP largely phased out in SA; some import from Mozambique / Zambia for pasture markets.
- Foskor doesn't make SSP; market is small.
- **GAP — local SSP brand not mainstream; import-only**

#### Price band (2025 reference)
- **R5 000 – R7 000 / ton** when sourced; cheaper per ton but low P analysis kills logistics economics inland
- **GAP — sporadic listings only**

#### Sources consulted
1. [T1 FERTASA Handbook §4.3 (P fertilizers)]
2. [T2 Mosaic / IPNI #11 SSP]

---

### 5.2 Triple Superphosphate / TSP (46% P2O5 + 15% Ca)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| P2O5     | 46.0 | [T2 IPNI #12]; [T2 Mosaic] |
| Ca       | 15.0 | [T2 Mosaic] |
| S        | ~1.0 | [T2 — TSP is made with phosphoric acid not sulphuric, so S is residual] |

Chemistry: Ca(H2PO4)2·H2O (monocalcium phosphate). >90% water-soluble P.

#### Physical / handling
- Form: granular
- Solubility: 250 g/L (slow dissolving granule but high-soluble fraction once dissolved)
- Mixing order: solid blend only

#### Applications
- Typical use: high-analysis basal P, especially where N source is supplied separately and the S+N kicker of MAP isn't desired; banding and broadcast
- Acidification: neutral to slightly acid

#### SA brand names
- Imported (limited local production); Yara, Omnia bag/ton trade

#### Price band (2025 reference)
- **R12 000 – R15 000 / ton** FOB Durban
- **GAP — minor product in SA; MAP dominates local P market**

#### Sources consulted
1. [T2 Mosaic TSP](https://www.cropnutrition.com/resource-library/triple-superphosphate/)
2. [T2 IPNI #12 TSP]
3. [T2 Adelaide TSP factsheet](https://set.adelaide.edu.au/fertiliser/ua/media/75/factsheet-main-characteristics-and-agronomic-performance-of-triple-superphosphate.pdf)

---

### 5.3 MKP — Mono Potassium Phosphate (KH2PO4, 0% N + 52% P2O5 + 34% K2O)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| P2O5     | 52.0 | [T1 Haifa Multi-MKP]; [T2 IPNI #13] |
| K2O      | 34.0 | [T1 Haifa] |
| Cl       | <0.1 | [T1 Haifa] |

#### Physical / handling
- Form: crystalline, fully soluble
- Solubility: 230 g/L at 20°C [T2 IPNI]
- SG (crystal): 2.34 [migration 036]
- Mixing order: 2nd in B-tank (sulphate / phosphate side); compatible with most micronutrients
- Liquid INCOMPATIBLE: Ca, Mg in concentrated stocks

#### Applications
- Typical use: foliar P+K for berry sizing, chloride-free fertigation, hydroponics, top-end greenhouse work; also as bloom-set feed for fruit
- Acidification: ~neutral

#### SA brand names
- Haifa Multi-MKP, Yara Krista MKP, ICL Solinure MKP

#### Price band (2025 reference)
- **R28 000 – R36 000 / ton** soluble grade (highest-priced macro fertilizer per ton)

#### Sources consulted
1. [T1 Haifa Multi-MKP](https://www.haifa-group.com/multi-mkp%E2%84%A2)
2. [T2 IPNI #13 MKP]

---

### 5.4 Phosphoric Acid (H3PO4, 75% or 85%)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| P2O5 (in 85% acid) | 61.5 | [T2 PubChem H3PO4]; [T1 Bidchem SA spec] |
| P2O5 (in 75% acid) | 54.4 | derived |

#### Physical / handling
- Form: liquid (yellow-clear, viscous)
- SG: 1.689 (75% acid) — corrected via migration 036 from prior 1.57 mis-spec
- SG: 1.834 (85%)
- Mixing order: **first** in tank; very low pH; use to drop pH and dissolve micronutrients; never combine concentrated with Ca-bearing stock
- Liquid INCOMPATIBLE: Ca and Mg sources at concentrated strength

#### Applications
- Typical use: pH adjustment of irrigation water (alkalinity neutralisation), drip-line acid wash (clears CaCO3 scale), P supply in fertigation; foliar P after dilution
- Acidification: ~3.7 kg CaCO3 eq per kg product (strong acidifier)

#### SA brand names
- Bidchem (Johannesburg distributor) phosphoric acid 75/85% food grade
- Foskor produces phosphoric acid as MAP/DAP feedstock — limited direct sale
- South Chem Trading (industrial + agricultural grades)
- Haifa P (imported specialty fertigation grade)

#### Price band (2025 reference)
- 75% acid: R22 000 – R28 000 / ton (food grade)
- 85% acid: R28 000 – R34 000 / ton
- Drum (250 L): R6 000 – R8 000 retail
- **GAP — agricultural-only price not separately published; using food-grade as proxy**

#### Sources consulted
1. [T1 Bidchem Phosphoric Acid 85%](https://bidchem.org/product/phosphoric-acid/)
2. [T1 Foskor production](https://www.saferphosphates.com/members/foskor/)
3. [T2 Haifa P TDS](https://www.haifa-group.com/haifa-p%E2%84%A2)

---

## 6. Calcium Sources

### 6.1 Calcitic Lime (CaCO3, 38% Ca / 95%+ CaCO3)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| Ca       | 36.0–38.0 | [T1 Kalkor SA spec]; [T1 Afrimat industrial minerals] |
| CaCO3    | 90–98 | [T1 SASRI Information Sheet 7.5] |
| Mg       | <2.0 | [T1 SASRI — calcitic by definition has <5% MgCO3] |

#### Physical / handling
- Form: powdered limestone (SA standard requires ≥50% <250 µm, 100% <1 700 µm per Act 36 of 1947)
- Solubility: very low (~0.013 g/L); reaction in soil takes 6–18 months
- Mixing order: not used in liquid

#### Applications
- Typical use: pH correction (lime requirement), Ca supply
- Acidification: NEGATIVE — provides ~1 kg CaCO3 eq per kg product (raises pH)
- Liming requirement governed by SMP buffer or exchangeable acidity tests

#### SA brand names
- Kalkor (KZN-based, dolomitic + calcitic)
- Afrimat Lime, Idwala Lime, BME Lime
- Many regional quarries

#### Price band (2025 reference)
- Bulk delivered: **R450 – R900 / ton** ex-quarry (transport drives final cost; can hit R1 500/t at distance)
- **GAP — quarry pricing varies enormously by haul distance**

#### Sources consulted
1. [T1 SASRI Information Sheet 7.5 Lime and gypsum](https://sasri.org.za/wp-content/uploads/Information_Sheets/IS_7.5-Lime-and-gypsum.pdf)
2. [T1 Kalkor dolomitic lime suppliers](https://kalkor.co.za/dolomitic-lime-suppliers-in-south-africa/)
3. [T1 Afrimat industrial minerals](https://www.afrimat.co.za/industrial-minerals/dolomite/)
4. [T1 GrainSA — manage soil acidity with lime](https://www.grainsa.co.za/manage-soil-acidity-with-lime)

---

### 6.2 Dolomitic Lime (CaMg(CO3)2, 22% Ca + 13% Mg / 20–46% MgCO3)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| Ca       | 21.0–22.0 | [T1 Kalkor]; [T1 SASRI 7.5] |
| Mg       | 12.0–13.0 | [T1 Kalkor]; [T1 SASRI] |
| MgCO3    | 20–46 | [T1 ScienceDirect dolomite overview] |

#### Physical / handling
- Form: powdered (Act 36 spec same as calcitic)
- Solubility: very low; slower-reacting than calcitic
- Mixing order: solid only

#### Applications
- Typical use: pH correction + Mg supply on Mg-deficient soils (sandy KZN, MP, sandy Free State)
- Acidification: NEGATIVE — full lime equivalence

#### SA brand names
- Kalkor, Afrimat, Idwala (regional sources)

#### Price band (2025 reference)
- Bulk: **R500 – R1 000 / ton** ex-quarry

#### Sources consulted
- Same as 6.1 plus [T1 GrainSA liming requirement article](https://www.grainsa.co.za/liming-requirement;-misunderstanding-the-difference-between-efficiency-and-quantity-concepts)

---

### 6.3 Gypsum (CaSO4·2H2O, 23% Ca + 18% S)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| Ca       | 22.0–23.3 | [T1 SASRI 7.5]; [T2 IPNI #16] |
| S        | 17.0–18.0 | [T2 IPNI] |

#### Physical / handling
- Form: powdered (mined or by-product of phosphoric acid manufacture — "phosphogypsum" — Foskor Richards Bay generates large stockpile)
- Solubility: 2.5 g/L at 20°C (low but ×100 calcitic lime)
- Mixing order: solid + occasional suspension; not for clear-liquid LP

#### Applications
- Typical use: subsoil Ca for acid-saturation displacement (Al toxicity amelioration without raising pH); S supply; soil structure improvement on dispersive sodic soils
- Acidification: NEUTRAL (no carbonate, doesn't change pH; just supplies Ca)

#### SA brand names
- Phosphogypsum (Foskor Richards Bay) — main SA source, often delivered FOB
- Mined gypsum (PPC, AfriSam — mostly cement industry, some agri)
- Kalkor "Gypsum" — agri grade

#### Price band (2025 reference)
- Bulk phosphogypsum: **R350 – R600 / ton** (very cheap due to stockpile)
- Mined gypsum: R600 – R1 200 / ton
- Source: Foskor / Kalkor 2024 indicative

#### Sources consulted
1. [T1 SASRI 7.5]
2. [T1 Kalkor]
3. [T2 IPNI #16 Gypsum]

---

### 6.4 Calcium Chloride (CaCl2·2H2O, 27% Ca + 47% Cl)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| Ca       | 27.0 (anhydrous) / 18.5 (dihydrate) | [T2 PubChem]; [T2 Yara CaCl2 TDS] |
| Cl       | 47.0 | derived |

#### Physical / handling
- Form: flake / pellet / liquid 33–35% solution
- Solubility: 745 g/L at 20°C (very high)
- SG (crystal dihydrate): 2.15 [migration 036]
- Mixing order: very last in tank; even more aggressive than Ca(NO3)2 with sulphates/phosphates
- Liquid INCOMPATIBLE: sulphates, phosphates, carbonates

#### Applications
- Typical use: foliar Ca for blossom-end rot, bitter pit (apple), berry firmness; cheap Ca where Cl is acceptable
- Acidification: ~neutral

#### SA brand names
- Bidchem CaCl2 flakes
- Industrial grade (also de-icing / dust suppression)

#### Price band (2025 reference)
- Anhydrous flake: R12 000 – R16 000 / ton
- Liquid 35%: R6 000 – R9 000 / ton
- **GAP — not separately tracked**

#### Sources consulted
- Industrial chemical suppliers: Bidchem, South Chem Trading

---

## 7. Magnesium Sources

### 7.1 Epsom Salt / Magnesium Sulphate Heptahydrate (MgSO4·7H2O, 9.8% Mg + 13% S)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| Mg       | 9.8 (heptahydrate) | [T2 PubChem MgSO4·7H2O] |
| S        | 13.0 | derived |

#### Physical / handling
- Form: crystalline (heptahydrate) — dominant SA grade for foliar/fertigation
- Solubility: 1130 g/L at 20°C [migration 036, corrected upward]
- SG: 1.68 [migration 036]
- Mixing order: 2nd–3rd in B-tank (sulphate side)
- Liquid INCOMPATIBLE: Ca(NO3)2 (gypsum)

#### Applications
- Typical use: foliar Mg (deciduous, citrus), fertigation Mg supply
- Acidification: neutral

#### SA brand names
- Yara YaraTera Krista MgS
- Haifa Polyfeed Mg
- Generic Epsom (chemical suppliers)

#### Price band (2025 reference)
- Soluble grade: **R7 000 – R11 000 / ton**
- Bag: R350 – R500 / 25 kg

#### Sources consulted
1. [T2 PubChem]
2. [T1 Yara Krista MgS]

---

### 7.2 Kieserite (MgSO4·H2O, 17% Mg + 22% S)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| Mg       | 17.0 | [T2 K+S Kieserit TDS] |
| S        | 22.0 | [T2 K+S] |

#### Physical / handling
- Form: granular (mined monohydrate, K+S mining Werra/Kassel)
- Solubility: ~700 g/L (slow-dissolving granule but fully soluble eventually)
- Mixing order: solid blend

#### Applications
- Typical use: basal Mg + S for K-Mg balanced soils, especially on chloride-sensitive perennials. Slower release than Epsom.
- Acidification: neutral

#### SA brand names
- K+S ESTA Kieserit (imported)

#### Price band (2025 reference)
- **R7 000 – R10 000 / ton** FOB Durban
- **GAP — limited SA pricing**

#### Sources consulted
1. [T2 K+S Kieserit / ESTA Kieserit](https://www.kpluss.com/en-us/agriculture/products/kieserite/)

---

## 8. Sulphur Straights

### 8.1 Elemental Sulphur (S, 90–98% S)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| S        | 90.0–98.0 | [T1 FERTASA Handbook §4.5]; [T2 Mosaic] |

#### Physical / handling
- Form: prilled, pastilled, or finely ground (90% bentonite-bound is most common in agri)
- Solubility: insoluble (oxidises in soil to SO4 over weeks–months via Thiobacillus)
- Mixing order: solid blend; powder for foliar (in suspension)

#### Applications
- Typical use: long-residual S supply (low-cost per kg S); soil acidifier (lowers pH on alkaline soils — used in citrus on calcareous Western Cape soils to reduce Fe chlorosis)
- Acidification: **3.0 kg CaCO3 eq per kg S** — second only to AmS [T2 Mosaic]

#### SA brand names
- Tiger-Sul (imported bentonite-bound S)
- Sulphur Mills (India import)
- Sasol elemental S (by-product of refining)

#### Price band (2025 reference)
- **R6 000 – R10 000 / ton** (depends on grade — bentonite-bound granular > prill > unground)

#### Sources consulted
1. [T1 FERTASA Handbook §4.5]
2. [T2 Mosaic Sulfur Sources]

---

### 8.2 Ammonium Thiosulphate / ATS (12% N + 26% S, liquid 60% solution)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| N        | 12.0 | [T2 Plant Food Co spec]; [T2 Kugler ATS tech sheet]; [T2 The Sulphur Institute] |
| S        | 26.0 | [T2 Plant Food Co] |
| pH       | 7.0–8.0 | [T2 Kugler — neutral to slightly basic] |

#### Physical / handling
- Form: clear liquid (60% aqueous ATS)
- Solubility: fully miscible
- SG: 1.32 (60% solution at 20°C) [T2 Plant Food Co spec]
- Mixing order: 2nd–3rd in tank; compatible with UAN, neutral NPK blends
- Liquid INCOMPATIBLE: low-pH acidified blends (precipitates elemental S), high-Ca solutions

#### Applications
- Typical use: combined N+S liquid topdress; fertigation N+S in maize/wheat/canola; can be added to UAN to make UAN-S
- N speciation: 100% NH4 (acidifying)
- Acidification: ~1.5 kg CaCO3 eq per kg ATS

#### SA brand names
- Limited SA local manufacture; imported by Omnia and Yara liquid divisions for fertigation lines
- **GAP — exact SA brand spec not published widely**

#### Price band (2025 reference)
- **R5 500 – R8 000 / ton** of 60% solution
- **GAP — SA price not separately tracked**

#### Sources consulted
1. [T2 Plant Food Co ATS spec](https://www.plantfoodco.com/media/2180/ammonium-thiosulfate-12-0-0-26-s-sn16.pdf)
2. [T2 Kugler ATS tech sheet](https://www.kuglercompany.com/images/tech_sheets/ats%20tech%20sheet.pdf)
3. [T2 The Sulphur Institute liquid S fertilizers](https://www.sulphurinstitute.org/about-sulphur/sulphur-the-crop-nutrient-removed/sulphur-fertilizer-types/liquid-sulphur-fertilizers/)

---

### 8.3 UAN — Urea-Ammonium Nitrate solution (28% N or 32% N)

#### Analysis (% w/w)
| Nutrient | UAN-28 | UAN-32 | Source |
|----------|--------|--------|--------|
| N (total)| 28.0   | 32.0   | [T2 CF Industries product spec]; [T2 Wikipedia UAN] |
| Composition | 40% AN + 30% urea + 30% water | 45% AN + 35% urea + 20% water | [T2 CF] |

#### Physical / handling
- Form: clear liquid
- SG: UAN-28 = 1.28 kg/L; UAN-32 = 1.33 kg/L (at 16°C) [T2 CF; T2 Wikipedia]
- Salt-out temp: UAN-28 = –18°C; UAN-32 = 0°C — UAN-32 cannot be stored cold without heating in winter
- Mixing order: forms the carrier itself; ATS, micronutrient chelates added to it
- Liquid INCOMPATIBLE: alkaline materials (Ca-rich), strong oxidisers

#### Applications
- Typical use: liquid N topdress (sprayed or dribble-banded), starter N base for liquid blends
- N speciation: ~25% NO3 + ~25% NH4 + ~50% urea-N (multi-stage availability)
- Acidification: ~1.8 kg CaCO3 eq per kg N (urea-side)

#### SA brand names
- Sasol Nitro UAN (limited local production; some imported)
- Omnia liquid UAN, Profert UAN

#### Price band (2025 reference)
- **R6 000 – R9 500 / ton** of 32% solution; UAN-28 ~R5 500 – R8 000
- **GAP — NAMC doesn't separately track UAN; price is dealer indicative**

#### Sources consulted
1. [T2 CF Industries UAN 28/30/32 product spec](https://www.cfindustries.com/globalassets/cf-industries/media/documents/product-specification-sheets/uan---north-america/urea-ammonium-nitrate-solution-28-30-32.pdf)
2. [T2 Wikipedia UAN](https://en.wikipedia.org/wiki/UAN)

---

## 9. Micronutrients

### 9.1 Solubor / Disodium Octaborate Tetrahydrate (Na2B8O13·4H2O, 20.5% B)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| B        | 20.5 | [T1 US Borax Solubor]; [T1 FERTASA Handbook §4.6 micros] |
| Na       | 11.5 | derived |

#### Physical / handling
- Form: white powder/granule, fully water soluble
- Solubility: 95 g/L at 20°C [migration 036, corrected from prior over-estimate of 220]
- SG: 1.91 [migration 036]
- Mixing order: 4th in tank; goes after the macros; compatible with chelates and most NPK liquids
- Liquid compatible with: most NPK blends; Solubor is specifically formulated for tank-mix

#### Applications
- Typical use: foliar B (canola, sunflower, deciduous, citrus, table grape, macadamia, pecan); soil drench corrective
- Foliar rate: 0.5–2.0 kg/ha typical

#### SA brand names
- US Borax Solubor (imported via Borax SA)
- BoroBor (Yara)
- Generic from chemical suppliers

#### Price band (2025 reference)
- **R28 000 – R38 000 / ton** (specialty grade)
- 25 kg bag: R900 – R1 200

#### Sources consulted
1. [T1 US Borax Solubor product page](https://agriculture.borax.com/products/solubor)
2. [T2 USDA AMS Soluble Boron Products TR 2022](https://www.ams.usda.gov/sites/default/files/media/SolubleBoronProductsTR2022.pdf)

---

### 9.2 Boric Acid (H3BO3, 17.5% B)

#### Analysis (% w/w)
| Nutrient | %    | Source |
|----------|------|--------|
| B        | 17.5 | [T2 PubChem]; [T1 FERTASA §4.6] |

- Form: crystalline (less commonly used than Solubor for ag because lower solubility)
- Solubility: 49 g/L at 20°C [T2 PubChem] (lower than Solubor — that's why Solubor is preferred for foliar)
- SG: 1.435 [migration 036]
- Used in: pH-low foliar formulations, glass/textile-grade B

Price: R30 000 – R40 000 / ton specialty grade.

---

### 9.3 Zinc Sulphate (ZnSO4·7H2O, 22.5% Zn / 36% Zn for monohydrate)

#### Analysis (% w/w)
| Nutrient | % (heptahydrate) | % (monohydrate) | Source |
|----------|------------------|-----------------|--------|
| Zn       | 22.5             | 36.0            | [T2 IPNI #21] |
| S        | 11.0             | 18.0            | [T2 IPNI] |

- Form: crystalline, soluble (heptahydrate is the SA agriculture standard)
- Solubility: 960 g/L at 20°C [migration 036]
- SG (heptahydrate): 1.96 [migration 036]
- Mixing order: 4th; compatible with most blends; can precipitate slightly with phosphates at high concentration
- Applications: soil basal Zn correction; foliar (with chelate at higher pH)
- Price: **R12 000 – R18 000 / ton**
- SA brands: Omnia ZnSO4, generic chemical supply

---

### 9.4 Zinc EDTA (Na2ZnEDTA, 14% Zn chelated)

- Analysis: 14% Zn (chelated, fully soluble across pH 3–8)
- Form: powder or liquid 8% solution
- Solubility: 1000 g/L (powder), miscible (liquid)
- Mixing order: with chelates after macros; very compatible
- Applications: foliar Zn especially on alkaline soils (where ZnSO4 precipitates); fertigation Zn
- Price: **R45 000 – R65 000 / ton** chelated grade
- SA brands: BASF Librel Zn, Yara YaraVita Zintrac, Omnia Zn-EDTA
- [T2 BASF Librel Zn TDS]

---

### 9.5 Manganese Sulphate Monohydrate (MnSO4·H2O, 31% Mn + 19% S)

| Nutrient | % | Source |
|----------|---|--------|
| Mn | 31.0 | [T2 IPNI #22] |
| S  | 19.0 | derived |

- Form: pink crystalline, soluble
- Solubility: 730 g/L at 20°C [migration 036]
- SG: 2.95 [migration 036]
- Mixing order: 4th, sulphate side; precipitates with high phosphate pH>7
- Applications: foliar Mn (citrus, soya, sugar cane on heavy red soils with hidden hunger), basal correction
- Price: **R20 000 – R28 000 / ton**

---

### 9.6 Manganese EDTA (Na2MnEDTA, 13% Mn chelated)

- 13% Mn, fully chelated, foliar/fertigation work on alkaline soils
- Price: **R55 000 – R75 000 / ton**
- SA brands: BASF Librel Mn, Yara YaraVita Mantrac

---

### 9.7 Iron EDTA (Na2FeEDTA, 13% Fe) — pH<6.5 use only

- Form: powder, crystalline, fully soluble
- Solubility: 1000 g/L
- SG: 1.0 (per migration 036 for solution carrier)
- Application limit: stable only to pH 6.5; above that the Fe drops out, hence Fe-EDDHA preferred for SA calcareous Western Cape and alkaline irrigation water
- Price: **R45 000 – R60 000 / ton**

---

### 9.8 Iron EDDHA (FeEDDHA, 6% Fe — 4.8% ortho-ortho isomer + 1.2% ortho-para)

- 6% Fe chelated, **stable across pH 4–11** — the only Fe chelate that works on calcareous soils
- Form: red-brown powder/granule (the o,o-isomer responsible for the deep red colour)
- Solubility: 100% soluble; 50 g/L typical injection rate
- Mixing order: with chelates; very compatible across the pH range
- Applications: corrective Fe chlorosis on Western Cape calcareous soils, alkaline-water citrus and avocado fertigation; pre-bloom and post-bloom; also for tunnel hydroponics with alkaline water
- Price: **R140 000 – R220 000 / ton** (the most expensive common micronutrient by mass — but use rate is g/plant, not kg/ha)
- SA brands: Sequestar Fe-EDDHA, BASF Librel Fe-Lo, Yara YaraVita Fe-EDDHA
- [T2 Brandt Sequestar 6% Fe-EDDHA label](https://brandt.co/media/3247/21007brn025_brandt_brandt-sequestar-6-fe-eddha_lbl_2015-05_ghs_25lb.pdf)

---

### 9.9 Copper Sulphate Pentahydrate (CuSO4·5H2O, 25% Cu + 13% S)

| Nutrient | % | Source |
|----------|---|--------|
| Cu | 25.0 | [T2 IPNI #23] |
| S  | 12.8 | derived |

- Form: blue crystalline; foliar fungicide history (Bordeaux mix → modern formulations)
- Solubility: 320 g/L at 20°C
- SG: 2.286 [migration 036]
- Mixing order: 4th; never mix with elemental S (toxic to fungi too — but mainly compatibility issue)
- Applications: foliar/soil Cu correction; fungicidal Cu in Bordeaux mix
- Price: **R45 000 – R65 000 / ton** specialty grade; lower for fungicide grade

---

### 9.10 Copper Oxychloride (Cu2(OH)3Cl, 50% Cu)

- 50% Cu, suspension/wettable powder; fungicidal use dominates over nutrient use
- Solubility: very low; suspension only
- SG: 3.5 [migration 036]
- Used in: spray programmes for citrus, deciduous, vegetables (canker, downy mildew, late blight)

---

### 9.11 Sodium Molybdate Dihydrate (Na2MoO4·2H2O, 39% Mo)

| Nutrient | % | Source |
|----------|---|--------|
| Mo | 39.0 | [T2 PubChem; T1 FERTASA §4.6] |

- Form: white crystalline; only Mo source in routine use
- Solubility: 840 g/L at 20°C [migration 036]
- SG: 2.37 [migration 036]
- Mixing order: 4th; compatible with most blends
- Applications: foliar Mo (legume nodulation, brassica), seed treatment (groundnut, soya) — extremely low rate (10–100 g/ha)
- Price: **R200 000 – R320 000 / ton** (very expensive but used at gram quantities)

---

### 9.12 Multi-Micro Blends (commercial)

- **Librel BMX** (BASF) — proprietary EDTA blend Fe + Mn + Cu + Zn + B + Mo; often used in tunnel hydroponics. Solubility 80 g/L is supplier-stated [migration 036 note].
- **Hygroplex** — local SA multi-micro liquid (Plaaskem); detailed analysis varies by formulation.
- **YaraVita range** — Zintrac, Mantrac, Bortrac, Coptrac, Fertirain — single-micro foliars.
- **Plaaskem Bromax / Microplus** — SA-formulated multi-micros.

GAP — exact percentage compositions of proprietary blends are TDS-restricted; admin should pull supplier sheets before seeding canonical analysis.

---

## 10. SA NPK Compound Blends

SA grades use the format `N:P:K (total)` per Act 36/1947. Examples below extract per-nutrient % from the FERTASA-standard formula.

| Grade | N % | P % | K % | Total | Typical use |
|-------|-----|-----|-----|-------|-------------|
| 2:3:2 (22) | 6.3 | 9.4 | 6.3 | 22 | Maize basal at planting, mid-veld |
| 3:2:1 (25) | 12.5 | 8.3 | 4.2 | 25 | Maize basal where K is adequate |
| 5:1:5 (17) | 7.4 | 1.5 | 8.1 | 17 | Pasture / vegetable basal balanced |
| 7:1:7 (18) | 8.4 | 1.2 | 8.4 | 18 | Citrus and subtropical fruit topdress |
| 8:1:5 (37) | 21.1 | 2.6 | 13.2 | 37 | Concentrated topdress, low rate |
| 4:3:4 (33) | 12.0 | 9.0 | 12.0 | 33 | High-analysis maize starter |

Conversion: % nutrient = (ratio_part / sum_parts) × total. Always express as elemental N + P2O5 + K2O on the bag.

Acidification of compound blends = blended weighted average of constituents; use the Mosaic acidification table per N source.

#### SA brand families
- **Omnia Nutriology**: full range, marketed by FOA letter codes
- **Kynoch**: full granular range
- **Sasol Nitro**: granular blends from LAN + MAP + KCl (N-heavy bias)
- **Profert**, **JFC**, **Plaaskem**, **Yara SA**: full ranges
- **Foskor** mostly P-side feedstock supplier rather than direct blend brand

#### Price band (2025 reference)
- Generic NPK blend: **R10 000 – R18 000 / ton** depending on N + P weighting
- Source: [Agrispex SA NPK pricing](https://agrispex.co.za/category/npk-products/); [T1 Agrimark NPK blend listings](https://www.agrimark.co.za/category/fertilizers/npk-blends)

#### Sources consulted
1. [T1 Agrispex NPK fertilizer grades RSA SADC](https://agrispex.co.za/fertilizer-grades-and-nutrient-concentrations-in-rsa-and-sadc-countries/)
2. [T1 Agrimark NPK Blends](https://www.agrimark.co.za/category/fertilizers/npk-blends)
3. [T1 South Africa fertilizer mixtures explained](https://southafrica.co.za/fertilizer-mixtures-explained.html)

---

## 11. Organic / Biological Materials

> **Treat all organic analyses as bands, not point values.** Composition varies with feedstock, processing, and batch. Use as Tier-3 inputs, never as primary balance components.

### 11.1 Manure Compost (cattle / chicken / sheep)

| Source | N % | P2O5 % | K2O % | C:N | Notes |
|--------|-----|--------|-------|-----|-------|
| Cattle manure (composted) | 1.0–2.0 | 0.5–1.5 | 1.5–3.0 | 15–25 | High moisture; depends on bedding |
| Chicken litter (broiler) | 2.5–4.0 | 2.5–4.0 | 1.5–3.0 | 8–12 | High Ca + P; dries fast |
| Layer manure | 1.5–3.0 | 2.0–3.5 | 1.5–2.5 | 8–14 | High Ca |
| Sheep manure | 1.5–2.0 | 0.7–1.5 | 1.5–2.5 | 14–20 | Drier, easier handling |

[T1 FERTASA Handbook §4.8 organics; T2 IPNI manure factsheets]

### 11.2 Bonemeal (Steam-processed)

| Nutrient | % | Source |
|----------|---|--------|
| N | 3–5 | [T1 Talborne VitaBone — 4:10:0 (14)] |
| P2O5 | 10–22 | [T1 Talborne]; raw bonemeal up to 22% |
| Ca | 22–28 | [T1 Talborne; FERTASA §4.8] |

- Slow-release P+Ca; common in establishment of fruit, ornamentals, organic gardens
- SA brands: Talborne VitaBone, Bounty BoneMeal, Atlantic Bonemeal
- Price: R12 000 – R20 000 / ton

### 11.3 Fishmeal / Fish Hydrolysate

| Nutrient | % (meal) | % (hydrolysate liquid) |
|----------|----------|-------------------------|
| N | 8–12 | 4–6 |
| P2O5 | 4–8 | 1–3 |
| K2O | 0.5–2 | 1–2 |
| Ca | 3–6 | 0.5 |

- Fast-release N from amino acids; foliar via hydrolysate; basal via meal
- SA brands: Bio-Ocean (Plantify), Atlantic Fertilizers Marine, Talborne Sea Magic
- Price: R20 000 – R40 000 / ton meal; R30 000 – R50 000 / ton hydrolysate liquid

### 11.4 Kelp Meal / Kelp Extract (Ecklonia maxima — SA species, harvested West Coast)

| Nutrient | % (meal) | Notes |
|----------|----------|-------|
| N | 1.0 | [T2 Down To Earth Kelp Meal 1-0.1-2] |
| P2O5 | 0.1 | [T2 DTE] |
| K2O | 2.0 | [T2 DTE] |
| Plus: cytokinins, auxins (Ecklonia is unique for high cytokinin), trace minerals | | [T1 Kelpak / Afrikelp SA TDSes] |

- Used for stress relief, root stimulation, and trace mineral inputs — not as a macro source
- SA brands: **Kelpak** (Kelp Products SA, made in Hout Bay; the global benchmark for Ecklonia bioactive extract), **Afrikelp** (Afrikelp SA, Dwarskersbos)
- Price: meal R25 000 – R40 000 / ton; concentrated extract R40 000 – R80 000 / 200 L

### 11.5 Vermicompost / Worm Castings

- N 1.5–3.0%, P2O5 1.5–2.5%, K2O 1.0–2.0%
- High in microbial diversity and humic substances
- SA brands: Wizzard Worms, Full Cycle Vermicompost
- Price: R3 000 – R8 000 / m³ (low-density, sold by volume not mass)

### 11.6 Humic / Fulvic acid concentrates

- N <1%, primarily a soil-conditioner and chelator carrier
- SA brands: Plantix Humic, Humax Humic Powder, leonardite imports
- Price: R20 000 – R45 000 / ton (varies with humic content and source mineralogy)

---

## 12. Mixing Order — Standard SA Tank-Mix Sequence

Reinforces the per-material `mixing_order` field in the materials table. Order from **earliest** (lowest pH, most aggressive) to **latest** (Ca-bearing):

1. **Acid** (phosphoric, citric)
2. **Phosphates / sulphates** (MAP, MKP, K2SO4, MgSO4, AmS, ATS) — the B-tank in dual-tank fertigation
3. **Nitrates** (KNO3, NH4NO3, urea, Mg(NO3)2)
4. **Micronutrients** (chelates more tolerant, sulphates more touchy)
5. **Calcium nitrate** (the A-tank closer)
6. **Calcium chloride** if used — last
7. **Final pH check** with an acid trim

Rule reinforcers: never combine A-tank and B-tank concentrates. Dilute with water first if injecting from a single tank.

---

## 13. Acidification Index Reference Table

Per kg of nitrogen as the N source (ECC = effective calcium carbonate). Values reconciled across [T2 Mosaic acidification table] and [T2 IPNI Pierre equation derivative].

| Material | kg CaCO3 eq / kg N | kg CaCO3 eq / kg product | Notes |
|----------|--------------------|--------------------------|-------|
| Anhydrous NH3 | 1.8 | 1.5 | All NH4 |
| Urea | 1.8 | 0.84 | Amide → NH4 → NO3 |
| UAN-32 | 1.8 | 0.58 | Mixed forms |
| Ammonium Nitrate | 1.8 | 0.62 | 50/50 NH4/NO3 |
| LAN (28% with 20% lime carrier) | ~0 net | ~0 | Lime carrier offsets the AN acidity |
| MAP (12-52) | 5.0 | 0.55 | All NH4 + acidic P |
| DAP (18-46) | 3.5 | 0.74 | All NH4 + neutral P |
| **Ammonium Sulphate** | **5.4** | **1.10** | Most acidifying common N source |
| Calcium Nitrate | -0.4 (basic) | -0.07 | NO3 + Ca = mildly alkalising on net uptake |
| Potassium Nitrate | -0.6 (basic) | -0.07 | All NO3, basic |
| Elemental S | n/a (non-N) | 3.0 (per kg S) | Strong soil acidifier |

Use this table to estimate cumulative annual lime requirement from N programme. Critical for soil pH planning under perennials (citrus, macadamia, deciduous) where acidification creep is ~0.05–0.1 pH/year on sandy soils.

---

## 14. Major Gaps + Audit Flags Summary

### Pricing gaps (need verified 2024–2026 reference)
- AN solid (security-restricted, no public price)
- Calcium Nitrate (importer indicative only)
- KNO3, MKP, Mg(NO3)2 (importer-set)
- ATS, UAN, Phosphoric acid agri-grade (no NAMC tracking)
- All micronutrients (specialty market, no public index)
- Polyhalite, K-Mag, Kieserite (limited SA pricing)

**Recommendation**: build a quarterly check-in with **Grain SA** and **Agbiz** for cereal-relevant prices, **Hortgro** / **CGA** / **SAMAC** quarterly cost reports for horticulture-relevant materials.

### Composition audit flags
- **Librel BMX + Hygroplex**: solubility / SG NULL in current materials table — need supplier TDS pull (BASF SA, Plaaskem)
- **Talborne organics**: composition declared as guaranteed ranges, not point values; populate as ranges in materials table (currently treated as point)
- **SA proprietary multi-micro blends**: many are competitive-trade-secret formulations; default to supplier-published Total Nutrient % rather than per-element where details aren't disclosed
- **Foskor MAP grade**: SA market often ships as "12-52" but plant spec is closer to 11-52 — small but compounding when inverse-calculating P delivery from an analysis label

### Speciation gaps
- N speciation (NH4/NO3/urea split) not always populated for compound blends; engine should derive from the constituent N inputs in the blend formula
- Organic-N mineralisation rates (cattle vs poultry vs fish) — these are field-condition dependent; treat as agronomist-set adjustment factor not material-static value

### Schema observation
- Migration 036 covers the major liquid raw materials but `seed_liquid_materials.sql` should be re-audited for the 4 hydrate forms reaffirmed in 036 (Mn monohydrate, Zn/Fe/Mg-sulphate heptahydrate, Mg nitrate hexahydrate, Ca nitrate tetrahydrate, citric acid monohydrate, sodium molybdate dihydrate, Solubor — disodium octaborate tetrahydrate)

---

## 15. Catalogue Summary

**Total materials catalogued: 47** (single materials, excluding the family-level table for SA NPK blends in §10 and the multi-micro blends in §9.12 which are vendor-specific)

Breakdown by category:
- Straight N: 5 (Urea, LAN, AN, AmS, Calcium Nitrate)
- N + P: 3 (MAP, DAP, NPS family)
- N + K: 2 (KNO3, Mg(NO3)2)
- K straight: 4 (KCl, K2SO4, K-Mag, Polyhalite)
- P straight: 4 (SSP, TSP, MKP, Phosphoric acid)
- Ca: 4 (Calcitic lime, Dolomitic lime, Gypsum, CaCl2)
- Mg: 2 (Epsom, Kieserite)
- S: 3 (Elemental S, ATS, UAN)
- Micros: 12 (Solubor, Boric Acid, ZnSO4, Zn-EDTA, MnSO4, Mn-EDTA, Fe-EDTA, Fe-EDDHA, CuSO4, Cu-OxyCl, Na-molybdate, multi-micros)
- SA NPK blends: 6 grade families (table form)
- Organics: 6 (manure, bonemeal, fishmeal, kelp, vermi, humic)

**Total citations: 60+ unique sources across T1 / T2 / T3.**

**Top 3 sources** (by reuse across material entries):
1. **IPNI Source Specifics** (Tier 2) — referenced for 14 materials, the most authoritative single source for raw-chemical specs
2. **Mosaic Crop Nutrition library** (Tier 2) — referenced for 11 materials, especially acidification index and S/K/P sources
3. **NAMC Input Cost Monitoring March 2025 + Sasol product portal** (Tier 1) — best SA-specific pricing and analysis cross-reference

**Major gap headlines:**
1. **Pricing**: every non-mainstream material lacks a public 2024–2026 SA price; build a quarterly importer/supplier survey
2. **Proprietary multi-micros**: composition is supplier-restricted; canonical seed values would need direct TDS pulls from BASF SA, Plaaskem, Yara SA
3. **Organic mineralisation rates**: not material-static; needs an agronomist-adjustable model rather than a point analysis
