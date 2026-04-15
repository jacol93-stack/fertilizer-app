-- Add storage references to lab_templates for OCR training data
-- Files stored in Supabase Storage bucket 'lab-reports'

ALTER TABLE lab_templates ADD COLUMN IF NOT EXISTS layout_data JSONB;  -- column positions, header locations, table structure
ALTER TABLE lab_templates ADD COLUMN IF NOT EXISTS sample_files TEXT[] DEFAULT '{}';  -- array of storage paths

-- Create storage bucket (if not exists — safe to run)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'lab-reports',
    'lab-reports',
    false,
    52428800,  -- 50MB limit
    ARRAY['application/pdf', 'image/jpeg', 'image/png', 'image/webp']
)
ON CONFLICT (id) DO NOTHING;

-- Storage policies: authenticated users can upload, service role can read all
CREATE POLICY "lab_reports_upload" ON storage.objects
    FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'lab-reports');

CREATE POLICY "lab_reports_read" ON storage.objects
    FOR SELECT TO authenticated
    USING (bucket_id = 'lab-reports');

CREATE POLICY "lab_reports_service" ON storage.objects
    FOR ALL TO service_role
    USING (bucket_id = 'lab-reports')
    WITH CHECK (bucket_id = 'lab-reports');
