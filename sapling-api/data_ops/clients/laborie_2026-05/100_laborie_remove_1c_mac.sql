-- ============================================================
-- 100: Laborie — soft-delete 1C-Mac (was a misread)
-- ============================================================
-- Migration 095 created '1C-Mac' (Macadamia 695, 2 ha, age 10, pop 217)
-- as a disambiguated re-creation of the bulk-import row that collided
-- with Citrus '1C' Turkey Valencia. The agronomist confirmed today
-- (2026-04-30) that 1C is a Citrus Turkey Valencia block, not a
-- Macadamia — the original upload row was wrong.
--
-- The 1C citrus row already in the DB matches the file exactly
-- (Citrus (Valencia), Turkey Valencia, 2 ha, age 1, pop 217), so we
-- just need to remove the orphan Macadamia row.
--
-- Soft-delete (not hard delete): preserves history per migration 089.
-- No leaf / soil / yield / programme references exist on this field
-- — verified via supabase query before applying.
-- ============================================================

BEGIN;

UPDATE public.fields
SET deleted_at = NOW()
WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND name = '1C-Mac'
  AND crop = 'Macadamia'
  AND deleted_at IS NULL;

DO $$
DECLARE
    active_total INT;
    active_mac INT;
    active_1c_count INT;
BEGIN
    SELECT COUNT(*) INTO active_total
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND deleted_at IS NULL;

    SELECT COUNT(*) INTO active_mac
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND crop = 'Macadamia'
      AND deleted_at IS NULL;

    SELECT COUNT(*) INTO active_1c_count
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND name = '1C'
      AND deleted_at IS NULL;

    RAISE NOTICE 'Laborie post-cleanup: total active=%, Macadamia=%, 1C count=%',
        active_total, active_mac, active_1c_count;

    IF active_total <> 37 THEN
        RAISE EXCEPTION 'Expected 37 active blocks, got %', active_total;
    END IF;
    IF active_mac <> 23 THEN
        RAISE EXCEPTION 'Expected 23 active Macadamia blocks, got %', active_mac;
    END IF;
    IF active_1c_count <> 1 THEN
        RAISE EXCEPTION 'Expected exactly one 1C block (Citrus Turkey Valencia), got %', active_1c_count;
    END IF;
END $$;

COMMIT;
