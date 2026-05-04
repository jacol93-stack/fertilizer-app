-- ============================================================
-- 105: Laborie — set yield_target = 65 t fruit/ha on all Citrus blocks
-- ============================================================
-- Per the agronomist (2026-04-30): use 65 t fruit/ha as the per-block
-- yield target across all Laborie citrus blocks. Sits at the high end
-- of the SA mature-bearing reference (yield_benchmarks: Valencia
-- irrigated 35-55-75, Navel 30-45-60, Star Ruby Grapefruit 35-55-75).
-- The engine's perennial_age_factors curve scales N/P/K down for young
-- blocks (e.g. 1C at 1 y.o., 8B at 5 y.o.) so the same 65 t/ha reference
-- is correct for every age bracket.
-- ============================================================

BEGIN;

UPDATE public.fields
SET yield_target = 65.0
WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND crop LIKE 'Citrus%'
  AND deleted_at IS NULL;

DO $$
DECLARE
    citrus_count INT;
BEGIN
    SELECT COUNT(*) INTO citrus_count
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND crop LIKE 'Citrus%'
      AND deleted_at IS NULL
      AND yield_target = 65.0;

    RAISE NOTICE 'Laborie Citrus blocks at 65 t fruit/ha: %', citrus_count;

    IF citrus_count <> 14 THEN
        RAISE EXCEPTION 'Expected 14 Citrus blocks at 65.0, got %', citrus_count;
    END IF;
END $$;

COMMIT;
