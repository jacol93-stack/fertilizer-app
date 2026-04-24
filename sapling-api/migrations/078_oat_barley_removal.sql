-- Migration 078: seed Oat + Barley nutrient removal data
--
-- Two gaps addressed:
--   1. crop_requirements.Oat row exists but all removal values are 0.0 —
--      the engine was silently under-targeting Oat by treating it as if
--      it removed nothing. Oat grain removal is close to Barley in
--      per-ton terms; values below come from FERTASA Handbook §5.6
--      (small grains, oats) + ARC Small Grain Institute winter-area
--      production guidelines.
--   2. fertasa_nutrient_removal has Wheat grain/straw/total rows (Tier 1,
--      FERTASA 5.4.3) but is missing Barley + Oat entirely. This matters
--      because the hay-harvest mode (A2 follow-up) needs straw removal
--      values — cereal straw carries a lot of K (~14-16 kg K per t grain
--      produced), which is the whole reason a hay cut depletes soil K
--      far faster than a grain harvest.
--
-- Tier 1 (SA_INDUSTRY_BODY). Source: FERTASA Handbook §5.4.3 (Wheat
-- convention extended), §5.6 (small grains / oats), ARC-SGI winter
-- rainfall production guidelines 2019/2020.
--
-- Note: some of the Wheat rows existing in fertasa_nutrient_removal
-- have Ca/Mg null. This migration seeds those values for the new rows
-- (not a backfill of Wheat — separate audit task).

-- ── crop_requirements: update Oat from zeros to real values ──────────
UPDATE crop_requirements SET
  n    = 20.0,   -- kg N per t grain
  p    = 3.5,    -- kg P per t grain
  k    = 5.0,    -- kg K per t grain
  ca   = 0.6,    -- kg Ca per t grain
  mg   = 1.4,    -- kg Mg per t grain
  s    = 2.0,    -- kg S per t grain
  fe   = 0.2,
  b    = 0.015,
  mn   = 0.04,
  zn   = 0.03,
  mo   = 0.004,
  cu   = 0.007
WHERE crop = 'Oat';

-- ── fertasa_nutrient_removal: Barley + Oat (grain, straw, total) ─────
INSERT INTO fertasa_nutrient_removal (crop, plant_part, yield_unit, n, p, k, ca, mg, s, b, zn, fe, mn, cu, mo, source_section, notes) VALUES
  ('Barley', 'grain', 'kg/t grain', 22.0, 3.5, 5.0, 0.5, 1.2, 2.0, 0.02, 0.04, 0.25, 0.04, 0.008, 0.004, '5.6',
   'Grain removal per ton grain produced. FERTASA §5.6 small grains / ARC-SGI.'),
  ('Barley', 'straw', 'kg/t grain', 7.0, 1.0, 16.0, 3.5, 1.3, 1.8, NULL, NULL, NULL, NULL, NULL, NULL, '5.6',
   'Straw removal per ton grain produced. Straw is K-rich — relevant for hay-cut / whole-plant-harvest modes where straw leaves the field.'),
  ('Barley', 'total', 'kg/t grain', 29.0, 4.5, 21.0, 4.0, 2.5, 3.8, 0.02, 0.04, 0.25, 0.04, 0.008, 0.004, '5.6',
   'Grain + straw total removal per ton grain produced. Use for hay-cut / silage harvest modes.'),

  ('Oat', 'grain', 'kg/t grain', 20.0, 3.5, 5.0, 0.6, 1.4, 2.0, 0.015, 0.03, 0.20, 0.04, 0.007, 0.004, '5.6',
   'Grain removal per ton grain produced. FERTASA §5.6 small grains / ARC-SGI.'),
  ('Oat', 'straw', 'kg/t grain', 6.0, 1.0, 14.0, 3.0, 1.2, 1.5, NULL, NULL, NULL, NULL, NULL, NULL, '5.6',
   'Straw removal per ton grain produced. Oat straw is highly K-rich — relevant for hay-cut / whole-plant-harvest modes.'),
  ('Oat', 'total', 'kg/t grain', 26.0, 4.5, 19.0, 3.6, 2.6, 3.5, 0.015, 0.03, 0.20, 0.04, 0.007, 0.004, '5.6',
   'Grain + straw total removal per ton grain produced. Use for hay-cut / silage harvest modes.');
