-- Nutrient safety limits and toxicity thresholds
-- Used by liquid blend optimizer, programme builder, soil/tissue analysis

CREATE TABLE IF NOT EXISTS nutrient_limits (
    id SERIAL PRIMARY KEY,
    nutrient TEXT NOT NULL,               -- n, p, k, ca, mg, s, fe, b, mn, zn, mo, cu
    -- Liquid blend optimizer ceiling (g/L in concentrate)
    liquid_max_g_per_l NUMERIC,
    -- Foliar spray max (g/L of element in tank mix)
    foliar_max_g_per_l NUMERIC,
    -- Fertigation max (mg/L in irrigation water)
    fertigation_max_mg_per_l NUMERIC,
    -- Soil toxicity threshold
    soil_tox_method TEXT,                 -- extraction method (DTPA, Bray-1, KCl, etc.)
    soil_tox_threshold NUMERIC,           -- mg/kg
    soil_tox_notes TEXT,
    -- General notes
    notes TEXT,
    UNIQUE(nutrient)
);

-- Tissue toxicity thresholds per crop
CREATE TABLE IF NOT EXISTS tissue_toxicity (
    id SERIAL PRIMARY KEY,
    crop TEXT NOT NULL,                    -- citrus, avocado, macadamia, maize, general
    nutrient TEXT NOT NULL,               -- n, p, k, ca, mg, s, fe, b, mn, zn, mo, cu
    excessive_value NUMERIC,              -- above this = excessive
    toxic_value NUMERIC,                  -- above this = toxic symptoms
    unit TEXT NOT NULL DEFAULT 'mg/kg',   -- mg/kg or %
    notes TEXT,
    UNIQUE(crop, nutrient)
);

-- Nutrient interaction warnings
CREATE TABLE IF NOT EXISTS nutrient_interactions (
    id SERIAL PRIMARY KEY,
    condition TEXT NOT NULL,               -- e.g. "Low pH + high Mn"
    mechanism TEXT,                        -- scientific explanation
    action TEXT,                           -- recommended corrective action
    crops TEXT[],                          -- applicable crops
    severity TEXT DEFAULT 'warning'        -- warning, caution, critical
);

-- ── Seed nutrient_limits ────────────────────────────────────────────────
INSERT INTO nutrient_limits (nutrient, liquid_max_g_per_l, foliar_max_g_per_l, fertigation_max_mg_per_l, soil_tox_method, soil_tox_threshold, soil_tox_notes, notes) VALUES
('n',  20.0, 5.0,  250, NULL,          NULL, NULL,                                'Urea foliar max 5 g/L; nitrate tolerates 10; ammonium only 2'),
('p',  15.0, 2.0,  100, 'Bray-1',     150,  'Induces Zn/Fe deficiency',          'Via MKP at ~1%'),
('k',  20.0, 5.0,  300, 'Amm. acetate',600, 'Induces Mg deficiency',             'KCl lower for Cl-sensitive crops'),
('ca', 15.0, 4.0,  200, NULL,          NULL, NULL,                                'Ca(NO3)2 limit; CaCl2 only 2 g/L'),
('mg', 10.0, 4.0,  60,  NULL,          NULL, NULL,                                'MgSO4; maintain Ca:Mg > 2:1'),
('s',  15.0, 10.0, 500, NULL,          NULL, NULL,                                'Rarely limiting; salt load is constraint'),
('fe', 2.0,  1.0,  5.0, 'DTPA',       200,  'Acid/waterlogged soils',            'Chelate limit; FeSO4 tolerates 2.5 g/L'),
('b',  0.5,  0.2,  1.0, 'Hot water',  2.0,  'Sensitive crops; tolerant 5.0',     'NARROWEST safe range — citrus max 0.05 foliar'),
('mn', 3.0,  2.5,  2.0, 'KCl',        100,  'At pH < 5.5; lime to correct',      'MnSO4'),
('zn', 3.0,  2.5,  2.0, 'DTPA',       20,   'Acid soils increase risk',          'ZnSO4; chelate only 0.5 g/L'),
('mo', 0.3,  0.25, 0.05,NULL,          NULL, NULL,                                'Animal toxicity concern > plant toxicity'),
('cu', 1.0,  0.5,  0.2, 'DTPA',       20,   'Old orchard soils with Cu buildup', 'Only with lime (Bordeaux) for CuSO4')
ON CONFLICT (nutrient) DO UPDATE SET
    liquid_max_g_per_l = EXCLUDED.liquid_max_g_per_l,
    foliar_max_g_per_l = EXCLUDED.foliar_max_g_per_l,
    fertigation_max_mg_per_l = EXCLUDED.fertigation_max_mg_per_l,
    soil_tox_method = EXCLUDED.soil_tox_method,
    soil_tox_threshold = EXCLUDED.soil_tox_threshold,
    soil_tox_notes = EXCLUDED.soil_tox_notes,
    notes = EXCLUDED.notes;

-- ── Seed tissue_toxicity ────────────────────────────────────────────────
INSERT INTO tissue_toxicity (crop, nutrient, excessive_value, toxic_value, unit, notes) VALUES
-- Citrus
('citrus', 'n',  3.0,  5.0,  '%',    'Normal 2.2-2.7%'),
('citrus', 'p',  0.22, 1.0,  '%',    'Normal 0.09-0.16%'),
('citrus', 'k',  2.0,  NULL, '%',    'Induces Ca/Mg deficiency'),
('citrus', 'ca', 6.0,  NULL, '%',    'Normal 3.0-5.0%'),
('citrus', 'mg', 0.6,  NULL, '%',    'Normal 0.25-0.50%'),
('citrus', 's',  0.5,  NULL, '%',    'Normal 0.20-0.40%'),
('citrus', 'fe', 200,  500,  'mg/kg','Normal 60-120'),
('citrus', 'b',  100,  200,  'mg/kg','Normal 36-100; yellow spotting'),
('citrus', 'mn', 300,  1000, 'mg/kg','Normal 25-100'),
('citrus', 'zn', 100,  300,  'mg/kg','Normal 25-100'),
('citrus', 'mo', 50,   100,  'mg/kg','Normal 0.1-3.0'),
('citrus', 'cu', 20,   50,   'mg/kg','Normal 5-16; wash before analysis'),
('citrus', 'cl', 3000, 7000, 'mg/kg','Normal 100-3000; rootstock dependent'),
-- Avocado
('avocado', 'n',  2.6,  NULL, '%',    'Normal 1.6-2.2%'),
('avocado', 'p',  0.15, NULL, '%',    'Normal 0.05-0.12%'),
('avocado', 'k',  2.5,  NULL, '%',    'Normal 0.75-2.0%'),
('avocado', 'ca', 3.0,  NULL, '%',    'Normal 0.5-2.0%'),
('avocado', 'mg', 1.0,  NULL, '%',    'Normal 0.25-0.80%'),
('avocado', 's',  0.6,  NULL, '%',    'Normal 0.2-0.5%'),
('avocado', 'fe', 300,  NULL, 'mg/kg','Normal 50-200'),
('avocado', 'b',  100,  200,  'mg/kg','Normal 25-75'),
('avocado', 'mn', 1000, NULL, 'mg/kg','Normal 50-500; accumulates in acid soils'),
('avocado', 'zn', 100,  NULL, 'mg/kg','Normal 30-80'),
('avocado', 'mo', 50,   NULL, 'mg/kg','Limited data'),
('avocado', 'cu', 20,   NULL, 'mg/kg','Normal 5-15'),
('avocado', 'cl', 2500, NULL, 'mg/kg','Normal 200-1500; very Cl-sensitive'),
-- Macadamia
('macadamia', 'n',  1.8,  NULL, '%',    'Normal 1.2-1.6%'),
('macadamia', 'p',  0.15, NULL, '%',    'Normal 0.06-0.10%'),
('macadamia', 'k',  1.0,  NULL, '%',    'Normal 0.35-0.70%'),
('macadamia', 'ca', 1.0,  NULL, '%',    'Normal 0.2-0.6%'),
('macadamia', 'mg', 0.3,  NULL, '%',    'Normal 0.08-0.20%'),
('macadamia', 'fe', 300,  NULL, 'mg/kg','Normal 50-200'),
('macadamia', 'b',  100,  NULL, 'mg/kg','Normal 25-75'),
('macadamia', 'mn', 1000, NULL, 'mg/kg','Normal 100-600; Mn-sensitive crop'),
('macadamia', 'zn', 80,   NULL, 'mg/kg','Normal 10-50'),
('macadamia', 'cu', 20,   NULL, 'mg/kg','Normal 3-15'),
('macadamia', 'cl', 5000, NULL, 'mg/kg','Limited data'),
-- Maize
('maize', 'n',  3.5,  NULL, '%',    'Ear leaf; normal 2.5-3.5%'),
('maize', 'p',  0.5,  NULL, '%',    'Normal 0.20-0.40%'),
('maize', 'k',  2.5,  NULL, '%',    'Normal 1.7-2.5%'),
('maize', 'mg', 0.6,  NULL, '%',    'Normal 0.15-0.45%'),
('maize', 's',  0.5,  NULL, '%',    'Normal 0.15-0.40%'),
('maize', 'fe', 500,  NULL, 'mg/kg','Normal 50-300'),
('maize', 'b',  100,  NULL, 'mg/kg','Normal 5-25; tolerant crop'),
('maize', 'mn', 200,  300,  'mg/kg','Normal 20-150'),
('maize', 'zn', 100,  NULL, 'mg/kg','Normal 20-70'),
('maize', 'mo', 50,   NULL, 'mg/kg','Limited data'),
('maize', 'cu', 25,   NULL, 'mg/kg','Normal 6-20')
ON CONFLICT (crop, nutrient) DO UPDATE SET
    excessive_value = EXCLUDED.excessive_value,
    toxic_value = EXCLUDED.toxic_value,
    unit = EXCLUDED.unit,
    notes = EXCLUDED.notes;

-- ── Seed nutrient_interactions ──────────────────────────────────────────
INSERT INTO nutrient_interactions (condition, mechanism, action, crops, severity) VALUES
('Low pH + high Mn',      'pH < 5.0 mobilizes Mn²⁺',                        'Lime to pH 5.5+',                                    ARRAY['macadamia','avocado'], 'critical'),
('Low pH + high Al',      'pH < 5.0 mobilizes Al³⁺ — root toxicity',        'Lime; Al saturation >20% is toxic',                   ARRAY['all'],                'critical'),
('High P + low Zn',       'P suppresses Zn uptake',                          'Include Zn if Bray P > 80 mg/kg',                     ARRAY['maize'],              'warning'),
('High P + low Fe',       'P precipitates Fe',                               'Apply Fe chelate',                                    ARRAY['citrus'],             'warning'),
('High K + low Ca/Mg',    'Cation antagonism',                               'Maintain K:Ca:Mg ratios',                             ARRAY['all'],                'warning'),
('High Cu + low Fe',      'Cu competes with Fe at root uptake',              'Apply Fe chelate in old Cu-sprayed orchards',          ARRAY['citrus'],             'warning'),
('High Zn + low Fe',      'Zn competes with Fe uptake',                      'Don''t over-apply Zn foliar',                         ARRAY['all'],                'caution'),
('High Mn + low Fe',      'Mn and Fe compete for same transporters',         'Address pH first',                                    ARRAY['all'],                'warning'),
('High B + dry conditions','B concentrates as soil dries',                    'B toxicity worse in SA winter dry periods',            ARRAY['citrus','avocado'],   'caution'),
('High Cl + high Na',     'Combined salinity/sodicity stress',               'Check borehole water quality',                        ARRAY['avocado','citrus'],   'warning')
ON CONFLICT DO NOTHING;
