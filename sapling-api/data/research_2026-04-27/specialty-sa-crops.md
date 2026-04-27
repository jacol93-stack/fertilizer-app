# Specialty SA Crops — Citation-backed Data Extract

Compiled 2026-04-27 for Sapling fertilizer recommendation engine seeding.
Source tier coding: T1 = SA institutional (SASRI / DALRRD / KZN-DARD / SA peer-reviewed),
T2 = international institutional (UF/IFAS, NC State, AHDB, Cotton Foundation, Haifa, FAO, Yara),
T3 = peer-reviewed journal / textbook fallback.

> Engine notes:
> - **Rooibos** and **Lucerne** are nitrogen-fixing legumes — engine MUST treat synthetic N target as 0 (rooibos) or starter-only (lucerne, ≤40 kg N/ha establishment). Hard-code this exception or output target_n_kg_ha = NULL with `legume_nfix = true` flag.
> - **Sugarcane** uses both Truog-P and Ambic-2 in SA (NOT Bray-1) — the SASRI calibration table is the canonical reference. Engine should accept either extractant for cane.
> - **Tobacco** uses MOP cautiously — chloride toxicity for burn quality. Prefer SOP for K above 30 kg K2O/ha.
> - **Cotton** boron is critical — soil B <0.25 ppm = mandatory broadcast B.

---

## Sugarcane (Saccharum officinarum × spp. hybrids) — perennial, 12-mo cycle, plant + 4-6 ratoons

### Growth stages

| Cycle stage | DAP | Months SA | Key process | Source |
|---|---|---|---|---|
| Germination / sprouting | 0–60 | Sept–Oct (plant cane) | Bud burst from setts; first leaves | [T2 EOS Sugarcane Manual] |
| Tillering | 60–150 | Nov–Jan | Multi-stem formation; tiller stabilisation | [T2 EOS Sugarcane Manual] |
| Grand growth (elongation) | 150–240 | Feb–Apr | Stalk elongation; ~4-5 internodes/month; peak N-K uptake | [T2 EOS Sugarcane Manual] [T2 IFAS SC075] |
| Maturation / ripening | 240–360+ | May–Aug | Sucrose accumulation; reduced N drives ripening; K critical | [T1 SASRI IS 12.1 Ripening] |
| Ratoon initiation | 0–60 post-cut | Variable | New shoots from stubble; higher early N demand than plant cane | [T1 SASRI Crop Nutrition page] |

### Leaf norms (TVD = top visible dewlap leaf, sampled grand-growth ~4-6 mo)

SA leaf K threshold value differs from US: SASRI uses **1.05 % K** as critical [T1 SASRI / Maharaj 2023 MDPI]. Macro/micro values below from UF IFAS SC075 Critical Value approach (consistent with SASRI ranges where overlap exists).

| Nutrient | Critical (CNL) | Adequate / Optimum | High | Source |
|---|---|---|---|---|
| N | 1.80 % | 2.00–2.60 % | >2.60 % | [T2 IFAS SC075] |
| P | 0.19 % | 0.22–0.30 % | >0.30 % | [T2 IFAS SC075] |
| K | 0.90 % (UF) / **1.05 % (SASRI)** | 1.00–1.60 % | >1.60 % | [T1 SASRI] [T2 IFAS SC075] |
| Ca | 0.20 % | 0.20–0.45 % | — | [T2 IFAS SC075] |
| Mg | 0.13 % | 0.15–0.32 % | >0.32 % | [T2 IFAS SC075] |
| S | 0.13 % | 0.13–0.18 % | — | [T2 IFAS SC075] |
| Fe | 50 mg/kg | 55–105 | >105 | [T2 IFAS SC075] |
| Mn | 16 mg/kg | 20–100 | >100 | [T2 IFAS SC075] |
| Zn | 15 mg/kg | 17–32 | >32 | [T2 IFAS SC075] |
| Cu | 3 mg/kg | 4–8 | >8 | [T2 IFAS SC075] |
| B | 4 mg/kg | 15–20 | — | [T2 IFAS SC075] |
| Mo | 0.05 mg/kg | — | — | [T2 IFAS SC075] |

Sample timing: middle third of TVD blade, 25 leaves per composite, during grand-growth phase (Feb–Apr in SA).

### Soil thresholds (SA SASRI calibration — Truog or Ambic-2 P, AMBIC K/Ca/Mg)

| Nutrient | Method | Deficient | Adequate / Target | High | Source |
|---|---|---|---|---|---|
| P (plant cane) | Modified Truog | <28 mg/L → 183 kg P2O5/ha needed | ~206 kg P2O5/ha equivalent ≈ 60–80 mg P/kg | >206 mg/L equiv | [T1 FAO Annex 1 SA SASRI calibration] |
| P (ratoon) | Modified Truog | <70 mg/L | ~70 mg/L target | — | [T1 FAO Annex 1 SA SASRI] |
| K | AMBIC | <0.10 cmol+/kg (low) | 0.15–0.25 cmol+/kg | >0.25 | [T1 SASRI Crop Nutrition] |
| Ca | AMBIC | <2 cmol+/kg | 4–8 cmol+/kg | — | [T1 SASRI Crop Nutrition] |
| Mg | AMBIC | <0.4 cmol+/kg | 0.8–1.5 cmol+/kg | — | [T1 SASRI Crop Nutrition] |
| pH (KCl) | — | <4.0 (Al toxicity) | 4.5–5.5 | >6.5 | [T1 SASRI Crop Nutrition] |
| OC % | Walkley-Black | <2 % (high N response likely) | 2–4 % | >4 % (low N response) | [T1 SASRI Crop Nutrition / N-min categories] |

PRF (phosphorus requirement factor) range for SA cane soils: **2.3–30.3 kg/ha per mg P/L** (Truog), **2.0–17.7 kg/ha per mg P/L** (Bray-1), **2.5–37.9 kg/ha per mg P/L** (Ambic-2) [T1 UKZN Researchspace 2014 PhD on SA cane P calibration].

### Crop requirements per ton cane (Haifa global, cross-checked Australian SRA)

| Nutrient | kg/t cane | Source |
|---|---|---|
| N | 1.0 (plant) – 1.25–1.50 (ratoon) per t expected yield | [T1 SASRI rule] [T2 Haifa] |
| N (uptake basis) | 1.4 kg N/t | [T2 Haifa] |
| P (P2O5) | 0.3 (P) ≈ 0.7 P2O5 | [T2 Haifa] |
| K (K2O) | 2.6 K2O | [T2 Haifa] |
| Ca | ~0.5 (varies by variety) | [T3 derived] |
| Mg (MgO) | 0.75 | [T2 Haifa] |
| S | 0.35 | [T2 Haifa] |

### Per-stage nutrient demand split (12-mo plant cane)

| Stage | %N | %P2O5 | %K2O | Source |
|---|---|---|---|---|
| Germination 0-60 d | 5 | 100 (banded at planting) | 30 (band) | [T2 Haifa, T2 IFAS] |
| Tillering 60-150 d | 35 | 0 | 25 | [T2 Haifa] |
| Grand growth 150-240 d | 55 | 0 | 35 | [T2 Haifa] |
| Maturation 240-360 d | 5 (taper for ripening) | 0 | 10 | [T1 SASRI IS12.1 Ripening principle — late N suppresses sucrose] |

Application rule (SASRI): all N within 3-4 months for 12-mo crop; ratoon N apply when shoots ~0.5 m high. [T1 SASRI / T2 IFAS SC101]

### Yield benchmarks (SA t cane / ha)

- Low (rainfed marginal): 40–60 t/ha
- Typical (rainfed Mpumalanga / KZN coast): 70–90 t/ha
- High (irrigated Pongola, Komati): 100–140 t/ha
[T1 SASRI Crop Performance page]

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Tillering / grand-growth (years 1-2 stand) | K (KNO3) | 2 % ground / 10 % aerial spray | [T2 Haifa Bonus] |
| Pre-maturation | K | 4 % ground / 12-15 % aerial | [T2 Haifa Bonus] |
| Series | — | 3-4 sprays at 3-4 wk intervals | [T2 Haifa] |

### Adjustments

| Factor | Multiplier | Source |
|---|---|---|
| Ratoon vs plant cane N | 1.25–1.50× plant rate | [T2 Haifa, FAO Annex 1] |
| Irrigated vs dryland N | +20 kg N/ha | [T1 FAO Annex 1 SA SASRI] |
| Soil OC <2 % (low N-min) | full N rate | [T1 SASRI categorisation] |
| Soil OC >4 % | reduce N up to 50 % | [T1 SASRI categorisation] |
| Clay >40 % + high base sat | K up to 300 kg K2O/ha | [T1 FAO Annex 1] |

### Notes

- SASRI uses **Truog-P and Ambic-2 K/Ca/Mg/Na** — engine schema must support these (NOT Bray-1 as default).
- Late-season N must be tapered to allow sucrose accumulation; chemical ripeners (glyphosate at 0.4 L/ha) used on cane <12 mo at maturation [T1 SASRI IS 12.1].
- K critical for sucrose: leaf K <1.05 % triggers SASRI K sufficiency flag.
- N response strongly depends on soil OC class (4 categories) — not yield band alone.

### Sources consulted

1. [T1] SASRI Crop Nutrition — https://sasri.org.za/crop-nutrition/
2. [T1] SASRI IS 12.1 Principles of Chemical Ripening — https://sasri.org.za/wp-content/uploads/Information_Sheets/IS_12.1-Principles-underlying-chemical-ripening.pdf
3. [T1] SASRI IS 7.10 Soil Sampling — https://sasri.org.za/wp-content/uploads/Information_Sheets/IS_7.10-Soil-sampling.pdf
4. [T1] FAO Annex 1 Fertilizer Recommendations for Sugar Cane (SA SASRI calibration) — https://www.fao.org/4/y5998e/y5998e0c.htm
5. [T1] Maharaj et al. 2023 MDPI Agronomy 13:1969 — Effect of K Application Rates on Sugarcane Yield (SA non-exchangeable K).
6. [T1] UKZN Researchspace PhD — Factors Affecting P Requirements for SA Sugarcane Soils.
7. [T2] UF IFAS SC075 Sugarcane Plant Nutrient Diagnosis — https://ask.ifas.ufl.edu/publication/SC075
8. [T2] UF IFAS AG345 Sugarcane Nutrient Management Using Leaf Analysis — https://ask.ifas.ufl.edu/publication/AG345
9. [T2] UF IFAS SC028 Florida Sugarcane Nutritional Requirements — https://ask.ifas.ufl.edu/publication/SC028
10. [T2] Sugar Research Australia 2022 Nutrition Manual — https://sugarresearch.com.au/wp-content/uploads/2022/04/2022_SRA-Nutrition-Manual_F2.pdf
11. [T2] Haifa Group Sugarcane Crop Guide — https://www.haifa-group.com/using-right-fertilizers-order-provide-sugar-cane-necessities

---

## Lucerne / Alfalfa (Medicago sativa) — perennial legume forage, 4–8 cuts/year, N-fix capable

### Growth stages (per cut cycle, ~28-35 d regrowth)

| Stage | Day from cut | Key process | Source |
|---|---|---|---|
| Vegetative regrowth | 0–14 | Crown bud expansion; carbohydrate drawdown | [T2 Nutrien-Ekonomics] |
| Mid-vegetative | 14–21 | Stem elongation; N-fix peak | [T2 PSU Extension] |
| Late vegetative / early bud | 21–28 | Flower bud initiation | [T2 PSU Extension] |
| Early bloom 10 % | 28–35 | **Optimal cut window** — yield × quality balance | [T2 PSU Extension, T2 Iowa State] |
| Late bloom / seed set | 35+ | Quality decline (fibre ↑); avoid in production cuts | [T2 PSU Extension] |

Annual structure (SA): autumn establishment; first cut at late-bud (60–70 days post-emergence); 4-8 cuts during October–April with 32-35 d intervals; final cut early autumn to allow root reserve build-up.

### Leaf norms (top 4-6 inches sampled prior-to or at 1/10 bloom)

| Nutrient | Deficient | Adequate / Sufficient | High | Source |
|---|---|---|---|---|
| N | <3.00 % | 3.00–5.00 % | >5.00 % | [T2 UGA Plant Nutrient pub] |
| P | <0.25 % | 0.25–0.70 % | >0.70 % | [T2 UGA] |
| K | <2.00 % | 2.00–3.50 % | >3.50 % | [T2 UGA] |
| Ca | <0.80 % | 0.80–3.00 % | — | [T2 UGA] |
| Mg | <0.25 % | 0.25–1.00 % | >1.00 % | [T2 UGA] |
| S | <0.25 % | 0.25–0.50 % | >0.50 % | [T2 UGA] |
| Mn | <25 mg/kg | 25–100 | >100 | [T2 UGA] |
| Fe | — | 30–250 mg/kg | — | [T2 UGA] |
| B | <20 mg/kg | 20–80 | >80 | [T2 UGA] |
| Cu | — | 5–30 mg/kg | — | [T2 UGA] |
| Zn | ≤10 (def) / 11–19 (low) | 20–70 mg/kg | — | [T2 UGA] |
| Mo | <1 mg/kg | 1–5 | — | [T2 UGA] |

### Soil thresholds (SA NWPG / Lusern.org calibration)

| Nutrient | Method | Deficient | Adequate (legume target) | High | Source |
|---|---|---|---|---|---|
| P | Bray-1 | <15 mg/kg | **≥25 mg/kg for legumes** | >40 | [T1 NWPG SA Planted Pasture & Lucerne] |
| K | Ammonium acetate | <0.20 cmol+/kg | 0.30 cmol+/kg | >0.40 | [T1 Lucerne Mgmt / NWPG SA] |
| S | KCl-40 / Mehlich | <8 mg/kg | ≥10 mg/kg | >25 | [T1 Lucerne Mgmt] |
| Ca | NH4OAc | <4 cmol+/kg | 5–10 | — | [T2 AHDB / Spectrum] |
| Mg | NH4OAc | <0.4 cmol+/kg | 0.8–1.5 | — | [T2 AHDB] |
| pH (KCl) | — | <5.0 (lime mandatory) | **6.0–6.8** | >7.5 | [T1 NWPG SA / DALRRD Lucerne king] |
| OC % | — | <1 % | 1.5–3 % | — | [T2 AHDB] |

### Crop requirements per ton dry matter

| Nutrient | kg/t DM | Source |
|---|---|---|
| N (in plant tissue, fixed not added) | 25–30 | [T1 NWPG SA] |
| P | 2.7 (NWPG) / 8–10 (AHDB removal) | [T1 NWPG SA, T2 AHDB] |
| K | 21 (NWPG) / 24–30 (AHDB) | [T1 NWPG SA, T2 AHDB] |
| Ca | 13 (NWPG) / 30 (AHDB removed) | [T1 NWPG SA, T2 AHDB] |
| Mg | 2.7 | [T1 NWPG SA] |
| S | 2.7 | [T1 NWPG SA] |

Annual demand for high-yield (15-20 t DM/ha irrigated): 55–65 kg P/ha, 75–100 kg K/ha establishment + 30–40 kg K2O/ha after each cut [T1 NWPG SA].

### Per-cut nutrient demand split

| Cut | %P | %K | Source |
|---|---|---|---|
| Establishment (yr 1) | 100 (band) | 50 (autumn) | [T2 AHDB] |
| Each subsequent cut | 0 | 12–15 % (30–40 kg K2O/ha) | [T1 NWPG SA] |
| Autumn topdress | balance P + K | balance | [T2 AHDB] |

N: starter ~40 kg N/ha at establishment only; thereafter rely on Rhizobium meliloti fixation (legume).

### Yield benchmarks (SA)

- Dryland (Karoo / W Cape): 5–10 t DM/ha/yr (4-6 cuts) [T1 IGC 1993 Western/Southern Cape]
- Irrigated summer rainfall: 15–20 t DM/ha/yr (7+ cuts) [T1 Farmer's Weekly W Free State]
- High-input irrigated: 18–30 t DM/ha/yr [T1 Lucerne SA industry]

Northern Cape dominates: >90 % of SA officially graded lucerne hay [T1 Tandfonline 2024 SA lucerne dynamics].

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Visible Mo deficiency (acid soils) | Sodium molybdate | 100-200 g/ha | [T2 UGA pub — Mo critical for legume N-fix] |
| B deficiency | Solubor | 1-2 kg/ha | [T2 UGA] |

### Adjustments

| Factor | Multiplier | Source |
|---|---|---|
| Acid soil pH <5.5 | Lime to pH 6.0 mandatory; otherwise yield -50 % | [T1 NWPG SA] |
| Inoculation with Rhizobium meliloti | N target → starter only | [T1 DALRRD / T2 AHDB] |
| Stand age >4 yr | P + K removal increases | [T2 AHDB] |

### Notes

- **LEGUME — engine MUST set N target = starter only (40 kg N/ha at establishment, 0 thereafter).** N required per kg DM is supplied by N-fixation when Rhizobium-inoculated and pH ≥6.0.
- Lime sensitivity: pH (KCl) <5.5 collapses N-fixation and yield; lime to ≥6.0 KCl before establishment.
- Mo essential for nitrogenase enzyme — soil Mo testing recommended on acidic SA soils.
- K-luxury consumption common; K critical for leaf retention through cuts.

### Sources consulted

1. [T1] North West Provincial Govt — Planted Pasture & Lucerne Production — https://dard.nwpg.gov.za/wp-content/uploads/2022/05/Planted-pasture-and-lucerne-production.pdf
2. [T1] Lusern.org Lucerne Management — https://lusern.org/p9/lucerne/lucerne-management.html
3. [T1] DALRRD Gadi Lucerne King of Fodder Crops — https://gadi.dalrrd.gov.za/articles/Agric/lucerne.php
4. [T1] van Heerden 1993 IGC — Production of Dryland Lucerne in W & S Cape — https://uknowledge.uky.edu/igc/1993/session19/12/
5. [T1] Tandfonline 2024 — Dynamics of SA Lucerne Hay Industry — https://www.tandfonline.com/doi/full/10.1080/03031853.2024.2407055
6. [T1] AGT Foods SA Lucerne Booklet — https://agtfoods.co.za/wp-content/uploads/2021/11/Lucern-Booklet-English.pdf
7. [T2] AHDB Lucerne Recommendations — https://ahdb.org.uk/knowledge-library/fertiliser-recommendations-for-lucerne
8. [T2] UGA AESL Plant Tissue — Alfalfa — https://aesl.ces.uga.edu/publications/plant/Alfalfa.html
9. [T2] Penn State Cutting Mgmt of Alfalfa — https://extension.psu.edu/cutting-management-of-alfalfa-red-clover-and-birdsfoot-trefoil
10. [T2] Nutrien-Ekonomics Alfalfa Growth Staging — https://nutrien-ekonomics.com/news/alfalfa-development-and-growth-staging/

---

## Rooibos (Aspalathus linearis) — endemic SA legume shrub, 4-5 yr productive cycle

### Growth stages (annual cycle, summer harvest)

| Month SA | Stage | Key process | Source |
|---|---|---|---|
| Feb–Mar | Seedbed | Seeds in nursery beds | [T1 Klipopmekaar, T1 Farmers Magazine SA] |
| Apr–May (autumn) | Transplant | Seedlings to plantation rows; winter rains establish | [T1 Klipopmekaar] |
| Jun–Aug | Winter establishment | Slow growth in cool wet | [T1 PlantZAfrica SANBI] |
| Sep–Dec | Spring/summer growth | N-fix via β/α-proteobacteria nodulation | [T1 SANBI, Hassen 2012 Soil Biol Fert] |
| Jan–Mar | **Harvest window** | Cut top 30-40 cm with sickles or mech cutter | [T1 Farmers Magazine SA, T1 SA Rooibos Council] |
| Apr–May | Recovery | Regrowth begins | [T1 Klipopmekaar] |

Productive cycle: first harvest 18-24 months from planting; harvested annually for 4-5 years; rotate to fallow / rotation crop 1-2 yr [T1 Farmers Magazine SA].

### Leaf norms

GAP — **no validated leaf norm tables published for rooibos.** Boundary-line work (Hattingh 2023) addresses soil only. Engine should not surface leaf-norm logic for rooibos.

### Soil thresholds (Hattingh et al. 2023 SAJPS boundary-line, n=120 commercial plantations Cederberg + N Cape)

| Nutrient | Method | Sufficiency Range | Optimum | Source |
|---|---|---|---|---|
| pH (KCl) | — | 4.2–4.7 | **4.5** | [T1 Hattingh 2023 SAJPS 40:4-5] |
| P | Bray-1 (assumed) | 7.4–26.4 mg/kg | **16.9** | [T1 Hattingh 2023] |
| K | (extractant per study) | 11.5–30.0 mg/kg | **20.8** | [T1 Hattingh 2023] |
| Ca | — | GAP | GAP | — |
| Mg | — | GAP | GAP | — |
| OC % | Walkley-Black | 0.5–2 % typical natural | — | [T1 Stanton 2018 Clanwilliam soil quality study] |

Natural Cederberg soils: pH 3.0–5.3; high Al (110–275 µg Al/g) [T2 Brown 2019 Sci Reports — Soil water dynamics in young rooibos].

### Crop requirements per ton dry leaf

GAP — no published per-ton uptake table. Field surveys indicate decline in soil OC and K most strongly correlated with declining yields [T1 Lötter et al. 2017 ResearchGate]. Use this as input for trend-based monitoring rather than removal-rate budgeting.

### Per-stage nutrient demand split

GAP. Industry norm is **no fertilization at all** for traditional rooibos.

### Yield benchmarks

| Tier | t/ha dry processed leaf | Source |
|---|---|---|
| Low / poor soils | 0.25 t/ha | [T1 Klipopmekaar] |
| Typical (Cederberg avg) | 0.4–0.6 t/ha | [T1 Klipopmekaar, T1 Farmers Mag SA] |
| Peak years 3-4 | 0.5–0.6 t/ha | [T1 Farmers Mag SA] |
| High-input | up to 1.2 t/ha | [T1 Klipopmekaar] |

### Foliar protocols

GAP — none published in SA literature.

### Adjustments

| Factor | Multiplier | Source |
|---|---|---|
| Cultivated vs wild | Wild plants better N-fix in dry season | [T1 Muofhe & Dakora 1999 Aust J Bot] |
| Deep sandy soil | Highest biomass with NO fertilizer | [T2 Brown 2019 Sci Reports] |

### Notes

- **LEGUME (β + α-proteobacteria nodulated) — engine MUST set N target = 0 kg N/ha. Hard-code rooibos in legume_nfix list.** Use this language verbatim in the renderer narrative: *"Rooibos is a leguminous shrub that fixes atmospheric N₂; synthetic N application is not recommended and may suppress nodulation."*
- Soil pH (KCl) target **4.5** — directly contradicts standard SA cropping (5.5-6.5). Engine must allow per-crop pH override.
- **No standard fertilization regime exists** — boundary-line study is the best published soil sufficiency reference.
- Aluminium tolerance unique among SA crops; do NOT recommend lime for rooibos (would push pH out of optimum).
- Decline in soil K is the strongest correlate with yield decline — surface this as a soil-monitoring guidance, NOT as a K target.

### Sources consulted

1. [T1] Hattingh G et al. 2023 — Determination of optimal soil pH and nutrient concentrations for cultivated rooibos using boundary line approach. SAJPS 40(4-5) — https://www.tandfonline.com/doi/full/10.1080/02571862.2023.2259860
2. [T1] Hassen et al. 2012 — Nodulation of rooibos by α/β-Proteobacteria. Biology & Fertility of Soils — https://link.springer.com/article/10.1007/s00374-011-0628-3
3. [T1] Lötter D et al. 2017 — Role of soil quality in declining rooibos yields, Clanwilliam — https://www.researchgate.net/publication/321363617
4. [T1] SANBI PlantZAfrica Aspalathus linearis — https://pza.sanbi.org/aspalathus-linearis
5. [T1] Klipopmekaar Rooibos Farming Process — https://www.klipopmekaar.co.za/rooibos-farming-production-process/
6. [T1] Farmers Magazine SA 2025 — Growing Rooibos for Small Farmers — https://farmersmag.co.za/2025/07/growing-rooibos-a-guide-for-small-farmers-in-the-cederberg/
7. [T1] Vanessa Barends-Jones 2020 (Elsenburg / W Cape DoA) — Rooibos in the Overberg — https://www.elsenburg.com/wp-content/uploads/2022/03/2020-Rooibos-Tea-in-the-Overberg.pdf
8. [T2] Brown LK et al. 2019 — Soil water dynamics & biomass production of young rooibos. Scientific Reports — https://www.nature.com/articles/s41598-023-41666-5
9. [T3] Muofhe & Dakora 1999 — Seasonal variation in N nutrition / C assimilation in wild & cultivated rooibos. Aust J Bot

---

## Asparagus (Asparagus officinalis) — perennial cut-and-regrow, 12-15 yr stand

### Growth stages

| Month SA (winter-rainfall production) | Stage | Key process | Source |
|---|---|---|---|
| Aug–Oct | Spear emergence | Carbohydrate from previous year's fern → spear | [T2 UMN Extension] |
| Spear cycle (8-12 wk) | Active harvest | Daily/alternate-day cutting | [T2 UMN] |
| Nov–Apr | Fern stage | Photosynthate replenishes crown for next spear cycle; **N + K applied here** | [T2 UMN, T2 UC IPM] |
| May–Jul | Senescence / dormancy | Fern dies down; mowing | [T2 UMN] |
| Yr 1-3 | Establishment | Allow full fern growth, do NOT harvest yr 1; light yr 2 | [T2 UMN] |

### Leaf / fern norms (mature fern, mid-summer)

| Nutrient | Deficient | Sufficient | High | Source |
|---|---|---|---|---|
| N | <2.5 % | 3.0–4.5 % | >5.0 % | [T2 Hawaii CTAHR PNM4 / NCDA tissue guide] |
| P | <0.20 % | 0.25–0.50 % | >0.7 % | [T2 NCDA] |
| K | <1.5 % | 2.0–3.5 % | >4.5 % | [T2 NCDA] |
| Ca | <0.4 % | 0.5–1.0 % | — | [T2 NCDA] |
| Mg | <0.15 % | 0.20–0.40 % | — | [T2 NCDA] |
| S | <0.20 % | 0.25–0.40 % | — | [T2 NCDA] |
| Fe | <40 mg/kg | 50–250 | — | [T2 NCDA] |
| Mn | <20 mg/kg | 25–200 | — | [T2 NCDA] |
| Zn | <15 mg/kg | 20–80 | — | [T2 NCDA] |
| B | <20 mg/kg | 25–75 | — | [T2 NCDA] |
| Cu | <3 mg/kg | 5–25 | — | [T2 NCDA] |

Note: Specific asparagus tissue tables not consistently published; values approximated from NCDA generic vegetable tissue ranges. Flag as MEDIUM confidence.

### Soil thresholds

| Nutrient | Method | Deficient | Adequate | High | Source |
|---|---|---|---|---|---|
| pH | — | <6.0 | **6.5–7.0** | >7.5 | [T2 UMN — won't tolerate extreme acid] |
| P | Bray-1 | <10 mg/kg | 20–30 | >30 | [T2 UMN] |
| K | Ammonium acetate | <50 mg/kg | 100–150 | >200 | [T2 UMN] |

### Crop requirements per ton harvested spears (2.5 t/acre = 6.2 t/ha example)

| Nutrient | kg/t spears | Source |
|---|---|---|
| N | ~3.7 (23 lb/2.5 t/acre) | [T2 UMN derived] |
| P | ~0.5 | [T2 UMN] |
| K | ~3.2 | [T2 UMN] |

Crown storage capacity: ~150 lb N, 37 lb P, 170 lb K per acre [T2 UMN] = 168, 41, 190 kg/ha equivalent. This buffers per-cycle deficits.

### Per-stage nutrient demand (annual)

| Stage | %N | %P2O5 | %K2O | Source |
|---|---|---|---|---|
| Pre-spear (late winter) | 50 | 100 | 50 (preplant or topdress) | [T2 UC IPM, UMN] |
| Post-harvest / fern stage | 50 | 0 | 50 | [T2 UMN — replenish for next year] |

Established N rates (lb/acre → kg/ha):
- Low OM (≤3 %): 90 kg N/ha
- Medium OM (3-4.5 %): 67 kg N/ha
- High OM (>4.6 %): 45 kg N/ha
[T2 UMN]

### Yield benchmarks

- Yr 1: no harvest
- Yr 2: 1-2 t/ha
- Yr 3 onwards (full): 4-7 t/ha
- Peak (good stand): 8-10 t/ha
[T2 UMN — derived from typical commercial bands]

### Foliar protocols

GAP — no widely cited foliar protocol for asparagus. Crown storage buffers most deficiencies.

### Adjustments

| Factor | Multiplier | Source |
|---|---|---|
| New planting (yr 1-3) | +50 % N to build crown | [T2 UMN] |
| High OM soil | -33 % N | [T2 UMN] |

### Notes

- **Nutrients applied during fern stage replenish for next spear cycle** — engine timing must split N and K 50/50 between pre-spear and post-harvest fern.
- pH 6.5-7.0 is unusually high for SA acid-tolerant cropping — lime mandatory in many SA soils.
- Crown reserves act as 1-yr buffer; tissue testing reflects the **previous year's** fertilization.
- Not yet a major SA crop (small acreage Mpumalanga / W Cape) — keep medium-confidence flag on data.

### Sources consulted

1. [T2] U Minnesota Extension Asparagus Nutrient Management — https://extension.umn.edu/vegetable-growing-guides-farmers/nutrient-management-asparagus
2. [T2] UC IPM Asparagus Fertilization — https://ipm.ucanr.edu/agriculture/asparagus/fertilization/
3. [T2] AHDB Asparagus Nutrient Management — https://projectblue.blob.core.windows.net/media/Default/Imported%20Publication%20Docs/14_13%20Asparagus%20nutrient%20management%20revised%20(1).pdf
4. [T2] Hawaii CTAHR Plant Nutrient Levels PNM4 — https://www.ctahr.hawaii.edu/oc/freepubs/pdf/pnm4.pdf
5. [T2] NCDA&CS Plant Tissue Analysis — https://www.ncagr.gov/plant-tissue-analysis-guide/open

---

## Cotton (Gossypium hirsutum) — annual, 160-180 day cycle in SA

### Growth stages

| DAP | Months SA | Stage | Key process | Source |
|---|---|---|---|---|
| 0–10 | Oct–Nov | Germination & emergence | Soil temp ≥17.5–18 °C | [T1 Cotton SA] |
| 10–35 | Nov–early Dec | Seedling | Cotyledons + first true leaves | [T2 Bayer / Tex A&M] |
| 35–70 | Dec–early Jan | Squaring | First square at 35-47 DAP | [T2 Bayer Cotton Growth] |
| 70–105 | Jan–Feb | Flowering / first bloom & peak bloom | First bloom 55-65 DAP; peak 90-105 DAP; **K + B critical** | [T1 Cotton SA, T2 Bayer] |
| 105–150 | Feb–Mar | Boll development | Boll fill, fibre quality determined | [T1 Cotton SA] |
| 150–180 | Mar–Apr | Maturation / open boll | First bolls open ~115-120 DAP; harvest 160-180 | [T1 Cotton SA] |

### Leaf petiole NO3-N norms (NC State / Mo Ext, by stage)

| Stage | Sufficient NO3-N (ppm) | Source |
|---|---|---|
| First square (early bloom) | 12,000–18,000 | [T2 NC State / Mo Ext approx — exact NC table requires direct PDF parse] |
| First wk of bloom | 8,000–14,000 | [T2 NC State petiole guide] |
| Third wk of bloom | 4,000–8,000 | [T2 NC State petiole guide] |
| Open boll | <2,000 | [T2 NC State petiole guide] |

Leaf blade norms (most-recent mature leaf):

| Nutrient | Sufficient | Source |
|---|---|---|
| N | 3.5–4.5 % | [T2 UGA / NCDA] |
| P | 0.30–0.50 % | [T2 UGA] |
| K | 1.7–3.0 % | [T2 UGA] |
| Ca | ~2 % critical | [T2 UGA] |
| Mg | 0.30 % critical | [T2 UGA] |
| S | 0.20–0.25 % | [T2 UGA] |
| B | **20 mg/kg critical** | [T2 UGA — cotton highly B-sensitive] |
| Mn | up to 500 ppm tolerated | [T2 UGA] |

### Soil thresholds (SA / Mo Ext)

| Nutrient | Method | Deficient | Adequate | High | Source |
|---|---|---|---|---|---|
| pH | — | <5.5 | **5.5–7.5** | >7.5 | [T1 Cotton SA] |
| P | Bray-1 | <10 mg/kg | ≥45 lb/acre ≈ 22 mg/kg | >40 | [T2 Mo Extension G4256] |
| K | NH4OAc | low | 220 + 5×CEC lb/acre | high | [T2 Mo Extension] |
| B | Hot-water | <0.25 ppm → 1 kg B/ha | 0.26–0.5 → 0.5 kg B/ha | >0.5 → 0 | [T2 Mo Ext G4257] |

### Crop requirements per bale (1 bale ≈ 218 kg lint, ~545 kg seed cotton)

| Nutrient | kg per bale | kg/t seed cotton | Source |
|---|---|---|---|
| N | 27 (60 lb/acre / 2 bale ≈ 27 kg/bale) — ~25 kg | ~50 | [T1 Cotton SA derived; T2 Mo Ext 80-120 lb N/ha for 2-bale] |
| P (P2O5) | ~10 | ~18 | [T1 Cotton SA: 30-40 kg P/ha @ 5 t/ha] |
| K (K2O) | 23.5 (52 lb K/bale) | ~50 | [T2 Cotton Foundation Ch 4] |
| Ca | ~5 | — | [T3 derived] |
| Mg | ~3 | — | [T3 derived] |
| S | ~3 | — | [T3 derived] |
| B | ~0.1 (uptake basis) | 0.2 | [T2 Mo Ext G4257] |

Brazilian benchmark: 2.5 t seed cotton/ha absorbed N 156, P2O5 36, K2O 151 kg/ha [T2 FAO Bulletin 17].

### Per-stage demand split

| Stage | %N | %P2O5 | %K2O | Source |
|---|---|---|---|---|
| Pre-plant / sowing | 30 | 100 | 30 | [T2 Bayer] |
| Squaring | 20 | 0 | 20 | [T2 NC State petiole logic] |
| First bloom | 30 | 0 | 30 | [T2 Bayer — 50 % K uptake in 6 wk post first bloom] |
| Boll fill | 20 | 0 | 20 | [T2 Cotton Foundation Ch 4] |

**Hard rule (T1 Cotton SA): no fertilizer after 8 weeks post-planting; "often not more than 150-180 kg N/ha by peak flowering."**

### Yield benchmarks (SA)

| Tier | Seed cotton t/ha | Lint bales/ha | Source |
|---|---|---|---|
| Dryland low | 1.2 | ~5 | [T1 Cotton SA] |
| Dryland typical | 1.5–2.0 | 7-9 | [T1 Cotton SA] |
| Irrigated | 3.6–5.0 | 16-23 | [T1 Cotton SA] |

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Squaring → bloom | B (Solubor) | 280-560 g B/ha (sprays) | [T2 Mo Ext G4257] |
| Boll fill | K (KNO3 or K-thiosulfate) | 5-10 kg K2O/ha per spray, 2-3 sprays | [T2 Mo Ext / Bayer] |

### Adjustments

| Factor | Multiplier | Source |
|---|---|---|
| Clay soil | -10–20 % N | [T1 Cotton SA] |
| Following legume / pasture | -20 % N | [T2 Mo Ext] |
| Low B soil (<0.25 ppm) | Mandatory broadcast B + foliar | [T2 Mo Ext G4257] |

### Notes

- B critical for fruit retention; B deficiency = boll shed, hollow heart. Engine should require B sufficiency check for cotton.
- K demand peak in 6-wk window post first-bloom; under-K = small bolls, poor fibre micronaire.
- N over-supply = vegetative excess, delayed maturity, reduced micronaire — Cotton SA explicit "no N after 8 weeks".
- Petiole NO3-N normative table is the canonical in-season decision tool for cotton (not leaf blade).

### Sources consulted

1. [T1] Cotton SA Technical Information — https://cottonsa.org.za/technical-information/
2. [T2] Cotton Foundation Ch 4 Nutritional Requirements during Flowering & Fruiting — https://www.cotton.org/foundation/upload/f-f-chapter-4.pdf
3. [T2] Missouri Extension G4256 Cotton Fertility — https://extension.missouri.edu/publications/g4256
4. [T2] Missouri Extension G4257 Sulfur & Boron on Cotton — https://extension.missouri.edu/publications/g4257
5. [T2] NCDA Cotton Tissue Sampling Guide — https://www.ncagr.gov/agronomic-services-cotton-tissue-sampling-guide/open
6. [T2] NC State 2023 Cotton Information — Fertilization (Gatiboni) — https://content.ces.ncsu.edu/pdf/fertilization/2023-01-23/202ssible_FINAL_CxRLLKB.pdf
7. [T2] Bayer Cotton Growth & Development — https://www.cropscience.bayer.us/articles/dad/cotton-growth-and-development
8. [T2] FAO Fertilizer & Plant Nutrition Bulletin 17 — https://www.fao.org/4/a0787e/a0787e00.pdf
9. [T2] FAO Ch 8 Nutrient Mgmt Guidelines for Major Field Crops — https://www.fao.org/4/a0443e/a0443e04.pdf

---

## Chillies / Paprika (Capsicum annuum) — annual, transplanted

### Growth stages

| Stage | Days from transplant | Key process | Source |
|---|---|---|---|
| Seedling / establishment | 0–21 | Root + leaf formation; low N | [T2 Birdhouse / pepper guides] |
| Vegetative | 21–42 | Balanced N P K | [T2 Haifa Pepper Guide] |
| Flower bud / first flowers | 42–60 | P + K demand rising | [T2 Haifa] |
| Fruit set & first harvest | 60–98 | Peak N + K + Ca; Ca for BER prevention | [T2 Diaz et al. / sweet pepper uptake] |
| Continuous harvest (chilli) | 98–180 | High K for capsaicin / colour | [T2 Haifa, T3 Birdhouse] |

### Leaf norms (most-recent mature leaf, sampled vegetative through fruit set)

| Nutrient | Deficient | Adequate (vegetative) | Adequate (fruit set) | Excess | Source |
|---|---|---|---|---|---|
| N | <2.8 % | 3.5–5.0 % | 3.0–4.0 % | >5.5 % | [T2 NC State Foliar Analysis Bell Pepper] |
| P | <0.25 % | 0.30–0.60 % | 0.30–0.60 % | >0.8 % | [T2 NC State] |
| K | <2.5 % | 3.0–5.0 % | 3.5–4.5 % | >5.5 % | [T2 NC State] |
| Ca | <1.0 % | 1.5–2.5 % | 1.5–2.5 % | rare | [T2 NC State] |
| Mg | <0.30 % | 0.30–0.50 % | 0.40–0.60 % | >1.0 % | [T2 NC State] |
| S | <0.20 % | 0.30–0.40 % | 0.30–0.40 % | — | [T2 NC State] |
| Fe | <50 mg/kg | 50–200 | 50–200 | >300 | [T2 NC State] |
| Mn | <25 mg/kg | 30–150 | 30–150 | >200 | [T2 NC State] |
| Zn | <20 mg/kg | 25–50 | 25–50 | >100 | [T2 NC State] |
| Cu | <5 mg/kg | 5–20 | 5–20 | >30 | [T2 NC State] |
| B | <15 mg/kg | 20–60 | 20–60 | >100 | [T2 NC State] |
| Mo | <0.1 mg/kg | 0.1–1.0 | 0.1–1.0 | — | [T2 NC State] |

Sample timing: 4-6 wk after transplant (vegetative), then at flowering, then at early fruit set [T2 NC State].

### Soil thresholds (SA KZN-DARD capsicums + general capsicum)

| Nutrient | Method | Deficient | Adequate | High | Source |
|---|---|---|---|---|---|
| pH | — | <5.5 | 6.0–6.8 | >7.5 | [T1 KZN-DARD Capsicums (file ref)] |
| P | Bray-1 | <15 mg/kg | 25–50 | >60 | [T2 Haifa Pepper Guide] |
| K | NH4OAc | <0.25 cmol+/kg | 0.4–0.8 | >1.0 | [T2 Haifa] |
| Ca | NH4OAc | <4 cmol+/kg | 6–10 | — | [T2 Haifa] |
| Mg | NH4OAc | <0.5 cmol+/kg | 1.0–2.0 | — | [T2 Haifa] |
| OC % | — | <1 % | 1.5–3 % | — | [T2 Haifa] |

### Crop requirements per ton fruit

Direct per-ton tables sparse; total uptake at 98 DAT (sweet pepper trial @ Jordan): 118 kg N, 15 kg P, 123 kg K, 41 kg Ca, 32 kg Mg [T3 Diaz et al. Journal of Plant Nutrition 14:11]. For typical 30 t/ha fresh pepper:

| Nutrient | kg / t fresh fruit | Source |
|---|---|---|
| N | ~4.0 | [T3 Diaz et al. derived] |
| P (P2O5) | ~1.1 (0.5 P) | [T3 derived] |
| K (K2O) | ~5.0 (4.1 K) | [T3 derived] |
| Ca | ~1.4 | [T3 derived] |
| Mg | ~1.1 | [T3 derived] |

For dried paprika (20-25× concentration): scale per-ton-dry by ~5×.

### Per-stage demand split (Haifa N:P2O5:K2O ratios)

| Stage | Ratio | %N | %P2O5 | %K2O | Source |
|---|---|---|---|---|---|
| Establishment | 1:2:1 | 10 | 30 | 5 | [T2 Haifa] |
| Vegetative growth | 1:1:1 | 25 | 40 | 15 | [T2 Haifa] |
| Flowering → fruit set | 2:1:3 | 30 | 25 | 35 | [T2 Haifa] |
| Fruit dev & maturation | 2:1:3 | 35 | 5 | 45 | [T2 Haifa] |

NO3:NH4 optimal 4:1; ≥50-90 % of N as NO3 [T2 Haifa].

### Yield benchmarks (SA)

| Tier | Fresh chilli t/ha | Dried paprika t/ha | Source |
|---|---|---|---|
| Low (dryland) | 5–10 fresh | 1.0–2.0 | [T1 KZN-DARD] |
| Typical irrigated | 15–25 fresh | 2.5–4.0 | [T2 Haifa] |
| High-tech tunnel | 40–80 fresh | — | [T2 Haifa] |

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Pre-flower | B + Ca | 200 g B/ha + Ca chelate | [T2 Haifa] |
| Fruit set | Ca (CaCl2) | 0.5-1 % spray, 3-4× to prevent BER | [T2 Haifa] |
| Fruit fill | K (KNO3) | 1-2 % per spray | [T2 Haifa] |

### Adjustments

| Factor | Multiplier | Source |
|---|---|---|
| Tunnel / hydroponic | +50 % nutrient targets | [T2 ICL Pepper Guide] |
| Capsaicin / colour focus | + K, + micros (Cu, Mn) | [T2 Birdhouse, T3 review on capsaicin] |
| Fruit-set BER prone | + Ca + B foliar mandatory | [T2 Haifa, NC State] |

### Notes

- K critical for capsaicin (heat) and oleoresin (paprika colour). Plants with low P showed reduced capsaicin and fructose [T3 plant trials].
- Highest N+K uptake: 56-70 days after transplant (rapid fruit growth window). Time fertigation accordingly.
- Engine should treat **paprika and chilli as same crop class** (Capsicum annuum); only the harvest form differs.
- Mo + Cu often deficient on sandy SA soils — include in foliar rotation for paprika colour.

### Sources consulted

1. [T1] KZN-DARD Capsicums Production Guide — https://www.kzndard.gov.za/images/Documents/Horticulture/Veg_prod/capsicums.pdf
2. [T2] NC State — Foliar Analysis for Bell Pepper Production NC — https://content.ces.ncsu.edu/foliar-analysis-for-bell-pepper-production-in-north-carolina-a-guide-for-growers
3. [T2] Haifa Group Pepper Crop Guide — https://www.haifa-group.com/articles/crop-guide-nutrients-pepper
4. [T2] Haifa Group Pepper Fertilization Recommendations — https://www.haifa-group.com/pepper-fertilizer/crop-guide-pepper-fertilization-recommendations
5. [T2] ICL Growing Solutions Pepper Crop — https://icl-growingsolutions.com/agriculture/crops/pepper/
6. [T2] UF/IFAS CV230 N P K Research with Pepper in FL — https://ask.ifas.ufl.edu/publication/CV230
7. [T3] Diaz et al. Journal of Plant Nutrition 14(11) — Nutrient uptake & yield of sweet pepper

---

## Tobacco (Nicotiana tabacum) — annual, ~110-130 days from transplant in field

### Growth stages

| Stage | Days from transplant | Key process | Source |
|---|---|---|---|
| Transplanting | 0 (after 40-60 d nursery) | Plants 15 cm at transplant | [T2 NC State / FAO] |
| Establishment | 0-21 | Root growth | [T2 Britannica] |
| Vegetative (knee-high → bud) | 21-45 | Rapid leaf expansion | [T2 NC State] |
| Budding / flowering | 45-75 | **Topping** at 10 % flowering — removes flower head + top leaves | [T2 NC State Topping] |
| Maturation | 75-110 | Bottom-up leaf yellowing | [T2 Britannica] |
| Harvest (priming) | 110-160 | 2-3 leaves/wk over 30-50 days | [T2 NC State] |

### Leaf norms (most recently mature leaf)

| Nutrient | Sufficient | Source |
|---|---|---|
| N | 3.5–6.5 % (peak vegetative); 2.5–4.0 % near harvest | [T2 NC State Tobacco Fertility] |
| P | 0.20–0.50 % | [T2 NC State, Burley research] |
| K | 2.5–5.0 % (high-K crops show >4 %) | [T2 NC State] |
| Ca | 1.5–4.0 % | [T2 NC State] |
| Mg | 0.20–0.60 % (most stages); 0.18–0.75 % at harvest | [T2 NC State Mg page] |
| S | 0.25–0.65 % (max ~0.49 % typical) | [T2 NC State] |
| B | 25–75 mg/kg | [T2 NC State] |
| Mn | 30–150 mg/kg | [T2 NC State] |
| Zn | 20–80 mg/kg | [T2 NC State] |
| **Cl (toxicity)** | **<1 % leaf (target); >2.5 % renders leaf nearly incombustible** | [T2 Agronomy J 2020 Cl rates / NC State] |

### Soil thresholds (NC State, applicable to SA flue-cured)

| Nutrient | Method | Deficient | Adequate | High | Source |
|---|---|---|---|---|---|
| pH | — | <5.5 (Mn toxicity / poor leaf) | **5.8–6.2** (dolomitic lime) | >6.5 (Mn lockup) | [T2 NC State] |
| P | Mehlich-3 | <30 mg/kg | 30–60 | >60 (skip P) | [T2 NC State] |
| K | Mehlich-3 | low | medium-high (~60 % NC tobacco soils already high) | high | [T2 NC State] |
| OC % | — | <0.5 (S risk) | 1–2 | — | [T2 NC State] |

### Crop requirements

| Nutrient | Rate kg/ha (flue-cured target) | Source |
|---|---|---|
| N | 56–90 (50-80 lb/acre) | [T2 NC State] |
| P (P2O5) | 0–45 (most NC soils need none) | [T2 NC State] |
| K (K2O) | ~100 (90 lb/acre crop removal) | [T2 NC State] |
| Ca | 45–55 | [T2 NC State] |
| Mg | 17–22 (deep sandy yr 2-3) | [T2 NC State] |
| S | 22–34 (sandy soils annual) | [T2 NC State] |
| Mn (rare) | 3.4 banded / 11 broadcast / 0.6 foliar | [T2 NC State] |
| Cl | **20–30 lb/acre MAXIMUM** ≈ 22-34 kg/ha | [T2 NC State — burn quality cap] |

Burley/sun-cured types: higher N (90-130 kg/ha) [T3 SA TISA literature, FAO global tobacco]. Flue-cured (SA dominant, Limpopo/Mpumalanga): 40-80 kg N/ha is the safe band.

### Per-stage demand split

| Stage | %N | %P2O5 | %K2O | Source |
|---|---|---|---|---|
| Pre-plant / transplant water | 30-50 | 100 | 50 | [T2 NC State] |
| Sidedress (knee-high) | 50-70 | 0 | 50 | [T2 NC State] |
| **No N after layby** | 0 | — | — | [T2 NC State — late N delays maturation, harms cure] |

### Yield benchmarks (flue-cured tobacco)

- Greek flue-cured average: 3,450 kg/ha cured leaf [T3 Honghe study comp]
- SA flue-cured typical: 2,000–2,800 kg/ha cured leaf [T3 industry estimate]
- High-input: 3,500+ kg/ha

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Mn deficiency (high-pH coastal) | MnSO4 | 0.5 lb/acre = 0.6 kg/ha foliar | [T2 NC State] |
| B for late-season | Solubor | 1-2 kg/ha | [T2 NC State] |

### Adjustments

| Factor | Multiplier | Source |
|---|---|---|
| Following legume / soybean | -20 % N | [T2 NC State] |
| Sandy soil <0.5 % OC | +S 22-34 kg/ha annual | [T2 NC State] |
| Deep sandy soil yr 2-3 post-lime | +Mg 17-22 kg/ha | [T2 NC State] |
| pH >6.2 coastal Mn-low | Mn supplementation mandatory | [T2 NC State] |

### Notes

- **CHLORIDE LIMIT IS ABSOLUTE** — engine MUST avoid MOP for K above 30 kg K2O/ha; switch to SOP or Sul-Po-Mag. Leaf Cl >1 % degrades burn quality, >2.5 % is uncombustible.
- **N over-supply = quality penalty** (delayed cure, unripe leaf, hornworm pressure). Engine should cap tobacco N at 80-90 kg/ha unless explicitly Burley.
- P needs are usually met by residual; check soil before adding.
- Mg deficiency = "sand drown" / interveinal chlorosis — common on SA Highveld sandy soils.
- Flue-cured ≠ Burley ≠ oriental — engine should ideally distinguish; default to flue-cured for SA.

### Sources consulted

1. [T2] NC State Tobacco Fertility-Nutrients — https://tobacco.ces.ncsu.edu/tobacco-fertility-nutrients/
2. [T2] NC State Tobacco Topping & Sucker Control — https://tobacco.ces.ncsu.edu/tobacco-topping-sucker-control/
3. [T2] NC State Tobacco Mg Deficiency Diagnostic — https://content.ces.ncsu.edu/tobacco-magnesium-deficiency
4. [T2] FAO Tobacco — https://www.fao.org/land-water/databases-and-software/crop-information/tobacco/en/
5. [T2] Virginia Tech / VAES 2024 Flue-Cured Production Guide — https://www.arec.vaes.vt.edu/content/dam/arec_vaes_vt_edu/southern-piedmont/2024-flue-cured-production-guide/
6. [T2] Agronomy J 2020 Lewis et al. — Flue-cured Tobacco & Cl Rates — https://acsess.onlinelibrary.wiley.com/doi/full/10.1002/agj2.21272
7. [T3] Sifola & Postiglione 2002 Field Crops Research — DM accumulation & nutrient uptake flue-cured tobacco

---

## Coverage summary

| Crop | Growth stages | Leaf norms | Soil thresholds | Per-ton demand | Stage split | Yield bands | Foliar | Adjustments |
|---|---|---|---|---|---|---|---|---|
| Sugarcane | Full (T2) | Full (T2 IFAS + T1 SASRI K) | Full (T1 SASRI Truog/Ambic) | Full (T2 Haifa) | Full | Full SA | Full | Full |
| Lucerne | Full (T2) | Full (T2 UGA) | Full (T1 NWPG SA) | Full (T1 NWPG SA + T2 AHDB) | Full | Full SA | Partial | Full |
| Rooibos | Partial (T1 SA) | **GAP** | Full (T1 Hattingh 2023) | **GAP** | **GAP** | Full SA | **GAP** | Partial |
| Asparagus | Full (T2) | Medium-conf (T2 NCDA) | Full (T2 UMN) | Partial (T2) | Full (T2) | Full | **GAP** | Partial |
| Cotton | Full (T1 Cotton SA) | Full (T2 NC State) | Full (T1 + T2) | Full (T1 + T2) | Full | Full SA | Full | Full |
| Chillies / Paprika | Full (T2) | Full (T2 NC State) | Full (T2 Haifa) | Partial (T3) | Full | Full | Full | Full |
| Tobacco | Full (T2 NC State) | Full (T2 NC State) | Full (T2 NC State) | Full (T2) | Full | Full | Full | Full |

## Top engine action items from this research

1. **Add `legume_nfix = true` flag** for rooibos and lucerne. Engine N-target logic must short-circuit for both.
2. **Sugarcane Truog-P + Ambic-2 K extractants** must be supported in soil-test schema; Bray-1 alone is wrong for SA cane.
3. **Tobacco chloride cap (max 30 kg K2O/ha as MOP)** must be enforced as a material-selection constraint.
4. **Rooibos pH (KCl) target = 4.5** — engine must allow per-crop pH override; lime is contra-indicated.
5. **Cotton boron mandatory** when soil B <0.25 ppm hot-water extractable; no exceptions.
6. **Cotton "no N after 8 weeks"** rule (T1 Cotton SA) should drive a programme-builder cutoff.
7. **Sugarcane late-season N taper** (last 60 days = ≤5 % of seasonal N) protects sucrose.
8. **Asparagus 50/50 N split pre-spear / post-harvest fern** — calendar logic, not yield-based.
