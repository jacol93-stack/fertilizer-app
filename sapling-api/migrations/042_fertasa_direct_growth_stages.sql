-- ============================================================
-- FERTASA-direct corrections to crop_growth_stages
-- ============================================================
-- Migration 041 seeded growth-stage NPK splits from a mix of sources
-- (SAMAC, FERTASA PDF fragments, Cornell Cheng 2013 for apple,
-- Conradie SAJEV for grape, Starke Ayres for vegetables, etc.).
--
-- We then bought authenticated access to the full FERTASA Fertilizer
-- Handbook (fertasastats.co.za) and scraped chapter 5 directly — the
-- archive lives at sapling-api/data/fertasa_handbook/ and the audit of
-- 041 against it is memoed at research_fertasa_direct_audit.md.
--
-- This migration applies the corrections FERTASA *directly contradicts*
-- in 041 — both value changes and calendar shifts. It does NOT touch
-- crops FERTASA doesn't cover (deciduous fruit, grapes, berries,
-- olives, rooibos, coffee, tea, pineapple, mango, guava, fig, passion
-- fruit, sweet potato, onion/garlic, peppers, cucurbits, leafy veg,
-- carrot) — for those, 041's reconstructions from Hortgro / Conradie /
-- Starke Ayres / Cheng etc. stand.
--
-- Shape of every affected crop: DELETE + INSERT the full row set from
-- FERTASA-direct values. Secondary-nutrient columns (Ca/Mg/S/Fe/B/Mn/
-- Zn) preserved from 041 where FERTASA doesn't speak to them.
--
-- Major corrections:
--   Macadamia  — N only Mar-Oct (041 had 10% N in Jan-Mar window)
--   Pecan      — FERTASA Table 5.8.2.3 is a DISCRETE Aug+Oct schedule,
--                not a continuous split
--   Dry Bean   — 0% N at flowering (FERTASA: induces flower drop)
--   Lucerne    — 0% applied N on established stands (legume + stimulates
--                grasses; FERTASA Table 5.12.2.4 is establishment-year
--                only)
--   Groundnut  — all applied N at planting only, ~10-40 kg/ha total;
--                K goes to preceding crop not direct
--   Soybean    — inoculated: near-zero applied N
--   Cotton     — FERTASA: all N before week 13 post-plant
--   Asparagus  — 50% N at ridging + 50% N Dec/Jan (FERTASA 5.6.3)
--   Tobacco    — flue-cured: all N ASAP post-transplant
--   Wheat irrigated — FERTASA Table 5.4.3.3.2 ~62/19/19 split
--   Canola     — FERTASA Table 5.5.1.2 ~17/25/25/25/8 split
--   Avocado    — FERTASA: N peak is summer flush Jan/Feb, not Aug/Sep
--   Citrus (Valencia + Grapefruit) — stage 1/2 month windows were
--                out of order in 041
-- ============================================================

BEGIN;

DELETE FROM crop_growth_stages WHERE crop IN (
    'Macadamia',
    'Pecan',
    'Bean (Dry)',
    'Lucerne',
    'Groundnut',
    'Soybean',
    'Cotton',
    'Potato',
    'Asparagus',
    'Tobacco',
    'Wheat',
    'Maize (irrigated)',
    'Canola',
    'Avocado',
    'Citrus (Valencia)',
    'Citrus (Grapefruit)'
);


-- ─── MACADAMIA — FERTASA 5.8.1 (Hawksworth & Sheard 2022) ──────────────
-- Direct quote: "In producing orchards, N is supplemented only between
-- March and October. Vegetative growth hampers nut growth and oil
-- accumulation in the period November to February."
-- Fix from 041: Nov-Feb window must have N=0 exactly.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Macadamia', 'Post-harvest + flower initiation', 1, 3, 5,
     25, 20, 10, 25, 15, 15, 15, 25, 15, 15, 1, 'broadcast',
     'FERTASA 5.8.1 direct: N supplemented Mar-Oct only; flower init May. K winter-early-summer.'),
    ('Macadamia', 'Pre-flowering & main flowering', 2, 6, 9,
     45, 40, 50, 50, 25, 20, 20, 20, 25, 20, 2, 'broadcast',
     'FERTASA 5.8.1: main flowering Aug-Sep; K peak Oct-Dec starts here. Peak N window while still allowed.'),
    ('Macadamia', 'Nut set (last N window)', 3, 10, 10,
     30, 40, 40, 15, 35, 40, 35, 40, 35, 40, 1, 'fertigation',
     'FERTASA 5.8.1: nut set Sep-Oct; last N dose before Nov-Feb cutoff. K at its peak per "Oct-Dec".'),
    ('Macadamia', 'Nut growth + oil accumulation (NO N)', 4, 11, 2,
     0, 0, 0, 10, 25, 25, 30, 15, 25, 25, 0, 'broadcast',
     'FERTASA 5.8.1 explicit: Nov-Feb has NO applied N. "Vegetative growth hampers nut growth and oil accumulation."');


-- ─── PECAN — FERTASA 5.8.2 Table 5.8.2.3 (Schmidt, ARC-TSC 2021) ──────
-- Direct quote: "From the fourth year, equal quantities of N should be
-- given in August and October. Phosphorus is applied in August as a
-- single application. All the potassium is applied in October."
-- Fix from 041: replace continuous 4-stage split with DISCRETE Aug + Oct
-- events. Mg in Jun/Jul.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Pecan', 'Mg application (winter)', 1, 6, 7,
     0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 1, 'broadcast',
     'FERTASA 5.8.2 Table 5.8.2.3: Mg 100% in Jun/Jul.'),
    ('Pecan', 'Pre-bud-break N + all P (August)', 2, 8, 8,
     50, 100, 0, 30, 0, 50, 50, 30, 40, 30, 1, 'broadcast',
     'FERTASA 5.8.2 Table 5.8.2.3: 50% N + 100% P in August. No K.'),
    ('Pecan', 'Budbreak / spring flush', 3, 9, 9,
     0, 0, 0, 20, 0, 0, 0, 20, 10, 20, 0, 'broadcast',
     'FERTASA 5.8.2: no N/P/K scheduled here. Zn foliars begin (5 cm bud to 3 wk intervals) — handled separately.'),
    ('Pecan', 'Late-spring N + all K (October)', 4, 10, 10,
     50, 0, 100, 30, 0, 50, 50, 30, 40, 50, 1, 'broadcast',
     'FERTASA 5.8.2 Table 5.8.2.3: 50% N + 100% K in October. No P.'),
    ('Pecan', 'Nut fill + harvest (Nov-May)', 5, 11, 5,
     0, 0, 0, 20, 0, 0, 0, 20, 10, 0, 0, 'broadcast',
     'FERTASA 5.8.2: no further N/P/K. Kernel fill Feb-Apr. Zn foliar continues.');


-- ─── DRY BEAN — FERTASA 5.5.2 ─────────────────────────────────────────
-- Direct quote: "N-application shortly before or during flowering tends
-- to induce flower drop."
-- "If top-dressing is to be applied, this should be done within 3 to 4
-- weeks after planting to derive maximum benefit."
-- Fix from 041: stage 3 (flowering) N must be 0, not 25.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Bean (Dry)', 'Planting & establishment', 1, 10, 11,
     60, 75, 65, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'FERTASA 5.5.2: band-placement enhances uptake. Starter N.'),
    ('Bean (Dry)', 'Top-dress (within 3-4 weeks post-plant)', 2, 11, 12,
     40, 20, 25, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'FERTASA 5.5.2: "top-dressing...should be done within 3 to 4 weeks after planting."'),
    ('Bean (Dry)', 'Flowering (NO N — induces flower drop)', 3, 1, 1,
     0, 5, 10, 25, 25, 25, 25, 30, 25, 25, 0, 'broadcast',
     'CRITICAL FERTASA 5.5.2: "N-application shortly before or during flowering tends to induce flower drop." ZERO N here.'),
    ('Bean (Dry)', 'Pod fill & maturity', 4, 2, 3,
     0, 0, 0, 20, 20, 20, 20, 15, 20, 20, 0, 'broadcast',
     'FERTASA 5.5.2: no further N/P/K. B applications NOT recommended (dry beans very susceptible to B toxicity).');


-- ─── LUCERNE — FERTASA 5.12.2 ────────────────────────────────────────
-- Direct quote: "Topdressing with N on established stands that have
-- healthy active buds, does not improve yield, quality or vitality of
-- the stand; on the contrary, it can cause lower yield or quality due
-- to the stimulation of the growth of grasses and weeds."
-- Fix from 041: 30% N in summer + 20% N in spring etc. is WRONG for
-- established stands. Only establishment year has applied N.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Lucerne', 'Establishment year starter (pre-plant + seedling)', 1, 3, 4,
     100, 50, 30, 50, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'FERTASA 5.12.2 Table 5.12.2.4: establishment year 25-55 kg N/ha starter only. ALL NPK in notes applies to ESTABLISHMENT YEAR only. Autumn or spring sow.'),
    ('Lucerne', 'Spring regrowth / first cut', 2, 9, 10,
     0, 30, 30, 25, 25, 25, 25, 25, 25, 25, 2, 'broadcast',
     'FERTASA 5.12.2: 0% applied N on established stands (stimulates grasses/weeds). K 100 kg/ha spring.'),
    ('Lucerne', 'Summer cuts (peak production)', 3, 11, 2,
     0, 10, 20, 15, 15, 15, 15, 15, 15, 15, 3, 'broadcast',
     'FERTASA 5.12.2: 0% applied N. Midsummer K top-up if needed.'),
    ('Lucerne', 'Autumn cuts / pre-winter', 4, 3, 5,
     0, 5, 10, 5, 10, 10, 10, 10, 10, 10, 2, 'broadcast',
     'FERTASA 5.12.2: early April P for winter hardiness.'),
    ('Lucerne', 'Winter dormancy', 5, 6, 8,
     0, 5, 10, 5, 10, 10, 10, 10, 10, 10, 0, 'broadcast',
     'FERTASA 5.12.2: light maintenance only. P every 2 years: 3 kg P per ton DM removed.');


-- ─── GROUNDNUT — FERTASA 5.5.3 Table 5.5.3.2 ──────────────────────────
-- Direct quote: "The groundnut plant is self-sufficient regarding
-- nitrogen... 10 to 15 kg N ha-1 should be applied [on sandy soils]...
-- Excessive N-applications hamper root nodule development."
-- "The safest policy would be to fertilize the preceding crop and not
-- to apply K directly to groundnuts."
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Groundnut', 'Planting & establishment', 1, 10, 11,
     100, 100, 0, 30, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'FERTASA 5.5.3: all applied N at planting (total only 10-40 kg/ha). Apply K to preceding crop, not directly.'),
    ('Groundnut', 'Vegetative', 2, 12, 12,
     0, 0, 0, 20, 25, 25, 25, 25, 25, 25, 0, 'broadcast',
     'FERTASA 5.5.3: Rhizobium handles N.'),
    ('Groundnut', 'Flowering & pegging', 3, 1, 2,
     0, 0, 0, 35, 25, 25, 25, 30, 25, 25, 1, 'broadcast',
     'FERTASA 5.5.3: GYPSUM 200-300 kg/ha at pegging for pod Ca. NOT in NPK split. Spanish (Robin) types lower Ca need.'),
    ('Groundnut', 'Pod fill & maturation', 4, 3, 5,
     0, 0, 0, 15, 25, 25, 25, 20, 25, 25, 0, 'broadcast',
     'FERTASA 5.5.3: no further feed.');


-- ─── SOYBEAN — FERTASA 5.5.5 Table 5.5.5.2 ────────────────────────────
-- Direct quote: "If the seed has been properly inoculated with the
-- correct rhizobia... a yield increase with N-fertilizer is unlikely."
-- "On sandy soils with less than 10% clay, an initial application of 10
-- to 20 kg ha-1 N could be advantageous."
-- Fix from 041: inoculated case should be 100/0/0/0 with tiny absolute
-- amount, not 60/15/10/15.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Soybean', 'Planting & emergence (VE-V2)', 1, 11, 12,
     100, 100, 100, 30, 30, 30, 30, 30, 30, 30, 1, 'band_place',
     'FERTASA 5.5.5: Rhizobium japonicum supplies most N. Sandy <10% clay only: 10-20 kg N starter. If nodulation fails, treat as maize.'),
    ('Soybean', 'Vegetative (V3-V6)', 2, 12, 1,
     0, 0, 0, 25, 25, 25, 25, 25, 25, 25, 0, 'broadcast',
     'FERTASA 5.5.5: nodules established; no N needed unless nodulation fails.'),
    ('Soybean', 'Flowering & pod set (R1-R3)', 3, 1, 2,
     0, 0, 0, 25, 25, 25, 25, 25, 25, 25, 0, 'broadcast',
     'FERTASA 5.5.5: Mo seed treatment (35 g sodium molybdate/50 kg seed).'),
    ('Soybean', 'Pod fill & maturation (R5-R7)', 4, 2, 4,
     0, 0, 0, 20, 20, 20, 20, 20, 20, 20, 0, 'broadcast',
     'FERTASA 5.5.5: Soya removes 5x more K than maize — manage rotation K.');


-- ─── COTTON — FERTASA 5.9 ─────────────────────────────────────────────
-- Direct quote: "It is recommended that all N be applied before 13 weeks
-- after planting."
-- "More than 70% of the total nitrogen is taken up in the period 6 to
-- 15 weeks after planting."
-- "Potassium should be applied prior to planting."
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Cotton', 'Planting & establishment (weeks 0-5)', 1, 10, 11,
     20, 100, 100, 30, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'FERTASA 5.9: K pre-plant only; starter N (salt-burn limit on band placement).'),
    ('Cotton', 'Squaring / early bloom (weeks 6-13 — PEAK N)', 2, 12, 2,
     80, 0, 0, 40, 45, 45, 45, 50, 45, 45, 2, 'broadcast',
     'FERTASA 5.9 CRITICAL: "all N be applied before 13 weeks after planting." Peak N uptake weeks 6-15.'),
    ('Cotton', 'Boll fill & maturation (weeks 14+)', 3, 2, 4,
     0, 0, 0, 20, 20, 20, 20, 15, 20, 20, 0, 'broadcast',
     'FERTASA 5.9: no N after week 13. K already pre-planted.'),
    ('Cotton', 'Defoliation & harvest', 4, 5, 6,
     0, 0, 0, 10, 10, 10, 10, 10, 10, 10, 0, 'broadcast',
     'Harvest prep.');


-- ─── POTATO — FERTASA 5.6.2 Table 5.6.2.3 ─────────────────────────────
-- Direct quote: "Maximum application up to tuber initiation: clay <10%
-- = 50-60%; 10-20% clay = 60-75%; >20% clay = 80-100% of total N."
-- "Phosphorus is not easily leached from the soil and can therefore be
-- applied one-off at planting."
-- Default: sandy (<10% clay, Sandveld — dominant SA processing region).
-- Heavy-soil split noted in `notes`.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Potato', 'Planting & emergence (pre-tuber)', 1, 8, 9,
     55, 100, 70, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'FERTASA 5.6.2 Table 5.6.2.3 (sandy <10% clay default). HEAVY SOILS: 10-20% clay → 68% N here; >20% clay → 90-100% N here.'),
    ('Potato', 'Vegetative (pre-tuber-init finish)', 2, 10, 11,
     0, 0, 0, 20, 20, 20, 20, 20, 20, 20, 0, 'broadcast',
     'FERTASA: all pre-tuber N already applied at planting for sandy soils.'),
    ('Potato', 'Tuber bulking', 3, 11, 12,
     45, 0, 30, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'FERTASA 5.6.2 Table 5.6.2.3: 40-50% N post-tuber-init (sandy). HEAVY SOILS: 25-40% (10-20% clay) or 0-20% (>20% clay).'),
    ('Potato', 'Maturation (STOP N >=4 weeks pre-die-back)', 4, 1, 1,
     0, 0, 0, 15, 15, 15, 15, 15, 15, 15, 0, 'broadcast',
     'FERTASA 5.6.2: no N in final 4 weeks before foliage die-back.');


-- ─── ASPARAGUS — FERTASA 5.6.3 ────────────────────────────────────────
-- Direct quote: "The most appropriate time of application, for all of
-- the phosphorus and potassium and half of the nitrogen, is just before
-- the levelling of the ridges."
-- "Additional nitrogen can be broadcast at a later stage, towards the
-- end of December or the beginning of January."
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Asparagus', 'Pre-ridging (winter dormancy — all P, all K, half N)', 1, 7, 8,
     50, 100, 100, 50, 50, 50, 50, 50, 50, 50, 1, 'broadcast',
     'FERTASA 5.6.3: "all the phosphorus and potassium and half of the nitrogen, just before levelling of the ridges."'),
    ('Asparagus', 'Spear emergence & harvest', 2, 8, 10,
     0, 0, 0, 25, 25, 25, 25, 25, 25, 25, 0, 'broadcast',
     'FERTASA 5.6.3: no N during harvest window. Optional 25-30 kg N when second shoots appear.'),
    ('Asparagus', 'Fern build / reserve restoration (Dec/Jan N top-up)', 3, 12, 1,
     50, 0, 0, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'FERTASA 5.6.3: "additional N broadcast...end of December or beginning of January, to stimulate maximum growth and ensure sufficient reserves in the roots."'),
    ('Asparagus', 'Fern maturation & senescence', 4, 2, 6,
     0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 'broadcast',
     'Years 1-2 post-planting: NO harvest. Different feed pattern (establishment-heavy N).');


-- ─── TOBACCO — FERTASA 5.11 ───────────────────────────────────────────
-- Direct quote: "In the case of both flue-cured and Burley tobacco, all
-- the nitrogen should be applied as soon as possible after planting. In
-- other types of tobacco the last top-dressing is at the initiation of
-- the flower bud."
-- Default: flue-cured (dominant SA type).
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Tobacco', 'Transplant & establishment (all N ASAP)', 1, 8, 9,
     60, 100, 60, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'FERTASA 5.11 (flue-cured): all N ASAP post-plant. K ONLY from SOP/KNO3 — chloride destroys leaf quality. Nitrate-N preferred (50% of basal + top-dresses nitrate only).'),
    ('Tobacco', 'Vegetative (weeks 2-8)', 2, 10, 11,
     40, 0, 30, 30, 30, 30, 30, 30, 30, 30, 1, 'broadcast',
     'FERTASA 5.11: K top-dress as late as 2 weeks before topping. K 12x P requirement, 2.5x N requirement.'),
    ('Tobacco', 'Topping / flowering', 3, 11, 12,
     0, 0, 10, 20, 20, 20, 20, 20, 20, 20, 0, 'broadcast',
     'FERTASA 5.11 (flue-cured): N already complete. Dark air-cured: last N at flower-bud initiation instead.'),
    ('Tobacco', 'Leaf maturation / harvest', 4, 1, 4,
     0, 0, 0, 10, 10, 10, 10, 10, 10, 10, 0, 'broadcast',
     'FERTASA 5.11: S <2-3% in fertilizer compound (too much S harms burn quality).');


-- ─── WHEAT — FERTASA 5.4.3 ────────────────────────────────────────────
-- Table 5.4.3.3.2 (irrigation): 62/19/19 split across planting-to-early
-- tillering / early-to-late tillering / flag-leaf-to-flowering.
-- Dryland Free State (5.4.3.1.1): ALL N at planting, no top-dress.
-- Dryland WC (5.4.3.2.2): 25-30 kg at planting + balance in 1-3 top-dresses.
-- Default: irrigation SA winter crop (most productive system).
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Wheat', 'Planting to early tillering', 1, 5, 7,
     62, 80, 100, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'FERTASA 5.4.3 irrigation Table 5.4.3.3.2. Dryland FS: ALL N here (no top-dress). Dryland WC: 25-30 kg N + balance later. Oats/barley: 65-70% of wheat N rate.'),
    ('Wheat', 'Early to late tillering', 2, 6, 8,
     19, 15, 0, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'FERTASA 5.4.3: potential ear number is most important yield component during tillering.'),
    ('Wheat', 'Flag leaf to flowering (protein boost)', 3, 8, 10,
     19, 5, 0, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'FERTASA 5.4.3: flag-leaf N increases grain protein by 1-1.5% (ARC-SGI Wheat Quality).'),
    ('Wheat', 'Grain fill & maturation', 4, 10, 11,
     0, 0, 0, 25, 25, 25, 25, 25, 25, 25, 0, 'broadcast',
     'Maturation phase.');


-- ─── MAIZE IRRIGATED — FERTASA 5.4.4 ──────────────────────────────────
-- FERTASA says "a portion at planting, balance before 5-6 weeks post-
-- emergence." No explicit 5-split table but pivot fertigation practice
-- in SA consistently uses 4-5 events. Keep 5-stage structure but keep
-- aligned with FERTASA's "planting + V6-V8 + pre-tassel" emphasis.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Maize (irrigated)', 'Planting & establishment', 1, 9, 10,
     15, 80, 60, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'FERTASA 5.4.4: all P + K pre-plant/at planting. Sandy FS soils: split planting-N further (seedbed salt-burn limit).'),
    ('Maize (irrigated)', 'Early vegetative (V4-V6)', 2, 10, 11,
     25, 10, 15, 20, 20, 20, 20, 20, 20, 20, 1, 'fertigation',
     'FERTASA 5.4.4: before 5-6 weeks post-emergence is the side-dress window.'),
    ('Maize (irrigated)', 'Late vegetative / pre-tassel (V8-VT)', 3, 11, 12,
     30, 5, 15, 20, 20, 20, 20, 25, 20, 20, 1, 'fertigation',
     'FERTASA 5.4.4: N-K uptake peaks 2 weeks before flowering.'),
    ('Maize (irrigated)', 'Silking & grain fill (R1-R3)', 4, 12, 1,
     20, 3, 7, 20, 20, 20, 20, 15, 20, 20, 1, 'fertigation',
     'FERTASA 5.4.4: P-uptake peaks at flowering. On >10 t/ha yields add 20-30 kg N/additional ton.'),
    ('Maize (irrigated)', 'Late grain fill to maturity (R4-R6)', 5, 2, 3,
     10, 2, 3, 15, 15, 15, 15, 15, 15, 15, 0, 'fertigation',
     'FERTASA 5.4.4: uptake tapers post-flowering.');


-- ─── CANOLA — FERTASA 5.5.1 Table 5.5.1.2 ─────────────────────────────
-- Explicit split: "30 broadcast OR 20 band-placed at planting; 40-50 at
-- 20 DAE; 40-50 at 50 DAE; 40-50 at stem elongation (70-80 DAE)."
-- Gives ~17/25/25/25/8 of ~180 kg/ha across 5 windows.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Canola', 'Planting & emergence', 1, 4, 5,
     17, 75, 70, 25, 25, 30, 25, 25, 25, 25, 1, 'band_place',
     'FERTASA 5.5.1 Table 5.5.1.2: 30 kg N broadcast OR 20 kg N band. S critical — 15-30 kg S/ha (4x wheat).'),
    ('Canola', 'Early rosette (20 DAE)', 2, 5, 6,
     25, 10, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'FERTASA 5.5.1 Table 5.5.1.2: 40-50 kg N at 20 days after emergence.'),
    ('Canola', 'Late rosette (50 DAE)', 3, 6, 7,
     25, 5, 10, 25, 25, 20, 25, 25, 25, 25, 1, 'broadcast',
     'FERTASA 5.5.1 Table 5.5.1.2: 40-50 kg N at 50 DAE.'),
    ('Canola', 'Stem elongation (70-80 DAE)', 4, 7, 8,
     25, 3, 3, 15, 15, 15, 15, 25, 15, 15, 1, 'broadcast',
     'FERTASA 5.5.1 Table 5.5.1.2: 40-50 kg N at stem elongation. B foliar spray 1-1.5 kg sodium tetraborate/ha here.'),
    ('Canola', 'Flowering & pod fill', 5, 9, 11,
     8, 2, 2, 10, 10, 10, 10, 15, 10, 10, 0, 'broadcast',
     'FERTASA 5.5.1: if rotation has no legume, add 20 kg N/ha at flowering.');


-- ─── AVOCADO — FERTASA 5.7.1 ──────────────────────────────────────────
-- Direct quote: "Nitrogen should be applied in three or four split
-- applications, most of which will coincide with the summer flush
-- during January/February."
-- "Most of the potassium fertilizer should be applied after fruit-set
-- to promote fruit size and quality."
-- "Phosphorus fertilization... A single application during the winter
-- months is sufficient."
-- Fix from 041: peak N should be Jan-Feb stage, not spring flush stage.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Avocado', 'Pre-flower / winter (P window)', 1, 5, 7,
     10, 100, 15, 15, 15, 15, 15, 25, 15, 15, 1, 'broadcast',
     'FERTASA 5.7.1: P single application during winter months. Cauliflower stage end.'),
    ('Avocado', 'Anthesis + fruit set', 2, 8, 9,
     15, 0, 15, 25, 20, 20, 20, 30, 20, 20, 1, 'fertigation',
     'FERTASA 5.7.1: "N can be applied earlier than January/February; shortly after fruit set for Hass, or once the spring flush has fully expanded." Fuerte sensitive to early N → fruit drop.'),
    ('Avocado', 'Spring flush / early fruit growth', 3, 10, 12,
     25, 0, 30, 20, 25, 25, 25, 20, 25, 25, 1, 'fertigation',
     'FERTASA 5.7.1: K applied after fruit-set.'),
    ('Avocado', 'Summer flush (PEAK N — FERTASA Jan/Feb)', 4, 1, 2,
     40, 0, 30, 20, 25, 25, 25, 15, 25, 25, 2, 'fertigation',
     'FERTASA 5.7.1 direct: "most [N] will coincide with the summer flush during January/February."'),
    ('Avocado', 'Post-harvest / pre-floral initiation', 5, 3, 4,
     10, 0, 10, 20, 15, 15, 15, 10, 15, 15, 1, 'broadcast',
     'FERTASA 5.7.1: K sulphate preferred over MOP (Cl sensitivity / leaf scorch). B & Zn soil-applied (immobile in plant).');


-- ─── CITRUS (VALENCIA + GRAPEFRUIT) — fix stage 1/2 month ordering ────
-- Migration 041 had Valencia + Grapefruit with stage 1 at months 9-10
-- and stage 2 at months 8-9 — out of chronological order. Fix.
-- FERTASA 5.7.3 Table 5.7.3.4: "Nitrogen: July to November. Phosphorus:
-- Any time of the year. Potassium: August/September/October."
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Citrus (Valencia)', 'Winter pre-flush', 1, 7, 8,
     20, 50, 15, 15, 15, 15, 15, 20, 15, 15, 1, 'fertigation',
     'FERTASA 5.7.3 Table 5.7.3.4: N Jul-Nov; P anytime; K Aug-Oct. Never apply N+K simultaneously (salinity spike).'),
    ('Citrus (Valencia)', 'Flowering / spring flush', 2, 9, 10,
     25, 50, 50, 20, 20, 20, 20, 25, 20, 20, 2, 'fertigation',
     'FERTASA 5.7.3: K window Aug-Sep-Oct. Separate N and K by >=2 irrigations.'),
    ('Citrus (Valencia)', 'Fruit set / cell division', 3, 11, 12,
     25, 0, 20, 25, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Peak uptake. Leaf sample Mar-May.'),
    ('Citrus (Valencia)', 'Summer fruit growth', 4, 1, 2,
     25, 0, 15, 25, 25, 25, 25, 15, 25, 25, 1, 'fertigation',
     'FERTASA 5.7.3: Aug-Feb split window.'),
    ('Citrus (Valencia)', 'Maturation / harvest (Jul-Sep)', 5, 4, 6,
     5, 0, 0, 15, 15, 15, 15, 15, 15, 15, 0, 'fertigation',
     'Valencia late-harvest Jul-Sep. Minimise N — delays internal colour break.'),
    ('Citrus (Grapefruit)', 'Winter pre-flush', 1, 7, 8,
     20, 50, 15, 15, 15, 15, 15, 20, 15, 15, 1, 'fertigation',
     'FERTASA 5.7.3. UF IFAS: grapefruit 10-15% less N than oranges.'),
    ('Citrus (Grapefruit)', 'Flowering / spring flush', 2, 9, 10,
     25, 50, 50, 20, 20, 20, 20, 25, 20, 20, 2, 'fertigation',
     'Star Ruby dominant (~80% SA grapefruit). K window Aug-Oct.'),
    ('Citrus (Grapefruit)', 'Fruit set / cell division', 3, 11, 12,
     25, 0, 20, 25, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Peak N uptake.'),
    ('Citrus (Grapefruit)', 'Summer fruit growth', 4, 1, 2,
     25, 0, 15, 25, 25, 25, 25, 15, 25, 25, 1, 'fertigation',
     'Grapefruit larger fruit justifies high K here.'),
    ('Citrus (Grapefruit)', 'Maturation / harvest (Apr-Sep)', 5, 4, 6,
     5, 0, 0, 15, 15, 15, 15, 15, 15, 15, 0, 'fertigation',
     'Grapefruit harvest Apr-Sep.');


COMMIT;
