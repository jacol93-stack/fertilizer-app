-- 088_field_history.sql
--
-- Historical Analysis tool storage. The field dashboard absorbs the
-- role of "historical analysis" — these tables let agronomists log
-- applications + management events that happened OUTSIDE a programme
-- artifact (back-fill of past seasons, ad-hoc applications, etc.).
--
-- artifact_applications already exists (migration 086) but it requires
-- artifact_id and is meant for in-season tracking against a planned
-- programme. field_applications is artifact-free + field-keyed.

BEGIN;

CREATE TABLE IF NOT EXISTS field_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    -- When the application happened (or was scheduled to happen)
    applied_date DATE NOT NULL,
    -- Product label as the agronomist wrote it ("5:1:5 (17) + Ca 4.1%",
    -- "Calcitic Lime", etc.) — free-form for historical entry.
    product_label TEXT,
    rate_kg_ha NUMERIC,
    rate_l_ha NUMERIC,
    method TEXT, -- broadcast / fertigation / foliar / band_place / etc.
    -- Captured nutrient delivery per ha — let the agronomist enter
    -- whatever they have (N, P2O5, K2O, Ca, Mg, S as kg/ha or
    -- equivalent). Stored as a JSON map so we can extend without
    -- schema churn (Zn, B, micros etc. follow the same shape).
    nutrients_kg_per_ha JSONB,
    notes TEXT,
    -- Optional link back to a programme artifact + adjustment if the
    -- application originated from a planned/recorded programme entry.
    -- Lets us merge artifact_applications + field_applications into
    -- one timeline view without duplicating rows.
    artifact_id UUID REFERENCES programme_artifacts(id) ON DELETE SET NULL,
    source TEXT NOT NULL DEFAULT 'manual', -- 'manual' | 'artifact' | 'import'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES profiles(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS field_applications_by_field
    ON field_applications (field_id, applied_date DESC);


CREATE TABLE IF NOT EXISTS field_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    -- 'cultivar_change' | 'replant' | 'pruning' | 'rootstock_change' |
    -- 'frost' | 'hail' | 'drought_stress' | 'irrigation_change' | 'other'
    event_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    -- Free-form context (old/new cultivar names, % canopy lost, etc.)
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES profiles(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS field_events_by_field
    ON field_events (field_id, event_date DESC);

COMMIT;
