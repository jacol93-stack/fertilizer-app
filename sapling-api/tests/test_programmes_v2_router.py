"""Router-level unit tests for /api/programmes/v2 helpers."""
from __future__ import annotations

from app.models import OutstandingItem, PreSeasonInput, RiskFlag, SoilSnapshot
from app.routers.programmes_v2 import (
    SkippedBlockRequest,
    _append_cluster_narrative,
    _append_n_cap_flags,
    _append_per_block_soil_snapshots,
    _append_skipped_block_items,
    _attach_dataless_blocks_to_clusters,
    _cluster_block_inputs,
)
from app.services.consolidator import _classify_stream
from app.services.programme_builder_orchestrator import BlockInput


class _StubArtifact:
    """Minimal stand-in for ProgrammeArtifact — all we need is mutable
    outstanding_items, risk_flags, decision_trace, and soil_snapshots
    lists. Lets us test router helpers without spinning up the
    orchestrator.
    """
    def __init__(self) -> None:
        self.outstanding_items: list[OutstandingItem] = []
        self.risk_flags: list[RiskFlag] = []
        self.decision_trace: list[str] = []
        self.soil_snapshots: list[SoilSnapshot] = []


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


def test_append_skipped_block_items_attached_to_cluster_emits_rough_plan():
    """Skipped block with attach_to_cluster set gets a different message —
    'on rough plan' — instead of 'not planned'."""
    artifact = _StubArtifact()
    skipped = [SkippedBlockRequest(
        block_name="Pivot 5", reason="no soil analysis linked",
        block_id="pivot_5", block_area_ha=12.0, attach_to_cluster="A",
    )]
    _append_skipped_block_items(artifact, skipped)

    item = artifact.outstanding_items[0]
    assert "rough plan" in item.item.lower()
    assert "Recipe A" in item.item
    assert "Pivot 5" in item.item
    # Guidance still nudges the agronomist to sample the block
    assert "sample" in (item.impact_if_skipped or "").lower()


# ============================================================
# dataless-block attachment to clusters
# ============================================================

def test_attach_dataless_block_merges_into_multi_cluster():
    """Dataless block joins the existing synthetic cluster — bumps area,
    block_ids/names, but doesn't add a parallel effective block. The
    cluster's recipe stays unchanged (no new soil data to average)."""
    b1 = _bi("blok-1", "Blok 1", 10.0, {"N": 100, "P2O5": 40, "K2O": 60})
    b2 = _bi("blok-2", "Blok 2", 10.0, {"N": 100, "P2O5": 40, "K2O": 60})
    effective, aggs, _ = _cluster_block_inputs([b1, b2])
    assert len(effective) == 1
    cluster_a_id = aggs[0].cluster_id
    initial_area = effective[0].block_area_ha
    initial_targets = dict(effective[0].season_targets)

    skipped = [SkippedBlockRequest(
        block_name="Blok 3 (dataless)", reason="no soil analysis linked",
        block_id="blok-3", block_area_ha=5.0, attach_to_cluster=cluster_a_id,
    )]
    _attach_dataless_blocks_to_clusters(effective, aggs, skipped)

    # ONE effective block still — the dataless block joined the cluster.
    assert len(effective) == 1
    eb = effective[0]
    # Area bumped by the dataless block
    assert eb.block_area_ha == initial_area + 5.0
    # Recipe unchanged
    assert eb.season_targets == initial_targets
    # Cluster aggregate metadata reflects all 3 blocks
    assert "blok-3" in aggs[0].block_ids
    assert "Blok 3 (dataless)" in aggs[0].block_names
    assert aggs[0].total_area_ha == initial_area + 5.0


def test_attach_dataless_block_converts_singleton_cluster():
    """Attaching to a singleton converts it to a synthetic cluster so
    multiple blocks can share the same effective_block without misleading
    lab metadata."""
    b1 = _bi("blok-1", "Blok 1", 10.0, {"N": 100, "P2O5": 40, "K2O": 60})
    effective, aggs, _ = _cluster_block_inputs([b1])
    assert len(effective) == 1
    assert effective[0].block_id == "blok-1"  # singleton — original passed through
    cid = aggs[0].cluster_id

    skipped = [SkippedBlockRequest(
        block_name="Blok 2", reason="no soil",
        block_id="blok-2", block_area_ha=4.0, attach_to_cluster=cid,
    )]
    _attach_dataless_blocks_to_clusters(effective, aggs, skipped)

    # Still one effective block, now synthetic
    assert len(effective) == 1
    eb = effective[0]
    assert eb.block_id == f"cluster_{cid}"
    assert eb.lab_name is None  # singleton's lab metadata dropped
    assert eb.block_area_ha == 14.0  # 10 + 4
    assert "blok-2" in aggs[0].block_ids


def test_attach_dataless_block_unknown_cluster_is_silent_skip():
    """Stale cluster_id (e.g. clustering re-ran and renamed) shouldn't crash;
    block falls through to OutstandingItem-only handling."""
    b1 = _bi("blok-1", "Blok 1", 10.0, {"N": 100, "P2O5": 40, "K2O": 60})
    effective, aggs, _ = _cluster_block_inputs([b1])
    pre_count = len(effective)
    pre_area = effective[0].block_area_ha
    skipped = [SkippedBlockRequest(
        block_name="Blok 2", reason="no soil analysis",
        block_id="blok-2", block_area_ha=5.0, attach_to_cluster="Z",
    )]
    _attach_dataless_blocks_to_clusters(effective, aggs, skipped)
    assert len(effective) == pre_count
    assert effective[0].block_area_ha == pre_area


def test_attach_dataless_block_missing_metadata_is_silent_skip():
    """attach_to_cluster set but block_id / area missing — can't attach."""
    b1 = _bi("blok-1", "Blok 1", 10.0, {"N": 100, "P2O5": 40, "K2O": 60})
    effective, aggs, _ = _cluster_block_inputs([b1])
    pre_area = effective[0].block_area_ha
    cid = aggs[0].cluster_id
    # Missing block_id
    _attach_dataless_blocks_to_clusters(effective, aggs, [SkippedBlockRequest(
        block_name="x", reason="r", block_area_ha=5.0, attach_to_cluster=cid,
    )])
    # Missing area
    _attach_dataless_blocks_to_clusters(effective, aggs, [SkippedBlockRequest(
        block_name="y", reason="r", block_id="bid", attach_to_cluster=cid,
    )])
    assert effective[0].block_area_ha == pre_area


def test_attach_dataless_block_no_attachment_is_noop():
    """attach_to_cluster not set → cluster area unchanged (block only
    surfaces as an OutstandingItem from _append_skipped_block_items)."""
    b1 = _bi("blok-1", "Blok 1", 10.0, {"N": 100, "P2O5": 40, "K2O": 60})
    effective, aggs, _ = _cluster_block_inputs([b1])
    pre_area = effective[0].block_area_ha
    skipped = [SkippedBlockRequest(block_name="Blok 2", reason="no soil")]
    _attach_dataless_blocks_to_clusters(effective, aggs, skipped)
    assert effective[0].block_area_ha == pre_area


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
    effective, aggs, _sources = _cluster_block_inputs([b1, b2])
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
    effective, aggs, _sources = _cluster_block_inputs([b1, b2])
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
    effective, _aggs, _sources = _cluster_block_inputs([b1, b2])
    # b1 kept singleton (pre-season); b2 clusters alone → 2 effective blocks
    assert len(effective) == 2
    assert b1 in effective


def test_append_cluster_narrative_adds_trace_for_multi_block_clusters():
    """Multi-block clusters get a decision_trace note; singletons don't."""
    b1 = _bi("1", "Land A", 2.0, {"N": 100, "P2O5": 40, "K2O": 60})
    b2 = _bi("2", "Land B", 8.0, {"N": 100, "P2O5": 40, "K2O": 60})
    _, aggs, _ = _cluster_block_inputs([b1, b2])

    artifact = _StubArtifact()
    _append_cluster_narrative(artifact, aggs)
    assert any("Clustered" in t for t in artifact.decision_trace)


def test_append_cluster_narrative_no_trace_for_all_singletons():
    b1 = _bi("1", "Land A", 10.0, {"N": 200, "P2O5": 40, "K2O": 20})
    b2 = _bi("2", "Land B", 10.0, {"N": 20, "P2O5": 40, "K2O": 200})
    _, aggs, _ = _cluster_block_inputs([b1, b2])

    artifact = _StubArtifact()
    _append_cluster_narrative(artifact, aggs)
    # No multi-block clusters → no trace, no risk flags
    assert artifact.decision_trace == []
    assert artifact.risk_flags == []


def test_append_per_block_soil_snapshots_for_multi_block_cluster():
    """Multi-block cluster → per-original-block SoilSnapshots appended,
    each with the block's raw soil_parameters + lab metadata, labelled
    with '(in Cluster X)' so the viewer knows the context."""
    # pH delta kept below the soil-state split threshold (0.8 units) so
    # the auto-refiner doesn't break this cluster apart — the test is
    # about snapshot emission, not clustering policy.
    b1 = _bi("1", "Land A", 2.0, {"N": 100, "P2O5": 40, "K2O": 60},
             soil={"pH": 5.7, "P_mgkg": 10})
    b2 = _bi("2", "Land B", 8.0, {"N": 100, "P2O5": 40, "K2O": 60},
             soil={"pH": 6.0, "P_mgkg": 30})
    _effective, _aggs, sources = _cluster_block_inputs([b1, b2])

    artifact = _StubArtifact()
    _append_per_block_soil_snapshots(artifact, sources)

    # Two per-block snapshots added
    assert len(artifact.soil_snapshots) == 2
    names = [s.block_name for s in artifact.soil_snapshots]
    assert any("Land A (in Cluster" in n for n in names)
    assert any("Land B (in Cluster" in n for n in names)
    # Raw parameters preserved — not the cluster's aggregated mean
    land_a = next(s for s in artifact.soil_snapshots if "Land A" in s.block_name)
    assert land_a.parameters["pH"] == 5.7
    assert land_a.parameters["P_mgkg"] == 10


def test_append_per_block_soil_snapshots_noop_for_singletons():
    """All-singleton input → no per-block snapshots added. The
    orchestrator already emitted one-snapshot-per-real-block."""
    b1 = _bi("1", "Land A", 10.0, {"N": 200, "P2O5": 40, "K2O": 20},
             soil={"pH": 5.5})
    b2 = _bi("2", "Land B", 10.0, {"N": 20, "P2O5": 40, "K2O": 200},
             soil={"pH": 7.0})
    _effective, _aggs, sources = _cluster_block_inputs([b1, b2])

    artifact = _StubArtifact()
    _append_per_block_soil_snapshots(artifact, sources)
    assert artifact.soil_snapshots == []


def test_auto_split_breaks_heterogeneous_cluster_by_worst_nutrient():
    """Three blocks with the same NPK ratio but very different absolute
    amounts get auto-split by the post-clustering pass — what would have
    been one heterogeneous cluster becomes two homogeneous ones, sorted
    by the worst-CV nutrient (K2O here). Replaces the prior contract
    where the system surfaced a heterogeneity warning instead of acting
    on it."""
    b1 = _bi("1", "Land A", 10.0, {"N": 120, "P2O5": 60, "K2O": 60})
    b2 = _bi("2", "Land B", 10.0, {"N": 360, "P2O5": 180, "K2O": 180})
    b3 = _bi("3", "Land C", 10.0, {"N": 480, "P2O5": 240, "K2O": 240})
    effective, aggs, _sources = _cluster_block_inputs([b1, b2, b3])
    # Auto-split kicks in: median split on K2O → low (b1) | high (b2,b3)
    assert len(aggs) == 2
    cluster_block_counts = sorted(len(a.block_ids) for a in aggs)
    assert cluster_block_counts == [1, 2]
    # Neither resulting cluster should still be split-level
    assert all(not a.heterogeneity.any_split for a in aggs)

    artifact = _StubArtifact()
    _append_cluster_narrative(artifact, aggs)
    # No RiskFlag because each resulting cluster is below the split
    # threshold — the auto-split addressed the underlying problem.
    assert artifact.risk_flags == []


def test_auto_split_separates_blocks_with_extreme_pH_spread():
    """Blocks with the same NPK ratio + similar absolute amounts but
    very different pH must split. An averaged programme pH-blind to
    the spread would lime an alkaline block (locking out micros) or
    pull an acidic block further down."""
    # Same recipe shape and similar magnitudes — pre-fix this would
    # cluster into one. pH delta of 3.2 units exceeds the 0.8 split
    # threshold and forces a split on soil-state alone.
    b1 = _bi("1", "Acid block", 10.0, {"N": 100, "P2O5": 40, "K2O": 60},
             soil={"pH (KCl)": 4.4})
    b2 = _bi("2", "Mid block", 10.0, {"N": 100, "P2O5": 40, "K2O": 60},
             soil={"pH (KCl)": 5.5})
    b3 = _bi("3", "Alkaline block", 10.0, {"N": 100, "P2O5": 40, "K2O": 60},
             soil={"pH (KCl)": 7.6})
    _, aggs, _ = _cluster_block_inputs([b1, b2, b3])
    # At least 2 sub-clusters — extreme blocks must NOT share a group
    assert len(aggs) >= 2
    # Acid + alkaline blocks must not share the same cluster
    cluster_for = {}
    for a in aggs:
        for bid in a.block_ids:
            cluster_for[bid] = a.cluster_id
    assert cluster_for["1"] != cluster_for["3"], (
        "pH 4.4 and pH 7.6 must not share a cluster"
    )


# ============================================================
# N/ha sanity cap
# ============================================================

class _StubArtifactWithTotals(_StubArtifact):
    def __init__(self, totals: dict):
        super().__init__()
        self.block_totals = totals


def test_n_cap_flag_critical_above_500():
    """N > 500 kg/ha = almost certainly a yield-target typo."""
    a = _StubArtifactWithTotals({"Block A": {"N": 550.0}})
    _append_n_cap_flags(a)
    assert len(a.risk_flags) == 1
    assert a.risk_flags[0].severity == "critical"
    assert "Block A" in a.risk_flags[0].message
    assert "yield-target typo" in a.risk_flags[0].message.lower()


def test_n_cap_flag_warn_between_350_and_500():
    a = _StubArtifactWithTotals({"Block B": {"N": 400.0}})
    _append_n_cap_flags(a)
    assert len(a.risk_flags) == 1
    assert a.risk_flags[0].severity == "warn"


def test_n_cap_no_flag_below_350():
    """Normal range (300 kg/ha for high-yield maize etc) gets no flag."""
    a = _StubArtifactWithTotals({"Block C": {"N": 280.0}})
    _append_n_cap_flags(a)
    assert a.risk_flags == []


def test_n_cap_handles_missing_n_totals():
    """block_totals without an N key should no-op, not crash."""
    a = _StubArtifactWithTotals({"Block D": {"P2O5": 80.0}})
    _append_n_cap_flags(a)
    assert a.risk_flags == []


# ============================================================
# Part A/B stream classifier — Mg inclusion
# ============================================================

def test_classify_stream_mg_nitrate_goes_part_a():
    """Mg Nitrate (N 11%, Mg 15%, S 0%) is a calcium-stream product
    per FERTASA §11 — previously misclassified as B because Ca < 5."""
    mg_nitrate = {"n": 11, "ca": 0, "mg": 15, "s": 0, "p": 0}
    assert _classify_stream(mg_nitrate) == "A"


def test_classify_stream_mgso4_stays_part_b():
    """Epsom salts (Mg 16%, S 13%) goes B because S ≥ 2 dominates —
    otherwise it'd form CaSO4 precipitate with Ca Nitrate."""
    mgso4 = {"ca": 0, "mg": 16, "s": 13, "p": 0}
    assert _classify_stream(mgso4) == "B"


def test_classify_stream_ca_nitrate_still_part_a():
    """Regression: adding the Mg limb must not demote Ca products."""
    ca_nitrate = {"n": 15, "ca": 19, "mg": 0, "s": 0, "p": 0}
    assert _classify_stream(ca_nitrate) == "A"


def test_classify_stream_metabophos_stays_part_b():
    """Metabophos (N 0, P 19, Ca 19, S 11): Ca ≥ 5 but S ≥ 2 and P ≥ 2
    dominate → B (sulphate+phosphate stream). Original corner case."""
    metab = {"n": 0, "p": 19, "ca": 19, "mg": 0, "s": 11}
    assert _classify_stream(metab) == "B"
