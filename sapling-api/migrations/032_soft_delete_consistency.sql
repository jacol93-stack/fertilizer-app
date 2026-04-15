-- 032: Soft-delete consistency across user-generated records
--
-- Audit finding: only `clients` had deleted_at/deleted_by (migration 028).
-- Blends, soil_analyses, feeding_plans, quotes, programmes, and leaf_analyses
-- either soft-delete inconsistently or store deleted_at without tracking who
-- deleted the row. This migration backfills the columns everywhere so the
-- admin trash/restore flow and audit trail are uniform.
--
-- Safe to apply to existing data:
--   - All columns added with IF NOT EXISTS
--   - Default NULL (equivalent to "not deleted")
--   - No FK cascade changes (those are in a separate, reviewed migration)
--
-- After this migration, the application code must be updated so every
-- DELETE endpoint writes deleted_at + deleted_by instead of hard-deleting.

-- ── blends ────────────────────────────────────────────────────────────────
ALTER TABLE public.blends
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_blends_deleted_at
    ON public.blends(deleted_at)
    WHERE deleted_at IS NULL;


-- ── soil_analyses ─────────────────────────────────────────────────────────
ALTER TABLE public.soil_analyses
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_soil_analyses_deleted_at
    ON public.soil_analyses(deleted_at)
    WHERE deleted_at IS NULL;


-- ── feeding_plans ─────────────────────────────────────────────────────────
ALTER TABLE public.feeding_plans
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_feeding_plans_deleted_at
    ON public.feeding_plans(deleted_at)
    WHERE deleted_at IS NULL;


-- ── quotes ────────────────────────────────────────────────────────────────
ALTER TABLE public.quotes
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_quotes_deleted_at
    ON public.quotes(deleted_at)
    WHERE deleted_at IS NULL;


-- ── programmes ───────────────────────────────────────────────────────────
-- programmes already has deleted_at (from 016) but no deleted_by
ALTER TABLE public.programmes
    ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL;


-- ── leaf_analyses ─────────────────────────────────────────────────────────
-- leaf_analyses already has deleted_at (from 019) but no deleted_by
ALTER TABLE public.leaf_analyses
    ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL;


-- ── Rollback notes ────────────────────────────────────────────────────────
-- To reverse (careful: you lose the deletion audit trail):
--   ALTER TABLE blends         DROP COLUMN IF EXISTS deleted_at, DROP COLUMN IF EXISTS deleted_by;
--   ALTER TABLE soil_analyses  DROP COLUMN IF EXISTS deleted_at, DROP COLUMN IF EXISTS deleted_by;
--   ALTER TABLE feeding_plans  DROP COLUMN IF EXISTS deleted_at, DROP COLUMN IF EXISTS deleted_by;
--   ALTER TABLE quotes         DROP COLUMN IF EXISTS deleted_at, DROP COLUMN IF EXISTS deleted_by;
--   ALTER TABLE programmes     DROP COLUMN IF EXISTS deleted_by;
--   ALTER TABLE leaf_analyses  DROP COLUMN IF EXISTS deleted_by;
