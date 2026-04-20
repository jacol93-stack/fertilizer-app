-- ============================================================
-- 058: Seed cotton + dry bean + groundnut rate tables (FERTASA)
-- ============================================================
-- Sources: FERTASA Handbook sections 5.9 (Cotton), 5.5.2 (Dry Beans),
-- 5.5.3 (Groundnuts). Refreshed via authenticated scrape 2026-04-20.
--
-- Scope: ~60 cells covering legume + industrial field crops.
--
--   Cotton    N   4 cells  yield → N (1-D, 4 yield bands)
--   Cotton    K   4 cells  yield → K (1-D, 4 yield bands)
--   Cotton    P  16 cells  Bray-1 × yield 2-D (from the P-specific table)
--   Dry bean  N  15 cells  yield × texture (clay / sandy loam / sand)
--   Dry bean  P  15 cells  Bray-1 × yield
--   Groundnut N   6 cells  yield → N (not-inoculated case only; see note)
--
-- Encoding notes:
--   * Cotton Table 0 publishes N, P and K per yield band. The separate
--     Table 3 gives a soil-test-aware P calibration, so we prefer Table 3
--     for P and take only N and K from Table 0. No double-seeding.
--   * Cotton yield "4 500+" is open-top (yield_max = NULL).
--   * Dry bean N texture axis is encoded via clay_pct bands: clay ≥ 35%,
--     sandy loam 10-35%, sand < 10%.
--   * Dry bean P Bray-1 band ">55" covers everything above 34 mg/kg in
--     the published table (there's an apparent gap 34-55 in the scraper
--     output; interpreted as the plateau rate extending from 34 upward).
--   * Groundnut N: SASRI-style practice is inoculation with Bradyrhizobium,
--     which mostly eliminates N need. FERTASA's table gives two columns —
--     "inoculated" (0-50 kg N/ha) vs "not inoculated" (10-60 kg N/ha).
--     Seeded as the conservative not-inoculated case. If the user confirms
--     inoculation, a +0-10 kg N reduction applies downstream (noted).
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE (crop = 'Cotton'      AND source_section IN ('5.9 Table 1', '5.9 Table 4'))
   OR (crop = 'Bean (Dry)'  AND source_section IN ('5.5.2 Table 1', '5.5.2 Table 2'))
   OR (crop = 'Groundnut'   AND source_section = '5.5.3 Table 2');

-- ============================================================
-- Cotton N and K (5.9 Table 1) — yield-only axis
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- N
    ('Cotton', 'N', 'elemental', 1.0, 1.0, 'dryland',  90,  90, 'FERTASA Handbook', '5.9 Table 1', 2019, 'yield in t seed cotton'),
    ('Cotton', 'N', 'elemental', 2.0, 2.0, 'dryland', 175, 175, 'FERTASA Handbook', '5.9 Table 1', 2019, 'yield in t seed cotton'),
    ('Cotton', 'N', 'elemental', 2.5, 2.5, 'dryland', 220, 220, 'FERTASA Handbook', '5.9 Table 1', 2019, 'yield in t seed cotton'),
    ('Cotton', 'N', 'elemental', 4.5, NULL, 'dryland', 250, 250, 'FERTASA Handbook', '5.9 Table 1', 2019, 'yield >= 4.5 t seed cotton; table caps at 4500+'),
    -- K
    ('Cotton', 'K', 'elemental', 1.0, 1.0, 'dryland',  60,  60, 'FERTASA Handbook', '5.9 Table 1', 2019, 'yield in t seed cotton'),
    ('Cotton', 'K', 'elemental', 2.0, 2.0, 'dryland',  70,  70, 'FERTASA Handbook', '5.9 Table 1', 2019, 'yield in t seed cotton'),
    ('Cotton', 'K', 'elemental', 2.5, 2.5, 'dryland',  85,  85, 'FERTASA Handbook', '5.9 Table 1', 2019, 'yield in t seed cotton'),
    ('Cotton', 'K', 'elemental', 4.5, NULL, 'dryland', 140, 140, 'FERTASA Handbook', '5.9 Table 1', 2019, 'yield >= 4.5 t seed cotton');

-- ============================================================
-- Cotton P (5.9 Table 4) — Bray-1 × yield
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Bray-1 band 0-10
    ('Cotton', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 0,  10,   'dryland', 15, 15, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 0,  10,   'dryland', 20, 20, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 0,  10,   'dryland', 30, 30, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 4.0, 4.0, 'Bray-1', 'mg/kg', 0,  10,   'dryland', 30, 30, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    -- 10-15
    ('Cotton', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 10, 10, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 15, 15, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 20, 20, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 4.0, 4.0, 'Bray-1', 'mg/kg', 10, 15,   'dryland', 25, 25, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    -- 15-20
    ('Cotton', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 0,  0,  'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 10, 10, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 15, 15, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 4.0, 4.0, 'Bray-1', 'mg/kg', 15, 20,   'dryland', 15, 15, 'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    -- >20 (open top)
    ('Cotton', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 20, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 20, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 3.0, 3.0, 'Bray-1', 'mg/kg', 20, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.9 Table 4', 2019, NULL),
    ('Cotton', 'P', 'elemental', 4.0, 4.0, 'Bray-1', 'mg/kg', 20, NULL, 'dryland', 0,  0,  'FERTASA Handbook', '5.9 Table 4', 2019, NULL);

-- ============================================================
-- Dry bean N (5.5.2 Table 1) — yield × texture
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     clay_pct_min, clay_pct_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Clay (≥ 35%)
    ('Bean (Dry)', 'N', 'elemental', 1.0, 1.0, 35, NULL, 'dryland', 10,  10,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Clay soil'),
    ('Bean (Dry)', 'N', 'elemental', 1.5, 1.5, 35, NULL, 'dryland', 20,  20,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Clay soil'),
    ('Bean (Dry)', 'N', 'elemental', 2.0, 2.0, 35, NULL, 'dryland', 30,  30,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Clay soil'),
    ('Bean (Dry)', 'N', 'elemental', 2.5, 2.5, 35, NULL, 'dryland', 50,  50,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Clay soil'),
    ('Bean (Dry)', 'N', 'elemental', 3.0, 3.0, 35, NULL, 'dryland', 70,  70,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Clay soil'),
    -- Sandy loam (10-35%)
    ('Bean (Dry)', 'N', 'elemental', 1.0, 1.0, 10, 35,   'dryland', 20,  20,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sandy loam'),
    ('Bean (Dry)', 'N', 'elemental', 1.5, 1.5, 10, 35,   'dryland', 35,  35,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sandy loam'),
    ('Bean (Dry)', 'N', 'elemental', 2.0, 2.0, 10, 35,   'dryland', 45,  45,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sandy loam'),
    ('Bean (Dry)', 'N', 'elemental', 2.5, 2.5, 10, 35,   'dryland', 65,  65,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sandy loam'),
    ('Bean (Dry)', 'N', 'elemental', 3.0, 3.0, 10, 35,   'dryland', 85,  85,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sandy loam'),
    -- Sand (< 10%)
    ('Bean (Dry)', 'N', 'elemental', 1.0, 1.0, 0,  10,   'dryland', 30,  30,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sand'),
    ('Bean (Dry)', 'N', 'elemental', 1.5, 1.5, 0,  10,   'dryland', 45,  45,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sand'),
    ('Bean (Dry)', 'N', 'elemental', 2.0, 2.0, 0,  10,   'dryland', 60,  60,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sand'),
    ('Bean (Dry)', 'N', 'elemental', 2.5, 2.5, 0,  10,   'dryland', 75,  75,  'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sand'),
    ('Bean (Dry)', 'N', 'elemental', 3.0, 3.0, 0,  10,   'dryland', 105, 105, 'FERTASA Handbook', '5.5.2 Table 1', 2019, 'Sand');

-- ============================================================
-- Dry bean P (5.5.2 Table 2) — Bray-1 × yield
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- 0-13
    ('Bean (Dry)', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 0,  13,   'dryland', 16, 16, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    ('Bean (Dry)', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 0,  13,   'dryland', 22, 22, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    ('Bean (Dry)', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 0,  13,   'dryland', 28, 28, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    -- 13-20
    ('Bean (Dry)', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 13, 20,   'dryland', 12, 12, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    ('Bean (Dry)', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 13, 20,   'dryland', 16, 16, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    ('Bean (Dry)', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 13, 20,   'dryland', 20, 20, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    -- 20-27
    ('Bean (Dry)', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 20, 27,   'dryland', 10, 10, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    ('Bean (Dry)', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 20, 27,   'dryland', 13, 13, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    ('Bean (Dry)', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 20, 27,   'dryland', 16, 16, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    -- 27-34
    ('Bean (Dry)', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 27, 34,   'dryland', 9,  9,  'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    ('Bean (Dry)', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 27, 34,   'dryland', 12, 12, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    ('Bean (Dry)', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 27, 34,   'dryland', 15, 15, 'FERTASA Handbook', '5.5.2 Table 2', 2019, NULL),
    -- 34+ (published as ">55"; interpreted as 34+ plateau)
    ('Bean (Dry)', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 34, NULL, 'dryland', 5,  5,  'FERTASA Handbook', '5.5.2 Table 2', 2019, 'Table header shows ">55" — scraper output may have skipped a 34-55 band. Minimum rate of 5 kg P/ha used as plateau.'),
    ('Bean (Dry)', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 34, NULL, 'dryland', 5,  5,  'FERTASA Handbook', '5.5.2 Table 2', 2019, 'Table header shows ">55" — scraper output may have skipped a 34-55 band. Minimum rate of 5 kg P/ha used as plateau.'),
    ('Bean (Dry)', 'P', 'elemental', 2.5, 2.5, 'Bray-1', 'mg/kg', 34, NULL, 'dryland', 5,  5,  'FERTASA Handbook', '5.5.2 Table 2', 2019, 'Table header shows ">55" — scraper output may have skipped a 34-55 band. Minimum rate of 5 kg P/ha used as plateau.');

-- ============================================================
-- Groundnut N (5.5.3 Table 2) — yield → N (not-inoculated case)
-- ============================================================
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Groundnut', 'N', 'elemental', 1, 1, 'dryland', 10, 10, 'FERTASA Handbook', '5.5.3 Table 2', 2019, 'Not-inoculated case. Subtract ~10 kg N/ha if Bradyrhizobium inoculation is confirmed.'),
    ('Groundnut', 'N', 'elemental', 2, 2, 'dryland', 20, 20, 'FERTASA Handbook', '5.5.3 Table 2', 2019, 'Not-inoculated case.'),
    ('Groundnut', 'N', 'elemental', 3, 3, 'dryland', 30, 30, 'FERTASA Handbook', '5.5.3 Table 2', 2019, 'Not-inoculated case.'),
    ('Groundnut', 'N', 'elemental', 4, 4, 'dryland', 40, 40, 'FERTASA Handbook', '5.5.3 Table 2', 2019, 'Not-inoculated case.'),
    ('Groundnut', 'N', 'elemental', 5, 5, 'dryland', 50, 50, 'FERTASA Handbook', '5.5.3 Table 2', 2019, 'Not-inoculated case.'),
    ('Groundnut', 'N', 'elemental', 6, 6, 'dryland', 60, 60, 'FERTASA Handbook', '5.5.3 Table 2', 2019, 'Not-inoculated case.');

COMMIT;
