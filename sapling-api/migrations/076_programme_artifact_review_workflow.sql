-- Migration 076: agronomist review workflow columns on programme_artifacts
--
-- When an artifact goes from draft → approved, record who reviewed
-- it, when, and any notes (e.g. "K reduced 15% — Ca:K ratio already
-- adequate per leaf norms"). Surfaced in the UI + the farmer-facing
-- PDF so the reviewer attribution travels with the programme.
--
-- Additive, nullable columns — existing rows stay valid.

ALTER TABLE programme_artifacts
ADD COLUMN IF NOT EXISTS reviewer_id uuid REFERENCES profiles(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS reviewer_notes text,
ADD COLUMN IF NOT EXISTS reviewed_at timestamptz;

COMMENT ON COLUMN programme_artifacts.reviewer_id IS
'Profile id of the agronomist who reviewed + approved this artifact. Set on draft→approved transition.';
COMMENT ON COLUMN programme_artifacts.reviewer_notes IS
'Free-text notes the reviewer wants attached to the artifact. Optional.';
COMMENT ON COLUMN programme_artifacts.reviewed_at IS
'Timestamp of the approve-state transition.';
