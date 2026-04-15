-- ============================================================
-- Phase 5: Liquid Blend + Foliar Spray support
-- Adds liquid properties to materials, creates product catalog
-- ============================================================

-- Add liquid/foliar columns to existing materials table
ALTER TABLE materials ADD COLUMN IF NOT EXISTS form TEXT DEFAULT 'solid';  -- solid, liquid, chelate
ALTER TABLE materials ADD COLUMN IF NOT EXISTS liquid_compatible BOOLEAN DEFAULT false;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS foliar_compatible BOOLEAN DEFAULT false;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS solubility_20c NUMERIC;     -- g/L at 20C
ALTER TABLE materials ADD COLUMN IF NOT EXISTS sg NUMERIC;                  -- specific gravity
ALTER TABLE materials ADD COLUMN IF NOT EXISTS ph_effect TEXT;              -- acidifying, alkalizing, neutral
ALTER TABLE materials ADD COLUMN IF NOT EXISTS mixing_order INTEGER;        -- 1=first (acids), 10=last (Ca salts)
ALTER TABLE materials ADD COLUMN IF NOT EXISTS mixing_notes TEXT;

-- Material compatibility (which pairs can/cannot be tank-mixed)
CREATE TABLE IF NOT EXISTS material_compatibility (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_a      TEXT NOT NULL,
    material_b      TEXT NOT NULL,
    compatible      BOOLEAN NOT NULL DEFAULT true,
    severity        TEXT DEFAULT 'safe',   -- safe, caution, incompatible
    reason          TEXT,
    UNIQUE(material_a, material_b)
);

ALTER TABLE material_compatibility ENABLE ROW LEVEL SECURITY;
CREATE POLICY "material_compat_select" ON material_compatibility FOR SELECT TO authenticated USING (true);
CREATE POLICY "material_compat_service" ON material_compatibility FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Liquid/foliar product catalog (the 42 commercial products)
CREATE TABLE IF NOT EXISTS liquid_products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL UNIQUE,
    product_type    TEXT NOT NULL,          -- foliar, fertigation, hydroponic
    batch_size_kg   NUMERIC,               -- recipe batch size in kg
    batch_size_l    NUMERIC,               -- recipe batch size in litres
    sg              NUMERIC,               -- specific gravity
    -- Nutrient analysis in g/kg (dry) or g/L (liquid)
    analysis_unit   TEXT DEFAULT 'g/kg',   -- g/kg or g/l
    n               NUMERIC DEFAULT 0,
    p               NUMERIC DEFAULT 0,
    k               NUMERIC DEFAULT 0,
    ca              NUMERIC DEFAULT 0,
    mg              NUMERIC DEFAULT 0,
    s               NUMERIC DEFAULT 0,
    fe              NUMERIC DEFAULT 0,     -- in mg/kg or mg/l
    b               NUMERIC DEFAULT 0,
    mn              NUMERIC DEFAULT 0,
    zn              NUMERIC DEFAULT 0,
    mo              NUMERIC DEFAULT 0,
    cu              NUMERIC DEFAULT 0,
    cl              NUMERIC DEFAULT 0,
    -- Recipe (raw materials)
    recipe          JSONB,                 -- [{material, kg, notes}]
    -- Application
    target_crops    TEXT[],                -- crops this is designed for
    dilution_rate   TEXT,                  -- e.g. "5 L per 100 L water"
    spray_volume_l_ha NUMERIC,            -- typical spray volume L/ha
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE liquid_products ENABLE ROW LEVEL SECURITY;
CREATE POLICY "liquid_products_select" ON liquid_products FOR SELECT TO authenticated USING (true);
CREATE POLICY "liquid_products_service" ON liquid_products FOR ALL TO service_role USING (true) WITH CHECK (true);

COMMENT ON TABLE liquid_products IS 'Commercial foliar spray and liquid fertilizer product catalog with formulas';
COMMENT ON TABLE material_compatibility IS 'Tank-mix compatibility matrix for liquid materials';
