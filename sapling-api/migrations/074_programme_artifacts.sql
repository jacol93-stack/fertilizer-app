-- ============================================================
-- 074: programme_artifacts table — persistence for the new typed
--      ProgrammeArtifact produced by programme_builder_orchestrator
-- ============================================================
-- Separate from the legacy `programmes` + `programme_blends` tables
-- which remain for Phase A-E Season Tracker foundations (detect/propose/
-- review/apply — migrations 037/038/039). The new artifact is the
-- source of truth for programmes built via the new orchestrator.
--
-- Structured columns enable filtering, listing, RLS, and search
-- without JSONB unpacking. The artifact JSONB carries everything else.
-- The original `inputs` JSONB is retained for reproducibility — users
-- can re-run a programme with different settings without re-entering
-- everything.
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.programme_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Ownership + filtering (RLS keys)
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    client_id UUID,  -- FK to clients when that table stabilises
    farm_name TEXT,  -- denormalised so programmes don't break if farm renamed

    -- Core programme metadata
    crop TEXT NOT NULL,
    planting_date DATE NOT NULL,
    build_date DATE NOT NULL,
    expected_harvest_date DATE,
    season TEXT,
    ref_number TEXT,
    prepared_for TEXT,

    -- Lifecycle state machine
    state TEXT NOT NULL DEFAULT 'draft'
        CHECK (state IN ('draft','approved','activated','in_progress','completed','archived')),
    replan_reason TEXT NOT NULL DEFAULT 'first_pass'
        CHECK (replan_reason IN (
            'first_pass','leaf_analysis','soil_analysis',
            'off_programme_application','weather_deviation',
            'yield_revision','cultivar_change','manual')),

    -- Summary metrics surfaced for listing pages without loading full JSONB
    worst_tier INTEGER,  -- 1-6; worst source tier across all computed numbers
    confidence_level TEXT
        CHECK (confidence_level IN ('minimum','standard','high') OR confidence_level IS NULL),
    blocks_count INTEGER NOT NULL DEFAULT 0,
    foliar_events_count INTEGER NOT NULL DEFAULT 0,
    risk_flags_count INTEGER NOT NULL DEFAULT 0,

    -- The typed payload
    artifact JSONB NOT NULL,
    artifact_version TEXT NOT NULL DEFAULT '1.0.0',

    -- Original inputs (for reproducibility — re-run with modified settings)
    inputs JSONB NOT NULL
);

COMMENT ON TABLE public.programme_artifacts IS
    'Typed ProgrammeArtifact persistence (2026-04-23 rebuild). Source of
     truth for programmes built via programme_builder_orchestrator.
     Legacy `programmes` + `programme_blends` tables remain for Season
     Tracker Phase A-E foundations.';

CREATE INDEX IF NOT EXISTS idx_prog_artifacts_user ON public.programme_artifacts (user_id);
CREATE INDEX IF NOT EXISTS idx_prog_artifacts_client ON public.programme_artifacts (client_id);
CREATE INDEX IF NOT EXISTS idx_prog_artifacts_state ON public.programme_artifacts (state);
CREATE INDEX IF NOT EXISTS idx_prog_artifacts_crop ON public.programme_artifacts (crop);
CREATE INDEX IF NOT EXISTS idx_prog_artifacts_planting ON public.programme_artifacts (planting_date DESC);
CREATE INDEX IF NOT EXISTS idx_prog_artifacts_created ON public.programme_artifacts (created_at DESC);

-- Updated_at trigger (same pattern as other tables in this DB)
CREATE OR REPLACE FUNCTION public._programme_artifacts_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_programme_artifacts_touch ON public.programme_artifacts;
CREATE TRIGGER trg_programme_artifacts_touch
BEFORE UPDATE ON public.programme_artifacts
FOR EACH ROW EXECUTE FUNCTION public._programme_artifacts_touch_updated_at();

-- RLS: user can only see their own artifacts (admin override handled in API)
ALTER TABLE public.programme_artifacts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS programme_artifacts_select_own ON public.programme_artifacts;
CREATE POLICY programme_artifacts_select_own ON public.programme_artifacts
    FOR SELECT
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS programme_artifacts_insert_own ON public.programme_artifacts;
CREATE POLICY programme_artifacts_insert_own ON public.programme_artifacts
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS programme_artifacts_update_own ON public.programme_artifacts;
CREATE POLICY programme_artifacts_update_own ON public.programme_artifacts
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

COMMIT;
