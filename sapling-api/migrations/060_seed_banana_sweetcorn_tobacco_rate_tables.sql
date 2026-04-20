-- ============================================================
-- 060: Seed banana + sweetcorn + tobacco rate tables (FERTASA)
-- ============================================================
-- Sources: FERTASA Handbook sections 5.7.2 (Bananas), 5.4.5 (Sweetcorn),
-- 5.11 (Tobacco). Refreshed via authenticated scrape 2026-04-20.
--
--   Banana     P    4  soil-P only, yield-agnostic (1-D)
--   Banana     K    7  soil-K × texture (clay >= 25% vs < 25%)
--   Banana     N    4  yield only (35-75 t/ha/yr; 4 ranges)
--   Sweetcorn  N    6  yield only (5 point yields + open top)
--   Sweetcorn  P   30  Bray-1 × yield (6 × 5)
--   Sweetcorn  K   35  Ambic-K × yield (7 × 5)
--   Tobacco    N    4  yield only (flue-cured; 3 point yields + open top)
--   Tobacco    P    6  Bray-1 only (yield-agnostic, 6 bands)
--   Tobacco    K   28  Ambic-K × yield (7 × 4)
--
-- Total: 124 cells.
--
-- Tomato (5.6.4) was inspected but skipped: rate tables heavily mangled
-- by the scraper (multi-column layouts collapsed into single rows). To
-- be revisited after scraper fixes or from the underlying handbook images.
--
-- Banana Table 2 (N+K only, yield 25-65) and Table 3 (N+P+K, yield 35-75)
-- partially overlap at 35-65 with different values — likely represent
-- different production systems (prose context not captured). Seeded
-- only Table 3 (richer NPK) and left T2 unseeded to avoid duplication.
-- Banana P is seeded from T1 (soil-test-driven) only; T3 P rates
-- (yield-driven) are redundant.
--
-- Tobacco rows are all FLUE-CURED specifically. Air-cured / dark /
-- burley have different N requirements (per Table 0 removal reference).
-- Current encoding applies to flue-cured only; the other types need
-- their own rows with a `cultivar` or crop-variant axis to be added
-- later.
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE (crop = 'Banana'    AND source_section IN ('5.7.2 Table 1', '5.7.2 Table 2', '5.7.2 Table 4'))
   OR (crop = 'Sweetcorn' AND source_section IN ('5.4.5 Table 1', '5.4.5 Table 2', '5.4.5 Table 3'))
   OR (crop = 'Tobacco'   AND source_section IN ('5.11 Table 5',  '5.11 Table 6',  '5.11 Table 7'));

-- Banana P (5.7.2 Table 0) - soil-P only, 4 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Banana', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 10, NULL, 100, 100, 'FERTASA Handbook', '5.7.2 Table 1', 2019, 'Yield-agnostic P rate keyed on soil-P only'),
    ('Banana', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 10, 25, NULL, 80, 80, 'FERTASA Handbook', '5.7.2 Table 1', 2019, 'Yield-agnostic P rate keyed on soil-P only'),
    ('Banana', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 25, 60, NULL, 50, 50, 'FERTASA Handbook', '5.7.2 Table 1', 2019, 'Yield-agnostic P rate keyed on soil-P only'),
    ('Banana', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 60, NULL, NULL, 0, 0, 'FERTASA Handbook', '5.7.2 Table 1', 2019, 'Yield-agnostic P rate keyed on soil-P only');

-- Banana K (5.7.2 Table 2) - soil-K x texture, 7 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     clay_pct_min, clay_pct_max, water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Banana', 'K', 'elemental', 0, NULL, 'Ambic', 'mg/kg', 0, 150, 25, NULL, NULL, 500, 500, 'FERTASA Handbook', '5.7.2 Table 2', 2019, 'Clay > 25%'),
    ('Banana', 'K', 'elemental', 0, NULL, 'Ambic', 'mg/kg', 150, 200, 25, NULL, NULL, 250, 250, 'FERTASA Handbook', '5.7.2 Table 2', 2019, 'Clay > 25%'),
    ('Banana', 'K', 'elemental', 0, NULL, 'Ambic', 'mg/kg', 200, 250, 25, NULL, NULL, 125, 125, 'FERTASA Handbook', '5.7.2 Table 2', 2019, 'Clay > 25%'),
    ('Banana', 'K', 'elemental', 0, NULL, 'Ambic', 'mg/kg', 250, NULL, 25, NULL, NULL, 0, 0, 'FERTASA Handbook', '5.7.2 Table 2', 2019, 'Clay > 25%'),
    ('Banana', 'K', 'elemental', 0, NULL, 'Ambic', 'mg/kg', 0, 100, 0, 25, NULL, 250, 250, 'FERTASA Handbook', '5.7.2 Table 2', 2019, 'Clay < 25%'),
    ('Banana', 'K', 'elemental', 0, NULL, 'Ambic', 'mg/kg', 100, 150, 0, 25, NULL, 125, 125, 'FERTASA Handbook', '5.7.2 Table 2', 2019, 'Clay < 25%'),
    ('Banana', 'K', 'elemental', 0, NULL, 'Ambic', 'mg/kg', 150, NULL, 0, 25, NULL, 0, 0, 'FERTASA Handbook', '5.7.2 Table 2', 2019, 'Clay < 25%');

-- Banana N (5.7.2 Table 4) - yield only, 4 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Banana', 'N', 'elemental', 35, 45, NULL, 200, 200, 'FERTASA Handbook', '5.7.2 Table 4', 2019, 'Annual yield t/ha/yr'),
    ('Banana', 'N', 'elemental', 46, 55, NULL, 270, 270, 'FERTASA Handbook', '5.7.2 Table 4', 2019, 'Annual yield t/ha/yr'),
    ('Banana', 'N', 'elemental', 56, 65, NULL, 300, 300, 'FERTASA Handbook', '5.7.2 Table 4', 2019, 'Annual yield t/ha/yr'),
    ('Banana', 'N', 'elemental', 66, 75, NULL, 360, 360, 'FERTASA Handbook', '5.7.2 Table 4', 2019, 'Annual yield t/ha/yr');

-- Sweetcorn N (5.4.5 Table 1) - yield only, 5 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Sweetcorn', 'N', 'elemental', 10, 10, 'dryland', 70, 70, 'FERTASA Handbook', '5.4.5 Table 1', 2019, NULL),
    ('Sweetcorn', 'N', 'elemental', 15, 15, 'dryland', 120, 120, 'FERTASA Handbook', '5.4.5 Table 1', 2019, NULL),
    ('Sweetcorn', 'N', 'elemental', 18, 18, 'dryland', 145, 145, 'FERTASA Handbook', '5.4.5 Table 1', 2019, NULL),
    ('Sweetcorn', 'N', 'elemental', 25, 25, 'dryland', 200, 200, 'FERTASA Handbook', '5.4.5 Table 1', 2019, NULL),
    ('Sweetcorn', 'N', 'elemental', 30, 30, 'dryland', 240, 240, 'FERTASA Handbook', '5.4.5 Table 1', 2019, NULL),
    ('Sweetcorn', 'N', 'elemental', 30, NULL, 'dryland', 240, 240, 'FERTASA Handbook', '5.4.5 Table 1', 2019, 'Plateau above 30 t/ha');

-- Sweetcorn P (5.4.5 Table 2) - Bray-1 x yield, 30 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Sweetcorn', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 0, 4, 'dryland', 65, 65, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 15, 15, 'Bray-1', 'mg/kg', 0, 4, 'dryland', 109, 109, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 18, 18, 'Bray-1', 'mg/kg', 0, 4, 'dryland', 130, 130, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 25, 25, 'Bray-1', 'mg/kg', 0, 4, 'dryland', 130, 130, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 0, 4, 'dryland', 130, 130, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 4, 8, 'dryland', 47, 47, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 15, 15, 'Bray-1', 'mg/kg', 4, 8, 'dryland', 78, 78, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 18, 18, 'Bray-1', 'mg/kg', 4, 8, 'dryland', 90, 90, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 25, 25, 'Bray-1', 'mg/kg', 4, 8, 'dryland', 97, 97, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 4, 8, 'dryland', 101, 101, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 8, 15, 'dryland', 30, 30, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 15, 15, 'Bray-1', 'mg/kg', 8, 15, 'dryland', 50, 50, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 18, 18, 'Bray-1', 'mg/kg', 8, 15, 'dryland', 59, 59, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 25, 25, 'Bray-1', 'mg/kg', 8, 15, 'dryland', 68, 68, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 8, 15, 'dryland', 72, 72, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 15, 21, 'dryland', 21, 21, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 15, 15, 'Bray-1', 'mg/kg', 15, 21, 'dryland', 36, 36, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 18, 18, 'Bray-1', 'mg/kg', 15, 21, 'dryland', 42, 42, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 25, 25, 'Bray-1', 'mg/kg', 15, 21, 'dryland', 53, 53, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 15, 21, 'dryland', 58, 58, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 21, 28, 'dryland', 15, 15, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 15, 15, 'Bray-1', 'mg/kg', 21, 28, 'dryland', 26, 26, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 18, 18, 'Bray-1', 'mg/kg', 21, 28, 'dryland', 31, 31, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 25, 25, 'Bray-1', 'mg/kg', 21, 28, 'dryland', 41, 41, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 21, 28, 'dryland', 48, 48, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 28, NULL, 'dryland', 12, 12, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 15, 15, 'Bray-1', 'mg/kg', 28, NULL, 'dryland', 18, 18, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 18, 18, 'Bray-1', 'mg/kg', 28, NULL, 'dryland', 21, 21, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 25, 25, 'Bray-1', 'mg/kg', 28, NULL, 'dryland', 30, 30, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL),
    ('Sweetcorn', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 28, NULL, 'dryland', 36, 36, 'FERTASA Handbook', '5.4.5 Table 2', 2019, NULL);

-- Sweetcorn K (5.4.5 Table 3) - Ambic-K x yield, 35 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Sweetcorn', 'K', 'elemental', 10, 10, 'Ambic', 'mg/kg', 0, 10, 'dryland', 27, 27, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 15, 15, 'Ambic', 'mg/kg', 0, 10, 'dryland', 45, 45, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 18, 18, 'Ambic', 'mg/kg', 0, 10, 'dryland', 54, 54, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 25, 25, 'Ambic', 'mg/kg', 0, 10, 'dryland', 82, 82, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 30, 30, 'Ambic', 'mg/kg', 0, 10, 'dryland', 100, 100, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 10, 10, 'Ambic', 'mg/kg', 10, 20, 'dryland', 20, 20, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 15, 15, 'Ambic', 'mg/kg', 10, 20, 'dryland', 39, 39, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 18, 18, 'Ambic', 'mg/kg', 10, 20, 'dryland', 47, 47, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 25, 25, 'Ambic', 'mg/kg', 10, 20, 'dryland', 74, 74, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 30, 30, 'Ambic', 'mg/kg', 10, 20, 'dryland', 92, 92, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 10, 10, 'Ambic', 'mg/kg', 20, 40, 'dryland', 13, 13, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 15, 15, 'Ambic', 'mg/kg', 20, 40, 'dryland', 31, 31, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 18, 18, 'Ambic', 'mg/kg', 20, 40, 'dryland', 39, 39, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 25, 25, 'Ambic', 'mg/kg', 20, 40, 'dryland', 64, 64, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 30, 30, 'Ambic', 'mg/kg', 20, 40, 'dryland', 81, 81, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 10, 10, 'Ambic', 'mg/kg', 40, 60, 'dryland', 8, 8, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 15, 15, 'Ambic', 'mg/kg', 40, 60, 'dryland', 25, 25, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 18, 18, 'Ambic', 'mg/kg', 40, 60, 'dryland', 33, 33, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 25, 25, 'Ambic', 'mg/kg', 40, 60, 'dryland', 56, 56, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 30, 30, 'Ambic', 'mg/kg', 40, 60, 'dryland', 71, 71, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 10, 10, 'Ambic', 'mg/kg', 60, 80, 'dryland', 0, 0, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 15, 15, 'Ambic', 'mg/kg', 60, 80, 'dryland', 21, 21, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 18, 18, 'Ambic', 'mg/kg', 60, 80, 'dryland', 29, 29, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 25, 25, 'Ambic', 'mg/kg', 60, 80, 'dryland', 50, 50, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 30, 30, 'Ambic', 'mg/kg', 60, 80, 'dryland', 65, 65, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 10, 10, 'Ambic', 'mg/kg', 80, 100, 'dryland', 0, 0, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 15, 15, 'Ambic', 'mg/kg', 80, 100, 'dryland', 18, 18, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 18, 18, 'Ambic', 'mg/kg', 80, 100, 'dryland', 25, 25, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 25, 25, 'Ambic', 'mg/kg', 80, 100, 'dryland', 45, 45, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 30, 30, 'Ambic', 'mg/kg', 80, 100, 'dryland', 59, 59, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 10, 10, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 0, 0, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 15, 15, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 15, 15, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 18, 18, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 22, 22, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 25, 25, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 41, 41, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL),
    ('Sweetcorn', 'K', 'elemental', 30, 30, 'Ambic', 'mg/kg', 100, NULL, 'dryland', 54, 54, 'FERTASA Handbook', '5.4.5 Table 3', 2019, NULL);

-- Tobacco (Flue-cured) N (5.11 Table 5) - yield only, 3 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Tobacco', 'N', 'elemental', 2.0, 2.0, 'dryland', 190, 190, 'FERTASA Handbook', '5.11 Table 5', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'N', 'elemental', 2.5, 2.5, 'dryland', 220, 220, 'FERTASA Handbook', '5.11 Table 5', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'N', 'elemental', 3.0, 3.0, 'dryland', 250, 250, 'FERTASA Handbook', '5.11 Table 5', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'N', 'elemental', 3.0, NULL, 'dryland', 250, 250, 'FERTASA Handbook', '5.11 Table 5', 2019, 'Flue-cured tobacco; plateau above 3 t/ha');

-- Tobacco (Flue-cured) P (5.11 Table 6) - soil-P only, 6 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Tobacco', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 10, 'dryland', 120, 120, 'FERTASA Handbook', '5.11 Table 6', 2019, 'Flue-cured tobacco; yield-agnostic'),
    ('Tobacco', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 10, 20, 'dryland', 110, 110, 'FERTASA Handbook', '5.11 Table 6', 2019, 'Flue-cured tobacco; yield-agnostic'),
    ('Tobacco', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 30, 'dryland', 100, 100, 'FERTASA Handbook', '5.11 Table 6', 2019, 'Flue-cured tobacco; yield-agnostic'),
    ('Tobacco', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 30, 40, 'dryland', 90, 90, 'FERTASA Handbook', '5.11 Table 6', 2019, 'Flue-cured tobacco; yield-agnostic'),
    ('Tobacco', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 40, 50, 'dryland', 80, 80, 'FERTASA Handbook', '5.11 Table 6', 2019, 'Flue-cured tobacco; yield-agnostic'),
    ('Tobacco', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, 'dryland', 70, 70, 'FERTASA Handbook', '5.11 Table 6', 2019, 'Flue-cured tobacco; yield-agnostic');

-- Tobacco (Flue-cured) K (5.11 Table 7) - Ambic-K x yield, 28 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Tobacco', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 0, 25, 'dryland', 140, 140, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 0, 25, 'dryland', 175, 175, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 0, 25, 'dryland', 220, 220, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 4.0, 4.0, 'Ambic', 'mg/kg', 0, 25, 'dryland', 280, 280, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 25, 50, 'dryland', 135, 135, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 25, 50, 'dryland', 165, 165, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 25, 50, 'dryland', 210, 210, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 4.0, 4.0, 'Ambic', 'mg/kg', 25, 50, 'dryland', 270, 270, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 50, 75, 'dryland', 125, 125, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 50, 75, 'dryland', 155, 155, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 50, 75, 'dryland', 205, 205, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 4.0, 4.0, 'Ambic', 'mg/kg', 50, 75, 'dryland', 260, 260, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 75, 100, 'dryland', 120, 120, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 75, 100, 'dryland', 145, 145, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 75, 100, 'dryland', 195, 195, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 4.0, 4.0, 'Ambic', 'mg/kg', 75, 100, 'dryland', 250, 250, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 100, 125, 'dryland', 115, 115, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 100, 125, 'dryland', 135, 135, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 100, 125, 'dryland', 185, 185, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 4.0, 4.0, 'Ambic', 'mg/kg', 100, 125, 'dryland', 240, 240, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 125, 150, 'dryland', 105, 105, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 125, 150, 'dryland', 125, 125, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 125, 150, 'dryland', 180, 180, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 4.0, 4.0, 'Ambic', 'mg/kg', 125, 150, 'dryland', 230, 230, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.0, 2.0, 'Ambic', 'mg/kg', 150, NULL, 'dryland', 100, 100, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 2.5, 2.5, 'Ambic', 'mg/kg', 150, NULL, 'dryland', 120, 120, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 3.0, 3.0, 'Ambic', 'mg/kg', 150, NULL, 'dryland', 170, 170, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco'),
    ('Tobacco', 'K', 'elemental', 4.0, 4.0, 'Ambic', 'mg/kg', 150, NULL, 'dryland', 220, 220, 'FERTASA Handbook', '5.11 Table 7', 2019, 'Flue-cured tobacco');

COMMIT;
