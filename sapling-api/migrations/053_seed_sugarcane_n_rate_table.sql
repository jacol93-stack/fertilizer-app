-- ============================================================
-- 053: Seed sugarcane N rate table (SASRI IS 7.2)
-- ============================================================
-- Source: South African Sugarcane Research Institute (SASRI) Information
--         Sheet 7.2 "Nitrogen management" (updated Oct 2025).
--         https://sasri.org.za/download/162/7-soils-nutrition/28628/
--         7-2-nitrogen-management.pdf
--
-- Only the numerical thresholds are reproduced here (facts, not subject
-- to copyright). The PDF itself is not committed — see .gitignore.
--
-- Table structure:
--   N-category × target yield × crop cycle (plant / ratoon) → kg N/ha
-- N-category is derived from soil organic matter (SOM) and clay:
--   * N-Cat 1: SOM < 2%, any clay
--   * N-Cat 2: SOM 2-4%, clay < 35%
--   * N-Cat 3: SOM 2-4%, clay ≥ 35%
--   * N-Cat 4: SOM > 4%, any clay
-- Stored as explicit (som_pct_min, som_pct_max) + (clay_pct_min, clay_pct_max)
-- pairs on each row — the lookup matches both bands at once.
-- Yield targets (t cane/ha): 75, 90, 100, 125, 150, 175, 200. Above 150
-- the plant rates plateau (the published table repeats 165 / 195 etc.
-- for 175 and 200 — preserved faithfully).
--
-- Total: 4 categories × 7 yield bands × 2 crop cycles = 56 cells.
-- ============================================================

BEGIN;

DELETE FROM public.fertilizer_rate_tables
WHERE crop = 'Sugarcane'
  AND nutrient = 'N'
  AND source_section = 'IS 7.2';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form,
     yield_min_t_ha, yield_max_t_ha,
     clay_pct_min, clay_pct_max,
     soil_organic_matter_pct_min, soil_organic_matter_pct_max,
     crop_cycle, water_regime,
     rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    -- N-Cat 1: SOM < 2%, any clay — plant & ratoon
    ('Sugarcane', 'N', 'elemental',  75,  75, NULL, NULL, 0, 2, 'plant',  NULL, 110, 110, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental',  90,  90, NULL, NULL, 0, 2, 'plant',  NULL, 130, 130, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 100, 100, NULL, NULL, 0, 2, 'plant',  NULL, 140, 140, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 125, 125, NULL, NULL, 0, 2, 'plant',  NULL, 165, 165, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 150, 150, NULL, NULL, 0, 2, 'plant',  NULL, 190, 190, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 175, 175, NULL, NULL, 0, 2, 'plant',  NULL, 215, 215, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 200, 200, NULL, NULL, 0, 2, 'plant',  NULL, 215, 215, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: plant rate plateaus at 215 above 175 t/ha'),
    ('Sugarcane', 'N', 'elemental',  75,  75, NULL, NULL, 0, 2, 'ratoon', NULL, 140, 140, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental',  90,  90, NULL, NULL, 0, 2, 'ratoon', NULL, 160, 160, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 100, 100, NULL, NULL, 0, 2, 'ratoon', NULL, 170, 170, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 125, 125, NULL, NULL, 0, 2, 'ratoon', NULL, 195, 195, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 150, 150, NULL, NULL, 0, 2, 'ratoon', NULL, 220, 220, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 175, 175, NULL, NULL, 0, 2, 'ratoon', NULL, 245, 245, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: SOM < 2%, any clay'),
    ('Sugarcane', 'N', 'elemental', 200, 200, NULL, NULL, 0, 2, 'ratoon', NULL, 245, 245, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 1: ratoon rate plateaus at 245 above 175 t/ha'),

    -- N-Cat 2: SOM 2-4%, clay < 35%
    ('Sugarcane', 'N', 'elemental',  75,  75, 0, 35, 2, 4, 'plant',  NULL,  90,  90, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental',  90,  90, 0, 35, 2, 4, 'plant',  NULL, 110, 110, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 100, 100, 0, 35, 2, 4, 'plant',  NULL, 120, 120, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 125, 125, 0, 35, 2, 4, 'plant',  NULL, 145, 145, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 150, 150, 0, 35, 2, 4, 'plant',  NULL, 170, 170, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 175, 175, 0, 35, 2, 4, 'plant',  NULL, 195, 195, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 200, 200, 0, 35, 2, 4, 'plant',  NULL, 195, 195, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: plateau above 175 t/ha'),
    ('Sugarcane', 'N', 'elemental',  75,  75, 0, 35, 2, 4, 'ratoon', NULL, 130, 130, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental',  90,  90, 0, 35, 2, 4, 'ratoon', NULL, 150, 150, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 100, 100, 0, 35, 2, 4, 'ratoon', NULL, 160, 160, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 125, 125, 0, 35, 2, 4, 'ratoon', NULL, 185, 185, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 150, 150, 0, 35, 2, 4, 'ratoon', NULL, 210, 210, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 175, 175, 0, 35, 2, 4, 'ratoon', NULL, 235, 235, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: SOM 2-4%, clay < 35%'),
    ('Sugarcane', 'N', 'elemental', 200, 200, 0, 35, 2, 4, 'ratoon', NULL, 235, 235, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 2: plateau above 175 t/ha'),

    -- N-Cat 3: SOM 2-4%, clay ≥ 35%
    ('Sugarcane', 'N', 'elemental',  75,  75, 35, NULL, 2, 4, 'plant',  NULL,  60,  60, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental',  90,  90, 35, NULL, 2, 4, 'plant',  NULL,  80,  80, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 100, 100, 35, NULL, 2, 4, 'plant',  NULL,  90,  90, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 125, 125, 35, NULL, 2, 4, 'plant',  NULL, 115, 115, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 150, 150, 35, NULL, 2, 4, 'plant',  NULL, 140, 140, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 175, 175, 35, NULL, 2, 4, 'plant',  NULL, 165, 165, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 200, 200, 35, NULL, 2, 4, 'plant',  NULL, 165, 165, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: plateau above 175 t/ha'),
    ('Sugarcane', 'N', 'elemental',  75,  75, 35, NULL, 2, 4, 'ratoon', NULL, 100, 100, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental',  90,  90, 35, NULL, 2, 4, 'ratoon', NULL, 120, 120, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 100, 100, 35, NULL, 2, 4, 'ratoon', NULL, 130, 130, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 125, 125, 35, NULL, 2, 4, 'ratoon', NULL, 155, 155, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 150, 150, 35, NULL, 2, 4, 'ratoon', NULL, 180, 180, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 175, 175, 35, NULL, 2, 4, 'ratoon', NULL, 205, 205, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: SOM 2-4%, clay >= 35%'),
    ('Sugarcane', 'N', 'elemental', 200, 200, 35, NULL, 2, 4, 'ratoon', NULL, 205, 205, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 3: plateau above 175 t/ha'),

    -- N-Cat 4: SOM > 4%, any clay
    ('Sugarcane', 'N', 'elemental',  75,  75, NULL, NULL, 4, NULL, 'plant',  NULL,  45,  45, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental',  90,  90, NULL, NULL, 4, NULL, 'plant',  NULL,  60,  60, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 100, 100, NULL, NULL, 4, NULL, 'plant',  NULL,  70,  70, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 125, 125, NULL, NULL, 4, NULL, 'plant',  NULL,  95,  95, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 150, 150, NULL, NULL, 4, NULL, 'plant',  NULL, 120, 120, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 175, 175, NULL, NULL, 4, NULL, 'plant',  NULL, 145, 145, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 200, 200, NULL, NULL, 4, NULL, 'plant',  NULL, 145, 145, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: plateau above 175 t/ha'),
    ('Sugarcane', 'N', 'elemental',  75,  75, NULL, NULL, 4, NULL, 'ratoon', NULL,  80,  80, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental',  90,  90, NULL, NULL, 4, NULL, 'ratoon', NULL, 100, 100, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 100, 100, NULL, NULL, 4, NULL, 'ratoon', NULL, 110, 110, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 125, 125, NULL, NULL, 4, NULL, 'ratoon', NULL, 135, 135, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 150, 150, NULL, NULL, 4, NULL, 'ratoon', NULL, 160, 160, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 175, 175, NULL, NULL, 4, NULL, 'ratoon', NULL, 185, 185, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: SOM > 4%, any clay'),
    ('Sugarcane', 'N', 'elemental', 200, 200, NULL, NULL, 4, NULL, 'ratoon', NULL, 185, 185, 'SASRI Information Sheet', 'IS 7.2', 2025, 'N-Cat 4: plateau above 175 t/ha');

COMMIT;
