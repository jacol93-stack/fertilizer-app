-- ============================================================
-- 051: Seed maize N rate table (ARC-GCI MIG 2017, Table 2)
-- ============================================================
-- Source: sapling-api/data/arc_gci/mig2017.pdf (page 79),
--         OCR'd to sapling-api/data/arc_gci/mig2017_ocr.txt
--         (lines ~4464-4540).
--
-- Cross-validation: The abbreviated 4x5 version of the same table is
-- reproduced in the FERTASA handbook at section 5.4.4 (see
-- data/fertasa_handbook/maize_old_guidelines.pdf Table 5.4.4). Every
-- overlapping cell matches exactly. Both trace to Andries Bloem's 2002
-- SA Graan/Grain research compiled by the North West Department of
-- Agriculture. MIG 2017 publishes the full 8x9 granular table; FERTASA
-- publishes the abbreviated 4x5 subset.
--
-- MIG 2017 is the authoritative SA maize reference — FERTASA's 5.4.4
-- section in the current electronic handbook is literally just a link
-- to the old-guidelines PDF, and the PDF points at the same research.
--
-- Data quality:
--   * Provenance: Tier-2 (ARC peer-reviewed research body), OCR-sourced.
--   * The single cell at (clay=15%, yield=5.5 t/ha) reads "133" via OCR;
--     linear row pattern suggests 130 is more likely. Seeded as 133 per
--     OCR to preserve fidelity; flagged in source_note for manual
--     verification against the PDF.
--
-- Schema fit:
--   * Yield stored as discrete points (2.0, 2.5, ... 6.0 t/ha).
--   * Clay stored via clay_pct_min / clay_pct_max. The MIG published
--     rows at 5, 10, 15, 20, 25, 30, 40, 50%. Stored as narrow ranges
--     centred on each published point, with [min, max) boundaries.
--   * water_regime = 'dryland' — MIG 2017 explicitly frames these
--     guidelines for dryland summer-rainfall production. Irrigated
--     maize has different rules (not in this table).
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Maize'
  AND nutrient = 'N'
  AND source_section = 'Table 2 (p.79)';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     clay_pct_min, clay_pct_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Clay 5% (centre of 0-7.5 band)
    ('Maize', 'N', 'elemental', 2.0, 2.0, 0,  7.5, 'dryland', 23,  23,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 2.5, 2.5, 0,  7.5, 'dryland', 41,  41,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.0, 3.0, 0,  7.5, 'dryland', 58,  58,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.5, 3.5, 0,  7.5, 'dryland', 75,  75,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.0, 4.0, 0,  7.5, 'dryland', 92,  92,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.5, 4.5, 0,  7.5, 'dryland', 109, 109, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.0, 5.0, 0,  7.5, 'dryland', 126, 126, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.5, 5.5, 0,  7.5, 'dryland', 143, 143, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 6.0, 6.0, 0,  7.5, 'dryland', 160, 160, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    -- Clay 10%
    ('Maize', 'N', 'elemental', 2.0, 2.0, 7.5, 12.5, 'dryland', 17,  17,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 2.5, 2.5, 7.5, 12.5, 'dryland', 35,  35,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.0, 3.0, 7.5, 12.5, 'dryland', 52,  52,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.5, 3.5, 7.5, 12.5, 'dryland', 69,  69,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.0, 4.0, 7.5, 12.5, 'dryland', 86,  86,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.5, 4.5, 7.5, 12.5, 'dryland', 103, 103, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.0, 5.0, 7.5, 12.5, 'dryland', 120, 120, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.5, 5.5, 7.5, 12.5, 'dryland', 137, 137, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 6.0, 6.0, 7.5, 12.5, 'dryland', 154, 154, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    -- Clay 15%
    ('Maize', 'N', 'elemental', 2.0, 2.0, 12.5, 17.5, 'dryland', 10,  10,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 2.5, 2.5, 12.5, 17.5, 'dryland', 28,  28,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.0, 3.0, 12.5, 17.5, 'dryland', 45,  45,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.5, 3.5, 12.5, 17.5, 'dryland', 62,  62,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.0, 4.0, 12.5, 17.5, 'dryland', 79,  79,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.5, 4.5, 12.5, 17.5, 'dryland', 96,  96,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.0, 5.0, 12.5, 17.5, 'dryland', 113, 113, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.5, 5.5, 12.5, 17.5, 'dryland', 133, 133, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, 'OCR read 133; row linear pattern suggests 130 — verify against PDF p.79'),
    ('Maize', 'N', 'elemental', 6.0, 6.0, 12.5, 17.5, 'dryland', 147, 147, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    -- Clay 20%
    ('Maize', 'N', 'elemental', 2.0, 2.0, 17.5, 22.5, 'dryland', 4,   4,   'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 2.5, 2.5, 17.5, 22.5, 'dryland', 22,  22,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.0, 3.0, 17.5, 22.5, 'dryland', 39,  39,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.5, 3.5, 17.5, 22.5, 'dryland', 56,  56,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.0, 4.0, 17.5, 22.5, 'dryland', 73,  73,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.5, 4.5, 17.5, 22.5, 'dryland', 90,  90,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.0, 5.0, 17.5, 22.5, 'dryland', 107, 107, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.5, 5.5, 17.5, 22.5, 'dryland', 124, 124, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 6.0, 6.0, 17.5, 22.5, 'dryland', 141, 141, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    -- Clay 25%
    ('Maize', 'N', 'elemental', 2.0, 2.0, 22.5, 27.5, 'dryland', 0,   0,   'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 2.5, 2.5, 22.5, 27.5, 'dryland', 16,  16,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.0, 3.0, 22.5, 27.5, 'dryland', 33,  33,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.5, 3.5, 22.5, 27.5, 'dryland', 50,  50,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.0, 4.0, 22.5, 27.5, 'dryland', 67,  67,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.5, 4.5, 22.5, 27.5, 'dryland', 84,  84,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.0, 5.0, 22.5, 27.5, 'dryland', 101, 101, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.5, 5.5, 22.5, 27.5, 'dryland', 118, 118, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 6.0, 6.0, 22.5, 27.5, 'dryland', 135, 135, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    -- Clay 30%
    ('Maize', 'N', 'elemental', 2.0, 2.0, 27.5, 35,   'dryland', 0,   0,   'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 2.5, 2.5, 27.5, 35,   'dryland', 9,   9,   'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.0, 3.0, 27.5, 35,   'dryland', 26,  26,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.5, 3.5, 27.5, 35,   'dryland', 43,  43,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.0, 4.0, 27.5, 35,   'dryland', 60,  60,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.5, 4.5, 27.5, 35,   'dryland', 77,  77,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.0, 5.0, 27.5, 35,   'dryland', 94,  94,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.5, 5.5, 27.5, 35,   'dryland', 111, 111, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 6.0, 6.0, 27.5, 35,   'dryland', 128, 128, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    -- Clay 40%
    ('Maize', 'N', 'elemental', 2.0, 2.0, 35, 45, 'dryland', 0,   0,   'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 2.5, 2.5, 35, 45, 'dryland', 0,   0,   'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.0, 3.0, 35, 45, 'dryland', 14,  14,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.5, 3.5, 35, 45, 'dryland', 31,  31,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.0, 4.0, 35, 45, 'dryland', 48,  48,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.5, 4.5, 35, 45, 'dryland', 65,  65,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.0, 5.0, 35, 45, 'dryland', 82,  82,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.5, 5.5, 35, 45, 'dryland', 99,  99,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 6.0, 6.0, 35, 45, 'dryland', 116, 116, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    -- Clay 50% (open upper — anything ≥45%)
    ('Maize', 'N', 'elemental', 2.0, 2.0, 45, NULL, 'dryland', 0,   0,   'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 2.5, 2.5, 45, NULL, 'dryland', 0,   0,   'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.0, 3.0, 45, NULL, 'dryland', 0,   0,   'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 3.5, 3.5, 45, NULL, 'dryland', 18,  18,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.0, 4.0, 45, NULL, 'dryland', 35,  35,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 4.5, 4.5, 45, NULL, 'dryland', 52,  52,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.0, 5.0, 45, NULL, 'dryland', 69,  69,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 5.5, 5.5, 45, NULL, 'dryland', 86,  86,  'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL),
    ('Maize', 'N', 'elemental', 6.0, 6.0, 45, NULL, 'dryland', 103, 103, 'ARC-GCI Maize Information Guide', 'Table 2 (p.79)', 2017, NULL);

COMMIT;
