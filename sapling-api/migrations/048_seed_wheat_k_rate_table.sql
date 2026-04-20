-- ============================================================
-- 048: Seed wheat K rate table (FERTASA 5.4.3.1.3)
-- ============================================================
-- Source: sapling-api/data/fertasa_handbook/5_4_3_wheat.json (tables[4])
--
-- Published structure:
--   yield bands (t/ha, ranges): 1-2, 2-3, 3-4
--   soil-K bands (mg/kg): <60, 60-80, 80-120, >120
--   cells: kg K/ha; ranges for 3-4 t/ha mid columns ("20-25")
--
-- CRITICAL context from handbook prose:
--   "* On soils with > 35% clay. (No K is recommended on soils
--    with < 35% clay.)"
-- The entire rate table applies ONLY to soils where clay >= 35%.
-- Seeding requires a clay filter, plus explicit zero-rows for
-- clay < 35% so the lookup returns 0 (not a heuristic extrapolation).
--
-- Notes on the shape vs wheat P (047):
--   * 048 is the first table using yield BANDS (not points + open-top).
--     The lookup_rate_table() function was extended today to handle
--     half-open interval membership: a band [1, 2) matches yield in
--     [1.0, 2.0). Above 4 t/ha, no row applies — we deliberately
--     DO NOT extrapolate (irrigated wheat K has its own table 5.4.3.3.4
--     which will be seeded separately).
--   * The 80-120* column's asterisk refers to the clay-filter footnote,
--     not a distinct rate-cell modifier.
--
-- Conservative decisions:
--   * Published yield bands are stored as [min, max) half-open.
--   * Zero-rows for clay < 35% use an open-top yield band (0, NULL) so
--     any yield matches and returns 0.
--   * soil_test_method = "Citric acid" per the handbook (Western Cape
--     wheat uses citric-acid extraction for K). For summer-rainfall
--     regions, Ambic or citric is typical; the number is the same
--     magnitude. Stored as Citric acid; the API will still match on
--     Ambic readings until we add explicit soil_test_method context.
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Wheat'
  AND nutrient = 'K'
  AND source_section = '5.4.3.1.3';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     clay_pct_min, clay_pct_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Clay >= 35%: published table (12 cells = 3 yield bands × 4 soil-K bands)
    -- Yield 1-2 t/ha
    ('Wheat', 'K', 'elemental', 1.0, 2.0, 'Citric acid', 'mg/kg', 0,   60,   35, NULL, 'dryland', 20, 20, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),
    ('Wheat', 'K', 'elemental', 1.0, 2.0, 'Citric acid', 'mg/kg', 60,  80,   35, NULL, 'dryland', 15, 15, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),
    ('Wheat', 'K', 'elemental', 1.0, 2.0, 'Citric acid', 'mg/kg', 80,  120,  35, NULL, 'dryland', 15, 15, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),
    ('Wheat', 'K', 'elemental', 1.0, 2.0, 'Citric acid', 'mg/kg', 120, NULL, 35, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),

    -- Yield 2-3 t/ha
    ('Wheat', 'K', 'elemental', 2.0, 3.0, 'Citric acid', 'mg/kg', 0,   60,   35, NULL, 'dryland', 30, 30, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),
    ('Wheat', 'K', 'elemental', 2.0, 3.0, 'Citric acid', 'mg/kg', 60,  80,   35, NULL, 'dryland', 20, 20, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),
    ('Wheat', 'K', 'elemental', 2.0, 3.0, 'Citric acid', 'mg/kg', 80,  120,  35, NULL, 'dryland', 20, 20, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),
    ('Wheat', 'K', 'elemental', 2.0, 3.0, 'Citric acid', 'mg/kg', 120, NULL, 35, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),

    -- Yield 3-4 t/ha
    ('Wheat', 'K', 'elemental', 3.0, 4.0, 'Citric acid', 'mg/kg', 0,   60,   35, NULL, 'dryland', 40, 40, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),
    ('Wheat', 'K', 'elemental', 3.0, 4.0, 'Citric acid', 'mg/kg', 60,  80,   35, NULL, 'dryland', 20, 25, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),
    ('Wheat', 'K', 'elemental', 3.0, 4.0, 'Citric acid', 'mg/kg', 80,  120,  35, NULL, 'dryland', 20, 25, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),
    ('Wheat', 'K', 'elemental', 3.0, 4.0, 'Citric acid', 'mg/kg', 120, NULL, 35, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.4.3.1.3', 2019, 'Clay > 35% only'),

    -- Clay < 35%: explicit zero rows per soil-K band, yield-agnostic via open-top band.
    -- Handbook explicitly states "No K is recommended on soils with < 35% clay".
    ('Wheat', 'K', 'elemental', 0.0, NULL, 'Citric acid', 'mg/kg', 0,   60,   NULL, 35, 'dryland', 0, 0, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'No K recommended on soils with < 35% clay'),
    ('Wheat', 'K', 'elemental', 0.0, NULL, 'Citric acid', 'mg/kg', 60,  80,   NULL, 35, 'dryland', 0, 0, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'No K recommended on soils with < 35% clay'),
    ('Wheat', 'K', 'elemental', 0.0, NULL, 'Citric acid', 'mg/kg', 80,  120,  NULL, 35, 'dryland', 0, 0, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'No K recommended on soils with < 35% clay'),
    ('Wheat', 'K', 'elemental', 0.0, NULL, 'Citric acid', 'mg/kg', 120, NULL, NULL, 35, 'dryland', 0, 0, 'FERTASA Handbook', '5.4.3.1.3', 2019, 'No K recommended on soils with < 35% clay');

COMMIT;
