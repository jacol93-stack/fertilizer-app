-- ============================================================
-- Seed: Growth stages for 48 crops (all crops missing stages)
-- Southern Hemisphere (SA) timing
-- Nutrient percentages sum to 100% per crop
-- ============================================================

INSERT INTO crop_growth_stages (crop, stage_name, stage_order, month_start, month_end,
    n_pct, p_pct, k_pct, ca_pct, mg_pct, s_pct, fe_pct, b_pct, mn_pct, zn_pct,
    num_applications, default_method, notes)
VALUES

-- APPLE
('Apple', 'Post-harvest recovery', 1, 4, 5, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Replenish reserves after harvest'),
('Apple', 'Dormancy', 2, 6, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Minimal uptake, base amendments'),
('Apple', 'Bud break & bloom', 3, 8, 9, 20, 25, 15, 15, 15, 15, 15, 20, 15, 15, 2, 'fertigation', 'P for root flush, B for pollination'),
('Apple', 'Fruit set & growth', 4, 10, 12, 40, 40, 35, 45, 45, 45, 45, 40, 45, 45, 3, 'fertigation', 'Peak N and Ca for cell division and fruit quality'),
('Apple', 'Maturation', 5, 1, 3, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for colour, sugar and firmness'),

-- APRICOT
('Apricot', 'Post-harvest recovery', 1, 2, 3, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Rebuild reserves after early harvest'),
('Apricot', 'Dormancy', 2, 4, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Winter rest, minimal demand'),
('Apricot', 'Bud break & bloom', 3, 7, 8, 20, 30, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'Early bloomer; P for roots, B for set'),
('Apricot', 'Fruit set & growth', 4, 9, 10, 40, 35, 35, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'Rapid fruit growth; high N, Ca'),
('Apricot', 'Maturation', 5, 11, 1, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for sugar; reduce N'),

-- BARLEY
('Barley', 'Planting & establishment', 1, 4, 5, 15, 35, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Seed-bed P for root establishment'),
('Barley', 'Tillering & vegetative', 2, 6, 7, 40, 25, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'broadcast', 'Peak N for tiller production'),
('Barley', 'Heading & flowering', 3, 8, 9, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 1, 'broadcast', 'B for pollen viability'),
('Barley', 'Grain fill & maturation', 4, 10, 11, 20, 20, 35, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for grain plumpness'),

-- BEAN (DRY)
('Bean (Dry)', 'Emergence & establishment', 1, 10, 11, 20, 35, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P for nodulation'),
('Bean (Dry)', 'Vegetative growth', 2, 11, 12, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 1, 'side_dress', 'N-fixation establishing'),
('Bean (Dry)', 'Flowering & pod set', 3, 1, 1, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 1, 'fertigation', 'B for flower retention; Ca for pods'),
('Bean (Dry)', 'Pod fill & maturity', 4, 2, 3, 30, 20, 35, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for seed weight'),

-- BEAN (GREEN)
('Bean (Green)', 'Emergence & establishment', 1, 9, 10, 20, 35, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P for early root growth'),
('Bean (Green)', 'Vegetative growth', 2, 10, 11, 30, 25, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'Strong canopy for pod production'),
('Bean (Green)', 'Flowering & pod set', 3, 11, 12, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 2, 'fertigation', 'B for pollination; Ca for quality'),
('Bean (Green)', 'Harvest period', 4, 1, 2, 25, 20, 35, 30, 30, 30, 30, 25, 30, 30, 1, 'fertigation', 'K for pod crispness'),

-- BLUEBERRY
('Blueberry', 'Post-harvest & leaf fall', 1, 2, 4, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Replenish after harvest; dormancy prep'),
('Blueberry', 'Dormancy', 2, 5, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Minimal demand; pH management'),
('Blueberry', 'Bud break & bloom', 3, 8, 9, 25, 30, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'P for roots; B for set; keep pH low'),
('Blueberry', 'Fruit development', 4, 10, 11, 35, 35, 35, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'Peak N; Ca for firmness'),
('Blueberry', 'Ripening & harvest', 5, 12, 1, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for sugar and colour'),

-- BUTTERNUT
('Butternut', 'Establishment', 1, 10, 10, 15, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P and Ca'),
('Butternut', 'Vine growth', 2, 11, 12, 35, 30, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'Peak N for canopy'),
('Butternut', 'Flowering & fruit set', 3, 1, 1, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 1, 'fertigation', 'B for pollination'),
('Butternut', 'Fruit fill & maturation', 4, 2, 4, 25, 20, 40, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for storage quality'),

-- CABBAGE
('Cabbage', 'Transplant & establishment', 1, 2, 3, 15, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P for transplant recovery'),
('Cabbage', 'Vegetative frame', 2, 3, 5, 40, 30, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'High N for leaf number and frame'),
('Cabbage', 'Head formation', 3, 5, 7, 30, 25, 35, 35, 35, 35, 35, 35, 35, 35, 2, 'fertigation', 'K and Ca for density and tipburn prevention'),
('Cabbage', 'Maturation & harvest', 4, 7, 8, 15, 15, 30, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast', 'Reduce N to prevent splitting'),

-- CANOLA
('Canola', 'Emergence & rosette', 1, 4, 6, 20, 30, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for roots; S critical for canola'),
('Canola', 'Stem elongation', 2, 7, 8, 35, 25, 25, 25, 25, 30, 25, 25, 25, 25, 2, 'broadcast', 'High N; S for amino acids'),
('Canola', 'Flowering', 3, 8, 9, 25, 25, 25, 30, 30, 30, 30, 35, 30, 30, 1, 'broadcast', 'B critical for pod set'),
('Canola', 'Pod fill & maturation', 4, 10, 11, 20, 20, 35, 30, 30, 25, 30, 25, 30, 30, 1, 'broadcast', 'K for oil content'),

-- CARROT
('Carrot', 'Germination & establishment', 1, 2, 3, 15, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for root initiation'),
('Carrot', 'Canopy development', 2, 3, 5, 40, 30, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'N for leaf area to drive root growth'),
('Carrot', 'Root bulking', 3, 5, 7, 30, 25, 40, 35, 35, 35, 35, 35, 35, 35, 2, 'fertigation', 'K for root size; Ca for crack resistance'),
('Carrot', 'Maturation', 4, 7, 8, 15, 10, 25, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast', 'Reduce N; K for storage'),

-- CHERRY
('Cherry', 'Post-harvest recovery', 1, 1, 2, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Replenish after harvest'),
('Cherry', 'Dormancy', 2, 3, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Winter rest; chill accumulation'),
('Cherry', 'Bud break & bloom', 3, 7, 8, 20, 30, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'P for root flush; B for set'),
('Cherry', 'Fruit development', 4, 9, 10, 40, 35, 35, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'Ca for cracking prevention'),
('Cherry', 'Ripening', 5, 11, 12, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for colour and sugar'),

-- COFFEE
('Coffee', 'Post-harvest & recovery', 1, 8, 9, 10, 10, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Recover after picking'),
('Coffee', 'Flowering', 2, 10, 11, 15, 20, 15, 15, 15, 20, 15, 30, 15, 15, 2, 'fertigation', 'B critical for flower set'),
('Coffee', 'Berry development', 3, 12, 2, 35, 35, 35, 40, 40, 35, 40, 35, 40, 40, 3, 'fertigation', 'Peak NPK; Ca for bean structure'),
('Coffee', 'Berry fill & ripening', 4, 3, 5, 25, 25, 30, 25, 25, 25, 25, 20, 25, 25, 2, 'fertigation', 'K for bean density and cup quality'),
('Coffee', 'Harvest', 5, 6, 7, 15, 10, 15, 15, 15, 15, 15, 10, 15, 15, 1, 'broadcast', 'Minimal; maintain tree health'),

-- COTTON
('Cotton', 'Emergence & establishment', 1, 10, 11, 10, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P; avoid excess early N'),
('Cotton', 'Vegetative (squaring)', 2, 12, 1, 30, 25, 20, 20, 20, 20, 20, 20, 20, 20, 2, 'side_dress', 'Moderate N for frame building'),
('Cotton', 'Flowering & boll set', 3, 1, 2, 35, 25, 30, 30, 30, 30, 30, 35, 30, 30, 2, 'fertigation', 'Peak N; B for boll retention'),
('Cotton', 'Boll fill & maturation', 4, 3, 4, 20, 15, 30, 25, 25, 25, 25, 20, 25, 25, 1, 'broadcast', 'K for fibre quality'),
('Cotton', 'Defoliation & harvest', 5, 5, 6, 5, 5, 10, 10, 10, 10, 10, 10, 10, 10, 0, 'broadcast', 'No fertiliser; harvest prep'),

-- FIG
('Fig', 'Post-harvest & leaf fall', 1, 4, 5, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Light feeding after harvest'),
('Fig', 'Dormancy', 2, 6, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Minimal demand'),
('Fig', 'Bud break & shoot growth', 3, 8, 9, 25, 30, 20, 20, 20, 20, 20, 20, 20, 20, 2, 'fertigation', 'N and P for new growth'),
('Fig', 'Fruit development', 4, 10, 12, 35, 35, 30, 40, 40, 40, 40, 40, 40, 40, 3, 'fertigation', 'Ca for fruit quality'),
('Fig', 'Ripening & harvest', 5, 1, 3, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for sugar and flavour'),

-- GARLIC
('Garlic', 'Planting & rooting', 1, 3, 4, 15, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for clove establishment'),
('Garlic', 'Vegetative leaf growth', 2, 5, 7, 40, 30, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'High N for leaf number = bulb size'),
('Garlic', 'Bulb initiation & fill', 3, 7, 9, 30, 25, 40, 35, 35, 35, 35, 35, 35, 35, 2, 'fertigation', 'K and S for quality and pungency'),
('Garlic', 'Maturation', 4, 9, 10, 15, 10, 25, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast', 'Reduce N; allow tops to dry'),

-- GRAPE (TABLE)
('Grape (Table)', 'Post-harvest & leaf fall', 1, 3, 4, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Reserve building'),
('Grape (Table)', 'Dormancy', 2, 5, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Pruning period; minimal uptake'),
('Grape (Table)', 'Bud break & bloom', 3, 8, 9, 20, 30, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'P for root flush; B for set'),
('Grape (Table)', 'Berry development', 4, 10, 11, 40, 35, 30, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'N for berry size; Ca for firmness'),
('Grape (Table)', 'Veraison & harvest', 5, 12, 2, 25, 25, 45, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for sugar and colour'),

-- GRAPE (WINE)
('Grape (Wine)', 'Post-harvest & leaf fall', 1, 4, 5, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Reserve replenishment'),
('Grape (Wine)', 'Dormancy', 2, 6, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Winter rest; pruning'),
('Grape (Wine)', 'Bud break & bloom', 3, 8, 9, 25, 30, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'Moderate inputs; avoid excess vigour'),
('Grape (Wine)', 'Berry development', 4, 10, 12, 35, 35, 30, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'Ca for skin integrity'),
('Grape (Wine)', 'Veraison & harvest', 5, 1, 4, 25, 25, 45, 30, 30, 30, 30, 30, 30, 30, 1, 'fertigation', 'K for phenolics; restrict N for quality'),

-- GROUNDNUT
('Groundnut', 'Emergence & establishment', 1, 11, 12, 15, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for nodulation'),
('Groundnut', 'Vegetative growth', 2, 12, 1, 20, 25, 20, 20, 20, 20, 20, 20, 20, 20, 1, 'side_dress', 'N-fixation active'),
('Groundnut', 'Flowering & pegging', 3, 1, 2, 25, 20, 25, 35, 30, 30, 30, 35, 30, 30, 2, 'broadcast', 'Ca critical for pegging; B for flowers'),
('Groundnut', 'Pod fill & maturation', 4, 3, 5, 40, 25, 45, 30, 35, 35, 35, 30, 35, 35, 1, 'broadcast', 'K for oil content'),

-- GUAVA
('Guava', 'Post-harvest recovery', 1, 6, 7, 10, 10, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Recovery after harvest'),
('Guava', 'Vegetative flush', 2, 8, 9, 30, 25, 20, 20, 20, 20, 20, 20, 20, 20, 2, 'fertigation', 'N for new growth'),
('Guava', 'Flowering & fruit set', 3, 10, 11, 20, 25, 20, 25, 25, 25, 25, 30, 25, 25, 2, 'fertigation', 'B for pollination'),
('Guava', 'Fruit development', 4, 12, 2, 25, 25, 30, 30, 30, 30, 30, 25, 30, 30, 2, 'fertigation', 'Ca for firmness; K for sugar'),
('Guava', 'Ripening & harvest', 5, 3, 5, 15, 15, 25, 20, 20, 20, 20, 20, 20, 20, 1, 'fertigation', 'K for flavour'),

-- LETTUCE
('Lettuce', 'Transplant & establishment', 1, 2, 3, 15, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P for root recovery'),
('Lettuce', 'Rapid leaf growth', 2, 3, 5, 50, 35, 40, 40, 40, 40, 40, 40, 40, 40, 3, 'fertigation', 'High N for leaf expansion'),
('Lettuce', 'Head formation & harvest', 3, 5, 7, 35, 30, 50, 45, 45, 45, 45, 45, 45, 45, 2, 'fertigation', 'K and Ca for tipburn prevention'),

-- LUCERNE
('Lucerne', 'Establishment', 1, 3, 5, 15, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P and lime for nodulation'),
('Lucerne', 'Spring growth & first cuts', 2, 9, 11, 25, 20, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'broadcast', 'Post-winter flush'),
('Lucerne', 'Summer production', 3, 12, 2, 35, 25, 35, 35, 35, 35, 35, 35, 35, 35, 2, 'broadcast', 'Peak growth; K for persistence'),
('Lucerne', 'Autumn recovery', 4, 3, 5, 25, 20, 30, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast', 'Crown reserve replenishment'),

-- MAIZE
('Maize', 'Planting & emergence', 1, 10, 11, 10, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P; Zn important'),
('Maize', 'Vegetative growth (V6-VT)', 2, 11, 1, 40, 25, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'Peak N for leaf area and ear size'),
('Maize', 'Silking & pollination', 3, 1, 2, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 1, 'fertigation', 'N for kernel number; B for silk; Zn for pollen'),
('Maize', 'Grain fill & maturation', 4, 2, 4, 25, 20, 40, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for kernel weight and stalk strength'),

-- NECTARINE
('Nectarine', 'Post-harvest recovery', 1, 2, 3, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Restore reserves'),
('Nectarine', 'Dormancy', 2, 4, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Winter rest'),
('Nectarine', 'Bud break & bloom', 3, 7, 8, 20, 30, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'P for root flush; B for pollination'),
('Nectarine', 'Fruit growth', 4, 9, 10, 40, 35, 35, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'Ca critical for stone fruit'),
('Nectarine', 'Ripening & harvest', 5, 11, 1, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for colour and firmness'),

-- OAT
('Oat', 'Planting & emergence', 1, 4, 5, 15, 35, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P'),
('Oat', 'Tillering & vegetative', 2, 6, 7, 40, 25, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'broadcast', 'Peak N for tiller number'),
('Oat', 'Heading & flowering', 3, 8, 9, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 1, 'broadcast', 'B for grain set'),
('Oat', 'Grain fill & maturity', 4, 10, 11, 20, 20, 35, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for test weight'),

-- OLIVE
('Olive', 'Post-harvest recovery', 1, 6, 7, 10, 10, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Recovery; flower initiation prep'),
('Olive', 'Winter rest & flower initiation', 2, 8, 9, 15, 20, 15, 15, 15, 15, 15, 20, 15, 15, 1, 'broadcast', 'B for flower differentiation'),
('Olive', 'Bloom & fruit set', 3, 10, 11, 20, 25, 20, 25, 25, 25, 25, 30, 25, 25, 2, 'fertigation', 'B critical for set'),
('Olive', 'Fruit growth & oil accumulation', 4, 12, 2, 35, 30, 30, 30, 30, 30, 30, 25, 30, 30, 2, 'fertigation', 'K for oil content'),
('Olive', 'Maturation & harvest', 5, 3, 5, 20, 15, 30, 25, 25, 25, 25, 20, 25, 25, 1, 'broadcast', 'K for oil quality'),

-- ONION
('Onion', 'Transplant & establishment', 1, 3, 4, 15, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for root recovery'),
('Onion', 'Leaf growth', 2, 5, 7, 40, 25, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'N for leaf number = bulb size'),
('Onion', 'Bulb initiation & fill', 3, 8, 10, 30, 25, 40, 35, 35, 35, 35, 35, 35, 35, 2, 'fertigation', 'K and S for quality'),
('Onion', 'Maturation & harvest', 4, 10, 12, 15, 15, 25, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast', 'Reduce N; K for storage'),

-- PASSION FRUIT
('Passion Fruit', 'Post-harvest & pruning', 1, 5, 6, 10, 10, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Clean up and light feeding'),
('Passion Fruit', 'Vegetative regrowth', 2, 7, 9, 30, 25, 20, 20, 20, 20, 20, 20, 20, 20, 2, 'fertigation', 'N for vine growth'),
('Passion Fruit', 'Flowering & fruit set', 3, 10, 11, 20, 25, 25, 25, 25, 25, 25, 30, 25, 25, 2, 'fertigation', 'B for pollination'),
('Passion Fruit', 'Fruit development', 4, 12, 2, 25, 25, 25, 30, 30, 30, 30, 25, 30, 30, 2, 'fertigation', 'Ca for rind; K for juice'),
('Passion Fruit', 'Ripening & harvest', 5, 3, 4, 15, 15, 25, 20, 20, 20, 20, 20, 20, 20, 1, 'fertigation', 'K for sugar and flavour'),

-- PEA
('Pea', 'Emergence & establishment', 1, 4, 5, 15, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for nodulation'),
('Pea', 'Vegetative growth', 2, 6, 7, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 1, 'side_dress', 'N-fixation active'),
('Pea', 'Flowering & pod set', 3, 7, 8, 30, 20, 30, 30, 30, 30, 30, 35, 30, 30, 2, 'fertigation', 'B for retention; K for quality'),
('Pea', 'Pod fill & harvest', 4, 9, 10, 30, 20, 35, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for sweetness'),

-- PEACH
('Peach', 'Post-harvest recovery', 1, 3, 4, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Replenish reserves'),
('Peach', 'Dormancy', 2, 5, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Winter rest'),
('Peach', 'Bud break & bloom', 3, 7, 8, 20, 30, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'P for roots; B for set'),
('Peach', 'Fruit growth', 4, 9, 11, 40, 35, 35, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'Ca for pit-split prevention'),
('Peach', 'Ripening & harvest', 5, 12, 2, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for colour and firmness'),

-- PEAR
('Pear', 'Post-harvest recovery', 1, 4, 5, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Replenish tree reserves'),
('Pear', 'Dormancy', 2, 6, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Chill requirement critical'),
('Pear', 'Bud break & bloom', 3, 8, 9, 20, 25, 15, 15, 15, 15, 15, 20, 15, 15, 2, 'fertigation', 'P for root flush; B for pollination'),
('Pear', 'Fruit set & growth', 4, 10, 12, 40, 40, 35, 45, 45, 45, 45, 40, 45, 45, 3, 'fertigation', 'Ca for cork spot prevention'),
('Pear', 'Maturation', 5, 1, 3, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for sugar and firmness'),

-- PEPPER (BELL)
('Pepper (Bell)', 'Transplant & establishment', 1, 9, 10, 10, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P for transplant recovery'),
('Pepper (Bell)', 'Vegetative growth', 2, 10, 11, 30, 25, 20, 20, 20, 20, 20, 20, 20, 20, 2, 'fertigation', 'N for frame building'),
('Pepper (Bell)', 'Flowering & fruit set', 3, 12, 1, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 2, 'fertigation', 'Ca for BER prevention; B for set'),
('Pepper (Bell)', 'Fruit fill & harvest', 4, 2, 4, 35, 25, 45, 35, 35, 35, 35, 30, 35, 35, 3, 'fertigation', 'K for colour and firmness'),

-- PERSIMMON
('Persimmon', 'Post-harvest & leaf fall', 1, 6, 7, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Light recovery'),
('Persimmon', 'Dormancy', 2, 7, 8, 5, 10, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Winter rest'),
('Persimmon', 'Bud break & bloom', 3, 9, 10, 20, 25, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'B for set; P for root flush'),
('Persimmon', 'Fruit development', 4, 11, 2, 40, 35, 35, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'Ca for cracking prevention'),
('Persimmon', 'Maturation & harvest', 5, 3, 5, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for astringency reduction'),

-- PINEAPPLE
('Pineapple', 'Planting & establishment', 1, 3, 6, 10, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for slip/sucker roots'),
('Pineapple', 'Vegetative rosette growth', 2, 7, 12, 40, 30, 30, 30, 30, 30, 30, 25, 30, 30, 3, 'side_dress', 'High N and K for leaf mass'),
('Pineapple', 'Flower induction & development', 3, 1, 4, 20, 20, 20, 25, 25, 25, 25, 30, 25, 25, 2, 'fertigation', 'B for flower quality'),
('Pineapple', 'Fruit development & harvest', 4, 5, 2, 30, 20, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for acidity and sugar balance'),

-- PLUM
('Plum', 'Post-harvest recovery', 1, 3, 4, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Restore reserves'),
('Plum', 'Dormancy', 2, 5, 6, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Chill accumulation'),
('Plum', 'Bud break & bloom', 3, 7, 8, 20, 30, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'P for roots; B for pollination'),
('Plum', 'Fruit growth', 4, 9, 11, 40, 35, 35, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'Ca for skin quality'),
('Plum', 'Ripening & harvest', 5, 12, 2, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for colour and sugar'),

-- POMEGRANATE
('Pomegranate', 'Post-harvest & leaf fall', 1, 5, 6, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Recovery after harvest'),
('Pomegranate', 'Dormancy', 2, 7, 8, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1, 'broadcast', 'Minimal demand'),
('Pomegranate', 'Bud break & bloom', 3, 9, 10, 20, 30, 15, 15, 15, 15, 15, 25, 15, 15, 2, 'fertigation', 'B for set'),
('Pomegranate', 'Fruit development', 4, 11, 1, 40, 35, 35, 45, 45, 45, 45, 35, 45, 45, 3, 'fertigation', 'Ca for aril quality'),
('Pomegranate', 'Maturation & harvest', 5, 2, 4, 25, 25, 40, 30, 30, 30, 30, 30, 30, 30, 2, 'fertigation', 'K for colour and sugar'),

-- PUMPKIN
('Pumpkin', 'Establishment', 1, 10, 10, 15, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P'),
('Pumpkin', 'Vine growth', 2, 11, 12, 35, 30, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'High N for vine extension'),
('Pumpkin', 'Flowering & fruit set', 3, 1, 2, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 2, 'fertigation', 'B for pollination'),
('Pumpkin', 'Fruit fill & maturation', 4, 3, 5, 25, 20, 40, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for storage quality'),

-- ROOIBOS
('Rooibos', 'Post-harvest recovery', 1, 4, 6, 15, 15, 10, 10, 10, 10, 10, 10, 10, 10, 1, 'broadcast', 'Minimal inputs; fynbos species'),
('Rooibos', 'Winter dormancy', 2, 7, 8, 5, 10, 5, 10, 10, 10, 10, 10, 10, 10, 1, 'broadcast', 'Adapted to low fertility'),
('Rooibos', 'Spring flush & growth', 3, 9, 12, 50, 45, 45, 45, 45, 45, 45, 45, 45, 45, 2, 'broadcast', 'Main growth; keep inputs low'),
('Rooibos', 'Harvest', 4, 1, 3, 30, 30, 40, 35, 35, 35, 35, 35, 35, 35, 1, 'broadcast', 'K for tea quality'),

-- SORGHUM
('Sorghum', 'Planting & emergence', 1, 10, 11, 10, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P'),
('Sorghum', 'Vegetative growth', 2, 12, 1, 40, 25, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'Peak N for head size'),
('Sorghum', 'Boot & flowering', 3, 2, 2, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 1, 'broadcast', 'B for pollen'),
('Sorghum', 'Grain fill & maturation', 4, 3, 5, 25, 20, 40, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for grain weight'),

-- SOYBEAN
('Soybean', 'Emergence & establishment', 1, 11, 12, 10, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P for nodulation'),
('Soybean', 'Vegetative growth', 2, 12, 1, 25, 25, 20, 20, 20, 20, 20, 20, 20, 20, 1, 'side_dress', 'N-fixation establishing'),
('Soybean', 'Flowering & pod set', 3, 2, 3, 30, 20, 30, 30, 30, 30, 30, 35, 30, 30, 2, 'fertigation', 'Peak N; B for retention'),
('Soybean', 'Pod fill & maturation', 4, 3, 5, 35, 20, 40, 35, 35, 35, 35, 30, 35, 35, 1, 'broadcast', 'K for oil content'),

-- SPINACH
('Spinach', 'Sowing & establishment', 1, 3, 4, 15, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for rapid root development'),
('Spinach', 'Rapid leaf growth', 2, 4, 6, 50, 35, 45, 45, 45, 45, 45, 45, 45, 45, 3, 'fertigation', 'High N for leaf mass'),
('Spinach', 'Harvest', 3, 6, 8, 35, 30, 45, 40, 40, 40, 40, 40, 40, 40, 2, 'fertigation', 'K for leaf quality; multiple cuts'),

-- STRAWBERRY
('Strawberry', 'Transplant & establishment', 1, 3, 4, 10, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for crown and root establishment'),
('Strawberry', 'Vegetative & crown development', 2, 5, 6, 25, 25, 20, 20, 20, 20, 20, 20, 20, 20, 2, 'fertigation', 'N for leaf area'),
('Strawberry', 'Flowering & fruit set', 3, 7, 8, 20, 20, 20, 25, 25, 25, 25, 30, 25, 25, 2, 'fertigation', 'B for pollination; Ca for firmness'),
('Strawberry', 'Fruit development & harvest', 4, 9, 11, 45, 25, 50, 40, 40, 40, 40, 35, 40, 40, 3, 'fertigation', 'K for sugar and colour'),

-- SUNFLOWER
('Sunflower', 'Emergence & establishment', 1, 11, 12, 15, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for root depth; B important'),
('Sunflower', 'Vegetative growth', 2, 1, 1, 35, 25, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'Peak N for head diameter'),
('Sunflower', 'Flowering', 3, 2, 2, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 1, 'broadcast', 'B critical for seed set'),
('Sunflower', 'Seed fill & maturation', 4, 3, 5, 25, 20, 40, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for oil content'),

-- SWEET POTATO
('Sweet Potato', 'Planting & establishment', 1, 10, 11, 15, 35, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'P for slip roots'),
('Sweet Potato', 'Vine growth', 2, 12, 1, 35, 25, 20, 25, 25, 25, 25, 25, 25, 25, 2, 'side_dress', 'Moderate N; avoid excess'),
('Sweet Potato', 'Tuber initiation & bulking', 3, 2, 4, 30, 25, 40, 35, 35, 35, 35, 35, 35, 35, 2, 'fertigation', 'K critical for tuber size'),
('Sweet Potato', 'Maturation & harvest', 4, 4, 6, 20, 15, 30, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast', 'K for dry matter'),

-- TEA
('Tea', 'Winter dormancy', 1, 5, 8, 10, 15, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'broadcast', 'Maintain soil health'),
('Tea', 'Spring flush', 2, 9, 10, 30, 30, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'broadcast', 'N for first flush quality'),
('Tea', 'Main harvest season', 3, 11, 2, 40, 35, 40, 35, 35, 35, 35, 35, 35, 35, 3, 'fertigation', 'Peak N and K for yield'),
('Tea', 'Late harvest & slowdown', 4, 3, 4, 20, 20, 25, 25, 25, 25, 25, 25, 25, 25, 1, 'broadcast', 'Taper feeding'),

-- TOBACCO
('Tobacco', 'Transplant & establishment', 1, 9, 10, 10, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P'),
('Tobacco', 'Rapid vegetative growth', 2, 10, 12, 45, 30, 30, 30, 30, 30, 30, 25, 30, 30, 3, 'side_dress', 'High N for leaf number and size'),
('Tobacco', 'Topping & ripening', 3, 12, 1, 25, 20, 30, 30, 30, 30, 30, 30, 30, 30, 1, 'fertigation', 'K for leaf body; reduce N'),
('Tobacco', 'Harvest & curing', 4, 1, 3, 20, 20, 30, 25, 25, 25, 25, 30, 25, 25, 1, 'broadcast', 'K for burn quality'),

-- TOMATO
('Tomato', 'Transplant & establishment', 1, 9, 10, 10, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P for transplant'),
('Tomato', 'Vegetative growth', 2, 10, 11, 25, 25, 15, 15, 15, 15, 15, 15, 15, 15, 2, 'fertigation', 'N for canopy'),
('Tomato', 'Flowering & fruit set', 3, 11, 12, 25, 20, 25, 35, 35, 35, 35, 40, 35, 35, 3, 'fertigation', 'Ca for BER; B for pollination'),
('Tomato', 'Fruit fill & harvest', 4, 1, 3, 40, 25, 50, 35, 35, 35, 35, 30, 35, 35, 3, 'fertigation', 'K for colour, firmness, flavour'),

-- WATERMELON
('Watermelon', 'Establishment', 1, 10, 10, 10, 30, 10, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P for roots'),
('Watermelon', 'Vine growth', 2, 11, 12, 30, 25, 20, 20, 20, 20, 20, 20, 20, 20, 2, 'side_dress', 'N for vine extension'),
('Watermelon', 'Flowering & fruit set', 3, 12, 1, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 2, 'fertigation', 'B for pollination; Ca for rind'),
('Watermelon', 'Fruit fill & harvest', 4, 1, 3, 35, 25, 45, 35, 35, 35, 35, 30, 35, 35, 2, 'fertigation', 'K for sugar and flesh colour'),

-- WHEAT
('Wheat', 'Planting & emergence', 1, 5, 6, 15, 35, 15, 15, 15, 15, 15, 15, 15, 15, 1, 'band_place', 'Starter P for roots and tillering'),
('Wheat', 'Tillering & vegetative', 2, 7, 8, 40, 25, 25, 25, 25, 25, 25, 25, 25, 25, 2, 'broadcast', 'Peak N for ear size'),
('Wheat', 'Heading & flowering', 3, 9, 10, 25, 20, 25, 30, 30, 30, 30, 35, 30, 30, 1, 'broadcast', 'N for protein; B for pollen'),
('Wheat', 'Grain fill & maturation', 4, 10, 12, 20, 20, 35, 30, 30, 30, 30, 25, 30, 30, 1, 'broadcast', 'K for kernel weight');
