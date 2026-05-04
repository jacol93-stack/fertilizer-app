-- ============================================================
-- 107: add Kiwi (genus) to the crop catalog
-- ============================================================
-- Bare scaffolding so the wizard can pick Kiwi for SA growers
-- (Eastern Cape + Western Cape mostly Hayward; SunGold scaling).
-- Nutrient targets are placeholders (0) until cited bands land in
-- crop_sufficiency_overrides / fertilizer_rate_tables / leaf_norms /
-- nutrient_removal — track via docs/CROP_DATA_COVERAGE.md.
--
-- Cultivar variants (Kiwi (Hayward), Kiwi (SunGold)) deferred — add
-- as separate rows with parent_crop = 'Kiwi' once we want different
-- defaults per cultivar.
--
-- Default yield 25 t/ha is a conservative SA-mature-Hayward target;
-- pop/ha 600 reflects a 5 m × 3.3 m pergola spacing (standard SA).
-- Per-tree-age scaling comes from perennial_age_factors once seeded.
-- ============================================================

BEGIN;

INSERT INTO public.crop_requirements (
    crop, type, crop_type,
    yield_unit, default_yield, pop_per_ha,
    n, p, k, ca, mg, s,
    fe, b, mn, zn, cu, mo,
    parent_crop, customer_ready
) VALUES (
    'Kiwi', 'Perennial', 'perennial',
    't fruit/ha', 25.0, 600.0,
    0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0,
    NULL, TRUE
)
ON CONFLICT (crop) DO NOTHING;

-- Application methods — the standard perennial trio. Nutrient suitability
-- mirrors Avocado/Citrus convention (broadcast for macros at dormancy;
-- fertigation primary in season; foliar for micros + Ca).
INSERT INTO public.crop_application_methods
    (crop, method, is_default, nutrients_suited, timing_notes, crop_specific_notes)
VALUES
    ('Kiwi', 'broadcast', TRUE,
     ARRAY['N', 'P', 'K', 'Ca', 'Mg', 'S'],
     'Winter dormancy + post-harvest; granular under canopy line. Split N across the season.',
     NULL),
    ('Kiwi', 'fertigation', FALSE,
     ARRAY['N', 'K', 'Ca', 'Mg', 'S', 'Fe', 'Zn', 'B', 'Mn'],
     'Primary in-season delivery; weekly during budbreak through fruit fill (Sep-Mar).',
     NULL),
    ('Kiwi', 'foliar', FALSE,
     ARRAY['Zn', 'B', 'Fe', 'Mn', 'Cu', 'Ca'],
     'Zn + B critical for fruit set; Ca sprays for storage quality.',
     NULL)
ON CONFLICT DO NOTHING;

COMMIT;
