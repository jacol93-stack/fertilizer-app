-- 034: RLS policies for tables left bare by migration 031
--
-- Migration 031 enabled RLS on 11 tables but wrote zero policies, relying
-- on the backend's service_role key to bypass RLS entirely. This works
-- today because the frontend only queries `profiles` directly — but it is
-- a single-point-of-failure: any future feature that wires sapling-web's
-- Supabase client to these tables (or any key leak) has no second line of
-- defense.
--
-- This migration adds least-privilege policies:
--   - service_role: full access (backend keeps working unchanged)
--   - authenticated agents: scoped per-table (own rows, or shared refs)
--   - admins: full access via role check against profiles
--
-- Pattern used throughout:
--   CREATE POLICY "<table>_service" FOR ALL TO service_role USING (true);
--   CREATE POLICY "<table>_admin"   FOR ALL TO authenticated USING (is_admin());
--   CREATE POLICY "<table>_agent"   FOR <action> TO authenticated USING (agent_id = auth.uid());
--
-- All CREATE POLICY statements are wrapped in DROP POLICY IF EXISTS so
-- re-running is safe.

-- ── Helper: is_admin() ────────────────────────────────────────────────────
-- Wraps the common "check my own profile" pattern so every policy is a
-- one-liner. SECURITY DEFINER lets it read profiles without hitting RLS
-- on that table. Marked STABLE so the planner can cache results inside a
-- single statement.

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid() AND role = 'admin'
    );
$$;

GRANT EXECUTE ON FUNCTION public.is_admin() TO authenticated;


-- ═══ USER-DATA TABLES (row-level agent isolation) ═════════════════════════

-- ── blends ────────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "blends_service"      ON public.blends;
DROP POLICY IF EXISTS "blends_admin"        ON public.blends;
DROP POLICY IF EXISTS "blends_agent_select" ON public.blends;
DROP POLICY IF EXISTS "blends_agent_insert" ON public.blends;
DROP POLICY IF EXISTS "blends_agent_update" ON public.blends;
DROP POLICY IF EXISTS "blends_agent_delete" ON public.blends;

CREATE POLICY "blends_service" ON public.blends
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "blends_admin" ON public.blends
    FOR ALL TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

CREATE POLICY "blends_agent_select" ON public.blends
    FOR SELECT TO authenticated
    USING (agent_id = auth.uid());

CREATE POLICY "blends_agent_insert" ON public.blends
    FOR INSERT TO authenticated
    WITH CHECK (agent_id = auth.uid());

CREATE POLICY "blends_agent_update" ON public.blends
    FOR UPDATE TO authenticated
    USING (agent_id = auth.uid())
    WITH CHECK (agent_id = auth.uid());

CREATE POLICY "blends_agent_delete" ON public.blends
    FOR DELETE TO authenticated
    USING (agent_id = auth.uid());


-- ── soil_analyses ─────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "soil_service"      ON public.soil_analyses;
DROP POLICY IF EXISTS "soil_admin"        ON public.soil_analyses;
DROP POLICY IF EXISTS "soil_agent_select" ON public.soil_analyses;
DROP POLICY IF EXISTS "soil_agent_insert" ON public.soil_analyses;
DROP POLICY IF EXISTS "soil_agent_update" ON public.soil_analyses;
DROP POLICY IF EXISTS "soil_agent_delete" ON public.soil_analyses;

CREATE POLICY "soil_service" ON public.soil_analyses
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "soil_admin" ON public.soil_analyses
    FOR ALL TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

CREATE POLICY "soil_agent_select" ON public.soil_analyses
    FOR SELECT TO authenticated
    USING (agent_id = auth.uid());

CREATE POLICY "soil_agent_insert" ON public.soil_analyses
    FOR INSERT TO authenticated
    WITH CHECK (agent_id = auth.uid());

CREATE POLICY "soil_agent_update" ON public.soil_analyses
    FOR UPDATE TO authenticated
    USING (agent_id = auth.uid())
    WITH CHECK (agent_id = auth.uid());

CREATE POLICY "soil_agent_delete" ON public.soil_analyses
    FOR DELETE TO authenticated
    USING (agent_id = auth.uid());


-- ── quotes ────────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "quotes_service"      ON public.quotes;
DROP POLICY IF EXISTS "quotes_admin"        ON public.quotes;
DROP POLICY IF EXISTS "quotes_agent_select" ON public.quotes;
DROP POLICY IF EXISTS "quotes_agent_insert" ON public.quotes;
DROP POLICY IF EXISTS "quotes_agent_update" ON public.quotes;
DROP POLICY IF EXISTS "quotes_agent_delete" ON public.quotes;

CREATE POLICY "quotes_service" ON public.quotes
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "quotes_admin" ON public.quotes
    FOR ALL TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

CREATE POLICY "quotes_agent_select" ON public.quotes
    FOR SELECT TO authenticated
    USING (agent_id = auth.uid());

CREATE POLICY "quotes_agent_insert" ON public.quotes
    FOR INSERT TO authenticated
    WITH CHECK (agent_id = auth.uid());

CREATE POLICY "quotes_agent_update" ON public.quotes
    FOR UPDATE TO authenticated
    USING (agent_id = auth.uid())
    WITH CHECK (agent_id = auth.uid());

CREATE POLICY "quotes_agent_delete" ON public.quotes
    FOR DELETE TO authenticated
    USING (agent_id = auth.uid());


-- ── quote_messages ────────────────────────────────────────────────────────
-- Messages inherit visibility from the parent quote. An agent can see
-- messages for any quote they own.
DROP POLICY IF EXISTS "quote_msgs_service" ON public.quote_messages;
DROP POLICY IF EXISTS "quote_msgs_admin"   ON public.quote_messages;
DROP POLICY IF EXISTS "quote_msgs_agent"   ON public.quote_messages;

CREATE POLICY "quote_msgs_service" ON public.quote_messages
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "quote_msgs_admin" ON public.quote_messages
    FOR ALL TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());

CREATE POLICY "quote_msgs_agent" ON public.quote_messages
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.quotes q
            WHERE q.id = quote_messages.quote_id
              AND q.agent_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.quotes q
            WHERE q.id = quote_messages.quote_id
              AND q.agent_id = auth.uid()
        )
    );


-- ── material_markups ──────────────────────────────────────────────────────
-- GLOBAL pricing table, keyed by `material` name — not per-agent. All
-- authenticated users can read; only admins (and service role) can write.
-- Earlier draft assumed an agent_id column — the real schema has no such
-- column, so those policies were rewritten as shared-read / admin-write.
DROP POLICY IF EXISTS "markups_service"      ON public.material_markups;
DROP POLICY IF EXISTS "markups_admin"        ON public.material_markups;
DROP POLICY IF EXISTS "markups_select"       ON public.material_markups;
DROP POLICY IF EXISTS "markups_agent_select" ON public.material_markups;  -- legacy cleanup

CREATE POLICY "markups_service" ON public.material_markups
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "markups_select" ON public.material_markups
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "markups_admin" ON public.material_markups
    FOR ALL TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());


-- ═══ SHARED REFERENCE TABLES (read to all, write to admin) ═══════════════

-- ── materials ─────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "materials_service" ON public.materials;
DROP POLICY IF EXISTS "materials_select"  ON public.materials;
DROP POLICY IF EXISTS "materials_admin"   ON public.materials;

CREATE POLICY "materials_service" ON public.materials
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "materials_select" ON public.materials
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "materials_admin" ON public.materials
    FOR ALL TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());


-- ── default_materials ─────────────────────────────────────────────────────
DROP POLICY IF EXISTS "default_materials_service" ON public.default_materials;
DROP POLICY IF EXISTS "default_materials_select"  ON public.default_materials;
DROP POLICY IF EXISTS "default_materials_admin"   ON public.default_materials;

CREATE POLICY "default_materials_service" ON public.default_materials
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "default_materials_select" ON public.default_materials
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "default_materials_admin" ON public.default_materials
    FOR ALL TO authenticated
    USING (public.is_admin())
    WITH CHECK (public.is_admin());


-- ── nutrient_interactions / nutrient_limits / tissue_toxicity ────────────
-- All three are reference-data tables used by the engine.

DROP POLICY IF EXISTS "nutrient_interactions_service" ON public.nutrient_interactions;
DROP POLICY IF EXISTS "nutrient_interactions_select"  ON public.nutrient_interactions;
DROP POLICY IF EXISTS "nutrient_interactions_admin"   ON public.nutrient_interactions;

CREATE POLICY "nutrient_interactions_service" ON public.nutrient_interactions
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "nutrient_interactions_select" ON public.nutrient_interactions
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "nutrient_interactions_admin" ON public.nutrient_interactions
    FOR ALL TO authenticated
    USING (public.is_admin()) WITH CHECK (public.is_admin());


DROP POLICY IF EXISTS "nutrient_limits_service" ON public.nutrient_limits;
DROP POLICY IF EXISTS "nutrient_limits_select"  ON public.nutrient_limits;
DROP POLICY IF EXISTS "nutrient_limits_admin"   ON public.nutrient_limits;

CREATE POLICY "nutrient_limits_service" ON public.nutrient_limits
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "nutrient_limits_select" ON public.nutrient_limits
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "nutrient_limits_admin" ON public.nutrient_limits
    FOR ALL TO authenticated
    USING (public.is_admin()) WITH CHECK (public.is_admin());


DROP POLICY IF EXISTS "tissue_toxicity_service" ON public.tissue_toxicity;
DROP POLICY IF EXISTS "tissue_toxicity_select"  ON public.tissue_toxicity;
DROP POLICY IF EXISTS "tissue_toxicity_admin"   ON public.tissue_toxicity;

CREATE POLICY "tissue_toxicity_service" ON public.tissue_toxicity
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "tissue_toxicity_select" ON public.tissue_toxicity
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "tissue_toxicity_admin" ON public.tissue_toxicity
    FOR ALL TO authenticated
    USING (public.is_admin()) WITH CHECK (public.is_admin());


-- ── crop_sufficiency_overrides ────────────────────────────────────────────
DROP POLICY IF EXISTS "crop_suf_service" ON public.crop_sufficiency_overrides;
DROP POLICY IF EXISTS "crop_suf_select"  ON public.crop_sufficiency_overrides;
DROP POLICY IF EXISTS "crop_suf_admin"   ON public.crop_sufficiency_overrides;

CREATE POLICY "crop_suf_service" ON public.crop_sufficiency_overrides
    FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "crop_suf_select" ON public.crop_sufficiency_overrides
    FOR SELECT TO authenticated USING (true);
CREATE POLICY "crop_suf_admin" ON public.crop_sufficiency_overrides
    FOR ALL TO authenticated
    USING (public.is_admin()) WITH CHECK (public.is_admin());


-- ── Rollback ──────────────────────────────────────────────────────────────
-- To remove all policies created by this migration:
--   DROP POLICY IF EXISTS <name> ON <table>;    -- for each name above
--   DROP FUNCTION IF EXISTS public.is_admin();
-- (The underlying ENABLE ROW LEVEL SECURITY from 031 will remain — tables
-- will then block all non-service-role access, which matches the state
-- prior to this migration.)
