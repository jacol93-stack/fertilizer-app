-- ============================================================
-- 068: Cation-ratio base-target path for Ca/Mg + provenance on
--      ideal_ratios + crop_calc_flags table
-- ============================================================
-- Replaces the heuristic "removal × yield × factor" path for Ca
-- and Mg with a FERTASA-5.2.2-grounded base-saturation target
-- calculation for crops on normal mineral soils.
--
-- What this migration does (SQL layer):
--   1. Add provenance columns (source / source_section / tier / ...)
--      to ideal_ratios, parallel to the 067 treatment of
--      adjustment_factors. Backfill existing rows with honest tier
--      attribution: the FERTASA-5.2.2-published ratios get Tier 1
--      (Ca:Mg 3-5, Ca:K 10-20, Mg:K 2-4, base-saturation targets);
--      the rest carry their provenance too.
--
--   2. Create `crop_calc_flags` — a per-crop flags table with
--      `skip_cation_ratio_path BOOLEAN`. Seed TRUE for the
--      acid-loving crops where the 60-70% Ca base sat target would
--      actively damage the crop (blueberry, raspberry, blackberry,
--      rooibos, honeybush). These crops keep the heuristic fallback.
--
-- What the engine does (app layer, applied in this commit):
--   - New function calculate_cation_ratio_target() applies FERTASA
--     5.2.2's base-saturation formula: (target_pct - current_pct) ×
--     CEC × equivalent_weight × soil_mass_ha to compute kg/ha.
--   - Conversion factors (from FERTASA 5.2.2): Ca ÷200, Mg ÷122,
--     K ÷391 for mg/kg → cmol_c/kg.
--   - Soil mass assumption: 2000 t/ha (consistent with existing code
--     in adjust_targets_for_ratios; equivalent to ~15 cm × 1.33
--     g/cm³ bulk density — standard SA topsoil sampling depth).
--   - Split-over-2-seasons by default (half of full shortfall
--     correction), with source_note flagging the convention.
--
-- Preemption order in calculate_nutrient_targets (Ca/Mg):
--     rate-table hit  →  ratio-path  →  heuristic fallback
-- For K the ratio-path is SKIPPED — most crops with K coverage
-- have a rate table (wheat, potato, banana, etc.), and when they
-- don't, heuristic is still closer to correct than base saturation
-- targeting (K is mobile, base-sat less physically meaningful).
--
-- Skip conditions for the ratio path:
--   * CEC < 3 cmol_c/kg (base-saturation math unstable on very
--     low-CEC sandy soils)
--   * crop has skip_cation_ratio_path = TRUE
--   * CEC not measured at all
-- Any of these → fall through to heuristic with a source_note.
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. ideal_ratios: provenance columns
-- ------------------------------------------------------------
ALTER TABLE public.ideal_ratios
    ADD COLUMN IF NOT EXISTS source         TEXT,
    ADD COLUMN IF NOT EXISTS source_section TEXT,
    ADD COLUMN IF NOT EXISTS source_year    INTEGER,
    ADD COLUMN IF NOT EXISTS source_note    TEXT,
    ADD COLUMN IF NOT EXISTS tier           INTEGER
        CHECK (tier IS NULL OR tier BETWEEN 1 AND 6);

COMMENT ON COLUMN public.ideal_ratios.tier IS
    'Source tier: 1=SA industry body (FERTASA/SASRI), 2=peer-reviewed SA, 3=international, 4=commercial bulletin, 5=lab guide, 6=implementer convention.';

-- Backfill — per-ratio provenance. FERTASA 5.2.2 publishes Ca:Mg,
-- Ca:K, Mg:K, and the base-saturation targets explicitly. The
-- other ratios (P:Zn antagonism, Fe:Mn balance, N:S protein ratio,
-- K:Na salinity) come from SA interpretation guides + international
-- calibrations.

UPDATE public.ideal_ratios
   SET source = 'FERTASA Handbook', source_section = '5.2.2', source_year = 2019,
       source_note = 'FERTASA 5.2.2 (cation ratios) endorses Ca:Mg around 3-5 on most SA soils. Drops below 2 indicate Mg excess; above 8 indicates Mg deficiency.',
       tier = 1, updated_at = NOW()
 WHERE ratio = 'Ca:Mg';

UPDATE public.ideal_ratios
   SET source = 'FERTASA Handbook', source_section = '5.2.2', source_year = 2019,
       source_note = 'FERTASA 5.2.2 cation-ratio guidance. Low Ca:K indicates K excess relative to Ca (common on over-fertilised orchards).',
       tier = 1, updated_at = NOW()
 WHERE ratio = 'Ca:K';

UPDATE public.ideal_ratios
   SET source = 'FERTASA Handbook', source_section = '5.2.2', source_year = 2019,
       source_note = 'FERTASA 5.2.2 cation-ratio guidance.',
       tier = 1, updated_at = NOW()
 WHERE ratio = 'Mg:K';

UPDATE public.ideal_ratios
   SET source = 'FERTASA Handbook', source_section = '5.2.2', source_year = 2019,
       source_note = 'Ideal Ca saturation of the exchange complex. FERTASA endorses this range for most non-acid-loving SA crops on mineral soils.',
       tier = 1, updated_at = NOW()
 WHERE ratio = 'Ca base sat.';

UPDATE public.ideal_ratios
   SET source = 'FERTASA Handbook', source_section = '5.2.2', source_year = 2019,
       source_note = 'Ideal Mg saturation of the exchange complex.',
       tier = 1, updated_at = NOW()
 WHERE ratio = 'Mg base sat.';

UPDATE public.ideal_ratios
   SET source = 'FERTASA Handbook', source_section = '5.2.2', source_year = 2019,
       source_note = 'Ideal K saturation of the exchange complex. Some SA orchard and vineyard calibrations target higher (5-8%).',
       tier = 1, updated_at = NOW()
 WHERE ratio = 'K base sat.';

UPDATE public.ideal_ratios
   SET source = 'FERTASA Handbook', source_section = '5.2.2', source_year = 2019,
       source_note = 'Na saturation; above 5% = sodic, above 15% = severe. FERTASA 5.2.2 and ARC-ISCW salinity guidelines.',
       tier = 1, updated_at = NOW()
 WHERE ratio = 'Na base sat.';

UPDATE public.ideal_ratios
   SET source = 'FERTASA Handbook', source_section = '5.2.2', source_year = 2019,
       source_note = 'Acid saturation (H + Al). Above 20% typically triggers lime application per Eksteen R-value concept (FERTASA 1.8).',
       tier = 1, updated_at = NOW()
 WHERE ratio = 'H+Al base sat.';

UPDATE public.ideal_ratios
   SET source = 'Combined Ca+Mg vs K balance (SA agronomy convention)', source_section = '5.2.2',
       source_note = 'Derived from individual Ca:K and Mg:K ratios in FERTASA 5.2.2.',
       tier = 2, updated_at = NOW()
 WHERE ratio = '(Ca+Mg):K';

UPDATE public.ideal_ratios
   SET source = 'IPNI Better Crops + SA lab interpretation guides', source_section = NULL,
       source_note = 'High P inhibits Zn uptake; SA lab interpretation convention flags ratios above 15-20 as risk of Zn deficiency. Present in Bemlab, Omnia Lab bulletins.',
       tier = 5, updated_at = NOW()
 WHERE ratio = 'P:Zn';

UPDATE public.ideal_ratios
   SET source = 'IPI / IPNI balance-of-nutrients literature', source_section = NULL,
       source_note = 'Soil Fe:Mn balance; high Fe can suppress Mn uptake. International literature; not explicit in FERTASA.',
       tier = 3, updated_at = NOW()
 WHERE ratio = 'Fe:Mn';

UPDATE public.ideal_ratios
   SET source = 'FERTASA per-crop protein prose', source_section = '5.4.3 (wheat)',
       source_note = 'Grain protein synthesis requires adequate S relative to N. FERTASA wheat 5.4.3 mentions leaf N:S >18 as S-deficiency risk.',
       tier = 2, updated_at = NOW()
 WHERE ratio = 'N:S';

UPDATE public.ideal_ratios
   SET source = 'ARC-ISCW salinity management guidelines', source_section = NULL,
       source_note = 'K:Na on the exchange complex. Below 3 indicates salinity concern; K should dominate to prevent Na-induced K deficiency.',
       tier = 2, updated_at = NOW()
 WHERE ratio = 'K:Na';

-- Lock in provenance for future inserts
ALTER TABLE public.ideal_ratios
    ALTER COLUMN source SET NOT NULL,
    ALTER COLUMN tier SET NOT NULL;

-- ------------------------------------------------------------
-- 2. crop_calc_flags: per-crop calculator behaviour flags
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.crop_calc_flags (
    crop                      TEXT PRIMARY KEY,
    skip_cation_ratio_path    BOOLEAN NOT NULL DEFAULT FALSE,
    source                    TEXT NOT NULL,
    source_section            TEXT,
    source_year               INTEGER,
    source_note               TEXT,
    tier                      INTEGER NOT NULL
        CHECK (tier BETWEEN 1 AND 6),
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.crop_calc_flags IS
    'Per-crop boolean switches that control calculator behaviour. Separate from crop_sufficiency_overrides (which stores per-parameter threshold bands) so the semantic shape stays clean — flags here toggle calc paths, not thresholds.';

COMMENT ON COLUMN public.crop_calc_flags.skip_cation_ratio_path IS
    'When TRUE, skip the FERTASA 5.2.2 base-saturation calc for Ca/Mg on this crop and fall through to heuristic. Required for acid-loving crops (blueberry, rooibos) where the universal 60-70% Ca target would cause real damage.';

-- Enable RLS (same pattern as adjustment_factors / ideal_ratios —
-- public-read, admin-write).
ALTER TABLE public.crop_calc_flags ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "crop_calc_flags_select" ON public.crop_calc_flags;
CREATE POLICY "crop_calc_flags_select" ON public.crop_calc_flags
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "crop_calc_flags_service" ON public.crop_calc_flags;
CREATE POLICY "crop_calc_flags_service" ON public.crop_calc_flags
    AS PERMISSIVE FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Seed acid-loving crops where universal base-saturation targets would
-- cause damage. Sources: the same horticultural literature that
-- informed the existing acidic-pH overrides (migration 063 for
-- blueberry, migration 065 for rooibos/honeybush).
INSERT INTO public.crop_calc_flags
    (crop, skip_cation_ratio_path, source, source_section, source_year, source_note, tier)
VALUES
    ('Blueberry',  TRUE, 'MSU Extension E2011 + SA blueberry industry practice', 'Table 4 + pH-targeting sections', 2012,
        'Blueberry thrives at pH 4.0-5.5 with low Ca saturation (<40%). FERTASA universal 60-70% Ca base-saturation target would damage the crop. Matches the acidic sufficiency overrides seeded in 063.',
        1),
    ('Raspberry',  TRUE, 'NCSU AG-697 + SA caneberry practice', NULL, 2018,
        'Raspberry prefers slightly acidic soils; universal cation-ratio targets over-apply Ca/Mg.',
        3),
    ('Blackberry', TRUE, 'NCSU AG-697 + SA caneberry practice', NULL, 2018,
        'Blackberry prefers slightly acidic soils; universal cation-ratio targets over-apply Ca/Mg.',
        3),
    ('Rooibos',    TRUE, 'SARC (SA Rooibos Council) cultivation guide', NULL, 2020,
        'Rooibos is native to acidic nutrient-poor Cape fynbos soils. Migration 065 already flagged this crop with "no artificial fertilisation" rate rows; the Ca/Mg ratio path must also skip.',
        1),
    ('Honeybush',  TRUE, 'DAFF honeybush cultivation guide', NULL, 2019,
        'Honeybush is native to acidic Cape fynbos soils like rooibos; same reasoning.',
        1);

COMMIT;
