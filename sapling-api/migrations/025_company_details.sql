-- ============================================================
-- Migration 025: Add company_details JSONB to profiles and clients
-- Run in Supabase SQL Editor
-- ============================================================

-- Sender details (Sapling / agent businesses)
ALTER TABLE profiles
ADD COLUMN IF NOT EXISTS company_details JSONB DEFAULT '{}'::jsonb;

-- Recipient details (customers)
ALTER TABLE clients
ADD COLUMN IF NOT EXISTS company_details JSONB DEFAULT '{}'::jsonb;

-- Store recipient details on quotes (for external clients not in the system)
ALTER TABLE quotes
ADD COLUMN IF NOT EXISTS client_company_details JSONB DEFAULT '{}'::jsonb;

-- Example structure for all three:
-- {
--   "company_name": "ABC Farming (Pty) Ltd",
--   "reg_number": "2024/123456/07",
--   "vat_number": "4012345678",
--   "address": "123 Farm Road, Tzaneen, Limpopo, 0850",
--   "phone": "+27 15 307 1234",
--   "email": "info@abcfarming.co.za"
-- }
