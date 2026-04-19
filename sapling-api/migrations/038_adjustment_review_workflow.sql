-- ============================================================
-- Season tracker — adjustment review workflow
-- ============================================================
-- programme_adjustments today has no lifecycle state. The tracker
-- needs three lifecycle stages so the agronomist can review before
-- applying:
--
--   suggested  — system proposed it (from new soil/leaf data)
--   approved   — agronomist confirmed but blends not yet updated
--   applied    — shift has been written into programme_blends
--   rejected   — agronomist dismissed it
--
-- Existing rows were created by the manual "create_adjustment"
-- endpoint and applied immediately — default those to 'applied'
-- so nothing is retroactively pulled back into a review queue.
-- ============================================================

BEGIN;

-- Status lifecycle
ALTER TABLE programme_adjustments
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'applied',
    ADD COLUMN IF NOT EXISTS applied_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS applied_by UUID REFERENCES profiles(id),
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES profiles(id);

-- Guard against typos downstream
ALTER TABLE programme_adjustments
    DROP CONSTRAINT IF EXISTS chk_prog_adj_status;
ALTER TABLE programme_adjustments
    ADD CONSTRAINT chk_prog_adj_status
    CHECK (status IN ('suggested', 'approved', 'applied', 'rejected'));

-- Existing manually-created adjustments retroactively: treat as applied
UPDATE programme_adjustments
SET status = 'applied',
    applied_at = COALESCE(applied_at, created_at)
WHERE status IS NULL OR status = 'applied';

-- Fast path for workbench "programmes needing review" card
CREATE INDEX IF NOT EXISTS idx_prog_adj_programme_status
    ON programme_adjustments(programme_id, status);

-- And for "what triggered this adjustment" lookups from the tracker
CREATE INDEX IF NOT EXISTS idx_prog_adj_trigger
    ON programme_adjustments(trigger_type, trigger_id)
    WHERE trigger_id IS NOT NULL;

COMMIT;
