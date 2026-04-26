-- 086_season_tracker_v2.sql
--
-- Season Tracker rebuilt on v2 ProgrammeArtifact. The v1 tables we
-- dropped in migration 082 (programme_applications + programme_adjustments)
-- referenced programmes(id) and programme_blocks(id); these new tables
-- reference programme_artifacts(id) directly and use the artifact's
-- soil_snapshots[].block_id for block correlation (a string, not an FK,
-- because the v2 artifact JSON owns its own block identifiers).
--
-- Two surfaces:
--   artifact_applications  — what the farmer actually applied (vs the
--                            artifact's planned blends.applications[])
--   artifact_adjustments   — proposed mid-season changes (leaf analysis
--                            triggered, off-schedule application, etc.)
--                            agronomist reviews + approves before they
--                            shift the active programme.

BEGIN;

CREATE TABLE IF NOT EXISTS artifact_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES programme_artifacts(id) ON DELETE CASCADE,
    -- block_id is a STRING from the artifact's soil_snapshots[].block_id;
    -- not an FK because artifacts own their block identifiers.
    block_id TEXT NOT NULL,
    -- Optional: link to a specific Blend in the artifact's blends[] by
    -- composite key (stage_number + method.kind). Stored as freeform
    -- text so artifact JSON renames don't orphan tracking rows.
    planned_blend_ref TEXT,
    -- When the application actually happened
    actual_date DATE NOT NULL,
    -- What was actually applied (free-form for now; rich blend
    -- structure deferred to Phase 5 once we trust the simpler shape)
    product_label TEXT,             -- e.g. "5:1:5 (17) + Ca 4.1%"
    rate_kg_ha NUMERIC,
    rate_l_ha NUMERIC,              -- for fertigation
    method TEXT,                    -- broadcast / fertigation / foliar / etc.
    notes TEXT,
    -- Variance flag: did it match the plan? Computed at insert time
    -- by the backend (within ±10% rate, within ±2 weeks of planned date).
    variance_flag TEXT,             -- 'on_plan' | 'off_plan' | 'unscheduled'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES profiles(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS artifact_applications_by_artifact
    ON artifact_applications (artifact_id, actual_date DESC);
CREATE INDEX IF NOT EXISTS artifact_applications_by_block
    ON artifact_applications (artifact_id, block_id);


CREATE TABLE IF NOT EXISTS artifact_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES programme_artifacts(id) ON DELETE CASCADE,
    block_id TEXT,
    -- What triggered the proposal
    trigger_type TEXT NOT NULL,     -- 'leaf_analysis' | 'soil_analysis' | 'off_programme' | 'manual'
    trigger_ref TEXT,               -- id of the leaf/soil row that triggered, if applicable
    -- Free-form proposal text (Phase 4 will replace with structured
    -- nutrient deltas once the engine knows how to consume them)
    proposal TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info', -- 'info' | 'warn' | 'critical'
    -- Lifecycle
    status TEXT NOT NULL DEFAULT 'suggested', -- 'suggested' | 'approved' | 'rejected' | 'applied'
    reviewed_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    reviewer_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES profiles(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS artifact_adjustments_by_artifact
    ON artifact_adjustments (artifact_id, status, created_at DESC);

COMMIT;
