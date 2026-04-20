-- ============================================================
-- 049: Seed potato N (dryland + irrigation) + P rate tables (FERTASA 5.6.2)
-- ============================================================
-- Source: sapling-api/data/fertasa_handbook/5_6_2_potatoes.json
--   Table 5.6.2.1 = N dryland (clay × yield)
--   Table 5.6.2.2 = N irrigation (clay × yield)
--   Table 5.6.2.4 = P (soil-P × yield)
--
-- K tables (5.6.2.5 + 5.6.2.6) and Ca/Mg tables seeded in a follow-up
-- migration — K tables switch on CEC ≤/> 6, which needs cec_min/cec_max
-- columns added to the schema first.
--
-- Shape decisions:
--   * Yield stored as discrete points (15, 20, 25, 30 for dryland;
--     30, 40-80 for irrigation). Same pattern as wheat P (migration 047).
--   * Clay stored via the clay_pct_min/max filter columns.
--     "< 10" → clay_pct_max = 10
--     "10 - 20" → clay_pct_min = 10, clay_pct_max = 20
--     "> 20" → clay_pct_min = 20
--   * water_regime distinguishes the two N tables. Dryland tables have
--     clay filter ALSO gated on water_regime='dryland'; irrigation on
--     'irrigated'.
--   * P table publishes Bray-1 AND Olsen equivalents for every band.
--     Seeded as separate rows per method so readings from either lab
--     type land on the right cell.
--   * P soil-P band 30+ row specifies minimum application rate; the "30"
--     cells at low yields stabilise rather than decline (capital-building).
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Potato'
  AND source_section IN ('5.6.2.1', '5.6.2.2', '5.6.2.4');

-- ============================================================
-- Table 5.6.2.1: N dryland (clay × yield)
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     clay_pct_min, clay_pct_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Clay < 10% (sandy)
    ('Potato', 'N', 'elemental', 15, 15, NULL, 10, 'dryland', 80,  80,  'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    ('Potato', 'N', 'elemental', 20, 20, NULL, 10, 'dryland', 95,  95,  'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    ('Potato', 'N', 'elemental', 25, 25, NULL, 10, 'dryland', 110, 110, 'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    ('Potato', 'N', 'elemental', 30, 30, NULL, 10, 'dryland', 130, 130, 'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    -- Clay 10-20%
    ('Potato', 'N', 'elemental', 15, 15, 10, 20, 'dryland', 70,  70,  'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    ('Potato', 'N', 'elemental', 20, 20, 10, 20, 'dryland', 85,  85,  'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    ('Potato', 'N', 'elemental', 25, 25, 10, 20, 'dryland', 100, 100, 'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    ('Potato', 'N', 'elemental', 30, 30, 10, 20, 'dryland', 120, 120, 'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    -- Clay > 20%
    ('Potato', 'N', 'elemental', 15, 15, 20, NULL, 'dryland', 60,  60,  'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    ('Potato', 'N', 'elemental', 20, 20, 20, NULL, 'dryland', 75,  75,  'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    ('Potato', 'N', 'elemental', 25, 25, 20, NULL, 'dryland', 90,  90,  'FERTASA Handbook', '5.6.2.1', 2019, NULL),
    ('Potato', 'N', 'elemental', 30, 30, 20, NULL, 'dryland', 110, 110, 'FERTASA Handbook', '5.6.2.1', 2019, NULL);

-- ============================================================
-- Table 5.6.2.2: N irrigation (clay × yield)
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     clay_pct_min, clay_pct_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Clay < 10%
    ('Potato', 'N', 'elemental', 30, 30, NULL, 10, 'irrigated', 170, 170, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 40, 40, NULL, 10, 'irrigated', 220, 220, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 50, 50, NULL, 10, 'irrigated', 250, 250, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 60, 60, NULL, 10, 'irrigated', 275, 275, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 70, 70, NULL, 10, 'irrigated', 300, 300, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 80, 80, NULL, 10, 'irrigated', 320, 320, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    -- Clay 10-20%
    ('Potato', 'N', 'elemental', 30, 30, 10, 20, 'irrigated', 150, 150, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 40, 40, 10, 20, 'irrigated', 190, 190, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 50, 50, 10, 20, 'irrigated', 220, 220, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 60, 60, 10, 20, 'irrigated', 240, 240, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 70, 70, 10, 20, 'irrigated', 260, 260, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 80, 80, 10, 20, 'irrigated', 280, 280, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    -- Clay > 20%
    ('Potato', 'N', 'elemental', 30, 30, 20, NULL, 'irrigated', 130, 130, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 40, 40, 20, NULL, 'irrigated', 160, 160, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 50, 50, 20, NULL, 'irrigated', 180, 180, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 60, 60, 20, NULL, 'irrigated', 200, 200, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 70, 70, 20, NULL, 'irrigated', 220, 220, 'FERTASA Handbook', '5.6.2.2', 2019, NULL),
    ('Potato', 'N', 'elemental', 80, 80, 20, NULL, 'irrigated', 240, 240, 'FERTASA Handbook', '5.6.2.2', 2019, NULL);

-- ============================================================
-- Table 5.6.2.4: P (soil-P × yield) — Bray-1 and Olsen variants
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Bray-1 band 0-5 (= Olsen 0-3)
    ('Potato', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 0, 5, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 0, 5, 115, 115, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 0, 5, 130, 130, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Bray-1', 'mg/kg', 0, 5, 145, 145, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Bray-1', 'mg/kg', 0, 5, 160, 160, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Bray-1', 'mg/kg', 0, 5, 175, 175, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Bray-1', 'mg/kg', 0, 5, 190, 190, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Bray-1', 'mg/kg', 0, 5, 205, 205, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 10, 10, 'Olsen', 'mg/kg', 0, 3, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Olsen', 'mg/kg', 0, 3, 115, 115, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Olsen', 'mg/kg', 0, 3, 130, 130, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Olsen', 'mg/kg', 0, 3, 145, 145, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Olsen', 'mg/kg', 0, 3, 160, 160, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Olsen', 'mg/kg', 0, 3, 175, 175, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Olsen', 'mg/kg', 0, 3, 190, 190, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Olsen', 'mg/kg', 0, 3, 205, 205, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),

    -- Bray-1 band 6-10 (= Olsen 4-6)
    ('Potato', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 6, 10, 80,  80,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 6, 10, 90,  90,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 6, 10, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Bray-1', 'mg/kg', 6, 10, 110, 110, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Bray-1', 'mg/kg', 6, 10, 120, 120, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Bray-1', 'mg/kg', 6, 10, 130, 130, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Bray-1', 'mg/kg', 6, 10, 140, 140, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Bray-1', 'mg/kg', 6, 10, 150, 150, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 10, 10, 'Olsen', 'mg/kg', 4, 6, 80,  80,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Olsen', 'mg/kg', 4, 6, 90,  90,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Olsen', 'mg/kg', 4, 6, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Olsen', 'mg/kg', 4, 6, 110, 110, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Olsen', 'mg/kg', 4, 6, 120, 120, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Olsen', 'mg/kg', 4, 6, 130, 130, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Olsen', 'mg/kg', 4, 6, 140, 140, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Olsen', 'mg/kg', 4, 6, 150, 150, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),

    -- Bray-1 band 11-19 (= Olsen 7-11)
    ('Potato', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 11, 19, 60,  60,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 11, 19, 70,  70,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 11, 19, 80,  80,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Bray-1', 'mg/kg', 11, 19, 90,  90,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Bray-1', 'mg/kg', 11, 19, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Bray-1', 'mg/kg', 11, 19, 110, 110, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Bray-1', 'mg/kg', 11, 19, 120, 120, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Bray-1', 'mg/kg', 11, 19, 130, 130, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 10, 10, 'Olsen', 'mg/kg', 7, 11, 60,  60,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Olsen', 'mg/kg', 7, 11, 70,  70,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Olsen', 'mg/kg', 7, 11, 80,  80,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Olsen', 'mg/kg', 7, 11, 90,  90,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Olsen', 'mg/kg', 7, 11, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Olsen', 'mg/kg', 7, 11, 110, 110, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Olsen', 'mg/kg', 7, 11, 120, 120, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Olsen', 'mg/kg', 7, 11, 130, 130, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),

    -- Bray-1 band 20-25 (= Olsen 12-15)
    ('Potato', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 20, 25, 50,  50,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 20, 25, 60,  60,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 20, 25, 70,  70,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Bray-1', 'mg/kg', 20, 25, 80,  80,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Bray-1', 'mg/kg', 20, 25, 90,  90,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Bray-1', 'mg/kg', 20, 25, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Bray-1', 'mg/kg', 20, 25, 110, 110, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Bray-1', 'mg/kg', 20, 25, 120, 120, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 10, 10, 'Olsen', 'mg/kg', 12, 15, 50,  50,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Olsen', 'mg/kg', 12, 15, 60,  60,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Olsen', 'mg/kg', 12, 15, 70,  70,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Olsen', 'mg/kg', 12, 15, 80,  80,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Olsen', 'mg/kg', 12, 15, 90,  90,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Olsen', 'mg/kg', 12, 15, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Olsen', 'mg/kg', 12, 15, 110, 110, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Olsen', 'mg/kg', 12, 15, 120, 120, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),

    -- Bray-1 band 25-30 (= Olsen 15-18)
    ('Potato', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 25, 30, 30,  30,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 25, 30, 40,  40,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 25, 30, 50,  50,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Bray-1', 'mg/kg', 25, 30, 60,  60,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Bray-1', 'mg/kg', 25, 30, 70,  70,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Bray-1', 'mg/kg', 25, 30, 80,  80,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Bray-1', 'mg/kg', 25, 30, 90,  90,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Bray-1', 'mg/kg', 25, 30, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 10, 10, 'Olsen', 'mg/kg', 15, 18, 30,  30,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 20, 20, 'Olsen', 'mg/kg', 15, 18, 40,  40,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 30, 30, 'Olsen', 'mg/kg', 15, 18, 50,  50,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 40, 40, 'Olsen', 'mg/kg', 15, 18, 60,  60,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 50, 50, 'Olsen', 'mg/kg', 15, 18, 70,  70,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 60, 60, 'Olsen', 'mg/kg', 15, 18, 80,  80,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 70, 70, 'Olsen', 'mg/kg', 15, 18, 90,  90,  'FERTASA Handbook', '5.6.2.4', 2019, NULL),
    ('Potato', 'P', 'elemental', 80, 80, 'Olsen', 'mg/kg', 15, 18, 100, 100, 'FERTASA Handbook', '5.6.2.4', 2019, NULL),

    -- Bray-1 band 30+ (= Olsen 18+) — minimum rate to stabilise P status
    ('Potato', 'P', 'elemental', 10, 10, 'Bray-1', 'mg/kg', 30, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 20, 20, 'Bray-1', 'mg/kg', 30, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 30, 30, 'Bray-1', 'mg/kg', 30, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 40, 40, 'Bray-1', 'mg/kg', 30, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 50, 50, 'Bray-1', 'mg/kg', 30, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 60, 60, 'Bray-1', 'mg/kg', 30, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 70, 70, 'Bray-1', 'mg/kg', 30, NULL, 35, 35, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 80, 80, 'Bray-1', 'mg/kg', 30, NULL, 45, 45, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 10, 10, 'Olsen', 'mg/kg', 18, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 20, 20, 'Olsen', 'mg/kg', 18, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 30, 30, 'Olsen', 'mg/kg', 18, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 40, 40, 'Olsen', 'mg/kg', 18, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 50, 50, 'Olsen', 'mg/kg', 18, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 60, 60, 'Olsen', 'mg/kg', 18, NULL, 30, 30, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 70, 70, 'Olsen', 'mg/kg', 18, NULL, 35, 35, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P'),
    ('Potato', 'P', 'elemental', 80, 80, 'Olsen', 'mg/kg', 18, NULL, 45, 45, 'FERTASA Handbook', '5.6.2.4', 2019, 'Minimum maintenance rate at high soil-P');

COMMIT;
