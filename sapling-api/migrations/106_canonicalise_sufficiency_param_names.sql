-- ============================================================
-- 106: canonicalise crop_sufficiency_overrides.parameter names
-- ============================================================
-- Rationale
--
-- The application code now merges generic `soil_sufficiency` with
-- `crop_sufficiency_overrides` through `merge_sufficiency_for_crop`,
-- which routes both row sources through the soil canonicaliser. So
-- runtime correctness is no longer sensitive to label drift between
-- the two tables.
--
-- This migration cleans up the stale data so a human reading the
-- override table sees one name per parameter and the dataset matches
-- the canonical schema.
--
-- Specific case (the bug that motivated all of this): Citrus had a
-- `'K (exchangeable)'` row that never matched the generic `'K'` row
-- under the old in-router merge logic, so the citrus K override was
-- silently dead. Renaming aligns it with `soil_sufficiency.parameter`
-- and the canonicaliser's canonical key for K.
--
-- Add new rules here when other non-canonical names show up. Each
-- rename is idempotent (no-ops if the row already uses the canonical
-- name).
-- ============================================================

BEGIN;

UPDATE public.crop_sufficiency_overrides
   SET parameter = 'K'
 WHERE parameter = 'K (exchangeable)';

UPDATE public.crop_sufficiency_overrides
   SET parameter = 'Ca'
 WHERE parameter = 'Ca (exchangeable)';

UPDATE public.crop_sufficiency_overrides
   SET parameter = 'Mg'
 WHERE parameter = 'Mg (exchangeable)';

UPDATE public.crop_sufficiency_overrides
   SET parameter = 'Na'
 WHERE parameter = 'Na (exchangeable)';

COMMIT;
