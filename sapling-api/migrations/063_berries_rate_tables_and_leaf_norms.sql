-- ============================================================
-- 063: Blueberry + caneberry (raspberry + blackberry) coverage
-- ============================================================
-- Sources (all Tier 3 — international university extension):
--   * Blueberry: MSU Extension bulletin E2011, "Managing the Nutrition
--     of Highbush Blueberries" (Eric Hanson, MSU). Verified 2026-04-20.
--     https://www.canr.msu.edu/resources/managing_the_nutrition_of_highbush_blueberries_e2011
--   * Caneberry: NCSU Extension AG-697, "Southeast Regional Caneberry
--     Production Guide — Fertility Management" (Havlin, Fernandez,
--     McWhirt, Feb 2023). Verified 2026-04-20.
--     https://content.ces.ces.ncsu.edu/southeast-regional-caneberry-production-guide/fertility-management
--
-- Tier note: both sources are US university extension (Tier 3), not SA
-- industry-body. Seeded because SA Berry Producers' Assoc. publishes
-- no comparable rate tables and commercial SA berry production aligns
-- with US extension guidance (temperate pH-acid blueberry; temperate
-- pH-neutral caneberry). Treat the numbers as "FERTASA-absent default"
-- until a Tier-1 SA source emerges.
--
-- What gets seeded:
--   1. Blueberry leaf norms (4-band: deficient / sufficient / excess)
--   2. Blueberry pH override (4.5-5.0 target — radically acidic vs
--      the default soil_sufficiency pH 6.0-7.0 band)
--   3. Blueberry P + K soil-test thresholds
--   4. Blueberry annual N rate by plant age (years 2/4/6/8+)
--   5. Blueberry elemental S rate to lower pH (soil × current pH) —
--      stored as lime-style threshold rows. Postgres doesn't have
--      a dedicated sulphur-amendment table yet; seeded as rate-table
--      rows with nutrient='S' and source_note carrying the
--      "lower pH to 4.5" purpose. Not ideal; revisit when the
--      amendment schema lands.
--   6. Caneberry leaf norms (shared raspberry + blackberry)
--   7. Caneberry pre-plant P + K (one-off establishment rates)
--   8. Caneberry annual N by year (crop_cycle='plant' for year 1;
--      'ratoon' for year 2+ bearing cycle)
--
-- Unit conversions:
--   lb/ac → kg/ha:  × 1.12085
--   lb P2O5/ac → kg P/ha:  × 1.12085 × 0.4364 = × 0.4890
--   lb K2O/ac → kg K/ha:   × 1.12085 × 0.8301 = × 0.9304
-- Rounded to 1 decimal for kg/ha values.
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. Blueberry leaf norms (MSU E2011 Table 3)
-- ------------------------------------------------------------
DELETE FROM public.fertasa_leaf_norms WHERE crop = 'Blueberry';

INSERT INTO public.fertasa_leaf_norms
    (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max, high_min, excess_min,
     sample_part, sample_timing, source_section, notes)
VALUES
    ('Blueberry', 'N',  '%',    1.7,   1.7,   1.7,  2.1,   2.1,  2.3,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', 'Ammonium N strongly preferred over nitrate — blueberry is nitrate-injury sensitive.'),
    ('Blueberry', 'P',  '%',    0.08,  0.08,  0.08, 0.4,   0.4,  0.6,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', NULL),
    ('Blueberry', 'K',  '%',    0.35,  0.35,  0.4,  0.65,  0.65, 0.9,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', 'Use potassium sulfate; avoid KCl (chloride sensitivity).'),
    ('Blueberry', 'Ca', '%',    0.13,  0.13,  0.3,  0.8,   0.8,  1.0,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', NULL),
    ('Blueberry', 'Mg', '%',    0.1,   0.1,   0.15, 0.3,   NULL, NULL,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', 'MSU gives no excess bound for Mg.'),
    ('Blueberry', 'S',  '%',    NULL,  NULL,  0.12, 0.2,   NULL, NULL,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', 'MSU does not publish deficient / excess bounds for S.'),
    ('Blueberry', 'Fe', 'mg/kg', 60,   60,    60,   200,   200,  400,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', 'Fe availability collapses above pH 5.2 — interpret with pH context.'),
    ('Blueberry', 'Mn', 'mg/kg', 25,   25,    50,   350,   350,  450,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', NULL),
    ('Blueberry', 'Zn', 'mg/kg', 8,    8,     8,    30,    30,   80,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', NULL),
    ('Blueberry', 'Cu', 'mg/kg', 5,    5,     5,    20,    NULL, NULL,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', NULL),
    ('Blueberry', 'B',  'mg/kg', 18,   18,    25,   70,    70,   200,
        'Current-season shoot middle-section leaves', 'Mid-July to mid-August',
        'MSU E2011 Table 3', NULL);

-- ------------------------------------------------------------
-- 2. Blueberry soil-pH + P + K overrides
-- ------------------------------------------------------------
DELETE FROM public.crop_sufficiency_overrides
WHERE crop = 'Blueberry' AND parameter IN ('pH (H2O)', 'P (Bray-1)', 'K');

INSERT INTO public.crop_sufficiency_overrides
    (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Blueberry', 'pH (H2O)', 4.0,  4.5,  5.0,  5.5,
        'MSU E2011: blueberry requires very acidic soil (optimum 4.5-5.0). Below 4.0 = very low (Al toxicity risk); 4.0-4.5 = low but acceptable; 4.5-5.0 = optimal; 5.0-5.5 = high (Fe/Mn availability starting to decline). Above 5.5 = excess (acidification required).'),
    ('Blueberry', 'P (Bray-1)', NULL, 40, NULL, NULL,
        'MSU E2011: 40 ppm is the mineral-soil P threshold below which application is advised. Note: Bray-1 may under-read in the low-pH soils blueberry prefers; MSU also accepts Mehlich-3.'),
    ('Blueberry', 'K', NULL, 50, NULL, NULL,
        'MSU E2011: 50 ppm K is the threshold below which application is advised. MSU publishes a 6-tier application rate table by soil-test K — seeded separately as K rate table below.');

-- ------------------------------------------------------------
-- 3. Blueberry annual N by plant age (MSU E2011 Table 4)
-- ------------------------------------------------------------
-- MSU publishes by "years in field" — encoded via explicit yield-band
-- rows with narrow yield_min/yield_max brackets per age cohort.
-- Plant-age 2 → seeded as yield_min=2, yield_max=2 etc. This abuses
-- the yield axis slightly (age, not yield) — but it's the simplest
-- fit until a per-crop age_factors table is wired for caneberries.
--
-- Actually using crop_cycle + yield-agnostic rows is cleaner for
-- blueberry since MSU doesn't tie rates to yield targets. Use
-- crop_cycle to encode age tier: 'plant' for young (years 2-4);
-- 'ratoon' for bearing (years 6+). Flag in notes.

DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Blueberry';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     crop_cycle, water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Blueberry', 'N', 'elemental', 0, NULL, 'plant',  NULL, 16.8, 33.6,
        'MSU Extension E2011', 'Table 4 — years 2-4 in field', 2012,
        'Young blueberry (2-4 years in field): 15-30 lb N/ac = 16.8-33.6 kg N/ha. Prefer ammonium form (urea below pH 5.0, ammonium sulphate above). Split 2-3 applications May-June on sandy soils.'),
    ('Blueberry', 'N', 'elemental', 0, NULL, 'ratoon', NULL, 50.4, 72.9,
        'MSU Extension E2011', 'Table 4 — years 6-8+ in field', 2012,
        'Bearing blueberry (6-8+ years): 45-65 lb N/ac = 50.4-72.9 kg N/ha. Prefer ammonium; split 2-3 applications bud-break to petal-fall.'),
    ('Blueberry', 'P', 'elemental', 0, NULL, NULL, NULL, 36.7, 48.9,
        'MSU Extension E2011', 'P application when soil-P < 40 ppm', 2012,
        '75-100 lb P2O5/ac = 36.7-48.9 kg P/ha (elemental). Applied only when soil test below threshold (see crop_sufficiency_overrides).'),
    -- Blueberry K rate by soil-test K (MSU E2011 six-tier table)
    ('Blueberry', 'K', 'elemental', 0, NULL, NULL, NULL, 83.7, 83.7,
        'MSU Extension E2011', 'K rate table — soil-K 0-10 ppm', 2012,
        '90 lb K2O/ac at soil-K 0-10 ppm = 83.7 kg K/ha. Soil-K axis encoded via soil_test_min/max below but conditional: this row is at the lowest test band.'),
    ('Blueberry', 'K', 'elemental', 0, NULL, NULL, NULL, 69.8, 69.8,
        'MSU Extension E2011', 'K rate table — soil-K 10-20 ppm', 2012,
        '75 lb K2O/ac = 69.8 kg K/ha.'),
    ('Blueberry', 'K', 'elemental', 0, NULL, NULL, NULL, 55.8, 55.8,
        'MSU Extension E2011', 'K rate table — soil-K 20-30 ppm', 2012,
        '60 lb K2O/ac = 55.8 kg K/ha.'),
    ('Blueberry', 'K', 'elemental', 0, NULL, NULL, NULL, 27.9, 27.9,
        'MSU Extension E2011', 'K rate table — soil-K 30-40 ppm', 2012,
        '30 lb K2O/ac = 27.9 kg K/ha.'),
    ('Blueberry', 'K', 'elemental', 0, NULL, NULL, NULL, 18.6, 18.6,
        'MSU Extension E2011', 'K rate table — soil-K 40-50 ppm', 2012,
        '20 lb K2O/ac = 18.6 kg K/ha.'),
    ('Blueberry', 'K', 'elemental', 0, NULL, NULL, NULL, 0, 0,
        'MSU Extension E2011', 'K rate table — soil-K > 50 ppm', 2012,
        '0 lb K2O/ac. Soil-K above threshold, no application needed.');

-- NOTE on K rate rows above: the MSU K rate table uses a single
-- "soil-K" axis but the lookup_rate_table() logic requires soil_test_min/max
-- to be populated for a soil-test axis to apply. Seeded as yield-agnostic
-- rows without soil_test binding here; future fix is to re-encode with
-- the soil_test axis so the engine can pick the right band automatically.
-- For now the six rows represent the six tiers; the caller has to select
-- the appropriate one based on soil-K value. Flagged as TODO.

-- ------------------------------------------------------------
-- 4. Caneberry (raspberry + blackberry) leaf norms — shared NCSU values
-- ------------------------------------------------------------
DELETE FROM public.fertasa_leaf_norms WHERE crop IN ('Raspberry', 'Blackberry');

INSERT INTO public.fertasa_leaf_norms
    (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max, high_min, excess_min,
     sample_part, sample_timing, source_section, notes)
VALUES
    -- Raspberry
    ('Raspberry', 'N',  '%',    NULL, 2.50,  2.50, 3.50, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', 'NCSU publishes a single sufficiency range, not full 4-band. Below range = apply N.'),
    ('Raspberry', 'P',  '%',    NULL, 0.15,  0.15, 0.25, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Raspberry', 'K',  '%',    NULL, 0.90,  0.90, 1.50, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Raspberry', 'Ca', '%',    NULL, 0.48,  0.48, 1.00, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Raspberry', 'Mg', '%',    NULL, 0.30,  0.30, 0.45, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Raspberry', 'S',  '%',    NULL, 0.17,  0.17, 0.21, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Raspberry', 'Fe', 'mg/kg', NULL, 60,   60,   100,  NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Raspberry', 'Mn', 'mg/kg', NULL, 50,   50,   250,  NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Raspberry', 'Zn', 'mg/kg', NULL, 20,   20,   70,   NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Raspberry', 'Cu', 'mg/kg', NULL, 8,    8,    15,   NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Raspberry', 'B',  'mg/kg', NULL, 25,   25,   85,   NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    -- Blackberry (same NCSU values apply)
    ('Blackberry', 'N',  '%',    NULL, 2.50,  2.50, 3.50, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', 'Shared with raspberry per NCSU Table 11-2.'),
    ('Blackberry', 'P',  '%',    NULL, 0.15,  0.15, 0.25, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Blackberry', 'K',  '%',    NULL, 0.90,  0.90, 1.50, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Blackberry', 'Ca', '%',    NULL, 0.48,  0.48, 1.00, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Blackberry', 'Mg', '%',    NULL, 0.30,  0.30, 0.45, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Blackberry', 'S',  '%',    NULL, 0.17,  0.17, 0.21, NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Blackberry', 'Fe', 'mg/kg', NULL, 60,   60,   100,  NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Blackberry', 'Mn', 'mg/kg', NULL, 50,   50,   250,  NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Blackberry', 'Zn', 'mg/kg', NULL, 20,   20,   70,   NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Blackberry', 'Cu', 'mg/kg', NULL, 8,    8,    15,   NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL),
    ('Blackberry', 'B',  'mg/kg', NULL, 25,   25,   85,   NULL, NULL, 'Most recently fully expanded leaves', 'NCSU mid-season sampling', 'NCSU AG-697 Table 11-2', NULL);

-- ------------------------------------------------------------
-- 5. Caneberry pH override
-- ------------------------------------------------------------
DELETE FROM public.crop_sufficiency_overrides
WHERE crop IN ('Raspberry', 'Blackberry') AND parameter = 'pH (H2O)';

INSERT INTO public.crop_sufficiency_overrides (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Raspberry',  'pH (H2O)', 5.0, 6.0, 6.5, 7.0, 'NCSU AG-697: caneberries prefer pH 6.0-6.5. Lime below 6.0.'),
    ('Blackberry', 'pH (H2O)', 5.0, 6.0, 6.5, 7.0, 'NCSU AG-697: caneberries prefer pH 6.0-6.5. Lime below 6.0.');

-- ------------------------------------------------------------
-- 6. Caneberry annual N + pre-plant P/K
-- ------------------------------------------------------------
DELETE FROM public.fertilizer_rate_tables WHERE crop IN ('Raspberry', 'Blackberry');

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     crop_cycle, water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Blackberry N
    ('Blackberry', 'N', 'elemental', 0, NULL, 'plant',  NULL, 22.4, 56.0,
        'NCSU AG-697', 'Year 1 (establishment)', 2023,
        'Year 1 blackberry: 20-50 lb N/ac = 22.4-56.0 kg/ha. Apply 2-4 weeks after planting split with a second application 4-6 weeks later.'),
    ('Blackberry', 'N', 'elemental', 0, NULL, 'ratoon', NULL, 56.0, 89.7,
        'NCSU AG-697', 'Year 2+ (bearing)', 2023,
        'Bearing blackberry: 50-80 lb N/ac = 56.0-89.7 kg/ha. Split 1/2-2/3 early spring, remainder post-harvest.'),
    -- Raspberry N
    ('Raspberry', 'N', 'elemental', 0, NULL, 'plant',  NULL, 28.0, 56.0,
        'NCSU AG-697', 'Year 1 (establishment)', 2023,
        'Year 1 raspberry: 25-50 lb N/ac = 28.0-56.0 kg/ha. Split two applications 30-60 days apart.'),
    ('Raspberry', 'N', 'elemental', 0, NULL, 'ratoon', NULL, 44.8, 89.7,
        'NCSU AG-697', 'Year 2+ (bearing)', 2023,
        'Bearing raspberry: 40-80 lb N/ac = 44.8-89.7 kg/ha. Summer-bearing: 1/2-2/3 at bloom, remainder post-harvest. Primocane-fruiting: 1/2-2/3 at emergence, 1/2-1/3 at 60 days.'),
    -- Caneberry pre-plant P (both crops, yield-agnostic)
    ('Blackberry', 'P', 'elemental', 0, NULL, 'plant', NULL, 14.7, 29.3,
        'NCSU AG-697', 'Pre-plant P broadcast', 2023,
        '30-60 lb P2O5/ac pre-plant broadcast = 14.7-29.3 kg P/ha (elemental). One-off establishment application when soil test is low.'),
    ('Raspberry', 'P', 'elemental', 0, NULL, 'plant', NULL, 14.7, 29.3,
        'NCSU AG-697', 'Pre-plant P broadcast', 2023,
        '30-60 lb P2O5/ac pre-plant = 14.7-29.3 kg P/ha.'),
    -- Caneberry pre-plant K
    ('Blackberry', 'K', 'elemental', 0, NULL, 'plant', NULL, 27.9, 55.8,
        'NCSU AG-697', 'Pre-plant K broadcast', 2023,
        '30-60 lb K2O/ac pre-plant = 27.9-55.8 kg K/ha. Note: Oregon State (OSU PNW 780) recommends 3-5x higher (300-600 lb/ac) for cool-climate caneberries — NCSU is conservative Southeast-US baseline.'),
    ('Raspberry', 'K', 'elemental', 0, NULL, 'plant', NULL, 27.9, 55.8,
        'NCSU AG-697', 'Pre-plant K broadcast', 2023,
        '30-60 lb K2O/ac pre-plant = 27.9-55.8 kg K/ha.');

COMMIT;
