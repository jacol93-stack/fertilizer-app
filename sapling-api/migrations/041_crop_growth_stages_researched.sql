-- ============================================================
-- Researched SA growth-stage NPK splits
-- ============================================================
-- Replaces the generic seed values in crop_growth_stages with cited
-- splits from the 2026-04-19 research sweep (SAMAC/FERTASA/SAAGA/CRI/
-- Hortgro/Winetech/SATI/BerriesZA/GrainSA/SASRI/SA Olive/Starke Ayres/
-- ARC-VOPI/NB Systems/Potatoes SA + international fallbacks where SA
-- sources are gated).
--
-- Sources + confidence grade for every crop are in the research memory
-- files: research_growth_stages_{subtropicals,citrus,deciduous,
-- grapes_berries,field_crops,vegetables,specialty}.md. The consolidated
-- index is research_growth_stages_consolidated.md.
--
-- This migration updates ONLY n_pct / p_pct / k_pct / month_start /
-- month_end / stage_name / stage_order / notes. Secondary nutrient
-- splits (ca_pct/mg_pct/s_pct/fe_pct/b_pct/mn_pct/zn_pct) are preserved
-- from the existing seed pending a separate research round.
--
-- Canonical-name fixes:
--   Grape (Wine)        -> Wine Grape          (industry usage)
--   Grape (Table)       -> Table Grape         (industry usage)
--   Potatoes            -> Potato              (singular, seed-data style)
--   Peach/Nectarine     -> (drop; keep Peach + Nectarine separate)
--   Maize (dryland)     -> (fold into Maize)
--   Dry Beans           -> (fold into Bean (Dry))
--   Green Beans         -> (fold into Bean (Green))
--   Lucerne/Alfalfa     -> (fold into Lucerne)
--
-- New crops added:
--   Asparagus (perennial, missing from current seed)
--   Lentils (annual, missing from current seed)
--
-- REVIEW BEFORE APPLYING: apple split changes materially (current seed
-- over-allocated mid-summer N; new split from Cheng 2013 Cornell is
-- bloom-heavy). Malting barley split is distinctly different from
-- wheat (protein cap dictates front-loading). Rooibos split sets N% = 0
-- everywhere — rooibos is a legume and does not take up synthetic N.
-- ============================================================

BEGIN;

-- ─── Canonical-name cleanup ────────────────────────────────────────────
-- Delete alias rows first so the subsequent DELETE WHERE crop=... doesn't
-- accidentally sweep the canonical row.

DELETE FROM crop_growth_stages WHERE crop IN (
    'Grape (Wine)', 'Grape (Table)',
    'Potatoes',
    'Peach/Nectarine',
    'Maize (dryland)',
    'Dry Beans',
    'Green Beans',
    'Lucerne/Alfalfa'
);

-- Also clean up any pre-existing rows for canonical crops we're about
-- to re-seed, so the INSERTs below land on a clean slate.
DELETE FROM crop_growth_stages WHERE crop IN (
    -- Subtropicals (High/Medium-High)
    'Macadamia', 'Pecan', 'Litchi', 'Avocado', 'Pomegranate',
    -- Citrus (all Medium)
    'Citrus (Valencia)', 'Citrus (Navel)', 'Citrus (Lemon)',
    'Citrus (Grapefruit)', 'Citrus (Soft Citrus)',
    -- Deciduous (Apple High; rest Medium; Persimmon Low)
    'Apple', 'Pear', 'Peach', 'Nectarine', 'Apricot', 'Plum', 'Cherry',
    -- Grapes + berries
    'Wine Grape', 'Table Grape', 'Blueberry', 'Strawberry',
    -- Field crops
    'Maize', 'Maize (irrigated)', 'Sweetcorn',
    'Wheat', 'Barley', 'Oat',
    'Sorghum', 'Sunflower', 'Canola',
    'Soybean', 'Groundnut', 'Cotton', 'Tobacco',
    'Bean (Dry)', 'Bean (Green)', 'Pea', 'Lucerne',
    -- Vegetables
    'Potato', 'Sweet Potato', 'Tomato', 'Pepper (Bell)',
    'Cabbage', 'Lettuce', 'Spinach',
    'Onion', 'Garlic', 'Carrot',
    'Butternut', 'Pumpkin', 'Watermelon',
    -- Specialty perennials
    'Sugarcane', 'Olive', 'Banana', 'Pineapple',
    'Coffee', 'Tea', 'Rooibos',
    -- New
    'Asparagus', 'Lentils'
);


-- ─── SUBTROPICALS ──────────────────────────────────────────────────────

-- Macadamia — FERTASA ch. 5.8.1 (Hawksworth & Sheard 2022). HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Macadamia', 'Post-harvest / flower initiation', 1, 5, 7,
     25, 20, 15, 25, 15, 15, 15, 25, 15, 15, 1, 'broadcast',
     'FERTASA 5.8.1. N supplemented Apr–Dec only. First N+K application.'),
    ('Macadamia', 'Main flowering + nut set', 2, 8, 9,
     40, 20, 20, 50, 25, 20, 20, 20, 25, 20, 2, 'broadcast',
     'FERTASA 5.8.1. Peak N for spring flush + nut set. Ca 50% for shell build.'),
    ('Macadamia', 'Nut development + oil accumulation start', 3, 10, 12,
     25, 40, 50, 15, 35, 40, 35, 40, 35, 40, 2, 'fertigation',
     'FERTASA 5.8.1: peak K Oct–Dec for new growth and nut development. Second P application.'),
    ('Macadamia', 'Oil fill taper / pre-harvest', 4, 1, 3,
     10, 20, 15, 10, 25, 25, 30, 15, 25, 25, 1, 'broadcast',
     'FERTASA 5.8.1: up to 10% N in Jan then stopped. Vegetative growth hampers oil accumulation.');

-- Pecan — FERTASA ch. 5.8.2 (Schmidt ARC-TSC 2021). HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Pecan', 'Bud break + leaf expansion', 1, 9, 10,
     30, 20, 15, 20, 20, 20, 20, 20, 20, 30, 2, 'fertigation',
     'FERTASA 5.8.2. Supplementary nutrition starts 3 weeks after bud-break. Zn foliars also begin here.'),
    ('Pecan', 'Flowering + early shoot growth', 2, 11, 12,
     25, 20, 25, 30, 25, 25, 25, 30, 25, 25, 2, 'fertigation',
     'FERTASA 5.8.2. Male/female flowering; nut set requires both N and K.'),
    ('Pecan', 'Nut fill (water/oil/kernel)', 3, 1, 3,
     25, 25, 35, 30, 35, 30, 30, 30, 30, 25, 3, 'fertigation',
     'FERTASA 5.8.2 Table 5: K focused during nut-fill. Kernel fill Feb–Apr.'),
    ('Pecan', 'Shuck split + harvest + winter fertilization', 4, 4, 6,
     20, 35, 25, 20, 20, 25, 25, 20, 25, 20, 1, 'broadcast',
     'FERTASA 5.8.2 Table 4 winter multipliers: N×0.25, P×0.10, K×0.3–0.5 of in-season rate.');

-- Litchi — DAFF Infopak + Subtrop Vegetables & Fruit 2022. MEDIUM-HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Litchi', 'Post-harvest flush (post-harvest N + all P)', 1, 1, 3,
     40, 70, 20, 25, 25, 25, 25, 20, 25, 25, 2, 'broadcast',
     'DAFF Infopak. Half N + all P post-harvest. Rebuild reserves.'),
    ('Litchi', 'Pre-flowering (autumn hardening)', 2, 4, 6,
     5, 5, 5, 10, 10, 10, 10, 5, 10, 10, 1, 'broadcast',
     'DAFF: very high N rates depress yield via autumn vegetative flushing.'),
    ('Litchi', 'Flowering + fruit set', 3, 8, 10,
     35, 15, 35, 35, 30, 30, 30, 40, 30, 30, 2, 'fertigation',
     'DAFF: half N + half K immediately before flowering. B critical for fruit set.'),
    ('Litchi', 'Fruit growth + maturation', 4, 11, 12,
     20, 10, 40, 30, 35, 35, 35, 35, 35, 35, 2, 'fertigation',
     'Subtrop V&F 2022: 60–70% annual K between full bloom and 2nd fruit drop.');

-- Avocado (Hass focus) — Lovatt SH-converted. MEDIUM. SAAGA has no public split.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Avocado', 'Pre-flower (cauliflower stage)', 1, 5, 6,
     15, 10, 15, 20, 15, 15, 15, 25, 15, 15, 1, 'broadcast',
     'Lovatt HortScience 2001 SH-converted. SAAGA public stage-split absent — refine with Westfalia/ZZ2.'),
    ('Avocado', 'Anthesis + early fruit set + spring flush', 2, 7, 8,
     25, 30, 15, 25, 20, 20, 20, 30, 20, 20, 2, 'fertigation',
     'Lovatt: early fruit set is the most critical stage. P demand high.'),
    ('Avocado', 'Summer fruit growth (cell division)', 3, 10, 12,
     25, 25, 30, 20, 25, 25, 25, 20, 25, 25, 2, 'fertigation',
     'SA spring flush + fruit sizing.'),
    ('Avocado', 'Mid-summer fruit expansion', 4, 1, 2,
     20, 20, 25, 15, 25, 25, 25, 15, 25, 25, 2, 'fertigation',
     'Exponential fruit growth; K peaks for fill.'),
    ('Avocado', 'Post-harvest / pre-floral initiation', 5, 3, 4,
     15, 15, 15, 20, 15, 15, 15, 10, 15, 15, 1, 'broadcast',
     'Reserve replenishment.');

-- Pomegranate — POMASA (Mulder). MEDIUM-LOW.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Pomegranate', 'Post-dormancy budbreak + spring flush', 1, 9, 10,
     40, 30, 25, 25, 25, 25, 25, 30, 25, 25, 2, 'fertigation',
     'POMASA: N during new vegetative flush. Budbreak Sep.'),
    ('Pomegranate', 'Flowering + fruit set', 2, 11, 12,
     30, 30, 30, 25, 25, 25, 25, 30, 25, 25, 2, 'fertigation',
     'Multiple bloom waves; balanced demand.'),
    ('Pomegranate', 'Fruit fill + colour', 3, 1, 3,
     20, 20, 35, 30, 30, 30, 30, 25, 30, 30, 2, 'fertigation',
     'POMASA: reduce N:P ratio closer to ripening for colour and sugar.'),
    ('Pomegranate', 'Harvest + post-harvest', 4, 4, 6,
     10, 20, 10, 20, 20, 20, 20, 15, 20, 20, 1, 'broadcast',
     'Wonderful cultivar harvest ~Apr. Restore reserves only.');


-- ─── CITRUS ────────────────────────────────────────────────────────────
-- All Medium confidence pending Raath 2021 handbook purchase (R250, CRI).

INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    -- Valencia
    ('Citrus (Valencia)', 'Post-harvest recovery', 1, 9, 10,
     20, 25, 15, 15, 15, 15, 15, 20, 15, 15, 1, 'fertigation',
     'CDFA/UC Davis/Haifa reconstruction. Raath 2021 pending.'),
    ('Citrus (Valencia)', 'Flowering / spring flush', 2, 8, 9,
     25, 20, 15, 20, 20, 20, 20, 25, 20, 20, 2, 'fertigation',
     'SA spring flush. N uptake rises at bud-break.'),
    ('Citrus (Valencia)', 'Fruit set / cell division', 3, 10, 11,
     30, 20, 20, 25, 25, 25, 25, 25, 25, 25, 3, 'fertigation',
     'Peak N uptake. Yara SA: up to 2 kg/ha N per day during fruit enlargement.'),
    ('Citrus (Valencia)', 'Cell expansion / fruit swell', 4, 12, 3,
     20, 20, 35, 25, 25, 25, 25, 15, 25, 25, 3, 'fertigation',
     'K peaks here — fruit size, TSS, peel quality.'),
    ('Citrus (Valencia)', 'Maturation / harvest', 5, 4, 8,
     5, 15, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'fertigation',
     'Valencia late-harvest Jul–Sep. Minimize N — delays internal colour break.'),
    -- Navel (same split, stage 5 window shifted)
    ('Citrus (Navel)', 'Post-harvest recovery', 1, 8, 9,
     20, 25, 15, 15, 15, 15, 15, 20, 15, 15, 1, 'fertigation',
     'CDFA/UC Davis/Haifa reconstruction. Raath 2021 pending.'),
    ('Citrus (Navel)', 'Flowering / spring flush', 2, 9, 10,
     25, 20, 15, 20, 20, 20, 20, 25, 20, 20, 2, 'fertigation',
     'EC/WC cooler regions flower slightly later than Valencia.'),
    ('Citrus (Navel)', 'Fruit set / cell division', 3, 10, 11,
     30, 20, 20, 25, 25, 25, 25, 25, 25, 25, 3, 'fertigation',
     'Peak N uptake.'),
    ('Citrus (Navel)', 'Cell expansion / fruit swell', 4, 12, 3,
     20, 20, 35, 25, 25, 25, 25, 15, 25, 25, 3, 'fertigation',
     'K peaks for fruit size.'),
    ('Citrus (Navel)', 'Maturation / harvest', 5, 4, 7,
     5, 15, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'fertigation',
     'Navel harvest Apr–Jul. Minimize N.'),
    -- Lemon (4 stages — everbearing)
    ('Citrus (Lemon)', 'Late winter / pre-flush', 1, 7, 8,
     30, 30, 20, 25, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Lemon flushes 3–4× per year; splits are monthly averages, not discrete phenology.'),
    ('Citrus (Lemon)', 'Spring flush / main flowering', 2, 9, 10,
     25, 25, 20, 25, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Primary spring flush.'),
    ('Citrus (Lemon)', 'Summer fruit development', 3, 11, 1,
     25, 20, 30, 25, 25, 25, 25, 25, 25, 25, 3, 'fertigation',
     'Continuous fruit set on overlapping flushes.'),
    ('Citrus (Lemon)', 'Autumn maturation / continued flushes', 4, 2, 6,
     20, 25, 30, 25, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Main crop maturation + secondary flush sets.'),
    -- Grapefruit (same split as Valencia; ~10–15% lower absolute N target per UF IFAS)
    ('Citrus (Grapefruit)', 'Post-harvest recovery', 1, 9, 10,
     20, 25, 15, 15, 15, 15, 15, 20, 15, 15, 1, 'fertigation',
     'UF IFAS: 10–15% less N than oranges. Raath 2021 pending.'),
    ('Citrus (Grapefruit)', 'Flowering / spring flush', 2, 8, 9,
     25, 20, 15, 20, 20, 20, 20, 25, 20, 20, 2, 'fertigation',
     'SA Star Ruby dominant (~80% SA grapefruit).'),
    ('Citrus (Grapefruit)', 'Fruit set / cell division', 3, 10, 11,
     30, 20, 20, 25, 25, 25, 25, 25, 25, 25, 3, 'fertigation',
     'Peak N uptake.'),
    ('Citrus (Grapefruit)', 'Cell expansion / fruit swell', 4, 12, 3,
     20, 20, 35, 25, 25, 25, 25, 15, 25, 25, 3, 'fertigation',
     'Grapefruit larger fruit justifies high K.'),
    ('Citrus (Grapefruit)', 'Maturation / harvest', 5, 4, 7,
     5, 15, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'fertigation',
     'Grapefruit harvest Apr–Sep.'),
    -- Soft Citrus (K bumped 40% in stage 4; N lifted at bloom per Lovatt Clementine)
    ('Citrus (Soft Citrus)', 'Post-harvest recovery', 1, 8, 9,
     15, 25, 10, 15, 15, 15, 15, 20, 15, 15, 1, 'fertigation',
     'Nadorcott ~37% of SA plantings. Raath 2021 pending.'),
    ('Citrus (Soft Citrus)', 'Flowering / spring flush', 2, 9, 10,
     30, 25, 15, 20, 20, 20, 20, 30, 20, 20, 2, 'fertigation',
     'Lovatt Clementine pre-bloom urea trials: higher N at bloom.'),
    ('Citrus (Soft Citrus)', 'Fruit set / cell division', 3, 10, 11,
     30, 20, 20, 25, 25, 25, 25, 25, 25, 25, 3, 'fertigation',
     'Peak N uptake.'),
    ('Citrus (Soft Citrus)', 'Rapid fruit swell', 4, 12, 2,
     20, 20, 40, 25, 25, 25, 25, 15, 25, 25, 3, 'fertigation',
     'Mandarin rapid swell: K% bumped to 40% (vs 35% oranges).'),
    ('Citrus (Soft Citrus)', 'Maturation / harvest', 5, 3, 7,
     5, 10, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'fertigation',
     'Soft citrus harvest Mar–Jul span varies by cultivar.');


-- ─── DECIDUOUS (POME + STONE) ──────────────────────────────────────────

-- Apple — Cornell Cheng 2013 uptake curves (transferable). HIGH.
-- Material change from current seed (was 10/5/20/40/25 for N).
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Apple', 'Dormancy', 1, 6, 8,
     0, 5, 0, 5, 5, 5, 5, 5, 5, 5, 0, 'broadcast',
     'Cheng 2013 Cornell. N/K uptake minimal. P broadcast now.'),
    ('Apple', 'Bud break & bloom', 2, 9, 9,
     25, 20, 10, 15, 15, 15, 15, 25, 15, 15, 1, 'fertigation',
     'Early N drives spur-leaf area. B for fruit set.'),
    ('Apple', 'Cell division / fruit set', 3, 10, 11,
     35, 25, 25, 35, 30, 30, 30, 30, 30, 30, 3, 'fertigation',
     'Cheng 2013 Fig 1A: peak N demand 4–6 weeks post-full-bloom.'),
    ('Apple', 'Cell expansion / fruit sizing', 4, 12, 1,
     25, 25, 40, 30, 30, 30, 30, 25, 30, 30, 3, 'fertigation',
     'K-dominant window. N tapered to protect storage quality and Ca partitioning (Lötze).'),
    ('Apple', 'Post-harvest recovery', 5, 2, 5,
     15, 25, 25, 15, 20, 20, 20, 15, 20, 20, 1, 'broadcast',
     'Cheng 2013: N reserves for next spring''s spur leaves.');

-- Pear — same biology as apple; Medium on split.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Pear', 'Dormancy', 1, 6, 8,
     0, 5, 0, 5, 5, 5, 5, 5, 5, 5, 0, 'broadcast',
     'Stassen & North 2008 Forelle + apple biology. P broadcast.'),
    ('Pear', 'Bud break & bloom', 2, 9, 10,
     25, 20, 10, 15, 15, 15, 15, 25, 15, 15, 1, 'fertigation',
     'Pear has higher B demand at bloom than apple.'),
    ('Pear', 'Cell division / fruit set', 3, 10, 11,
     35, 25, 25, 35, 30, 30, 30, 30, 30, 30, 3, 'fertigation',
     'Peak vegetative + fruit N demand.'),
    ('Pear', 'Cell expansion', 4, 12, 2,
     25, 25, 40, 30, 30, 30, 30, 25, 30, 30, 3, 'fertigation',
     'K-heavy. Forelle/Packham''s benefit from K for flesh texture and blush.'),
    ('Pear', 'Post-harvest recovery', 5, 3, 5,
     15, 25, 25, 15, 20, 20, 20, 15, 20, 20, 1, 'broadcast',
     'Reserve N build.');

-- Peach — CDFA + Haifa stone-fruit biology. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Peach', 'Dormancy', 1, 5, 6,
     0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 'broadcast',
     'CDFA: N uptake minimal during dormancy.'),
    ('Peach', 'Bud break & bloom', 2, 7, 8,
     15, 20, 15, 15, 15, 15, 15, 25, 15, 15, 1, 'fertigation',
     'Haifa: ~15% K at leaf emergence, 20% at flowering.'),
    ('Peach', 'Fruit set & cell division (incl pit hardening)', 3, 9, 10,
     30, 25, 25, 30, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Compressed 90-day bloom→harvest window.'),
    ('Peach', 'Cell expansion & ripening', 4, 11, 1,
     30, 25, 40, 30, 30, 30, 30, 25, 30, 30, 3, 'fertigation',
     'CDFA: end fertigation 50 days before harvest.'),
    ('Peach', 'Post-harvest recovery', 5, 2, 4,
     25, 25, 15, 20, 25, 25, 25, 20, 25, 25, 1, 'broadcast',
     'Haifa: post-harvest 45–60 kg N/ha to rebuild reserves.');

-- Nectarine — identical biology to Peach.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Nectarine', 'Dormancy', 1, 5, 6,
     0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 'broadcast',
     'Krige & Stassen 2008 Donnarine — identical stage biology to peach.'),
    ('Nectarine', 'Bud break & bloom', 2, 7, 8,
     15, 20, 15, 15, 15, 15, 15, 25, 15, 15, 1, 'fertigation',
     'Same as peach.'),
    ('Nectarine', 'Fruit set & pit hardening', 3, 9, 10,
     30, 25, 25, 30, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Same as peach.'),
    ('Nectarine', 'Cell expansion & ripening', 4, 11, 1,
     30, 25, 40, 30, 30, 30, 30, 25, 30, 30, 3, 'fertigation',
     'Same as peach.'),
    ('Nectarine', 'Post-harvest recovery', 5, 2, 4,
     25, 25, 15, 20, 25, 25, 25, 20, 25, 25, 1, 'broadcast',
     'Same as peach.');

-- Apricot — very short cycle (90–110 days). MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Apricot', 'Dormancy', 1, 5, 6,
     0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 'broadcast',
     'Klein Karoo dominant. Earliest stone fruit.'),
    ('Apricot', 'Bud break & bloom', 2, 7, 8,
     20, 25, 15, 15, 15, 15, 15, 30, 15, 15, 1, 'fertigation',
     'B critical at bloom (Hortgro Stone).'),
    ('Apricot', 'Fruit set & pit hardening', 3, 9, 10,
     35, 25, 30, 30, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Short 90-day cycle → most nutrients needed before Nov.'),
    ('Apricot', 'Ripening & harvest', 4, 11, 12,
     20, 25, 35, 30, 30, 30, 30, 20, 30, 30, 2, 'fertigation',
     'K for sugar/flavour final 3–4 weeks.'),
    ('Apricot', 'Post-harvest recovery', 5, 1, 4,
     25, 20, 15, 20, 25, 25, 25, 20, 25, 25, 1, 'broadcast',
     'Long Jan–Apr recovery window.');

-- Plum — longer season than peach. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Plum', 'Dormancy', 1, 5, 7,
     0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 'broadcast',
     'WC Paarl/Wellington/Stellenbosch dominant. 93% Japanese plum.'),
    ('Plum', 'Bud break & bloom', 2, 8, 9,
     20, 25, 15, 15, 15, 15, 15, 25, 15, 15, 1, 'fertigation',
     'Songold/Sapphire/Laetitia/African Delight/Angeleno.'),
    ('Plum', 'Fruit set & cell division', 3, 10, 11,
     30, 25, 25, 30, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Peak vegetative + fruit demand.'),
    ('Plum', 'Cell expansion & ripening', 4, 12, 2,
     25, 25, 40, 30, 30, 30, 30, 25, 30, 30, 3, 'fertigation',
     'K drives skin colour + brix in Songold/Angeleno.'),
    ('Plum', 'Post-harvest recovery', 5, 3, 4,
     25, 20, 15, 20, 25, 25, 25, 20, 25, 25, 1, 'broadcast',
     'Restore reserves.');

-- Cherry — lightest feeder. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Cherry', 'Dormancy', 1, 5, 7,
     0, 10, 5, 5, 5, 5, 5, 5, 5, 5, 0, 'broadcast',
     'WSU: cherry lightest feeder in stone group. P winter-applied.'),
    ('Cherry', 'Bud break & bloom', 2, 8, 9,
     25, 25, 20, 20, 20, 20, 20, 30, 20, 20, 1, 'fertigation',
     'WSU: most uptake between bloom and rapid vegetative growth.'),
    ('Cherry', 'Fruit set & cell division', 3, 10, 10,
     30, 25, 30, 30, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Fast cell division (~60–80 days bloom→harvest). Peak uptake.'),
    ('Cherry', 'Ripening & harvest', 4, 11, 12,
     15, 20, 30, 25, 25, 25, 25, 20, 25, 25, 2, 'fertigation',
     'WSU: stop N ≥1 month before harvest.'),
    ('Cherry', 'Post-harvest recovery', 5, 1, 4,
     30, 20, 15, 20, 25, 25, 25, 20, 25, 25, 1, 'broadcast',
     'Long 4-month post-harvest → heavy reserve build.');


-- ─── GRAPES + BERRIES ──────────────────────────────────────────────────

-- Wine Grape — Conradie 1986/2022 SAJEV + CDFA. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Wine Grape', 'Dormancy / pre-bud break', 1, 6, 7,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'broadcast',
     'Conradie 1986 15N-labelled: negligible uptake pre-budbreak.'),
    ('Wine Grape', 'Bud break to flowering', 2, 8, 10,
     20, 25, 15, 20, 20, 20, 20, 25, 20, 20, 1, 'fertigation',
     'SA wine-quality principle: restrict early N for vigour control.'),
    ('Wine Grape', 'Flowering to veraison', 3, 11, 12,
     30, 30, 45, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation',
     'CDFA: ~50% annual N and ~60% annual K in this window. K drives berry expansion.'),
    ('Wine Grape', 'Veraison to harvest', 4, 1, 3,
     15, 10, 10, 20, 20, 20, 20, 20, 20, 20, 1, 'fertigation',
     'N restricted for quality/colour. K uptake decelerates post-veraison.'),
    ('Wine Grape', 'Post-harvest (leaf fall)', 5, 4, 5,
     35, 35, 30, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast',
     'Conradie 1986: post-harvest N 68% retained as reserves — critical for next-season bud fertility.');

-- Table Grape — Conradie 2022 Sultanina partitioning + Saayman 1995 Barlinka. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Table Grape', 'Dormancy / pruning', 1, 5, 7,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'broadcast',
     'Conradie 2022: uptake effectively zero during dormancy.'),
    ('Table Grape', 'Bud break to fruit-set', 2, 8, 10,
     25, 38, 20, 25, 20, 20, 20, 30, 20, 20, 2, 'fertigation',
     'Conradie 2022 Sultanina Lower Orange sand. Canopy + inflorescence.'),
    ('Table Grape', 'Fruit-set to veraison (berry development)', 3, 11, 12,
     42, 20, 45, 35, 35, 35, 35, 30, 35, 35, 2, 'fertigation',
     'Conradie 2022: Sultanina "fruit-set to harvest" 41.8% N sandy / 55.7% alluvial. Table-grape berry size window.'),
    ('Table Grape', 'Veraison to harvest', 4, 12, 3,
     8, 5, 20, 15, 20, 20, 20, 15, 20, 20, 2, 'fertigation',
     'Saayman 1995: >105 kg N/ha reduced colour/sugar in Barlinka.'),
    ('Table Grape', 'Post-harvest (reserve replenishment)', 5, 3, 5,
     25, 37, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Efficient N uptake window. Orange River shifts one month earlier.');

-- Blueberry (Southern Highbush, WC Aug bud-break / Oct–Jan harvest). MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Blueberry', 'Dormancy / chill accumulation', 1, 5, 7,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'broadcast',
     'No active uptake. pH management (acidic 4.0–5.2).'),
    ('Blueberry', 'Bud break to bloom', 2, 8, 9,
     25, 25, 15, 25, 20, 20, 20, 30, 20, 20, 2, 'fertigation',
     'UGA C1163: 25% annual N at bud break. AMMONIUM-N form preferred.'),
    ('Blueberry', 'Fruit set to fruit development', 3, 10, 11,
     30, 25, 40, 30, 25, 25, 25, 25, 25, 25, 3, 'fertigation',
     'Peak K for sugar + firmness.'),
    ('Blueberry', 'Ripening & harvest', 4, 11, 1,
     10, 10, 30, 25, 20, 20, 20, 20, 20, 20, 2, 'fertigation',
     'K for °Brix and shelf-life. N restricted.'),
    ('Blueberry', 'Post-harvest (summer pruning, floral bud induction)', 5, 2, 4,
     35, 40, 15, 20, 35, 35, 35, 25, 35, 35, 1, 'fertigation',
     'Pescie 2018: post-harvest N drives next-season floral bud differentiation.');

-- Strawberry — Haifa + NSW DPI (short-day dominant SA). MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Strawberry', 'Transplant & establishment', 1, 3, 4,
     10, 25, 10, 20, 15, 15, 15, 20, 15, 15, 1, 'fertigation',
     'Haifa / NSW DPI. No SA industry body publishes split — international fallback.'),
    ('Strawberry', 'Vegetative & crown development', 2, 5, 6,
     25, 25, 20, 25, 25, 25, 25, 25, 25, 25, 2, 'fertigation',
     'Runner/crown canopy; N drives leaf area.'),
    ('Strawberry', 'Flowering & fruit set', 3, 7, 8,
     20, 25, 20, 25, 25, 25, 25, 30, 25, 25, 2, 'fertigation',
     'B for pollen viability; K ramping.'),
    ('Strawberry', 'Fruit development & harvest (peak)', 4, 9, 11,
     35, 15, 40, 20, 25, 25, 25, 15, 25, 25, 3, 'fertigation',
     'K:N ~3–4:1 during fruiting (universal).'),
    ('Strawberry', 'Late fruiting & senescence', 5, 12, 2,
     10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 1, 'fertigation',
     'Day-neutral Southern Cape cycles differently.');


-- ─── FIELD CROPS ───────────────────────────────────────────────────────

-- Maize (canonical; dryland default) — FERTASA/GrainSA/SA Grain. HIGH structure, MEDIUM %.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Maize', 'Planting & establishment (VE–V3)', 1, 10, 11,
     25, 80, 70, 30, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'FERTASA. Starter band (MAP / 3:2:1) + ~25% N seed-row. Most P and K down at planting.'),
    ('Maize', 'Vegetative / V6–V8 top-dress', 2, 12, 12,
     45, 10, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Primary N top-dress at V6–V8 (growing point emerges).'),
    ('Maize', 'Tasseling / silking (VT–R1)', 3, 1, 2,
     20, 5, 10, 25, 25, 25, 25, 30, 25, 25, 1, 'broadcast',
     'GrainSA: before blossoming most nutrients already absorbed.'),
    ('Maize', 'Grain fill to maturity (R2–R6)', 4, 3, 5,
     10, 5, 5, 20, 25, 25, 25, 20, 25, 25, 0, 'broadcast',
     'Uptake tapers. K redistribution to kernel.');

-- Maize (irrigated) — pivot fertigation, 4–5 split. HIGH structure.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Maize (irrigated)', 'Planting & establishment', 1, 9, 10,
     15, 80, 60, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Vaalharts/Douglas pivots. Lower planting-N than dryland; more splits via fertigation.'),
    ('Maize (irrigated)', 'Early vegetative (V4–V6)', 2, 10, 11,
     25, 10, 15, 20, 20, 20, 20, 20, 20, 20, 1, 'fertigation',
     'First pivot-fertigated N split.'),
    ('Maize (irrigated)', 'Late vegetative / pre-tassel (V8–VT)', 3, 11, 12,
     30, 5, 15, 20, 20, 20, 20, 25, 20, 20, 1, 'fertigation',
     'Peak N demand.'),
    ('Maize (irrigated)', 'Silking & grain fill (R1–R3)', 4, 12, 1,
     20, 3, 7, 20, 20, 20, 20, 15, 20, 20, 1, 'fertigation',
     'Kernel fill.'),
    ('Maize (irrigated)', 'Late grain fill to maturity (R4–R6)', 5, 2, 3,
     10, 2, 3, 15, 15, 15, 15, 15, 15, 15, 0, 'fertigation',
     'Uptake tapers.');

-- Sweetcorn — distinct from maize. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Sweetcorn', 'Planting & establishment', 1, 9, 10,
     15, 75, 55, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Shorter cycle + sandy soils. Vaalharts / Tala Valley.'),
    ('Sweetcorn', 'Small-leaf (V4–V6)', 2, 10, 10,
     30, 15, 20, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'Early top-dress.'),
    ('Sweetcorn', 'Large-leaf (V8–V12)', 3, 11, 11,
     35, 5, 15, 25, 20, 20, 20, 25, 20, 20, 1, 'broadcast',
     'Main top-dress; CERES-Maize sandy-soil BMPs.'),
    ('Sweetcorn', 'Ear development (R1–R3)', 4, 12, 12,
     15, 3, 7, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'Kernel fill.'),
    ('Sweetcorn', 'Harvest', 5, 1, 2,
     5, 2, 3, 10, 15, 15, 15, 10, 15, 15, 0, 'broadcast',
     'No further feed.');

-- Wheat — GrainSA classic 1/3-1/3-1/3 split. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Wheat', 'Planting & establishment', 1, 5, 6,
     20, 70, 60, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'GrainSA. Winter crop. Starter with seed.'),
    ('Wheat', 'Tillering', 2, 6, 7,
     35, 15, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'GrainSA: N sufficiency during tillering — potential ear number is most important yield component.'),
    ('Wheat', 'Stem elongation', 3, 8, 8,
     30, 10, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Classic 1/3-1/3-1/3 split.'),
    ('Wheat', 'Flag leaf / heading / grain fill', 4, 9, 10,
     15, 5, 10, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Late N supports protein (ARC-SGI Wheat Quality).');

-- Barley (malting) — CRITICALLY DIFFERENT from wheat. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Barley', 'Planting & establishment', 1, 5, 6,
     65, 75, 70, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Malting: 2/3 of N at/before planting. Protein cap <1.8% dictates front-loading.'),
    ('Barley', 'Tillering', 2, 6, 7,
     25, 15, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Rest applied from 6 weeks after emergence until flag leaf depending on clay %.'),
    ('Barley', 'Stem elongation / flag leaf', 3, 8, 9,
     10, 5, 10, 25, 25, 25, 25, 35, 25, 25, 0, 'broadcast',
     'Late N avoided — grain protein must be <1.8% for malting grade.'),
    ('Barley', 'Grain fill & maturation', 4, 10, 11,
     0, 5, 5, 20, 25, 25, 25, 20, 25, 25, 0, 'broadcast',
     'Intentionally no N. K for grain plumpness.');

-- Oat — forage focus. MEDIUM/LOW.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Oat', 'Planting & establishment', 1, 3, 4,
     20, 85, 65, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'AGT Foods. ~10 kg P/ha at sowing.'),
    ('Oat', 'Tillering / first graze recovery', 2, 5, 6,
     40, 10, 20, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Oats: ~7.25 kg N / tonne DM.'),
    ('Oat', 'Regrowth / second graze', 3, 7, 8,
     30, 3, 10, 25, 25, 25, 25, 30, 25, 25, 1, 'broadcast',
     'N top-dress after grazing.'),
    ('Oat', 'Heading (grain) / final graze', 4, 9, 10,
     10, 2, 5, 25, 25, 25, 25, 20, 25, 25, 0, 'broadcast',
     'Last cycle before dry-down.');

-- Sorghum — US/AUS structure + SA maize practice. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Sorghum', 'Planting & establishment', 1, 10, 11,
     40, 80, 70, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'P&K at planting. No more than 50% anticipated N as preplant.'),
    ('Sorghum', 'Rapid vegetative (~30 DAE)', 2, 12, 12,
     35, 10, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'First critical N window. Panicle initiation.'),
    ('Sorghum', 'Boot / pre-heading', 3, 1, 2,
     15, 5, 10, 25, 25, 25, 25, 30, 25, 25, 1, 'broadcast',
     'Second critical N window.'),
    ('Sorghum', 'Grain fill & maturation', 4, 3, 5,
     10, 5, 5, 20, 25, 25, 25, 20, 25, 25, 0, 'broadcast',
     'Uptake tapers.');

-- Sunflower — SA 50/50 rule. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Sunflower', 'Planting & establishment', 1, 11, 12,
     50, 80, 75, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'SA signature rule: 50% N at planting (ARC-GCI). P & K pre-planting.'),
    ('Sunflower', 'Vegetative (10–12 leaf, ~30 cm)', 2, 12, 1,
     40, 15, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Top-dress N pre-anthesis.'),
    ('Sunflower', 'Flowering (R1–R5)', 3, 1, 2,
     10, 3, 5, 25, 25, 25, 25, 30, 25, 25, 0, 'broadcast',
     'Minimal late N — seed oil quality at risk.'),
    ('Sunflower', 'Seed fill & maturation', 4, 3, 5,
     0, 2, 5, 25, 25, 25, 25, 20, 25, 25, 0, 'broadcast',
     'No N. K supports seed filling.');

-- Canola — Stellenbosch protocol. HIGH. S critical.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Canola', 'Planting & emergence', 1, 4, 5,
     35, 75, 70, 25, 25, 30, 25, 25, 25, 25, 1, 'band_place',
     'Stellenbosch: 50–70 kg N/ha at planting. S critical (15–30 kg/ha, up to 4× wheat).'),
    ('Canola', 'Rosette', 2, 6, 7,
     30, 10, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Top-dress 30–50 kg N/ha at 6–8 WAP.'),
    ('Canola', 'Stem elongation / bolting', 3, 7, 8,
     20, 10, 10, 25, 25, 20, 25, 25, 25, 25, 1, 'broadcast',
     'Third split (pivot / intensive systems).'),
    ('Canola', 'Flowering & podding', 4, 8, 9,
     10, 3, 3, 15, 15, 15, 15, 30, 15, 15, 0, 'broadcast',
     'B for pod set. Taper N.'),
    ('Canola', 'Pod fill & maturation', 5, 10, 11,
     5, 2, 2, 10, 10, 10, 10, 15, 10, 10, 0, 'broadcast',
     'Minimal uptake.');

-- Soybean — summer legume. HIGH structure.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Soybean', 'Planting & emergence (VE–V2)', 1, 11, 12,
     60, 85, 80, 30, 30, 30, 30, 30, 30, 30, 1, 'band_place',
     'Inoculation (Bradyrhizobium) supplies 50–70% N. Starter N ≤15–20 kg/ha only on sandy soils.'),
    ('Soybean', 'Vegetative (V3–V6)', 2, 12, 1,
     15, 8, 10, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Nodules established; minimal applied N.'),
    ('Soybean', 'Flowering & pod set (R1–R3)', 3, 1, 2,
     10, 3, 5, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'K critical — >60% of P ultimately translocated to seed + pod.'),
    ('Soybean', 'Pod fill & maturation (R5–R7)', 4, 2, 4,
     15, 4, 5, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'K for seed weight.');

-- Groundnut — legume + gypsum at pegging.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Groundnut', 'Planting & establishment', 1, 10, 11,
     50, 80, 70, 30, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Legume — minimal applied N. P & K pre-plant.'),
    ('Groundnut', 'Vegetative', 2, 12, 12,
     20, 10, 10, 20, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Standard growth phase.'),
    ('Groundnut', 'Flowering & pegging', 3, 1, 2,
     20, 5, 10, 35, 25, 25, 25, 30, 25, 25, 1, 'broadcast',
     'GYPSUM 200–300 kg/ha at pegging for pod Ca. Not in NPK split.'),
    ('Groundnut', 'Pod fill & maturation', 4, 3, 5,
     10, 5, 10, 15, 25, 25, 25, 20, 25, 25, 0, 'broadcast',
     'Maturation.');

-- Cotton — K peaks after first bloom. HIGH on late-K timing.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Cotton', 'Planting & establishment', 1, 10, 11,
     10, 75, 55, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Starter P critical. Avoid excess early N (vegetative bias).'),
    ('Cotton', 'Vegetative / squaring', 2, 12, 1,
     30, 15, 20, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Side-dress 20–30 kg N/ha.'),
    ('Cotton', 'Flowering & boll set', 3, 1, 2,
     35, 5, 15, 25, 25, 25, 25, 30, 25, 25, 2, 'broadcast',
     'Cotton Foundation: 70% K uptake after first bloom. Peak N.'),
    ('Cotton', 'Boll fill & maturation', 4, 3, 4,
     20, 3, 8, 15, 15, 15, 15, 15, 15, 15, 1, 'broadcast',
     'K for fibre length + micronaire.'),
    ('Cotton', 'Defoliation & harvest', 5, 5, 6,
     5, 2, 2, 10, 10, 10, 10, 5, 10, 10, 0, 'broadcast',
     'No N. Harvest prep.');

-- Tobacco — K from SOP only (chloride-sensitive).
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Tobacco', 'Transplant & establishment', 1, 8, 9,
     30, 70, 50, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'CRITICAL: K from SOP only (chloride destroys leaf quality). 1000–1500 kg/ha 10:10:10.'),
    ('Tobacco', 'Vegetative (weeks 1–6)', 2, 10, 11,
     40, 15, 20, 25, 25, 25, 25, 25, 25, 25, 2, 'broadcast',
     'Ideal 100:50:100 NPK ratio.'),
    ('Tobacco', 'Topping / flowering', 3, 12, 12,
     20, 10, 20, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Topping redirects energy to leaves.'),
    ('Tobacco', 'Leaf maturation / harvest', 4, 1, 4,
     10, 5, 10, 15, 15, 15, 15, 15, 15, 15, 0, 'broadcast',
     'Reduce N for curing quality.');

-- Bean (Dry) — P-response strong.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Bean (Dry)', 'Planting & establishment', 1, 10, 11,
     30, 75, 65, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'P-response strong (20 kg P/ha → +143% grain yield). Inoculation + starter N 10–20 kg.'),
    ('Bean (Dry)', 'Vegetative', 2, 11, 12,
     25, 15, 20, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Standard growth.'),
    ('Bean (Dry)', 'Flowering & pod set', 3, 1, 1,
     25, 5, 10, 25, 25, 25, 25, 30, 25, 25, 1, 'broadcast',
     'Flower + pod set.'),
    ('Bean (Dry)', 'Pod fill & maturity', 4, 2, 3,
     20, 5, 5, 20, 20, 20, 20, 15, 20, 20, 0, 'broadcast',
     'Maturation.');

-- Bean (Green) — keep existing pattern (no SA source distinguishes)
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Bean (Green)', 'Emergence & establishment', 1, 8, 9,
     20, 35, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'No SA-specific split; generic international pattern.'),
    ('Bean (Green)', 'Vegetative growth', 2, 9, 10,
     30, 25, 25, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Canopy build.'),
    ('Bean (Green)', 'Flowering & pod set', 3, 10, 11,
     25, 20, 25, 25, 25, 25, 25, 30, 25, 25, 1, 'broadcast',
     'Pod set.'),
    ('Bean (Green)', 'Harvest', 4, 11, 2,
     25, 20, 35, 25, 25, 25, 25, 20, 25, 25, 1, 'broadcast',
     'Ongoing harvest.');

-- Pea — winter. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Pea', 'Planting & establishment', 1, 4, 5,
     50, 75, 60, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Legume but P high for nodulation. No SA-specific split; international pulse fallback.'),
    ('Pea', 'Vegetative', 2, 5, 6,
     25, 15, 20, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Canopy build.'),
    ('Pea', 'Flowering & pod set', 3, 7, 8,
     15, 5, 10, 25, 25, 25, 25, 30, 25, 25, 1, 'broadcast',
     'Pod set.'),
    ('Pea', 'Pod fill & harvest', 4, 9, 10,
     10, 5, 10, 25, 25, 25, 25, 15, 25, 25, 0, 'broadcast',
     'Maturation.');

-- Lucerne — perennial cut crop. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Lucerne', 'Establishment (pre-plant + seedling)', 1, 3, 4,
     30, 50, 30, 40, 30, 30, 30, 30, 30, 30, 1, 'band_place',
     'Pre-plant lime/P/K band. Small starter N until nodulation. ESTABLISHMENT YEAR ONLY.'),
    ('Lucerne', 'Spring regrowth (first cut)', 2, 9, 10,
     20, 15, 20, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'After each cut — 30–40 kg K₂O/ha top-dress.'),
    ('Lucerne', 'Summer cuts (peak production)', 3, 11, 2,
     30, 20, 30, 25, 25, 25, 25, 25, 25, 25, 3, 'broadcast',
     'K removal highest (30 kg K₂O/t DM).'),
    ('Lucerne', 'Autumn cuts', 4, 3, 5,
     15, 10, 15, 25, 25, 25, 25, 25, 25, 25, 2, 'broadcast',
     'Continued production.'),
    ('Lucerne', 'Winter dormancy / re-establishment P + K', 5, 6, 8,
     5, 5, 5, 15, 15, 15, 15, 15, 15, 15, 0, 'broadcast',
     'Perennial cut crop: stages apply per production year after establishment.');

-- Lentils — NEW CROP. Saskatchewan fallback. LOW-MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Lentils', 'Planting & establishment', 1, 5, 6,
     60, 80, 70, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Not commercial SA — Saskatchewan Pulse Growers protocol. Inoculation supplies ≥70% N.'),
    ('Lentils', 'Vegetative', 2, 7, 8,
     20, 10, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Standard pulse growth.'),
    ('Lentils', 'Bud formation / flowering', 3, 9, 9,
     15, 5, 10, 25, 25, 25, 25, 30, 25, 25, 1, 'broadcast',
     'In-season broadcast targeted for bud formation before flowering.'),
    ('Lentils', 'Pod fill & maturity', 4, 10, 11,
     5, 5, 5, 25, 25, 25, 25, 20, 25, 25, 0, 'broadcast',
     'Maturation.');


-- ─── VEGETABLES ────────────────────────────────────────────────────────

-- Potato — FERTASA Table 4 via NB Systems (sandy <10% clay default). HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Potato', 'Planting & emergence', 1, 8, 9,
     25, 100, 70, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'All P pre-plant. 70% K banded (sandy). Starter N. Heavy soils (>20% clay): shift N to 50/45/5/0.'),
    ('Potato', 'Vegetative growth', 2, 10, 11,
     30, 0, 0, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'N topdress pre-tuber-initiation.'),
    ('Potato', 'Tuber initiation & bulking', 3, 11, 12,
     30, 0, 30, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Peak K demand at bulking.'),
    ('Potato', 'Maturation', 4, 1, 1,
     15, 0, 0, 15, 15, 15, 15, 15, 15, 15, 0, 'broadcast',
     'Stop N ≥4 weeks before die-back.');

-- Sweet Potato — KZN DARD + SA extension.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Sweet Potato', 'Planting & establishment', 1, 10, 11,
     50, 100, 100, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'Basal 1000 kg/ha 2:3:4(30) pre-plant. High N:K maintained.'),
    ('Sweet Potato', 'Vine growth', 2, 12, 1,
     25, 0, 0, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'LAN 120–150 kg/ha at 3 weeks.'),
    ('Sweet Potato', 'Storage root initiation & bulking', 3, 2, 4,
     25, 0, 0, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'LAN repeat at 6 weeks. Critical 30–60 DAP window.'),
    ('Sweet Potato', 'Maturation & harvest', 4, 4, 6,
     0, 0, 0, 15, 15, 15, 15, 15, 15, 15, 0, 'broadcast',
     'No late feeding.');

-- Tomato — Starke Ayres Table 6 (indeterminate default). HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Tomato', 'Pre-plant + transplant (Wk 0–7)', 1, 9, 10,
     25, 57, 26, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Starke Ayres Table 6 (indeterminate). Basal 35+35 N, 50+18 P, 60+60 K.'),
    ('Tomato', 'Flowering to fruit set (Wk 7–13)', 2, 11, 12,
     25, 15, 24, 30, 25, 25, 25, 30, 25, 25, 2, 'fertigation',
     '70 N, 18 P, 110 K. B for set. Ca for BER.'),
    ('Tomato', 'Fruit fill & harvest (Wk 13–25)', 3, 1, 3,
     50, 28, 50, 45, 50, 50, 50, 45, 50, 50, 3, 'fertigation',
     '144 N, 33 P, 228 K — peak uptake.');

-- Pepper (Bell) — Starke Ayres + tomato analogue. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Pepper (Bell)', 'Transplant & establishment', 1, 9, 10,
     15, 50, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Very sensitive to seedling over-fertilisation.'),
    ('Pepper (Bell)', 'Vegetative growth', 2, 10, 11,
     25, 20, 15, 25, 25, 25, 25, 25, 25, 25, 1, 'fertigation',
     'Avoid excess N (flower drop).'),
    ('Pepper (Bell)', 'Flowering & fruit set', 3, 12, 1,
     25, 15, 25, 30, 25, 25, 25, 30, 25, 25, 2, 'fertigation',
     'Ca for BER (pepper more Ca-sensitive than tomato).'),
    ('Pepper (Bell)', 'Fruit fill & harvest', 4, 2, 4,
     35, 15, 45, 30, 30, 30, 30, 25, 30, 30, 2, 'fertigation',
     'Peak K for colour + firmness.');

-- Cabbage — ARC-VOPI. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Cabbage', 'Transplant & establishment', 1, 2, 3,
     37, 100, 100, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'Basal 600–900 kg 2:3:4(27) pre-plant.'),
    ('Cabbage', 'Vegetative frame', 2, 3, 4,
     21, 0, 0, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'LAN 4g/plant at 2 weeks.'),
    ('Cabbage', 'Head formation', 3, 4, 6,
     21, 0, 0, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'LAN 10g/plant at 4 weeks.'),
    ('Cabbage', 'Maturation & harvest', 4, 6, 7,
     21, 0, 0, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'Last top-dress. Stop to avoid splitting.');

-- Lettuce — Starke Ayres. HIGH. 3 stages.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Lettuce', 'Transplant & establishment', 1, 2, 3,
     34, 100, 100, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'Starke Ayres: 110 N, 14 P, 190 K total. All P + K pre-plant.'),
    ('Lettuce', 'Rapid leaf growth', 2, 3, 5,
     36, 0, 0, 30, 30, 30, 30, 30, 30, 30, 1, 'broadcast',
     'LAN topdress ~4 weeks.'),
    ('Lettuce', 'Head formation & harvest', 3, 5, 6,
     30, 0, 0, 30, 30, 30, 30, 30, 30, 30, 1, 'broadcast',
     'Final feed before cut.');

-- Spinach — Starke Ayres Swiss Chard. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Spinach', 'Sowing & establishment', 1, 3, 4,
     38, 100, 100, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     '500–1000 kg 2:3:4(30) basal.'),
    ('Spinach', 'Rapid leaf growth', 2, 4, 6,
     31, 0, 0, 30, 30, 30, 30, 30, 30, 30, 1, 'broadcast',
     '175–225 kg LAN at 4 weeks.'),
    ('Spinach', 'Harvest (multi-cut)', 3, 6, 8,
     31, 0, 0, 30, 30, 30, 30, 30, 30, 30, 1, 'broadcast',
     '175–225 kg LAN at 8 weeks.');

-- Onion — Starke Ayres. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Onion', 'Transplant & establishment', 1, 3, 4,
     33, 100, 65, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'Starke Ayres: 60 N + 100 P + 110 K pre-plant.'),
    ('Onion', 'Leaf growth (vegetative)', 2, 5, 7,
     67, 0, 0, 30, 30, 30, 30, 30, 30, 30, 2, 'broadcast',
     '60 kg N at 2-leaf + 60 kg N at 4 weeks.'),
    ('Onion', 'Bulb initiation & fill', 3, 8, 10,
     0, 0, 35, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     '60 kg K at 7–8 weeks before harvest.'),
    ('Onion', 'Maturation & harvest', 4, 10, 12,
     0, 0, 0, 10, 10, 10, 10, 10, 10, 10, 0, 'broadcast',
     'Excess late N → thick-necked bulbs. No water 3 weeks pre-harvest.');

-- Garlic — onion-analogue. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Garlic', 'Planting & rooting', 1, 3, 4,
     54, 60, 57, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'Pre-plant analogue to onion. No SA industry body publishes garlic-specific split.'),
    ('Garlic', 'Vegetative leaf growth', 2, 5, 7,
     46, 40, 43, 30, 30, 30, 30, 30, 30, 30, 2, 'broadcast',
     '500 kg 3:2:3 at 14–21 days + 275 kg 3:2:3 at 8 weeks.'),
    ('Garlic', 'Bulb initiation & fill', 3, 7, 9,
     0, 0, 0, 20, 20, 20, 20, 20, 20, 20, 0, 'broadcast',
     'No late N (delays bulbing).'),
    ('Garlic', 'Maturation', 4, 9, 10,
     0, 0, 0, 10, 10, 10, 10, 10, 10, 10, 0, 'broadcast',
     'Allow tops to dry.');

-- Carrot — ARC-VOPI + Starke Ayres. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Carrot', 'Germination & establishment', 1, 2, 3,
     54, 100, 100, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     '1000 kg 2:3:4(30) pre-plant.'),
    ('Carrot', 'Canopy development', 2, 3, 4,
     46, 0, 0, 30, 30, 30, 30, 30, 30, 30, 2, 'broadcast',
     '10g LAN/m row at 3 weeks + again at 6 weeks.'),
    ('Carrot', 'Root bulking', 3, 4, 6,
     0, 0, 0, 20, 20, 20, 20, 20, 20, 20, 0, 'broadcast',
     'No further feed.'),
    ('Carrot', 'Maturation', 4, 6, 7,
     0, 0, 0, 10, 10, 10, 10, 10, 10, 10, 0, 'broadcast',
     'Dry-down. No N (would cause cracking).');

-- Butternut — Starke Ayres. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Butternut', 'Establishment', 1, 10, 10,
     49, 100, 30, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'Starke Ayres. 50% N + all P + 30% K pre-plant.'),
    ('Butternut', 'Vine growth', 2, 11, 12,
     17, 0, 30, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'First topdress 3-week interval. K at 4 weeks.'),
    ('Butternut', 'Flowering & fruit set', 3, 1, 1,
     17, 0, 30, 20, 20, 20, 20, 30, 20, 20, 1, 'broadcast',
     'Second topdress. K at first flower.'),
    ('Butternut', 'Fruit fill & maturation', 4, 2, 4,
     17, 0, 10, 20, 20, 20, 20, 10, 20, 20, 1, 'broadcast',
     'Third topdress.');

-- Pumpkin — Same as butternut (Starke Ayres lumps squash). MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Pumpkin', 'Establishment', 1, 10, 10,
     49, 100, 30, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     'Starke Ayres Squash. 750–1000 kg 2:3:4 pre-plant.'),
    ('Pumpkin', 'Vine growth', 2, 11, 12,
     17, 0, 30, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'Top-dress.'),
    ('Pumpkin', 'Flowering & fruit set', 3, 1, 2,
     17, 0, 30, 20, 20, 20, 20, 30, 20, 20, 1, 'broadcast',
     'Top-dress + K.'),
    ('Pumpkin', 'Fruit fill & maturation', 4, 3, 5,
     17, 0, 10, 20, 20, 20, 20, 10, 20, 20, 1, 'broadcast',
     'Top-dress.');

-- Watermelon — Starke Ayres. HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Watermelon', 'Establishment', 1, 10, 10,
     30, 100, 30, 40, 40, 40, 40, 40, 40, 40, 1, 'band_place',
     '30% N + all P + 30% K pre-plant.'),
    ('Watermelon', 'Vine growth', 2, 11, 12,
     35, 0, 35, 25, 25, 25, 25, 25, 25, 25, 1, 'fertigation',
     'First side-dressing (N + K simultaneously, KNO₃).'),
    ('Watermelon', 'Flowering & fruit set', 3, 12, 1,
     35, 0, 35, 25, 25, 25, 25, 35, 25, 25, 1, 'fertigation',
     'Second side-dressing.'),
    ('Watermelon', 'Fruit fill & harvest', 4, 1, 3,
     0, 0, 0, 10, 10, 10, 10, 0, 10, 10, 0, 'broadcast',
     'Stop irrigation 7–10 days pre-harvest.');

-- Asparagus — NEW CROP. Perennial. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Asparagus', 'Dormancy & pre-spear', 1, 6, 7,
     0, 100, 10, 40, 40, 40, 40, 40, 40, 40, 1, 'broadcast',
     'NEW CROP. SA extension + AHDB UK fallback for fern-build. Winter rest. Year 1-2: NO harvest.'),
    ('Asparagus', 'Spear emergence & harvest', 2, 8, 10,
     30, 0, 30, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'LAN 1 week after harvest starts.'),
    ('Asparagus', 'Fern build (post-harvest recovery)', 3, 11, 12,
     50, 0, 40, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'LAN repeat 6–8 weeks post-harvest. Drives fern for next-season reserves.'),
    ('Asparagus', 'Fern maturation & senescence', 4, 1, 5,
     20, 0, 20, 10, 10, 10, 10, 10, 10, 10, 0, 'broadcast',
     'Reserve loading into crowns.');


-- ─── SPECIALTY PERENNIALS ──────────────────────────────────────────────

-- Sugarcane — SASRI + FAO. MEDIUM-HIGH on P front-loading.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Sugarcane', 'Planting & establishment (basal)', 1, 2, 4,
     15, 70, 30, 30, 30, 30, 30, 30, 30, 30, 1, 'band_place',
     'SASRI. Plant crop default. Basal P in furrow (Natal Midlands P fixation).'),
    ('Sugarcane', 'Tillering & canopy close (top-dress 1)', 2, 5, 7,
     50, 20, 40, 30, 30, 30, 30, 30, 30, 30, 1, 'broadcast',
     'Peak N demand. Meyer split framework.'),
    ('Sugarcane', 'Grand growth & stalk elongation (top-dress 2)', 3, 8, 11,
     30, 10, 25, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast',
     'Sustained N for stalk elongation. Cease N ~6 months before harvest.'),
    ('Sugarcane', 'Ripening & pre-harvest', 4, 12, 1,
     5, 0, 5, 15, 15, 15, 15, 15, 15, 15, 0, 'broadcast',
     'No late N — sucrose quality. RATOONS: no basal P, start at stage 2 equivalent.');

-- Olive — SA Olive + CDFA. MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Olive', 'Post-harvest recovery', 1, 6, 7,
     5, 20, 5, 15, 15, 15, 15, 15, 15, 15, 1, 'broadcast',
     'SA Olive + CDFA. Reserve rebuild after late-autumn harvest.'),
    ('Olive', 'Winter rest & flower differentiation', 2, 8, 9,
     10, 20, 10, 20, 20, 20, 20, 25, 20, 20, 1, 'broadcast',
     'Budbreak prep. B critical for flower differentiation.'),
    ('Olive', 'Bloom & fruit set (peak vegetative)', 3, 10, 11,
     40, 30, 20, 25, 25, 25, 25, 30, 25, 25, 2, 'fertigation',
     'SA Olive: weekly fertigation Oct–Feb. 40% annual N here (CDFA Italian trial).'),
    ('Olive', 'Pit hardening & oil accumulation', 4, 12, 2,
     30, 20, 40, 25, 25, 25, 25, 15, 25, 25, 2, 'fertigation',
     'K peaks Jul–Nov NH = Jan–Mar SA for oil loading.'),
    ('Olive', 'Fruit maturation & harvest', 5, 3, 5,
     15, 10, 25, 15, 15, 15, 15, 15, 15, 15, 1, 'fertigation',
     'Cease N end-March to avoid winter flushing.');

-- Banana — Haifa 35/40/25. HIGH. STAGES ARE MONTHS-FROM-SUCKER, NOT CALENDAR.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Banana', 'Vegetative growth (pre-flower differentiation)', 1, 1, 6,
     35, 35, 20, 30, 30, 30, 30, 30, 30, 30, 6, 'fertigation',
     'Haifa benchmark. Stages are MONTHS-FROM-SUCKER, not calendar months.'),
    ('Banana', 'Pre-flower emergence (flower diff → shooting)', 2, 7, 9,
     40, 40, 40, 30, 30, 30, 30, 30, 30, 30, 3, 'fertigation',
     'Haifa: 80% of total K applied before peak flowering.'),
    ('Banana', 'Bunch fill (post flower emergence)', 3, 10, 12,
     20, 20, 35, 25, 25, 25, 25, 25, 25, 25, 3, 'fertigation',
     'K tilted higher for finger fill.'),
    ('Banana', 'Bunch maturation & harvest', 4, 13, 14,
     5, 5, 5, 15, 15, 15, 15, 15, 15, 15, 1, 'fertigation',
     'Final fill; minimal top-ups.');

-- Pineapple — CTAHR + CIRAD. HIGH. STAGES ARE CYCLE MONTHS.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Pineapple', 'Planting & establishment (slips)', 1, 1, 3,
     10, 50, 10, 40, 25, 25, 25, 25, 25, 25, 1, 'band_place',
     'Stages are CYCLE MONTHS. Bathurst EC + KZN Hluhluwe. P front-loaded for slip rooting.'),
    ('Pineapple', 'Vegetative rosette (D-leaf production)', 2, 4, 12,
     55, 40, 55, 30, 30, 30, 30, 30, 30, 30, 8, 'fertigation',
     '14–16 months vegetative. 80% K before flower set. Cease N ~2 months before forcing.'),
    ('Pineapple', 'Forcing & flower development', 3, 13, 16,
     5, 5, 10, 15, 15, 15, 15, 25, 15, 15, 0, 'fertigation',
     'N MUST STOP 2 months before forcing. Ethephon/CaC₂ induction.'),
    ('Pineapple', 'Fruit development & harvest', 4, 17, 20,
     30, 5, 25, 15, 30, 30, 30, 35, 30, 30, 2, 'fertigation',
     'N resumes at moderate rate post-flowering.');

-- Coffee — Haifa Arabica (international fallback). MEDIUM-HIGH.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Coffee', 'Post-harvest & pruning recovery', 1, 8, 9,
     10, 10, 5, 15, 15, 15, 15, 15, 15, 15, 1, 'fertigation',
     'Haifa Arabica — SA crop ~150 ha, no public SA handbook.'),
    ('Coffee', 'Pre-flowering & bud swell', 2, 10, 10,
     10, 10, 10, 15, 15, 15, 15, 20, 15, 15, 1, 'fertigation',
     'Pre-flower 15-day window.'),
    ('Coffee', 'Flowering', 3, 11, 12,
     20, 25, 20, 25, 25, 25, 25, 35, 25, 25, 1, 'fertigation',
     'Haifa: 170 kg 23-7-23+ME over 30 days. B critical for fruit set.'),
    ('Coffee', 'Green berry expansion & fill', 4, 1, 4,
     45, 40, 55, 30, 30, 30, 30, 15, 30, 30, 2, 'fertigation',
     'Peak uptake. Haifa 550 kg 12-5-40+ME over 150 days.'),
    ('Coffee', 'Berry maturation & harvest', 5, 5, 7,
     15, 15, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'fertigation',
     'Haifa: 200 kg 12-5-40 over 60 days.');

-- Tea — Kenya Tea Board (SA defunct). MEDIUM.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Tea', 'Winter dry-period maintenance', 1, 5, 8,
     10, 40, 15, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'Kenya KALRO/Tea Board — SA industry effectively defunct.'),
    ('Tea', 'Spring flush (first flush)', 2, 9, 10,
     30, 20, 30, 30, 30, 30, 30, 30, 30, 30, 1, 'broadcast',
     'Pre-rain NPK broadcast.'),
    ('Tea', 'Main wet-season plucking', 3, 11, 2,
     45, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'broadcast',
     'N applied every 2–3 months during active plucking.'),
    ('Tea', 'Late-season tapering', 4, 3, 4,
     15, 15, 15, 20, 20, 20, 20, 20, 20, 20, 1, 'broadcast',
     'Autumn flush less productive.');

-- Rooibos — LEGUME. Synthetic N schedule is AGRONOMICALLY WRONG.
-- Current schema forces n_pct to sum to 100 — noted in notes column.
INSERT INTO crop_growth_stages
    (crop, stage_name, stage_order, month_start, month_end,
     n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
     num_applications, default_method, notes)
VALUES
    ('Rooibos', 'Pre-plant soil amendment', 1, 5, 7,
     0, 80, 20, 50, 40, 40, 40, 40, 40, 40, 1, 'broadcast',
     'ROOIBOS IS A LEGUME. No synthetic N recommended (SA Rooibos Council, Hawker 2023 Nature Sci-Rep). Atlantic Fertilisers uses rock phosphate (roots sensitive to high soluble P). P target Bray-II 15–25 ppm.'),
    ('Rooibos', 'Establishment year 1 (winter plant → spring flush)', 2, 8, 11,
     0, 10, 30, 25, 25, 25, 25, 25, 25, 25, 0, 'broadcast',
     'N-fixation handles N. Low-input maintenance only.'),
    ('Rooibos', 'Spring/summer growth (productive years 2-5)', 3, 12, 2,
     0, 5, 30, 15, 15, 15, 15, 15, 15, 15, 0, 'broadcast',
     'Legume N self-sufficient. Minor K for tea quality if soil-test deficient.'),
    ('Rooibos', 'Harvest & post-harvest', 4, 3, 4,
     0, 5, 20, 10, 15, 15, 15, 15, 15, 15, 0, 'broadcast',
     'Minimal post-harvest top-up.');

COMMIT;
