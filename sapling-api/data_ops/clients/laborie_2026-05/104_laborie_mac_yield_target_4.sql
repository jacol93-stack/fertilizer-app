-- ============================================================
-- 104: Laborie — set yield_target = 4 t NIS/ha on all Macadamia blocks
-- ============================================================
-- Per the agronomist (2026-04-30): use 4 t NIS/ha as the per-block
-- yield target across all Laborie macadamia blocks. This matches the
-- SAMAC mature-bearing reference and the crop_requirements.default_yield
-- for Macadamia. The engine's perennial_age_factors curve scales N/P/K
-- down for young blocks (e.g. 14 at 3 y.o., the A4 plantings at 6 y.o.)
-- so the same 4 t/ha reference is correct for every age bracket; the
-- scaling happens at compute time, not in this stored value.
--
-- Citrus blocks intentionally not touched. Citrus default_yield in
-- crop_requirements is calibrated per-variant (Valencia 40 t/ha,
-- Navel 35, Grapefruit 45, Lemon 40). Leaving yield_target NULL on
-- citrus lets the engine fall back to the variant default rather than
-- forcing a one-size-fits-all number.
-- ============================================================

BEGIN;

UPDATE public.fields
SET yield_target = 4.0
WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND crop = 'Macadamia'
  AND deleted_at IS NULL;

DO $$
DECLARE
    mac_count INT;
    citrus_unchanged INT;
BEGIN
    SELECT COUNT(*) INTO mac_count
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND crop = 'Macadamia'
      AND deleted_at IS NULL
      AND yield_target = 4.0;

    SELECT COUNT(*) INTO citrus_unchanged
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND crop LIKE 'Citrus%'
      AND deleted_at IS NULL
      AND yield_target IS NULL;

    RAISE NOTICE 'Laborie post-update: Mac at 4 t/ha = %, Citrus untouched (NULL) = %',
        mac_count, citrus_unchanged;

    IF mac_count <> 23 THEN
        RAISE EXCEPTION 'Expected 23 Macadamia blocks at 4.0, got %', mac_count;
    END IF;
    IF citrus_unchanged <> 14 THEN
        RAISE EXCEPTION 'Expected 14 Citrus blocks unchanged (NULL yield_target), got %', citrus_unchanged;
    END IF;
END $$;

COMMIT;
