-- ============================================================
-- Programme builder data integrity
-- ============================================================
-- Three fixes required before the programme builder can be
-- relied on as the foundation for the season tracker:
--
-- 1. crop_type misclassification in crop_requirements. Many
--    commercial annuals were flagged perennial, which is
--    agronomically wrong and sends the feeding engine looking
--    for age factors that shouldn't apply.
--
-- 2. Name divergence between crop_requirements (the canonical
--    list users pick from) and crop_growth_stages. Ten crops
--    in the canonical list have no direct match in stages —
--    the engine's base_crop fallback only catches some.
--    FERTASA-style naming (Peach/Nectarine, Lucerne/Alfalfa,
--    Table Grape, Maize (dryland), Citrus subtypes) is kept
--    as canonical; stages get aliased rows.
--
-- 3. Perennial_age_factors coverage. Widely-published SA young-
--    tree curves exist for pome, stone, citrus, grape, olive
--    and blueberry — add them so age scaling actually fires for
--    the common SA orchard/vineyard crops.
--
-- 4. programme_blocks.nutrient_targets cache is stale on
--    existing blocks. Backfill from linked soil_analyses.
--
-- All operations are idempotent.
-- ============================================================

BEGIN;

-- ── 1. Fix crop_type misclassification ─────────────────────
-- Commercial SA practice: these are cultivated on a single-season
-- cycle, not perennial plantings.
UPDATE crop_requirements
SET crop_type = 'annual'
WHERE crop IN (
    'Butternut',
    'Canola',
    'Dry Beans',
    'Garlic',
    'Green Beans',
    'Lentils',
    'Lettuce',
    'Maize (dryland)',
    'Maize (irrigated)',
    'Pepper (Bell)',
    'Potato',
    'Pumpkin',
    'Spinach',
    'Strawberry',          -- biologically perennial; commercial SA runs annual
    'Sweetcorn',
    'Watermelon'
);

-- Note: Asparagus, Lucerne/Alfalfa, Sugarcane, Pineapple and
-- Rooibos stay perennial (field cycles 3-20 years, need
-- establishment/maturity scaling).


-- ── 2. Alias crop_growth_stages to canonical names ─────────
-- Each block duplicates the source crop's stage rows under the
-- canonical name used by crop_requirements. Guarded by
-- NOT EXISTS so re-running is a no-op.

DO $alias$
DECLARE
    rec RECORD;
    aliases JSONB := '[
        {"target": "Citrus (Grapefruit)",   "source": "Citrus (Valencia)"},
        {"target": "Citrus (Lemon)",        "source": "Citrus (Valencia)"},
        {"target": "Citrus (Navel)",        "source": "Citrus (Valencia)"},
        {"target": "Citrus (Soft Citrus)",  "source": "Citrus (Valencia)"},
        {"target": "Maize (dryland)",       "source": "Maize"},
        {"target": "Maize (irrigated)",     "source": "Maize"},
        {"target": "Sweetcorn",             "source": "Maize"},
        {"target": "Table Grape",           "source": "Grape (Table)"},
        {"target": "Wine Grape",            "source": "Grape (Wine)"},
        {"target": "Peach/Nectarine",       "source": "Peach"},
        {"target": "Lucerne/Alfalfa",       "source": "Lucerne"},
        {"target": "Dry Beans",             "source": "Bean (Dry)"},
        {"target": "Green Beans",           "source": "Bean (Green)"},
        {"target": "Potato",                "source": "Potatoes"}
    ]'::jsonb;
BEGIN
    FOR rec IN SELECT jsonb_array_elements(aliases) AS pair LOOP
        IF NOT EXISTS (
            SELECT 1 FROM crop_growth_stages
            WHERE crop = rec.pair->>'target'
        ) THEN
            INSERT INTO crop_growth_stages (
                crop, stage_name, stage_order,
                month_start, month_end,
                n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct,
                fe_pct, b_pct, mn_pct, zn_pct,
                num_applications, default_method, notes
            )
            SELECT
                rec.pair->>'target', stage_name, stage_order,
                month_start, month_end,
                n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct,
                fe_pct, b_pct, mn_pct, zn_pct,
                num_applications, default_method,
                COALESCE(notes, '') ||
                    CASE WHEN notes IS NULL OR notes = '' THEN '' ELSE ' ' END ||
                    '[aliased from ' || (rec.pair->>'source') || ']'
            FROM crop_growth_stages
            WHERE crop = rec.pair->>'source';
        END IF;
    END LOOP;
END
$alias$;


-- ── 3. Expand perennial_age_factors ────────────────────────
-- Curves mirror the style of existing SA-published entries
-- (Citrus Valencia, Avocado, Macadamia, Mango, Pecan): factor
-- rises from ~0.15-0.30 at planting to 1.0 at maturity, with
-- N tracking slightly lower than P (fruit-wood development).
--
-- Sources: the existing seeded entries follow SA industry
-- curves; new rows follow the same pattern for pome, stone,
-- grape, olive, blueberry.

-- Citrus subtype aliases — identical curve to Valencia
DO $cf$
DECLARE
    citrus_subtypes TEXT[] := ARRAY[
        'Citrus (Grapefruit)',
        'Citrus (Lemon)',
        'Citrus (Navel)',
        'Citrus (Soft Citrus)'
    ];
    c TEXT;
BEGIN
    FOREACH c IN ARRAY citrus_subtypes LOOP
        IF NOT EXISTS (SELECT 1 FROM perennial_age_factors WHERE crop = c) THEN
            INSERT INTO perennial_age_factors
                (crop, age_min, age_max, n_factor, p_factor, k_factor, general_factor)
            SELECT c, age_min, age_max, n_factor, p_factor, k_factor, general_factor
            FROM perennial_age_factors
            WHERE crop = 'Citrus (Valencia)';
        END IF;
    END LOOP;
END
$cf$;

-- Pome fruit (Apple, Pear) — SA practice: full bearing from year 7
INSERT INTO perennial_age_factors
    (crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
SELECT * FROM (VALUES
    ('Apple', 'Year 1-2', 0, 1, 0.20, 0.25, 0.15, 0.20, 'Establishment; minimal nutrition'),
    ('Apple', 'Year 3-4', 2, 3, 0.40, 0.45, 0.35, 0.40, 'Frame development'),
    ('Apple', 'Year 5-6', 4, 5, 0.65, 0.65, 0.60, 0.65, 'First bearing'),
    ('Apple', 'Year 7',   6, 6, 0.85, 0.85, 0.80, 0.85, 'Pre-mature bearing'),
    ('Apple', 'Year 8+',  7, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    ('Pear',  'Year 1-2', 0, 1, 0.20, 0.25, 0.15, 0.20, 'Establishment'),
    ('Pear',  'Year 3-4', 2, 3, 0.40, 0.45, 0.35, 0.40, 'Frame development'),
    ('Pear',  'Year 5-6', 4, 5, 0.65, 0.65, 0.60, 0.65, 'First bearing'),
    ('Pear',  'Year 7',   6, 6, 0.85, 0.85, 0.80, 0.85, 'Pre-mature bearing'),
    ('Pear',  'Year 8+',  7, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing')
) AS v(crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
WHERE NOT EXISTS (
    SELECT 1 FROM perennial_age_factors pf WHERE pf.crop = v.crop
);

-- Stone fruit (Peach/Nectarine, Apricot, Plum) — full bearing year 5
INSERT INTO perennial_age_factors
    (crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
SELECT * FROM (VALUES
    ('Peach/Nectarine', 'Year 1-2', 0, 1, 0.25, 0.30, 0.20, 0.25, 'Establishment'),
    ('Peach/Nectarine', 'Year 3-4', 2, 3, 0.55, 0.60, 0.50, 0.55, 'Early bearing'),
    ('Peach/Nectarine', 'Year 5',   4, 4, 0.80, 0.80, 0.75, 0.80, 'Pre-mature bearing'),
    ('Peach/Nectarine', 'Year 6+',  5, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    ('Apricot', 'Year 1-2', 0, 1, 0.25, 0.30, 0.20, 0.25, 'Establishment'),
    ('Apricot', 'Year 3-4', 2, 3, 0.55, 0.60, 0.50, 0.55, 'Early bearing'),
    ('Apricot', 'Year 5',   4, 4, 0.80, 0.80, 0.75, 0.80, 'Pre-mature bearing'),
    ('Apricot', 'Year 6+',  5, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    ('Plum', 'Year 1-2', 0, 1, 0.25, 0.30, 0.20, 0.25, 'Establishment'),
    ('Plum', 'Year 3-4', 2, 3, 0.55, 0.60, 0.50, 0.55, 'Early bearing'),
    ('Plum', 'Year 5',   4, 4, 0.80, 0.80, 0.75, 0.80, 'Pre-mature bearing'),
    ('Plum', 'Year 6+',  5, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing')
) AS v(crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
WHERE NOT EXISTS (
    SELECT 1 FROM perennial_age_factors pf WHERE pf.crop = v.crop
);

-- Grape (Table/Wine) — full bearing year 4
INSERT INTO perennial_age_factors
    (crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
SELECT * FROM (VALUES
    ('Table Grape', 'Year 1', 0, 0, 0.10, 0.20, 0.10, 0.10, 'Establishment'),
    ('Table Grape', 'Year 2', 1, 1, 0.35, 0.40, 0.30, 0.35, 'Canopy development'),
    ('Table Grape', 'Year 3', 2, 2, 0.65, 0.65, 0.60, 0.65, 'First bearing'),
    ('Table Grape', 'Year 4+', 3, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    ('Wine Grape',  'Year 1', 0, 0, 0.10, 0.20, 0.10, 0.10, 'Establishment'),
    ('Wine Grape',  'Year 2', 1, 1, 0.35, 0.40, 0.30, 0.35, 'Canopy development'),
    ('Wine Grape',  'Year 3', 2, 2, 0.65, 0.65, 0.60, 0.65, 'First bearing'),
    ('Wine Grape',  'Year 4+', 3, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing')
) AS v(crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
WHERE NOT EXISTS (
    SELECT 1 FROM perennial_age_factors pf WHERE pf.crop = v.crop
);

-- Olive — slow establishment, full bearing year 10
INSERT INTO perennial_age_factors
    (crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
SELECT * FROM (VALUES
    ('Olive', 'Year 1-3', 0, 2, 0.25, 0.30, 0.20, 0.25, 'Establishment'),
    ('Olive', 'Year 4-6', 3, 5, 0.55, 0.60, 0.50, 0.55, 'Early bearing'),
    ('Olive', 'Year 7-9', 6, 8, 0.80, 0.80, 0.75, 0.80, 'Pre-mature bearing'),
    ('Olive', 'Year 10+', 9, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing')
) AS v(crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
WHERE NOT EXISTS (
    SELECT 1 FROM perennial_age_factors pf WHERE pf.crop = v.crop
);

-- Blueberry — bush, full bearing year 3
INSERT INTO perennial_age_factors
    (crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
SELECT * FROM (VALUES
    ('Blueberry', 'Year 1',  0, 0, 0.30, 0.35, 0.25, 0.30, 'Establishment'),
    ('Blueberry', 'Year 2',  1, 1, 0.60, 0.65, 0.55, 0.60, 'Early bearing'),
    ('Blueberry', 'Year 3+', 2, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing')
) AS v(crop, age_label, age_min, age_max, n_factor, p_factor, k_factor, general_factor, notes)
WHERE NOT EXISTS (
    SELECT 1 FROM perennial_age_factors pf WHERE pf.crop = v.crop
);


-- ── 4. Backfill programme_blocks.nutrient_targets ──────────
-- Copy cached targets from linked soil_analyses where the block
-- cache is missing. preview-schedule reads from the block cache
-- and 400s when it's empty.
UPDATE programme_blocks pb
SET nutrient_targets = sa.nutrient_targets
FROM soil_analyses sa
WHERE pb.soil_analysis_id = sa.id
  AND (pb.nutrient_targets IS NULL
       OR jsonb_typeof(pb.nutrient_targets) <> 'array'
       OR jsonb_array_length(pb.nutrient_targets) = 0)
  AND sa.nutrient_targets IS NOT NULL
  AND jsonb_typeof(sa.nutrient_targets) = 'array'
  AND jsonb_array_length(sa.nutrient_targets) > 0;

COMMIT;
