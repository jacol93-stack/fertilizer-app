-- ============================================================
-- 069: Canola S (soil-test based) + Lucerne S (yield-band)
-- ============================================================
-- FERTASA publishes per-crop S-fertilization tables for the two
-- SA crops where S response is consistently economic:
--
--   * Canola 5.5.1 Table 5.5.1.5 — S driven by soil-S content only
--     (soil-S  < 6  mg/kg  → apply >15-20 kg S/ha, deficiency)
--     (soil-S 7-12 mg/kg  → 15 kg S/ha maintenance)
--     (soil-S > 12 mg/kg  → 10 kg S/ha, below maintenance)
--     FERTASA prose (5.5.1 canola): "The sulphur requirements of
--     canola are approximately four times those of wheat." The
--     guidelines target canola's crucifer-high S demand without
--     introducing a yield-axis table.
--
--   * Lucerne 5.12.2 Table 5.12.2.7 — yield-band annual maintenance
--     (Low yield  → 25 kg S/ha/yr)
--     (Medium     → 30 kg S/ha/yr)
--     (High       → 40 kg S/ha/yr)
--     FERTASA Low/Medium/High yield labels are qualitative in this
--     section. We map them to the same DM yield bands the lucerne
--     P and K tables use (4-8 / 8-16 / 16+ t DM/ha — see 059).
--     The secondary "25-50 kg/ha, adequate for 1-2 years" one-off
--     sulphate-sulphur build-up option is captured in source_note
--     rather than as rows, since it's a different decision mode
--     (capital-building one-off vs. annual maintenance).
--
-- NOT seeded this migration:
--   * Wheat S (5.4.3.2.3 Table + image 484) — rate table is only
--     in the handbook's image assets, not scraped OCR text. Needs
--     an OCR pass (same pipeline as maize MIG 2017). DATA_AUDIT_PLAN
--     already lists this as deferred.
--   * Tobacco S — FERTASA 5.11 gives an excess-S quality constraint
--     ("S content of tobacco fertilizer compounds should preferably
--     not exceed 2-3%"), not a rate. Needs a separate "formulation
--     constraint" mechanism; schema TBD.
--   * Dry bean / groundnut / soya S — FERTASA discusses S as a
--     carrier concern (through single-super or ammoniated-super),
--     not as a distinct rate. No standalone recommendation to seed.
--
-- Cells: 3 canola + 3 lucerne = 6 rows.
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
 WHERE (crop = 'Canola'  AND source_section = '5.5.1.5')
    OR (crop = 'Lucerne' AND source_section = '5.12.2.7');

-- ------------------------------------------------------------
-- Canola S (5.5.1.5) — yield-agnostic, soil-test driven
-- ------------------------------------------------------------
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Canola', 'S', 'elemental', 0, NULL, 'Ca-phosphate', 'mg/kg',  0,  6, 'dryland', 15, 20,
        'FERTASA Handbook', '5.5.1.5', 2019,
        'Soil-S < 6 mg/kg = deficient. FERTASA prose: "S application above specific crop requirement (>15-20 S/ha)." Ca-phosphate extraction is FERTASA''s named method for S (see 5.4.3.2.3 wheat prose). Canola S demand ~4× wheat; 5.5.1 notes alternative per-yield mode of 10-15 kg S/ha/t on soils with deficiency history.'),
    ('Canola', 'S', 'elemental', 0, NULL, 'Ca-phosphate', 'mg/kg',  7, 12, 'dryland', 15, 15,
        'FERTASA Handbook', '5.5.1.5', 2019,
        'Soil-S 7-12 mg/kg = sufficient; apply 15 kg S/ha at maintenance level. FERTASA 5.5.1.5.'),
    ('Canola', 'S', 'elemental', 0, NULL, 'Ca-phosphate', 'mg/kg', 12, NULL, 'dryland', 10, 10,
        'FERTASA Handbook', '5.5.1.5', 2019,
        'Soil-S > 12 mg/kg = more than sufficient; apply 10 kg S/ha below maintenance. FERTASA 5.5.1.5.');

-- ------------------------------------------------------------
-- Lucerne S (5.12.2.7) — yield-band annual maintenance
-- ------------------------------------------------------------
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Lucerne', 'S', 'elemental', 4,    8, NULL, 25, 25, 'FERTASA Handbook', '5.12.2.7', 2019,
        'Low DM yield band (4-8 t/ha). Annual maintenance where deficiencies exist and S-containing NPK fertilizer is used. FERTASA 5.12.2.7. Yield-band mapping (Low / Medium / High) taken from the lucerne P/K yield axis in the same section (migration 059). One-off alternative: sulphate sulphur 25-50 kg/ha adequate for 1-2 years.'),
    ('Lucerne', 'S', 'elemental', 8,   16, NULL, 30, 30, 'FERTASA Handbook', '5.12.2.7', 2019,
        'Medium DM yield band (8-16 t/ha). Annual maintenance. FERTASA 5.12.2.7.'),
    ('Lucerne', 'S', 'elemental', 16, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.12.2.7', 2019,
        'High DM yield band (16+ t/ha). Annual maintenance. FERTASA 5.12.2.7.');

COMMIT;
