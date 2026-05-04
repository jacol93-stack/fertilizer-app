-- ============================================================
-- 097: Laborie — restrict accepted_methods to orchard-applicable set
-- ============================================================
-- Migration 096 set all five canonical methods on every Laborie block,
-- but band_place and side_dress are annual-crop methods that don't
-- apply to mac / citrus orchards:
--   - band_place: banding fertilizer in a furrow at sowing
--   - side_dress: row-crop interrow placement on actively growing crops
--
-- The field-editor UI silently strips any accepted_methods value not
-- listed in crop_application_methods for that crop. For Macadamia and
-- Citrus (Valencia/Grapefruit), the catalog correctly lists only:
--   broadcast | fertigation | foliar
--
-- This migration aligns the DB with the catalog so the engine and UI
-- agree, and so the next "save field" in the UI doesn't silently
-- contradict what the engine sees.
-- ============================================================

BEGIN;

UPDATE public.fields
SET accepted_methods = '["broadcast","fertigation","foliar"]'::jsonb
WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND deleted_at IS NULL;

DO $$
DECLARE
    correct_count INT;
BEGIN
    SELECT COUNT(*) INTO correct_count
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND deleted_at IS NULL
      AND accepted_methods @> '["broadcast","fertigation","foliar"]'::jsonb
      AND jsonb_array_length(accepted_methods) = 3;

    RAISE NOTICE 'Laborie blocks with orchard methods (broadcast/fertigation/foliar): %', correct_count;

    IF correct_count <> 38 THEN
        RAISE EXCEPTION 'Expected 38 blocks, got %', correct_count;
    END IF;
END $$;

COMMIT;
