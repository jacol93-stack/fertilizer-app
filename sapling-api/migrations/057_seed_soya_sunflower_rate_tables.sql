-- ============================================================
-- 057: Seed soya + sunflower rate tables (FERTASA)
-- ============================================================
-- Sources: FERTASA Handbook sections 5.5.5 (Soya beans) and
-- 5.5.6 (Sunflower). Refreshed via authenticated scrape 2026-04-20
-- into sapling-api/data/fertasa_handbook/5_5_5_soya_beans.json and
-- 5_5_6_sunflower.json.
--
-- Shape conventions:
--   * Yield in t/ha stored as discrete published points (1, 2, 3, 4 for
--     soya; 1, 1.5, 2, 2.5, 3 for sunflower). Matches wheat P pattern.
--   * Soil-test axis: FERTASA publishes header values 5, 10, 15, ... as
--     shorthand for half-open bands. We encode each row as [prev, this):
--       Row "5"  → soil-P in [0, 5)
--       Row "10" → soil-P in [5, 10)
--       ...
--       Last row  → [prev, NULL)  (open top — plateau at the minimum)
--   * Soil-P is Bray-1 method (per FERTASA prose).
--   * water_regime = 'dryland' (FERTASA field crops default; irrigated
--     versions would need their own rows).
--
-- Cell counts:
--   Soya    P: 6 soil-P bands × 4 yields = 24
--   Soya    K: 6 soil-K bands × 4 yields = 24
--   Sunf    N: 5 yields × 1 = 5 (N is 1-D vs yield only)
--   Sunf    P: 6 soil-P bands × 5 yields = 30
--   Sunf    K: 6 soil-K bands × 5 yields = 30
--   Total: 113 cells.
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE (crop = 'Soybean' AND source_section IN ('5.5.5 Table 1', '5.5.5 Table 2'))
   OR (crop = 'Sunflower' AND source_section IN ('5.5.6 Table 1', '5.5.6 Table 2', '5.5.6 Table 3'));

-- ============================================================
-- Soya Beans: P (5.5.5 Table 1) — 6 soil-P bands × 4 yields
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Yield 1 t/ha
    ('Soybean', 'P', 'elemental', 1, 1, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 20, 20, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 1, 1, 'Bray-1', 'mg/kg', 5,  10,   'dryland', 17, 17, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 1, 1, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 15, 15, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 1, 1, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 13, 13, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 1, 1, 'Bray-1', 'mg/kg', 20, 25,   'dryland', 11, 11, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 1, 1, 'Bray-1', 'mg/kg', 25, NULL, 'dryland', 10, 10, 'FERTASA Handbook', '5.5.5 Table 1', 2019, 'Top band is open-ended; rates plateau at the minimum above 25 mg/kg'),
    -- Yield 2 t/ha
    ('Soybean', 'P', 'elemental', 2, 2, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 40, 40, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 2, 2, 'Bray-1', 'mg/kg', 5,  10,   'dryland', 31, 31, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 2, 2, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 25, 25, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 2, 2, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 21, 21, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 2, 2, 'Bray-1', 'mg/kg', 20, 25,   'dryland', 19, 19, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 2, 2, 'Bray-1', 'mg/kg', 25, NULL, 'dryland', 18, 18, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    -- Yield 3 t/ha
    ('Soybean', 'P', 'elemental', 3, 3, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 60, 60, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 3, 3, 'Bray-1', 'mg/kg', 5,  10,   'dryland', 45, 45, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 3, 3, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 35, 35, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 3, 3, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 31, 31, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 3, 3, 'Bray-1', 'mg/kg', 20, 25,   'dryland', 28, 28, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 3, 3, 'Bray-1', 'mg/kg', 25, NULL, 'dryland', 26, 26, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    -- Yield 4 t/ha
    ('Soybean', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 80, 80, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 5,  10,   'dryland', 59, 59, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 45, 45, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 42, 42, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 20, 25,   'dryland', 38, 38, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL),
    ('Soybean', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 25, NULL, 'dryland', 34, 34, 'FERTASA Handbook', '5.5.5 Table 1', 2019, NULL);

-- ============================================================
-- Soya Beans: K (5.5.5 Table 2) — 6 soil-K bands × 4 yields
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Yield 1 t/ha
    ('Soybean', 'K', 'elemental', 1, 1, 'Ambic',  'mg/kg', 0,   20,   'dryland', 20,  20,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 1, 1, 'Ambic',  'mg/kg', 20,  40,   'dryland', 16,  16,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 1, 1, 'Ambic',  'mg/kg', 40,  60,   'dryland', 13,  13,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 1, 1, 'Ambic',  'mg/kg', 60,  80,   'dryland', 11,  11,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 1, 1, 'Ambic',  'mg/kg', 80,  100,  'dryland', 10,  10,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 1, 1, 'Ambic',  'mg/kg', 100, NULL, 'dryland', 9,   9,   'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    -- Yield 2 t/ha
    ('Soybean', 'K', 'elemental', 2, 2, 'Ambic',  'mg/kg', 0,   20,   'dryland', 40,  40,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 2, 2, 'Ambic',  'mg/kg', 20,  40,   'dryland', 31,  31,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 2, 2, 'Ambic',  'mg/kg', 40,  60,   'dryland', 25,  25,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 2, 2, 'Ambic',  'mg/kg', 60,  80,   'dryland', 22,  22,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 2, 2, 'Ambic',  'mg/kg', 80,  100,  'dryland', 20,  20,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 2, 2, 'Ambic',  'mg/kg', 100, NULL, 'dryland', 19,  19,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    -- Yield 3 t/ha
    ('Soybean', 'K', 'elemental', 3, 3, 'Ambic',  'mg/kg', 0,   20,   'dryland', 60,  60,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 3, 3, 'Ambic',  'mg/kg', 20,  40,   'dryland', 47,  47,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 3, 3, 'Ambic',  'mg/kg', 40,  60,   'dryland', 39,  39,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 3, 3, 'Ambic',  'mg/kg', 60,  80,   'dryland', 34,  34,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 3, 3, 'Ambic',  'mg/kg', 80,  100,  'dryland', 31,  31,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 3, 3, 'Ambic',  'mg/kg', 100, NULL, 'dryland', 30,  30,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    -- Yield 4 t/ha
    ('Soybean', 'K', 'elemental', 4, 4, 'Ambic',  'mg/kg', 0,   20,   'dryland', 80,  80,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 4, 4, 'Ambic',  'mg/kg', 20,  40,   'dryland', 63,  63,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 4, 4, 'Ambic',  'mg/kg', 40,  60,   'dryland', 53,  53,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 4, 4, 'Ambic',  'mg/kg', 60,  80,   'dryland', 46,  46,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 4, 4, 'Ambic',  'mg/kg', 80,  100,  'dryland', 41,  41,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL),
    ('Soybean', 'K', 'elemental', 4, 4, 'Ambic',  'mg/kg', 100, NULL, 'dryland', 40,  40,  'FERTASA Handbook', '5.5.5 Table 2', 2019, NULL);

-- ============================================================
-- Sunflower N (5.5.6 Table 1) — 5 yields × 1 (yield-only axis)
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Sunflower', 'N', 'elemental', 1.0, 1.0, 'dryland', 20, 20, 'FERTASA Handbook', '5.5.6 Table 1', 2019, NULL),
    ('Sunflower', 'N', 'elemental', 1.5, 1.5, 'dryland', 30, 30, 'FERTASA Handbook', '5.5.6 Table 1', 2019, NULL),
    ('Sunflower', 'N', 'elemental', 2.0, 2.0, 'dryland', 40, 40, 'FERTASA Handbook', '5.5.6 Table 1', 2019, NULL),
    ('Sunflower', 'N', 'elemental', 2.5, 2.5, 'dryland', 50, 50, 'FERTASA Handbook', '5.5.6 Table 1', 2019, NULL),
    ('Sunflower', 'N', 'elemental', 3.0, 3.0, 'dryland', 60, 60, 'FERTASA Handbook', '5.5.6 Table 1', 2019, NULL);

-- ============================================================
-- Sunflower P (5.5.6 Table 2) — 6 soil-P bands × 5 yields
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Soil-P band 0-5
    ('Sunflower', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 12, 12, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 14, 14, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 16, 16, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 18, 18, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 20, 20, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    -- 5-10
    ('Sunflower', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 5,  10,   'dryland', 8,  8,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 5,  10,   'dryland', 10, 10, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 5,  10,   'dryland', 12, 12, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 5,  10,   'dryland', 14, 14, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 5,  10,   'dryland', 16, 16, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    -- 10-15
    ('Sunflower', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 4,  4,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 6,  6,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 8,  8,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 10, 10, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 12, 12, 'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    -- 15-20
    ('Sunflower', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 3,  3,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 5,  5,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 7,  7,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 9,  9,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    -- 20-25
    ('Sunflower', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 20, 25,   'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 20, 25,   'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 20, 25,   'dryland', 3,  3,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 20, 25,   'dryland', 5,  5,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 20, 25,   'dryland', 7,  7,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    -- 25+ (open top)
    ('Sunflower', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 25, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 25, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 25, NULL, 'dryland', 2,  2,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 25, NULL, 'dryland', 4,  4,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL),
    ('Sunflower', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 25, NULL, 'dryland', 6,  6,  'FERTASA Handbook', '5.5.6 Table 2', 2019, NULL);

-- ============================================================
-- Sunflower K (5.5.6 Table 3) — 6 soil-K bands × 5 yields
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Soil-K band 0-20
    ('Sunflower', 'K', 'elemental', 1.0, 1.0, 'Ambic', 'mg/kg', 0,   20,   'dryland', 16, 16, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 1.5, 1.5, 'Ambic', 'mg/kg', 0,   20,   'dryland', 21, 21, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 0,   20,   'dryland', 27, 27, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 0,   20,   'dryland', 33, 33, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 0,   20,   'dryland', 39, 39, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    -- 20-40
    ('Sunflower', 'K', 'elemental', 1.0, 1.0, 'Ambic', 'mg/kg', 20,  40,   'dryland', 10, 10, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 1.5, 1.5, 'Ambic', 'mg/kg', 20,  40,   'dryland', 15, 15, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 20,  40,   'dryland', 20, 20, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 20,  40,   'dryland', 25, 25, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 20,  40,   'dryland', 30, 30, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    -- 40-60
    ('Sunflower', 'K', 'elemental', 1.0, 1.0, 'Ambic', 'mg/kg', 40,  60,   'dryland', 7,  7,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 1.5, 1.5, 'Ambic', 'mg/kg', 40,  60,   'dryland', 10, 10, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 40,  60,   'dryland', 14, 14, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 40,  60,   'dryland', 18, 18, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 40,  60,   'dryland', 22, 22, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    -- 60-80
    ('Sunflower', 'K', 'elemental', 1.0, 1.0, 'Ambic', 'mg/kg', 60,  80,   'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 1.5, 1.5, 'Ambic', 'mg/kg', 60,  80,   'dryland', 8,  8,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 60,  80,   'dryland', 11, 11, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 60,  80,   'dryland', 14, 14, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 60,  80,   'dryland', 17, 17, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    -- 80-100
    ('Sunflower', 'K', 'elemental', 1.0, 1.0, 'Ambic', 'mg/kg', 80,  100,  'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 1.5, 1.5, 'Ambic', 'mg/kg', 80,  100,  'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 80,  100,  'dryland', 9,  9,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 80,  100,  'dryland', 11, 11, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 80,  100,  'dryland', 14, 14, 'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    -- 100+ (open top — no K needed)
    ('Sunflower', 'K', 'elemental', 1.0, 1.0, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 1.5, 1.5, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL),
    ('Sunflower', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.5.6 Table 3', 2019, NULL);

COMMIT;
