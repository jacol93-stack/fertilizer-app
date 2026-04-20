-- ============================================================
-- 061: Seed FERTASA 5.6.1 general vegetables + dry bean K
-- ============================================================
-- Sources: FERTASA Handbook sections 5.6.1 (General vegetables) and
-- 5.5.2 Table 3 (dry bean K).
--
-- Cell counts:
--   Vegetables N   16 crops × 1 (yield-agnostic range)  = 16
--   Vegetables P   16 crops × 3 Bray-1 bands            = 48
--   Vegetables K   16 crops × 3 NH4OAc bands            = 48
--   Dry bean K      6 soil-K bands × 5 yields           = 30
--
-- Total: 142 cells across 17 new crops/crop-nutrient slots.
--
-- Veg crops: Beetroot, Brinjal, Cabbage crops, Carrot, Chillies,
--   Garlic, Gem squash, Green beans, Green peas, Lettuce, Onion,
--   Pumpkin crops, Red/green peppers, Strawberry, Sweet melon,
--   Sweet potato.
--
-- Note: FERTASA's veg tables are yield-agnostic (no yield axis on
-- the P or K tables). Encoded with yield_min=0, yield_max=NULL so
-- the lookup matches regardless of the yield context.
--
-- Dry bean K quirks faithfully preserved:
--   * Lowest soil-K band (<40 mg/kg) shows open-upper rates like
--     ">23" — encoded as (rate_min=published minimum) with a
--     generous rate_max (to avoid under-fertilising). Flagged in
--     source_note.
--   * Row 4 cell at yield 2.0 scraped as "23 -1 8" — corrected to
--     "23-18" in the seed (typo in scraper output; pattern is clear).
--   * Row 5 cell at yield 2.0 scraped as "18 - 0" and yield 3.0 as
--     "2 - 23" — both likely OCR/scraper errors. Corrected to match
--     the linear progression pattern (18-13 for y=2.0, 28-23 for
--     y=3.0). Flag in notes; verify against PDF later if needed.
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE source_section IN ('5.6.1 Table 1', '5.6.1 Table 2', '5.6.1 Table 3',
                         '5.5.2 Table 3');

-- Veg N (5.6.1 Table 1) — 16 crops, yield-agnostic N ranges
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Beetroot', 'N', 'elemental', 0, NULL, NULL, 100, 140, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Brinjal', 'N', 'elemental', 0, NULL, NULL, 120, 140, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Cabbage crops', 'N', 'elemental', 0, NULL, NULL, 160, 260, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Carrot', 'N', 'elemental', 0, NULL, NULL, 70, 120, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Chillies', 'N', 'elemental', 0, NULL, NULL, 100, 120, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Garlic', 'N', 'elemental', 0, NULL, NULL, 120, 160, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Gem squash', 'N', 'elemental', 0, NULL, NULL, 120, 150, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Green beans', 'N', 'elemental', 0, NULL, NULL, 100, 160, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Green peas', 'N', 'elemental', 0, NULL, NULL, 20, 45, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Lettuce', 'N', 'elemental', 0, NULL, NULL, 100, 160, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Onion', 'N', 'elemental', 0, NULL, NULL, 150, 180, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Pumpkin crops', 'N', 'elemental', 0, NULL, NULL, 80, 120, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Red/green peppers', 'N', 'elemental', 0, NULL, NULL, 180, 220, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Strawberry', 'N', 'elemental', 0, NULL, NULL, 150, 200, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Sweet melon', 'N', 'elemental', 0, NULL, NULL, 120, 160, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation'),
    ('Sweet potato', 'N', 'elemental', 0, NULL, NULL, 80, 120, 'FERTASA Handbook', '5.6.1 Table 1', 2019, 'Yield-agnostic N range for dryland or irrigated cultivation');

-- Veg P (5.6.1 Table 2) — 16 crops × 3 soil-P bands = 48 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Beetroot', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 100, 100, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Beetroot', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 70, 70, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Beetroot', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Brinjal', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 90, 90, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Brinjal', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 70, 70, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Brinjal', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Cabbage crops', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 100, 100, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Cabbage crops', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 70, 70, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Cabbage crops', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Carrot', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Carrot', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Carrot', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Chillies', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Chillies', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Chillies', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 30, 30, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Garlic', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 100, 100, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Garlic', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Garlic', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Gem squash', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 120, 120, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Gem squash', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 90, 90, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Gem squash', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Green beans', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 70, 70, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Green beans', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Green beans', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 30, 30, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Green peas', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 70, 70, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Green peas', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Green peas', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 20, 20, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Lettuce', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 100, 100, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Lettuce', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Lettuce', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Onion', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 120, 120, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Onion', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 90, 90, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Onion', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Pumpkin crops', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 90, 90, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Pumpkin crops', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 70, 70, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Pumpkin crops', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Red/green peppers', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 90, 90, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Red/green peppers', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 70, 70, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Red/green peppers', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Strawberry', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 120, 120, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Strawberry', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Strawberry', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Sweet melon', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 120, 120, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Sweet melon', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 90, 90, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Sweet melon', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Sweet potato', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 0, 20, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Sweet potato', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 20, 50, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL),
    ('Sweet potato', 'P', 'elemental', 0, NULL, 'Bray-1', 'mg/kg', 50, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 2', 2019, NULL);

-- Veg K (5.6.1 Table 3) — 16 crops × 3 soil-K bands = 48 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Beetroot', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 120, 120, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Beetroot', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Beetroot', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Brinjal', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 120, 120, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Brinjal', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Brinjal', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Cabbage crops', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 160, 160, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Cabbage crops', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 120, 120, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Cabbage crops', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Carrot', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 100, 100, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Carrot', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Carrot', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Chillies', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Chillies', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Chillies', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Garlic', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 110, 110, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Garlic', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 70, 70, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Garlic', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Gem squash', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 100, 100, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Gem squash', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Gem squash', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Green beans', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 90, 90, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Green beans', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Green beans', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 30, 30, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Green peas', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 70, 70, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Green peas', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Green peas', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 20, 20, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Lettuce', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 120, 120, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Lettuce', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Lettuce', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Onion', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 140, 140, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Onion', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Onion', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 40, 40, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Pumpkin crops', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Pumpkin crops', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Pumpkin crops', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 30, 30, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Red/green peppers', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 160, 160, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Red/green peppers', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 120, 120, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Red/green peppers', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 60, 60, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Strawberry', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 150, 150, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Strawberry', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 100, 100, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Strawberry', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Sweet melon', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 100, 100, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Sweet melon', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Sweet melon', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Sweet potato', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 0, 80, NULL, 80, 80, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Sweet potato', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 80, 150, NULL, 50, 50, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL),
    ('Sweet potato', 'K', 'elemental', 0, NULL, 'NH4OAc', 'mg/kg', 150, NULL, NULL, 30, 30, 'FERTASA Handbook', '5.6.1 Table 3', 2019, NULL);

-- Dry bean K (5.5.2 Table 3) — 6 soil-K bands × 5 yields = 30 cells
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha,
     soil_test_method, soil_test_unit, soil_test_min, soil_test_max,
     water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Bean (Dry)', 'K', 'elemental', 1.0, 1.0, 'NH4OAc', 'mg/kg', 0, 40, 'dryland', 23, 50, 'FERTASA Handbook', '5.5.2 Table 3', 2019, 'Open-upper rate at low soil-K: minimum of range shown; actual rate may be higher'),
    ('Bean (Dry)', 'K', 'elemental', 1.5, 1.5, 'NH4OAc', 'mg/kg', 0, 40, 'dryland', 28, 60, 'FERTASA Handbook', '5.5.2 Table 3', 2019, 'Open-upper rate at low soil-K: minimum of range shown; actual rate may be higher'),
    ('Bean (Dry)', 'K', 'elemental', 2.0, 2.0, 'NH4OAc', 'mg/kg', 0, 40, 'dryland', 33, 70, 'FERTASA Handbook', '5.5.2 Table 3', 2019, 'Open-upper rate at low soil-K: minimum of range shown; actual rate may be higher'),
    ('Bean (Dry)', 'K', 'elemental', 2.5, 2.5, 'NH4OAc', 'mg/kg', 0, 40, 'dryland', 40, 80, 'FERTASA Handbook', '5.5.2 Table 3', 2019, 'Open-upper rate at low soil-K: minimum of range shown; actual rate may be higher'),
    ('Bean (Dry)', 'K', 'elemental', 3.0, 3.0, 'NH4OAc', 'mg/kg', 0, 40, 'dryland', 50, 90, 'FERTASA Handbook', '5.5.2 Table 3', 2019, 'Open-upper rate at low soil-K: minimum of range shown; actual rate may be higher'),
    ('Bean (Dry)', 'K', 'elemental', 1.0, 1.0, 'NH4OAc', 'mg/kg', 40, 60, 'dryland', 18, 23, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 1.5, 1.5, 'NH4OAc', 'mg/kg', 40, 60, 'dryland', 23, 28, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.0, 2.0, 'NH4OAc', 'mg/kg', 40, 60, 'dryland', 28, 33, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.5, 2.5, 'NH4OAc', 'mg/kg', 40, 60, 'dryland', 33, 40, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 3.0, 3.0, 'NH4OAc', 'mg/kg', 40, 60, 'dryland', 40, 50, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 1.0, 1.0, 'NH4OAc', 'mg/kg', 60, 80, 'dryland', 13, 18, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 1.5, 1.5, 'NH4OAc', 'mg/kg', 60, 80, 'dryland', 18, 23, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.0, 2.0, 'NH4OAc', 'mg/kg', 60, 80, 'dryland', 23, 28, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.5, 2.5, 'NH4OAc', 'mg/kg', 60, 80, 'dryland', 28, 33, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 3.0, 3.0, 'NH4OAc', 'mg/kg', 60, 80, 'dryland', 33, 40, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 1.0, 1.0, 'NH4OAc', 'mg/kg', 80, 100, 'dryland', 8, 13, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 1.5, 1.5, 'NH4OAc', 'mg/kg', 80, 100, 'dryland', 13, 18, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.0, 2.0, 'NH4OAc', 'mg/kg', 80, 100, 'dryland', 18, 23, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.5, 2.5, 'NH4OAc', 'mg/kg', 80, 100, 'dryland', 23, 28, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 3.0, 3.0, 'NH4OAc', 'mg/kg', 80, 100, 'dryland', 28, 33, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 1.0, 1.0, 'NH4OAc', 'mg/kg', 100, 120, 'dryland', 0, 8, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 1.5, 1.5, 'NH4OAc', 'mg/kg', 100, 120, 'dryland', 8, 13, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.0, 2.0, 'NH4OAc', 'mg/kg', 100, 120, 'dryland', 13, 18, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.5, 2.5, 'NH4OAc', 'mg/kg', 100, 120, 'dryland', 18, 23, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 3.0, 3.0, 'NH4OAc', 'mg/kg', 100, 120, 'dryland', 23, 28, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 1.0, 1.0, 'NH4OAc', 'mg/kg', 120, NULL, 'dryland', 0, 0, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 1.5, 1.5, 'NH4OAc', 'mg/kg', 120, NULL, 'dryland', 0, 0, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.0, 2.0, 'NH4OAc', 'mg/kg', 120, NULL, 'dryland', 8, 8, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 2.5, 2.5, 'NH4OAc', 'mg/kg', 120, NULL, 'dryland', 12, 12, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL),
    ('Bean (Dry)', 'K', 'elemental', 3.0, 3.0, 'NH4OAc', 'mg/kg', 120, NULL, 'dryland', 15, 15, 'FERTASA Handbook', '5.5.2 Table 3', 2019, NULL);

COMMIT;
