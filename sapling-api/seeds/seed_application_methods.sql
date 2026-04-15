-- ============================================================
-- Seed: Application methods for all crops
-- Maps valid methods per crop with suitability notes
-- Methods: broadcast, band_place, side_dress, fertigation, foliar
-- Crop names MUST match crop_requirements table exactly
-- ============================================================

-- Clear existing data to avoid duplicates on re-run
DELETE FROM crop_application_methods;

-- ── DECIDUOUS TREE CROPS ──────────────────────────────────────────
-- Typically: broadcast (dormancy), fertigation (active growth), foliar (micros)

INSERT INTO crop_application_methods (crop, method, is_default, nutrients_suited, timing_notes) VALUES
('Apple', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Dormancy and post-harvest; granular under canopy'),
('Apple', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Active growth through drip/micro; primary method when irrigated'),
('Apple', 'foliar', false, '["Fe","B","Mn","Zn","Cu","Ca"]', 'Micronutrient correction and Ca sprays for fruit quality'),

('Apricot', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Dormancy and post-harvest'),
('Apricot', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Active growth; primary for irrigated orchards'),
('Apricot', 'foliar', false, '["Fe","B","Mn","Zn","Cu","Ca"]', 'Micronutrient and Ca sprays'),

('Peach/Nectarine', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Dormancy and post-harvest'),
('Peach/Nectarine', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Active growth'),
('Peach/Nectarine', 'foliar', false, '["Fe","B","Mn","Zn","Cu","Ca"]', 'Micronutrient correction'),

('Pear', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Dormancy and post-harvest'),
('Pear', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Active growth'),
('Pear', 'foliar', false, '["Fe","B","Mn","Zn","Cu","Ca"]', 'Ca sprays for cork spot prevention'),

('Plum', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Dormancy and post-harvest'),
('Plum', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Active growth'),
('Plum', 'foliar', false, '["Fe","B","Mn","Zn","Cu","Ca"]', 'Micronutrient correction'),

('Fig', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Dormancy and post-harvest'),
('Fig', 'fertigation', false, '["N","K","Ca","Mg","S"]', 'Active growth when irrigated'),
('Fig', 'foliar', false, '["Fe","B","Mn","Zn","Cu"]', 'Micronutrient correction'),

('Olive', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'All stages; primary for dryland'),
('Olive', 'fertigation', false, '["N","K","Ca","Mg","S","B"]', 'When irrigated'),
('Olive', 'foliar', false, '["Fe","B","Mn","Zn","Cu"]', 'B critical for fruit set'),

('Pomegranate', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Dormancy and post-harvest'),
('Pomegranate', 'fertigation', false, '["N","K","Ca","Mg","S","B"]', 'Active growth when irrigated'),
('Pomegranate', 'foliar', false, '["Fe","B","Mn","Zn","Cu","Ca"]', 'B for fruit set; Ca for rind quality'),

-- ── SUBTROPICAL / TROPICAL FRUIT ──────────────────────────────────

('Avocado', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Dormancy/post-harvest; granular under canopy drip-line. Split N across 3-4 applications'),
('Avocado', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary for irrigated orchards; weekly during active growth (Aug-Mar)'),
('Avocado', 'foliar', false, '["Zn","B","Fe","Mn","Cu","Ca","K"]', 'Zn and B critical for set; Ca sprays for fruit quality; K foliar late season'),

('Macadamia', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Primary method; 3-4 split applications. Heavy K and Ca demand during nut fill'),
('Macadamia', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B"]', 'When irrigated; critical during nut development (Jan-Apr)'),
('Macadamia', 'foliar', false, '["Zn","B","Fe","Mn","Cu"]', 'Zn and B for set and nut quality; Fe on alkaline soils'),

('Citrus (Valencia)', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Split 3-4 applications Aug-Mar; P and K pre-bloom'),
('Citrus (Valencia)', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary for irrigated; weekly during active flush'),
('Citrus (Valencia)', 'foliar', false, '["Zn","B","Fe","Mn","Cu","Ca","K"]', 'Zn + B + urea pre-bloom spray; Cu for disease resistance'),

('Citrus (Navel)', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Split 3-4 applications Aug-Mar; moderate N to manage fruit size'),
('Citrus (Navel)', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary for irrigated orchards'),
('Citrus (Navel)', 'foliar', false, '["Zn","B","Fe","Mn","Cu","Ca","K"]', 'Ca sprays for rind quality; K late season'),

('Citrus (Lemon)', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Year-round bearer; split applications'),
('Citrus (Lemon)', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Continuous feeding for year-round production'),
('Citrus (Lemon)', 'foliar', false, '["Zn","B","Fe","Mn","Cu","Ca"]', 'Micronutrient correction'),

('Citrus (Soft Citrus)', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Split applications; careful N management for fruit size'),
('Citrus (Soft Citrus)', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary for irrigated'),
('Citrus (Soft Citrus)', 'foliar', false, '["Zn","B","Fe","Mn","Cu","Ca","K"]', 'Ca for rind; K for internal quality'),

('Citrus (Grapefruit)', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Split applications; high K demand'),
('Citrus (Grapefruit)', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary for irrigated orchards'),
('Citrus (Grapefruit)', 'foliar', false, '["Zn","B","Fe","Mn","Cu","Ca"]', 'Zn + B pre-bloom'),

('Mango', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Post-harvest and pre-bloom; avoid N during flower induction'),
('Mango', 'fertigation', false, '["N","K","Ca","Mg","S","Zn","B"]', 'During fruit development when irrigated'),
('Mango', 'foliar', false, '["Zn","B","Fe","Mn","Cu","Ca","K"]', 'Zn critical; B for panicle development; KNO3 for flower induction'),

('Litchi', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Post-harvest main application; avoid N during flower induction (Apr-Jun)'),
('Litchi', 'fertigation', false, '["N","K","Ca","Mg","S","Zn","B"]', 'During fruit development; K critical for fruit colour'),
('Litchi', 'foliar', false, '["Zn","B","Fe","Mn","Cu","Ca"]', 'B for fruit set; Zn for leaf health'),

('Banana', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Split monthly; heavy K feeder (K:N ratio 2:1 at bunch stage)'),
('Banana', 'fertigation', false, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary for irrigated; weekly feeding ideal'),
('Banana', 'foliar', false, '["Zn","B","Fe","Mn","Cu"]', 'Micronutrient correction; Zn important'),

('Pecan', 'broadcast', true, '["N","P","K","Ca","Mg","S","Zn"]', 'Primary method; Zn in broadcast critical for pecan. Split N 3-4 times'),
('Pecan', 'fertigation', false, '["N","K","Ca","Mg","S","Zn","B"]', 'When irrigated; heavy Zn and N demand during nut fill'),
('Pecan', 'foliar', false, '["Zn","Ni","Fe","Mn","Cu","B"]', 'Zn foliar 3-6 sprays/season is standard practice; Ni for mouse-ear'),

('Blueberry', 'fertigation', true, '["N","K","Ca","Mg","S","Fe","Zn","Mn"]', 'Primary method; pH-sensitive crop needs precise delivery'),
('Blueberry', 'broadcast', false, '["S","Ca","Mg"]', 'Amendments only; avoid granular N near shallow roots'),
('Blueberry', 'foliar', false, '["Fe","Mn","Zn","B","Cu"]', 'Fe chlorosis common; foliar Fe critical on high-pH soils'),

('Guava', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Primary for dryland; under canopy'),
('Guava', 'fertigation', false, '["N","K","Ca","Mg","S"]', 'When irrigated'),
('Guava', 'foliar', false, '["Fe","B","Mn","Zn","Cu"]', 'Micronutrient correction'),

('Passion Fruit', 'fertigation', true, '["N","K","Ca","Mg","S","Fe","Zn","B"]', 'Primary method; vines need regular feeding'),
('Passion Fruit', 'broadcast', false, '["P","Ca","Mg","S"]', 'Base amendments'),
('Passion Fruit', 'foliar', false, '["Fe","B","Mn","Zn","Cu"]', 'Micronutrient correction'),

('Pineapple', 'foliar', true, '["N","K","Fe","Zn","B","Mn","Cu"]', 'Primary method — pineapple absorbs through leaves'),
('Pineapple', 'broadcast', false, '["P","K","Ca","Mg","S"]', 'Pre-plant and base amendments only'),
('Pineapple', 'side_dress', false, '["N","K"]', 'Supplementary N and K between rows'),

('Strawberry', 'fertigation', true, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary method; drip essential'),
('Strawberry', 'broadcast', false, '["P","Ca","Mg","S"]', 'Pre-plant bed preparation only'),
('Strawberry', 'foliar', false, '["Fe","B","Mn","Zn","Cu","Ca"]', 'Ca for firmness; B for set'),

-- ── GRAPE ──────────────────────────────────────────────────────────

('Table Grape', 'fertigation', true, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary method for irrigated vineyards'),
('Table Grape', 'broadcast', false, '["P","Ca","Mg","S"]', 'Dormancy amendments'),
('Table Grape', 'foliar', false, '["Fe","B","Mn","Zn","Cu","Ca","K"]', 'K foliar for colour; Ca for firmness; B for set'),

('Wine Grape', 'fertigation', true, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary for irrigated; careful N management'),
('Wine Grape', 'broadcast', false, '["P","Ca","Mg","S"]', 'Dormancy amendments; conservative N'),
('Wine Grape', 'foliar', false, '["Fe","B","Mn","Zn","Cu"]', 'B for set; micronutrient correction'),

-- ── GRAIN CROPS ────────────────────────────────────────────────────

('Maize (dryland)', 'band_place', true, '["N","P","K","S","Zn"]', 'At planting; starter band with seed'),
('Maize (dryland)', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant or topdress'),
('Maize (dryland)', 'side_dress', false, '["N","K","S"]', 'V6-V8 N topdress; critical timing'),
('Maize (dryland)', 'foliar', false, '["Zn","B","Mn","Fe"]', 'Zn deficiency common on high-pH soils'),

('Maize (irrigated)', 'band_place', true, '["N","P","K","S","Zn"]', 'At planting; starter band'),
('Maize (irrigated)', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant'),
('Maize (irrigated)', 'side_dress', false, '["N","K","S"]', 'V6-V8 N topdress'),
('Maize (irrigated)', 'fertigation', false, '["N","K","S"]', 'Under pivot or drip; spoon-feed N through season'),
('Maize (irrigated)', 'foliar', false, '["Zn","B","Mn","Fe"]', 'Zn deficiency common on high-pH soils'),

('Wheat', 'band_place', true, '["N","P","K","S"]', 'At planting; starter band'),
('Wheat', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant or topdress'),
('Wheat', 'side_dress', false, '["N","S"]', 'Tillering topdress'),
('Wheat', 'foliar', false, '["Mn","Cu","Zn"]', 'Mn and Cu deficiency correction'),

('Barley', 'band_place', true, '["N","P","K","S"]', 'At planting; starter band'),
('Barley', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant or topdress'),
('Barley', 'side_dress', false, '["N","S"]', 'Tillering topdress'),

('Sorghum', 'band_place', true, '["N","P","K","S","Zn"]', 'At planting'),
('Sorghum', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant'),
('Sorghum', 'side_dress', false, '["N","K","S"]', 'V6 topdress'),
('Sorghum', 'foliar', false, '["Zn","Fe","Mn"]', 'Micronutrient correction'),

('Sweetcorn', 'band_place', true, '["N","P","K","S","Zn"]', 'At planting'),
('Sweetcorn', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant'),
('Sweetcorn', 'side_dress', false, '["N","K","S"]', 'V6 N topdress'),
('Sweetcorn', 'fertigation', false, '["N","K","S"]', 'When irrigated'),
('Sweetcorn', 'foliar', false, '["Zn","B","Mn","Fe"]', 'Zn correction'),

-- ── OILSEEDS & LEGUMES ──────────────────────────────────────────────

('Canola', 'band_place', true, '["N","P","K","S"]', 'At planting; S critical for canola'),
('Canola', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant'),
('Canola', 'side_dress', false, '["N","S"]', 'Rosette topdress'),
('Canola', 'foliar', false, '["B","Mo","Mn"]', 'B for pod set; Mo for N-fixation'),

('Groundnut', 'band_place', true, '["P","K","S"]', 'At planting; avoid high N near seed'),
('Groundnut', 'broadcast', false, '["Ca","Mg","S","P"]', 'Pre-plant Ca critical for pegging zone'),
('Groundnut', 'foliar', false, '["B","Mo","Fe","Mn"]', 'Mo for fixation; B for pegging'),

('Soybean', 'band_place', true, '["P","K","S"]', 'At planting; N-fixation crop'),
('Soybean', 'broadcast', false, '["P","K","Ca","Mg","S"]', 'Pre-plant'),
('Soybean', 'foliar', false, '["Mo","Mn","Fe","B"]', 'Mo critical for nodulation'),

('Sunflower', 'band_place', true, '["N","P","K","S"]', 'At planting'),
('Sunflower', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant'),
('Sunflower', 'side_dress', false, '["N","K","S"]', 'V6 topdress'),
('Sunflower', 'foliar', false, '["B","Zn","Mn"]', 'B critical for head development'),

('Dry Beans', 'band_place', true, '["P","K","S"]', 'At planting; starter P for nodulation'),
('Dry Beans', 'side_dress', false, '["N","K"]', 'Supplementary if fixation poor'),
('Dry Beans', 'fertigation', false, '["N","K","Ca","S"]', 'When irrigated'),
('Dry Beans', 'foliar', false, '["Mo","B","Mn","Fe"]', 'Mo for fixation; B for pod set'),

('Green Beans', 'band_place', true, '["P","K","S"]', 'At planting'),
('Green Beans', 'side_dress', false, '["N","K"]', 'Supplementary N'),
('Green Beans', 'fertigation', false, '["N","K","Ca","S"]', 'When irrigated'),
('Green Beans', 'foliar', false, '["Mo","B","Mn","Fe","Ca"]', 'Ca for pod quality'),

('Lentils', 'band_place', true, '["P","K","S"]', 'At planting; N-fixing legume'),
('Lentils', 'broadcast', false, '["P","K","Ca","Mg","S"]', 'Pre-plant'),
('Lentils', 'foliar', false, '["Mo","B","Mn","Fe"]', 'Mo for fixation'),

('Lucerne/Alfalfa', 'broadcast', true, '["P","K","Ca","Mg","S"]', 'After each cut; primary method'),
('Lucerne/Alfalfa', 'fertigation', false, '["N","K","S"]', 'When under pivot; N only if stand is thin'),
('Lucerne/Alfalfa', 'foliar', false, '["B","Mo","Fe","Mn"]', 'B for persistence; Mo for fixation'),

-- ── VEGETABLES ──────────────────────────────────────────────────────

('Tomato', 'fertigation', true, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary; drip essential for quality'),
('Tomato', 'broadcast', false, '["P","Ca","Mg","S"]', 'Pre-plant bed preparation'),
('Tomato', 'foliar', false, '["Ca","B","Fe","Mn","Zn","Cu"]', 'Ca for BER prevention; B for set'),

('Pepper (Bell)', 'fertigation', true, '["N","K","Ca","Mg","S","Fe","Zn","B","Mn"]', 'Primary; similar to tomato'),
('Pepper (Bell)', 'broadcast', false, '["P","Ca","Mg","S"]', 'Pre-plant'),
('Pepper (Bell)', 'foliar', false, '["Ca","B","Fe","Mn","Zn"]', 'Ca for BER; B for set'),

('Cabbage', 'band_place', true, '["N","P","K","S"]', 'At transplant'),
('Cabbage', 'side_dress', false, '["N","K","Ca"]', 'Head formation topdress'),
('Cabbage', 'fertigation', false, '["N","K","Ca","Mg","S","B"]', 'When irrigated'),
('Cabbage', 'foliar', false, '["B","Mo","Ca"]', 'B for hollow stem prevention; Mo for whiptail'),

('Lettuce', 'fertigation', true, '["N","K","Ca","Mg","S"]', 'Primary; short cycle needs precise delivery'),
('Lettuce', 'broadcast', false, '["P","Ca","Mg","S"]', 'Pre-plant'),
('Lettuce', 'foliar', false, '["Ca","B","Fe","Mn"]', 'Ca for tipburn prevention'),

('Spinach', 'fertigation', true, '["N","K","Ca","Mg","S"]', 'Primary; fast-growing crop'),
('Spinach', 'broadcast', false, '["P","Ca","Mg","S"]', 'Pre-plant'),
('Spinach', 'foliar', false, '["Fe","Mn","B"]', 'Fe for leaf colour'),

('Onion', 'band_place', true, '["N","P","K","S"]', 'At planting'),
('Onion', 'broadcast', false, '["P","K","Ca","Mg","S"]', 'Pre-plant'),
('Onion', 'side_dress', false, '["N","K","S"]', 'Bulb initiation topdress; stop N 6 weeks before harvest'),
('Onion', 'fertigation', false, '["N","K","S"]', 'When irrigated'),
('Onion', 'foliar', false, '["Cu","B","Mn"]', 'Cu for disease resistance'),

('Garlic', 'band_place', true, '["N","P","K","S"]', 'At planting'),
('Garlic', 'broadcast', false, '["P","K","Ca","Mg","S"]', 'Pre-plant'),
('Garlic', 'side_dress', false, '["N","K","S"]', 'Active growth topdress'),
('Garlic', 'foliar', false, '["B","Mn","Zn"]', 'Micronutrient correction'),

('Carrot', 'band_place', true, '["P","K","S"]', 'At planting; avoid excess N near seed'),
('Carrot', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant'),
('Carrot', 'side_dress', false, '["N","K"]', 'Root development topdress'),
('Carrot', 'foliar', false, '["B","Mn","Cu"]', 'B for root quality'),

('Butternut', 'band_place', true, '["N","P","K","S"]', 'At planting'),
('Butternut', 'side_dress', false, '["N","K"]', 'Vine growth topdress'),
('Butternut', 'fertigation', false, '["N","K","Ca","S"]', 'When irrigated'),
('Butternut', 'foliar', false, '["B","Ca","Mn"]', 'B for pollination'),

('Pumpkin', 'band_place', true, '["N","P","K","S"]', 'At planting'),
('Pumpkin', 'side_dress', false, '["N","K"]', 'Vine growth topdress'),
('Pumpkin', 'fertigation', false, '["N","K","Ca","S"]', 'When irrigated'),
('Pumpkin', 'foliar', false, '["B","Ca","Mn"]', 'B for pollination'),

('Watermelon', 'band_place', true, '["N","P","K","S"]', 'At planting'),
('Watermelon', 'fertigation', false, '["N","K","Ca","Mg","S"]', 'Primary when irrigated'),
('Watermelon', 'foliar', false, '["B","Ca","Mn","Zn"]', 'Ca for rind strength; B for set'),

('Asparagus', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Post-harvest fern growth; heavy K feeder'),
('Asparagus', 'fertigation', false, '["N","K","Ca","S"]', 'When irrigated; during fern growth'),
('Asparagus', 'foliar', false, '["Fe","B","Mn","Zn"]', 'Micronutrient correction during fern stage'),

('Potato', 'band_place', true, '["N","P","K","S","Zn"]', 'At planting; starter in furrow'),
('Potato', 'broadcast', false, '["N","P","K","Ca","Mg","S"]', 'Pre-plant and hilling'),
('Potato', 'side_dress', false, '["N","K","Ca"]', 'Tuber initiation topdress; Ca for scab prevention'),
('Potato', 'fertigation', false, '["N","K","Ca","S"]', 'Under pivot or drip; primary for irrigated'),
('Potato', 'foliar', false, '["Mn","Zn","B","Ca"]', 'Mn and Ca for tuber quality'),

('Sweet Potato', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Pre-plant; primary method'),
('Sweet Potato', 'side_dress', false, '["N","K"]', 'Vine establishment topdress'),
('Sweet Potato', 'foliar', false, '["B","Mn","Zn"]', 'Micronutrient correction'),

-- ── INDUSTRIAL / CASH CROPS ──────────────────────────────────────────

('Sugarcane', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Primary method; heavy N and K feeder. Split N: plant crop and ratoons differ'),
('Sugarcane', 'band_place', false, '["N","P","K","S","Zn"]', 'At planting in furrow'),
('Sugarcane', 'side_dress', false, '["N","K","S"]', 'Ratoon topdress; N applied 6-8 weeks after harvest'),
('Sugarcane', 'fertigation', false, '["N","K","S"]', 'Under pivot irrigation'),
('Sugarcane', 'foliar', false, '["Zn","Fe","Mn","Si"]', 'Micronutrient correction; Si for stalk strength'),

('Cotton', 'band_place', true, '["N","P","K","S","Zn"]', 'At planting'),
('Cotton', 'side_dress', false, '["N","K"]', 'Square/boll topdress; K critical for fibre'),
('Cotton', 'fertigation', false, '["N","K","S"]', 'Under pivot'),
('Cotton', 'foliar', false, '["B","Zn","Mn","Fe"]', 'B for boll retention'),

('Tobacco', 'band_place', true, '["N","P","K","S"]', 'At transplant'),
('Tobacco', 'side_dress', false, '["N","K"]', 'Topping-stage topdress'),
('Tobacco', 'foliar', false, '["B","Mo","Mn"]', 'Mo for leaf quality'),

('Rooibos', 'broadcast', true, '["P","K","Ca","Mg","S"]', 'Primary; fynbos species sensitive to excess N'),
('Rooibos', 'foliar', false, '["Fe","Mn","Zn","B"]', 'Micronutrient correction on acid soils'),

('Tea', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Primary; after each flush'),
('Tea', 'fertigation', false, '["N","K","S"]', 'When irrigated'),
('Tea', 'foliar', false, '["Zn","Mn","Cu","B"]', 'Micronutrient correction'),

('Coffee', 'broadcast', true, '["N","P","K","Ca","Mg","S"]', 'Primary; under canopy'),
('Coffee', 'fertigation', false, '["N","K","Ca","Mg","S","Zn","B"]', 'When irrigated; primary for modern plantings'),
('Coffee', 'foliar', false, '["Zn","B","Fe","Mn","Cu"]', 'Zn and B critical for berry development');
