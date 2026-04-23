-- ============================================================
-- 073: materials.applicability + reaction_time for pre-season vs
--      in-season distinction
-- ============================================================
-- Phase 2 module 2 (pre-season) needs to distinguish:
--
--   * pre_season_only  — soil amendments applied weeks/months before
--     planting for soil chemistry change. Example: lime (3-6 months
--     for full reaction), gypsum (weeks-months for sodicity), rock
--     phosphate (slow P release).
--
--   * in_season_only — fertilisers delivered during the crop season
--     for plant nutrition. Example: water-soluble Calcium Nitrate,
--     foliar Zinc Sulphate, drip-injected MKP.
--
--   * both — products that serve either purpose depending on timing.
--     Example: Manure Compost (pre-plant for soil-building, OR
--     side-dressed for in-season slow N), single superphosphate
--     (pre-plant basal P, OR banded at planting).
--
-- Plus reaction_time_months_min/max for pre_season_only and 'both' —
-- drives the 3-mode pre-season decision:
--   Mode A: programme build_date + reaction_time < planting_date →
--           RECOMMEND application with timing
--   Mode B: programme already lists application as PreSeasonInput →
--           SUBTRACT residual contribution from season targets
--   Mode C: programme build_date too close to planting →
--           LOST OPPORTUNITY narrative (note in Outstanding Items)
--
-- Backfills the 4 known soil-amendment materials. All others default
-- to 'in_season_only' (safe — engine treats unknown as in-season).
-- ============================================================

BEGIN;

ALTER TABLE public.materials
    ADD COLUMN IF NOT EXISTS applicability TEXT NOT NULL DEFAULT 'in_season_only'
        CHECK (applicability IN ('pre_season_only', 'in_season_only', 'both'));

ALTER TABLE public.materials
    ADD COLUMN IF NOT EXISTS reaction_time_months_min NUMERIC,
    ADD COLUMN IF NOT EXISTS reaction_time_months_max NUMERIC,
    ADD COLUMN IF NOT EXISTS soil_improvement_purpose TEXT;

COMMENT ON COLUMN public.materials.applicability IS
    'When in the cropping cycle this material is used. pre_season_only =
     soil amendment applied weeks/months pre-plant. in_season_only =
     fertiliser delivered during crop. both = serves either depending on
     timing. Drives Phase 2 pre-season-module decision branches.';

COMMENT ON COLUMN public.materials.reaction_time_months_min IS
    'Minimum months from application to full chemical reaction in soil.
     Lime: ~3 months on warm acidic soils. Gypsum: ~0.5 months for Na
     displacement. NULL for in_season_only fertilisers (irrelevant).';

COMMENT ON COLUMN public.materials.reaction_time_months_max IS
    'Maximum months from application to full chemical reaction. Lime: ~6
     on cool soils with low fineness. Gypsum: ~2. Drives the lead-time
     check in pre-season recommendations.';

COMMENT ON COLUMN public.materials.soil_improvement_purpose IS
    'Free-text label for the agronomic purpose. e.g. "pH lift + Ca",
     "Na displacement + Ca + S", "P build-up + Ca". Surfaces in the
     Pre-Season Recommendations section of the Programme Artifact.';

-- ------------------------------------------------------------
-- Backfill known soil-amendment materials
-- ------------------------------------------------------------

-- Calcitic Lime — pH lift + Ca contribution
UPDATE public.materials SET
    applicability = 'pre_season_only',
    reaction_time_months_min = 3,
    reaction_time_months_max = 6,
    soil_improvement_purpose = 'pH lift via CaCO3 neutralisation; Ca contribution to base saturation; partial Al displacement on acid soils'
WHERE material = 'Calcitic Lime';

-- Dolomitic Lime — pH lift + Ca + Mg
UPDATE public.materials SET
    applicability = 'pre_season_only',
    reaction_time_months_min = 4,
    reaction_time_months_max = 8,
    soil_improvement_purpose = 'pH lift + Ca + Mg contribution. Slower-reacting than calcitic; preferred where Mg is also low'
WHERE material = 'Dolomitic Lime (Filler)';

-- Gypsum — Na displacement + Ca + S
UPDATE public.materials SET
    applicability = 'both',
    reaction_time_months_min = 0.5,
    reaction_time_months_max = 2,
    soil_improvement_purpose = 'Na displacement on sodic soils (SAR > 13); subsoil Ca + S delivery; pH-neutral (does not lift pH like lime)'
WHERE material = 'Gypsum';

-- Manure Compost — slow N + OM building
UPDATE public.materials SET
    applicability = 'both',
    reaction_time_months_min = 2,
    reaction_time_months_max = 12,
    soil_improvement_purpose = 'OM building, soil structure, slow N release (~20-30% Y1, ~70-80% by Y3). Pre-plant for full mineralisation; side-dress for in-season slow N'
WHERE material = 'Manure Compost';

-- Verification
DO $$
DECLARE
    pre_count INTEGER;
    both_count INTEGER;
    total INTEGER;
BEGIN
    SELECT COUNT(*) INTO pre_count FROM public.materials WHERE applicability = 'pre_season_only';
    SELECT COUNT(*) INTO both_count FROM public.materials WHERE applicability = 'both';
    SELECT COUNT(*) INTO total FROM public.materials;
    RAISE NOTICE '073: pre_season_only=% both=% in_season_only=% (of % total)',
                 pre_count, both_count, (total - pre_count - both_count), total;
END $$;

COMMIT;
