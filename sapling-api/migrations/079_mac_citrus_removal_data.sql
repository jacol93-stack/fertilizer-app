-- Migration 079: seed Macadamia + Citrus nutrient removal data
--
-- Addresses the fertasa_nutrient_removal gaps surfaced when auditing
-- engine coverage for Muller Familie Boerdery demo prep (mac + citrus
-- programmes). Without these rows, subtract_harvested_removal does
-- nothing for either crop — the engine over-targets by the amount
-- that leaves the field at harvest.
--
-- ── Macadamia (per ton DNIS / nut-in-shell) ────────────────────────
-- Source: SAMAC Schoeman 2021 + Stephenson & Gallagher (1986)
-- Australian baseline. Two plant_parts:
--   'nuts'  — NIS only leaves the field; husks stay as mulch on-farm
--             (the common Tzaneen practice: husks dried on-farm,
--             cracked, husks returned as orchard mulch).
--   'total' — whole off-farm export including husk (DNIS farm-gate
--             after off-farm husk removal).
-- Husk:NIS mass ratio ~2:1 dry basis; husks carry significant K.
--
-- ── Citrus (per ton fruit) ────────────────────────────────────────
-- Source: FERTASA 5.7.3 + Du Plessis & Koen (1988).
-- Fruit-only removal — the rest of the tree stays. Seeded for
-- Valencia (primary SA variety); variants without overrides fall
-- through to Valencia values. Lemon + Grapefruit carry slightly
-- different removal profiles (published rates vary ±15 %) but
-- Valencia is the conservative default.

INSERT INTO fertasa_nutrient_removal (crop, plant_part, yield_unit, n, p, k, ca, mg, s, b, zn, fe, mn, cu, mo, source_section, notes) VALUES
  -- Macadamia: NIS-only removal (husks stay on farm)
  ('Macadamia', 'nuts', 'kg/t NIS', 12.0, 0.8, 8.0, 6.0, 1.0, 3.0, 0.15, 0.07, 0.35, 0.10, 0.035, 0.015, '5.8.1',
   'SAMAC Schoeman 2021 / Kleinhans: NIS-only off-farm export (husks mulched on-farm per common Tzaneen practice). Per ton NIS dry nut-in-shell.'),

  ('Macadamia', 'husk', 'kg/t NIS', 6.0, 0.4, 4.0, 4.0, 0.5, 2.0, NULL, NULL, NULL, NULL, NULL, NULL, '5.8.1',
   'Husk removal per ton NIS produced (husk:NIS mass ratio ~2:1 dry). Relevant only if husks leave the field (uncommon in SA).'),

  ('Macadamia', 'total', 'kg/t NIS', 18.0, 1.2, 12.0, 10.0, 1.5, 5.0, 0.20, 0.10, 0.50, 0.15, 0.050, 0.020, '5.8.1',
   'Full off-farm export (NIS + husk). Use when husks leave the field. Matches crop_requirements.Macadamia seasonal demand.'),

  -- Citrus (Valencia as canonical): fruit-only removal per FERTASA 5.7.3
  ('Citrus (Valencia)', 'fruit', 'kg/t fruit', 1.4, 0.18, 2.0, 0.8, 0.15, 0.10, 0.03, 0.02, 0.05, 0.02, 0.005, 0.002, '5.7.3',
   'FERTASA 5.7.3 + Du Plessis & Koen 1988: per-ton-fruit export for Valencia. Tree biomass (leaves, branches, roots) stays in orchard.'),

  -- Navel (approximately Valencia values — slight N/Ca uptick)
  ('Citrus (Navel)', 'fruit', 'kg/t fruit', 1.5, 0.20, 2.1, 0.9, 0.16, 0.11, 0.03, 0.02, 0.05, 0.02, 0.005, 0.002, '5.7.3',
   'FERTASA 5.7.3: navel has slightly higher demand than Valencia; per-ton-fruit export.'),

  -- Soft citrus (mandarins / clementines — smaller fruit, slightly higher per-ton N)
  ('Citrus (Soft Citrus)', 'fruit', 'kg/t fruit', 1.5, 0.18, 2.0, 0.8, 0.15, 0.10, 0.03, 0.02, 0.05, 0.02, 0.005, 0.002, '5.7.3',
   'FERTASA 5.7.3: soft citrus similar to Valencia per-ton basis; export-per-ton-fruit.'),

  -- Lemon (higher K removal per published literature)
  ('Citrus (Lemon)', 'fruit', 'kg/t fruit', 1.3, 0.16, 2.3, 0.9, 0.15, 0.10, 0.03, 0.02, 0.05, 0.02, 0.005, 0.002, '5.7.3',
   'FERTASA 5.7.3: lemon slightly higher K per ton fruit than oranges.'),

  -- Grapefruit (larger fruit, slightly lower N density per UF-IFAS)
  ('Citrus (Grapefruit)', 'fruit', 'kg/t fruit', 1.2, 0.15, 1.9, 0.7, 0.14, 0.09, 0.03, 0.02, 0.05, 0.02, 0.005, 0.002, '5.7.3',
   'FERTASA 5.7.3 + UF-IFAS: grapefruit ~10-15 % less N density than Valencia.')
ON CONFLICT DO NOTHING;
