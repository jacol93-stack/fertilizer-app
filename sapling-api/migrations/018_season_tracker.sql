-- Phase 6: Season Tracker — record actual applications and mid-season adjustments

CREATE TABLE IF NOT EXISTS programme_applications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    programme_id        UUID NOT NULL REFERENCES programmes(id),
    block_id            UUID NOT NULL REFERENCES programme_blocks(id),
    planned_blend_id    UUID REFERENCES programme_blends(id),
    actual_blend_id     UUID REFERENCES blends(id),
    planned_date        DATE,
    actual_date         DATE,
    planned_rate_kg_ha  NUMERIC,
    actual_rate_kg_ha   NUMERIC,
    method              TEXT,
    weather_notes       TEXT,
    notes               TEXT,
    status              TEXT DEFAULT 'pending'  -- pending, applied, skipped, partial
);

CREATE INDEX idx_prog_apps_programme ON programme_applications(programme_id);
CREATE INDEX idx_prog_apps_block ON programme_applications(block_id);

CREATE TABLE IF NOT EXISTS programme_adjustments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    programme_id    UUID NOT NULL REFERENCES programmes(id),
    block_id        UUID REFERENCES programme_blocks(id),
    trigger_type    TEXT NOT NULL,  -- leaf_analysis, observation, weather, manual
    trigger_id      UUID,          -- e.g. leaf_analysis ID
    trigger_data    JSONB,
    adjustment_data JSONB NOT NULL, -- what changed
    notes           TEXT,
    created_by      UUID NOT NULL REFERENCES profiles(id)
);

CREATE INDEX idx_prog_adj_programme ON programme_adjustments(programme_id);

-- RLS
ALTER TABLE programme_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE programme_adjustments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "prog_apps_select" ON programme_applications FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM programmes p WHERE p.id = programme_applications.programme_id
        AND (p.agent_id = auth.uid() OR EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'))));
CREATE POLICY "prog_apps_service" ON programme_applications FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "prog_adj_select" ON programme_adjustments FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM programmes p WHERE p.id = programme_adjustments.programme_id
        AND (p.agent_id = auth.uid() OR EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'))));
CREATE POLICY "prog_adj_service" ON programme_adjustments FOR ALL TO service_role USING (true) WITH CHECK (true);
