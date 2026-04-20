-- ============================================================
-- 052: Rate-table schema — add crop_cycle + soil organic matter filters
-- ============================================================
-- Needed for SASRI sugarcane data (IS 7.2) which keys N rates on:
--   * crop_cycle ('plant' vs 'ratoon') — sugarcane's two-phase lifecycle
--   * N-category, derived from (SOM%, clay%) jointly:
--       Cat 1: SOM < 2%, any clay
--       Cat 2: SOM 2-4%, clay < 35%
--       Cat 3: SOM 2-4%, clay ≥ 35%
--       Cat 4: SOM > 4%, any clay
--
-- Storing SOM% as its own numeric band + keeping clay_pct_min/max
-- (added in 046) lets us express all four N-categories without a
-- lookup-time "category string" mapping layer. More rows, cleaner semantics.
--
-- Both columns are nullable: existing rate-table rows continue to work
-- (NULL means "no constraint on this dimension").
-- ============================================================

BEGIN;

ALTER TABLE public.fertilizer_rate_tables
    ADD COLUMN IF NOT EXISTS crop_cycle            TEXT
        CHECK (crop_cycle IS NULL OR crop_cycle IN ('plant', 'ratoon'));

ALTER TABLE public.fertilizer_rate_tables
    ADD COLUMN IF NOT EXISTS soil_organic_matter_pct_min NUMERIC;

ALTER TABLE public.fertilizer_rate_tables
    ADD COLUMN IF NOT EXISTS soil_organic_matter_pct_max NUMERIC;

COMMENT ON COLUMN public.fertilizer_rate_tables.crop_cycle IS
    'Crop lifecycle phase (primarily sugarcane: plant vs ratoon). NULL means row applies regardless of cycle.';

COMMENT ON COLUMN public.fertilizer_rate_tables.soil_organic_matter_pct_min IS
    'Half-open SOM% band: row applies iff context.som_pct >= min. NULL = no lower bound.';

COMMENT ON COLUMN public.fertilizer_rate_tables.soil_organic_matter_pct_max IS
    'Half-open SOM% band: row applies iff context.som_pct < max. NULL = no upper bound (open top).';

COMMIT;
