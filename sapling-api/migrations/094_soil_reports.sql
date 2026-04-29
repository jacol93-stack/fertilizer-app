-- ============================================================
-- 094: soil_reports table
-- ============================================================
-- Per-block (or multi-block) soil interpretation report. Replaces the
-- old `/quick-analysis` page. Three scope kinds:
--   single_block            — 1 block, 1 analysis; deepest single-snapshot dive
--   block_with_history      — 1 block, N analyses; trend analysis over time
--   multi_block             — N blocks (each with 1+ analyses); per-block + holistic summary
--
-- Mirrors programme_artifacts' shape so the renderer + narrative
-- pipeline can reuse most existing code paths. Lifecycle is identical:
-- draft (mutable) → approved (narrative locked, immutable) → archived.
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.soil_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    client_id UUID,
    farm_id UUID,
    farm_name TEXT,

    title TEXT,
    scope_kind TEXT NOT NULL DEFAULT 'single_block'
        CHECK (scope_kind IN ('single_block','block_with_history','multi_block')),
    block_ids UUID[] NOT NULL DEFAULT '{}',
    analysis_ids UUID[] NOT NULL DEFAULT '{}',

    state TEXT NOT NULL DEFAULT 'draft'
        CHECK (state IN ('draft','approved','archived')),

    report_payload JSONB NOT NULL,

    narrative_overrides JSONB,
    narrative_report JSONB,
    narrative_generated_at TIMESTAMPTZ,
    narrative_locked_at TIMESTAMPTZ,

    reviewer_id UUID,
    reviewed_at TIMESTAMPTZ,
    reviewer_notes TEXT,

    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_soil_reports_user ON public.soil_reports (user_id);
CREATE INDEX IF NOT EXISTS idx_soil_reports_client ON public.soil_reports (client_id);
CREATE INDEX IF NOT EXISTS idx_soil_reports_state ON public.soil_reports (state);
CREATE INDEX IF NOT EXISTS idx_soil_reports_created ON public.soil_reports (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_soil_reports_active ON public.soil_reports (client_id, created_at DESC) WHERE deleted_at IS NULL;

CREATE OR REPLACE FUNCTION public._soil_reports_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_soil_reports_touch ON public.soil_reports;
CREATE TRIGGER trg_soil_reports_touch
BEFORE UPDATE ON public.soil_reports
FOR EACH ROW EXECUTE FUNCTION public._soil_reports_touch_updated_at();

ALTER TABLE public.soil_reports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS soil_reports_select_own ON public.soil_reports;
CREATE POLICY soil_reports_select_own ON public.soil_reports
    FOR SELECT USING (user_id = auth.uid());

DROP POLICY IF EXISTS soil_reports_insert_own ON public.soil_reports;
CREATE POLICY soil_reports_insert_own ON public.soil_reports
    FOR INSERT WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS soil_reports_update_own ON public.soil_reports;
CREATE POLICY soil_reports_update_own ON public.soil_reports
    FOR UPDATE USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

COMMENT ON TABLE public.soil_reports IS
    'Sapling-generated soil interpretation reports. Replaces the legacy /quick-analysis page. Three scope kinds: single_block, block_with_history, multi_block. Mirrors programme_artifacts shape for renderer + narrative-pipeline reuse.';

COMMIT;
