-- Add blend_type and liquid-specific columns to blends table
ALTER TABLE blends ADD COLUMN IF NOT EXISTS blend_type TEXT NOT NULL DEFAULT 'dry';
ALTER TABLE blends ADD COLUMN IF NOT EXISTS tank_volume_l NUMERIC;
ALTER TABLE blends ADD COLUMN IF NOT EXISTS sg_estimate NUMERIC;
ALTER TABLE blends ADD COLUMN IF NOT EXISTS mixing_instructions JSONB;

-- Add liquid material defaults column to default_materials
ALTER TABLE default_materials ADD COLUMN IF NOT EXISTS liquid_materials JSONB DEFAULT '[]'::jsonb;
