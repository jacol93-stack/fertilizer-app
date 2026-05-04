-- ============================================================
-- 108: Macadamia data fill — soil bands + age-factor recalibration
--      + per-ton micro-element corrections + Schoeman trace removal
-- ============================================================
-- Sources (T1 throughout):
--   * FERTASA (2017 rev) chapter 5.8.1 Macadamias — Mark Hawksworth /
--     Sheard ADM edits, October 2021 PDF
--   * Schoeman 2017 SAMAC FERTASA Symposium "Macadamia Nutrition" deck
--   * Manson & Sheard 2007 — Macadamia Fertilization in KZN (Cedara)
--
-- Critical corrections:
--   1. Mn per-ton-DNIS in crop_requirements: 0.15 → 0.75 (Schoeman 2017
--      kg/4t-DIS slide). Engine was under-applying Mn 5× for every Mac
--      block.
--   2. perennial_age_factors recalibrated per Manson & Sheard 2007 Table 6
--      per-tree N/K data — Y1 was 0.20 (engine), should be ~0.14 → 43%
--      over-application on year-1 trees.
--   3. Trace elements B/Zn/Cu/Fe/Mn raised to Schoeman 2017 mid-band
--      values (was sub-FERTASA on every micro).
--
-- Additions:
--   * 12 cited soil-sufficiency bands (pH KCl/H2O, Org C, P-Bray-1/Bray-2/
--     Ambic/Resin, Ca, Mg, S, Acid Saturation, Ca:Mg ratio).
--   * fertasa_nutrient_removal trace-element row from Schoeman 2017.
--
-- Conflicts kept on existing rows (NOT overridden):
--   * K — existing Schoeman young-tree deck (85/145) more SA-recent than
--     FERTASA 5.8.1 (80/150).
--   * N (mineral) — existing Schoeman (6/15) tighter than FERTASA (15/25)
--     and matches young-tree deck targeting.
--
-- Genuine gaps (no source found) — flagged in CROP_DATA_COVERAGE.md:
--   * Mo (soil + leaf + removal)
--   * Cu / Fe / Mn soil bands (FERTASA narrative-only)
--   * P / K very-high toxicity cut-offs (partial — FERTASA narrative)
-- ============================================================

BEGIN;

-- ── 1. crop_requirements micro-element corrections ─────────────
UPDATE public.crop_requirements
   SET b = 0.35,
       zn = 0.35,
       cu = 0.065,
       fe = 0.75,
       mn = 0.75
 WHERE crop = 'Macadamia';

-- ── 2. crop_sufficiency_overrides — 12 cited soil bands ────────
INSERT INTO public.crop_sufficiency_overrides
    (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Macadamia', 'pH (KCl)', 4.0, 4.5, 5.5, 6.0,
     'FERTASA 5.8.1 (2017 rev) Table 5.8.1.2: target 4.5-5.5. T1.'),
    ('Macadamia', 'pH (H2O)', 5.0, 5.5, 6.5, 7.0,
     'FERTASA 5.8.1 (2017 rev) Table 5.8.1.2 + ARC-ITSC: at least 5.5-6.5. T1.'),
    ('Macadamia', 'Org C', 0.8, 1.5, 4.0, NULL,
     'FERTASA 5.8.1 p.406: <1.5% urgent intervention; 4% ideal. Manson & Sheard 2007 Table 8: 2-6% range. T1.'),
    ('Macadamia', 'P (Bray-1)', 10, 20, 30, 50,
     'FERTASA 5.8.1: target 30 mg/kg; >50 mg/kg detrimental (depresses Fe/Zn). Farmers Weekly expert review confirms ceiling. T1.'),
    ('Macadamia', 'P (Bray-2)', NULL, 20, 80, NULL,
     'FERTASA 5.8.1 Table 5.8.1.2: Bray-2 = 20-80 mg/kg sufficient. T1.'),
    ('Macadamia', 'P (Ambic)', 8, 14, 34, 50,
     'FERTASA 5.8.1 Table 5.8.1.2 + Manson & Sheard 2007 Table 8: Ambic 14-34 mg/kg. T1.'),
    ('Macadamia', 'P (Olsen)', NULL, 10, 20, NULL,
     'FERTASA 5.8.1 Table 5.8.1.2: Resin/Olsen-P = 10-20 mg/kg sufficient. T1. (Engine canonical key for Resin = Olsen.)'),
    ('Macadamia', 'Ca', 250, 400, 1000, 1500,
     'FERTASA 5.8.1 Table 5.8.1.2: 400-1000 sufficient, 1500 = 7.5% of Total CEC threshold. Manson & Sheard 600-1500 mg/L. T1.'),
    ('Macadamia', 'Mg', 60, 100, 200, 210,
     'FERTASA 5.8.1 Table 5.8.1.2: 100-200 sufficient, 210 = 15% of Total CEC threshold. Manson & Sheard corrective formula triggers <100 mg/L. T1.'),
    ('Macadamia', 'S', NULL, 10, 20, NULL,
     'FERTASA 5.8.1 Table 5.8.1.2: sulphate-S phosphate extraction = 20 mg/kg sufficient. T1.'),
    ('Macadamia', 'Acid Saturation', NULL, 1, 5, NULL,
     'FERTASA 5.8.1 Table 5.8.1.2: 0-1% ideal; acceptable up to 5%. Manson & Sheard "1% or less before establishment". T1.'),
    ('Macadamia', 'Ca:Mg', NULL, 2.5, 5.4, NULL,
     'Manson & Sheard 2007 Cedara Table 8: Ca/Mg 2.5-5.4 ratio band. FERTASA 5.8.1 p.409 references the principle. T1.')
ON CONFLICT (crop, parameter) DO UPDATE
    SET very_low_max = EXCLUDED.very_low_max,
        low_max = EXCLUDED.low_max,
        optimal_max = EXCLUDED.optimal_max,
        high_max = EXCLUDED.high_max,
        notes = EXCLUDED.notes;

-- ── 3. perennial_age_factors — recalibrate per Manson & Sheard 2007 Table 6
DELETE FROM public.perennial_age_factors WHERE crop = 'Macadamia';

INSERT INTO public.perennial_age_factors
    (crop, age_label, age_min, age_max, general_factor, n_factor, p_factor, k_factor, notes)
VALUES
    ('Macadamia', 'Year 1', 0, 1, 0.15, 0.14, 0.15, 0.13,
     'Manson & Sheard 2007 Table 6: 50 g N/tree vs mature 360 g = 0.14. Lower than engine''s prior 0.20 (over-applied 43%). T1.'),
    ('Macadamia', 'Year 2', 2, 2, 0.25, 0.22, 0.25, 0.40,
     'Manson & Sheard 2007 Table 6: 80 g N/tree = 0.22 ratio; K jumps to 0.40 at year 2 (canopy K demand ramps fast). T1.'),
    ('Macadamia', 'Year 3-5', 3, 5, 0.40, 0.36, 0.40, 0.59,
     'Manson & Sheard 2007 Table 6: 130 g N/tree mid-band = 0.36; 220 g K/tree = 0.59. T1.'),
    ('Macadamia', 'Year 6-8', 6, 8, 0.60, 0.58, 0.60, 0.75,
     'Manson & Sheard 2007 Table 6: 210 g N/tree = 0.58; 280 g K/tree = 0.75. T1.'),
    ('Macadamia', 'Year 9+', 9, 99, 1.00, 1.00, 1.00, 1.00,
     'Manson & Sheard 2007 Table 6: full bearing; 360 g N/tree, 375 g K/tree. T1.');

-- ── 4. fertasa_nutrient_removal — Schoeman trace-element row ───
INSERT INTO public.fertasa_nutrient_removal
    (crop, plant_part, yield_unit, b, zn, fe, mn, cu, mo, source_section, notes)
VALUES
    ('Macadamia', 'total trace (nuts+husks)', 'kg/t DNIS',
     0.5, 0.5, 1.0, 1.0, 0.075, NULL,
     'Schoeman 2017 SAMAC FERTASA Symposium',
     'Schoeman 2017 "Kg/4 ton DIS" slide trace fraction divided by 4: B 0.5, Zn 0.5, Fe 1.0, Mn 1.0, Cu 0.075 kg/t DNIS. Mo not published. T1.');

COMMIT;
