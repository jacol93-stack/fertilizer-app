-- ============================================================
-- Crop name consolidation — follow-up to 044
-- ============================================================
-- Migration 044 consolidated aliases in a subset of tables but
-- missed: crop_application_methods, crop_micronutrient_schedule,
-- perennial_age_factors, fertasa_nutrient_removal,
-- fertasa_recommendation_tables, fertasa_sampling_guide,
-- fertasa_soil_norms, agent_crop_overrides, feeding_plans,
-- field_crop_history, fields, soil_analyses.
--
-- Consequence of the miss: the programme builder reads
-- crop_application_methods during method validation, so a user
-- picking the canonical name (e.g. "Peach") from the wizard
-- after 044 would hit an empty methods lookup because the rows
-- were still keyed to "Peach/Nectarine".
--
-- Same alias → canonical map as 044, same UPSERT-safe pattern.
-- ============================================================

BEGIN;

DO $$
DECLARE
    mapping RECORD;
    data_tables TEXT[] := ARRAY[
        'crop_application_methods',
        'crop_micronutrient_schedule',
        'perennial_age_factors',
        'fertasa_nutrient_removal',
        'fertasa_recommendation_tables',
        'fertasa_sampling_guide',
        'fertasa_soil_norms'
    ];
    user_tables TEXT[] := ARRAY[
        'agent_crop_overrides',
        'feeding_plans',
        'field_crop_history',
        'fields',
        'soil_analyses'
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

        FOREACH tbl IN ARRAY data_tables LOOP
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

COMMIT;
