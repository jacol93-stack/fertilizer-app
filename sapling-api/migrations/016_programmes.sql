-- ============================================================
-- Season Manager: programmes, blocks, and blends
-- A programme is a full-season fertilizer plan for a client/farm
-- with multiple blocks that can share blends
-- ============================================================

-- Programmes: the top-level season plan
CREATE TABLE IF NOT EXISTS programmes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    agent_id        UUID NOT NULL REFERENCES profiles(id),
    client_id       UUID REFERENCES clients(id),
    farm_id         UUID REFERENCES farms(id),
    name            TEXT NOT NULL,
    season          TEXT,                  -- e.g. "2026/2027"
    status          TEXT NOT NULL DEFAULT 'draft',  -- draft, active, completed, archived
    notes           TEXT,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID
);

CREATE INDEX idx_programmes_agent ON programmes(agent_id);
CREATE INDEX idx_programmes_client ON programmes(client_id);
CREATE INDEX idx_programmes_status ON programmes(status) WHERE deleted_at IS NULL;

-- Programme blocks: individual land units within a programme
CREATE TABLE IF NOT EXISTS programme_blocks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    programme_id        UUID NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,          -- e.g. "Block A", "Lower Orchard"
    area_ha             NUMERIC,
    crop                TEXT NOT NULL,
    cultivar            TEXT,
    yield_target        NUMERIC,
    yield_unit          TEXT,
    tree_age            INTEGER,
    pop_per_ha          INTEGER,
    soil_analysis_id    UUID REFERENCES soil_analyses(id),
    feeding_plan_id     UUID REFERENCES feeding_plans(id),
    blend_group         TEXT,                   -- letter grouping for shared blends
    nutrient_targets    JSONB,                  -- cached targets from soil analysis
    notes               TEXT
);

CREATE INDEX idx_programme_blocks_programme ON programme_blocks(programme_id);

-- Programme blends: actual blend recipes linked to block groups
CREATE TABLE IF NOT EXISTS programme_blends (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    programme_id        UUID NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    blend_group         TEXT NOT NULL,           -- matches programme_blocks.blend_group
    stage_name          TEXT,
    application_month   INTEGER,
    blend_id            UUID REFERENCES blends(id),
    blend_recipe        JSONB,                   -- cached recipe snapshot
    blend_nutrients     JSONB,                   -- cached nutrient analysis
    blend_cost_per_ton  NUMERIC,
    sa_notation         TEXT,
    rate_kg_ha          NUMERIC,
    total_kg            NUMERIC,                 -- rate * sum(block areas in group)
    notes               TEXT
);

CREATE INDEX idx_programme_blends_programme ON programme_blends(programme_id);
CREATE INDEX idx_programme_blends_group ON programme_blends(programme_id, blend_group);

-- ── RLS Policies ──────────────────────────────────────────────────────

ALTER TABLE programmes ENABLE ROW LEVEL SECURITY;
ALTER TABLE programme_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE programme_blends ENABLE ROW LEVEL SECURITY;

-- Programmes: agents see own, admins see all
CREATE POLICY "programmes_agent_select" ON programmes
    FOR SELECT TO authenticated
    USING (agent_id = auth.uid() OR EXISTS (
        SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'
    ));

CREATE POLICY "programmes_agent_insert" ON programmes
    FOR INSERT TO authenticated
    WITH CHECK (agent_id = auth.uid());

CREATE POLICY "programmes_agent_update" ON programmes
    FOR UPDATE TO authenticated
    USING (agent_id = auth.uid() OR EXISTS (
        SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'
    ));

CREATE POLICY "programmes_service" ON programmes
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Blocks: follow programme ownership
CREATE POLICY "programme_blocks_select" ON programme_blocks
    FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM programmes p
        WHERE p.id = programme_blocks.programme_id
        AND (p.agent_id = auth.uid() OR EXISTS (
            SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'
        ))
    ));

CREATE POLICY "programme_blocks_service" ON programme_blocks
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Blends: follow programme ownership
CREATE POLICY "programme_blends_select" ON programme_blends
    FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM programmes p
        WHERE p.id = programme_blends.programme_id
        AND (p.agent_id = auth.uid() OR EXISTS (
            SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'
        ))
    ));

CREATE POLICY "programme_blends_service" ON programme_blends
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_programmes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER programmes_updated_at
    BEFORE UPDATE ON programmes
    FOR EACH ROW EXECUTE FUNCTION update_programmes_updated_at();

CREATE TRIGGER programme_blocks_updated_at
    BEFORE UPDATE ON programme_blocks
    FOR EACH ROW EXECUTE FUNCTION update_programmes_updated_at();

COMMENT ON TABLE programmes IS 'Full-season fertilizer programmes per client/farm';
COMMENT ON TABLE programme_blocks IS 'Individual land blocks within a programme, each with its own soil analysis and crop';
COMMENT ON TABLE programme_blends IS 'Blend recipes assigned to block groups within a programme';
