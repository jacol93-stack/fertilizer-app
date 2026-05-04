-- ============================================================
-- 099: Laborie — rename block 'c' → '10A' + import its leaf analysis
-- ============================================================
-- The agronomist re-uploaded sapling-fields-template.xlsx with block
-- 'c' renamed to '10A'. Same crop (Citrus Star Ruby = Grapefruit),
-- same area (4 ha), same age (19), same pop (470). Only the block
-- name changed.
--
-- This also fills the lab-analysis gap: NviroTek WO 197378:251823
-- sample L14-9064 was skipped in migration 098 because no '10A' field
-- existed at the time. Now that the block has its proper name, that
-- row goes in.
-- ============================================================

BEGIN;

-- ── 1. Rename c → 10A ─────────────────────────────────────────────
UPDATE public.fields
SET name = '10A'
WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND name = 'c'
  AND deleted_at IS NULL;

-- ── 2. Add the missing lab analysis (sample L14-9064) ─────────────
-- Idempotent: skip if a NviroTek 2026-03-10 row for this field already exists.
INSERT INTO public.leaf_analyses (
    agent_id, client_id, farm_id, field_id, crop, sample_part,
    sample_date, lab_name, values, status, notes
)
SELECT
    '4c9f4275-2e4c-4032-9d74-8a2db77eeea6'::uuid,
    'd11c1f53-4d06-4141-b632-7d8bebf3d0dc'::uuid,
    '5264f5c4-d9f9-450a-a884-5bb735b88c21'::uuid,
    f.id,
    f.crop,
    'recently matured leaf',
    '2026-03-10'::date,
    'NviroTek Labs',
    '{"N": 2.31, "Ca": 4.08, "Mg": 0.41, "K": 1.93, "Na": 866, "S": 0.44, "P": 0.19, "Fe": 272, "Mn": 167, "Cu": 430, "Zn": 41, "B": 188}'::jsonb,
    'saved',
    'NviroTek WO 197378:251823 sample L14-9064 (Blok 10A). Mo <1 mg/kg (below LOD) — stored as null. Sample dried at 60 deg C; leaves could not be washed — Cu reading is surface spray residue (430 mg/kg vs FERTASA Citrus sufficient 5-20). Fe (272) borderline — possibly small residue layer over real internal Fe.'
FROM public.fields f
WHERE f.farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
  AND f.name = '10A'
  AND f.deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM public.leaf_analyses la
      WHERE la.field_id = f.id
        AND la.sample_date = '2026-03-10'::date
        AND la.lab_name = 'NviroTek Labs'
        AND la.deleted_at IS NULL
  );

-- ── 3. Verify ─────────────────────────────────────────────────────
DO $$
DECLARE
    has_10a BOOLEAN;
    has_c BOOLEAN;
    leaf_count_10a INT;
    total_leaf_count INT;
BEGIN
    SELECT EXISTS(SELECT 1 FROM public.fields
        WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
          AND name = '10A' AND deleted_at IS NULL) INTO has_10a;
    SELECT EXISTS(SELECT 1 FROM public.fields
        WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
          AND name = 'c' AND deleted_at IS NULL) INTO has_c;
    SELECT COUNT(*) INTO leaf_count_10a
    FROM public.leaf_analyses la
    JOIN public.fields f ON la.field_id = f.id
    WHERE f.farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND f.name = '10A'
      AND la.sample_date = '2026-03-10'
      AND la.lab_name = 'NviroTek Labs'
      AND la.deleted_at IS NULL;
    SELECT COUNT(*) INTO total_leaf_count
    FROM public.leaf_analyses
    WHERE farm_id = '5264f5c4-d9f9-450a-a884-5bb735b88c21'
      AND sample_date = '2026-03-10'
      AND lab_name = 'NviroTek Labs'
      AND deleted_at IS NULL;

    RAISE NOTICE 'Laborie post-rename: 10A exists=%, c exists=%, 10A leaf rows=%, total leaf rows for batch=%',
        has_10a, has_c, leaf_count_10a, total_leaf_count;

    IF NOT has_10a THEN
        RAISE EXCEPTION 'Block 10A not present after rename';
    END IF;
    IF has_c THEN
        RAISE EXCEPTION 'Block c still present after rename';
    END IF;
    IF leaf_count_10a <> 1 THEN
        RAISE EXCEPTION 'Expected 1 leaf row for 10A, got %', leaf_count_10a;
    END IF;
    IF total_leaf_count <> 25 THEN
        RAISE EXCEPTION 'Expected 25 total Laborie leaf rows for 2026-03-10, got %', total_leaf_count;
    END IF;
END $$;

COMMIT;
