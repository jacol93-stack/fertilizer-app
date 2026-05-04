-- ============================================================
-- 096: Laborie (Anton Muller) — accept all application methods
-- ============================================================
-- The 2026-04-30 fields-bulk import left every Laborie block with an
-- empty accepted_methods array. The programmes_v2 router falls through
-- to a fertigation/foliar derivation when the array is empty, but only
-- if irrigation_type + fertigation_capable are set — and even then it
-- skips band_place and side_dress entirely. To give the engine full
-- routing freedom, set all 38 active blocks on the farm to accept the
-- full canonical method set: band_place, broadcast, fertigation,
-- foliar, side_dress.
-- ============================================================

BEGIN;

UPDATE public.fields
SET accepted_methods = '["band_place","broadcast","fertigation","foliar","side_dress"]'::jsonb
WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND deleted_at IS NULL;

DO $$
DECLARE
    updated_count INT;
BEGIN
    SELECT COUNT(*) INTO updated_count
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND deleted_at IS NULL
      AND accepted_methods @> '["band_place","broadcast","fertigation","foliar","side_dress"]'::jsonb
      AND jsonb_array_length(accepted_methods) = 5;

    RAISE NOTICE 'Laborie blocks now accepting all 5 methods: %', updated_count;

    IF updated_count <> 38 THEN
        RAISE EXCEPTION 'Expected 38 blocks updated on Laborie, got %', updated_count;
    END IF;
END $$;

COMMIT;
