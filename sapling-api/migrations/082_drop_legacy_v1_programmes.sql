-- 082_drop_legacy_v1_programmes.sql
--
-- Drop the legacy v1 programme engine surface area. Everything moves to
-- the v2 ProgrammeArtifact pipeline (programme_artifacts table). Phase 4
-- of the roadmap will rebuild Season Tracker (applications + adjustments)
-- on top of v2; the v1 tables are removed in this migration.
--
-- Tables dropped:
--   programmes, programme_blocks, programme_blends,
--   programme_applications, programme_adjustments, programme_baselines,
--   feeding_plans, feeding_plan_items
--
-- External FKs cleaned up:
--   leaf_analyses.programme_id   → v1 programmes (drop column)
--   leaf_analyses.block_id       → v1 programme_blocks (drop column)
--   quotes.feeding_plan_id       → v1 feeding_plans (drop column)
--
-- Run via:
--   mcp__supabase__apply_migration  (or the SQL editor)

BEGIN;

-- 1. Drop columns on outside tables that referenced v1.
ALTER TABLE leaf_analyses DROP COLUMN IF EXISTS programme_id;
ALTER TABLE leaf_analyses DROP COLUMN IF EXISTS block_id;
ALTER TABLE quotes        DROP COLUMN IF EXISTS feeding_plan_id;

-- 2. Drop the v1 tables. CASCADE handles any remaining FK constraints
--    between them (programme_blocks.programme_id, programme_applications,
--    programme_adjustments, programme_baselines, programme_blends, etc.).
DROP TABLE IF EXISTS feeding_plan_items     CASCADE;
DROP TABLE IF EXISTS feeding_plans          CASCADE;
DROP TABLE IF EXISTS programme_applications CASCADE;
DROP TABLE IF EXISTS programme_adjustments  CASCADE;
DROP TABLE IF EXISTS programme_baselines    CASCADE;
DROP TABLE IF EXISTS programme_blends       CASCADE;
DROP TABLE IF EXISTS programme_blocks       CASCADE;
DROP TABLE IF EXISTS programmes             CASCADE;

COMMIT;
