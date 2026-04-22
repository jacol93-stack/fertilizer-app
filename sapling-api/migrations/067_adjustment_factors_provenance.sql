-- ============================================================
-- 067: Provenance + tier on adjustment_factors
-- ============================================================
-- The adjustment_factors table stores the classification ×
-- nutrient_group multipliers that drive the heuristic calc path
-- (removal × yield × factor) whenever fertilizer_rate_tables has
-- no matching cell. Until now the table had no provenance columns
-- and the specific factors (1.5/1.25/1.0/0.75/0.5/0.0) were
-- committed to the schema without a citation — which is inconsistent
-- with the discipline we apply everywhere else in Track A.
--
-- This migration adds source/source_section/source_year/source_note/
-- tier columns and honestly backfills the existing 20 rows as Tier 6
-- ("implementer convention / agronomist rule"). The shape follows
-- the FSSA/FERTASA buildup-drawdown principle described qualitatively
-- in FERTASA 5.1 (Fertilizer guidelines — principles), but FERTASA
-- does NOT publish these specific numeric factors anywhere in the
-- handbook. Sections 5.1 + 5.2 (soil interpretation) are intros
-- with no table that says "Very Low → 1.5×".
--
-- What these factors actually drive today:
--   * Ca/Mg/S on every crop (no rate tables for these nutrients yet)
--   * Micros (Zn/B/Mn/Fe/Cu/Mo) on every crop (no micro rules yet)
--   * All nutrients for crops without any fertilizer_rate_tables
--     coverage (citrus pending Raath 2021, pecan, mango, etc.)
--
-- When a fertilizer_rate_tables row exists for (crop, nutrient,
-- yield-band, soil-band), the rate table overrides this factor —
-- see calculate_nutrient_targets() in soil_engine.py.
--
-- The next migrations (068 Ca/Mg cation-ratio path, 069 S rate
-- tables, 070+ micro application rules) will progressively
-- eliminate the scenarios where this Tier-6 fallback runs, driving
-- the calculator toward zero heuristic-path recommendations.
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- Schema: add provenance + tier columns
-- ------------------------------------------------------------
ALTER TABLE public.adjustment_factors
    ADD COLUMN IF NOT EXISTS source         TEXT,
    ADD COLUMN IF NOT EXISTS source_section TEXT,
    ADD COLUMN IF NOT EXISTS source_year    INTEGER,
    ADD COLUMN IF NOT EXISTS source_note    TEXT,
    ADD COLUMN IF NOT EXISTS tier           INTEGER
        CHECK (tier IS NULL OR tier BETWEEN 1 AND 6);

COMMENT ON COLUMN public.adjustment_factors.tier IS
    'Source tier per DATA_AUDIT_PLAN.md tier system: 1=SA industry body (FERTASA/SASRI/SAMAC/ARC), 2=peer-reviewed SA research, 3=international (SA-applicable), 4=commercial bulletin, 5=lab interpretation guide, 6=implementer convention / agronomist rule capture.';

COMMENT ON COLUMN public.adjustment_factors.source_note IS
    'Rationale for this factor. When Tier 6, explains what principle the shape follows and why these specific values are implementer convention rather than handbook-published.';

-- ------------------------------------------------------------
-- Backfill: mark all 20 existing rows as Tier 6 with per-group
-- rationale notes. Separate UPDATEs so each nutrient group can
-- carry a distinct source_note explaining WHY its curve looks
-- the way it does.
-- ------------------------------------------------------------

UPDATE public.adjustment_factors
   SET source         = 'Implementer convention (SA agronomy practice)',
       source_section = '5.1',
       source_note    = 'N is not bankable in soil — mineralization flux dominates, soil-test classification does not reliably drive buildup/drawdown decisions for nitrogen. Factor held at 1.0 for all classifications. N targets come from removal × yield (heuristic) or fertilizer_rate_tables (authoritative when seeded). FERTASA 5.1 discusses this principle qualitatively.',
       tier           = 6,
       updated_at     = NOW()
 WHERE nutrient_group = 'N';

UPDATE public.adjustment_factors
   SET source         = 'Implementer convention (SA agronomy practice)',
       source_section = '5.1',
       source_note    = 'Micro-element quantities are too small for buildup/drawdown logic to materially affect outcomes. Factor held at 1.0 for all classifications. FERTASA publishes isolated per-crop micro exceptions (e.g. 5.12.2 lucerne B can be increased by factor 1.5 at very-low B on non-clay soils) — these belong in crop_sufficiency_overrides or a per-crop micro-rules table, not this universal table. Migration 070+ will build that schema.',
       tier           = 6,
       updated_at     = NOW()
 WHERE nutrient_group = 'micro';

UPDATE public.adjustment_factors
   SET source         = 'Implementer convention (FSSA/FERTASA drawdown shape, not handbook-published)',
       source_section = '5.1',
       source_note    = 'The 1.5 / 1.25 / 1.0 / 0.75 / 0.5 shape follows the FSSA/FERTASA buildup-drawdown principle described qualitatively in FERTASA 5.1 ("Fertilizer guidelines — principles"). The specific numeric factors are implementer convention, not handbook-published. P curve is gentler than cations (bottoms at 0.5 not 0.0) because P is less leachable and productive fixed-P inventory shouldn''t be stranded by a "stop applying" recommendation — FERTASA keeps a minimum-maintenance P rate at high soil-P (see potato 5.6.2.4, wheat P 5.4.3.1.2). Superseded by fertilizer_rate_tables whenever a cell matches (crop, nutrient, yield, soil-band).',
       tier           = 6,
       updated_at     = NOW()
 WHERE nutrient_group = 'P';

UPDATE public.adjustment_factors
   SET source         = 'Implementer convention (FSSA/FERTASA drawdown shape, not handbook-published)',
       source_section = '5.1',
       source_note    = 'The 1.5 / 1.25 / 1.0 / 0.5 / 0.0 shape follows the FSSA/FERTASA buildup-drawdown principle described qualitatively in FERTASA 5.1. The specific numeric factors are implementer convention, not handbook-published. K/Ca/Mg/S curve bottoms at 0.0 (Very High → no application) because cations can be fully held off at saturated soils without stranding productive inventory. Superseded by fertilizer_rate_tables for K; Ca/Mg handled by cation-ratio logic (migration 068, pending) via FERTASA 5.2.2 formulas; S handled by per-crop rate tables (migration 069, pending).',
       tier           = 6,
       updated_at     = NOW()
 WHERE nutrient_group = 'cations';

-- ------------------------------------------------------------
-- Lock in provenance discipline: source and tier NOT NULL going
-- forward. Future inserts must cite or acknowledge Tier 6.
-- ------------------------------------------------------------
ALTER TABLE public.adjustment_factors
    ALTER COLUMN source SET NOT NULL,
    ALTER COLUMN tier   SET NOT NULL;

COMMIT;
