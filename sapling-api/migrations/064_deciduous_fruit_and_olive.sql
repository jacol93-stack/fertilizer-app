-- Deciduous fruit leaf norms (WSU Table 4) + olive (CDFA FREP)
DELETE FROM public.fertasa_leaf_norms WHERE crop IN ('Apple', 'Pear', 'Cherry', 'Peach', 'Nectarine', 'Apricot', 'Plum', 'Olive');

INSERT INTO public.fertasa_leaf_norms
    (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max, high_min, excess_min, sample_part, sample_timing, source_section, notes)
VALUES
    -- Apple (WSU Table 4; recently mature leaves, July-August)
    ('Apple', 'N',  '%',    NULL, 1.7,  1.7,  2.5,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', 'Honeycrisp: manage at lower end of range.'),
    ('Apple', 'P',  '%',    NULL, 0.15, 0.15, 0.3,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apple', 'K',  '%',    NULL, 1.2,  1.2,  1.9,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', 'Honeycrisp: manage at lower end.'),
    ('Apple', 'Ca', '%',    NULL, 1.5,  1.5,  2.0,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', 'Low Ca predisposes bitter pit; consider foliar Ca sprays in the 6-8 weeks before harvest.'),
    ('Apple', 'Mg', '%',    NULL, 0.25, 0.25, 0.35, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apple', 'S',  '%',    NULL, 0.01, 0.01, 0.10, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apple', 'Cu', 'mg/kg', NULL, 5,   5,    12,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apple', 'Zn', 'mg/kg', NULL, 15,  15,   200,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', 'Wide sufficient range.'),
    ('Apple', 'Mn', 'mg/kg', NULL, 25,  25,   150,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apple', 'Fe', 'mg/kg', NULL, 60,  60,   120,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', 'Total Fe is not a good indicator; use visual chlorosis + soil pH.'),
    ('Apple', 'B',  'mg/kg', NULL, 20,  20,   60,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    -- Pear
    ('Pear', 'N',  '%',    NULL, 1.8,  1.8,  2.6,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Pear', 'P',  '%',    NULL, 0.12, 0.12, 0.25, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Pear', 'K',  '%',    NULL, 1.0,  1.0,  2.0,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Pear', 'Ca', '%',    NULL, 1.0,  1.0,  3.7,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Pear', 'Mg', '%',    NULL, 0.25, 0.25, 0.90, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Pear', 'S',  '%',    NULL, 0.01, 0.01, 0.03, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Pear', 'Cu', 'mg/kg', NULL, 6,   6,    20,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Pear', 'Zn', 'mg/kg', NULL, 20,  20,   60,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Pear', 'Mn', 'mg/kg', NULL, 20,  20,   170,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Pear', 'Fe', 'mg/kg', NULL, 100, 100,  800,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', 'Total Fe not a reliable indicator; cross-check with visual chlorosis + soil pH.'),
    ('Pear', 'B',  'mg/kg', NULL, 20,  20,   60,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    -- Cherry (Sweet)
    ('Cherry', 'N',  '%',    NULL, 2.00, 2.00, 3.03, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'P',  '%',    NULL, 0.10, 0.10, 0.27, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'K',  '%',    NULL, 1.20, 1.20, 3.3,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'Ca', '%',    NULL, 1.20, 1.20, 2.37, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'Mg', '%',    NULL, 0.30, 0.30, 0.77, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'S',  '%',    NULL, 0.20, 0.20, 0.40, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'Cu', 'mg/kg', NULL, 0,   0,    16,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'Zn', 'mg/kg', NULL, 12,  12,   50,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'Mn', 'mg/kg', NULL, 17,  17,   160,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'Fe', 'mg/kg', NULL, 57,  57,   250,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Cherry', 'B',  'mg/kg', NULL, 17,  17,   60,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    -- Peach
    ('Peach', 'N',  '%',    NULL, 2.7,  2.7,  3.5,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'P',  '%',    NULL, 0.1,  0.1,  0.30, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'K',  '%',    NULL, 1.2,  1.2,  3.0,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'Ca', '%',    NULL, 1.0,  1.0,  2.5,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'Mg', '%',    NULL, 0.25, 0.25, 0.50, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'S',  '%',    NULL, 0.2,  0.2,  0.4,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'Cu', 'mg/kg', NULL, 4,   4,    16,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'Zn', 'mg/kg', NULL, 20,  20,   50,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'Mn', 'mg/kg', NULL, 20,  20,   200,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'Fe', 'mg/kg', NULL, 120, 120,  200,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Peach', 'B',  'mg/kg', NULL, 20,  20,   80,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    -- Nectarine (copies Peach — same species Prunus persica var. nucipersica)
    ('Nectarine', 'N',  '%',    NULL, 2.7,  2.7,  3.5,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', 'Nectarine = Prunus persica var. nucipersica; same species as peach. WSU does not publish separate nectarine norms.'),
    ('Nectarine', 'P',  '%',    NULL, 0.1,  0.1,  0.30, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    ('Nectarine', 'K',  '%',    NULL, 1.2,  1.2,  3.0,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    ('Nectarine', 'Ca', '%',    NULL, 1.0,  1.0,  2.5,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    ('Nectarine', 'Mg', '%',    NULL, 0.25, 0.25, 0.50, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    ('Nectarine', 'S',  '%',    NULL, 0.2,  0.2,  0.4,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    ('Nectarine', 'Cu', 'mg/kg', NULL, 4,   4,    16,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    ('Nectarine', 'Zn', 'mg/kg', NULL, 20,  20,   50,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    ('Nectarine', 'Mn', 'mg/kg', NULL, 20,  20,   200,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    ('Nectarine', 'Fe', 'mg/kg', NULL, 120, 120,  200,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    ('Nectarine', 'B',  'mg/kg', NULL, 20,  20,   80,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Peach)', NULL),
    -- Apricot
    ('Apricot', 'N',  '%',    NULL, 2.4,  2.4,  3.3,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'P',  '%',    NULL, 0.1,  0.1,  0.3,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'K',  '%',    NULL, 2.0,  2.0,  3.5,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'Ca', '%',    NULL, 1.10, 1.10, 4.00, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'Mg', '%',    NULL, 0.25, 0.25, 0.80, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'S',  '%',    NULL, 0.20, 0.20, 0.40, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'Cu', 'mg/kg', NULL, 4,   4,    16,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'Zn', 'mg/kg', NULL, 16,  16,   50,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'Mn', 'mg/kg', NULL, 20,  20,   160,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'Fe', 'mg/kg', NULL, 60,  60,   250,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    ('Apricot', 'B',  'mg/kg', NULL, 20,  20,   70,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4', NULL),
    -- Plum (uses Apricot norms — same Prunus genus; WSU Table 4 omits plum)
    ('Plum', 'N',  '%',    NULL, 2.4,  2.4,  3.3,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', 'WSU does not publish separate plum norms. Apricot values used as the closest Prunus-genus proxy; verify against Beyers 1958 SA leaf data when extraction available.'),
    ('Plum', 'P',  '%',    NULL, 0.1,  0.1,  0.3,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    ('Plum', 'K',  '%',    NULL, 2.0,  2.0,  3.5,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    ('Plum', 'Ca', '%',    NULL, 1.10, 1.10, 4.00, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    ('Plum', 'Mg', '%',    NULL, 0.25, 0.25, 0.80, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    ('Plum', 'S',  '%',    NULL, 0.20, 0.20, 0.40, NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    ('Plum', 'Cu', 'mg/kg', NULL, 4,   4,    16,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    ('Plum', 'Zn', 'mg/kg', NULL, 16,  16,   50,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    ('Plum', 'Mn', 'mg/kg', NULL, 20,  20,   160,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    ('Plum', 'Fe', 'mg/kg', NULL, 60,  60,   250,  NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    ('Plum', 'B',  'mg/kg', NULL, 20,  20,   70,   NULL, NULL, 'Recently mature leaves', 'July-August', 'WSU Table 4 (via Apricot)', NULL),
    -- Olive (CDFA FREP July leaf — full 4-band)
    ('Olive', 'N',  '%',    1.4,  1.4,  1.5,  2.0,  2.0,  2.0,  'Recently mature leaves', 'July', 'CDFA FREP Olive Guideline', 'Some studies suggest 1.7% is a better upper threshold due to fruit set / oil quality declines above that level.'),
    ('Olive', 'P',  '%',    NULL, 0.1,  0.1,  0.3,  NULL, NULL, 'Recently mature leaves', 'July', 'CDFA FREP Olive Guideline', 'Low leaf P usually indicates poor drainage, not P deficiency — fix drainage before applying P.'),
    ('Olive', 'K',  '%',    0.4,  0.4,  0.8,  NULL, NULL, NULL, 'Recently mature leaves', 'July', 'CDFA FREP Olive Guideline', NULL),
    ('Olive', 'B',  'mg/kg', 14,   14,   19,  150,  150,  185,  'Recently mature leaves', 'July', 'CDFA FREP Olive Guideline', 'Olives are more B-tolerant than most tree crops but still toxic above 185 ppm. 14-19 ppm may respond to B application without visible deficiency.');

-- Olive pH + B soil overrides
DELETE FROM public.crop_sufficiency_overrides WHERE crop = 'Olive';

INSERT INTO public.crop_sufficiency_overrides (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Olive', 'K', NULL, 125, NULL, NULL, 'CDFA: pre-plant minimum 125 ppm K for new orchards (per Vossen).'),
    ('Olive', 'B', NULL, 0.33, NULL, 2.0, 'CDFA: hot-water soil B below 0.33 = deficient (older literature used 0.5). Above 2 ppm saturated paste = toxicity risk.');

-- Olive annual N + K rates
DELETE FROM public.fertilizer_rate_tables WHERE crop = 'Olive';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha, water_regime, rate_min_kg_ha, rate_max_kg_ha, source, source_section, source_year, source_note)
VALUES
    ('Olive', 'N', 'elemental', 0, NULL, NULL, 44.8, 112.1, 'CDFA FREP Olive Guideline', 'SHD (super-high density)', 2020,
        '40-100 lb N/ac = 44.8-112.1 kg N/ha annual for super-high-density orchards. Spanish Arbequina reference: ~80 lb/ac in harvested fruit + prunings. Soil applications: February to September; avoid before January (leaching risk).'),
    ('Olive', 'N', 'elemental', 0, NULL, NULL, 48.2, 95.3, 'CDFA FREP Olive Guideline', 'Traditional density ~85 trees/ac', 2020,
        '0.5-1.0 lb N/tree × ~85 trees/ac = 43-85 lb/ac = 48.2-95.3 kg N/ha. Young trees: mature rate × % canopy cover.'),
    ('Olive', 'K', 'elemental', 0, NULL, NULL, 70, 93, 'CDFA FREP Olive Guideline', 'K removal reference (irrigated)', 2020,
        'Irrigated K removal in fruit: 15-20 lb K2O/ton harvested × 5 t/ac typical = 75-100 lb K2O/ac ≈ 70-93 kg K/ha. Use for replenishment planning.');
