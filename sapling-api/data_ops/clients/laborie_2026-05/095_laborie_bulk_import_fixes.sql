-- ============================================================
-- 095: Laborie (Anton Muller) bulk-import data repair
-- ============================================================
-- Repairs the 2026-04-30 fields-bulk upload to Laborie farm
-- (client Anton Muller). Two issues to fix:
--
--   1. All 14 citrus blocks landed with crop='Citrus' (parent),
--      which has zero per_unit values in crop_requirements. The
--      engine's heuristic path returns 0 kg/ha for every nutrient
--      on these blocks. Remap based on cultivar:
--        Star Ruby                                  → Citrus (Grapefruit)
--        Valencia Late / Turkey Valencia / Bennie Valencia → Citrus (Valencia)
--
--   2. Macadamia "1C" (cv 695, 2 ha, age 10, pop 217.5) was silently
--      dropped because the upload also contained a Citrus "1C" Turkey
--      Valencia block. The bulk-import default on_conflict=skip plus
--      the partial-unique index from migration 091 collapsed the two
--      rows into one. Re-create the mac block under the disambiguated
--      name "1C-Mac" so it can coexist with the citrus 1C.
--
-- Scope is intentionally narrow: this migration only touches the
-- Laborie farm (farm_id 5264f5c4-d9f9-450a-a884-5bb735b88c21). The
-- underlying canonicaliser logic that should infer Citrus (Variant)
-- from a Valencia/Star Ruby/Lemon cultivar is a code-level fix on
-- the bulk-import path (out of scope here).
-- ============================================================

BEGIN;

-- ── 1. Star Ruby cultivar → Citrus (Grapefruit) ──────────────────────
UPDATE public.fields
SET crop = 'Citrus (Grapefruit)'
WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND crop = 'Citrus'
  AND cultivar = 'Star Ruby'
  AND deleted_at IS NULL;

-- ── 2. Valencia-family cultivars → Citrus (Valencia) ─────────────────
UPDATE public.fields
SET crop = 'Citrus (Valencia)'
WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND crop = 'Citrus'
  AND cultivar IN ('Valencia Late', 'Turkey Valencia', 'Bennie Valencia')
  AND deleted_at IS NULL;

-- ── 3. Re-create the missing Macadamia 1C block ──────────────────────
-- Idempotent: WHERE NOT EXISTS skips the insert if the block already
-- exists (e.g. on a re-run of this migration).
INSERT INTO public.fields (
    farm_id, name, crop, cultivar, size_ha, tree_age, pop_per_ha,
    yield_unit, irrigation_type, fertigation_capable
)
SELECT
    '5264f5c4-d9f9-450a-a884-5bb735b88c21'::uuid,
    '1C-Mac',
    'Macadamia',
    '695',
    2.0,
    10,
    217,           -- 217.5 from upload, truncated to fit int column
    't NIS/ha',
    'micro',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND name = '1C-Mac'
      AND deleted_at IS NULL
);

-- ── 4. Postcondition checks ──────────────────────────────────────────
DO $$
DECLARE
    grapefruit_count INT;
    valencia_count INT;
    mac_1c_exists BOOLEAN;
    parent_citrus_remaining INT;
BEGIN
    SELECT COUNT(*) INTO grapefruit_count
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND crop = 'Citrus (Grapefruit)'
      AND deleted_at IS NULL;

    SELECT COUNT(*) INTO valencia_count
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND crop = 'Citrus (Valencia)'
      AND deleted_at IS NULL;

    SELECT EXISTS(
        SELECT 1 FROM public.fields
        WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
          AND name = '1C-Mac'
          AND crop = 'Macadamia'
          AND deleted_at IS NULL
    ) INTO mac_1c_exists;

    SELECT COUNT(*) INTO parent_citrus_remaining
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND crop = 'Citrus'
      AND deleted_at IS NULL;

    RAISE NOTICE 'Laborie post-fix: Citrus (Grapefruit)=%, Citrus (Valencia)=%, Mac 1C-Mac present=%, parent Citrus remaining=%',
        grapefruit_count, valencia_count, mac_1c_exists, parent_citrus_remaining;

    IF grapefruit_count <> 2 THEN
        RAISE EXCEPTION 'Expected 2 Citrus (Grapefruit) rows on Laborie, got %', grapefruit_count;
    END IF;
    IF valencia_count <> 12 THEN
        RAISE EXCEPTION 'Expected 12 Citrus (Valencia) rows on Laborie, got %', valencia_count;
    END IF;
    IF NOT mac_1c_exists THEN
        RAISE EXCEPTION 'Mac 1C-Mac block missing after migration';
    END IF;
    IF parent_citrus_remaining <> 0 THEN
        RAISE EXCEPTION 'Still % parent "Citrus" rows on Laborie — should be 0', parent_citrus_remaining;
    END IF;
END $$;

COMMIT;
