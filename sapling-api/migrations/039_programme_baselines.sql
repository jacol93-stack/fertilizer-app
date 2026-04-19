-- ============================================================
-- Programme baselines — the original plan, frozen at activation
-- ============================================================
-- Every programme that gets activated should carry a snapshot of
-- its blocks + blends at the moment of activation. This is the
-- anchor every later comparison uses:
--
--   "what's changed since we activated" → current vs baseline
--   "what must now be done vs original"  → baseline minus applied
--                                           minus adjustments
--
-- A programme can have multiple baselines if the agent chooses to
-- "rebase" mid-season (deliberate reset of the plan). Latest
-- baseline wins for comparison by default.
--
-- JSONB snapshots rather than FK references — we want the comparison
-- to survive block/blend renames, deletes, and schema shifts in the
-- live tables. The baseline is a frozen contract.
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS programme_baselines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    programme_id    UUID NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      UUID REFERENCES profiles(id),
    reason          TEXT NOT NULL DEFAULT 'activation',
                    -- 'activation' | 'manual_rebase' | 'import'
    is_current      BOOLEAN NOT NULL DEFAULT TRUE,
    blocks          JSONB NOT NULL,
                    -- frozen programme_blocks snapshot at this moment
    blends          JSONB NOT NULL,
                    -- frozen programme_blends snapshot
    nutrient_targets_by_block JSONB,
                    -- {block_id: [{Nutrient, Final_Target_kg_ha, ...}]}
                    -- convenience copy so we don't have to re-dig the
                    -- block.nutrient_targets field
    notes           TEXT
);

-- Only one row per programme carries is_current=TRUE at a time.
-- When a new baseline lands, the old one is flipped to FALSE.
CREATE UNIQUE INDEX IF NOT EXISTS ux_baselines_current_per_programme
    ON programme_baselines(programme_id)
    WHERE is_current = TRUE;

CREATE INDEX IF NOT EXISTS idx_baselines_programme
    ON programme_baselines(programme_id, created_at DESC);

-- Constrain reason to known values
ALTER TABLE programme_baselines
    DROP CONSTRAINT IF EXISTS chk_baseline_reason;
ALTER TABLE programme_baselines
    ADD CONSTRAINT chk_baseline_reason
    CHECK (reason IN ('activation', 'manual_rebase', 'import'));

-- RLS: baselines inherit access from the parent programme
ALTER TABLE programme_baselines ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS baselines_agent_select ON programme_baselines;
CREATE POLICY baselines_agent_select ON programme_baselines
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM programmes p
            WHERE p.id = programme_baselines.programme_id
              AND (p.agent_id = auth.uid() OR public.is_admin())
        )
    );

DROP POLICY IF EXISTS baselines_agent_write ON programme_baselines;
CREATE POLICY baselines_agent_write ON programme_baselines
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM programmes p
            WHERE p.id = programme_baselines.programme_id
              AND (p.agent_id = auth.uid() OR public.is_admin())
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM programmes p
            WHERE p.id = programme_baselines.programme_id
              AND (p.agent_id = auth.uid() OR public.is_admin())
        )
    );

DROP POLICY IF EXISTS baselines_service_role ON programme_baselines;
CREATE POLICY baselines_service_role ON programme_baselines
    FOR ALL TO service_role
    USING (TRUE) WITH CHECK (TRUE);

COMMIT;
