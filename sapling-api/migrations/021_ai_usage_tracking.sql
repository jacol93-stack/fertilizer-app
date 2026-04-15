-- AI usage tracking — cost per call, per user, with totals

CREATE TABLE IF NOT EXISTS ai_usage (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id         UUID NOT NULL REFERENCES profiles(id),
    operation       TEXT NOT NULL,       -- extract_lab, classify_leaf, etc.
    model           TEXT NOT NULL,       -- claude-sonnet-4-20250514
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    cost_usd        NUMERIC NOT NULL DEFAULT 0,  -- estimated cost
    metadata        JSONB                -- lab_name, num_samples, file_type, etc.
);

CREATE INDEX idx_ai_usage_user ON ai_usage(user_id);
CREATE INDEX idx_ai_usage_date ON ai_usage(created_at);

ALTER TABLE ai_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "ai_usage_admin_select" ON ai_usage
    FOR SELECT TO authenticated
    USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "ai_usage_service" ON ai_usage
    FOR ALL TO service_role USING (true) WITH CHECK (true);
