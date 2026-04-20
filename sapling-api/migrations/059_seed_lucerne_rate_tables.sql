-- ============================================================
-- 059: Seed lucerne rate tables (FERTASA 5.12.2)
-- ============================================================
-- Source: FERTASA Handbook section 5.12.2 (Lucerne). Refreshed via
-- authenticated scrape 2026-04-20 into
-- sapling-api/data/fertasa_handbook/5_12_2_lucerne.json.
--
-- Lucerne yield is published as DRY MATTER (t/ha), not fresh bale or
-- grain. Yield bands: 4, 8, 12, 16, 20 t DM/ha.
--
-- Two rate tables seeded (third K table using K-%-of-CEC skipped
-- pending the cec_min/max schema extension — Table 2 below uses
-- the standard soil-K mg/kg axis which most SA labs report directly).
--
--   Lucerne P  60 cells  clay × soil-P × yield
--     Clay bands: < 15%, > 15%
--     Bray-1 bands: (0,4) (4,8) (8,16) (16,24) (24,32) (32+)
--     Yields: 4, 8, 12, 16, 20 t DM/ha
--     Range cells like "0-10" preserved as rate_min/rate_max range.
--
--   Lucerne K  40 cells  soil-K × yield
--     Ambic-K bands: (0,20) (20,40) (40,60) (60,80) (80,100)
--                    (100,120) (120,160) (160+)
--     Same yield band set.
--
-- N establishment (Table 3) is situational prose — not a clean rate
-- table. S fertilisation (Table 6) has 3 categorical yield tiers
-- (Low / Medium / High). Both deferred to a later migration.
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Lucerne'
  AND source_section IN ('5.12.2 Table 1', '5.12.2 Table 2');

-- Lucerne P (5.12.2 Table 1) — 60 cells (clay × soil-P × yield)
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     clay_pct_min, clay_pct_max, water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 0, 4, 0, 15, 'dryland', 93.0, 93.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 0, 4, 0, 15, 'dryland', 118.0, 118.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 0, 4, 0, 15, 'dryland', 145.0, 145.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 0, 4, 0, 15, 'dryland', 183.0, 183.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 0, 4, 0, 15, 'dryland', 228.0, 228.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 4, 8, 0, 15, 'dryland', 73.0, 73.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 4, 8, 0, 15, 'dryland', 98.0, 98.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 4, 8, 0, 15, 'dryland', 125.0, 125.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 4, 8, 0, 15, 'dryland', 163.0, 163.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 4, 8, 0, 15, 'dryland', 208.0, 208.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 8, 16, 0, 15, 'dryland', 33.0, 33.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 8, 16, 0, 15, 'dryland', 58.0, 58.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 8, 16, 0, 15, 'dryland', 85.0, 85.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 8, 16, 0, 15, 'dryland', 123.0, 123.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 8, 16, 0, 15, 'dryland', 168.0, 168.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 16, 24, 0, 15, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 16, 24, 0, 15, 'dryland', 18.0, 18.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 16, 24, 0, 15, 'dryland', 45.0, 45.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 16, 24, 0, 15, 'dryland', 83.0, 83.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 16, 24, 0, 15, 'dryland', 128.0, 128.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 24, 32, 0, 15, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 24, 32, 0, 15, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 24, 32, 0, 15, 'dryland', 5.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 24, 32, 0, 15, 'dryland', 43.0, 43.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 24, 32, 0, 15, 'dryland', 88.0, 88.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 32, NULL, 0, 15, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 32, NULL, 0, 15, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 32, NULL, 0, 15, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 32, NULL, 0, 15, 'dryland', 3.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 32, NULL, 0, 15, 'dryland', 48.0, 48.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay < 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 0, 4, 15, NULL, 'dryland', 121.0, 121.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 0, 4, 15, NULL, 'dryland', 153.0, 153.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 0, 4, 15, NULL, 'dryland', 189.0, 189.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 0, 4, 15, NULL, 'dryland', 237.0, 237.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 0, 4, 15, NULL, 'dryland', 296.0, 296.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 4, 8, 15, NULL, 'dryland', 95.0, 95.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 4, 8, 15, NULL, 'dryland', 127.0, 127.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 4, 8, 15, NULL, 'dryland', 163.0, 163.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 4, 8, 15, NULL, 'dryland', 211.0, 211.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 4, 8, 15, NULL, 'dryland', 270.0, 270.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 8, 16, 15, NULL, 'dryland', 43.0, 43.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 8, 16, 15, NULL, 'dryland', 75.0, 75.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 8, 16, 15, NULL, 'dryland', 111.0, 111.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 8, 16, 15, NULL, 'dryland', 159.0, 159.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 8, 16, 15, NULL, 'dryland', 218.0, 218.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 16, 24, 15, NULL, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 16, 24, 15, NULL, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 16, 24, 15, NULL, 'dryland', 7.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 16, 24, 15, NULL, 'dryland', 55.0, 55.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 16, 24, 15, NULL, 'dryland', 114.0, 114.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 24, 32, 15, NULL, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 24, 32, 15, NULL, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 24, 32, 15, NULL, 'dryland', 7.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 24, 32, 15, NULL, 'dryland', 55.0, 55.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 24, 32, 15, NULL, 'dryland', 114.0, 114.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 4, 4, 'Bray-1', 'mg/kg', 32, NULL, 15, NULL, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 8, 8, 'Bray-1', 'mg/kg', 32, NULL, 15, NULL, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 12, 12, 'Bray-1', 'mg/kg', 32, NULL, 15, NULL, 'dryland', 0.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 16, 16, 'Bray-1', 'mg/kg', 32, NULL, 15, NULL, 'dryland', 3.0, 10.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield'),
    ('Lucerne', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 32, NULL, 15, NULL, 'dryland', 62.0, 62.0, 'FERTASA Handbook', '5.12.2 Table 1', 2019, 'Clay > 15%; dry matter yield');

-- Lucerne K (5.12.2 Table 2) — 40 cells (soil-K × yield)
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Lucerne', 'K', 'elemental', 4, 4, 'Ambic', 'mg/kg', 0, 20, 'dryland', 208.0, 208.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 8, 8, 'Ambic', 'mg/kg', 0, 20, 'dryland', 270.0, 270.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 12, 12, 'Ambic', 'mg/kg', 0, 20, 'dryland', 327.0, 327.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 16, 16, 'Ambic', 'mg/kg', 0, 20, 'dryland', 379.0, 379.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 20, 20, 'Ambic', 'mg/kg', 0, 20, 'dryland', 426.0, 426.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 4, 4, 'Ambic', 'mg/kg', 20, 40, 'dryland', 168.0, 168.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 8, 8, 'Ambic', 'mg/kg', 20, 40, 'dryland', 230.0, 230.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 12, 12, 'Ambic', 'mg/kg', 20, 40, 'dryland', 287.0, 287.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 16, 16, 'Ambic', 'mg/kg', 20, 40, 'dryland', 339.0, 339.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 20, 20, 'Ambic', 'mg/kg', 20, 40, 'dryland', 386.0, 386.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 4, 4, 'Ambic', 'mg/kg', 40, 60, 'dryland', 128.0, 128.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 8, 8, 'Ambic', 'mg/kg', 40, 60, 'dryland', 190.0, 190.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 12, 12, 'Ambic', 'mg/kg', 40, 60, 'dryland', 247.0, 247.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 16, 16, 'Ambic', 'mg/kg', 40, 60, 'dryland', 299.0, 299.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 20, 20, 'Ambic', 'mg/kg', 40, 60, 'dryland', 346.0, 346.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 4, 4, 'Ambic', 'mg/kg', 60, 80, 'dryland', 88.0, 88.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 8, 8, 'Ambic', 'mg/kg', 60, 80, 'dryland', 150.0, 150.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 12, 12, 'Ambic', 'mg/kg', 60, 80, 'dryland', 207.0, 207.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 16, 16, 'Ambic', 'mg/kg', 60, 80, 'dryland', 259.0, 259.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 20, 20, 'Ambic', 'mg/kg', 60, 80, 'dryland', 306.0, 306.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 4, 4, 'Ambic', 'mg/kg', 80, 100, 'dryland', 48.0, 48.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 8, 8, 'Ambic', 'mg/kg', 80, 100, 'dryland', 110.0, 110.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 12, 12, 'Ambic', 'mg/kg', 80, 100, 'dryland', 167.0, 167.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 16, 16, 'Ambic', 'mg/kg', 80, 100, 'dryland', 219.0, 219.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 20, 20, 'Ambic', 'mg/kg', 80, 100, 'dryland', 266.0, 266.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 4, 4, 'Ambic', 'mg/kg', 100, 120, 'dryland', 8.0, 8.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 8, 8, 'Ambic', 'mg/kg', 100, 120, 'dryland', 70.0, 70.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 12, 12, 'Ambic', 'mg/kg', 100, 120, 'dryland', 127.0, 127.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 16, 16, 'Ambic', 'mg/kg', 100, 120, 'dryland', 179.0, 179.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 20, 20, 'Ambic', 'mg/kg', 100, 120, 'dryland', 226.0, 226.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 4, 4, 'Ambic', 'mg/kg', 120, 160, 'dryland', 0.0, 0.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 8, 8, 'Ambic', 'mg/kg', 120, 160, 'dryland', 0.0, 0.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 12, 12, 'Ambic', 'mg/kg', 120, 160, 'dryland', 47.0, 47.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 16, 16, 'Ambic', 'mg/kg', 120, 160, 'dryland', 99.0, 99.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 20, 20, 'Ambic', 'mg/kg', 120, 160, 'dryland', 146.0, 146.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 4, 4, 'Ambic', 'mg/kg', 160, NULL, 'dryland', 0.0, 0.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 8, 8, 'Ambic', 'mg/kg', 160, NULL, 'dryland', 0.0, 0.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 12, 12, 'Ambic', 'mg/kg', 160, NULL, 'dryland', 0.0, 0.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 16, 16, 'Ambic', 'mg/kg', 160, NULL, 'dryland', 19.0, 19.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield'),
    ('Lucerne', 'K', 'elemental', 20, 20, 'Ambic', 'mg/kg', 160, NULL, 'dryland', 66.0, 66.0, 'FERTASA Handbook', '5.12.2 Table 2', 2019, 'Dry matter yield');

COMMIT;
