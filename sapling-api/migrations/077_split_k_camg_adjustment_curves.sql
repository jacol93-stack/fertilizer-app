-- Migration 077: split the shared "cations" adjustment curve into
-- separate K, ca_mg, and S curves.
--
-- Prior state: K / Ca / Mg / S all shared nutrient_group='cations' with
-- curve 1.5 / 1.25 / 1.0 / 0.5 / 0.0 across Very Low → Very High. That
-- shape suits K (highly mobile, luxury consumption is real, aggressive
-- drawdown on High/Very High soils is agronomically sound) but over-
-- reduces Ca and Mg. Ca/Mg drive base saturation, pH buffering, and
-- structural uptake — zeroing them out on "Very High" soils creates
-- Ca:Mg:K imbalance and starves the reactor for future season buffering.
-- S is an anion (SO4): classification-based drawdown doesn't apply, as
-- sulfate leaches seasonally; stay flat at 1.0 and rely on S_pct minima.
--
-- New curves:
--   K     : 1.5 / 1.25 / 1.0 / 0.5 / 0.0 (unchanged shape — K luxury OK)
--   ca_mg : 1.25 / 1.1 / 1.0 / 0.75 / 0.5 (gentler — base saturation)
--   S     : 1.0 / 1.0 / 1.0 / 1.0 / 1.0 (flat — sulfate mobility)
--
-- Legacy 'cations' rows retained for backward compat with any external
-- consumer that queries by group='cations'; the Python engine now maps
-- K → 'K', Ca/Mg → 'ca_mg', S → 'S' (see NUTRIENT_GROUP_MAP).
--
-- Tier 6 (implementer convention with SA agronomy + FERTASA rate-table
-- drawdown reasoning); a FERTASA handbook-direct source would be Tier 1
-- if published — none is per a search of the 2024 edition. Source note
-- records the agronomic rationale.

INSERT INTO adjustment_factors (classification, nutrient_group, factor, source, source_section, source_note, tier) VALUES
  ('Very Low',  'K', 1.5,   'Implementer convention (FSSA/FERTASA drawdown shape; K-specific split 2026-04-24)', '5.1', 'K is mobile + luxury consumption is real; aggressive bump on Very Low is justified by FERTASA rate-table shape.', 6),
  ('Low',       'K', 1.25,  'Implementer convention (FSSA/FERTASA drawdown shape; K-specific split 2026-04-24)', '5.1', 'Standard low-K bump.', 6),
  ('Optimal',   'K', 1.0,   'Implementer convention (FSSA/FERTASA drawdown shape; K-specific split 2026-04-24)', '5.1', 'Replacement rate.', 6),
  ('High',      'K', 0.5,   'Implementer convention (FSSA/FERTASA drawdown shape; K-specific split 2026-04-24)', '5.1', 'High-K soils: drawdown to half-replacement (luxury consumption acceptable).', 6),
  ('Very High', 'K', 0.0,   'Implementer convention (FSSA/FERTASA drawdown shape; K-specific split 2026-04-24)', '5.1', 'Very-High K: hold application; residual supplies season demand.', 6),

  ('Very Low',  'ca_mg', 1.25, 'Implementer convention (SA agronomy, base-saturation-preserving 2026-04-24)', '5.1', 'Ca/Mg drive base saturation + pH buffering; gentler bump than K.', 6),
  ('Low',       'ca_mg', 1.1,  'Implementer convention (SA agronomy, base-saturation-preserving 2026-04-24)', '5.1', 'Mild Ca/Mg bump.', 6),
  ('Optimal',   'ca_mg', 1.0,  'Implementer convention (SA agronomy, base-saturation-preserving 2026-04-24)', '5.1', 'Replacement rate.', 6),
  ('High',      'ca_mg', 0.75, 'Implementer convention (SA agronomy, base-saturation-preserving 2026-04-24)', '5.1', 'High Ca/Mg: soften drawdown (structural cations; zeroing creates Ca:Mg:K imbalance on high-K soils).', 6),
  ('Very High', 'ca_mg', 0.5,  'Implementer convention (SA agronomy, base-saturation-preserving 2026-04-24)', '5.1', 'Very-High Ca/Mg: reduce to half-replacement, not zero — base saturation must stay stable.', 6),

  ('Very Low',  'S', 1.0, 'Implementer convention (sulfate mobility; classification-based drawdown does not apply 2026-04-24)', '5.1', 'S flat — sulfate leaches seasonally. Replenishment logic is via S_pct minima in blends, not this curve.', 6),
  ('Low',       'S', 1.0, 'Implementer convention (sulfate mobility; classification-based drawdown does not apply 2026-04-24)', '5.1', 'S flat.', 6),
  ('Optimal',   'S', 1.0, 'Implementer convention (sulfate mobility; classification-based drawdown does not apply 2026-04-24)', '5.1', 'S flat.', 6),
  ('High',      'S', 1.0, 'Implementer convention (sulfate mobility; classification-based drawdown does not apply 2026-04-24)', '5.1', 'S flat.', 6),
  ('Very High', 'S', 1.0, 'Implementer convention (sulfate mobility; classification-based drawdown does not apply 2026-04-24)', '5.1', 'S flat.', 6)
ON CONFLICT (classification, nutrient_group) DO UPDATE SET
  factor = EXCLUDED.factor,
  source = EXCLUDED.source,
  source_section = EXCLUDED.source_section,
  source_note = EXCLUDED.source_note,
  tier = EXCLUDED.tier;
