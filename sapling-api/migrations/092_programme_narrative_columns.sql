-- ============================================================
-- 092: Opus narrative storage on programme_artifacts
-- ============================================================
-- Adds the columns the narrative pipeline persists to. The flow:
--   1. User clicks "Generate Narrative" on an artifact in draft state.
--   2. Backend fires Opus, validator, policeman; persists overrides +
--      report. narrative_generated_at = now(). narrative_locked_at NULL.
--   3. While narrative_locked_at IS NULL, Generate is re-runnable (fresh
--      Opus call replaces the stored overrides).
--   4. On draft → approved transition, narrative_locked_at = now().
--      From this point the narrative is immutable; PDFs render against
--      the same prose every time.
--
-- Three columns rather than embedding in the existing artifact JSONB
-- because (a) we want clean lifecycle separation between engine output
-- (immutable from build time) and narrative (mutable until approval),
-- (b) narrative_locked_at gates write access, (c) telemetry queries
-- can hit narrative_report directly without unpacking the artifact.
-- ============================================================

BEGIN;

ALTER TABLE public.programme_artifacts
    ADD COLUMN IF NOT EXISTS narrative_overrides JSONB,
    ADD COLUMN IF NOT EXISTS narrative_report JSONB,
    ADD COLUMN IF NOT EXISTS narrative_generated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS narrative_locked_at TIMESTAMPTZ;

COMMENT ON COLUMN public.programme_artifacts.narrative_overrides IS
    'Per-section Opus prose, dict of {section_id: text|list}. NULL when
     no narrative has been generated yet. Read by render_programme_pdf
     when narrative_mode="opus" — supersedes engine baseline prose.';

COMMENT ON COLUMN public.programme_artifacts.narrative_report IS
    'Verdict + issues + token telemetry from the most recent Opus run.
     Includes verdict (PASS/WARN/FAIL), issues list (severity, category,
     where, what, fix), used_opus_prose (bool), input/output/cache
     tokens, duration_seconds. Surfaced in the wizard for review.';

COMMENT ON COLUMN public.programme_artifacts.narrative_generated_at IS
    'Wall-clock timestamp of the most recent successful Opus generation.
     Updated every regenerate. NULL when no narrative exists yet.';

COMMENT ON COLUMN public.programme_artifacts.narrative_locked_at IS
    'Set on draft→approved transition when narrative_overrides is
     present. Once non-NULL the narrative is immutable; generate-
     narrative endpoint refuses with 409. PDF renders are deterministic
     from this point onward.';

COMMIT;
