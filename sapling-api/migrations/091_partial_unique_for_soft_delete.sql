-- 091 — Partial unique indexes for soft-delete name reuse.
--
-- Soft-deletes left the unique-name slot occupied because the original
-- UNIQUE constraints didn't know about deleted_at. Converting to
-- PARTIAL UNIQUE INDEXES filtered on deleted_at IS NULL frees the slot
-- the moment a row is soft-deleted, so agronomists can reuse names
-- without a "_old" workaround.
--
-- Already applied to production via Supabase MCP on 2026-04-28 ~15:11.
-- This file exists so a fresh DB rebuild reproduces the schema.
--
-- Done in one transaction so a failure on any one constraint rolls
-- the whole migration back; the previous constraints stay intact.

BEGIN;

ALTER TABLE public.clients DROP CONSTRAINT IF EXISTS clients_agent_id_name_key;
CREATE UNIQUE INDEX IF NOT EXISTS clients_agent_id_name_active_uniq
  ON public.clients (agent_id, name)
  WHERE deleted_at IS NULL;

ALTER TABLE public.farms DROP CONSTRAINT IF EXISTS farms_client_id_name_key;
CREATE UNIQUE INDEX IF NOT EXISTS farms_client_id_name_active_uniq
  ON public.farms (client_id, name)
  WHERE deleted_at IS NULL;

ALTER TABLE public.fields DROP CONSTRAINT IF EXISTS fields_farm_id_name_key;
CREATE UNIQUE INDEX IF NOT EXISTS fields_farm_id_name_active_uniq
  ON public.fields (farm_id, name)
  WHERE deleted_at IS NULL;

COMMIT;
