-- ============================================================
-- 072: Drop empty legacy tables + mark wire-pending tables
-- ============================================================
-- Phase 0.3 of the 2026-04-23 programme-engine rebaseline. Handles
-- the remaining legacy-table decisions after 070 (canonical names)
-- and 071 (retire recommendation_tables):
--
--   * crop_application_windows — schema from migration 046, never
--     seeded, never read by engine. The season tracker + stage
--     schedule + crop_application_methods supersede this concern.
--     DROP.
--
--   * fertasa_nutrient_removal (27 rows) — has unique "kg nutrient
--     per tonne product" data for crop nutrient-balance programmes.
--     Engine doesn't read it yet. Tagged for Phase 2 wiring (target-
--     compute module should subtract harvested removal from next-
--     season targets). KEEP + comment.
--
--   * fertasa_soil_norms (26 rows) — crop-specific ideal soil param
--     targets (Macadamia pH 6.4, Ca 1500, K 260 etc.). Duplicates
--     the function of crop_sufficiency_overrides. Data merge (with
--     proper column mapping) deferred to a future focused migration;
--     table stays, tagged for that work. KEEP + comment.
--
-- Also: adds a "data_integrity_view" for CI — shows any crop-name
-- orphans across wired tables. After 070 this should return zero.
-- ============================================================

BEGIN;

-- 1. Drop the empty + unwired crop_application_windows table
DROP TABLE IF EXISTS public.crop_application_windows;

-- 2. Tag fertasa_nutrient_removal for Phase 2 wiring
COMMENT ON TABLE public.fertasa_nutrient_removal IS
    'FERTASA per-crop nutrient removal per tonne of harvested product
     (kg N/P/K/Ca/Mg/S per t grain / fruit / leaves etc.). NOT currently
     read by the engine. Phase 2 target-computation module should use
     this to feed harvested-removal subtraction (crop nutrient balance)
     when building next-season targets. 27 rows as of 2026-04-23.
     Wiring target: programme_engine.compute_season_targets().';

-- 3. Tag fertasa_soil_norms for merge-then-drop
COMMENT ON TABLE public.fertasa_soil_norms IS
    'FERTASA crop-specific ideal soil parameter targets (ideal_value
     or ideal_min/max per parameter per crop). Duplicates the function
     of crop_sufficiency_overrides. Pending data-merge migration that
     maps rows into crop_sufficiency_overrides with appropriate
     parameter+method mapping, then drops this table. 26 rows as of
     2026-04-23. DO NOT READ FROM THIS TABLE IN NEW ENGINE CODE.';

-- 4. Data-integrity view: crop-name orphans across wired tables
CREATE OR REPLACE VIEW public.v_crop_name_orphans AS
SELECT DISTINCT crop, tbl
FROM (
    SELECT crop, 'fertilizer_rate_tables' AS tbl FROM public.fertilizer_rate_tables
    UNION SELECT crop, 'crop_growth_stages' FROM public.crop_growth_stages
    UNION SELECT crop, 'crop_application_methods' FROM public.crop_application_methods
    UNION SELECT crop, 'crop_micronutrient_schedule' FROM public.crop_micronutrient_schedule
    UNION SELECT crop, 'fertasa_leaf_norms' FROM public.fertasa_leaf_norms
    UNION SELECT crop, 'fertasa_sampling_guide' FROM public.fertasa_sampling_guide
    UNION SELECT crop, 'fertasa_nutrient_removal' FROM public.fertasa_nutrient_removal
    UNION SELECT crop, 'fertasa_soil_norms' FROM public.fertasa_soil_norms
    UNION SELECT crop, 'crop_sufficiency_overrides' FROM public.crop_sufficiency_overrides
    UNION SELECT crop, 'crop_calc_flags' FROM public.crop_calc_flags
) refs
LEFT JOIN public.crop_requirements cr ON refs.crop = cr.crop
WHERE cr.crop IS NULL;

COMMENT ON VIEW public.v_crop_name_orphans IS
    'CI data-integrity check — lists any crop-name references in the
     10 wired data tables that do not resolve to crop_requirements.
     Target: 0 rows. Non-zero rows indicate new crop seeded without
     registry entry, or a rename that missed a table. Run as part of
     test suite + any migration that touches crop names.';

COMMIT;
