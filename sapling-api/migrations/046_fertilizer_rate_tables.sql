-- ============================================================
-- 046: FERTASA 2-D rate tables + crop application windows
-- ============================================================
-- Our current nutrient-target math is:
--     target = removal_per_t(crop, nutrient) * yield_target
--              * adjustment_factor(soil_classification)
--
-- That's a flat multiplier over a constant removal. It can't
-- express the nonlinear soil-test × yield interaction that
-- FERTASA actually publishes in its 2-D rate tables — e.g.,
-- wheat Table 5.4.3.1.2 prescribes 6 kg P/ha at 1.0 t/ha / <5 mg/kg,
-- and 15-18 kg at 2.5+ t/ha / <5 mg/kg, with zero at high soil-P
-- even when yield is moderate. Our current method would return
-- 25 kg P/ha for wheat @ 2.0 t/ha / 8 mg/kg (low); FERTASA says
-- 9-12 kg. ~2.5x divergence — not cosmetic.
--
-- This migration adds the schema to store those tables. Seeding
-- follows in 047+ (wheat P first, then wheat K / potato N/P/K /
-- canola N, then whatever the research pass turns up).
--
-- Design decisions (conservative, audit-friendly):
--   * Snap to bands, no interpolation. Faithful to published cell.
--   * Rate stored as min/max (most cells are exact, some are ranges
--     like "4 - 6 kg/ha" — midpoint is computed at read-time).
--   * Third-axis dimensions (clay%, texture, rainfall band, region,
--     prior crop, water regime) as explicit nullable columns rather
--     than JSONB. Queryable, self-documenting, no hidden shape.
--   * yield_max_t_ha = NULL means "and above" (e.g., the 2.5+ band).
--   * soil_test_max = NULL means the same for the top soil-test band.
--   * source_section is the FERTASA handbook table number, kept as
--     free text ('5.4.3.1.2') so we can cite non-FERTASA sources too.
--
-- crop_application_windows is separate (below). Schema only — engine
-- wiring in a later migration once we decide the enforcement model
-- (hard-block vs. warn-only).
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. fertilizer_rate_tables
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.fertilizer_rate_tables (
    id              SERIAL PRIMARY KEY,

    -- Key
    crop            TEXT NOT NULL,
    nutrient        TEXT NOT NULL
        CHECK (nutrient IN ('N','P','K','Ca','Mg','S','B','Cu','Fe','Mn','Zn','Mo')),
    nutrient_form   TEXT NOT NULL DEFAULT 'elemental'
        CHECK (nutrient_form IN ('elemental','oxide')),

    -- Yield axis (required; inclusive min, exclusive max; NULL max = open upper bound)
    yield_min_t_ha  NUMERIC NOT NULL,
    yield_max_t_ha  NUMERIC,

    -- Soil-test axis (optional — some tables, e.g. canola N, don't use soil test)
    soil_test_method TEXT,   -- 'Bray-1', 'Olsen', 'Ambic', 'Citric acid', 'Mehlich-3', etc.
    soil_test_unit   TEXT,   -- 'mg/kg', 'cmol/kg', '%'
    soil_test_min    NUMERIC,
    soil_test_max    NUMERIC,

    -- Optional third-axis filters (explicit nullable columns; a row applies
    -- only when the context value is non-NULL AND the lookup input matches)
    clay_pct_min    NUMERIC,
    clay_pct_max    NUMERIC,
    texture         TEXT,   -- e.g. 'sandy', 'loam', 'clay'
    rainfall_mm_min NUMERIC,
    rainfall_mm_max NUMERIC,
    region          TEXT,   -- e.g. 'Southern Cape', 'Swartland', 'Southern Free State'
    prior_crop      TEXT,   -- e.g. 'lucerne', 'wheat', 'fallow'
    water_regime    TEXT
        CHECK (water_regime IS NULL OR water_regime IN ('dryland','irrigated')),

    -- Rate cell (kg/ha). For exact values, min = max. For ranges, both set.
    rate_min_kg_ha  NUMERIC NOT NULL CHECK (rate_min_kg_ha >= 0),
    rate_max_kg_ha  NUMERIC NOT NULL CHECK (rate_max_kg_ha >= rate_min_kg_ha),

    -- Provenance
    source          TEXT NOT NULL,          -- 'FERTASA Handbook 8th Ed.', 'GrainSA 2023', etc.
    source_section  TEXT NOT NULL,          -- '5.4.3.1.2'
    source_year     INTEGER,
    source_note     TEXT,                   -- footnotes / asterisks

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Lookup paths:
--   primary: (crop, nutrient) then range-filter in app code
--   secondary: by source_section (for audit)
CREATE INDEX IF NOT EXISTS idx_rate_tables_crop_nut
    ON public.fertilizer_rate_tables (crop, nutrient);
CREATE INDEX IF NOT EXISTS idx_rate_tables_source_section
    ON public.fertilizer_rate_tables (source_section);

COMMENT ON TABLE public.fertilizer_rate_tables IS
    'FERTASA (and equivalent) 2-D fertilizer rate tables. Each row is one cell: yield band × soil-test band × optional third-axis filter → kg/ha range. Read-time: snap yield to nearest band, snap soil-test to containing band, filter by any non-NULL third-axis columns that match the lookup context.';

COMMENT ON COLUMN public.fertilizer_rate_tables.yield_max_t_ha IS
    'NULL = open upper bound (FERTASA "2.5+ t/ha" convention).';

COMMENT ON COLUMN public.fertilizer_rate_tables.soil_test_max IS
    'NULL = open upper bound ("> 30 mg/kg" convention). NULL in ALL soil-test columns = table does not use a soil-test axis (e.g. canola N).';

COMMENT ON COLUMN public.fertilizer_rate_tables.rate_max_kg_ha IS
    'Equal to rate_min_kg_ha for exact cells; greater for range cells ("4 - 6 kg/ha"). Consumers display the midpoint by default and surface both bounds in diagnostics.';

-- ------------------------------------------------------------
-- 2. crop_application_windows
-- ------------------------------------------------------------
-- Time-based application constraints: "don't apply N to dry bean at
-- flowering", "macadamia N only Mar-Oct", etc.
-- Two ways to express a window: month range OR growth stage. Exactly
-- one must be populated per row (enforced by CHECK).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.crop_application_windows (
    id              SERIAL PRIMARY KEY,

    crop            TEXT NOT NULL,
    nutrient        TEXT NOT NULL,   -- 'N','P','K',... or 'ALL'

    -- Month-range constraint (inclusive). If earliest > latest, the window
    -- wraps the calendar year (e.g., earliest=10, latest=2 means Oct-Feb).
    earliest_month  INTEGER CHECK (earliest_month BETWEEN 1 AND 12),
    latest_month    INTEGER CHECK (latest_month BETWEEN 1 AND 12),

    -- Growth-stage constraint (alternative to month range)
    growth_stage    TEXT,            -- 'flowering', 'before_tillering', 'budbreak', etc.

    rule_type       TEXT NOT NULL
        CHECK (rule_type IN ('avoid','prefer','split')),
    reason          TEXT NOT NULL,
    source          TEXT NOT NULL,
    source_section  TEXT NOT NULL,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Exactly one constraint mode per row
    CHECK (
        (earliest_month IS NOT NULL AND latest_month IS NOT NULL AND growth_stage IS NULL)
        OR
        (earliest_month IS NULL AND latest_month IS NULL AND growth_stage IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_windows_crop_nut
    ON public.crop_application_windows (crop, nutrient);

COMMENT ON TABLE public.crop_application_windows IS
    'Temporal / phenological fertilizer application rules (e.g. macadamia N only Mar-Oct, dry bean no N at flowering). Schema-only in 046 — engine enforcement wired in a later migration.';

-- ------------------------------------------------------------
-- 3. RLS — match 031's convention
-- ------------------------------------------------------------
-- Backend uses service role (bypasses RLS). Enabling RLS with no
-- policies means no anon/authenticated read, which is correct for
-- these reference tables. Frontend never queries them directly.
-- ------------------------------------------------------------
ALTER TABLE public.fertilizer_rate_tables    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crop_application_windows  ENABLE ROW LEVEL SECURITY;

COMMIT;
