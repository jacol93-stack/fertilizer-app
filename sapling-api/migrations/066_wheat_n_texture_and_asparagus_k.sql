-- ============================================================
-- 066: Wheat N (Western Cape, texture-banded) + Asparagus K
-- ============================================================
-- Source: FERTASA Handbook 8th Ed.
--
--   Section 5.4.3.2.2 — Wheat N in the Swartland/Western Cape and
--     Southern Cape. Base Table 5.4.3.2.2 (stubble field, shallow
--     tine tillage) is N1 by yield target. Prose at the same section
--     gives an explicit texture multiplier:
--
--       "ii) Soil texture. The N guideline should be increased by
--        10 to 15% for sandy soils and decreased by 10 to 15% for
--        clayey soils."
--
--     Seeded as three texture bands against the published N1:
--       sandy  (< 15% clay)    : base × 1.125 (midpoint of +10-15%)
--       loam   (15-35% clay)   : base × 1.0   (published, unmodified)
--       clayey (>= 35% clay)   : base × 0.875 (midpoint of -10-15%)
--
--     Cut thresholds (15%, 35%) follow the same convention used by
--     the wheat K table 5.4.3.1.3, which cuts at 35% clay explicitly.
--     Full ±15% envelope flagged in source_note for auditors.
--
--     Free State / summer-rainfall wheat N (Table 5.4.3.1.1 = #2 in
--     the scraped JSON) is a separate regional × yield table with no
--     texture prose in its own section — deferred.
--
--   Section 5.6.3.3 — Asparagus K. Four soil-K bands × (establishment
--     Sand/Clay + established annual). crop_cycle follows the
--     convention set by migration 063 (Blueberry): 'plant' =
--     establishment / young years, 'ratoon' = bearing / established
--     years. Sand/Clay cut at 25% clay, matching the banana K
--     convention in migration 060.
--
--     Note: the scraped JSON header labels this table "Soil-P
--     (NH 4 0Ac)" — a scraper mislabel. Ammonium acetate (NH4OAc)
--     is the standard K extractant, and FERTASA prose at 5.6.3.3
--     identifies the table explicitly as "Guidelines for
--     K-fertilization of asparagus".
--
-- Cells:
--   Wheat N       15  (5 yield bands × 3 texture bands)
--   Asparagus K   12  (4 soil-K bands × 3 rows: est-sandy, est-clay,
--                      established-annual)
-- Total: 27 rows.
-- ============================================================

BEGIN;

-- Guard against re-runs
DELETE FROM public.fertilizer_rate_tables
 WHERE (crop = 'Wheat'     AND source_section = '5.4.3.2.2')
    OR (crop = 'Asparagus' AND source_section = '5.6.3.3');

-- ============================================================
-- Wheat N (Western Cape, Table 5.4.3.2.2)
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     clay_pct_min, clay_pct_max,
     region, water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Loam (15-35% clay) — published base, unmodified
    ('Wheat', 'N', 'elemental', 4,    5, 15,   35,   'Western Cape', 'dryland',  80, 130, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base N1 for 4-5 t/ha. Assumes stubble field, shallow tine tillage (FERTASA preconditions). Published range spans rainfall variation within the Western Cape.'),
    ('Wheat', 'N', 'elemental', 5,    6, 15,   35,   'Western Cape', 'dryland', 130, 160, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base N1 for 5-6 t/ha.'),
    ('Wheat', 'N', 'elemental', 6,    7, 15,   35,   'Western Cape', 'dryland', 160, 180, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base N1 for 6-7 t/ha.'),
    ('Wheat', 'N', 'elemental', 7,    8, 15,   35,   'Western Cape', 'dryland', 180, 200, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base N1 for 7-8 t/ha.'),
    ('Wheat', 'N', 'elemental', 8, NULL, 15,   35,   'Western Cape', 'dryland', 200, 250, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base N1 for >= 8 t/ha (open-top band).'),

    -- Sandy (< 15% clay) — base × 1.125 (midpoint of +10-15%)
    ('Wheat', 'N', 'elemental', 4,    5, NULL, 15,   'Western Cape', 'dryland',  90, 146, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 1.125 (midpoint of the +10-15% sandy adjustment prescribed by FERTASA 5.4.3.2.2 prose: "The N guideline should be increased by 10 to 15% for sandy soils"). Full +10%/+15% envelope at this band: 88-150 kg N/ha.'),
    ('Wheat', 'N', 'elemental', 5,    6, NULL, 15,   'Western Cape', 'dryland', 146, 180, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 1.125 (sandy); +10/+15 envelope 143-184.'),
    ('Wheat', 'N', 'elemental', 6,    7, NULL, 15,   'Western Cape', 'dryland', 180, 202, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 1.125 (sandy); +10/+15 envelope 176-207.'),
    ('Wheat', 'N', 'elemental', 7,    8, NULL, 15,   'Western Cape', 'dryland', 202, 225, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 1.125 (sandy); +10/+15 envelope 198-230.'),
    ('Wheat', 'N', 'elemental', 8, NULL, NULL, 15,   'Western Cape', 'dryland', 225, 281, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 1.125 (sandy, open-top); +10/+15 envelope 220-288.'),

    -- Clayey (>= 35% clay) — base × 0.875 (midpoint of -10-15%)
    ('Wheat', 'N', 'elemental', 4,    5, 35,   NULL, 'Western Cape', 'dryland',  70, 114, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 0.875 (midpoint of the -10-15% clayey adjustment prescribed by FERTASA 5.4.3.2.2 prose: "decreased by 10 to 15% for clayey soils"). Full -10%/-15% envelope at this band: 68-117 kg N/ha.'),
    ('Wheat', 'N', 'elemental', 5,    6, 35,   NULL, 'Western Cape', 'dryland', 114, 140, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 0.875 (clayey); -10/-15 envelope 111-144.'),
    ('Wheat', 'N', 'elemental', 6,    7, 35,   NULL, 'Western Cape', 'dryland', 140, 158, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 0.875 (clayey); -10/-15 envelope 136-162.'),
    ('Wheat', 'N', 'elemental', 7,    8, 35,   NULL, 'Western Cape', 'dryland', 158, 175, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 0.875 (clayey); -10/-15 envelope 153-180.'),
    ('Wheat', 'N', 'elemental', 8, NULL, 35,   NULL, 'Western Cape', 'dryland', 175, 219, 'FERTASA Handbook', '5.4.3.2.2', 2019, 'Base × 0.875 (clayey, open-top); -10/-15 envelope 170-225.');

-- ============================================================
-- Asparagus K (Table 5.6.3.3)
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     clay_pct_min, clay_pct_max,
     crop_cycle,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Soil-K 66-99 mg/kg (NH4OAc)
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg',  66,  99, NULL,   25, 'plant',  187, 187, 'FERTASA Handbook', '5.6.3.3', 2019, 'Establishment year, sandy soils (<25% clay). FERTASA Table 5.6.3.3 publishes a binary Sand/Clay split; 25% cut matches banana K convention (migration 060).'),
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg',  66,  99,   25, NULL, 'plant',  140, 140, 'FERTASA Handbook', '5.6.3.3', 2019, 'Establishment year, clay soils (>=25% clay).'),
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg',  66,  99, NULL, NULL, 'ratoon',  93,  93, 'FERTASA Handbook', '5.6.3.3', 2019, 'Established bearing years, yield-agnostic annual rate (crop_cycle=ratoon per migration 063 convention). FERTASA does not split the maintenance rate by texture.'),

    -- Soil-K 100-149 mg/kg
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 100, 149, NULL,   25, 'plant',  140, 140, 'FERTASA Handbook', '5.6.3.3', 2019, NULL),
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 100, 149,   25, NULL, 'plant',   93,  93, 'FERTASA Handbook', '5.6.3.3', 2019, NULL),
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 100, 149, NULL, NULL, 'ratoon',  47,  47, 'FERTASA Handbook', '5.6.3.3', 2019, NULL),

    -- Soil-K 150-199 mg/kg
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, 199, NULL,   25, 'plant',   93,  93, 'FERTASA Handbook', '5.6.3.3', 2019, NULL),
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, 199,   25, NULL, 'plant',   47,  47, 'FERTASA Handbook', '5.6.3.3', 2019, NULL),
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, 199, NULL, NULL, 'ratoon',  24,  24, 'FERTASA Handbook', '5.6.3.3', 2019, NULL),

    -- Soil-K 200-249 mg/kg
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 200, 249, NULL,   25, 'plant',   47,  47, 'FERTASA Handbook', '5.6.3.3', 2019, NULL),
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 200, 249,   25, NULL, 'plant',   24,  24, 'FERTASA Handbook', '5.6.3.3', 2019, NULL),
    ('Asparagus', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 200, 249, NULL, NULL, 'ratoon',   0,   0, 'FERTASA Handbook', '5.6.3.3', 2019, 'At or above high soil-K band, established plantings need no maintenance K.');

COMMIT;
