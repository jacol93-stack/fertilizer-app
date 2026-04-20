-- ============================================================
-- 056: SASRI sugarcane soil-test thresholds (S, Ca, Mg)
-- ============================================================
-- Source: SASRI Information Sheets 7.6 (Sulphur), 7.7 (Calcium and
--         magnesium management). Oct 2025 editions.
--
-- SASRI publishes specific soil-test thresholds below which response is
-- expected. These are sugarcane-tuned and differ from the universal
-- soil_sufficiency values; seeded as crop_sufficiency_overrides keyed
-- on crop='Sugarcane'.
--
-- Per-parameter SASRI thresholds:
--   * Sulphur (IS 7.6):
--       - < 3 mg S/kg topsoil → response guaranteed
--       - 3 to 10 mg S/kg → response uncertain
--       - > 10 mg S/kg → no response expected
--     Encoded as very_low_max=3, low_max=10. Optimal/High left to
--     universal soil_sufficiency (merge path in the engine picks
--     non-NULL override values and falls back to universal otherwise).
--
--   * Calcium (IS 7.7):
--       - < 300 mg Ca/L (≈ mg/kg) → inadequate, supplement advised.
--     Encoded as low_max=300 (boundary between "supplement required"
--     and "adequate"). Universal very_low_max=200 retained so severely
--     depleted soils still classify as Very Low and trigger the larger
--     sufficiency adjustment.
--
--   * Magnesium (IS 7.7):
--       - < 50 mg Mg/L → inadequate, supplement advised (usually
--         dolomitic lime).
--     Encoded as low_max=50. Same pattern as Ca.
--
-- Not included:
--   * P and K (IS 7.4 / 7.5): SASRI doesn't publish specific per-soil-
--     type threshold values in the public Information Sheets — these
--     live inside the FAS lab report (paid analysis service). Existing
--     universal soil_sufficiency P and K bands apply in the meantime.
-- ============================================================

BEGIN;

-- Upsert pattern: remove any existing SASRI-sourced overrides first.
-- The pre-existing K override from migration 044 stays untouched.
DELETE FROM public.crop_sufficiency_overrides
WHERE crop = 'Sugarcane' AND parameter IN ('S', 'Ca', 'Mg');

INSERT INTO public.crop_sufficiency_overrides
    (crop, parameter, very_low_max, low_max, optimal_max, high_max, notes)
VALUES
    ('Sugarcane', 'S',  3,    10,   NULL, NULL,
        'SASRI IS 7.6: response guaranteed below 3 mg/kg; uncertain 3-10; unlikely above 10. Optimal/High bounds fall through to universal soil_sufficiency.'),
    ('Sugarcane', 'Ca', NULL, 300,  NULL, NULL,
        'SASRI IS 7.7: < 300 mg/L topsoil Ca is inadequate and supplement is advised (typically calcitic lime). Very_low_max left to universal (200).'),
    ('Sugarcane', 'Mg', NULL, 50,   NULL, NULL,
        'SASRI IS 7.7: < 50 mg/L topsoil Mg is inadequate; dolomitic lime typically advised. Very_low_max left to universal (40).');

COMMIT;
