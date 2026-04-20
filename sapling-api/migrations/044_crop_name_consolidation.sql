-- ============================================================
-- Crop name consolidation — collapse duplicate naming variants
-- ============================================================
-- migrations 041/042 seeded FERTASA-aligned names but the existing
-- seed data left alias rows around, so e.g. `Dry Beans` and
-- `Bean (Dry)` both exist, splitting programme lookups.
--
-- This migration renames alias → canonical where possible, otherwise
-- deletes the alias (when canonical already carries the authoritative
-- 041/042/043 data).
--
-- Alias → Canonical:
--   Dry Beans         → Bean (Dry)
--   Green Beans       → Bean (Green)
--   Grape (Wine)      → Wine Grape
--   Grape (Table)     → Table Grape
--   Peach/Nectarine   → Peach              (keeps `Nectarine` as separate crop)
--   Potatoes          → Potato
--   Lucerne/Alfalfa   → Lucerne
--
-- Pattern per data table (UPSERT-safe):
--   1. UPDATE alias → canonical IF canonical doesn't already exist
--      (preserves alias-only rows when canonical is missing)
--   2. DELETE any remaining alias rows (canonical now wins)
--
-- Pattern per user-facing table (programme_blocks / leaf_analyses):
--   Always UPDATE alias → canonical (unconditional rename)
--   NB: `programmes` has no `crop` column — crop lives on programme_blocks.
-- ============================================================

BEGIN;

DO $$
DECLARE
    mapping RECORD;
    data_tables TEXT[] := ARRAY[
        'crop_growth_stages',
        'crop_requirements',
        'fertasa_leaf_norms',
        'crop_sufficiency_overrides',
        'tissue_toxicity'
    ];
    user_tables TEXT[] := ARRAY[
        'programme_blocks',
        'leaf_analyses'
    ];
    tbl TEXT;
BEGIN
    FOR mapping IN SELECT * FROM (VALUES
        ('Dry Beans',       'Bean (Dry)'),
        ('Green Beans',     'Bean (Green)'),
        ('Grape (Wine)',    'Wine Grape'),
        ('Grape (Table)',   'Table Grape'),
        ('Peach/Nectarine', 'Peach'),
        ('Potatoes',        'Potato'),
        ('Lucerne/Alfalfa', 'Lucerne')
    ) AS m(alias, canonical) LOOP

        -- Data tables: preserve alias-only rows, delete redundant aliases
        FOREACH tbl IN ARRAY data_tables LOOP
            -- Skip if table doesn't exist in this deployment
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = tbl) THEN
                EXECUTE format(
                    'UPDATE %I SET crop = %L
                     WHERE crop = %L
                       AND NOT EXISTS (SELECT 1 FROM %I WHERE crop = %L)',
                    tbl, mapping.canonical, mapping.alias, tbl, mapping.canonical
                );
                EXECUTE format('DELETE FROM %I WHERE crop = %L', tbl, mapping.alias);
            END IF;
        END LOOP;

        -- User-facing tables: unconditional rename (no canonical "rows"
        -- to collide with; these hold user-entered block/programme crops)
        FOREACH tbl IN ARRAY user_tables LOOP
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = tbl) THEN
                EXECUTE format(
                    'UPDATE %I SET crop = %L WHERE crop = %L',
                    tbl, mapping.canonical, mapping.alias
                );
            END IF;
        END LOOP;

    END LOOP;
END $$;

-- Verification — surface any leftover alias rows (should be empty).
-- Uncomment if you want to manually re-run the check:
--
-- SELECT 'crop_growth_stages' AS tbl, crop, COUNT(*) FROM crop_growth_stages
-- WHERE crop IN ('Dry Beans','Green Beans','Grape (Wine)','Grape (Table)',
--                'Peach/Nectarine','Potatoes','Lucerne/Alfalfa')
-- GROUP BY crop;

COMMIT;
