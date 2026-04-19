-- ============================================================
-- Multi-sample aggregation on soil_analyses
-- ============================================================
-- A block is often sampled at multiple zones, depths, or replicates
-- for statistical reliability. Previously the app flattened those
-- into one arithmetic mean at upload time and discarded the
-- components, so downstream consumers could not tell one sample
-- from five averaged, could not re-aggregate after dropping an
-- outlier, and could not add a fourth sample later.
--
-- This migration adds non-destructive retention:
--   component_samples   — the raw samples that produced this record
--   composition_method  — how they were combined
--   replicate_count     — convenience n (length of component_samples)
--   aggregation_stats   — per-parameter variance / CV / outlier flags
--
-- Existing rows keep working unchanged: `composition_method` defaults
-- to 'single' and `replicate_count` to 1 via column defaults, so no
-- backfill write is required. Read paths that encounter
-- `component_samples IS NULL` should treat the record as a single
-- sample.
-- ============================================================

BEGIN;

ALTER TABLE soil_analyses
    ADD COLUMN IF NOT EXISTS component_samples   JSONB,
    ADD COLUMN IF NOT EXISTS composition_method  TEXT NOT NULL DEFAULT 'single',
    ADD COLUMN IF NOT EXISTS replicate_count     INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS aggregation_stats   JSONB;

ALTER TABLE soil_analyses
    DROP CONSTRAINT IF EXISTS chk_soil_composition_method;
ALTER TABLE soil_analyses
    ADD CONSTRAINT chk_soil_composition_method
    CHECK (composition_method IN (
        'single',
        'composite_mean',
        'composite_area_weighted',
        'composite_median'
    ));

ALTER TABLE soil_analyses
    DROP CONSTRAINT IF EXISTS chk_soil_replicate_count;
ALTER TABLE soil_analyses
    ADD CONSTRAINT chk_soil_replicate_count
    CHECK (replicate_count >= 1);

-- Index the composite methods only — single-sample rows dominate and
-- don't need to be in this index.
CREATE INDEX IF NOT EXISTS idx_soil_analyses_composite
    ON soil_analyses (composition_method)
    WHERE composition_method <> 'single';

COMMENT ON COLUMN soil_analyses.component_samples IS
    'Array of raw samples that produced this record. Each entry: '
    '{values: {parameter: number}, weight_ha?: number, location_label?: text, depth_cm?: number}. '
    'NULL for legacy/single-sample records.';
COMMENT ON COLUMN soil_analyses.composition_method IS
    'How component samples were combined. single | composite_mean | composite_area_weighted | composite_median.';
COMMENT ON COLUMN soil_analyses.replicate_count IS
    'Number of component samples. 1 for single-sample records.';
COMMENT ON COLUMN soil_analyses.aggregation_stats IS
    'Per-parameter stats from the aggregation primitive: '
    '{parameter: {n, mean, variance, cv_pct, outlier_sample_indices}}. '
    'Also includes top-level {weight_strategy} (area_weighted | equal).';

COMMIT;
