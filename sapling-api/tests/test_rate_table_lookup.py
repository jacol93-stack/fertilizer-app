"""Tests for lookup_rate_table() + rate-table override path in
calculate_nutrient_targets.

These lock in the semantics we shipped in migration 046/047 and the
soil_engine changes that wire the FERTASA 2-D rate tables through the
existing target-calc pipeline. Any future change that shifts snap
behaviour, specificity, or fallback must break one of these tests and
force a conscious decision.

Reference:
  - FERTASA Handbook Table 5.4.3.1.2 (wheat P, dryland summer rainfall)
  - Yield bands (t/ha): 1.0, 1.5, 2.0, 2.5+
  - Soil-P bands (mg/kg Bray-1): <5, 5-18, 18-30, >30
"""
from __future__ import annotations

import pytest

from app.services.soil_engine import (
    calculate_nutrient_targets,
    lookup_rate_table,
)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def wheat_crop_row():
    """Wheat removal figures for the heuristic fallback path.

    The numbers are representative (FERTASA Table 5.4.3.2 total-removal
    column: N=27, P=4.8, K=12.9, S=1.5 per tonne of grain + straw)."""
    return {
        "crop": "Wheat",
        "n": 27.0, "p": 4.8, "k": 12.9, "ca": 1.0, "mg": 0.5, "s": 1.5,
        "fe": 0.01, "b": 0.005, "mn": 0.02, "zn": 0.02, "mo": 0.001, "cu": 0.005,
    }


@pytest.fixture
def wheat_p_rate_table():
    """16 rows mirroring migration 047's seed. Deliberately duplicated
    in Python so the test doesn't need a live DB — if the SQL seed
    drifts from this, fix both together."""
    rows = []

    def add(yield_min, yield_max, soil_min, soil_max, rmin, rmax):
        rows.append({
            "crop": "Wheat", "nutrient": "P", "nutrient_form": "elemental",
            "yield_min_t_ha": yield_min, "yield_max_t_ha": yield_max,
            "soil_test_method": "Bray-1", "soil_test_unit": "mg/kg",
            "soil_test_min": soil_min, "soil_test_max": soil_max,
            "clay_pct_min": None, "clay_pct_max": None,
            "texture": None, "rainfall_mm_min": None, "rainfall_mm_max": None,
            "region": None, "prior_crop": None, "water_regime": "dryland",
            "rate_min_kg_ha": rmin, "rate_max_kg_ha": rmax,
            "source": "FERTASA Handbook", "source_section": "5.4.3.1.2",
            "source_year": 2019, "source_note": None,
        })

    # Yield 1.0: 6, 4-6, 4, 4
    add(1.0, 1.0, 0,  5,    6,  6)
    add(1.0, 1.0, 5,  18,   4,  6)
    add(1.0, 1.0, 18, 30,   4,  4)
    add(1.0, 1.0, 30, None, 4,  4)
    # Yield 1.5: 9, 7-9, 5-7, 5
    add(1.5, 1.5, 0,  5,    9,  9)
    add(1.5, 1.5, 5,  18,   7,  9)
    add(1.5, 1.5, 18, 30,   5,  7)
    add(1.5, 1.5, 30, None, 5,  5)
    # Yield 2.0: 12, 9-12, 7-9, 7
    add(2.0, 2.0, 0,  5,    12, 12)
    add(2.0, 2.0, 5,  18,   9,  12)
    add(2.0, 2.0, 18, 30,   7,  9)
    add(2.0, 2.0, 30, None, 7,  7)
    # Yield 2.5+: 15-18, 12-18, 9-15, 9-11
    add(2.5, None, 0,  5,    15, 18)
    add(2.5, None, 5,  18,   12, 18)
    add(2.5, None, 18, 30,   9,  15)
    add(2.5, None, 30, None, 9,  11)
    return rows


@pytest.fixture
def dryland_ctx():
    return {"water_regime": "dryland"}


# ── lookup_rate_table: band snap semantics ─────────────────────────────────


class TestLookupRateTableSnap:
    def test_exact_yield_exact_band(self, wheat_p_rate_table, dryland_ctx):
        """Wheat @ 2.0 t/ha, soil-P 8 mg/kg → lands in the 5-18 band → 9-12 kg."""
        hit = lookup_rate_table(
            "Wheat", "P", yield_target=2.0, soil_value=8,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        )
        assert hit is not None
        assert hit["Rate_Min"] == 9
        assert hit["Rate_Max"] == 12
        assert hit["Rate_Mid"] == 10.5
        assert hit["Is_Range"] is True
        assert hit["Source_Section"] == "5.4.3.1.2"

    def test_exact_yield_exact_value(self, wheat_p_rate_table, dryland_ctx):
        """Wheat @ 1.0 t/ha, soil-P 3 mg/kg → <5 band → exact 6 kg."""
        hit = lookup_rate_table(
            "Wheat", "P", yield_target=1.0, soil_value=3,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        )
        assert hit["Rate_Min"] == 6
        assert hit["Rate_Max"] == 6
        assert hit["Is_Range"] is False

    def test_open_top_soil_band(self, wheat_p_rate_table, dryland_ctx):
        """soil-P 45 mg/kg (> 30) hits the open upper band → 7 kg @ 2.0 t/ha."""
        hit = lookup_rate_table(
            "Wheat", "P", yield_target=2.0, soil_value=45,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        )
        assert hit["Rate_Min"] == 7
        assert hit["Rate_Max"] == 7

    def test_open_top_yield_band(self, wheat_p_rate_table, dryland_ctx):
        """Yield 3.5 t/ha (> 2.5) → 2.5+ band wins outright → 9-11 kg @ >30 soil-P."""
        hit = lookup_rate_table(
            "Wheat", "P", yield_target=3.5, soil_value=45,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        )
        assert hit["Rate_Min"] == 9
        assert hit["Rate_Max"] == 11

    def test_yield_between_bands_snaps_to_nearest(self, wheat_p_rate_table, dryland_ctx):
        """Yield 1.7 t/ha is closer to 1.5 (distance 0.2) than 2.0 (distance 0.3)."""
        hit = lookup_rate_table(
            "Wheat", "P", yield_target=1.7, soil_value=8,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        )
        # Expect 1.5 t/ha / 5-18 band → 7-9 kg
        assert hit["Rate_Min"] == 7
        assert hit["Rate_Max"] == 9
        assert hit["Matched_Band"]["yield_min"] == 1.5

    def test_yield_tie_breaks_upward(self, wheat_p_rate_table, dryland_ctx):
        """Yield 1.75 t/ha is equidistant from 1.5 and 2.0; prefer the higher
        band (agronomist-conservative: don't under-fertilize)."""
        hit = lookup_rate_table(
            "Wheat", "P", yield_target=1.75, soil_value=8,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        )
        # Expect 2.0 t/ha / 5-18 band → 9-12 kg
        assert hit["Matched_Band"]["yield_min"] == 2.0
        assert hit["Rate_Min"] == 9
        assert hit["Rate_Max"] == 12

    def test_yield_below_all_bands_still_snaps(self, wheat_p_rate_table, dryland_ctx):
        """Yield 0.5 t/ha (below the 1.0 minimum) snaps to the nearest band
        (1.0 t/ha). The handbook doesn't publish below-1.0 rates, but the
        caller has the cell's provenance and can surface that."""
        hit = lookup_rate_table(
            "Wheat", "P", yield_target=0.5, soil_value=3,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        )
        assert hit["Matched_Band"]["yield_min"] == 1.0
        assert hit["Rate_Min"] == 6  # 1.0 t/ha, <5 soil-P

    def test_soil_value_on_band_boundary_is_exclusive_upper(
        self, wheat_p_rate_table, dryland_ctx,
    ):
        """Band <5 means [0, 5). A reading of exactly 5 mg/kg falls in 5-18."""
        hit_just_under = lookup_rate_table(
            "Wheat", "P", yield_target=2.0, soil_value=4.99,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        )
        hit_at_boundary = lookup_rate_table(
            "Wheat", "P", yield_target=2.0, soil_value=5,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        )
        # <5 band → exact 12 kg; 5-18 band → 9-12 kg
        assert hit_just_under["Rate_Min"] == 12
        assert hit_just_under["Rate_Max"] == 12
        assert hit_at_boundary["Rate_Min"] == 9
        assert hit_at_boundary["Rate_Max"] == 12


# ── lookup_rate_table: misses ──────────────────────────────────────────────


class TestLookupRateTableMisses:
    def test_wrong_crop_returns_none(self, wheat_p_rate_table, dryland_ctx):
        assert lookup_rate_table(
            "Maize", "P", yield_target=2.0, soil_value=8,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        ) is None

    def test_wrong_nutrient_returns_none(self, wheat_p_rate_table, dryland_ctx):
        assert lookup_rate_table(
            "Wheat", "N", yield_target=2.0, soil_value=8,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        ) is None

    def test_empty_rate_table_returns_none(self, dryland_ctx):
        assert lookup_rate_table(
            "Wheat", "P", yield_target=2.0, soil_value=8,
            rate_table_rows=[], context=dryland_ctx,
        ) is None

    def test_rate_table_none_returns_none(self, dryland_ctx):
        assert lookup_rate_table(
            "Wheat", "P", yield_target=2.0, soil_value=8,
            rate_table_rows=None, context=dryland_ctx,
        ) is None

    def test_missing_soil_value_with_soil_axis_returns_none(
        self, wheat_p_rate_table, dryland_ctx,
    ):
        """Wheat P has a soil-test axis; if soil_value is unknown, no cell applies."""
        assert lookup_rate_table(
            "Wheat", "P", yield_target=2.0, soil_value=None,
            rate_table_rows=wheat_p_rate_table, context=dryland_ctx,
        ) is None

    def test_wrong_water_regime_returns_none(self, wheat_p_rate_table):
        """All rows are water_regime='dryland'. An irrigated context doesn't match."""
        assert lookup_rate_table(
            "Wheat", "P", yield_target=2.0, soil_value=8,
            rate_table_rows=wheat_p_rate_table,
            context={"water_regime": "irrigated"},
        ) is None

    def test_missing_water_regime_returns_none(self, wheat_p_rate_table):
        """Row requires water_regime='dryland'; empty context doesn't match."""
        assert lookup_rate_table(
            "Wheat", "P", yield_target=2.0, soil_value=8,
            rate_table_rows=wheat_p_rate_table, context={},
        ) is None


# ── Integration: calculate_nutrient_targets routing ────────────────────────


class TestCalculateNutrientTargetsRateTablePath:
    def test_rate_table_override_replaces_heuristic_for_wheat_p(
        self, sufficiency_rows, adjustment_rows, param_map_rows,
        wheat_crop_row, wheat_p_rate_table, dryland_ctx,
    ):
        """Canonical example: wheat @ 2.0 t/ha, soil-P 8 mg/kg.
        Heuristic: 4.8 * 2.0 * 1.25 (Low) = 12 kg P/ha.
        FERTASA 5.4.3.1.2: 9-12 kg → midpoint 10.5.
        Expected: rate-table path wins; Source cites 5.4.3.1.2."""
        soil = {
            "K": 180, "P (Bray-1)": 8, "N (total)": 30, "Ca": 800, "Mg": 150,
            "S": 15, "Zn": 2.0, "B": 1.0, "Mn": 20, "Fe": 20, "Cu": 1.0, "Mo": 0.2,
        }
        targets = calculate_nutrient_targets(
            crop_name="Wheat", yield_target=2.0, soil_values=soil,
            crop_rows=[wheat_crop_row],
            sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows,
            param_map_rows=param_map_rows,
            rate_table_rows=wheat_p_rate_table,
            rate_table_context=dryland_ctx,
        )
        p = next(t for t in targets if t["Nutrient"] == "P")
        assert p["Target_kg_ha"] == 10.5
        assert "5.4.3.1.2" in p["Source"]
        assert p["Rate_Table_Hit"] is not None
        assert p["Rate_Table_Hit"]["Rate_Min"] == 9
        assert p["Rate_Table_Hit"]["Rate_Max"] == 12

    def test_no_rate_table_falls_back_to_heuristic(
        self, sufficiency_rows, adjustment_rows, param_map_rows,
        wheat_crop_row, dryland_ctx,
    ):
        """Without rate-table rows, the original removal × factor path
        runs and the result cites the heuristic in Source."""
        soil = {
            "K": 180, "P (Bray-1)": 8, "N (total)": 30, "Ca": 800, "Mg": 150,
            "S": 15, "Zn": 2.0, "B": 1.0, "Mn": 20, "Fe": 20, "Cu": 1.0, "Mo": 0.2,
        }
        targets = calculate_nutrient_targets(
            crop_name="Wheat", yield_target=2.0, soil_values=soil,
            crop_rows=[wheat_crop_row],
            sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows,
            param_map_rows=param_map_rows,
            rate_table_rows=None,
            rate_table_context=dryland_ctx,
        )
        p = next(t for t in targets if t["Nutrient"] == "P")
        # removal 4.8 * yield 2.0 = 9.6 base; P (Bray-1)=8 classifies as "Very Low"
        # in the test fixture (very_low_max=10), so factor=1.5 → 14.4 kg
        assert p["Target_kg_ha"] == 14.4
        assert p["Source"] == "removal × factor (heuristic)"
        assert p["Rate_Table_Hit"] is None

    def test_other_nutrients_still_use_heuristic_when_no_table(
        self, sufficiency_rows, adjustment_rows, param_map_rows,
        wheat_crop_row, wheat_p_rate_table, dryland_ctx,
    ):
        """Only P has a rate table; N/K/etc. must continue through the
        existing removal × factor path even when rate_table_rows is
        provided (but doesn't cover that nutrient)."""
        soil = {
            "K": 180, "P (Bray-1)": 8, "N (total)": 30, "Ca": 800, "Mg": 150,
            "S": 15, "Zn": 2.0, "B": 1.0, "Mn": 20, "Fe": 20, "Cu": 1.0, "Mo": 0.2,
        }
        targets = calculate_nutrient_targets(
            crop_name="Wheat", yield_target=2.0, soil_values=soil,
            crop_rows=[wheat_crop_row],
            sufficiency_rows=sufficiency_rows,
            adjustment_rows=adjustment_rows,
            param_map_rows=param_map_rows,
            rate_table_rows=wheat_p_rate_table,
            rate_table_context=dryland_ctx,
        )
        n = next(t for t in targets if t["Nutrient"] == "N")
        # N (total) = 30 → Optimal band (low_max=20, optimal_max=40), factor=1.0
        # Base 27.0 * 2.0 * 1.0 = 54
        assert n["Target_kg_ha"] == 54.0
        assert n["Source"] == "removal × factor (heuristic)"


# ── Texture-banded rate tables (migration 066) ─────────────────────────────


@pytest.fixture
def wheat_n_western_cape_texture_table():
    """15 rows mirroring migration 066's seed. FERTASA 5.4.3.2.2 Western
    Cape N1 with explicit texture-adjusted bands (sandy / loam / clayey)
    from the same section's prose. Duplicated in Python so the test can
    run without a live DB — keep in sync with the migration."""
    rows = []

    def add(yield_min, yield_max, clay_min, clay_max, rmin, rmax):
        rows.append({
            "crop": "Wheat", "nutrient": "N", "nutrient_form": "elemental",
            "yield_min_t_ha": yield_min, "yield_max_t_ha": yield_max,
            "soil_test_method": None, "soil_test_unit": None,
            "soil_test_min": None, "soil_test_max": None,
            "clay_pct_min": clay_min, "clay_pct_max": clay_max,
            "texture": None, "rainfall_mm_min": None, "rainfall_mm_max": None,
            "region": "Western Cape", "prior_crop": None,
            "water_regime": "dryland", "crop_cycle": None,
            "rate_min_kg_ha": rmin, "rate_max_kg_ha": rmax,
            "source": "FERTASA Handbook", "source_section": "5.4.3.2.2",
            "source_year": 2019, "source_note": None,
        })

    # Loam band (15-35% clay) — published base
    add(4, 5,    15, 35,  80, 130)
    add(5, 6,    15, 35, 130, 160)
    add(6, 7,    15, 35, 160, 180)
    add(7, 8,    15, 35, 180, 200)
    add(8, None, 15, 35, 200, 250)
    # Sandy band (<15% clay) — base × 1.125
    add(4, 5,    None, 15,  90, 146)
    add(5, 6,    None, 15, 146, 180)
    add(6, 7,    None, 15, 180, 202)
    add(7, 8,    None, 15, 202, 225)
    add(8, None, None, 15, 225, 281)
    # Clayey band (>=35% clay) — base × 0.875
    add(4, 5,    35, None,  70, 114)
    add(5, 6,    35, None, 114, 140)
    add(6, 7,    35, None, 140, 158)
    add(7, 8,    35, None, 158, 175)
    add(8, None, 35, None, 175, 219)
    return rows


@pytest.fixture
def asparagus_k_rate_table():
    """12 rows mirroring migration 066's seed. FERTASA 5.6.3.3 K with
    establishment Sand/Clay split + established-annual (crop_cycle)."""
    rows = []

    def add(soil_min, soil_max, clay_min, clay_max, cycle, rate):
        rows.append({
            "crop": "Asparagus", "nutrient": "K", "nutrient_form": "elemental",
            "yield_min_t_ha": 0, "yield_max_t_ha": None,
            "soil_test_method": "NH4OAc", "soil_test_unit": "mg/kg",
            "soil_test_min": soil_min, "soil_test_max": soil_max,
            "clay_pct_min": clay_min, "clay_pct_max": clay_max,
            "texture": None, "rainfall_mm_min": None, "rainfall_mm_max": None,
            "region": None, "prior_crop": None, "water_regime": None,
            "crop_cycle": cycle,
            "rate_min_kg_ha": rate, "rate_max_kg_ha": rate,
            "source": "FERTASA Handbook", "source_section": "5.6.3.3",
            "source_year": 2019, "source_note": None,
        })

    for (smin, smax, est_sand, est_clay, estab_annual) in [
        ( 66,  99, 187, 140, 93),
        (100, 149, 140,  93, 47),
        (150, 199,  93,  47, 24),
        (200, 249,  47,  24,  0),
    ]:
        add(smin, smax, None,   25, "plant",  est_sand)
        add(smin, smax,   25, None, "plant",  est_clay)
        add(smin, smax, None, None, "ratoon", estab_annual)
    return rows


class TestWheatNWesternCapeTexture:
    """Migration 066: wheat N by yield × texture (sandy / loam / clayey).
    These lock in the FERTASA 5.4.3.2.2 prose adjustment: +10-15% sandy,
    -10-15% clayey, applied to the published N1."""

    def _ctx(self, clay_pct, region="Western Cape"):
        return {"water_regime": "dryland", "region": region,
                "clay_pct": clay_pct}

    def test_loam_matches_published_base(self, wheat_n_western_cape_texture_table):
        """clay=25% lands in the loam band [15, 35) → published base
        (80-130 at 4-5 t/ha)."""
        hit = lookup_rate_table(
            "Wheat", "N", yield_target=4.5, soil_value=None,
            rate_table_rows=wheat_n_western_cape_texture_table,
            context=self._ctx(clay_pct=25),
        )
        assert hit is not None
        assert hit["Rate_Min"] == 80
        assert hit["Rate_Max"] == 130
        assert hit["Matched_Band"]["clay_pct_min"] == 15
        assert hit["Matched_Band"]["clay_pct_max"] == 35

    def test_sandy_applies_plus_12_5_pct(self, wheat_n_western_cape_texture_table):
        """clay=8% → sandy band; rate 1.125× base (90-146 at 4-5 t/ha)."""
        hit = lookup_rate_table(
            "Wheat", "N", yield_target=4.5, soil_value=None,
            rate_table_rows=wheat_n_western_cape_texture_table,
            context=self._ctx(clay_pct=8),
        )
        assert hit["Rate_Min"] == 90
        assert hit["Rate_Max"] == 146

    def test_clayey_applies_minus_12_5_pct(self, wheat_n_western_cape_texture_table):
        """clay=45% → clayey band; rate 0.875× base (70-114 at 4-5 t/ha)."""
        hit = lookup_rate_table(
            "Wheat", "N", yield_target=4.5, soil_value=None,
            rate_table_rows=wheat_n_western_cape_texture_table,
            context=self._ctx(clay_pct=45),
        )
        assert hit["Rate_Min"] == 70
        assert hit["Rate_Max"] == 114

    def test_clay_15_is_loam_not_sandy(self, wheat_n_western_cape_texture_table):
        """Boundary: sandy = [NULL, 15) so clay=15 lands in loam."""
        hit = lookup_rate_table(
            "Wheat", "N", yield_target=4.5, soil_value=None,
            rate_table_rows=wheat_n_western_cape_texture_table,
            context=self._ctx(clay_pct=15),
        )
        assert hit["Rate_Min"] == 80  # loam base

    def test_clay_35_is_clayey_not_loam(self, wheat_n_western_cape_texture_table):
        """Boundary: loam = [15, 35) so clay=35 lands in clayey."""
        hit = lookup_rate_table(
            "Wheat", "N", yield_target=4.5, soil_value=None,
            rate_table_rows=wheat_n_western_cape_texture_table,
            context=self._ctx(clay_pct=35),
        )
        assert hit["Rate_Min"] == 70  # clayey

    def test_missing_clay_pct_misses(self, wheat_n_western_cape_texture_table):
        """Every row requires clay_pct context. No context → no match."""
        hit = lookup_rate_table(
            "Wheat", "N", yield_target=4.5, soil_value=None,
            rate_table_rows=wheat_n_western_cape_texture_table,
            context={"water_regime": "dryland", "region": "Western Cape"},
        )
        assert hit is None

    def test_wrong_region_misses(self, wheat_n_western_cape_texture_table):
        """This is the Western Cape table; Free State context must miss."""
        hit = lookup_rate_table(
            "Wheat", "N", yield_target=4.5, soil_value=None,
            rate_table_rows=wheat_n_western_cape_texture_table,
            context=self._ctx(clay_pct=25, region="Free State"),
        )
        assert hit is None

    def test_open_top_yield_clayey(self, wheat_n_western_cape_texture_table):
        """Yield 10 t/ha (>8) + clayey → open-top 175-219."""
        hit = lookup_rate_table(
            "Wheat", "N", yield_target=10, soil_value=None,
            rate_table_rows=wheat_n_western_cape_texture_table,
            context=self._ctx(clay_pct=45),
        )
        assert hit["Rate_Min"] == 175
        assert hit["Rate_Max"] == 219


class TestAsparagusKCropCycle:
    """Migration 066: asparagus K by soil-K × texture × crop_cycle.
    FERTASA 5.6.3.3 splits establishment rates by sand/clay but bearing
    rates by soil-K only."""

    def test_establishment_sandy(self, asparagus_k_rate_table):
        """Establishment (crop_cycle='plant') on sandy soil (clay=10%),
        soil-K 80 (band 66-99) → 187 kg K/ha."""
        hit = lookup_rate_table(
            "Asparagus", "K", yield_target=0, soil_value=80,
            rate_table_rows=asparagus_k_rate_table,
            context={"crop_cycle": "plant", "clay_pct": 10},
        )
        assert hit is not None
        assert hit["Rate_Min"] == 187
        assert hit["Rate_Max"] == 187

    def test_establishment_clay(self, asparagus_k_rate_table):
        """Establishment on clay soil (clay=40%), soil-K 80 → 140 kg K/ha."""
        hit = lookup_rate_table(
            "Asparagus", "K", yield_target=0, soil_value=80,
            rate_table_rows=asparagus_k_rate_table,
            context={"crop_cycle": "plant", "clay_pct": 40},
        )
        assert hit["Rate_Min"] == 140

    def test_established_annual_ignores_clay(self, asparagus_k_rate_table):
        """Bearing years (crop_cycle='ratoon'): rate depends only on
        soil-K, not texture. Even with clay_pct=5 or 60 the value is 93."""
        for clay in (5, 40, 60):
            hit = lookup_rate_table(
                "Asparagus", "K", yield_target=0, soil_value=80,
                rate_table_rows=asparagus_k_rate_table,
                context={"crop_cycle": "ratoon", "clay_pct": clay},
            )
            assert hit["Rate_Min"] == 93, f"ratoon@clay={clay} should be 93"

    def test_top_band_ratoon_is_zero(self, asparagus_k_rate_table):
        """At soil-K 220 (band 200-249), bearing plantings need 0 K."""
        hit = lookup_rate_table(
            "Asparagus", "K", yield_target=0, soil_value=220,
            rate_table_rows=asparagus_k_rate_table,
            context={"crop_cycle": "ratoon"},
        )
        assert hit["Rate_Min"] == 0
        assert hit["Rate_Max"] == 0

    def test_establishment_missing_clay_misses(self, asparagus_k_rate_table):
        """Establishment rows all require clay_pct. Missing context →
        no establishment match. Since no ratoon row matches either in
        a pure 'plant' context, result is None."""
        hit = lookup_rate_table(
            "Asparagus", "K", yield_target=0, soil_value=80,
            rate_table_rows=asparagus_k_rate_table,
            context={"crop_cycle": "plant"},
        )
        assert hit is None

    def test_wrong_crop_cycle_misses(self, asparagus_k_rate_table):
        """crop_cycle='plant' rows don't match a context asking for
        something else entirely."""
        hit = lookup_rate_table(
            "Asparagus", "K", yield_target=0, soil_value=80,
            rate_table_rows=asparagus_k_rate_table,
            context={"crop_cycle": "fallow", "clay_pct": 10},
        )
        assert hit is None
