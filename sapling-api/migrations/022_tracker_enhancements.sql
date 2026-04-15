-- 022: Add product tracking fields to programme_applications
-- Supports: product name/type recording, competitor product detection

ALTER TABLE programme_applications
  ADD COLUMN IF NOT EXISTS product_name TEXT,
  ADD COLUMN IF NOT EXISTS product_type TEXT,
  ADD COLUMN IF NOT EXISTS is_sapling_product BOOLEAN DEFAULT true;
