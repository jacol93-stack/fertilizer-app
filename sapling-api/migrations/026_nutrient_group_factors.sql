-- ============================================================
-- Migration 026: Nutrient-group-specific adjustment factors
--
-- Replaces blanket factors with nutrient-group-aware factors:
--   N      — always 1.0 (not bankable in soil)
--   P      — conservative reductions (slow draw-down)
--   cations — standard reductions (K, Ca, Mg, S)
--   micro  — always 1.0 (tiny quantities, not worth cutting)
-- ============================================================

-- Step 1: Add nutrient_group column
ALTER TABLE adjustment_factors
ADD COLUMN IF NOT EXISTS nutrient_group TEXT;

-- Step 2: Tag existing rows as "cations" (their values suit K/Ca/Mg/S)
UPDATE adjustment_factors
SET nutrient_group = 'cations'
WHERE nutrient_group IS NULL;

-- Step 3: Make NOT NULL
ALTER TABLE adjustment_factors
ALTER COLUMN nutrient_group SET NOT NULL;

-- Step 4: Drop old unique constraint on classification alone
ALTER TABLE adjustment_factors
DROP CONSTRAINT IF EXISTS adjustment_factors_classification_key;

-- Step 5: N group — always 1.0
INSERT INTO adjustment_factors (classification, nutrient_group, factor) VALUES
  ('Very Low',  'N', 1.0),
  ('Low',       'N', 1.0),
  ('Optimal',   'N', 1.0),
  ('High',      'N', 1.0),
  ('Very High', 'N', 1.0);

-- Step 5: P group — conservative reductions
INSERT INTO adjustment_factors (classification, nutrient_group, factor) VALUES
  ('Very Low',  'P', 1.5),
  ('Low',       'P', 1.25),
  ('Optimal',   'P', 1.0),
  ('High',      'P', 0.75),
  ('Very High', 'P', 0.5);

-- Step 6: Micro group — always 1.0
INSERT INTO adjustment_factors (classification, nutrient_group, factor) VALUES
  ('Very Low',  'micro', 1.0),
  ('Low',       'micro', 1.0),
  ('Optimal',   'micro', 1.0),
  ('High',      'micro', 1.0),
  ('Very High', 'micro', 1.0);

-- Step 7: Add composite unique constraint
ALTER TABLE adjustment_factors
ADD CONSTRAINT adjustment_factors_classification_nutrient_group_key
UNIQUE (classification, nutrient_group);
