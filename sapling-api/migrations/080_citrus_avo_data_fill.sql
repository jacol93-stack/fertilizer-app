-- Migration 080: Citrus + Avocado data fill
--
-- Closes the data gaps identified in the live coverage audit
-- (2026-04-25 session) so the Muller demo doesn't render under
-- "Data Confidence: minimum" for the citrus and avocado crops.
--
-- Source-tier rules (per the relaxed-FERTASA feedback memo —
-- feedback_fertasa_first.md):
--   T1 = SA Tier 1 — FERTASA / SAMAC / SASRI / CRI / Citrus Academy /
--        SAAGA / NZAGA / ARC / DALRRD / Hortgro / GrainSA
--   T2 = international parallel (IPNI / Yara / Haifa / CABI / UC ANR /
--        UF/IFAS / Cornell / WSU / FAO / IFA)
--   T3 = peer-reviewed paper (SAJEV / SAJPS / HortScience / etc.)
--
-- ─── KEY SOURCES USED ────────────────────────────────────────────────
--
-- AVOCADO:
--   Köhne, J.S., Kremer-Köhne, S., Wolstenholme, B.N. (1990). "Soil and
--   leaf analytical norms for South African avocado orchards."
--   South African Avocado Growers' Association Yearbook 13: 8-10.
--   Table 2 is the canonical SA avocado soil + leaf norms reference,
--   cited by FERTASA 5.7.1.1. OCR'd transcript at /tmp/saaga_1990_8-10.pdf;
--   recommend committing to sapling-api/data/saaga/kohne_1990_soil_leaf_norms.txt
--   as the SA avocado norm reference.
--
--   Du Plessis, M.H. & Koen, T.J. (1992). "Leaf analysis norms for the
--   Fuerte avocado." Proc. World Avocado Congress II (WAC2): 289-299.
--   Table 4 — refines Köhne 1990 N/P/K bands for Fuerte specifically.
--   T3 peer-reviewed.
--
--   FERTASA Handbook 5.7.1 "Avocados" — pH 6.0 target, P-Bray-1 25 mg/kg
--   target, Cl-sensitivity prose ("susceptible to leaf scorch caused by
--   excessive chloride").
--
-- CITRUS:
--   Citrus Academy NQ2 Learner Guide §3.1 (pH), §3.4 (Fertility Level
--   p.29). Public, T1 SA. Most norms expressed as % base saturation,
--   which is structurally a poor fit for the existing schema's mg/kg
--   parameter set — those rows are deferred (see "Schema gaps" below).
--
--   UC Davis Geisseler Lab — Citrus Fertilization Guidelines, Soil
--   Test Ranges table. T2, used for mg/kg P and K bands citrus where
--   Citrus Academy publishes only base-saturation %.
--
--   UF/IFAS Citrus Production Guide CG091 (2025-26 edition), Table 1
--   leaf nutrient bands + salinity threshold. T2 international parallel
--   used for chloride toxicity and EC bands.
--
--   FERTASA 5.3.2 — existing Valencia leaf bands seeded in migration 043.
--   Source explicitly notes "shared across citrus varieties." Cloned to
--   Navel/Lemon/Grapefruit/Soft Citrus for the Ca/Mg/S/B/Zn/Mn/Fe/Cu/Mo
--   elements where no SA source publishes variant-specific values.
--
-- ─── SCHEMA GAPS NOTED FOR POST-DEMO ─────────────────────────────────
--
-- 1. Citrus K/Ca/Mg base-saturation values from Citrus Academy NQ2
--    (Ca 70-80% BS, Mg 20-25% BS, K 5-7.5% BS) are citrus-specific
--    overrides of FERTASA's global ideal_ratios bands (60-70 / 12-18 /
--    3-5). The current schema has no per-crop column on ideal_ratios.
--    Defer until Phase C — either add `crop` column to ideal_ratios
--    or extend crop_sufficiency_overrides with a base-saturation type.
--
-- 2. Avocado organic carbon, total-S, and Na-soil thresholds — no SA
--    source publishes a defensible numeric. Left NULL.
--
-- 3. Citrus organic carbon — no SA-specific number found. Left NULL.
--
-- 4. The "Manson & Sheard 2007 SAJEV citrus" reference in the existing
--    tests/fixtures/FERTASA_CROSSCHECK.md appears to be misattributed —
--    the publicly-accessible 2007 paper is the Macadamia Fertilization
--    in KwaZulu-Natal one, not citrus. Flag for the next FERTASA cross-
--    check pass.
--
-- ─── ROW COUNT SUMMARY ───────────────────────────────────────────────
--   fertasa_soil_norms: +9 rows (5 avo, 3 citrus, 1 alt method)
--   crop_sufficiency_overrides: +13 rows (6 avo, 7 citrus)
--   fertasa_leaf_norms: +36 rows (4 citrus variants × 9 elements cloned
--                                  from Valencia)
-- =====================================================================

BEGIN;

-- ─── fertasa_soil_norms ──────────────────────────────────────────────

-- Avocado: extend the existing P-Bray-1 + pH rows with K, Ca, Mg
-- (Köhne 1990 SAAGA Yearbook 13 Table 2). The existing FERTASA 5.7.1
-- point-targets stay; Köhne adds the published bands.
INSERT INTO fertasa_soil_norms (crop, parameter, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Avocado', 'K (exchangeable)', 150, 250, 'mg/kg', 'ammonium acetate',
   'Köhne 1990 SAAGA YB 13 Table 2',
   'Optimum 150-250 mg/kg; Du Plessis & Koen 1992 WAC2 Friedenheim trial showed adequate yield down to 60 mg/kg, treat as critical not target. T1+T3.'),
  ('Avocado', 'Ca (exchangeable)', 750, 1000, 'mg/kg', 'ammonium acetate',
   'Köhne 1990 SAAGA YB 13 Table 2',
   'Optimum 750-1000 mg/kg; high/excess columns left null per Köhne 1990 convention. T1.'),
  ('Avocado', 'Mg (exchangeable)', 100, 300, 'mg/kg', 'ammonium acetate',
   'Köhne 1990 SAAGA YB 13 Table 2',
   'Optimum 100-300 mg/kg. T1.'),
  ('Avocado', 'P (Hars resin)', 8, 27, 'mg/kg', 'Hars (resin)',
   'Köhne 1990 SAAGA YB 13 Table 2',
   'Hot-water resin extraction alternative to Bray-1. Optimum 8-27 mg/kg. T1.'),
  ('Avocado', 'clay content', 20, 40, '%', 'texture',
   'Köhne 1990 SAAGA YB 13 (Site Selection)',
   'Köhne citing Nel 1983: avocado prefers loam soils 20-40% clay. T1.')
ON CONFLICT DO NOTHING;

-- Citrus: previously zero rows in fertasa_soil_norms. Seed mg/kg-native
-- values from Citrus Academy NQ2 + UC Davis Geisseler. Base-saturation
-- values deferred (schema gap noted above).
INSERT INTO fertasa_soil_norms (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Citrus', 'pH (H2O)', NULL, 6.5, 7.5, '-', '1:2.5 H2O',
   'Citrus Academy NQ2 §3.1 p.28',
   'Optimum 6.5-7.5; below 5.3 Al-toxic; above 7.5 P/Zn/Mn lock-up. T1.'),
  ('Citrus', 'P (Bray-1)', NULL, 25, 50, 'mg/kg', 'Bray 1',
   'Citrus Academy NQ2 §3.4 p.29',
   'Optimum 25-50 mg/kg Bray-1. UC Davis Geisseler T2 cross-check uses 20-40 medium / 40-100 high. T1.'),
  ('Citrus', 'K (exchangeable)', NULL, 150, 250, 'mg/kg', 'ammonium acetate',
   'UC Davis Geisseler Citrus Fertilization Guidelines',
   'Optimum 150-250 mg/kg, very-low <75, low 75-150, high 250-800, excess >800. T2 (no SA mg/kg source — Citrus Academy publishes K as %BS only).'),
  ('Citrus', 'EC (saturated paste)', NULL, NULL, 1.7, 'dS/m', 'saturated paste',
   'UF/IFAS CG091 (2025-26)',
   'Citrus moderately salinity-sensitive. Threshold 1.7 dS/m above which yield declines ~16% per dS/m. Valencia rootzone tolerance ~2.5-3.0 dS/m. T2.')
ON CONFLICT DO NOTHING;


-- ─── crop_sufficiency_overrides ──────────────────────────────────────

-- Avocado bands — Köhne 1990 SAAGA Yearbook 13 Table 2 published full
-- 5-class banding. Seed all 6 macros + Cl-leaf for the Cl-sensitivity
-- workflow (avocado Cl toxicity).
INSERT INTO crop_sufficiency_overrides (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes) VALUES
  ('Avocado', 'P (Bray-1)', 20, 29, 90, 129,
   'Köhne 1990 SAAGA YB 13 Table 2 (T1). FERTASA 5.7.1 prose target ~25 mg/kg sits in the same Optimal band.'),
  ('Avocado', 'K (exchangeable)', 100, 149, 250, 499,
   'Köhne 1990 SAAGA YB 13 Table 2 (T1). Du Plessis & Koen 1992 WAC2 showed 60 mg/kg sufficient at high-yielding Friedenheim trial — treat as agronomic critical, not target. T1+T3.'),
  ('Avocado', 'Ca (exchangeable)', 250, 749, 1000, NULL,
   'Köhne 1990 SAAGA YB 13 Table 2 (T1). High/excess columns NULL per SAAGA convention.'),
  ('Avocado', 'Mg (exchangeable)', 50, 99, 300, NULL,
   'Köhne 1990 SAAGA YB 13 Table 2 (T1). High/excess columns NULL per SAAGA convention.'),
  ('Avocado', 'pH (H2O)', 4.5, 5.4, 6.5, 7.5,
   'Köhne 1990 SAAGA YB 13 Table 2 (T1). FERTASA 5.7.1 target 6.0 sits in the Optimal band. Du Plessis & Koen 1992 trial baseline 6.15.'),
  ('Avocado', 'Cl (leaf)', NULL, NULL, 0.23, 0.25,
   'Köhne 1990 SAAGA YB 13 Table 2 (T1) — leaf Cl normal 0.07-0.23%, excess >=0.25%. Avocado Cl-sensitive; FERTASA 5.7.1 explicitly recommends SOP not KCl.')
ON CONFLICT (crop, parameter) DO UPDATE
  SET very_low_max = EXCLUDED.very_low_max,
      low_max = EXCLUDED.low_max,
      optimal_max = EXCLUDED.optimal_max,
      high_max = EXCLUDED.high_max,
      notes = EXCLUDED.notes;

-- Citrus bands — primary T1 source is Citrus Academy NQ2 §3.4 p.29 for
-- pH; P band cross-validates Citrus Academy + UC Davis Geisseler. K
-- band is UC Davis only (T2) since Citrus Academy K is %BS not mg/kg.
-- Cl + EC are UF/IFAS T2 — citrus salinity workflow.
INSERT INTO crop_sufficiency_overrides (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes) VALUES
  ('Citrus', 'P (Bray-1)', 20, 24, 50, 100,
   'Citrus Academy NQ2 §3.4 p.29 (T1) ideal 25-50; UC Davis Geisseler (T2) cross-check 20-40 medium / 40-100 high. Bray-1 method.'),
  ('Citrus', 'K (exchangeable)', 75, 150, 250, 800,
   'UC Davis Geisseler Citrus Fertilization Guidelines (T2). Citrus Academy NQ2 publishes K only as %BS — schema gap noted in migration header.'),
  ('Citrus', 'pH (H2O)', 5.3, 6.4, 7.5, 8.0,
   'Citrus Academy NQ2 §3.1 p.28 (T1). Below 5.3 Al-toxic; above 7.5 P/Zn/Mn lock-up.'),
  ('Citrus', 'Cl (leaf)', NULL, NULL, 0.7, 1.0,
   'UF/IFAS CG091 leaf table (T2). Optimum <0.7%; toxicity >1.0% causes leaf burn/defoliation. Storey & Walker 1999 SAJPS — Cl-not-Na is the primary citrus salinity injury (T3 cross-validation).'),
  ('Citrus', 'Na (leaf)', NULL, NULL, 0.15, 0.25,
   'UF/IFAS CG091 leaf table (T2). High Na 0.15-0.25%; excess >0.25%.'),
  ('Citrus', 'EC (saturated paste)', NULL, NULL, 1.7, 3.0,
   'UF/IFAS CG091 (T2) — citrus moderately sensitive. Threshold 1.7 dS/m, ~16% yield decline per dS/m beyond. Valencia rootzone tolerance ~2.5-3.0 dS/m.')
ON CONFLICT (crop, parameter) DO UPDATE
  SET very_low_max = EXCLUDED.very_low_max,
      low_max = EXCLUDED.low_max,
      optimal_max = EXCLUDED.optimal_max,
      high_max = EXCLUDED.high_max,
      notes = EXCLUDED.notes;


-- ─── fertasa_leaf_norms — citrus variant clones ──────────────────────
--
-- FERTASA 5.3.2 publishes one shared micronutrient table across all
-- citrus varieties. UF/IFAS CG091 does the same. Migration 043 seeded
-- Valencia's full Ca/Mg/S/B/Zn/Mn/Fe/Cu/Mo bands; this clones them to
-- Navel, Lemon, Grapefruit, Soft Citrus. The notes field calls out
-- the cloned status so the renderer can attribute correctly.
--
-- Numeric values mirror the existing Valencia rows (queried 2026-04-25
-- from the live `fertasa_leaf_norms` table).

INSERT INTO fertasa_leaf_norms (crop, element, unit, deficient_max, low_max, sufficient_min, sufficient_max, high_min, excess_min, sample_part, sample_timing, source_section, notes) VALUES
  -- Navel
  ('Citrus (Navel)', 'Ca', '%', 2.50, 3.49, 3.50, 6.00, 6.10, 7.01, '4-7 mo leaf', 'Mar-May', '5.3.2',
   'Cloned from FERTASA 5.3.2 Valencia bands; FERTASA 5.3.2 explicitly shares micronutrient norms across citrus varieties. T1.'),
  ('Citrus (Navel)', 'Mg', '%', 0.25, 0.34, 0.35, 0.50, 0.51, 0.76, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Navel)', 'S', '%', 0.14, 0.19, 0.20, 0.30, 0.31, 0.51, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Navel)', 'B', 'mg/kg', 40, 74, 75, 200, 201, 301, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Navel)', 'Zn', 'mg/kg', 15, 24, 25, 100, 101, 201, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Navel)', 'Mn', 'mg/kg', 25, 39, 40, 150, 151, 301, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Navel)', 'Cu', 'mg/kg', 3, NULL, 5, 20, 21, 41, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Navel)', 'Fe', 'mg/kg', NULL, 49, 50, 300, NULL, NULL, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Navel)', 'Mo', 'mg/kg', 0.03, 0.04, 0.05, 3.00, NULL, NULL, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  -- Lemon
  ('Citrus (Lemon)', 'Ca', '%', 2.50, 3.49, 3.50, 6.00, 6.10, 7.01, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Lemon)', 'Mg', '%', 0.25, 0.34, 0.35, 0.50, 0.51, 0.76, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Lemon)', 'S', '%', 0.14, 0.19, 0.20, 0.30, 0.31, 0.51, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Lemon)', 'B', 'mg/kg', 40, 74, 75, 200, 201, 301, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Lemon)', 'Zn', 'mg/kg', 15, 24, 25, 100, 101, 201, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Lemon)', 'Mn', 'mg/kg', 25, 39, 40, 150, 151, 301, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Lemon)', 'Cu', 'mg/kg', 3, NULL, 5, 20, 21, 41, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Lemon)', 'Fe', 'mg/kg', NULL, 49, 50, 300, NULL, NULL, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Lemon)', 'Mo', 'mg/kg', 0.03, 0.04, 0.05, 3.00, NULL, NULL, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  -- Grapefruit
  ('Citrus (Grapefruit)', 'Ca', '%', 2.50, 3.49, 3.50, 6.00, 6.10, 7.01, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Grapefruit)', 'Mg', '%', 0.25, 0.34, 0.35, 0.50, 0.51, 0.76, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Grapefruit)', 'S', '%', 0.14, 0.19, 0.20, 0.30, 0.31, 0.51, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Grapefruit)', 'B', 'mg/kg', 40, 74, 75, 200, 201, 301, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Grapefruit)', 'Zn', 'mg/kg', 15, 24, 25, 100, 101, 201, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Grapefruit)', 'Mn', 'mg/kg', 25, 39, 40, 150, 151, 301, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Grapefruit)', 'Cu', 'mg/kg', 3, NULL, 5, 20, 21, 41, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Grapefruit)', 'Fe', 'mg/kg', NULL, 49, 50, 300, NULL, NULL, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Grapefruit)', 'Mo', 'mg/kg', 0.03, 0.04, 0.05, 3.00, NULL, NULL, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  -- Soft Citrus
  ('Citrus (Soft Citrus)', 'Ca', '%', 2.50, 3.49, 3.50, 6.00, 6.10, 7.01, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Soft Citrus)', 'Mg', '%', 0.25, 0.34, 0.35, 0.50, 0.51, 0.76, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Soft Citrus)', 'S', '%', 0.14, 0.19, 0.20, 0.30, 0.31, 0.51, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Soft Citrus)', 'B', 'mg/kg', 40, 74, 75, 200, 201, 301, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Soft Citrus)', 'Zn', 'mg/kg', 15, 24, 25, 100, 101, 201, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Soft Citrus)', 'Mn', 'mg/kg', 25, 39, 40, 150, 151, 301, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Soft Citrus)', 'Cu', 'mg/kg', 3, NULL, 5, 20, 21, 41, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Soft Citrus)', 'Fe', 'mg/kg', NULL, 49, 50, 300, NULL, NULL, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.'),
  ('Citrus (Soft Citrus)', 'Mo', 'mg/kg', 0.03, 0.04, 0.05, 3.00, NULL, NULL, '4-7 mo leaf', 'Mar-May', '5.3.2', 'Cloned from FERTASA 5.3.2 Valencia. T1.')
ON CONFLICT DO NOTHING;

COMMIT;
