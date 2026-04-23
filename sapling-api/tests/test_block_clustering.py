"""Unit tests for Phase 3 block clustering + area-weighted aggregation.

Mirrors the legacy test_programme_heterogeneity.py contract but against
the v2 block_clustering module, which operates on orchestrator
BlockInput-shaped objects rather than legacy programme_engine dicts.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.services.block_clustering import (
    HETEROGENEITY_CITATION,
    aggregate_cluster,
    classify_heterogeneity,
    cluster_and_aggregate,
    cluster_blocks_by_npk,
)


@dataclass
class _StubBlock:
    """Stand-in for BlockInput with only the fields clustering touches.

    Avoids importing BlockInput (which lives in the orchestrator) to
    keep these tests pure to the clustering module.
    """
    block_id: str
    block_name: str
    block_area_ha: float | None
    season_targets: dict
    soil_parameters: dict | None = None


# ============================================================
# clustering behavior
# ============================================================

def test_single_block_produces_single_cluster():
    blocks = [_StubBlock("1", "Land A", 10.0, {"N": 120, "P2O5": 40, "K2O": 60})]
    groups = cluster_blocks_by_npk(blocks)
    assert len(groups) == 1
    assert groups[0][0].block_id == "1"


def test_similar_ratios_share_a_cluster():
    # Same ratios, different absolute scale — same cluster
    blocks = [
        _StubBlock("1", "A", 10.0, {"N": 100, "P2O5": 40, "K2O": 60}),
        _StubBlock("2", "B", 5.0, {"N": 150, "P2O5": 60, "K2O": 90}),
    ]
    groups = cluster_blocks_by_npk(blocks)
    assert len(groups) == 1
    assert {b.block_id for b in groups[0]} == {"1", "2"}


def test_dissimilar_ratios_split_into_clusters():
    # Block 1 is N-heavy; block 2 is K-heavy. Ratios differ > 0.15.
    blocks = [
        _StubBlock("1", "A", 10.0, {"N": 200, "P2O5": 40, "K2O": 20}),
        _StubBlock("2", "B", 10.0, {"N": 20, "P2O5": 40, "K2O": 200}),
    ]
    groups = cluster_blocks_by_npk(blocks)
    assert len(groups) == 2


def test_zero_total_block_becomes_singleton():
    blocks = [
        _StubBlock("1", "A", 10.0, {}),
        _StubBlock("2", "B", 10.0, {"N": 100, "P2O5": 40, "K2O": 60}),
    ]
    groups = cluster_blocks_by_npk(blocks)
    # Block 1 has no targets → singleton; block 2 is its own cluster
    assert len(groups) == 2


def test_empty_input_returns_empty():
    assert cluster_blocks_by_npk([]) == []


# ============================================================
# aggregation — area-weighted vs equal
# ============================================================

def test_area_weighted_mean_of_targets():
    # 2 ha at N=100 + 8 ha at N=200 → weighted mean 180
    blocks = [
        _StubBlock("1", "A", 2.0, {"N": 100}),
        _StubBlock("2", "B", 8.0, {"N": 200}),
    ]
    agg = aggregate_cluster(blocks, cluster_id="A")
    assert agg.aggregated_targets["N"] == pytest.approx(180.0)
    assert agg.weight_strategy == "area_weighted"
    assert agg.total_area_ha == pytest.approx(10.0)
    assert agg.cluster_id == "A"


def test_missing_area_falls_back_to_equal_weights():
    blocks = [
        _StubBlock("1", "A", 2.0, {"N": 100}),
        _StubBlock("2", "B", None, {"N": 200}),
    ]
    agg = aggregate_cluster(blocks, cluster_id="A")
    # Equal weights → 150, not the area-weighted 180
    assert agg.aggregated_targets["N"] == pytest.approx(150.0)
    assert agg.weight_strategy == "equal"


def test_soil_parameters_also_aggregated_area_weighted():
    blocks = [
        _StubBlock("1", "A", 2.0, {"N": 100}, soil_parameters={"pH": 6.0, "P_mgkg": 10}),
        _StubBlock("2", "B", 8.0, {"N": 100}, soil_parameters={"pH": 7.0, "P_mgkg": 30}),
    ]
    agg = aggregate_cluster(blocks, cluster_id="A")
    assert agg.aggregated_soil_parameters["pH"] == pytest.approx(6.8)  # 0.2*6 + 0.8*7
    assert agg.aggregated_soil_parameters["P_mgkg"] == pytest.approx(26.0)  # 0.2*10 + 0.8*30


def test_single_block_cluster_is_passthrough():
    blocks = [_StubBlock("1", "A", 10.0, {"N": 120, "P2O5": 40, "K2O": 60})]
    agg = aggregate_cluster(blocks, cluster_id="A")
    assert agg.aggregated_targets["N"] == pytest.approx(120.0)
    # Single-sample aggregation never has heterogeneity warnings
    assert agg.heterogeneity.any_warn is False
    assert agg.heterogeneity.any_split is False


# ============================================================
# heterogeneity — CV classification
# ============================================================

def test_p2o5_cv_above_50pct_flags_split():
    """P2O5 gets the wider (35/50) band — CVs of 50%+ trigger 'split'."""
    blocks = [
        _StubBlock("1", "A", 10.0, {"P2O5": 10}),
        _StubBlock("2", "B", 10.0, {"P2O5": 30}),
        _StubBlock("3", "C", 10.0, {"P2O5": 80}),
    ]
    agg = aggregate_cluster(blocks, cluster_id="A")
    per_nut = agg.heterogeneity.per_nutrient
    assert per_nut["P2O5"]["level"] == "split"
    assert agg.heterogeneity.any_split is True
    # any_warn rolls up splits
    assert agg.heterogeneity.any_warn is True


def test_k2o_cv_between_warn_and_split_flags_warn():
    # K2O [100, 180, 230] → CV ~31.5% → above 25 (warn), below 35 (split)
    blocks = [
        _StubBlock("1", "A", 10.0, {"K2O": 100}),
        _StubBlock("2", "B", 10.0, {"K2O": 180}),
        _StubBlock("3", "C", 10.0, {"K2O": 230}),
    ]
    agg = aggregate_cluster(blocks, cluster_id="A")
    assert agg.heterogeneity.per_nutrient["K2O"]["level"] == "warn"
    assert agg.heterogeneity.any_warn is True
    assert agg.heterogeneity.any_split is False


def test_tight_variation_is_ok():
    blocks = [
        _StubBlock("1", "A", 10.0, {"N": 100}),
        _StubBlock("2", "B", 10.0, {"N": 105}),
        _StubBlock("3", "C", 10.0, {"N": 95}),
    ]
    agg = aggregate_cluster(blocks, cluster_id="A")
    assert agg.heterogeneity.per_nutrient["N"]["level"] == "ok"
    assert agg.heterogeneity.any_warn is False
    assert agg.heterogeneity.any_split is False


def test_classify_heterogeneity_uses_oxide_keyed_thresholds():
    # P2O5 (35/50) vs K2O (25/35) — different bands, same CV classifies
    # differently
    assert classify_heterogeneity("P2O5", 40.0) == "warn"   # 35 <= 40 < 50
    assert classify_heterogeneity("K2O", 40.0) == "split"   # 35 <= 40
    assert classify_heterogeneity("P2O5", 20.0) == "ok"
    assert classify_heterogeneity("P2O5", None) == "ok"


def test_unknown_nutrient_uses_fallback_threshold():
    # Fe not listed → fallback 30/50
    assert classify_heterogeneity("Fe", 35.0) == "warn"
    assert classify_heterogeneity("Fe", 55.0) == "split"


def test_warnings_include_threshold_context():
    blocks = [
        _StubBlock("1", "A", 10.0, {"P2O5": 10}),
        _StubBlock("2", "B", 10.0, {"P2O5": 30}),
        _StubBlock("3", "C", 10.0, {"P2O5": 80}),
    ]
    agg = aggregate_cluster(blocks, cluster_id="A")
    p_warning = next(w for w in agg.heterogeneity.warnings if w.nutrient == "P2O5")
    assert p_warning.threshold_pct == 50.0
    assert p_warning.cv_pct is not None
    assert p_warning.level == "split"


def test_citation_carried_on_the_report():
    blocks = [_StubBlock("1", "A", 10.0, {"N": 100})]
    agg = aggregate_cluster(blocks, cluster_id="A")
    assert "Wilding" in agg.heterogeneity.citation
    assert agg.heterogeneity.citation == HETEROGENEITY_CITATION


# ============================================================
# end-to-end cluster_and_aggregate
# ============================================================

def test_cluster_and_aggregate_produces_labelled_clusters():
    blocks = [
        _StubBlock("1", "A", 10.0, {"N": 100, "P2O5": 40, "K2O": 60}),
        _StubBlock("2", "B", 10.0, {"N": 100, "P2O5": 40, "K2O": 60}),
        _StubBlock("3", "C", 10.0, {"N": 200, "P2O5": 40, "K2O": 20}),
    ]
    clusters = cluster_and_aggregate(blocks)
    # Blocks 1+2 same ratio → share cluster A; block 3 different → B
    assert len(clusters) == 2
    assert clusters[0].cluster_id == "A"
    assert clusters[1].cluster_id == "B"
    assert set(clusters[0].block_ids) == {"1", "2"}
    assert clusters[1].block_ids == ["3"]


def test_cluster_and_aggregate_empty_input_returns_empty():
    assert cluster_and_aggregate([]) == []


def test_identical_blocks_aggregate_to_the_input_values():
    """Sanity — aggregating identical blocks gives back the inputs."""
    targets = {"N": 150, "P2O5": 50, "K2O": 80, "Ca": 30, "Mg": 10, "S": 20}
    blocks = [
        _StubBlock(str(i), f"Block {i}", 10.0, targets.copy())
        for i in range(1, 4)
    ]
    clusters = cluster_and_aggregate(blocks)
    assert len(clusters) == 1
    for nut, val in targets.items():
        assert clusters[0].aggregated_targets[nut] == pytest.approx(val)
    # Identical inputs → zero CV → no warnings
    assert clusters[0].heterogeneity.any_warn is False
