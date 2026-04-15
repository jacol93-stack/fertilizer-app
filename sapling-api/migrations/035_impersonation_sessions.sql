-- 035: Impersonation session tracking
--
-- Audit finding: auth.py stores impersonation sessions in a process-local
-- dict (_impersonation_sessions). This means:
--   - Session state is lost on every app restart
--   - Horizontally scaled workers each have their own view (inconsistent timeouts)
--   - There is no audit trail of past impersonation events beyond the
--     per-event audit_log entry (no duration, no end-time, no IP trail)
--
-- This migration creates a durable table. auth.py is updated in the same
-- patch to read/write against it.
--
-- The impersonation timeout is also tightened from 60 minutes to 15 in the
-- auth.py change — 60 minutes is too long for a sensitive, footgun-capable
-- capability like viewing another user's data.

CREATE TABLE IF NOT EXISTS public.impersonation_sessions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id     UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    target_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at   TIMESTAMPTZ NOT NULL,
    ended_at     TIMESTAMPTZ,
    end_reason   TEXT,  -- "expired" | "manual" | "admin_logout"
    ip_address   INET,
    user_agent   TEXT,

    CONSTRAINT chk_imp_duration CHECK (ended_at IS NULL OR ended_at >= started_at),
    CONSTRAINT chk_imp_expires  CHECK (expires_at > started_at)
);

-- Fast lookups by admin (the common query: "does this admin have an active session?")
CREATE INDEX IF NOT EXISTS idx_imp_admin_active
    ON public.impersonation_sessions(admin_id)
    WHERE ended_at IS NULL;

-- Secondary: audit search by target user
CREATE INDEX IF NOT EXISTS idx_imp_target
    ON public.impersonation_sessions(target_id, started_at DESC);

-- RLS: only service_role (backend) and admins can see impersonation history.
-- Targets deliberately CANNOT see that they were impersonated — that is the
-- admin's job to disclose (or not). If you later want to surface this to
-- users, add a "target_select" policy with target_id = auth.uid().
ALTER TABLE public.impersonation_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "imp_service" ON public.impersonation_sessions;
DROP POLICY IF EXISTS "imp_admin"   ON public.impersonation_sessions;

CREATE POLICY "imp_service" ON public.impersonation_sessions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "imp_admin" ON public.impersonation_sessions
    FOR SELECT TO authenticated
    USING (public.is_admin());

-- Rollback:
--   DROP TABLE IF EXISTS public.impersonation_sessions CASCADE;
