-- ============================================================
-- 050: Seed canola N rate table (FERTASA 5.5.1.X, image 501)
-- ============================================================
-- Source: sapling-api/data/fertasa_handbook/image_transcriptions.json (key "501")
--
-- Unique shape: this is our first rate table with no soil-test axis.
-- Canola N is keyed on region × rainfall × prior_crop × yield, NOT on
-- soil Nmin or soil-N (FERTASA doesn't treat canola N as soil-calibrated).
--
-- Dimensions used:
--   * region ('Southern Cape' | 'Swartland')
--   * rainfall_mm band (half-open ranges)
--   * prior_crop ('Lucerne' | 'Annual legume' | 'Grain stubble')
--   * yield target (discrete point)
--
-- Published quirks captured:
--   * Swartland after lucerne is NULL (not a practiced rotation there —
--     Swartland's sandy/low-rainfall profile doesn't support lucerne).
--     Those cells are simply omitted from the seed; lookup will miss
--     and fall back to heuristic for that specific combination.
--   * Rates published as ranges ("25-30") are stored as both min and max.
--
-- Requires: the context passed to lookup_rate_table() must supply
-- 'region', 'rainfall_mm', and 'prior_crop'. Without these, the rate-
-- table lookup misses (by design — canola N IS the regional call).
-- The router's _rate_table_context() helper will need to populate these
-- from client/farm records when the user works canola; flagged as a
-- follow-up (the current default is just water_regime='dryland').
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Canola'
  AND source_section = '5.5.1.X';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     rainfall_mm_min, rainfall_mm_max,
     region, prior_crop, water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Southern Cape, 65% winter rainfall
    -- < 350 mm, yield 1.25 t/ha
    ('Canola', 'N', 'elemental', 1.25, 1.25, 0,   350,  'Southern Cape', 'Lucerne',        'dryland', 10, 10, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    ('Canola', 'N', 'elemental', 1.25, 1.25, 0,   350,  'Southern Cape', 'Annual legume',  'dryland', 25, 30, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    ('Canola', 'N', 'elemental', 1.25, 1.25, 0,   350,  'Southern Cape', 'Grain stubble',  'dryland', 30, 50, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    -- 350-425 mm, yield 1.50 t/ha
    ('Canola', 'N', 'elemental', 1.50, 1.50, 350, 425,  'Southern Cape', 'Lucerne',        'dryland', 10, 20, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    ('Canola', 'N', 'elemental', 1.50, 1.50, 350, 425,  'Southern Cape', 'Annual legume',  'dryland', 30, 35, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    ('Canola', 'N', 'elemental', 1.50, 1.50, 350, 425,  'Southern Cape', 'Grain stubble',  'dryland', 50, 70, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    -- 425-500 mm, yield 2.00 t/ha
    ('Canola', 'N', 'elemental', 2.00, 2.00, 425, 500,  'Southern Cape', 'Lucerne',        'dryland', 20, 30, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    ('Canola', 'N', 'elemental', 2.00, 2.00, 425, 500,  'Southern Cape', 'Annual legume',  'dryland', 30, 45, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    ('Canola', 'N', 'elemental', 2.00, 2.00, 425, 500,  'Southern Cape', 'Grain stubble',  'dryland', 60, 90, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    -- > 500 mm, yield 2.50 t/ha
    ('Canola', 'N', 'elemental', 2.50, 2.50, 500, NULL, 'Southern Cape', 'Lucerne',        'dryland', 40, 50,  'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    ('Canola', 'N', 'elemental', 2.50, 2.50, 500, NULL, 'Southern Cape', 'Annual legume',  'dryland', 50, 55,  'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),
    ('Canola', 'N', 'elemental', 2.50, 2.50, 500, NULL, 'Southern Cape', 'Grain stubble',  'dryland', 80, 110, 'FERTASA Handbook', '5.5.1.X', 2019, 'Southern Cape 65% winter rainfall'),

    -- Swartland, 83% winter rainfall (no lucerne rotation practiced)
    -- < 325 mm, yield 1.25 t/ha
    ('Canola', 'N', 'elemental', 1.25, 1.25, 0,   325,  'Swartland',     'Annual legume',  'dryland', 50, 70,  'FERTASA Handbook', '5.5.1.X', 2019, 'Swartland 83% winter rainfall'),
    ('Canola', 'N', 'elemental', 1.25, 1.25, 0,   325,  'Swartland',     'Grain stubble',  'dryland', 70, 90,  'FERTASA Handbook', '5.5.1.X', 2019, 'Swartland 83% winter rainfall'),
    -- 325-425 mm, yield 1.75 t/ha
    ('Canola', 'N', 'elemental', 1.75, 1.75, 325, 425,  'Swartland',     'Annual legume',  'dryland', 70, 90,   'FERTASA Handbook', '5.5.1.X', 2019, 'Swartland 83% winter rainfall'),
    ('Canola', 'N', 'elemental', 1.75, 1.75, 325, 425,  'Swartland',     'Grain stubble',  'dryland', 90, 110,  'FERTASA Handbook', '5.5.1.X', 2019, 'Swartland 83% winter rainfall'),
    -- > 425 mm, yield 2.50 t/ha
    ('Canola', 'N', 'elemental', 2.50, 2.50, 425, NULL, 'Swartland',     'Annual legume',  'dryland', 90,  110, 'FERTASA Handbook', '5.5.1.X', 2019, 'Swartland 83% winter rainfall'),
    ('Canola', 'N', 'elemental', 2.50, 2.50, 425, NULL, 'Swartland',     'Grain stubble',  'dryland', 110, 130, 'FERTASA Handbook', '5.5.1.X', 2019, 'Swartland 83% winter rainfall');

COMMIT;
