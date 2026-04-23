"""Router-level unit tests for /api/programmes/v2 helpers."""
from __future__ import annotations

from app.models import OutstandingItem, PreSeasonInput, RiskFlag
from app.routers.programmes_v2 import (
    SkippedBlockRequest,
    _append_cluster_narrative,
    _append_skipped_block_items,
    _cluster_block_inputs,
)
from app.services.programme_builder_orchestrator import BlockInput


class _StubArtifact:
    """Minimal stand-in for ProgrammeArtifact — all we need is mutable
    outstanding_items, risk_flags, and decision_trace lists. Lets us
    test router helpers without spinning up the orchestrator.
    """
    def __init__(self) -> None:
        self.outstanding_items: list[OutstandingItem] = []
        self.risk_flags: list[RiskFlag] = []
        self.decision_trace: list[str] = []


def test_append_skipped_block_items_empty_input_is_noop():
    artifact = _StubArtifact()
    _append_skipped_block_items(artifact, [])
    assert artifact.outstanding_items == []


def test_append_skipped_block_items_adds_one_per_block():
    artifact = _StubArtifact()
    skipped = [
        SkippedBlockRequest(block_name="Land A", reason="no soil analysis linked"),
        SkippedBlockRequest(block_name="Pivot 2", reason="no soil analysis linked"),
    ]
    _append_skipped_block_items(artifact, skipped)

    assert len(artifact.outstanding_items) == 2
    names = [item.item for item in artifact.outstanding_items]
    assert any("Land A" in n for n in names)
    assert any("Pivot 2" in n for n in names)


def test_append_skipped_block_items_includes_reason_and_guidance():
    artifact = _StubArtifact()
    skipped = [SkippedBlockRequest(block_name="Land C", reason="custom reason here")]
    _append_skipped_block_items(artifact, skipped)

    item = artifact.outstanding_items[0]
    assert "Land C" in item.item
    assert "custom reason here" in item.item
    # why_it_matters + impact_if_skipped guide the agronomist
    assert item.why_it_matters
    assert item.impact_if_skipped
    assert "soil analysis" in (item.impact_if_skipped or "").lower()


def test_append_skipped_block_items_preserves_existing_items():
    artifact = _StubArtifact()
    existing = OutstandingItem(
        item="Existing item",
        why_it_matters="unrelated prior finding",
    )
    artifact.outstanding_items.append(existing)

    _append_skipped_block_items(artifact, [
        SkippedBlockRequest(block_name="Land D", reason="no soil analysis linked"),
    ])

    assert len(artifact.outstanding_items) == 2
    assert artifact.outstanding_items[0] is existing
    assert "Land D" in artifact.outstanding_items[1].item


# ============================================================
# Phase 3 — clustering helpers
# ============================================================

def _bi(block_id: str, name: str, area: float, targets: dict,
        soil=None, pre_season=None) -> BlockInput:
    """Build a BlockInput with sensible defaults for tests."""
    return BlockInput(
        block_id=block_id,
        block_name=name,
        block_area_ha=area,
        soil_parameters=soil or {},
        season_targets=targets,
        pre_season_inputs=pre_season or [],
    )


def test_cluster_block_inputs_preserves_singleton_blocks_by_reference():
    """Singleton clusters should pass the original BlockInput through
    untouched — preserves lab metadata etc."""
    b1 = _bi("1", "Land A", 10.0, {"N": 120, "P2O5": 40, "K2O": 60})
    b2 = _bi("2", "Land B", 10.0, {"N": 20, "P2O5": 40, "K2O": 200})
    effective, aggs = _cluster_block_inputs([b1, b2])
    assert len(effective) == 2
    assert b1 in effective
    assert b2 in effective
    # Each cluster is a singleton
    assert len(aggs) == 2
    assert all(len(a.block_ids) == 1 for a in aggs)


def test_cluster_block_inputs_aggregates_similar_blocks():
    """Two blocks with the same NPK ratio collapse into one synthetic
    BlockInput with area-weighted targets."""
    b1 = _bi("1", "Land A", 2.0, {"N": 100, "P2O5": 40, "K2O": 60})
    b2 = _bi("2", "Land B", 8.0, {"N": 100, "P2O5": 40, "K2O": 60})
    effective, aggs = _cluster_block_inputs([b1, b2])
    assert len(effective) == 1
    assert len(aggs) == 1
    assert len(aggs[0].block_ids) == 2

    eb = effective[0]
    assert eb.block_id.startswith("cluster_")
    assert eb.block_area_ha == 10.0
    # Identical inputs → aggregated = same
    assert eb.season_targets["N"] == 100


def test_cluster_block_inputs_excludes_blocks_with_pre_season_inputs():
    """Blocks with pre_season_inputs must stay as singletons — those
    inputs are per-block history, not safe to combine across blocks."""
    ps = [PreSeasonInput(
        product="Lime", rate="2 t/ha", contribution_per_ha="2 t/ha",
        status_at_planting="settled",
        effective_n_kg_per_ha=0, effective_p2o5_kg_per_ha=0,
        effective_k2o_kg_per_ha=0, effective_ca_kg_per_ha=800,
        effective_mg_kg_per_ha=0, effective_s_kg_per_ha=0,
    )]
    b1 = _bi("1", "Land A", 10.0, {"N": 100, "P2O5": 40, "K2O": 60}, pre_season=ps)
    b2 = _bi("2", "Land B", 10.0, {"N": 100, "P2O5": 40, "K2O": 60})
    effective, _ = _cluster_block_inputs([b1, b2])
    # b1 kept singleton (pre-season); b2 clusters alone → 2 effective blocks
    assert len(effective) == 2
    assert b1 in effective


def test_append_cluster_narrative_adds_trace_for_multi_block_clusters():
    """Multi-block clusters get a decision_trace note; singletons don't."""
    b1 = _bi("1", "Land A", 2.0, {"N": 100, "P2O5": 40, "K2O": 60})
    b2 = _bi("2", "Land B", 8.0, {"N": 100, "P2O5": 40, "K2O": 60})
    _, aggs = _cluster_block_inputs([b1, b2])

    artifact = _StubArtifact()
    _append_cluster_narrative(artifact, aggs)
    assert any("Clustered" in t for t in artifact.decision_trace)


def test_append_cluster_narrative_no_trace_for_all_singletons():
    b1 = _bi("1", "Land A", 10.0, {"N": 200, "P2O5": 40, "K2O": 20})
    b2 = _bi("2", "Land B", 10.0, {"N": 20, "P2O5": 40, "K2O": 200})
    _, aggs = _cluster_block_inputs([b1, b2])

    artifact = _StubArtifact()
    _append_cluster_narrative(artifact, aggs)
    # No multi-block clusters → no trace, no risk flags
    assert artifact.decision_trace == []
    assert artifact.risk_flags == []


def test_append_cluster_narrative_emits_risk_flag_on_heterogeneity():
    """Cluster with high nutrient variation produces a critical/watch
    RiskFlag naming the affected nutrients."""
    # Same NPK ratio (20:10:10 across the board) so they cluster, but
    # very different absolute K2O: 60, 180, 240 → CV ~48% → split-level
    # (K2O split threshold is 35%).
    b1 = _bi("1", "Land A", 10.0, {"N": 120, "P2O5": 60, "K2O": 60})
    b2 = _bi("2", "Land B", 10.0, {"N": 360, "P2O5": 180, "K2O": 180})
    b3 = _bi("3", "Land C", 10.0, {"N": 480, "P2O5": 240, "K2O": 240})
    effective, aggs = _cluster_block_inputs([b1, b2, b3])
    # All three have the same ratio (2:1:1) → one cluster
    assert len(aggs) == 1
    assert len(aggs[0].block_ids) == 3

    artifact = _StubArtifact()
    _append_cluster_narrative(artifact, aggs)
    assert len(artifact.risk_flags) == 1
    msg = artifact.risk_flags[0].message
    assert "Cluster" in msg
    assert "K2O" in msg
    # Split → "Consider splitting" message; citation included
    assert artifact.risk_flags[0].severity == "critical"
    assert "splitting" in msg.lower()
    assert "Wilding" in msg
