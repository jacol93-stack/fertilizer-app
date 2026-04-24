-- Migration 075: Phase 7 customer-ready gate scaffold
--
-- Adds a boolean column `customer_ready` to crop_requirements. When
-- false, the crop is hidden from non-admin users in the crop picker
-- (see /api/crop-norms/ role-aware filter). Defaults to TRUE on every
-- existing row so today's behavior is unchanged — admin flips to
-- false per-crop as data-quality review sign-off completes.
--
-- Rationale: per state_of_play 2026-04-23, the customer-ready gate is
-- the mechanism for "5 crops at 100% beats 40 at 60%". Data coverage
-- varies per crop (ideal_ratios sparse, foliar triggers seeded for 4
-- crops only, crop_sufficiency_overrides covers 15/81 crops). Flipping
-- a crop to customer_ready=true should require:
--   (1) FERTASA / SA-industry-body source for per-tree or per-ha target
--   (2) Growth stage rows seeded
--   (3) Sufficiency override rows for the critical parameters
--   (4) Foliar trigger rules (at minimum soil-availability-gap)
--   (5) Agronomist sign-off on a golden programme

ALTER TABLE crop_requirements
ADD COLUMN IF NOT EXISTS customer_ready boolean NOT NULL DEFAULT true;

COMMENT ON COLUMN crop_requirements.customer_ready IS
'Phase 7 gate: when false, this crop is hidden from non-admin users in the crop picker. Default true preserves current behavior; flip per-crop as data quality review sign-off completes.';
