-- 089_soft_delete_columns.sql
-- Adds deleted_at + deleted_by to farms, fields, yield_records,
-- field_crop_history, field_applications, field_events so non-admin
-- DELETE becomes soft-delete and admins can restore. Mirrors the
-- existing soil_analyses / leaf_analyses pattern.

BEGIN;

ALTER TABLE farms
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES profiles(id) ON DELETE SET NULL;

ALTER TABLE fields
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES profiles(id) ON DELETE SET NULL;

ALTER TABLE yield_records
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES profiles(id) ON DELETE SET NULL;

ALTER TABLE field_crop_history
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES profiles(id) ON DELETE SET NULL;

ALTER TABLE field_applications
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES profiles(id) ON DELETE SET NULL;

ALTER TABLE field_events
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES profiles(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS farms_deleted_at_idx ON farms (deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS fields_deleted_at_idx ON fields (deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS yield_records_deleted_at_idx ON yield_records (deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS field_crop_history_deleted_at_idx ON field_crop_history (deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS field_applications_deleted_at_idx ON field_applications (deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS field_events_deleted_at_idx ON field_events (deleted_at) WHERE deleted_at IS NOT NULL;

COMMIT;
