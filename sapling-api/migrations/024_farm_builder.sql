-- 024: Farm Builder — fields become single source of agronomic truth
-- Run against Supabase SQL editor

-- ── Extend fields table with agronomic columns ─────────────────────────

ALTER TABLE fields
  ADD COLUMN IF NOT EXISTS crop              TEXT,
  ADD COLUMN IF NOT EXISTS cultivar          TEXT,
  ADD COLUMN IF NOT EXISTS crop_type         TEXT,
  ADD COLUMN IF NOT EXISTS planting_date     DATE,
  ADD COLUMN IF NOT EXISTS tree_age          INTEGER,
  ADD COLUMN IF NOT EXISTS pop_per_ha        INTEGER,
  ADD COLUMN IF NOT EXISTS yield_target      NUMERIC,
  ADD COLUMN IF NOT EXISTS yield_unit        TEXT,
  ADD COLUMN IF NOT EXISTS irrigation_type   TEXT,
  ADD COLUMN IF NOT EXISTS accepted_methods  JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS fertigation_months JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS latest_analysis_id UUID REFERENCES soil_analyses(id) ON DELETE SET NULL;

-- Validate irrigation_type
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_fields_irrigation_type'
  ) THEN
    ALTER TABLE fields
      ADD CONSTRAINT chk_fields_irrigation_type
      CHECK (irrigation_type IS NULL OR irrigation_type IN ('drip', 'pivot', 'micro', 'flood', 'none'));
  END IF;
END $$;

-- Validate crop_type
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_fields_crop_type'
  ) THEN
    ALTER TABLE fields
      ADD CONSTRAINT chk_fields_crop_type
      CHECK (crop_type IS NULL OR crop_type IN ('annual', 'perennial'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_fields_crop ON fields(crop) WHERE crop IS NOT NULL;


-- ── Add field_id to programme_blocks ────────────────────────────────────

ALTER TABLE programme_blocks
  ADD COLUMN IF NOT EXISTS field_id UUID REFERENCES fields(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_programme_blocks_field ON programme_blocks(field_id) WHERE field_id IS NOT NULL;
