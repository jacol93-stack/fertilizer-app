-- Phase 7: Leaf/sap analysis table

CREATE TABLE IF NOT EXISTS leaf_analyses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    agent_id        UUID NOT NULL REFERENCES profiles(id),
    client_id       UUID REFERENCES clients(id),
    farm_id         UUID REFERENCES farms(id),
    field_id        UUID REFERENCES fields(id),
    programme_id    UUID REFERENCES programmes(id),
    block_id        UUID REFERENCES programme_blocks(id),
    crop            TEXT NOT NULL,
    sample_part     TEXT,           -- e.g. "recently matured leaf", "fruit"
    sample_date     DATE,
    lab_name        TEXT,
    values          JSONB NOT NULL, -- {element: value} e.g. {"N": 2.5, "P": 0.18}
    classifications JSONB,          -- {element: "Sufficient"} from Fertasa norms
    recommendations JSONB,          -- generated adjustment recommendations
    foliar_recommendations JSONB,   -- recommended foliar sprays for deficiencies
    status          TEXT DEFAULT 'saved',
    notes           TEXT,
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_leaf_agent ON leaf_analyses(agent_id);
CREATE INDEX idx_leaf_programme ON leaf_analyses(programme_id);

ALTER TABLE leaf_analyses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "leaf_agent_select" ON leaf_analyses FOR SELECT TO authenticated
    USING (agent_id = auth.uid() OR EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "leaf_agent_insert" ON leaf_analyses FOR INSERT TO authenticated WITH CHECK (agent_id = auth.uid());
CREATE POLICY "leaf_service" ON leaf_analyses FOR ALL TO service_role USING (true) WITH CHECK (true);
