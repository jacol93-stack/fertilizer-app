-- ============================================================
-- 047: Seed wheat P rate table (FERTASA 5.4.3.1.2)
-- ============================================================
-- Source: sapling-api/data/fertasa_handbook/5_4_3_wheat.json (tables[3])
--
-- Published context: Dryland summer-rainfall regions (Free State,
-- North West, Mpumalanga, Limpopo, Eastern Cape coastal). The
-- handbook notes: "The same guidelines can be applied to other
-- winter cereals." Western Cape winter-rainfall has a separate
-- table (5.4.3.2.5) which will be seeded in a later migration.
--
-- Table shape:
--   yield targets (t/ha): 1.0, 1.5, 2.0, 2.5+
--   soil-P bands (mg/kg Bray-1): <5, 5-18, 18-30, >30
--   cells: kg P/ha (some exact, some ranges)
--   footnote *: "Minimum amount to be applied at low soil-P levels"
--     (applies to the <5 and 5-18 columns).
--
-- Conservative storage decisions:
--   * Yield modelled as discrete published points (min = max)
--     except the open-top 2.5+ band (min=2.5, max=NULL).
--     Lookup snaps to nearest discrete point; yields >= 2.5
--     always land on the open-top band regardless of distance.
--   * Soil-P bands stored as half-open intervals [min, max).
--     <5 => (0, 5). 5-18 => (5, 18). 18-30 => (18, 30).
--     >30 => (30, NULL).
--   * Cell ranges (e.g., "4 - 6") stored as min/max. Exact
--     cells (e.g., "6") stored with min = max.
--   * water_regime = 'dryland'; region left NULL (applies broadly
--     across summer-rainfall zones; more-specific rows can
--     override via extra third-axis filters in future seeds).
-- ============================================================

BEGIN;

-- Guard against duplicate seeding if this migration ever re-runs
DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Wheat'
  AND nutrient = 'P'
  AND source_section = '5.4.3.1.2';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- Yield 1.0 t/ha
    ('Wheat', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 6,  6,  'FERTASA Handbook', '5.4.3.1.2', 2019, 'Minimum amount to be applied at low soil-P levels (*)'),
    ('Wheat', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 5,  18,   'dryland', 4,  6,  'FERTASA Handbook', '5.4.3.1.2', 2019, 'Minimum amount to be applied at low soil-P levels (*)'),
    ('Wheat', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 18, 30,   'dryland', 4,  4,  'FERTASA Handbook', '5.4.3.1.2', 2019, NULL),
    ('Wheat', 'P', 'elemental', 1.0, 1.0, 'Bray-1', 'mg/kg', 30, NULL, 'dryland', 4,  4,  'FERTASA Handbook', '5.4.3.1.2', 2019, NULL),

    -- Yield 1.5 t/ha
    ('Wheat', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 9,  9,  'FERTASA Handbook', '5.4.3.1.2', 2019, 'Minimum amount to be applied at low soil-P levels (*)'),
    ('Wheat', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 5,  18,   'dryland', 7,  9,  'FERTASA Handbook', '5.4.3.1.2', 2019, 'Minimum amount to be applied at low soil-P levels (*)'),
    ('Wheat', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 18, 30,   'dryland', 5,  7,  'FERTASA Handbook', '5.4.3.1.2', 2019, NULL),
    ('Wheat', 'P', 'elemental', 1.5, 1.5, 'Bray-1', 'mg/kg', 30, NULL, 'dryland', 5,  5,  'FERTASA Handbook', '5.4.3.1.2', 2019, NULL),

    -- Yield 2.0 t/ha
    ('Wheat', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 12, 12, 'FERTASA Handbook', '5.4.3.1.2', 2019, 'Minimum amount to be applied at low soil-P levels (*)'),
    ('Wheat', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 5,  18,   'dryland', 9,  12, 'FERTASA Handbook', '5.4.3.1.2', 2019, 'Minimum amount to be applied at low soil-P levels (*)'),
    ('Wheat', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 18, 30,   'dryland', 7,  9,  'FERTASA Handbook', '5.4.3.1.2', 2019, NULL),
    ('Wheat', 'P', 'elemental', 2.0, 2.0, 'Bray-1', 'mg/kg', 30, NULL, 'dryland', 7,  7,  'FERTASA Handbook', '5.4.3.1.2', 2019, NULL),

    -- Yield 2.5+ t/ha (open upper bound)
    ('Wheat', 'P', 'elemental', 2.5, NULL, 'Bray-1', 'mg/kg', 0,  5,    'dryland', 15, 18, 'FERTASA Handbook', '5.4.3.1.2', 2019, 'Minimum amount to be applied at low soil-P levels (*)'),
    ('Wheat', 'P', 'elemental', 2.5, NULL, 'Bray-1', 'mg/kg', 5,  18,   'dryland', 12, 18, 'FERTASA Handbook', '5.4.3.1.2', 2019, 'Minimum amount to be applied at low soil-P levels (*)'),
    ('Wheat', 'P', 'elemental', 2.5, NULL, 'Bray-1', 'mg/kg', 18, 30,   'dryland', 9,  15, 'FERTASA Handbook', '5.4.3.1.2', 2019, NULL),
    ('Wheat', 'P', 'elemental', 2.5, NULL, 'Bray-1', 'mg/kg', 30, NULL, 'dryland', 9,  11, 'FERTASA Handbook', '5.4.3.1.2', 2019, NULL);

COMMIT;
