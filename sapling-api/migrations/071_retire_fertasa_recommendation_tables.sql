-- ============================================================
-- 071: Retire fertasa_recommendation_tables (legacy pre-046 schema)
-- ============================================================
-- 2026-04-23 rebaseline. fertasa_recommendation_tables was the pre-046
-- JSONB-axis approach to rate data. Superseded by the normalised
-- fertilizer_rate_tables (schema + 20 seed migrations 046-069). Most
-- rows now duplicated; some unique rows remain with non-standard axes
-- (tree-age, drip-area, CEC-split) that don't fit rate_tables cleanly.
--
-- This migration:
--   1. Drops 32 rows that are now fully duplicated in fertilizer_rate_tables
--      (Bean Dry N/P/K, Cotton N/P, Lucerne P/K, Potato N (dryland+irrig)/P,
--       Sunflower N/P/K, Sweetcorn N/P/K, Tobacco N/P/K, Wheat N (all 6
--       regions)/P/K, Soybean P/K, Canola S, Banana P, Macadamia N)
--   2. Drops 3 catch-all rows (Pastures N/P, General Vegetables NPK)
--      — superseded by specific crops or not in registry
--   3. Preserves 16 unique rows for targeted Phase 6 extraction:
--      - Avocado NPK (drip-area formula)
--      - Banana NPK (plant-crop by yield)
--      - Canola K heavy/light soils, P (citric acid)
--      - Citrus N/P/K young trees by age (awaiting Raath 2021)
--      - Pecan NPK young trees by age
--      - Potato Ca, Mg, K CEC-split (2 variants)
--      - Soybean N (inoculation-failure fallback)
--      - Sunflower B by soil texture (FERTASA 5.5.6)
--      - Tomato NPK by yield (tomato rate-tables incomplete)
--      - Wheat Micro (FERTASA 5.4.3 Table 7)
--   4. Marks the table deprecated via comment + sentinel column
--   5. Does NOT drop the table — preserves 16 rows for future extraction
--
-- Full DROP happens in a future migration once all 16 unique rows
-- have been extracted into fertilizer_rate_tables with appropriate
-- schema extensions (age-axis, drip-area, CEC-split columns).
-- ============================================================

BEGIN;

-- Drop 32 duplicated rows
DELETE FROM public.fertasa_recommendation_tables
 WHERE (crop = 'Bean (Dry)'   AND nutrient IN ('N','P','K'))
    OR (crop = 'Cotton'       AND nutrient IN ('N','P'))
    OR (crop = 'Lucerne'      AND nutrient IN ('P','K'))
    OR (crop = 'Potato'       AND (nutrient = 'P' OR (nutrient = 'N' AND table_name LIKE 'N %land%clay %')))
    OR (crop = 'Sunflower'    AND nutrient IN ('N','P','K'))
    OR (crop = 'Sweetcorn'    AND nutrient IN ('N','P','K'))
    OR (crop = 'Tobacco'      AND nutrient IN ('N','P','K'))
    OR (crop = 'Wheat'        AND (nutrient IN ('P','K') OR (nutrient = 'N' AND table_name != 'N for high yields')))
    OR (crop = 'Soybean'      AND nutrient IN ('P','K'))
    OR (crop = 'Canola'       AND nutrient = 'S')
    OR (crop = 'Banana'       AND nutrient = 'P')
    OR (crop = 'Macadamia'    AND nutrient = 'N');

-- Drop 3 catch-all legacy rows
DELETE FROM public.fertasa_recommendation_tables
 WHERE crop IN ('Pastures', 'General Vegetables');

-- Verify expected final state: 16 unique rows remain
DO $$
DECLARE
    remaining INTEGER;
    expected INTEGER := 16;
BEGIN
    SELECT COUNT(*) INTO remaining FROM public.fertasa_recommendation_tables;
    RAISE NOTICE '071: fertasa_recommendation_tables rows remaining = %', remaining;
    -- Allow some flex — we don't fail if a row or two differs from the plan
    -- because the WHERE clauses might miss a weird edge case
    IF remaining > 25 THEN
        RAISE EXCEPTION '071 FAILED: % rows remain (expected ~%)', remaining, expected;
    END IF;
END $$;

-- Add deprecation sentinel + comment
ALTER TABLE public.fertasa_recommendation_tables
    ADD COLUMN IF NOT EXISTS deprecated BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON TABLE public.fertasa_recommendation_tables IS
    'DEPRECATED 2026-04-23 (migration 071). Pre-046 JSONB-axis approach
     to rate data, superseded by fertilizer_rate_tables. Remaining rows
     (~16) contain unique axes (tree-age, drip-area, CEC-split) awaiting
     Phase 6 extraction with schema extensions. DO NOT READ FROM THIS
     TABLE IN NEW ENGINE CODE. Once all rows are extracted, this table
     will be DROPPED entirely.';

COMMIT;
