-- Migration 081: Last-mile data fill — Avocado + Citrus + Macadamia
--
-- Closes the residual gaps from migration 080 so all three Muller-demo
-- crops (Mac, Citrus, Avo) are complete to the limits of cited
-- published agronomy. Source-tier rules per feedback_fertasa_first.md.
--
-- ─── KEY NEW SOURCES (PDFs committed alongside this migration) ────────
--
-- FERTASA Handbook 5.8.1 "Macadamias" Table 5.8.1.1 (Hawksworth-Sheard
-- 2021 ed.) — the canonical SA macadamia 5-class leaf-norm grid.
-- Migration 043 seeded the sufficient_min/sufficient_max columns only;
-- this migration fills the deficient_max / low_max / high_min /
-- excess_min columns from the same table. PDF at
-- sapling-api/data/fertasa_handbook/5_8_1_macadamia_2021_table_5_8_1_1.pdf
--
-- Wolstenholme, B.N. (n.d.) "Importance of Soil Organic Matter in Soil
-- Health and Avocado Orchard Management" — SAAGA Subtrop publication,
-- consolidates Soil Classification Working Group 1991 + Dlamini, Haynes
-- & van Antwerpen 2001 Eshowe survey + Mexican-andosol baselines.
-- Provides the avocado-specific organic-C banding. PDF at
-- sapling-api/data/saaga/wolstenholme_som_avocado.pdf
--
-- Acosta-Rangel et al. 2018, "Salt Tolerance and Growth of 13 Avocado
-- Rootstocks Related Best to Chloride Uptake," HortScience 53(12):
-- 1737-1745, DOI 10.21273/HORTSCI13198-18 (T3 peer-reviewed).
-- Source for avocado Cl bands stratified by rootstock race
-- (Mexican / Guatemalan / West Indian) — consolidates Bernstein et al.
-- + Ayers & Westcot 1985 FAO I&D Paper 29.
--
-- UC ANR / California Avocado Commission "Salinity Management of
-- Avocados" — Oster et al. — source for avocado EC bands. T2.
--
-- UF/IFAS Citrus Production Guide CG091 (2025-26) Table 4 — explicitly
-- states "There is no established sufficiency value for soil organic
-- matter" for citrus. T2 — used as the negative-finding citation for
-- citrus organic-C (capture as documented gap, don't fabricate).
--
-- ─── HONEST NULLS (real outcomes, captured here for traceability) ────
--
-- 1. Avocado total-S / sulphate-S soil mg/kg — no SA or international
--    source publishes a crop-specific soil-S band for avocado. Generic
--    agronomy 12-25 mg/kg SO4-S applies but isn't avocado-specific.
--    Not seeded.
-- 2. Avocado Na soil mg/kg — rootstock-dependent; Mexican-race most
--    sensitive, West Indian most tolerant. Best handled via ESP/SAR
--    proxy, not a single Na-mg/kg band. Not seeded.
-- 3. Citrus organic carbon 5-class banding — UF/IFAS CG091 Table 4
--    explicit "no value." Florida observational ~1%, Midwest >5%,
--    informal 2% N-credit threshold are descriptive only, not
--    sufficiency thresholds. Not seeded.
-- 4. Macadamia Cl 5-class leaf — FERTASA 5.8.1 Table publishes only
--    the sufficient norm (0.03-0.05%); Cl is absent from the 5-class
--    grid. Excess >1.0% comes from Huett & Vimpany 2007 Aust J Exp Ag
--    47(7):869-876 (T3, paywalled — referenced by FERTASA).
-- 5. Macadamia Fe upper bands — FERTASA publishes only deficient (<25)
--    and sufficient (25-200). No high or excess; mac Fe-toxicity is
--    rare; deficiency is the clinical condition. Manson & Sheard 2007
--    notes Fe/Mn ratio <1.2 as the better deficiency indicator.
-- 6. Macadamia S, Cu, Zn, B excess columns — FERTASA publishes through
--    "high" but no separate excess column for these. In practice the
--    high threshold is the de-facto excess.
--
-- ─── NOTABLE CORRECTION ──────────────────────────────────────────────
--
-- Macadamia Na leaf row from migration 043 was seeded (sufficient_max
-- 0.02) per a SAMAC interpretation. The actual FERTASA 5.8.1 Table
-- 5.8.1.1 publishes a fuller band: sufficient ≤0.07%, high 0.08-0.10%,
-- range 0.2-0.3% high, >0.4% excess. This migration UPDATEs the row to
-- match the published table.
--
-- ─── ROW COUNT ───────────────────────────────────────────────────────
--   fertasa_soil_norms: +2 rows (avocado EC + Cl reference)
--   crop_sufficiency_overrides: +2 rows (avo OC + EC)
--   fertasa_leaf_norms: +12 mac rows UPDATEd (all elements except Cl
--                        which only has sufficient band published)
-- =====================================================================

BEGIN;

-- ─── fertasa_soil_norms (Avocado EC + Cl reference) ─────────────────

INSERT INTO fertasa_soil_norms (crop, parameter, ideal_value, ideal_min, ideal_max, unit, method, source_section, notes) VALUES
  ('Avocado', 'EC (saturated paste)', NULL, NULL, 0.4, 'dS/m', 'saturated paste',
   'UC ANR Salinity Management of Avocados (Oster)',
   'No-decline ceiling 0.4 dS/m on Mexican-race rootstocks; 1.4-1.5 dS/m field-tolerated by Hass on Duke-7 with yield decline. Avocado is salt-sensitive; FAO classifies as S (Sensitive). T2.'),
  ('Avocado', 'Cl (sat extract, Mexican rootstock)', NULL, NULL, 177, 'mg/L', '1:1 saturation extract',
   'Acosta-Rangel et al. 2018 HortScience 53(12):1737-1745',
   'Mexican-race rootstock max 5.0 mmol/L (≈177 mg/L). Most common rootstock in SA avo (Duke-7 etc. is Mexican-race). Guatemalan tolerates 6.0 mmol/L (≈213 mg/L); West Indian 7.5 mmol/L (≈266 mg/L). T3 peer-reviewed; consolidates Bernstein + Ayers & Westcot 1985 FAO I&D Paper 29.')
ON CONFLICT DO NOTHING;


-- ─── crop_sufficiency_overrides (Avocado OC + EC) ───────────────────

INSERT INTO crop_sufficiency_overrides (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes) VALUES
  ('Avocado', 'Organic C (Walkley-Black)', 0.8, 1.5, 3.0, 6.0,
   'Wolstenholme SAAGA Subtrop "SOM in Avocado Orchard Management" — consolidates Soil Classification Working Group 1991 + Dlamini, Haynes & van Antwerpen 2001 Eshowe survey + Mexican-andosol baselines (best avo soils 4-6% SOM). FERTASA mac chapter sets <1.5% as the "urgent intervention" threshold; same applies for tree-crop subtropicals by analogy. Method: Walkley-Black, top 30 cm. T1.'),
  ('Avocado', 'EC (saturated paste)', NULL, NULL, 0.4, 1.0,
   'UC ANR Oster + Steinhardt-Kalmar-Shalhevet Israeli field trial (T2+T3). Optimal ≤0.4 dS/m; 0.4-1.0 = moderate yield decline; >1.5 = >50% yield loss documented at Steinhardt orchard. Avocado FAO-classified S (Sensitive). Saturated-paste extract method.')
ON CONFLICT (crop, parameter) DO UPDATE
  SET very_low_max = EXCLUDED.very_low_max,
      low_max = EXCLUDED.low_max,
      optimal_max = EXCLUDED.optimal_max,
      high_max = EXCLUDED.high_max,
      notes = EXCLUDED.notes;


-- ─── fertasa_leaf_norms (Macadamia 5-class banding completion) ──────
--
-- Existing rows from migration 043 had only sufficient_min/sufficient_max
-- populated. UPDATE each to fill in the deficient_max / low_max /
-- high_min / excess_min columns from FERTASA 5.8.1 Table 5.8.1.1.
-- Cl row not updated (FERTASA publishes only the sufficient norm).
-- Where FERTASA does not publish a high or excess band, the column
-- stays NULL — see honest-NULL notes in the migration header.

-- Nitrogen
UPDATE fertasa_leaf_norms
SET deficient_max = 0.8, low_max = 1.19, sufficient_min = 1.2, sufficient_max = 1.59,
    high_min = 1.6, excess_min = 2.0,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1 (Hawksworth-Sheard 2021 ed.). N sufficient 1.2-1.59%, high 1.6-1.99%, excess ≥2.0%. T1.'
WHERE crop = 'Macadamia' AND element = 'N';

-- Phosphorus
UPDATE fertasa_leaf_norms
SET deficient_max = 0.05, low_max = 0.06, sufficient_min = 0.07, sufficient_max = 0.09,
    high_min = 0.10, excess_min = 0.16,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. Existing sufficient 0.08-0.10 from migration 043 was the older SAMAC interpretation; FERTASA Table 5.8.1.1 publishes 0.07-0.09 with high 0.10-0.15 and excess ≥0.16. T1.'
WHERE crop = 'Macadamia' AND element = 'P';

-- Potassium
UPDATE fertasa_leaf_norms
SET deficient_max = 0.34, low_max = 0.49, sufficient_min = 0.50, sufficient_max = 0.70,
    high_min = 0.71, excess_min = 1.21,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. K sufficient 0.50-0.70%, high 0.71-1.20%, excess ≥1.21%. Existing sufficient 0.6-0.7 from migration 043 narrows the K band; FERTASA Table 5.8.1.1 broadens it to 0.50-0.70. T1.'
WHERE crop = 'Macadamia' AND element = 'K';

-- Sulphur — FERTASA publishes through "high" only, no excess column
UPDATE fertasa_leaf_norms
SET deficient_max = 0.10, low_max = 0.19, sufficient_min = 0.20, sufficient_max = 0.30,
    high_min = 0.31, excess_min = NULL,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. S sufficient 0.20-0.30%, high ≥0.31%. FERTASA does not publish an S excess band; high serves as de-facto excess. T1.'
WHERE crop = 'Macadamia' AND element = 'S';

-- Calcium
UPDATE fertasa_leaf_norms
SET deficient_max = 0.3, low_max = 0.5, sufficient_min = 0.6, sufficient_max = 0.9,
    high_min = 1.0, excess_min = 1.2,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. Ca sufficient 0.6-0.9%, high 1.0-1.1%, excess ≥1.2%. T1.'
WHERE crop = 'Macadamia' AND element = 'Ca';

-- Magnesium
UPDATE fertasa_leaf_norms
SET deficient_max = 0.05, low_max = 0.08, sufficient_min = 0.09, sufficient_max = 0.11,
    high_min = 0.12, excess_min = 0.21,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. Mg sufficient 0.09-0.11%, high 0.12-0.20%, excess ≥0.21%. Existing sufficient 0.08-0.10 from migration 043 narrowly differs; FERTASA Table publishes 0.09-0.11. T1.'
WHERE crop = 'Macadamia' AND element = 'Mg';

-- Zinc — FERTASA publishes through "high" only
UPDATE fertasa_leaf_norms
SET deficient_max = 9, low_max = 14, sufficient_min = 15, sufficient_max = 50,
    high_min = 51, excess_min = NULL,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. Zn sufficient 15-50 mg/kg, high ≥51 mg/kg. FERTASA does not publish a Zn excess band; high serves as de-facto excess. T1.'
WHERE crop = 'Macadamia' AND element = 'Zn';

-- Manganese
UPDATE fertasa_leaf_norms
SET deficient_max = 20, low_max = 149, sufficient_min = 150, sufficient_max = 1000,
    high_min = 1600, excess_min = 3600,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. Mn sufficient 150-1000 mg/kg, high 1600-3000, excess ≥3600 (excessive 3600-5500). Cross-validated by CTAHR Hue/Fox/McCall 1987: macadamia tolerates ≤1000 mg/kg leaf Mn without adverse effects, so high-min 1600 is conservative and biologically defensible. T1+T2.'
WHERE crop = 'Macadamia' AND element = 'Mn';

-- Iron — FERTASA only publishes deficient (<25) and sufficient (25-200)
UPDATE fertasa_leaf_norms
SET deficient_max = 25, low_max = NULL, sufficient_min = 25, sufficient_max = 200,
    high_min = NULL, excess_min = NULL,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1 publishes only deficient (<25) and sufficient (25-200) for Fe; no high or excess band. Mac Fe-toxicity is rare; Fe-deficiency is the clinical condition. Manson & Sheard 2007 KZN paper recommends Fe/Mn ratio <1.2 as the better deficiency indicator than Fe alone. T1.'
WHERE crop = 'Macadamia' AND element = 'Fe';

-- Copper — FERTASA publishes through "high" with high_max 70
UPDATE fertasa_leaf_norms
SET deficient_max = 3, low_max = 4, sufficient_min = 5, sufficient_max = 12,
    high_min = 20, excess_min = NULL,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. Cu sufficient 5-12 mg/kg (existing migration-043 row was 5-10, slightly narrow), high 20-70. FERTASA does not publish a Cu excess band beyond high; >70 mg/kg de-facto excess. T1.'
WHERE crop = 'Macadamia' AND element = 'Cu';

-- Boron — FERTASA publishes through "high" only
UPDATE fertasa_leaf_norms
SET deficient_max = 12, low_max = 49, sufficient_min = 50, sufficient_max = 90,
    high_min = 91, excess_min = NULL,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. B sufficient 50-90 mg/kg (existing migration-043 row was 40-75, narrower band), high ≥91. FERTASA does not publish a B excess band; high serves as de-facto excess. Manson & Sheard 2007 KZN paper: low leaf B widespread in KZN, B deficiency probably common. T1.'
WHERE crop = 'Macadamia' AND element = 'B';

-- Sodium — full FERTASA Table 5.8.1.1 band correcting the migration-043
-- placeholder of sufficient_max 0.02
UPDATE fertasa_leaf_norms
SET deficient_max = NULL, low_max = NULL, sufficient_min = NULL, sufficient_max = 0.07,
    high_min = 0.08, excess_min = 0.21,
    notes = 'FERTASA 5.8.1 Table 5.8.1.1. Na has no biological deficient state for mac; sufficient ≤0.07%, high 0.08-0.10%, range 0.2-0.3% high, >0.4% excess. Migration 043 originally seeded sufficient_max=0.02 per an older SAMAC interpretation; this row updates to the FERTASA published table. T1.'
WHERE crop = 'Macadamia' AND element = 'Na';

COMMIT;
