-- 085_default_cluster_margin.sql
--
-- App-wide cluster margin default lives on default_materials (the same
-- admin-managed config row that holds materials list, compost min %,
-- variability margin, etc.). Non-admin wizard users always run on this
-- value; admins can override per-build via the ClusterBoard dropdown.

ALTER TABLE default_materials
  ADD COLUMN IF NOT EXISTS cluster_margin_default NUMERIC DEFAULT 0.25;

COMMENT ON COLUMN default_materials.cluster_margin_default IS
  'App-wide default NPK-ratio L1 distance threshold for clustering blocks. Non-admin users always use this value; admins can override per-build via the wizard ClusterBoard dropdown.';
