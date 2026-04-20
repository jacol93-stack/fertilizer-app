-- ============================================================
-- FERTASA-direct corrections to crop_requirements + fertasa_leaf_norms
-- ============================================================
-- Companion to migration 042 (growth stages). This one touches:
--
-- 1) crop_requirements — three P0 data bugs and three P1 fixes:
--    * Groundnut: N=10 was fertilizer-starter, not removal. Fix to 30.
--    * Soybean:   N=10 same bug. Fix to ~90 per FERTASA 5.5.5.1.
--    * Cotton:    yield_unit="t lint/ha" but values match per-t seed-
--                 cotton (FERTASA Table 5.9.1). Fix unit + default yield.
--    * Lucerne:   Ca 8→13, Mg 2→2.7, S 2→2.7 per FERTASA 5.12.2.5.
--    * Bean (Dry): S 2.5→3.0 per FERTASA 5.5.2 prose.
--
-- 2) fertasa_leaf_norms — add ~60 new rows covering crops FERTASA
--    publishes in the consolidated Table 5.3 image-tables that were
--    missing from the app (Citrus, Fruit trees, Maize, Wheat, Soya
--    beans, Lucerne, Sugar cane, Avocado cultivar-split). Also adds
--    Na and Cl completeness to existing Macadamia + Canola rows.
--
-- Every new row cites FERTASA table number + source quote in `notes`.
-- Values transcribed from
-- data/fertasa_handbook/image_transcriptions.json (images 466 sugar
-- cane, 468 citrus, 470 fruit trees, 472 maize/wheat/soya/lucerne,
-- 506 soya removal, 517 avocado soil+leaf) — cross-check there if any
-- number looks off.
--
-- Full audit + reasoning: research_fertasa_*.md memory files.
-- ============================================================

BEGIN;

-- ─── 1) crop_requirements fixes ───────────────────────────────────────

-- Groundnut: fix the N=10 fertilizer-starter bug + Ca/S/Mg per FERTASA Table 5.5.3.1.
-- 1 ton unshelled pods = 30 kg N, 3.15 kg P, 9 kg K, 1.4 kg Ca, 1.55 kg Mg, 10 kg S.
UPDATE crop_requirements SET
    n = 30.0,
    p = 3.15,
    k = 9.0,
    ca = 1.4,
    mg = 1.55,
    s = 10.0,
    updated_at = now()
WHERE crop = 'Groundnut';

-- Soybean: fix the N=10 bug per FERTASA Table 5.5.5.1 (image 506 transcription).
-- Per 1 t seed: 75-105 N (mid 90), 8-9 P (mid 8.5), 25-40 K (mid 32.5).
UPDATE crop_requirements SET
    n = 90.0,
    p = 8.5,
    k = 32.5,
    updated_at = now()
WHERE crop = 'Soybean';

-- Cotton: resolve unit/value mismatch. FERTASA Table 5.9.1 gives per-t
-- seed cotton: 90 N, 15 P, 60 K (matches our values) — NOT per-t lint.
-- Rename unit; update default yield (1.5 t lint ≈ 4.3 t seed cotton @ 35% lint).
UPDATE crop_requirements SET
    yield_unit = 't seed cotton/ha',
    default_yield = 4.3,
    updated_at = now()
WHERE crop = 'Cotton';

-- Lucerne: Ca/Mg/S fixes per FERTASA Table 5.12.2.5.
UPDATE crop_requirements SET
    ca = 13.0,
    mg = 2.7,
    s = 2.7,
    updated_at = now()
WHERE crop = 'Lucerne';

-- Bean (Dry): S per FERTASA 5.5.2 prose ("approximately 3 kg of sulphur
-- is removed per ton of beans").
UPDATE crop_requirements SET
    s = 3.0,
    updated_at = now()
WHERE crop = 'Bean (Dry)';


-- ─── 2) fertasa_leaf_norms additions ─────────────────────────────────

-- Clean up any prior test-seeded rows for these crops before inserting.
DELETE FROM fertasa_leaf_norms WHERE crop IN (
    'Citrus (Valencia)', 'Citrus (Navel)', 'Citrus (Lemon)', 'Citrus (Grapefruit)',
    'Apple', 'Pear', 'Peach', 'Nectarine', 'Apricot', 'Plum', 'Wine Grape', 'Table Grape',
    'Maize', 'Maize (irrigated)', 'Wheat', 'Soybean', 'Lucerne',
    'Sugarcane',
    'Avocado'
);


-- ─── Citrus leaf norms (FERTASA Table 5.3.2 — image 468) ──────────────
-- 5-band: deficiency / below / normal / above / excess. Per-variety (N/P/K)
-- + shared (Ca/Mg/Na/Cl/S + micros). Unit: % for macros, mg/kg for micros.

INSERT INTO fertasa_leaf_norms (crop, element, unit, deficient_max, low_max,
    sufficient_min, sufficient_max, high_min, excess_min,
    sample_part, sample_timing, source_section, notes) VALUES

-- Valencia
('Citrus (Valencia)', 'N',  '%',     1.80, 2.09, 2.10, 2.30, 2.31, 2.51,
    '4-7 mo old leaf from non-bearing twigs, spring flush', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2 Table 5.3.2: Valencia N 2.10-2.30% normal.'),
('Citrus (Valencia)', 'K',  '%',     0.60, 0.89, 0.90, 1.50, 1.51, 1.81,
    '4-7 mo old leaf from non-bearing twigs', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Valencia K 0.90-1.50% normal.'),

-- Navels
('Citrus (Navel)', 'N',  '%',        1.90, 2.39, 2.40, 2.60, 2.61, 2.81,
    '4-7 mo old leaf from non-bearing twigs, spring flush', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Navels N 2.40-2.60% normal.'),
('Citrus (Navel)', 'P',  '%',        0.09, 0.10, 0.11, 0.14, 0.15, 0.18,
    '4-7 mo old leaf from non-bearing twigs', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Navels P 0.11-0.14% normal.'),
('Citrus (Navel)', 'K',  '%',        0.40, 0.69, 0.70, 1.10, 1.11, 1.41,
    '4-7 mo old leaf from non-bearing twigs', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Navels K 0.70-1.10% normal.'),

-- Lemons
('Citrus (Lemon)', 'N',  '%',        1.90, 2.29, 2.30, 2.60, 2.61, 2.81,
    '4-7 mo old leaf from non-bearing twigs', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Lemons N 2.30-2.60% normal.'),
('Citrus (Lemon)', 'P',  '%',        0.09, 0.10, 0.11, 0.14, 0.15, 0.18,
    '4-7 mo old leaf from non-bearing twigs', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Lemons P 0.11-0.14% normal.'),
('Citrus (Lemon)', 'K',  '%',        0.60, 0.79, 0.80, 1.20, 1.21, 1.71,
    '4-7 mo old leaf from non-bearing twigs', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Lemons K 0.80-1.20% normal.'),

-- Grapefruit
('Citrus (Grapefruit)', 'N',  '%',   1.90, 2.29, 2.30, 2.50, 2.51, 2.81,
    '4-7 mo old leaf from non-bearing twigs', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Grapefruit N 2.30-2.50% normal.'),
('Citrus (Grapefruit)', 'P',  '%',   0.08, 0.09, 0.10, 0.14, 0.15, 0.18,
    '4-7 mo old leaf from non-bearing twigs', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Grapefruit P 0.10-0.14% normal.'),
('Citrus (Grapefruit)', 'K',  '%',   0.40, 0.79, 0.80, 1.00, 1.01, 1.21,
    '4-7 mo old leaf from non-bearing twigs', 'Mar-May',
    '5.3.2', 'FERTASA 5.3.2: Grapefruit K 0.80-1.00% normal.'),

-- Shared across all citrus varieties (Ca/Mg/Na/Cl/S + micros)
('Citrus (Valencia)', 'Ca', '%',     2.50, 3.49, 3.50, 6.00, 6.10, 7.01,
    '4-7 mo leaf', 'Mar-May', '5.3.2', 'FERTASA 5.3.2: shared Ca norm across citrus varieties.'),
('Citrus (Valencia)', 'Mg', '%',     0.25, 0.34, 0.35, 0.50, 0.51, 0.76,
    '4-7 mo leaf', 'Mar-May', '5.3.2', 'FERTASA 5.3.2: shared Mg.'),
('Citrus (Valencia)', 'S',  '%',     0.14, 0.19, 0.20, 0.30, 0.31, 0.51,
    '4-7 mo leaf', 'Mar-May', '5.3.2', 'FERTASA 5.3.2: shared S.'),
('Citrus (Valencia)', 'B',  'mg/kg', 40,   74,   75,   200,  201,  301,
    '4-7 mo leaf', 'Mar-May', '5.3.2', 'FERTASA 5.3.2: shared B.'),
('Citrus (Valencia)', 'Zn', 'mg/kg', 15,   24,   25,   100,  101,  201,
    '4-7 mo leaf', 'Mar-May', '5.3.2', 'FERTASA 5.3.2: shared Zn.'),
('Citrus (Valencia)', 'Mn', 'mg/kg', 25,   39,   40,   150,  151,  301,
    '4-7 mo leaf', 'Mar-May', '5.3.2', 'FERTASA 5.3.2: shared Mn.'),
('Citrus (Valencia)', 'Cu', 'mg/kg', 3,    NULL, 5,    20,   21,   41,
    '4-7 mo leaf', 'Mar-May', '5.3.2', 'FERTASA 5.3.2: shared Cu. Below-normal single value = 4 mg/kg.'),
('Citrus (Valencia)', 'Fe', 'mg/kg', NULL, 49,   50,   300,  NULL, NULL,
    '4-7 mo leaf', 'Mar-May', '5.3.2', 'FERTASA 5.3.2: shared Fe.'),
('Citrus (Valencia)', 'Mo', 'mg/kg', 0.03, 0.04, 0.05, 3.00, NULL, NULL,
    '4-7 mo leaf', 'Mar-May', '5.3.2', 'FERTASA 5.3.2: shared Mo.');


-- ─── Fruit trees leaf norms (FERTASA Table 5.3.3 — image 470) ─────────
-- The -/+/++ bands mean: "-" = lower deficiency threshold, "+" = upper
-- (approaching excess), "++" = absolute excess.
-- Sample: summer leaves mid-shoot, typically Jan-Feb for deciduous SA.

INSERT INTO fertasa_leaf_norms (crop, element, unit, deficient_max, low_max,
    sufficient_min, sufficient_max, high_min, excess_min,
    sample_part, sample_timing, source_section, notes) VALUES

-- Apple
('Apple', 'N',  '%',     2.00, NULL, 2.00, 3.00, 3.00, NULL,    'Mid-shoot leaf', 'Jan-Feb (70-120 days after full bloom)', '5.3.3', 'FERTASA 5.3.3 Table 5.3.3 Apple.'),
('Apple', 'P',  '%',     0.12, NULL, 0.12, 0.22, 0.22, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),
('Apple', 'K',  '%',     0.80, NULL, 0.80, 2.20, 2.20, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),
('Apple', 'Ca', '%',     0.70, NULL, 0.70, 1.60, 1.60, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3. Ca target particularly critical for bitter-pit-prone cvs.'),
('Apple', 'Mg', '%',     0.30, NULL, 0.30, 0.60, 0.60, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),
('Apple', 'Na', '%',     NULL, NULL, NULL, 0.05, 0.05, 0.20,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3: +=0.05%, ++ toxic=0.20%.'),
('Apple', 'Cl', '%',     NULL, NULL, NULL, 0.15, 0.15, 0.35,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3: +=0.15%, ++ toxic=0.35%.'),
('Apple', 'Mn', 'mg/kg', 25,   NULL, 25,   140,  140,  NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),
('Apple', 'Fe', 'mg/kg', 60,   NULL, 60,   240,  240,  NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),
('Apple', 'B',  'mg/kg', 25,   NULL, 25,   40,   40,   140,     'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3: -=25, +=40, ++ toxic=140 mg/kg.'),
('Apple', 'Zn', 'mg/kg', 15,   NULL, 15,   NULL, NULL, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3: below 15 = deficient; upper threshold not given.'),

-- Pear
('Pear', 'N',  '%',      2.00, NULL, 2.00, 2.80, 2.80, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3 Pear.'),
('Pear', 'P',  '%',      0.10, NULL, 0.10, 0.18, 0.18, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),
('Pear', 'K',  '%',      0.70, NULL, 0.70, 2.00, 2.00, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),
('Pear', 'Ca', '%',      0.80, NULL, 0.80, 1.60, 1.60, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),
('Pear', 'Mg', '%',      0.25, NULL, 0.25, 0.60, 0.60, NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),
('Pear', 'B',  'mg/kg',  22,   NULL, 22,   29,   29,   NULL,    'Mid-shoot leaf', 'Jan-Feb', '5.3.3', 'FERTASA 5.3.3.'),

-- Peach
('Peach', 'N',  '%',     2.20, NULL, 2.20, 3.80, 3.80, NULL,    'Mid-shoot leaf', 'Dec-Jan (60-80 days after full bloom)', '5.3.3', 'FERTASA 5.3.3 Peach.'),
('Peach', 'P',  '%',     0.12, NULL, 0.12, 0.20, 0.20, NULL,    'Mid-shoot leaf', 'Dec-Jan', '5.3.3', 'FERTASA 5.3.3.'),
('Peach', 'K',  '%',     0.80, NULL, 0.80, 3.20, 3.20, NULL,    'Mid-shoot leaf', 'Dec-Jan', '5.3.3', 'FERTASA 5.3.3.'),
('Peach', 'Ca', '%',     1.20, NULL, 1.20, 3.50, 3.50, NULL,    'Mid-shoot leaf', 'Dec-Jan', '5.3.3', 'FERTASA 5.3.3.'),
('Peach', 'Mg', '%',     0.35, NULL, 0.35, 1.10, 1.10, NULL,    'Mid-shoot leaf', 'Dec-Jan', '5.3.3', 'FERTASA 5.3.3.'),
('Peach', 'Mn', 'mg/kg', 30,   NULL, 30,   140,  140,  400,     'Mid-shoot leaf', 'Dec-Jan', '5.3.3', 'FERTASA 5.3.3: ++ toxic 400.'),
('Peach', 'B',  'mg/kg', 24,   NULL, 24,   45,   45,   80,      'Mid-shoot leaf', 'Dec-Jan', '5.3.3', 'FERTASA 5.3.3.'),

-- Apricot
('Apricot', 'N',  '%',   1.80, NULL, 1.80, 2.80, 2.80, NULL,    'Mid-shoot leaf', 'Dec (60-90 DAFB)', '5.3.3', 'FERTASA 5.3.3 Apricot.'),
('Apricot', 'P',  '%',   0.11, NULL, 0.11, 0.20, 0.20, NULL,    'Mid-shoot leaf', 'Dec', '5.3.3', 'FERTASA 5.3.3.'),
('Apricot', 'K',  '%',   2.00, NULL, 2.00, 3.60, 3.60, NULL,    'Mid-shoot leaf', 'Dec', '5.3.3', 'FERTASA 5.3.3.'),
('Apricot', 'Ca', '%',   1.10, NULL, 1.10, 1.80, 1.80, NULL,    'Mid-shoot leaf', 'Dec', '5.3.3', 'FERTASA 5.3.3.'),
('Apricot', 'Mg', '%',   0.25, NULL, 0.25, 0.70, 0.70, NULL,    'Mid-shoot leaf', 'Dec', '5.3.3', 'FERTASA 5.3.3.'),

-- Plum
('Plum', 'N',  '%',      2.20, NULL, 2.20, 3.00, 3.00, NULL,    'Mid-shoot leaf', 'Jan', '5.3.3', 'FERTASA 5.3.3 Plum.'),
('Plum', 'K',  '%',      2.00, NULL, 2.00, 3.20, 3.20, NULL,    'Mid-shoot leaf', 'Jan', '5.3.3', 'FERTASA 5.3.3.'),
('Plum', 'Ca', '%',      1.20, NULL, 1.20, 2.60, 2.60, NULL,    'Mid-shoot leaf', 'Jan', '5.3.3', 'FERTASA 5.3.3.'),
('Plum', 'B',  'mg/kg',  30,   NULL, 30,   45,   45,   180,     'Mid-shoot leaf', 'Jan', '5.3.3', 'FERTASA 5.3.3: ++ toxic 180 for Japanese plum.'),

-- Grape (Wine Grape) — fruit-tree row applies to both wine + table grape
('Wine Grape', 'N',  '%',    1.60, NULL, 1.60, 2.40, 2.40, NULL,  'Petiole opposite basal cluster', 'Full bloom', '5.3.3', 'FERTASA 5.3.3 Grape. Applies to wine grape (WC).'),
('Wine Grape', 'P',  '%',    0.12, NULL, 0.12, 0.40, 0.40, NULL,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Wine Grape', 'K',  '%',    0.80, NULL, 0.80, 1.60, 1.60, NULL,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Wine Grape', 'Ca', '%',    1.60, NULL, 1.60, 2.40, 2.40, NULL,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Wine Grape', 'Mg', '%',    0.30, NULL, 0.30, 0.60, 0.60, NULL,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Wine Grape', 'B',  'mg/kg', 30,  NULL, 30,   65,   65,   400,   'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3: ++ toxic 400 mg/kg B in grape.'),
('Wine Grape', 'Mn', 'mg/kg', 20,  NULL, 20,   300,  300,  1000,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Wine Grape', 'Fe', 'mg/kg', 60,  NULL, 60,   240,  240,  NULL,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),

('Table Grape', 'N',  '%',    1.60, NULL, 1.60, 2.40, 2.40, NULL,  'Petiole opposite basal cluster', 'Full bloom', '5.3.3', 'FERTASA 5.3.3 Grape. Applies to table grape.'),
('Table Grape', 'P',  '%',    0.12, NULL, 0.12, 0.40, 0.40, NULL,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Table Grape', 'K',  '%',    0.80, NULL, 0.80, 1.60, 1.60, NULL,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Table Grape', 'Ca', '%',    1.60, NULL, 1.60, 2.40, 2.40, NULL,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Table Grape', 'Mg', '%',    0.30, NULL, 0.30, 0.60, 0.60, NULL,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Table Grape', 'B',  'mg/kg', 30,  NULL, 30,   65,   65,   400,   'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.'),
('Table Grape', 'Mn', 'mg/kg', 20,  NULL, 20,   300,  300,  1000,  'Petiole', 'Full bloom', '5.3.3', 'FERTASA 5.3.3.');


-- ─── Broadacre leaf norms (FERTASA Table 5.3.4 — image 472) ───────────
-- Single sufficient-level value per element per crop (not banded).
-- Units: % for macros, mg/kg for micros.

INSERT INTO fertasa_leaf_norms (crop, element, unit, deficient_max, low_max,
    sufficient_min, sufficient_max, high_min, excess_min,
    sample_part, sample_timing, source_section, notes) VALUES

-- Maize
('Maize', 'N',  '%',     NULL, NULL, 3.00, NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4: sufficient level 3.00% N maize.'),
('Maize', 'P',  '%',     NULL, NULL, 0.25, NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4.'),
('Maize', 'K',  '%',     NULL, NULL, 1.90, NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4: 5.4.4 adds "K <1.9% at flowering = deficiency".'),
('Maize', 'Ca', '%',     NULL, NULL, 0.40, NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4.'),
('Maize', 'Mg', '%',     NULL, NULL, 0.25, NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4.'),
('Maize', 'Mn', 'mg/kg', NULL, NULL, 15,   NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4.'),
('Maize', 'Fe', 'mg/kg', NULL, NULL, 25,   NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4.'),
('Maize', 'B',  'mg/kg', NULL, 10,   10,   NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4: 5.4.4 adds "B <8-10 mg/kg at flowering = deficiency".'),
('Maize', 'Cu', 'mg/kg', NULL, NULL, 5,    NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4.'),
('Maize', 'Zn', 'mg/kg', NULL, NULL, 15,   NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4.'),
('Maize', 'Mo', 'mg/kg', NULL, NULL, 0.2,  NULL, NULL, NULL,   'Opposite/below ear leaf', 'Tasseling / silking', '5.3.4', 'FERTASA 5.3.4.'),

-- Wheat
('Wheat', 'N',  '%',     NULL, NULL, 2.60, NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.3.4.'),
('Wheat', 'P',  '%',     NULL, NULL, 0.30, NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.3.4.'),
('Wheat', 'K',  '%',     NULL, NULL, 1.80, NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.3.4.'),
('Wheat', 'Ca', '%',     NULL, NULL, 0.25, NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.3.4.'),
('Wheat', 'Mg', '%',     NULL, NULL, 0.15, NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.3.4.'),
('Wheat', 'S',  '%',     NULL, 0.15, 0.15, NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.4.3 prose: leaf S <0.15% = deficiency.'),
('Wheat', 'Mn', 'mg/kg', NULL, NULL, 30,   NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.3.4.'),
('Wheat', 'B',  'mg/kg', NULL, NULL, 15,   NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.3.4.'),
('Wheat', 'Zn', 'mg/kg', NULL, NULL, 15,   NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.3.4.'),
('Wheat', 'Mo', 'mg/kg', NULL, NULL, 0.3,  NULL, NULL, NULL,   'Flag leaf', 'Anthesis', '5.3.4', 'FERTASA 5.3.4.'),

-- Soya beans
('Soybean', 'P',  '%',     NULL, NULL, 0.35, NULL, NULL, NULL, 'Uppermost mature trifoliate', 'Early pod fill (R3-R4)', '5.3.4', 'FERTASA 5.3.4.'),
('Soybean', 'K',  '%',     NULL, NULL, 2.20, NULL, NULL, NULL, 'Uppermost trifoliate', 'R3-R4', '5.3.4', 'FERTASA 5.3.4.'),
('Soybean', 'Ca', '%',     NULL, NULL, 0.40, NULL, NULL, NULL, 'Uppermost trifoliate', 'R3-R4', '5.3.4', 'FERTASA 5.3.4.'),
('Soybean', 'Mg', '%',     NULL, NULL, 0.30, NULL, NULL, NULL, 'Uppermost trifoliate', 'R3-R4', '5.3.4', 'FERTASA 5.3.4.'),
('Soybean', 'Mn', 'mg/kg', NULL, NULL, 20,   NULL, NULL, NULL, 'Uppermost trifoliate', 'R3-R4', '5.3.4', 'FERTASA 5.3.4.'),
('Soybean', 'B',  'mg/kg', NULL, NULL, 25,   NULL, NULL, NULL, 'Uppermost trifoliate', 'R3-R4', '5.3.4', 'FERTASA 5.3.4.'),
('Soybean', 'Zn', 'mg/kg', NULL, NULL, 15,   NULL, NULL, NULL, 'Uppermost trifoliate', 'R3-R4', '5.3.4', 'FERTASA 5.3.4.'),
('Soybean', 'Mo', 'mg/kg', NULL, NULL, 0.5,  NULL, NULL, NULL, 'Uppermost trifoliate', 'R3-R4', '5.3.4', 'FERTASA 5.3.4. Mo seed treatment standard.'),

-- Lucerne (from 5.3.4 — simplified single-value norms; Table 5.12.2.6 has stage-split)
('Lucerne', 'P',  '%',     NULL, NULL, 0.35, NULL, NULL, NULL, 'Top 150-200mm stem + leaves', 'Early flowering', '5.3.4', 'FERTASA 5.3.4 simplified. For stage-specific see Table 5.12.2.6.'),
('Lucerne', 'K',  '%',     NULL, NULL, 2.20, NULL, NULL, NULL, 'Top 150-200mm', 'Early flowering', '5.3.4', 'FERTASA 5.3.4.'),
('Lucerne', 'Ca', '%',     NULL, NULL, 0.80, NULL, NULL, NULL, 'Top 150-200mm', 'Early flowering', '5.3.4', 'FERTASA 5.3.4.'),
('Lucerne', 'Mg', '%',     NULL, NULL, 0.40, NULL, NULL, NULL, 'Top 150-200mm', 'Early flowering', '5.3.4', 'FERTASA 5.3.4.'),
('Lucerne', 'Mn', 'mg/kg', NULL, NULL, 25,   NULL, NULL, NULL, 'Top 150-200mm', 'Early flowering', '5.3.4', 'FERTASA 5.3.4.'),
('Lucerne', 'B',  'mg/kg', NULL, NULL, 30,   NULL, NULL, NULL, 'Top 150-200mm', 'Early flowering', '5.3.4', 'FERTASA 5.3.4.'),
('Lucerne', 'Cu', 'mg/kg', NULL, NULL, 7,    NULL, NULL, NULL, 'Top 150-200mm', 'Early flowering', '5.3.4', 'FERTASA 5.3.4.'),
('Lucerne', 'Zn', 'mg/kg', NULL, NULL, 15,   NULL, NULL, NULL, 'Top 150-200mm', 'Early flowering', '5.3.4', 'FERTASA 5.3.4.'),
('Lucerne', 'Mo', 'mg/kg', NULL, NULL, 0.5,  NULL, NULL, NULL, 'Top 150-200mm', 'Early flowering', '5.3.4', 'FERTASA 5.3.4.');


-- ─── Avocado cultivar-split leaf + soil norms (image 517, FERTASA 5.7.1.1) ─
-- Fuerte / Hass / Pinkerton / Ryan / Edranol have distinct N norms.
-- Per-cultivar rows for N; shared rows for P/K/Ca/Mg/S + micros.

INSERT INTO fertasa_leaf_norms (crop, element, unit, deficient_max, low_max,
    sufficient_min, sufficient_max, high_min, excess_min,
    sample_part, sample_timing, source_section, notes) VALUES

('Avocado', 'N',        '%',     NULL, 1.7, 1.7, 1.9, NULL, NULL,  'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1: FUERTE cv 1.7-1.9%.'),
('Avocado', 'N (Hass)', '%',     NULL, 2.2, 2.2, 2.3, NULL, NULL,  'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1: HASS cv 2.2-2.3%. Cultivar-specific — Hass highest.'),
('Avocado', 'N (Pinkerton)', '%', NULL, NULL, 2.0, 2.0, NULL, NULL, 'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1: Pinkerton 2.00%.'),
('Avocado', 'N (Ryan)',  '%',    NULL, NULL, 2.1, 2.1, NULL, NULL, 'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1: Ryan 2.10%.'),
('Avocado', 'N (Edranol)', '%',  NULL, NULL, 2.0, 2.0, NULL, NULL, 'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1: Edranol 2.00%.'),
('Avocado', 'P',  '%',     NULL, NULL, 0.08, 0.15, NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.'),
('Avocado', 'K',  '%',     NULL, NULL, 0.75, 1.15, NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.'),
('Avocado', 'Ca', '%',     NULL, NULL, 1.0,  2.0,  NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.'),
('Avocado', 'Mg', '%',     NULL, NULL, 0.4,  0.8,  NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.'),
('Avocado', 'S',  '%',     NULL, NULL, 0.2,  0.6,  NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.'),
('Avocado', 'Zn', 'mg/kg', NULL, NULL, 25,   100,  NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.'),
('Avocado', 'Cu', 'mg/kg', NULL, NULL, 5,    15,   NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.'),
('Avocado', 'Mn', 'mg/kg', NULL, NULL, 50,   250,  NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.'),
('Avocado', 'Fe', 'mg/kg', NULL, NULL, 50,   150,  NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.'),
('Avocado', 'B',  'mg/kg', NULL, NULL, 40,   80,   NULL, NULL,     'Recent fully-expanded leaf', 'Feb-Apr', '5.7.1', 'FERTASA 5.7.1.1.');


-- ─── Sugar cane leaf norms (image 466, FERTASA Table 5.3.1) ──────────
-- Single critical values for each element; N varies by area × month
-- (not easily represented in the current schema — use Northern irrigation
-- Oct-Dec as canonical plant-crop value, note the full matrix in notes).

INSERT INTO fertasa_leaf_norms (crop, element, unit, deficient_max, low_max,
    sufficient_min, sufficient_max, high_min, excess_min,
    sample_part, sample_timing, source_section, notes) VALUES

('Sugarcane', 'N',  '%',     NULL, NULL, 1.7, 1.9, NULL, NULL,  '3rd fully-expanded leaf', 'Oct-Apr per area/month',
    '5.3.1', 'FERTASA 5.3.1 Table 5.3.1: 1.9% Oct-Dec → 1.7% Mar-Apr for plant crop (N Irrigation / Coastal / Midlands). Ratoon 0.1% lower.'),
('Sugarcane', 'P',  '%',     NULL, NULL, 0.19, NULL, NULL, NULL, '3rd fully-expanded leaf', 'Active growth',
    '5.3.1', 'FERTASA 5.3.1: P+ critical 0.19%. Only-N12 plantings 0.16%.'),
('Sugarcane', 'K',  '%',     NULL, NULL, 1.05, NULL, NULL, NULL, '3rd fully-expanded leaf', 'Active growth',
    '5.3.1', 'FERTASA 5.3.1: K++ critical 1.05%. Only-N14 plantings 0.90%.'),
('Sugarcane', 'Ca', '%',     NULL, NULL, 0.15, NULL, NULL, NULL, '3rd fully-expanded leaf', 'Active growth',
    '5.3.1', 'FERTASA 5.3.1.'),
('Sugarcane', 'Mg', '%',     NULL, NULL, 0.08, NULL, NULL, NULL, '3rd fully-expanded leaf', 'Active growth',
    '5.3.1', 'FERTASA 5.3.1.'),
('Sugarcane', 'S',  '%',     NULL, NULL, 0.12, NULL, NULL, NULL, '3rd fully-expanded leaf', 'Active growth',
    '5.3.1', 'FERTASA 5.3.1.'),
('Sugarcane', 'Si', '%',     NULL, NULL, 0.50, NULL, NULL, NULL, '3rd fully-expanded leaf', 'Active growth',
    '5.3.1', 'FERTASA 5.3.1: Si norm — unique to sugar cane.'),
('Sugarcane', 'Zn', 'mg/kg', NULL, NULL, 13,   NULL, NULL, NULL, '3rd fully-expanded leaf', 'Active growth',
    '5.3.1', 'FERTASA 5.3.1.'),
('Sugarcane', 'Cu', 'mg/kg', NULL, NULL, 3,    NULL, NULL, NULL, '3rd fully-expanded leaf', 'Active growth',
    '5.3.1', 'FERTASA 5.3.1.'),
('Sugarcane', 'Mn', 'mg/kg', NULL, NULL, 15,   NULL, NULL, NULL, '3rd fully-expanded leaf', 'Active growth',
    '5.3.1', 'FERTASA 5.3.1.');


-- ─── Macadamia + Canola completeness additions ───────────────────────
-- Audit found Na missing on both; Cl missing on macadamia.

INSERT INTO fertasa_leaf_norms (crop, element, unit, deficient_max, low_max,
    sufficient_min, sufficient_max, high_min, excess_min,
    sample_part, sample_timing, source_section, notes) VALUES

('Macadamia', 'Na', '%', NULL, NULL, NULL, 0.02, 0.02, NULL,
    '3rd-4th pair from growth tip on primary branch', 'Oct-Nov',
    '5.8.1', 'FERTASA 5.8.1.1 Table (SAMAC): Na <0.02% upper tolerance.'),
('Macadamia', 'Cl', '%', NULL, NULL, 0.03, 0.05, NULL, NULL,
    '3rd-4th pair from growth tip on primary branch', 'Oct-Nov',
    '5.8.1', 'FERTASA 5.8.1.1: Cl 0.03-0.05%.'),
('Canola', 'Na', '%', NULL, NULL, 0.03, 0.5, NULL, NULL,
    'Rosette stage leaf', '30-40 days after emergence',
    '5.5.1', 'FERTASA 5.5.1.7: Na 0.03-0.5%.');


COMMIT;
