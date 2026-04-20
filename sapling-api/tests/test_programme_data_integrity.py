"""Integration-style tests that hit the live Supabase reference data
to lock in the outcomes of migration 037.

These tests verify the DB state the programme builder depends on:

- Every crop in crop_requirements has growth stages + application methods
- Every perennial in the core SA orchard/vineyard list has age factors
- crop_type classifications are agronomically correct
- The alias additions haven't clobbered pre-existing data

They're marked `integration` because they read the live DB; skip in
the unit-test pass (`pytest -m 'not integration'`).
"""

from __future__ import annotations

import pytest

from app.supabase_client import get_supabase_admin


pytestmark = pytest.mark.integration


# Crops that MUST have all three reference datasets (requirements,
# growth stages, application methods). These are the crops that show
# up in the wizard dropdown and must build a programme cleanly.
CORE_CROPS_WITH_FULL_COVERAGE = [
    # Perennials the FERTASA/industry curves cover
    "Apple", "Pear",
    "Peach", "Apricot", "Plum",
    "Table Grape", "Wine Grape",
    "Olive", "Blueberry",
    "Avocado", "Macadamia", "Mango", "Litchi", "Pecan",
    "Citrus (Valencia)", "Citrus (Grapefruit)", "Citrus (Lemon)",
    "Citrus (Navel)", "Citrus (Soft Citrus)",
    "Banana",
    # Annuals
    "Maize (dryland)", "Maize (irrigated)",
    "Wheat", "Barley", "Sorghum",
    "Soybean", "Groundnut", "Sunflower",
    "Potato", "Tomato", "Onion",
]

PERENNIAL_CROPS_NEEDING_AGE_FACTORS = [
    "Apple", "Pear",
    "Peach", "Apricot", "Plum",
    "Table Grape", "Wine Grape",
    "Olive", "Blueberry",
    "Avocado", "Macadamia", "Mango", "Litchi", "Pecan",
    "Citrus (Valencia)", "Citrus (Grapefruit)", "Citrus (Lemon)",
    "Citrus (Navel)", "Citrus (Soft Citrus)",
    "Banana",
]


@pytest.fixture(scope="module")
def sb():
    return get_supabase_admin()


@pytest.fixture(scope="module")
def crops_by_table(sb):
    return {
        "requirements": {
            r["crop"]: r for r in sb.table("crop_requirements").select("*").execute().data
        },
        "stages": {
            r["crop"] for r in sb.table("crop_growth_stages").select("crop").execute().data
        },
        "methods": {
            r["crop"] for r in sb.table("crop_application_methods").select("crop").execute().data
        },
        "age_factors": {
            r["crop"] for r in sb.table("perennial_age_factors").select("crop").execute().data
        },
    }


@pytest.mark.parametrize("crop", CORE_CROPS_WITH_FULL_COVERAGE)
def test_core_crop_has_full_reference_coverage(crops_by_table, crop):
    """Every core crop must have requirements, stages, and methods data."""
    assert crop in crops_by_table["requirements"], (
        f"{crop!r} not in crop_requirements — cannot generate nutrient targets"
    )
    assert crop in crops_by_table["stages"], (
        f"{crop!r} has no rows in crop_growth_stages — feeding plan will fail"
    )
    assert crop in crops_by_table["methods"], (
        f"{crop!r} has no rows in crop_application_methods — method validation will fail"
    )


@pytest.mark.parametrize("crop", PERENNIAL_CROPS_NEEDING_AGE_FACTORS)
def test_core_perennial_has_age_factors(crops_by_table, crop):
    """Core SA perennials must have young-tree curves seeded."""
    assert crop in crops_by_table["age_factors"], (
        f"{crop!r} is a perennial in core SA production but has no "
        f"perennial_age_factors rows — young plantings will be given "
        f"mature-rate nutrition"
    )


# Crops that were miscategorised as perennial pre-migration 037.
# These should now all be annual.
FIXED_ANNUALS = [
    "Butternut", "Canola", "Bean (Dry)", "Garlic", "Bean (Green)",
    "Lentils", "Lettuce", "Maize (dryland)", "Maize (irrigated)",
    "Pepper (Bell)", "Potato", "Pumpkin", "Spinach", "Strawberry",
    "Sweetcorn", "Watermelon",
]


@pytest.mark.parametrize("crop", FIXED_ANNUALS)
def test_fixed_annuals_are_annual(crops_by_table, crop):
    """Post-037, these commercial-annual crops must be classified annual."""
    row = crops_by_table["requirements"].get(crop)
    assert row is not None, f"{crop!r} missing from crop_requirements"
    assert row.get("crop_type") == "annual", (
        f"{crop!r} still classified as {row.get('crop_type')!r} — migration 037 "
        f"should have flipped it to 'annual'"
    )


CORE_PERENNIALS_TO_KEEP = [
    "Apple", "Pear", "Avocado", "Macadamia", "Mango", "Citrus (Valencia)",
    "Table Grape", "Wine Grape", "Olive", "Blueberry",
    "Lucerne", "Sugarcane", "Asparagus",  # long-cycle crops that
                                           # stay perennial
]


@pytest.mark.parametrize("crop", CORE_PERENNIALS_TO_KEEP)
def test_core_perennials_kept_perennial(crops_by_table, crop):
    """Migration 037 must not have over-corrected — true perennials stay."""
    row = crops_by_table["requirements"].get(crop)
    assert row is not None, f"{crop!r} missing from crop_requirements"
    assert row.get("crop_type") == "perennial", (
        f"{crop!r} should stay perennial (long field cycle) but is "
        f"{row.get('crop_type')!r}"
    )


def test_age_factor_curves_monotonic(sb):
    """A young-tree curve should never drop the multiplier as the plant
    ages — that's agronomically impossible. This would catch a data
    entry mistake in migration 037 or any future seed."""
    rows = sb.table("perennial_age_factors").select("*").execute().data
    by_crop: dict[str, list[dict]] = {}
    for r in rows:
        by_crop.setdefault(r["crop"], []).append(r)

    for crop, curve in by_crop.items():
        curve_sorted = sorted(curve, key=lambda r: r["age_min"])
        for prev, nxt in zip(curve_sorted, curve_sorted[1:]):
            for field in ("n_factor", "p_factor", "k_factor", "general_factor"):
                assert nxt[field] >= prev[field], (
                    f"{crop!r} curve has {field} dropping from {prev[field]} at "
                    f"age {prev['age_min']}-{prev['age_max']} to {nxt[field]} at "
                    f"age {nxt['age_min']}-{nxt['age_max']}"
                )


def test_age_factor_reaches_one_at_maturity(sb):
    """Every seeded curve must terminate at 1.0 (mature tree = full
    nutrition). If a curve peaks below 1.0 the engine will
    permanently under-feed even a mature orchard."""
    rows = sb.table("perennial_age_factors").select("*").execute().data
    by_crop: dict[str, list[dict]] = {}
    for r in rows:
        by_crop.setdefault(r["crop"], []).append(r)

    for crop, curve in by_crop.items():
        mature = max(curve, key=lambda r: r["age_max"])
        for field in ("n_factor", "p_factor", "k_factor", "general_factor"):
            assert mature[field] == 1.0, (
                f"{crop!r} mature tier ({mature['age_label']}) has {field}="
                f"{mature[field]}, should be 1.0"
            )


def test_default_materials_variability_margin_is_set(sb):
    """The programme engine reads variability_margin from default_materials
    to decide how strictly to group blocks. Must exist and be sane."""
    rows = sb.table("default_materials").select("*").execute().data
    assert rows, "default_materials is empty — programme grouping will use hardcoded fallback"
    vm = rows[0].get("variability_margin")
    assert vm is not None, "default_materials.variability_margin is null"
    assert 1 <= vm <= 50, f"variability_margin={vm} is outside sane range (1-50%)"
