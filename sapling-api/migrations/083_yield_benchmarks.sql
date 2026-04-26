-- 083_yield_benchmarks.sql
--
-- Two new tables for the historical-data + insights workstream:
--
--   crop_yield_benchmarks — published reference bands (low/typical/high)
--     per crop × cultivar × irrigation regime. Drives the field
--     dashboard's "is 4.5 t/ha a lot?" overlay on yield bars.
--
--   yield_records — actual recorded yields per field per season.
--     Imported from spreadsheets or entered manually. Anchors trend
--     analysis and "yield X% above benchmark" insight cards.
--
-- Sources for the seed rows are SA-direct (T1) where available — SAMAC
-- Industry Statistics, SAAGA Yearbook, CRI Industry Statistics,
-- FERTASA, Schoeman 2021 SAMAC Day, Köhne 1990, Manson & Sheard 2007 —
-- with NZAGA (T2) and rolled industry means (T3) where SA peer-reviewed
-- numbers don't exist. Honest NULLs on bands the literature doesn't
-- publish (rainfed citrus across the board, etc.).

BEGIN;

-- ── crop_yield_benchmarks ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS crop_yield_benchmarks (
    id SERIAL PRIMARY KEY,
    crop TEXT NOT NULL,
    cultivar TEXT,                                  -- NULL = generic / unspecified
    irrigation_regime TEXT NOT NULL,                -- 'rainfed' / 'irrigated' / 'fertigated'
    yield_unit TEXT NOT NULL DEFAULT 't/ha',
    low_t_per_ha NUMERIC,                           -- NULL when no band published
    typical_t_per_ha NUMERIC NOT NULL,              -- always present (the anchor value)
    high_t_per_ha NUMERIC,                          -- NULL when no band published
    region TEXT,                                    -- NULL = SA-wide
    source TEXT NOT NULL,
    source_tier TEXT NOT NULL CHECK (source_tier IN ('T1', 'T2', 'T3')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS crop_yield_benchmarks_lookup
    ON crop_yield_benchmarks (
        crop,
        COALESCE(cultivar, ''),
        irrigation_regime,
        COALESCE(region, '')
    );

CREATE INDEX IF NOT EXISTS crop_yield_benchmarks_by_crop
    ON crop_yield_benchmarks (crop);


-- ── yield_records ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS yield_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    season TEXT NOT NULL,                           -- e.g. "2024/25"
    yield_actual NUMERIC NOT NULL,
    yield_unit TEXT NOT NULL,                       -- 't/ha' / 't NIS/ha' / etc.
    harvest_date DATE,
    source TEXT NOT NULL DEFAULT 'self_reported',   -- 'self_reported' / 'lab_confirmed' / 'imported'
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES profiles(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS yield_records_field_season
    ON yield_records (field_id, season);

CREATE INDEX IF NOT EXISTS yield_records_by_field
    ON yield_records (field_id, harvest_date DESC);


-- ── seed: Macadamia ──────────────────────────────────────────────

INSERT INTO crop_yield_benchmarks
    (crop, cultivar, irrigation_regime, yield_unit, low_t_per_ha, typical_t_per_ha, high_t_per_ha, source, source_tier, notes)
VALUES
    ('Macadamia', 'Beaumont', 'irrigated',  't NIS/ha', 3.5, 5.0, 7.5, 'SAMAC Industry Statistics 2022; Schoeman 2021 SAMAC Day', 'T1', 'High-yielding cultivar; sun damage risk drives micro-irrigation adoption. Mature yr 10+.'),
    ('Macadamia', 'Beaumont', 'fertigated', 't NIS/ha', 4.5, 6.0, 8.5, 'Schoeman 2021 SAMAC Day intensive Levubu/Nelspruit blocks', 'T1', 'Top-end blocks reported in industry days; not a peer-reviewed mean.'),
    ('Macadamia', 'Beaumont', 'rainfed',    't NIS/ha', NULL, 2.5, NULL, 'Manson & Sheard 2007 (KZN Midlands dryland reference)', 'T1', 'Rare in commercial production; low/high not published.'),

    ('Macadamia', 'A4',       'irrigated',  't NIS/ha', 2.5, 3.5, 5.0, 'SAMAC Industry Statistics 2022; Schoeman 2021 cultivar comparison', 'T1', 'Lower yielding than Beaumont but premium kernel recovery (33-35%).'),
    ('Macadamia', 'A4',       'fertigated', 't NIS/ha', 3.0, 4.5, 6.0, 'Schoeman 2021 SAMAC Day intensive blocks', 'T1', NULL),
    ('Macadamia', 'A4',       'rainfed',    't NIS/ha', NULL, 2.0, NULL, 'Manson & Sheard 2007', 'T1', NULL),

    ('Macadamia', '816',      'irrigated',  't NIS/ha', 2.5, 3.5, 5.0, 'SAMAC Industry Statistics 2022', 'T1', 'Comparable to A4; slightly later bearing.'),
    ('Macadamia', '816',      'fertigated', 't NIS/ha', 3.0, 4.5, 6.0, 'Schoeman 2021 SAMAC Day', 'T1', NULL),

    ('Macadamia', NULL,       'irrigated',  't NIS/ha', 3.0, 4.0, 5.5, 'SAMAC Industry Statistics 2022 national rolled mean', 'T3', 'Generic / unspecified cultivar — industry rolled mean weighted across cultivars.'),
    ('Macadamia', NULL,       'fertigated', 't NIS/ha', 3.5, 5.0, 7.0, 'SAMAC Industry Statistics 2022 top quartile', 'T3', NULL),
    ('Macadamia', NULL,       'rainfed',    't NIS/ha', 1.5, 2.5, 3.5, 'Manson & Sheard 2007 dryland reference', 'T1', NULL);


-- ── seed: Citrus ─────────────────────────────────────────────────

INSERT INTO crop_yield_benchmarks
    (crop, cultivar, irrigation_regime, yield_unit, low_t_per_ha, typical_t_per_ha, high_t_per_ha, source, source_tier, notes)
VALUES
    ('Citrus', 'Valencia',           'irrigated',  't/ha',  35, 55, 75, 'CRI Industry Statistics 2023; FERTASA 5.7.3', 'T1', 'Mid-veld / Sundays River canopy yields. Mature yr 8+.'),
    ('Citrus', 'Valencia',           'fertigated', 't/ha',  45, 65, 90, 'CRI Citrus Academy NQ2 high-density drip blocks', 'T1', 'Top blocks 80-90 t/ha; not a population mean.'),

    ('Citrus', 'Navel',              'irrigated',  't/ha',  30, 45, 60, 'CRI Industry Statistics 2023; Citrus Academy Toolkit 3.5', 'T1', 'Lower than Valencia due to alternate bearing + thinning.'),
    ('Citrus', 'Navel',              'fertigated', 't/ha',  35, 55, 75, 'CRI Citrus Academy NQ2 high-input WC / Sundays River', 'T1', NULL),

    ('Citrus', 'Eureka Lemon',       'irrigated',  't/ha',  40, 60, 90,  'CRI Industry Statistics 2023; Letaba/Limpopo benchmarking', 'T1', 'Lemons routinely outyield oranges per ha.'),
    ('Citrus', 'Eureka Lemon',       'fertigated', 't/ha',  50, 75, 110, 'CRI Citrus Academy NQ2 intensive drip', 'T1', NULL),

    ('Citrus', 'Star Ruby',          'irrigated',  't/ha',  35, 55, 75, 'CRI Industry Statistics 2023 (Hoedspruit / Limpopo lowveld)', 'T1', 'Sensitive to wind-rub; export pack-out drives effective yield.'),
    ('Citrus', 'Star Ruby',          'fertigated', 't/ha',  45, 65, 90, 'CRI grower benchmarking', 'T1', NULL),

    ('Citrus', NULL,                 'irrigated',  't/ha',  30, 50, 70, 'CRI Industry Statistics 2023 national rolled mean', 'T3', 'Generic / unspecified cultivar.'),
    ('Citrus', NULL,                 'fertigated', 't/ha',  40, 60, 85, 'CRI Industry Statistics 2023 top-quartile growers', 'T3', NULL);


-- ── seed: Avocado ────────────────────────────────────────────────

INSERT INTO crop_yield_benchmarks
    (crop, cultivar, irrigation_regime, yield_unit, low_t_per_ha, typical_t_per_ha, high_t_per_ha, source, source_tier, notes)
VALUES
    ('Avocado', 'Hass',    'irrigated',  't/ha',  8, 12, 18, 'SAAGA Yearbook industry stats; FERTASA 5.7.1', 'T1', 'Strongly alternate-bearing; "typical" is a 2-yr rolling average. Mature yr 8+.'),
    ('Avocado', 'Hass',    'fertigated', 't/ha', 10, 15, 22, 'SAAGA grower-day reports (Mooketsi / Levubu); NZAGA Avocado Growers Manual', 'T2', 'NZ data used as upper-bound parallel.'),
    ('Avocado', 'Hass',    'rainfed',    't/ha', NULL, 6, NULL, 'Köhne 1990 SAAGA YB 13:8-10', 'T1', 'Marginal in SA; Hass needs reliable summer water.'),

    ('Avocado', 'Fuerte',  'irrigated',  't/ha',  6, 10, 14, 'SAAGA Yearbook industry stats; Du Plessis & Koen 1992 WAC2 p.289', 'T1', 'Lower yielding than Hass; declining commercial footprint.'),
    ('Avocado', 'Fuerte',  'fertigated', 't/ha',  7, 12, 16, 'SAAGA grower benchmarking', 'T1', NULL),
    ('Avocado', 'Fuerte',  'rainfed',    't/ha', NULL, 5, NULL, 'Köhne 1990 SAAGA YB 13:8-10', 'T1', NULL),

    ('Avocado', NULL,      'irrigated',  't/ha',  7, 11, 16, 'SAAGA Industry Statistics national rolled mean', 'T3', 'Generic / unspecified cultivar.'),
    ('Avocado', NULL,      'fertigated', 't/ha',  9, 14, 20, 'SAAGA top-quartile grower reports', 'T3', NULL),
    ('Avocado', NULL,      'rainfed',    't/ha', NULL, 5, NULL, 'Köhne 1990 SAAGA YB 13:8-10', 'T1', NULL);

COMMIT;
