"""Unit tests for Level 2 programme-group aggregation + heterogeneity gate.

Covers:
* Area-weighted mean of per-block nutrient targets
* Fallback to equal weights when any block lacks a positive area
* Per-nutrient CV threshold classification (Wilding-derived)
* `any_warn` / `any_split` roll-up flags
* Template-item aggregation across a group (non-foliar path)
"""

from __future__ import annotations

import pytest

from app.services.programme_engine import (
    _aggregate_blend_group,
    _build_group_template_items,
    _classify_heterogeneity,
)


def _block(name, area_ha, targets):
    return {
        "block": {
            "name": name,
            "area_ha": area_ha,
            "crop": "Maize",
            "nutrient_targets": targets,
        },
        "items": [],
        "npk_profile": (0, 0, 0),
    }


def test_single_block_group_has_no_heterogeneity_warnings():
    g = [_block("A", 10, [
        {"Nutrient": "N", "Target_kg_ha": 120},
        {"Nutrient": "P", "Target_kg_ha": 40},
    ])]
    result = _aggregate_blend_group(g)
    assert result["heterogeneity"]["any_warn"] is False
    assert result["heterogeneity"]["any_split"] is False
    assert result["heterogeneity"]["warnings"] == []
    assert result["weight_strategy"] == "area_weighted"


def test_area_weighted_mean_of_targets():
    # 2 ha block at N=100 + 8 ha block at N=200 → weighted mean N=180
    g = [
        _block("A", 2, [{"Nutrient": "N", "Target_kg_ha": 100}]),
        _block("B", 8, [{"Nutrient": "N", "Target_kg_ha": 200}]),
    ]
    result = _aggregate_blend_group(g)
    n_target = next(t for t in result["aggregated_targets"] if t["Nutrient"] == "N")
    assert n_target["Target_kg_ha"] == pytest.approx(180.0)
    assert result["weight_strategy"] == "area_weighted"


def test_missing_area_falls_back_to_equal():
    g = [
        _block("A", 2, [{"Nutrient": "N", "Target_kg_ha": 100}]),
        _block("B", None, [{"Nutrient": "N", "Target_kg_ha": 200}]),
    ]
    result = _aggregate_blend_group(g)
    n_target = next(t for t in result["aggregated_targets"] if t["Nutrient"] == "N")
    # Equal weights → mean is 150, not the weighted 180
    assert n_target["Target_kg_ha"] == pytest.approx(150.0)
    assert result["weight_strategy"] == "equal"


def test_p_cv_above_50pct_flags_split():
    """P has a wider threshold (warn 35 / split 50) because in-field P CVs
    of 40–100% are empirically normal. A CV clearly above 50% should
    trigger the 'split' level."""
    g = [
        _block("A", 10, [{"Nutrient": "P", "Target_kg_ha": 10}]),
        _block("B", 10, [{"Nutrient": "P", "Target_kg_ha": 30}]),
        _block("C", 10, [{"Nutrient": "P", "Target_kg_ha": 80}]),
    ]
    result = _aggregate_blend_group(g)
    per_nut = result["heterogeneity"]["per_nutrient"]
    assert per_nut["P"]["level"] == "split"
    assert result["heterogeneity"]["any_split"] is True
    assert any(w["nutrient"] == "P" and w["level"] == "split"
               for w in result["heterogeneity"]["warnings"])


def test_k_cv_between_warn_and_split_flags_warn():
    # K [100, 180, 230] → mean 170, pop std ≈53.5, CV ≈31.5%
    # Above 25 (K warn), below 35 (K split)
    g = [
        _block("A", 10, [{"Nutrient": "K", "Target_kg_ha": 100}]),
        _block("B", 10, [{"Nutrient": "K", "Target_kg_ha": 180}]),
        _block("C", 10, [{"Nutrient": "K", "Target_kg_ha": 230}]),
    ]
    result = _aggregate_blend_group(g)
    per_nut = result["heterogeneity"]["per_nutrient"]
    assert per_nut["K"]["level"] == "warn", f"expected warn, got {per_nut['K']}"
    assert result["heterogeneity"]["any_warn"] is True
    assert result["heterogeneity"]["any_split"] is False


def test_tight_variation_is_ok():
    # All within ~5% — comfortably below every threshold
    g = [
        _block("A", 10, [{"Nutrient": "N", "Target_kg_ha": 100}]),
        _block("B", 10, [{"Nutrient": "N", "Target_kg_ha": 105}]),
        _block("C", 10, [{"Nutrient": "N", "Target_kg_ha": 95}]),
    ]
    result = _aggregate_blend_group(g)
    per_nut = result["heterogeneity"]["per_nutrient"]
    assert per_nut["N"]["level"] == "ok"
    assert result["heterogeneity"]["any_warn"] is False
    assert result["heterogeneity"]["any_split"] is False


def test_classify_heterogeneity_uses_per_nutrient_thresholds():
    # P gets wider band than K
    assert _classify_heterogeneity("P", 40.0) == "warn"    # 35 < 40 < 50
    assert _classify_heterogeneity("K", 40.0) == "split"   # 35 <= 40
    assert _classify_heterogeneity("P", 20.0) == "ok"
    assert _classify_heterogeneity("P", None) == "ok"


def test_fallback_threshold_for_unlisted_nutrient():
    # Fe is not in HETEROGENEITY_THRESHOLDS — uses the generic 30/50 fallback
    assert _classify_heterogeneity("Fe", 35.0) == "warn"
    assert _classify_heterogeneity("Fe", 55.0) == "split"


def test_warnings_include_threshold_context():
    g = [
        _block("A", 10, [{"Nutrient": "P", "Target_kg_ha": 10}]),
        _block("B", 10, [{"Nutrient": "P", "Target_kg_ha": 30}]),
        _block("C", 10, [{"Nutrient": "P", "Target_kg_ha": 80}]),
    ]
    result = _aggregate_blend_group(g)
    p_warning = next(
        w for w in result["heterogeneity"]["warnings"] if w["nutrient"] == "P"
    )
    # Split threshold for P is 50%
    assert p_warning["threshold_pct"] == 50.0
    assert p_warning["cv_pct"] is not None


def test_citation_is_carried_in_response():
    g = [_block("A", 10, [{"Nutrient": "N", "Target_kg_ha": 100}])]
    result = _aggregate_blend_group(g)
    assert "Wilding" in result["heterogeneity"]["citation"]


def test_empty_group_returns_empty_shape():
    result = _aggregate_blend_group([])
    assert result["aggregated_targets"] == []
    assert result["heterogeneity"]["any_warn"] is False
    assert result["heterogeneity"]["warnings"] == []


def test_blocks_without_targets_skipped():
    g = [
        _block("A", 10, [{"Nutrient": "N", "Target_kg_ha": 100}]),
        _block("B", 10, []),  # no targets — should be skipped, not crash
    ]
    result = _aggregate_blend_group(g)
    # Mean of just block A
    n_target = next(t for t in result["aggregated_targets"] if t["Nutrient"] == "N")
    assert n_target["Target_kg_ha"] == pytest.approx(100.0)


def test_template_items_area_weighted_across_group():
    """_build_group_template_items should produce area-weighted nutrient
    kg_ha instead of just copying the first block's plan."""
    group = [
        {
            "block": {"name": "A", "area_ha": 2, "crop": "Maize"},
            "items": [{
                "stage": "planting", "month_target": 10, "method": "broadcast",
                "n_kg_ha": 50, "p_kg_ha": 20, "k_kg_ha": 30, "total_kg_ha": 100,
            }],
        },
        {
            "block": {"name": "B", "area_ha": 8, "crop": "Maize"},
            "items": [{
                "stage": "planting", "month_target": 10, "method": "broadcast",
                "n_kg_ha": 100, "p_kg_ha": 40, "k_kg_ha": 60, "total_kg_ha": 200,
            }],
        },
    ]
    result = _build_group_template_items(group)
    # Area-weighted: 2ha at 50N + 8ha at 100N → 90N
    assert result[0]["n_kg_ha"] == pytest.approx(90.0)
    assert result[0]["p_kg_ha"] == pytest.approx(36.0)
    assert result[0]["k_kg_ha"] == pytest.approx(54.0)
    # total_kg_ha is recomputed from the aggregated vector
    assert result[0]["total_kg_ha"] == pytest.approx(180.0)
    # Metadata from the first block is preserved
    assert result[0]["stage"] == "planting"
    assert result[0]["method"] == "broadcast"


def test_template_items_pass_foliar_through_unchanged():
    """Foliar items carry product recommendations — mechanically averaging
    them produces numbers no product matches. Pass through as-is."""
    group = [
        {
            "block": {"name": "A", "area_ha": 2, "crop": "Maize"},
            "items": [{"method": "foliar", "n_kg_ha": 5, "foliar_recommendations": ["Productive A"]}],
        },
        {
            "block": {"name": "B", "area_ha": 8, "crop": "Maize"},
            "items": [{"method": "foliar", "n_kg_ha": 10, "foliar_recommendations": ["Productive A"]}],
        },
    ]
    result = _build_group_template_items(group)
    # First block's foliar item is returned verbatim
    assert result[0]["n_kg_ha"] == 5
    assert result[0]["foliar_recommendations"] == ["Productive A"]
