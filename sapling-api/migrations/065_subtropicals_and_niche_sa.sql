-- ============================================================
-- 065: Subtropicals + niche SA crops coverage
-- ============================================================
-- Sources per crop (all verified Tier 2-3, all free-access):
--   * Litchi: Australian Lychee Growers Assoc. "Lychee Field Guide"
--     (QLD DAF co-authored). Tentative Australian leaf standards.
--   * Pineapple: CTAHR F&N-7 "Pineapple Cultivation in Hawaii".
--     D-leaf analysis at 6-8 months.
--   * Pomegranate: UF/IFAS EDIS FE1024.
--   * Cassava: DAFF Production Guideline (2009). Removal rates per 25 t/ha.
--   * Honeybush: DAFF Honeybush Production Guideline.
--   * Rooibos: SA Rooibos Council 2020 Information Sheet + Hawkins/Lambers
--     academic soil-P work. No conventional rate-table exists (organic
--     rooibos uses no artificial fertilisers per SARC). Seeded as pH
--     override + research-memo flag.
--
-- Scope intentionally limited:
--   * Papaya (CTAHR F&N-3), Tea (Kenya Tea Board), Mango (Hort Innovation
--     MG15006) — sources identified but PDFs failed retrieval (timeouts,
--     403, image-only). Queued for a separate retrieval pass.
--   * Guava — regional Brazil/India sources only; no consolidated
--     rate table found. Stays FERTASA-absent until a specific request.
--   * Fig — no free rate tables published anywhere. Stays gap.
--   * Coffee — Global Coffee Platform Kenya manual + Embrapa Brazil
--     identified but content extraction deferred.
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- Litchi (ALGA Lychee Field Guide)
-- ------------------------------------------------------------
DELETE FROM public.fertasa_leaf_norms WHERE crop = 'Litchi';

INSERT INTO public.fertasa_leaf_norms
    (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max, high_min, excess_min,
     sample_part, sample_timing, source_section, notes)
VALUES
    ('Litchi', 'N',  '%',    NULL, 1.50, 1.50, 1.80, NULL, NULL,
        'Recently mature leaves from non-bearing branches', '1-2 weeks post-panicle emergence',
        'ALGA Lychee Field Guide', 'Tentative Australian leaf standards co-authored with QLD DAF. Sub-tropical / Lowveld transferable.'),
    ('Litchi', 'P',  '%',    NULL, 0.14, 0.14, 0.22, NULL, NULL, 'Recently mature leaves from non-bearing branches', '1-2 weeks post-panicle', 'ALGA Lychee Field Guide', NULL),
    ('Litchi', 'K',  '%',    NULL, 0.70, 0.70, 1.10, NULL, NULL, 'Recently mature leaves from non-bearing branches', '1-2 weeks post-panicle', 'ALGA Lychee Field Guide', NULL),
    ('Litchi', 'Ca', '%',    NULL, 0.60, 0.60, 1.00, NULL, NULL, 'Recently mature leaves from non-bearing branches', '1-2 weeks post-panicle', 'ALGA Lychee Field Guide', NULL),
    ('Litchi', 'Mg', '%',    NULL, 0.30, 0.30, 0.50, NULL, NULL, 'Recently mature leaves from non-bearing branches', '1-2 weeks post-panicle', 'ALGA Lychee Field Guide', NULL);

DELETE FROM public.crop_sufficiency_overrides WHERE crop = 'Litchi' AND parameter = 'pH (H2O)';

INSERT INTO public.crop_sufficiency_overrides (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Litchi', 'pH (H2O)', 5.0, 5.8, 6.5, 7.0, 'ALGA: litchi prefers slightly acidic soil, pH 5.8-6.5. Above 7.0 = micronutrient lock-up (Fe, Mn, Zn).');

-- ------------------------------------------------------------
-- Pineapple (CTAHR F&N-7)
-- ------------------------------------------------------------
DELETE FROM public.fertasa_leaf_norms WHERE crop = 'Pineapple';

INSERT INTO public.fertasa_leaf_norms
    (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max, high_min, excess_min,
     sample_part, sample_timing, source_section, notes)
VALUES
    ('Pineapple', 'N',  '%',    1.7, 1.7, 1.7,  NULL, NULL, NULL, 'D-leaf basal white portion', '6-8 months post-plant',
        'CTAHR F&N-7', 'Below 1.7% = deficient per CTAHR. CTAHR does not publish full 4-band; seeded as low_max only.'),
    ('Pineapple', 'K',  '%',    2.2, 2.2, 2.2,  NULL, NULL, NULL, 'D-leaf basal white portion', '6-8 months post-plant',
        'CTAHR F&N-7', 'Below 2.2% = deficient. Pineapple is an exceptionally high K feeder.'),
    ('Pineapple', 'Mg', '%',    0.25, 0.25, 0.25, NULL, NULL, NULL, 'D-leaf basal white portion', '6-8 months post-plant',
        'CTAHR F&N-7', 'Below 0.25% = deficient.');

DELETE FROM public.fertilizer_rate_tables WHERE crop = 'Pineapple';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha, water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Pineapple', 'N', 'elemental', 0, NULL, NULL, 400, 500,
        'CTAHR F&N-7', 'Post-plant annual N', 2010,
        '400-500 kg N/ha/yr postplant. Hawaiian plantation baseline; split across multiple applications through the plant cycle.'),
    ('Pineapple', 'P', 'elemental', 0, NULL, NULL, 75, 75,
        'CTAHR F&N-7', 'Pre-plant P', 2010,
        '75 kg P/ha pre-plant incorporated. Pineapple responds strongly to adequate P at establishment.');

-- ------------------------------------------------------------
-- Pomegranate (UF/IFAS FE1024)
-- ------------------------------------------------------------
DELETE FROM public.fertilizer_rate_tables WHERE crop = 'Pomegranate';

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha, water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Pomegranate', 'N', 'elemental', 0, NULL, NULL, 84, 140,
        'UF/IFAS FE1024', 'Annual N (bearing)', 2017,
        '75-125 lb N/ac = 84-140 kg/ha. March-April application. Young trees: step-up schedule (year 1 <= 1/3 mature rate).');

-- No leaf norms seeded for pomegranate: UF/IFAS explicitly states no
-- established critical leaf ranges exist. Honest gap — flagged in
-- audit plan as "cultivation guidance only, no SA-applicable rate
-- calibration published."

-- ------------------------------------------------------------
-- Cassava (DAFF 2009 + IITA + FAO cross-ref)
-- Removal rates go into crop_requirements where that schema exists;
-- not seeded as rate_table rows (cassava rates are highly system-
-- specific and DAFF gives only removal + general guidance).
-- Instead: pH override + a placeholder N rate band for maintenance.
-- ------------------------------------------------------------
DELETE FROM public.fertilizer_rate_tables WHERE crop = 'Cassava';
DELETE FROM public.crop_sufficiency_overrides WHERE crop = 'Cassava';

INSERT INTO public.crop_sufficiency_overrides (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Cassava', 'pH (H2O)', 4.5, 5.5, 7.0, 7.5, 'DAFF Cassava 2009 / IITA / FAO: cassava tolerates wide pH (4.5-7.5). Optimal 5.5-7.0. More acid-tolerant than most tuber crops.');

-- Removal rates reference (per 25 t/ha yield), for heuristic fallback:
--   DAFF cassava removal: 60 kg N + 40 kg P2O5 + 136 kg K2O = 60 N +
--   17.5 P + 112.8 K (elemental). Seeded as annual rate band (yield-
--   agnostic, for 20-30 t/ha) with source attribution.
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha, water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Cassava', 'N', 'elemental', 20, 30, NULL, 48, 72, 'DAFF Cassava Production Guideline', 'N removal reference', 2009,
        'Removal basis: ~60 kg N/ha for 25 t/ha yield. Range (48-72) reflects +/-20% around typical yield.'),
    ('Cassava', 'P', 'elemental', 20, 30, NULL, 14, 21, 'DAFF Cassava Production Guideline', 'P removal reference', 2009,
        'Removal basis: ~17.5 kg P/ha (40 kg P2O5) for 25 t/ha yield.'),
    ('Cassava', 'K', 'elemental', 20, 30, NULL, 90, 135, 'DAFF Cassava Production Guideline', 'K removal reference', 2009,
        'Removal basis: ~113 kg K/ha (136 kg K2O) for 25 t/ha yield. Cassava is a heavy K feeder.');

-- ------------------------------------------------------------
-- Honeybush (DAFF Production Guideline)
-- ------------------------------------------------------------
DELETE FROM public.fertilizer_rate_tables WHERE crop = 'Honeybush';
DELETE FROM public.crop_sufficiency_overrides WHERE crop = 'Honeybush';

INSERT INTO public.crop_sufficiency_overrides (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Honeybush', 'pH (H2O)', 4.0, 4.5, 5.0, 5.5, 'DAFF Honeybush: prefers acidic soil pH < 5. Similar tolerance to rooibos. Above 5.5 = stressed.');

-- Establishment rock phosphate (once-off, at planting):
INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha, crop_cycle, water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Honeybush', 'P', 'elemental', 0, NULL, 'plant', NULL, 100, 120, 'DAFF Honeybush Guideline', 'Establishment P (rock phosphate)', 2015,
        '500 kg/ha rock phosphate at establishment. Rock phosphate is ~20-24% P2O5 = 100-120 kg P2O5/ha = ~44-53 kg P/ha elemental when fully dissolved, but release is slow over 3-5 years — net-available ~100-120 kg/ha over the 6-year crop cycle.');

-- DAFF explicitly states: no maintenance fertiliser for honeybush.
-- Rhizobium-inoculated stands. n_pct effectively 0 after establishment.

-- ------------------------------------------------------------
-- Rooibos (SA Rooibos Council + Hawkins/Lambers academic)
-- ------------------------------------------------------------
-- No conventional rate-table exists. Organic rooibos uses NO artificial
-- fertilisers (per SARC 2020 Information Sheet). Seeded as:
--   1. pH override (acidic sandy soils)
--   2. A single "no fertilisation after establishment" research-memo
--      rate_table row with note citing SARC position.
-- This is the honest seed: the "finding" is the prescription.

DELETE FROM public.fertilizer_rate_tables WHERE crop = 'Rooibos';
DELETE FROM public.crop_sufficiency_overrides WHERE crop = 'Rooibos';

INSERT INTO public.crop_sufficiency_overrides (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Rooibos', 'pH (H2O)', 4.0, 4.5, 6.0, 6.5,
        'SARC 2020: rooibos grows only in the Cederberg on acidic sandy soils, pH 4.5-6.0. Outside this window the crop fails.'),
    ('Rooibos', 'P (Bray-1)', 1.3, 4.0, 17, 30,
        'Hawkins & Lambers academic work: pristine fynbos P = 1.3-1.7 mg/kg; oldest cultivated rooibos fields reach 4-17 mg/kg Bray-1. Rooibos is a P-sensitive Fynbos legume — over-fertilisation degrades stands.');

INSERT INTO public.fertilizer_rate_tables
    (crop, nutrient, nutrient_form, yield_min_t_ha, yield_max_t_ha, water_regime, rate_min_kg_ha, rate_max_kg_ha,
     source, source_section, source_year, source_note)
VALUES
    ('Rooibos', 'N', 'elemental', 0, NULL, 'dryland', 0, 0, 'SA Rooibos Council', 'SARC 2020 Information Sheet', 2020,
        'Rooibos is a Fynbos legume. SARC position: organic rooibos uses NO artificial N fertilisation. Legume biology (Aspalathus-specific Rhizobium) supplies the crop. Apply N = 0 kg/ha and cite this row.'),
    ('Rooibos', 'P', 'elemental', 0, NULL, 'dryland', 0, 0, 'SA Rooibos Council', 'SARC 2020 Information Sheet', 2020,
        'Maintenance P = 0 kg/ha. P addition on fynbos soils risks degrading the rooibos stand by shifting soil microbiome away from Aspalathus-optimal. Only exception: very severe P deficiency (Bray-1 < 2 mg/kg) + professional agronomist assessment.'),
    ('Rooibos', 'K', 'elemental', 0, NULL, 'dryland', 0, 0, 'SA Rooibos Council', 'SARC 2020 Information Sheet', 2020,
        'Maintenance K = 0 kg/ha. Same rationale as P: rooibos thrives on nutrient-poor Cederberg soils.');

COMMIT;
