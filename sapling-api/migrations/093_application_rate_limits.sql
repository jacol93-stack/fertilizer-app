-- ============================================================
-- 093: Per-event application-rate ceilings
-- ============================================================
-- Operationally-sane upper bounds per delivery method. Enforced as
-- watch-severity warnings by blend_validator (not hard blocks) so the
-- engine's blend output stays unblocked but the agronomist sees when
-- a recipe overshoots reasonable per-pass volumes.
--
-- Defaults are SA agronomy norms — granular spreader passes top out
-- ~350-400 kg/ha for clean coverage; 1500 kg/ha is the upper limit
-- before requiring multiple passes. Liquid fertigation 500 L/ha covers
-- a typical 2-3 hour drip cycle. Foliar 800 L/ha covers a thorough
-- airblast pass; above that wets the canopy past run-off.
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.application_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    method_kind TEXT NOT NULL UNIQUE,
    max_kg_per_ha NUMERIC,
    max_litres_per_ha NUMERIC,
    notes TEXT,
    source TEXT DEFAULT 'IMPLEMENTER_CONVENTION',
    tier INT DEFAULT 6,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO public.application_rate_limits (method_kind, max_kg_per_ha, max_litres_per_ha, notes)
VALUES
  ('dry_broadcast',     1500, NULL, 'SA granular spreader practical ceiling per pass — above this requires split passes'),
  ('dry_side_dress',     600, NULL, 'Side-dress band rate limit; higher requires re-banding'),
  ('dry_band',           600, NULL, 'Same as side-dress: row-banding ceiling'),
  ('dry_basal',         1500, NULL, 'Pre-plant broadcast ceiling — same as dry_broadcast'),
  ('liquid_fertigation', NULL, 500, 'Drip cycle volume per ha for a 2-3 hour run'),
  ('liquid_drip',        NULL, 500, 'Drip-line equivalent of fertigation'),
  ('liquid_drench',      NULL, 800, 'Drench around root zone — higher than fertigation since infiltration is direct'),
  ('foliar',             NULL, 800, 'Airblast canopy spray ceiling — above this runs off'),
  ('foliar_spray',       NULL, 800, 'Alias of foliar')
ON CONFLICT (method_kind) DO NOTHING;

COMMENT ON TABLE public.application_rate_limits IS
  'Per-event operational rate ceilings. blend_validator surfaces a watch-severity warning when a blend exceeds the ceiling for its method_kind. Tunable without code change.';

COMMIT;
