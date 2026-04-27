-- 087_research_2026-04-27_seed.sql
--
-- Seeds extracted from /sapling-api/data/research_2026-04-27/*.md
-- Quality bar: T1 SA institutional + T3 SA peer-reviewed when no T1 exists.
-- Skipped: GAP rows, flagged anomalies, conflict rows, duplicates against
-- existing DB state at 2026-04-27.
--
-- Counts (applied via Supabase MCP):
--   fertasa_leaf_norms:       +11 rows (1 new crop: Pecan; Mo row dropped on review)
--   crop_yield_benchmarks:    +49 rows across 32 crops (multi-regime where data allows)
--   fertasa_soil_norms:       +25 rows (Wine/Table Grape, Sugarcane, Lucerne, Rooibos, Cotton, Pecan)
--   fertasa_nutrient_removal: +6  rows (Maize grain, Dry bean seed, Lucerne fresh, Tomato fruit, Sweet pepper fruit open + tunnel)
--   perennial_age_factors:    +0  rows (every candidate already covered by existing 87 rows)

BEGIN;

-- ── Leaf norms ──────────────────────────────────────────────────────
-- Schmidt 2021 ARC-ITSC Pecan chapter (FERTASA companion). Schmidt explicitly
-- recommends the Georgia analogue table for SA subtropical pecan growing
-- regions — treated as T1 SA-adapted reference.
-- Mo row dropped on review: source cited Ni essentiality (different nutrient);
-- 2.5 mg/kg far above typical Mo sufficiency (0.1-0.5 mg/kg).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Pecan', 'N',  '%',     2.05, NULL, 2.50, 3.00, 3.01, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted'),
  ('Pecan', 'P',  '%',     0.10, NULL, 0.14, 0.30, 0.31, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted'),
  ('Pecan', 'K',  '%',     0.90, NULL, 1.30, 2.50, 2.51, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted; target N:K 2:1'),
  ('Pecan', 'Ca', '%',     0.90, NULL, 1.30, 1.75, 1.76, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted'),
  ('Pecan', 'Mg', '%',     0.30, NULL, 0.35, 0.60, 0.61, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted'),
  ('Pecan', 'S',  '%',     0.14, NULL, 0.25, 0.50, NULL, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted'),
  ('Pecan', 'Zn', 'mg/kg', 50,   NULL, 50,   100,  101,  NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted'),
  ('Pecan', 'Fe', 'mg/kg', 50,   NULL, 50,   300,  NULL, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted'),
  ('Pecan', 'Mn', 'mg/kg', NULL, NULL, 100,  800,  NULL, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted'),
  ('Pecan', 'Cu', 'mg/kg', 6,    NULL, 6,    30,   NULL, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted'),
  ('Pecan', 'B',  'mg/kg', 50,   NULL, 50,   100,  NULL, NULL,
   'Middle leaflets, mid-shoot', '120-150 days after flowering',
   'Schmidt 2021 ARC-ITSC Tbl 3 (Georgia)', 'T1 SA-adapted')
ON CONFLICT DO NOTHING;

-- ── Yield benchmarks: tree fruit / grapes / berries / field / specialty ──
-- source_tier follows memory rule: T1 = SA institutional (FERTASA, SAMAC,
-- SASRI, SATI, Vinpro, Cotton SA, GrainSA, Hortgro, ARC, NWPG, KZN-DARD,
-- DALRRD, Cotton SA, Starke Ayres, etc.); T2 = international parallels +
-- SA industry press (Farmers Weekly, Berries for Africa); T3 = SA peer-
-- reviewed (SAJPS, SAJEV, MSc theses).
INSERT INTO crop_yield_benchmarks
  (crop, cultivar, irrigation_regime, yield_unit, low_t_per_ha, typical_t_per_ha, high_t_per_ha,
   region, source, source_tier, notes) VALUES
  ('Apple',     NULL, 'irrigated', 't fruit/ha', 35,  65,  110, 'Western Cape', 'Hortgro Key Deciduous Fruit Statistics 2024', 'T1', 'Hortgro budget assumes 65 t/ha at 1667 trees/ha; high-density M.9/M.26 80-110'),
  ('Pear',      NULL, 'irrigated', 't fruit/ha', 30,  55,  80,  'Western Cape', 'Hortgro Key Deciduous Fruit Statistics 2024', 'T1', '1667 trees/ha typical'),
  ('Plum',      NULL, 'irrigated', 't fruit/ha', 18,  30,  50,  'Western Cape', 'Hortgro Key Deciduous Fruit Statistics 2024', 'T1', '1524 trees/ha V-trellis'),
  ('Peach',     NULL, 'irrigated', 't fruit/ha', 12,  25,  45,  'Western Cape', 'Hortgro Key Deciduous Fruit Statistics 2024', 'T1', '1250 trees/ha'),
  ('Nectarine', NULL, 'irrigated', 't fruit/ha', 12,  25,  45,  'Western Cape', 'Hortgro Key Deciduous Fruit Statistics 2024', 'T1', '1250 trees/ha'),
  ('Apricot',   NULL, 'irrigated', 't fruit/ha', 10,  20,  30,  'Klein Karoo',  'Hortgro Key Deciduous Fruit Statistics 2024', 'T1', '1250 trees/ha'),
  ('Cherry',    NULL, 'irrigated', 't fruit/ha', 6,   12,  20,  'Ceres / Free State / Mpumalanga', 'Hortgro Key Deciduous Fruit Statistics 2024', 'T1', '1667 trees/ha; high-density Gisela 15-20'),
  ('Wine Grape', NULL, 'irrigated', 't fruit/ha', 4,  10,  18,  'Western Cape', 'Vinpro 2023 Harvest Report', 'T1', 'Premium 7-12; cap for Cab/Shiraz <=10'),
  ('Wine Grape', NULL, 'rainfed',   't fruit/ha', 4,  7,   12,  'Stellenbosch / Hemel-en-Aarde', 'Vinpro 2023 — premium estate band', 'T1', 'Low-N flagship sites'),
  ('Table Grape', NULL, 'irrigated', 't fruit/ha', 15, 30,  50, 'Hex River / Berg River / Olifants', 'SATI 2023 industry report', 'T1', '25-35 typical export; 35-50 high-input'),
  ('Blueberry', NULL, 'tunnel',    't fruit/ha', 2,  14,  25,  'Western Cape / KZN / Limpopo', 'Berries for Africa cv notes; Farmers Weekly SA blueberry guide', 'T1', 'Mature SHB SA 10-18; high-tunnel 18-25'),
  ('Maize',     NULL, 'rainfed',   't grain/ha', 2.5, 4.5, 8.0, 'Highveld', 'GrainSA archives', 'T1', 'White + yellow combined'),
  ('Maize',     NULL, 'irrigated', 't grain/ha', 8.0, 11.0, 14.0, 'Vaalharts / Douglas', 'Pannar Irrigated Maize Mgmt; ARC-GCI', 'T1', NULL),
  ('Wheat',     NULL, 'rainfed',   't grain/ha', 1.8, 3.5, 5.5, 'Western Cape Rûens', 'ARC-Small Grain Bethlehem/Rûens calibrations', 'T1', 'Winter wheat'),
  ('Wheat',     NULL, 'irrigated', 't grain/ha', 6.5, 8.5, 11.0, 'Vaalharts / Douglas', 'GrainSA Irrigated wheat', 'T1', NULL),
  ('Soybean',   NULL, 'rainfed',   't grain/ha', 1.5, 2.5, 3.5, 'Mpumalanga / KZN', 'GrainSA cultivar trials; FAO 3-4 t/ha', 'T1', NULL),
  ('Soybean',   NULL, 'irrigated', 't grain/ha', 3.0, 4.0, 5.0, NULL, 'GrainSA cultivar trials', 'T1', NULL),
  ('Sunflower', NULL, 'rainfed',   't grain/ha', 1.0, 1.5, 2.2, 'North West / Free State', 'KZN-DARD Sunflower Production Tbl 1', 'T1', 'Yields scale with soil depth x rainfall'),
  ('Canola',    NULL, 'rainfed',   't grain/ha', 1.0, 1.8, 2.5, 'Western Cape Rûens', 'Hardy & Strauss SAJPS 2014 31(2)', 'T3', '>2.0 t/ha needs 120 N + 15-30 S'),
  ('Canola',    NULL, 'irrigated', 't grain/ha', 2.0, 3.0, 4.0, 'Central Free State', 'SAJPS 2024 Nel et al.', 'T3', NULL),
  ('Sorghum',   NULL, 'rainfed',   't grain/ha', 1.0, 2.0, 3.5, 'Free State', 'GrainSA — Free State produces 50% of SA sorghum', 'T1', NULL),
  ('Malting Barley', NULL, 'rainfed',   't grain/ha', 2.5, 4.0, 5.3, 'Caledon (Western Cape)', 'Khumalo MSc Stellenbosch 2020', 'T3', '80 kg N/ha gave 5.29 t/ha at Caledon'),
  ('Malting Barley', NULL, 'irrigated', 't grain/ha', 5.0, 7.0, 9.0, 'Northern Cape / Vaalharts', 'SABBI Irrigation Guidelines for Malting Barley 2012', 'T1', 'Hard cap on grain N <=1.8% for malting'),
  ('Bean (Dry)', NULL, 'rainfed',   't grain/ha', 0.8, 1.5, 2.5, 'Mpumalanga / KZN', 'ARC-GCI dry bean cultivar trials', 'T1', NULL),
  ('Bean (Dry)', NULL, 'irrigated', 't grain/ha', 2.0, 3.0, 3.5, NULL, 'ARC-GCI dry bean cultivar trials', 'T1', NULL),
  ('Sugarcane', NULL, 'rainfed',   't cane/ha',  40,  80,  100, 'KZN coast / Mpumalanga', 'SASRI Crop Performance page', 'T1', 'Typical 70-90; rainfed marginal 40-60'),
  ('Sugarcane', NULL, 'irrigated', 't cane/ha',  100, 120, 140, 'Pongola / Komati', 'SASRI Crop Performance page', 'T1', NULL),
  ('Lucerne',   NULL, 'rainfed',   't DM/ha',    5,   8,   10,  'Karoo / Western Cape', 'van Heerden 1993 IGC', 'T3', '4-6 cuts/yr'),
  ('Lucerne',   NULL, 'irrigated', 't DM/ha',    15,  20,  30,  'Northern Cape / W Free State', 'Farmer''s Weekly W Free State; SA Lucerne industry', 'T2', '7+ cuts/yr; high-input 18-30'),
  ('Cotton',    NULL, 'rainfed',   't seed cotton/ha', 1.2, 1.75, 2.0, NULL, 'Cotton SA Technical Information', 'T1', 'Dryland low 1.2; typical 1.5-2.0'),
  ('Cotton',    NULL, 'irrigated', 't seed cotton/ha', 3.6, 4.5, 5.0, NULL, 'Cotton SA Technical Information', 'T1', '16-23 lint bales/ha'),
  ('Olive',     NULL, 'irrigated', 't fruit/ha', 5,   8,   20,  'Western Cape', 'SA Olive Association Olive Growing', 'T1', 'Typical 5-10 at 250-400 trees/ha; SHD >1200 = 12-20'),
  ('Olive',     NULL, 'rainfed',   't fruit/ha', 2,   3,   4,   'Western Cape', 'SA Olive Association Olive Growing', 'T1', 'Rainfed traditional / off year'),
  ('Rooibos',   NULL, 'rainfed',   't dry leaf/ha', 0.25, 0.5, 1.2, 'Cederberg', 'Klipopmekaar; Farmers Magazine SA 2025', 'T2', 'Cederberg avg 0.4-0.6; high-input up to 1.2')
ON CONFLICT DO NOTHING;

-- Vegetables — Starke Ayres T1 yield bands (2019 production guidelines).
INSERT INTO crop_yield_benchmarks
  (crop, cultivar, irrigation_regime, yield_unit, low_t_per_ha, typical_t_per_ha, high_t_per_ha,
   region, source, source_tier, notes) VALUES
  ('Tomato',       'determinate (open field)',     'irrigated', 't fruit/ha', 60,  100, 120, NULL, 'Starke Ayres Tomato Production Guideline 2019 Tbl 4', 'T1', '18-week cycle, 12-18k plants/ha'),
  ('Tomato',       'indeterminate (open field)',   'irrigated', 't fruit/ha', 80,  150, 200, NULL, 'Starke Ayres Tomato 2019 Tbls 5-6', 'T1', '20-25 week cycle'),
  ('Tomato',       'tunnel',                       'tunnel',    't fruit/ha', 120, 250, 500, NULL, 'Starke Ayres Tomato 2019 Under Protection', 'T1', '20-28k plants/ha tunnel'),
  ('Sweet pepper', 'open field',                   'irrigated', 't fruit/ha', 20,  60,  140, NULL, 'Starke Ayres Sweet & Hot Pepper 2019 Tbl 4', 'T1', '30k plants/ha'),
  ('Sweet pepper', 'tunnel',                       'tunnel',    't fruit/ha', 50,  100, 200, NULL, 'Starke Ayres Sweet & Hot Pepper 2019 Tbl 5', 'T1', 'Up to 35k plants/ha tunnel'),
  ('Onion',        'dry bulb',                     'irrigated', 't bulb/ha',  30,  70,  110, NULL, 'Starke Ayres Onion Production Guideline 2019', 'T1', '700-800k plants/ha'),
  ('Cabbage',      'pre-pack (35-45k plants/ha)',  'irrigated', 't head/ha',  50,  100, 120, NULL, 'Starke Ayres Cabbage 2019', 'T1', NULL),
  ('Carrot',       'hybrid commercial',            'irrigated', 't root/ha',  30,  60,  100, NULL, 'Starke Ayres Carrot 2019', 'T1', 'OP 30-40; hybrid 50-70; top 100'),
  ('Lettuce',      'Crisphead',                    'irrigated', 't head/ha',  30,  45,  60,  NULL, 'Starke Ayres Lettuce 2019', 'T1', '45-60k plants × ~700g head'),
  ('Butternut',    NULL,                           'irrigated', 't fruit/ha', 15,  25,  35,  NULL, 'Starke Ayres Butternut 2019', 'T1', '14-18k plants/ha'),
  ('Pumpkin',      'vining',                       'irrigated', 't fruit/ha', 20,  30,  40,  NULL, 'Starke Ayres Pumpkin & Hubbard Squash 2019', 'T1', '5000 plants/ha'),
  ('Sweet corn',   NULL,                           'irrigated', 't cob/ha',   8,   11,  14,  NULL, 'Starke Ayres Sweet Corn 2019', 'T1', 'Cobs fresh weight'),
  ('Broccoli',     NULL,                           'irrigated', 't head/ha',  8,   12,  15,  NULL, 'Starke Ayres Broccoli 2019', 'T1', '30-40k plants × ~0.4 kg head'),
  ('Cauliflower',  NULL,                           'irrigated', 't head/ha',  8,   12,  15,  NULL, 'Starke Ayres Cauliflower 2019', 'T1', NULL),
  ('Chillies',     NULL,                           'irrigated', 't fresh fruit/ha', 5,  20,  80, NULL, 'KZN-DARD Capsicums Production Guide; Haifa Pepper Guide as upper-bound', 'T1', 'Dryland 5-10; typical irrigated 15-25; high-tech tunnel 40-80')
ON CONFLICT DO NOTHING;

-- ── Soil norms ──────────────────────────────────────────────────────
-- pH rows store unit='-' to satisfy the table's NOT NULL unit constraint
-- (matches existing pattern for Macadamia/Avocado/Citrus pH rows).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Wine Grape', 'pH (KCl)',     NULL, 5.5,  6.5,  '-',     NULL,        'Conradie 1994 via Wineland', 'T1 SA-canonical'),
  ('Wine Grape', 'P (Bray-1)',   NULL, 25,   35,   'mg/kg', 'Bray-1',    'SATI handbook 2019; Conradie 1994', 'T1; sandy → sandy clay loam'),
  ('Wine Grape', 'K',            NULL, 70,   120,  'mg/kg', 'NH4-OAc',   'SATI handbook 2019',   'T1'),
  ('Wine Grape', 'Ca',           NULL, 360,  500,  'mg/kg', 'NH4-OAc',   'SATI handbook 2019',   'T1; sandy band'),
  ('Wine Grape', 'Mg',           NULL, 40,   120,  'mg/kg', 'NH4-OAc',   'SATI handbook 2019',   'T1'),
  ('Wine Grape', 'B',            NULL, 0.3,  1.0,  'mg/kg', 'hot-water', 'SATI handbook 2019',   'T1'),
  ('Table Grape', 'pH (KCl)',    NULL, 5.5,  6.5,  '-',     NULL,        'SATI handbook 2019',   'T1'),
  ('Table Grape', 'P (Bray-1)',  NULL, 25,   35,   'mg/kg', 'Bray-1',    'SATI handbook 2019',   'T1; 4.5 kg P/ha per 1 mg/kg increase'),
  ('Table Grape', 'B',           NULL, 0.3,  NULL, 'mg/kg', 'hot-water', 'SATI handbook 2019',   'T1; minimum'),
  ('Sugarcane',  'pH (KCl)',     NULL, 4.5,  5.5,  '-',     NULL,        'SASRI Crop Nutrition page', 'T1; <4.0 Al toxicity'),
  ('Sugarcane',  'K',            NULL, 0.15, 0.25, 'cmol+/kg', 'AMBIC-2', 'SASRI Crop Nutrition page', 'T1; SASRI uses Ambic-2'),
  ('Sugarcane',  'Ca',           NULL, 4,    8,    'cmol+/kg', 'AMBIC-2', 'SASRI Crop Nutrition page', 'T1'),
  ('Sugarcane',  'Mg',           NULL, 0.8,  1.5,  'cmol+/kg', 'AMBIC-2', 'SASRI Crop Nutrition page', 'T1'),
  ('Lucerne',    'P (Bray-1)',   NULL, 25,   NULL, 'mg/kg', 'Bray-1',    'NWPG SA — Planted Pasture & Lucerne Production', 'T1; >=25 for legumes'),
  ('Lucerne',    'K',            NULL, 0.30, NULL, 'cmol+/kg', 'NH4-OAc', 'NWPG SA — Planted Pasture & Lucerne Production', 'T1'),
  ('Lucerne',    'pH (KCl)',     NULL, 6.0,  6.8,  '-',     NULL,        'NWPG SA / DALRRD Lucerne', 'T1; <5.5 collapses N-fix'),
  ('Rooibos',    'pH (KCl)',     4.5,  4.2,  4.7,  '-',     NULL,        'Hattingh et al. 2023 SAJPS 40:4-5', 'T3 peer-reviewed; rooibos pH unique among SA crops'),
  ('Rooibos',    'P (Bray-1)',   16.9, 7.4,  26.4, 'mg/kg', 'Bray-1',    'Hattingh et al. 2023 SAJPS 40:4-5', 'T3 peer-reviewed; boundary-line study, n=120'),
  ('Rooibos',    'K',            20.8, 11.5, 30.0, 'mg/kg', NULL,        'Hattingh et al. 2023 SAJPS 40:4-5', 'T3 peer-reviewed'),
  ('Cotton',     'pH (H2O)',     NULL, 5.5,  7.5,  '-',     NULL,        'Cotton SA Technical Information', 'T1'),
  ('Pecan',      'pH (H2O)',     6.0,  NULL, NULL, '-',     '1:2.5',     'Schmidt 2021 ARC-ITSC Soil norms', 'T1; pH(KCl) 5.0-5.5'),
  ('Pecan',      'pH (KCl)',     NULL, 5.0,  5.5,  '-',     NULL,        'Schmidt 2021 ARC-ITSC Soil norms', 'T1'),
  ('Pecan',      'K',            NULL, 100,  NULL, 'mg/kg', 'NH4-OAc',   'Schmidt 2021 ARC-ITSC Soil norms', 'T1; >100-110'),
  ('Pecan',      'Ca',           NULL, 250,  NULL, 'mg/kg', 'NH4-OAc',   'Schmidt 2021 ARC-ITSC Soil norms', 'T1'),
  ('Pecan',      'Mg',           NULL, 80,   NULL, 'mg/kg', 'NH4-OAc',   'Schmidt 2021 ARC-ITSC Soil norms', 'T1')
ON CONFLICT DO NOTHING;

-- ── Nutrient removal ───────────────────────────────────────────────
-- Lucerne 'fresh' row deliberately stores N=NULL because lucerne is a
-- legume — tissue N (~27.5 kg/t DM) comes from atmospheric fixation,
-- not synthetic. Existing 'total' row from FERTASA 5.12.2 also has
-- N=NULL for the same reason. plant_part='fresh' distinguishes the row.
INSERT INTO fertasa_nutrient_removal
  (crop, plant_part, yield_unit, n, p, k, ca, mg, s, b, zn, fe, mn, cu, mo,
   source_section, notes) VALUES
  ('Maize',   'grain', 'kg per t grain', 15.0, 3.0,  4.0, 0.5, 1.0, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'GrainSA Fertiliser Requirements; ARC-GCI Du Plessis Maize Production Guide',
   'T1; SA canonical 15-3-4-0.5-1 N-P-K-Ca-Mg per t; S excluded due to source conflict'),
  ('Bean (Dry)', 'seed', 'kg per t seed', 36.0, 8.0, 18.0, NULL, NULL, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'NDA / DALRRD Drybean Infopak', 'T1; 36 kg N, 8 kg P, 18 kg K per ton seed'),
  ('Lucerne', 'fresh', 'kg per t DM', NULL, 2.7, 21.0, 13.0, 2.7, 2.7,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'NWPG SA — Planted Pasture & Lucerne Production',
   'T1; legume — N from biological fixation, do not recommend synthetic N'),
  ('Tomato', 'fruit (open field)', 'kg per t fruit', 3.0, 0.75, 4.0, NULL, NULL, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Starke Ayres Tomato Production Guideline 2019',
   'T1; fruit-only band 2.0-4.0 N / 0.5-1.0 P / 3.0-5.0 K kg/t — midpoints stored'),
  ('Sweet pepper', 'fruit (open field)', 'kg per t fruit', 2.0, 0.6, 3.5, 0.5, 0.3, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Starke Ayres Sweet & Hot Pepper 2019 Tbl 4',
   'T1; linear removal rate per ton fruit, identical for tunnel'),
  ('Sweet pepper', 'fruit (tunnel)', 'kg per t fruit', 2.0, 0.6, 3.5, 0.5, 0.3, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Starke Ayres Sweet & Hot Pepper 2019 Tbl 5',
   'T1; tunnel reaches 200 t/ha at same per-ton rate')
ON CONFLICT DO NOTHING;

-- ── Perennial age factors ──────────────────────────────────────────
-- Every perennial covered by the research files (Apple/Pear/Plum/Peach/
-- Apricot/Cherry/Citrus/Avocado/Macadamia/Pecan/Mango/Litchi/Olive/
-- Banana/Pineapple/Papaya/Wine Grape/Table Grape/Blueberry) already has
-- rows in the existing 87. Skipping all to avoid duplicates.

COMMIT;
