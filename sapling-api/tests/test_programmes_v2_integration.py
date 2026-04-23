"""Integration tests for the /api/programmes/v2/build endpoint.

Exercises the full router flow — target prep, Phase 3 clustering,
orchestrator, skipped-block wiring, cluster narrative, per-block
snapshot preservation, and artifact persistence — against a stubbed
Supabase. Catches integration regressions that the unit tests on the
individual helpers don't.

Uses `asyncio.run` to drive the async endpoint directly rather than
spinning up a TestClient, keeping the test surface small.
"""
from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace

import pytest

from app.routers import programmes_v2 as pv2
from app.routers.programmes_v2 import (
    BlockRequest,
    BuildProgrammeRequest,
    MethodAvailability,
    SkippedBlockRequest,
    build_programme_endpoint,
)


# ============================================================
# Fake Supabase — enough surface for the build endpoint
# ============================================================

class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    """Chainable stub — supports select/insert/execute chains the
    router uses. Everything else raises AttributeError intentionally
    (fail loud if the test hits an unexpected path)."""

    def __init__(self, store: dict, table: str):
        self._store = store
        self._table = table
        self._payload = None

    def select(self, *_args, **_kwargs):
        return self

    def insert(self, payload: dict):
        self._payload = payload
        return self

    def execute(self):
        if self._payload is not None:
            # Assign a fake id + echo back the inserted row (Supabase
            # behavior with returning='representation').
            row = {**self._payload, "id": str(uuid.uuid4())}
            self._store.setdefault(self._table, []).append(row)
            return _FakeResult([row])
        rows = self._store.get(self._table, [])
        return _FakeResult(list(rows))


class _FakeSupabase:
    def __init__(self, store: dict | None = None):
        self._store = store if store is not None else {}

    def table(self, name: str):
        return _FakeQuery(self._store, name)


@pytest.fixture
def fake_sb(monkeypatch):
    sb = _FakeSupabase()
    monkeypatch.setattr(pv2, "get_supabase_admin", lambda: sb)
    return sb


@pytest.fixture
def fake_user():
    # Shape the router touches: .id, .role
    return SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        role="admin",
    )


# ============================================================
# Request helpers
# ============================================================

def _method_availability_all() -> MethodAvailability:
    return MethodAvailability(
        has_drip=True,
        has_pivot=False,
        has_sprinkler=False,
        has_foliar_sprayer=True,
        has_granular_spreader=True,
        has_fertigation_injectors=True,
        has_seed_treatment=False,
    )


def _block_request(
    block_id: str,
    name: str,
    area: float,
    n: float = 120,
    p: float = 40,
    k: float = 60,
) -> BlockRequest:
    """Minimal block request with pre-computed season_targets so the
    endpoint skips the catalog-backed target computation path."""
    return BlockRequest(
        block_id=block_id,
        block_name=name,
        block_area_ha=area,
        soil_parameters={"pH": 6.2},
        yield_target_per_ha=60.0,
        season_targets={"N": n, "P2O5": p, "K2O": k},
    )


def _build_request(
    blocks: list[BlockRequest],
    skipped: list[SkippedBlockRequest] | None = None,
) -> BuildProgrammeRequest:
    return BuildProgrammeRequest(
        client_name="Test Farmer",
        farm_name="Test Farm",
        prepared_for="Test Farmer",
        crop="Maize",
        planting_date="2026-10-01",
        season="2026/2027",
        stage_count=5,
        blocks=blocks,
        method_availability=_method_availability_all(),
        skipped_blocks=skipped or [],
    )


# ============================================================
# End-to-end tests
# ============================================================

def test_build_endpoint_single_block_persists_artifact(fake_sb, fake_user):
    """Happy path — one block, no clustering, artifact returned and
    persisted to programme_artifacts."""
    request = _build_request([_block_request("1", "Land A", 10.0)])
    response = asyncio.run(build_programme_endpoint(request, fake_user))

    assert response.id is not None
    assert response.state in {"draft", "approved", "activated"}
    # Full artifact returned, keyed by the orchestrator's schema
    assert "soil_snapshots" in response.artifact
    assert len(response.artifact["soil_snapshots"]) == 1
    # Row persisted
    stored = fake_sb._store["programme_artifacts"]
    assert len(stored) == 1
    assert stored[0]["user_id"] == fake_user.id


def test_build_endpoint_surfaces_skipped_blocks_as_outstanding_items(
    fake_sb, fake_user,
):
    """Skipped blocks (no soil analysis) flow through to
    artifact.outstanding_items."""
    request = _build_request(
        blocks=[_block_request("1", "Land A", 10.0)],
        skipped=[
            SkippedBlockRequest(block_name="Pivot 2", reason="no soil analysis linked"),
            SkippedBlockRequest(block_name="Pivot 3", reason="no soil analysis linked"),
        ],
    )
    response = asyncio.run(build_programme_endpoint(request, fake_user))

    outstanding_items = response.artifact["outstanding_items"]
    names_mentioned = " ".join(i["item"] for i in outstanding_items)
    assert "Pivot 2" in names_mentioned
    assert "Pivot 3" in names_mentioned


def test_build_endpoint_clusters_similar_blocks_and_attaches_per_block_snapshots(
    fake_sb, fake_user,
):
    """Multi-block cluster: the orchestrator runs on one synthetic
    block, but per-original-block SoilSnapshots are appended post-
    build so the agronomist keeps drill-down visibility."""
    request = _build_request([
        _block_request("1", "Land A", 2.0),   # same ratio
        _block_request("2", "Land B", 8.0),   # same ratio → same cluster
    ])
    response = asyncio.run(build_programme_endpoint(request, fake_user))

    snapshots = response.artifact["soil_snapshots"]
    # 1 cluster-level (from orchestrator) + 2 per-block (from router)
    assert len(snapshots) == 3
    names = [s["block_name"] for s in snapshots]
    assert any("Cluster" in n for n in names)
    assert any("Land A" in n and "in Cluster" in n for n in names)
    assert any("Land B" in n and "in Cluster" in n for n in names)


def test_build_endpoint_leaves_dissimilar_blocks_as_singletons(fake_sb, fake_user):
    """Blocks with very different NPK ratios stay as singletons — no
    cluster narrative, no per-block extra snapshots."""
    request = _build_request([
        _block_request("1", "Land A", 10.0, n=200, p=40, k=20),
        _block_request("2", "Land B", 10.0, n=20, p=40, k=200),
    ])
    response = asyncio.run(build_programme_endpoint(request, fake_user))

    snapshots = response.artifact["soil_snapshots"]
    # Two singletons → two snapshots, no extras
    assert len(snapshots) == 2
    # No cluster-related RiskFlag because no multi-block cluster formed
    cluster_flags = [
        f for f in response.artifact["risk_flags"]
        if "Cluster" in f["message"]
    ]
    assert cluster_flags == []


def test_build_endpoint_emits_heterogeneity_risk_flag_when_cluster_breaches_thresholds(
    fake_sb, fake_user,
):
    """Blocks with the same NPK ratio but wildly different magnitudes
    cluster together, then fail the heterogeneity check — the router
    must emit a RiskFlag naming the affected nutrient + citation."""
    request = _build_request([
        _block_request("1", "Land A", 10.0, n=60, p=30, k=30),
        _block_request("2", "Land B", 10.0, n=180, p=90, k=90),
        _block_request("3", "Land C", 10.0, n=240, p=120, k=120),
    ])
    response = asyncio.run(build_programme_endpoint(request, fake_user))

    cluster_flags = [
        f for f in response.artifact["risk_flags"]
        if "Cluster" in f["message"]
    ]
    assert len(cluster_flags) == 1
    msg = cluster_flags[0]["message"]
    assert "Wilding" in msg
    assert "Land A" in msg and "Land B" in msg and "Land C" in msg
