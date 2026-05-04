-- ============================================================
-- 121: crop_calc_flags schema extension
-- ============================================================
-- Adds 19 columns to crop_calc_flags so engine code can act on
-- agronomic rules that the CropNote prose system already surfaces.
--
-- Until this lands, the engine consumes flags via the artifact's
-- `crop_notes[].kind` strings. These columns make those same flags
-- queryable directly + give the future product selector typed
-- columns to filter blend candidates against.
--
-- 16 boolean flags + 3 numeric ceilings. All nullable booleans
-- default FALSE; numeric ceilings default NULL (= "no cap").
-- ============================================================

BEGIN;

ALTER TABLE public.crop_calc_flags
    -- Boolean behavioural flags
    ADD COLUMN IF NOT EXISTS no_chloride_fertilisers BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS chloride_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS sulfur_critical BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS acid_intolerant BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS acid_obligate BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS salt_tolerant BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS n_fixation_active BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS mo_responsive BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS inoculant_required BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS boron_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS boron_critical_for_set BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS nitrate_form_required BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS photoperiod_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS alternate_bearing_risk BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS ca_quality_critical BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS k_luxury_consumer BOOLEAN NOT NULL DEFAULT FALSE,
    -- Numeric ceilings (NULL = uncapped)
    ADD COLUMN IF NOT EXISTS n_protein_cap_kg_ha NUMERIC,
    ADD COLUMN IF NOT EXISTS n_rate_ceiling_kg_per_ha NUMERIC,
    ADD COLUMN IF NOT EXISTS cec_floor_cmol NUMERIC;

-- Comments — keep schema self-documenting
COMMENT ON COLUMN public.crop_calc_flags.no_chloride_fertilisers IS
    'TRUE = engine must filter KCl/MOP from blend candidates (Kiwi, Avocado, Blueberry, Tobacco — Cl-toxic).';
COMMENT ON COLUMN public.crop_calc_flags.sulfur_critical IS
    'TRUE = engine must enforce minimum S in blend (Garlic, Cabbage, Canola — S drives yield + quality).';
COMMENT ON COLUMN public.crop_calc_flags.boron_sensitive IS
    'TRUE = engine must NOT auto-apply soil B (Dry Bean — toxicity hard cap; FERTASA 5.5.2).';
COMMENT ON COLUMN public.crop_calc_flags.n_fixation_active IS
    'TRUE = engine should not auto-apply starter N beyond a small establishment dose (8 legumes).';
COMMENT ON COLUMN public.crop_calc_flags.acid_obligate IS
    'TRUE = pH > threshold actively damages stand (Rooibos, Honeybush, Blueberry). Engine must not lime.';
COMMENT ON COLUMN public.crop_calc_flags.n_protein_cap_kg_ha IS
    'Hard ceiling for late-season N to protect grain protein (Malting Barley = 80 kg N/ha pre-Z37).';
COMMENT ON COLUMN public.crop_calc_flags.n_rate_ceiling_kg_per_ha IS
    'Total-season N ceiling for quality (Wine Grape Saayman 1995 = 105 kg N/ha for Barlinka colour/sugar).';
COMMENT ON COLUMN public.crop_calc_flags.cec_floor_cmol IS
    'Below this CEC, skip cation-ratio path (Citrus on lowveld sandy soils ~ 4 cmol/kg).';

-- Seed flags for the crops where the CropNote knowledge base
-- already declares them. Keeps the schema in sync with the
-- prose layer so the engine's typed access matches.
--
-- One UPSERT per crop — preserves any existing skip_cation_ratio_path
-- or source_note set in earlier migrations.

INSERT INTO public.crop_calc_flags (
    crop, source, source_section, source_year, tier,
    no_chloride_fertilisers, sulfur_critical, acid_intolerant,
    acid_obligate, salt_tolerant, n_fixation_active, mo_responsive,
    inoculant_required, boron_sensitive, boron_critical_for_set,
    nitrate_form_required, photoperiod_sensitive,
    alternate_bearing_risk, ca_quality_critical, k_luxury_consumer,
    chloride_sensitive,
    n_protein_cap_kg_ha, n_rate_ceiling_kg_per_ha, cec_floor_cmol
) VALUES
    -- Cl-sensitive crops (filter KCl/MOP)
    ('Avocado', 'Köhne 1990 SAAGA + Storey & Walker 1999', '5.7.1', 1990, 1,
     TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, TRUE,
     NULL, NULL, NULL),
    ('Tobacco', 'FERTASA 5.11', '5.11', 2017, 1,
     TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     TRUE, FALSE, FALSE, FALSE, FALSE, TRUE,
     NULL, NULL, NULL),
    ('Tobacco (Flue-cured)', 'FERTASA 5.11', '5.11', 2017, 1,
     TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     TRUE, FALSE, FALSE, FALSE, FALSE, TRUE,
     NULL, NULL, NULL),
    ('Tobacco (Burley)', 'FERTASA 5.11', '5.11', 2017, 1,
     TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     TRUE, FALSE, FALSE, FALSE, FALSE, TRUE,
     NULL, NULL, NULL),
    ('Tobacco (Dark air-cured)', 'FERTASA 5.11', '5.11', 2017, 1,
     TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     TRUE, FALSE, FALSE, FALSE, FALSE, TRUE,
     NULL, NULL, NULL),
    ('Tobacco (Light air-cured)', 'FERTASA 5.11', '5.11', 2017, 1,
     TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     TRUE, FALSE, FALSE, FALSE, FALSE, TRUE,
     NULL, NULL, NULL),

    -- High-S crops
    ('Garlic', 'Nguyen 2022 + Reddy 2017', '5.6.1', 2022, 2,
     FALSE, TRUE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, TRUE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Cabbage', 'UF/IFAS HS964 + Starke Ayres 2019', '5.6.1', 2019, 2,
     FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Canola', 'FERTASA 5.5.1 + Hardy 2014', '5.5.1', 2017, 1,
     FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),

    -- Acid-obligate crops
    ('Rooibos', 'SARC 2020 + Hawkins & Lambers 2011', '5.x', 2020, 1,
     FALSE, FALSE, TRUE, TRUE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Honeybush', 'DAFF Honeybush Production Guide 2019', '5.x', 2019, 1,
     FALSE, FALSE, TRUE, TRUE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),

    -- N-fixing legumes (don't auto-apply N)
    ('Soybean', 'FERTASA 5.5.5 + Grain SA Soybean Guide 2019', '5.5.5', 2017, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, TRUE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Bean (Dry)', 'FERTASA 5.5.2 + ARC-GCI Drybean Manual', '5.5.2', 2017, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, TRUE, TRUE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Bean (Green)', 'FERTASA 5.6.1 + UF/IFAS HS725', '5.6.1', 2017, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Groundnut', 'FERTASA 5.5.3 + Manson 2013 SAJPS', '5.5.3', 2017, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, TRUE, FALSE, FALSE,
     FALSE, FALSE, FALSE, TRUE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Lentils', 'GRDC GrowNote Lentil + ICARDA 2009', '5.5.4', 2017, 2,
     FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, TRUE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Pea', 'GRDC GrowNote Field Pea + AHDB UK', 'n/a', 2018, 2,
     FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, TRUE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Pea (Green)', 'DAFF Vegetable Production Guide + UF/IFAS HS725', '5.6.1', 2011, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, FALSE, FALSE, TRUE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Lucerne', 'FERTASA 5.12.2', '5.12.2', 2017, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, TRUE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, TRUE, FALSE,
     NULL, NULL, NULL),

    -- Salt-tolerant crops (high Na/Cl tolerance)
    ('Pomegranate', 'Holland 2009 Hort Reviews 35 + Day & Wilkins 2011', 'n/a', 2009, 2,
     FALSE, FALSE, FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Fig', 'FAO Salinity Handbook 1985 + Yara Fig', 'n/a', 1985, 2,
     FALSE, FALSE, FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Beetroot', 'UC ANR Beet Production', 'n/a', 2018, 2,
     FALSE, FALSE, FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Asparagus', 'FERTASA 5.6.3 + UMN Asparagus', '5.6.3', 2017, 1,
     FALSE, FALSE, FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),

    -- Photoperiod-sensitive
    ('Onion', 'DAFF Onion Production Guide + Starke Ayres 2019', 'n/a', 2019, 1,
     FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, TRUE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),

    -- Quality-critical Ca crops
    ('Tomato', 'UF/IFAS HS739 + UC ANR', 'HS739', 2024, 2,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, TRUE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Pepper (Bell)', 'UF/IFAS HS732', 'HS732', 2024, 2,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, TRUE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Lettuce', 'UC ANR Lettuce Production', 'n/a', 2018, 2,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, TRUE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Apple', 'Cheng 2013 Cornell + Lötze SA', 'n/a', 2013, 2,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, TRUE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Pear', 'NSW DPI Primefact 85 + Cornell Pear', 'n/a', 2024, 2,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, TRUE, FALSE, FALSE,
     NULL, NULL, NULL),

    -- Alternate-bearing risk
    ('Persimmon', 'George 1997 Acta Hort 436', 'n/a', 1997, 3,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, TRUE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Mango', 'Mudo et al. 2020 + Pretest 2008 Acta Hort 509', 'n/a', 2020, 3,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE,
     FALSE, FALSE, TRUE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),
    ('Litchi', 'Stassen 2007 + ALGA Lychee Field Guide', 'n/a', 2007, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, TRUE, FALSE, FALSE, FALSE,
     NULL, NULL, NULL),

    -- K luxury consumers
    ('Banana', 'Haifa Banana + IFA 1992', 'n/a', 2017, 2,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, TRUE, FALSE,
     NULL, NULL, NULL),

    -- Numeric ceilings
    ('Barley', 'SAB Maltings + ARC-SGI Barley Guideline', 'n/a', 2017, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     80, NULL, NULL),
    ('Wine Grape', 'Saayman & Lambrechts 1995 SAJEV 16(2)', 'n/a', 1995, 3,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, 105, NULL),
    ('Citrus', 'ARC-ISCW lowveld sandy soil baseline + FAO Y5998E', 'n/a', 2016, 1,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     FALSE, FALSE, FALSE, FALSE, FALSE, FALSE,
     NULL, NULL, 4)
ON CONFLICT (crop) DO UPDATE SET
    no_chloride_fertilisers = EXCLUDED.no_chloride_fertilisers,
    chloride_sensitive = EXCLUDED.chloride_sensitive,
    sulfur_critical = EXCLUDED.sulfur_critical,
    acid_intolerant = EXCLUDED.acid_intolerant,
    acid_obligate = EXCLUDED.acid_obligate,
    salt_tolerant = EXCLUDED.salt_tolerant,
    n_fixation_active = EXCLUDED.n_fixation_active,
    mo_responsive = EXCLUDED.mo_responsive,
    inoculant_required = EXCLUDED.inoculant_required,
    boron_sensitive = EXCLUDED.boron_sensitive,
    boron_critical_for_set = EXCLUDED.boron_critical_for_set,
    nitrate_form_required = EXCLUDED.nitrate_form_required,
    photoperiod_sensitive = EXCLUDED.photoperiod_sensitive,
    alternate_bearing_risk = EXCLUDED.alternate_bearing_risk,
    ca_quality_critical = EXCLUDED.ca_quality_critical,
    k_luxury_consumer = EXCLUDED.k_luxury_consumer,
    n_protein_cap_kg_ha = EXCLUDED.n_protein_cap_kg_ha,
    n_rate_ceiling_kg_per_ha = EXCLUDED.n_rate_ceiling_kg_per_ha,
    cec_floor_cmol = EXCLUDED.cec_floor_cmol,
    source = EXCLUDED.source,
    source_section = EXCLUDED.source_section,
    source_year = EXCLUDED.source_year,
    tier = EXCLUDED.tier,
    updated_at = NOW();

COMMIT;
