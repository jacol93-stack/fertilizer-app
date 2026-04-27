# Grapes + Berries — SA agronomy data extract

**Date:** 2026-04-27
**Scope:** Wine grapes (Cabernet Sauvignon, Shiraz, Chenin Blanc, Pinotage, Sauvignon Blanc, Chardonnay) | Table grapes (Crimson, Thompson Seedless, Flame, Prime) | Blueberry | Raspberry | Strawberry
**Hemisphere:** Southern (Western Cape calendar)

> **CRITICAL POLICY FLAG — wine grapes are quality-first.** Engine MUST NOT auto-push N to "adequate" leaf-norm midpoint when the production target is premium wine. Conradie's SA-canonical work and global consensus: excess N drives vigour, delays ripening, raises pH/hexoses, and depresses colour and varietal character. Wine grape is the *only* major SA crop where the agronomic optimum sits in the **lower** half of the published "sufficient" band. Treat upper bound as a ceiling, not a target. See policy block at end of wine grape section.

---

## Wine grape (*Vitis vinifera*) — Cabernet Sauvignon, Shiraz, Chenin Blanc, Pinotage, Sauvignon Blanc, Chardonnay

### Growth stages (Western Cape, Stellenbosch reference; ±2 weeks per cultivar/region)

| Month (SA) | Stage | BBCH | Key process | Source |
|---|---|---|---|---|
| Aug (late) – Sep | Budbreak | 07–09 | Wool stage → green tip; root reserves drive growth | [T1 SA Wine sawine.co.za phenology] |
| Sep – Oct | Shoot growth, leaf separation | 11–19 | Canopy expansion, low N uptake from soil | [T2 UC Davis Geisseler] |
| Late Oct – early Nov | Inflorescence visible → cap fall | 53–60 | Flower development; B critical | [T3 BBCH grapevine] |
| Nov | **Bloom / flowering** | 61–69 | Sampling window (petiole at full bloom = SA canonical) | [T1 Conradie 1994 SAJEV petiole protocol] |
| Late Nov – Dec | **Fruit set, berry formation** | 71–75 | Peak N + K uptake begins; Ca demand starts | [T2 UC Davis "highest uptake right after fruit set"] |
| Dec | Pea size → bunch closure | 75–79 | K + P rapid uptake | [T2 Advanced Viticulture] |
| **Jan (mid-late)** | **Veraison** | 81–83 | Colour change, sugar accumulation; canonical 2nd sampling window for mobile NPK | [T2 Penn State, Ohio State HYG-1438] |
| Jan – Mar | Ripening | 85–89 | K continues to fruit; N uptake winds down | [T2 UC Davis] |
| **Feb (whites) – Mar (reds)** | **Harvest** | 89 | Chenin/Chard/SB/Pinotage Feb; Cab/Shiraz/Merlot early-mid Mar | [T1 Vinpro 2023 Harvest Report] |
| Mar – Apr | **Post-harvest, leaf-active** | 91–93 | N application here refills reserves (~85 % of woody-tissue N comes from leaf re-translocation pre-leaffall) | [T2 UC Davis Geisseler N partitioning] |
| May – Jul | Dormancy, pruning | 95–00 | No active uptake; soil amendments / lime / gypsum applied | [T2 UC Davis] |

### Leaf / petiole norms — sample at full bloom (SA canonical, Conradie protocol); veraison values added for cross-check

**Sampling: petiole opposite first inflorescence, full bloom.** SA labs report on petiole basis (NOT blade). Conradie established this as the SA standard.

| Nutrient | Deficient | Adequate (BLOOM) | Adequate (VERAISON) | High / excess | Source |
|---|---|---|---|---|---|
| **N total %** | <0.8 | **1.20 – 2.20** *(quality-wine target: 1.2 – 1.6; bulk: up to 2.0)* | 0.90 – 1.30 | >2.5 | [T2 Penn State, T2 Wine Grape Production Guide ENA 2008] |
| NO3-N ppm (petiole) | <340 | **500 – 1200** | 350 – 500 | >1200 | [T2 UC Davis Geisseler] |
| **P %** | <0.12 | **0.17 – 0.30** | 0.16 – 0.29 | >0.50 | [T2 Penn State / WGPG-ENA] |
| **K %** | <0.80 | **1.50 – 2.50** | 1.50 – 2.50 | >3.0 | [T2 Penn State / Ohio HYG-1438] |
| Ca % | <0.50 | 1.00 – 3.00 | 1.20 – 1.80 | >3.5 | [T2 Penn State] |
| Mg % | <0.20 | 0.30 – 0.50 | 0.26 – 0.45 | >0.80 | [T2 Penn State] |
| S % | <0.10 | 0.18 – 0.40 | 0.18 – 0.40 | — | [T2 Haifa / IPNI] |
| B ppm | <25 | **25 – 50** | 25 – 50 | >100 | [T2 Penn State, T1 SATI handbook] |
| Zn ppm | <15 | **30 – 60** | 30 – 50 | >150 | [T2 Penn State, T1 SATI] |
| Mn ppm | <20 | 25 – 1000 | 31 – 150 | >1500 | [T2 Penn State] |
| Fe ppm | <30 | 30 – 100 | 31 – 50 | >200 | [T2 Penn State] |
| Cu ppm | <3 | 5 – 15 | 5 – 15 | >25 | [T2 Penn State, T1 SATI] |
| Mo ppm | <0.1 | 0.3 – 1.5 | 0.3 – 1.5 | — | [T2 Haifa] |

> **Why two columns:** SA convention (Conradie) is bloom petiole. International best-practice (UC Davis, Penn State) increasingly favours veraison for **mobile N/P/K** because bloom values are inflated by remobilisation from reserves. Engine should accept either; flag mismatch.

### Soil thresholds (SA convention — Bray-1 P, ammonium-acetate K/Ca/Mg; 0–300 mm)

| Nutrient | Deficient | Adequate / target | High | Source |
|---|---|---|---|---|
| pH (KCl) | <5.0 | **5.5 – 6.5** | >7.0 | [T1 Conradie 1994 via Wineland] |
| Bray-1 P (mg/kg) | <15 | **25 – 35** (sandy → sandy clay loam) | >50 | [T1 Conradie 1994 via SATI handbook] |
| K (mg/kg, NH4-OAc) | <50 | **70 – 120** | >180 | [T1 SATI handbook 2019] |
| Ca (mg/kg) | <300 | **360 – 500** (sandy) / 500 – 800 (clay) | >1200 | [T1 SATI handbook] |
| Mg (mg/kg) | <30 | **40 – 120** | >250 | [T1 SATI handbook] |
| S (mg/kg) | <5 | 10 – 20 | — | [T2 IFA] |
| B (mg/kg, hot-water) | <0.3 | **0.3 – 1.0** | >1.5 | [T1 SATI handbook] |
| Zn (mg/kg, DTPA) | <0.5 | 0.5 – 2.0 | >5 | [T1 SATI handbook] |
| Mn (mg/kg, DTPA) | <2 | 2 – 30 | >50 | [T1 SATI handbook] |
| Cu (mg/kg, DTPA) | <0.5 | 0.5 – 5.0 | >10 (Cu spray accumulation) | [T1 SATI handbook] |
| OC % | <0.5 | **0.6 – 1.5** *(higher OK but not required for wine quality)* | >2.0 | [T1 Wineland organic guide] |
| CEC (cmol/kg) | <4 | 6 – 15 | >25 | [T2 standard SA convention] |

> **Wine grape quirk on OC:** unlike most crops, very low organic carbon (0.5 – 1.0 %) is **acceptable to preferred** for premium wine sites because it limits N mineralisation and vigour. Don't recommend organic-carrier blends for high-end wine vineyards solely on OC grounds.

### Crop nutrient requirements per ton fruit (with quality cap on N)

| Nutrient | kg / ton | Annual cap kg/ha (mature, sandy loam) | Source |
|---|---|---|---|
| **N** | **1.6 – 2.6** (quality wine); 3.0 – 4.0 (bulk wine) | **35 – 60** (fine wine cap); up to 80 (bulk) | [T1 Wineland; T2 CDFA "3.6 lb/ton wine fresh wt"; Vinpro guidance] |
| P (P2O5) | 0.6 – 1.5 (≈ 0.27 – 0.65 P) | 15 – 30 | [T2 Haifa 60 kg P2O5/20 t = 3.0 kg/t] |
| K (K2O) | **3.0 – 9.0** (3 kg K/t maintenance on sandy = ~3.6 kg K2O/t) | 60 – 120 | [T1 Conradie 1994; T2 Haifa 190 kg K2O/20 t = 9.5 kg/t] |
| Ca (CaO) | 2.5 – 4.5 (lime as needed; rarely fertigated) | 50 – 200 (lime) | [T2 Haifa 360 kg CaO/20 t = 18 kg/t] |
| Mg (MgO) | 0.5 – 1.2 | 10 – 25 | [T2 Haifa 48 kg MgO/20 t = 2.4 kg/t] |
| S | 0.4 – 0.8 | 8 – 20 | [T2 IFA] |
| B | 30 – 50 g/ha | — | [T2 Haifa 180 g/20 t = 9 g/t] |
| Zn | 80 – 120 g/ha | — | [T2 Haifa 470 g/20 t = 23 g/t] |
| Cu | 50 – 100 g/ha (spray Cu adds heavily) | — | [T2 Haifa] |
| Fe | foliar correction only | — | [T2 Haifa] |

### Per-stage nutrient demand split (mature vine; % of annual budget)

| Stage | %N | %P2O5 | %K2O | %Ca | Source |
|---|---|---|---|---|---|
| Budbreak → 5-leaf | 5 – 10 | 5 | 5 – 10 | 5 | [T2 UC Davis: "low until flowering, root/wood reserves dominate"] |
| Bloom | 15 – 20 | 15 | 15 – 20 | 15 | [T2 Haifa K split table; UC Davis "bloom = peak uptake rate"] |
| Fruit set → pea size | **25 – 30** | 25 | **25 – 30** | 30 | [T2 UC Davis "highest uptake right after fruit set"] |
| Pea size → veraison | 20 – 25 | 25 | **25 – 30** | 25 | [T2 Haifa K table fruit-growth 25 %] |
| Veraison → harvest | 5 – 10 | 15 | 15 | 15 | [T2 Haifa K table fruit maturation 15 %] |
| **Post-harvest (leaf-active)** | **15 – 20** *(critical for reserves)* | 15 | 5 – 10 | 10 | [T2 UC Davis: "85 % of woody-tissue N reserves from post-harvest leaf re-translocation"] |

### Yield benchmark bands (SA Western Cape)

| Tier | t/ha | Notes | Source |
|---|---|---|---|
| Very low (premium estate) | 4 – 7 | Low-N, low-irrigation; flagship Stellenbosch / Hemel-en-Aarde | [T1 Vinpro] |
| **Premium / fine wine** | **7 – 12** | Most quality wine in WC | [T1 Vinpro] |
| Standard / commercial | 12 – 18 | Bulk + good-quality export | [T1 Vinpro 2023 report avg ~13 t/ha] |
| Bulk (high-yield district) | 18 – 25 | Olifants River / Lower Orange | [T1 Vinpro] |
| Cap for quality (Cab/Shiraz) | ≤ 10 | Above this, varietal expression and concentration drop | [T1 Vinpro field practice] |

### Foliar protocols — wine grape

| Stage | Nutrient | Rate | Purpose | Source |
|---|---|---|---|---|
| Pre-bloom (~14 d) | B (Solubor 21 %) | 1 – 2 kg/ha | Pollen viability, fruit set | [T2 Yara] |
| Pre-bloom + post-set | Zn (chelate or sulphate) | 0.5 – 1.0 kg/ha | Shot-berry prevention; chloroplast | [T2 Yara] |
| Pea size | Mg (MgSO4 or Mg-nitrate) | 5 – 10 kg/ha (1 – 2 % spray) | Inter-veinal chlorosis correction | [T2 Haifa] |
| Veraison (whites only, light) | K (KNO3 or K2SO4) | 3 – 5 kg/ha | Sugar / acid balance — DO NOT overdo on reds (raises pH) | [T2 Haifa] |
| Pre-harvest (Cab/Shiraz only) | Ca (Ca-nitrate or CaCl2) | 2 – 4 kg/ha | Berry-skin firmness, rot suppression — minor for wine vs. table | [T2 Yara] |
| Post-harvest (leaf still green) | Urea LB | 5 kg N/ha | Reserve build-up | [T2 UC Davis] |
| Dormant (Aug, late dormancy) | KNO3 6 % + Dormex 2 % | spray to drip | Bud-break uniformity (Haifa Multi-K trial: +27 % first-pick) | [T2 Haifa] |

### Adjustments

| Factor | Multiplier on baseline | Source / note |
|---|---|---|
| Quality target — flagship wine | × 0.50 – 0.65 N | Conradie + Vinpro field practice; restrain vigour |
| Quality target — premium | × 0.70 – 0.85 N | Vinpro |
| Quality target — bulk | × 1.00 – 1.20 N | Vinpro |
| Vine age 1–3 yr | × 0.30 – 0.50 (all) | [T2 UC Davis] |
| Vine age 4–6 yr (filling) | × 0.70 – 0.90 | [T2 UC Davis] |
| Vine age 7–25 yr (mature) | × 1.0 (baseline) | — |
| Vine age >30 yr (senescent) | × 0.80 | [T2 IPNI] |
| Vigorous rootstock (e.g. Richter 110, 99R) | × 0.85 N | Reduce N to restrain vigour |
| Devigorating rootstock (101-14 Mgt, 3309C) | × 1.10 N | [T1 SAJEV Conradie rootstock study] |
| High-density (>3500 vines/ha) | × 1.10 – 1.20 (per ha basis) | More vines, more demand |
| Drought / dryland | × 0.70 (lower yield expected) | [T1 Conradie SAJEV] |
| Sandy soil (low CEC) | split N into 4+ apps | Leaching risk |
| Saline soil (EC >1.5 dS/m) | avoid Cl carriers; use K2SO4 not KCl | [T2 standard] |
| Granitic / decomposed-granite (Stellenbosch) | × 1.05 K | Lower K-supplying power |

### Notes — wine grape

- **LOW-N RULE:** Conradie's central finding (multiple SAJEV papers 1986–2001): on sandy WC soils, N application beyond ~50 kg/ha actively *hurts* wine quality (raises pH, reduces colour, delays ripening, increases botrytis risk). Engine MUST treat the lower half of the bloom-petiole N band (1.2 – 1.6 % N) as the **target** for premium wine, not the midpoint of the published 1.2 – 2.2 % adequacy range.
- **K balance is delicate.** Excess K → high must pH → flat wines, especially reds. Don't push K above maintenance unless petiole truly deficient.
- **Post-harvest N matters more than people think.** ~85 % of next year's spring growth N comes from re-translocation, not new uptake. Skipping post-harvest N hurts the *next* season's set.
- **Sample petiole at bloom AND veraison** for premium operations. Engine should treat veraison values as more reliable for mobile NPK; bloom for B/Zn diagnosis.
- **OC % is not a nutrient lever for wine grape.** Don't recommend compost / organic carriers to "build OC" on premium wine sites — that's vegetable-grower thinking. Wine grape soils want low–moderate OC.
- **Cultivar nuance** (qualitative — no SA tabulated norms found):
  - *Cabernet Sauvignon, Shiraz:* most N-sensitive; restrain hardest.
  - *Pinotage:* SA-bred, vigorous; very low N.
  - *Chenin Blanc:* tolerates more N than reds; can be pushed for bulk dry-white.
  - *Chardonnay, Sauvignon Blanc:* moderate N; SB benefits from B and S for thiol expression.

---

## Table grape (*Vitis vinifera*) — Crimson Seedless, Thompson Seedless, Flame Seedless, Prime

### Growth stages (Western Cape Hex River + Lower Orange / Northern Cape)

| Month (SA) | Stage | Key process | Source |
|---|---|---|---|
| Aug (Northern Cape) / Sep (Hex) | Budbreak | Hydrogen cyanamide spray for early districts | [T1 SATI] |
| Sep – Oct | Shoot growth | Canopy + first GA sprays (Thompson) | [T1 SATI] |
| Oct – Nov | Bloom | Berry-thinning sprays; Crimson late Oct | [T1 SATI] |
| Nov – Dec | Fruit set, berry sizing | **Peak K demand** (table grapes need MORE K than wine) | [T1 SATI handbook] |
| Dec – Jan | Veraison | Crimson colour development; K + ABA sprays | [T1 SATI] |
| **Late Nov (NC, early) – Apr (Hex, late)** | **Harvest** | NC starts ~last week Nov (Prime); Hex finishes Apr (Crimson) | [T1 SATI] |
| Apr – Jun | Post-harvest, dormancy | Pruning, lime, organic amendments | [T1 SATI] |

### Petiole norms — at fruit set / veraison (SATI 2019 handbook, Table 6)

| Nutrient | Deficient | Sufficient | High / excess | Source |
|---|---|---|---|---|
| N % | <0.8 | 0.9 – 1.3 | >2.0 | [T2 UC Davis veraison / SATI] |
| P % | <0.10 | 0.16 – 0.30 | >0.50 | [T1 SATI handbook] |
| K % | <1.0 | **1.5 – 2.5** *(table grape needs HIGH K)* | >3.5 | [T1 SATI handbook] |
| Ca % | <0.5 | 1.0 – 1.8 | >3.0 | [T1 SATI] |
| Mg % | <0.20 | 0.26 – 0.45 | >0.80 | [T1 SATI] |
| **B (mg/kg)** | **<25** | **30 – 70** | **>150** | [T1 SATI handbook Table 6] |
| **Zn (mg/kg)** | **<15** | **20 – 150** | **>300** | [T1 SATI handbook Table 6] |
| **Mn (mg/kg)** | **<20** | **30 – 60** | **>100** | [T1 SATI handbook Table 6] |
| **Cu (mg/kg)** | **<3** | **5 – 10** | — | [T1 SATI handbook Table 6] |
| Fe (mg/kg) | <30 | 30 – 50 | >150 | [T2 Haifa] |
| Mo (mg/kg) | <0.1 | 0.3 – 1.5 | — | [T2 Haifa] |

### Soil thresholds — table grape (SATI handbook)

| Nutrient | Adequate | Source |
|---|---|---|
| pH (KCl) | 5.5 – 6.5 | [T1 SATI] |
| **P (Bray-1)** | **25 – 35 mg/kg** ("4.5 kg P/ha per 1 mg/kg increase needed", 0–300 mm) | [T1 SATI handbook] |
| **K (NH4-OAc)** | **70 – 120 mg/kg** (regional max varies) | [T1 SATI handbook] |
| **Ca** | **360 – 500 mg/kg** (sandy → clayey) | [T1 SATI handbook] |
| **Mg** | **40 – 120 mg/kg** | [T1 SATI handbook] |
| B (hot water) | ≥ 0.3 mg/kg | [T1 SATI] |
| Mn (DTPA) | ≥ 2.0 mg/kg | [T1 SATI] |
| Zn (DTPA) | ≥ 0.5 mg/kg | [T1 SATI] |
| Cu (DTPA) | ≥ 0.5 mg/kg | [T1 SATI] |

### Crop requirements per ton (Haifa universal grape model, calibrated to 20 t/ha mature table grape)

| Nutrient | kg / ton | kg/ha @ 25 t/ha | Source |
|---|---|---|---|
| N | 4 – 8 (table grapes) | **80 – 160** | [T2 Haifa "N 4–8 kg/t" + UC Davis "table 2.26 lb N/t" baseline] |
| P (as P2O5) | 0.7 – 1.5 (≈ 3.0 kg P2O5/t) | 50 – 80 | [T2 Haifa 60/20] |
| **K (as K2O)** | **3 – 9 (≈ 9.5 kg K2O/t for high-end size targets)** | **150 – 230** | [T2 Haifa 190/20; T1 SATI 3 kg K/t maintenance baseline] |
| Ca (CaO) | 1.5 – 3.0 | 40 – 90 | [T2 Haifa 360 CaO/20 = 18 kg CaO/t — Haifa figure includes lime; functional uptake ~2 kg/t] |
| Mg (MgO) | 0.5 – 1.5 | 10 – 30 | [T2 Haifa 48/20] |
| S | 0.4 – 0.8 | 10 – 20 | [T2 IFA] |
| B | 30 – 50 g/ha | — | [T2 Haifa 180g/20t] |
| Zn | 80 – 120 g/ha | — | [T2 Haifa 470/20] |
| Cu | 50 – 100 g/ha | — | [T2 Haifa] |

### Per-stage demand split — table grape (Haifa K-share table, Table 2)

| Stage | % K2O | Indicative K rate kg/ha (75 t/ha-equivalent demand) | Source |
|---|---|---|---|
| Leaf emergence | 15 | 45 | [T2 Haifa Table 2] |
| Flowering | 20 | 60 | [T2 Haifa] |
| **Fruit set** | **25** | **75** | [T2 Haifa] |
| **Fruit growth** | **25** | **75** | [T2 Haifa] |
| Fruit maturation | 15 | 45 | [T2 Haifa] |

For N: ~10 % budbreak, 20 % bloom, 30 % set–pea, 25 % berry growth, 5 % maturation, 10 % post-harvest.

### Yield benchmarks — table grape SA

| Tier | t/ha | Notes |
|---|---|---|
| Low | 15 – 22 | Older blocks, dryland |
| **Typical export** | **25 – 35** | Hex River, Berg River, Olifants |
| **High-input commercial** | **35 – 50** | Lower Orange irrigated, drip + GA programmes |

Source: [T1 SATI 2023 industry report]

### Foliar protocols — table grape

| Stage | Nutrient | Rate | Purpose | Source |
|---|---|---|---|---|
| Pre-bloom | B | 1 – 2 kg/ha (Solubor 21 %) | Set | [T2 Yara] |
| Bloom + post-set | Zn | 0.5 – 1 kg/ha chelate | Berry uniformity | [T2 Yara] |
| Pea size onwards | **Ca (CaCl2 or Ca-nitrate)** | **3 – 5 kg/ha every 7–10 days × 4–6 sprays** | **Berry-skin firmness, post-harvest shelf-life — table grape critical** | [T1 Yara SA Ca deficiency page; SATI] |
| Pea size – veraison | K (Multi-K, KNO3) | 5 – 10 kg/ha | Berry size + sugar | [T2 Yara, Haifa] |
| Veraison (Crimson, Flame) | K + ABA programme | per label | Colour development on red varieties | [T1 SATI] |
| Mid-season | Mg | 5 kg/ha MgSO4 | Chlorosis correction | [T2 Haifa] |
| Post-harvest | Urea LB | 5 – 8 kg N/ha | Reserves | [T2 UC Davis] |
| Late dormancy | 2 % Dormex + 6 % KNO3 | spray-to-drip | Bud-break uniformity (+27 % first-pick uniformity in Haifa trial) | [T2 Haifa] |

### Adjustments — table grape

| Factor | Multiplier | Source |
|---|---|---|
| Crimson (red, late, big-bunch) | × 1.10 K | Berry size + colour |
| Thompson Seedless (white, GA-treated, biggest berries) | × 1.15 K, × 1.10 Ca | Berry sizing programme |
| Flame Seedless (early red) | × 1.05 K | Early colour need |
| Prime (very early white) | × 1.0 baseline | Earliest harvest |
| Vine age 1–3 | × 0.40 | UC Davis |
| Vine age 4–6 | × 0.75 | UC Davis |
| Mature 7–25 | × 1.0 | — |
| Saline soil / brackish water (Lower Orange) | use K2SO4 not KCl | SATI |
| Sandy (Lower Orange flats) | split into 6+ fertigation events | SATI |
| Hex River clay loam | split into 4 events | SATI |

### Notes — table grape

- **Fundamentally different K target vs wine grape.** Table grape competes on visual berry size and skin colour — K and Ca are the levers. Wine grape K excess is bad; table grape K excess is OK up to ~3 % petiole.
- **Calcium spray programme is non-negotiable** for export shelf-life. SATI/Yara recommend 4–6 Ca sprays from pea size to pre-harvest.
- **Cultivar harvest staggering** allows SA to ship Nov–Apr to EU/UK off-season — Prime first, Crimson last.
- **GA3 sizing programmes (Thompson, Crimson)** raise Ca and K demand by ~10–15 % vs untreated.
- No published tabulated cultivar-specific norm differentials; adjust on quality target and rootstock instead.

---

## Blueberry (*Vaccinium corymbosum* — Northern Highbush; *V. virgatum* — Rabbiteye; SH Southern Highbush dominates SA)

### Growth stages (SA — Western Cape, KZN, Limpopo evergreen)

| Month (SA) | Stage | Source |
|---|---|---|
| Apr – Jun | Floral initiation, dormancy onset (deciduous types); evergreen continues | [T1 Hortgro berry guide] |
| Jul – Aug | Budbreak (early SHB cv. Snowchaser, Jewel start fruiting) | [T1 Berries-for-Africa cv. notes] |
| Aug – Nov | **Harvest window (early SH cultivars)** | [T1 Farmers Weekly SA blueberry guide] |
| Sep – Dec | Vegetative flush, root flush | [T2 OSU Strik berry nutrient guide] |
| Dec – Mar | Continued vegetative growth, flower-bud differentiation | [T2 OSU] |

### Leaf norms — sample at first dormant leaf / late summer (NHB protocol)

| Nutrient | Deficient (<) | Sufficient | Excess (>) | Source |
|---|---|---|---|---|
| **N %** | **1.7** | **1.7 – 2.1** | **2.3** | [T2 MSU Hanson E2011] |
| P % | 0.08 | 0.08 – 0.40 | 0.60 | [T2 MSU E2011] |
| K % | 0.35 | 0.40 – 0.65 | 0.90 | [T2 MSU E2011] |
| Ca % | 0.13 | 0.30 – 0.80 | 1.00 | [T2 MSU E2011] |
| Mg % | 0.10 | 0.15 – 0.30 | — | [T2 MSU] |
| S % | — | 0.12 – 0.20 | — | [T2 MSU] |
| B (ppm) | 18 | 25 – 70 | 200 | [T2 MSU] |
| Cu (ppm) | 5 | 5 – 20 | — | [T2 MSU] |
| Fe (ppm) | 60 | 60 – 200 | 400 | [T2 MSU] |
| Mn (ppm) | 25 | 50 – 350 | 450 | [T2 MSU] |
| Zn (ppm) | 8 | 8 – 30 | 80 | [T2 MSU] |

### Soil thresholds — blueberry (the pH rule is hard)

| Parameter | Adequate | Source |
|---|---|---|
| **pH (water)** | **4.5 – 5.0 (target); 4.0 – 5.5 acceptable** — **HARD CONSTRAINT** | [T2 MSU; T2 OSU; T2 Cornell — universal] |
| OC % | **>3 % preferred** (acid-loving, high-organic-matter rooting medium) | [T2 OSU] |
| P (Bray-1) | 20 – 40 mg/kg | [T2 Cornell] |
| K | 80 – 150 mg/kg | [T2 Cornell] |
| Ca | 250 – 600 mg/kg (lower than most crops — high Ca raises pH) | [T2 Cornell] |
| Mg | 50 – 120 mg/kg | [T2 Cornell] |
| **N form** | **prefer NH4+ (ammonium); avoid NO3- as primary source** | [T2 Cornell, MSU] |

### Crop requirements per ton fruit

| Nutrient | kg / ton | Source |
|---|---|---|
| N | 5 – 8 | [T2 OSU Strik] |
| P (P2O5) | 1.5 – 2.5 | [T2 OSU] |
| K (K2O) | 6 – 10 | [T2 OSU] |
| Ca | 1.0 – 1.5 | [T2 OSU] |
| Mg | 0.5 – 0.8 | [T2 OSU] |
| S | as elemental S to maintain pH (5–10 kg/ha typical) | [T2 MSU] |

### Annual N rate by plant age (mature target ~70 kg N/ha for SHB SA evergreen)

| Plant age (yr) | N kg/ha (actual) | Source |
|---|---|---|
| 1–2 | 15 – 20 | [T2 MSU] |
| 3–4 | 30 – 40 | [T2 MSU] |
| 5–6 | 45 – 55 | [T2 MSU] |
| 7+ (mature) | **60 – 80** | [T2 MSU; converted from MSU's 65 lb/A bench] |

### Per-stage demand split

| Stage | %N | Source |
|---|---|---|
| Pre-budbreak / dormant break | 50 (split half-rate) | [T2 MSU "half before bloom"] |
| Petal fall | 50 (split second half) | [T2 MSU "half at petal fall"] |
| Continuous fertigation (SA evergreen) | 10 % monthly Aug–Apr | [T1 SA practice — Berries for Africa, Hortgro] |

### Yield benchmarks — SHB SA

| Tier | t/ha | Source |
|---|---|---|
| Establishment yr 2–3 | 2 – 5 | [T1 Berries-for-Africa] |
| Mature SHB SA | **10 – 18** | [T1 Berries-for-Africa, Farmers Weekly] |
| High-tunnel intensive | 18 – 25 | [T1 SA industry data] |

### Foliar protocols — blueberry

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Pre-bloom | B | 0.5 – 1 kg/ha Solubor | [T2 OSU] |
| Pre-bloom | Zn | 0.3 – 0.5 kg/ha chelate | [T2 OSU] |
| Mid-season (chlorosis) | Fe-EDDHA | 1 – 2 kg/ha (rare; address pH first) | [T2 OSU] |
| Post-harvest | Urea LB | 3 – 5 kg N/ha | [T2 MSU] |
| Soil amendment | **Elemental S** | 0.7 lb/100 sq ft → ~340 kg/ha to drop pH 5.5 → 4.5 (sandy soil) | [T2 MSU; UGA blueberry fertilization] |

### Adjustments — blueberry

| Factor | Adjust | Source |
|---|---|---|
| Soil pH > 5.5 | apply S; do NOT push N until pH corrected | [T2 MSU "if pH > 5.5 leaves chlorotic"] |
| Sandy / leaching soil | split N into 4–6 fertigation events; use ammonium sulphate | [T2 MSU] |
| Cv. Jewel | + Ca + Zn + amino acid foliar boosted yield 22 % | [T1 Farmers Weekly SA trial] |
| Cv. Snowchaser | same trial showed no response | [T1 Farmers Weekly] |
| Evergreen production (SA, SHB) | continuous fertigation Aug–Apr; total slightly higher than NHB seasonal | [T1 Hortgro] |
| Container / coir / pine-bark substrate | full nutrient supplied via fertigation; soil-test irrelevant | [T1 SA industry standard] |

### Notes — blueberry

- **pH 4.5 is the hardest single constraint in SA agronomy.** No other commercial crop tolerates acid this low. Most SA soils (pH 5.5–7) require massive elemental-S or substrate cultivation (pine bark, coir).
- **NH4+ over NO3-:** blueberry physiology lacks nitrate reductase activity at high efficiency; ammonium sulphate is the canonical N source. Calcium nitrate / KNO3 are sub-optimal.
- **Calcium is low-target.** High Ca → high pH → blueberry death. Don't push Ca above 600 mg/kg soil.
- **Root sensitivity:** no root hairs, shallow fine roots <130 d lifespan — implies frequent low-rate fertigation > occasional bulk applications.
- **SA cv. landscape:** SHB (Snowchaser, Jewel, Suziblue, Star, Emerald, Misty, Bluecrop hybrids) dominate; rabbiteye marginal in Limpopo. Almost all commercial SA production is now substrate (coir/pine-bark) under tunnels — soil-based less common.

---

## Raspberry (*Rubus idaeus*) — primocane + floricane

### Growth stages (SA — limited but expanding industry; cool sites in WC, Mpumalanga, KZN highveld)

| Month (SA) | Stage | Source |
|---|---|---|
| Jul – Aug | Dormancy → budbreak (floricane) | [T2 OSU EM8903] |
| Aug – Sep | Primocane emergence | [T2 OSU] |
| Sep – Oct | Floricane bloom | [T2 NC State caneberry guide] |
| Oct – Dec | Floricane harvest | [T2 NC State] |
| Dec – Apr | Primocane bloom + harvest (primocane-fruiting types) | [T2 NC State] |
| Apr – Jul | Floricane removal, primocane management | [T2 NC State] |

### Leaf nutrient sufficiency — primocane leaf, late Jul – early Aug NH equivalent (SA: ~late Jan – early Feb)

| Nutrient | Sufficient range | Source |
|---|---|---|
| N % | 2.50 – 3.50 | [T2 NC State Table 11-2] |
| P % | 0.15 – 0.25 | [T2 NC State] |
| K % | 0.90 – 1.50 | [T2 NC State] |
| Ca % | 0.48 – 1.00 | [T2 NC State] |
| Mg % | 0.30 – 0.45 | [T2 NC State] |
| S % | 0.17 – 0.21 | [T2 NC State] |
| B ppm | 25 – 85 | [T2 NC State] |
| Cu ppm | 8 – 15 | [T2 NC State] |
| Fe ppm | 60 – 100 | [T2 NC State] |
| Mn ppm | 50 – 250 | [T2 NC State] |
| Zn ppm | 20 – 70 | [T2 NC State] |

> **GAP — no SA-published leaf norms for raspberry.** Use NC State / OSU.

### Soil thresholds — raspberry (NC State)

| Parameter | Adequate | Source |
|---|---|---|
| pH | 5.5 – 6.5 | [T2 NC State] |
| P (soil) | 20 – 30 mg/kg | [T2 NC State] |
| K | 100 – 180 mg/kg | [T2 NC State] |
| OC % | >2 % preferred | [T2 OSU] |

### Crop nutrient removal per ton fruit

| Nutrient | kg / ton (converted from NC State 11–18 lb/ac N at 5 t/ac) | Source |
|---|---|---|
| N | 1.0 – 1.5 (fruit removal); 4 – 8 plant demand | [T2 NC State] |
| P (P2O5) | 0.4 – 0.8 | [T2 NC State] |
| K (K2O) | 1.0 – 1.7 | [T2 NC State] |
| Ca | 0.1 – 0.2 | [T2 NC State] |
| Mg | 0.1 – 0.4 | [T2 NC State] |

### Annual N rate

| Stage | N kg/ha | Source |
|---|---|---|
| Establishment year | 25 – 60 | [T2 NC State 25–50 lb/A] |
| Year 2 + (mature) | **40 – 100** | [T2 NC State 40–80 lb/A; OSU 56–90 kg/ha] |

### Per-stage demand split — raspberry

| Stage | %N | Source |
|---|---|---|
| Floricane budbreak / primocane emergence | 40 – 50 | [T2 NC State "early spring ½ – ⅔"] |
| Through bloom – early harvest (fertigation) | 30 | [T2 OSU "fertigation weekly bloom → harvest"] |
| Post-harvest | 20 – 30 | [T2 NC State, OSU "post-harvest 10–30 lb"] |

### Yield benchmarks — raspberry SA (small industry, mostly tunnel)

| Tier | t/ha | Source |
|---|---|---|
| Field establishment | 3 – 6 | [T2 OSU baseline] |
| Tunnel mature | 10 – 18 | [T2 NC State / industry] |

### Foliar protocols — raspberry

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Pre-bloom | B | 0.5 – 1 kg/ha Solubor | [T2 NC State] |
| Pre-bloom | Zn | 0.3 – 0.5 kg/ha | [T2 NC State] |
| Bloom – fruit | Ca (CaCl2) | 2 – 4 kg/ha — fruit firmness | [T2 NC State] |

### Adjustments — raspberry

| Factor | Adjust | Source |
|---|---|---|
| Primocane-fruiting types (Heritage, Polka) | +20 % N (longer fruiting season) | [T2 OSU] |
| Floricane-fruiting only | baseline | — |
| Sandy / drip-fertigated | weekly low-dose | [T2 OSU] |

### Notes — raspberry

- SA raspberry industry is small and tunnel-dominated; treat as minor crop and pull from US/Oregon norms with caution.
- Primocane vs floricane distinction matters for timing — floricane = previous-season cane fruiting; primocane = current-season cane fruiting (extended late season).
- Post-harvest N important: floricane senescence translocates ~50 % of leaf N back to roots/crown. (NC State / OSU.)

---

## Strawberry (*Fragaria × ananassa*) — short-day cultivars dominate SA (Festival, Camarosa, Sweet Charlie); day-neutral (Albion) in highveld

### Growth stages (SA — annual replant, plug + bare-root; main season Apr–Oct WC, year-round in tunnels)

| Month (SA) | Stage | Source |
|---|---|---|
| Mar – Apr | Plant establishment (plugs, bare-root from cold-store) | [T1 SA strawberry industry practice] |
| Apr – May | Crown growth, root development | [T2 NCDA] |
| **May – Jun** | **Floral initiation (short-day photoperiod trigger)** | [T2 UC Davis Bolda] |
| Jun – Jul | Bloom | [T2 NCDA] |
| **Jul – Oct** | **Main harvest (WC field)** | [T1 SA growers] |
| Year-round | Tunnel / hydroponic continuous | [T1 SA] |

### Leaf nutrient sufficiency (most-recent mature trifoliate leaf at peak harvest)

| Nutrient | Deficient | Sufficient | Excess | Source |
|---|---|---|---|---|
| N % | <2.5 | 3.0 – 4.0 | >4.5 | [T2 NCDA strawberry manual] |
| P % | <0.10 | 0.20 – 0.40 | >0.50 | [T2 NCDA] |
| K % | <1.0 | 1.1 – 2.5 | >3.0 | [T2 NCDA] |
| Ca % | <0.4 | 0.7 – 1.7 | >2.0 | [T2 NCDA] |
| Mg % | <0.20 | 0.30 – 0.50 | >0.80 | [T2 NCDA] |
| S % | <0.10 | 0.15 – 0.40 | — | [T2 NCDA] |
| B ppm | <20 | 30 – 70 | >100 | [T2 NCDA] |
| Cu ppm | <3 | 5 – 15 | — | [T2 NCDA] |
| Fe ppm | <40 | 60 – 250 | — | [T2 NCDA] |
| Mn ppm | <30 | 50 – 200 | >500 | [T2 NCDA] |
| Zn ppm | <15 | 20 – 50 | >80 | [T2 NCDA] |

### Petiole sap (UC Davis — fertigation tracking)

| Stage | NO3-N (ppm) target | PO4-P (ppm) target | Source |
|---|---|---|---|
| Establishment | 4000 – 5000 | >1500 | [T2 UC Davis] |
| Early fruiting | 3000 – 4000 | >1200 | [T2 UC Davis] |
| Late harvest | ~500 (declining is normal) | >800 | [T2 UC Davis] |

### Soil thresholds — strawberry

| Parameter | Adequate | Source |
|---|---|---|
| pH | 6.0 – 6.5 | [T2 TPS Lab] |
| P | 25 – 60 mg/kg | [T2 NCDA] |
| K | 120 – 200 mg/kg | [T2 NCDA] |
| Ca | ~1000 mg/kg target | [T2 TPS Lab] |
| Mg | ~150 mg/kg | [T2 TPS Lab] |
| OC % | >2 % | [T2 NCDA] |

### Crop nutrient requirements per ton fruit

| Nutrient | kg / ton | Source |
|---|---|---|
| N | 4 – 6 | [T2 Haifa strawberry guide] |
| P (P2O5) | 1.5 – 2.5 | [T2 Haifa] |
| K (K2O) | 6 – 10 | [T2 Haifa] |
| Ca | 1.0 – 2.0 | [T2 Haifa] |
| Mg | 0.4 – 0.8 | [T2 Haifa] |

### Annual rate (field, SA short-day system)

| Nutrient | Rate kg/ha | Source |
|---|---|---|
| N | **150 – 220 (new); 75 – 120 (carry-over)** | [T2 TPS Lab] |
| P (P2O5) | 60 – 100 | [T2 TPS] |
| K (K2O) | **150 – 250** | [T2 TPS] |

### Per-stage demand split — strawberry (fertigation)

| Stage | %N | %K2O | Source |
|---|---|---|---|
| Establishment (1st 6 wk) | 25 | 15 | [T2 NCDA] |
| Vegetative + crown | 25 | 20 | [T2 NCDA] |
| Bloom | 15 | 20 | [T2 NCDA] |
| **Fruit fill / harvest (most of season)** | **30 – 35** | **40 – 45** | [T2 NCDA] |

### Yield benchmarks — SA strawberry

| Tier | t/ha | Source |
|---|---|---|
| Field, open-pollinated | 15 – 25 | [T2 industry] |
| Tunnel + drip | 30 – 50 | [T2 Haifa] |
| Hydroponic (substrate, NFT) | 50 – 80 | [T2 Haifa SA market] |

### Foliar protocols — strawberry

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Pre-bloom | B | 0.3 – 0.5 kg/ha Solubor | [T2 UC Davis] |
| Bloom – early fruit | **Ca (CaCl2)** | **2 – 4 kg/ha weekly** — firmness, shelf-life | [T2 UC Davis] |
| Mid-season (chlorosis) | Fe-EDDHA | 1 – 2 kg/ha | [T2 NCDA] |

### Adjustments — strawberry

| Factor | Adjust | Source |
|---|---|---|
| Day-neutral (Albion) cv. — extended fruiting | +20 % seasonal N | [T2 UC Davis Bolda] |
| Short-day (Camarosa, Festival) | baseline | [T2 UC Davis] |
| Hydroponic / substrate | full nutrient via solution; ignore soil-test | [T2 Haifa] |
| Sandy soil | split into 8+ events; use slow-release for K | [T2 Haifa CRF guide] |
| Plastic-mulch SA (fumigated, raised bed) | full fertigation; reduce broadcast P/K pre-plant | [T1 SA practice] |

### Notes — strawberry

- SA strawberry production splits two ways: **(a) field / plastic-mulch, short-day cv. (Camarosa, Festival, Sweet Charlie)** — main crop Jul–Oct in WC, May–Sep in Mpumalanga; **(b) tunnel hydroponic / substrate** day-neutral (Albion) — year-round.
- Calcium is the **single most important late-season nutrient** for shelf-life and resistance to soft rot. Weekly Ca foliar from first fruit to last pick is standard SA practice.
- Petiole NO3-N decline through the season is **normal and desired** — don't fertigate to maintain 4000 ppm late-season; berries will be soft.
- GAP: no SA-published leaf norms — use UC Davis / NCDA.

---

## Cross-crop policy box for the engine

1. **Wine grape low-N rule (HARD).** When `crop=wine_grape AND quality_target IN (premium, flagship)`:
   - Target petiole bloom N at **lower 25 % of band** (1.2 – 1.5 %) not midpoint.
   - Cap annual N at 35 – 50 kg/ha regardless of yield demand.
   - Engine narrative MUST state: "N restraint is intentional for wine quality (Conradie 1994; VinPro guideline)."

2. **Blueberry pH rule (HARD).** When `crop=blueberry`:
   - If soil pH > 5.5 → first recommendation is **elemental S (or substrate switch)**, NOT NPK.
   - N source must be **NH4+ (ammonium sulphate, urea)**, never primarily nitrate.
   - Ca cap: don't push above 600 mg/kg soil.

3. **Table grape K + Ca rule.** When `crop=table_grape`:
   - K target at upper half of band (export size).
   - Ca foliar programme (4–6 sprays pea-size to pre-harvest) is standard, not optional.

4. **Berry crops fertigation default.** Strawberry / blueberry / raspberry → split annual N into 6 – 12 events; broadcast bulk N is wrong.

5. **Wine grape OC quirk.** Don't penalise low-OC soils for wine grape — premium quality often requires it.

---

## Top 3 sources used

1. **Conradie 1994** (SAJEV, multiple papers) — SA-canonical wine grape petiole/soil norms; cited universally by VinPro and downstream lab interpretations. Petiole-at-bloom + N restraint for quality are his contributions. *(Multiple SAJEV vols 7–22 — primary research not openly downloadable; used via downstream citations in Wineland and SATI handbook.)*
2. **SATI / Villa Crop Protection 2019 — *Fertilisation Guidelines for the Table Grape Industry*** — only SA-comprehensive table grape handbook; Table 6 micronutrient norms + soil thresholds extracted.
3. **Penn State Extension + Ohio State HYG-1438 + UC Davis Geisseler** — international Tier 2 best-in-class for petiole bloom + veraison norms and N partitioning by stage. Used to fill what Conradie did not publish openly.

## Gaps (no data found / GAP rows)

- **Conradie's actual bloom petiole macronutrient table (% N, % P, % K)** — paywalled in SAJEV vols 7, 8, 22; only paraphrased in downstream lit. Penn State/Ohio used as adequate proxy.
- **VinPro current published nutrient guideline numbers** — VinPro's modern advisory is consultant-delivered, not in a single open document. Wineland and ARC-Infruitec articles paraphrase.
- **Cultivar-specific SA petiole differentials** (Cab vs Shiraz vs Chenin) — none published; qualitative cv. notes only.
- **Hortgro published blueberry SA norms** — Hortgro covers stone/pome/citrus deciduous; berry-specific guidance comes from private agronomists (Berries for Africa, Fall Creek SA), not open.
- **SA raspberry leaf norms** — none found; NC State / OSU used.
- **SA strawberry leaf norms** — none found; UC Davis / NCDA used.
- **Crimson / Thompson / Flame cv-specific differential nutrient tables** — none in SATI handbook (handbook is generic to table grape).
- **Hex River vs Lower Orange district demand differential** — referenced qualitatively only.

## Sources consulted (numbered, with tier)

1. [T1] Wineland (SA wine industry magazine) — Conradie's NPK/grapevine performance series — https://www.wineland.co.za/effect-nitrogen-phosphorus-potassium-fertilisation-soil-grapevine-performance-part-1/
2. [T1] Wineland — *When and how to fertilise* — https://wineland.co.za/when-and-how-to-fertilise/
3. [T1] Wineland — *Organic wine grape monitoring guidelines* — https://www.wineland.co.za/guidelines-for-monitoring-soil-fertility-plant-nutrient-status-and-compost-quality-in-organic-wine-grape-production-systems/
4. [T1] SATI — *Fertilisation Guidelines for the Table Grape Industry* (Villa) — https://user-hpa96tt.cld.bz/FERTILISATION-GUIDELINES-FOR-THE-TABLE-GRAPE-INDUSTRY
5. [T1] SATI handbook product page — https://www.satgi.co.za/product/fertilisation-guidelines-for-the-table-grape-industry/
6. [T1] VinPro — *Handbook for Irrigation of Wine Grapes in SA* — https://user-hpa96tt.cld.bz/Handbook-for-irrigation-of-wine-grapes-in-SA-digital
7. [T1] VinPro — 2023 Harvest report — https://vinpro.co.za/wp-content/uploads/2023/05/South-African-Wine-Harvest-Report-2023.pdf
8. [T1] SAJEV — Conradie *Timing of N Fertilisation, Poultry Manure, Sandy Soil* I & II — https://www.journals.ac.za/index.php/sajev/article/view/2192 + 2193
9. [T1] SAJEV — *Utilisation of N by the Grape-vine as Affected by Time of Application and Soil Type* (Conradie) — https://www.journals.ac.za/index.php/sajev/article/view/2331
10. [T1] SAJEV — *Effects of Rootstock on Grapevine Performance, Petiole and Must Composition* — https://www.journals.ac.za/index.php/sajev/article/view/1399
11. [T1] Yara SA — Improving table grape quality — https://www.yara.co.za/crop-nutrition/table-grape/improving-table-grape-quality/
12. [T1] Yara SA — Calcium deficiency in table grape — https://www.yara.co.za/crop-nutrition/table-grape/nutrient-deficiencies-table-grape/calcium-deficiency-table-grape/
13. [T1] Kynoch SA — Best fertiliser for grapes — https://www.kynoch.co.za/fertiliser-for-grapes/
14. [T1] Farmers Weekly SA — *Optimising blueberry production* — https://www.farmersweekly.co.za/crops/fruit-and-nuts/a-guide-to-optimising-blueberry-production/
15. [T1] Berries for Africa — Blueberries — https://www.berriesforafrica.co.za/our-berry-plants/blueberries/
16. [T1] Fall Creek Nursery SA — Growing blueberries in SA — https://www.fallcreeknursery.com/commercial-fruit-growers/south-africa
17. [T1] SA Wine — Effect of temperature on grapevine phenology — https://sawine.co.za/effect-of-temperature-on-grapevine-phenology/
18. [T2] UC Davis (Geisseler) — Grapevine nutrient management — http://geisseler.ucdavis.edu/Guidelines/Grapevines.html
19. [T2] UC Davis / CDFA FREP — Grapevine N uptake & partitioning — https://www.cdfa.ca.gov/is/ffldrs/frep/FertilizationGuidelines/N_Grapevines.html
20. [T2] Penn State Extension — Fundamentals of grapevine tissue sampling — https://extension.psu.edu/the-fundamentals-of-grapevine-tissue-sampling-for-nutrient-analysis
21. [T2] Ohio State HYG-1438 — Grapevine petiole sampling and analysis — https://ohioline.osu.edu/factsheet/hyg-1438
22. [T2] Haifa — Vineyard fertilization recommendation — https://www.haifa-group.com/complete-haifa-recommendation-fertilization-vineyards
23. [T2] Haifa — Strawberry CRF — https://www.haifa-group.com/sites/default/files/2024-03/CRF-for-strawberries-Updated.pdf
24. [T2] Haifa — Crop guide strawberry — https://www.haifa-group.com/crop-guide/vegetables/strawberry-fertilizer/crop-guide-strawberry-1
25. [T2] Advanced Viticulture — Fertilizer applications throughout season — https://advancedvit.com/season-of-nutrition/
26. [T2] OENO One — *Understanding and managing N nutrition in grapevine* — https://oeno-one.eu/article/view/3866
27. [T2] AWRI viti-notes Petiole analysis (PDF, partial) — https://www.awri.com.au/wp-content/uploads/5_nutrition_petiole_analysis.pdf
28. [T2] MSU E2011 (Hanson) — Managing nutrition of highbush blueberries — https://www.canr.msu.edu/resources/managing_the_nutrition_of_highbush_blueberries_e2011
29. [T2] Cornell — Soil test interpretation blueberries — http://hort.cornell.edu/gardening/soil/blueberries.pdf
30. [T2] OSU — Bernadine Strik nutrient management berry crops — https://agsci.oregonstate.edu/sites/agscid7/files/horticulture/berry/nutrient_management_berry_crops_osu.pdf
31. [T2] OSU EM 8918 — Nutrient management for blueberries — https://ir.library.oregonstate.edu/downloads/6d56zx00s
32. [T2] OSU EM 8903 — Nutrient management of raspberries — https://extension.oregonstate.edu/sites/extd8/files/catalog/auto/EM8903.pdf
33. [T2] NC State — Caneberry fertility management — https://content.ces.ncsu.edu/southeast-regional-caneberry-production-guide/fertility-management
34. [T2] NCDA strawberry fertility manual — https://www.ncagr.gov/ncdacs-strawberry-fertility-manual/open
35. [T2] UC Davis — Strawberry fertilization guidelines — http://geisseler.ucdavis.edu/Guidelines/Strawberry.html
36. [T2] UGA — Suggested blueberry fertilization timings and rates — https://fieldreport.caes.uga.edu/wp-content/uploads/2025/08/C-1163_1.pdf
37. [T2] UGA Krewer / NeSmith — Blueberry fertilization in soil — https://smallfruits.org/files/2019/06/blueberryfert.pdf
38. [T2] Southern Region Small Fruit Consortium — Strawberry tissue testing — https://smallfruits.org/2022/04/optimize-strawberry-fertility-with-plant-tissue-testing/
39. [T2] TPS Lab — Strawberries plant nutrition notes — https://www.tpslab.com/strawberries-plant-nutrition-notes
40. [T3] Bell & Henschke (2005) — *Implications of N nutrition for grapes, fermentation and wine* — Aust J Grape & Wine Res — https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1755-0238.2005.tb00028.x
41. [T3] Williams & Fidelibus — *Nitrogen requirements of table grape* — https://ives-openscience.eu/wp-content/uploads/2023/08/WILLIAMS-and-FEDELIBUS.pdf
42. [T3] Schreiner et al. — *N, P, K supply to Pinot noir grapevines* — AJEV 2013 — https://www.ars.usda.gov/ARSUserFiles/5018/PDF/2013/2013%20AJEV%2064-26-38.pdf
43. [T3] *Leaf tissue macronutrient standards for NHB grown in contrasting environments* — Plants 2022 — https://www.mdpi.com/2223-7747/11/23/3376
