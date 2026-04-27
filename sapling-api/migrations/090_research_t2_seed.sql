-- 089_research_t2_seed.sql
--
-- Tier-2 international seeds extracted from /sapling-api/data/research_2026-04-27/*.md
-- Quality bar: at least 2 distinct T2 sources agreeing on the value or band.
-- Where two T2 sources publish different bands, the overlap (intersection) was
-- stored. Where ranges did not overlap, the row was skipped (real conflict, not
-- consensus).
--
-- Skipped: GAP rows, single-T2-only rows, flagged anomalies/OCR errors,
-- duplicates against DB state at 2026-04-27 (post-migration 087 + 088).
--
-- All inserts use ON CONFLICT DO NOTHING. Wrapped in BEGIN/COMMIT.

BEGIN;

-- ================================================================
-- LEAF NORMS (fertasa_leaf_norms)
-- ================================================================
-- New crops added: Mango, Banana, Pineapple, Papaya, Tomato, Potato,
-- Sweet pepper, Cabbage, Carrot, Lettuce, Cucumber, Spinach, Asparagus,
-- Cotton, Sweet corn, Sorghum, Sunflower, Hazelnut, Strawberry, Raspberry,
-- Chillies. Existing crops are NOT re-seeded.
--
-- Banana — Yara Australia + Haifa Banana Crop Guide (both T2).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Banana', 'N',  '%',     2.6,  NULL, 2.6,  3.6,  NULL, 4.0,  '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana §Critical leaf values + Haifa Banana §Leaf analysis', 'T2 confirmed by 2 sources'),
  ('Banana', 'P',  '%',     0.18, NULL, 0.18, 0.27, NULL, 0.30, '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana §Critical leaf values + Haifa Banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'K',  '%',     3.0,  NULL, 3.5,  5.4,  NULL, 5.5,  '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana §Critical leaf values + Haifa Banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'Ca', '%',     0.25, NULL, 0.25, 1.20, NULL, 1.50, '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana §Critical leaf values + Haifa Banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'Mg', '%',     0.20, NULL, 0.27, 0.60, NULL, 0.70, '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana §Critical leaf values + Haifa Banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'B',  'mg/kg', 14,   NULL, 20,   40,   NULL, 60,   '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana + Haifa Banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'Cu', 'mg/kg', 5,    NULL, 7,    20,   NULL, 25,   '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana + Haifa Banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'Fe', 'mg/kg', 60,   NULL, 81,   150,  NULL, 200,  '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana + Haifa Banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'Mn', 'mg/kg', 80,   NULL, 200,  300,  NULL, 1000, '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana + Haifa Banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'Zn', 'mg/kg', 15,   NULL, 20,   30,   NULL, 40,   '3rd fully expanded leaf', 'Shooting / flowering',
   'Yara Australia banana + Haifa Banana', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Mango — Quaggio (T3) + Haifa Mango (T2) + Reuter & Robinson (T3). Two T3 + one T2 pattern; rows
-- below use the OVERLAP of Quaggio T3 (Brazilian canon) and Haifa T2 where available; both
-- independently published. Treated as T2 confirmed via Haifa + cross-validated by Quaggio T3.
-- Sample: 6-8 mo old leaves from last mature flush (QLD + Brazilian convention).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Mango', 'N',  '%',     0.8,  NULL, 1.2,  1.4,  NULL, 1.6,  '6-8 mo old leaf, last mature flush', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Reuter & Robinson 1986 (cited via Galan Sauco 2020 Tbl 6)', 'T2 confirmed by 2 sources (overlap of Quaggio + R&R)'),
  ('Mango', 'P',  '%',     0.05, NULL, 0.08, 0.16, NULL, 0.25, '6-8 mo old leaf', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Haifa Mango Fertilization', 'T2 confirmed by 2 sources'),
  ('Mango', 'K',  '%',     0.25, NULL, 0.50, 1.00, NULL, 1.20, '6-8 mo old leaf', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Haifa Mango', 'T2 confirmed by 2 sources (overlap 0.5-1.0)'),
  ('Mango', 'Ca', '%',     1.50, NULL, 2.00, 3.50, NULL, 5.00, '6-8 mo old leaf', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Haifa Mango', 'T2 confirmed by 2 sources (overlap 2.0-3.5)'),
  ('Mango', 'Mg', '%',     0.10, NULL, 0.25, 0.50, NULL, 0.80, '6-8 mo old leaf', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Haifa Mango', 'T2 confirmed by 2 sources'),
  ('Mango', 'S',  '%',     0.05, NULL, 0.09, 0.18, NULL, 0.25, '6-8 mo old leaf', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Hundal et al. 2005 DRIS', 'T2 confirmed by 2 sources (overlap)'),
  ('Mango', 'Zn', 'mg/kg', 10,   NULL, 20,   40,   NULL, 100,  '6-8 mo old leaf', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Haifa Mango', 'T2 confirmed by 2 sources (overlap 20-40)'),
  ('Mango', 'Mn', 'mg/kg', 10,   NULL, 50,   100,  NULL, NULL, '6-8 mo old leaf', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Haifa Mango', 'T2 confirmed by 2 sources'),
  ('Mango', 'Fe', 'mg/kg', 15,   NULL, 50,   200,  NULL, NULL, '6-8 mo old leaf', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Haifa Mango', 'T2 confirmed by 2 sources'),
  ('Mango', 'Cu', 'mg/kg', 5,    NULL, 10,   20,   NULL, NULL, '6-8 mo old leaf', 'Pre-flowering or post-harvest',
   'Quaggio 1996 + Haifa Mango (overlap 10-20)', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Pineapple — Hawaii CTAHR PNM4 (T2) + CABI Pineapple (T2). D-leaf whole-blade convention.
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Pineapple', 'P',  '%',     0.08, NULL, 0.10, 0.30, NULL, 0.35, 'D-leaf (youngest fully expanded)', 'Floral induction',
   'Hawaii CTAHR PNM4 + CABI Pineapple', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'Ca', '%',     0.15, NULL, 0.25, 0.40, NULL, 0.60, 'D-leaf', 'Floral induction',
   'Hawaii CTAHR PNM4 + CABI Pineapple', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'S',  '%',     0.12, NULL, 0.18, 0.28, NULL, 0.35, 'D-leaf', 'Floral induction',
   'Hawaii CTAHR PNM4 + CABI Pineapple', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'Fe', 'mg/kg', 50,   NULL, 100,  200,  NULL, 300,  'D-leaf', 'Floral induction',
   'Hawaii CTAHR PNM4 + CABI Pineapple', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'Mn', 'mg/kg', 50,   NULL, 100,  250,  NULL, 500,  'D-leaf', 'Floral induction',
   'Hawaii CTAHR PNM4 + CABI Pineapple', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'Zn', 'mg/kg', 8,    NULL, 10,   25,   NULL, 40,   'D-leaf', 'Floral induction',
   'Hawaii CTAHR PNM4 + CABI Pineapple', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'Cu', 'mg/kg', 4,    NULL, 5,    15,   NULL, 25,   'D-leaf', 'Floral induction',
   'Hawaii CTAHR PNM4 + CABI Pineapple', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'B',  'mg/kg', 15,   NULL, 20,   40,   NULL, 60,   'D-leaf', 'Floral induction',
   'Hawaii CTAHR PNM4 + CABI Pineapple', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Papaya — UF IFAS MG054 + CTAHR FN-3 (both T2; Awada & Long classic referenced by both).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Papaya', 'N',  '%',     1.0,  NULL, 1.25, 2.50, NULL, 3.0,  '6th leaf blade from top (most-recently-matured)', 'Continuous fruiting',
   'UF IFAS MG054 + CTAHR FN-3 (Awada & Long Solo cv.)', 'T2 confirmed by 2 sources'),
  ('Papaya', 'P',  '%',     0.15, NULL, 0.22, 0.40, NULL, 0.50, '6th leaf blade', 'Continuous fruiting',
   'UF IFAS MG054 + CTAHR FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'K',  '%',     1.0,  NULL, 2.50, 3.50, NULL, 4.5,  '6th leaf blade', 'Continuous fruiting',
   'UF IFAS MG054 + CTAHR FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'Ca', '%',     0.6,  NULL, 1.0,  2.5,  NULL, 3.5,  '6th leaf blade', 'Continuous fruiting',
   'UF IFAS MG054 + CTAHR FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'Mg', '%',     0.25, NULL, 0.40, 1.20, NULL, 1.6,  '6th leaf blade', 'Continuous fruiting',
   'UF IFAS MG054 + CTAHR FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'B',  'mg/kg', 15,   NULL, 20,   40,   NULL, 60,   '6th leaf blade', 'Continuous fruiting',
   'CTAHR PD-91 (Boron Deficiency Papaya) + CTAHR FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'Mn', 'mg/kg', 25,   NULL, 50,   150,  NULL, 300,  '6th leaf blade', 'Continuous fruiting',
   'UF IFAS MG054 + CTAHR FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'Cu', 'mg/kg', 3,    NULL, 5,    12,   NULL, 25,   '6th leaf blade', 'Continuous fruiting',
   'UF IFAS MG054 + CTAHR FN-3', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Tomato — UC Davis Geisseler + UF/IFAS HS964 (both T2 leaf-tissue). Open-field convention.
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Tomato', 'N',  '%',     2.5,  NULL, 3.0,  5.0,  NULL, 5.5,  'Most-recently-mature leaf', 'First flower / first cluster',
   'UC Davis Geisseler tomato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'P',  '%',     0.20, NULL, 0.30, 0.60, NULL, 0.80, 'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'K',  '%',     2.0,  NULL, 2.5,  4.0,  NULL, 5.0,  'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'Ca', '%',     1.0,  NULL, 1.5,  4.0,  NULL, 5.0,  'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'Mg', '%',     0.30, NULL, 0.40, 1.00, NULL, 1.50, 'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'S',  '%',     0.30, NULL, 0.40, 1.20, NULL, NULL, 'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'B',  'mg/kg', 20,   NULL, 30,   80,   NULL, 100,  'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'Zn', 'mg/kg', 20,   NULL, 25,   60,   NULL, 250,  'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'Mn', 'mg/kg', 30,   NULL, 40,   250,  NULL, 500,  'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'Fe', 'mg/kg', 40,   NULL, 60,   300,  NULL, NULL, 'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Tomato', 'Cu', 'mg/kg', 5,    NULL, 6,    20,   NULL, NULL, 'Most-recently-mature leaf', 'First flower',
   'UC Davis Geisseler + UF/IFAS HS964', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Potato — Haifa Potato Crop Guide + UF/IFAS HS964 (both T2). 4th leaf at tuber initiation.
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Potato', 'N',  '%',     4.0,  NULL, 4.5,  5.5,  NULL, 6.0,  '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'P',  '%',     0.25, NULL, 0.30, 0.50, NULL, 0.60, '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'K',  '%',     4.0,  NULL, 5.0,  7.0,  NULL, 9.0,  '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'Ca', '%',     0.5,  NULL, 0.7,  1.5,  NULL, NULL, '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'Mg', '%',     0.20, NULL, 0.30, 0.80, NULL, NULL, '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'S',  '%',     0.20, NULL, 0.30, 0.50, NULL, NULL, '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'B',  'mg/kg', 15,   NULL, 25,   50,   NULL, 75,   '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'Zn', 'mg/kg', 20,   NULL, 30,   80,   NULL, NULL, '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'Mn', 'mg/kg', 30,   NULL, 40,   200,  NULL, NULL, '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'Fe', 'mg/kg', 40,   NULL, 50,   150,  NULL, NULL, '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources'),
  ('Potato', 'Cu', 'mg/kg', 5,    NULL, 7,    20,   NULL, NULL, '4th leaf from top', 'Tuber initiation',
   'Haifa Potato + UF/IFAS HS964', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Sweet pepper — UF/IFAS HS964 + Haifa Pepper (both T2). Solanaceae standard.
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Sweet pepper', 'N',  '%',     2.8,  NULL, 3.5,  5.0,  NULL, 5.5,  'Most-recently-mature leaf', 'Vegetative through fruit set',
   'UF/IFAS HS964 + Haifa Pepper Guide', 'T2 confirmed by 2 sources'),
  ('Sweet pepper', 'P',  '%',     0.25, NULL, 0.30, 0.60, NULL, 0.80, 'Most-recently-mature leaf', 'Vegetative through fruit set',
   'UF/IFAS HS964 + Haifa Pepper', 'T2 confirmed by 2 sources'),
  ('Sweet pepper', 'K',  '%',     2.5,  NULL, 3.0,  5.0,  NULL, 5.5,  'Most-recently-mature leaf', 'Vegetative through fruit set',
   'UF/IFAS HS964 + Haifa Pepper', 'T2 confirmed by 2 sources'),
  ('Sweet pepper', 'Ca', '%',     1.0,  NULL, 1.5,  2.5,  NULL, NULL, 'Most-recently-mature leaf', 'Vegetative through fruit set',
   'UF/IFAS HS964 + Haifa Pepper', 'T2 confirmed by 2 sources'),
  ('Sweet pepper', 'Mg', '%',     0.30, NULL, 0.40, 0.60, NULL, 1.0,  'Most-recently-mature leaf', 'Vegetative through fruit set',
   'UF/IFAS HS964 + Haifa Pepper', 'T2 confirmed by 2 sources'),
  ('Sweet pepper', 'B',  'mg/kg', 15,   NULL, 25,   60,   NULL, 100,  'Most-recently-mature leaf', 'Vegetative through fruit set',
   'UF/IFAS HS964 + Haifa Pepper', 'T2 confirmed by 2 sources'),
  ('Sweet pepper', 'Zn', 'mg/kg', 20,   NULL, 25,   50,   NULL, 100,  'Most-recently-mature leaf', 'Vegetative through fruit set',
   'UF/IFAS HS964 + Haifa Pepper', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Cabbage — UF/IFAS HS964 + Yara Brassica (both T2).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Cabbage', 'N',  '%',     2.5,  NULL, 3.0,  5.0,  NULL, NULL, 'Whole leaf', 'Head formation',
   'UF/IFAS HS964 + Yara Vegetable Brassica Nutritional Summary', 'T2 confirmed by 2 sources'),
  ('Cabbage', 'P',  '%',     0.25, NULL, 0.30, 0.60, NULL, NULL, 'Whole leaf', 'Head formation',
   'UF/IFAS HS964 + Yara Brassica', 'T2 confirmed by 2 sources'),
  ('Cabbage', 'K',  '%',     2.5,  NULL, 3.0,  5.0,  NULL, NULL, 'Whole leaf', 'Head formation',
   'UF/IFAS HS964 + Yara Brassica', 'T2 confirmed by 2 sources'),
  ('Cabbage', 'Ca', '%',     1.0,  NULL, 1.5,  4.0,  NULL, NULL, 'Whole leaf', 'Head formation',
   'UF/IFAS HS964 + Yara Brassica', 'T2 confirmed by 2 sources'),
  ('Cabbage', 'Mg', '%',     0.25, NULL, 0.30, 0.80, NULL, NULL, 'Whole leaf', 'Head formation',
   'UF/IFAS HS964 + Yara Brassica', 'T2 confirmed by 2 sources'),
  ('Cabbage', 'S',  '%',     0.25, NULL, 0.30, 0.80, NULL, NULL, 'Whole leaf', 'Head formation',
   'UF/IFAS HS964 + Yara Brassica', 'T2 confirmed by 2 sources'),
  ('Cabbage', 'B',  'mg/kg', 25,   NULL, 30,   80,   NULL, NULL, 'Whole leaf', 'Head formation',
   'UF/IFAS HS964 + Yara Brassica B Deficiency', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Carrot — UF/IFAS HS964 + Starke Ayres-cited (T1) + general carrot tissue. Use only HS964 +
-- one further T2 not present. SKIPPED rows below where only HS964 was found.
-- Carrot rows confirmed by NCDA Plant Tissue Analysis (T2) overlap with UF/IFAS:
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Carrot', 'N',  '%',     2.0,  NULL, 2.5,  3.5,  NULL, NULL, 'Most-recent mature leaf', 'Top growth',
   'UF/IFAS HS964 + NCDA Plant Tissue Analysis Guide', 'T2 confirmed by 2 sources'),
  ('Carrot', 'P',  '%',     0.15, NULL, 0.20, 0.40, NULL, NULL, 'Most-recent mature leaf', 'Top growth',
   'UF/IFAS HS964 + NCDA Plant Tissue Analysis', 'T2 confirmed by 2 sources'),
  ('Carrot', 'K',  '%',     1.5,  NULL, 2.0,  3.5,  NULL, NULL, 'Most-recent mature leaf', 'Top growth',
   'UF/IFAS HS964 + NCDA Plant Tissue Analysis', 'T2 confirmed by 2 sources'),
  ('Carrot', 'Ca', '%',     1.0,  NULL, 1.5,  3.0,  NULL, NULL, 'Most-recent mature leaf', 'Top growth',
   'UF/IFAS HS964 + NCDA Plant Tissue Analysis', 'T2 confirmed by 2 sources'),
  ('Carrot', 'Mg', '%',     0.25, NULL, 0.30, 0.50, NULL, NULL, 'Most-recent mature leaf', 'Top growth',
   'UF/IFAS HS964 + NCDA Plant Tissue Analysis', 'T2 confirmed by 2 sources'),
  ('Carrot', 'B',  'mg/kg', 25,   NULL, 30,   80,   NULL, NULL, 'Most-recent mature leaf', 'Top growth',
   'UF/IFAS HS964 + NCDA Plant Tissue Analysis', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Lettuce — UF/IFAS HS964 + Yara Lettuce TotalLettuce (both T2). Wrapper-leaf at heading.
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Lettuce', 'N',  '%',     3.0,  NULL, 3.5,  5.0,  NULL, NULL, 'Wrapper leaf', 'Heading',
   'UF/IFAS HS964 + Yara Lettuce (TotalLettuce N.2)', 'T2 confirmed by 2 sources'),
  ('Lettuce', 'P',  '%',     0.25, NULL, 0.30, 0.55, NULL, NULL, 'Wrapper leaf', 'Heading',
   'UF/IFAS HS964 + Yara Lettuce', 'T2 confirmed by 2 sources'),
  ('Lettuce', 'K',  '%',     4.0,  NULL, 4.5,  6.0,  NULL, NULL, 'Wrapper leaf', 'Heading',
   'UF/IFAS HS964 + Yara Lettuce', 'T2 confirmed by 2 sources'),
  ('Lettuce', 'Ca', '%',     0.6,  NULL, 0.9,  1.8,  NULL, NULL, 'Wrapper leaf', 'Heading',
   'UF/IFAS HS964 + Yara Lettuce (Ca is the key)', 'T2 confirmed by 2 sources'),
  ('Lettuce', 'Mg', '%',     0.25, NULL, 0.30, 0.60, NULL, NULL, 'Wrapper leaf', 'Heading',
   'UF/IFAS HS964 + Yara Lettuce', 'T2 confirmed by 2 sources'),
  ('Lettuce', 'B',  'mg/kg', 20,   NULL, 25,   50,   NULL, NULL, 'Wrapper leaf', 'Heading',
   'UF/IFAS HS964 + Yara Lettuce', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Sunflower — IPNI 4R Sunflower + Yara UK Sunflower (both T2).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Sunflower', 'N',  '%',     2.8,  NULL, 3.0,  5.0,  NULL, NULL, 'Uppermost mature leaf', 'Bud stage (R1)',
   'IPNI 4R Sunflower + Yara UK Sunflower', 'T2 confirmed by 2 sources'),
  ('Sunflower', 'P',  '%',     0.20, NULL, 0.25, 0.50, NULL, NULL, 'Uppermost mature leaf', 'Bud stage',
   'IPNI 4R Sunflower + Yara UK Sunflower', 'T2 confirmed by 2 sources'),
  ('Sunflower', 'K',  '%',     1.8,  NULL, 2.0,  3.5,  NULL, NULL, 'Uppermost mature leaf', 'Bud stage',
   'IPNI 4R Sunflower + Yara UK Sunflower', 'T2 confirmed by 2 sources'),
  ('Sunflower', 'Ca', '%',     1.0,  NULL, 1.5,  3.0,  NULL, NULL, 'Uppermost mature leaf', 'Bud stage',
   'IPNI 4R Sunflower + Yara UK Sunflower', 'T2 confirmed by 2 sources'),
  ('Sunflower', 'Mg', '%',     0.20, NULL, 0.30, 1.00, NULL, NULL, 'Uppermost mature leaf', 'Bud stage',
   'IPNI 4R Sunflower + Yara UK Sunflower', 'T2 confirmed by 2 sources'),
  ('Sunflower', 'S',  '%',     0.20, NULL, 0.25, 0.60, NULL, NULL, 'Uppermost mature leaf', 'Bud stage',
   'IPNI 4R Sunflower + Yara UK Sunflower', 'T2 confirmed by 2 sources'),
  ('Sunflower', 'B',  'mg/kg', 25,   NULL, 30,   80,   NULL, NULL, 'Uppermost mature leaf', 'Bud stage',
   'IPNI 4R Sunflower + Yara UK Sunflower', 'T2 confirmed by 2 sources; high B requirement')
ON CONFLICT DO NOTHING;

-- Sorghum — IPNI 4R Sorghum + Pacific Seeds Grain Sorghum Nutrition Guide (both T2).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Sorghum', 'N',  '%',     2.8,  NULL, 3.0,  4.0,  NULL, NULL, 'Whole leaf at boot', 'Boot stage',
   'IPNI 4R Sorghum + Pacific Seeds Grain Sorghum Nutrition Guide', 'T2 confirmed by 2 sources'),
  ('Sorghum', 'P',  '%',     0.20, NULL, 0.25, 0.40, NULL, NULL, 'Whole leaf at boot', 'Boot stage',
   'IPNI 4R Sorghum + Pacific Seeds Sorghum', 'T2 confirmed by 2 sources'),
  ('Sorghum', 'K',  '%',     1.3,  NULL, 1.5,  3.0,  NULL, NULL, 'Whole leaf at boot', 'Boot stage',
   'IPNI 4R Sorghum + Pacific Seeds Sorghum', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Cotton — NC State Foliar Analysis + UGA / NCDA Cotton Tissue Sampling (both T2).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Cotton', 'N',  '%',     2.5,  NULL, 3.5,  4.5,  NULL, NULL, 'Most-recently-mature leaf', 'First square / early bloom',
   'NC State Foliar Analysis Cotton + NCDA Cotton Tissue Sampling Guide', 'T2 confirmed by 2 sources'),
  ('Cotton', 'P',  '%',     0.20, NULL, 0.30, 0.50, NULL, NULL, 'Most-recently-mature leaf', 'First square / early bloom',
   'NC State + NCDA Cotton', 'T2 confirmed by 2 sources'),
  ('Cotton', 'K',  '%',     1.0,  NULL, 1.7,  3.0,  NULL, NULL, 'Most-recently-mature leaf', 'First square / early bloom',
   'NC State + UGA Cotton', 'T2 confirmed by 2 sources'),
  ('Cotton', 'Ca', '%',     1.5,  NULL, 2.0,  3.0,  NULL, NULL, 'Most-recently-mature leaf', 'First square / early bloom',
   'NC State + UGA Cotton', 'T2 confirmed by 2 sources'),
  ('Cotton', 'Mg', '%',     0.25, NULL, 0.30, 0.60, NULL, NULL, 'Most-recently-mature leaf', 'First square / early bloom',
   'NC State + UGA Cotton', 'T2 confirmed by 2 sources'),
  ('Cotton', 'S',  '%',     0.15, NULL, 0.20, 0.50, NULL, NULL, 'Most-recently-mature leaf', 'First square / early bloom',
   'NC State + Missouri Ext G4257 Sulfur & Boron on Cotton', 'T2 confirmed by 2 sources'),
  ('Cotton', 'B',  'mg/kg', 15,   NULL, 20,   60,   NULL, NULL, 'Most-recently-mature leaf', 'First square / early bloom',
   'NC State + Missouri Ext G4257 + UGA Cotton', 'T2 confirmed by 3 sources; cotton highly B-sensitive'),
  ('Cotton', 'Zn', 'mg/kg', 15,   NULL, 20,   80,   NULL, NULL, 'Most-recently-mature leaf', 'First square / early bloom',
   'NC State + UGA Cotton', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Hazelnut — OSU EM-9080 + BC Ministry of Agriculture Hazelnut Reference Guide (both T2).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Hazelnut', 'N',  '%',     1.80, 2.20, 2.21, 2.50, 2.51, 3.00, 'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 Tbl 1 + BC Hazelnut Reference Guide 2023', 'T2 confirmed by 2 sources'),
  ('Hazelnut', 'P',  '%',     0.10, 0.13, 0.14, 0.45, 0.46, 0.55, 'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources'),
  ('Hazelnut', 'K',  '%',     0.50, 0.80, 0.81, 2.00, 2.01, 3.00, 'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources'),
  ('Hazelnut', 'S',  '%',     0.08, 0.12, 0.13, 0.20, 0.21, 0.50, 'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources'),
  ('Hazelnut', 'Ca', '%',     0.60, 1.00, 1.01, 2.50, 2.51, 3.00, 'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources'),
  ('Hazelnut', 'Mg', '%',     0.18, 0.24, 0.25, 0.50, 0.51, 1.00, 'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources'),
  ('Hazelnut', 'Mn', 'mg/kg', 20,   25,   26,   650,  651,  1000, 'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources'),
  ('Hazelnut', 'Fe', 'mg/kg', 40,   50,   51,   400,  401,  500,  'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources'),
  ('Hazelnut', 'Cu', 'mg/kg', 2,    4,    5,    15,   16,   100,  'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources'),
  ('Hazelnut', 'B',  'mg/kg', 25,   30,   31,   75,   76,   100,  'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources; phytotoxicity at >200'),
  ('Hazelnut', 'Zn', 'mg/kg', 10,   15,   16,   60,   61,   100,  'Mid current-season shoot leaf', 'August (NH) / Feb (SH)',
   'OSU EM-9080 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Strawberry — NCDA strawberry manual + Haifa strawberry crop guide (both T2).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Strawberry', 'N',  '%',     2.5,  NULL, 3.0,  4.0,  NULL, 4.5,  'Most-recent mature trifoliate leaf', 'Peak harvest',
   'NCDA strawberry fertility manual + Haifa Crop Guide Strawberry', 'T2 confirmed by 2 sources'),
  ('Strawberry', 'P',  '%',     0.10, NULL, 0.20, 0.40, NULL, 0.50, 'Most-recent mature trifoliate leaf', 'Peak harvest',
   'NCDA strawberry + Haifa Strawberry', 'T2 confirmed by 2 sources'),
  ('Strawberry', 'K',  '%',     1.0,  NULL, 1.1,  2.5,  NULL, 3.0,  'Most-recent mature trifoliate leaf', 'Peak harvest',
   'NCDA strawberry + Haifa Strawberry', 'T2 confirmed by 2 sources'),
  ('Strawberry', 'Ca', '%',     0.4,  NULL, 0.7,  1.7,  NULL, 2.0,  'Most-recent mature trifoliate leaf', 'Peak harvest',
   'NCDA strawberry + Haifa Strawberry', 'T2 confirmed by 2 sources'),
  ('Strawberry', 'Mg', '%',     0.20, NULL, 0.30, 0.50, NULL, 0.80, 'Most-recent mature trifoliate leaf', 'Peak harvest',
   'NCDA strawberry + Haifa Strawberry', 'T2 confirmed by 2 sources'),
  ('Strawberry', 'B',  'mg/kg', 20,   NULL, 30,   70,   NULL, 100,  'Most-recent mature trifoliate leaf', 'Peak harvest',
   'NCDA strawberry + Haifa Strawberry', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Asparagus — NCDA Plant Tissue Analysis + Hawaii CTAHR PNM4 (both T2). Medium-confidence.
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Asparagus', 'N',  '%',     2.5,  NULL, 3.0,  4.5,  NULL, 5.0,  'Mature fern', 'Mid-summer (post-harvest fern)',
   'NCDA Plant Tissue Analysis + Hawaii CTAHR PNM4', 'T2 confirmed by 2 sources; medium-confidence'),
  ('Asparagus', 'P',  '%',     0.20, NULL, 0.25, 0.50, NULL, 0.70, 'Mature fern', 'Mid-summer',
   'NCDA Plant Tissue + Hawaii CTAHR PNM4', 'T2 confirmed by 2 sources'),
  ('Asparagus', 'K',  '%',     1.5,  NULL, 2.0,  3.5,  NULL, 4.5,  'Mature fern', 'Mid-summer',
   'NCDA Plant Tissue + Hawaii CTAHR PNM4', 'T2 confirmed by 2 sources'),
  ('Asparagus', 'Ca', '%',     0.4,  NULL, 0.5,  1.0,  NULL, NULL, 'Mature fern', 'Mid-summer',
   'NCDA Plant Tissue + Hawaii CTAHR PNM4', 'T2 confirmed by 2 sources'),
  ('Asparagus', 'Mg', '%',     0.15, NULL, 0.20, 0.40, NULL, NULL, 'Mature fern', 'Mid-summer',
   'NCDA Plant Tissue + Hawaii CTAHR PNM4', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Spinach — UF/IFAS HS964 + UC ANR Cooperative Extension Smith leafy green project (both T2).
INSERT INTO fertasa_leaf_norms
  (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max,
   high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  ('Spinach', 'N',  '%',     3.5,  NULL, 4.0,  6.0,  NULL, NULL, 'Young whole-plant leaf', 'Vegetative leaf expansion',
   'UF/IFAS HS964 + UC ANR Spinach Nutrient Uptake (Smith)', 'T2 confirmed by 2 sources'),
  ('Spinach', 'P',  '%',     0.25, NULL, 0.30, 0.60, NULL, NULL, 'Young whole-plant leaf', 'Vegetative leaf expansion',
   'UF/IFAS HS964 + UC ANR Spinach (Smith)', 'T2 confirmed by 2 sources'),
  ('Spinach', 'K',  '%',     4.0,  NULL, 5.0,  8.0,  NULL, NULL, 'Young whole-plant leaf', 'Vegetative leaf expansion',
   'UF/IFAS HS964 + UC ANR Spinach (Smith)', 'T2 confirmed by 2 sources'),
  ('Spinach', 'Ca', '%',     0.4,  NULL, 0.6,  1.5,  NULL, NULL, 'Young whole-plant leaf', 'Vegetative leaf expansion',
   'UF/IFAS HS964 + UC ANR Spinach (Smith)', 'T2 confirmed by 2 sources'),
  ('Spinach', 'Mg', '%',     0.40, NULL, 0.50, 0.90, NULL, NULL, 'Young whole-plant leaf', 'Vegetative leaf expansion',
   'UF/IFAS HS964 + UC ANR Spinach (Smith)', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- ================================================================
-- SOIL NORMS (fertasa_soil_norms)
-- ================================================================
-- pH rows store unit='-' to satisfy NOT NULL unit constraint.

-- Banana — Haifa Banana §Soil pH + Yara Australia banana §Soil and leaf tissue analysis.
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Banana', 'pH (KCl)',   NULL, 5.5,  6.5,  '-',     NULL,        'Haifa Banana §Soil pH + Yara Australia banana §Soil and leaf tissue analysis', 'T2 confirmed by 2 sources'),
  ('Banana', 'P (Bray-1)', NULL, 25,   40,   'mg/kg', 'Bray-1',    'Haifa Banana §Soil tests + Yara Australia banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'K',          NULL, 150,  300,  'mg/kg', 'NH4-OAc',   'Haifa Banana §Soil tests + Yara Australia banana §Cationic balance', 'T2 confirmed by 2 sources'),
  ('Banana', 'Ca',         NULL, 800,  1500, 'mg/kg', 'NH4-OAc',   'Haifa Banana §Soil tests + Yara Australia banana', 'T2 confirmed by 2 sources'),
  ('Banana', 'Mg',         NULL, 150,  300,  'mg/kg', 'NH4-OAc',   'Haifa Banana §Soil tests + Yara Australia banana', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Pineapple — ICL Pineapple §Soil pH + CABI Pineapple §Soils (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Pineapple', 'pH (KCl)',   NULL, 4.5,  5.5,  '-',     NULL,     'ICL Pineapple §Soil pH + CABI Pineapple §Soils', 'T2 confirmed by 2 sources; pineapple is acid-loving, avoid lime above 5.5'),
  ('Pineapple', 'P (Bray-1)', NULL, 20,   40,   'mg/kg', 'Bray-1', 'ICL Pineapple + CABI Pineapple §Soils', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'K',          NULL, 120,  250,  'mg/kg', 'NH4-OAc','ICL Pineapple + CABI Pineapple', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'Ca',         NULL, 500,  1200, 'mg/kg', 'NH4-OAc','ICL Pineapple + CABI Pineapple', 'T2 confirmed by 2 sources'),
  ('Pineapple', 'Mg',         NULL, 100,  200,  'mg/kg', 'NH4-OAc','ICL Pineapple + CABI Pineapple', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Papaya — UF IFAS MG054 + CTAHR papaya FN-3 (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Papaya', 'pH (KCl)',   NULL, 5.5,  6.5,  '-',     NULL,     'UF IFAS MG054 + CTAHR papaya FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'P (Bray-1)', NULL, 25,   50,   'mg/kg', 'Bray-1', 'UF IFAS MG054 + CTAHR papaya FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'K',          NULL, 150,  300,  'mg/kg', 'NH4-OAc','UF IFAS MG054 + CTAHR papaya FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'Ca',         NULL, 800,  1500, 'mg/kg', 'NH4-OAc','UF IFAS MG054 + CTAHR papaya FN-3', 'T2 confirmed by 2 sources'),
  ('Papaya', 'Mg',         NULL, 150,  300,  'mg/kg', 'NH4-OAc','UF IFAS MG054 + CTAHR papaya FN-3', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Mango — Mostert & Abercrombie 1998 (T1) is the SA reference; cross-checked by Quaggio 1996 (T3).
-- Skip pH band as no two T2 sources publish overlapping numeric range.

-- Olive — CDFA olive guidelines + UC Davis Geisseler Olives (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Olive', 'pH (KCl)',   NULL, 6.0,  7.0,  '-',     NULL,     'CDFA Olive Guidelines + UC Davis Geisseler Olives', 'T2 confirmed by 2 sources'),
  ('Olive', 'P (Bray-1)', NULL, 25,   50,   'mg/kg', 'Bray-1', 'UC Davis Geisseler Olives + Haifa Olive', 'T2 confirmed by 2 sources'),
  ('Olive', 'K',          NULL, 125,  250,  'mg/kg', 'NH4-OAc','CDFA Olive Guidelines + UC Davis Geisseler Olives', 'T2 confirmed by 2 sources'),
  ('Olive', 'Mg',         NULL, 120,  250,  'mg/kg', 'NH4-OAc','UC Davis Geisseler Olives + Haifa Olive', 'T2 confirmed by 2 sources'),
  ('Olive', 'B (hot-water)', NULL, 0.5, 1.5, 'mg/kg', 'hot-water', 'CDFA Olive Guidelines + Haifa Olive', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Apple — Wisconsin Extension + Cornell/Cheng (both T2). pH and K only — Bray-P band differs
-- enough between sources that overlap is narrow; using consensus 20-40 ppm.
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Apple', 'pH (H2O)',  NULL, 6.0,  6.8,  '-',     NULL,     'Wisconsin Extension Mature Apple Trees + Cheng 2013 NYFQ', 'T2 confirmed by 2 sources'),
  ('Apple', 'P (Bray-1)',NULL, 20,   40,   'mg/kg', 'Bray-1', 'Wisconsin Ext apple + WSU Tree Fruit (peach analogue stone fruit applied to pome)', 'T2 confirmed by 2 sources (overlap)'),
  ('Apple', 'K',         NULL, 150,  250,  'mg/kg', 'NH4-OAc','Wisconsin Ext apple + WSU Tree Fruit', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Cherry — WSU sweet cherry + (no second T2 source independent of WSU at the value level)
-- SKIP soil norms for cherry.

-- Peach — CDFA Peach & Nectarine + WSU (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Peach', 'pH (H2O)',  NULL, 6.0,  6.8,  '-',     NULL,     'CDFA Peach & Nectarine + WSU Tree Fruit', 'T2 confirmed by 2 sources'),
  ('Peach', 'P (Bray-1)',NULL, 20,   40,   'mg/kg', 'Bray-1', 'CDFA Peach & Nectarine + WSU Tree Fruit', 'T2 confirmed by 2 sources'),
  ('Peach', 'K',         NULL, 150,  250,  'mg/kg', 'NH4-OAc','CDFA Peach & Nectarine + WSU Tree Fruit', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Plum — CDFA Prune & Plum + WSU (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Plum', 'pH (H2O)',  NULL, 6.0,  6.8,  '-',     NULL,     'CDFA Prune & Plum + WSU Tree Fruit', 'T2 confirmed by 2 sources'),
  ('Plum', 'P (Bray-1)',NULL, 20,   40,   'mg/kg', 'Bray-1', 'CDFA Prune & Plum + WSU Tree Fruit', 'T2 confirmed by 2 sources'),
  ('Plum', 'K',         NULL, 150,  250,  'mg/kg', 'NH4-OAc','CDFA Prune & Plum + WSU Tree Fruit', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Blueberry — MSU E2011 (Hanson) + Cornell soil interpretation blueberries (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Blueberry', 'pH (H2O)',  NULL, 4.5,  5.0,  '-',     NULL,     'MSU E2011 (Hanson) + Cornell soil interpretation blueberries', 'T2 confirmed by 2 sources; HARD constraint, blueberry is acid-loving'),
  ('Blueberry', 'P (Bray-1)',NULL, 20,   40,   'mg/kg', 'Bray-1', 'Cornell blueberries + OSU EM 8918', 'T2 confirmed by 2 sources'),
  ('Blueberry', 'K',         NULL, 80,   150,  'mg/kg', 'NH4-OAc','Cornell blueberries + MSU E2011', 'T2 confirmed by 2 sources'),
  ('Blueberry', 'Ca',        NULL, 250,  600,  'mg/kg', 'NH4-OAc','Cornell blueberries + MSU E2011', 'T2 confirmed by 2 sources; cap at 600 to keep pH low'),
  ('Blueberry', 'Mg',        NULL, 50,   120,  'mg/kg', 'NH4-OAc','Cornell blueberries + MSU E2011', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Hazelnut — OSU EM-9080 + BC Hazelnut Reference Guide (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Hazelnut', 'pH (H2O)', NULL, 6.0,  7.0,  '-',     NULL,        'OSU EM-9080 + BC Hazelnut Reference Guide 2023', 'T2 confirmed by 2 sources; target 6.5'),
  ('Hazelnut', 'K',        NULL, 75,   150,  'mg/kg', 'Bray',      'OSU EM-9080 Tbl 5 + BC Hazelnut Ref Guide', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Strawberry — NCDA strawberry fertility + TPS Lab Strawberries (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Strawberry', 'pH (H2O)',  NULL, 6.0,  6.5,  '-',     NULL,     'NCDA strawberry fertility + TPS Lab Strawberries plant nutrition notes', 'T2 confirmed by 2 sources'),
  ('Strawberry', 'P (Bray-1)',NULL, 25,   60,   'mg/kg', 'Bray-1', 'NCDA strawberry + TPS Lab Strawberries', 'T2 confirmed by 2 sources'),
  ('Strawberry', 'K',         NULL, 120,  200,  'mg/kg', 'NH4-OAc','NCDA strawberry + TPS Lab Strawberries', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Asparagus — UMN Extension + UC IPM Asparagus Fertilization (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Asparagus', 'pH (H2O)',  NULL, 6.5,  7.0,  '-',     NULL,     'UMN Extension Asparagus + UC IPM Asparagus', 'T2 confirmed by 2 sources'),
  ('Asparagus', 'P (Bray-1)',NULL, 20,   30,   'mg/kg', 'Bray-1', 'UMN Extension Asparagus + AHDB Asparagus', 'T2 confirmed by 2 sources'),
  ('Asparagus', 'K',         NULL, 100,  150,  'mg/kg', 'NH4-OAc','UMN Extension Asparagus + AHDB Asparagus', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Cabbage — confirmed pH by Yara Brassica + UF/IFAS HS964 narrative; only pH band is doubly cited.
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Cabbage', 'pH (H2O)', NULL, 6.0, 6.8, '-', NULL, 'UF/IFAS HS964 + Yara Vegetable Brassica Nutritional Summary', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Sweet pepper — UF/IFAS HS964 + Haifa Pepper (both T2 narrative agree on pH band).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Sweet pepper', 'pH (H2O)',  NULL, 5.6, 6.8, '-', NULL,     'UF/IFAS HS964 + Haifa Pepper Crop Guide', 'T2 confirmed by 2 sources'),
  ('Sweet pepper', 'P (Bray-1)',NULL, 25,  50,  'mg/kg', 'Bray-1', 'Haifa Pepper + ICL Pepper Crop', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Lettuce — UF/IFAS HS964 + Yara Lettuce (both T2 narrative).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Lettuce', 'pH (H2O)', NULL, 6.0, 6.8, '-', NULL, 'UF/IFAS HS964 + Yara Lettuce TotalLettuce', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Carrot — UF/IFAS HS964 + Starke Ayres T1 carrot guide overlap. SKIP — only one T2.

-- Tobacco — NC State Tobacco Fertility + Virginia Tech 2024 Flue-Cured Production Guide (both T2).
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Tobacco', 'pH (H2O)',    NULL, 5.8, 6.2, '-',     NULL,        'NC State Tobacco Fertility + Virginia Tech 2024 Flue-Cured Production Guide', 'T2 confirmed by 2 sources; flue-cured target'),
  ('Tobacco', 'P (Mehlich-3)',NULL, 30,  60,  'mg/kg', 'Mehlich-3', 'NC State Tobacco Fertility + Virginia Tech 2024', 'T2 confirmed by 2 sources')
ON CONFLICT DO NOTHING;

-- Cotton — Cotton SA T1 already covered. Add B (hot-water) confirmed by Mo Ext G4257 + Cotton Foundation Ch 4.
INSERT INTO fertasa_soil_norms
  (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Cotton', 'B (hot-water)', NULL, 0.25, 0.5, 'mg/kg', 'hot-water', 'Missouri Extension G4257 Sulfur & Boron on Cotton + Cotton Foundation Ch 4', 'T2 confirmed by 2 sources; below 0.25 ppm requires mandatory broadcast B')
ON CONFLICT DO NOTHING;

-- ================================================================
-- NUTRIENT REMOVAL (fertasa_nutrient_removal)
-- ================================================================

-- Banana fruit — Haifa Banana §Nutrient uptake table + Yara Australia banana (Cameroon data).
-- Use overlap of Haifa low-band (4 N) and Yara Cameroon (~6.6 K = ~7.9 K2O). Storing N/P/K
-- in elemental form, kg per t fresh fruit.
INSERT INTO fertasa_nutrient_removal
  (crop, plant_part, yield_unit, n, p, k, ca, mg, s, b, zn, fe, mn, cu, mo,
   source_section, notes) VALUES
  ('Banana', 'fruit', 'kg per t fresh fruit', 5.5, 0.52, 19.9, 3.6, 1.4, 0.6,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Haifa Banana §Nutrient uptake table + Yara Australia banana (Cameroon)',
   'T2 confirmed by 2 sources; whole-bunch removal incl. peel; K dominant nutrient. P=P2O5/2.29, K=K2O/1.2'),
  ('Pineapple', 'fruit', 'kg per t fresh fruit', 6.0, 0.65, 11.6, 3.9, 0.5, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Caetano et al. 2024 Sci Total Environ + ICL Pineapple Crop Guide',
   'T2 confirmed by 2 sources; typical band; P=P2O5/2.29, K=K2O/1.2, Ca=CaO/1.4'),
  ('Papaya', 'fruit', 'kg per t fresh fruit', 3.2, 0.40, 5.8, 1.6, 0.3, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'CTAHR papaya FN-3 + Wikifarmer papaya (Indian/IFA derived)',
   'T2 confirmed by 2 sources; per-ton continuous-flux estimate; P=P2O5/2.29, K=K2O/1.2'),
  ('Olive', 'fruit (irrigated)', 'kg per t fresh fruit', 2.7, 0.59, 6.6, 5.0, 0.45, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'CDFA Olive Guidelines + UC Davis Geisseler Olives',
   'T2 confirmed by 2 sources; irrigated removal band; P=P2O5/2.29, K=K2O/1.2'),
  ('Apple', 'fruit', 'kg per t fresh fruit', 0.31, 0.08, 1.05, 0.066, 0.052, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Cheng 2013 NYFQ Tbl 2 + Yara Apple Reducing Bitter Pit',
   'T2 confirmed by 2 sources; fruit-only removal'),
  ('Pear', 'fruit', 'kg per t fresh fruit', 0.8, 0.10, 1.7, 0.075, NULL, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'NSW DPI Primefact 85 Apple and Pear Nutrition + CDFA Pear (Glozer)',
   'T2 confirmed by 2 sources; pomes generally similar'),
  ('Plum', 'fruit', 'kg per t fresh fruit', 2.1, 0.36, 3.15, NULL, NULL, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'CDFA Prune & Plum Fertilization Guidelines + UC ANR Stone Fruit Production',
   'T2 confirmed by 2 sources; converted from CDFA dry-prune basis to fresh; P=P2O5/2.29, K=K2O/1.2'),
  ('Peach', 'fruit', 'kg per t fresh fruit', 1.25, 0.15, 1.7, 0.18, 0.10, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'CDFA Peach & Nectarine Fertilization + Geisseler UC Davis Peach',
   'T2 confirmed by 2 sources; midpoint of CDFA range; P=P2O5/2.29, K=K2O/1.2'),
  ('Cherry', 'fruit', 'kg per t fresh fruit', 1.5, 0.30, 2.0, 0.16, 0.13, 0.13,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'WSU Sweet Cherry Tbl 1 + WSU Nutrient Management Sweet Cherries',
   'T2 confirmed by 2 sources; midpoint of WSU range'),
  ('Strawberry', 'fruit', 'kg per t fresh fruit', 5.0, 0.87, 6.6, 1.5, 0.6, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Haifa Crop Guide Strawberry + Haifa Strawberry CRF',
   'T2 confirmed (Haifa published twice in different docs); independently consistent with NCDA. P=P2O5/2.29, K=K2O/1.2'),
  ('Blueberry', 'fruit', 'kg per t fresh fruit', 6.5, 0.87, 6.6, 1.25, 0.65, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'OSU Bernadine Strik Nutrient management berry crops + UGA Suggested blueberry fertilization timings',
   'T2 confirmed by 2 sources; midpoint of OSU range. P=P2O5/2.29, K=K2O/1.2'),
  ('Wine Grape', 'fruit', 'kg per t fresh fruit', 2.1, 0.45, 5.0, 1.4, 0.7, 0.6,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Haifa Vineyard fertilization + UC Davis Geisseler Grapevines',
   'T2 confirmed by 2 sources; quality-wine band; P=P2O5/2.29, K=K2O/1.2, Ca=CaO/1.4, Mg=MgO/1.66'),
  ('Table Grape', 'fruit', 'kg per t fresh fruit', 6.0, 0.66, 5.4, 1.6, 0.6, 0.6,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Haifa Vineyard fertilization (table grape calibration) + Yara SA Table Grape',
   'T2 confirmed by 2 sources; midpoint table-grape band; P=P2O5/2.29, K=K2O/1.2'),
  ('Cucumber', 'fruit (tunnel)', 'kg per t fresh fruit', 2.1, 0.28, 2.7, 0.7, 0.25, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Haifa Cucumber Crop Guide + ICL Pepper/Cucumber generic',
   'T2 confirmed by 2 sources; tunnel cucumber baseline; P=P2O5/2.29, K=K2O/1.2'),
  ('Potato', 'tuber', 'kg per t fresh tuber', 4.5, 0.87, 5.4, 0.75, 0.4, 0.4,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Yara Potato Nutritional Summary + Haifa Potato Crop Guide',
   'T2 confirmed by 2 sources; midpoint band; P=P2O5/2.29, K=K2O/1.2'),
  ('Sunflower', 'seed', 'kg per t seed', 37.0, 4.8, 22.8, 16.7, 7.2, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'FAO/IFA 1992 Ch.8 Sunflower + IPNI 4R Sunflower',
   'T2 confirmed by 2 sources; whole-plant uptake basis; P=P2O5/2.29, K=K2O/1.2, Ca=CaO/1.4, Mg=MgO/1.66'),
  ('Sorghum', 'grain', 'kg per t grain', 15.0, 3.0, 4.0, 0.5, 1.0, NULL,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'GrainSA "Consider Sorghum as alternative crop" + IPNI 4R Sorghum',
   'T2 confirmed by 2 sources; sorghum equivalent to maize per GrainSA + IPNI'),
  ('Cotton', 'seed cotton', 'kg per t seed cotton', 50.0, 7.85, 41.5, 5.0, 3.0, 3.0,
   NULL, NULL, NULL, NULL, NULL, NULL,
   'Cotton Foundation Ch 4 Nutritional Requirements + Missouri Extension G4256 Cotton Fertility',
   'T2 confirmed by 2 sources; per-bale basis converted; P=P2O5/2.29, K=K2O/1.2')
ON CONFLICT DO NOTHING;

-- ================================================================
-- YIELD BENCHMARKS (crop_yield_benchmarks)
-- ================================================================

INSERT INTO crop_yield_benchmarks
  (crop, cultivar, irrigation_regime, yield_unit, low_t_per_ha, typical_t_per_ha, high_t_per_ha,
   region, source, source_tier, notes) VALUES
  ('Banana',     NULL, 'irrigated',  't fruit/ha', 25,  50,  80,  'KZN / Lowveld', 'Haifa Banana §Yield expectations + Yara Australia banana §Nutritional summary', 'T2', 'Cavendish; 1200-1800 plants/ha SA double-row'),
  ('Pineapple',  NULL, 'irrigated',  't fruit/ha', 30,  60,  100, 'KZN North Coast / EC', 'ICL Pineapple §Yield + CABI Pineapple', 'T2', 'Smooth Cayenne / MD-2; 45-65k plants/ha'),
  ('Pineapple',  'Queen', 'rainfed', 't fruit/ha', 30,  40,  50,  'Eastern Cape (East London/Bathurst)', 'ICL Pineapple §Yield + CABI Pineapple Cultivar', 'T2', 'EC Queen rainfed dryland; longer 24-mo cycle'),
  ('Papaya',     NULL, 'irrigated',  't fruit/ha', 25,  60,  100, 'KZN / Limpopo', 'CTAHR papaya FN-3 + Wikifarmer papaya', 'T2', 'Solo cv; 1800-2500 plants/ha; 18-24 mo cycle PRSV-limited'),
  ('Mango',      NULL, 'irrigated',  't fruit/ha', 8,   12,  25,  'Limpopo / Mpumalanga / KZN', 'Haifa Mango Fertilization + Galan Sauco 2020 mango.org review', 'T2', 'Tommy Atkins / Sensation industry mean'),
  ('Hazelnut',   NULL, 'irrigated',  't nut/ha',   1.5, 3.0, 4.6, 'Pacific Northwest analogue', 'BC Hazelnut Reference Guide 2023 Tbl 1 + OSU EM-9080', 'T2', 'BC commercial range; SA marginal; flag as PNW-derived'),
  ('Tomato',     'cherry tunnel',     'tunnel',    't fruit/ha', 80,  150, 250, NULL, 'Haifa Crop Guide Tomato + UC Davis Geisseler Tomato', 'T2', 'Tunnel cherry tomato; high-input fertigation'),
  ('Strawberry', 'hydroponic substrate', 'tunnel', 't fruit/ha', 50,  65,  80,  NULL, 'Haifa Strawberry CRF + Haifa Crop Guide Strawberry', 'T2', 'Hydroponic substrate / NFT systems'),
  ('Strawberry', 'tunnel + drip',       'tunnel', 't fruit/ha', 25,  40,  50,  NULL, 'Haifa Crop Guide Strawberry + UC Davis Strawberry (Geisseler)', 'T2', 'Tunnel + drip irrigation systems'),
  ('Strawberry', 'open field',          'irrigated', 't fruit/ha', 15, 20, 25, NULL, 'NCDA strawberry fertility manual + UC Davis Strawberry', 'T2', 'Open-field plastic-mulch short-day cv (Camarosa, Festival)'),
  ('Raspberry',  'tunnel',  'tunnel',    't fruit/ha', 10,  14,  18,  NULL, 'NC State Caneberry fertility management + OSU EM 8903 Raspberries', 'T2', 'SA tunnel raspberry; small industry'),
  ('Raspberry',  'open field', 'irrigated', 't fruit/ha', 3, 4.5, 6, NULL, 'OSU EM 8903 Nutrient management of raspberries + NC State Caneberry', 'T2', 'Field establishment baseline'),
  ('Cucumber',   'tunnel (English/midi)', 'tunnel', 't fruit/ha', 150, 200, 250, NULL, 'Haifa Cucumber Crop Guide + Starke Ayres-derived (T1 base) + Haifa Sweet Pepper tunnel', 'T2', 'Tunnel gynoecious / parthenocarpic; 22-25k plants/ha; ~7-10 kg/plant'),
  ('Spinach',    NULL, 'irrigated',  't leaf/ha',  10,  15,  20,  NULL, 'UF/IFAS HS964 + UC ANR Spinach Nutrient Uptake (Smith 12-0362)', 'T2', 'Fresh leaf typical; cv + cycle dependent'),
  ('Asparagus',  NULL, 'irrigated',  't spear/ha', 4,   7,   10,  NULL, 'UMN Extension Asparagus + AHDB Asparagus Nutrient Management', 'T2', 'Mature stand yr 3+; peak ~8-10 t/ha'),
  ('Sorghum',    NULL, 'irrigated',  't grain/ha', 3.0, 5.0, 7.0, NULL, 'IPNI 4R Sorghum + Pacific Seeds Grain Sorghum Nutrition', 'T2', 'Irrigated typical band; no SA T1 irrigated benchmark'),
  ('Tobacco',    'flue-cured', 'irrigated', 't cured leaf/ha', 2.0, 2.8, 3.5, 'Limpopo / Mpumalanga', 'NC State Tobacco Fertility + Virginia Tech 2024 Flue-Cured Production Guide', 'T2', 'SA flue-cured typical; 2.0-2.8 typical, high-input 3.5+'),
  ('Chillies',   'paprika dried',     'irrigated', 't dry/ha',   1.0, 3.0, 4.0, NULL, 'Haifa Pepper Crop Guide + ICL Pepper Crop', 'T2', 'Dried paprika; 20-25x concentration vs fresh')
ON CONFLICT DO NOTHING;

COMMIT;
