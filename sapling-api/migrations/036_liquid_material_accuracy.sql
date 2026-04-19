-- ============================================================
-- Migration 036: Liquid raw material accuracy pass
--
-- A verification round against authoritative sources (PubChem, Wikipedia
-- solubility tables, Haifa/Mosaic/Yara/BASF/ICSC TDS) caught two classes
-- of issue in seed_liquid_materials.sql:
--
-- 1. Solubility values that were off by >15% — usually because the seed
--    picked a value for the wrong hydrate / anhydrous form, or because
--    the temperature pinned in the column comment (20°C) didn't match
--    the value used.
-- 2. Material density (SG, kg/L) was almost entirely NULL — only
--    phosphoric acid had it, and at the wrong number for 80% strength.
--    SG is load-bearing for the liquid LP's volume-displacement math,
--    so filling it in materially improves blend accuracy.
--
-- This migration updates solubility_20c + sg on the standard SA liquid
-- raw materials. Hydrate form pinned to the common commercial SA ag
-- grade: Mn monohydrate, Zn/Fe/Mg-sulphate heptahydrate, Mg nitrate
-- hexahydrate, Ca nitrate tetrahydrate, citric acid monohydrate, sodium
-- molybdate dihydrate, disodium octaborate (Solubor) tetrahydrate.
--
-- Unchanged materials (verified correct): KNO3, MAP, Urea, Ca(NO3)2·4H2O,
-- MKP, SOP, CaCl2, KOH, Boric Acid, CuSO4·5H2O, FeSO4·7H2O, ZnO,
-- Copper Oxy Chloride, (NH4)2SO4. Librel BMX and Hygroplex left at
-- seeded 80 g/L because authoritative supplier TDSes weren't available.
-- ============================================================

-- ── Solubility corrections (the six cases >15% off) ──────────────

UPDATE materials SET solubility_20c = 1130
    WHERE material ILIKE '%magnesium sulphate%'
       OR material ILIKE '%epsom%'
       OR material ILIKE '%MgSO4%';

UPDATE materials SET solubility_20c = 1250
    WHERE material = 'Magnesium Nitrate'
       OR material ILIKE '%magnesium nitrate%';

UPDATE materials SET solubility_20c = 95
    WHERE material ILIKE '%solubor%'
       OR material ILIKE '%disodium octaborate%';

UPDATE materials SET solubility_20c = 840
    WHERE material ILIKE '%sodium molybdate%'
       OR material = 'Sodium Molybdate';

UPDATE materials SET solubility_20c = 730
    WHERE material ILIKE '%manganese sulphate%'
       OR material ILIKE '%MnSO4%';

UPDATE materials SET solubility_20c = 960
    WHERE material ILIKE '%zinc sulphate%'
       OR material ILIKE '%ZnSO4%';

-- ── SG (material density, kg/L) — mostly new values ──────────────
-- Crystal densities for solids; for the phosphoric acid 80% solution
-- we correct 1.57 (which is the density of ~73% acid) to 1.689 @ 20°C.

UPDATE materials SET sg = 2.11  WHERE material ILIKE '%KNO3%' OR material ILIKE '%potassium nitrate%';
UPDATE materials SET sg = 1.80  WHERE material ILIKE '%MAP%' OR material ILIKE '%monoammonium phosphate%';
UPDATE materials SET sg = 1.335 WHERE material ILIKE '%urea%';
UPDATE materials SET sg = 1.89  WHERE material ILIKE '%calcium nitrate%';
UPDATE materials SET sg = 2.34  WHERE material ILIKE '%MKP%' OR material ILIKE '%monopotassium phosphate%';
UPDATE materials SET sg = 1.46  WHERE material ILIKE '%magnesium nitrate%';
UPDATE materials SET sg = 1.68  WHERE material ILIKE '%magnesium sulphate%' OR material ILIKE '%epsom%';
UPDATE materials SET sg = 2.66  WHERE material = 'Potassium Sulphate (SOP)' OR material ILIKE '%K2SO4%';
UPDATE materials SET sg = 2.15  WHERE material ILIKE '%calcium chloride%';
UPDATE materials SET sg = 1.689 WHERE material ILIKE '%phosphoric acid%';
UPDATE materials SET sg = 2.04  WHERE material ILIKE '%potassium hydroxide%' OR material ILIKE '%KOH%';
UPDATE materials SET sg = 1.91  WHERE material ILIKE '%solubor%';
UPDATE materials SET sg = 1.435 WHERE material ILIKE '%boric acid%';
UPDATE materials SET sg = 2.37  WHERE material ILIKE '%sodium molybdate%';
UPDATE materials SET sg = 2.95  WHERE material ILIKE '%manganese sulphate%';
UPDATE materials SET sg = 1.96  WHERE material ILIKE '%zinc sulphate%';
UPDATE materials SET sg = 2.286 WHERE material ILIKE '%copper sulphate%';
UPDATE materials SET sg = 1.898 WHERE material ILIKE '%ferrous sulphate%';
UPDATE materials SET sg = 1.0   WHERE material ILIKE '%iron EDTA%' OR material ILIKE '%Fe 13%';
UPDATE materials SET sg = 5.61  WHERE material ILIKE '%zinc oxide%';
UPDATE materials SET sg = 3.5   WHERE material ILIKE '%copper oxy chloride%' OR material ILIKE '%copper oxychloride%';
UPDATE materials SET sg = 1.542 WHERE material ILIKE '%citric acid%';
UPDATE materials SET sg = 1.77  WHERE material ILIKE '%ammonium sulphate%';

-- Librel BMX and Hygroplex: solubility left at 80 g/L, sg left NULL.
-- Authoritative supplier TDSes not available at time of writing; admin
-- can override both via the /admin/materials dialog once BASF/rebadge
-- data sheets are obtained.
