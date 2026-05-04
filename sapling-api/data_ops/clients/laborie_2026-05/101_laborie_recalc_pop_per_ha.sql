-- ============================================================
-- 101: Laborie — recalc pop_per_ha from Boordsensus 2025 source
-- ============================================================
-- The original bulk-import computed pop_per_ha as Qty / 4 (constant
-- divisor) instead of Qty / Ha. Where Ha = 4 the values coincidentally
-- matched; everywhere else they were wrong by 13–150%.
--
-- This migration aligns pop_per_ha with the August 2025 Boordsensus
-- source (Laborie 515 LT Gedeeltes 3 & 4):
--   pop_per_ha = round(Qty / Ha)
--
-- Engine impact: target_computation density-scales the per-ha target
-- by block_pop_per_ha ÷ reference_pop_per_ha. With wrong pops, half
-- the blocks were being under-targeted and the other half over-
-- targeted. This fix is a prerequisite for accurate programme builds.
--
-- Source: 2025 Boordsensus Laborie Ged 3 en 4.xlsx (Aug 2025).
-- ============================================================

BEGIN;

UPDATE public.fields f
SET pop_per_ha = src.pop
FROM (VALUES
    -- Citrus (14 blocks)
    ('10A', 470),  -- 1880 / 4.0
    ('10B', 400),  -- 1600 / 4.0
    ('4A',  290),  --  754 / 2.6
    ('4B',  201),  --  602 / 3.0
    ('4C',  250),  --  750 / 3.0
    ('4D',  283),  --  850 / 3.0
    ('7A',  381),  -- 1142 / 3.0
    ('7B',  444),  -- 1331 / 3.0
    ('6A',  400),  -- 2200 / 5.5
    ('9A',  382),  -- 2100 / 5.5
    ('8B',  455),  --  455 / 1.0
    ('1C',  435),  --  870 / 2.0
    ('5C',  446),  -- 1560 / 3.5
    ('12',  448),  -- 2556 / 5.71
    -- Macadamia Gedeelte 3 (8 blocks)
    ('5A',  343),  -- 2400 / 7.0
    ('1A',  252),  -- 1008 / 4.0
    ('1B',  280),  --  560 / 2.0
    ('2A',  421),  --  421 / 1.0
    ('2B',  404),  --  807 / 2.0
    ('7C2', 369),  --  369 / 1.0
    ('7C3', 261),  --  652 / 2.5
    ('7C1', 266),  --  532 / 2.0
    -- Macadamia Gedeelte 4 (15 blocks)
    ('8',   286),  -- 2863 / 10.0
    ('11',  350),  -- 2450 / 7.0
    ('13',  251),  -- 1755 / 7.0
    ('1',   300),  -- 1200 / 4.0
    ('2',   310),  --  620 / 2.0
    ('15',  280),  --  700 / 2.5
    ('17',  288),  -- 1008 / 3.5
    ('3',   310),  --  620 / 2.0
    ('4',   297),  --  475 / 1.6
    ('5',   301),  --  511 / 1.7
    ('6',   294),  --  587 / 2.0
    ('7',   274),  --  547 / 2.0
    ('9',   245),  --  638 / 2.6
    ('10',  271),  -- 1764 / 6.5
    ('14',  250)   -- 1650 / 6.6
) AS src(name, pop)
WHERE f.farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND f.deleted_at IS NULL
  AND f.name = src.name;

DO $$
DECLARE
    matched_count INT;
    active_count INT;
BEGIN
    SELECT COUNT(*) INTO active_count
    FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND deleted_at IS NULL;

    -- Spot-check a handful of post-fix values
    PERFORM 1 FROM public.fields
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND deleted_at IS NULL
      AND ((name = '8'  AND pop_per_ha = 286)
        OR (name = '8B' AND pop_per_ha = 455)
        OR (name = '12' AND pop_per_ha = 448)
        OR (name = '1C' AND pop_per_ha = 435))
    HAVING COUNT(*) = 4;
    GET DIAGNOSTICS matched_count = ROW_COUNT;

    RAISE NOTICE 'Laborie pop_per_ha recalc: active blocks=%, spot-check matched=%',
        active_count, matched_count;

    IF active_count <> 37 THEN
        RAISE EXCEPTION 'Expected 37 active blocks, got %', active_count;
    END IF;
    IF matched_count <> 1 THEN
        RAISE EXCEPTION 'Spot-check failed — at least one of {8, 8B, 12, 1C} did not get its expected pop_per_ha';
    END IF;
END $$;

COMMIT;
