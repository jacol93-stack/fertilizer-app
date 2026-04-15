-- ============================================================
-- Seed: Liquid-compatible materials with solubility data
-- Updates existing materials + inserts new ones
-- Solubility at 20C in g/L water
-- Mixing order: 1=acids first, 5=salts, 8=chelates, 10=Ca last
-- ============================================================

-- Update existing materials with liquid properties where they exist
UPDATE materials SET liquid_compatible = true, foliar_compatible = true, form = 'solid',
    solubility_20c = 316, ph_effect = 'neutral', mixing_order = 5
    WHERE material = 'Potassium Nitrate (KNO3)' OR material ILIKE '%potassium nitrate%' OR material ILIKE '%KNO3%';

UPDATE materials SET liquid_compatible = true, foliar_compatible = true, form = 'solid',
    solubility_20c = 374, ph_effect = 'acidifying', mixing_order = 4
    WHERE material ILIKE '%MAP%' OR material ILIKE '%monoammonium phosphate%';

UPDATE materials SET liquid_compatible = true, foliar_compatible = true, form = 'solid',
    solubility_20c = 1080, ph_effect = 'neutral', mixing_order = 5
    WHERE material ILIKE '%urea%';

UPDATE materials SET liquid_compatible = true, foliar_compatible = false, form = 'solid',
    solubility_20c = 1290, ph_effect = 'neutral', mixing_order = 10
    WHERE material ILIKE '%calcium nitrate%';

-- Insert liquid-specific materials that may not exist yet
INSERT INTO materials (material, type, cost_per_ton, n, p, k, ca, mg, s, fe, b, mn, zn, mo, cu, c,
    form, liquid_compatible, foliar_compatible, solubility_20c, sg, ph_effect, mixing_order, mixing_notes)
VALUES
-- Macro sources
('MKP (Monopotassium Phosphate)', 'Phosphate Source', 0, 0, 22.6, 28.2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    'solid', true, true, 230, NULL, 'acidifying', 4, 'Dissolve before adding other salts'),
('Magnesium Nitrate', 'Magnesium Source', 0, 11, 0, 0, 0, 9.5, 0, 0, 0, 0, 0, 0, 0, 0,
    'solid', true, true, 710, NULL, 'neutral', 6, NULL),
('Magnesium Sulphate (Epsom)', 'Magnesium Source', 0, 0, 0, 0, 0, 9.9, 12.75, 0, 0, 0, 0, 0, 0, 0,
    'solid', true, true, 355, NULL, 'neutral', 5, NULL),
('Potassium Sulphate (SOP)', 'Potassium Source', 0, 0, 0, 42, 0, 0, 17, 0, 0, 0, 0, 0, 0, 0,
    'solid', true, false, 111, NULL, 'neutral', 5, 'Low solubility — dissolve fully before use'),
('Calcium Chloride', 'Calcium Source', 0, 0, 0, 0, 27.8, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    'solid', true, false, 745, NULL, 'neutral', 10, 'Never mix with sulphates or phosphates'),
('Phosphoric Acid (80%)', 'Phosphate Source', 0, 0, 25.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    'liquid', true, false, NULL, 1.57, 'acidifying', 1, 'Add FIRST — acid goes in before salts'),
('Potassium Hydroxide (KOH 90%)', 'Potassium Source', 0, 0, 0, 65.8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    'solid', true, false, 1210, NULL, 'alkalizing', 2, 'Dissolve carefully — exothermic'),
-- Trace element sources
('Solubor', 'Boron Source', 0, 0, 0, 0, 0, 0, 0, 0, 20.5, 0, 0, 0, 0, 0,
    'solid', true, true, 220, NULL, 'neutral', 7, NULL),
('Boric Acid', 'Boron Source', 0, 0, 0, 0, 0, 0, 0, 0, 17.48, 0, 0, 0, 0, 0,
    'solid', true, true, 50, NULL, 'acidifying', 7, 'Low solubility — dissolve in warm water'),
('Sodium Molybdate', 'Molybdenum Source', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 39.5, 0, 0,
    'solid', true, true, 560, NULL, 'alkalizing', 7, NULL),
('Manganese Sulphate', 'Manganese Source', 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.13, 0, 0, 0, 0,
    'solid', true, true, 520, NULL, 'acidifying', 6, NULL),
('Zinc Sulphate', 'Zinc Source', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 36, 0, 0, 0,
    'solid', true, true, 580, NULL, 'acidifying', 6, NULL),
('Copper Sulphate', 'Copper Source', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.84, 0,
    'solid', true, true, 320, NULL, 'acidifying', 6, NULL),
('Ferrous Sulphate', 'Iron Source', 0, 0, 0, 0, 0, 0, 0, 34.69, 0, 0, 0, 0, 0, 0,
    'solid', true, true, 256, NULL, 'acidifying', 6, NULL),
('Iron EDTA Chelate (Fe 13%)', 'Iron Source', 0, 0, 0, 0, 0, 0, 0, 13, 0, 0, 0, 0, 0, 0,
    'chelate', true, true, 100, NULL, 'neutral', 8, 'Add after all salts dissolved'),
('Zinc Oxide', 'Zinc Source', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 78.6, 0, 0, 0,
    'solid', false, true, 0, NULL, 'alkalizing', 6, 'Insoluble — for suspension sprays only'),
('Copper Oxy Chloride', 'Copper Source', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 50, 0,
    'solid', false, true, 0, NULL, 'neutral', 6, 'Insoluble — for suspension sprays only'),
('Librel BMX (Trace Mix)', 'Trace Element Mix', 0, 0, 0, 0, 0, 0, 0, 3.35, 0.87, 1.7, 0.6, 0.028, 1.7, 0,
    'chelate', true, true, 80, NULL, 'neutral', 8, 'Chelated multi-trace — add last'),
('Hygroplex (Microplex)', 'Trace Element Mix', 0, 0, 0, 0, 0, 0, 0, 8.4, 2.5, 2, 1, 0.25, 0.159, 0,
    'chelate', true, true, 80, NULL, 'neutral', 8, 'Chelated multi-trace — add last'),
('Citric Acid', 'pH Adjuster', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    'solid', true, true, 730, NULL, 'acidifying', 3, 'pH buffer — add early'),
('Ammonium Sulphate', 'Nitrogen Source', 0, 21.1, 0, 0, 0, 0, 18.4, 0, 0, 0, 0, 0, 0, 0,
    'solid', true, true, 754, NULL, 'acidifying', 5, NULL)
ON CONFLICT (material) DO UPDATE SET
    form = EXCLUDED.form,
    liquid_compatible = EXCLUDED.liquid_compatible,
    foliar_compatible = EXCLUDED.foliar_compatible,
    solubility_20c = EXCLUDED.solubility_20c,
    sg = EXCLUDED.sg,
    ph_effect = EXCLUDED.ph_effect,
    mixing_order = EXCLUDED.mixing_order,
    mixing_notes = EXCLUDED.mixing_notes;

-- ── Key compatibility rules ────────────────────────────────────────────
-- Calcium + Sulphate = gypsum precipitate
-- Calcium + Phosphate = calcium phosphate precipitate

INSERT INTO material_compatibility (material_a, material_b, compatible, severity, reason) VALUES
('Calcium Nitrate', 'Magnesium Sulphate (Epsom)', false, 'incompatible', 'Forms calcium sulphate (gypsum) precipitate'),
('Calcium Nitrate', 'Potassium Sulphate (SOP)', false, 'incompatible', 'Forms calcium sulphate (gypsum) precipitate'),
('Calcium Nitrate', 'Ammonium Sulphate', false, 'incompatible', 'Forms calcium sulphate precipitate'),
('Calcium Nitrate', 'Manganese Sulphate', false, 'incompatible', 'Forms calcium sulphate precipitate'),
('Calcium Nitrate', 'Zinc Sulphate', false, 'incompatible', 'Forms calcium sulphate precipitate'),
('Calcium Nitrate', 'Copper Sulphate', false, 'incompatible', 'Forms calcium sulphate precipitate'),
('Calcium Nitrate', 'Ferrous Sulphate', false, 'incompatible', 'Forms calcium sulphate precipitate'),
('Calcium Nitrate', 'MAP (Monoammonium Phosphate)', false, 'incompatible', 'Forms calcium phosphate precipitate'),
('Calcium Nitrate', 'MKP (Monopotassium Phosphate)', false, 'incompatible', 'Forms calcium phosphate precipitate'),
('Calcium Nitrate', 'Phosphoric Acid (80%)', false, 'incompatible', 'Forms calcium phosphate precipitate'),
('Calcium Chloride', 'Magnesium Sulphate (Epsom)', false, 'incompatible', 'Forms calcium sulphate precipitate'),
('Calcium Chloride', 'Potassium Sulphate (SOP)', false, 'incompatible', 'Forms calcium sulphate precipitate'),
('Calcium Chloride', 'MAP (Monoammonium Phosphate)', false, 'incompatible', 'Forms calcium phosphate precipitate'),
('Calcium Chloride', 'MKP (Monopotassium Phosphate)', false, 'incompatible', 'Forms calcium phosphate precipitate'),
('Calcium Chloride', 'Phosphoric Acid (80%)', false, 'incompatible', 'Forms calcium phosphate precipitate'),
-- Iron chelates degrade with phosphate at low pH
('Iron EDTA Chelate (Fe 13%)', 'Phosphoric Acid (80%)', false, 'caution', 'Iron chelate may degrade at low pH with phosphate')
ON CONFLICT (material_a, material_b) DO NOTHING;
