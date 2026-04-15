-- ============================================================
-- Seed: Liquid/foliar product catalog (42 products)
-- Nutrient values in g/kg (dry) or g/L (liquid) as specified
-- Trace elements in mg/kg or mg/L
-- ============================================================

INSERT INTO liquid_products (name, product_type, batch_size_kg, batch_size_l, sg, analysis_unit,
    n, p, k, ca, mg, s, fe, b, mn, zn, mo, cu, cl, recipe, target_crops, notes)
VALUES

-- ── FOLIAR SPRAYS ────────────────────────────────────────────────────

('Citrospray', 'foliar', 100, NULL, NULL, 'g/kg',
    317, 0, 0, 0, 0, 20, 0, 14, 33, 82, 0, 0, 0,
    '[{"material":"Urea LB","kg":69.021},{"material":"Solubor","kg":6.848},{"material":"Manganese Sulphate","kg":13.752},{"material":"Zinc Oxide","kg":10.379}]',
    '{"Citrus"}', 'Basic citrus foliar — N + traces'),

('NU-Citrospray', 'foliar', 100, NULL, NULL, 'g/kg',
    288, 0, 0, 0, 0, 0, 0, 13, 30, 74, 0, 47, 0,
    '[{"material":"Urea LB","kg":62.549},{"material":"Solubor","kg":6.144},{"material":"Copper Oxy Chloride","kg":9.494},{"material":"Manganese Sulphate","kg":12.446},{"material":"Zinc Oxide","kg":9.367}]',
    '{"Citrus"}', 'Citrus foliar with copper'),

('Cotton K', 'foliar', 100, NULL, NULL, 'g/kg',
    118, 0, 346, 0, 0, 0, 0, 18, 0, 0, 0, 0, 0,
    '[{"material":"Potassium Nitrate","kg":91.1},{"material":"Solubor","kg":8.9}]',
    '{"Cotton"}', 'K-heavy cotton foliar'),

('Folifeed', 'foliar', 100, NULL, NULL, 'g/kg',
    264, 42, 134, 0, 0.9, 0, 0.52, 0.65, 0.3, 0.35, 0.07, 0.075, 0,
    '[{"material":"Potassium Nitrate","kg":35.32},{"material":"MAP","kg":15.489},{"material":"Urea LB","kg":43.266},{"material":"Magnesium Nitrate","kg":0.947},{"material":"Iron EDTA Chelate","kg":0.4},{"material":"Copper Sulphate","kg":0.03},{"material":"Manganese Sulphate","kg":0.124},{"material":"Solubor","kg":0.317},{"material":"Sodium Molybdate","kg":0.018},{"material":"Citric Acid","kg":3.989},{"material":"Zinc Sulphate","kg":0.1}]',
    NULL, 'General foliar — high N with full traces'),

('Fosfaspray', 'foliar', 100, NULL, NULL, 'g/kg',
    94, 253, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '[{"material":"MAP","kg":78.658},{"material":"MKP","kg":18.085},{"material":"Citric Acid","kg":1.95}]',
    NULL, 'High-P foliar spray'),

('Macrospray 3:1:5', 'foliar', 100, NULL, NULL, 'g/kg',
    156, 52, 261, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '[{"material":"MAP","kg":19.377},{"material":"Potassium Nitrate","kg":68.588},{"material":"Urea LB","kg":9.475},{"material":"Citric Acid","kg":2.56}]',
    NULL, 'General NPK foliar — 3:1:5 ratio'),

('Equifeed 1:1:1', 'foliar', 100, NULL, NULL, 'g/kg',
    143, 143, 143, 0, 0, 0, 1.005, 0.26, 0.51, 0.51, 0.0084, 0.51, 0,
    '[{"material":"Librel BMX","kg":3},{"material":"Urea LB","kg":6.645},{"material":"MAP","kg":52.821},{"material":"Potassium Nitrate","kg":37.534}]',
    NULL, 'Balanced 1:1:1 with traces'),

('Manzinc Spray', 'foliar', 100, NULL, NULL, 'g/kg',
    0, 0, 0, 0, 0, 0, 0, 0, 121, 180, 0, 0, 0,
    '[{"material":"Manganese Sulphate","kg":50.069},{"material":"Zinc Sulphate","kg":49.931}]',
    NULL, 'Mn + Zn correction spray'),

('Mobonspray', 'foliar', 100, NULL, NULL, 'g/kg',
    0, 0, 0, 0, 0, 0, 0, 165, 0, 0, 24, 0, 0,
    '[{"material":"Solubor","kg":80.488},{"material":"Sodium Molybdate","kg":6.076}]',
    NULL, 'B + Mo spray — for legume nodulation and fruit set'),

('Spoorspray 30', 'foliar', 100, NULL, NULL, 'g/kg',
    0, 0, 0, 0, 0, 0, 0, 0, 104, 146, 0, 55, 0,
    '[{"material":"Zinc Sulphate","kg":40.556},{"material":"Manganese Sulphate","kg":43.1},{"material":"Copper Oxy Chloride","kg":11}]',
    NULL, 'Trace element spray — Zn, Mn, Cu'),

('Spoorspray 15', 'foliar', 100, NULL, NULL, 'g/kg',
    0, 0, 0, 0, 0, 0, 184, 58, 0, 0, 11, 0, 0,
    '[{"material":"Ferrous Sulphate","kg":53.136},{"material":"Solubor","kg":28.142},{"material":"Sodium Molybdate","kg":2.85},{"material":"Citric Acid","kg":4.334}]',
    NULL, 'Trace element spray — Fe, B, Mo'),

-- ── FERTIGATION / LIQUID FERTILIZERS ────────────────────────────────

('Calmabon Dry', 'fertigation', 100, NULL, NULL, 'g/kg',
    139, 0, 0, 139, 27, 0, 0, 2.29, 0, 0, 2.71, 0, 0,
    '[{"material":"Calcium Nitrate","kg":69.645},{"material":"Magnesium Nitrate","kg":28.663},{"material":"Solubor","kg":1.117},{"material":"Sodium Molybdate","kg":0.575}]',
    NULL, 'Ca-Mg-B-Mo mix for Ca-hungry crops'),

('Calmabon Liquid', 'fertigation', NULL, 1000, NULL, 'g/l',
    133, 0, 0, 132, 26, 0, 0, 2.289, 0, 0, 2.275, 0, 0,
    '[{"material":"Calcium Nitrate","kg":665},{"material":"Magnesium Nitrate","kg":273.685},{"material":"Solubor","kg":11.165},{"material":"Sodium Molybdate","kg":5.76}]',
    NULL, 'Liquid Ca-Mg-B-Mo'),

('Calmag + Boron', 'fertigation', 100, NULL, NULL, 'g/kg',
    136, 0, 0, 120, 37, 0, 0, 2, 0, 0, 0, 0, 0,
    '[{"material":"Magnesium Nitrate","kg":39.223},{"material":"Calcium Nitrate","kg":59.78},{"material":"Solubor","kg":0.997}]',
    NULL, 'Ca-Mg-B for fruit crops'),

('Camax Foliar', 'fertigation', NULL, 1000, 1.54, 'g/l',
    129, 0, 0, 128, 26, 0, 1.5, 1.511, 0.75, 0.75, 0.103, 0.75, 0,
    '[{"material":"Magnesium Nitrate","kg":273.684},{"material":"Calcium Nitrate","kg":640},{"material":"Librel BMX","kg":44.1},{"material":"Iron EDTA Chelate","kg":0.17},{"material":"Solubor","kg":5.5},{"material":"Sodium Molybdate","kg":0.23}]',
    NULL, 'Concentrated Ca-Mg with full traces — SG 1.54'),

('Citrogro', 'fertigation', 100, NULL, NULL, 'g/kg',
    138, 22, 71, 86, 21, 15, 2.158, 0.433, 0.058, 1.771, 0.043, 0.042, 0,
    '[{"material":"MAP","kg":8.111},{"material":"Potassium Nitrate","kg":18.6},{"material":"Magnesium Nitrate","kg":22.006},{"material":"Calcium Nitrate","kg":42.807},{"material":"Ammonium Sulphate","kg":6.092},{"material":"Iron EDTA Chelate","kg":1.628},{"material":"Manganese Sulphate","kg":0.028},{"material":"Zinc Sulphate","kg":0.49},{"material":"Copper Sulphate","kg":0.017},{"material":"Solubor","kg":0.21},{"material":"Sodium Molybdate","kg":0.011}]',
    '{"Citrus"}', 'Complete citrus fertigation — full macro + micro'),

('Dripfeed', 'fertigation', 100, NULL, NULL, 'g/kg',
    189, 85, 157, 0, 0.9, 0, 0.75, 1.2, 0.35, 0.35, 0.075, 0.08, 0,
    '[{"material":"Potassium Nitrate","kg":41.301},{"material":"MAP","kg":31.457},{"material":"Urea LB","kg":21.055},{"material":"Magnesium Nitrate","kg":0.947},{"material":"Iron EDTA Chelate","kg":0.577},{"material":"Manganese Sulphate","kg":0.145},{"material":"Copper Sulphate","kg":0.032},{"material":"Zinc Sulphate","kg":0.097},{"material":"Solubor","kg":0.585},{"material":"Sodium Molybdate","kg":0.019},{"material":"Citric Acid","kg":3.785}]',
    NULL, 'General fertigation — NPK with traces'),

('Hydrofeed', 'fertigation', 100, NULL, NULL, 'g/kg',
    107, 22, 152, 75, 15, 34, 0.391, 0.469, 0.198, 0.198, 0.032, 0.198, 0,
    '[{"material":"Calcium Nitrate","kg":37.443},{"material":"Magnesium Sulphate","kg":14.832},{"material":"Potassium Sulphate","kg":8.845},{"material":"Potassium Nitrate","kg":30.153},{"material":"MAP","kg":7.976},{"material":"Sodium Molybdate","kg":0.008},{"material":"Manganese Sulphate","kg":0.082},{"material":"Zinc Sulphate","kg":0.055},{"material":"Copper Sulphate","kg":0.079},{"material":"Iron EDTA Chelate","kg":0.301},{"material":"Solubor","kg":0.299}]',
    NULL, 'Complete fertigation with Ca — requires A/B tank split'),

('Hygrofert A', 'fertigation', 100, NULL, NULL, 'g/kg',
    136, 68, 209, 0, 10, 13, 1.871, 0.557, 0.445, 0.223, 0.056, 0.033, 0,
    '[{"material":"Magnesium Sulphate","kg":10.101},{"material":"Potassium Nitrate","kg":54.991},{"material":"MAP","kg":25.316},{"material":"Urea LB","kg":7.365},{"material":"Hygroplex","kg":2.227}]',
    NULL, 'A-tank fertigation — no calcium, P-compatible'),

('Hygrofert B', 'fertigation', 100, NULL, NULL, 'g/kg',
    153, 69, 183, 0, 11, 14, 1.885, 0.561, 0.449, 0.224, 0.056, 0.034, 0,
    '[{"material":"Magnesium Sulphate","kg":11.112},{"material":"Potassium Nitrate","kg":48.245},{"material":"MAP","kg":25.417},{"material":"Urea LB","kg":12.982},{"material":"Hygroplex","kg":2.244}]',
    NULL, 'A-tank fertigation — higher N variant'),

('Hygrofert C', 'fertigation', 100, NULL, NULL, 'g/kg',
    101, 0, 87, 125, 18, 23, 1.26, 0.375, 0.3, 0.15, 0.038, 0.023, 59,
    '[{"material":"Calcium Nitrate","kg":45.767},{"material":"Calcium Chloride","kg":11.939},{"material":"Potassium Nitrate","kg":22.883},{"material":"Magnesium Sulphate","kg":17.911},{"material":"Hygroplex","kg":1.5}]',
    NULL, 'B-tank fertigation — calcium-rich, no phosphate'),

('Hygrofert Chips', 'fertigation', 100, NULL, NULL, 'g/kg',
    102, 51, 157, 0, 32, 42, 1.403, 0.418, 0.334, 0.167, 0.042, 0.027, 0,
    '[{"material":"Magnesium Sulphate","kg":32.575},{"material":"Potassium Nitrate","kg":41.243},{"material":"MAP","kg":18.987},{"material":"Urea LB","kg":5.524},{"material":"Hygroplex","kg":1.67}]',
    NULL, 'Soluble chip format — high Mg'),

('Hygrofert P', 'fertigation', 100, NULL, NULL, 'g/kg',
    68, 42, 208, 0, 30, 64, 1.254, 0.373, 0.299, 0.149, 0.037, 0.022, 0,
    '[{"material":"Hygroplex","kg":1.493},{"material":"Magnesium Sulphate","kg":29.851},{"material":"MAP","kg":15.423},{"material":"Potassium Nitrate","kg":37.811},{"material":"Potassium Sulphate","kg":15.422}]',
    NULL, 'K-heavy fertigation with high S and Mg'),

('Hygrophil', 'fertigation', 100, NULL, NULL, 'g/kg',
    98, 92, 245, 0, 0, 31, 2.856, 0.85, 0.68, 0.34, 0.085, 0.054, 0,
    '[{"material":"MAP","kg":34},{"material":"Potassium Nitrate","kg":44.2},{"material":"Potassium Sulphate","kg":18.4},{"material":"Hygroplex","kg":3.4}]',
    NULL, 'K-dominant fertigation'),

('Hyperfeed', 'fertigation', 100, NULL, NULL, 'g/kg',
    156, 52, 260, 0, 0.9, 0, 1.0, 1.2, 0.5, 0.5, 0.075, 0.5, 0,
    '[{"material":"Potassium Nitrate","kg":68.523},{"material":"MAP","kg":19.358},{"material":"Urea LB","kg":9.251},{"material":"Magnesium Nitrate","kg":0.947},{"material":"Zinc Sulphate","kg":0.14},{"material":"Copper Sulphate","kg":0.201},{"material":"Iron EDTA Chelate","kg":0.769},{"material":"Manganese Sulphate","kg":0.207},{"material":"Solubor","kg":0.585},{"material":"Sodium Molybdate","kg":0.019}]',
    NULL, 'High-K fertigation 3:1:5 with traces'),

('Nutra-Phos 45 SP', 'fertigation', 100, NULL, NULL, 'g/kg',
    60, 248, 141, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '[{"material":"MAP","kg":50},{"material":"MKP","kg":50}]',
    NULL, 'High-P starter — simple 2-component'),

('Stimufoliar', 'fertigation', NULL, 1000, 1.22, 'g/l',
    73, 18, 109, 0, 0, 0, 1.248, 1.251, 0.624, 0.126, 0.079, 0.63, 0,
    '[{"material":"MKP","kg":35.7},{"material":"Potassium Nitrate","kg":220},{"material":"MAP","kg":36.8},{"material":"Urea LB","kg":87},{"material":"Manganese Chelate","kg":4.8},{"material":"Iron EDTA Chelate","kg":9.6},{"material":"Copper Chelate","kg":4.5},{"material":"Zinc Chelate","kg":0.9},{"material":"Solubor","kg":6.1},{"material":"Sodium Molybdate","kg":0.2}]',
    NULL, 'Concentrated K-dominant with full chelated traces'),

('Aquafert 1', 'fertigation', NULL, NULL, NULL, 'g/l',
    77, 0, 85.8, 60, 15, 0, 0, 0, 0, 0, 0, 0, 36,
    '[{"material":"Calcium Chloride","kg":73.9},{"material":"Magnesium Nitrate","kg":157.895},{"material":"Potassium Nitrate","kg":225.789},{"material":"Calcium Nitrate","kg":197.25},{"material":"Citric Acid","kg":30.75}]',
    NULL, 'Liquid N-K-Ca-Mg — complete macro without P'),

('Rose 8:1:5', 'fertigation', 100, NULL, NULL, 'g/kg',
    269, 34, 167, 0, 0, 0, 0.52, 0.65, 0.3, 0.36, 0.07, 0.075, 0,
    '[{"material":"MAP","kg":12.452},{"material":"Potassium Nitrate","kg":44.031},{"material":"Urea LB","kg":42.778},{"material":"Ferrous Sulphate","kg":0.15},{"material":"Zinc Sulphate","kg":0.1},{"material":"Manganese Sulphate","kg":0.124},{"material":"Copper Sulphate","kg":0.03},{"material":"Solubor","kg":0.317},{"material":"Sodium Molybdate","kg":0.018}]',
    '{"Rose"}', 'Rose fertigation — 8:1:5 with traces'),

-- ── CROP-SPECIFIC FERTIGATION ────────────────────────────────────────

('Pepper A', 'fertigation', 100, NULL, NULL, 'g/kg',
    33, 64, 371, 0, 0, 79, 0, 0, 0, 0, 0, 0, 0,
    '[{"material":"Potassium Nitrate","kg":25.375},{"material":"Potassium Sulphate","kg":46.454},{"material":"MKP","kg":28.171}]',
    '{"Pepper"}', 'Pepper A-tank — very high K'),

('Pepper C', 'fertigation', 100, NULL, NULL, 'g/kg',
    131, 0, 0, 161, 28, 0, 0.974, 0.29, 0.232, 0.116, 0.029, 0.017, 29,
    '[{"material":"Magnesium Nitrate","kg":23.083},{"material":"Calcium Nitrate","kg":63.96},{"material":"Calcium Chloride","kg":5.797},{"material":"Hygroplex","kg":1.16}]',
    '{"Pepper"}', 'Pepper B-tank — calcium-rich'),

('Tomato C', 'fertigation', 100, NULL, NULL, 'g/kg',
    50, 0, 54, 114, 36, 68, 0.588, 0.175, 0.14, 0.07, 0.016, 0.011, 88,
    '[{"material":"Calcium Chloride","kg":17.91},{"material":"Calcium Nitrate","kg":32.337},{"material":"Potassium Sulphate","kg":12.935},{"material":"Magnesium Sulphate","kg":36.118},{"material":"Hygroplex","kg":0.7}]',
    '{"Tomato"}', 'Tomato B-tank — Ca-Mg-S heavy'),

('Tunnel Tomato', 'fertigation', 100, NULL, NULL, 'g/kg',
    27, 44, 197, 0, 44, 0, 1.42, 0.423, 0.338, 0.372, 0.042, 0.025, 0,
    '[{"material":"Magnesium Sulphate","kg":44.425},{"material":"Potassium Nitrate","kg":20.943},{"material":"MKP","kg":19.461},{"material":"Potassium Sulphate","kg":14.858},{"material":"Hygroplex","kg":0.169},{"material":"Zinc Chelate","kg":0.145}]',
    '{"Tomato"}', 'Tunnel tomato A-tank — K-Mg heavy'),

('Strawberry 8-12-32', 'fertigation', 100, NULL, NULL, 'g/kg',
    95, 66, 290, 0, 5, 3, 3.0, 0.8, 1.5, 0.3, 0.08, 0.5, 0,
    '[{"material":"MAP","kg":7.12},{"material":"MKP","kg":16.246},{"material":"Potassium Nitrate","kg":63.537},{"material":"Magnesium Nitrate","kg":3.194},{"material":"Magnesium Sulphate","kg":1.985},{"material":"Citric Acid","kg":3},{"material":"Solubor","kg":0.39},{"material":"Sodium Molybdate","kg":0.02},{"material":"Manganese Sulphate","kg":0.622},{"material":"Iron EDTA Chelate","kg":2.308}]',
    '{"Strawberry"}', 'Strawberry fertigation — very high K'),

('Cucumber Fertigation', 'fertigation', 100, NULL, NULL, 'g/kg',
    122, 8, 139, 77, 19, 25, 0.25, 0.12, 0.15, 0.15, 0.025, 0.02, 0,
    '[{"material":"Magnesium Sulphate","kg":19.432},{"material":"Calcium Nitrate","kg":38.476},{"material":"MAP","kg":2.85},{"material":"Potassium Nitrate","kg":36.451},{"material":"Urea LB","kg":2.422},{"material":"Iron EDTA Chelate","kg":0.192},{"material":"Manganese Sulphate","kg":0.062},{"material":"Zinc Sulphate","kg":0.042},{"material":"Copper Sulphate","kg":0.008},{"material":"Solubor","kg":0.059},{"material":"Sodium Molybdate","kg":0.006}]',
    '{"Cucumber"}', 'Complete cucumber mix — requires A/B split for Ca'),

('Papaya Special', 'fertigation', 100, NULL, NULL, 'g/kg',
    96, 50, 79, 47, 26, 16, 16, 0.26, 1.3, 0.78, 0.13, 0.08, 0,
    '[{"material":"Calcium Nitrate","kg":23.47},{"material":"Potassium Nitrate","kg":14.114},{"material":"Magnesium Sulphate","kg":12.254},{"material":"Magnesium Nitrate","kg":14.64},{"material":"MAP","kg":10.7},{"material":"MKP","kg":9.146},{"material":"Urea LB","kg":1.918},{"material":"Solubor","kg":0.127},{"material":"Iron EDTA Chelate","kg":12.019},{"material":"Manganese Chelate","kg":1.002},{"material":"Copper Chelate","kg":0.056},{"material":"Sodium Molybdate","kg":0.033}]',
    '{"Papaya"}', 'Complete papaya mix — very high Fe'),

('Inca Lily Special', 'fertigation', 100, NULL, NULL, 'g/kg',
    81, 7, 68, 93, 34, 55, 0, 0, 0, 0, 0, 0, 0,
    '[{"material":"MKP","kg":3.159},{"material":"Potassium Nitrate","kg":7.559},{"material":"Magnesium Sulphate","kg":33.96},{"material":"Potassium Sulphate","kg":7.133},{"material":"Calcium Nitrate","kg":46.189},{"material":"Citric Acid","kg":2}]',
    '{"Alstroemeria","Cut Flowers"}', 'Inca lily — Ca-Mg-S dominant'),

-- ── HYDROPONIC ────────────────────────────────────────────────────────

('Hydroponic Lettuce', 'hydroponic', 100, NULL, NULL, 'g/kg',
    150, 10, 180, 54, 13, 0, 0.25, 0.12, 0.15, 0.15, 0.025, 0.02, 0,
    '[{"material":"Iron EDTA Chelate","kg":0.192},{"material":"Manganese Sulphate","kg":0.062},{"material":"Zinc Sulphate","kg":0.042},{"material":"Copper Sulphate","kg":0.008},{"material":"Solubor","kg":0.059},{"material":"Sodium Molybdate","kg":0.006},{"material":"MAP","kg":3.704},{"material":"Potassium Sulphate","kg":8.824},{"material":"Potassium Nitrate","kg":37.616},{"material":"Calcium Nitrate","kg":26.776},{"material":"Magnesium Nitrate","kg":14.092},{"material":"Urea LB","kg":8.619}]',
    '{"Lettuce"}', 'Hydroponic lettuce — N-K dominant'),

('Hydroponic LTT', 'hydroponic', 100, NULL, NULL, 'g/kg',
    63, 43, 231, 0, 29, 58, 0.168, 0.5, 0.401, 0.202, 0.051, 0.03, 0,
    '[{"material":"Magnesium Sulphate","kg":29.199},{"material":"Potassium Sulphate","kg":11.908},{"material":"MKP","kg":9.472},{"material":"Potassium Nitrate","kg":40.67},{"material":"MAP","kg":8.131},{"material":"Copper Sulphate","kg":0.012},{"material":"Manganese Sulphate","kg":0.166},{"material":"Solubor","kg":0.244},{"material":"Zinc Sulphate","kg":0.056},{"material":"Sodium Molybdate","kg":0.013},{"material":"Iron EDTA Chelate","kg":0.129}]',
    NULL, 'General hydroponic — very high K'),

('Hygrobuff 7', 'hydroponic', NULL, 1, NULL, 'g/l',
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '[{"material":"Phosphoric Acid 80%","kg":0.49},{"material":"KOH 90%","kg":0.374}]',
    NULL, 'pH 7 buffer solution — for pH adjustment')

ON CONFLICT (name) DO UPDATE SET
    product_type = EXCLUDED.product_type,
    batch_size_kg = EXCLUDED.batch_size_kg,
    batch_size_l = EXCLUDED.batch_size_l,
    sg = EXCLUDED.sg,
    analysis_unit = EXCLUDED.analysis_unit,
    n = EXCLUDED.n, p = EXCLUDED.p, k = EXCLUDED.k,
    ca = EXCLUDED.ca, mg = EXCLUDED.mg, s = EXCLUDED.s,
    fe = EXCLUDED.fe, b = EXCLUDED.b, mn = EXCLUDED.mn,
    zn = EXCLUDED.zn, mo = EXCLUDED.mo, cu = EXCLUDED.cu, cl = EXCLUDED.cl,
    recipe = EXCLUDED.recipe,
    target_crops = EXCLUDED.target_crops,
    notes = EXCLUDED.notes;
