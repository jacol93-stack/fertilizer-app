-- Lab templates for AI-powered soil report extraction
-- Self-learning: field mappings improve with each user correction

CREATE TABLE IF NOT EXISTS lab_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lab_name        TEXT NOT NULL UNIQUE,
    field_mappings  JSONB NOT NULL DEFAULT '{}',
    sample_count    INTEGER DEFAULT 0,
    last_used       TIMESTAMPTZ,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RLS: all authenticated users can read templates, only service role can write
ALTER TABLE lab_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "lab_templates_select" ON lab_templates
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "lab_templates_service" ON lab_templates
    FOR ALL TO service_role USING (true) WITH CHECK (true);

COMMENT ON TABLE lab_templates IS 'Self-learning lab report extraction templates. Each lab accumulates field mappings from user corrections.';
