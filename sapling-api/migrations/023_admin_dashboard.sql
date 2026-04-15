-- 023: Admin dashboard — session tracking, VPS metrics history, DB metrics RPC
-- Run against Supabase SQL editor

-- ── User sessions table ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS user_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at        TIMESTAMPTZ,
    last_heartbeat  TIMESTAMPTZ NOT NULL DEFAULT now(),
    duration_seconds INTEGER,
    ip_address      INET,
    user_agent      TEXT,
    device_type     TEXT,
    browser         TEXT,
    os              TEXT
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_started ON user_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(user_id) WHERE ended_at IS NULL;

ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "sessions_service_all" ON user_sessions
    FOR ALL TO service_role USING (true) WITH CHECK (true);


-- ── VPS metrics history table ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vps_metrics_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    cpu_percent     NUMERIC(5,2),
    memory_percent  NUMERIC(5,2),
    memory_used_mb  INTEGER,
    memory_total_mb INTEGER,
    disk_percent    NUMERIC(5,2),
    disk_used_gb    NUMERIC(8,2),
    disk_total_gb   NUMERIC(8,2),
    net_bytes_sent  BIGINT,
    net_bytes_recv  BIGINT,
    uptime_seconds  BIGINT
);

CREATE INDEX IF NOT EXISTS idx_vps_metrics_time ON vps_metrics_history(recorded_at DESC);

ALTER TABLE vps_metrics_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "vps_metrics_service_all" ON vps_metrics_history
    FOR ALL TO service_role USING (true) WITH CHECK (true);


-- ── Add last_login_at to profiles ───────────────────────────────────────

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;


-- ── DB metrics RPC function ─────────────────────────────────────────────

-- ── Stale session cleanup RPC ────────────────────────────────────────────

CREATE OR REPLACE FUNCTION cleanup_stale_sessions()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE user_sessions
    SET ended_at = last_heartbeat,
        duration_seconds = EXTRACT(EPOCH FROM last_heartbeat - started_at)::INTEGER
    WHERE ended_at IS NULL
      AND last_heartbeat < now() - interval '5 minutes';
END;
$$;


-- ── DB metrics RPC function ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_db_metrics()
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'db_size_bytes', pg_database_size(current_database()),
        'connection_count', (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()),
        'tables', (
            SELECT COALESCE(jsonb_agg(jsonb_build_object(
                'table_name', relname,
                'row_estimate', n_live_tup,
                'size_bytes', pg_total_relation_size(schemaname || '.' || relname)
            ) ORDER BY pg_total_relation_size(schemaname || '.' || relname) DESC), '[]'::jsonb)
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
        )
    ) INTO result;
    RETURN result;
END;
$$;
