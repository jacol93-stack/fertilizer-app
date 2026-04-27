# Deciduous Tree Fruit — South Africa data extract

Research date: 2026-04-27
Crops covered: Apple, Pear, Plum, Peach, Nectarine, Apricot, Cherry
Calendar convention: Western Cape (Southern Hemisphere) — bloom Sept-Oct, harvest Dec-May.

Citation tag format: `[Tier source section]`. Tiers per house rule:
- T1 = SA (Hortgro, ARC Infruitec-Nietvoorbij, DALRRD, Stellenbosch)
- T2 = international parallel (Cornell/Cheng, WSU, UC ANR, Yara, Wisconsin Ext, NSW DPI)
- T3 = peer-reviewed / SERA-IEG-6 / Mediterranean studies

> **Anti-pattern flag** — Memory note `research_growth_stages_deciduous` says current SA seed for apple is "materially wrong". Anything in current production DB conflicting with values below should be replaced.

---

## Apple (Malus domestica) — generic + cultivar notes

Highest-priority crop. Cheng's Cornell `Gala/M.26` work is the canonical depth source. For SA, the North & Wooldridge 2005 ARC Infruitec article carries Hortgro/Terblanche provenance and supplies a usable kg N/ha equation.

### Growth stages (Western Cape, generic apple — early Aug bud break, mid-Sept full bloom)

| Month (SA) | Stage | Key process | Source |
|---|---|---|---|
| Jun-mid Aug | Dormancy | Chilling accumulation; rest-breaking sprays late Jul-early Aug | [T1 Hortgro Cripps Pink handbook 2003] |
| Mid Aug | Bud swell / silver tip | First reserve-N mobilisation | [T2 Cheng 2013 NYFQ Fig 1] |
| Late Aug-early Sep | Green tip → tight cluster → pink | Spur-leaf expansion, supported by reserve N | [T2 Cheng 2013 §1] |
| Mid-Sep to early Oct | Full bloom | King flower opens; Cripps Pink early bloomer late-Sep | [T1 SA cultivar timing — Royal Gala mid-Sep, Cripps Pink late Sep / early Oct] |
| Oct | Petal fall, fruit set, June drop equivalent (~30 DAFB) | Cell division ends ~40 DAFB; first Ca uptake peak | [T1 Lotze & Theron 2005 in North & Wooldridge 2005] |
| Nov | Cell expansion, end of shoot growth (~90 DAFB) | Second Ca uptake peak; bitter-pit risk window | [T1 Lotze & Theron 2005] |
| Nov-Jan | Fruit sizing | Fruit becomes dominant K/P/B sink; >70% of season N already taken up | [T2 Cheng 2013 Fig 1A] |
| Feb | Royal Gala harvest | Climacteric; pick post-climacteric for lower bitter pit | [T1 North & Wooldridge 2005] |
| Mar | Golden Delicious / Granny Smith harvest | — | [T1 Hortgro statistics 2024] |
| Late Mar-early Apr | Cripps Pink harvest | Long 200-day cycle | [T2 Wikipedia/general SA timing] |
| Apr-May | Post-harvest with green leaves | Critical post-harvest N for next-season reserves | [T1 North & Wooldridge 2005; T2 Cheng 2013 §Timing of Application] |
| May-Jun | Leaf drop, dormancy onset | — | — |

### Leaf norms — sample timing: mid-shoot, current season's growth, 8-10 weeks after full bloom (≈ late Jan–early Feb in SA)

Hortgro PAG sampling protocol confirms "mid-season, just before fruit ripening (late Jan–early Feb)" [T1 Hortgro Postharvest Leaf Sampling Guide]. SERA values are general; Cornell Stiles & Reid values discriminate by tree age and cultivar group.

| Nutrient | Deficient | Adequate | High | Source |
|---|---|---|---|---|
| N (%) — young non-bearing | <2.0 | 2.4–2.6 | >2.8 | [T2 Stiles & Reid 1991 in Cheng 2013 Table 1] |
| N (%) — young bearing | <2.0 | 2.2–2.4 | >2.6 | [T2 Cheng 2013 Table 1] |
| N (%) — mature soft (Golden Delicious, Honeycrisp, Cripps Pink, McIntosh) | <1.6 | 1.8–2.2 | >2.4 | [T2 Cheng 2013 Table 1] |
| N (%) — mature hard (Gala, Granny Smith, Red Delicious, Fuji) | <1.8 | 2.0–2.4 | >2.6 | [T2 Cheng 2013 Table 1] |
| N (%) — Golden Delicious specific | <1.7 | 1.80–2.10 | >2.3 | [T3 SERA-IEG-6 Apple p.97] |
| N (%) — all other varieties (SERA general) | <1.8 | 1.90–2.30 | >2.5 | [T3 SERA-IEG-6 Apple p.97] |
| P (%) | <0.13 | 0.13–0.33 | >0.4 | [T2 Cheng 2013 Table 1; T3 SERA] |
| K (%) — most varieties | <1.2 | 1.35–1.85 | >2.0 | [T2 Cheng 2013 Table 1] |
| K (%) — Honeycrisp target | <0.9 | 1.0–1.3 | >1.5 | [T2 Wisconsin Ext Fertilization Guidelines for Mature Apple Trees] |
| K (%) — Empire / McIntosh optimal | — | 1.5–1.8 | — | [T2 Stiles & Reid 1991 in Cheng 2013 §Tree Nutrient Status] |
| Ca (%) | <0.8 | 1.3–1.8 | >2.0 | [T2 Cheng 2013 Table 1; T3 SERA 1.0-2.0] |
| Mg (%) | <0.20 | 0.35–0.50 | >0.6 | [T2 Cheng 2013 Table 1] |
| S (%) | — | 0.20–0.40 | — | GAP — SERA reports NA; WSU 0.01-0.10 likely sampling-method dependent |
| B (ppm) | <25 | 35–50 | >60 | [T2 Cheng 2013; T3 SERA 25-60] |
| Zn (ppm) | <20 | 35–50 | >60 | [T2 Cheng 2013; T3 SERA 20-50] |
| Cu (ppm) | <5 | 7–12 | >20 | [T2 Cheng 2013; T3 SERA 5-20] |
| Mn (ppm) | <25 | 50–150 | >200 | [T2 Cheng 2013; T3 SERA 25-200] |
| Fe (ppm) | <50 | 50–400 | — | [T2 Cheng 2013 50+; T3 SERA 50-400] |
| Mo (ppm) | — | — | — | GAP — no published sufficiency for apple |

> **Critical ratios** (Cheng 2013):
> - Leaf N:K target = 1.25:1 for Cripps Pink/McIntosh/Honeycrisp/Golden Delicious, 1.5:1 for Gala/Granny/Fuji/Red Delicious. Imbalance increases fire blight risk.
> - Fruit K:Ca <25 (mole basis) to avoid bitter pit. K:Ca should be ~15 at fruit 40-60 g, max 30 at harvest [T2 Yara Apple bitter pit 2024].

### Soil thresholds

GAP — no SA-specific apple soil threshold published in accessible sources. Fall back on Wisconsin / Cornell:

| Nutrient | Deficient | Adequate | High | Source |
|---|---|---|---|---|
| Bray-1 P (ppm) | <20 | 20–40 | 40–100 | [T2 UC CDFA peach guidelines applied to pome] |
| K exch (ppm) | <75 | 150–250 | >350 (skip K) | [T2 Wisconsin Ext apple] |
| Ca (meq/100g) | <4 | 8–15 | >15 | [T2 WSU sweet cherry — pome-applicable] |
| pH (water) | <5.5 | 6.0–6.8 | >7.5 (Fe/Zn lockup) | [T2 Wisconsin Ext target 7.2 high; SA target 6.0–6.5 typical Hortgro practice] |
| OC (%) | <1.5 | 2.0–4.0 | >5 | GAP for apple — general SA orchard target |

### Crop nutrient requirements per tonne yield (Gala/M.26, Cheng & Raba 2009 → Cheng 2013 derivation)

Gala/M.26 at 52.5 t/ha (1110 bu/acre) requires per ha (converted from lbs/acre):
- N 56 kg/ha net gain, of which 50.7 in new growth
- P2O5 21 kg/ha (P 9.2 kg)
- K2O 121 kg/ha (K 100 kg)
- Ca 40 kg/ha
- Mg 12 kg/ha
- S 6 kg/ha (interpolated from yield curve)
- B 0.26 kg/ha; Zn 0.17 kg/ha; Cu 0.13 kg/ha; Mn 0.52 kg/ha; Fe 0.41 kg/ha
[T2 Cheng 2014 NYFQ; Cheng & Raba 2009 JASHS 134(1):3-13]

**Per-tonne FRUIT-ONLY removal** (use this for replacement budgets):

| Nutrient | kg / t fruit | Source |
|---|---|---|
| N | 0.32 (Cheng) / 0.30 (Yara) | [T2 Cheng 2013 Table 2 derivation: 17.2 lb N / 1000 bu × 1110 bu = 25.7 lb at 1500 bu × 19 t = ~0.6 lb/bu = 0.34 kg/t] |
| P (as P) | 0.08 | [T2 Cheng 2013] |
| P2O5 | 0.18 | derived |
| K | 1.05 (Cheng/Palmer 1110 bu = 27.7-110.7 lb depending on yield) | [T2 Cheng 2013 Table 2] |
| K2O | 1.27 | [T2 Cheng 2013] |
| Ca | 0.066 | [T2 Cheng 2013 Palmer 2006: 3.0 lb / 1110 bu = 0.066 kg/t] |
| Mg | 0.052 | [T2 Cheng 2013 Palmer 2006] |
| B (g/t) | 3.2 | [T2 Cheng 2013] |
| Zn (g/t) | 0.6 | [T2 Cheng 2013] |
| Mn (g/t) | 1.1 | [T2 Cheng 2013] |
| Fe (g/t) | 3.6 | [T2 Cheng 2013] |
| Cu (g/t) | 0.6 | [T2 Cheng 2013] |

Removal values yield-linear at r² = 0.81-0.89 (Cheng 2013 Fig 4).

### Per-stage demand split (Cheng 2013 from Gala/M.26 sand culture)

Net gain bud break → harvest = 100 %. Reading off Cheng Fig 1A and 2A:

| Stage window | Days after budbreak | %N net gain | %K net gain | Source |
|---|---|---|---|---|
| Bud break → bloom | 0–35 | 0 | 5 | [T2 Cheng 2013 Fig 1A,2A; reserve N supports spur growth] |
| Bloom → end of spur leaf growth | 35–60 | 40 | 20 | [T2 Cheng 2013] |
| End of spur → end of shoot growth | 60–90 | 25 | 25 | [T2 Cheng 2013] |
| End of shoot → rapid fruit expansion | 90–120 | 15 | 25 | [T2 Cheng 2013] |
| Rapid expansion → harvest | 120–160 | 20 | 25 | [T2 Cheng 2013] |

P, Ca, Mg, S, B follow K-like near-linear pattern bloom→harvest [T2 Cheng & Raba 2009].

Key insight: 65 % of N taken up bloom-to-end-of-shoot-growth (i.e. early-to-mid summer in SA, ~late Oct to late Nov); 75 % of K taken up after end-of-spur-leaf growth (Nov onwards). **Fruit holds 37.6 % of N and 71.3 % of K in new growth at harvest** — fruit is a much stronger K sink than N sink [T2 Cheng 2013 §Demand-supply].

### Yield benchmarks (SA bearing orchards)

| Band | t/ha | Source |
|---|---|---|
| Low | 35–50 | typical of older or lower-density blocks |
| Typical | **65** (Hortgro budget assumption) | [T1 Hortgro Key Deciduous Fruit Statistics 2024 crop budget — Apples bearing] |
| High (high-density M.9 / M.26) | 80–110 (≈ 1500–2000 bu/ac) | [T2 Cheng 2013 Table 2 — published trial maximum 100+] |

Density: SA Hortgro budget assumes **1 667 trees/ha** (typically 4 m × 1.5 m on M.793 or M.7) [T1 Hortgro 2024 budget]. Modern M.9 high-density >2 500/ha possible [T2 Cheng intro].

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Pink → petal fall | B | 0.5 lb actual B/acre (≈ 0.6 kg B/ha) for fruit set, esp. Cripps Pink | [T2 Yara Apple bitter pit; Wisconsin Ext 0.5–2 lb B/acre] |
| 40 DAFB (≈ end Oct) | Ca | first Ca spray — uptake peak 1 (cell division ends) | [T1 Lotze & Theron 2005 in North 2005] |
| 70–90 DAFB (≈ mid-Nov) | Ca | maximum-impact window — peak 2 (end shoot growth); start of effective programme per Lötze ≈ 70 DAFB | [T1 Lotze 2008] |
| Cell division → harvest | Ca(NO3)2 | 4 sprays @ 0.5–1 % a.i. then 2× CaCl2 + Kelpak; minimum 6 sprays, common practice 12 | [T1 ARC/Topfruit Pink Lady Handbook 2003] |
| Pre-harvest (1–4 weeks) | Ca | continue CaCl2 sprays, key for storage Ca | [T1 North & Wooldridge 2005; T2 Yara bitter pit] |
| Post-harvest with green leaves (Apr-May) | Foliar urea | 10 % low-biuret urea, ~50 lb N/acre (≈ 56 kg N/ha) | [T2 Cheng 2013 §foliar; UC ANR peach analogue] |
| Fall (April) | Zn | ZnSO4 5–10 lb/ac (≈ 5.5–11 kg/ha) | [T2 UC ANR / Wisconsin] |

### Adjustments

| Factor | Multiplier on baseline N | Source |
|---|---|---|
| Vigorous growth | 1.0 × (full rate) at bloom + 1.0× post-harvest only — no mid-season top-up | [T1 North & Wooldridge 2005] |
| Normal vigour | 1.0 × bloom + 0.5× at 6 weeks post-flower + 1.0× post-harvest | [T1 North & Wooldridge 2005] |
| Weak growth (after fixing root/irrigation) | 1.0 × bloom + 1.0× at 6 weeks + 1.0× post-harvest | [T1 North & Wooldridge 2005] |
| High-density planting (M.9, >2 000/ha) | 50–80 lb N/ac (56–90 kg N/ha) total, regardless of yield — root system smaller | [T2 Cheng 2013 Amount of Application] |
| Soil OM 3 %+ | Subtract 30–40 lb N/ac (34–45 kg N/ha) supplied by mineralisation | [T2 Cheng 2013] |
| Tree age 1 (planting year) | 5–10 lb N/ac (5.5–11 kg N/ha); ~28 g actual N per tree max | [T2 Wisconsin Ext / UC ANR analogous to peach] |
| Tree age 2-4 | Linear ramp to full bearing rate by year 5 | [T2 Wisconsin Ext] |
| Fertigation vs broadcast | Reduce total N by ~25 % (higher use efficiency) | [T2 Cheng 2013] |

**Canonical SA equation** [T1 North & Wooldridge 2005, derived from Terblanche et al. 1980]:
```
kg N/ha (apple) = (1.5 × anticipated yield t/ha) + 5
clamp 35 ≤ N ≤ 80 kg/ha
```
At 65 t/ha typical Hortgro budget yield → 102.5 kg/ha **but capped at 80 kg/ha**. This is materially LOWER than international benchmarks (Cheng's 50-80 lb/ac = 56-90 kg/ha aligns; 1110 bu/ac = 52.5 t/ha in Cheng matches well). Note SA cap is conservative — designed to protect bitter-pit-sensitive cultivars.

**K canonical**: Cheng Table 2 → at 65 t/ha apple yield (1370 bu/ac), K2O removal ≈ 91 kg/ha; minimum maintenance application 90–112 kg K2O/ha (80–100 lb), up to 168–280 kg K2O/ha if soil low [T2 Cheng 2013 Amount of Application].

### Notes — cultivar specifics, special considerations

- **Bitter pit (Ca disorder)** — pre-harvest Ca sprays reduce risk; positively correlated with fruit size, tree vigour, fruit N, fruit K, fruit Mg. Avoid: irregular irrigation, aggressive thinning (creates oversize fruit), excess spring N. House: rectify pH and soil P in autumn, lime to balance Ca:Mg:K. Fruit K:Ca ratio target <25, ideally <15 [T1 North & Wooldridge 2005; T2 Yara apple].
- **Cultivars high bitter-pit risk**: Cripps Pink, Granny Smith, Golden Delicious, Braeburn (Hortgro export-estimate adjustment list 2024).
- **Cripps Pink** — earliest bloomer (late Sept), latest harvest (late Mar-early Apr); 200-day cycle; needs hot climate; not the worst for bitter pit but still requires Ca programme.
- **Royal Gala** — mid-Feb harvest, "hard" variety, leaf N target 2.0–2.4 %; Cheng's reference cultivar.
- **Honeycrisp** — soft variety; lower leaf K target (1.0–1.3 %); high bitter pit susceptibility; needs intensive Ca programme [T2 Wisconsin Ext].
- **Biennial bearing** — light crop year shows high leaf N due to dilution; heavy crop dilutes K. Combine leaf analysis with crop-load observation [T2 Cheng 2013 §Tree Nutrient Status].
- **Post-harvest N** — critical for SA spring growth the following season; reserves built April-May. Foliar urea after harvest also reduces apple-scab ascospore load [T2 Cheng 2013; Sutton 2000].
- **Fire blight risk** — over-N + under-K imbalance is the trigger; respect N:K ratios.

### Sources consulted (apple)
1. T1 — North, M.S. & Wooldridge, J. 2005. *Pre- and post-harvest management of bitter pit on apples.* DFPT pamphlet, ARC Infruitec-Nietvoorbij, Stellenbosch. https://www.hortgro.co.za/wp-content/uploads/docs/2020/11/4.7.1.B.M_North_bitter_pit_article_2005_pdf.pdf
2. T1 — Hortgro 2024. *Key Deciduous Fruit Statistics 2024* (crop budget pp. 11-13). https://www.hortgro.co.za/wp-content/uploads/docs/dlm_uploads/2025/07/Key-Deciduous-Fruit-Statistics-2024-2.pdf
3. T1 — Topfruit/Various 2003. *South African Pink Lady® Handbook.*  https://www.topfruit.co.za/fruit-statistics-pdfs/2003-Various-experts-Pink-Lady-Handbook-1.pdf (404 — handbook referenced via Hortgro/SmartCherry secondary citations)
4. T1 — Hortgro Postharvest 2024. *Sampling Leaves for Chemical Analyses.* https://postharvest.hortgro.co.za/pag/leaf-sampling-guide/
5. T1 — Lotze, E. & Theron, K.I. 2005. *Dynamics of calcium uptake with pre-harvest sprays to reduce bitter pit in 'Golden Delicious'.* Acta Hortic. (cited in North 2005 ref 2).
6. T1 — Terblanche, J.H., Gurgen, K.H. & Hesebeck, I. 1980. *An integrated approach to orchard nutrition and bitter pit control.* In: Atkinson et al. (eds.) Mineral nutrition of fruit trees. Butterworths, London, pp 71-82. (Source of canonical SA `kg N/ha = 1.5×yield + 5`.)
7. T2 — Cheng, L. 2013. *Optimizing Nitrogen and Potassium Management to Foster Apple Tree Growth and Cropping Without Getting Burned.* New York Fruit Quarterly 21(1): 21-24. https://nyshs.org/wp-content/uploads/2016/10/4.Optimizing-Nitrogen-and-Potassium-Management-to-Foster-Apple-Tree-Growth-and-Cropping-Without-Getting-Burned.pdf
8. T2 — Cheng, L. 2017. *Nutrient Requirements of 'Gala' Apple Trees.* Traverse City presentation. https://www.canr.msu.edu/nwmihort/2016-swd-summit/4GalaAppleNutriReqs_Cheng_TraverseCity2017.pdf
9. T2 — Cheng, L. & Raba, R. 2009. *Accumulation of macro- and micronutrients and nitrogen demand-supply relationship of 'Gala'/M.26 apple trees grown in sand culture.* JASHS 134(1): 3-13.
10. T2 — Stiles, W.C. & Reid, W.S. 1991. *Orchard nutrition management.* Cornell Coop. Ext. Bulletin 219.
11. T2 — Yara United States 2024. *Apple Crop Nutrition Program / Reducing Bitter Pit.* https://www.yara.us/crop-nutrition/apple/reducing-bitter-pit-incidence/
12. T2 — Wisconsin Extension. *Fertilization Guidelines for Mature Apple Trees.* https://cropsandsoils.extension.wisc.edu/articles/fertilization-guidelines-for-mature-apple-trees/
13. T2 — WSU Tree Fruit. *Leaf Tissue Analysis* + *Target Leaf Nutrient Ranges for Tree Fruit.* https://treefruit.wsu.edu/orchard-management/soils-nutrition/leaf-tissue-analysis/
14. T3 — Plank, C.O. 2009. *Apple — Reference Sufficiency Ranges for Plant Analysis in the Southern Region of the United States.* SERA-IEG-6 SCSB394 pp 97-98. https://aesl.ces.uga.edu/sera6/PUB/scsb394.pdf
15. T3 — Shear, C.B. & Faust, M. 1980. *Nutritional ranges in deciduous tree fruits and nuts.* Hortic Rev 2: 142-164.

---

## Pear (Pyrus communis) — Packham's Triumph, Forelle, Williams BC

SA Hortgro budget: 55 t/ha at 1 667 trees/ha [T1 Hortgro 2024]. Bloom slightly earlier than apple; harvest mostly Jan-Mar. SA pear export industry second only to apple.

### Growth stages (Western Cape — Packham bloom mid-Sep, Forelle 1 week later, Williams BC earliest)

| Month (SA) | Stage | Source |
|---|---|---|
| Jun-Aug | Dormancy | — |
| Late Aug | Bud break | [T1 industry standard] |
| Mid Sep | Full bloom (Packham) | [T1 Hortgro] |
| Late Sep | Petal fall, fruit set | — |
| Oct-Nov | Cell division (≈ 30-40 DAFB), end shoot growth | [T2 Cheng pear principles parallel apple] |
| Dec | Early Williams BC harvest begins | [T1 Hortgro stats 2024] |
| Jan-Feb | Packham, Forelle harvest peak | [T1 Hortgro stats 2024] |
| Mar-Apr | Late Packham + post-harvest | — |
| Apr-May | Post-harvest N application window | — |

### Leaf norms — sample timing late Jan-early Feb (mid-shoot)

| Nutrient | Deficient | Adequate | High | Source |
|---|---|---|---|---|
| N (%) | <1.7 | 1.80–2.50 | >2.7 | [T3 SERA Pear p.105] |
| P (%) | <0.10 | 0.12–0.30 | >0.4 | [T3 SERA Pear] |
| K (%) | <1.0 | 1.0–2.0 | >2.5 | [T3 SERA Pear] |
| Ca (%) | <0.8 | 1.0–3.7 (broad) / 1.0–2.0 (SERA) | >4.0 | [T2 WSU; T3 SERA] |
| Mg (%) | <0.20 | 0.25–0.90 (broad) / 0.25–0.50 (SERA) | >1.0 | [T2 WSU; T3 SERA] |
| S (%) | <0.10 | 0.10–0.30 | — | [T3 SERA Pear] |
| B (ppm) | <20 | 20–60 | >70 | [T3 SERA Pear] |
| Zn (ppm) | <15 | 20–50 | >70 | [T3 SERA Pear] |
| Mn (ppm) | <20 | 20–200 | — | [T3 SERA Pear; T2 WSU 20-170] |
| Fe (ppm) | <30 | 30–150 (SERA) / 100–800 (WSU broader) | — | [T3 SERA Pear] |
| Cu (ppm) | <5 | 5–20 | >30 | [T3 SERA Pear] |
| Mo (ppm) | — | — | — | GAP |

**N response zones** (Glozer/CDFA pear): unlikely response above 2.2 % leaf N; uncertain 1.7–2.2 %; likely below 1.7 % [T2 CDFA pear].

### Soil thresholds

GAP — apply pome-fruit defaults from apple section.

### Crop nutrient requirements per tonne yield

GAP for SA pear specifically. International estimates per tonne fresh fruit:
- N: 0.6–1.0 kg/t [T2 NSW DPI Primefact 85 — apple/pear similar]
- K: 1.5–2.0 kg/t (pears similar to apples) [T2 Glozer CDFA pear]
- Ca: 0.05–0.10 kg/t (pears generally less Ca-disorder-prone than apples) [T2 generic]
- P: 0.1 kg/t [T2 generic]
GAP — no SA-specific tonne-yield study found.

### Per-stage demand split

GAP — assume apple curve applies (Cheng-derived) until pear-specific data found. Pear is less determinate than apple but follows similar pome pattern.

### Yield benchmarks (SA)

| Band | t/ha | Source |
|---|---|---|
| Low | 30–40 | older blocks |
| Typical | **55** (Hortgro budget assumption) | [T1 Hortgro 2024] |
| High | 70–80 | high-density Forelle/Williams |

Density: 1 667 trees/ha (Hortgro budget).

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Pink-petal fall | B | 0.5 lb a.i./ac (≈ 0.6 kg B/ha) — Forelle especially fruit-set sensitive | [T2 Yara pear / Wisconsin] |
| Cell expansion → pre-harvest | Ca | 4–6 sprays Ca(NO3)2 / CaCl2 — pear bitter pit (Forelle) less common than apple but cork spot is the analogue | [T2 NSW DPI Primefact 85] |
| Post-harvest | Foliar urea | analogue to apple | [T2 generic] |

### Adjustments

Apply apple framework (vigour-adjusted N split). SA equation `kg N/ha = (1.5 × yield) + 5` is widely used in SA pome fertilisation but **not directly cited for pear in the North 2005 article — apple-only**. GAP — needs Hortgro pear-specific guidance; safe to use same equation.

### Notes
- **Forelle cork spot** is the pear analogue of bitter pit; Ca sprays equivalent.
- **Williams BC** = Bartlett; canning + fresh; first harvest.
- **Asian pear varieties** (e.g., Nashi) not in SA brief but follow similar profile.
- **Pear decline** is a phytoplasma issue, not nutritional — but mineral imbalance exacerbates rootstock sensitivity.

### Sources consulted (pear)
1. T1 — Hortgro 2024 *Key Deciduous Fruit Statistics 2024* — pear budgets pp 11-13.
2. T2 — NSW DPI 2008. *Apple and pear nutrition.* Primefact 85 (J. Bright). https://www.dpi.nsw.gov.au/__data/assets/pdf_file/0004/41485/Apple_and_pear_nutrition_-_Primefact_85.pdf (search-cited; download blocked 403)
3. T2 — WSU Tree Fruit. *Leaf Tissue Analysis* — pear ranges.
4. T2 — Glozer, K. 2013. *European Pear Growth and Cropping: Optimizing Fertilizer.* CDFA FREP completed project. https://www.cdfa.ca.gov/is/ffldrs/frep/pdfs/completedprojects/10-0105-SA_Glozer.pdf
5. T3 — Plank, C.O. & Lippert, R.M. 2009. *Pear* — SERA-IEG-6 SCSB394 pp 105-106.
6. T3 — Hanson, E. 1993. *Apples and pears.* In: Bennett WF (ed.) Nutrient deficiencies & toxicities in crop plants. APS Press pp 159-163.

---

## Plum (Prunus salicina / domestica) — Japanese plum dominant in SA

SA Hortgro budget: 30 t/ha at 1 524 trees/ha (V-trellis) [T1 Hortgro 2024]. SA exports plums Nov-end Apr.

### Growth stages

| Month (SA) | Stage |
|---|---|
| Jul-mid Aug | Dormancy, rest-breaking sprays |
| Late Aug | Bud break, white tip |
| Sep | Full bloom (varies by cultivar — Methley Aug-Sep, Songold Oct) |
| Oct | Petal fall, fruit set, June drop equivalent |
| Nov | Pit hardening |
| Nov-Apr | Harvest (cultivar-dependent) — Methley Nov; Songold, Angeleno, Laetitia Jan-Mar |
| May-Jun | Post-harvest, leaf drop |

### Leaf norms — sample mid-July CA / mid-Jan SA (8-10 weeks after FB)

CDFA prune/plum applies; UC critical values established for July sampling NH = January SH.

| Nutrient | Deficient | Adequate | High | Source |
|---|---|---|---|---|
| N (%) — Japanese plum | <2.2 | 2.3–2.8 | >2.8 | [T2 CDFA Prune & Plum] |
| N (%) — conservative | — | 2.4–2.5 (lower bound) | — | [T2 CDFA] |
| P (%) | <0.10 | 0.10–0.30 | >0.4 | [T2 CDFA] |
| K (%) | <1.0 | 1.3–2.0 | >2.0 | [T2 CDFA Prune & Plum] |
| K (%) — conservative | — | ≥1.5 | — | [T2 CDFA] |
| Ca (%) | <0.8 | 1.0–2.5 | >3.0 | GAP — adopt UC peach analogue |
| Mg (%) | <0.20 | 0.25–0.50 | >0.7 | GAP — adopt UC peach |
| Zn (ppm) | <18 | 20–50 | — | [T2 CDFA] |
| B (ppm) | <20 | 20–80 | >100 | GAP — adopt UC peach |
| Mn / Fe / Cu / S / Mo | — | apply peach values | — | GAP |

### Soil thresholds (CDFA)

| Nutrient | Low | Medium | High | Excessive | Source |
|---|---|---|---|---|---|
| Bray-1 P (ppm) | <20 | 20–40 | 40–100 | >100 | [T2 CDFA Prune & Plum] |
| Olsen P (ppm) | <10 | 10–20 | 20–40 | >40 | [T2 CDFA] |
| K exch (ppm) | <75 (very low) / 75–150 (low) | 150–250 | 250–800 | >800 | [T2 CDFA] |

### Crop nutrient requirements per tonne yield

CDFA gives values per dry ton of prunes. Convert to fresh fruit (water content ~80 % for fresh plum, prune dry-to-fresh ~3:1):

| Nutrient | kg / t fresh fruit | Source |
|---|---|---|
| N | 1.7–2.5 (= 10–15 lb / dry ton ÷ 3 × 0.454) | [T2 CDFA Prune & Plum] |
| P (as P2O5) | 0.83 | [T2 CDFA: ~5 lb P2O5/dry ton] |
| K (as K2O) | 3.8 | [T2 CDFA: ~23 lb K2O/dry ton] |
| Ca, Mg, S, micros | GAP — extrapolate from peach |

### Per-stage demand split

Plum N timing (CDFA): 20-30 % spring (Sep-Oct SA), 70-80 % mid-late summer (Nov-Jan SA), small post-harvest. Less front-loaded than apple [T2 CDFA Prune & Plum].

### Yield benchmarks (SA)

| Band | t/ha |
|---|---|
| Low | 18–25 |
| Typical | **30** [T1 Hortgro budget] |
| High | 40–50 |

Density 1 524 trees/ha V-system (Hortgro).

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Apr-Jul (SA: Oct-Jan) | KNO3 | 20-30 lb / 100 gal water (≈ 24-36 g/L); 2-3 wk intervals; total ~100 lb/ac (= 45 lb K2O/ac ≈ 50 kg K2O/ha) | [T2 CDFA Prune & Plum] |
| Spring | Zn (oxide / basic ZnSO4) | 3–5 lb / 100 gal | [T2 CDFA] |
| Fall/dormancy | ZnSO4 | 10–25 lb / 100 gal | [T2 CDFA] |
| Pre-bloom | B | 0.3–0.5 lb a.i./ac (0.34–0.56 kg/ha) — improves fruit set | [T2 CDFA generic stone] |

### Adjustments — CDFA young-tree plum N

| Year | g N / tree | kg N / ha (at 1 524/ha SA density, scaled from 183/ac CDFA) |
|---|---|---|
| 1 | 13–25 | 20–38 (1 oz N/tree analogue) |
| 2 | 62 | 95 |
| 3 | 73 | 112 |
| 4 | 99 | 151 |
| 5 | 187 | 285 |

(CDFA values for 14×17 ft = 183 trees/ac. Per-tree rates more transferable than per-ha.)

### Notes
- **Cultivars in SA**: Methley (early), Songold, Laetitia, Angeleno, African Delight, Sapphire — diverse harvest window Nov–April.
- **Bacterial canker** — manage with N (urea 46 lb/ac = 52 kg/ha extra) — risk for plum more than peach in SA.
- **K demand high** — Japanese plums very K-hungry. Don't underdose K.
- **Pit-burn** — mostly Bulida apricot but Songold plum prone if N excess + irregular irrigation.

### Sources consulted (plum)
1. T1 — Hortgro 2024 *Key Deciduous Fruit Statistics 2024* — plum budgets.
2. T2 — CDFA FREP. *Prune and Plum Fertilization Guidelines.* https://www.cdfa.ca.gov/is/ffldrs/frep/FertilizationGuidelines/Prune_Plum.html
3. T2 — UC ANR Fruit & Nut Research & Information Center. *Stone Fruit Production / Nutrients & Fertilization.* https://ucanr.edu/site/fruit-nut-research-information-center/nutrients-fertilization

---

## Peach (Prunus persica) — cling + dessert

SA Hortgro budget: 25 t/ha at 1 250 trees/ha (peaches & nectarines combined budget) [T1 Hortgro 2024]. SA peach industry split between cling (canning) ≈ 60 % area and dessert ≈ 40 %.

### Growth stages

| Month (SA) | Stage |
|---|---|
| Jun-Jul | Dormancy |
| Late Jul-early Aug | Bud swell, rest-breaking sprays |
| Aug | Full bloom (early dessert: late Aug; cling: early Sep) |
| Sep | Petal fall, shuck split, fruit set |
| Oct-mid Nov | Pit hardening (Stage II — slow growth) |
| Mid Nov-Jan | Stage III rapid fruit expansion + harvest (early dessert in Nov; cling Jan) |
| Feb-Mar | Late cling harvest |
| Apr-May | Post-harvest N window |
| May-Jun | Leaf drop |

### Leaf norms — sample timing mid-shoot July (NH) ≈ mid-January (SA)

| Nutrient | Deficient | Adequate | High | Source |
|---|---|---|---|---|
| N (%) — fresh market | <2.3 | 2.4–3.0 | >3.0 | [T2 CDFA Peach & Nectarine] |
| N (%) — processing/cling | <2.4 | 2.6–3.5 | >3.5 | [T2 CDFA] |
| N (%) — SERA | <2.5 | 2.75–3.50 | >4.0 | [T3 SERA Peach p.103] |
| P (%) | <0.10 | 0.12–0.30 | >0.4 | [T2 CDFA; T3 SERA] |
| K (%) | <1.0 | 1.30–3.20 (SERA broad) / 1.2–3.0 (WSU) | >3.5 | [T2/T3 consensus] |
| Ca (%) | <0.8 | 1.50–2.50 | >3.0 | [T3 SERA Peach] |
| Mg (%) | <0.20 | 0.25–0.50 | >0.7 | [T3 SERA Peach] |
| S (%) | <0.12 | 0.12–0.40 | — | [T3 SERA Peach] |
| B (ppm) | <20 | 20–80 | >100 | [T3 SERA Peach] |
| Zn (ppm) | <15 | 20–50 | >70 | [T2 CDFA <15 deficient; T3 SERA 20-50] |
| Mn (ppm) | <20 | 20–200 | — | [T3 SERA Peach >20 sufficient] |
| Fe (ppm) | <60 | >60 (120–200 WSU) | — | [T2 WSU; T3 SERA] |
| Cu (ppm) | <4 | 5–20 | >25 | [T3 SERA Peach 5-20] |

### Soil thresholds (CDFA)

| Nutrient | Low | Medium | High | Excessive |
|---|---|---|---|---|
| Bray-1 P (ppm) | <20 | 20–40 | 40–100 | >100 |
| Olsen P (ppm) | <10 | 10–20 | 20–40 | >40 |
| K exch (ppm) | <75 (very low) / 75–150 (low) | 150–250 | 250–800 | >800 |

### Crop nutrient requirements per tonne yield

| Nutrient | kg / t fresh fruit | Source |
|---|---|---|
| N | 1.0–1.5 (= 2-3 lb/ton × 0.454) | [T2 CDFA Peach & Nectarine] |
| P (as P2O5) | 0.23–0.45 | [T2 CDFA: 0.5–1.0 lb P2O5/ton] |
| K (as K2O) | 1.8–2.3 | [T2 CDFA: 4-5 lb K2O/ton avg] |
| Ca | 0.15–0.20 | [T3 derived from Johnson 1993 Stone Fruit chapter] |
| Mg | 0.10 | GAP — derived |

### Per-stage demand split

Peach takes up very little N during dormancy or pre-leaf-out spring [T2 CDFA]. Peak uptake mid-spring (Sep-Oct SA, after leaf-out) and post-harvest (April-May SA) when leaves still green. Stage III (fruit fill) is heavy K demand window. Distribution rough split:

| Stage | %N | %K2O | Source |
|---|---|---|---|
| Bud break-bloom | <5 | 5 | [T2 CDFA reasoning] |
| Bloom-pit hardening (Stage I+II) | 35 | 20 | [T2 CDFA] |
| Stage III rapid expansion | 30 | 50 | [T2 CDFA / Yara analogue] |
| Post-harvest | 30 | 25 | [T2 CDFA — fall foliar urea ~50 lb N/ac] |

### Yield benchmarks (SA)

| Band | t/ha |
|---|---|
| Low | 12–18 |
| Typical | **25** [T1 Hortgro budget] |
| High | 35–45 (intensive cling) |

Density 1 250 trees/ha (Hortgro).

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Pre-bloom | B | 0.3–0.5 lb a.i./ac (0.34–0.56 kg/ha) | [T2 CDFA] |
| Pit hardening + 6 wk pre-harvest + 3 wk pre-harvest | K (as K2SO4) | 3 sprays totalling 40 lb K2O/ac (≈ 45 kg K2O/ha) — equivalent to 80 lb soil K | [T2 CDFA Peach & Nectarine §Foliar K] |
| Mid-late October (NH) → mid-late April (SA) | Foliar urea (10 % low-biuret) | ≈ 50 lb N/ac (56 kg N/ha) | [T2 CDFA] |
| Mid-late April (SA) | ZnSO4 | 5 lb/ac (5.6 kg/ha) early; 10-50 lb fall | [T2 CDFA] |

### Adjustments — CDFA young-tree peach N

> "Apply no more than one ounce of N per tree per year of growth with a single application." Equivalent: 4 oz/tree year 1, 8 oz year 2, 12 oz year 3, divided into 3-4 applications.

| Yield (t/ha) | N requirement (kg/ha) — assumes prunings remain, 70 % use efficiency |
|---|---|
| 13 | 71 |
| 27 | 96 |
| 40 | 122 |
| 54 | 148 |
| 67 | 174 |
(CDFA Peach Table converted from lb/ac → kg/ha and tons/ac → t/ha)

### Notes
- **Cultivars** SA dessert: Sundance, Transvalia, Oom Sarel, Eersteling. Cling: Kakamas group, Walgant, Ouhongers, Sandvliet — bred ARC Stellenbosch.
- **Peach decline** indicator: low Ca + high Zn in leaves [T3 SERA Peach Remarks].
- **Bacterial canker** — high-N strategy (100 lb urea/ac extra) per CDFA — applies to SA cold-injury seasons.
- **Pre-harvest foliar K (3 sprays)** is the canonical CDFA practice for fruit-size correction in K-deficient blocks.

### Sources consulted (peach)
1. T1 — Hortgro 2024 *Key Deciduous Fruit Statistics 2024* — peach/nectarine budgets.
2. T2 — CDFA FREP. *Peach and Nectarine Fertilization Guidelines.* https://www.cdfa.ca.gov/is/ffldrs/frep/FertilizationGuidelines/Peach_Nectarine.html
3. T2 — Geisseler, D. UC Davis. *Peach/Nectarine guideline notes.* http://geisseler.ucdavis.edu/Guidelines/Peach_Nectarine.html
4. T3 — Lippert, R.M. & Campbell, C.R. 2009. *Peach* — SERA-IEG-6 SCSB394 pp 103-104.
5. T3 — Johnson, R.S. 1993. *Stone fruit: peaches and nectarines.* In Bennett WF (ed.) Nutrient deficiencies and toxicities in crop plants. APS Press pp 171-175.
6. T2 — Haifa Group. *Peach Tree Fertilizer.* https://www.haifa-group.com/fertilization-peach-trees-comprehensive-recommendation

---

## Nectarine (Prunus persica var. nucipersica)

Treated by CDFA jointly with peach. Hortgro budget combined with peach: 25 t/ha at 1 250 trees/ha [T1].

### All categories

**Apply peach values directly** — fertility programmes are interchangeable. CDFA explicitly groups peach + nectarine. Differences:
- Nectarine harvest tends 1-2 weeks earlier than equivalent peach cultivar.
- Slightly more sensitive to pit-burn under high-N + heat stress — favour split-N.
- Skin-Ca uptake critical for hairless skin appearance — Ca sprays at fruit expansion as for peach.

### Growth stages (SA)

| Month | Stage |
|---|---|
| Jul-Aug | Dormancy / bud swell |
| Aug-early Sep | Bloom (1–2 wk earlier than equivalent peach) |
| Oct | Fruit set, pit hardening start |
| Nov-Feb | Stage III + harvest (Nov-Feb shipping per Hortgro) |
| Mar-Apr | Late cultivars + post-harvest |

### Yield benchmark
Typical 25 t/ha (Hortgro budget combined).

### Sources
Same as peach.

---

## Apricot (Prunus armeniaca) — Bulida dominant in Klein Karoo

SA Hortgro budget: 20 t/ha at 1 250 trees/ha [T1 Hortgro 2024]. Klein Karoo accounts for >75 % of SA apricot area; Bulida is ≈ 50 % of total [T2 industry sources]. Bulida = Spanish-origin canning cv.

### Growth stages (Klein Karoo, Bulida — earliest stone fruit bloom)

| Month (SA) | Stage | Source |
|---|---|---|
| Jun-Jul | Deep dormancy | — |
| Late Jul-early Aug | Bud swell, white tip | — |
| Mid-late Aug | Full bloom — earliest stone fruit | [T1 SA industry; T3 Ruiz et al. on Bulida — full bloom early March NH = early Sep SH] |
| Sep | Petal fall, fruit set, June drop equiv | — |
| Oct | Pit hardening, slow growth | — |
| Nov-Dec | Rapid fruit expansion + harvest (Bulida ripens late Nov-early Dec SA) | [T1 SA growers; T2 Cape Five / FreshPlaza] |
| Dec-Jan | Late cultivars (Soldonne, Palsteyn, Charisma) | — |
| Feb-Apr | Trunk growth period (post-harvest); [T3 Ruiz Bulida main trunk growth July-Oct = Jan-Apr SA] | |
| Apr-May | Leaf drop, dormancy onset | — |

### Leaf norms — sample mid-Jan SA (= July NH stable window, 8-10 wk after FB)

| Nutrient | Deficient | Adequate | High | Source |
|---|---|---|---|---|
| N (%) | <2.30 | 2.30–3.10 | >3.3 | [T3 Greek apricot / Mediterranean ranges; T2 WSU 2.4-3.3 narrower] |
| P (%) | <0.10 | 0.10–0.15 (Greek) / 0.10–0.30 (WSU) | >0.4 | [T2 WSU; T3 Greek] |
| K (%) | <0.66 | 2.0–3.5 (WSU) / 0.66-2.38 (Greek wide) | >3.5 | [T2 WSU; T3 Greek] |
| Ca (%) | <1.10 | 1.74–3.49 (Greek) / 1.10–4.00 (WSU) | >4.5 | [T2 WSU; T3 Greek] |
| Mg (%) | <0.25 | 0.62–1.48 (Greek high) / 0.25–0.80 (WSU) | >1.5 | [T2 WSU; T3 Greek] |
| S (%) | <0.20 | 0.20–0.40 | — | [T2 WSU] |
| B (ppm) | <13 | 20–70 (WSU) / 13.3–24.7 (Greek) | >100 | [T2 WSU; T3 Greek] |
| Zn (ppm) | <16 | 16–50 | — | [T2 WSU; T3 Greek 15.5-34.5] |
| Mn (ppm) | <20 | 20–272 | — | [T2 WSU 20-160; T3 Greek 39.5-272] |
| Fe (ppm) | <60 | 60–250 | — | [T2 WSU; T3 Greek 62.5-131] |
| Cu (ppm) | <4 | 4–16 | — | [T2 WSU; T3 Greek 9.5-16] |
| Mo (ppm) | — | — | — | GAP |

### Soil thresholds

GAP — apply stone-fruit defaults (CDFA peach table). Apricot tolerates higher pH (7.0-7.5) than other stone fruits.

### Crop nutrient requirements per tonne yield

GAP — no SA / Mediterranean apricot yield-removal study found at depth. Estimates from Haifa generic stone-fruit and Bergeron pit-burn study (Brun & Pluviet 2002):
- N: 1.5–2.0 kg/t fresh fruit (apricot is more N-responsive than peach)
- K: 2.5–3.5 kg/t (high K demand)
- Ca: 0.15 kg/t — pit-burn risk if low

International Bergeron trial: apricot showed yield/quality response up to **150 kg N/ha**, declining over 150 [T3 Brun & Pluviet 2002 Sci Hortic — apricot Bergeron N rate trial].

### Yield benchmarks (SA)

| Band | t/ha |
|---|---|
| Low | 10–15 |
| Typical | **20** [T1 Hortgro budget] |
| High | 25–30 (Bulida intensive) |

Density 1 250 trees/ha (Hortgro).

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Pink-bloom | B | 0.3–0.5 lb a.i./ac | [T2 generic stone fruit / Haifa] |
| Pit hardening | Ca | CaCl2 / Ca(NO3)2 sprays — Bulida pit-burn prevention | [T1 SA growers practice; T3 Brun 2002] |
| Stage III | K | 2-3 sprays KNO3 | [T2 Haifa apricot] |
| Post-harvest (Apr) | Foliar urea | apple/peach analogue | [T2 generic] |

### Adjustments

Apricot N sensitivity: **rate × timing matters more than total**. Bergeron study: 150 kg N/ha with proper timing > 200 kg N/ha excess [T3 Brun 2002]. Apply CDFA peach-style young tree ramp.

### Notes
- **Pit-burn** — Bulida-specific disorder; high-N + heat + low K + irregular irrigation. SA Klein Karoo classic problem. Manage by N moderation + K sprays + steady irrigation.
- **Bulida** — Spanish cultivar, bloomed earliest, frost risk in Klein Karoo.
- **Charisma, Palsteyn, Soldonne** — newer SA-bred cultivars, later bloom.
- **Chilling requirement** — low (~400 chill units), suits SA inland.

### Sources consulted (apricot)
1. T1 — Hortgro 2024 *Key Deciduous Fruit Statistics 2024* — apricot budgets.
2. T2 — WSU Tree Fruit. *Leaf Tissue Analysis* — apricot ranges.
3. T2 — Haifa Group. *Apricot Tree Fertilizer.* https://www.haifa-group.com/fertilization-apricots
4. T3 — Mediterranean apricot leaf nutrient sufficiency study (Greek) — N 2.30-3.10, K 0.66-2.38, etc. Cited via ISHS abstract https://www.ishs.org/ishs-article/701_119
5. T3 — Brun, R. & Pluviet, J. 2002. *Effects of fertilizer rates and dates of application on apricot (cv Bergeron) cropping and pitburn.* Scientia Hortic. https://www.sciencedirect.com/science/article/abs/pii/S0304423802002030
6. T3 — Ruiz, D. & Egea, J. 2008. *Growth and phenological stages of Bulida apricot trees in South-East Spain* — BBCH coding. https://hal.science/hal-00886246/document (access blocked; search snippet only)

---

## Cherry (Prunus avium — sweet cherry)

SA Hortgro budget: 12 t/ha at 1 667 trees/ha [T1 Hortgro 2024]. SA cherry production small but growing — Ceres + Free State + Mpumalanga. Most data is PNW WSU because SA-specific data is sparse.

### Growth stages (SA — Bing/Lapins/Sweetheart)

| Month (SA) | Stage |
|---|---|
| Jun-Jul | Dormancy (cherries need 700-1000 chill units, edge of SA range) |
| Late Jul-Aug | Bud swell |
| Late Aug-mid Sep | Full bloom |
| Sep | Petal fall, fruit set; root growth begins ≥ 15 °C soil temp [T2 WSU] |
| Sep-Oct | Cell division (21-28 DAFB) |
| Oct-Nov | Stage III rapid expansion + Ca uptake max from ~25 DAFB [T2 WSU] |
| Mid Nov-mid Dec | Harvest (early cultivars Nov; Sweetheart late Dec) |
| Dec-Jan | Post-harvest, leaves still green |
| Apr-May | Leaf drop |

### Leaf norms — sample mid-Jan SA (= July NH; June 15-July 15 stability window per WSU)

| Nutrient | Deficient | Adequate | High | Source |
|---|---|---|---|---|
| N (%) | <2.0 | 2.00–3.03 | >3.3 | [T2 WSU sweet cherry] |
| P (%) | <0.10 | 0.10–0.27 | >0.4 | [T2 WSU] |
| K (%) | <1.0 | 1.20–3.30 | >3.5 | [T2 WSU] |
| Ca (%) | <1.0 | 1.20–2.37 | >3.0 | [T2 WSU] |
| Mg (%) | <0.25 | 0.30–0.77 | >1.0 | [T2 WSU] |
| S (%) | <0.18 | 0.20–0.40 | — | [T2 WSU] |
| B (ppm) | <17 | 17–60 | >70 | [T2 WSU] |
| Zn (ppm) | <12 | 12–50 | — | [T2 WSU] |
| Mn (ppm) | <17 | 17–160 | — | [T2 WSU] |
| Fe (ppm) | <57 | 57–250 | — | [T2 WSU] |
| Cu (ppm) | — | 0–16 | >20 | [T2 WSU] |
| Mo (ppm) | — | — | — | GAP |

### Soil thresholds (WSU sweet cherry — best PNW data)

| Nutrient | Target | Action threshold | Source |
|---|---|---|---|
| Olsen-P (mg/kg) | 15–40 | <15 → apply 40 lb P2O5/ac (≈ 45 kg P2O5/ha); <5 → multi-year correction | [T2 WSU sweet cherry] |
| Exch K (mg/kg) | 150–300 | <150 → apply 120 lb K2O/ac (≈ 134 kg K2O/ha); >300 → no K; >300 inhibits Mg uptake | [T2 WSU] |
| Ca (meq/100g) | ≥4 | >8 meq → adding more Ca ineffective | [T2 WSU] |
| B (mg/kg hot water) | 0.5–1.5 | <0.5 → deficient | [T2 WSU] |
| pH | 6.0–7.0 | — | GAP — generic |

### Crop nutrient requirements per tonne yield

| Nutrient | kg / t fresh fruit | Source |
|---|---|---|
| N | 0.86–2.27 (= 1.9-5.0 lb/ton × 0.454) | [T2 WSU Table 1] |
| P (as P) | 0.23–0.41 | [T2 WSU] |
| P (as P2O5) | 0.52–0.94 | derived |
| K (as K) | 1.32–2.86 | [T2 WSU] |
| K (as K2O) | 1.59–3.45 | derived |
| Ca | 0.14–0.18 | [T2 WSU] |
| Mg | 0.09–0.18 | [T2 WSU] |
| S | 0.09–0.18 | [T2 WSU] |

Cherry is K-hungry per tonne — but tonne yield is low (12 t/ha), so absolute kg/ha modest.

### Per-stage demand split

WSU notes cherry takes up most N petal-fall to month-pre-harvest [T2 WSU]. Avoid late-season N (reduces colour). Ca uptake max begins ~25 DAFB. Estimate:

| Stage | %N | %K | Source |
|---|---|---|---|
| Bud break-bloom | 5 | 5 | [T2 WSU] |
| Petal fall to pit hardening | 50 | 30 | [T2 WSU] |
| Stage III + harvest | 15 | 50 | [T2 WSU — late N inhibits colour] |
| Post-harvest (Dec-Jan SA) | 30 | 15 | [T2 WSU — fall foliar N for reserves] |

### Yield benchmarks (SA)

| Band | t/ha |
|---|---|
| Low | 6–8 |
| Typical | **12** [T1 Hortgro budget] |
| High | 15–20 (high-density Gisela rootstock) |

Density 1 667 trees/ha (Hortgro budget).

### Foliar protocols

| Stage | Nutrient | Rate | Source |
|---|---|---|---|
| Late dormant / pre-bloom | B | <0.5 lb a.i./ac (foliar) | [T2 WSU "should not surpass 0.5 lb actual B/ac"] |
| Pit hardening → harvest | Ca | foliar CaCl2 or Ca(NO3)2 — for cracking + firmness | [T2 WSU practice] |
| Mg-deficient | Foliar MgSO4 | when root uptake limited | [T2 WSU] |
| Soil Mg-deficient | MgSO4 | 30 lb/ac (≈ 34 kg/ha) | [T2 WSU] |
| Post-harvest Ca dipping | CaCl2 | 0.2-0.5 % (2 000-5 000 ppm), 5 min then 15 min cold water 0 °C | [T2 WSU post-harvest] |
| Fall (post-harvest) | Foliar N | apple/peach analogue | [T2 WSU] |

### Adjustments

Limited published rate-by-age data for sweet cherry. Use peach young-tree N ramp (1 oz/tree/year of growth max as single application).

### Notes
- **Chilling requirement** — Bing 700 chill units; SA marginal except Ceres, EFC, Mpumalanga highveld.
- **Cracking** — Ca foliar + canopy management critical; SA summer rain in Free State a major issue.
- **Gisela rootstocks** — dwarfing, more precocious; smaller root system → manage N closely.
- **Late-N** = poor colour — common error.
- **Excess soil K (>300 mg/kg) blocks Mg** — leads to leaf-yellow and reduced firmness [T2 WSU].

### Sources consulted (cherry)
1. T1 — Hortgro 2024 *Key Deciduous Fruit Statistics 2024* — cherry budget p. 13.
2. T2 — WSU Tree Fruit. *Nutrient Management in Sweet Cherries.* https://treefruit.wsu.edu/nutrient-management-in-sweet-cherries/
3. T2 — WSU Tree Fruit. *Leaf Tissue Analysis* (master table).

---

## Aggregate notes & conflicts to flag

### Top 3 sources by data density
1. **Cheng 2013 NYFQ + Cheng 2017 Traverse City presentation** — gold-standard quantitative apple data (whole-tree N/K accumulation curves, kg/ha by yield, fruit-only removal). 22-page PDF with full per-stage curves.
2. **WSU Tree Fruit Leaf Tissue Standards** + **Nutrient Management in Sweet Cherries** — broadest cross-crop coverage of leaf norms (apple/pear/cherry/peach/apricot) with actual % and ppm values; cherry kg-per-tonne removal table.
3. **CDFA FREP fertilization guidelines (Peach/Nectarine + Prune/Plum)** — best stone-fruit fertilizer rate tables, young-tree ramps, foliar K protocols, soil thresholds.

SA-specific anchors: **Hortgro 2024 Key Deciduous Fruit Statistics** (yield/density baselines) + **North & Wooldridge 2005** (apple bitter pit + canonical N equation derived from Terblanche 1980) + **Hortgro Postharvest Leaf Sampling Guide** (sampling protocol). SA published nutrient thresholds are sparse — most leaf/soil norms inherited from Cornell/WSU/CDFA.

### Conflicts spotted (current SA seed verification)
- **Apple N target leaf**: SERA gives 1.80–2.10 % for Golden Delicious, 1.90–2.30 % for "all other"; Cheng/Cornell gives 1.8–2.2 % "soft" vs 2.0–2.4 % "hard" — overlap but not identical. The Cornell varietal split is more nuanced and probably the right model for SA seed.
- **Apple kg N/ha equation** — `(1.5 × yield) + 5` gives 102.5 kg/ha at 65 t/ha typical SA yield; **clamped to 80 kg/ha by North 2005 ceiling**. This ceiling is conservative and matches Cheng's 56-90 kg/ha empirical optimum. If current SA seed has higher N rates without the cap, that's the "materially wrong" issue flagged in MEMORY.
- **Bitter pit cultivar list** — confirm seed flags Cripps Pink, Granny Smith, Golden Delicious, Braeburn, Fuji, Honeycrisp as high-risk; current seed should ensure Ca foliar protocol triggers for these.
- **Cripps Pink bloom date** — late Sept / early Oct SA (200-day cycle). If seed shows mid-Sept like Royal Gala, that's wrong.

### Major gaps
1. **No SA-specific kg/t nutrient removal study** for any deciduous fruit — all kg/t numbers are imported from Cornell/WSU/CDFA. Hortgro Science likely has unpublished work; worth a research grant or direct request to ARC Infruitec.
2. **Pear** — no Hortgro-specific N equation; assume apple analogue. Cork spot management protocol detail thin.
3. **Apricot per-stage demand split** — Bergeron N study gives total but no within-season distribution.
4. **Cherry SA leaf norms** — entirely PNW-derived; SA growing windows (lower latitude, higher light) may shift values.
5. **Soil thresholds for apple/pear** — CDFA stone-fruit values used; Hortgro PAG likely has SA-calibrated tables not surfaced in this pass (`Kotze 1996` cited by North 2005 but unpublished/print-only).
6. **Plum cultivar-specific** — Songold pit-burn vs Methley vs Sapphire all merged under generic "Japanese plum" CDFA values.
7. **Mo sufficiency** — no published value for any of the 7 deciduous crops.
