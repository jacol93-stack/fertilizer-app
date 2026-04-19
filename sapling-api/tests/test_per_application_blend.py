"""Unit tests for per-application blend optimization + method-aware
material filtering in the programme pipeline.

Locks in the two behaviours the user hit in production:
  1. Every application gets its own recipe, not the group average.
  2. Foliar applications skip the dry/liquid LP entirely — the caller
     is expected to route those through the foliar product catalog.

Materials dataframe fixture mimics the production shape: a mix of solid
(dry, `liquid_compatible=False`) and liquid/chelate (`liquid_compatible
=True`) rows.
"""

from __future__ import annotations

import pandas as pd
import pytest

from app.services.programme_engine import (
    FERTIGATION_METHODS,
    FOLIAR_METHODS,
    filter_materials_for_method,
    optimize_blend_for_application,
)


# ─── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def materials_df():
    """Minimal set that covers a broad-brush dry blend + a liquid chelate.

    Columns mirror what `load_materials_df` produces after the uppercase
    rename: nutrient cols as N/P/K/Ca/Mg/S, plus liquid_compatible flag.
    """
    rows = [
        # Dry granular materials
        {"material": "Urea",  "cost_per_ton": 12000, "liquid_compatible": False,
         "N": 46, "P": 0,  "K": 0,  "Ca": 0,  "Mg": 0, "S": 0},
        {"material": "DAP",   "cost_per_ton": 14000, "liquid_compatible": False,
         "N": 18, "P": 20, "K": 0,  "Ca": 0,  "Mg": 0, "S": 0},
        {"material": "KCl",   "cost_per_ton": 11000, "liquid_compatible": False,
         "N": 0,  "P": 0,  "K": 50, "Ca": 0,  "Mg": 0, "S": 0},
        {"material": "Lime",  "cost_per_ton": 2500,  "liquid_compatible": False,
         "N": 0,  "P": 0,  "K": 0,  "Ca": 32, "Mg": 0, "S": 0},
        {"material": "Manure Compost", "cost_per_ton": 3000, "liquid_compatible": False,
         "N": 1,  "P": 0.5, "K": 1, "Ca": 2,  "Mg": 0.5, "S": 0},
        # Liquid-compatible materials (for fertigation). Water acts as
        # a zero-nutrient volume filler — without it the dry LP has no
        # room to balance mass against nutrient equality constraints,
        # which mirrors the real carrier-volume concern with liquids.
        {"material": "Water Filler", "cost_per_ton": 0, "liquid_compatible": True,
         "N": 0,  "P": 0,  "K": 0,  "Ca": 0,  "Mg": 0, "S": 0},
        {"material": "UAN32",       "cost_per_ton": 8000,  "liquid_compatible": True,
         "N": 32, "P": 0,  "K": 0,  "Ca": 0,  "Mg": 0, "S": 0},
        {"material": "Potassium Nitrate Liquid", "cost_per_ton": 14000, "liquid_compatible": True,
         "N": 13, "P": 0,  "K": 44, "Ca": 0,  "Mg": 0, "S": 0},
        {"material": "Calcium Nitrate Liquid",   "cost_per_ton": 9000,  "liquid_compatible": True,
         "N": 15, "P": 0,  "K": 0,  "Ca": 19, "Mg": 0, "S": 0},
    ]
    return pd.DataFrame(rows)


# ─── filter_materials_for_method ────────────────────────────────────────


def test_dry_method_filters_out_liquid_materials(materials_df):
    out = filter_materials_for_method(materials_df, "broadcast")
    assert len(out) > 0
    assert (out["liquid_compatible"] == False).all()  # noqa: E712
    assert "Urea" in out["material"].values
    assert "UAN32" not in out["material"].values


def test_fertigation_method_filters_out_dry_materials(materials_df):
    out = filter_materials_for_method(materials_df, "fertigation")
    assert len(out) > 0
    assert (out["liquid_compatible"] == True).all()  # noqa: E712
    assert "UAN32" in out["material"].values
    assert "Urea" not in out["material"].values
    # Lime/compost (dry-only) must not sneak into a fertigation blend
    assert "Lime" not in out["material"].values


def test_all_dry_method_aliases_filter_dry(materials_df):
    for method in ["broadcast", "band_place", "side_dress", "topdress"]:
        out = filter_materials_for_method(materials_df, method)
        assert (out["liquid_compatible"] == False).all(), f"{method} leaked liquid rows"  # noqa: E712


def test_unknown_method_returns_full_set(materials_df):
    # Unknown methods shouldn't silently filter — return everything and
    # let the caller handle it explicitly.
    out = filter_materials_for_method(materials_df, "unknown_method")
    assert len(out) == len(materials_df)


def test_missing_column_returns_unchanged(materials_df):
    df = materials_df.drop(columns=["liquid_compatible"])
    out = filter_materials_for_method(df, "broadcast")
    assert len(out) == len(df)


# ─── optimize_blend_for_application ─────────────────────────────────────


def _item(method: str, n=0, p=0, k=0, ca=0, mg=0, s=0, stage="test", month=1):
    return {
        "stage_name": stage,
        "month_target": month,
        "method": method,
        "n_kg_ha": n, "p_kg_ha": p, "k_kg_ha": k,
        "ca_kg_ha": ca, "mg_kg_ha": mg, "s_kg_ha": s,
    }


def test_foliar_application_returns_none(materials_df):
    """Foliar items should bypass the LP — they're routed through the
    foliar product catalog instead."""
    for method in FOLIAR_METHODS:
        res = optimize_blend_for_application(
            _item(method, n=5, k=10), materials_df, batch_size=1000, c_idx=0, min_pct=0,
        )
        assert res is None, f"foliar method {method} should skip LP"


def test_dry_application_returns_recipe_with_solids_only(materials_df):
    """Broadcast application fed a dry-filtered material set yields a
    recipe composed exclusively of dry materials."""
    dry = filter_materials_for_method(materials_df, "broadcast")
    # Need a c_idx for compost-containing dry LP
    from app.services.material_loader import find_compost_index
    c_idx = find_compost_index(dry)

    res = optimize_blend_for_application(
        _item("broadcast", n=100, p=20, k=50),
        dry, batch_size=1000, c_idx=c_idx, min_pct=0,
    )
    assert res is not None
    assert "recipe" in res and res["recipe"]
    # Every material used must be solid
    dry_names = set(dry["material"].tolist())
    for r in res["recipe"]:
        assert r["material"] in dry_names, f"{r['material']} leaked from non-dry set"


def test_fertigation_application_returns_recipe_with_liquids_only(materials_df):
    fert = filter_materials_for_method(materials_df, "fertigation")
    res = optimize_blend_for_application(
        _item("fertigation", n=30, k=30),
        fert, batch_size=1000, c_idx=None, min_pct=0,
    )
    assert res is not None
    liquid_names = set(fert["material"].tolist())
    for r in res["recipe"]:
        assert r["material"] in liquid_names, f"{r['material']} leaked from non-liquid set"


def test_different_stages_produce_different_recipes(materials_df):
    """The real bug from the macadamia screenshot: every application
    was getting the same recipe. Two items with clearly different
    nutrient vectors must produce different recipes."""
    dry = filter_materials_for_method(materials_df, "broadcast")
    from app.services.material_loader import find_compost_index
    c_idx = find_compost_index(dry)

    flowering = _item("broadcast", n=20, p=5, k=50, stage="flowering", month=9)
    nut_fill  = _item("broadcast", n=80, p=20, k=20, stage="nut fill", month=11)

    res_a = optimize_blend_for_application(flowering, dry, 1000, c_idx, 0)
    res_b = optimize_blend_for_application(nut_fill, dry, 1000, c_idx, 0)

    assert res_a is not None and res_b is not None
    assert res_a["sa_notation"] != res_b["sa_notation"], (
        "two distinct nutrient demands must not produce the same notation "
        f"(got {res_a['sa_notation']!r} for both)"
    )
    # And the rate should differ since total demand differs
    assert res_a["rate_kg_ha"] != res_b["rate_kg_ha"]


def test_zero_demand_returns_none(materials_df):
    """An application with no nutrient demand shouldn't force the LP
    to invent a blend."""
    dry = filter_materials_for_method(materials_df, "broadcast")
    res = optimize_blend_for_application(
        _item("broadcast"),  # all zeros
        dry, batch_size=1000, c_idx=0, min_pct=0,
    )
    assert res is None


def test_empty_item_returns_none(materials_df):
    dry = filter_materials_for_method(materials_df, "broadcast")
    assert optimize_blend_for_application({}, dry, 1000, 0, 0) is None


def test_fertigation_method_set_exposed():
    """Guard: the FERTIGATION_METHODS set is imported elsewhere — if
    someone renames it the import will fail loudly rather than silently."""
    assert "fertigation" in FERTIGATION_METHODS
