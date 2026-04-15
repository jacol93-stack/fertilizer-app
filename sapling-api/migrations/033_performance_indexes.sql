-- 033: Performance indexes for list/search queries
--
-- Audit finding: list endpoints filter by agent_id / client_id and order by
-- created_at, but only agent_id indexes exist. Client drill-down and records
-- filtering are sequential scans on tables that grow with every analysis.
--
-- All indexes here are additive, CREATE INDEX IF NOT EXISTS, partial where
-- the query predicate is stable (excluding soft-deleted rows). Safe to drop.
--
-- Apply during a quiet window — CREATE INDEX holds an ACCESS SHARE lock
-- briefly; use CONCURRENTLY if the table is large and you can't afford the
-- blink. (Omitted here because CONCURRENTLY can't run in a transaction
-- block; run manually: CREATE INDEX CONCURRENTLY ...)

-- ── blends ────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_blends_client_id
    ON public.blends(client_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_blends_agent_created
    ON public.blends(agent_id, created_at DESC)
    WHERE deleted_at IS NULL;


-- ── soil_analyses ─────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_soil_analyses_client_id
    ON public.soil_analyses(client_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_soil_analyses_field_id
    ON public.soil_analyses(field_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_soil_analyses_agent_created
    ON public.soil_analyses(agent_id, created_at DESC)
    WHERE deleted_at IS NULL;


-- ── feeding_plans ─────────────────────────────────────────────────────────
-- Previously had no indexes at all.
CREATE INDEX IF NOT EXISTS idx_feeding_plans_agent_id
    ON public.feeding_plans(agent_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_feeding_plans_soil_analysis_id
    ON public.feeding_plans(soil_analysis_id);

CREATE INDEX IF NOT EXISTS idx_feeding_plans_created_at
    ON public.feeding_plans(created_at DESC)
    WHERE deleted_at IS NULL;


-- ── clients ───────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_clients_agent_id
    ON public.clients(agent_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_clients_deleted_at
    ON public.clients(deleted_at)
    WHERE deleted_at IS NULL;


-- ── quotes ────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_quotes_agent_status
    ON public.quotes(agent_id, status)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_quotes_client_id
    ON public.quotes(client_id)
    WHERE deleted_at IS NULL;


-- ── programmes ────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_programmes_agent_status
    ON public.programmes(agent_id, status)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_programmes_client_id
    ON public.programmes(client_id)
    WHERE deleted_at IS NULL;


-- ── material_markups ──────────────────────────────────────────────────────
-- Removed: prior draft assumed an agent_id column (per-agent pricing).
-- Schema is actually global — markups are keyed by `material` name and
-- apply to all agents. Admin-only writes. No index needed on a small
-- global table.


-- ── leaf_analyses ─────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_leaf_analyses_client_id
    ON public.leaf_analyses(client_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_leaf_analyses_agent_created
    ON public.leaf_analyses(agent_id, created_at DESC)
    WHERE deleted_at IS NULL;


-- ── audit_log ─────────────────────────────────────────────────────────────
-- For the admin audit viewer (filter by user/event_type/entity_type + date).
CREATE INDEX IF NOT EXISTS idx_audit_log_user_created
    ON public.audit_log(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity
    ON public.audit_log(entity_type, entity_id);


-- ── Rollback ──────────────────────────────────────────────────────────────
-- DROP INDEX IF EXISTS idx_blends_client_id, idx_blends_agent_created,
--    idx_soil_analyses_client_id, idx_soil_analyses_field_id,
--    idx_soil_analyses_agent_created, idx_feeding_plans_agent_id,
--    idx_feeding_plans_soil_analysis_id, idx_feeding_plans_created_at,
--    idx_clients_agent_id, idx_clients_deleted_at,
--    idx_quotes_agent_status, idx_quotes_client_id,
--    idx_programmes_agent_status, idx_programmes_client_id,
--    idx_leaf_analyses_client_id, idx_leaf_analyses_agent_created,
--    idx_audit_log_user_created, idx_audit_log_entity;
