-- ============================================================
-- 103: extend soil_analyses.composition_method with 'shared_zone'
-- ============================================================
-- Common SA orchard practice: one block is sampled and its analysis
-- is treated as representative of all blocks in the same soil zone
-- (planted contemporaneously, on the same soil mapping unit, with
-- the same management history). The row in soil_analyses is a
-- legitimate duplicate of another row, attributed to a different
-- field_id.
--
-- This is semantically distinct from the existing values:
--   single                   — one physical sample, one block
--   composite_mean           — multiple sub-samples, mean
--   composite_area_weighted  — multiple sub-samples, area-weighted
--   composite_median         — multiple sub-samples, median
--   shared_zone (new)        — duplicate of another row, no new sample
--
-- The renderer + soil-engine treat shared_zone identically to single
-- for classification, but this column lets the agronomist see at a
-- glance that the row is a copy and not a fresh lab result.
-- ============================================================

BEGIN;

ALTER TABLE public.soil_analyses
    DROP CONSTRAINT IF EXISTS chk_soil_composition_method;

ALTER TABLE public.soil_analyses
    ADD CONSTRAINT chk_soil_composition_method
    CHECK (composition_method IN (
        'single',
        'composite_mean',
        'composite_area_weighted',
        'composite_median',
        'shared_zone'
    ));

COMMENT ON COLUMN public.soil_analyses.composition_method IS
    'How the row was produced. single | composite_mean | composite_area_weighted | composite_median | shared_zone (duplicate of another block''s sample, common in SA orchards where one block represents a soil zone).';

COMMIT;
