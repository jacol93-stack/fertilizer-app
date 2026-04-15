-- ============================================================
-- Seed Script: Test data for Sapling Blend Calculator
-- Run in Supabase SQL Editor
-- ============================================================

DO $$
DECLARE
  v_agent_id UUID;
  -- Client IDs
  c_bosveld UUID;
  c_limpopo UUID;
  c_highveld UUID;
  c_karoo UUID;
  c_kwazulu UUID;
  -- Farm IDs
  f_bosveld_north UUID;
  f_bosveld_south UUID;
  f_limpopo_avo UUID;
  f_limpopo_citrus UUID;
  f_limpopo_mac UUID;
  f_highveld_grain UUID;
  f_highveld_veg UUID;
  f_karoo_olives UUID;
  f_karoo_grapes UUID;
  f_kwazulu_sugar UUID;
  f_kwazulu_banana UUID;
  -- Field IDs
  fd_bn_1 UUID; fd_bn_2 UUID; fd_bn_3 UUID;
  fd_bs_1 UUID; fd_bs_2 UUID;
  fd_la_1 UUID; fd_la_2 UUID; fd_la_3 UUID;
  fd_lc_1 UUID; fd_lc_2 UUID;
  fd_lm_1 UUID; fd_lm_2 UUID;
  fd_hg_1 UUID; fd_hg_2 UUID; fd_hg_3 UUID;
  fd_hv_1 UUID; fd_hv_2 UUID;
  fd_ko_1 UUID; fd_ko_2 UUID;
  fd_kg_1 UUID; fd_kg_2 UUID;
  fd_ks_1 UUID; fd_ks_2 UUID; fd_ks_3 UUID;
  fd_kb_1 UUID; fd_kb_2 UUID;
BEGIN
  -- Get agent ID (Jaco)
  SELECT id INTO v_agent_id FROM profiles WHERE email = 'jaco@saplingfertilizer.co.za' LIMIT 1;
  IF v_agent_id IS NULL THEN
    SELECT id INTO v_agent_id FROM profiles WHERE role = 'admin' LIMIT 1;
  END IF;
  IF v_agent_id IS NULL THEN
    RAISE EXCEPTION 'No agent found. Create a user first.';
  END IF;

  RAISE NOTICE 'Using agent_id: %', v_agent_id;

  -- ════════════════════════════════════════════════════════════
  -- CLIENTS
  -- ════════════════════════════════════════════════════════════

  INSERT INTO clients (id, agent_id, name, contact_person, email, phone, notes)
  VALUES
    (gen_random_uuid(), v_agent_id, 'Bosveld Boerdery', 'Piet van der Merwe', 'piet@bosveld.co.za', '082 555 1234', 'Large mixed farm in Limpopo. Avocados and macadamias main crops.')
  RETURNING id INTO c_bosveld;

  INSERT INTO clients (id, agent_id, name, contact_person, email, phone, notes)
  VALUES
    (gen_random_uuid(), v_agent_id, 'Limpopo Tropicals', 'Johan Steyn', 'johan@limpotropics.co.za', '083 444 5678', 'Specializes in tropical fruit. Expanding into new avocado blocks.')
  RETURNING id INTO c_limpopo;

  INSERT INTO clients (id, agent_id, name, contact_person, email, phone, notes)
  VALUES
    (gen_random_uuid(), v_agent_id, 'Highveld Agri', 'Francois du Plessis', 'francois@highveldagri.co.za', '071 333 9012', 'Grain and vegetable producer. Mpumalanga region.')
  RETURNING id INTO c_highveld;

  INSERT INTO clients (id, agent_id, name, contact_person, email, phone, notes)
  VALUES
    (gen_random_uuid(), v_agent_id, 'Karoo Estates', 'Anna Olivier', 'anna@karooestates.co.za', '084 222 3456', 'Wine grapes and table olives. Western Cape.')
  RETURNING id INTO c_karoo;

  INSERT INTO clients (id, agent_id, name, contact_person, email, phone, notes)
  VALUES
    (gen_random_uuid(), v_agent_id, 'KwaZulu Growers', 'Thabo Dlamini', 'thabo@kzgrowers.co.za', '072 111 7890', 'Sugarcane and banana production. North Coast KZN.')
  RETURNING id INTO c_kwazulu;

  -- ════════════════════════════════════════════════════════════
  -- FARMS
  -- ════════════════════════════════════════════════════════════

  -- Bosveld Boerdery farms
  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_bosveld, 'Bosveld North', 'Tzaneen', 'Main avo block, established 2015')
  RETURNING id INTO f_bosveld_north;

  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_bosveld, 'Bosveld South', 'Hazyview', 'Macadamia and new plantings')
  RETURNING id INTO f_bosveld_south;

  -- Limpopo Tropicals farms
  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_limpopo, 'Avocado Estate', 'Levubu', 'Premium Hass avocados')
  RETURNING id INTO f_limpopo_avo;

  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_limpopo, 'Citrus Valley', 'Letsitele', 'Valencia and Navel oranges')
  RETURNING id INTO f_limpopo_citrus;

  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_limpopo, 'Mac Ridge', 'Levubu', 'Beaumont and 816 cultivars')
  RETURNING id INTO f_limpopo_mac;

  -- Highveld Agri farms
  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_highveld, 'Grain Fields', 'Ermelo', 'Maize and soybean rotation')
  RETURNING id INTO f_highveld_grain;

  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_highveld, 'Veggie Valley', 'Nelspruit', 'Potato and tomato production')
  RETURNING id INTO f_highveld_veg;

  -- Karoo Estates farms
  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_karoo, 'Olive Grove', 'Paarl', 'Mission and Kalamata varieties')
  RETURNING id INTO f_karoo_olives;

  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_karoo, 'Vineyard Hills', 'Stellenbosch', 'Cabernet and Shiraz blocks')
  RETURNING id INTO f_karoo_grapes;

  -- KwaZulu Growers farms
  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_kwazulu, 'Sugar Plains', 'Tongaat', 'NCo376 sugarcane')
  RETURNING id INTO f_kwazulu_sugar;

  INSERT INTO farms (id, client_id, name, region, notes)
  VALUES (gen_random_uuid(), c_kwazulu, 'Banana Belt', 'Port Edward', 'Williams and Grand Nain')
  RETURNING id INTO f_kwazulu_banana;

  -- ════════════════════════════════════════════════════════════
  -- FIELDS
  -- ════════════════════════════════════════════════════════════

  -- Bosveld North fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_bosveld_north, 'Block A - Hass', 12.5, 'Sandy loam') RETURNING id INTO fd_bn_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_bosveld_north, 'Block B - Fuerte', 8.0, 'Clay loam') RETURNING id INTO fd_bn_2;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_bosveld_north, 'Block C - New Hass', 15.0, 'Sandy loam') RETURNING id INTO fd_bn_3;

  -- Bosveld South fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_bosveld_south, 'Mac Block 1', 10.0, 'Red clay') RETURNING id INTO fd_bs_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_bosveld_south, 'Mac Block 2', 7.5, 'Red clay') RETURNING id INTO fd_bs_2;

  -- Limpopo Avo fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_limpopo_avo, 'Hass A', 20.0, 'Sandy clay loam') RETURNING id INTO fd_la_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_limpopo_avo, 'Hass B', 18.0, 'Sandy clay loam') RETURNING id INTO fd_la_2;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_limpopo_avo, 'Maluma Block', 10.0, 'Clay loam') RETURNING id INTO fd_la_3;

  -- Limpopo Citrus fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_limpopo_citrus, 'Valencia West', 25.0, 'Sandy loam') RETURNING id INTO fd_lc_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_limpopo_citrus, 'Navel East', 15.0, 'Loam') RETURNING id INTO fd_lc_2;

  -- Limpopo Mac fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_limpopo_mac, 'Beaumont Block', 12.0, 'Clay') RETURNING id INTO fd_lm_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_limpopo_mac, '816 Block', 8.0, 'Sandy clay') RETURNING id INTO fd_lm_2;

  -- Highveld Grain fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_highveld_grain, 'Maize Camp 1', 50.0, 'Black turf') RETURNING id INTO fd_hg_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_highveld_grain, 'Maize Camp 2', 45.0, 'Black turf') RETURNING id INTO fd_hg_2;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_highveld_grain, 'Soybean Block', 30.0, 'Sandy loam') RETURNING id INTO fd_hg_3;

  -- Highveld Veggie fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_highveld_veg, 'Potato Field', 8.0, 'Sandy loam') RETURNING id INTO fd_hv_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_highveld_veg, 'Tomato Tunnel', 2.0, 'Compost mix') RETURNING id INTO fd_hv_2;

  -- Karoo Olive fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_karoo_olives, 'Mission Grove', 6.0, 'Sandy') RETURNING id INTO fd_ko_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_karoo_olives, 'Kalamata Block', 4.0, 'Sandy loam') RETURNING id INTO fd_ko_2;

  -- Karoo Grape fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_karoo_grapes, 'Cab Sav Block', 5.0, 'Shale') RETURNING id INTO fd_kg_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_karoo_grapes, 'Shiraz Slope', 3.5, 'Decomposed granite') RETURNING id INTO fd_kg_2;

  -- KwaZulu Sugar fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_kwazulu_sugar, 'Cane A', 40.0, 'Hutton') RETURNING id INTO fd_ks_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_kwazulu_sugar, 'Cane B', 35.0, 'Hutton') RETURNING id INTO fd_ks_2;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_kwazulu_sugar, 'Cane C - replant', 20.0, 'Clovelly') RETURNING id INTO fd_ks_3;

  -- KwaZulu Banana fields
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_kwazulu_banana, 'Williams Block', 6.0, 'Alluvial') RETURNING id INTO fd_kb_1;
  INSERT INTO fields (id, farm_id, name, size_ha, soil_type) VALUES
    (gen_random_uuid(), f_kwazulu_banana, 'Grand Nain Block', 4.0, 'Alluvial') RETURNING id INTO fd_kb_2;

  -- ════════════════════════════════════════════════════════════
  -- SOIL ANALYSES
  -- ════════════════════════════════════════════════════════════

  -- Bosveld North - Block A Hass
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_bosveld, f_bosveld_north, fd_bn_1,
    'Avocado', 'Hass', 15, 't fruit/ha', 400, 'NviroTek', '2026-02-15', 'saved',
    '{"pH(KCl)": 5.8, "P(Bray1)": 28, "K": 180, "Ca": 1250, "Mg": 310, "Na": 15, "Cu": 2.1, "Zn": 3.8, "Mn": 45, "B": 0.6, "Fe": 28, "S": 12, "CEC": 12.5, "Clay%": 22}'::jsonb,
    '{"pH(KCl)": "Optimal", "P(Bray1)": "Optimal", "K": "Optimal", "Ca": "High", "Mg": "Optimal", "Cu": "Optimal", "Zn": "Optimal", "Mn": "High", "B": "Low", "Fe": "Optimal", "S": "Low"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 4.03, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Ideal"},{"ratio_name": "Ca:K", "actual": 6.94, "ideal_min": 5.0, "ideal_max": 8.0, "status": "Ideal"},{"ratio_name": "P:Zn", "actual": 7.37, "ideal_min": 5.0, "ideal_max": 10.0, "status": "Ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 8.0, "Base_Req_kg_ha": 120.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 120.0},{"Nutrient": "P", "Per_Unit": 1.0, "Base_Req_kg_ha": 15.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 15.0},{"Nutrient": "K", "Per_Unit": 10.0, "Base_Req_kg_ha": 150.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 150.0},{"Nutrient": "Ca", "Per_Unit": 1.5, "Base_Req_kg_ha": 22.5, "Classification": "High", "Factor": 0.75, "Target_kg_ha": 16.9},{"Nutrient": "Mg", "Per_Unit": 1.0, "Base_Req_kg_ha": 15.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 15.0},{"Nutrient": "S", "Per_Unit": 0.6, "Base_Req_kg_ha": 9.0, "Classification": "Low", "Factor": 1.5, "Target_kg_ha": 13.5}]'::jsonb,
    'Bosveld Boerdery', 'Bosveld North', 'Block A - Hass', 8500);

  -- Bosveld North - Block B Fuerte
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_bosveld, f_bosveld_north, fd_bn_2,
    'Avocado', 'Fuerte', 12, 't fruit/ha', 400, 'NviroTek', '2026-02-15', 'saved',
    '{"pH(KCl)": 5.2, "P(Bray1)": 15, "K": 140, "Ca": 850, "Mg": 280, "Na": 20, "Cu": 1.5, "Zn": 2.1, "Mn": 38, "B": 0.4, "Fe": 35, "S": 8, "CEC": 10.2, "Clay%": 28}'::jsonb,
    '{"pH(KCl)": "Low", "P(Bray1)": "Low", "K": "Low", "Ca": "Optimal", "Mg": "Optimal", "Cu": "Optimal", "Zn": "Low", "Mn": "Optimal", "B": "Very Low", "Fe": "Optimal", "S": "Very Low"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 3.04, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Ideal"},{"ratio_name": "Ca:K", "actual": 6.07, "ideal_min": 5.0, "ideal_max": 8.0, "status": "Ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 8.0, "Base_Req_kg_ha": 96.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 96.0},{"Nutrient": "P", "Per_Unit": 1.0, "Base_Req_kg_ha": 12.0, "Classification": "Low", "Factor": 1.5, "Target_kg_ha": 18.0},{"Nutrient": "K", "Per_Unit": 10.0, "Base_Req_kg_ha": 120.0, "Classification": "Low", "Factor": 1.5, "Target_kg_ha": 180.0}]'::jsonb,
    'Bosveld Boerdery', 'Bosveld North', 'Block B - Fuerte', 11200);

  -- Bosveld South - Mac Block 1
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_bosveld, f_bosveld_south, fd_bs_1,
    'Macadamia', 'Beaumont', 4, 't NIS/ha', 312, 'SGS', '2026-01-20', 'saved',
    '{"pH(KCl)": 5.5, "P(Bray1)": 22, "K": 160, "Ca": 1100, "Mg": 350, "Na": 18, "Cu": 1.8, "Zn": 3.2, "Mn": 52, "B": 0.8, "Fe": 32, "S": 14, "CEC": 14.0, "Clay%": 35}'::jsonb,
    '{"pH(KCl)": "Optimal", "P(Bray1)": "Optimal", "K": "Optimal", "Ca": "Optimal", "Mg": "Optimal", "Cu": "Optimal", "Zn": "Optimal", "Mn": "High", "B": "Optimal", "Fe": "Optimal", "S": "Optimal"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 3.14, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 6.0, "Base_Req_kg_ha": 24.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 24.0},{"Nutrient": "P", "Per_Unit": 0.8, "Base_Req_kg_ha": 3.2, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 3.2},{"Nutrient": "K", "Per_Unit": 5.0, "Base_Req_kg_ha": 20.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 20.0}]'::jsonb,
    'Bosveld Boerdery', 'Bosveld South', 'Mac Block 1', 4200);

  -- Limpopo Tropicals - Hass A
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_limpopo, f_limpopo_avo, fd_la_1,
    'Avocado', 'Hass', 18, 't fruit/ha', 416, 'NviroTek', '2026-03-01', 'saved',
    '{"pH(KCl)": 6.1, "P(Bray1)": 35, "K": 210, "Ca": 1450, "Mg": 380, "Na": 12, "Cu": 2.5, "Zn": 4.5, "Mn": 40, "B": 0.9, "Fe": 25, "S": 16, "CEC": 15.0, "Clay%": 25}'::jsonb,
    '{"pH(KCl)": "Optimal", "P(Bray1)": "High", "K": "High", "Ca": "High", "Mg": "Optimal", "Cu": "Optimal", "Zn": "Optimal", "Mn": "Optimal", "B": "Optimal", "Fe": "Optimal", "S": "Optimal"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 3.82, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Ideal"},{"ratio_name": "Ca:K", "actual": 6.9, "ideal_min": 5.0, "ideal_max": 8.0, "status": "Ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 8.0, "Base_Req_kg_ha": 144.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 144.0},{"Nutrient": "P", "Per_Unit": 1.0, "Base_Req_kg_ha": 18.0, "Classification": "High", "Factor": 0.75, "Target_kg_ha": 13.5},{"Nutrient": "K", "Per_Unit": 10.0, "Base_Req_kg_ha": 180.0, "Classification": "High", "Factor": 0.75, "Target_kg_ha": 135.0}]'::jsonb,
    'Limpopo Tropicals', 'Avocado Estate', 'Hass A', 9800);

  -- Limpopo Tropicals - Valencia West
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_limpopo, f_limpopo_citrus, fd_lc_1,
    'Citrus', 'Valencia', 40, 't/ha', 500, 'SGS', '2026-02-20', 'saved',
    '{"pH(KCl)": 5.9, "P(Bray1)": 32, "K": 195, "Ca": 1200, "Mg": 290, "Na": 10, "Cu": 2.0, "Zn": 3.5, "Mn": 35, "B": 0.7, "Fe": 30, "S": 11, "CEC": 11.8, "Clay%": 18}'::jsonb,
    '{"pH(KCl)": "Optimal", "P(Bray1)": "Optimal", "K": "Optimal", "Ca": "Optimal", "Mg": "Optimal", "Cu": "Optimal", "Zn": "Optimal", "Mn": "Optimal", "B": "Low", "Fe": "Optimal", "S": "Low"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 4.14, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 3.0, "Base_Req_kg_ha": 120.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 120.0},{"Nutrient": "P", "Per_Unit": 0.4, "Base_Req_kg_ha": 16.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 16.0},{"Nutrient": "K", "Per_Unit": 3.5, "Base_Req_kg_ha": 140.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 140.0}]'::jsonb,
    'Limpopo Tropicals', 'Citrus Valley', 'Valencia West', 7600);

  -- Limpopo Tropicals - Beaumont Block
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_limpopo, f_limpopo_mac, fd_lm_1,
    'Macadamia', 'Beaumont', 5, 't NIS/ha', 278, 'NviroTek', '2026-03-10', 'saved',
    '{"pH(KCl)": 5.4, "P(Bray1)": 18, "K": 145, "Ca": 950, "Mg": 320, "Na": 22, "Cu": 1.6, "Zn": 2.8, "Mn": 48, "B": 0.5, "Fe": 40, "S": 10, "CEC": 13.0, "Clay%": 32}'::jsonb,
    '{"pH(KCl)": "Low", "P(Bray1)": "Optimal", "K": "Low", "Ca": "Optimal", "Mg": "Optimal", "Cu": "Optimal", "Zn": "Low", "Mn": "High", "B": "Low", "Fe": "Optimal", "S": "Low"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 2.97, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Below ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 6.0, "Base_Req_kg_ha": 30.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 30.0},{"Nutrient": "K", "Per_Unit": 5.0, "Base_Req_kg_ha": 25.0, "Classification": "Low", "Factor": 1.5, "Target_kg_ha": 37.5}]'::jsonb,
    'Limpopo Tropicals', 'Mac Ridge', 'Beaumont Block', 5100);

  -- Highveld Agri - Maize Camp 1
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_highveld, f_highveld_grain, fd_hg_1,
    'Maize', 'PAN 5R-589R', 10, 't/ha', 80000, 'NviroTek', '2026-01-10', 'saved',
    '{"pH(KCl)": 5.6, "P(Bray1)": 25, "K": 170, "Ca": 1350, "Mg": 340, "Na": 8, "Cu": 2.2, "Zn": 3.0, "Mn": 42, "B": 0.5, "Fe": 28, "S": 13, "CEC": 18.0, "Clay%": 40}'::jsonb,
    '{"pH(KCl)": "Optimal", "P(Bray1)": "Optimal", "K": "Optimal", "Ca": "Optimal", "Mg": "Optimal", "Cu": "Optimal", "Zn": "Optimal", "Mn": "Optimal", "B": "Low", "Fe": "Optimal", "S": "Optimal"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 3.97, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 22.0, "Base_Req_kg_ha": 220.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 220.0},{"Nutrient": "P", "Per_Unit": 3.5, "Base_Req_kg_ha": 35.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 35.0},{"Nutrient": "K", "Per_Unit": 5.0, "Base_Req_kg_ha": 50.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 50.0}]'::jsonb,
    'Highveld Agri', 'Grain Fields', 'Maize Camp 1', 6800);

  -- Highveld Agri - Potato
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_highveld, f_highveld_veg, fd_hv_1,
    'Potato', 'Mondial', 50, 't/ha', 44000, 'SGS', '2026-02-05', 'saved',
    '{"pH(KCl)": 5.3, "P(Bray1)": 45, "K": 220, "Ca": 980, "Mg": 250, "Na": 12, "Cu": 1.9, "Zn": 4.2, "Mn": 55, "B": 0.8, "Fe": 35, "S": 18, "CEC": 9.5, "Clay%": 15}'::jsonb,
    '{"pH(KCl)": "Low", "P(Bray1)": "High", "K": "High", "Ca": "Optimal", "Mg": "Optimal", "Cu": "Optimal", "Zn": "Optimal", "Mn": "High", "B": "Optimal", "Fe": "Optimal", "S": "Optimal"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 3.92, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 4.0, "Base_Req_kg_ha": 200.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 200.0},{"Nutrient": "P", "Per_Unit": 0.6, "Base_Req_kg_ha": 30.0, "Classification": "High", "Factor": 0.75, "Target_kg_ha": 22.5},{"Nutrient": "K", "Per_Unit": 6.0, "Base_Req_kg_ha": 300.0, "Classification": "High", "Factor": 0.75, "Target_kg_ha": 225.0}]'::jsonb,
    'Highveld Agri', 'Veggie Valley', 'Potato Field', 12500);

  -- KwaZulu - Sugar Cane A
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_kwazulu, f_kwazulu_sugar, fd_ks_1,
    'Sugarcane', 'NCo376', 80, 't cane/ha', 12000, 'SASRI', '2026-03-05', 'saved',
    '{"pH(KCl)": 5.0, "P(Bray1)": 12, "K": 120, "Ca": 750, "Mg": 200, "Na": 25, "Cu": 1.2, "Zn": 1.8, "Mn": 60, "B": 0.3, "Fe": 45, "S": 8, "CEC": 8.5, "Clay%": 20}'::jsonb,
    '{"pH(KCl)": "Very Low", "P(Bray1)": "Low", "K": "Low", "Ca": "Low", "Mg": "Low", "Cu": "Low", "Zn": "Very Low", "Mn": "High", "B": "Very Low", "Fe": "High", "S": "Very Low"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 3.75, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 1.2, "Base_Req_kg_ha": 96.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 96.0},{"Nutrient": "P", "Per_Unit": 0.3, "Base_Req_kg_ha": 24.0, "Classification": "Low", "Factor": 1.5, "Target_kg_ha": 36.0},{"Nutrient": "K", "Per_Unit": 1.5, "Base_Req_kg_ha": 120.0, "Classification": "Low", "Factor": 1.5, "Target_kg_ha": 180.0}]'::jsonb,
    'KwaZulu Growers', 'Sugar Plains', 'Cane A', 5400);

  -- KwaZulu - Banana Williams
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_kwazulu, f_kwazulu_banana, fd_kb_1,
    'Banana', 'Williams', 40, 't/ha', 1800, 'NviroTek', '2026-02-25', 'saved',
    '{"pH(KCl)": 5.7, "P(Bray1)": 30, "K": 250, "Ca": 1100, "Mg": 300, "Na": 15, "Cu": 2.0, "Zn": 3.5, "Mn": 42, "B": 0.7, "Fe": 30, "S": 15, "CEC": 12.0, "Clay%": 22}'::jsonb,
    '{"pH(KCl)": "Optimal", "P(Bray1)": "Optimal", "K": "High", "Ca": "Optimal", "Mg": "Optimal", "Cu": "Optimal", "Zn": "Optimal", "Mn": "Optimal", "B": "Low", "Fe": "Optimal", "S": "Optimal"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 3.67, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 5.0, "Base_Req_kg_ha": 200.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 200.0},{"Nutrient": "P", "Per_Unit": 0.4, "Base_Req_kg_ha": 16.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 16.0},{"Nutrient": "K", "Per_Unit": 18.0, "Base_Req_kg_ha": 720.0, "Classification": "High", "Factor": 0.75, "Target_kg_ha": 540.0}]'::jsonb,
    'KwaZulu Growers', 'Banana Belt', 'Williams Block', 14200);

  -- Karoo - Cab Sav grapes
  INSERT INTO soil_analyses (id, agent_id, client_id, farm_id, field_id, crop, cultivar, yield_target, yield_unit, pop_per_ha, lab_name, analysis_date, status,
    soil_values, classifications, ratio_results, nutrient_targets, customer, farm, field, total_cost_ha)
  VALUES (gen_random_uuid(), v_agent_id, c_karoo, f_karoo_grapes, fd_kg_1,
    'Grapes', 'Cabernet Sauvignon', 10, 't/ha', 3300, 'Bemlab', '2026-01-28', 'saved',
    '{"pH(KCl)": 6.2, "P(Bray1)": 20, "K": 155, "Ca": 1600, "Mg": 280, "Na": 8, "Cu": 3.5, "Zn": 2.8, "Mn": 30, "B": 0.9, "Fe": 22, "S": 10, "CEC": 10.0, "Clay%": 14}'::jsonb,
    '{"pH(KCl)": "Optimal", "P(Bray1)": "Optimal", "K": "Optimal", "Ca": "High", "Mg": "Optimal", "Cu": "High", "Zn": "Optimal", "Mn": "Optimal", "B": "Optimal", "Fe": "Optimal", "S": "Low"}'::jsonb,
    '[{"ratio_name": "Ca:Mg", "actual": 5.71, "ideal_min": 3.0, "ideal_max": 5.0, "status": "Above ideal"}]'::jsonb,
    '[{"Nutrient": "N", "Per_Unit": 5.0, "Base_Req_kg_ha": 50.0, "Classification": "N/A", "Factor": 1.0, "Target_kg_ha": 50.0},{"Nutrient": "P", "Per_Unit": 0.5, "Base_Req_kg_ha": 5.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 5.0},{"Nutrient": "K", "Per_Unit": 4.0, "Base_Req_kg_ha": 40.0, "Classification": "Optimal", "Factor": 1.0, "Target_kg_ha": 40.0}]'::jsonb,
    'Karoo Estates', 'Vineyard Hills', 'Cab Sav Block', 3200);

  -- ════════════════════════════════════════════════════════════
  -- BLENDS
  -- ════════════════════════════════════════════════════════════

  INSERT INTO blends (id, agent_id, client_id, farm_id, field_id, blend_name, batch_size, min_compost_pct, cost_per_ton, selling_price, status, client, farm,
    targets, recipe, nutrients, selected_materials)
  VALUES
    -- Bosveld - Avo blend Block A
    (gen_random_uuid(), v_agent_id, c_bosveld, f_bosveld_north, fd_bn_1,
     'Hass Avo Spring', 1000, 50, 4200, 5800, 'saved', 'Bosveld Boerdery', 'Bosveld North',
     '{"N": 8.0, "P": 1.0, "K": 10.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 120, "pct": 12.0, "cost": 540},{"material": "Urea", "type": "Nitrogen", "kg": 140, "pct": 14.0, "cost": 980},{"material": "MAP", "type": "Phosphorus", "kg": 80, "pct": 8.0, "cost": 720},{"material": "Filler", "type": "Filler", "kg": 160, "pct": 16.0, "cost": 210}]'::jsonb,
     '[{"nutrient": "N", "target": 8.0, "actual": 8.1, "diff": 0.1, "kg_per_ton": 81.0},{"nutrient": "P", "target": 1.0, "actual": 1.05, "diff": 0.05, "kg_per_ton": 10.5},{"nutrient": "K", "target": 10.0, "actual": 9.8, "diff": -0.2, "kg_per_ton": 98.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'Urea', 'MAP', 'Filler']),

    -- Bosveld - Avo blend Block B
    (gen_random_uuid(), v_agent_id, c_bosveld, f_bosveld_north, fd_bn_2,
     'Fuerte Recovery', 1000, 50, 4500, 6200, 'saved', 'Bosveld Boerdery', 'Bosveld North',
     '{"N": 6.0, "P": 2.0, "K": 12.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 150, "pct": 15.0, "cost": 675},{"material": "Urea", "type": "Nitrogen", "kg": 95, "pct": 9.5, "cost": 665},{"material": "MAP", "type": "Phosphorus", "kg": 130, "pct": 13.0, "cost": 1170},{"material": "Filler", "type": "Filler", "kg": 125, "pct": 12.5, "cost": 240}]'::jsonb,
     '[{"nutrient": "N", "target": 6.0, "actual": 6.2, "diff": 0.2, "kg_per_ton": 62.0},{"nutrient": "P", "target": 2.0, "actual": 2.1, "diff": 0.1, "kg_per_ton": 21.0},{"nutrient": "K", "target": 12.0, "actual": 11.8, "diff": -0.2, "kg_per_ton": 118.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'Urea', 'MAP', 'Filler']),

    -- Bosveld - Mac blend
    (gen_random_uuid(), v_agent_id, c_bosveld, f_bosveld_south, fd_bs_1,
     'Mac Maintenance', 1000, 50, 3800, 5200, 'saved', 'Bosveld Boerdery', 'Bosveld South',
     '{"N": 5.0, "P": 1.0, "K": 8.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 95, "pct": 9.5, "cost": 428},{"material": "Urea", "type": "Nitrogen", "kg": 80, "pct": 8.0, "cost": 560},{"material": "MAP", "type": "Phosphorus", "kg": 70, "pct": 7.0, "cost": 630},{"material": "Filler", "type": "Filler", "kg": 255, "pct": 25.5, "cost": 432}]'::jsonb,
     '[{"nutrient": "N", "target": 5.0, "actual": 5.1, "diff": 0.1, "kg_per_ton": 51.0},{"nutrient": "P", "target": 1.0, "actual": 0.95, "diff": -0.05, "kg_per_ton": 9.5},{"nutrient": "K", "target": 8.0, "actual": 7.9, "diff": -0.1, "kg_per_ton": 79.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'Urea', 'MAP', 'Filler']),

    -- Limpopo - Avo premium
    (gen_random_uuid(), v_agent_id, c_limpopo, f_limpopo_avo, fd_la_1,
     'Premium Hass', 1000, 50, 4800, 6500, 'saved', 'Limpopo Tropicals', 'Avocado Estate',
     '{"N": 8.0, "P": 1.0, "K": 9.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 110, "pct": 11.0, "cost": 495},{"material": "Urea", "type": "Nitrogen", "kg": 135, "pct": 13.5, "cost": 945},{"material": "MAP", "type": "Phosphorus", "kg": 75, "pct": 7.5, "cost": 675},{"material": "Calcitic Lime", "type": "Ca Amendment", "kg": 80, "pct": 8.0, "cost": 135},{"material": "Filler", "type": "Filler", "kg": 100, "pct": 10.0, "cost": 800}]'::jsonb,
     '[{"nutrient": "N", "target": 8.0, "actual": 8.0, "diff": 0.0, "kg_per_ton": 80.0},{"nutrient": "P", "target": 1.0, "actual": 1.0, "diff": 0.0, "kg_per_ton": 10.0},{"nutrient": "K", "target": 9.0, "actual": 8.8, "diff": -0.2, "kg_per_ton": 88.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'Urea', 'MAP', 'Calcitic Lime', 'Filler']),

    -- Limpopo - Citrus Valencia
    (gen_random_uuid(), v_agent_id, c_limpopo, f_limpopo_citrus, fd_lc_1,
     'Valencia Citrus', 1000, 50, 3950, 5500, 'saved', 'Limpopo Tropicals', 'Citrus Valley',
     '{"N": 10.0, "P": 2.0, "K": 8.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 90, "pct": 9.0, "cost": 405},{"material": "LAN", "type": "Nitrogen", "kg": 160, "pct": 16.0, "cost": 672},{"material": "MAP", "type": "Phosphorus", "kg": 120, "pct": 12.0, "cost": 1080},{"material": "Filler", "type": "Filler", "kg": 130, "pct": 13.0, "cost": 43}]'::jsonb,
     '[{"nutrient": "N", "target": 10.0, "actual": 10.2, "diff": 0.2, "kg_per_ton": 102.0},{"nutrient": "P", "target": 2.0, "actual": 1.9, "diff": -0.1, "kg_per_ton": 19.0},{"nutrient": "K", "target": 8.0, "actual": 8.1, "diff": 0.1, "kg_per_ton": 81.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'LAN', 'MAP', 'Filler']),

    -- Highveld - Maize
    (gen_random_uuid(), v_agent_id, c_highveld, f_highveld_grain, fd_hg_1,
     'Maize Planting', 1000, 50, 3600, 4800, 'saved', 'Highveld Agri', 'Grain Fields',
     '{"N": 12.0, "P": 3.0, "K": 5.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 55, "pct": 5.5, "cost": 248},{"material": "LAN", "type": "Nitrogen", "kg": 200, "pct": 20.0, "cost": 840},{"material": "MAP", "type": "Phosphorus", "kg": 150, "pct": 15.0, "cost": 1350},{"material": "Filler", "type": "Filler", "kg": 95, "pct": 9.5, "cost": 12}]'::jsonb,
     '[{"nutrient": "N", "target": 12.0, "actual": 12.1, "diff": 0.1, "kg_per_ton": 121.0},{"nutrient": "P", "target": 3.0, "actual": 2.9, "diff": -0.1, "kg_per_ton": 29.0},{"nutrient": "K", "target": 5.0, "actual": 5.0, "diff": 0.0, "kg_per_ton": 50.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'LAN', 'MAP', 'Filler']),

    -- Highveld - Potato
    (gen_random_uuid(), v_agent_id, c_highveld, f_highveld_veg, fd_hv_1,
     'Potato Premium', 1000, 50, 5200, 7000, 'saved', 'Highveld Agri', 'Veggie Valley',
     '{"N": 8.0, "P": 2.0, "K": 15.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 190, "pct": 19.0, "cost": 855},{"material": "Urea", "type": "Nitrogen", "kg": 120, "pct": 12.0, "cost": 840},{"material": "MAP", "type": "Phosphorus", "kg": 115, "pct": 11.5, "cost": 1035},{"material": "Gypsum", "type": "Ca/S Amendment", "kg": 75, "pct": 7.5, "cost": 120}]'::jsonb,
     '[{"nutrient": "N", "target": 8.0, "actual": 8.2, "diff": 0.2, "kg_per_ton": 82.0},{"nutrient": "P", "target": 2.0, "actual": 1.8, "diff": -0.2, "kg_per_ton": 18.0},{"nutrient": "K", "target": 15.0, "actual": 14.8, "diff": -0.2, "kg_per_ton": 148.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'Urea', 'MAP', 'Gypsum']),

    -- KwaZulu - Sugarcane
    (gen_random_uuid(), v_agent_id, c_kwazulu, f_kwazulu_sugar, fd_ks_1,
     'Cane NPK', 1000, 50, 3400, 4600, 'saved', 'KwaZulu Growers', 'Sugar Plains',
     '{"N": 6.0, "P": 2.0, "K": 10.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 125, "pct": 12.5, "cost": 563},{"material": "LAN", "type": "Nitrogen", "kg": 100, "pct": 10.0, "cost": 420},{"material": "MAP", "type": "Phosphorus", "kg": 120, "pct": 12.0, "cost": 1080},{"material": "Filler", "type": "Filler", "kg": 155, "pct": 15.5, "cost": 87}]'::jsonb,
     '[{"nutrient": "N", "target": 6.0, "actual": 6.1, "diff": 0.1, "kg_per_ton": 61.0},{"nutrient": "P", "target": 2.0, "actual": 2.0, "diff": 0.0, "kg_per_ton": 20.0},{"nutrient": "K", "target": 10.0, "actual": 9.9, "diff": -0.1, "kg_per_ton": 99.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'LAN', 'MAP', 'Filler']),

    -- KwaZulu - Banana
    (gen_random_uuid(), v_agent_id, c_kwazulu, f_kwazulu_banana, fd_kb_1,
     'Banana High-K', 1000, 50, 4100, 5600, 'saved', 'KwaZulu Growers', 'Banana Belt',
     '{"N": 5.0, "P": 1.0, "K": 18.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 230, "pct": 23.0, "cost": 1035},{"material": "Urea", "type": "Nitrogen", "kg": 70, "pct": 7.0, "cost": 490},{"material": "MAP", "type": "Phosphorus", "kg": 65, "pct": 6.5, "cost": 585},{"material": "Filler", "type": "Filler", "kg": 135, "pct": 13.5, "cost": 240}]'::jsonb,
     '[{"nutrient": "N", "target": 5.0, "actual": 5.0, "diff": 0.0, "kg_per_ton": 50.0},{"nutrient": "P", "target": 1.0, "actual": 0.9, "diff": -0.1, "kg_per_ton": 9.0},{"nutrient": "K", "target": 18.0, "actual": 17.6, "diff": -0.4, "kg_per_ton": 176.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'Urea', 'MAP', 'Filler']),

    -- Karoo - Grape blend
    (gen_random_uuid(), v_agent_id, c_karoo, f_karoo_grapes, fd_kg_1,
     'Cab Sav Vineyard', 1000, 50, 3200, 4400, 'saved', 'Karoo Estates', 'Vineyard Hills',
     '{"N": 5.0, "P": 1.0, "K": 4.0}'::jsonb,
     '[{"material": "Compost", "type": "Organic", "kg": 500, "pct": 50.0, "cost": 750},{"material": "KCL (Potassium Chloride)", "type": "Potassium", "kg": 40, "pct": 4.0, "cost": 180},{"material": "LAN", "type": "Nitrogen", "kg": 80, "pct": 8.0, "cost": 336},{"material": "MAP", "type": "Phosphorus", "kg": 60, "pct": 6.0, "cost": 540},{"material": "Dolomitic Lime", "type": "Ca/Mg Amendment", "kg": 120, "pct": 12.0, "cost": 144},{"material": "Filler", "type": "Filler", "kg": 200, "pct": 20.0, "cost": 250}]'::jsonb,
     '[{"nutrient": "N", "target": 5.0, "actual": 4.9, "diff": -0.1, "kg_per_ton": 49.0},{"nutrient": "P", "target": 1.0, "actual": 1.0, "diff": 0.0, "kg_per_ton": 10.0},{"nutrient": "K", "target": 4.0, "actual": 4.1, "diff": 0.1, "kg_per_ton": 41.0}]'::jsonb,
     ARRAY['Compost', 'KCL (Potassium Chloride)', 'LAN', 'MAP', 'Dolomitic Lime', 'Filler']);

  RAISE NOTICE 'Seed complete! Created: 5 clients, 11 farms, 27 fields, 11 soil analyses, 10 blends';
END $$;
