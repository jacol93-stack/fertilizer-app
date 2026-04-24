"""Shared pytest fixtures for engine tests.

The engines take plain lists/dicts (not Supabase rows), so these fixtures
mirror the shape of the seeded reference tables without needing a DB.

Values here are representative, not authoritative — they exist to lock in
current engine behavior. If reference-data shape changes, update here.
"""

from __future__ import annotations

import os
import sys

import pytest

# Make `app` importable when running pytest from sapling-api/
_HERE = os.path.dirname(os.path.abspath(__file__))
_API_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
if _API_ROOT not in sys.path:
    sys.path.insert(0, _API_ROOT)


@pytest.fixture
def sufficiency_rows():
    """Simplified universal soil sufficiency thresholds."""
    return [
        {"parameter": "pH (H2O)", "very_low_max": 4.5, "low_max": 5.5, "optimal_max": 7.0, "high_max": 8.0},
        {"parameter": "P (Bray-1)", "very_low_max": 10, "low_max": 20, "optimal_max": 40, "high_max": 60},
        {"parameter": "K", "very_low_max": 50, "low_max": 100, "optimal_max": 200, "high_max": 350},
        {"parameter": "Ca", "very_low_max": 200, "low_max": 400, "optimal_max": 1000, "high_max": 2000},
        {"parameter": "Mg", "very_low_max": 40, "low_max": 80, "optimal_max": 200, "high_max": 400},
        {"parameter": "S", "very_low_max": 5, "low_max": 10, "optimal_max": 20, "high_max": 40},
        {"parameter": "N (total)", "very_low_max": 10, "low_max": 20, "optimal_max": 40, "high_max": 60},
        {"parameter": "Zn", "very_low_max": 0.5, "low_max": 1.0, "optimal_max": 3.0, "high_max": 5.0},
        {"parameter": "B", "very_low_max": 0.2, "low_max": 0.5, "optimal_max": 1.5, "high_max": 3.0},
        {"parameter": "Mn", "very_low_max": 5, "low_max": 10, "optimal_max": 30, "high_max": 60},
        {"parameter": "Fe", "very_low_max": 5, "low_max": 10, "optimal_max": 30, "high_max": 60},
        {"parameter": "Cu", "very_low_max": 0.3, "low_max": 0.5, "optimal_max": 2.0, "high_max": 5.0},
        {"parameter": "Mo", "very_low_max": 0.05, "low_max": 0.1, "optimal_max": 0.3, "high_max": 0.5},
    ]


_TIER6_NOTE = (
    "Implementer convention per FERTASA 5.1 drawdown principle; "
    "specific numeric factors not handbook-published. See migration 067."
)


def _adj(cls, factor, group):
    """Factory so every fixture row carries the Tier-6 provenance fields that
    migration 067 enforces on the live table."""
    return {
        "classification": cls, "factor": factor, "nutrient_group": group,
        "source": "Implementer convention (SA agronomy practice)",
        "source_section": "5.1", "source_year": None,
        "source_note": _TIER6_NOTE, "tier": 6,
    }


@pytest.fixture
def adjustment_rows():
    """Adjustment factors by classification. Covers the universal fallback path."""
    return [
        _adj("Very Low",  1.5,  None),
        _adj("Low",       1.25, None),
        _adj("Optimal",   1.0,  None),
        _adj("High",      0.5,  None),
        _adj("Very High", 0.0,  None),
    ]


@pytest.fixture
def adjustment_rows_grouped():
    """Adjustment factors with nutrient-group specificity.

    Mirrors the post-migration-077 DB shape:
      - N, micro: flat 1.0
      - P: 1.5 / 1.25 / 1.0 / 0.75 / 0.5 (moderate drawdown)
      - K: 1.5 / 1.25 / 1.0 / 0.5 / 0.0 (aggressive — luxury OK)
      - ca_mg: 1.25 / 1.1 / 1.0 / 0.75 / 0.5 (gentle — base saturation)
      - S: flat 1.0 (sulfate mobility — drawdown doesn't apply)
      - cations: retained as legacy fallback shape (1.5/1.25/1.0/0.5/0.0)
    """
    curves = {
        "N":       {"Very Low": 1.0,  "Low": 1.0,  "Optimal": 1.0, "High": 1.0,  "Very High": 1.0},
        "P":       {"Very Low": 1.5,  "Low": 1.25, "Optimal": 1.0, "High": 0.75, "Very High": 0.5},
        "K":       {"Very Low": 1.5,  "Low": 1.25, "Optimal": 1.0, "High": 0.5,  "Very High": 0.0},
        "ca_mg":   {"Very Low": 1.25, "Low": 1.1,  "Optimal": 1.0, "High": 0.75, "Very High": 0.5},
        "S":       {"Very Low": 1.0,  "Low": 1.0,  "Optimal": 1.0, "High": 1.0,  "Very High": 1.0},
        "micro":   {"Very Low": 1.0,  "Low": 1.0,  "Optimal": 1.0, "High": 1.0,  "Very High": 1.0},
        # Legacy cation group retained for backwards-compat consumers;
        # mirrors the original pre-077 shape so the fallback path is
        # testable.
        "cations": {"Very Low": 1.5,  "Low": 1.25, "Optimal": 1.0, "High": 0.5,  "Very High": 0.0},
    }
    rows = []
    for g, curve in curves.items():
        for cls, factor in curve.items():
            rows.append(_adj(cls, factor, g))
    return rows


@pytest.fixture
def param_map_rows():
    """Maps engine nutrient names (N, P, K, ...) to soil lab parameter names."""
    return [
        {"crop_nutrient": "N",  "soil_parameter": "N (total)"},
        {"crop_nutrient": "P",  "soil_parameter": "P (Bray-1)"},
        {"crop_nutrient": "K",  "soil_parameter": "K"},
        {"crop_nutrient": "Ca", "soil_parameter": "Ca"},
        {"crop_nutrient": "Mg", "soil_parameter": "Mg"},
        {"crop_nutrient": "S",  "soil_parameter": "S"},
        {"crop_nutrient": "Fe", "soil_parameter": "Fe"},
        {"crop_nutrient": "B",  "soil_parameter": "B"},
        {"crop_nutrient": "Mn", "soil_parameter": "Mn"},
        {"crop_nutrient": "Zn", "soil_parameter": "Zn"},
        {"crop_nutrient": "Mo", "soil_parameter": "Mo"},
        {"crop_nutrient": "Cu", "soil_parameter": "Cu"},
    ]


@pytest.fixture
def crop_rows():
    """Per-unit nutrient requirements for a couple of representative crops."""
    return [
        {
            "crop": "Avocado",
            "n": 8.0, "p": 1.5, "k": 10.0, "ca": 3.0, "mg": 1.0, "s": 1.0,
            "fe": 0.1, "b": 0.05, "mn": 0.08, "zn": 0.05, "mo": 0.005, "cu": 0.02,
        },
        {
            "crop": "Maize",
            "n": 22.0, "p": 4.0, "k": 18.0, "ca": 3.0, "mg": 2.0, "s": 2.5,
            "fe": 0.15, "b": 0.02, "mn": 0.1, "zn": 0.08, "mo": 0.001, "cu": 0.015,
        },
    ]


@pytest.fixture
def ratio_rows():
    """Ideal nutrient ratios with min/max bands."""
    return [
        {"ratio": "Ca:Mg",  "ideal_min": 3.0, "ideal_max": 6.0, "unit": "ratio"},
        {"ratio": "Ca:K",   "ideal_min": 10.0, "ideal_max": 30.0, "unit": "ratio"},
        {"ratio": "Mg:K",   "ideal_min": 2.0, "ideal_max": 6.0, "unit": "ratio"},
        {"ratio": "P:Zn",   "ideal_min": 5.0, "ideal_max": 15.0, "unit": "ratio"},
        {"ratio": "N:S",    "ideal_min": 8.0, "ideal_max": 12.0, "unit": "ratio"},
        {"ratio": "K:Na",   "ideal_min": 2.0, "ideal_max": 6.0, "unit": "ratio"},
        {"ratio": "Ca base sat.", "ideal_min": 60.0, "ideal_max": 75.0, "unit": "%"},
        {"ratio": "Mg base sat.", "ideal_min": 10.0, "ideal_max": 15.0, "unit": "%"},
        {"ratio": "K base sat.",  "ideal_min": 3.0,  "ideal_max": 7.0,  "unit": "%"},
    ]


@pytest.fixture
def optimal_soil():
    """A soil sample where every macro nutrient classifies as Optimal."""
    return {
        "pH (H2O)": 6.5,
        "P (Bray-1)": 30,
        "K": 180,
        "Ca": 800,
        "Mg": 150,
        "S": 15,
        "N (total)": 30,
        "Zn": 2.0,
        "B": 1.0,
        "Mn": 20,
        "Fe": 20,
        "Cu": 1.0,
        "Mo": 0.2,
        "CEC": 10.0,
        "Na": 30,
    }
