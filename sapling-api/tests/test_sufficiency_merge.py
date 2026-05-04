"""Tests for `merge_sufficiency_for_crop` — the shared per-crop sufficiency
catalog builder used by both the programme builder's range-bar lookup
and the soil-report renderer.

Regression context: through 2026-04 the programme builder ignored
`crop_sufficiency_overrides` entirely (only generic `soil_sufficiency`
flowed into `_build_nutrient_status`), and the soil-reports loader's
in-line merge keyed on raw parameter names — so a citrus override row
labelled `'K (exchangeable)'` silently failed to shadow the generic `'K'`
row, and the report displayed universal bands for citrus K. This module
locks the merging contract end-to-end.
"""
from __future__ import annotations

from app.services.soil_engine import merge_sufficiency_for_crop


_GENERIC = [
    {"parameter": "K", "very_low_max": 40, "low_max": 80, "optimal_max": 150, "high_max": 250},
    {"parameter": "Ca", "very_low_max": 200, "low_max": 500, "optimal_max": 1500, "high_max": 3000},
    {"parameter": "Mg", "very_low_max": 50, "low_max": 120, "optimal_max": 300, "high_max": 600},
    {"parameter": "P (Bray-1)", "very_low_max": 8, "low_max": 15, "optimal_max": 30, "high_max": 60},
    {"parameter": "pH (KCl)", "very_low_max": 4.0, "low_max": 4.5, "optimal_max": 5.5, "high_max": 6.5},
]


def _by_param(rows):
    return {r["parameter"]: r for r in rows}


def test_no_override_returns_generic_unchanged():
    out = merge_sufficiency_for_crop(_GENERIC, [], "Wheat")
    assert _by_param(out)["K"]["optimal_max"] == 150


def test_macadamia_K_override_shadows_generic():
    overrides = [
        {"crop": "Macadamia", "parameter": "K",
         "very_low_max": None, "low_max": 85, "optimal_max": 145, "high_max": None},
    ]
    out = _by_param(merge_sufficiency_for_crop(_GENERIC, overrides, "Macadamia"))
    # Mac override wins on the override fields; generic fields fall through.
    assert out["K"]["low_max"] == 85
    assert out["K"]["optimal_max"] == 145
    assert out["K"]["very_low_max"] == 40   # generic kept (override was None)
    assert out["K"]["high_max"] == 250      # generic kept (override was None)


def test_citrus_K_exchangeable_alias_resolves_to_K_and_shadows_generic():
    # The original bug: citrus row keyed 'K (exchangeable)', generic
    # keyed 'K' — old merge logic left both keys in the dict and the
    # override never fired against lab data labelled 'K'.
    overrides = [
        {"crop": "Citrus", "parameter": "K (exchangeable)",
         "very_low_max": 75, "low_max": 150, "optimal_max": 250, "high_max": 800},
    ]
    out = _by_param(merge_sufficiency_for_crop(_GENERIC, overrides, "Citrus"))
    # One canonical row, citrus values win, parameter name normalised.
    assert "K (exchangeable)" not in out
    assert out["K"]["low_max"] == 150
    assert out["K"]["optimal_max"] == 250
    assert out["K"]["high_max"] == 800
    assert out["K"]["parameter"] == "K"


def test_pH_method_qualifiers_stay_distinct():
    # pH (KCl) and pH (H2O) are different scales — must NOT collapse.
    overrides = [
        {"crop": "Citrus", "parameter": "pH (H2O)",
         "very_low_max": 5.3, "low_max": 6.4, "optimal_max": 7.5, "high_max": 8.0},
    ]
    out = _by_param(merge_sufficiency_for_crop(_GENERIC, overrides, "Citrus"))
    # Generic pH (KCl) untouched; citrus added a separate pH (H2O) entry.
    assert out["pH (KCl)"]["optimal_max"] == 5.5
    assert out["pH (H2O)"]["optimal_max"] == 7.5


def test_genus_fallback_when_cultivar_not_seeded():
    overrides = [
        {"crop": "Citrus", "parameter": "Mg",
         "very_low_max": 80, "low_max": 150, "optimal_max": 400, "high_max": 700},
    ]
    out = _by_param(merge_sufficiency_for_crop(_GENERIC, overrides, "Citrus (Valencia)"))
    # No exact match for "Citrus (Valencia)" — fall back to "Citrus".
    assert out["Mg"]["optimal_max"] == 400


def test_cultivar_specific_override_wins_over_genus_fallback():
    overrides = [
        {"crop": "Citrus", "parameter": "Mg",
         "very_low_max": 80, "low_max": 150, "optimal_max": 400, "high_max": 700},
        {"crop": "Citrus (Valencia)", "parameter": "Mg",
         "very_low_max": 90, "low_max": 160, "optimal_max": 420, "high_max": 720},
    ]
    out = _by_param(merge_sufficiency_for_crop(_GENERIC, overrides, "Citrus (Valencia)"))
    # Cultivar variant has its own row → no fallback to genus.
    assert out["Mg"]["optimal_max"] == 420


def test_irrelevant_crop_override_ignored():
    overrides = [
        {"crop": "Wheat", "parameter": "K",
         "very_low_max": 30, "low_max": 60, "optimal_max": 100, "high_max": 200},
    ]
    out = _by_param(merge_sufficiency_for_crop(_GENERIC, overrides, "Macadamia"))
    # Mac doesn't have its own K override; Wheat's row must NOT bleed across.
    assert out["K"]["optimal_max"] == 150


def test_parameter_field_always_canonical_after_merge():
    # Even non-canonical override input → output uses canonical name.
    overrides = [
        {"crop": "Macadamia", "parameter": "Potassium",
         "very_low_max": None, "low_max": 85, "optimal_max": 145, "high_max": None},
    ]
    out = _by_param(merge_sufficiency_for_crop(_GENERIC, overrides, "Macadamia"))
    assert "Potassium" not in out
    assert out["K"]["parameter"] == "K"
    assert out["K"]["low_max"] == 85


def test_empty_inputs_safe():
    assert merge_sufficiency_for_crop(None, None, "Wheat") == []
    assert merge_sufficiency_for_crop([], [], "Wheat") == []
