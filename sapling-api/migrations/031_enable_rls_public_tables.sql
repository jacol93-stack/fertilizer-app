-- 031: Enable RLS on tables that were left public
-- Supabase flagged these as rls_disabled_in_public on 2026-04-07.
-- All access goes through sapling-api with the service role key, which
-- bypasses RLS, so enabling RLS with no policies is safe for the backend.
-- The frontend never queries these tables directly (verified: only `profiles`
-- is queried directly from sapling-web, and that already has RLS).

ALTER TABLE public.blends                     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quotes                     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quote_messages             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.soil_analyses              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.materials                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.material_markups           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.default_materials          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrient_interactions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrient_limits            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tissue_toxicity            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crop_sufficiency_overrides ENABLE ROW LEVEL SECURITY;
