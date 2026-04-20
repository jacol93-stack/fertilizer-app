-- ============================================================
-- 055: Avocado leaf norms — add deficient / excess bounds (NZAGA 2008)
-- ============================================================
-- Source: Thorp et al. (2008) "The leaf mineral status of New Zealand
--         'Hass' avocados". New Zealand Avocado Growers' Association
--         Annual Research Report, Vol 8. Table 1 — "Avocado Book"
--         column — lists deficient / range / excess bounds that trace
--         through to the canonical "The Avocado: Botany, Production and
--         Uses" reference (Whiley, Schaffer, Wolstenholme 2002).
--         Free PDF: https://www.avocadosource.com/Journals/NZAGA/
--                   NZAGA_2008/NZAGA_2008_01.pdf
--
-- Why we need it: the existing Avocado rows (seeded in 043 from FERTASA
-- 5.7.1) only populated sufficient_min/max. Deficient_max and excess_min
-- were all NULL, so the engine couldn't distinguish "Low but OK" from
-- "actually deficient" or "High but OK" from "toxic excess." NZAGA's
-- published bounds fill both tails without contradicting FERTASA's
-- sufficient range — the Avocado Book's "Range" is broader than FERTASA's
-- SA-specific optimal target, so leaving the tighter FERTASA sufficient
-- band in place is correct. NZAGA's deficient and excess edges are
-- additive: they flag genuinely problematic readings.
--
-- Scope:
--   * Generic Avocado rows: updated with the Avocado Book values.
--   * Hass-specific N row: same deficient/excess applied (NZAGA's
--     Table 1 is explicitly Hass).
--   * Edranol / Pinkerton / Ryan cultivar-specific N rows: left unchanged
--     — NZAGA doesn't publish cultivar-specific deficient/excess bounds
--     for those.
-- ============================================================

BEGIN;

-- Generic Avocado (no cultivar marker in element name)
UPDATE public.fertasa_leaf_norms SET
    deficient_max = 1.6,
    excess_min = 3.0,
    notes = 'Deficient <1.6% / Excess >3.0% per NZAGA 2008 Table 1 ("Avocado Book" column). FERTASA 5.7.1 sufficient range 1.7-1.9% retained as the SA-specific optimal target.'
WHERE crop = 'Avocado' AND element = 'N';

UPDATE public.fertasa_leaf_norms SET
    deficient_max = 0.14,
    excess_min = 0.30,
    notes = 'Deficient <0.14% / Excess >0.30% per NZAGA 2008 Table 1 ("Avocado Book" column). FERTASA 5.7.1 sufficient range 0.08-0.15% retained (SA trials show adequate yield at leaf P >= 0.08%; Du Plessis & Koen WAC2).'
WHERE crop = 'Avocado' AND element = 'P';

UPDATE public.fertasa_leaf_norms SET
    deficient_max = 0.9,
    excess_min = 3.0,
    notes = 'Deficient <0.9% / Excess >3.0% per NZAGA 2008 Table 1 ("Avocado Book" column). FERTASA 5.7.1 sufficient range 0.75-1.15% retained.'
WHERE crop = 'Avocado' AND element = 'K';

UPDATE public.fertasa_leaf_norms SET
    deficient_max = 0.5,
    excess_min = 4.0,
    notes = 'Deficient <0.5% / Excess >4.0% per NZAGA 2008 Table 1 ("Avocado Book" column). FERTASA 5.7.1 sufficient range 1.0-2.0% retained.'
WHERE crop = 'Avocado' AND element = 'Ca';

UPDATE public.fertasa_leaf_norms SET
    deficient_max = 0.15,
    excess_min = 1.0,
    notes = 'Deficient <0.15% / Excess >1.0% per NZAGA 2008 Table 1 ("Avocado Book" column). FERTASA 5.7.1 sufficient range 0.4-0.8% retained.'
WHERE crop = 'Avocado' AND element = 'Mg';

UPDATE public.fertasa_leaf_norms SET
    deficient_max = 0.05,
    excess_min = 1.0,
    notes = 'Deficient <0.05% / Excess >1.0% per NZAGA 2008 Table 1 ("Avocado Book" column). FERTASA 5.7.1 sufficient range 0.2-0.6% retained.'
WHERE crop = 'Avocado' AND element = 'S';

UPDATE public.fertasa_leaf_norms SET
    deficient_max = 40,
    notes = 'Deficient range 20-40 mg/kg per NZAGA 2008; deficient_max set to the upper of that (40). FERTASA 5.7.1 sufficient range 50-150 mg/kg retained. Avocado Book does not publish a hard Fe excess bound.'
WHERE crop = 'Avocado' AND element = 'Fe';

UPDATE public.fertasa_leaf_norms SET
    deficient_max = 15,
    excess_min = 1000,
    notes = 'Deficient <15 mg/kg / Excess >1000 mg/kg per NZAGA 2008 Table 1 ("Avocado Book" column). FERTASA 5.7.1 sufficient range 50-250 mg/kg retained.'
WHERE crop = 'Avocado' AND element = 'Mn';

UPDATE public.fertasa_leaf_norms SET
    deficient_max = 20,
    excess_min = 100,
    notes = 'Deficient <20 mg/kg / Excess >100 mg/kg per NZAGA 2008 Table 1 ("Avocado Book" column). FERTASA 5.7.1 sufficient range 25-100 mg/kg retained.'
WHERE crop = 'Avocado' AND element = 'Zn';

UPDATE public.fertasa_leaf_norms SET
    deficient_max = 20,
    excess_min = 100,
    notes = 'Deficient <20 mg/kg / Excess >100 mg/kg per NZAGA 2008 Table 1 ("Avocado Book" column). FERTASA 5.7.1 sufficient range 40-80 mg/kg retained.'
WHERE crop = 'Avocado' AND element = 'B';

-- Cu: NZAGA 2008 doesn't publish Cu in Table 1. Leave the FERTASA row as-is
-- (sufficient 5-15 mg/kg, no deficient/excess bounds).

-- Hass-specific N row (FERTASA cultivar variant): NZAGA's Hass data
-- applies directly here.
UPDATE public.fertasa_leaf_norms SET
    deficient_max = 1.6,
    excess_min = 3.0,
    notes = 'Hass-specific. Deficient <1.6% / Excess >3.0% per NZAGA 2008 Table 1 (Hass cultivar). FERTASA 5.7.1 sufficient range 2.2-2.3% retained (SA cultivar target).'
WHERE crop = 'Avocado' AND element = 'N (Hass)';

COMMIT;
