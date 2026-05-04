-- ============================================================
-- 109: Citrus genus data fill — soil bands + genus-level leaf
--      norms + age factors + low-CEC awareness note
-- ============================================================
-- Sources:
--   * UF/IFAS Citrus Production Guide CG091, SS584 (Ca/S), SS492 (Cu),
--     SS582 (Mg) — T2.
--   * CDFA-FREP Geisseler Citrus Fertilization Guidelines — T2.
--   * Citrus Academy NQ2 §3.1 (existing pH H2O row from migration 080).
--   * FERTASA 2016 cited via SciELO Limpopo baseline study — T1 cross-check.
--   * Haifa Crop Guide Citrus — T2.
--
-- Honest provenance: the pH (KCl) row is DERIVED from the Citrus Academy
-- pH (H2O) band minus the FERTASA-published 0.5 H2O→KCl offset. No
-- citrus-specific pH (KCl) source exists openly; the Raath 2021 R250
-- handbook is the gap. Flagged as derived in the row's notes.
--
-- Genus vs cultivar split: 5 cultivars (Valencia, Navel, Lemon,
-- Grapefruit, Soft Citrus) had leaf norms + age factors but the parent
-- "Citrus" row was empty — meaning Quick Analysis runs against the
-- bare crop dropped through to no leaf interpretation. Cloning
-- Valencia up to genus per migration 080's cultivar-clone convention.
--
-- crop_calc_flags low-CEC concern: the FERTASA cation-ratio path
-- becomes statistically unstable on lowveld sandy soils with CEC <4
-- cmol/kg. Schema doesn't currently support a "skip_if_cec_below"
-- threshold — only a blanket skip flag. Skipping the flag rather than
-- over-firing on every citrus block. TODO: extend crop_calc_flags
-- with a cec_floor column when the engine is ready.
--
-- Genuine gaps after this migration (see CROP_DATA_COVERAGE.md):
--   * pH (KCl) directly cited (currently derived) — pending Raath 2021
--   * CRI FertMap rate tables (members-only)
--   * Org C / CEC overrides — fall through to universal soil_sufficiency
-- ============================================================

BEGIN;

INSERT INTO public.crop_sufficiency_overrides
    (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Citrus', 'pH (KCl)', 4.5, 5.0, 6.5, 7.0,
     'DERIVED from Citrus Academy NQ2 pH(H2O) band − 0.5 KCl/H2O offset (FERTASA 2016). T1 (derived).'),
    ('Citrus', 'P (Olsen)', 5, 10, 40, 60,
     'CDFA-FREP Geisseler Citrus Fertilization Guidelines. T2.'),
    ('Citrus', 'Ca', 200, 400, 1500, 3000,
     'UF/IFAS SS584 + FERTASA 2016 cross-check. T2 + T1 cross-check.'),
    ('Citrus', 'S', 5, 10, 30, 60,
     'Derived from UF/IFAS SS584 leaf S 0.20-0.40% optimum. T2 (derived).'),
    ('Citrus', 'Cu', 1, 3, 25, 50,
     'UF/IFAS SS492 — Cu toxicity threshold 25 mg/kg. T2.'),
    ('Citrus', 'Zn', 1, 2, 10, 25,
     'UF/IFAS general citrus micronutrient guidance. T2.'),
    ('Citrus', 'Mn', 2, 5, 50, 150,
     'UF/IFAS general citrus micronutrient guidance. T2.'),
    ('Citrus', 'B', 0.3, 0.5, 2.0, 5.0,
     'UF/IFAS + Haifa Crop Guide Citrus. T2.'),
    ('Citrus', 'Fe', 2, 5, 50, 100,
     'UF/IFAS general citrus micronutrient guidance. T2.')
ON CONFLICT (crop, parameter) DO UPDATE
    SET very_low_max = EXCLUDED.very_low_max,
        low_max = EXCLUDED.low_max,
        optimal_max = EXCLUDED.optimal_max,
        high_max = EXCLUDED.high_max,
        notes = EXCLUDED.notes;

-- Genus-level leaf norms + age factors are cloned from Valencia at
-- application time via the supabase admin client (see commit body —
-- python clone preserves all numeric bands + appends a "Cloned from
-- Valencia" provenance note). Pure SQL clone left out because the
-- target columns include all of element/sample_part/sample_timing/
-- low_max/sufficient_min/sufficient_max/excess_min/notes — a verbose
-- INSERT ... SELECT would be longer than the python.

COMMIT;
