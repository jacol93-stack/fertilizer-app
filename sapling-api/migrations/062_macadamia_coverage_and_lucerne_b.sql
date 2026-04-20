-- ============================================================
-- 062: Macadamia coverage + lucerne B fertilization
-- ============================================================
-- Sources:
--   * Schoeman ("Macadamia Nutrition") deck hosted by SAMAC, OCR'd
--     from PDF page renders 2026-04-20.
--   * SAMAC Young-Tree Nutrition deck (Schoeman, via gfnc.co.za mirror).
--   * FERTASA Handbook image-table 519 (Lucerne B fertilisation).
--
-- Scope:
--   1. Macadamia annual application rate table — first rate-table entry
--      for mac, derived from Schoeman's "Application norms" slide which
--      publishes yield-agnostic annual NPK + Zn + B rates.
--   2. Macadamia soil-test threshold overrides — K and mineral-N, where
--      Schoeman's young-tree deck gives mac-specific thresholds that
--      differ meaningfully from the universal soil_sufficiency bands.
--   3. Lucerne B fertilisation — 3-row table by soil texture from the
--      FERTASA image 519.
--
-- Deferred (flagged for a later pass):
--   * Mac leaf norms upgrade: Schoeman deck shows a 3-column comparison
--     table (FSSA / current SA / international) but column headers were
--     cut off in OCR, so authoritative attribution of the newer values
--     is uncertain. Existing FERTASA-sourced sufficient_min/max rows
--     remain in place until the physical deck or a clean source
--     confirms which column is the "current SA norm".
--   * Mac-specific P thresholds vary by clay-texture (<6% / 6-15% / >15%).
--     Our crop_sufficiency_overrides schema doesn't split on texture;
--     deferred pending either a schema extension or an explicit clay-
--     texture-indexed sufficiency path.
--   * Boron foliar protocol from Schoeman (mac is highly B-sensitive):
--     schema-less for now; plan as a foliar_protocol row once we decide
--     the foliar schema for nut crops.
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. Macadamia annual application rates (yield-agnostic)
-- ------------------------------------------------------------
-- From Schoeman SAMAC nutrition deck "Application norms" slide.
-- Published as broad annual ranges for bearing macadamia orchards.
-- Encoded as yield_min=0, yield_max=NULL so the rate-table lookup
-- matches any yield context.

DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Macadamia'
  AND source_section = 'Schoeman 2021 — Application norms';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Macadamia', 'N', 'elemental', 0, NULL, NULL, 126, 166,
        'SAMAC / Schoeman', 'Schoeman 2021 — Application norms', 2021,
        'Bearing-orchard annual N range. Apply within the Mar-Oct N window (SAMAC phenology).'),
    ('Macadamia', 'P', 'elemental', 0, NULL, NULL, 26, 32,
        'SAMAC / Schoeman', 'Schoeman 2021 — Application norms', 2021,
        'Bearing-orchard annual P range.'),
    ('Macadamia', 'K', 'elemental', 0, NULL, NULL, 156, 180,
        'SAMAC / Schoeman', 'Schoeman 2021 — Application norms', 2021,
        'Bearing-orchard annual K range.'),
    ('Macadamia', 'Zn', 'elemental', 0, NULL, NULL, 8, 41,
        'SAMAC / Schoeman', 'Schoeman 2021 — Application norms', 2021,
        'Annual Zn (bearing). Wide range reflects orchard-to-orchard variation; narrow via leaf analysis.'),
    ('Macadamia', 'B', 'elemental', 0, NULL, NULL, 6, 23,
        'SAMAC / Schoeman', 'Schoeman 2021 — Application norms', 2021,
        'Annual B (bearing). Mac is highly B-sensitive; deficiency limits kernel recovery.');

-- ------------------------------------------------------------
-- 2. Macadamia-specific soil sufficiency thresholds
-- ------------------------------------------------------------
-- From SAMAC young-tree nutrition deck "SOIL ANALYSIS NORMS" slide.
-- Only unambiguous crop-wide thresholds seeded here. Texture-varying
-- P threshold is deferred (see header notes).

DELETE FROM public.crop_sufficiency_overrides
WHERE crop = 'Macadamia' AND parameter IN ('K', 'N (mineral)');

INSERT INTO public.crop_sufficiency_overrides
    (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Macadamia', 'K', NULL, 85, 145, NULL,
        'SAMAC young-tree deck (Schoeman): mac-specific K in soil solution thresholds. < 85 mg/kg = mac requires K supplement. 85-145 = sufficient. > 145 may cause Mg antagonism.'),
    ('Macadamia', 'N (mineral)', NULL, 6, 15, NULL,
        'SAMAC young-tree deck: mineral-N (NH4+ + NO3-) in topsoil. < 6 mg/kg = deficient. 6-15 = ok. Mac orchards under low-OM sandy soils drop below the 6 threshold readily.');

-- ------------------------------------------------------------
-- 3. Lucerne B fertilisation by soil B + texture
-- ------------------------------------------------------------
-- FERTASA image-table 519 (lucerne B). Applies when hot-water
-- extractable B < 0.5 mg/kg; rate varies by soil texture.

DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Lucerne'
  AND nutrient = 'B'
  AND source_section = '5.12.2 image 519';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     clay_pct_min, clay_pct_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Lucerne', 'B', 'elemental', 0, NULL, 'Hot-water', 'mg/kg', 0, 0.5, 0,  14,  'dryland', 1, 1,
        'FERTASA Handbook', '5.12.2 image 519', 2019,
        'Sand (< 14% clay). Annual B rate when soil B < 0.5 mg/kg hot-water extract.'),
    ('Lucerne', 'B', 'elemental', 0, NULL, 'Hot-water', 'mg/kg', 0, 0.5, 14, 35,  'dryland', 2, 2,
        'FERTASA Handbook', '5.12.2 image 519', 2019,
        'Medium clay (14-35%). Annual B rate at low soil B.'),
    ('Lucerne', 'B', 'elemental', 0, NULL, 'Hot-water', 'mg/kg', 0, 0.5, 35, NULL, 'dryland', 3, 3,
        'FERTASA Handbook', '5.12.2 image 519', 2019,
        'Clay (>= 35%). Annual B rate at low soil B.');

COMMIT;
