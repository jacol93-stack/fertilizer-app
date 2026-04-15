-- 030: Add source document storage to analyses
-- Stores the Supabase Storage path so agents can view/download original lab reports

ALTER TABLE soil_analyses
  ADD COLUMN IF NOT EXISTS source_document_url TEXT;

ALTER TABLE leaf_analyses
  ADD COLUMN IF NOT EXISTS source_document_url TEXT;
