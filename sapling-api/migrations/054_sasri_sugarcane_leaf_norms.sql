-- ============================================================
-- 054: SASRI sugarcane leaf norms (IS 7.15)
-- ============================================================
-- Source: SASRI Information Sheet 7.15 "Sugarcane leaf sampling"
--         (updated October 2025).
--         https://sasri.org.za/download/162/7-soils-nutrition/28625/
--         7-15-sugarcane-leaf-sampling.pdf
--
-- Replaces the skeletal sugarcane rows seeded from FERTASA 5.3.1 (which
-- only populated `sufficient_min`) with SASRI's complete 4-band set
-- (Low / Sufficient / High / Excess) for 12 elements.
--
-- Mapping SASRI bands to schema columns:
--   SASRI "Low"       → low_max        = upper bound (inclusive, per
--                                         existing engine convention)
--   SASRI "Sufficient"→ sufficient_min + sufficient_max
--   SASRI "High"      → high_min
--   SASRI "Excess"    → excess_min
--   `deficient_max` left NULL — SASRI collapses Deficient into Low.
--
-- Quirks faithfully preserved:
--   * P has a cultivar-specific exception for N12 (Low <0.14 vs <0.19
--     for other varieties). N12 is not a common SA variety; the general
--     threshold is seeded here with a note.
--   * N thresholds vary by region × crop age × sampling month × crop
--     cycle (plant/ratoon). A single general 1.7-1.9% sufficient range
--     is seeded here as an interim; the detailed table (Northern
--     Irrigated / Coastal Lowlands / Midlands × age × month × cycle)
--     needs a richer schema (to be tackled in a follow-up migration).
--   * Sample part: 3rd fully-expanded leaf (same as FERTASA convention).
-- ============================================================

BEGIN;

-- Remove the FERTASA 5.3.1 sugarcane skeleton so we can replace it with
-- the SASRI-complete set. Old rows had only sufficient_min populated.
DELETE FROM public.fertasa_leaf_norms WHERE crop = 'Sugarcane';

INSERT INTO public.fertasa_leaf_norms
    (crop, element, unit,
     deficient_max, low_max,
     sufficient_min, sufficient_max,
     high_min, excess_min,
     sample_part, sample_timing, source_section, notes)
VALUES
    -- Macro + secondary nutrients (%)
    ('Sugarcane', 'N',  '%',    NULL, NULL,   1.7,  1.9, NULL, NULL,
        '3rd fully-expanded leaf', 'Season/area-specific — see IS 7.15 table on page 3',
        'SASRI IS 7.15',
        'Interim general sufficient range. Actual SASRI thresholds vary by region (Northern Irrigated / Coastal Lowlands / Midlands), crop age (3-5 / 4-7 / 4-9 months), sampling month, and crop cycle (plant vs ratoon). Plant-cycle thresholds run 1.7-1.9% depending on month; ratoon 1.6-1.8%. Richer schema needed to encode this fully.'),
    ('Sugarcane', 'P',  '%',    NULL, 0.19,   0.19, 0.24, 0.25, 0.40,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        'Thresholds for all varieties except N12. N12 variety has lower Low/Sufficient threshold (<0.14 Low, 0.14-0.24 Sufficient) per IS 7.15.'),
    ('Sugarcane', 'K',  '%',    NULL, 1.05,   1.05, 1.59, 1.60, 1.79,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        NULL),
    ('Sugarcane', 'Ca', '%',    NULL, 0.15,   0.15, 0.38, 0.39, 0.59,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        NULL),
    ('Sugarcane', 'Mg', '%',    NULL, 0.08,   0.08, 0.18, 0.19, 0.34,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        NULL),
    ('Sugarcane', 'S',  '%',    NULL, 0.12,   0.12, 0.23, 0.24, 0.39,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        NULL),
    ('Sugarcane', 'Si', '%',    NULL, 0.75,   0.75, 1.99, 2.00, 4.99,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        'Silicon is critical for sugarcane (disease resistance, stalk strength). SASRI treats Si as a near-essential element.'),

    -- Micronutrients (mg/kg = ppm)
    ('Sugarcane', 'Zn', 'mg/kg', NULL, 13,     13,   24,   25,   75,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        NULL),
    ('Sugarcane', 'Mn', 'mg/kg', NULL, 15,     15,   99,   100,  250,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        NULL),
    ('Sugarcane', 'Cu', 'mg/kg', NULL, 3,      3,    7,    8,    12,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        NULL),
    ('Sugarcane', 'Fe', 'mg/kg', NULL, 75,     75,   99,   100,  300,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        NULL),
    ('Sugarcane', 'B',  'mg/kg', NULL, 10,     10,   20,   21,   35,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        NULL),
    ('Sugarcane', 'Mo', 'mg/kg', NULL, 0.08,   0.08, 1.0,  NULL, 1.0,
        '3rd fully-expanded leaf', NULL, 'SASRI IS 7.15',
        'SASRI publishes only 3 bands for Mo: Low <0.08, Sufficient 0.08-1, Excess >1. No High band defined — excess_min = sufficient_max.');

COMMIT;
