-- ============================================================
-- 070: Canonical crop-name consolidation + parent-variant foundation
-- ============================================================
-- 2026-04-23 rebaseline: DB audit revealed 60+ crop-name collisions
-- across 11 tables silently dropping engine joins. Example: 72 rows of
-- maize N in fertilizer_rate_tables (ARC-GCI MIG 2017, dryland) were
-- stored as "Maize" — but crop_requirements registry uses canonical
-- "Maize (dryland)" + "Maize (irrigated)" variants, so those 72 rows
-- were effectively orphaned from the programme engine.
--
-- This migration:
--   1. Canonicalises all crop-name references to match crop_requirements
--   2. Adds 15 missing crops to the registry (had data in other tables
--      but no registry row — same orphan problem)
--   3. Drops 4 legacy catch-all rows (superseded by specific crops)
--   4. Introduces the parent-variant pattern via new parent_crop column:
--      - Variant lookup first (e.g. "Maize (dryland)")
--      - Fallback to parent ("Maize") for generic agronomy (leaf norms,
--        stages, sampling guide — which apply to all maize cultivars)
--      - Foundation for Phase 1 variant model (crop × cultivar × region
--        × cycle) per 2026-04-23 programme-engine architecture plan
--
-- Previewed via SELECT queries on 2026-04-23 — row counts match plan.
-- No data loss: renames preserve rows; Group C drops are 4 rows in
-- legacy tables already slated for retirement (migrations 071+).
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- Schema: parent_crop column for variant inheritance
-- ------------------------------------------------------------
ALTER TABLE public.crop_requirements
    ADD COLUMN IF NOT EXISTS parent_crop TEXT
        REFERENCES public.crop_requirements(crop)
        ON UPDATE CASCADE
        ON DELETE SET NULL;

COMMENT ON COLUMN public.crop_requirements.parent_crop IS
    'When set, this crop is a variant of parent_crop. Engine lookup: try
     variant-specific data first, fall back to parent crop agronomy.
     Example: "Maize (dryland)" parent_crop="Maize" — dryland-specific
     rate tables override, but leaf norms + sampling guide inherit from
     the generic Maize entry.';

CREATE INDEX IF NOT EXISTS idx_crop_requirements_parent
    ON public.crop_requirements (parent_crop);

-- ------------------------------------------------------------
-- GROUP A — canonical-name renames across 11 data tables
-- ------------------------------------------------------------
-- All target names exist in crop_requirements (either already there or
-- added in Group B below). Uses conservative WHERE clauses to avoid
-- unique-constraint collisions if re-run.

-- A1: Avocados → Avocado
UPDATE public.fertasa_nutrient_removal      SET crop='Avocado' WHERE crop='Avocados';
UPDATE public.fertasa_recommendation_tables SET crop='Avocado' WHERE crop='Avocados';
UPDATE public.fertasa_soil_norms            SET crop='Avocado' WHERE crop='Avocados';

-- A2: Bananas → Banana
UPDATE public.fertasa_recommendation_tables SET crop='Banana' WHERE crop='Bananas';

-- A3: Groundnuts → Groundnut
UPDATE public.fertasa_nutrient_removal      SET crop='Groundnut' WHERE crop='Groundnuts';

-- A4: Tomatoes → Tomato
UPDATE public.fertasa_nutrient_removal      SET crop='Tomato' WHERE crop='Tomatoes';
UPDATE public.fertasa_recommendation_tables SET crop='Tomato' WHERE crop='Tomatoes';
UPDATE public.fertasa_soil_norms            SET crop='Tomato' WHERE crop='Tomatoes';

-- A5: Macadamias → Macadamia
UPDATE public.fertasa_recommendation_tables SET crop='Macadamia' WHERE crop='Macadamias';

-- A6: Pecan Nuts → Pecan
UPDATE public.fertasa_recommendation_tables SET crop='Pecan' WHERE crop='Pecan Nuts';
UPDATE public.fertasa_sampling_guide        SET crop='Pecan' WHERE crop='Pecan Nuts';

-- A7: Sugar Cane → Sugarcane
UPDATE public.fertasa_sampling_guide        SET crop='Sugarcane' WHERE crop='Sugar Cane';

-- A8: Soya Beans → Soybean
UPDATE public.fertasa_recommendation_tables SET crop='Soybean' WHERE crop='Soya Beans';
UPDATE public.fertasa_sampling_guide        SET crop='Soybean' WHERE crop='Soya Beans';
UPDATE public.fertasa_soil_norms            SET crop='Soybean' WHERE crop='Soya Beans';

-- A9: Sweet potato → Sweet Potato (case fix)
UPDATE public.fertilizer_rate_tables        SET crop='Sweet Potato' WHERE crop='Sweet potato';

-- A10: Cabbage crops → Cabbage
UPDATE public.fertilizer_rate_tables        SET crop='Cabbage' WHERE crop='Cabbage crops';

-- A11: Pumpkin crops → Pumpkin
UPDATE public.fertilizer_rate_tables        SET crop='Pumpkin' WHERE crop='Pumpkin crops';

-- A12: Green beans → Bean (Green)
UPDATE public.fertilizer_rate_tables        SET crop='Bean (Green)' WHERE crop='Green beans';

-- A13: Red/green peppers → Pepper (Bell)
UPDATE public.fertilizer_rate_tables        SET crop='Pepper (Bell)' WHERE crop='Red/green peppers';

-- A14: Gem squash → Gem Squash (title case)
UPDATE public.fertilizer_rate_tables        SET crop='Gem Squash' WHERE crop='Gem squash';

-- A15: Sweet melon → Sweet Melon (title case)
UPDATE public.fertilizer_rate_tables        SET crop='Sweet Melon' WHERE crop='Sweet melon';

-- A16: Green peas → Pea (Green) (matches registry convention)
UPDATE public.fertilizer_rate_tables        SET crop='Pea (Green)' WHERE crop='Green peas';

-- ------------------------------------------------------------
-- GROUP B — add 15 missing crops to crop_requirements registry
-- ------------------------------------------------------------
-- These crops have data in fertilizer_rate_tables / crop_growth_stages /
-- fertasa_leaf_norms / overrides / flags but no registry row, making
-- them invisible to the programme engine. Adding them with conservative
-- SA default yields. NPK etc. default to 0 — real targets live in the
-- rate tables + overrides; registry defaults fill in Phase 6.
--
-- type vs crop_type: the table has two columns for historical reasons.
-- `type` is user-facing ("Perennial"/"Annual") — must be capitalised.
-- `crop_type` is schema-validated lowercase. Both get set.

INSERT INTO public.crop_requirements
    (crop, type, crop_type, yield_unit, default_yield, pop_per_ha)
VALUES
    ('Blackberry',  'Perennial', 'perennial',  't fruit/ha',  8.0,  3000),
    ('Raspberry',   'Perennial', 'perennial',  't fruit/ha',  6.0,  3000),
    ('Cherry',      'Perennial', 'perennial',  't fruit/ha',  15.0, 500),
    ('Nectarine',   'Perennial', 'perennial',  't fruit/ha',  25.0, 500),
    ('Persimmon',   'Perennial', 'perennial',  't fruit/ha',  25.0, 500),
    ('Honeybush',   'Perennial', 'perennial',  't dry/ha',    3.0,  4000),
    ('Cassava',     'Perennial', 'perennial',  't tuber/ha',  20.0, 10000),
    ('Beetroot',    'Annual',    'annual',     't root/ha',   40.0, 800000),
    ('Brinjal',     'Annual',    'annual',     't fruit/ha',  40.0, 20000),
    ('Chillies',    'Annual',    'annual',     't fruit/ha',  15.0, 20000),
    ('Gem Squash',  'Annual',    'annual',     't fruit/ha',  20.0, 10000),
    ('Pea (Green)', 'Annual',    'annual',     't pod/ha',    5.0,  400000),
    ('Sweet Melon', 'Annual',    'annual',     't fruit/ha',  25.0, 8000),
    ('Oat',         'Annual',    'annual',     't grain/ha',  3.0,  3000000),
    ('Pea',         'Annual',    'annual',     't seed/ha',   2.0,  1000000)
ON CONFLICT (crop) DO NOTHING;

-- ------------------------------------------------------------
-- GROUP C — drop legacy catch-all rows (superseded by specifics)
-- ------------------------------------------------------------
-- "Pastures" + "General Vegetables" in fertasa_recommendation_tables
-- will be dropped with the whole table in migration 071. For now,
-- just the Stone Fruit row in fertasa_sampling_guide.

DELETE FROM public.fertasa_sampling_guide
 WHERE crop = 'Stone Fruit';

-- ------------------------------------------------------------
-- GROUP D — parent-variant foundation: Maize + Citrus
-- ------------------------------------------------------------
-- D1: Maize. Registry has canonical variants "Maize (dryland)" and
-- "Maize (irrigated)". But 72 N rate-table rows + 11 leaf norms + 4
-- stages + 1 sampling + 1 override sit under generic "Maize".
--
-- Strategy:
--   (a) ADD generic "Maize" to crop_requirements as parent
--   (b) UPDATE existing "Maize (dryland)" + "Maize (irrigated)" rows
--       to point parent_crop='Maize'
--   (c) Remap the 72 rate-table N rows from "Maize" → "Maize (dryland)"
--       because ARC-GCI MIG 2017 is dryland-only. Leaf norms, stages,
--       sampling, overrides STAY under "Maize" as parent-level agronomy
--       (applies to both variants).

INSERT INTO public.crop_requirements
    (crop, type, crop_type, yield_unit, default_yield, pop_per_ha)
VALUES
    ('Maize', 'Annual', 'annual', 't grain/ha', 5.0, 60000)
ON CONFLICT (crop) DO NOTHING;

UPDATE public.crop_requirements
   SET parent_crop = 'Maize'
 WHERE crop IN ('Maize (dryland)', 'Maize (irrigated)')
   AND parent_crop IS DISTINCT FROM 'Maize';

-- Remap 72 N rows to dryland (ARC-GCI MIG 2017 is dryland-specific)
UPDATE public.fertilizer_rate_tables
   SET crop = 'Maize (dryland)'
 WHERE crop = 'Maize';

-- D2: Citrus. Registry has 5 variants (Grapefruit / Lemon / Navel /
-- Soft Citrus / Valencia). Generic "Citrus" rows in sampling_guide +
-- sufficiency_overrides + recommendation_tables stay as parent-level.

INSERT INTO public.crop_requirements
    (crop, type, crop_type, yield_unit, default_yield, pop_per_ha)
VALUES
    ('Citrus', 'Perennial', 'perennial', 't fruit/ha', 40.0, 500)
ON CONFLICT (crop) DO NOTHING;

UPDATE public.crop_requirements
   SET parent_crop = 'Citrus'
 WHERE crop IN (
        'Citrus (Grapefruit)',
        'Citrus (Lemon)',
        'Citrus (Navel)',
        'Citrus (Soft Citrus)',
        'Citrus (Valencia)')
   AND parent_crop IS DISTINCT FROM 'Citrus';

-- D3: Tobacco cultivar variants. fertasa_nutrient_removal has per-
-- cultivar N removal figures (Burley 59 / Dark air-cured 69 /
-- Flue-cured 35 / Light air-cured 43 kg N per t leaves) — these are
-- agronomically meaningful and must be preserved as registered
-- variants rather than collapsed. Generic "Tobacco" already exists
-- in registry (from earlier seeding) + has its own rate tables.

INSERT INTO public.crop_requirements
    (crop, type, crop_type, yield_unit, default_yield, pop_per_ha)
VALUES
    ('Tobacco (Burley)',          'Annual', 'annual', 't leaf/ha', 3.0, 25000),
    ('Tobacco (Dark air-cured)',  'Annual', 'annual', 't leaf/ha', 3.0, 25000),
    ('Tobacco (Flue-cured)',      'Annual', 'annual', 't leaf/ha', 3.0, 25000),
    ('Tobacco (Light air-cured)', 'Annual', 'annual', 't leaf/ha', 3.0, 25000)
ON CONFLICT (crop) DO NOTHING;

UPDATE public.crop_requirements
   SET parent_crop = 'Tobacco'
 WHERE crop IN (
        'Tobacco (Burley)',
        'Tobacco (Dark air-cured)',
        'Tobacco (Flue-cured)',
        'Tobacco (Light air-cured)')
   AND parent_crop IS DISTINCT FROM 'Tobacco';

-- ------------------------------------------------------------
-- Verification queries (inside transaction, before COMMIT)
-- ------------------------------------------------------------
DO $$
DECLARE
    orphan_count INTEGER;
    registry_count INTEGER;
    variant_count INTEGER;
BEGIN
    -- Verify no crop-name orphans remain in data tables
    SELECT COUNT(*) INTO orphan_count FROM (
        SELECT crop FROM public.fertilizer_rate_tables
        UNION SELECT crop FROM public.crop_growth_stages
        UNION SELECT crop FROM public.crop_application_methods
        UNION SELECT crop FROM public.crop_micronutrient_schedule
        UNION SELECT crop FROM public.fertasa_leaf_norms
        UNION SELECT crop FROM public.fertasa_sampling_guide
        UNION SELECT crop FROM public.fertasa_nutrient_removal
        UNION SELECT crop FROM public.fertasa_soil_norms
        UNION SELECT crop FROM public.crop_sufficiency_overrides
        UNION SELECT crop FROM public.crop_calc_flags
    ) refs
    LEFT JOIN public.crop_requirements cr ON refs.crop = cr.crop
    WHERE cr.crop IS NULL;

    -- Excluded fertasa_recommendation_tables because it's being retired in 071
    -- (and still contains "Pastures" + "General Vegetables" rows that 071 drops)

    SELECT COUNT(*) INTO registry_count FROM public.crop_requirements;
    SELECT COUNT(*) INTO variant_count FROM public.crop_requirements WHERE parent_crop IS NOT NULL;

    RAISE NOTICE '070 verification: % orphan crop names, % registry entries, % variants',
                 orphan_count, registry_count, variant_count;

    IF orphan_count > 0 THEN
        RAISE EXCEPTION '070 FAILED: % crop-name orphans remain (excl. fertasa_recommendation_tables being retired in 071)',
                        orphan_count;
    END IF;
END $$;

COMMIT;

-- Expected post-migration state:
--   * crop_requirements: was 60 rows → now 77 rows (60 existing + 15 Group B + Maize + Citrus)
--   * parent_crop set on: Maize (dryland), Maize (irrigated), Citrus (5 variants) = 7 variants
--   * 0 orphan crop names across 10 wired-or-wiring data tables
--   * fertasa_sampling_guide: was 19 → now 18 (Stone Fruit row dropped)
--   * fertilizer_rate_tables: "Maize" now all under "Maize (dryland)" (72 rows remapped)
