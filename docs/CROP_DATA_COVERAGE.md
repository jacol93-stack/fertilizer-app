# Crop Data Coverage Audit

_Generated 2026-05-04 23:25 UTC. 82 crops in `crop_requirements`._
_Regenerate: `python sapling-api/scripts/generate_crop_coverage.py`_

Every blank cell or `_needs source_` marker is a literature search. When a citation lands, add the row to the appropriate table and rerun this script — the gap will close on the next diff.

## Summary — coverage matrix

Counts are rows in each per-crop table.

| Crop | base reqs | soil bands | growth stages | rate cells | leaf norms | removal | age factors | yield bench | calc flags | methods |
|---|---|---|---|---|---|---|---|---|---|---|
| [Apple](#apple) | 1 | 8 | 5 | 0 | 11 | 1 | 5 | 1 | 1 | 3 |
| [Apricot](#apricot) | 1 | 5 | 5 | 0 | 11 | 0 | 4 | 1 | 0 | 3 |
| [Asparagus](#asparagus) | 1 | 0 | 4 | 12 | 5 | 2 | 0 | 1 | 1 | 3 |
| [Avocado](#avocado) | 1 | 10 | 5 | 0 | 16 | 1 | 5 | 9 | 1 | 3 |
| [Banana](#banana) | 1 | 7 | 4 | 15 | 11 | 1 | 2 | 1 | 1 | 3 |
| [Barley](#barley) | 1 | 0 | 4 | 0 | 1 | 3 | 0 | 0 | 1 | 3 |
| [Bean (Dry)](#bean-dry) | 1 | 5 | 4 | 60 | 0 | 2 | 0 | 2 | 1 | 4 |
| [Bean (Green)](#bean-green) | 1 | 0 | 4 | 7 | 0 | 0 | 0 | 0 | 1 | 4 |
| [Beetroot](#beetroot) | 1 | 4 | 0 | 7 | 0 | 0 | 0 | 0 | 1 | 0 |
| [Blackberry](#blackberry) | 1 | 1 | 0 | 4 | 11 | 0 | 0 | 0 | 1 | 0 |
| [Blueberry](#blueberry) | 1 | 3 | 5 | 3 | 11 | 1 | 3 | 1 | 1 | 3 |
| [Brinjal](#brinjal) | 1 | 6 | 0 | 7 | 11 | 0 | 0 | 0 | 0 | 0 |
| [Butternut](#butternut) | 1 | 0 | 4 | 9 | 11 | 0 | 0 | 1 | 0 | 4 |
| [Cabbage](#cabbage) | 1 | 1 | 4 | 7 | 8 | 1 | 0 | 1 | 1 | 4 |
| [Canola](#canola) | 1 | 6 | 5 | 21 | 13 | 1 | 0 | 2 | 1 | 4 |
| [Carrot](#carrot) | 1 | 3 | 4 | 7 | 6 | 0 | 0 | 1 | 0 | 4 |
| [Cassava](#cassava) | 1 | 1 | 0 | 3 | 0 | 1 | 0 | 0 | 0 | 0 |
| [Cherry](#cherry) | 1 | 5 | 5 | 0 | 11 | 1 | 4 | 1 | 0 | 0 |
| [Chillies](#chillies) | 1 | 5 | 0 | 7 | 11 | 0 | 0 | 2 | 0 | 0 |
| [Citrus](#citrus) | 1 | 16 | 0 | 0 | 11 | 0 | 5 | 12 | 1 | 0 |
| [Citrus (Grapefruit)](#citrus-grapefruit) | 1 | 0 | 5 | 0 | 12 | 1 | 5 | 0 | 0 | 3 |
| [Citrus (Lemon)](#citrus-lemon) | 1 | 0 | 4 | 0 | 12 | 1 | 5 | 0 | 0 | 3 |
| [Citrus (Navel)](#citrus-navel) | 1 | 0 | 5 | 0 | 12 | 1 | 5 | 0 | 0 | 3 |
| [Citrus (Soft Citrus)](#citrus-soft-citrus) | 1 | 0 | 5 | 0 | 12 | 1 | 5 | 0 | 0 | 3 |
| [Citrus (Valencia)](#citrus-valencia) | 1 | 0 | 5 | 0 | 11 | 1 | 5 | 0 | 0 | 3 |
| [Coffee](#coffee) | 1 | 2 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| [Cotton](#cotton) | 1 | 5 | 4 | 24 | 8 | 2 | 0 | 2 | 0 | 4 |
| [Fig](#fig) | 1 | 5 | 5 | 0 | 11 | 1 | 5 | 3 | 1 | 3 |
| [Garlic](#garlic) | 1 | 5 | 4 | 10 | 11 | 1 | 0 | 3 | 1 | 4 |
| [Gem Squash](#gem-squash) | 1 | 0 | 0 | 3 | 11 | 0 | 0 | 0 | 0 | 0 |
| [Groundnut](#groundnut) | 1 | 5 | 4 | 6 | 1 | 4 | 0 | 0 | 1 | 3 |
| [Guava](#guava) | 1 | 6 | 5 | 0 | 11 | 1 | 4 | 3 | 0 | 3 |
| [Honeybush](#honeybush) | 1 | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| [Kiwi](#kiwi) | 1 | 8 | 7 | 0 | 12 | 1 | 6 | 5 | 1 | 3 |
| [Lentils](#lentils) | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 3 |
| [Lettuce](#lettuce) | 1 | 0 | 3 | 7 | 7 | 0 | 0 | 1 | 1 | 3 |
| [Litchi](#litchi) | 1 | 10 | 5 | 0 | 11 | 0 | 4 | 0 | 1 | 3 |
| [Lucerne](#lucerne) | 1 | 7 | 5 | 106 | 9 | 2 | 4 | 2 | 1 | 3 |
| [Macadamia](#macadamia) | 1 | 16 | 4 | 5 | 13 | 4 | 5 | 11 | 0 | 3 |
| [Maize](#maize) | 1 | 6 | 4 | 75 | 11 | 1 | 0 | 2 | 0 | 0 |
| [Maize (dryland)](#maize-dryland) | 1 | 5 | 4 | 48 | 1 | 0 | 0 | 0 | 0 | 4 |
| [Maize (irrigated)](#maize-irrigated) | 1 | 5 | 5 | 44 | 1 | 0 | 0 | 0 | 0 | 5 |
| [Mango](#mango) | 1 | 6 | 5 | 0 | 11 | 1 | 4 | 1 | 1 | 3 |
| [Nectarine](#nectarine) | 1 | 7 | 5 | 0 | 11 | 1 | 0 | 1 | 0 | 0 |
| [Oat](#oat) | 1 | 0 | 4 | 0 | 1 | 3 | 0 | 0 | 0 | 0 |
| [Olive](#olive) | 1 | 5 | 5 | 3 | 11 | 1 | 4 | 2 | 0 | 3 |
| [Onion](#onion) | 1 | 0 | 4 | 7 | 10 | 0 | 0 | 1 | 1 | 5 |
| [Passion Fruit](#passion-fruit) | 1 | 6 | 5 | 0 | 11 | 1 | 4 | 3 | 0 | 3 |
| [Pea](#pea) | 1 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| [Pea (Green)](#pea-green) | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| [Peach](#peach) | 1 | 7 | 5 | 0 | 11 | 1 | 4 | 1 | 0 | 3 |
| [Pear](#pear) | 1 | 8 | 5 | 0 | 11 | 1 | 5 | 1 | 1 | 3 |
| [Pecan](#pecan) | 1 | 9 | 5 | 0 | 11 | 2 | 5 | 0 | 0 | 3 |
| [Pepper (Bell)](#pepper-bell) | 1 | 7 | 4 | 7 | 11 | 0 | 0 | 0 | 1 | 3 |
| [Persimmon](#persimmon) | 1 | 4 | 5 | 0 | 11 | 0 | 4 | 2 | 1 | 0 |
| [Pineapple](#pineapple) | 1 | 4 | 4 | 2 | 11 | 1 | 0 | 2 | 0 | 3 |
| [Plum](#plum) | 1 | 6 | 5 | 0 | 11 | 1 | 4 | 1 | 0 | 3 |
| [Pomegranate](#pomegranate) | 1 | 7 | 5 | 1 | 11 | 1 | 5 | 4 | 1 | 3 |
| [Potato](#potato) | 1 | 3 | 4 | 126 | 11 | 1 | 0 | 0 | 0 | 5 |
| [Pumpkin](#pumpkin) | 1 | 0 | 4 | 7 | 11 | 0 | 0 | 1 | 0 | 4 |
| [Raspberry](#raspberry) | 1 | 2 | 0 | 4 | 11 | 0 | 0 | 2 | 1 | 0 |
| [Rooibos](#rooibos) | 1 | 2 | 4 | 3 | 0 | 0 | 0 | 1 | 1 | 2 |
| [Sorghum](#sorghum) | 1 | 0 | 4 | 0 | 4 | 1 | 0 | 2 | 0 | 4 |
| [Soybean](#soybean) | 1 | 6 | 4 | 48 | 8 | 0 | 0 | 2 | 1 | 3 |
| [Spinach](#spinach) | 1 | 0 | 3 | 0 | 6 | 0 | 0 | 1 | 0 | 3 |
| [Strawberry](#strawberry) | 1 | 2 | 4 | 7 | 6 | 1 | 0 | 3 | 0 | 3 |
| [Sugarcane](#sugarcane) | 1 | 4 | 4 | 56 | 13 | 0 | 0 | 2 | 0 | 5 |
| [Sunflower](#sunflower) | 1 | 5 | 4 | 65 | 7 | 4 | 0 | 1 | 0 | 4 |
| [Sweet Melon](#sweet-melon) | 1 | 0 | 0 | 0 | 11 | 0 | 0 | 0 | 0 | 0 |
| [Sweet Potato](#sweet-potato) | 1 | 5 | 4 | 7 | 11 | 0 | 0 | 0 | 0 | 3 |
| [Sweetcorn](#sweetcorn) | 1 | 0 | 4 | 71 | 0 | 3 | 0 | 0 | 0 | 5 |
| [Table Grape](#table-grape) | 1 | 7 | 5 | 0 | 7 | 1 | 4 | 1 | 0 | 3 |
| [Tea](#tea) | 1 | 2 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| [Tobacco](#tobacco) | 1 | 2 | 4 | 34 | 12 | 0 | 0 | 1 | 1 | 3 |
| [Tobacco (Burley)](#tobacco-burley) | 1 | 0 | 0 | 0 | 12 | 1 | 0 | 0 | 1 | 0 |
| [Tobacco (Dark air-cured)](#tobacco-dark-air-cured) | 1 | 0 | 0 | 4 | 12 | 1 | 0 | 0 | 1 | 0 |
| [Tobacco (Flue-cured)](#tobacco-flue-cured) | 1 | 0 | 0 | 3 | 12 | 1 | 0 | 0 | 1 | 0 |
| [Tobacco (Light air-cured)](#tobacco-light-air-cured) | 1 | 0 | 0 | 0 | 12 | 1 | 0 | 0 | 1 | 0 |
| [Tomato](#tomato) | 1 | 7 | 4 | 0 | 11 | 3 | 0 | 4 | 1 | 3 |
| [Watermelon](#watermelon) | 1 | 0 | 4 | 0 | 11 | 0 | 0 | 1 | 0 | 3 |
| [Wheat](#wheat) | 1 | 9 | 4 | 47 | 10 | 3 | 0 | 2 | 0 | 4 |
| [Wine Grape](#wine-grape) | 1 | 7 | 5 | 0 | 8 | 1 | 4 | 2 | 1 | 3 |


---

## Per-crop detail

### Apple

<a id="apple"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 50 |
| Yield unit | t fruit/ha |
| Population / ha | 1250 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 2.5 |
| P | 0.3 |
| K | 3.5 |
| Ca | 0.8 |
| Mg | 0.3 |
| S | 0.2 |
| B | 0.04 |
| Zn | 0.02 |
| Fe | 0.08 |
| Mn | 0.02 |
| Cu | 0.008 |
| Mo | 0.004 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | — | 5.5 | 6.3 | 7 | DERIVED from H2O − 0.5 (FERTASA 2016 offset). T2 (derived). |
| pH (H2O) | — | 6 | 6.8 | 7.5 | Cheng 2013 NYFQ + Wisconsin Ext Mature Apple Trees. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 40 | 80 | Wisconsin Ext apple + Cheng 2013 (>80 ppm risks Zn antagonism). T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 250 | 400 | Cheng 2013 NYFQ + WSU Tree Fruit (NH4OAc). T2 cross-confirmed. |
| Ca | 300 | 700 | 2500 | 5000 | Higher Ca threshold for fruit quality; Ca prevents bitter pit. |
| Mg | 60 | 120 | 250 | 500 | Cheng 2013 + Cornell Soil Health 2018. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 1.5 | 3 | WSU Tree Fruit + Wisconsin Ext (hot-water). T2. |
| Zn | 1 | 2 | 8 | 25 | WSU Tree Fruit + IPNI Better Crops apple Zn. T2. |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Dormancy | 6–8 | 0 | 0 | 5 | 0 | 5 | 5 | broadcast | Cheng 2013 Cornell. N/K uptake minimal. P broadcast now. |
| 2 | Bud break & bloom | 9–9 | 1 | 25 | 20 | 10 | 15 | 15 | fertigation | Early N drives spur-leaf area. B for fruit set. |
| 3 | Cell division / fruit set | 10–11 | 3 | 35 | 25 | 25 | 35 | 30 | fertigation | Cheng 2013 Fig 1A: peak N demand 4-6 weeks post-full-bloom. |
| 4 | Cell expansion / fruit sizing | 12–1 | 3 | 25 | 25 | 40 | 30 | 30 | fertigation | K-dominant window. N tapered to protect storage quality and Ca partitioning (Lötze). |
| 5 | Post-harvest recovery | 2–5 | 1 | 15 | 25 | 25 | 15 | 20 | broadcast | Cheng 2013: N reserves for next spring spur leaves. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recently mature leaves | July-August | 1.7 | 1.7–2.5 | — | WSU Table 4 |
| P | Recently mature leaves | July-August | 0.15 | 0.15–0.3 | — | WSU Table 4 |
| K | Recently mature leaves | July-August | 1.2 | 1.2–1.9 | — | WSU Table 4 |
| Ca | Recently mature leaves | July-August | 1.5 | 1.5–2 | — | WSU Table 4 |
| Mg | Recently mature leaves | July-August | 0.25 | 0.25–0.35 | — | WSU Table 4 |
| S | Recently mature leaves | July-August | 0.01 | 0.01–0.1 | — | WSU Table 4 |
| B | Recently mature leaves | July-August | 20 | 20–60 | — | WSU Table 4 |
| Zn | Recently mature leaves | July-August | 15 | 15–200 | — | WSU Table 4 |
| Fe | Recently mature leaves | July-August | 60 | 60–120 | — | WSU Table 4 |
| Mn | Recently mature leaves | July-August | 25 | 25–150 | — | WSU Table 4 |
| Cu | Recently mature leaves | July-August | 5 | 5–12 | — | WSU Table 4 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg per t fresh fruit | 0.31 | 0.08 | 1.05 | 0.066 | 0.052 | — | Cheng 2013 NYFQ + Yara Apple |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.14 | 0.14 | 0.15 | 0.13 | Cheng 2013 Cornell + Marini 2003 Virginia Tech HORT-310: 25 g N/tree at year 1 vs 175 g mature = 0.14. Engine prior 0.20 over-applied 43%. T2. |
| Year 2 | 2–2 | 0.3 | 0.3 | 0.35 | 0.28 | Cheng 2013 + Marini 2003: 50 g N/tree = 0.29. T2. |
| Year 3-4 | 3–4 | 0.55 | 0.55 | 0.6 | 0.5 | Cheng 2013 frame development. T2. |
| Year 5-6 | 5–6 | 0.8 | 0.8 | 0.85 | 0.75 | Cheng 2013 first bearing → pre-mature. T2. |
| Year 7+ | 7–99 | 1 | 1 | 1 | 1 | Cheng 2013: full bearing 175 g N/tree. T2. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape | irrigated | 35 | 65 | 110 | t fruit/ha | Hortgro Key Deciduous Fruit Statistics 2024 |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | Cheng 2013 Cornell + Lötze SA | n/a | 2013 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Dormancy and post-harvest; granular under canopy | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Active growth through drip/micro; primary method when irrigated | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu', 'Ca'] | Micronutrient correction and Ca sprays for fruit quality | — |



### Apricot

<a id="apricot"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 20 |
| Yield unit | t fruit/ha |
| Population / ha | 800 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4.5 |
| P | 0.55 |
| K | 5.5 |
| Ca | 1.1 |
| Mg | 0.55 |
| S | 0.32 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | — | 6 | 7 | 7.5 | DERIVED from H2O − 0.5. T2 (derived). |
| pH (H2O) | — | 6.5 | 7.5 | 8 | UC ANR Apricot Production. Most pH-tolerant of stone fruit. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 40 | 80 | UC ANR Apricot + CDFA Stone Fruit. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 250 | 400 | UC ANR Apricot + Tagliavini 2002 Acta Hort 594. T2 cross-confirmed. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 1.5 | 2 | UC ANR Apricot. More B-sensitive than peach. T2. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Dormancy | 5–6 | 0 | 0 | 5 | 5 | 5 | 5 | broadcast | Klein Karoo dominant. Earliest stone fruit. |
| 2 | Bud break & bloom | 7–8 | 1 | 20 | 25 | 15 | 15 | 15 | fertigation | B critical at bloom (Hortgro Stone). |
| 3 | Fruit set & pit hardening | 9–10 | 2 | 35 | 25 | 30 | 30 | 25 | fertigation | Short 90-day cycle → most nutrients needed before Nov. |
| 4 | Ripening & harvest | 11–12 | 2 | 20 | 25 | 35 | 30 | 30 | fertigation | K for sugar/flavour final 3-4 weeks. |
| 5 | Post-harvest recovery | 1–4 | 1 | 25 | 20 | 15 | 20 | 25 | broadcast | Long Jan-Apr recovery window. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recently mature leaves | July-August | 2.4 | 2.4–3.3 | — | WSU Table 4 |
| P | Recently mature leaves | July-August | 0.1 | 0.1–0.3 | — | WSU Table 4 |
| K | Recently mature leaves | July-August | 2 | 2–3.5 | — | WSU Table 4 |
| Ca | Recently mature leaves | July-August | 1.1 | 1.1–4 | — | WSU Table 4 |
| Mg | Recently mature leaves | July-August | 0.25 | 0.25–0.8 | — | WSU Table 4 |
| S | Recently mature leaves | July-August | 0.2 | 0.2–0.4 | — | WSU Table 4 |
| B | Recently mature leaves | July-August | 20 | 20–70 | — | WSU Table 4 |
| Zn | Recently mature leaves | July-August | 16 | 16–50 | — | WSU Table 4 |
| Fe | Recently mature leaves | July-August | 60 | 60–250 | — | WSU Table 4 |
| Mn | Recently mature leaves | July-August | 20 | 20–160 | — | WSU Table 4 |
| Cu | Recently mature leaves | July-August | 4 | 4–16 | — | WSU Table 4 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-2 | 0–1 | 0.25 | 0.25 | 0.3 | 0.2 | Establishment |
| Year 3-4 | 2–3 | 0.55 | 0.55 | 0.6 | 0.5 | Early bearing |
| Year 5 | 4–4 | 0.8 | 0.8 | 0.8 | 0.75 | Pre-mature bearing |
| Year 6+ | 5–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Klein Karoo | irrigated | 10 | 20 | 30 | t fruit/ha | Hortgro Key Deciduous Fruit Statistics 2024 |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Dormancy and post-harvest | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Active growth; primary for irrigated orchards | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu', 'Ca'] | Micronutrient and Ca sprays | — |



### Asparagus

<a id="asparagus"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 5 |
| Yield unit | t shoots/ha |
| Population / ha | 0 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4.2 |
| P | 0.7 |
| K | 3.4 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Pre-ridging (winter dormancy — all P, all K, half N) | 7–8 | 1 | 50 | 100 | 100 | 50 | 50 | broadcast | FERTASA 5.6.3: "all the phosphorus and potassium and half of the nitrogen, just before levelling of the ridges." |
| 2 | Spear emergence & harvest | 8–10 | 0 | 0 | 0 | 0 | 25 | 25 | broadcast | FERTASA 5.6.3: no N during harvest window. Optional 25-30 kg N when second shoots appear. |
| 3 | Fern build / reserve restoration (Dec/Jan N top-up) | 12–1 | 1 | 50 | 0 | 0 | 20 | 20 | broadcast | FERTASA 5.6.3: "additional N broadcast...end of December or beginning of January, to stimulate maximum growth and ensure sufficient reserves in the roots." |
| 4 | Fern maturation & senescence | 2–6 | 0 | 0 | 0 | 0 | 5 | 5 | broadcast | Years 1-2 post-planting: NO harvest. Different feed pattern (establishment-heavy N). |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 66–99 mg/kg | 0–— | 187–187 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 66–99 mg/kg | 0–— | 140–140 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 66–99 mg/kg | 0–— | 93–93 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 100–149 mg/kg | 0–— | 140–140 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 100–149 mg/kg | 0–— | 93–93 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 100–149 mg/kg | 0–— | 47–47 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 150–199 mg/kg | 0–— | 93–93 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 150–199 mg/kg | 0–— | 47–47 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 150–199 mg/kg | 0–— | 24–24 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 200–249 mg/kg | 0–— | 47–47 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 200–249 mg/kg | 0–— | 24–24 | — | FERTASA Handbook 5.6.3.3 |
| K | NH4OAc | 200–249 mg/kg | 0–— | 0–0 | — | FERTASA Handbook 5.6.3.3 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Mature fern | Mid-summer (post-harvest fern) | — | 3–4.5 | 5 | NCDA Plant Tissue Analysis + Hawaii CTAHR PNM4 |
| P | Mature fern | Mid-summer | — | 0.25–0.5 | 0.7 | NCDA Plant Tissue + Hawaii CTAHR PNM4 |
| K | Mature fern | Mid-summer | — | 2–3.5 | 4.5 | NCDA Plant Tissue + Hawaii CTAHR PNM4 |
| Ca | Mature fern | Mid-summer | — | 0.5–1 | — | NCDA Plant Tissue + Hawaii CTAHR PNM4 |
| Mg | Mature fern | Mid-summer | — | 0.2–0.4 | — | NCDA Plant Tissue + Hawaii CTAHR PNM4 |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| shoots | kg/t shoots | 4.2 | 0.7 | 3.4 | — | — | — | 5.6.3 |
| total | kg/t shoots | 50.2 | 9.2 | 51.4 | — | — | — | 5.6.3 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | — | irrigated | 4 | 7 | 10 | t spear/ha | UMN Extension Asparagus + AHDB Asparagus |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.6.3 + UMN Asparagus | 5.6.3 | 2017 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Post-harvest fern growth; heavy K feeder | — |
| fertigation | False | ['N', 'K', 'Ca', 'S'] | When irrigated; during fern growth | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn'] | Micronutrient correction during fern stage | — |



### Avocado

<a id="avocado"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 15 |
| Yield unit | t fruit/ha |
| Population / ha | 400 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 7.1 |
| P | 1.2 |
| K | 10.2 |
| Ca | 3.3 |
| Mg | 2.3 |
| S | 0.6 |
| B | 0.7 |
| Zn | 0.25 |
| Fe | 0.15 |
| Mn | 0.05 |
| Cu | 0.02 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4 | 4.9 | 6 | 7 | DERIVED from Köhne 1990 H2O − 0.5 (FERTASA convention). Wolstenholme & Sheard 2011 SAAGA Part 1. T1 derived. |
| pH (H2O) | 4.5 | 5.4 | 6.5 | 7.5 | Köhne 1990 SAAGA YB 13 Table 2 (T1). FERTASA 5.7.1 target 6.0 sits in the Optimal band. Du Plessis & Koen 1992 trial baseline 6.15. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 20 | 29 | 90 | 129 | Köhne 1990 SAAGA YB 13 Table 2 (T1). FERTASA 5.7.1 prose target ~25 mg/kg sits in the same Optimal band. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 100 | 149 | 250 | 499 | Köhne 1990 SAAGA YB 13 Table 2 (T1). Du Plessis & Koen 1992 WAC2 showed 60 mg/kg sufficient at high-yielding Friedenheim trial — treat as agronomic critical, not target. T1+T3. |
| Ca | 250 | 749 | 1000 | — | Köhne 1990 SAAGA YB 13 Table 2 (T1). High/excess columns NULL per SAAGA convention. |
| Mg | 50 | 99 | 300 | — | Köhne 1990 SAAGA YB 13 Table 2 (T1). High/excess columns NULL per SAAGA convention. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.8 | 1.5 | 2.5 | Higher B requirement; B deficiency causes misshapen fruit. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `Cl (leaf)`, `EC (saturated paste)`, `Organic C (Walkley-Black)`

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Pre-flower / winter (P window) | 5–7 | 1 | 10 | 100 | 15 | 15 | 15 | broadcast | FERTASA 5.7.1: P single application during winter months. Cauliflower stage end. |
| 2 | Anthesis + fruit set | 8–9 | 1 | 15 | 0 | 15 | 25 | 20 | fertigation | FERTASA 5.7.1: "N can be applied earlier than January/February; shortly after fruit set for Hass, or once the spring flush has fully expanded." Fuerte sensitive to early N → fruit drop. |
| 3 | Spring flush / early fruit growth | 10–12 | 1 | 25 | 0 | 30 | 20 | 25 | fertigation | FERTASA 5.7.1: K applied after fruit-set. |
| 4 | Summer flush (PEAK N — FERTASA Jan/Feb) | 1–2 | 2 | 40 | 0 | 30 | 20 | 25 | fertigation | FERTASA 5.7.1 direct: "most [N] will coincide with the summer flush during January/February." |
| 5 | Post-harvest / pre-floral initiation | 3–4 | 1 | 10 | 0 | 10 | 20 | 15 | broadcast | FERTASA 5.7.1: K sulphate preferred over MOP (Cl sensitivity / leaf scorch). B & Zn soil-applied (immobile in plant). |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recent fully-expanded leaf | Feb-Apr | 1.7 | 1.7–1.9 | 3 | 5.7.1 |
| P | Recent fully-expanded leaf | Feb-Apr | — | 0.08–0.15 | 0.3 | 5.7.1 |
| K | Recent fully-expanded leaf | Feb-Apr | — | 0.75–1.15 | 3 | 5.7.1 |
| Ca | Recent fully-expanded leaf | Feb-Apr | — | 1–2 | 4 | 5.7.1 |
| Mg | Recent fully-expanded leaf | Feb-Apr | — | 0.4–0.8 | 1 | 5.7.1 |
| S | Recent fully-expanded leaf | Feb-Apr | — | 0.2–0.6 | 1 | 5.7.1 |
| B | Recent fully-expanded leaf | Feb-Apr | — | 40–80 | 100 | 5.7.1 |
| Zn | Recent fully-expanded leaf | Feb-Apr | — | 25–100 | 100 | 5.7.1 |
| Fe | Recent fully-expanded leaf | Feb-Apr | — | 50–150 | — | 5.7.1 |
| Mn | Recent fully-expanded leaf | Feb-Apr | — | 50–250 | 1000 | 5.7.1 |
| Cu | Recent fully-expanded leaf | Feb-Apr | — | 5–15 | — | 5.7.1 |
| Mo | mature leaf | mid-season | 0.05 | 0.05–1 | 2 | UC ANR Ventura Avocado Leaf Analysis Guide (Lee 1980). T2. |

_Extra leaf rows outside the canonical element set:_ `N (Edranol)`, `N (Hass)`, `N (Pinkerton)`, `N (Ryan)`

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fruit | 7.1 | 1.2 | 10.2 | 3.3 | 2.3 | — | 5.7.1 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.15 | 0.15 | 0.2 | 0.1 | Newly planted; focus on root establishment |
| Year 2-3 | 2–3 | 0.35 | 0.35 | 0.4 | 0.3 | Canopy development |
| Year 4-5 | 4–5 | 0.6 | 0.6 | 0.6 | 0.55 | First fruit; transition to bearing |
| Year 6-7 | 6–7 | 0.8 | 0.8 | 0.8 | 0.8 | Increasing yield |
| Year 8+ | 8–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| Hass | — | irrigated | 8 | 12 | 18 | t/ha | SAAGA Yearbook industry stats; FERTASA 5.7.1 |
| Hass | — | fertigated | 10 | 15 | 22 | t/ha | SAAGA grower-day reports; NZAGA Avocado Growers Manual |
| Hass | — | rainfed | — | 6 | — | t/ha | Kohne 1990 SAAGA YB 13:8-10 |
| Fuerte | — | irrigated | 6 | 10 | 14 | t/ha | SAAGA Yearbook industry stats; Du Plessis & Koen 1992 WAC2 p.289 |
| Fuerte | — | fertigated | 7 | 12 | 16 | t/ha | SAAGA grower benchmarking |
| Fuerte | — | rainfed | — | 5 | — | t/ha | Kohne 1990 SAAGA YB 13:8-10 |
| — | — | irrigated | 7 | 11 | 16 | t/ha | SAAGA Industry Statistics national rolled mean |
| — | — | fertigated | 9 | 14 | 20 | t/ha | SAAGA top-quartile grower reports |
| — | — | rainfed | — | 5 | — | t/ha | Kohne 1990 SAAGA YB 13:8-10 |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | Köhne 1990 SAAGA + Storey & Walker 1999 | 5.7.1 | 1990 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Dormancy/post-harvest; granular under canopy drip-line. Split N across 3-4 applications | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary for irrigated orchards; weekly during active growth (Aug-Mar) | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca', 'K'] | Zn and B critical for set; Ca sprays for fruit quality; K foliar late season | — |



### Banana

<a id="banana"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 50 |
| Yield unit | t fruit/ha |
| Population / ha | 1800 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 5 |
| P | 0.4 |
| K | 18 |
| Ca | 3.5 |
| Mg | 1.2 |
| S | 0.5 |
| B | 0.02 |
| Zn | 0.02 |
| Fe | 0.05 |
| Mn | 0.02 |
| Cu | 0.005 |
| Mo | 0.003 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 5.5 | 6.5 | Haifa Banana Crop Guide + NSW DPI Cavendish. T2. |
| pH (H2O) | 5 | 5.5 | 6 | 7 | Haifa Banana Tab 22 + ARC-ITSC SA Banana Cultivation. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 60 | 100 | Haifa Banana Tab 22 preferred levels. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 300 | 500 | Very high K feeder; K critical for bunch weight and fruit quality. |
| Ca | 400 | 800 | 2000 | 3000 | Haifa Banana Tab 22 (Ca 4-10 meq/100g). T2. |
| Mg | 60 | 120 | 360 | 500 | Haifa Banana Tab 22 (Mg 1-3 meq/100g). T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `EC (saturated paste)`

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Vegetative growth (sucker) | 8–11 | 4 | 30 | 30 | 20 | 25 | 25 | fertigation | High N for leaf production; monthly applications |
| 2 | Flower emergence | 12–1 | 2 | 20 | 25 | 20 | 25 | 25 | fertigation | P for flower initiation; B for bunch quality |
| 3 | Bunch development | 2–4 | 3 | 25 | 25 | 35 | 25 | 25 | fertigation | High K for finger fill and bunch weight |
| 4 | Harvest & ratoon management | 5–7 | 3 | 25 | 20 | 25 | 25 | 25 | fertigation | Support both harvest and ratoon sucker growth |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | Ambic | 0–150 mg/kg | 0–— | 500–500 | — | FERTASA Handbook 5.7.2 Table 2 |
| K | Ambic | 0–100 mg/kg | 0–— | 250–250 | — | FERTASA Handbook 5.7.2 Table 2 |
| K | Ambic | 100–150 mg/kg | 0–— | 125–125 | — | FERTASA Handbook 5.7.2 Table 2 |
| K | Ambic | 150–200 mg/kg | 0–— | 250–250 | — | FERTASA Handbook 5.7.2 Table 2 |
| K | Ambic | 150–— mg/kg | 0–— | 0–0 | — | FERTASA Handbook 5.7.2 Table 2 |
| K | Ambic | 200–250 mg/kg | 0–— | 125–125 | — | FERTASA Handbook 5.7.2 Table 2 |
| K | Ambic | 250–— mg/kg | 0–— | 0–0 | — | FERTASA Handbook 5.7.2 Table 2 |
| N | — | —–— — | 35–45 | 200–200 | — | FERTASA Handbook 5.7.2 Table 4 |
| N | — | —–— — | 46–55 | 270–270 | — | FERTASA Handbook 5.7.2 Table 4 |
| N | — | —–— — | 56–65 | 300–300 | — | FERTASA Handbook 5.7.2 Table 4 |
| N | — | —–— — | 66–75 | 360–360 | — | FERTASA Handbook 5.7.2 Table 4 |
| P | Bray-1 | 0–10 mg/kg | 0–— | 100–100 | — | FERTASA Handbook 5.7.2 Table 1 |
| P | Bray-1 | 10–25 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.7.2 Table 1 |
| P | Bray-1 | 25–60 mg/kg | 0–— | 50–50 | — | FERTASA Handbook 5.7.2 Table 1 |
| P | Bray-1 | 60–— mg/kg | 0–— | 0–0 | — | FERTASA Handbook 5.7.2 Table 1 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 3rd fully expanded leaf | Shooting / flowering | — | 2.6–3.6 | 4 | Yara Australia banana + Haifa Banana |
| P | 3rd fully expanded leaf | Shooting / flowering | — | 0.18–0.27 | 0.3 | Yara Australia banana + Haifa Banana |
| K | 3rd fully expanded leaf | Shooting / flowering | — | 3.5–5.4 | 5.5 | Yara Australia banana + Haifa Banana |
| Ca | 3rd fully expanded leaf | Shooting / flowering | — | 0.25–1.2 | 1.5 | Yara Australia banana + Haifa Banana |
| Mg | 3rd fully expanded leaf | Shooting / flowering | — | 0.27–0.6 | 0.7 | Yara Australia banana + Haifa Banana |
| S | 3rd leaf from top | mid-cycle | 0.16 | 0.16–0.3 | 0.5 | Lahav & Turner 1983/1989 — sufficient 0.16-0.30%. T3. |
| B | 3rd fully expanded leaf | Shooting / flowering | — | 20–40 | 60 | Yara Australia banana + Haifa Banana |
| Zn | 3rd fully expanded leaf | Shooting / flowering | — | 20–30 | 40 | Yara Australia banana + Haifa Banana |
| Fe | 3rd fully expanded leaf | Shooting / flowering | — | 81–150 | 200 | Yara Australia banana + Haifa Banana |
| Mn | 3rd fully expanded leaf | Shooting / flowering | — | 200–300 | 1000 | Yara Australia banana + Haifa Banana |
| Cu | 3rd fully expanded leaf | Shooting / flowering | — | 7–20 | 25 | Yara Australia banana + Haifa Banana |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg per t fresh fruit | 5.5 | 0.52 | 19.9 | 3.6 | 1.4 | 0.6 | Haifa Banana + Yara Australia banana |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Plant crop (Year 1) | 0–1 | 0.8 | 0.8 | 0.8 | 0.75 | First cycle; slightly lower demand than ratoon |
| Ratoon (Year 2+) | 2–99 | 1 | 1 | 1 | 1 | Full production ratoon cycles |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | KZN / Lowveld | irrigated | 25 | 50 | 80 | t fruit/ha | Haifa Banana + Yara Australia banana |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | Haifa Banana + IFA 1992 | n/a | 2017 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Split monthly; heavy K feeder (K:N ratio 2:1 at bunch stage) | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary for irrigated; weekly feeding ideal | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu'] | Micronutrient correction; Zn important | — |



### Barley

<a id="barley"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 4 |
| Yield unit | t grain/ha |
| Population / ha | 3000000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 22 |
| P | 3.5 |
| K | 5 |
| Ca | 2.5 |
| Mg | 2 |
| S | 2 |
| B | 0.02 |
| Zn | 0.04 |
| Fe | 0.25 |
| Mn | 0.04 |
| Cu | 0.008 |
| Mo | 0.004 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & establishment | 4–5 | 1 | 15 | 35 | 15 | 15 | 15 | band_place | Seed-bed P for root establishment |
| 2 | Tillering & vegetative | 6–7 | 2 | 40 | 25 | 25 | 25 | 25 | broadcast | Peak N for tiller production |
| 3 | Heading & flowering | 8–9 | 1 | 25 | 20 | 25 | 30 | 30 | broadcast | B for pollen viability |
| 4 | Grain fill & maturation | 10–11 | 1 | 20 | 20 | 35 | 30 | 30 | broadcast | K for grain plumpness |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | mature leaf | mid-season | 0.1 | 0.1–2 | 5 | SCSB394 small grains. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| grain | kg/t grain | 22 | 3.5 | 5 | 0.5 | 1.2 | 2 | 5.6 |
| straw | kg/t grain | 7 | 1 | 16 | 3.5 | 1.3 | 1.8 | 5.6 |
| total | kg/t grain | 29 | 4.5 | 21 | 4 | 2.5 | 3.8 | 5.6 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | SAB Maltings + ARC-SGI Barley Guideline | n/a | 2017 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At planting; starter band | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant or topdress | — |
| side_dress | False | ['N', 'S'] | Tillering topdress | — |



### Bean (Dry)

<a id="bean-dry"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 2 |
| Yield unit | t grain/ha |
| Population / ha | 0 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 35 |
| P | 6 |
| K | 18 |
| Ca | 5 |
| Mg | 3 |
| S | 2.5 |
| B | 0.04 |
| Zn | 0.06 |
| Fe | 0.35 |
| Mn | 0.06 |
| Cu | 0.015 |
| Mo | 0.008 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 6.2 | 7 | FERTASA 5.5.2 + ARC-GCI Drybean. T1. |
| pH (H2O) | 5 | 5.5 | 6.5 | 7.5 | DAFF Drybean Infopak. T1. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 5 | 13 | 27 | 40 | FERTASA 5.5.2 Tab 2. T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 40 | 60 | 100 | 150 | FERTASA 5.5.2 Tab 3. T1. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.2 | 0.4 | 0.8 | 1.5 | FERTASA 5.5.2: B applications NOT recommended (toxicity). T1. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & establishment | 10–11 | 1 | 60 | 75 | 65 | 25 | 25 | band_place | FERTASA 5.5.2: band-placement enhances uptake. Starter N. |
| 2 | Top-dress (within 3-4 weeks post-plant) | 11–12 | 1 | 40 | 20 | 25 | 25 | 25 | broadcast | FERTASA 5.5.2: "top-dressing...should be done within 3 to 4 weeks after planting." |
| 3 | Flowering (NO N — induces flower drop) | 1–1 | 0 | 0 | 5 | 10 | 25 | 25 | broadcast | CRITICAL FERTASA 5.5.2: "N-application shortly before or during flowering tends to induce flower drop." ZERO N here. |
| 4 | Pod fill & maturity | 2–3 | 0 | 0 | 0 | 0 | 20 | 20 | broadcast | FERTASA 5.5.2: no further N/P/K. B applications NOT recommended (dry beans very susceptible to B toxicity). |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–40 mg/kg | 1–1 | 23–50 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 0–40 mg/kg | 1.5–1.5 | 28–60 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 0–40 mg/kg | 2–2 | 33–70 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 0–40 mg/kg | 2.5–2.5 | 40–80 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 0–40 mg/kg | 3–3 | 50–90 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 40–60 mg/kg | 1–1 | 18–23 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 40–60 mg/kg | 1.5–1.5 | 23–28 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 40–60 mg/kg | 2–2 | 28–33 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 40–60 mg/kg | 2.5–2.5 | 33–40 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 40–60 mg/kg | 3–3 | 40–50 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 60–80 mg/kg | 1–1 | 13–18 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 60–80 mg/kg | 1.5–1.5 | 18–23 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 60–80 mg/kg | 2–2 | 23–28 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 60–80 mg/kg | 2.5–2.5 | 28–33 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 60–80 mg/kg | 3–3 | 33–40 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 80–100 mg/kg | 1–1 | 8–13 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 80–100 mg/kg | 1.5–1.5 | 13–18 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 80–100 mg/kg | 2–2 | 18–23 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 80–100 mg/kg | 2.5–2.5 | 23–28 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 80–100 mg/kg | 3–3 | 28–33 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 100–120 mg/kg | 1–1 | 0–8 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 100–120 mg/kg | 1.5–1.5 | 8–13 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 100–120 mg/kg | 2–2 | 13–18 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 100–120 mg/kg | 2.5–2.5 | 18–23 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 100–120 mg/kg | 3–3 | 23–28 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 120–— mg/kg | 1–1 | 0–0 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 120–— mg/kg | 1.5–1.5 | 0–0 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 120–— mg/kg | 2–2 | 8–8 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 120–— mg/kg | 2.5–2.5 | 12–12 | — | FERTASA Handbook 5.5.2 Table 3 |
| K | NH4OAc | 120–— mg/kg | 3–3 | 15–15 | — | FERTASA Handbook 5.5.2 Table 3 |
| N | — | —–— — | 1–1 | 10–10 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 1.5–1.5 | 20–20 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 2–2 | 30–30 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 2.5–2.5 | 50–50 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 3–3 | 70–70 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 1–1 | 20–20 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 1.5–1.5 | 35–35 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 2–2 | 45–45 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 2.5–2.5 | 65–65 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 3–3 | 85–85 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 1–1 | 30–30 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 1.5–1.5 | 45–45 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 2–2 | 60–60 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 2.5–2.5 | 75–75 | — | FERTASA Handbook 5.5.2 Table 1 |
| N | — | —–— — | 3–3 | 105–105 | — | FERTASA Handbook 5.5.2 Table 1 |
| P | Bray-1 | 0–13 mg/kg | 1.5–1.5 | 16–16 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 0–13 mg/kg | 2–2 | 22–22 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 0–13 mg/kg | 2.5–2.5 | 28–28 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 13–20 mg/kg | 1.5–1.5 | 12–12 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 13–20 mg/kg | 2–2 | 16–16 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 13–20 mg/kg | 2.5–2.5 | 20–20 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 20–27 mg/kg | 1.5–1.5 | 10–10 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 20–27 mg/kg | 2–2 | 13–13 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 20–27 mg/kg | 2.5–2.5 | 16–16 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 27–34 mg/kg | 1.5–1.5 | 9–9 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 27–34 mg/kg | 2–2 | 12–12 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 27–34 mg/kg | 2.5–2.5 | 15–15 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 34–— mg/kg | 1.5–1.5 | 5–5 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 34–— mg/kg | 2–2 | 5–5 | — | FERTASA Handbook 5.5.2 Table 2 |
| P | Bray-1 | 34–— mg/kg | 2.5–2.5 | 5–5 | — | FERTASA Handbook 5.5.2 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| total | kg/t grain | 35 | 6 | 18 | — | — | — | 5.5.2 |
| seed | kg per t seed | 36 | 8 | 18 | — | — | — | NDA / DALRRD Drybean Infopak |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Mpumalanga / KZN | rainfed | 0.8 | 1.5 | 2.5 | t grain/ha | ARC-GCI dry bean cultivar trials |
| — | — | irrigated | 2 | 3 | 3.5 | t grain/ha | ARC-GCI dry bean cultivar trials |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.5.2 + ARC-GCI Drybean Manual | 5.5.2 | 2017 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['P', 'K', 'S'] | At planting; starter P for nodulation | — |
| side_dress | False | ['N', 'K'] | Supplementary if fixation poor | — |
| fertigation | False | ['N', 'K', 'Ca', 'S'] | When irrigated | — |
| foliar | False | ['Mo', 'B', 'Mn', 'Fe'] | Mo for fixation; B for pod set | — |



### Bean (Green)

<a id="bean-green"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 15 |
| Yield unit | t pod/ha |
| Population / ha | 200000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 6 |
| P | 0.8 |
| K | 5 |
| Ca | 1 |
| Mg | 0.5 |
| S | 0.3 |
| B | 0.008 |
| Zn | 0.008 |
| Fe | 0.03 |
| Mn | 0.008 |
| Cu | 0.003 |
| Mo | 0.002 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Emergence & establishment | 9–10 | 1 | 20 | 35 | 15 | 15 | 15 | band_place | Starter P for early root growth |
| 2 | Vegetative growth | 10–11 | 2 | 30 | 25 | 25 | 25 | 25 | side_dress | Strong canopy for pod production |
| 3 | Flowering & pod set | 11–12 | 2 | 25 | 20 | 25 | 30 | 30 | fertigation | B for pollination; Ca for quality |
| 4 | Harvest period | 1–2 | 1 | 25 | 20 | 35 | 30 | 30 | fertigation | K for pod crispness |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 90–90 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 30–30 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 100–160 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 70–70 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 50–50 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 30–30 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.6.1 + UF/IFAS HS725 | 5.6.1 | 2017 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['P', 'K', 'S'] | At planting | — |
| side_dress | False | ['N', 'K'] | Supplementary N | — |
| fertigation | False | ['N', 'K', 'Ca', 'S'] | When irrigated | — |
| foliar | False | ['Mo', 'B', 'Mn', 'Fe', 'Ca'] | Ca for pod quality | — |



### Beetroot

<a id="beetroot"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 40 |
| Yield unit | t root/ha |
| Population / ha | 800000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 0 |
| P | 0 |
| K | 0 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 5.3 | 6 | 6.5 | 7 | DAFF Beetroot + UC ANR Beet. T1+T2. |
| pH (H2O) | 5.8 | 6.5 | 7.2 | 7.8 | DAFF Beetroot + UF/IFAS HS720. T1+T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| Na | — | — | 2000 | 3000 | UC ANR Beet — halophyte; tolerates ECe 4 dS/m. T2. |
| B | 0.4 | 0.7 | 2 | 4 | Starke Ayres Beetroot (heart-rot prevention). T1. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 120–120 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 100–140 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 100–100 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 70–70 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 50–50 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | UC ANR Beet Production | n/a | 2018 | 2 | — |

**Application methods** (`crop_application_methods`)

_No rows._



### Blackberry

<a id="blackberry"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 8 |
| Yield unit | t fruit/ha |
| Population / ha | 3000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 0 |
| P | 0 |
| K | 0 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| pH (H2O) | 5 | 6 | 6.5 | 7 | NCSU AG-697: caneberries prefer pH 6.0-6.5. Lime below 6.0. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | — | —–— — | 0–— | 27.9–55.8 | — | NCSU AG-697 Pre-plant K broadcast |
| N | — | —–— — | 0–— | 22.4–56 | — | NCSU AG-697 Year 1 (establishment) |
| N | — | —–— — | 0–— | 56–89.7 | — | NCSU AG-697 Year 2+ (bearing) |
| P | — | —–— — | 0–— | 14.7–29.3 | — | NCSU AG-697 Pre-plant P broadcast |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Most recently fully expanded leaves | NCSU mid-season | 2.5 | 2.5–3.5 | — | NCSU AG-697 Table 11-2 |
| P | Most recently fully expanded leaves | NCSU mid-season | 0.15 | 0.15–0.25 | — | NCSU AG-697 Table 11-2 |
| K | Most recently fully expanded leaves | NCSU mid-season | 0.9 | 0.9–1.5 | — | NCSU AG-697 Table 11-2 |
| Ca | Most recently fully expanded leaves | NCSU mid-season | 0.48 | 0.48–1 | — | NCSU AG-697 Table 11-2 |
| Mg | Most recently fully expanded leaves | NCSU mid-season | 0.3 | 0.3–0.45 | — | NCSU AG-697 Table 11-2 |
| S | Most recently fully expanded leaves | NCSU mid-season | 0.17 | 0.17–0.21 | — | NCSU AG-697 Table 11-2 |
| B | Most recently fully expanded leaves | NCSU mid-season | 25 | 25–85 | — | NCSU AG-697 Table 11-2 |
| Zn | Most recently fully expanded leaves | NCSU mid-season | 20 | 20–70 | — | NCSU AG-697 Table 11-2 |
| Fe | Most recently fully expanded leaves | NCSU mid-season | 60 | 60–100 | — | NCSU AG-697 Table 11-2 |
| Mn | Most recently fully expanded leaves | NCSU mid-season | 50 | 50–250 | — | NCSU AG-697 Table 11-2 |
| Cu | Most recently fully expanded leaves | NCSU mid-season | 8 | 8–15 | — | NCSU AG-697 Table 11-2 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| True | NCSU AG-697 + SA caneberry practice | — | 2018 | 3 | Blackberry prefers slightly acidic soils; universal cation-ratio targets over-apply Ca/Mg. |

**Application methods** (`crop_application_methods`)

_No rows._



### Blueberry

<a id="blueberry"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 10 |
| Yield unit | t fruit/ha |
| Population / ha | 4500 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 8 |
| P | 0.8 |
| K | 5 |
| Ca | 2 |
| Mg | 1 |
| S | 0.5 |
| B | 0.08 |
| Zn | 0.05 |
| Fe | 0.15 |
| Mn | 0.05 |
| Cu | 0.02 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| pH (H2O) | 4 | 4.5 | 5 | 5.5 | MSU E2011: blueberry requires very acidic soil (optimum 4.5-5.0). Below 4.0 = very low (Al toxicity risk); 4.0-4.5 = low but acceptable; 4.5-5.0 = optimal; 5.0-5.5 = high (Fe/Mn availability starting to decline). Above 5.5 = excess (acidification required). |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | — | 40 | — | — | MSU E2011: 40 ppm is the mineral-soil P threshold below which application is advised. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | — | 50 | — | — | MSU E2011: 50 ppm K is the threshold below which application is advised. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest & leaf fall | 2–4 | 1 | 10 | 5 | 5 | 5 | 5 | broadcast | Replenish after harvest; dormancy prep |
| 2 | Dormancy | 5–7 | 1 | 5 | 5 | 5 | 5 | 5 | broadcast | Minimal demand; pH management |
| 3 | Bud break & bloom | 8–9 | 2 | 25 | 30 | 15 | 15 | 15 | fertigation | P for roots; B for set; keep pH low |
| 4 | Fruit development | 10–11 | 3 | 35 | 35 | 35 | 45 | 45 | fertigation | Peak N; Ca for firmness |
| 5 | Ripening & harvest | 12–1 | 2 | 25 | 25 | 40 | 30 | 30 | fertigation | K for sugar and colour |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | — | —–— — | 0–— | 16.8–33.6 | — | MSU Extension E2011 Table 4 - years 2-4 in field |
| N | — | —–— — | 0–— | 50.4–72.9 | — | MSU Extension E2011 Table 4 - years 6-8+ in field |
| P | — | —–— — | 0–— | 36.7–48.9 | — | MSU Extension E2011 P application when soil-P < 40 ppm |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Current-season shoot middle-section leaves | Mid-July to mid-August | 1.7 | 1.7–2.1 | 2.3 | MSU E2011 Table 3 |
| P | Current-season shoot middle-section leaves | Mid-July to mid-August | 0.08 | 0.08–0.4 | 0.6 | MSU E2011 Table 3 |
| K | Current-season shoot middle-section leaves | Mid-July to mid-August | 0.35 | 0.4–0.65 | 0.9 | MSU E2011 Table 3 |
| Ca | Current-season shoot middle-section leaves | Mid-July to mid-August | 0.13 | 0.3–0.8 | 1 | MSU E2011 Table 3 |
| Mg | Current-season shoot middle-section leaves | Mid-July to mid-August | 0.1 | 0.15–0.3 | — | MSU E2011 Table 3 |
| S | Current-season shoot middle-section leaves | Mid-July to mid-August | — | 0.12–0.2 | — | MSU E2011 Table 3 |
| B | Current-season shoot middle-section leaves | Mid-July to mid-August | 18 | 25–70 | 200 | MSU E2011 Table 3 |
| Zn | Current-season shoot middle-section leaves | Mid-July to mid-August | 8 | 8–30 | 80 | MSU E2011 Table 3 |
| Fe | Current-season shoot middle-section leaves | Mid-July to mid-August | 60 | 60–200 | 400 | MSU E2011 Table 3 |
| Mn | Current-season shoot middle-section leaves | Mid-July to mid-August | 25 | 50–350 | 450 | MSU E2011 Table 3 |
| Cu | Current-season shoot middle-section leaves | Mid-July to mid-August | 5 | 5–20 | — | MSU E2011 Table 3 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg per t fresh fruit | 6.5 | 0.87 | 6.6 | 1.25 | 0.65 | — | OSU Bernadine Strik + UGA Blueberry Fertilization |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–0 | 0.3 | 0.3 | 0.35 | 0.25 | Establishment |
| Year 2 | 1–1 | 0.6 | 0.6 | 0.65 | 0.55 | Early bearing |
| Year 3+ | 2–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape / KZN / Limpopo | tunnel | 2 | 14 | 25 | t fruit/ha | Berries for Africa cv notes; Farmers Weekly SA blueberry guide |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| True | MSU Extension E2011 + SA blueberry industry practice | Table 4 + pH-targeting sections | 2012 | 1 | Blueberry thrives at pH 4.0-5.5 with low Ca saturation (<40%). FERTASA universal 60-70% Ca base-sat target would damage the crop. |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| fertigation | True | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'Mn'] | Primary method; pH-sensitive crop needs precise delivery | — |
| broadcast | False | ['S', 'Ca', 'Mg'] | Amendments only; avoid granular N near shallow roots | — |
| foliar | False | ['Fe', 'Mn', 'Zn', 'B', 'Cu'] | Fe chlorosis common; foliar Fe critical on high-pH soils | — |



### Brinjal

<a id="brinjal"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 40 |
| Yield unit | t fruit/ha |
| Population / ha | 20000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 0 |
| P | 0 |
| K | 0 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.8 | 5.5 | 6 | 6.5 | ICAR-IIVR Brinjal + UF/IFAS HS734. T2. |
| pH (H2O) | 5.3 | 6 | 6.8 | 7.2 | UF/IFAS HS734 + ICAR-IIVR. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 25 | 50 | 100 | UF/IFAS HS734 + Yara Eggplant. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 100 | 180 | 300 | 500 | Yara Eggplant + ICAR-IIVR. T2. |
| Ca | 300 | 700 | 2500 | 5000 | UF/IFAS HS734 — Solanum BER pathway. T2. |
| Mg | 80 | 150 | 300 | 500 | UF/IFAS HS734. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 120–120 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 120–140 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 90–90 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 70–70 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | most-recent mature leaf | first flower | 3 | 3.5–5 | 5.5 | UC ANR Eggplant + UF/IFAS HS734. T2. |
| P | most-recent mature leaf | first flower | 0.2 | 0.3–0.6 | 0.8 | UC ANR Eggplant + UF/IFAS HS734. T2. |
| K | most-recent mature leaf | first flower | 2.5 | 3–4.5 | 5.5 | UC ANR Eggplant + UF/IFAS HS734. T2. |
| Ca | most-recent mature leaf | first flower | 1 | 1.5–3 | 4 | UC ANR Eggplant + UF/IFAS HS734. T2. |
| Mg | most-recent mature leaf | first flower | 0.3 | 0.4–0.8 | 1.2 | UC ANR Eggplant + UF/IFAS HS734. T2. |
| S | most-recent mature leaf | first flower | 0.2 | 0.3–0.6 | 0.8 | UC ANR Eggplant + UF/IFAS HS734. T2. |
| B | most-recent mature leaf | first flower | 25 | 30–80 | 100 | UC ANR Eggplant + UF/IFAS HS734. T2. |
| Zn | most-recent mature leaf | first flower | 18 | 25–60 | 200 | UC ANR Eggplant + UF/IFAS HS734. T2. |
| Fe | most-recent mature leaf | first flower | 50 | 60–300 | — | UC ANR Eggplant + UF/IFAS HS734. T2. |
| Mn | most-recent mature leaf | first flower | 30 | 40–250 | 500 | UC ANR Eggplant + UF/IFAS HS734. T2. |
| Cu | most-recent mature leaf | first flower | 5 | 6–25 | — | UC ANR Eggplant + UF/IFAS HS734. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

_No rows._



### Butternut

<a id="butternut"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 30 |
| Yield unit | t fruit/ha |
| Population / ha | 10000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3.5 |
| P | 0.45 |
| K | 4.5 |
| Ca | 0.4 |
| Mg | 0.3 |
| S | 0.2 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Establishment | 10–10 | 1 | 15 | 30 | 10 | 15 | 15 | band_place | Starter P and Ca |
| 2 | Vine growth | 11–12 | 2 | 35 | 30 | 25 | 25 | 25 | side_dress | Peak N for canopy |
| 3 | Flowering & fruit set | 1–1 | 1 | 25 | 20 | 25 | 30 | 30 | fertigation | B for pollination |
| 4 | Fruit fill & maturation | 2–4 | 1 | 25 | 20 | 40 | 30 | 30 | broadcast | K for storage quality |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| P | Bray-1 | 1–10 mg/kg | 0–65 | 140–160 | — | Hortgro horticulture.org.za butternut soil-type tables Butternut Fertilizer Application by Soil Type |
| P | Bray-1 | 11–20 mg/kg | 0–65 | 120–140 | — | Hortgro horticulture.org.za butternut soil-type tables Butternut Fertilizer Application by Soil Type |
| P | Bray-1 | 21–30 mg/kg | 0–65 | 100–120 | — | Hortgro horticulture.org.za butternut soil-type tables Butternut Fertilizer Application by Soil Type |
| P | Bray-1 | 31–40 mg/kg | 0–65 | 80–100 | — | Hortgro horticulture.org.za butternut soil-type tables Butternut Fertilizer Application by Soil Type |
| P | Bray-1 | 41–60 mg/kg | 0–65 | 60–80 | — | Hortgro horticulture.org.za butternut soil-type tables Butternut Fertilizer Application by Soil Type |
| P | Bray-1 | 61–80 mg/kg | 0–65 | 40–60 | — | Hortgro horticulture.org.za butternut soil-type tables Butternut Fertilizer Application by Soil Type |
| P | Bray-1 | 81–100 mg/kg | 0–65 | 20–40 | — | Hortgro horticulture.org.za butternut soil-type tables Butternut Fertilizer Application by Soil Type |
| P | Bray-1 | 101–120 mg/kg | 0–65 | 0–20 | — | Hortgro horticulture.org.za butternut soil-type tables Butternut Fertilizer Application by Soil Type |
| P | Bray-1 | 121–200 mg/kg | 0–65 | 0–0 | — | Hortgro horticulture.org.za butternut soil-type tables Butternut Fertilizer Application by Soil Type |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | most-recent mature leaf | all stages | 4 | 4–5 | 5.5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| P | most-recent mature leaf | all stages | 0.3 | 0.3–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| K | most-recent mature leaf | all stages | 3 | 3–4 | 5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Ca | most-recent mature leaf | all stages | 1.2 | 1.2–2 | 3 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mg | most-recent mature leaf | all stages | 0.25 | 0.25–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| S | most-recent mature leaf | all stages | 0.2 | 0.2–0.75 | 1 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| B | most-recent mature leaf | all stages | 25 | 25–85 | 120 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Zn | most-recent mature leaf | all stages | 20 | 20–200 | 300 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Fe | most-recent mature leaf | all stages | 50 | 50–300 | — | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mn | most-recent mature leaf | all stages | 25 | 25–250 | 500 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Cu | most-recent mature leaf | all stages | 5 | 5–60 | 100 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | — | irrigated | 15 | 25 | 35 | t fruit/ha | Starke Ayres Butternut 2019 |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At planting | — |
| side_dress | False | ['N', 'K'] | Vine growth topdress | — |
| fertigation | False | ['N', 'K', 'Ca', 'S'] | When irrigated | — |
| foliar | False | ['B', 'Ca', 'Mn'] | B for pollination | — |



### Cabbage

<a id="cabbage"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 60 |
| Yield unit | t head/ha |
| Population / ha | 40000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3.5 |
| P | 0.4 |
| K | 3.5 |
| Ca | 0.5 |
| Mg | 0.2 |
| S | 0.4 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.8 | 1.5 | 2.5 | High B requirement; B deficiency causes hollow stem. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Transplant & establishment | 2–3 | 1 | 15 | 30 | 10 | 15 | 15 | band_place | Starter P for transplant recovery |
| 2 | Vegetative frame | 3–5 | 2 | 40 | 30 | 25 | 25 | 25 | side_dress | High N for leaf number and frame |
| 3 | Head formation | 5–7 | 2 | 30 | 25 | 35 | 35 | 35 | fertigation | K and Ca for density and tipburn prevention |
| 4 | Maturation & harvest | 7–8 | 1 | 15 | 15 | 30 | 25 | 25 | broadcast | Reduce N to prevent splitting |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 160–160 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 120–120 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 160–260 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 100–100 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 70–70 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Whole leaf | Head formation | — | 3–5 | — | UF/IFAS HS964 + Yara Vegetable Brassica Nutritional Summary |
| P | Whole leaf | Head formation | — | 0.3–0.6 | — | UF/IFAS HS964 + Yara Brassica |
| K | Whole leaf | Head formation | — | 3–5 | — | UF/IFAS HS964 + Yara Brassica |
| Ca | Whole leaf | Head formation | — | 1.5–4 | — | UF/IFAS HS964 + Yara Brassica |
| Mg | Whole leaf | Head formation | — | 0.3–0.8 | — | UF/IFAS HS964 + Yara Brassica |
| S | Whole leaf | Head formation | — | 0.3–0.8 | — | UF/IFAS HS964 + Yara Brassica |
| B | Whole leaf | Head formation | — | 30–80 | — | UF/IFAS HS964 + Yara Brassica B Deficiency |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | most-recent mature leaf | mid-growth | 0.1 | 0.2–1 | 5 | SCSB#394 + UF/IFAS HS964 brassica Mo guidance. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| head | kg/t fresh head | 2.2 | 0.5 | 1.5 | 0.5 | 0.2 | 0.3 | Starke Ayres Cabbage 2019 + UF/IFAS Brassica |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| pre-pack (35-45k plants/ha) | — | irrigated | 50 | 100 | 120 | t head/ha | Starke Ayres Cabbage 2019 |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | UF/IFAS HS964 + Starke Ayres 2019 | 5.6.1 | 2019 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At transplant | — |
| side_dress | False | ['N', 'K', 'Ca'] | Head formation topdress | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'B'] | When irrigated | — |
| foliar | False | ['B', 'Mo', 'Ca'] | B for hollow stem prevention; Mo for whiptail | — |



### Canola

<a id="canola"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 2 |
| Yield unit | t seed/ha |
| Population / ha | 0 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 40 |
| P | 7 |
| K | 9 |
| Ca | 4.1 |
| Mg | 4 |
| S | 10 |
| B | 0.1 |
| Zn | 0.06 |
| Fe | 0.4 |
| Mn | 0.06 |
| Cu | 0.015 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 6.5 | 7 | FERTASA 5.5.1 + Hardy & Strauss SAJPS 2014. T1+T3. |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 6 | 14 | 24 | 34 | FERTASA 5.5.1.3 — point of departure 24 mg/kg. T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 50 | 60 | 80 | — | FERTASA 5.5.1.4 split heavy/light texture. T1. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| S | 6 | 12 | — | — | FERTASA 5.5.1.5: <6 deficient. T1. |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.8 | 1.5 | 2.5 | High B requirement; B deficiency causes flower sterility. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| Org C | — | 1 | — | — | FERTASA 5.5.1: <1% suboptimal. T1. |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & emergence | 4–5 | 1 | 17 | 75 | 70 | 25 | 25 | band_place | FERTASA 5.5.1 Table 5.5.1.2: 30 kg N broadcast OR 20 kg N band. S critical — 15-30 kg S/ha (4x wheat). |
| 2 | Early rosette (20 DAE) | 5–6 | 1 | 25 | 10 | 15 | 25 | 25 | broadcast | FERTASA 5.5.1 Table 5.5.1.2: 40-50 kg N at 20 days after emergence. |
| 3 | Late rosette (50 DAE) | 6–7 | 1 | 25 | 5 | 10 | 25 | 25 | broadcast | FERTASA 5.5.1 Table 5.5.1.2: 40-50 kg N at 50 DAE. |
| 4 | Stem elongation (70-80 DAE) | 7–8 | 1 | 25 | 3 | 3 | 15 | 15 | broadcast | FERTASA 5.5.1 Table 5.5.1.2: 40-50 kg N at stem elongation. B foliar spray 1-1.5 kg sodium tetraborate/ha here. |
| 5 | Flowering & pod fill | 9–11 | 0 | 8 | 2 | 2 | 10 | 10 | broadcast | FERTASA 5.5.1: if rotation has no legume, add 20 kg N/ha at flowering. |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | — | —–— — | 1.25–1.25 | 10–10 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 1.25–1.25 | 25–30 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 1.25–1.25 | 30–50 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 1.5–1.5 | 10–20 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 1.5–1.5 | 30–35 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 1.5–1.5 | 50–70 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 2–2 | 20–30 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 2–2 | 30–45 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 2–2 | 60–90 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 2.5–2.5 | 40–50 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 2.5–2.5 | 50–55 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 2.5–2.5 | 80–110 | Southern Cape | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 1.25–1.25 | 50–70 | Swartland | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 1.25–1.25 | 70–90 | Swartland | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 1.75–1.75 | 70–90 | Swartland | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 1.75–1.75 | 90–110 | Swartland | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 2.5–2.5 | 90–110 | Swartland | FERTASA Handbook 5.5.1.X |
| N | — | —–— — | 2.5–2.5 | 110–130 | Swartland | FERTASA Handbook 5.5.1.X |
| S | Ca-phosphate | 0–6 mg/kg | 0–— | 15–20 | — | FERTASA Handbook 5.5.1.5 |
| S | Ca-phosphate | 7–12 mg/kg | 0–— | 15–15 | — | FERTASA Handbook 5.5.1.5 |
| S | Ca-phosphate | 12–— mg/kg | 0–— | 10–10 | — | FERTASA Handbook 5.5.1.5 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Rosette stage leaf | 30-40 days after emergence | — | 3.5–— | — | 5.5.1 |
| P | Rosette stage leaf | 30-40 days after emergence | — | 0.3–0.6 | — | 5.5.1 |
| K | Rosette stage leaf | 30-40 days after emergence | — | 2.2–— | — | 5.5.1 |
| Ca | Rosette stage leaf | 30-40 days after emergence | — | 1.4–3 | — | 5.5.1 |
| Mg | Rosette stage leaf | 30-40 days after emergence | — | 0.2–0.6 | — | 5.5.1 |
| S | Rosette stage leaf | 30-40 days after emergence | — | —–0.5 | — | 5.5.1 |
| B | Rosette stage leaf | 30-40 days after emergence | — | 20–50 | — | 5.5.1 |
| Zn | Rosette stage leaf | 30-40 days after emergence | — | 20–— | — | 5.5.1 |
| Fe | Rosette stage leaf | 30-40 days after emergence | — | 50–300 | — | 5.5.1 |
| Mn | Rosette stage leaf | 30-40 days after emergence | — | 30–200 | — | 5.5.1 |
| Cu | Rosette stage leaf | 30-40 days after emergence | — | 3–5 | — | 5.5.1 |
| Mo | Rosette stage leaf | 30-40 days after emergence | — | 0.25–0.5 | — | 5.5.1 |

_Extra leaf rows outside the canonical element set:_ `Na`

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| total | kg/t grain | 40 | 7 | 9 | 4.1 | 4 | 10 | 5.5.1 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape Rûens | rainfed | 1 | 1.8 | 2.5 | t grain/ha | Hardy & Strauss SAJPS 2014 31(2) |
| — | Central Free State | irrigated | 2 | 3 | 4 | t grain/ha | SAJPS 2024 Nel et al. |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.5.1 + Hardy 2014 | 5.5.1 | 2017 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At planting; S critical for canola | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| side_dress | False | ['N', 'S'] | Rosette topdress | — |
| foliar | False | ['B', 'Mo', 'Mn'] | B for pod set; Mo for N-fixation | — |



### Carrot

<a id="carrot"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 50 |
| Yield unit | t root/ha |
| Population / ha | 600000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3 |
| P | 0.5 |
| K | 5 |
| Ca | 0.4 |
| Mg | 0.2 |
| S | 0.2 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 5.3 | 5.8 | 6.5 | 7 | UC ANR Carrot + Starke Ayres Carrot 2019. T1+T2. |
| pH (H2O) | 5.8 | 6.3 | 7 | 7.5 | DAFF Carrot + UF/IFAS HS726. T1+T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 1 | 2 | UC ANR Carrot — narrow band (cracking >2 ppm). T2. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Germination & establishment | 2–3 | 1 | 15 | 35 | 10 | 15 | 15 | band_place | P for root initiation |
| 2 | Canopy development | 3–5 | 2 | 40 | 30 | 25 | 25 | 25 | side_dress | N for leaf area to drive root growth |
| 3 | Root bulking | 5–7 | 2 | 30 | 25 | 40 | 35 | 35 | fertigation | K for root size; Ca for crack resistance |
| 4 | Maturation | 7–8 | 1 | 15 | 10 | 25 | 25 | 25 | broadcast | Reduce N; K for storage |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 100–100 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 70–120 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Most-recent mature leaf | Top growth | — | 2.5–3.5 | — | UF/IFAS HS964 + NCDA Plant Tissue Analysis Guide |
| P | Most-recent mature leaf | Top growth | — | 0.2–0.4 | — | UF/IFAS HS964 + NCDA Plant Tissue Analysis |
| K | Most-recent mature leaf | Top growth | — | 2–3.5 | — | UF/IFAS HS964 + NCDA Plant Tissue Analysis |
| Ca | Most-recent mature leaf | Top growth | — | 1.5–3 | — | UF/IFAS HS964 + NCDA Plant Tissue Analysis |
| Mg | Most-recent mature leaf | Top growth | — | 0.3–0.5 | — | UF/IFAS HS964 + NCDA Plant Tissue Analysis |
| **S** | — | — | — | — | — | _needs source_ |
| B | Most-recent mature leaf | Top growth | — | 30–80 | — | UF/IFAS HS964 + NCDA Plant Tissue Analysis |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| hybrid commercial | — | irrigated | 30 | 60 | 100 | t root/ha | Starke Ayres Carrot 2019 |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['P', 'K', 'S'] | At planting; avoid excess N near seed | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| side_dress | False | ['N', 'K'] | Root development topdress | — |
| foliar | False | ['B', 'Mn', 'Cu'] | B for root quality | — |



### Cassava

<a id="cassava"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 20 |
| Yield unit | t tuber/ha |
| Population / ha | 10000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 0 |
| P | 0 |
| K | 0 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| pH (H2O) | 4.5 | 5.5 | 7 | 7.5 | DAFF Cassava 2009 / IITA / FAO: cassava tolerates wide pH (4.5-7.5). Optimal 5.5-7.0. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | — | —–— — | 20–30 | 90–135 | — | DAFF Cassava Production Guideline K removal reference |
| N | — | —–— — | 20–30 | 48–72 | — | DAFF Cassava Production Guideline N removal reference |
| P | — | —–— — | 20–30 | 14–21 | — | DAFF Cassava Production Guideline P removal reference |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| storage root | kg/t fresh root | 2 | 0.31 | 1.66 | — | — | — | Imran et al. 2020 Agron Sustain Dev 40:8 + IITA |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

_No rows._



### Cherry

<a id="cherry"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 15 |
| Yield unit | t fruit/ha |
| Population / ha | 500 |
| Years to bearing | 4 |
| Years to full bearing | 7 |
| N (target/uptake) | 4.5 |
| P | 0.9 |
| K | 6 |
| Ca | 0.5 |
| Mg | 0.4 |
| S | 0.4 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | — | 6 | 6.5 | 7 | DERIVED from H2O − 0.5. T2 (derived). |
| pH (H2O) | — | 6.5 | 7 | 7.5 | WSU Sweet Cherry. Cherry tighter pH band than peach. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 40 | 80 | WSU Sweet Cherry. T2 (single source). |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 250 | 400 | WSU Sweet Cherry. T2. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 1.5 | 2 | WSU Sweet Cherry. B critical for fruit set; narrow toxicity. T2. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Dormancy | 5–7 | 0 | 0 | 10 | 5 | 5 | 5 | broadcast | WSU: cherry lightest feeder in stone group. P winter-applied. |
| 2 | Bud break & bloom | 8–9 | 1 | 25 | 25 | 20 | 20 | 20 | fertigation | WSU: most uptake between bloom and rapid vegetative growth. |
| 3 | Fruit set & cell division | 10–10 | 2 | 30 | 25 | 30 | 30 | 25 | fertigation | Fast cell division (~60-80 days). Peak uptake. |
| 4 | Ripening & harvest | 11–12 | 2 | 15 | 20 | 30 | 25 | 25 | fertigation | WSU: stop N ≥1 month before harvest. |
| 5 | Post-harvest recovery | 1–4 | 1 | 30 | 20 | 15 | 20 | 25 | broadcast | Long 4-month post-harvest → heavy reserve build. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recently mature leaves | July-August | 2 | 2–3.03 | — | WSU Table 4 |
| P | Recently mature leaves | July-August | 0.1 | 0.1–0.27 | — | WSU Table 4 |
| K | Recently mature leaves | July-August | 1.2 | 1.2–3.3 | — | WSU Table 4 |
| Ca | Recently mature leaves | July-August | 1.2 | 1.2–2.37 | — | WSU Table 4 |
| Mg | Recently mature leaves | July-August | 0.3 | 0.3–0.77 | — | WSU Table 4 |
| S | Recently mature leaves | July-August | 0.2 | 0.2–0.4 | — | WSU Table 4 |
| B | Recently mature leaves | July-August | 17 | 17–60 | — | WSU Table 4 |
| Zn | Recently mature leaves | July-August | 12 | 12–50 | — | WSU Table 4 |
| Fe | Recently mature leaves | July-August | 57 | 57–250 | — | WSU Table 4 |
| Mn | Recently mature leaves | July-August | 17 | 17–160 | — | WSU Table 4 |
| Cu | Recently mature leaves | July-August | 0 | 0–16 | — | WSU Table 4 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fresh fruit | 1.5 | 0.3 | 2 | 0.16 | 0.13 | 0.13 | WSU Sweet Cherry Tbl 1 + WSU Nutrient Management Sweet Cherries |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-2 | 0–1 | 0.2 | 0.2 | 0.25 | 0.18 | WSU Sweet Cherry orchard establishment. Year 1-2 establishment. |
| Year 3-4 | 2–3 | 0.45 | 0.45 | 0.5 | 0.4 | WSU: early bearing on Gisela rootstock. |
| Year 5 | 4–4 | 0.75 | 0.75 | 0.8 | 0.7 | WSU: pre-mature bearing. |
| Year 6+ | 5–99 | 1 | 1 | 1 | 1 | WSU: full bearing 5-6 yr Gisela / 7 yr Mazzard. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Ceres / Free State / Mpumalanga | irrigated | 6 | 12 | 20 | t fruit/ha | Hortgro Key Deciduous Fruit Statistics 2024 |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

_No rows._



### Chillies

<a id="chillies"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 15 |
| Yield unit | t fruit/ha |
| Population / ha | 20000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 0 |
| P | 0 |
| K | 0 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.8 | 5.5 | 6 | 6.5 | KZN-DARD Capsicum + UC ANR Pepper. T1+T2. |
| pH (H2O) | 5.3 | 6 | 6.8 | 7.2 | KZN-DARD Capsicum + UF/IFAS HS732. T1+T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 12 | 25 | 50 | 100 | UC ANR Pepper. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 100 | 180 | 300 | 500 | Haifa Pepper + KZN-DARD. T1+T2. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.5 | 0.8 | 1.5 | 3 | KZN-DARD: chilli flower-set fails below 30 ppm leaf B. T1. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 100–120 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 50–50 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 30–30 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | most-recent mature leaf | first flower | 3 | 3.5–5 | 5.5 | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| P | most-recent mature leaf | first flower | 0.2 | 0.3–0.6 | 0.8 | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| K | most-recent mature leaf | first flower | 2.5 | 3–4.5 | 5.5 | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| Ca | most-recent mature leaf | first flower | 1 | 1.5–3 | 4 | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| Mg | most-recent mature leaf | first flower | 0.3 | 0.4–0.8 | 1.2 | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| S | most-recent mature leaf | first flower | 0.2 | 0.3–0.6 | 0.8 | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| B | most-recent mature leaf | first flower | 25 | 40–80 | 100 | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| Zn | most-recent mature leaf | first flower | 18 | 25–60 | 200 | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| Fe | most-recent mature leaf | first flower | 50 | 60–300 | — | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| Mn | most-recent mature leaf | first flower | 30 | 40–250 | 500 | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| Cu | most-recent mature leaf | first flower | 5 | 6–25 | — | UC Davis Geisseler Pepper + KZN-DARD Capsicum (chilli upper B band raised). T1+T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | — | irrigated | 5 | 20 | 80 | t fresh fruit/ha | KZN-DARD Capsicums Production Guide; Haifa Pepper Guide as upper-bound |
| paprika dried | — | irrigated | 1 | 3 | 4 | t dry/ha | Haifa Pepper + ICL Pepper |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

_No rows._



### Citrus

<a id="citrus"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 40 |
| Yield unit | t fruit/ha |
| Population / ha | 500 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 0 |
| P | 0 |
| K | 0 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 6.5 | 7 | Derived from Citrus Academy NQ2 §3.1 pH(H2O) 5.3-7.5 minus standard 0.5 KCl/H2O offset (FERTASA 2016 / GrainSA). Flagged DERIVED — no direct citrus pH(KCl) source published openly; Raath 2021 R250 handbook is the gap. T1 (derived). |
| pH (H2O) | 5.3 | 6.4 | 7.5 | 8 | Citrus Academy NQ2 §3.1 p.28 (T1). Below 5.3 Al-toxic; above 7.5 P/Zn/Mn lock-up. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 20 | 24 | 50 | 100 | Citrus Academy NQ2 §3.4 p.29 (T1) ideal 25-50; UC Davis Geisseler (T2) cross-check 20-40 medium / 40-100 high. Bray-1 method. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| P (Olsen) | 5 | 10 | 40 | 60 | CDFA-FREP Geisseler Citrus Fertilization Guidelines. T2. |
| K | 75 | 150 | 250 | 800 | UC Davis Geisseler Citrus Fertilization Guidelines (T2). Citrus Academy NQ2 publishes K only as %BS — schema gap noted in migration header. |
| Ca | 200 | 400 | 1500 | 3000 | UF/IFAS SS584 + FERTASA 2016 (cited via SciELO Limpopo baseline study). T2 + T1 cross-check. |
| Mg | 80 | 150 | 400 | 700 | Higher Mg requirement; Mg deficiency common in SA citrus orchards. |
| S | 5 | 10 | 30 | 60 | Derived from UF/IFAS SS584 leaf S 0.20-0.40% optimum mapping to soil S norms. No direct citrus-specific SA cite. T2 (derived). |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 2 | 5 | UF/IFAS + Haifa Crop Guide Citrus. T2. |
| Zn | 1 | 2 | 10 | 25 | UF/IFAS general citrus micronutrient guidance + Florida Citrus Production Guide. T2. |
| Fe | 2 | 5 | 50 | 100 | UF/IFAS general citrus micronutrient guidance. T2. |
| Mn | 2 | 5 | 50 | 150 | UF/IFAS general citrus micronutrient guidance. T2. |
| Cu | 1 | 3 | 25 | 50 | UF/IFAS SS492 — copper toxicity threshold 25 mg/kg (lime to pH 6.5 above this). T2. |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `Cl (leaf)`, `EC (saturated paste)`, `Na (leaf)`

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 4-7 mo old leaf from non-bearing twigs, spring flush | Mar-May | 2.09 | 2.1–2.3 | 2.51 | 5.3.2 |
| **P** | — | — | — | — | — | _needs source_ |
| K | 4-7 mo old leaf from non-bearing twigs | Mar-May | 0.89 | 0.9–1.5 | 1.81 | 5.3.2 |
| Ca | 4-7 mo leaf | Mar-May | 3.49 | 3.5–6 | 7.01 | 5.3.2 |
| Mg | 4-7 mo leaf | Mar-May | 0.34 | 0.35–0.5 | 0.76 | 5.3.2 |
| S | 4-7 mo leaf | Mar-May | 0.19 | 0.2–0.3 | 0.51 | 5.3.2 |
| B | 4-7 mo leaf | Mar-May | 74 | 75–200 | 301 | 5.3.2 |
| Zn | 4-7 mo leaf | Mar-May | 24 | 25–100 | 201 | 5.3.2 |
| Fe | 4-7 mo leaf | Mar-May | 49 | 50–300 | — | 5.3.2 |
| Mn | 4-7 mo leaf | Mar-May | 39 | 40–150 | 301 | 5.3.2 |
| Cu | 4-7 mo leaf | Mar-May | — | 5–20 | 41 | 5.3.2 |
| Mo | 4-7 mo leaf | Mar-May | 0.04 | 0.05–3 | — | 5.3.2 |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.15 | 0.15 | 0.2 | 0.1 | Newly planted; focus on root establishment [Cloned from Valencia — no SA-specific T1 genus age-factor source.] |
| Year 2 | 2–2 | 0.3 | 0.3 | 0.35 | 0.25 | Canopy development [Cloned from Valencia — no SA-specific T1 genus age-factor source.] |
| Year 3-4 | 3–4 | 0.5 | 0.5 | 0.55 | 0.45 | First fruit; transition to bearing [Cloned from Valencia — no SA-specific T1 genus age-factor source.] |
| Year 5-6 | 5–6 | 0.75 | 0.75 | 0.75 | 0.7 | Increasing yield [Cloned from Valencia — no SA-specific T1 genus age-factor source.] |
| Year 7+ | 7–99 | 1 | 1 | 1 | 1 | Full bearing [Cloned from Valencia — no SA-specific T1 genus age-factor source.] |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| Valencia | — | irrigated | 35 | 55 | 75 | t/ha | CRI Industry Statistics 2023; FERTASA 5.7.3 |
| Valencia | — | fertigated | 45 | 65 | 90 | t/ha | CRI Citrus Academy NQ2 high-density drip blocks |
| Navel | — | irrigated | 30 | 45 | 60 | t/ha | CRI Industry Statistics 2023; Citrus Academy Toolkit 3.5 |
| Navel | — | fertigated | 35 | 55 | 75 | t/ha | CRI Citrus Academy NQ2 high-input WC / Sundays River |
| Eureka Lemon | — | irrigated | 40 | 60 | 90 | t/ha | CRI Industry Statistics 2023; Letaba/Limpopo benchmarking |
| Eureka Lemon | — | fertigated | 50 | 75 | 110 | t/ha | CRI Citrus Academy NQ2 intensive drip |
| Star Ruby | — | irrigated | 35 | 55 | 75 | t/ha | CRI Industry Statistics 2023 (Hoedspruit / Limpopo lowveld) |
| Star Ruby | — | fertigated | 45 | 65 | 90 | t/ha | CRI grower benchmarking |
| — | — | irrigated | 30 | 50 | 70 | t/ha | CRI Industry Statistics 2023 national rolled mean |
| — | — | fertigated | 40 | 60 | 85 | t/ha | CRI Industry Statistics 2023 top-quartile growers |
| Bennie Valencia | Letsitele/Limpopo | irrigated | 60 | 70 | 80 | t fruit/ha | SA Fruit Journal Dec 2023/Jan 2024 — Valencia orange selections Letsitele |
| Bennie Valencia | Letsitele/Limpopo | fertigated | 70 | 80 | 90 | t fruit/ha | SA Fruit Journal Dec 2023/Jan 2024. |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | ARC-ISCW lowveld sandy soil baseline + FAO Y5998E | n/a | 2016 | 1 | — |

**Application methods** (`crop_application_methods`)

_No rows._



### Citrus (Grapefruit)

<a id="citrus-grapefruit"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | Citrus |
| Default yield | 45 |
| Yield unit | t fruit/ha |
| Population / ha | 555 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3.5 |
| P | 0.45 |
| K | 3.8 |
| Ca | 1.3 |
| Mg | 0.4 |
| S | 0.25 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Winter pre-flush | 7–8 | 1 | 20 | 50 | 15 | 15 | 15 | fertigation | FERTASA 5.7.3. UF IFAS: grapefruit 10-15% less N than oranges. |
| 2 | Flowering / spring flush | 9–10 | 2 | 25 | 50 | 50 | 20 | 20 | fertigation | Star Ruby dominant (~80% SA grapefruit). K window Aug-Oct. |
| 3 | Fruit set / cell division | 11–12 | 2 | 25 | 0 | 20 | 25 | 25 | fertigation | Peak N uptake. |
| 4 | Summer fruit growth | 1–2 | 1 | 25 | 0 | 15 | 25 | 25 | fertigation | Grapefruit larger fruit justifies high K here. |
| 5 | Maturation / harvest (Apr-Sep) | 4–6 | 0 | 5 | 0 | 0 | 15 | 15 | fertigation | Grapefruit harvest Apr-Sep. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 4-7 mo old leaf from non-bearing twigs | Mar-May | 2.29 | 2.3–2.5 | 2.81 | 5.3.2 |
| P | 4-7 mo old leaf from non-bearing twigs | Mar-May | 0.09 | 0.1–0.14 | 0.18 | 5.3.2 |
| K | 4-7 mo old leaf from non-bearing twigs | Mar-May | 0.79 | 0.8–1 | 1.21 | 5.3.2 |
| Ca | 4-7 mo leaf | Mar-May | 3.49 | 3.5–6 | 7.01 | 5.3.2 |
| Mg | 4-7 mo leaf | Mar-May | 0.34 | 0.35–0.5 | 0.76 | 5.3.2 |
| S | 4-7 mo leaf | Mar-May | 0.19 | 0.2–0.3 | 0.51 | 5.3.2 |
| B | 4-7 mo leaf | Mar-May | 74 | 75–200 | 301 | 5.3.2 |
| Zn | 4-7 mo leaf | Mar-May | 24 | 25–100 | 201 | 5.3.2 |
| Fe | 4-7 mo leaf | Mar-May | 49 | 50–300 | — | 5.3.2 |
| Mn | 4-7 mo leaf | Mar-May | 39 | 40–150 | 301 | 5.3.2 |
| Cu | 4-7 mo leaf | Mar-May | — | 5–20 | 41 | 5.3.2 |
| Mo | 4-7 mo leaf | Mar-May | 0.04 | 0.05–3 | — | 5.3.2 |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fruit | 1.2 | 0.15 | 1.9 | 0.7 | 0.14 | 0.09 | 5.7.3 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.15 | 0.15 | 0.2 | 0.1 | Newly planted; focus on root establishment |
| Year 2 | 2–2 | 0.3 | 0.3 | 0.35 | 0.25 | Canopy development |
| Year 3-4 | 3–4 | 0.5 | 0.5 | 0.55 | 0.45 | First fruit; transition to bearing |
| Year 5-6 | 5–6 | 0.75 | 0.75 | 0.75 | 0.7 | Increasing yield |
| Year 7+ | 7–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Split applications; high K demand | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary for irrigated orchards | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca'] | Zn + B pre-bloom | — |



### Citrus (Lemon)

<a id="citrus-lemon"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | Citrus |
| Default yield | 40 |
| Yield unit | t fruit/ha |
| Population / ha | 555 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3.8 |
| P | 0.5 |
| K | 4.2 |
| Ca | 1.4 |
| Mg | 0.45 |
| S | 0.28 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Winter rest / pruning | 6–7 | 5 | 5 | 10 | 5 | 5 | 5 | broadcast | Lemon flushes year-round; Eureka SA harvests Apr-Aug primarily. Migration 116 corrects 037 Valencia-clone clobber. |
| 2 | Major spring flush + bloom | 8–10 | 1 | 30 | 30 | 25 | 30 | 25 | fertigation | Eureka spring flush Aug-Oct. T1 (SA grower observation, CRI Citrus Academy NQ2). |
| 3 | Summer flush + fruit fill | 11–1 | 2 | 35 | 30 | 35 | 35 | 35 | fertigation | Continued flushing through summer; multiple fruit cohorts. T1. |
| 4 | Autumn fruit colour + harvest | 2–5 | 2 | 30 | 30 | 35 | 30 | 35 | fertigation | Apr-Aug primary harvest; K for skin colour. T1. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 4-7 mo old leaf from non-bearing twigs | Mar-May | 2.29 | 2.3–2.6 | 2.81 | 5.3.2 |
| P | 4-7 mo old leaf from non-bearing twigs | Mar-May | 0.1 | 0.11–0.14 | 0.18 | 5.3.2 |
| K | 4-7 mo old leaf from non-bearing twigs | Mar-May | 0.79 | 0.8–1.2 | 1.71 | 5.3.2 |
| Ca | 4-7 mo leaf | Mar-May | 3.49 | 3.5–6 | 7.01 | 5.3.2 |
| Mg | 4-7 mo leaf | Mar-May | 0.34 | 0.35–0.5 | 0.76 | 5.3.2 |
| S | 4-7 mo leaf | Mar-May | 0.19 | 0.2–0.3 | 0.51 | 5.3.2 |
| B | 4-7 mo leaf | Mar-May | 74 | 75–200 | 301 | 5.3.2 |
| Zn | 4-7 mo leaf | Mar-May | 24 | 25–100 | 201 | 5.3.2 |
| Fe | 4-7 mo leaf | Mar-May | 49 | 50–300 | — | 5.3.2 |
| Mn | 4-7 mo leaf | Mar-May | 39 | 40–150 | 301 | 5.3.2 |
| Cu | 4-7 mo leaf | Mar-May | — | 5–20 | 41 | 5.3.2 |
| Mo | 4-7 mo leaf | Mar-May | 0.04 | 0.05–3 | — | 5.3.2 |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fruit | 1.3 | 0.16 | 2.3 | 0.9 | 0.15 | 0.1 | 5.7.3 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.15 | 0.15 | 0.2 | 0.1 | Newly planted; focus on root establishment |
| Year 2 | 2–2 | 0.3 | 0.3 | 0.35 | 0.25 | Canopy development |
| Year 3-4 | 3–4 | 0.5 | 0.5 | 0.55 | 0.45 | First fruit; transition to bearing |
| Year 5-6 | 5–6 | 0.75 | 0.75 | 0.75 | 0.7 | Increasing yield |
| Year 7+ | 7–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Year-round bearer; split applications | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Continuous feeding for year-round production | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca'] | Micronutrient correction | — |



### Citrus (Navel)

<a id="citrus-navel"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | Citrus |
| Default yield | 35 |
| Yield unit | t fruit/ha |
| Population / ha | 555 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4.2 |
| P | 0.6 |
| K | 4.8 |
| Ca | 1.6 |
| Mg | 0.55 |
| S | 0.32 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Pre-flush dormancy | 6–7 | 0 | 5 | 10 | 0 | 5 | 5 | broadcast | Navel pre-flush. Migration 116 corrects 037 Valencia-clone clobber. Navel harvests Apr-Jul (3 months earlier than Valencia). |
| 2 | Bloom + spring flush | 8–9 | 1 | 25 | 25 | 15 | 25 | 25 | fertigation | Bloom Aug-Sep. T1 CRI Citrus Academy NQ2 §3.5. |
| 3 | Cell division + early fruit fill | 10–12 | 2 | 35 | 30 | 35 | 30 | 30 | fertigation | Cell division Oct-Dec. T1. |
| 4 | Maturation + early harvest | 1–4 | 2 | 25 | 25 | 35 | 30 | 30 | fertigation | Apr-Jul harvest; K for sugar/colour. T1. |
| 5 | Post-harvest reserve | 5–5 | 1 | 10 | 10 | 15 | 10 | 10 | broadcast | Reserve build before next dormancy. T1. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 4-7 mo old leaf from non-bearing twigs, spring flush | Mar-May | 2.39 | 2.4–2.6 | 2.81 | 5.3.2 |
| P | 4-7 mo old leaf from non-bearing twigs | Mar-May | 0.1 | 0.11–0.14 | 0.18 | 5.3.2 |
| K | 4-7 mo old leaf from non-bearing twigs | Mar-May | 0.69 | 0.7–1.1 | 1.41 | 5.3.2 |
| Ca | 4-7 mo leaf | Mar-May | 3.49 | 3.5–6 | 7.01 | 5.3.2 |
| Mg | 4-7 mo leaf | Mar-May | 0.34 | 0.35–0.5 | 0.76 | 5.3.2 |
| S | 4-7 mo leaf | Mar-May | 0.19 | 0.2–0.3 | 0.51 | 5.3.2 |
| B | 4-7 mo leaf | Mar-May | 74 | 75–200 | 301 | 5.3.2 |
| Zn | 4-7 mo leaf | Mar-May | 24 | 25–100 | 201 | 5.3.2 |
| Fe | 4-7 mo leaf | Mar-May | 49 | 50–300 | — | 5.3.2 |
| Mn | 4-7 mo leaf | Mar-May | 39 | 40–150 | 301 | 5.3.2 |
| Cu | 4-7 mo leaf | Mar-May | — | 5–20 | 41 | 5.3.2 |
| Mo | 4-7 mo leaf | Mar-May | 0.04 | 0.05–3 | — | 5.3.2 |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fruit | 1.5 | 0.2 | 2.1 | 0.9 | 0.16 | 0.11 | 5.7.3 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.15 | 0.15 | 0.2 | 0.1 | Newly planted; focus on root establishment |
| Year 2 | 2–2 | 0.3 | 0.3 | 0.35 | 0.25 | Canopy development |
| Year 3-4 | 3–4 | 0.5 | 0.5 | 0.55 | 0.45 | First fruit; transition to bearing |
| Year 5-6 | 5–6 | 0.75 | 0.75 | 0.75 | 0.7 | Increasing yield |
| Year 7+ | 7–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Split 3-4 applications Aug-Mar; moderate N to manage fruit size | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary for irrigated orchards | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca', 'K'] | Ca sprays for rind quality; K late season | — |



### Citrus (Soft Citrus)

<a id="citrus-soft-citrus"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | Citrus |
| Default yield | 35 |
| Yield unit | t fruit/ha |
| Population / ha | 700 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4 |
| P | 0.55 |
| K | 4.5 |
| Ca | 1.5 |
| Mg | 0.5 |
| S | 0.3 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Pre-flush dormancy | 6–7 | 0 | 5 | 10 | 0 | 5 | 5 | broadcast | Soft Citrus pre-flush. Migration 116 corrects 037 Valencia-clone clobber. Mar-Jul harvest (earliest citrus). |
| 2 | Bloom | 8–9 | 1 | 25 | 25 | 15 | 25 | 25 | fertigation | Bloom Aug-Sep — same window as Navel. T1 CRI + Lovatt 2013 HortScience Clementine. |
| 3 | Cell division + fruit fill | 10–12 | 2 | 35 | 30 | 40 | 30 | 30 | fertigation | Lovatt 2013: K bumped 40% in cell-division stage for Clementine. T1. |
| 4 | Maturation + harvest | 1–3 | 2 | 25 | 25 | 35 | 30 | 30 | fertigation | Mar-Jul harvest; alternate-bearing risk on Nadorcott. T1. |
| 5 | Post-harvest | 4–5 | 1 | 10 | 10 | 10 | 10 | 10 | broadcast | Reserve build. T1. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | leaf | spring flush | 2.3 | 2.3–2.6 | 3 | FERTASA 5.3.2 Mandarin row + Lovatt 2013 HortScience 48(6) Clementine cross-validation. T1. |
| P | leaf | spring flush | 0.1 | 0.1–0.14 | 0.2 | FERTASA 5.3.2 Mandarin row. T1. |
| K | leaf | spring flush | 0.7 | 0.7–1.1 | 1.5 | FERTASA 5.3.2 Mandarin row + Lovatt 2013 cross-check. T1. |
| Ca | 4-7 mo leaf | Mar-May | 3.49 | 3.5–6 | 7.01 | 5.3.2 |
| Mg | 4-7 mo leaf | Mar-May | 0.34 | 0.35–0.5 | 0.76 | 5.3.2 |
| S | 4-7 mo leaf | Mar-May | 0.19 | 0.2–0.3 | 0.51 | 5.3.2 |
| B | 4-7 mo leaf | Mar-May | 74 | 75–200 | 301 | 5.3.2 |
| Zn | 4-7 mo leaf | Mar-May | 24 | 25–100 | 201 | 5.3.2 |
| Fe | 4-7 mo leaf | Mar-May | 49 | 50–300 | — | 5.3.2 |
| Mn | 4-7 mo leaf | Mar-May | 39 | 40–150 | 301 | 5.3.2 |
| Cu | 4-7 mo leaf | Mar-May | — | 5–20 | 41 | 5.3.2 |
| Mo | 4-7 mo leaf | Mar-May | 0.04 | 0.05–3 | — | 5.3.2 |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fruit | 1.5 | 0.18 | 2 | 0.8 | 0.15 | 0.1 | 5.7.3 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.15 | 0.15 | 0.2 | 0.1 | Newly planted; focus on root establishment |
| Year 2 | 2–2 | 0.3 | 0.3 | 0.35 | 0.25 | Canopy development |
| Year 3-4 | 3–4 | 0.5 | 0.5 | 0.55 | 0.45 | First fruit; transition to bearing |
| Year 5-6 | 5–6 | 0.75 | 0.75 | 0.75 | 0.7 | Increasing yield |
| Year 7+ | 7–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Split applications; careful N management for fruit size | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary for irrigated | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca', 'K'] | Ca for rind; K for internal quality | — |



### Citrus (Valencia)

<a id="citrus-valencia"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | Citrus |
| Default yield | 40 |
| Yield unit | t fruit/ha |
| Population / ha | 555 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4 |
| P | 0.55 |
| K | 4.5 |
| Ca | 1.5 |
| Mg | 0.5 |
| S | 0.3 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Winter pre-flush | 7–8 | 1 | 20 | 50 | 15 | 15 | 15 | fertigation | FERTASA 5.7.3 Table 5.7.3.4: N Jul-Nov; P anytime; K Aug-Oct. Never apply N+K simultaneously (salinity spike). |
| 2 | Flowering / spring flush | 9–10 | 2 | 25 | 50 | 50 | 20 | 20 | fertigation | FERTASA 5.7.3: K window Aug-Sep-Oct. Separate N and K by >=2 irrigations. |
| 3 | Fruit set / cell division | 11–12 | 2 | 25 | 0 | 20 | 25 | 25 | fertigation | Peak uptake. Leaf sample Mar-May. |
| 4 | Summer fruit growth | 1–2 | 1 | 25 | 0 | 15 | 25 | 25 | fertigation | FERTASA 5.7.3: Aug-Feb split window. |
| 5 | Maturation / harvest (Jul-Sep) | 4–6 | 0 | 5 | 0 | 0 | 15 | 15 | fertigation | Valencia late-harvest Jul-Sep. Minimise N — delays internal colour break. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 4-7 mo old leaf from non-bearing twigs, spring flush | Mar-May | 2.09 | 2.1–2.3 | 2.51 | 5.3.2 |
| **P** | — | — | — | — | — | _needs source_ |
| K | 4-7 mo old leaf from non-bearing twigs | Mar-May | 0.89 | 0.9–1.5 | 1.81 | 5.3.2 |
| Ca | 4-7 mo leaf | Mar-May | 3.49 | 3.5–6 | 7.01 | 5.3.2 |
| Mg | 4-7 mo leaf | Mar-May | 0.34 | 0.35–0.5 | 0.76 | 5.3.2 |
| S | 4-7 mo leaf | Mar-May | 0.19 | 0.2–0.3 | 0.51 | 5.3.2 |
| B | 4-7 mo leaf | Mar-May | 74 | 75–200 | 301 | 5.3.2 |
| Zn | 4-7 mo leaf | Mar-May | 24 | 25–100 | 201 | 5.3.2 |
| Fe | 4-7 mo leaf | Mar-May | 49 | 50–300 | — | 5.3.2 |
| Mn | 4-7 mo leaf | Mar-May | 39 | 40–150 | 301 | 5.3.2 |
| Cu | 4-7 mo leaf | Mar-May | — | 5–20 | 41 | 5.3.2 |
| Mo | 4-7 mo leaf | Mar-May | 0.04 | 0.05–3 | — | 5.3.2 |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fruit | 1.4 | 0.18 | 2 | 0.8 | 0.15 | 0.1 | 5.7.3 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.15 | 0.15 | 0.2 | 0.1 | Newly planted; focus on root establishment |
| Year 2 | 2–2 | 0.3 | 0.3 | 0.35 | 0.25 | Canopy development |
| Year 3-4 | 3–4 | 0.5 | 0.5 | 0.55 | 0.45 | First fruit; transition to bearing |
| Year 5-6 | 5–6 | 0.75 | 0.75 | 0.75 | 0.7 | Increasing yield |
| Year 7+ | 7–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Split 3-4 applications Aug-Mar; P and K pre-bloom | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary for irrigated; weekly during active flush | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca', 'K'] | Zn + B + urea pre-bloom spray; Cu for disease resistance | — |



### Coffee

<a id="coffee"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 2 |
| Yield unit | t green/ha |
| Population / ha | 5000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 60 |
| P | 5 |
| K | 50 |
| Ca | 8 |
| Mg | 5 |
| S | 3 |
| B | 0.25 |
| Zn | 0.1 |
| Fe | 0.6 |
| Mn | 0.15 |
| Cu | 0.05 |
| Mo | 0.02 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.2 | 4.8 | 5.8 | 6.5 | Prefers slightly acid soil; optimal pH 5.0-5.8 KCl. |
| pH (H2O) | 4.7 | 5.3 | 6.3 | 7 | Prefers slightly acid soil; optimal pH 5.5-6.3 H2O. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest & recovery | 8–9 | 1 | 10 | 10 | 5 | 5 | 5 | broadcast | Recover after picking |
| 2 | Flowering | 10–11 | 2 | 15 | 20 | 15 | 15 | 15 | fertigation | B critical for flower set |
| 3 | Berry development | 12–2 | 3 | 35 | 35 | 35 | 40 | 40 | fertigation | Peak NPK; Ca for bean structure |
| 4 | Berry fill & ripening | 3–5 | 2 | 25 | 25 | 30 | 25 | 25 | fertigation | K for bean density and cup quality |
| 5 | Harvest | 6–7 | 1 | 15 | 10 | 15 | 15 | 15 | broadcast | Minimal; maintain tree health |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Primary; under canopy | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Zn', 'B'] | When irrigated; primary for modern plantings | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu'] | Zn and B critical for berry development | — |



### Cotton

<a id="cotton"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 4.3 |
| Yield unit | t seed cotton/ha |
| Population / ha | 50000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 90 |
| P | 15 |
| K | 60 |
| Ca | 8 |
| Mg | 5 |
| S | 4 |
| B | 0.1 |
| Zn | 0.08 |
| Fe | 0.5 |
| Mn | 0.08 |
| Cu | 0.02 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 5 | 5.5 | 7 | 7.5 | FERTASA 5.9 + UGA Cotton. T1+T2. |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 15 | 20 | — | FERTASA 5.9.4 directly. T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 50 | 80 | 100 | 120 | FERTASA 5.9 K-prose: 80/100/120 mg/kg cutoffs for sand/loam/clay. CORRECTED from prior 60/120/250/450. T1. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| Zn | 0.5 | 1 | 2 | 5 | NC State + UGA Cotton Mehlich-1 Zn. T2. |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `Acid Saturation`

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & establishment (weeks 0-5) | 10–11 | 1 | 20 | 100 | 100 | 30 | 25 | band_place | FERTASA 5.9: K pre-plant only; starter N (salt-burn limit on band placement). |
| 2 | Squaring / early bloom (weeks 6-13 — PEAK N) | 12–2 | 2 | 80 | 0 | 0 | 40 | 45 | broadcast | FERTASA 5.9 CRITICAL: "all N be applied before 13 weeks after planting." Peak N uptake weeks 6-15. |
| 3 | Boll fill & maturation (weeks 14+) | 2–4 | 0 | 0 | 0 | 0 | 20 | 20 | broadcast | FERTASA 5.9: no N after week 13. K already pre-planted. |
| 4 | Defoliation & harvest | 5–6 | 0 | 0 | 0 | 0 | 10 | 10 | broadcast | Harvest prep. |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | — | —–— — | 1–1 | 60–60 | — | FERTASA Handbook 5.9 Table 1 |
| K | — | —–— — | 2–2 | 70–70 | — | FERTASA Handbook 5.9 Table 1 |
| K | — | —–— — | 2.5–2.5 | 85–85 | — | FERTASA Handbook 5.9 Table 1 |
| K | — | —–— — | 4.5–— | 140–140 | — | FERTASA Handbook 5.9 Table 1 |
| N | — | —–— — | 1–1 | 90–90 | — | FERTASA Handbook 5.9 Table 1 |
| N | — | —–— — | 2–2 | 175–175 | — | FERTASA Handbook 5.9 Table 1 |
| N | — | —–— — | 2.5–2.5 | 220–220 | — | FERTASA Handbook 5.9 Table 1 |
| N | — | —–— — | 4.5–— | 250–250 | — | FERTASA Handbook 5.9 Table 1 |
| P | Bray-1 | 0–10 mg/kg | 1–1 | 15–15 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 0–10 mg/kg | 2–2 | 20–20 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 0–10 mg/kg | 3–3 | 30–30 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 0–10 mg/kg | 4–4 | 30–30 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 10–15 mg/kg | 1–1 | 10–10 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 10–15 mg/kg | 2–2 | 15–15 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 10–15 mg/kg | 3–3 | 20–20 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 10–15 mg/kg | 4–4 | 25–25 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 15–20 mg/kg | 1–1 | 0–0 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 15–20 mg/kg | 2–2 | 10–10 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 15–20 mg/kg | 3–3 | 15–15 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 15–20 mg/kg | 4–4 | 15–15 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 20–— mg/kg | 1–1 | 0–0 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 20–— mg/kg | 2–2 | 0–0 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 20–— mg/kg | 3–3 | 0–0 | — | FERTASA Handbook 5.9 Table 4 |
| P | Bray-1 | 20–— mg/kg | 4–4 | 0–0 | — | FERTASA Handbook 5.9 Table 4 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Most-recently-mature leaf | First square / early bloom | — | 3.5–4.5 | — | NC State Foliar Analysis Cotton + NCDA Cotton Tissue Sampling Guide |
| P | Most-recently-mature leaf | First square / early bloom | — | 0.3–0.5 | — | NC State + NCDA Cotton |
| K | Most-recently-mature leaf | First square / early bloom | — | 1.7–3 | — | NC State + UGA Cotton |
| Ca | Most-recently-mature leaf | First square / early bloom | — | 2–3 | — | NC State + UGA Cotton |
| Mg | Most-recently-mature leaf | First square / early bloom | — | 0.3–0.6 | — | NC State + UGA Cotton |
| S | Most-recently-mature leaf | First square / early bloom | — | 0.2–0.5 | — | NC State + Missouri Ext G4257 Sulfur & Boron on Cotton |
| B | Most-recently-mature leaf | First square / early bloom | — | 20–60 | — | NC State + Missouri Ext G4257 + UGA Cotton |
| Zn | Most-recently-mature leaf | First square / early bloom | — | 20–80 | — | NC State + UGA Cotton |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| total | kg/t seed cotton | 90 | 15 | 60 | — | — | — | 5.9 |
| seed cotton | kg per t seed cotton | 50 | 7.85 | 41.5 | 5 | 3 | 3 | Cotton Foundation Ch 4 + Missouri Extension G4256 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | — | rainfed | 1.2 | 1.75 | 2 | t seed cotton/ha | Cotton SA Technical Information |
| — | — | irrigated | 3.6 | 4.5 | 5 | t seed cotton/ha | Cotton SA Technical Information |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S', 'Zn'] | At planting | — |
| side_dress | False | ['N', 'K'] | Square/boll topdress; K critical for fibre | — |
| fertigation | False | ['N', 'K', 'S'] | Under pivot | — |
| foliar | False | ['B', 'Zn', 'Mn', 'Fe'] | B for boll retention | — |



### Fig

<a id="fig"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 12 |
| Yield unit | t fruit/ha |
| Population / ha | 500 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 6 |
| P | 0.7 |
| K | 6 |
| Ca | 2 |
| Mg | 0.8 |
| S | 0.4 |
| B | 0.06 |
| Zn | 0.04 |
| Fe | 0.12 |
| Mn | 0.04 |
| Cu | 0.015 |
| Mo | 0.008 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 5.4 | 5.9 | 6.9 | 7.4 | DERIVED from H2O − 0.6 offset. T2 (derived). |
| pH (H2O) | 6 | 6.5 | 7.5 | 8 | Yara Fig Crop Guide + UC ANR Fig Production. Tolerates alkaline; pH 6.0-7.8 ideal. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| P (Olsen) | 8 | 15 | 40 | 80 | Mediterranean fig orchards baseline (UC ANR + Israeli Volcani). T2. |
| **K** | — | — | — | — | _needs source_ |
| Ca | 800 | 1500 | 5000 | 10000 | High-Ca tolerance is a Ficus carica trademark. Soliman et al. 2018 Egypt J Hort 45. T3. |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| Na | — | 200 | 600 | 1200 | Cl/Na tolerance high; salt-tolerant rootstocks tolerate ECe 4 dS/m. FAO Salinity Handbook 1985 + Yara. T2. |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest & leaf fall | 4–5 | 1 | 10 | 5 | 5 | 5 | 5 | broadcast | Light feeding after harvest |
| 2 | Dormancy | 6–7 | 1 | 5 | 5 | 5 | 5 | 5 | broadcast | Minimal demand |
| 3 | Bud break & shoot growth | 8–9 | 2 | 25 | 30 | 20 | 20 | 20 | fertigation | N and P for new growth |
| 4 | Fruit development | 10–12 | 3 | 35 | 35 | 30 | 40 | 40 | fertigation | Ca for fruit quality |
| 5 | Ripening & harvest | 1–3 | 2 | 25 | 25 | 40 | 30 | 30 | fertigation | K for sugar and flavour |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | mid-shoot full leaf | post-harvest | 1.7 | 2–2.5 | 2.8 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| P | mid-shoot full leaf | post-harvest | 0.1 | 0.15–0.25 | 0.35 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| K | mid-shoot full leaf | post-harvest | 1.2 | 1.5–2.5 | 3 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| Ca | mid-shoot full leaf | post-harvest | 1.5 | 2.5–4 | 5 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| Mg | mid-shoot full leaf | post-harvest | 0.4 | 0.5–1 | 1.5 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| S | mid-shoot full leaf | post-harvest | 0.15 | 0.2–0.4 | 0.55 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| B | mid-shoot full leaf | post-harvest | 25 | 30–80 | 120 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| Zn | mid-shoot full leaf | post-harvest | 18 | 20–50 | 70 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| Fe | mid-shoot full leaf | post-harvest | 80 | 100–250 | 350 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| Mn | mid-shoot full leaf | post-harvest | 30 | 40–150 | 250 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| Cu | mid-shoot full leaf | post-harvest | 5 | 7–20 | 30 | Yara Fig Crop Guide + Marondedze et al. 2020 Acta Hort 1310:215. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fresh fruit | 4.5 | 0.6 | 5.5 | 1.8 | 0.7 | 0.35 | Migration 112 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.2 | 0.2 | 0.15 | 0.2 | Yara Fig + DAFF Fig Production Guide 2018. Bears year 2, full year 5. |
| Year 2 | 2–2 | 0.45 | 0.45 | 0.4 | 0.45 | Yara Fig. |
| Year 3 | 3–3 | 0.7 | 0.7 | 0.65 | 0.7 | Yara Fig. |
| Year 4 | 4–4 | 0.9 | 0.9 | 0.85 | 0.9 | Yara Fig. |
| Year 5+ | 5–99 | 1 | 1 | 1 | 1 | Yara Fig — full bearing. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | SA | dryland | 6 | 8 | 12 | t fresh fruit/ha | DAFF Fig Production Guide 2018. |
| — | SA | irrigated | 12 | 15 | 20 | t fresh fruit/ha | DAFF + Subtrop industry note. |
| Brown Turkey | Mediterranean | irrigated | 15 | 18 | 25 | t fresh fruit/ha | UC ANR + Yara. |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FAO Salinity Handbook 1985 + Yara Fig | n/a | 1985 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Dormancy and post-harvest | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S'] | Active growth when irrigated | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu'] | Micronutrient correction | — |



### Garlic

<a id="garlic"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 8 |
| Yield unit | t bulb/ha |
| Population / ha | 200000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 8.4 |
| P | 2 |
| K | 9.8 |
| Ca | 0.6 |
| Mg | 0.3 |
| S | 4.6 |
| B | 0.005 |
| Zn | 0.016 |
| Fe | 0.108 |
| Mn | 0.017 |
| Cu | 0.004 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.4 | 5.4 | 6.4 | 6.9 | DERIVED from H2O band − 0.6 KCl/H2O offset. T2 (derived). |
| pH (H2O) | 5 | 6 | 7 | 7.5 | UMN Extension + UC ANR Garlic + Graceland SA: target 6.0-7.0; 6.5 mid. Garlic acid-intolerant. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 50 | 100 | FERTASA Handbook 7th ed. §5.6.1 Table 2 (matches existing rate-table seed). T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 50 | 80 | 150 | 250 | FERTASA Handbook 7th ed. §5.6.1 Table 3 (matches existing rate-table seed). T1. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| S | 5 | 10 | 30 | 60 | Nguyen et al. 2022 Plants 11:2571 — yield rising to 30 kg S/ha, optimum 75; 10 mg/kg topsoil S = low baseline. T2. |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & rooting | 3–4 | 1 | 15 | 35 | 10 | 15 | 15 | band_place | P for clove establishment |
| 2 | Vegetative leaf growth | 5–7 | 2 | 40 | 30 | 25 | 25 | 25 | side_dress | High N for leaf number = bulb size |
| 3 | Bulb initiation & fill | 7–9 | 2 | 30 | 25 | 40 | 35 | 35 | fertigation | K and S for quality and pungency |
| 4 | Maturation | 9–10 | 1 | 15 | 10 | 25 | 25 | 25 | broadcast | Reduce N; allow tops to dry |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 110–110 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 70–70 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 120–160 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 100–100 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 50–50 | — | FERTASA Handbook 5.6.1 Table 2 |
| S | KCl-extractable | 0–10 mg/kg | 0–12 | 60–75 | — | Nguyen et al. 2022 + Bideshki 2013 Plants 11:2571 |
| S | KCl-extractable | 10–20 mg/kg | 0–12 | 30–45 | — | Nguyen et al. 2022 + Bideshki 2013 Plants 11:2571 |
| S | KCl-extractable | 20–999 mg/kg | 0–12 | 15–20 | — | Nguyen et al. 2022 + Bideshki 2013 Plants 11:2571 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | YFEL | bulb initiation | 3 | 3.5–5 | 5.5 | Trani & Raij 1997 (Brazilian official) cross-checked Cornell 2021 (>3.5% late May). T2. |
| P | YFEL | bulb initiation | 0.25 | 0.3–0.5 | 0.6 | Trani & Raij 1997. T2. |
| K | YFEL | bulb initiation | 3 | 3.5–5 | 6 | Trani & Raij 1997. T2. |
| Ca | YFEL | bulb initiation | 0.5 | 0.6–1.2 | 1.5 | Trani & Raij 1997. T2. |
| Mg | YFEL | bulb initiation | 0.15 | 0.2–0.4 | 0.5 | Trani & Raij 1997. T2. |
| S | YFEL | bulb initiation | 0.4 | 0.5–0.8 | 1.2 | Nguyen et al. 2022 Plants 11:2571 — >5.5 g S/kg DW = max-yield threshold. T2. |
| B | YFEL | bulb initiation | 25 | 30–60 | 80 | Trani & Raij 1997. T2. |
| Zn | YFEL | bulb initiation | 25 | 30–100 | 150 | Trani & Raij 1997. T2. |
| Fe | YFEL | bulb initiation | 40 | 50–100 | 150 | Trani & Raij 1997. T2. |
| Mn | YFEL | bulb initiation | 25 | 30–100 | 150 | Trani & Raij 1997. T2. |
| Cu | YFEL | bulb initiation | 4 | 5–10 | 15 | Trani & Raij 1997. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| total (leaves + bulb) | kg/t fresh bulb | 8.4 | 2 | 9.8 | — | — | 4.6 | Reddy et al. 2017 Int J Curr Microbiol App Sci |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | SA | dryland | 4 | 5 | 6 | t fresh bulb/ha | nufarmer Africa 2024. |
| — | SA | irrigated commercial | 6 | 8 | 9 | t fresh bulb/ha | Graceland Garlic Growers Guide 2021 (SA). |
| Egyptian White / Plouton (giant) | SA | irrigated | 8 | 10 | 12 | t fresh bulb/ha | Farmers Weekly + Graceland varietal notes. |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | Nguyen 2022 + Reddy 2017 | 5.6.1 | 2022 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At planting | — |
| broadcast | False | ['P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| side_dress | False | ['N', 'K', 'S'] | Active growth topdress | — |
| foliar | False | ['B', 'Mn', 'Zn'] | Micronutrient correction | — |



### Gem Squash

<a id="gem-squash"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 20 |
| Yield unit | t fruit/ha |
| Population / ha | 10000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3.5 |
| P | 0.45 |
| K | 4.5 |
| Ca | 0.4 |
| Mg | 0.3 |
| S | 0.2 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | — | —–— — | 0–— | 120–150 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 120–120 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 90–90 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | most-recent mature leaf | all stages | 4 | 4–5 | 5.5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| P | most-recent mature leaf | all stages | 0.3 | 0.3–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| K | most-recent mature leaf | all stages | 3 | 3–4 | 5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Ca | most-recent mature leaf | all stages | 1.2 | 1.2–2 | 3 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mg | most-recent mature leaf | all stages | 0.25 | 0.25–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| S | most-recent mature leaf | all stages | 0.2 | 0.2–0.75 | 1 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| B | most-recent mature leaf | all stages | 25 | 25–85 | 120 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Zn | most-recent mature leaf | all stages | 20 | 20–200 | 300 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Fe | most-recent mature leaf | all stages | 50 | 50–300 | — | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mn | most-recent mature leaf | all stages | 25 | 25–250 | 500 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Cu | most-recent mature leaf | all stages | 5 | 5–60 | 100 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

_No rows._



### Groundnut

<a id="groundnut"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 3 |
| Yield unit | t pod/ha |
| Population / ha | 0 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 30 |
| P | 3.15 |
| K | 9 |
| Ca | 1.4 |
| Mg | 1.55 |
| S | 10 |
| B | 0.05 |
| Zn | 0.05 |
| Fe | 0.3 |
| Mn | 0.06 |
| Cu | 0.015 |
| Mo | 0.008 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 6.2 | 7 | FERTASA 5.5.3 + Groundnut Forum SA. T1. |
| pH (H2O) | 5 | 5.5 | 6.8 | 7.5 | DAFF Groundnut Production Guide 2010. T1. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 5 | 10 | 20 | 40 | FERTASA 5.5.3 Table 1 + ARC-GCI. T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 30 | 50 | 100 | 200 | FERTASA 5.5.3 Tab 2 + UF/IFAS SS-AGR-263. T1+T2. |
| Ca | 300 | 800 | 2500 | 5000 | High Ca in pegging zone for proper pod fill. Critical for kernel quality. |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & establishment | 10–11 | 1 | 100 | 100 | 0 | 30 | 25 | band_place | FERTASA 5.5.3: all applied N at planting (total only 10-40 kg/ha). Apply K to preceding crop, not directly. |
| 2 | Vegetative | 12–12 | 0 | 0 | 0 | 0 | 20 | 25 | broadcast | FERTASA 5.5.3: Rhizobium handles N. |
| 3 | Flowering & pegging | 1–2 | 1 | 0 | 0 | 0 | 35 | 25 | broadcast | FERTASA 5.5.3: GYPSUM 200-300 kg/ha at pegging for pod Ca. NOT in NPK split. Spanish (Robin) types lower Ca need. |
| 4 | Pod fill & maturation | 3–5 | 0 | 0 | 0 | 0 | 15 | 25 | broadcast | FERTASA 5.5.3: no further feed. |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | — | —–— — | 1–1 | 10–10 | — | FERTASA Handbook 5.5.3 Table 2 |
| N | — | —–— — | 2–2 | 20–20 | — | FERTASA Handbook 5.5.3 Table 2 |
| N | — | —–— — | 3–3 | 30–30 | — | FERTASA Handbook 5.5.3 Table 2 |
| N | — | —–— — | 4–4 | 40–40 | — | FERTASA Handbook 5.5.3 Table 2 |
| N | — | —–— — | 5–5 | 50–50 | — | FERTASA Handbook 5.5.3 Table 2 |
| N | — | —–— — | 6–6 | 60–60 | — | FERTASA Handbook 5.5.3 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | mature leaf | mid-season | 0.1 | 0.1–5 | 10 | SCSB394 — peanut Mo wide range; pH-dependent. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| hay | kg/2t hay | 40 | 2 | 34 | 20 | 7 | — | 5.5.3 |
| nuts | kg/640kg nuts | 28 | 3 | 5 | 0.4 | 1.2 | 10 | 5.5.3 |
| pods | kg/360kg pods | 2 | 0.15 | 4 | 1 | 0.35 | — | 5.5.3 |
| total | kg/3t unshelled | 70 | 5.15 | 43 | 21.4 | 8.55 | 10 | 5.5.3 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.5.3 + Manson 2013 SAJPS | 5.5.3 | 2017 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['P', 'K', 'S'] | At planting; avoid high N near seed | — |
| broadcast | False | ['Ca', 'Mg', 'S', 'P'] | Pre-plant Ca critical for pegging zone | — |
| foliar | False | ['B', 'Mo', 'Fe', 'Mn'] | Mo for fixation; B for pegging | — |



### Guava

<a id="guava"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t fruit/ha |
| Population / ha | 600 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4 |
| P | 0.5 |
| K | 2 |
| Ca | 1.2 |
| Mg | 0.5 |
| S | 0.3 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.9 | 5.4 | 6.9 | 7.4 | DERIVED from H2O − 0.6 offset. T2 (derived). |
| pH (H2O) | 5.5 | 6 | 7.5 | 8 | ICAR Lucknow Guava Manual 2018 + Yara Guava Crop Guide. Wide tolerance. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 8 | 15 | 30 | 60 | Embrapa Goiabeira (Natale et al. 2009 Rev Bras Frut 31:1142). T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 120 | 250 | 400 | Embrapa + ICAR. T2. |
| Ca | 600 | 1000 | 3000 | 6000 | Natale et al. 2009 Rev Bras Frut. T2. |
| Mg | 80 | 120 | 250 | 400 | Natale et al. 2009. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest recovery | 6–7 | 1 | 10 | 10 | 5 | 5 | 5 | broadcast | Recovery after harvest |
| 2 | Vegetative flush | 8–9 | 2 | 30 | 25 | 20 | 20 | 20 | fertigation | N for new growth |
| 3 | Flowering & fruit set | 10–11 | 2 | 20 | 25 | 20 | 25 | 25 | fertigation | B for pollination |
| 4 | Fruit development | 12–2 | 2 | 25 | 25 | 30 | 30 | 30 | fertigation | Ca for firmness; K for sugar |
| 5 | Ripening & harvest | 3–5 | 1 | 15 | 15 | 25 | 20 | 20 | fertigation | K for flavour |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 3rd-4th leaf pair | fruit set | 1.4 | 1.6–2.4 | 2.8 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| P | 3rd-4th leaf pair | fruit set | 0.14 | 0.16–0.3 | 0.4 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| K | 3rd-4th leaf pair | fruit set | 1.4 | 1.6–2.5 | 3.5 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| Ca | 3rd-4th leaf pair | fruit set | 0.8 | 1–2 | 3 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| Mg | 3rd-4th leaf pair | fruit set | 0.2 | 0.25–0.45 | 0.6 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| S | 3rd-4th leaf pair | fruit set | 0.18 | 0.2–0.35 | 0.5 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| B | 3rd-4th leaf pair | fruit set | 25 | 30–60 | 100 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| Zn | 3rd-4th leaf pair | fruit set | 18 | 20–40 | 60 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| Fe | 3rd-4th leaf pair | fruit set | 70 | 80–200 | 300 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| Mn | 3rd-4th leaf pair | fruit set | 30 | 40–150 | 250 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| Cu | 3rd-4th leaf pair | fruit set | 5 | 7–20 | 30 | ICAR Indian J Hort 74:381 Singh et al. 2017 + Embrapa Natale et al. 2009. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fresh fruit | 6.5 | 1 | 7.5 | 1.5 | 0.6 | 0.4 | Migration 112 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-2 | 0–2 | 0.2 | 0.2 | 0.2 | 0.2 | ICAR Lucknow Manual 2018. Bears year 3 from cutting, full year 5. |
| Year 3 | 3–3 | 0.5 | 0.5 | 0.5 | 0.5 | ICAR Lucknow Manual 2018. |
| Year 4 | 4–4 | 0.8 | 0.8 | 0.8 | 0.8 | ICAR Lucknow Manual 2018. |
| Year 5+ | 5–99 | 1 | 1 | 1 | 1 | ICAR Lucknow Manual 2018 — full bearing. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| Fan Retief | SA | irrigated | 18 | 25 | 35 | t fresh fruit/ha | ARC LNR Nelspruit guava trial (Schoeman 2014 SA Subtrop). |
| Allahabad Safeda | India | irrigated | 25 | 35 | 50 | t fresh fruit/ha | ICAR Lucknow Manual 2018. |
| — | SA | dryland | 8 | 12 | 18 | t fresh fruit/ha | DAFF Guava Production Guide 2014. |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Primary for dryland; under canopy | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S'] | When irrigated | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu'] | Micronutrient correction | — |



### Honeybush

<a id="honeybush"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 3 |
| Yield unit | t dry/ha |
| Population / ha | 4000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 0 |
| P | 0 |
| K | 0 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| pH (H2O) | 4 | 4.5 | 5 | 5.5 | DAFF Honeybush: prefers acidic soil pH < 5. Similar tolerance to rooibos. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 3 | 6 | 20 | 50 | Cawe & Dlamini 2007 SAJPS Vol 24 No 3 — below 6 mg/kg suppresses growth; target ≥20 mg/kg for plastic-mulched Cyclopia subternata. T1 SA. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| P | — | —–— — | 0–— | 100–120 | — | DAFF Honeybush Guideline Establishment P (rock phosphate) |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| True | DAFF Honeybush Production Guide 2019 | 5.x | 2019 | 1 | Honeybush is native to acidic Cape fynbos soils like rooibos; same reasoning. |

**Application methods** (`crop_application_methods`)

_No rows._



### Kiwi

<a id="kiwi"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t fruit/ha |
| Population / ha | 600 |
| Years to bearing | 3 |
| Years to full bearing | 7 |
| N (target/uptake) | 5.4 |
| P | 0.92 |
| K | 4.2 |
| Ca | 4.5 |
| Mg | 0.8 |
| S | 0.8 |
| B | 0.05 |
| Zn | 0.05 |
| Fe | 0.1 |
| Mn | 0.05 |
| Cu | 0.01 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 6 | 6.5 | DERIVED from H2O band − 0.5 KCl/H2O offset. NZ literature is exclusively pH(H2O); SA labs report KCl. T3 (derived). |
| pH (H2O) | 5 | 5.5 | 6.5 | 7 | OSU PNW 507 (2005) Soil section: optimum 5.5-6.0; poor growth above 7.2. Hill Labs Kiwifruit Crop Guide cross-check. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 25 | 40 | 80 | 130 | DERIVED from Olsen × ~1.6 conversion (FERTASA 5.7 method ratio). NZ literature uses Olsen exclusively. T3 (derived). |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| P (Olsen) | 15 | 25 | 50 | 80 | Fertiliser Association of NZ + Hill Labs Basic Soil interpretation: tree-fruit/orchard horticulture optimum 25-50 mg/kg. T1. |
| K | 80 | 150 | 300 | 600 | OSU PNW 507 + Smith/Asher/Clark 1985: NZ K demand high; deficiency widespread. T2. |
| **Ca** | — | — | — | — | _needs source_ |
| Mg | 60 | 100 | 300 | 600 | Smith/Asher/Clark 1985 + Buwalda generic horticulture bands. Mg deficiency observed Feb-onward in older leaves. T3. |
| **S** | — | — | — | — | _needs source_ |
| Na | — | — | 50 | 100 | Hill Labs Kiwifruit Crop Guide + PNW 507 Table 1: kiwifruit cannot tolerate high Na; irrigation Na <50 ppm. T1. |
| B | 0.5 | 0.8 | 1.5 | 2.5 | Hill Labs Kiwifruit Crop Guide: B-sensitive crop; excess B causes premature ripening. Narrow band justified. T1. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Dormancy / pre-bud-break | 7–8 | 1 | 5 | 10 | 5 | 5 | 5 | broadcast | Pre-budbreak P + Ca lime application; ~50% of season P (PNW 507). |
| 2 | Budbreak & leaf emergence | 9–9 | 2 | 30 | 25 | 15 | 20 | 20 | fertigation | Major N split — PNW 507: "two-thirds of N at bud break". Haifa K2O 15%. |
| 3 | Flowering | 10–10 | 1 | 20 | 15 | 20 | 20 | 20 | fertigation | Haifa K2O 20%. B + Zn foliar at bloom (kiwi B-sensitive but B-demanding for set). |
| 4 | Fruit set & cell division | 11–11 | 1 | 15 | 15 | 25 | 25 | 20 | fertigation | Haifa K2O 25%. Ca-critical period — foliar Ca starts. |
| 5 | Fruit fill / cell expansion | 12–2 | 3 | 20 | 20 | 25 | 20 | 20 | fertigation | Haifa K2O 25%. Peak K demand (Smith & Buwalda 1988). Maintain N moderate to avoid succulence. |
| 6 | Fruit maturation | 3–3 | 1 | 5 | 10 | 10 | 5 | 10 | fertigation | Haifa K2O 15%. Reduce N — high N at maturation suppresses dry-matter % (Morton 2013 Massey). |
| 7 | Post-harvest reserve build | 4–5 | 1 | 5 | 5 | 0 | 5 | 5 | broadcast | Late-season foliar N for reserve storage (Tagliavini 2007). |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Leaf opposite fruit | Feb-Apr (late summer SH) | 2 | 2–2.8 | 3 | OSU PNW 507 Table 2 (2005). Cross-check Hills 2010 normal 2.4-4.0% for early-season Oct-Nov. T2. |
| P | Leaf opposite fruit | Feb-Apr | 0.13 | 0.13–0.3 | 0.4 | OSU PNW 507 Table 2; Smith/Asher/Clark 1987 P 0.18-0.22%. T2. |
| K | Leaf opposite fruit | Feb-Apr | 1.5 | 1.5–2.5 | 3 | OSU PNW 507 Table 2; Testolin & Crivello 1987 critical 1.6-2.0%. T2. |
| Ca | Leaf opposite fruit | Feb-Apr | 2 | 2–4 | — | OSU PNW 507 Table 2. T2. |
| Mg | Leaf opposite fruit | Feb-Apr | 0.2 | 0.2–0.8 | 1 | OSU PNW 507 Table 2. T2. |
| S | Leaf opposite fruit | Feb-Apr | 0.15 | 0.15–0.45 | 0.5 | OSU PNW 507 Table 2. T2. |
| B | Leaf opposite fruit | Feb-Apr | 25 | 25–200 | 250 | OSU PNW 507 Table 2. Hill Labs: B-sensitive crop. T2. |
| Zn | Leaf opposite fruit | Feb-Apr | 15 | 15–30 | 50 | OSU PNW 507 Table 2. T2. |
| Fe | Leaf opposite fruit | Feb-Apr | 60 | 60–200 | 250 | OSU PNW 507 Table 2. T2. |
| Mn | Leaf opposite fruit | Feb-Apr | 50 | 50–200 | 1500 | OSU PNW 507 Table 2. Hill Labs: Mn toxicity at pH 5.2. T2. |
| Cu | Leaf opposite fruit | Feb-Apr | 5 | 5–15 | 25 | OSU PNW 507 Table 2. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

_Extra leaf rows outside the canonical element set:_ `Cl`

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| total (annual vine uptake) | kg/t fresh fruit | 5.4 | 0.92 | 4.2 | 4.5 | 0.8 | 0.8 | Zhao Tong Wang 2013 Acta Hort 984:169 + Smith Buwalda Clark 1988 Sci Hort 37:87 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 (planting) | 1–1 | 0.1 | 0.1 | 0.2 | 0.1 | PNW 507 p.12: 1.2 oz N/vine season ≈ 13 kg N/ha vs mature 190 kg/ha = 7%. T2. |
| Year 2 | 2–2 | 0.2 | 0.2 | 0.4 | 0.25 | PNW 507: 3.2 oz N/vine = 35 kg N/ha = 18%. T2. |
| Year 3 | 3–3 | 0.4 | 0.4 | 0.6 | 0.5 | PNW 507: year 3 60-90 lb N/acre ≈ 80 kg N/ha = 42%. T2. |
| Year 4 | 4–4 | 0.65 | 0.65 | 0.8 | 0.75 | Buwalda et al. 1990 Te Puke: 4-y vines 35-55 t/ha at low density. T2. |
| Year 5-6 | 5–6 | 0.85 | 0.85 | 0.95 | 0.9 | Smith et al. 1988: 5-y uptake 141 vs 6-y 165 kg N/ha = 85%. T3. |
| Year 7+ (mature) | 7–99 | 1 | 1 | 1 | 1 | PNW 507: "mature 7+ years". T2. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| Hayward | NZ Bay of Plenty | irrigated pergola | 25 | 35 | 55 | t fruit/ha | Buwalda et al. 1990 (4-year × 2-density trial); Sale 1997. |
| Hayward | SA Western Cape | irrigated, T-bar/pergola | 15 | 25 | 35 | t fruit/ha | Inferred from NZ mature − SA establishment penalty; Food For Mzansi. |
| SunGold (Hort16A / G3) | NZ | irrigated pergola | 35 | 45 | 65 | t fruit/ha | Hill Labs Crop Guide; Mills et al. 2008 used 295 kg N/ha at high yield. |
| SunGold (Hort16A / G3) | SA | irrigated | 20 | 30 | 45 | t fruit/ha | Inferred SH penalty; producepulse 2025 SA-Kiwi industry data. |
| Hardy kiwi (A. arguta) | PNW / cool SA | varies | — | 12 | 25 | t fruit/ha | PNW 507 p.5 (Ananasnaya 60-125 lb/vine × 480 vines/ha). |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| True | OSU PNW 507 + Smith/Asher/Clark 1985 | PNW 507 Soil section + Smith 1985 leaf nutrition | 2005 | 2 | Kiwi calcifuge-leaning (5.5-6.5 H2O); Mn toxicity at pH 5.2. Universal FERTASA ratio path over-limes kiwi. Same rationale as Blueberry/Blackberry. TODO: no_chloride_fertilisers flag pending schema extension — kiwi acutely Cl-sensitive (PNW 507 p.12). |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Winter dormancy + post-harvest; granular under canopy line. Split N across the season. | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary in-season delivery; weekly during budbreak through fruit fill (Sep-Mar). | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca'] | Zn + B critical for fruit set; Ca sprays for storage quality. | — |



### Lentils

<a id="lentils"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 2 |
| Yield unit | t seed/ha |
| Population / ha | 0 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 50 |
| P | 6.2 |
| K | 32 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| total | kg/t seed | 50 | 6.2 | 32 | — | — | — | 5.5.4 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | GRDC GrowNote Lentil + ICARDA 2009 | 5.5.4 | 2017 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['P', 'K', 'S'] | At planting; N-fixing legume | — |
| broadcast | False | ['P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| foliar | False | ['Mo', 'B', 'Mn', 'Fe'] | Mo for fixation | — |



### Lettuce

<a id="lettuce"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 40 |
| Yield unit | t head/ha |
| Population / ha | 60000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3 |
| P | 0.4 |
| K | 4.5 |
| Ca | 0.5 |
| Mg | 0.2 |
| S | 0.15 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Transplant & establishment | 2–3 | 1 | 15 | 35 | 10 | 15 | 15 | band_place | Starter P for root recovery |
| 2 | Rapid leaf growth | 3–5 | 3 | 50 | 35 | 40 | 40 | 40 | fertigation | High N for leaf expansion |
| 3 | Head formation & harvest | 5–7 | 2 | 35 | 30 | 50 | 45 | 45 | fertigation | K and Ca for tipburn prevention |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 120–120 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 100–160 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 100–100 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Wrapper leaf | Heading | — | 3.5–5 | — | UF/IFAS HS964 + Yara Lettuce TotalLettuce |
| P | Wrapper leaf | Heading | — | 0.3–0.55 | — | UF/IFAS HS964 + Yara Lettuce |
| K | Wrapper leaf | Heading | — | 4.5–6 | — | UF/IFAS HS964 + Yara Lettuce |
| Ca | Wrapper leaf | Heading | — | 0.9–1.8 | — | UF/IFAS HS964 + Yara Lettuce |
| Mg | Wrapper leaf | Heading | — | 0.3–0.6 | — | UF/IFAS HS964 + Yara Lettuce |
| **S** | — | — | — | — | — | _needs source_ |
| B | Wrapper leaf | Heading | — | 25–50 | — | UF/IFAS HS964 + Yara Lettuce |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | most-recent mature leaf | mid-growth | 0.1 | 0.2–1 | 5 | SCSB#394 p.73 Lettuce, Greenhouse. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| Crisphead | — | irrigated | 30 | 45 | 60 | t head/ha | Starke Ayres Lettuce 2019 |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | UC ANR Lettuce Production | n/a | 2018 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| fertigation | True | ['N', 'K', 'Ca', 'Mg', 'S'] | Primary; short cycle needs precise delivery | — |
| broadcast | False | ['P', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| foliar | False | ['Ca', 'B', 'Fe', 'Mn'] | Ca for tipburn prevention | — |



### Litchi

<a id="litchi"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 10 |
| Yield unit | t fruit/ha |
| Population / ha | 200 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 7 |
| P | 0.8 |
| K | 7 |
| Ca | 1.5 |
| Mg | 0.8 |
| S | 0.4 |
| B | 0.06 |
| Zn | 0.04 |
| Fe | 0.12 |
| Mn | 0.04 |
| Cu | 0.015 |
| Mo | 0.008 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 6 | 6.5 | Menzel & Simpson 1992 ACOTANC: H2O 5.8-6.5 minus 0.5. T2 derived. |
| pH (H2O) | 5 | 5.8 | 6.5 | 7 | ALGA: litchi prefers slightly acidic soil, pH 5.8-6.5. Above 7.0 = micronutrient lock-up (Fe, Mn, Zn). |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 30 | 60 | 200 | 350 | Menzel & Simpson 1992: 100-300 mg/kg. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 100 | 200 | 400 | 600 | Menzel & Simpson 1992 (0.5-1.0 meq/100g converted). T2. |
| Ca | 300 | 600 | 1000 | 1600 | Menzel & Simpson 1992 (3.0-5.0 meq/100g converted). T2. |
| Mg | 120 | 240 | 480 | 720 | Menzel & Simpson 1992 (2.0-4.0 meq/100g converted). T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 1 | 2 | 4 | Menzel & Simpson 1992. T2. |
| Zn | 0.5 | 2 | 15 | 30 | Menzel & Simpson 1992. T2. |
| **Fe** | — | — | — | — | _needs source_ |
| Mn | 5 | 10 | 50 | 100 | Menzel & Simpson 1992. T2. |
| Cu | 0.5 | 1 | 3 | 6 | Menzel & Simpson 1992. T2. |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest recovery | 2–3 | 1 | 20 | 25 | 15 | 20 | 20 | broadcast | Recovery from heavy fruiting |
| 2 | Vegetative flush | 4–5 | 1 | 25 | 20 | 15 | 20 | 20 | fertigation | New growth for next season flowers |
| 3 | Flower induction (stress period) | 6–7 | 1 | 5 | 15 | 10 | 10 | 10 | foliar | Minimal N — cold/dry stress triggers flowering |
| 4 | Flowering & fruit set | 8–9 | 2 | 20 | 20 | 25 | 25 | 25 | fertigation | B critical for fruit set; K for retention |
| 5 | Fruit development & harvest | 10–1 | 3 | 30 | 20 | 35 | 25 | 25 | fertigation | High K for fruit colour, size, and sugar; Ca for skin quality |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recently mature leaves from non-bearing branches | 1-2 weeks post-panicle emergence | 1.5 | 1.5–1.8 | — | ALGA Lychee Field Guide |
| P | Recently mature leaves | 1-2 weeks post-panicle | 0.14 | 0.14–0.22 | — | ALGA Lychee Field Guide |
| K | Recently mature leaves | 1-2 weeks post-panicle | 0.7 | 0.7–1.1 | — | ALGA Lychee Field Guide |
| Ca | Recently mature leaves | 1-2 weeks post-panicle | 0.6 | 0.6–1 | — | ALGA Lychee Field Guide |
| Mg | Recently mature leaves | 1-2 weeks post-panicle | 0.3 | 0.3–0.5 | — | ALGA Lychee Field Guide |
| S | leaf | fruit set | 0.15 | 0.18–0.3 | 0.5 | Menzel & Simpson 1992 ACOTANC. T2. |
| B | leaf | fruit set | 20 | 25–60 | 80 | Menzel & Simpson 1992. T2. |
| Zn | leaf | fruit set | 12 | 15–30 | 50 | Menzel & Simpson 1992. T2. |
| Fe | leaf | fruit set | 40 | 50–100 | 200 | Menzel & Simpson 1992. T2. |
| Mn | leaf | fruit set | 80 | 100–250 | 500 | Menzel & Simpson 1992. T2. |
| Cu | leaf | fruit set | 8 | 10–25 | 40 | Menzel & Simpson 1992. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-2 | 0–2 | 0.2 | 0.2 | 0.25 | 0.15 | Establishment |
| Year 3-4 | 3–4 | 0.4 | 0.4 | 0.4 | 0.35 | Pre-bearing |
| Year 5-7 | 5–7 | 0.7 | 0.7 | 0.7 | 0.65 | Increasing yield |
| Year 8+ | 8–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | Stassen 2007 + ALGA Lychee Field Guide | n/a | 2007 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Post-harvest main application; avoid N during flower induction (Apr-Jun) | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Zn', 'B'] | During fruit development; K critical for fruit colour | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca'] | B for fruit set; Zn for leaf health | — |



### Lucerne

<a id="lucerne"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 15 |
| Yield unit | t hay/ha |
| Population / ha | 0 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 0 |
| P | 2.7 |
| K | 21 |
| Ca | 8 |
| Mg | 2 |
| S | 2 |
| B | 0.1 |
| Zn | 0.03 |
| Fe | 0.3 |
| Mn | 0.05 |
| Cu | 0.02 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 5 | 5.5 | 6.8 | 7.5 | Requires higher pH (5.8-6.8 KCl) for Rhizobium nodulation and Mo availability. |
| pH (H2O) | 5.5 | 6 | 7.3 | 8 | Requires higher pH for nodulation; sensitive to acid soils. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 4 | 8 | 16 | 32 | FERTASA 5.12.2 Tab 1. T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| Ca | 1000 | 2000 | 4000 | 8000 | FERTASA 5.12.2 + UC ANR 8287 (high Ca demand). T1+T2. |
| Mg | 100 | 150 | 300 | 600 | UC ANR 8287 Alfalfa Soil Fertility. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.8 | 1.5 | 2.5 | High B requirement; B deficiency causes yellowing and poor regrowth. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| Mo | 0.05 | 0.1 | 0.3 | — | FERTASA 5.12.2 + UC ANR 8290 — Mo critical for Sinorhizobium meliloti. T1+T2. |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Establishment year starter (pre-plant + seedling) | 3–4 | 1 | 100 | 50 | 30 | 50 | 40 | band_place | FERTASA 5.12.2 Table 5.12.2.4: establishment year 25-55 kg N/ha starter only. ALL NPK in notes applies to ESTABLISHMENT YEAR only. Autumn or spring sow. |
| 2 | Spring regrowth / first cut | 9–10 | 2 | 0 | 30 | 30 | 25 | 25 | broadcast | FERTASA 5.12.2: 0% applied N on established stands (stimulates grasses/weeds). K 100 kg/ha spring. |
| 3 | Summer cuts (peak production) | 11–2 | 3 | 0 | 10 | 20 | 15 | 15 | broadcast | FERTASA 5.12.2: 0% applied N. Midsummer K top-up if needed. |
| 4 | Autumn cuts / pre-winter | 3–5 | 2 | 0 | 5 | 10 | 5 | 10 | broadcast | FERTASA 5.12.2: early April P for winter hardiness. |
| 5 | Winter dormancy | 6–8 | 0 | 0 | 5 | 10 | 5 | 10 | broadcast | FERTASA 5.12.2: light maintenance only. P every 2 years: 3 kg P per ton DM removed. |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| B | Hot-water | 0–0.5 mg/kg | 0–— | 1–1 | — | FERTASA Handbook 5.12.2 image 519 |
| B | Hot-water | 0–0.5 mg/kg | 0–— | 2–2 | — | FERTASA Handbook 5.12.2 image 519 |
| B | Hot-water | 0–0.5 mg/kg | 0–— | 3–3 | — | FERTASA Handbook 5.12.2 image 519 |
| K | Ambic | 0–20 mg/kg | 4–4 | 208–208 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 0–20 mg/kg | 8–8 | 270–270 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 0–20 mg/kg | 12–12 | 327–327 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 0–20 mg/kg | 16–16 | 379–379 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 0–20 mg/kg | 20–20 | 426–426 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 20–40 mg/kg | 4–4 | 168–168 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 20–40 mg/kg | 8–8 | 230–230 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 20–40 mg/kg | 12–12 | 287–287 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 20–40 mg/kg | 16–16 | 339–339 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 20–40 mg/kg | 20–20 | 386–386 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 40–60 mg/kg | 4–4 | 128–128 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 40–60 mg/kg | 8–8 | 190–190 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 40–60 mg/kg | 12–12 | 247–247 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 40–60 mg/kg | 16–16 | 299–299 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 40–60 mg/kg | 20–20 | 346–346 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 60–80 mg/kg | 4–4 | 88–88 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 60–80 mg/kg | 8–8 | 150–150 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 60–80 mg/kg | 12–12 | 207–207 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 60–80 mg/kg | 16–16 | 259–259 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 60–80 mg/kg | 20–20 | 306–306 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 80–100 mg/kg | 4–4 | 48–48 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 80–100 mg/kg | 8–8 | 110–110 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 80–100 mg/kg | 12–12 | 167–167 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 80–100 mg/kg | 16–16 | 219–219 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 80–100 mg/kg | 20–20 | 266–266 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 100–120 mg/kg | 4–4 | 8–8 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 100–120 mg/kg | 8–8 | 70–70 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 100–120 mg/kg | 12–12 | 127–127 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 100–120 mg/kg | 16–16 | 179–179 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 100–120 mg/kg | 20–20 | 226–226 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 120–160 mg/kg | 4–4 | 0–0 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 120–160 mg/kg | 8–8 | 0–0 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 120–160 mg/kg | 12–12 | 47–47 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 120–160 mg/kg | 16–16 | 99–99 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 120–160 mg/kg | 20–20 | 146–146 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 160–— mg/kg | 4–4 | 0–0 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 160–— mg/kg | 8–8 | 0–0 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 160–— mg/kg | 12–12 | 0–0 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 160–— mg/kg | 16–16 | 19–19 | — | FERTASA Handbook 5.12.2 Table 2 |
| K | Ambic | 160–— mg/kg | 20–20 | 66–66 | — | FERTASA Handbook 5.12.2 Table 2 |
| P | Bray-1 | 0–4 mg/kg | 4–4 | 93–93 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 8–8 | 118–118 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 12–12 | 145–145 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 16–16 | 183–183 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 20–20 | 228–228 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 4–4 | 121–121 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 8–8 | 153–153 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 12–12 | 189–189 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 16–16 | 237–237 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 20–20 | 296–296 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 4–4 | 73–73 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 8–8 | 98–98 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 12–12 | 125–125 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 16–16 | 163–163 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 20–20 | 208–208 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 4–4 | 95–95 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 8–8 | 127–127 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 12–12 | 163–163 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 16–16 | 211–211 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 4–8 mg/kg | 20–20 | 270–270 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 4–4 | 33–33 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 8–8 | 58–58 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 12–12 | 85–85 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 16–16 | 123–123 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 20–20 | 168–168 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 4–4 | 43–43 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 8–8 | 75–75 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 12–12 | 111–111 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 16–16 | 159–159 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 8–16 mg/kg | 20–20 | 218–218 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 4–4 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 8–8 | 18–18 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 12–12 | 45–45 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 16–16 | 83–83 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 20–20 | 128–128 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 4–4 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 8–8 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 12–12 | 7–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 16–16 | 55–55 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 16–24 mg/kg | 20–20 | 114–114 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 4–4 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 8–8 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 12–12 | 5–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 16–16 | 43–43 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 20–20 | 88–88 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 4–4 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 8–8 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 12–12 | 7–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 16–16 | 55–55 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 24–32 mg/kg | 20–20 | 114–114 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 4–4 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 8–8 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 12–12 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 16–16 | 3–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 20–20 | 48–48 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 4–4 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 8–8 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 12–12 | 0–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 16–16 | 3–10 | — | FERTASA Handbook 5.12.2 Table 1 |
| P | Bray-1 | 32–— mg/kg | 20–20 | 62–62 | — | FERTASA Handbook 5.12.2 Table 1 |
| S | — | —–— — | 4–8 | 25–25 | — | FERTASA Handbook 5.12.2.7 |
| S | — | —–— — | 8–16 | 30–30 | — | FERTASA Handbook 5.12.2.7 |
| S | — | —–— — | 16–— | 40–40 | — | FERTASA Handbook 5.12.2.7 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| P | Top 150-200mm stem + leaves | Early flowering | — | 0.35–— | — | 5.3.4 |
| K | Top 150-200mm | Early flowering | — | 2.2–— | — | 5.3.4 |
| Ca | Top 150-200mm | Early flowering | — | 0.8–— | — | 5.3.4 |
| Mg | Top 150-200mm | Early flowering | — | 0.4–— | — | 5.3.4 |
| **S** | — | — | — | — | — | _needs source_ |
| B | Top 150-200mm | Early flowering | — | 30–— | — | 5.3.4 |
| Zn | Top 150-200mm | Early flowering | — | 15–— | — | 5.3.4 |
| **Fe** | — | — | — | — | — | _needs source_ |
| Mn | Top 150-200mm | Early flowering | — | 25–— | — | 5.3.4 |
| Cu | Top 150-200mm | Early flowering | — | 7–— | — | 5.3.4 |
| Mo | Top 150-200mm | Early flowering | — | 0.5–— | — | 5.3.4 |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| total | kg/t dry matter | — | 2.7 | 21 | — | — | — | 5.12.2 |
| fresh | kg per t DM | — | 2.7 | 21 | 13 | 2.7 | 2.7 | NWPG SA — Planted Pasture & Lucerne Production |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 establishment | 0–1 | 0.4 | 1 | 0.7 | 0.5 | FERTASA 5.12.2.4: 25-55 kg N starter only year. T1. |
| Year 2 first full | 1–2 | 0.85 | 1 | 1 | 1 | UC ANR 8287: 2nd year full P+K demand; 0% N. T1+T2. |
| Year 3+ mature | 2–6 | 1 | 1 | 1 | 1 | FERTASA 5.12.2: mature stand; no N. T1. |
| Stand decline | 7–99 | 1 | 1 | 1 | 1 | UC ANR 8287: rotate before yields drop <70%. T2. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Karoo / Western Cape | rainfed | 5 | 8 | 10 | t DM/ha | van Heerden 1993 IGC |
| — | Northern Cape / W Free State | irrigated | 15 | 20 | 30 | t DM/ha | Farmer's Weekly W Free State; SA Lucerne industry |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.12.2 | 5.12.2 | 2017 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['P', 'K', 'Ca', 'Mg', 'S'] | After each cut; primary method | — |
| fertigation | False | ['N', 'K', 'S'] | When under pivot; N only if stand is thin | — |
| foliar | False | ['B', 'Mo', 'Fe', 'Mn'] | B for persistence; Mo for fixation | — |



### Macadamia

<a id="macadamia"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 4 |
| Yield unit | t NIS/ha |
| Population / ha | 312 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 18 |
| P | 1.2 |
| K | 12 |
| Ca | 10 |
| Mg | 1.5 |
| S | 5 |
| B | 0.35 |
| Zn | 0.35 |
| Fe | 0.75 |
| Mn | 0.75 |
| Cu | 0.065 |
| Mo | 0.02 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4 | 4.5 | 5.5 | 6 | FERTASA 5.8.1 (2017 rev) Table 5.8.1.2: target 4.5-5.5. T1. |
| pH (H2O) | 5 | 5.5 | 6.5 | 7 | FERTASA 5.8.1 Table 5.8.1.2 + ARC-ITSC: at least 5.5-6.5. T1. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 30 | 50 | FERTASA 5.8.1: target 30 mg/kg; >50 detrimental (depresses Fe/Zn). T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| P (Olsen) | — | 10 | 20 | — | FERTASA 5.8.1 Table 5.8.1.2: Resin/Olsen-P = 10-20 mg/kg. T1. |
| K | — | 85 | 145 | — | SAMAC young-tree deck (Schoeman): mac-specific K in soil solution thresholds. < 85 mg/kg = mac requires K supplement. 85-145 = sufficient. > 145 may cause Mg antagonism. |
| Ca | 250 | 400 | 1000 | 1500 | FERTASA 5.8.1: 400-1000 sufficient, 1500 = 7.5% of Total CEC. Manson & Sheard 600-1500 mg/L. T1. |
| Mg | 60 | 100 | 200 | 210 | FERTASA 5.8.1: 100-200 sufficient, 210 = 15% of Total CEC. T1. |
| S | — | 10 | 20 | — | FERTASA 5.8.1 Table 5.8.1.2: sulphate-S phosphate extraction = 20 mg/kg. T1. |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.8 | 1.5 | 2.5 | Elevated B requirement; B deficiency causes blank nuts and poor set. |
| Zn | 0.8 | 2 | 6 | 12 | Elevated Zn requirement for nut development and tree health. |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| Org C | 0.8 | 1.5 | 4 | — | FERTASA 5.8.1 p.406: <1.5% urgent; 4% ideal. Manson & Sheard 2007 Table 8: 2-6%. T1. |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `Acid Saturation`, `Ca:Mg`, `N (mineral)`, `P (Ambic)`, `P (Bray-2)`

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest + flower initiation | 3–5 | 1 | 25 | 20 | 10 | 25 | 15 | broadcast | FERTASA 5.8.1 direct: N supplemented Mar-Oct only; flower init May. K winter-early-summer. |
| 2 | Pre-flowering & main flowering | 6–9 | 2 | 45 | 40 | 50 | 50 | 25 | broadcast | FERTASA 5.8.1: main flowering Aug-Sep; K peak Oct-Dec starts here. Peak N window while still allowed. |
| 3 | Nut set (last N window) | 10–10 | 1 | 30 | 40 | 40 | 15 | 35 | fertigation | FERTASA 5.8.1: nut set Sep-Oct; last N dose before Nov-Feb cutoff. K at its peak per "Oct-Dec". |
| 4 | Nut growth + oil accumulation (NO N) | 11–2 | 0 | 0 | 0 | 0 | 10 | 25 | broadcast | FERTASA 5.8.1 explicit: Nov-Feb has NO applied N. "Vegetative growth hampers nut growth and oil accumulation." |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| B | — | —–— — | 0–— | 6–23 | — | SAMAC / Schoeman Schoeman 2021 - Application norms |
| K | — | —–— — | 0–— | 156–180 | — | SAMAC / Schoeman Schoeman 2021 - Application norms |
| N | — | —–— — | 0–— | 126–166 | — | SAMAC / Schoeman Schoeman 2021 - Application norms |
| P | — | —–— — | 0–— | 26–32 | — | SAMAC / Schoeman Schoeman 2021 - Application norms |
| Zn | — | —–— — | 0–— | 8–41 | — | SAMAC / Schoeman Schoeman 2021 - Application norms |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 1.19 | 1.2–1.59 | 2 | 5.8.1 |
| P | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 0.06 | 0.07–0.09 | 0.16 | 5.8.1 |
| K | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 0.49 | 0.5–0.7 | 1.21 | 5.8.1 |
| Ca | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 0.5 | 0.6–0.9 | 1.2 | 5.8.1 |
| Mg | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 0.08 | 0.09–0.11 | 0.21 | 5.8.1 |
| S | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 0.19 | 0.2–0.3 | — | 5.8.1 |
| B | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 49 | 50–90 | — | 5.8.1 |
| Zn | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 14 | 15–50 | — | 5.8.1 |
| Fe | 3rd-4th pair from growth tip on primary branch | Oct-Nov | — | 25–200 | — | 5.8.1 |
| Mn | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 149 | 150–1000 | 3600 | 5.8.1 |
| Cu | 3rd-4th pair from growth tip on primary branch | Oct-Nov | 4 | 5–12 | — | 5.8.1 |
| **Mo** | — | — | — | — | — | _needs source_ |

_Extra leaf rows outside the canonical element set:_ `Cl`, `Na`

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| nuts | kg/t NIS | 12 | 0.8 | 8 | 6 | 1 | 3 | 5.8.1 |
| husk | kg/t NIS | 6 | 0.4 | 4 | 4 | 0.5 | 2 | 5.8.1 |
| total | kg/t NIS | 18 | 1.2 | 12 | 10 | 1.5 | 5 | 5.8.1 |
| total trace (nuts+husks) | kg/t DNIS | — | — | — | — | — | — | Schoeman 2017 SAMAC FERTASA Symposium |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.15 | 0.14 | 0.15 | 0.13 | Manson & Sheard 2007 Table 6: 50 g N/tree vs mature 360 g = 0.14. T1. |
| Year 2 | 2–2 | 0.25 | 0.22 | 0.25 | 0.4 | Manson & Sheard 2007 Table 6: 80 g N/tree = 0.22; K demand ramps fast. T1. |
| Year 3-5 | 3–5 | 0.4 | 0.36 | 0.4 | 0.59 | Manson & Sheard 2007 Table 6: 130 g N/tree = 0.36; 220 g K/tree = 0.59. T1. |
| Year 6-8 | 6–8 | 0.6 | 0.58 | 0.6 | 0.75 | Manson & Sheard 2007 Table 6: 210 g N/tree = 0.58; 280 g K/tree = 0.75. T1. |
| Year 9+ | 9–99 | 1 | 1 | 1 | 1 | Manson & Sheard 2007 Table 6: full bearing 360 g N/tree, 375 g K/tree. T1. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| Beaumont | — | irrigated | 3.5 | 5 | 7.5 | t NIS/ha | SAMAC Industry Statistics 2022; Schoeman 2021 SAMAC Day |
| Beaumont | — | fertigated | 4.5 | 6 | 8.5 | t NIS/ha | Schoeman 2021 SAMAC Day intensive Levubu/Nelspruit blocks |
| Beaumont | — | rainfed | — | 2.5 | — | t NIS/ha | Manson & Sheard 2007 (KZN Midlands dryland reference) |
| A4 | — | irrigated | 2.5 | 3.5 | 5 | t NIS/ha | SAMAC Industry Statistics 2022; Schoeman 2021 cultivar comparison |
| A4 | — | fertigated | 3 | 4.5 | 6 | t NIS/ha | Schoeman 2021 SAMAC Day intensive blocks |
| A4 | — | rainfed | — | 2 | — | t NIS/ha | Manson & Sheard 2007 |
| 816 | — | irrigated | 2.5 | 3.5 | 5 | t NIS/ha | SAMAC Industry Statistics 2022 |
| 816 | — | fertigated | 3 | 4.5 | 6 | t NIS/ha | Schoeman 2021 SAMAC Day |
| — | — | irrigated | 3 | 4 | 5.5 | t NIS/ha | SAMAC Industry Statistics 2022 national rolled mean |
| — | — | fertigated | 3.5 | 5 | 7 | t NIS/ha | SAMAC Industry Statistics 2022 top quartile |
| — | — | rainfed | 1.5 | 2.5 | 3.5 | t NIS/ha | Manson & Sheard 2007 dryland reference |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Primary method; 3-4 split applications. Heavy K and Ca demand during nut fill | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B'] | When irrigated; critical during nut development (Jan-Apr) | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu'] | Zn and B for set and nut quality; Fe on alkaline soils | — |



### Maize

<a id="maize"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 5 |
| Yield unit | t grain/ha |
| Population / ha | 60000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 25 |
| P | 4 |
| K | 5 |
| Ca | 3 |
| Mg | 2.5 |
| S | 2.5 |
| B | 0.05 |
| Zn | 0.1 |
| Fe | 0.2 |
| Mn | 0.1 |
| Cu | 0.02 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4 | 4.5 | 5.5 | 6.5 | FERTASA 5.4.4: ≥4.5; optimum 4.8-5.5. T1. |
| pH (H2O) | 4.5 | 5 | 6 | 7 | DERIVED from KCl + 0.5. T1 derived. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 40 | 80 | 120 | 300 | FERTASA 5.4.4: 80-120 sufficient. T1. |
| **Ca** | — | — | — | — | _needs source_ |
| Mg | — | 50 | 200 | — | FERTASA 5.4.4: ≥50 mg/kg explicitly. T1. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| Zn | 0.8 | 2 | 6 | 12 | Zn-sensitive crop; Zn deficiency widespread in SA maize production. |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `Acid Saturation`

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & emergence | 10–11 | 1 | 10 | 35 | 10 | 15 | 15 | band_place | Starter P; Zn important |
| 2 | Vegetative growth (V6-VT) | 11–1 | 2 | 40 | 25 | 25 | 25 | 25 | side_dress | Peak N for leaf area and ear size |
| 3 | Silking & pollination | 1–2 | 1 | 25 | 20 | 25 | 30 | 30 | fertigation | N for kernel number; B for silk; Zn for pollen |
| 4 | Grain fill & maturation | 2–4 | 1 | 25 | 20 | 40 | 30 | 30 | broadcast | K for kernel weight and stalk strength |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 10–29 mg/kg | 3–3 | 19–19 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 10–29 mg/kg | 4–4 | 28–28 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 10–29 mg/kg | 5–5 | 37–37 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 10–29 mg/kg | 6–6 | 46–46 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 10–29 mg/kg | 7–7 | 55–55 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 10–29 mg/kg | 10–10 | 82–82 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 10–29 mg/kg | 2–2 | 10–10 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 10–29 mg/kg | 8–8 | 64–64 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 10–29 mg/kg | 9–9 | 73–73 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 20–39 mg/kg | 2–2 | 0–0 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 20–39 mg/kg | 3–3 | 11–11 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 20–39 mg/kg | 4–4 | 20–20 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 20–39 mg/kg | 5–5 | 29–29 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 20–39 mg/kg | 6–6 | 38–38 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 20–39 mg/kg | 7–7 | 47–47 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 20–39 mg/kg | 8–8 | 56–56 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 20–39 mg/kg | 9–9 | 64–64 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 20–39 mg/kg | 10–10 | 73–73 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 40–59 mg/kg | 2–2 | 0–0 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 40–59 mg/kg | 3–3 | 5–5 | low-clay <25% | FERTASA Table 5.4.6 |
| K | NH4OAc | 40–59 mg/kg | 4–4 | 13–13 | low-clay <25% | FERTASA Table 5.4.6 |
| P | Bray-1 | 0–4 mg/kg | 2–2 | 20–20 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 3–3 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 5–5 | 88–88 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 6–6 | 109–109 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 7–7 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 9–9 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 4–4 | 65–65 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 8–8 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 10–10 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 2–2 | 17–17 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 3–3 | 31–31 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 5–5 | 63–63 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 7–7 | 90–90 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 9–9 | 95–95 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 10–10 | 97–97 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 4–4 | 47–47 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 6–6 | 67–67 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 8–8 | 93–93 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 2–2 | 13–13 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 6–6 | 50–50 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 7–7 | 59–59 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 9–9 | 67–67 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 10–10 | 68–68 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 3–3 | 19–19 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 4–4 | 30–30 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 5–5 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 8–8 | 64–64 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 2–2 | 10–10 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 3–3 | 13–13 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 5–5 | 29–29 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 6–6 | 36–36 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 7–7 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 8–8 | 47–47 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 9–9 | 50–50 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 4–4 | 21–21 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 10–10 | 53–53 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 3–3 | 10–10 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 4–4 | 15–15 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 5–5 | 19–19 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 9–9 | 38–38 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 10–10 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 2–2 | 7–7 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 6–6 | 26–26 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 7–7 | 31–31 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 8–8 | 34–34 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 3–3 | 9–9 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 5–5 | 15–15 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 7–7 | 22–22 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 9–9 | 27–27 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 2–2 | 6–6 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 4–4 | 12–12 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 6–6 | 18–18 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 8–8 | 24–24 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 10–10 | 30–30 | — | FERTASA Table 5.4.5 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Opposite/below ear leaf | Tasseling / silking | — | 3–— | — | 5.3.4 |
| P | Opposite/below ear leaf | Tasseling / silking | — | 0.25–— | — | 5.3.4 |
| K | Opposite/below ear leaf | Tasseling / silking | — | 1.9–— | — | 5.3.4 |
| Ca | Opposite/below ear leaf | Tasseling / silking | — | 0.4–— | — | 5.3.4 |
| Mg | Opposite/below ear leaf | Tasseling / silking | — | 0.25–— | — | 5.3.4 |
| **S** | — | — | — | — | — | _needs source_ |
| B | Opposite/below ear leaf | Tasseling / silking | 10 | 10–— | — | 5.3.4 |
| Zn | Opposite/below ear leaf | Tasseling / silking | — | 15–— | — | 5.3.4 |
| Fe | Opposite/below ear leaf | Tasseling / silking | — | 25–— | — | 5.3.4 |
| Mn | Opposite/below ear leaf | Tasseling / silking | — | 15–— | — | 5.3.4 |
| Cu | Opposite/below ear leaf | Tasseling / silking | — | 5–— | — | 5.3.4 |
| Mo | Opposite/below ear leaf | Tasseling / silking | — | 0.2–— | — | 5.3.4 |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| grain | kg per t grain | 15 | 3 | 4 | 0.5 | 1 | — | GrainSA Fertiliser Requirements; ARC-GCI Du Plessis Maize Production Guide |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Highveld | rainfed | 2.5 | 4.5 | 8 | t grain/ha | GrainSA archives |
| — | Vaalharts / Douglas | irrigated | 8 | 11 | 14 | t grain/ha | Pannar Irrigated Maize Mgmt; ARC-GCI |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

_No rows._



### Maize (dryland)

<a id="maize-dryland"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | Maize |
| Default yield | 5 |
| Yield unit | t grain/ha |
| Population / ha | 20000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 25 |
| P | 4 |
| K | 5 |
| Ca | 3 |
| Mg | 2.5 |
| S | 2 |
| B | 0.02 |
| Zn | 0.05 |
| Fe | 0.3 |
| Mn | 0.05 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4 | 4.5 | 5.5 | 6.5 | FERTASA 5.4.4: ≥4.5; optimum 4.8-5.5. T1. |
| pH (H2O) | 4.5 | 5 | 6 | 7 | DERIVED from KCl + 0.5. T1 derived. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 40 | 80 | 120 | 300 | FERTASA 5.4.4: 80-120 sufficient. T1. |
| **Ca** | — | — | — | — | _needs source_ |
| Mg | — | 50 | 200 | — | FERTASA 5.4.4: ≥50 mg/kg explicitly. T1. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `Acid Saturation`

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & emergence | 10–11 | 1 | 10 | 35 | 10 | 15 | 15 | band_place | Starter P; Zn important [aliased from Maize] |
| 2 | Vegetative growth (V6-VT) | 11–1 | 2 | 40 | 25 | 25 | 25 | 25 | side_dress | Peak N for leaf area and ear size [aliased from Maize] |
| 3 | Silking & pollination | 1–2 | 1 | 25 | 20 | 25 | 30 | 30 | fertigation | N for kernel number; B for silk; Zn for pollen [aliased from Maize] |
| 4 | Grain fill & maturation | 2–4 | 1 | 25 | 20 | 40 | 30 | 30 | broadcast | K for kernel weight and stalk strength [aliased from Maize] |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| P | Bray-1 | 0–4 mg/kg | 5–5 | 88–88 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 7–7 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 9–9 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 2–2 | 20–20 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 3–3 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 4–4 | 65–65 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 6–6 | 109–109 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 8–8 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 10–10 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 2–2 | 17–17 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 8–8 | 93–93 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 9–9 | 95–95 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 3–3 | 31–31 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 4–4 | 47–47 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 5–5 | 63–63 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 6–6 | 67–67 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 7–7 | 90–90 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 10–10 | 97–97 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 2–2 | 13–13 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 4–4 | 30–30 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 6–6 | 50–50 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 9–9 | 67–67 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 10–10 | 68–68 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 3–3 | 19–19 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 5–5 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 7–7 | 59–59 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 8–8 | 64–64 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 3–3 | 13–13 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 5–5 | 29–29 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 6–6 | 36–36 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 9–9 | 50–50 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 2–2 | 10–10 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 4–4 | 21–21 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 7–7 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 8–8 | 47–47 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 10–10 | 53–53 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 2–2 | 7–7 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 3–3 | 10–10 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 4–4 | 15–15 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 5–5 | 19–19 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 10–10 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 6–6 | 26–26 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 7–7 | 31–31 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 8–8 | 34–34 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 9–9 | 38–38 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 8–8 | 24–24 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 9–9 | 27–27 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 2–2 | 6–6 | — | FERTASA Table 5.4.5 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | mature leaf | mid-season | 0.1 | 0.1–2 | 5 | SCSB394. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S', 'Zn'] | At planting; starter band with seed | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant or topdress | — |
| side_dress | False | ['N', 'K', 'S'] | V6-V8 N topdress; critical timing | — |
| foliar | False | ['Zn', 'B', 'Mn', 'Fe'] | Zn deficiency common on high-pH soils | — |



### Maize (irrigated)

<a id="maize-irrigated"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | Maize |
| Default yield | 12 |
| Yield unit | t grain/ha |
| Population / ha | 80000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 22 |
| P | 3.5 |
| K | 4.5 |
| Ca | 3 |
| Mg | 2.5 |
| S | 2 |
| B | 0.02 |
| Zn | 0.05 |
| Fe | 0.3 |
| Mn | 0.05 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4 | 4.5 | 5.5 | 6.5 | FERTASA 5.4.4: ≥4.5; optimum 4.8-5.5. T1. |
| pH (H2O) | 4.5 | 5 | 6 | 7 | DERIVED from KCl + 0.5. T1 derived. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 40 | 80 | 120 | 300 | FERTASA 5.4.4: 80-120 sufficient. T1. |
| **Ca** | — | — | — | — | _needs source_ |
| Mg | — | 50 | 200 | — | FERTASA 5.4.4: ≥50 mg/kg explicitly. T1. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `Acid Saturation`

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & establishment | 9–10 | 1 | 15 | 80 | 60 | 25 | 25 | band_place | FERTASA 5.4.4: all P + K pre-plant/at planting. Sandy FS soils: split planting-N further (seedbed salt-burn limit). |
| 2 | Early vegetative (V4-V6) | 10–11 | 1 | 25 | 10 | 15 | 20 | 20 | fertigation | FERTASA 5.4.4: before 5-6 weeks post-emergence is the side-dress window. |
| 3 | Late vegetative / pre-tassel (V8-VT) | 11–12 | 1 | 30 | 5 | 15 | 20 | 20 | fertigation | FERTASA 5.4.4: N-K uptake peaks 2 weeks before flowering. |
| 4 | Silking & grain fill (R1-R3) | 12–1 | 1 | 20 | 3 | 7 | 20 | 20 | fertigation | FERTASA 5.4.4: P-uptake peaks at flowering. On >10 t/ha yields add 20-30 kg N/additional ton. |
| 5 | Late grain fill to maturity (R4-R6) | 2–3 | 0 | 10 | 2 | 3 | 15 | 15 | fertigation | FERTASA 5.4.4: uptake tapers post-flowering. |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| P | Bray-1 | 0–4 mg/kg | 2–2 | 20–20 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 6–6 | 109–109 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 8–8 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 0–4 mg/kg | 10–10 | 130–130 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 3–3 | 31–31 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 5–5 | 63–63 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 7–7 | 90–90 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 5–7 mg/kg | 9–9 | 95–95 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 2–2 | 13–13 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 4–4 | 30–30 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 7–7 | 59–59 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 8–8 | 64–64 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 10–10 | 68–68 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 3–3 | 19–19 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 5–5 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 6–6 | 50–50 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 8–14 mg/kg | 9–9 | 67–67 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 4–4 | 21–21 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 6–6 | 36–36 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 7–7 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 9–9 | 50–50 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 2–2 | 10–10 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 3–3 | 13–13 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 5–5 | 29–29 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 8–8 | 47–47 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 15–20 mg/kg | 10–10 | 53–53 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 9–9 | 38–38 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 2–2 | 7–7 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 4–4 | 15–15 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 5–5 | 19–19 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 7–7 | 31–31 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 3–3 | 10–10 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 6–6 | 26–26 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 8–8 | 34–34 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 21–27 mg/kg | 10–10 | 42–42 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 2–2 | 6–6 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 5–5 | 15–15 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 6–6 | 18–18 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 7–7 | 22–22 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 8–8 | 24–24 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 3–3 | 9–9 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 4–4 | 12–12 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 9–9 | 27–27 | — | FERTASA Table 5.4.5 |
| P | Bray-1 | 28–34 mg/kg | 10–10 | 30–30 | — | FERTASA Table 5.4.5 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | mature leaf | mid-season | 0.1 | 0.1–2 | 5 | SCSB394. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S', 'Zn'] | At planting; starter band | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| side_dress | False | ['N', 'K', 'S'] | V6-V8 N topdress | — |
| fertigation | False | ['N', 'K', 'S'] | Under pivot or drip; spoon-feed N through season | — |
| foliar | False | ['Zn', 'B', 'Mn', 'Fe'] | Zn deficiency common on high-pH soils | — |



### Mango

<a id="mango"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 15 |
| Yield unit | t fruit/ha |
| Population / ha | 400 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 6 |
| P | 0.8 |
| K | 8 |
| Ca | 1.2 |
| Mg | 0.8 |
| S | 0.4 |
| B | 0.06 |
| Zn | 0.04 |
| Fe | 0.12 |
| Mn | 0.04 |
| Cu | 0.015 |
| Mo | 0.008 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 5 | 5.5 | 6 | 7 | DERIVED from Quaggio 1996 H2O − 0.5. T2 derived. |
| pH (H2O) | 5.5 | 6 | 6.5 | 7.5 | Quaggio 1996 IAC Tech Bull 100 + Galan Sauco 2020. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 6 | 12 | 25 | 40 | Galan Sauco 2020 Mango Tab + Quaggio 1996 IAC. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 60 | 120 | 240 | 480 | Quaggio 1996 (cmolc converted to mg/kg). T2. |
| Ca | 400 | 800 | 1600 | 2400 | Quaggio 1996 (cmolc 2-4-8-12 converted). T2. |
| Mg | 60 | 120 | 360 | 600 | Quaggio 1996. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest & vegetative flush | 3–5 | 2 | 25 | 25 | 15 | 20 | 20 | broadcast | Encourage new growth for next season's fruiting wood |
| 2 | Flower induction & dormancy | 6–7 | 1 | 5 | 15 | 15 | 15 | 15 | foliar | Avoid N — triggers vegetative growth instead of flowering |
| 3 | Flowering & fruit set | 8–9 | 2 | 20 | 25 | 20 | 25 | 25 | fertigation | B foliar for fruit set; moderate N |
| 4 | Fruit development | 10–12 | 3 | 30 | 25 | 35 | 25 | 25 | fertigation | High K for fruit size, colour, sugar content |
| 5 | Harvest | 1–2 | 1 | 20 | 10 | 15 | 15 | 15 | fertigation | Light feeding during harvest period |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 6-8 mo old leaf, last mature flush | Pre-flowering or post-harvest | — | 1.2–1.4 | 1.6 | Quaggio 1996 + Reuter & Robinson 1986 (cited via Galan Sauco 2020 Tbl 6) |
| P | 6-8 mo old leaf | Pre-flowering or post-harvest | — | 0.08–0.16 | 0.25 | Quaggio 1996 + Haifa Mango Fertilization |
| K | 6-8 mo old leaf | Pre-flowering or post-harvest | — | 0.5–1 | 1.2 | Quaggio 1996 + Haifa Mango |
| Ca | 6-8 mo old leaf | Pre-flowering or post-harvest | — | 2–3.5 | 5 | Quaggio 1996 + Haifa Mango |
| Mg | 6-8 mo old leaf | Pre-flowering or post-harvest | — | 0.25–0.5 | 0.8 | Quaggio 1996 + Haifa Mango |
| S | 6-8 mo old leaf | Pre-flowering or post-harvest | — | 0.09–0.18 | 0.25 | Quaggio 1996 + Hundal et al. 2005 DRIS |
| B | leaf | flowering | 25 | 30–100 | 150 | Mudo et al. 2020 + Pretest 2008 Acta Hort 509: B-critical for fruit set on Tommy Atkins. T3. |
| Zn | 6-8 mo old leaf | Pre-flowering or post-harvest | — | 20–40 | 100 | Quaggio 1996 + Haifa Mango |
| Fe | 6-8 mo old leaf | Pre-flowering or post-harvest | — | 50–200 | — | Quaggio 1996 + Haifa Mango |
| Mn | 6-8 mo old leaf | Pre-flowering or post-harvest | — | 50–100 | — | Quaggio 1996 + Haifa Mango |
| Cu | 6-8 mo old leaf | Pre-flowering or post-harvest | — | 10–20 | — | Quaggio 1996 + Haifa Mango (overlap 10-20) |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fresh fruit | 6.5 | 0.74 | 6.2 | 5.5 | 3 | — | A&L Handbook + Kynoch RSA via mango.org Lit Rev |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-2 | 0–2 | 0.2 | 0.2 | 0.25 | 0.15 | Establishment |
| Year 3-4 | 3–4 | 0.45 | 0.45 | 0.45 | 0.4 | First fruit possible |
| Year 5-7 | 5–7 | 0.7 | 0.7 | 0.7 | 0.65 | Increasing production |
| Year 8+ | 8–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Limpopo / Mpumalanga / KZN | irrigated | 8 | 12 | 25 | t fruit/ha | Haifa Mango + Galan Sauco 2020 |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | Mudo et al. 2020 + Pretest 2008 Acta Hort 509 | n/a | 2020 | 3 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Post-harvest and pre-bloom; avoid N during flower induction | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Zn', 'B'] | During fruit development when irrigated | — |
| foliar | False | ['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca', 'K'] | Zn critical; B for panicle development; KNO3 for flower induction | — |



### Nectarine

<a id="nectarine"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t fruit/ha |
| Population / ha | 500 |
| Years to bearing | 3 |
| Years to full bearing | 5 |
| N (target/uptake) | 4 |
| P | 0.5 |
| K | 5.5 |
| Ca | 1 |
| Mg | 0.5 |
| S | 0.3 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | — | 5.5 | 6.3 | 7 | DERIVED from H2O − 0.5. T2 (derived). |
| pH (H2O) | — | 6 | 6.8 | 7.5 | Cloned from Peach (same species P. persica). CDFA Peach & Nectarine + WSU. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 40 | 80 | Cloned from Peach. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 250 | 400 | Cloned from Peach. T2. |
| Ca | 300 | 600 | 2000 | 4000 | Cloned from Peach. T2. |
| Mg | 60 | 120 | 250 | 500 | Cloned from Peach. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 1.5 | 2.5 | Cloned from Peach. T2. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Dormancy | 5–6 | 0 | 0 | 5 | 5 | 5 | 5 | broadcast | Krige & Stassen 2008 Donnarine — identical biology to peach. |
| 2 | Bud break & bloom | 7–8 | 1 | 15 | 20 | 15 | 15 | 15 | fertigation | Same as peach. |
| 3 | Fruit set & pit hardening | 9–10 | 2 | 30 | 25 | 25 | 30 | 25 | fertigation | Same as peach. |
| 4 | Cell expansion & ripening | 11–1 | 3 | 30 | 25 | 40 | 30 | 30 | fertigation | Same as peach. |
| 5 | Post-harvest recovery | 2–4 | 1 | 25 | 25 | 15 | 20 | 25 | broadcast | Same as peach. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recently mature leaves | July-August | 2.7 | 2.7–3.5 | — | WSU Table 4 (via Peach) |
| P | Recently mature leaves | July-August | 0.1 | 0.1–0.3 | — | WSU Table 4 (via Peach) |
| K | Recently mature leaves | July-August | 1.2 | 1.2–3 | — | WSU Table 4 (via Peach) |
| Ca | Recently mature leaves | July-August | 1 | 1–2.5 | — | WSU Table 4 (via Peach) |
| Mg | Recently mature leaves | July-August | 0.25 | 0.25–0.5 | — | WSU Table 4 (via Peach) |
| S | Recently mature leaves | July-August | 0.2 | 0.2–0.4 | — | WSU Table 4 (via Peach) |
| B | Recently mature leaves | July-August | 20 | 20–80 | — | WSU Table 4 (via Peach) |
| Zn | Recently mature leaves | July-August | 20 | 20–50 | — | WSU Table 4 (via Peach) |
| Fe | Recently mature leaves | July-August | 120 | 120–200 | — | WSU Table 4 (via Peach) |
| Mn | Recently mature leaves | July-August | 20 | 20–200 | — | WSU Table 4 (via Peach) |
| Cu | Recently mature leaves | July-August | 4 | 4–16 | — | WSU Table 4 (via Peach) |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fresh fruit | 1.25 | 0.15 | 1.7 | 0.18 | 0.1 | — | CDFA Peach & Nectarine (treats them identically) |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape | irrigated | 12 | 25 | 45 | t fruit/ha | Hortgro Key Deciduous Fruit Statistics 2024 |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

_No rows._



### Oat

<a id="oat"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 3 |
| Yield unit | t grain/ha |
| Population / ha | 3000000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 20 |
| P | 3.5 |
| K | 5 |
| Ca | 0.6 |
| Mg | 1.4 |
| S | 2 |
| B | 0.015 |
| Zn | 0.03 |
| Fe | 0.2 |
| Mn | 0.04 |
| Cu | 0.007 |
| Mo | 0.004 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & emergence | 4–5 | 1 | 15 | 35 | 15 | 15 | 15 | band_place | Starter P |
| 2 | Tillering & vegetative | 6–7 | 2 | 40 | 25 | 25 | 25 | 25 | broadcast | Peak N for tiller number |
| 3 | Heading & flowering | 8–9 | 1 | 25 | 20 | 25 | 30 | 30 | broadcast | B for grain set |
| 4 | Grain fill & maturity | 10–11 | 1 | 20 | 20 | 35 | 30 | 30 | broadcast | K for test weight |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | mature leaf | mid-season | 0.1 | 0.1–2 | 5 | SCSB394 small grains. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| grain | kg/t grain | 20 | 3.5 | 5 | 0.6 | 1.4 | 2 | 5.6 |
| straw | kg/t grain | 6 | 1 | 14 | 3 | 1.2 | 1.5 | 5.6 |
| total | kg/t grain | 26 | 4.5 | 19 | 3.6 | 2.6 | 3.5 | 5.6 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

_No rows._



### Olive

<a id="olive"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 8 |
| Yield unit | t fruit/ha |
| Population / ha | 400 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 12 |
| P | 1.5 |
| K | 15 |
| Ca | 3 |
| Mg | 1.5 |
| S | 0.8 |
| B | 0.1 |
| Zn | 0.05 |
| Fe | 0.2 |
| Mn | 0.06 |
| Cu | 0.02 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 6 | 6.5 | 7 | 7.8 | UC Davis Geisseler Olives + SA Olive Association: calcicole. T2. |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | — | 125 | — | — | CDFA: pre-plant minimum 125 ppm K for new orchards (per Vossen). |
| Ca | — | 1500 | 4000 | — | UC Davis Geisseler (calcicole; deficiency rare). T2. |
| Mg | 60 | 100 | 250 | 500 | Fernandez-Escobar 2011. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | — | 0.33 | — | 2 | CDFA: hot-water soil B below 0.33 = deficient (older literature used 0.5). Above 2 ppm saturated paste = toxicity risk. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest recovery | 6–7 | 1 | 10 | 10 | 5 | 5 | 5 | broadcast | Recovery; flower initiation prep |
| 2 | Winter rest & flower initiation | 8–9 | 1 | 15 | 20 | 15 | 15 | 15 | broadcast | B for flower differentiation |
| 3 | Bloom & fruit set | 10–11 | 2 | 20 | 25 | 20 | 25 | 25 | fertigation | B critical for set |
| 4 | Fruit growth & oil accumulation | 12–2 | 2 | 35 | 30 | 30 | 30 | 30 | fertigation | K for oil content |
| 5 | Maturation & harvest | 3–5 | 1 | 20 | 15 | 30 | 25 | 25 | broadcast | K for oil quality |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | — | —–— — | 0–— | 70–93 | — | CDFA FREP Olive Guideline K removal reference (irrigated) |
| N | — | —–— — | 0–— | 44.8–112.1 | — | CDFA FREP Olive Guideline SHD (super-high density) |
| N | — | —–— — | 0–— | 48.2–95.3 | — | CDFA FREP Olive Guideline Traditional density ~85 trees/ac |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recently mature leaves | July | 1.4 | 1.5–2 | 2 | CDFA FREP Olive Guideline |
| P | Recently mature leaves | July | 0.1 | 0.1–0.3 | — | CDFA FREP Olive Guideline |
| K | Recently mature leaves | July | 0.4 | 0.8–— | — | CDFA FREP Olive Guideline |
| Ca | mid-shoot leaf | July (NH winter rest) | 1 | 1–2.5 | 4 | Fernandez-Escobar 2011 J Plant Nutr + IFAPA Spain Olivar protocol. T2. |
| Mg | mid-shoot leaf | July (NH winter rest) | 0.08 | 0.1–0.3 | 1 | Fernandez-Escobar 2011 J Plant Nutr + IFAPA Spain Olivar protocol. T2. |
| S | mid-shoot leaf | July (NH winter rest) | 0.1 | 0.1–0.15 | — | Fernandez-Escobar 2011 J Plant Nutr + IFAPA Spain Olivar protocol. T2. |
| B | Recently mature leaves | July | 14 | 19–150 | 185 | CDFA FREP Olive Guideline |
| Zn | mid-shoot leaf | July (NH winter rest) | 10 | 10–30 | 80 | Fernandez-Escobar 2011 J Plant Nutr + IFAPA Spain Olivar protocol. T2. |
| Fe | mid-shoot leaf | July (NH winter rest) | 80 | 90–200 | — | Fernandez-Escobar 2011 J Plant Nutr + IFAPA Spain Olivar protocol. T2. |
| Mn | mid-shoot leaf | July (NH winter rest) | 20 | 20–150 | 1000 | Fernandez-Escobar 2011 J Plant Nutr + IFAPA Spain Olivar protocol. T2. |
| Cu | mid-shoot leaf | July (NH winter rest) | 4 | 4–15 | — | Fernandez-Escobar 2011 J Plant Nutr + IFAPA Spain Olivar protocol. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit (irrigated) | kg per t fresh fruit | 2.7 | 0.59 | 6.6 | 5 | 0.45 | — | CDFA Olive + UC Davis Geisseler Olives |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-3 | 0–2 | 0.25 | 0.25 | 0.3 | 0.2 | Establishment |
| Year 4-6 | 3–5 | 0.55 | 0.55 | 0.6 | 0.5 | Early bearing |
| Year 7-9 | 6–8 | 0.8 | 0.8 | 0.8 | 0.75 | Pre-mature bearing |
| Year 10+ | 9–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape | irrigated | 5 | 8 | 20 | t fruit/ha | SA Olive Association Olive Growing |
| — | Western Cape | rainfed | 2 | 3 | 4 | t fruit/ha | SA Olive Association Olive Growing |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | All stages; primary for dryland | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'B'] | When irrigated | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu'] | B critical for fruit set | — |



### Onion

<a id="onion"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 50 |
| Yield unit | t bulb/ha |
| Population / ha | 750000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3 |
| P | 0.5 |
| K | 3.5 |
| Ca | 0.4 |
| Mg | 0.2 |
| S | 0.3 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Transplant & establishment | 3–4 | 1 | 15 | 35 | 10 | 15 | 15 | band_place | P for root recovery |
| 2 | Leaf growth | 5–7 | 2 | 40 | 25 | 25 | 25 | 25 | side_dress | N for leaf number = bulb size |
| 3 | Bulb initiation & fill | 8–10 | 2 | 30 | 25 | 40 | 35 | 35 | fertigation | K and S for quality |
| 4 | Maturation & harvest | 10–12 | 1 | 15 | 15 | 25 | 25 | 25 | broadcast | Reduce N; K for storage |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 140–140 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 150–180 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 120–120 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 90–90 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | most-recent mature leaf | pre bulb enlargement | 3 | 3.1–4.27 | 5 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| P | most-recent mature leaf | pre bulb enlargement | 0.2 | 0.26–0.48 | 0.6 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| K | most-recent mature leaf | pre bulb enlargement | 1.5 | 1.98–4.22 | 5 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| Ca | most-recent mature leaf | pre bulb enlargement | 0.7 | 0.9–1.84 | 2.5 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| Mg | most-recent mature leaf | pre bulb enlargement | 0.1 | 0.16–0.32 | 0.5 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| S | most-recent mature leaf | pre bulb enlargement | 0.1 | 0.15–0.57 | 0.8 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| B | most-recent mature leaf | pre bulb enlargement | 5 | 6–15 | 30 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| Zn | most-recent mature leaf | pre bulb enlargement | 12 | 16–45 | 100 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| **Fe** | — | — | — | — | — | _needs source_ |
| Mn | most-recent mature leaf | pre bulb enlargement | 30 | 51–149 | 300 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| Cu | most-recent mature leaf | pre bulb enlargement | 4 | 5–28 | 50 | SCSB#394 p.83 Vidalia Onion (Caldwell 1991, Pankov 1984). T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| dry bulb | — | irrigated | 30 | 70 | 110 | t bulb/ha | Starke Ayres Onion Production Guideline 2019 |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | DAFF Onion Production Guide + Starke Ayres 2019 | n/a | 2019 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At planting | — |
| broadcast | False | ['P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| side_dress | False | ['N', 'K', 'S'] | Bulb initiation topdress; stop N 6 weeks before harvest | — |
| fertigation | False | ['N', 'K', 'S'] | When irrigated | — |
| foliar | False | ['Cu', 'B', 'Mn'] | Cu for disease resistance | — |



### Passion Fruit

<a id="passion-fruit"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 15 |
| Yield unit | t fruit/ha |
| Population / ha | 1000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 6 |
| P | 0.7 |
| K | 7 |
| Ca | 1.2 |
| Mg | 0.6 |
| S | 0.35 |
| B | 0.06 |
| Zn | 0.04 |
| Fe | 0.12 |
| Mn | 0.04 |
| Cu | 0.015 |
| Mo | 0.008 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.4 | 4.9 | 5.9 | 6.4 | DERIVED from H2O − 0.6 offset. T2 (derived). |
| pH (H2O) | 5 | 5.5 | 6.5 | 7 | Borges & Lima 2003 Embrapa Maracujazeiro + Yara Passion Fruit. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 8 | 15 | 30 | 60 | Borges & Lima 2003 Embrapa. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 120 | 250 | 400 | Borges & Lima 2003. T2. |
| Ca | 500 | 800 | 2500 | 5000 | Borges et al. 2006 Rev Bras Frut 28. T2. |
| Mg | 80 | 120 | 250 | 400 | Borges et al. 2006. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest & pruning | 5–6 | 1 | 10 | 10 | 5 | 5 | 5 | broadcast | Clean up and light feeding |
| 2 | Vegetative regrowth | 7–9 | 2 | 30 | 25 | 20 | 20 | 20 | fertigation | N for vine growth |
| 3 | Flowering & fruit set | 10–11 | 2 | 20 | 25 | 25 | 25 | 25 | fertigation | B for pollination |
| 4 | Fruit development | 12–2 | 2 | 25 | 25 | 25 | 30 | 30 | fertigation | Ca for rind; K for juice |
| 5 | Ripening & harvest | 3–4 | 1 | 15 | 15 | 25 | 20 | 20 | fertigation | K for sugar and flavour |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 4th leaf from apex on fruiting branch | fruit development | 4 | 4.5–5.5 | 6 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| P | 4th leaf from apex on fruiting branch | fruit development | 0.2 | 0.25–0.35 | 0.45 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| K | 4th leaf from apex on fruiting branch | fruit development | 1.5 | 2–3 | 4 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| Ca | 4th leaf from apex on fruiting branch | fruit development | 1.5 | 2–3.5 | 4.5 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| Mg | 4th leaf from apex on fruiting branch | fruit development | 0.25 | 0.3–0.5 | 0.7 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| S | 4th leaf from apex on fruiting branch | fruit development | 0.25 | 0.3–0.5 | 0.7 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| B | 4th leaf from apex on fruiting branch | fruit development | 30 | 35–80 | 120 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| Zn | 4th leaf from apex on fruiting branch | fruit development | 25 | 30–60 | 100 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| Fe | 4th leaf from apex on fruiting branch | fruit development | 100 | 120–250 | 400 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| Mn | 4th leaf from apex on fruiting branch | fruit development | 80 | 100–250 | 500 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| Cu | 4th leaf from apex on fruiting branch | fruit development | 5 | 7–15 | 25 | Embrapa Borges & Lima 2003 + Carvalho et al. 2002 Rev Bras Frut 24:469. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit (yellow) | kg/t fresh fruit | 3.5 | 0.45 | 6 | 0.6 | 0.3 | 0.3 | Migration 112 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.5 | 0.55 | 0.55 | 0.45 | Borges & Lima 2003. First-year vine — 50-60% of mature N supports vine + first crop. 2-3 year economic life. |
| Year 2 | 2–2 | 1 | 1 | 1 | 1 | Borges & Lima 2003 — full bearing. |
| Year 3 | 3–3 | 1 | 1 | 1 | 1 | Borges & Lima 2003 — full bearing; some decline. |
| Year 4+ | 4–99 | 1 | 1 | 1 | 1 | Borges & Lima 2003 — vine still bearing; economic-life decision is management, not engine scaling. Test_programme_data_integrity expects monotonic curves. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| Yellow | Brazil | irrigated | 25 | 35 | 50 | t fresh fruit/ha | Embrapa Borges & Lima 2003. |
| Purple Granadilla | SA Mpumalanga | irrigated | 12 | 15 | 25 | t fresh fruit/ha | DAFF Granadilla Production Guide 2010. |
| Yellow | SA Lowveld | irrigated | 15 | 20 | 30 | t fresh fruit/ha | ARC LNR Nelspruit subtrop bulletin. |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| fertigation | True | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B'] | Primary method; vines need regular feeding | — |
| broadcast | False | ['P', 'Ca', 'Mg', 'S'] | Base amendments | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu'] | Micronutrient correction | — |



### Pea

<a id="pea"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 2 |
| Yield unit | t seed/ha |
| Population / ha | 800000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 35 |
| P | 5 |
| K | 18 |
| Ca | 3.5 |
| Mg | 2 |
| S | 2.5 |
| B | 0.04 |
| Zn | 0.05 |
| Fe | 0.3 |
| Mn | 0.06 |
| Cu | 0.012 |
| Mo | 0.008 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Emergence & establishment | 4–5 | 1 | 15 | 35 | 10 | 15 | 15 | band_place | P for nodulation |
| 2 | Vegetative growth | 6–7 | 1 | 25 | 25 | 25 | 25 | 25 | side_dress | N-fixation active |
| 3 | Flowering & pod set | 7–8 | 2 | 30 | 20 | 30 | 30 | 30 | fertigation | B for retention; K for quality |
| 4 | Pod fill & harvest | 9–10 | 1 | 30 | 20 | 35 | 30 | 30 | broadcast | K for sweetness |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | GRDC GrowNote Field Pea + AHDB UK | n/a | 2018 | 2 | — |

**Application methods** (`crop_application_methods`)

_No rows._



### Pea (Green)

<a id="pea-green"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 5 |
| Yield unit | t pod/ha |
| Population / ha | 400000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 5 |
| P | 0.7 |
| K | 6 |
| Ca | 1.5 |
| Mg | 0.4 |
| S | 0.5 |
| B | 0.008 |
| Zn | 0.008 |
| Fe | 0.04 |
| Mn | 0.008 |
| Cu | 0.003 |
| Mo | 0.002 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | DAFF Vegetable Production Guide + UF/IFAS HS725 | 5.6.1 | 2011 | 1 | — |

**Application methods** (`crop_application_methods`)

_No rows._



### Peach

<a id="peach"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 30 |
| Yield unit | t fruit/ha |
| Population / ha | 1000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4 |
| P | 0.5 |
| K | 5.5 |
| Ca | 1 |
| Mg | 0.5 |
| S | 0.3 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | — | 5.5 | 6.3 | 7 | DERIVED from H2O − 0.5. T2 (derived). |
| pH (H2O) | — | 6 | 6.8 | 7.5 | CDFA Peach & Nectarine + WSU Tree Fruit. T2 cross-confirmed. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 40 | 80 | CDFA Peach & Nectarine + WSU. T2 cross-confirmed. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 250 | 400 | CDFA Peach + WSU (NH4OAc). T2 cross-confirmed. |
| Ca | 300 | 600 | 2000 | 4000 | CDFA Peach (peach less Ca-sensitive than pome — pit-split is partition-driven). T2. |
| Mg | 60 | 120 | 250 | 500 | CDFA Peach. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 1.5 | 2.5 | CDFA Peach. Peach B-sensitive — lower toxicity ceiling than pome. T2. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Dormancy | 5–6 | 0 | 0 | 5 | 5 | 5 | 5 | broadcast | CDFA: N uptake minimal during dormancy. |
| 2 | Bud break & bloom | 7–8 | 1 | 15 | 20 | 15 | 15 | 15 | fertigation | Haifa: ~15% K at leaf emergence, 20% at flowering. |
| 3 | Fruit set & cell division (incl pit hardening) | 9–10 | 2 | 30 | 25 | 25 | 30 | 25 | fertigation | Compressed 90-day bloom→harvest window. |
| 4 | Cell expansion & ripening | 11–1 | 3 | 30 | 25 | 40 | 30 | 30 | fertigation | CDFA: end fertigation 50 days before harvest. |
| 5 | Post-harvest recovery | 2–4 | 1 | 25 | 25 | 15 | 20 | 25 | broadcast | Haifa: post-harvest 45-60 kg N/ha to rebuild reserves. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recently mature leaves | July-August | 2.7 | 2.7–3.5 | — | WSU Table 4 |
| P | Recently mature leaves | July-August | 0.1 | 0.1–0.3 | — | WSU Table 4 |
| K | Recently mature leaves | July-August | 1.2 | 1.2–3 | — | WSU Table 4 |
| Ca | Recently mature leaves | July-August | 1 | 1–2.5 | — | WSU Table 4 |
| Mg | Recently mature leaves | July-August | 0.25 | 0.25–0.5 | — | WSU Table 4 |
| S | Recently mature leaves | July-August | 0.2 | 0.2–0.4 | — | WSU Table 4 |
| B | Recently mature leaves | July-August | 20 | 20–80 | — | WSU Table 4 |
| Zn | Recently mature leaves | July-August | 20 | 20–50 | — | WSU Table 4 |
| Fe | Recently mature leaves | July-August | 120 | 120–200 | — | WSU Table 4 |
| Mn | Recently mature leaves | July-August | 20 | 20–200 | — | WSU Table 4 |
| Cu | Recently mature leaves | July-August | 4 | 4–16 | — | WSU Table 4 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg per t fresh fruit | 1.25 | 0.15 | 1.7 | 0.18 | 0.1 | — | CDFA Peach & Nectarine + Geisseler UC Davis Peach |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-2 | 0–1 | 0.25 | 0.25 | 0.3 | 0.2 | Establishment |
| Year 3-4 | 2–3 | 0.55 | 0.55 | 0.6 | 0.5 | Early bearing |
| Year 5 | 4–4 | 0.8 | 0.8 | 0.8 | 0.75 | Pre-mature bearing |
| Year 6+ | 5–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape | irrigated | 12 | 25 | 45 | t fruit/ha | Hortgro Key Deciduous Fruit Statistics 2024 |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Dormancy and post-harvest | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Active growth | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu', 'Ca'] | Micronutrient correction | — |



### Pear

<a id="pear"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 45 |
| Yield unit | t fruit/ha |
| Population / ha | 2000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 2.8 |
| P | 0.35 |
| K | 3.8 |
| Ca | 0.9 |
| Mg | 0.35 |
| S | 0.22 |
| B | 0.04 |
| Zn | 0.02 |
| Fe | 0.08 |
| Mn | 0.02 |
| Cu | 0.008 |
| Mo | 0.004 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | — | 5.5 | 6.3 | 7 | DERIVED from H2O − 0.5. T2 (derived). |
| pH (H2O) | — | 6 | 6.8 | 7.5 | NSW DPI Primefact 85 + Cornell Pear. T2 cross-confirmed. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 40 | 80 | NSW DPI Primefact 85 + Wisconsin Ext apple/pear. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 250 | 400 | NSW DPI + WSU Tree Fruit. T2 cross-confirmed. |
| Ca | 300 | 700 | 2500 | 5000 | Higher Ca threshold; Ca prevents cork spot and internal breakdown. |
| Mg | 60 | 120 | 250 | 500 | Cornell Pear soil interpretation. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 1.5 | 3 | NSW DPI Primefact 85. Pear B critical for pollination. T2. |
| Zn | 1 | 2 | 8 | 25 | NSW DPI Primefact 85. T2. |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Dormancy | 6–8 | 0 | 0 | 5 | 0 | 5 | 5 | broadcast | Stassen & North 2008 Forelle + apple biology. P broadcast. |
| 2 | Bud break & bloom | 9–10 | 1 | 25 | 20 | 10 | 15 | 15 | fertigation | Pear has higher B demand at bloom than apple. |
| 3 | Cell division / fruit set | 10–11 | 3 | 35 | 25 | 25 | 35 | 30 | fertigation | Peak vegetative + fruit N demand. |
| 4 | Cell expansion | 12–2 | 3 | 25 | 25 | 40 | 30 | 30 | fertigation | K-heavy. Forelle/Packham benefit from K for flesh texture and blush. |
| 5 | Post-harvest recovery | 3–5 | 1 | 15 | 25 | 25 | 15 | 20 | broadcast | Reserve N build. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recently mature leaves | July-August | 1.8 | 1.8–2.6 | — | WSU Table 4 |
| P | Recently mature leaves | July-August | 0.12 | 0.12–0.25 | — | WSU Table 4 |
| K | Recently mature leaves | July-August | 1 | 1–2 | — | WSU Table 4 |
| Ca | Recently mature leaves | July-August | 1 | 1–3.7 | — | WSU Table 4 |
| Mg | Recently mature leaves | July-August | 0.25 | 0.25–0.9 | — | WSU Table 4 |
| S | Recently mature leaves | July-August | 0.01 | 0.01–0.03 | — | WSU Table 4 |
| B | Recently mature leaves | July-August | 20 | 20–60 | — | WSU Table 4 |
| Zn | Recently mature leaves | July-August | 20 | 20–60 | — | WSU Table 4 |
| Fe | Recently mature leaves | July-August | 100 | 100–800 | — | WSU Table 4 |
| Mn | Recently mature leaves | July-August | 20 | 20–170 | — | WSU Table 4 |
| Cu | Recently mature leaves | July-August | 6 | 6–20 | — | WSU Table 4 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg per t fresh fruit | 0.8 | 0.1 | 1.7 | 0.075 | — | — | NSW DPI Primefact 85 + CDFA Pear (Glozer) |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.14 | 0.14 | 0.15 | 0.13 | Cheng 2013 Cornell + Marini 2003 Virginia Tech HORT-310: 25 g N/tree at year 1 vs 175 g mature = 0.14. Engine prior 0.20 over-applied 43%. T2. |
| Year 2 | 2–2 | 0.3 | 0.3 | 0.35 | 0.28 | Cheng 2013 + Marini 2003: 50 g N/tree = 0.29. T2. |
| Year 3-4 | 3–4 | 0.55 | 0.55 | 0.6 | 0.5 | Cheng 2013 frame development. T2. |
| Year 5-6 | 5–6 | 0.8 | 0.8 | 0.85 | 0.75 | Cheng 2013 first bearing → pre-mature. T2. |
| Year 7+ | 7–99 | 1 | 1 | 1 | 1 | Cheng 2013: full bearing 175 g N/tree. T2. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape | irrigated | 30 | 55 | 80 | t fruit/ha | Hortgro Key Deciduous Fruit Statistics 2024 |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | NSW DPI Primefact 85 + Cornell Pear | n/a | 2024 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Dormancy and post-harvest | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Active growth | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu', 'Ca'] | Ca sprays for cork spot prevention | — |



### Pecan

<a id="pecan"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 3 |
| Yield unit | t NIS/ha |
| Population / ha | 200 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 50 |
| P | 5 |
| K | 15 |
| Ca | 6 |
| Mg | 5 |
| S | 3.5 |
| B | 0.25 |
| Zn | 0.15 |
| Fe | 0.6 |
| Mn | 0.2 |
| Cu | 0.06 |
| Mo | 0.025 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 6 | 7 | FERTASA 5.8.2 Schmidt 2021 narrative + NMSU H-658. T1 derived. |
| pH (H2O) | 5 | 5.5 | 6.5 | 7.5 | FERTASA 5.8.2 Schmidt 2021 + NMSU H-658. T1+T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 40 | 80 | NMSU H-658 + Mississippi State P3055 + UGA Pecan. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 50 | 100 | 200 | 400 | UGA Pecan Crop Code + Schmidt 2021 narrative. T2. |
| Ca | 250 | 400 | 1500 | 3000 | Schmidt 2021 cross-applies mac chapter (FERTASA 5.8.1). T1 cross-applied. |
| Mg | 60 | 100 | 250 | 500 | Schmidt 2021 cross-applies mac chapter. T1 cross-applied. |
| S | 5 | 10 | 25 | 50 | Generic pecan, T2. |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.8 | 1.5 | 2.5 | Elevated B requirement for nut fill and kernel quality. |
| Zn | 1 | 2.5 | 7 | 12 | Very high Zn requirement; most common nutritional disorder in pecans. |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mg application (winter) | 6–7 | 1 | 0 | 0 | 0 | 0 | 100 | broadcast | FERTASA 5.8.2 Table 5.8.2.3: Mg 100% in Jun/Jul. |
| 2 | Pre-bud-break N + all P (August) | 8–8 | 1 | 50 | 100 | 0 | 30 | 0 | broadcast | FERTASA 5.8.2 Table 5.8.2.3: 50% N + 100% P in August. No K. |
| 3 | Budbreak / spring flush | 9–9 | 0 | 0 | 0 | 0 | 20 | 0 | broadcast | FERTASA 5.8.2: no N/P/K scheduled here. Zn foliars begin (5 cm bud to 3 wk intervals) — handled separately. |
| 4 | Late-spring N + all K (October) | 10–10 | 1 | 50 | 0 | 100 | 30 | 0 | broadcast | FERTASA 5.8.2 Table 5.8.2.3: 50% N + 100% K in October. No P. |
| 5 | Nut fill + harvest (Nov-May) | 11–5 | 0 | 0 | 0 | 0 | 20 | 0 | broadcast | FERTASA 5.8.2: no further N/P/K. Kernel fill Feb-Apr. Zn foliar continues. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 2.5–3 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| P | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 0.14–0.3 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| K | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 1.3–2.5 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| Ca | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 1.3–1.75 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| Mg | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 0.35–0.6 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| S | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 0.25–0.5 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| B | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 50–100 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| Zn | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 50–100 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| Fe | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 50–300 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| Mn | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 100–800 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| Cu | Middle leaflets, mid-shoot | 120-150 days after flowering | — | 6–30 | — | Schmidt 2021 ARC-ITSC Tbl 3 (Georgia) |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| in-shell | kg/t in-shell | 50 | 5 | 15 | 6 | 5 | — | UGA Cooperative Extension Bulletin 1304 + Wells 2017 |
| total trace | kg/t in-shell | — | — | — | — | — | — | Schoeman 2017 SAMAC FERTASA Symposium (cross-applied to pecan) |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-3 | 0–3 | 0.15 | 0.15 | 0.2 | 0.1 | Establishment; very slow grower |
| Year 4-6 | 4–6 | 0.35 | 0.35 | 0.35 | 0.3 | Pre-bearing; canopy filling |
| Year 7-9 | 7–9 | 0.55 | 0.55 | 0.55 | 0.5 | First commercial crop |
| Year 10-12 | 10–12 | 0.8 | 0.8 | 0.8 | 0.75 | Building to full production |
| Year 13+ | 13–99 | 1 | 1 | 1 | 1 | Full bearing; alternate bearing management |

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S', 'Zn'] | Primary method; Zn in broadcast critical for pecan. Split N 3-4 times | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Zn', 'B'] | When irrigated; heavy Zn and N demand during nut fill | — |
| foliar | False | ['Zn', 'Ni', 'Fe', 'Mn', 'Cu', 'B'] | Zn foliar 3-6 sprays/season is standard practice; Ni for mouse-ear | — |



### Pepper (Bell)

<a id="pepper-bell"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 50 |
| Yield unit | t fruit/ha |
| Population / ha | 25000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3 |
| P | 0.45 |
| K | 4.5 |
| Ca | 0.3 |
| Mg | 0.25 |
| S | 0.25 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5.5 | 6 | 6.5 | UC ANR Pepper + KZN-DARD Capsicum. T1+T2. |
| pH (H2O) | 5 | 6 | 6.8 | 7.2 | UF/IFAS HS732 + KZN-DARD. T1+T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 12 | 30 | 60 | 120 | UC ANR Pepper + Haifa. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 100 | 180 | 300 | 500 | Haifa Pepper + UC ANR. T2. |
| Ca | 300 | 700 | 2500 | 5000 | High Ca requirement; reduces blossom end rot. |
| Mg | 80 | 150 | 300 | 500 | UF/IFAS HS732. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.4 | 0.6 | 1.5 | 3 | UC ANR — pepper flower-set sensitive. T2. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Transplant & establishment | 9–10 | 1 | 10 | 30 | 10 | 15 | 15 | band_place | Starter P for transplant recovery |
| 2 | Vegetative growth | 10–11 | 2 | 30 | 25 | 20 | 20 | 20 | fertigation | N for frame building |
| 3 | Flowering & fruit set | 12–1 | 2 | 25 | 20 | 25 | 30 | 30 | fertigation | Ca for BER prevention; B for set |
| 4 | Fruit fill & harvest | 2–4 | 3 | 35 | 25 | 45 | 35 | 35 | fertigation | K for colour and firmness |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 160–160 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 120–120 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 180–220 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 90–90 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 70–70 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | most-recent mature leaf | first flower | 3 | 3.5–5 | 5.5 | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| P | most-recent mature leaf | first flower | 0.2 | 0.3–0.6 | 0.8 | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| K | most-recent mature leaf | first flower | 2.5 | 3–4.5 | 5.5 | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| Ca | most-recent mature leaf | first flower | 1 | 1.5–3 | 4 | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| Mg | most-recent mature leaf | first flower | 0.3 | 0.4–0.8 | 1.2 | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| S | most-recent mature leaf | first flower | 0.2 | 0.3–0.6 | 0.8 | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| B | most-recent mature leaf | first flower | 25 | 30–80 | 100 | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| Zn | most-recent mature leaf | first flower | 18 | 25–60 | 200 | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| Fe | most-recent mature leaf | first flower | 50 | 60–300 | — | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| Mn | most-recent mature leaf | first flower | 30 | 40–250 | 500 | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| Cu | most-recent mature leaf | first flower | 5 | 6–25 | — | UC Davis Geisseler Pepper + UF/IFAS HS732. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | UF/IFAS HS732 | HS732 | 2024 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| fertigation | True | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary; similar to tomato | — |
| broadcast | False | ['P', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| foliar | False | ['Ca', 'B', 'Fe', 'Mn', 'Zn'] | Ca for BER; B for set | — |



### Persimmon

<a id="persimmon"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t fruit/ha |
| Population / ha | 500 |
| Years to bearing | 4 |
| Years to full bearing | 7 |
| N (target/uptake) | 4 |
| P | 0.5 |
| K | 5 |
| Ca | 1.5 |
| Mg | 0.5 |
| S | 0.3 |
| B | 0.04 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.04 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.9 | 5.4 | 6.4 | 6.9 | DERIVED from H2O − 0.6 offset. T3 (derived). |
| pH (H2O) | 5.5 | 6 | 7 | 7.5 | Bellini & Giordani 2005 Acta Hort 685 (Italian persimmon symposium). Tighter band than fig/pomegranate. T3. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| P (Olsen) | 8 | 12 | 30 | 60 | George et al. 1997 Acta Hort 436. T3. |
| **K** | — | — | — | — | _needs source_ |
| Ca | 800 | 1200 | 3500 | 6000 | Italian calcicole tendency. Bellini & Giordani 2005. T3. |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest & leaf fall | 6–7 | 1 | 10 | 5 | 5 | 5 | 5 | broadcast | Light recovery |
| 2 | Dormancy | 7–8 | 1 | 5 | 10 | 5 | 5 | 5 | broadcast | Winter rest |
| 3 | Bud break & bloom | 9–10 | 2 | 20 | 25 | 15 | 15 | 15 | fertigation | B for set; P for root flush |
| 4 | Fruit development | 11–2 | 3 | 40 | 35 | 35 | 45 | 45 | fertigation | Ca for cracking prevention |
| 5 | Maturation & harvest | 3–5 | 2 | 25 | 25 | 40 | 30 | 30 | fertigation | K for astringency reduction |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | mid-shoot leaf | mid-summer | 1.8 | 2–2.5 | 3 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| P | mid-shoot leaf | mid-summer | 0.1 | 0.12–0.2 | 0.3 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| K | mid-shoot leaf | mid-summer | 1.2 | 1.5–2.5 | 3.5 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| Ca | mid-shoot leaf | mid-summer | 1 | 1.2–2.5 | 3.5 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| Mg | mid-shoot leaf | mid-summer | 0.3 | 0.35–0.6 | 0.9 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| S | mid-shoot leaf | mid-summer | 0.15 | 0.18–0.35 | 0.5 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| B | mid-shoot leaf | mid-summer | 25 | 30–50 | 80 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| Zn | mid-shoot leaf | mid-summer | 15 | 20–40 | 60 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| Fe | mid-shoot leaf | mid-summer | 70 | 80–150 | 250 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| Mn | mid-shoot leaf | mid-summer | 30 | 40–150 | 350 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| Cu | mid-shoot leaf | mid-summer | 5 | 6–15 | 25 | George et al. 1997 Acta Hort 436 Persimmon Symposium + Bellini & Giordani 2005 Acta Hort 685. T3. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-2 | 0–2 | 0.15 | 0.15 | 0.15 | 0.15 | George et al. 1997 — bears year 4, full year 7. Slow establishment. |
| Year 3 | 3–3 | 0.3 | 0.3 | 0.3 | 0.3 | George et al. 1997. |
| Year 4-6 | 4–6 | 0.65 | 0.65 | 0.65 | 0.65 | George et al. 1997. |
| Year 7+ | 7–99 | 1 | 1 | 1 | 1 | George et al. 1997 — full bearing. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| Triumph | SA WC | irrigated | 18 | 25 | 35 | t fresh fruit/ha | Hortgro Persimmon industry summary 2022 (Subtrop). |
| Fuyu | Italy + Israel | irrigated | 25 | 35 | 50 | t fresh fruit/ha | Bellini & Giordani 2005 Acta Hort 685. |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | George 1997 Acta Hort 436 | n/a | 1997 | 3 | — |

**Application methods** (`crop_application_methods`)

_No rows._



### Pineapple

<a id="pineapple"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 60 |
| Yield unit | t fruit/ha |
| Population / ha | 60000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 2.5 |
| P | 0.3 |
| K | 5 |
| Ca | 0.3 |
| Mg | 0.3 |
| S | 0.15 |
| B | 0.02 |
| Zn | 0.02 |
| Fe | 0.05 |
| Mn | 0.02 |
| Cu | 0.005 |
| Mo | 0.003 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 3.8 | 4.2 | 5.5 | 6 | Acidophilic crop; optimal pH 4.5-5.5 KCl. |
| pH (H2O) | 4.3 | 4.7 | 6 | 6.5 | Acidophilic crop; optimal pH 5.0-6.0 H2O. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 5 | 12 | 30 | 60 | Hawaii CTAHR PNM4. T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 40 | 80 | 150 | 300 | CTAHR pineapple low-K threshold. T2. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & establishment | 3–6 | 1 | 10 | 30 | 10 | 15 | 15 | band_place | P for slip/sucker roots |
| 2 | Vegetative rosette growth | 7–12 | 3 | 40 | 30 | 30 | 30 | 30 | side_dress | High N and K for leaf mass |
| 3 | Flower induction & development | 1–4 | 2 | 20 | 20 | 20 | 25 | 25 | fertigation | B for flower quality |
| 4 | Fruit development & harvest | 5–2 | 2 | 30 | 20 | 40 | 30 | 30 | fertigation | K for acidity and sugar balance |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | — | —–— — | 0–— | 400–500 | — | CTAHR F&N-7 Post-plant annual N |
| P | — | —–— — | 0–— | 75–75 | — | CTAHR F&N-7 Pre-plant P |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | D-leaf basal white portion | 6-8 months post-plant | 1.7 | 1.7–— | — | CTAHR F&N-7 |
| P | D-leaf (youngest fully expanded) | Floral induction | — | 0.1–0.3 | 0.35 | Hawaii CTAHR PNM4 + CABI Pineapple |
| K | D-leaf basal white portion | 6-8 months post-plant | 2.2 | 2.2–— | — | CTAHR F&N-7 |
| Ca | D-leaf | Floral induction | — | 0.25–0.4 | 0.6 | Hawaii CTAHR PNM4 + CABI Pineapple |
| Mg | D-leaf basal white portion | 6-8 months post-plant | 0.25 | 0.25–— | — | CTAHR F&N-7 |
| S | D-leaf | Floral induction | — | 0.18–0.28 | 0.35 | Hawaii CTAHR PNM4 + CABI Pineapple |
| B | D-leaf | Floral induction | — | 20–40 | 60 | Hawaii CTAHR PNM4 + CABI Pineapple |
| Zn | D-leaf | Floral induction | — | 10–25 | 40 | Hawaii CTAHR PNM4 + CABI Pineapple |
| Fe | D-leaf | Floral induction | — | 100–200 | 300 | Hawaii CTAHR PNM4 + CABI Pineapple |
| Mn | D-leaf | Floral induction | — | 100–250 | 500 | Hawaii CTAHR PNM4 + CABI Pineapple |
| Cu | D-leaf | Floral induction | — | 5–15 | 25 | Hawaii CTAHR PNM4 + CABI Pineapple |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg per t fresh fruit | 6 | 0.65 | 11.6 | 3.9 | 0.5 | — | Caetano et al. 2024 + ICL Pineapple |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | KZN North Coast / EC | irrigated | 30 | 60 | 100 | t fruit/ha | ICL Pineapple + CABI Pineapple |
| Queen | Eastern Cape | rainfed | 30 | 40 | 50 | t fruit/ha | ICL Pineapple + CABI Pineapple |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| foliar | True | ['N', 'K', 'Fe', 'Zn', 'B', 'Mn', 'Cu'] | Primary method — pineapple absorbs through leaves | — |
| broadcast | False | ['P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant and base amendments only | — |
| side_dress | False | ['N', 'K'] | Supplementary N and K between rows | — |



### Plum

<a id="plum"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t fruit/ha |
| Population / ha | 1000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4 |
| P | 0.5 |
| K | 5 |
| Ca | 1 |
| Mg | 0.5 |
| S | 0.3 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | — | 5.5 | 6.3 | 7 | DERIVED from H2O − 0.5. T2 (derived). |
| pH (H2O) | — | 6 | 6.8 | 7.5 | CDFA Prune & Plum + WSU Tree Fruit. T2 cross-confirmed. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 20 | 40 | 80 | CDFA Prune & Plum + WSU. T2 cross-confirmed. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 250 | 400 | CDFA Prune & Plum + WSU. T2 cross-confirmed. |
| Ca | 300 | 600 | 2000 | 4000 | CDFA Prune & Plum (similar to peach; lower than pome). T2. |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 1.5 | 2.5 | CDFA Prune & Plum. T2. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Dormancy | 5–7 | 0 | 0 | 5 | 5 | 5 | 5 | broadcast | WC Paarl/Wellington/Stellenbosch dominant. 93% Japanese plum. |
| 2 | Bud break & bloom | 8–9 | 1 | 20 | 25 | 15 | 15 | 15 | fertigation | Songold/Sapphire/Laetitia/African Delight/Angeleno. |
| 3 | Fruit set & cell division | 10–11 | 2 | 30 | 25 | 25 | 30 | 25 | fertigation | Peak vegetative + fruit demand. |
| 4 | Cell expansion & ripening | 12–2 | 3 | 25 | 25 | 40 | 30 | 30 | fertigation | K drives skin colour + brix in Songold/Angeleno. |
| 5 | Post-harvest recovery | 3–4 | 1 | 25 | 20 | 15 | 20 | 25 | broadcast | Restore reserves. |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Recently mature leaves | July-August | 2.4 | 2.4–3.3 | — | WSU Table 4 (via Apricot) |
| P | Recently mature leaves | July-August | 0.1 | 0.1–0.3 | — | WSU Table 4 (via Apricot) |
| K | Recently mature leaves | July-August | 2 | 2–3.5 | — | WSU Table 4 (via Apricot) |
| Ca | Recently mature leaves | July-August | 1.1 | 1.1–4 | — | WSU Table 4 (via Apricot) |
| Mg | Recently mature leaves | July-August | 0.25 | 0.25–0.8 | — | WSU Table 4 (via Apricot) |
| S | Recently mature leaves | July-August | 0.2 | 0.2–0.4 | — | WSU Table 4 (via Apricot) |
| B | Recently mature leaves | July-August | 20 | 20–70 | — | WSU Table 4 (via Apricot) |
| Zn | Recently mature leaves | July-August | 16 | 16–50 | — | WSU Table 4 (via Apricot) |
| Fe | Recently mature leaves | July-August | 60 | 60–250 | — | WSU Table 4 (via Apricot) |
| Mn | Recently mature leaves | July-August | 20 | 20–160 | — | WSU Table 4 (via Apricot) |
| Cu | Recently mature leaves | July-August | 4 | 4–16 | — | WSU Table 4 (via Apricot) |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg per t fresh fruit | 2.1 | 0.36 | 3.15 | — | — | — | CDFA Prune & Plum + UC ANR Stone Fruit |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1-2 | 0–1 | 0.25 | 0.25 | 0.3 | 0.2 | Establishment |
| Year 3-4 | 2–3 | 0.55 | 0.55 | 0.6 | 0.5 | Early bearing |
| Year 5 | 4–4 | 0.8 | 0.8 | 0.8 | 0.75 | Pre-mature bearing |
| Year 6+ | 5–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape | irrigated | 18 | 30 | 50 | t fruit/ha | Hortgro Key Deciduous Fruit Statistics 2024 |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Dormancy and post-harvest | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Active growth | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu', 'Ca'] | Micronutrient correction | — |



### Pomegranate

<a id="pomegranate"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t fruit/ha |
| Population / ha | 600 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 5 |
| P | 0.6 |
| K | 6 |
| Ca | 1.5 |
| Mg | 0.6 |
| S | 0.35 |
| B | 0.05 |
| Zn | 0.03 |
| Fe | 0.1 |
| Mn | 0.03 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.9 | 5.9 | 6.9 | 7.9 | DERIVED from H2O − 0.6 offset. T2 (derived). |
| pH (H2O) | 5.5 | 6.5 | 7.5 | 8.5 | Yara Pomegranate Crop Guide + Iranian Pomegranate Research Centre Yazd: extreme alkaline tolerance. T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| P (Olsen) | 8 | 12 | 30 | 60 | ICAR-NRC Pomegranate Solapur Guidelines 2017 + Haifa Pomegranate. T2. |
| K | 100 | 150 | 300 | 500 | ICAR-NRC Solapur 2017. T2. |
| Ca | 800 | 1500 | 5000 | 10000 | Wonderful in calcareous soils (Holland et al. 2009 Hort Reviews 35 — Israel Volcani). T2. |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| Na | — | 200 | 800 | 2000 | Pomegranate tolerates ECe 6 dS/m; salt tolerance high. Holland et al. 2009 + Day & Wilkins 2011 UC ANR. T2. |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `Acid Saturation`

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest & leaf fall | 5–6 | 1 | 10 | 5 | 5 | 5 | 5 | broadcast | Recovery after harvest |
| 2 | Dormancy | 7–8 | 1 | 5 | 5 | 5 | 5 | 5 | broadcast | Minimal demand |
| 3 | Bud break & bloom | 9–10 | 2 | 20 | 30 | 15 | 15 | 15 | fertigation | B for set |
| 4 | Fruit development | 11–1 | 3 | 40 | 35 | 35 | 45 | 45 | fertigation | Ca for aril quality |
| 5 | Maturation & harvest | 2–4 | 2 | 25 | 25 | 40 | 30 | 30 | fertigation | K for colour and sugar |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | — | —–— — | 0–— | 84–140 | — | UF/IFAS FE1024 Annual N (bearing) |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | non-bearing twig leaf | fruit-set 60-90d post-bloom | 1.5 | 1.8–2.5 | 3 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| P | non-bearing twig leaf | fruit-set 60-90d post-bloom | 0.1 | 0.12–0.2 | 0.3 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| K | non-bearing twig leaf | fruit-set 60-90d post-bloom | 0.7 | 0.9–1.6 | 2.5 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| Ca | non-bearing twig leaf | fruit-set 60-90d post-bloom | 1.5 | 2–3.5 | 5 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| Mg | non-bearing twig leaf | fruit-set 60-90d post-bloom | 0.2 | 0.25–0.5 | 0.75 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| S | non-bearing twig leaf | fruit-set 60-90d post-bloom | 0.15 | 0.18–0.3 | 0.45 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| B | non-bearing twig leaf | fruit-set 60-90d post-bloom | 25 | 30–60 | 100 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| Zn | non-bearing twig leaf | fruit-set 60-90d post-bloom | 18 | 20–40 | 60 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| Fe | non-bearing twig leaf | fruit-set 60-90d post-bloom | 70 | 80–200 | 350 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| Mn | non-bearing twig leaf | fruit-set 60-90d post-bloom | 25 | 30–100 | 200 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| Cu | non-bearing twig leaf | fruit-set 60-90d post-bloom | 5 | 7–15 | 25 | ICAR-NRC Solapur Pomegranate Production Manual 2017 + Holland et al. 2009 Hort Reviews 35 + Yara Pomegranate. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fresh fruit | 5 | 0.6 | 7 | 1.2 | 0.4 | 0.3 | Migration 112 |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–1 | 0.15 | 0.15 | 0.15 | 0.15 | ICAR-NRC Solapur 2017 + Day & Wilkins 2011. Bears year 3, full year 5. |
| Year 2 | 2–2 | 0.3 | 0.3 | 0.3 | 0.3 | ICAR-NRC Solapur 2017. |
| Year 3 | 3–3 | 0.55 | 0.55 | 0.55 | 0.55 | ICAR-NRC Solapur 2017. |
| Year 4 | 4–4 | 0.8 | 0.8 | 0.8 | 0.8 | ICAR-NRC Solapur 2017. |
| Year 5+ | 5–99 | 1 | 1 | 1 | 1 | ICAR-NRC Solapur 2017 — full bearing. |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| Wonderful | SA WC | irrigated | 18 | 25 | 35 | t fresh fruit/ha | SA Pomegranate Producers Assoc 2019 industry summary. |
| Acra | SA WC | irrigated | 15 | 22 | 30 | t fresh fruit/ha | SAPPA 2019. |
| Wonderful | California | irrigated | 25 | 35 | 50 | t fresh fruit/ha | Day & Wilkins 2011 UC ANR ACTAHO. |
| Bhagwa | India | irrigated | 18 | 25 | 35 | t fresh fruit/ha | ICAR-NRC Solapur Manual 2017. |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | Holland 2009 Hort Reviews 35 + Day & Wilkins 2011 | n/a | 2009 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Dormancy and post-harvest | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S', 'B'] | Active growth when irrigated | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu', 'Ca'] | B for fruit set; Ca for rind quality | — |



### Potato

<a id="potato"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 50 |
| Yield unit | t tuber/ha |
| Population / ha | 45000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4.5 |
| P | 0.6 |
| K | 6.5 |
| Ca | 0.2 |
| Mg | 0.3 |
| S | 0.3 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4 | 4.5 | 5.5 | 6.5 | Lower pH (4.8-5.5) reduces common scab incidence. |
| pH (H2O) | 4.5 | 5 | 6 | 7 | Lower pH reduces common scab incidence. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 8 | 20 | 35 | 60 | High P feeder; tuber initiation and bulking require ample P. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & emergence (pre-tuber) | 8–9 | 1 | 55 | 100 | 70 | 40 | 40 | band_place | FERTASA 5.6.2 Table 5.6.2.3 (sandy <10% clay default). HEAVY SOILS: 10-20% clay → 68% N here; >20% clay → 90-100% N here. |
| 2 | Vegetative (pre-tuber-init finish) | 10–11 | 0 | 0 | 0 | 0 | 20 | 20 | broadcast | FERTASA: all pre-tuber N already applied at planting for sandy soils. |
| 3 | Tuber bulking | 11–12 | 1 | 45 | 0 | 30 | 25 | 25 | broadcast | FERTASA 5.6.2 Table 5.6.2.3: 40-50% N post-tuber-init (sandy). HEAVY SOILS: 25-40% (10-20% clay) or 0-20% (>20% clay). |
| 4 | Maturation (STOP N >=4 weeks pre-die-back) | 1–1 | 0 | 0 | 0 | 0 | 15 | 15 | broadcast | FERTASA 5.6.2: no N in final 4 weeks before foliage die-back. |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | — | —–— — | 15–15 | 80–80 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 20–20 | 95–95 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 25–25 | 110–110 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 30–30 | 130–130 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 15–15 | 70–70 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 20–20 | 85–85 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 25–25 | 100–100 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 30–30 | 120–120 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 15–15 | 60–60 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 20–20 | 75–75 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 25–25 | 90–90 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 30–30 | 110–110 | — | FERTASA Handbook 5.6.2.1 |
| N | — | —–— — | 30–30 | 170–170 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 40–40 | 220–220 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 50–50 | 250–250 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 60–60 | 275–275 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 70–70 | 300–300 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 80–80 | 320–320 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 30–30 | 150–150 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 40–40 | 190–190 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 50–50 | 220–220 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 60–60 | 240–240 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 70–70 | 260–260 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 80–80 | 280–280 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 30–30 | 130–130 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 40–40 | 160–160 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 50–50 | 180–180 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 60–60 | 200–200 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 70–70 | 220–220 | — | FERTASA Handbook 5.6.2.2 |
| N | — | —–— — | 80–80 | 240–240 | — | FERTASA Handbook 5.6.2.2 |
| P | Bray-1 | 0–5 mg/kg | 10–10 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 0–5 mg/kg | 20–20 | 115–115 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 0–5 mg/kg | 30–30 | 130–130 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 0–5 mg/kg | 40–40 | 145–145 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 0–5 mg/kg | 50–50 | 160–160 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 0–5 mg/kg | 60–60 | 175–175 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 0–5 mg/kg | 70–70 | 190–190 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 0–5 mg/kg | 80–80 | 205–205 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 0–3 mg/kg | 10–10 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 0–3 mg/kg | 20–20 | 115–115 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 0–3 mg/kg | 30–30 | 130–130 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 0–3 mg/kg | 40–40 | 145–145 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 0–3 mg/kg | 50–50 | 160–160 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 0–3 mg/kg | 60–60 | 175–175 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 0–3 mg/kg | 70–70 | 190–190 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 0–3 mg/kg | 80–80 | 205–205 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 4–6 mg/kg | 10–10 | 80–80 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 4–6 mg/kg | 20–20 | 90–90 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 4–6 mg/kg | 30–30 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 4–6 mg/kg | 40–40 | 110–110 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 4–6 mg/kg | 50–50 | 120–120 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 4–6 mg/kg | 60–60 | 130–130 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 4–6 mg/kg | 70–70 | 140–140 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 4–6 mg/kg | 80–80 | 150–150 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 6–10 mg/kg | 10–10 | 80–80 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 6–10 mg/kg | 20–20 | 90–90 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 6–10 mg/kg | 30–30 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 6–10 mg/kg | 40–40 | 110–110 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 6–10 mg/kg | 50–50 | 120–120 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 6–10 mg/kg | 60–60 | 130–130 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 6–10 mg/kg | 70–70 | 140–140 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 6–10 mg/kg | 80–80 | 150–150 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 7–11 mg/kg | 10–10 | 60–60 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 7–11 mg/kg | 20–20 | 70–70 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 7–11 mg/kg | 30–30 | 80–80 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 7–11 mg/kg | 40–40 | 90–90 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 7–11 mg/kg | 50–50 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 7–11 mg/kg | 60–60 | 110–110 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 7–11 mg/kg | 70–70 | 120–120 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 7–11 mg/kg | 80–80 | 130–130 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 11–19 mg/kg | 10–10 | 60–60 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 11–19 mg/kg | 20–20 | 70–70 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 11–19 mg/kg | 30–30 | 80–80 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 11–19 mg/kg | 40–40 | 90–90 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 11–19 mg/kg | 50–50 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 11–19 mg/kg | 60–60 | 110–110 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 11–19 mg/kg | 70–70 | 120–120 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 11–19 mg/kg | 80–80 | 130–130 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 12–15 mg/kg | 10–10 | 50–50 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 12–15 mg/kg | 20–20 | 60–60 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 12–15 mg/kg | 30–30 | 70–70 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 12–15 mg/kg | 40–40 | 80–80 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 12–15 mg/kg | 50–50 | 90–90 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 12–15 mg/kg | 60–60 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 12–15 mg/kg | 70–70 | 110–110 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 12–15 mg/kg | 80–80 | 120–120 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 15–18 mg/kg | 10–10 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 15–18 mg/kg | 20–20 | 40–40 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 15–18 mg/kg | 30–30 | 50–50 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 15–18 mg/kg | 40–40 | 60–60 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 15–18 mg/kg | 50–50 | 70–70 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 15–18 mg/kg | 60–60 | 80–80 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 15–18 mg/kg | 70–70 | 90–90 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 15–18 mg/kg | 80–80 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 18–— mg/kg | 10–10 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 18–— mg/kg | 20–20 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 18–— mg/kg | 30–30 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 18–— mg/kg | 40–40 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 18–— mg/kg | 50–50 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 18–— mg/kg | 60–60 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 18–— mg/kg | 70–70 | 35–35 | — | FERTASA Handbook 5.6.2.4 |
| P | Olsen | 18–— mg/kg | 80–80 | 45–45 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 20–25 mg/kg | 10–10 | 50–50 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 20–25 mg/kg | 20–20 | 60–60 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 20–25 mg/kg | 30–30 | 70–70 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 20–25 mg/kg | 40–40 | 80–80 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 20–25 mg/kg | 50–50 | 90–90 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 20–25 mg/kg | 60–60 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 20–25 mg/kg | 70–70 | 110–110 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 20–25 mg/kg | 80–80 | 120–120 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 25–30 mg/kg | 10–10 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 25–30 mg/kg | 20–20 | 40–40 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 25–30 mg/kg | 30–30 | 50–50 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 25–30 mg/kg | 40–40 | 60–60 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 25–30 mg/kg | 50–50 | 70–70 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 25–30 mg/kg | 60–60 | 80–80 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 25–30 mg/kg | 70–70 | 90–90 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 25–30 mg/kg | 80–80 | 100–100 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 30–— mg/kg | 10–10 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 30–— mg/kg | 20–20 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 30–— mg/kg | 30–30 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 30–— mg/kg | 40–40 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 30–— mg/kg | 50–50 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 30–— mg/kg | 60–60 | 30–30 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 30–— mg/kg | 70–70 | 35–35 | — | FERTASA Handbook 5.6.2.4 |
| P | Bray-1 | 30–— mg/kg | 80–80 | 45–45 | — | FERTASA Handbook 5.6.2.4 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 4th leaf from top | Tuber initiation | — | 4.5–5.5 | 6 | Haifa Potato + UF/IFAS HS964 |
| P | 4th leaf from top | Tuber initiation | — | 0.3–0.5 | 0.6 | Haifa Potato + UF/IFAS HS964 |
| K | 4th leaf from top | Tuber initiation | — | 5–7 | 9 | Haifa Potato + UF/IFAS HS964 |
| Ca | 4th leaf from top | Tuber initiation | — | 0.7–1.5 | — | Haifa Potato + UF/IFAS HS964 |
| Mg | 4th leaf from top | Tuber initiation | — | 0.3–0.8 | — | Haifa Potato + UF/IFAS HS964 |
| S | 4th leaf from top | Tuber initiation | — | 0.3–0.5 | — | Haifa Potato + UF/IFAS HS964 |
| B | 4th leaf from top | Tuber initiation | — | 25–50 | 75 | Haifa Potato + UF/IFAS HS964 |
| Zn | 4th leaf from top | Tuber initiation | — | 30–80 | — | Haifa Potato + UF/IFAS HS964 |
| Fe | 4th leaf from top | Tuber initiation | — | 50–150 | — | Haifa Potato + UF/IFAS HS964 |
| Mn | 4th leaf from top | Tuber initiation | — | 40–200 | — | Haifa Potato + UF/IFAS HS964 |
| Cu | 4th leaf from top | Tuber initiation | — | 7–20 | — | Haifa Potato + UF/IFAS HS964 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| tuber | kg per t fresh tuber | 4.5 | 0.87 | 5.4 | 0.75 | 0.4 | 0.4 | Yara Potato + Haifa Potato |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S', 'Zn'] | At planting; starter in furrow | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant and hilling | — |
| side_dress | False | ['N', 'K', 'Ca'] | Tuber initiation topdress; Ca for scab prevention | — |
| fertigation | False | ['N', 'K', 'Ca', 'S'] | Under pivot or drip; primary for irrigated | — |
| foliar | False | ['Mn', 'Zn', 'B', 'Ca'] | Mn and Ca for tuber quality | — |



### Pumpkin

<a id="pumpkin"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t fruit/ha |
| Population / ha | 5000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4 |
| P | 0.5 |
| K | 5 |
| Ca | 0.5 |
| Mg | 0.35 |
| S | 0.25 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Establishment | 10–10 | 1 | 15 | 30 | 10 | 15 | 15 | band_place | Starter P |
| 2 | Vine growth | 11–12 | 2 | 35 | 30 | 25 | 25 | 25 | side_dress | High N for vine extension |
| 3 | Flowering & fruit set | 1–2 | 2 | 25 | 20 | 25 | 30 | 30 | fertigation | B for pollination |
| 4 | Fruit fill & maturation | 3–5 | 1 | 25 | 20 | 40 | 30 | 30 | broadcast | K for storage quality |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 30–30 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 80–120 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 90–90 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 70–70 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | most-recent mature leaf | all stages | 4 | 4–5 | 5.5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| P | most-recent mature leaf | all stages | 0.3 | 0.3–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| K | most-recent mature leaf | all stages | 3 | 3–4 | 5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Ca | most-recent mature leaf | all stages | 1.2 | 1.2–2 | 3 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mg | most-recent mature leaf | all stages | 0.25 | 0.25–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| S | most-recent mature leaf | all stages | 0.2 | 0.2–0.75 | 1 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| B | most-recent mature leaf | all stages | 25 | 25–85 | 120 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Zn | most-recent mature leaf | all stages | 20 | 20–200 | 300 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Fe | most-recent mature leaf | all stages | 50 | 50–300 | — | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mn | most-recent mature leaf | all stages | 25 | 25–250 | 500 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Cu | most-recent mature leaf | all stages | 5 | 5–60 | 100 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| vining | — | irrigated | 20 | 30 | 40 | t fruit/ha | Starke Ayres Pumpkin & Hubbard Squash 2019 |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At planting | — |
| side_dress | False | ['N', 'K'] | Vine growth topdress | — |
| fertigation | False | ['N', 'K', 'Ca', 'S'] | When irrigated | — |
| foliar | False | ['B', 'Ca', 'Mn'] | B for pollination | — |



### Raspberry

<a id="raspberry"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 6 |
| Yield unit | t fruit/ha |
| Population / ha | 3000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 0 |
| P | 0 |
| K | 0 |
| Ca | 0 |
| Mg | 0 |
| S | 0 |
| B | 0 |
| Zn | 0 |
| Fe | 0 |
| Mn | 0 |
| Cu | 0 |
| Mo | 0 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 5.5 | 6 | DERIVED from H2O-0.5 (FERTASA convention) for SA cool-climate raspberry. T2 derived. |
| pH (H2O) | 4.7 | 5.5 | 6 | 6.5 | NZ Plant & Food + WSU PNW 656 — raspberry more acid-preferring than blackberry in cool climate. Replaces NCSU 6.0-6.5 (Southeast US warm-climate). T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | — | —–— — | 0–— | 27.9–55.8 | — | NCSU AG-697 Pre-plant K broadcast |
| N | — | —–— — | 0–— | 28–56 | — | NCSU AG-697 Year 1 (establishment) |
| N | — | —–— — | 0–— | 44.8–89.7 | — | NCSU AG-697 Year 2+ (bearing) |
| P | — | —–— — | 0–— | 14.7–29.3 | — | NCSU AG-697 Pre-plant P broadcast |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Most recently fully expanded leaves | NCSU mid-season | 2.5 | 2.5–3.5 | — | NCSU AG-697 Table 11-2 |
| P | Most recently fully expanded leaves | NCSU mid-season | 0.15 | 0.15–0.25 | — | NCSU AG-697 Table 11-2 |
| K | Most recently fully expanded leaves | NCSU mid-season | 0.9 | 0.9–1.5 | — | NCSU AG-697 Table 11-2 |
| Ca | Most recently fully expanded leaves | NCSU mid-season | 0.48 | 0.48–1 | — | NCSU AG-697 Table 11-2 |
| Mg | Most recently fully expanded leaves | NCSU mid-season | 0.3 | 0.3–0.45 | — | NCSU AG-697 Table 11-2 |
| S | Most recently fully expanded leaves | NCSU mid-season | 0.17 | 0.17–0.21 | — | NCSU AG-697 Table 11-2 |
| B | Most recently fully expanded leaves | NCSU mid-season | 25 | 25–85 | — | NCSU AG-697 Table 11-2 |
| Zn | Most recently fully expanded leaves | NCSU mid-season | 20 | 20–70 | — | NCSU AG-697 Table 11-2 |
| Fe | Most recently fully expanded leaves | NCSU mid-season | 60 | 60–100 | — | NCSU AG-697 Table 11-2 |
| Mn | Most recently fully expanded leaves | NCSU mid-season | 50 | 50–250 | — | NCSU AG-697 Table 11-2 |
| Cu | Most recently fully expanded leaves | NCSU mid-season | 8 | 8–15 | — | NCSU AG-697 Table 11-2 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| tunnel | — | tunnel | 10 | 14 | 18 | t fruit/ha | NC State Caneberry + OSU EM 8903 Raspberries |
| open field | — | irrigated | 3 | 4.5 | 6 | t fruit/ha | OSU EM 8903 + NC State Caneberry |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| True | NCSU AG-697 + SA caneberry practice | — | 2018 | 3 | Raspberry prefers slightly acidic soils; universal cation-ratio targets over-apply Ca/Mg. |

**Application methods** (`crop_application_methods`)

_No rows._



### Rooibos

<a id="rooibos"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 3 |
| Yield unit | t dry/ha |
| Population / ha | 3000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 20 |
| P | 2 |
| K | 10 |
| Ca | 5 |
| Mg | 2.5 |
| S | 1.5 |
| B | 0.1 |
| Zn | 0.06 |
| Fe | 0.3 |
| Mn | 0.08 |
| Cu | 0.03 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| pH (H2O) | 4 | 4.5 | 6 | 6.5 | SARC 2020: rooibos grows only in the Cederberg on acidic sandy soils, pH 4.5-6.0. Outside this window the crop fails. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 1.3 | 4 | 17 | 30 | Hawkins & Lambers academic work: pristine fynbos P = 1.3-1.7 mg/kg; oldest cultivated rooibos fields reach 4-17 mg/kg Bray-1. Rooibos is a P-sensitive Fynbos legume. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest recovery | 4–6 | 1 | 15 | 15 | 10 | 10 | 10 | broadcast | Minimal inputs; fynbos species |
| 2 | Winter dormancy | 7–8 | 1 | 5 | 10 | 5 | 10 | 10 | broadcast | Adapted to low fertility |
| 3 | Spring flush & growth | 9–12 | 2 | 50 | 45 | 45 | 45 | 45 | broadcast | Main growth; keep inputs low |
| 4 | Harvest | 1–3 | 1 | 30 | 30 | 40 | 35 | 35 | broadcast | K for tea quality |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | — | —–— — | 0–— | 0–0 | — | SA Rooibos Council SARC 2020 Information Sheet |
| N | — | —–— — | 0–— | 0–0 | — | SA Rooibos Council SARC 2020 Information Sheet |
| P | — | —–— — | 0–— | 0–0 | — | SA Rooibos Council SARC 2020 Information Sheet |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Cederberg | rainfed | 0.25 | 0.5 | 1.2 | t dry leaf/ha | Klipopmekaar; Farmers Magazine SA 2025 |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| True | SARC 2020 + Hawkins & Lambers 2011 | 5.x | 2020 | 1 | Rooibos native to acidic nutrient-poor Cape fynbos soils. Migration 065 flagged with no-artificial-fertiliser rate rows; Ca/Mg ratio path must also skip. |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['P', 'K', 'Ca', 'Mg', 'S'] | Primary; fynbos species sensitive to excess N | — |
| foliar | False | ['Fe', 'Mn', 'Zn', 'B'] | Micronutrient correction on acid soils | — |



### Sorghum

<a id="sorghum"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 5 |
| Yield unit | t grain/ha |
| Population / ha | 150000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 22 |
| P | 3.5 |
| K | 4 |
| Ca | 2.5 |
| Mg | 2 |
| S | 1.8 |
| B | 0.02 |
| Zn | 0.04 |
| Fe | 0.25 |
| Mn | 0.04 |
| Cu | 0.008 |
| Mo | 0.004 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & emergence | 10–11 | 1 | 10 | 35 | 10 | 15 | 15 | band_place | Starter P |
| 2 | Vegetative growth | 12–1 | 2 | 40 | 25 | 25 | 25 | 25 | side_dress | Peak N for head size |
| 3 | Boot & flowering | 2–2 | 1 | 25 | 20 | 25 | 30 | 30 | broadcast | B for pollen |
| 4 | Grain fill & maturation | 3–5 | 1 | 25 | 20 | 40 | 30 | 30 | broadcast | K for grain weight |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Whole leaf at boot | Boot stage | — | 3–4 | — | IPNI 4R Sorghum + Pacific Seeds Grain Sorghum Nutrition Guide |
| P | Whole leaf at boot | Boot stage | — | 0.25–0.4 | — | IPNI 4R Sorghum + Pacific Seeds Sorghum |
| K | Whole leaf at boot | Boot stage | — | 1.5–3 | — | IPNI 4R Sorghum + Pacific Seeds Sorghum |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | mature leaf | mid-season | 0.1 | 0.1–2 | 5 | SCSB394 (seedling 0.1-5.0 wider band). T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| grain | kg per t grain | 15 | 3 | 4 | 0.5 | 1 | — | GrainSA + IPNI 4R Sorghum |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Free State | rainfed | 1 | 2 | 3.5 | t grain/ha | GrainSA — Free State produces 50% of SA sorghum |
| — | — | irrigated | 3 | 5 | 7 | t grain/ha | IPNI 4R Sorghum + Pacific Seeds Grain Sorghum |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S', 'Zn'] | At planting | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| side_dress | False | ['N', 'K', 'S'] | V6 topdress | — |
| foliar | False | ['Zn', 'Fe', 'Mn'] | Micronutrient correction | — |



### Soybean

<a id="soybean"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 3 |
| Yield unit | t grain/ha |
| Population / ha | 0 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 90 |
| P | 8.5 |
| K | 32.5 |
| Ca | 4 |
| Mg | 3.5 |
| S | 3 |
| B | 0.05 |
| Zn | 0.08 |
| Fe | 0.4 |
| Mn | 0.08 |
| Cu | 0.02 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.8 | 5.3 | 6.3 | 7.2 | Higher pH preferred for Bradyrhizobium nodulation. |
| pH (H2O) | 5.3 | 5.8 | 6.8 | 7.7 | Higher pH preferred for nodulation and nutrient availability. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 5 | 10 | 25 | 40 | FERTASA 5.5.5 Tab 1. T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 20 | 40 | 80 | 120 | FERTASA 5.5.5 Tab 2. T1. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| S | 6 | 10 | 15 | 25 | IPNI 2014 Soybean. T2. |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| Mo | 0.05 | 0.1 | 0.3 | — | FERTASA 5.5.5: sodium molybdate seed treatment <0.1 ppm. T1. |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & emergence (VE-V2) | 11–12 | 1 | 100 | 100 | 100 | 30 | 30 | band_place | FERTASA 5.5.5: Rhizobium japonicum supplies most N. Sandy <10% clay only: 10-20 kg N starter. If nodulation fails, treat as maize. |
| 2 | Vegetative (V3-V6) | 12–1 | 0 | 0 | 0 | 0 | 25 | 25 | broadcast | FERTASA 5.5.5: nodules established; no N needed unless nodulation fails. |
| 3 | Flowering & pod set (R1-R3) | 1–2 | 0 | 0 | 0 | 0 | 25 | 25 | broadcast | FERTASA 5.5.5: Mo seed treatment (35 g sodium molybdate/50 kg seed). |
| 4 | Pod fill & maturation (R5-R7) | 2–4 | 0 | 0 | 0 | 0 | 20 | 20 | broadcast | FERTASA 5.5.5: Soya removes 5x more K than maize — manage rotation K. |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | Ambic | 0–20 mg/kg | 1–1 | 20–20 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 0–20 mg/kg | 2–2 | 40–40 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 0–20 mg/kg | 3–3 | 60–60 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 0–20 mg/kg | 4–4 | 80–80 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 20–40 mg/kg | 1–1 | 16–16 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 20–40 mg/kg | 2–2 | 31–31 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 20–40 mg/kg | 3–3 | 47–47 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 20–40 mg/kg | 4–4 | 63–63 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 40–60 mg/kg | 1–1 | 13–13 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 40–60 mg/kg | 2–2 | 25–25 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 40–60 mg/kg | 3–3 | 39–39 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 40–60 mg/kg | 4–4 | 53–53 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 60–80 mg/kg | 1–1 | 11–11 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 60–80 mg/kg | 2–2 | 22–22 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 60–80 mg/kg | 3–3 | 34–34 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 60–80 mg/kg | 4–4 | 46–46 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 80–100 mg/kg | 1–1 | 10–10 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 80–100 mg/kg | 2–2 | 20–20 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 80–100 mg/kg | 3–3 | 31–31 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 80–100 mg/kg | 4–4 | 41–41 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 100–— mg/kg | 1–1 | 9–9 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 100–— mg/kg | 2–2 | 19–19 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 100–— mg/kg | 3–3 | 30–30 | — | FERTASA Handbook 5.5.5 Table 2 |
| K | Ambic | 100–— mg/kg | 4–4 | 40–40 | — | FERTASA Handbook 5.5.5 Table 2 |
| P | Bray-1 | 0–5 mg/kg | 1–1 | 20–20 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 0–5 mg/kg | 2–2 | 40–40 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 0–5 mg/kg | 3–3 | 60–60 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 0–5 mg/kg | 4–4 | 80–80 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 5–10 mg/kg | 1–1 | 17–17 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 5–10 mg/kg | 2–2 | 31–31 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 5–10 mg/kg | 3–3 | 45–45 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 5–10 mg/kg | 4–4 | 59–59 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 10–15 mg/kg | 1–1 | 15–15 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 10–15 mg/kg | 2–2 | 25–25 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 10–15 mg/kg | 3–3 | 35–35 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 10–15 mg/kg | 4–4 | 45–45 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 15–20 mg/kg | 1–1 | 13–13 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 15–20 mg/kg | 2–2 | 21–21 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 15–20 mg/kg | 3–3 | 31–31 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 15–20 mg/kg | 4–4 | 42–42 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 20–25 mg/kg | 1–1 | 11–11 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 20–25 mg/kg | 2–2 | 19–19 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 20–25 mg/kg | 3–3 | 28–28 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 20–25 mg/kg | 4–4 | 38–38 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 25–— mg/kg | 1–1 | 10–10 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 25–— mg/kg | 2–2 | 18–18 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 25–— mg/kg | 3–3 | 26–26 | — | FERTASA Handbook 5.5.5 Table 1 |
| P | Bray-1 | 25–— mg/kg | 4–4 | 34–34 | — | FERTASA Handbook 5.5.5 Table 1 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| P | Uppermost mature trifoliate | Early pod fill (R3-R4) | — | 0.35–— | — | 5.3.4 |
| K | Uppermost trifoliate | R3-R4 | — | 2.2–— | — | 5.3.4 |
| Ca | Uppermost trifoliate | R3-R4 | — | 0.4–— | — | 5.3.4 |
| Mg | Uppermost trifoliate | R3-R4 | — | 0.3–— | — | 5.3.4 |
| **S** | — | — | — | — | — | _needs source_ |
| B | Uppermost trifoliate | R3-R4 | — | 25–— | — | 5.3.4 |
| Zn | Uppermost trifoliate | R3-R4 | — | 15–— | — | 5.3.4 |
| **Fe** | — | — | — | — | — | _needs source_ |
| Mn | Uppermost trifoliate | R3-R4 | — | 20–— | — | 5.3.4 |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | Uppermost trifoliate | R3-R4 | — | 0.5–— | — | 5.3.4 |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Mpumalanga / KZN | rainfed | 1.5 | 2.5 | 3.5 | t grain/ha | GrainSA cultivar trials; FAO 3-4 t/ha |
| — | — | irrigated | 3 | 4 | 5 | t grain/ha | GrainSA cultivar trials |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.5.5 + Grain SA Soybean Guide 2019 | 5.5.5 | 2017 | 1 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['P', 'K', 'S'] | At planting; N-fixation crop | — |
| broadcast | False | ['P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| foliar | False | ['Mo', 'Mn', 'Fe', 'B'] | Mo critical for nodulation | — |



### Spinach

<a id="spinach"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t leaf/ha |
| Population / ha | 150000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 5 |
| P | 0.6 |
| K | 5 |
| Ca | 0.8 |
| Mg | 0.5 |
| S | 0.3 |
| B | 0.008 |
| Zn | 0.008 |
| Fe | 0.04 |
| Mn | 0.008 |
| Cu | 0.003 |
| Mo | 0.002 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Sowing & establishment | 3–4 | 1 | 15 | 35 | 10 | 15 | 15 | band_place | P for rapid root development |
| 2 | Rapid leaf growth | 4–6 | 3 | 50 | 35 | 45 | 45 | 45 | fertigation | High N for leaf mass |
| 3 | Harvest | 6–8 | 2 | 35 | 30 | 45 | 40 | 40 | fertigation | K for leaf quality; multiple cuts |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Young whole-plant leaf | Vegetative leaf expansion | — | 4–6 | — | UF/IFAS HS964 + UC ANR Spinach Nutrient Uptake (Smith) |
| P | Young whole-plant leaf | Vegetative leaf expansion | — | 0.3–0.6 | — | UF/IFAS HS964 + UC ANR Spinach (Smith) |
| K | Young whole-plant leaf | Vegetative leaf expansion | — | 5–8 | — | UF/IFAS HS964 + UC ANR Spinach (Smith) |
| Ca | Young whole-plant leaf | Vegetative leaf expansion | — | 0.6–1.5 | — | UF/IFAS HS964 + UC ANR Spinach (Smith) |
| Mg | Young whole-plant leaf | Vegetative leaf expansion | — | 0.5–0.9 | — | UF/IFAS HS964 + UC ANR Spinach (Smith) |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | most-recent mature leaf | mid-growth | 0.1 | 0.2–1 | 5 | SCSB#394 p.77 Spinach, Greenhouse. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | — | irrigated | 10 | 15 | 20 | t leaf/ha | UF/IFAS HS964 + UC ANR Spinach Nutrient Uptake |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| fertigation | True | ['N', 'K', 'Ca', 'Mg', 'S'] | Primary; fast-growing crop | — |
| broadcast | False | ['P', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| foliar | False | ['Fe', 'Mn', 'B'] | Fe for leaf colour | — |



### Strawberry

<a id="strawberry"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 30 |
| Yield unit | t fruit/ha |
| Population / ha | 50000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 6.5 |
| P | 0.5 |
| K | 4 |
| Ca | 1.2 |
| Mg | 0.6 |
| S | 0.4 |
| B | 0.06 |
| Zn | 0.04 |
| Fe | 0.12 |
| Mn | 0.04 |
| Cu | 0.015 |
| Mo | 0.008 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.2 | 4.8 | 5.8 | 6.5 | Prefers slightly acid soil; optimal pH 5.0-5.8 KCl. |
| pH (H2O) | 4.7 | 5.3 | 6.3 | 7 | Prefers slightly acid soil; optimal pH 5.5-6.3 H2O. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Transplant & establishment | 3–4 | 1 | 10 | 30 | 10 | 15 | 15 | band_place | P for crown and root establishment |
| 2 | Vegetative & crown development | 5–6 | 2 | 25 | 25 | 20 | 20 | 20 | fertigation | N for leaf area |
| 3 | Flowering & fruit set | 7–8 | 2 | 20 | 20 | 20 | 25 | 25 | fertigation | B for pollination; Ca for firmness |
| 4 | Fruit development & harvest | 9–11 | 3 | 45 | 25 | 50 | 40 | 40 | fertigation | K for sugar and colour |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 150–150 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 100–100 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 50–50 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 150–200 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 120–120 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 50–50 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Most-recent mature trifoliate leaf | Peak harvest | — | 3–4 | 4.5 | NCDA strawberry fertility manual + Haifa Crop Guide Strawberry |
| P | Most-recent mature trifoliate leaf | Peak harvest | — | 0.2–0.4 | 0.5 | NCDA strawberry + Haifa Strawberry |
| K | Most-recent mature trifoliate leaf | Peak harvest | — | 1.1–2.5 | 3 | NCDA strawberry + Haifa Strawberry |
| Ca | Most-recent mature trifoliate leaf | Peak harvest | — | 0.7–1.7 | 2 | NCDA strawberry + Haifa Strawberry |
| Mg | Most-recent mature trifoliate leaf | Peak harvest | — | 0.3–0.5 | 0.8 | NCDA strawberry + Haifa Strawberry |
| **S** | — | — | — | — | — | _needs source_ |
| B | Most-recent mature trifoliate leaf | Peak harvest | — | 30–70 | 100 | NCDA strawberry + Haifa Strawberry |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg per t fresh fruit | 5 | 0.87 | 6.6 | 1.5 | 0.6 | — | Haifa Crop Guide Strawberry + Haifa Strawberry CRF |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| hydroponic substrate | — | tunnel | 50 | 65 | 80 | t fruit/ha | Haifa Strawberry CRF + Haifa Crop Guide Strawberry |
| tunnel + drip | — | tunnel | 25 | 40 | 50 | t fruit/ha | Haifa Crop Guide Strawberry + UC Davis Strawberry |
| open field | — | irrigated | 15 | 20 | 25 | t fruit/ha | NCDA strawberry + UC Davis Strawberry |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| fertigation | True | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary method; drip essential | — |
| broadcast | False | ['P', 'Ca', 'Mg', 'S'] | Pre-plant bed preparation only | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu', 'Ca'] | Ca for firmness; B for set | — |



### Sugarcane

<a id="sugarcane"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 120 |
| Yield unit | t cane/ha |
| Population / ha | 12000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 1.32 |
| P | 0.27 |
| K | 2.5 |
| Ca | 0.363 |
| Mg | 0.313 |
| S | 0.4 |
| B | 0.159 |
| Zn | 0.199 |
| Fe | 0.239 |
| Mn | 0.879 |
| Cu | 0.099 |
| Mo | 0.079 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 60 | 120 | 250 | 450 | High K feeder; K important for sucrose accumulation. |
| Ca | — | 300 | — | — | SASRI IS 7.7: < 300 mg/L topsoil Ca is inadequate and supplement is advised (typically calcitic lime). Very_low_max left to universal (200). |
| Mg | — | 50 | — | — | SASRI IS 7.7: < 50 mg/L topsoil Mg is inadequate; dolomitic lime typically advised. Very_low_max left to universal (40). |
| S | 3 | 10 | — | — | SASRI IS 7.6: response guaranteed below 3 mg/kg; uncertain 3-10; unlikely above 10. Optimal/High bounds fall through to universal soil_sufficiency. |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Germination & establishment | 9–10 | 1 | 15 | 40 | 15 | 20 | 20 | band_place | P at planting for root development; N at 6-8 weeks |
| 2 | Tillering | 11–1 | 2 | 35 | 25 | 20 | 25 | 25 | side_dress | Critical N period; promotes tiller development |
| 3 | Grand growth (stalk elongation) | 2–5 | 2 | 35 | 20 | 30 | 30 | 30 | side_dress | Maximum growth rate; high N + K demand; irrigated Lowveld |
| 4 | Ripening & sucrose accumulation | 6–8 | 1 | 15 | 15 | 35 | 25 | 25 | fertigation | Stop N 8-10 weeks before harvest; K for sucrose content |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | — | —–— — | 75–75 | 110–110 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 90–90 | 130–130 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 100–100 | 140–140 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 125–125 | 165–165 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 150–150 | 190–190 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 175–175 | 215–215 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 200–200 | 215–215 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 75–75 | 140–140 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 90–90 | 160–160 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 100–100 | 170–170 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 125–125 | 195–195 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 150–150 | 220–220 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 175–175 | 245–245 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 200–200 | 245–245 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 75–75 | 90–90 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 90–90 | 110–110 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 100–100 | 120–120 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 125–125 | 145–145 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 150–150 | 170–170 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 175–175 | 195–195 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 200–200 | 195–195 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 75–75 | 130–130 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 90–90 | 150–150 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 100–100 | 160–160 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 125–125 | 185–185 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 150–150 | 210–210 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 175–175 | 235–235 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 200–200 | 235–235 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 75–75 | 60–60 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 90–90 | 80–80 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 100–100 | 90–90 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 125–125 | 115–115 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 150–150 | 140–140 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 175–175 | 165–165 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 200–200 | 165–165 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 75–75 | 100–100 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 90–90 | 120–120 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 100–100 | 130–130 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 125–125 | 155–155 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 150–150 | 180–180 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 175–175 | 205–205 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 200–200 | 205–205 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 75–75 | 45–45 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 90–90 | 60–60 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 100–100 | 70–70 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 125–125 | 95–95 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 150–150 | 120–120 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 175–175 | 145–145 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 200–200 | 145–145 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 75–75 | 80–80 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 90–90 | 100–100 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 100–100 | 110–110 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 125–125 | 135–135 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 150–150 | 160–160 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 175–175 | 185–185 | — | SASRI Information Sheet IS 7.2 |
| N | — | —–— — | 200–200 | 185–185 | — | SASRI Information Sheet IS 7.2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | 3rd fully-expanded leaf | Season/area-specific - see IS 7.15 table on page 3 | — | 1.7–1.9 | — | SASRI IS 7.15 |
| P | 3rd fully-expanded leaf | — | 0.19 | 0.19–0.24 | 0.4 | SASRI IS 7.15 |
| K | 3rd fully-expanded leaf | — | 1.05 | 1.05–1.59 | 1.79 | SASRI IS 7.15 |
| Ca | 3rd fully-expanded leaf | — | 0.15 | 0.15–0.38 | 0.59 | SASRI IS 7.15 |
| Mg | 3rd fully-expanded leaf | — | 0.08 | 0.08–0.18 | 0.34 | SASRI IS 7.15 |
| S | 3rd fully-expanded leaf | — | 0.12 | 0.12–0.23 | 0.39 | SASRI IS 7.15 |
| B | 3rd fully-expanded leaf | — | 10 | 10–20 | 35 | SASRI IS 7.15 |
| Zn | 3rd fully-expanded leaf | — | 13 | 13–24 | 75 | SASRI IS 7.15 |
| Fe | 3rd fully-expanded leaf | — | 75 | 75–99 | 300 | SASRI IS 7.15 |
| Mn | 3rd fully-expanded leaf | — | 15 | 15–99 | 250 | SASRI IS 7.15 |
| Cu | 3rd fully-expanded leaf | — | 3 | 3–7 | 12 | SASRI IS 7.15 |
| Mo | 3rd fully-expanded leaf | — | 0.08 | 0.08–1 | 1 | SASRI IS 7.15 |

_Extra leaf rows outside the canonical element set:_ `Si`

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | KZN coast / Mpumalanga | rainfed | 40 | 80 | 100 | t cane/ha | SASRI Crop Performance page |
| — | Pongola / Komati | irrigated | 100 | 120 | 140 | t cane/ha | SASRI Crop Performance page |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Primary method; heavy N and K feeder. Split N: plant crop and ratoons differ | — |
| band_place | False | ['N', 'P', 'K', 'S', 'Zn'] | At planting in furrow | — |
| side_dress | False | ['N', 'K', 'S'] | Ratoon topdress; N applied 6-8 weeks after harvest | — |
| fertigation | False | ['N', 'K', 'S'] | Under pivot irrigation | — |
| foliar | False | ['Zn', 'Fe', 'Mn', 'Si'] | Micronutrient correction; Si for stalk strength | — |



### Sunflower

<a id="sunflower"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 2.5 |
| Yield unit | t seed/ha |
| Population / ha | 0 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 28 |
| P | 3.7 |
| K | 6 |
| Ca | 4 |
| Mg | 3 |
| S | 3 |
| B | 0.05 |
| Zn | 0.06 |
| Fe | 0.4 |
| Mn | 0.06 |
| Cu | 0.015 |
| Mo | 0.008 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 6.5 | 7.5 | FERTASA 5.5.6 + ARC-GCI. T1. |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 5 | 10 | 14 | 25 | FERTASA 5.5.6.5: optimum 14 mg/kg. T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 20 | 60 | 100 | 120 | FERTASA 5.5.6.6 Ambic. T1. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.8 | 1.5 | 2.5 | High B requirement; B deficiency causes hollow stem and poor head fill. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

_Extra rows on this crop outside the canonical soil schema:_ `Acid Saturation`

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Emergence & establishment | 11–12 | 1 | 15 | 35 | 10 | 15 | 15 | band_place | P for root depth; B important |
| 2 | Vegetative growth | 1–1 | 2 | 35 | 25 | 25 | 25 | 25 | side_dress | Peak N for head diameter |
| 3 | Flowering | 2–2 | 1 | 25 | 20 | 25 | 30 | 30 | broadcast | B critical for seed set |
| 4 | Seed fill & maturation | 3–5 | 1 | 25 | 20 | 40 | 30 | 30 | broadcast | K for oil content |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | Ambic | 0–20 mg/kg | 1–1 | 16–16 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 0–20 mg/kg | 1.5–1.5 | 21–21 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 0–20 mg/kg | 2–2 | 27–27 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 0–20 mg/kg | 2.5–2.5 | 33–33 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 0–20 mg/kg | 3–3 | 39–39 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 20–40 mg/kg | 1–1 | 10–10 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 20–40 mg/kg | 1.5–1.5 | 15–15 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 20–40 mg/kg | 2–2 | 20–20 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 20–40 mg/kg | 2.5–2.5 | 25–25 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 20–40 mg/kg | 3–3 | 30–30 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 40–60 mg/kg | 1–1 | 7–7 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 40–60 mg/kg | 1.5–1.5 | 10–10 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 40–60 mg/kg | 2–2 | 14–14 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 40–60 mg/kg | 2.5–2.5 | 18–18 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 40–60 mg/kg | 3–3 | 22–22 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 60–80 mg/kg | 1–1 | 0–0 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 60–80 mg/kg | 1.5–1.5 | 8–8 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 60–80 mg/kg | 2–2 | 11–11 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 60–80 mg/kg | 2.5–2.5 | 14–14 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 60–80 mg/kg | 3–3 | 17–17 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 80–100 mg/kg | 1–1 | 0–0 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 80–100 mg/kg | 1.5–1.5 | 0–0 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 80–100 mg/kg | 2–2 | 9–9 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 80–100 mg/kg | 2.5–2.5 | 11–11 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 80–100 mg/kg | 3–3 | 14–14 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 100–— mg/kg | 1–1 | 0–0 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 100–— mg/kg | 1.5–1.5 | 0–0 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 100–— mg/kg | 2–2 | 0–0 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 100–— mg/kg | 2.5–2.5 | 0–0 | — | FERTASA Handbook 5.5.6 Table 3 |
| K | Ambic | 100–— mg/kg | 3–3 | 0–0 | — | FERTASA Handbook 5.5.6 Table 3 |
| N | — | —–— — | 1–1 | 20–20 | — | FERTASA Handbook 5.5.6 Table 1 |
| N | — | —–— — | 1.5–1.5 | 30–30 | — | FERTASA Handbook 5.5.6 Table 1 |
| N | — | —–— — | 2–2 | 40–40 | — | FERTASA Handbook 5.5.6 Table 1 |
| N | — | —–— — | 2.5–2.5 | 50–50 | — | FERTASA Handbook 5.5.6 Table 1 |
| N | — | —–— — | 3–3 | 60–60 | — | FERTASA Handbook 5.5.6 Table 1 |
| P | Bray-1 | 0–5 mg/kg | 1–1 | 12–12 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 0–5 mg/kg | 1.5–1.5 | 14–14 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 0–5 mg/kg | 2–2 | 16–16 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 0–5 mg/kg | 2.5–2.5 | 18–18 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 0–5 mg/kg | 3–3 | 20–20 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 5–10 mg/kg | 1–1 | 8–8 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 5–10 mg/kg | 1.5–1.5 | 10–10 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 5–10 mg/kg | 2–2 | 12–12 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 5–10 mg/kg | 2.5–2.5 | 14–14 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 5–10 mg/kg | 3–3 | 16–16 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 10–15 mg/kg | 1–1 | 4–4 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 10–15 mg/kg | 1.5–1.5 | 6–6 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 10–15 mg/kg | 2–2 | 8–8 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 10–15 mg/kg | 2.5–2.5 | 10–10 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 10–15 mg/kg | 3–3 | 12–12 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 15–20 mg/kg | 1–1 | 0–0 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 15–20 mg/kg | 1.5–1.5 | 3–3 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 15–20 mg/kg | 2–2 | 5–5 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 15–20 mg/kg | 2.5–2.5 | 7–7 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 15–20 mg/kg | 3–3 | 9–9 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 20–25 mg/kg | 1–1 | 0–0 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 20–25 mg/kg | 1.5–1.5 | 0–0 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 20–25 mg/kg | 2–2 | 3–3 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 20–25 mg/kg | 2.5–2.5 | 5–5 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 20–25 mg/kg | 3–3 | 7–7 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 25–— mg/kg | 1–1 | 0–0 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 25–— mg/kg | 1.5–1.5 | 0–0 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 25–— mg/kg | 2–2 | 2–2 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 25–— mg/kg | 2.5–2.5 | 4–4 | — | FERTASA Handbook 5.5.6 Table 2 |
| P | Bray-1 | 25–— mg/kg | 3–3 | 6–6 | — | FERTASA Handbook 5.5.6 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Uppermost mature leaf | Bud stage (R1) | — | 3–5 | — | IPNI 4R Sunflower + Yara UK Sunflower |
| P | Uppermost mature leaf | Bud stage | — | 0.25–0.5 | — | IPNI 4R Sunflower + Yara UK Sunflower |
| K | Uppermost mature leaf | Bud stage | — | 2–3.5 | — | IPNI 4R Sunflower + Yara UK Sunflower |
| Ca | Uppermost mature leaf | Bud stage | — | 1.5–3 | — | IPNI 4R Sunflower + Yara UK Sunflower |
| Mg | Uppermost mature leaf | Bud stage | — | 0.3–1 | — | IPNI 4R Sunflower + Yara UK Sunflower |
| S | Uppermost mature leaf | Bud stage | — | 0.25–0.6 | — | IPNI 4R Sunflower + Yara UK Sunflower |
| B | Uppermost mature leaf | Bud stage | — | 30–80 | — | IPNI 4R Sunflower + Yara UK Sunflower |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| grain | kg/t seed | 28 | 3.7 | 6 | — | — | — | 5.5.6 |
| stalks_leaves | kg/1.7t stalks | 7 | 1.4 | 85 | — | — | — | 5.5.6 |
| total | kg/t seed | 35 | 5.1 | 91 | — | — | — | 5.5.6 |
| seed | kg per t seed | 37 | 4.8 | 22.8 | 16.7 | 7.2 | — | FAO/IFA 1992 Ch.8 Sunflower + IPNI 4R Sunflower |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | North West / Free State | rainfed | 1 | 1.5 | 2.2 | t grain/ha | KZN-DARD Sunflower Production Tbl 1 |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At planting | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| side_dress | False | ['N', 'K', 'S'] | V6 topdress | — |
| foliar | False | ['B', 'Zn', 'Mn'] | B critical for head development | — |



### Sweet Melon

<a id="sweet-melon"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t fruit/ha |
| Population / ha | 8000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3 |
| P | 0.4 |
| K | 4.5 |
| Ca | 0.4 |
| Mg | 0.2 |
| S | 0.15 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | most-recent mature leaf | all stages | 4 | 4–5 | 5.5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| P | most-recent mature leaf | all stages | 0.3 | 0.3–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| K | most-recent mature leaf | all stages | 3 | 3–4 | 5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Ca | most-recent mature leaf | all stages | 1.2 | 1.2–2 | 3 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mg | most-recent mature leaf | all stages | 0.25 | 0.25–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| S | most-recent mature leaf | all stages | 0.2 | 0.2–0.75 | 1 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| B | most-recent mature leaf | all stages | 25 | 25–85 | 120 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Zn | most-recent mature leaf | all stages | 20 | 20–200 | 300 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Fe | most-recent mature leaf | all stages | 50 | 50–300 | — | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mn | most-recent mature leaf | all stages | 25 | 25–250 | 500 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Cu | most-recent mature leaf | all stages | 5 | 5–60 | 100 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

_No rows._



### Sweet Potato

<a id="sweet-potato"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 30 |
| Yield unit | t tuber/ha |
| Population / ha | 40000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3.5 |
| P | 0.5 |
| K | 6 |
| Ca | 0.3 |
| Mg | 0.3 |
| S | 0.25 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5 | 6 | 6.5 | DAFF Sweet Potato + ARC LNR Roodeplaat. T1. |
| pH (H2O) | 5 | 5.5 | 6.5 | 7 | DAFF Sweet Potato + ICAR-CTCRI. T1+T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 8 | 20 | 40 | 80 | DAFF Sweet Potato + Yara. T1+T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 250 | 400 | DAFF Sweet Potato + ICAR-CTCRI. T1+T2. |
| **Ca** | — | — | — | — | _needs source_ |
| Mg | 60 | 100 | 200 | 400 | UF/IFAS HS743 + Yara Sweet Potato. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & establishment | 10–11 | 1 | 15 | 35 | 10 | 15 | 15 | band_place | P for slip roots |
| 2 | Vine growth | 12–1 | 2 | 35 | 25 | 20 | 25 | 25 | side_dress | Moderate N; avoid excess |
| 3 | Tuber initiation & bulking | 2–4 | 2 | 30 | 25 | 40 | 35 | 35 | fertigation | K critical for tuber size |
| 4 | Maturation & harvest | 4–6 | 1 | 20 | 15 | 30 | 25 | 25 | broadcast | K for dry matter |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | NH4OAc | 0–80 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 80–150 mg/kg | 0–— | 50–50 | — | FERTASA Handbook 5.6.1 Table 3 |
| K | NH4OAc | 150–— mg/kg | 0–— | 30–30 | — | FERTASA Handbook 5.6.1 Table 3 |
| N | — | —–— — | 0–— | 80–120 | — | FERTASA Handbook 5.6.1 Table 1 |
| P | Bray-1 | 0–20 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 20–50 mg/kg | 0–— | 60–60 | — | FERTASA Handbook 5.6.1 Table 2 |
| P | Bray-1 | 50–— mg/kg | 0–— | 40–40 | — | FERTASA Handbook 5.6.1 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | petiole / 7th leaf from tip | mid-bulking | 3.5 | 4–5.5 | 6.5 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| P | petiole / 7th leaf from tip | mid-bulking | 0.2 | 0.25–0.5 | 0.7 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| K | petiole / 7th leaf from tip | mid-bulking | 3 | 3.5–6 | 7 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| Ca | petiole / 7th leaf from tip | mid-bulking | 0.5 | 0.7–1.5 | 2.5 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| Mg | petiole / 7th leaf from tip | mid-bulking | 0.25 | 0.3–0.8 | 1 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| S | petiole / 7th leaf from tip | mid-bulking | 0.15 | 0.2–0.4 | 0.6 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| B | petiole / 7th leaf from tip | mid-bulking | 25 | 30–80 | 120 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| Zn | petiole / 7th leaf from tip | mid-bulking | 15 | 20–60 | 150 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| Fe | petiole / 7th leaf from tip | mid-bulking | 40 | 50–300 | — | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| Mn | petiole / 7th leaf from tip | mid-bulking | 25 | 30–250 | 500 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| Cu | petiole / 7th leaf from tip | mid-bulking | 4 | 5–20 | 50 | ICAR-CTCRI Sweet Potato Bulletin + UF/IFAS HS743. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant; primary method | — |
| side_dress | False | ['N', 'K'] | Vine establishment topdress | — |
| foliar | False | ['B', 'Mn', 'Zn'] | Micronutrient correction | — |



### Sweetcorn

<a id="sweetcorn"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 20 |
| Yield unit | t fresh cobs/ha |
| Population / ha | 50000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 8.3 |
| P | 1 |
| K | 5.6 |
| Ca | 2 |
| Mg | 1.5 |
| S | 1 |
| B | 0.04 |
| Zn | 0.08 |
| Fe | 0.15 |
| Mn | 0.08 |
| Cu | 0.015 |
| Mo | 0.003 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting & emergence | 10–11 | 1 | 10 | 35 | 10 | 15 | 15 | band_place | Starter P; Zn important [aliased from Maize] |
| 2 | Vegetative growth (V6-VT) | 11–1 | 2 | 40 | 25 | 25 | 25 | 25 | side_dress | Peak N for leaf area and ear size [aliased from Maize] |
| 3 | Silking & pollination | 1–2 | 1 | 25 | 20 | 25 | 30 | 30 | fertigation | N for kernel number; B for silk; Zn for pollen [aliased from Maize] |
| 4 | Grain fill & maturation | 2–4 | 1 | 25 | 20 | 40 | 30 | 30 | broadcast | K for kernel weight and stalk strength [aliased from Maize] |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | Ambic | 0–10 mg/kg | 10–10 | 27–27 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 0–10 mg/kg | 15–15 | 45–45 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 0–10 mg/kg | 18–18 | 54–54 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 0–10 mg/kg | 25–25 | 82–82 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 0–10 mg/kg | 30–30 | 100–100 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 10–20 mg/kg | 10–10 | 20–20 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 10–20 mg/kg | 15–15 | 39–39 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 10–20 mg/kg | 18–18 | 47–47 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 10–20 mg/kg | 25–25 | 74–74 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 10–20 mg/kg | 30–30 | 92–92 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 20–40 mg/kg | 10–10 | 13–13 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 20–40 mg/kg | 15–15 | 31–31 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 20–40 mg/kg | 18–18 | 39–39 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 20–40 mg/kg | 25–25 | 64–64 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 20–40 mg/kg | 30–30 | 81–81 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 40–60 mg/kg | 10–10 | 8–8 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 40–60 mg/kg | 15–15 | 25–25 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 40–60 mg/kg | 18–18 | 33–33 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 40–60 mg/kg | 25–25 | 56–56 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 40–60 mg/kg | 30–30 | 71–71 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 60–80 mg/kg | 10–10 | 0–0 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 60–80 mg/kg | 15–15 | 21–21 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 60–80 mg/kg | 18–18 | 29–29 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 60–80 mg/kg | 25–25 | 50–50 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 60–80 mg/kg | 30–30 | 65–65 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 80–100 mg/kg | 10–10 | 0–0 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 80–100 mg/kg | 15–15 | 18–18 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 80–100 mg/kg | 18–18 | 25–25 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 80–100 mg/kg | 25–25 | 45–45 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 80–100 mg/kg | 30–30 | 59–59 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 100–— mg/kg | 10–10 | 0–0 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 100–— mg/kg | 15–15 | 15–15 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 100–— mg/kg | 18–18 | 22–22 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 100–— mg/kg | 25–25 | 41–41 | — | FERTASA Handbook 5.4.5 Table 3 |
| K | Ambic | 100–— mg/kg | 30–30 | 54–54 | — | FERTASA Handbook 5.4.5 Table 3 |
| N | — | —–— — | 10–10 | 70–70 | — | FERTASA Handbook 5.4.5 Table 1 |
| N | — | —–— — | 15–15 | 120–120 | — | FERTASA Handbook 5.4.5 Table 1 |
| N | — | —–— — | 18–18 | 145–145 | — | FERTASA Handbook 5.4.5 Table 1 |
| N | — | —–— — | 25–25 | 200–200 | — | FERTASA Handbook 5.4.5 Table 1 |
| N | — | —–— — | 30–30 | 240–240 | — | FERTASA Handbook 5.4.5 Table 1 |
| N | — | —–— — | 30–— | 240–240 | — | FERTASA Handbook 5.4.5 Table 1 |
| P | Bray-1 | 0–4 mg/kg | 10–10 | 65–65 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 0–4 mg/kg | 15–15 | 109–109 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 0–4 mg/kg | 18–18 | 130–130 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 0–4 mg/kg | 25–25 | 130–130 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 0–4 mg/kg | 30–30 | 130–130 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 4–8 mg/kg | 10–10 | 47–47 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 4–8 mg/kg | 15–15 | 78–78 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 4–8 mg/kg | 18–18 | 90–90 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 4–8 mg/kg | 25–25 | 97–97 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 4–8 mg/kg | 30–30 | 101–101 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 8–15 mg/kg | 10–10 | 30–30 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 8–15 mg/kg | 15–15 | 50–50 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 8–15 mg/kg | 18–18 | 59–59 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 8–15 mg/kg | 25–25 | 68–68 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 8–15 mg/kg | 30–30 | 72–72 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 15–21 mg/kg | 10–10 | 21–21 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 15–21 mg/kg | 15–15 | 36–36 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 15–21 mg/kg | 18–18 | 42–42 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 15–21 mg/kg | 25–25 | 53–53 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 15–21 mg/kg | 30–30 | 58–58 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 21–28 mg/kg | 10–10 | 15–15 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 21–28 mg/kg | 15–15 | 26–26 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 21–28 mg/kg | 18–18 | 31–31 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 21–28 mg/kg | 25–25 | 41–41 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 21–28 mg/kg | 30–30 | 48–48 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 28–— mg/kg | 10–10 | 12–12 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 28–— mg/kg | 15–15 | 18–18 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 28–— mg/kg | 18–18 | 21–21 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 28–— mg/kg | 25–25 | 30–30 | — | FERTASA Handbook 5.4.5 Table 2 |
| P | Bray-1 | 28–— mg/kg | 30–30 | 36–36 | — | FERTASA Handbook 5.4.5 Table 2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fresh cobs | 3 | 0.4 | 1.6 | — | — | — | 5.4.5 |
| stalks_leaves | kg/t fresh cobs | 5.3 | 0.6 | 4 | — | — | — | 5.4.5 |
| total | kg/t fresh cobs | 8.3 | 1 | 5.6 | — | — | — | 5.4.5 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S', 'Zn'] | At planting | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant | — |
| side_dress | False | ['N', 'K', 'S'] | V6 N topdress | — |
| fertigation | False | ['N', 'K', 'S'] | When irrigated | — |
| foliar | False | ['Zn', 'B', 'Mn', 'Fe'] | Zn correction | — |



### Table Grape

<a id="table-grape"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 25 |
| Yield unit | t fruit/ha |
| Population / ha | 2200 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 4 |
| P | 0.6 |
| K | 3.4 |
| Ca | 2 |
| Mg | 0.6 |
| S | 0.4 |
| B | 0.06 |
| Zn | 0.04 |
| Fe | 0.1 |
| Mn | 0.04 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5.5 | 6.5 | 7.5 | SATI Ch 3 p20 (Raath & Conradie). T1. |
| pH (H2O) | 5 | 6 | 7 | 8 | DERIVED from KCl + 1.0 (SATI offset). T1 derived. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 8 | 25 | 35 | 70 | SATI Ch 3 Tbl 1. T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 40 | 80 | 200 | 400 | Raath SATI Ch 3 Tbl 2: Orange River 120 max — higher than wine grape because juice pH is not a fresh-export concern. T1. |
| Ca | 200 | 360 | 1500 | 3000 | Raath SATI Ch 3 Tbl 3 (same as wine grape). T1. |
| Mg | 30 | 40 | 250 | 500 | Raath SATI Ch 3 Tbl 3. T1. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.2 | 0.3 | 1 | 2 | Raath SATI Ch 3 Tbl 5. T1. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest & leaf fall | 3–4 | 1 | 10 | 5 | 5 | 5 | 5 | broadcast | Reserve building [aliased from Grape (Table)] |
| 2 | Dormancy | 5–7 | 1 | 5 | 5 | 5 | 5 | 5 | broadcast | Pruning period; minimal uptake [aliased from Grape (Table)] |
| 3 | Bud break & bloom | 8–9 | 2 | 20 | 30 | 15 | 15 | 15 | fertigation | P for root flush; B for set [aliased from Grape (Table)] |
| 4 | Berry development | 10–11 | 3 | 40 | 35 | 30 | 45 | 45 | fertigation | N for berry size; Ca for firmness [aliased from Grape (Table)] |
| 5 | Veraison & harvest | 12–2 | 2 | 25 | 25 | 45 | 30 | 30 | fertigation | K for sugar and colour [aliased from Grape (Table)] |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Petiole opposite basal cluster | Full bloom | — | 1.6–2.4 | — | 5.3.3 |
| P | Petiole | Full bloom | — | 0.12–0.4 | — | 5.3.3 |
| K | Petiole | Full bloom | — | 0.8–1.6 | — | 5.3.3 |
| Ca | Petiole | Full bloom | — | 1.6–2.4 | — | 5.3.3 |
| Mg | Petiole | Full bloom | — | 0.3–0.6 | — | 5.3.3 |
| **S** | — | — | — | — | — | _needs source_ |
| B | Petiole | Full bloom | — | 30–65 | 400 | 5.3.3 |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| Mn | Petiole | Full bloom | — | 20–300 | 1000 | 5.3.3 |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fresh fruit | 4 | 0.65 | 3.4 | 2.07 | 0.83 | 0.6 | Conradie, Raath, Mulidzi & Howell 2022 SAJEV 43(1) |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–0 | 0.1 | 0.1 | 0.2 | 0.1 | Establishment |
| Year 2 | 1–1 | 0.35 | 0.35 | 0.4 | 0.3 | Canopy development |
| Year 3 | 2–2 | 0.65 | 0.65 | 0.65 | 0.6 | First bearing |
| Year 4+ | 3–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Hex River / Berg River / Olifants | irrigated | 15 | 30 | 50 | t fruit/ha | SATI 2023 industry report |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| fertigation | True | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary method for irrigated vineyards | — |
| broadcast | False | ['P', 'Ca', 'Mg', 'S'] | Dormancy amendments | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu', 'Ca', 'K'] | K foliar for colour; Ca for firmness; B for set | — |



### Tea

<a id="tea"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 3 |
| Yield unit | t made/ha |
| Population / ha | 10000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 40 |
| P | 2.5 |
| K | 15 |
| Ca | 5 |
| Mg | 3 |
| S | 2 |
| B | 0.1 |
| Zn | 0.06 |
| Fe | 0.4 |
| Mn | 0.08 |
| Cu | 0.03 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 3.8 | 4.2 | 5.5 | 6 | Acidophilic crop; optimal pH 4.5-5.5 KCl. Aluminium tolerant. |
| pH (H2O) | 4.3 | 4.7 | 6 | 6.5 | Acidophilic crop; optimal pH 5.0-5.8 H2O. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Winter dormancy | 5–8 | 1 | 10 | 15 | 10 | 15 | 15 | broadcast | Maintain soil health |
| 2 | Spring flush | 9–10 | 2 | 30 | 30 | 25 | 25 | 25 | broadcast | N for first flush quality |
| 3 | Main harvest season | 11–2 | 3 | 40 | 35 | 40 | 35 | 35 | fertigation | Peak N and K for yield |
| 4 | Late harvest & slowdown | 3–4 | 1 | 20 | 20 | 25 | 25 | 25 | broadcast | Taper feeding |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| **N** | — | — | — | — | — | _needs source_ |
| **P** | — | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| broadcast | True | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Primary; after each flush | — |
| fertigation | False | ['N', 'K', 'S'] | When irrigated | — |
| foliar | False | ['Zn', 'Mn', 'Cu', 'B'] | Micronutrient correction | — |



### Tobacco

<a id="tobacco"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 3 |
| Yield unit | t leaf/ha |
| Population / ha | 15000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 35 |
| P | 6 |
| K | 72 |
| Ca | 27 |
| Mg | 11 |
| S | 9 |
| B | 0.08 |
| Zn | 0.06 |
| Fe | 0.4 |
| Mn | 0.08 |
| Cu | 0.02 |
| Mo | 0.01 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.2 | 4.8 | 5.8 | 6.5 | Prefers slightly acid soil; optimal pH 5.0-5.8 KCl. |
| pH (H2O) | 4.7 | 5.3 | 6.3 | 7 | Prefers slightly acid soil for optimal nutrient balance. |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Transplant & establishment (all N ASAP) | 8–9 | 1 | 60 | 100 | 60 | 40 | 40 | band_place | FERTASA 5.11 (flue-cured): all N ASAP post-plant. K ONLY from SOP/KNO3 — chloride destroys leaf quality. Nitrate-N preferred (50% of basal + top-dresses nitrate only). |
| 2 | Vegetative (weeks 2-8) | 10–11 | 1 | 40 | 0 | 30 | 30 | 30 | broadcast | FERTASA 5.11: K top-dress as late as 2 weeks before topping. K 12x P requirement, 2.5x N requirement. |
| 3 | Topping / flowering | 11–12 | 0 | 0 | 0 | 10 | 20 | 20 | broadcast | FERTASA 5.11 (flue-cured): N already complete. Dark air-cured: last N at flower-bud initiation instead. |
| 4 | Leaf maturation / harvest | 1–4 | 0 | 0 | 0 | 0 | 10 | 10 | broadcast | FERTASA 5.11: S <2-3% in fertilizer compound (too much S harms burn quality). |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | Ambic | 0–25 mg/kg | 2–2 | 140–140 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 0–25 mg/kg | 2.5–2.5 | 175–175 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 0–25 mg/kg | 3–3 | 220–220 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 0–25 mg/kg | 4–4 | 280–280 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 25–50 mg/kg | 2–2 | 135–135 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 25–50 mg/kg | 2.5–2.5 | 165–165 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 25–50 mg/kg | 3–3 | 210–210 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 25–50 mg/kg | 4–4 | 270–270 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 50–75 mg/kg | 2–2 | 125–125 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 50–75 mg/kg | 2.5–2.5 | 155–155 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 50–75 mg/kg | 3–3 | 205–205 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 50–75 mg/kg | 4–4 | 260–260 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 75–100 mg/kg | 2–2 | 120–120 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 75–100 mg/kg | 2.5–2.5 | 145–145 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 75–100 mg/kg | 3–3 | 195–195 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 75–100 mg/kg | 4–4 | 250–250 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 100–125 mg/kg | 2–2 | 115–115 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 100–125 mg/kg | 2.5–2.5 | 135–135 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 100–125 mg/kg | 3–3 | 185–185 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 100–125 mg/kg | 4–4 | 240–240 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 125–150 mg/kg | 2–2 | 105–105 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 125–150 mg/kg | 2.5–2.5 | 125–125 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 125–150 mg/kg | 3–3 | 180–180 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 125–150 mg/kg | 4–4 | 230–230 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 150–— mg/kg | 2–2 | 100–100 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 150–— mg/kg | 2.5–2.5 | 120–120 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 150–— mg/kg | 3–3 | 170–170 | — | FERTASA Handbook 5.11 Table 7 |
| K | Ambic | 150–— mg/kg | 4–4 | 220–220 | — | FERTASA Handbook 5.11 Table 7 |
| P | Bray-1 | 0–10 mg/kg | 0–— | 120–120 | — | FERTASA Handbook 5.11 Table 6 |
| P | Bray-1 | 10–20 mg/kg | 0–— | 110–110 | — | FERTASA Handbook 5.11 Table 6 |
| P | Bray-1 | 20–30 mg/kg | 0–— | 100–100 | — | FERTASA Handbook 5.11 Table 6 |
| P | Bray-1 | 30–40 mg/kg | 0–— | 90–90 | — | FERTASA Handbook 5.11 Table 6 |
| P | Bray-1 | 40–50 mg/kg | 0–— | 80–80 | — | FERTASA Handbook 5.11 Table 6 |
| P | Bray-1 | 50–— mg/kg | 0–— | 70–70 | — | FERTASA Handbook 5.11 Table 6 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | mid-canopy leaf | topping | 3.5 | 3.5–5 | 5.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| P | mid-canopy leaf | topping | 0.25 | 0.25–0.5 | 0.55 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| K | mid-canopy leaf | topping | 2.5 | 2.5–4.5 | 5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Ca | mid-canopy leaf | topping | 1 | 1–3 | 4 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mg | mid-canopy leaf | topping | 0.25 | 0.25–1 | 1.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| S | mid-canopy leaf | topping | 0.25 | 0.25–0.6 | 0.8 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| B | mid-canopy leaf | topping | 25 | 25–75 | 100 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Zn | mid-canopy leaf | topping | 25 | 25–100 | 150 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Fe | mid-canopy leaf | topping | 50 | 50–250 | — | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mn | mid-canopy leaf | topping | 30 | 30–100 | 250 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Cu | mid-canopy leaf | topping | 5 | 5–25 | 50 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mo | mature leaf | mid-season | 0.2 | 0.2–1 | 2 | NC State Extension Tobacco Mo Deficiency. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| flue-cured | Limpopo / Mpumalanga | irrigated | 2 | 2.8 | 3.5 | t cured leaf/ha | NC State Tobacco + Virginia Tech 2024 |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.11 | 5.11 | 2017 | 1 | Cross-validated NC State Extension Tobacco Fertility (no T1 SA soil-Cl threshold published — confirmed gap; T2 fallback documented). |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At transplant | — |
| side_dress | False | ['N', 'K'] | Topping-stage topdress | — |
| foliar | False | ['B', 'Mo', 'Mn'] | Mo for leaf quality | — |



### Tobacco (Burley)

<a id="tobacco-burley"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | Tobacco |
| Default yield | 2.8 |
| Yield unit | t leaf/ha |
| Population / ha | 25000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 59 |
| P | 6 |
| K | 72 |
| Ca | 27 |
| Mg | 11 |
| S | 9 |
| B | 0.08 |
| Zn | 0.04 |
| Fe | 0.3 |
| Mn | 0.06 |
| Cu | 0.012 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | mid-canopy leaf | topping | 3.5 | 3.5–5 | 5.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| P | mid-canopy leaf | topping | 0.25 | 0.25–0.5 | 0.55 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| K | mid-canopy leaf | topping | 2.5 | 2.5–4.5 | 5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Ca | mid-canopy leaf | topping | 1 | 1–3 | 4 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mg | mid-canopy leaf | topping | 0.25 | 0.25–1 | 1.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| S | mid-canopy leaf | topping | 0.25 | 0.25–0.6 | 0.8 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| B | mid-canopy leaf | topping | 25 | 25–75 | 100 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Zn | mid-canopy leaf | topping | 25 | 25–100 | 150 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Fe | mid-canopy leaf | topping | 50 | 50–250 | — | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mn | mid-canopy leaf | topping | 30 | 30–100 | 250 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Cu | mid-canopy leaf | topping | 5 | 5–25 | 50 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mo | mature leaf | mid-season | 0.2 | 0.2–1 | 2 | NC State Extension. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| leaves | kg/t leaves | 59 | 6 | 72 | 27 | 11 | 9 | 5.11 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.11 | 5.11 | 2017 | 1 | Cross-validated NC State Extension Tobacco Fertility (no T1 SA soil-Cl threshold published — confirmed gap; T2 fallback documented). |

**Application methods** (`crop_application_methods`)

_No rows._



### Tobacco (Dark air-cured)

<a id="tobacco-dark-air-cured"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | Tobacco |
| Default yield | 2.4 |
| Yield unit | t leaf/ha |
| Population / ha | 25000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 69 |
| P | 6 |
| K | 72 |
| Ca | 27 |
| Mg | 11 |
| S | 9 |
| B | 0.08 |
| Zn | 0.04 |
| Fe | 0.3 |
| Mn | 0.06 |
| Cu | 0.012 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | — | —–— — | 2–2 | 190–190 | — | FERTASA Handbook 5.11 Table 5 |
| N | — | —–— — | 2.5–2.5 | 220–220 | — | FERTASA Handbook 5.11 Table 5 |
| N | — | —–— — | 3–3 | 250–250 | — | FERTASA Handbook 5.11 Table 5 |
| N | — | —–— — | 3–— | 250–250 | — | FERTASA Handbook 5.11 Table 5 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | mid-canopy leaf | topping | 3.5 | 3.5–5 | 5.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| P | mid-canopy leaf | topping | 0.25 | 0.25–0.5 | 0.55 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| K | mid-canopy leaf | topping | 2.5 | 2.5–4.5 | 5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Ca | mid-canopy leaf | topping | 1 | 1–3 | 4 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mg | mid-canopy leaf | topping | 0.25 | 0.25–1 | 1.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| S | mid-canopy leaf | topping | 0.25 | 0.25–0.6 | 0.8 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| B | mid-canopy leaf | topping | 25 | 25–75 | 100 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Zn | mid-canopy leaf | topping | 25 | 25–100 | 150 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Fe | mid-canopy leaf | topping | 50 | 50–250 | — | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mn | mid-canopy leaf | topping | 30 | 30–100 | 250 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Cu | mid-canopy leaf | topping | 5 | 5–25 | 50 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mo | mature leaf | mid-season | 0.2 | 0.2–1 | 2 | NC State Extension. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| leaves | kg/t leaves | 69 | 6 | 72 | 27 | 11 | 9 | 5.11 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.11 | 5.11 | 2017 | 1 | Cross-validated NC State Extension Tobacco Fertility (no T1 SA soil-Cl threshold published — confirmed gap; T2 fallback documented). |

**Application methods** (`crop_application_methods`)

_No rows._



### Tobacco (Flue-cured)

<a id="tobacco-flue-cured"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | Tobacco |
| Default yield | 3.5 |
| Yield unit | t leaf/ha |
| Population / ha | 25000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 35 |
| P | 6 |
| K | 72 |
| Ca | 27 |
| Mg | 11 |
| S | 9 |
| B | 0.08 |
| Zn | 0.04 |
| Fe | 0.3 |
| Mn | 0.06 |
| Cu | 0.012 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| N | clay-banded | 5–15 % | 3–4 | 120–140 | — | FERTASA 5.11.4 Tab 5.11.4 |
| N | clay-banded | 15–25 % | 3–4 | 90–120 | — | FERTASA 5.11.4 Tab 5.11.4 |
| N | clay-banded | 25–40 % | 3–4 | 80–90 | — | FERTASA 5.11.4 Tab 5.11.4 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | mid-canopy leaf | topping | 3.5 | 3.5–5 | 5.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| P | mid-canopy leaf | topping | 0.25 | 0.25–0.5 | 0.55 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| K | mid-canopy leaf | topping | 2.5 | 2.5–4.5 | 5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Ca | mid-canopy leaf | topping | 1 | 1–3 | 4 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mg | mid-canopy leaf | topping | 0.25 | 0.25–1 | 1.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| S | mid-canopy leaf | topping | 0.25 | 0.25–0.6 | 0.8 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| B | mid-canopy leaf | topping | 25 | 25–75 | 100 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Zn | mid-canopy leaf | topping | 25 | 25–100 | 150 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Fe | mid-canopy leaf | topping | 50 | 50–250 | — | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mn | mid-canopy leaf | topping | 30 | 30–100 | 250 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Cu | mid-canopy leaf | topping | 5 | 5–25 | 50 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mo | mature leaf | mid-season | 0.2 | 0.2–1 | 2 | NC State Extension. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| leaves | kg/t leaves | 35 | 6 | 72 | 27 | 11 | 9 | 5.11 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.11 | 5.11 | 2017 | 1 | Cross-validated NC State Extension Tobacco Fertility (no T1 SA soil-Cl threshold published — confirmed gap; T2 fallback documented). |

**Application methods** (`crop_application_methods`)

_No rows._



### Tobacco (Light air-cured)

<a id="tobacco-light-air-cured"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | Tobacco |
| Default yield | 2.4 |
| Yield unit | t leaf/ha |
| Population / ha | 25000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 43 |
| P | 6 |
| K | 72 |
| Ca | 27 |
| Mg | 11 |
| S | 9 |
| B | 0.08 |
| Zn | 0.04 |
| Fe | 0.3 |
| Mn | 0.06 |
| Cu | 0.012 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

_No rows._

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | mid-canopy leaf | topping | 3.5 | 3.5–5 | 5.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| P | mid-canopy leaf | topping | 0.25 | 0.25–0.5 | 0.55 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| K | mid-canopy leaf | topping | 2.5 | 2.5–4.5 | 5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Ca | mid-canopy leaf | topping | 1 | 1–3 | 4 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mg | mid-canopy leaf | topping | 0.25 | 0.25–1 | 1.5 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| S | mid-canopy leaf | topping | 0.25 | 0.25–0.6 | 0.8 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| B | mid-canopy leaf | topping | 25 | 25–75 | 100 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Zn | mid-canopy leaf | topping | 25 | 25–100 | 150 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Fe | mid-canopy leaf | topping | 50 | 50–250 | — | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mn | mid-canopy leaf | topping | 30 | 30–100 | 250 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Cu | mid-canopy leaf | topping | 5 | 5–25 | 50 | NC State Tobacco Production Guide + UTennessee Burley + UKentucky Burley. T2 cross-apply (Nicotiana tabacum same species globally). |
| Mo | mature leaf | mid-season | 0.2 | 0.2–1 | 2 | NC State Extension. T2. |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| leaves | kg/t leaves | 43 | 6 | 72 | 27 | 11 | 9 | 5.11 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

_No rows._

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | FERTASA 5.11 | 5.11 | 2017 | 1 | Cross-validated NC State Extension Tobacco Fertility (no T1 SA soil-Cl threshold published — confirmed gap; T2 fallback documented). |

**Application methods** (`crop_application_methods`)

_No rows._



### Tomato

<a id="tomato"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 80 |
| Yield unit | t fruit/ha |
| Population / ha | 25000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 3 |
| P | 0.75 |
| K | 4 |
| Ca | 0.3 |
| Mg | 0.2 |
| S | 0.2 |
| B | 0.005 |
| Zn | 0.005 |
| Fe | 0.02 |
| Mn | 0.005 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5.5 | 6 | 6.5 | UC ANR + UF/IFAS HS739. T2 derived. |
| pH (H2O) | 5 | 6 | 6.8 | 7.5 | UF/IFAS HS739 + DAFF Tomato Production. T1+T2. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 10 | 25 | 50 | 100 | UC ANR Tomato + Starke Ayres Tomato 2019. T1+T2. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 80 | 150 | 250 | 400 | UC ANR + Starke Ayres Tomato 2019. T1+T2. |
| Ca | 300 | 700 | 2500 | 5000 | High Ca requirement; adequate soil Ca reduces blossom end rot. |
| Mg | 80 | 150 | 300 | 500 | UF/IFAS HS739 + Yara Tomato. T2. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.3 | 0.5 | 1.5 | 3 | UC ANR (flower-set sensitive). T2. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Transplant & establishment | 9–10 | 1 | 10 | 30 | 10 | 15 | 15 | band_place | Starter P for transplant |
| 2 | Vegetative growth | 10–11 | 2 | 25 | 25 | 15 | 15 | 15 | fertigation | N for canopy |
| 3 | Flowering & fruit set | 11–12 | 3 | 25 | 20 | 25 | 35 | 35 | fertigation | Ca for BER; B for pollination |
| 4 | Fruit fill & harvest | 1–3 | 3 | 40 | 25 | 50 | 35 | 35 | fertigation | K for colour, firmness, flavour |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Most-recently-mature leaf | First flower / first cluster | — | 3–5 | 5.5 | UC Davis Geisseler tomato + UF/IFAS HS964 |
| P | Most-recently-mature leaf | First flower | — | 0.3–0.6 | 0.8 | UC Davis Geisseler + UF/IFAS HS964 |
| K | Most-recently-mature leaf | First flower | — | 2.5–4 | 5 | UC Davis Geisseler + UF/IFAS HS964 |
| Ca | Most-recently-mature leaf | First flower | — | 1.5–4 | 5 | UC Davis Geisseler + UF/IFAS HS964 |
| Mg | Most-recently-mature leaf | First flower | — | 0.4–1 | 1.5 | UC Davis Geisseler + UF/IFAS HS964 |
| S | Most-recently-mature leaf | First flower | — | 0.4–1.2 | — | UC Davis Geisseler + UF/IFAS HS964 |
| B | Most-recently-mature leaf | First flower | — | 30–80 | 100 | UC Davis Geisseler + UF/IFAS HS964 |
| Zn | Most-recently-mature leaf | First flower | — | 25–60 | 250 | UC Davis Geisseler + UF/IFAS HS964 |
| Fe | Most-recently-mature leaf | First flower | — | 60–300 | — | UC Davis Geisseler + UF/IFAS HS964 |
| Mn | Most-recently-mature leaf | First flower | — | 40–250 | 500 | UC Davis Geisseler + UF/IFAS HS964 |
| Cu | Most-recently-mature leaf | First flower | — | 6–20 | — | UC Davis Geisseler + UF/IFAS HS964 |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg/t fruit | 3 | 0.75 | 4 | — | — | — | 5.6.4 |
| total | kg/t fruit | 5.5 | 2.5 | 7.5 | — | — | — | 5.6.4 |
| fruit (open field) | kg per t fruit | 3 | 0.75 | 4 | — | — | — | Starke Ayres Tomato Production Guideline 2019 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| determinate (open field) | — | irrigated | 60 | 100 | 120 | t fruit/ha | Starke Ayres Tomato Production Guideline 2019 Tbl 4 |
| indeterminate (open field) | — | irrigated | 80 | 150 | 200 | t fruit/ha | Starke Ayres Tomato 2019 Tbls 5-6 |
| tunnel | — | tunnel | 120 | 250 | 500 | t fruit/ha | Starke Ayres Tomato 2019 Under Protection |
| cherry tunnel | — | tunnel | 80 | 150 | 250 | t fruit/ha | Haifa Crop Guide Tomato + UC Davis Geisseler Tomato |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | UF/IFAS HS739 + UC ANR | HS739 | 2024 | 2 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| fertigation | True | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary; drip essential for quality | — |
| broadcast | False | ['P', 'Ca', 'Mg', 'S'] | Pre-plant bed preparation | — |
| foliar | False | ['Ca', 'B', 'Fe', 'Mn', 'Zn', 'Cu'] | Ca for BER prevention; B for set | — |



### Watermelon

<a id="watermelon"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 40 |
| Yield unit | t fruit/ha |
| Population / ha | 5000 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 2.5 |
| P | 0.35 |
| K | 3.5 |
| Ca | 0.25 |
| Mg | 0.2 |
| S | 0.15 |
| B | 0.004 |
| Zn | 0.004 |
| Fe | 0.02 |
| Mn | 0.004 |
| Cu | 0.002 |
| Mo | 0.001 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| **pH (KCl)** | — | — | — | — | _needs source_ |
| **pH (H2O)** | — | — | — | — | _needs source_ |
| **N (total)** | — | — | — | — | _needs source_ |
| **P (Bray-1)** | — | — | — | — | _needs source_ |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| **K** | — | — | — | — | _needs source_ |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| **B** | — | — | — | — | _needs source_ |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Establishment | 10–10 | 1 | 10 | 30 | 10 | 15 | 15 | band_place | Starter P for roots |
| 2 | Vine growth | 11–12 | 2 | 30 | 25 | 20 | 20 | 20 | side_dress | N for vine extension |
| 3 | Flowering & fruit set | 12–1 | 2 | 25 | 20 | 25 | 30 | 30 | fertigation | B for pollination; Ca for rind |
| 4 | Fruit fill & harvest | 1–3 | 2 | 35 | 25 | 45 | 35 | 35 | fertigation | K for sugar and flesh colour |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | most-recent mature leaf | all stages | 4 | 4–5 | 5.5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| P | most-recent mature leaf | all stages | 0.3 | 0.3–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| K | most-recent mature leaf | all stages | 3 | 3–4 | 5 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Ca | most-recent mature leaf | all stages | 1.2 | 1.2–2 | 3 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mg | most-recent mature leaf | all stages | 0.25 | 0.25–1 | 1.2 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| S | most-recent mature leaf | all stages | 0.2 | 0.2–0.75 | 1 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| B | most-recent mature leaf | all stages | 25 | 25–85 | 120 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Zn | most-recent mature leaf | all stages | 20 | 20–200 | 300 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Fe | most-recent mature leaf | all stages | 50 | 50–300 | — | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Mn | most-recent mature leaf | all stages | 25 | 25–250 | 500 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| Cu | most-recent mature leaf | all stages | 5 | 5–60 | 100 | SCSB#394 p.69 Cucumber as cucurbit-family proxy. T2. |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

_No rows._

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| All-Sweet / Crimson Sweet | SA | irrigated | 30 | 40 | 60 | t fresh fruit/ha | SA Vegetable Farming portal + Starke Ayres Watermelon 2019. |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At planting | — |
| fertigation | False | ['N', 'K', 'Ca', 'Mg', 'S'] | Primary when irrigated | — |
| foliar | False | ['B', 'Ca', 'Mn', 'Zn'] | Ca for rind strength; B for set | — |



### Wheat

<a id="wheat"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | annual |
| Type (legacy) | Annual |
| Parent crop | — |
| Default yield | 5 |
| Yield unit | t grain/ha |
| Population / ha | 0 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 22.5 |
| P | 3.8 |
| K | 4.3 |
| Ca | 3 |
| Mg | 2.5 |
| S | 2.5 |
| B | 0.02 |
| Zn | 0.05 |
| Fe | 0.3 |
| Mn | 0.05 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 4.8 | 5.5 | 6.5 | FERTASA 5.4.3.1: <4.8 needs lime. WC minimum 5.0. T1. |
| pH (H2O) | 5 | 5.3 | 6 | 7 | DERIVED from KCl + 0.5. T1 derived. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 5 | 18 | 30 | 60 | FERTASA 5.4.3.1.2 banding: <5 deficient, 18-30 optimal. T1. |
| P (Citric acid) | 60 | 80 | 120 | 200 | FERTASA 5.4.3.1.3 banding. T1. |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 40 | 80 | 120 | 250 | FERTASA 5.4.3.1: NH4OAc 80-120 sufficient. T1. |
| **Ca** | — | — | — | — | _needs source_ |
| **Mg** | — | — | — | — | _needs source_ |
| S | — | 10 | 20 | — | FERTASA 5.4.3.2.3: <10 mg/kg = include S. T1. |
| **Na** | — | — | — | — | _needs source_ |
| B | — | 0.5 | 1 | — | FERTASA 5.4.3.2.7 hot-water B. T1. |
| Zn | 0.8 | 2 | 6 | 12 | Elevated Zn requirement; Zn deficiency common in SA wheat soils. |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| Cu | — | 0.5 | 1 | — | FERTASA 5.4.3.2.7 EDTA-Cu. T1. |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Planting to early tillering | 5–7 | 1 | 62 | 80 | 100 | 25 | 25 | band_place | FERTASA 5.4.3 irrigation Table 5.4.3.3.2. Dryland FS: ALL N here (no top-dress). Dryland WC: 25-30 kg N + balance later. Oats/barley: 65-70% of wheat N rate. |
| 2 | Early to late tillering | 6–8 | 1 | 19 | 15 | 0 | 25 | 25 | broadcast | FERTASA 5.4.3: potential ear number is most important yield component during tillering. |
| 3 | Flag leaf to flowering (protein boost) | 8–10 | 1 | 19 | 5 | 0 | 25 | 25 | broadcast | FERTASA 5.4.3: flag-leaf N increases grain protein by 1-1.5% (ARC-SGI Wheat Quality). |
| 4 | Grain fill & maturation | 10–11 | 0 | 0 | 0 | 0 | 25 | 25 | broadcast | Maturation phase. |

**Rate-table cells** (`fertilizer_rate_tables`)

| Nutrient | Soil method | Soil-test band | Yield band (t/ha) | Rate (kg/ha) | Filter | Source |
|---|---|---|---|---|---|---|
| K | Citric acid | 0–60 mg/kg | 1–2 | 20–20 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 0–60 mg/kg | 2–3 | 30–30 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 0–60 mg/kg | 3–4 | 40–40 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 0–60 mg/kg | 0–— | 0–0 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 60–80 mg/kg | 1–2 | 15–15 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 60–80 mg/kg | 2–3 | 20–20 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 60–80 mg/kg | 3–4 | 20–25 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 60–80 mg/kg | 0–— | 0–0 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 80–120 mg/kg | 1–2 | 15–15 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 80–120 mg/kg | 2–3 | 20–20 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 80–120 mg/kg | 3–4 | 20–25 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 80–120 mg/kg | 0–— | 0–0 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 120–— mg/kg | 1–2 | 0–0 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 120–— mg/kg | 2–3 | 0–0 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 120–— mg/kg | 3–4 | 0–0 | — | FERTASA Handbook 5.4.3.1.3 |
| K | Citric acid | 120–— mg/kg | 0–— | 0–0 | — | FERTASA Handbook 5.4.3.1.3 |
| N | — | —–— — | 4–5 | 80–130 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 5–6 | 130–160 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 6–7 | 160–180 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 7–8 | 180–200 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 8–— | 200–250 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 4–5 | 90–146 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 5–6 | 146–180 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 6–7 | 180–202 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 7–8 | 202–225 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 8–— | 225–281 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 4–5 | 70–114 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 5–6 | 114–140 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 6–7 | 140–158 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 7–8 | 158–175 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| N | — | —–— — | 8–— | 175–219 | Western Cape | FERTASA Handbook 5.4.3.2.2 |
| P | Bray-1 | 0–5 mg/kg | 1–1 | 6–6 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 0–5 mg/kg | 1.5–1.5 | 9–9 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 0–5 mg/kg | 2–2 | 12–12 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 0–5 mg/kg | 2.5–— | 15–18 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 5–18 mg/kg | 1–1 | 4–6 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 5–18 mg/kg | 1.5–1.5 | 7–9 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 5–18 mg/kg | 2–2 | 9–12 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 5–18 mg/kg | 2.5–— | 12–18 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 18–30 mg/kg | 1–1 | 4–4 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 18–30 mg/kg | 1.5–1.5 | 5–7 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 18–30 mg/kg | 2–2 | 7–9 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 18–30 mg/kg | 2.5–— | 9–15 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 30–— mg/kg | 1–1 | 4–4 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 30–— mg/kg | 1.5–1.5 | 5–5 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 30–— mg/kg | 2–2 | 7–7 | — | FERTASA Handbook 5.4.3.1.2 |
| P | Bray-1 | 30–— mg/kg | 2.5–— | 9–11 | — | FERTASA Handbook 5.4.3.1.2 |

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Flag leaf | Anthesis | — | 2.6–— | — | 5.3.4 |
| P | Flag leaf | Anthesis | — | 0.3–— | — | 5.3.4 |
| K | Flag leaf | Anthesis | — | 1.8–— | — | 5.3.4 |
| Ca | Flag leaf | Anthesis | — | 0.25–— | — | 5.3.4 |
| Mg | Flag leaf | Anthesis | — | 0.15–— | — | 5.3.4 |
| S | Flag leaf | Anthesis | 0.15 | 0.15–— | — | 5.3.4 |
| B | Flag leaf | Anthesis | — | 15–— | — | 5.3.4 |
| Zn | Flag leaf | Anthesis | — | 15–— | — | 5.3.4 |
| **Fe** | — | — | — | — | — | _needs source_ |
| Mn | Flag leaf | Anthesis | — | 30–— | — | 5.3.4 |
| **Cu** | — | — | — | — | — | _needs source_ |
| Mo | Flag leaf | Anthesis | — | 0.3–— | — | 5.3.4 |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| grain | kg/t grain | 22.5 | 3.8 | 4.3 | — | — | 2.5 | 5.4.3 |
| straw | kg/t grain | 5 | 1 | 8.6 | — | — | 2 | 5.4.3 |
| total | kg/t grain | 27 | 4.8 | 12.9 | — | — | 1.5 | 5.4.3 |

**Perennial age factors** (`perennial_age_factors`)

_No rows._

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape Rûens | rainfed | 1.8 | 3.5 | 5.5 | t grain/ha | ARC-Small Grain Bethlehem/Rûens calibrations |
| — | Vaalharts / Douglas | irrigated | 6.5 | 8.5 | 11 | t grain/ha | GrainSA Irrigated wheat |

**Calc flags** (`crop_calc_flags`)

_No rows._

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| band_place | True | ['N', 'P', 'K', 'S'] | At planting; starter band | — |
| broadcast | False | ['N', 'P', 'K', 'Ca', 'Mg', 'S'] | Pre-plant or topdress | — |
| side_dress | False | ['N', 'S'] | Tillering topdress | — |
| foliar | False | ['Mn', 'Cu', 'Zn'] | Mn and Cu deficiency correction | — |



### Wine Grape

<a id="wine-grape"></a>

**Base requirements** (`crop_requirements`)

| Field | Value |
|---|---|
| Crop type | perennial |
| Type (legacy) | Perennial |
| Parent crop | — |
| Default yield | 12 |
| Yield unit | t fruit/ha |
| Population / ha | 3300 |
| Years to bearing | — |
| Years to full bearing | — |
| N (target/uptake) | 5 |
| P | 0.6 |
| K | 5.5 |
| Ca | 2.5 |
| Mg | 0.8 |
| S | 0.5 |
| B | 0.06 |
| Zn | 0.04 |
| Fe | 0.12 |
| Mn | 0.04 |
| Cu | 0.01 |
| Mo | 0.005 |
| Customer-ready flag | True |

**Soil sufficiency bands** (`crop_sufficiency_overrides`)

_Engine merges these on top of universal `soil_sufficiency`. Bold rows are gaps — generic bands apply until a citation is added._

| Parameter | Very Low ≤ | Low ≤ | Optimal ≤ | High ≤ | Source / notes |
|---|---|---|---|---|---|
| pH (KCl) | 4.5 | 5.5 | 6.5 | 7.5 | Raath & Conradie SATI Ch 3 p20: optimal 5.5-6.5. T1. |
| pH (H2O) | 5 | 6 | 7 | 8 | DERIVED from KCl + 1.0 (SATI offset, grape-specific). T1 derived. |
| **N (total)** | — | — | — | — | _needs source_ |
| P (Bray-1) | 8 | 20 | 35 | 70 | Raath SATI Ch 3 Tbl 1: sandy 20 / loamy 25 / clayey 30 mg/kg minimum. T1. |
| **P (Citric acid)** | — | — | — | — | _needs source_ |
| **P (Olsen)** | — | — | — | — | _needs source_ |
| K | 30 | 60 | 100 | 150 | Raath SATI Ch 3 Tbl 2 max norms — Coastal 70, Breede 80, Olifants/Karoo 100. EXCESS RAISES JUICE pH — wine quality cap. T1. |
| Ca | 200 | 360 | 1500 | 3000 | Raath SATI Ch 3 Tbl 3: 360 sandy / 500 clayey minimum. T1. |
| Mg | 30 | 40 | 250 | 500 | Raath SATI Ch 3 Tbl 3. Ca:Mg ≤ 6 ratio rule. T1. |
| **S** | — | — | — | — | _needs source_ |
| **Na** | — | — | — | — | _needs source_ |
| B | 0.2 | 0.3 | 1 | 2 | Raath SATI Ch 3 Tbl 5: ≥0.3 mg/kg hot-water minimum. T1. |
| **Zn** | — | — | — | — | _needs source_ |
| **Fe** | — | — | — | — | _needs source_ |
| **Mn** | — | — | — | — | _needs source_ |
| **Cu** | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | _needs source_ |
| **Org C** | — | — | — | — | _needs source_ |
| **CEC** | — | — | — | — | _needs source_ |

**Growth stages** (`crop_growth_stages`)

| # | Stage | Months | Apps | N % | P % | K % | Ca % | Mg % | Method | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Post-harvest & leaf fall | 4–5 | 1 | 10 | 5 | 5 | 5 | 5 | broadcast | Reserve replenishment [aliased from Grape (Wine)] |
| 2 | Dormancy | 6–7 | 1 | 5 | 5 | 5 | 5 | 5 | broadcast | Winter rest; pruning [aliased from Grape (Wine)] |
| 3 | Bud break & bloom | 8–9 | 2 | 25 | 30 | 15 | 15 | 15 | fertigation | Moderate inputs; avoid excess vigour [aliased from Grape (Wine)] |
| 4 | Berry development | 10–12 | 3 | 35 | 35 | 30 | 45 | 45 | fertigation | Ca for skin integrity [aliased from Grape (Wine)] |
| 5 | Veraison & harvest | 1–4 | 1 | 25 | 25 | 45 | 30 | 30 | fertigation | K for phenolics; restrict N for quality [aliased from Grape (Wine)] |

**Rate-table cells** (`fertilizer_rate_tables`)

_No rows._

**Leaf norms** (`fertasa_leaf_norms`)

| Element | Part | Timing | Low ≤ | Sufficient | Excess ≥ | Source / notes |
|---|---|---|---|---|---|---|
| N | Petiole opposite basal cluster | Full bloom | — | 1.6–2.4 | — | 5.3.3 |
| P | Petiole | Full bloom | — | 0.12–0.4 | — | 5.3.3 |
| K | Petiole | Full bloom | — | 0.8–1.6 | — | 5.3.3 |
| Ca | Petiole | Full bloom | — | 1.6–2.4 | — | 5.3.3 |
| Mg | Petiole | Full bloom | — | 0.3–0.6 | — | 5.3.3 |
| **S** | — | — | — | — | — | _needs source_ |
| B | Petiole | Full bloom | — | 30–65 | 400 | 5.3.3 |
| **Zn** | — | — | — | — | — | _needs source_ |
| Fe | Petiole | Full bloom | — | 60–240 | — | 5.3.3 |
| Mn | Petiole | Full bloom | — | 20–300 | 1000 | 5.3.3 |
| **Cu** | — | — | — | — | — | _needs source_ |
| **Mo** | — | — | — | — | — | _needs source_ |

**Nutrient removal** (`fertasa_nutrient_removal`)

| Part | Per | N | P | K | Ca | Mg | S | Source / notes |
|---|---|---|---|---|---|---|---|---|
| fruit | kg per t fresh fruit | 2.1 | 0.45 | 5 | 1.4 | 0.7 | 0.6 | Haifa Vineyard fertilization + UC Davis Geisseler Grapevines |

**Perennial age factors** (`perennial_age_factors`)

| Age label | Age range (yr) | General | N | P | K | Notes |
|---|---|---|---|---|---|---|
| Year 1 | 0–0 | 0.1 | 0.1 | 0.2 | 0.1 | Establishment |
| Year 2 | 1–1 | 0.35 | 0.35 | 0.4 | 0.3 | Canopy development |
| Year 3 | 2–2 | 0.65 | 0.65 | 0.65 | 0.6 | First bearing |
| Year 4+ | 3–99 | 1 | 1 | 1 | 1 | Full bearing |

**Yield benchmarks** (`crop_yield_benchmarks`)

| Cultivar | Region | Water regime | Low t/ha | Typical t/ha | High t/ha | Unit | Source |
|---|---|---|---|---|---|---|---|
| — | Western Cape | irrigated | 4 | 10 | 18 | t fruit/ha | Vinpro 2023 Harvest Report |
| — | Stellenbosch / Hemel-en-Aarde | rainfed | 4 | 7 | 12 | t fruit/ha | Vinpro 2023 — premium estate band |

**Calc flags** (`crop_calc_flags`)

| skip_cation_ratio_path | Source | Section | Year | Tier | Note |
|---|---|---|---|---|---|
| False | Saayman & Lambrechts 1995 SAJEV 16(2) | n/a | 1995 | 3 | — |

**Application methods** (`crop_application_methods`)

| Method | Default | Nutrients suited | Timing | Crop notes |
|---|---|---|---|---|
| fertigation | True | ['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'] | Primary for irrigated; careful N management | — |
| broadcast | False | ['P', 'Ca', 'Mg', 'S'] | Dormancy amendments; conservative N | — |
| foliar | False | ['Fe', 'B', 'Mn', 'Zn', 'Cu'] | B for set; micronutrient correction | — |


