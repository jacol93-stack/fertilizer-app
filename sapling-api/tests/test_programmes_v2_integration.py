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
    _suggest_pdf_filename,
    build_programme_endpoint,
    get_programme_artifact,
    render_programme_artifact_pdf,
)
from app.models import ProgrammeArtifact, ProgrammeHeader, ProgrammeState
from app.models.confidence import DataCompleteness, Tier
from app.models.variants import VariantKey
from datetime import date as _date


# ============================================================
# Fake Supabase — enough surface for the build endpoint
# ============================================================

class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    """Chainable stub — supports select/insert/eq/limit/execute chains
    the router uses. Everything else raises AttributeError intentionally
    (fail loud if the test hits an unexpected path)."""

    def __init__(self, store: dict, table: str):
        self._store = store
        self._table = table
        self._payload = None
        self._filters: list[tuple[str, object]] = []
        self._limit: int | None = None

    def select(self, *_args, **_kwargs):
        return self

    def insert(self, payload: dict):
        self._payload = payload
        return self

    def eq(self, column: str, value):
        self._filters.append((column, value))
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def execute(self):
        if self._payload is not None:
            row = {**self._payload, "id": str(uuid.uuid4())}
            self._store.setdefault(self._table, []).append(row)
            return _FakeResult([row])
        rows = self._store.get(self._table, [])
        for col, val in self._filters:
            rows = [r for r in rows if r.get(col) == val]
        if self._limit is not None:
            rows = rows[: self._limit]
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
    soil_parameters: dict | None = None,
) -> BlockRequest:
    """Minimal block request with pre-computed season_targets so the
    endpoint skips the catalog-backed target computation path."""
    return BlockRequest(
        block_id=block_id,
        block_name=name,
        block_area_ha=area,
        soil_parameters=soil_parameters or {"pH": 6.2},
        yield_target_per_ha=60.0,
        season_targets={"N": n, "P2O5": p, "K2O": k},
    )


def _build_request(
    blocks: list[BlockRequest],
    skipped: list[SkippedBlockRequest] | None = None,
    water_values: dict | None = None,
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
        water_values=water_values,
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
    """Multi-block cluster: the orchestrator runs soil-side reasoning
    on each SOURCE block (preserves block-specific signals like
    Al-saturation that would average out in a cluster aggregate), then
    emits a cluster-directory snapshot whose block_id is `cluster_<X>`
    and whose block_name is the comma-joined member list. Blend
    production still runs on the cluster aggregate."""
    request = _build_request([
        _block_request("1", "Land A", 2.0),   # same ratio
        _block_request("2", "Land B", 8.0),   # same ratio → same cluster
    ])
    response = asyncio.run(build_programme_endpoint(request, fake_user))

    snapshots = response.artifact["soil_snapshots"]
    # 2 per-source snapshots ("Land A", "Land B") + 1 cluster directory snapshot
    assert len(snapshots) == 3

    cluster_snaps = [s for s in snapshots if s["block_id"].startswith("cluster_")]
    source_snaps = [s for s in snapshots if not s["block_id"].startswith("cluster_")]

    # Exactly one cluster-directory snapshot, with comma-joined member names.
    assert len(cluster_snaps) == 1
    cluster_name = cluster_snaps[0]["block_name"]
    assert "Land A" in cluster_name and "Land B" in cluster_name

    # Per-source snapshots keep their original block names so the
    # agronomist can still drill into block-specific findings.
    source_names = {s["block_name"] for s in source_snaps}
    assert source_names == {"Land A", "Land B"}


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


def test_build_endpoint_auto_splits_heterogeneous_clusters_into_homogeneous_subgroups(
    fake_sb, fake_user,
):
    """Blocks with the same NPK ratio but wildly different magnitudes
    used to cluster together and trigger a heterogeneity warning. The
    auto-split post-pass now subdivides them by the worst-CV nutrient
    until each resulting cluster is below the split threshold — so the
    router emits no cluster-heterogeneity RiskFlag."""
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
    # Auto-split prevents a heterogeneous cluster from surviving — no
    # warning needed because the split itself was the action.
    assert cluster_flags == []
    # Per-block snapshots cover all three blocks (the three were split
    # across two clusters of {1} + {2,3} or similar — every block is
    # represented).
    snapshot_blocks = {s["block_name"] for s in response.artifact["soil_snapshots"]}
    assert {"Land A", "Land B", "Land C"}.issubset(snapshot_blocks)


# ============================================================
# A4 — Water quality × soil ESP compounding
# ============================================================

# Soil mirroring Gamka Land 1-4: ESP ≈ 14.7 % (Na 2.0 cmol/kg, CEC 13.63)
GAMKA_LIKE_SOIL = {
    "pH": 8.3, "pH (KCl)": 8.3,
    "Na": 2.0, "K": 0.33, "Ca": 9.7, "Mg": 1.6,
    "T Value": 13.63,  # CEC
    "Na_base_sat_pct": 14.67,
    "P (Olsen)": 3.6,
    "B": 1.2,
    "C": 0.40,  # Walkley-Black %
}

# Typical Karoo borehole — elevated Na + HCO3
KAROO_BOREHOLE_WATER = {
    "EC": 1.8,
    "Na": 220,
    "Ca": 50,
    "Mg": 25,
    "HCO3": 380,
    "pH": 7.8,
}

# Clean irrigation water — low Na, balanced Ca/Mg
CLEAN_WATER = {
    "EC": 0.5,
    "Na": 20,
    "Ca": 60,
    "Mg": 30,
    "HCO3": 100,
    "pH": 7.2,
}


def test_build_endpoint_sodic_soil_plus_sodic_water_fires_compounding_risk(
    fake_sb, fake_user,
):
    """Karoo-pattern: trending-sodic soil + Na-loaded water →
    compounding RiskFlag surfaces in the artifact with 'critical'
    severity and an escalate-gypsum recommendation."""
    request = _build_request(
        blocks=[_block_request("1", "Gamka Land", 5.0, soil_parameters=GAMKA_LIKE_SOIL)],
        water_values=KAROO_BOREHOLE_WATER,
    )
    response = asyncio.run(build_programme_endpoint(request, fake_user))

    # Look for the compounding-hazard finding in risk_flags
    compounding = [
        f for f in response.artifact["risk_flags"]
        if ("compound" in f["message"].lower()
            or "treading water" in f["message"].lower()
            or "treading water" in f["message"].lower()
            or "every irrigation cycle" in f["message"].lower())
    ]
    assert len(compounding) >= 1, (
        f"Expected compounding water×soil RiskFlag, got: "
        f"{[f['message'][:80] for f in response.artifact['risk_flags']]}"
    )
    # Critical severity
    assert any(f["severity"] == "critical" for f in compounding)


def test_build_endpoint_benign_water_does_not_fire_compounding(fake_sb, fake_user):
    """Same sodic soil + clean irrigation water → no compounding flag.
    The water rule only fires when BOTH soil ESP and water SAR exceed
    threshold."""
    request = _build_request(
        blocks=[_block_request("1", "Gamka Land", 5.0, soil_parameters=GAMKA_LIKE_SOIL)],
        water_values=CLEAN_WATER,
    )
    response = asyncio.run(build_programme_endpoint(request, fake_user))

    compounding_messages = [
        f["message"] for f in response.artifact["risk_flags"]
        if "every irrigation cycle" in f["message"].lower()
        or "compounding" in f["message"].lower()
    ]
    assert compounding_messages == [], (
        f"Clean water should not trigger compounding risk; got: {compounding_messages}"
    )


def test_build_endpoint_no_water_values_skips_water_rules(fake_sb, fake_user):
    """When water_values is omitted (default), no water-quality findings
    fire — soil-only rules run as before. Important for the agronomist
    who hasn't tested water yet."""
    request = _build_request(
        blocks=[_block_request("1", "Gamka Land", 5.0, soil_parameters=GAMKA_LIKE_SOIL)],
        # water_values omitted
    )
    response = asyncio.run(build_programme_endpoint(request, fake_user))

    # Soil ESP finding can still fire (trending sodic, warn severity),
    # but NO findings from the FAO water-quality source should appear
    water_sourced = [
        f for f in response.artifact["risk_flags"]
        if f.get("source", {}).get("source_id") == "FAO_IRRIGATION_29"
    ]
    assert water_sourced == []


# ============================================================
# PDF render endpoint
# ============================================================

def test_render_pdf_endpoint_returns_pdf_for_owned_artifact(fake_sb, fake_user):
    """Build → render-pdf round trip. Caller owns the artifact, gets a
    sapling-branded PDF byte stream back with PDF magic header + a
    Content-Disposition filename."""
    build_request = _build_request([_block_request("1", "Land A", 10.0)])
    build_response = asyncio.run(build_programme_endpoint(build_request, fake_user))
    artifact_id = build_response.id

    response = asyncio.run(render_programme_artifact_pdf(artifact_id, fake_user))
    assert response.media_type == "application/pdf"
    assert response.body[:4] == b"%PDF"
    assert len(response.body) > 100_000
    cd = response.headers.get("content-disposition", "")
    assert "attachment;" in cd
    assert ".pdf" in cd


def test_render_pdf_endpoint_404_when_artifact_missing(fake_sb, fake_user):
    import uuid as _uuid
    from fastapi import HTTPException

    bogus_id = _uuid.UUID("00000000-0000-0000-0000-000000000abc")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(render_programme_artifact_pdf(bogus_id, fake_user))
    assert exc.value.status_code == 404


def test_render_pdf_endpoint_scopes_to_user(fake_sb):
    """Non-admin user A cannot pull user B's artifact PDF."""
    from fastapi import HTTPException

    user_a = SimpleNamespace(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", role="user")
    user_b = SimpleNamespace(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", role="user")
    build_request = _build_request([_block_request("1", "Land A", 10.0)])
    build_response = asyncio.run(build_programme_endpoint(build_request, user_a))
    artifact_id = build_response.id

    # User B reading user A's artifact → 404 (scoped, not 403, to avoid
    # leaking existence)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(render_programme_artifact_pdf(artifact_id, user_b))
    assert exc.value.status_code == 404


def test_render_pdf_endpoint_admin_sees_any_artifact(fake_sb):
    """Admin role bypasses user_id scope."""
    user_a = SimpleNamespace(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", role="user")
    admin = SimpleNamespace(id="11111111-1111-1111-1111-111111111111", role="admin")
    build_request = _build_request([_block_request("1", "Land A", 10.0)])
    build_response = asyncio.run(build_programme_endpoint(build_request, user_a))

    response = asyncio.run(
        render_programme_artifact_pdf(build_response.id, admin),
    )
    assert response.media_type == "application/pdf"


def test_get_artifact_endpoint_scopes_to_user(fake_sb):
    """Non-admin user B cannot GET user A's artifact (returns 404, not
    403, to avoid leaking artifact existence). Locks the user_id scope
    on the v2 GET endpoint that the artifact-detail page hits on
    every load."""
    from fastapi import HTTPException

    user_a = SimpleNamespace(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", role="user")
    user_b = SimpleNamespace(id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", role="user")
    build_request = _build_request([_block_request("1", "Land A", 10.0)])
    build_response = asyncio.run(build_programme_endpoint(build_request, user_a))

    # User A reading their own artifact → succeeds
    own_response = asyncio.run(get_programme_artifact(build_response.id, user_a))
    assert str(own_response.id) == str(build_response.id)

    # User B reading user A's artifact → 404
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_programme_artifact(build_response.id, user_b))
    assert exc.value.status_code == 404


def test_get_artifact_endpoint_admin_bypasses_scope(fake_sb):
    """Admin role can pull any user's artifact (mirrors the PDF-scope
    admin bypass for the same endpoint group)."""
    user_a = SimpleNamespace(id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", role="user")
    admin = SimpleNamespace(id="11111111-1111-1111-1111-111111111111", role="admin")
    build_request = _build_request([_block_request("1", "Land A", 10.0)])
    build_response = asyncio.run(build_programme_endpoint(build_request, user_a))

    response = asyncio.run(get_programme_artifact(build_response.id, admin))
    assert str(response.id) == str(build_response.id)


# ============================================================
# Filename helper
# ============================================================

def _bare_artifact(crop="Macadamia", season="2026/27", client="Test Farmer",
                   ref="REF-001") -> ProgrammeArtifact:
    return ProgrammeArtifact(
        header=ProgrammeHeader(
            client_name=client,
            farm_name="Test Farm",
            prepared_for="Test",
            prepared_date=_date(2026, 4, 25),
            crop=crop,
            variant_key=VariantKey(canonical_crop=crop),
            season=season,
            planting_date=_date(2026, 5, 1),
            data_completeness=DataCompleteness(level="standard"),
            method_availability=MethodAvailability(has_drip=True),
            state=ProgrammeState.DRAFT,
            ref_number=ref,
        ),
        soil_snapshots=[],
        stage_schedules=[],
    )


def test_pdf_filename_combines_client_crop_season():
    art = _bare_artifact(client="Acme", crop="Macadamia", season="2026/27")
    name = _suggest_pdf_filename(art)
    assert name.endswith(".pdf")
    assert "Acme" in name
    assert "Macadamia" in name
    assert "2026/27" not in name  # forward slash stripped from filename
    assert "2026" in name and "27" in name


def test_pdf_filename_strips_filesystem_unsafe_chars():
    art = _bare_artifact(client="A:B/C\\D", season="2026/27")
    name = _suggest_pdf_filename(art)
    for bad in (":", "/", "\\", "*", "?", '"', "<", ">", "|"):
        assert bad not in name


def test_pdf_filename_falls_back_to_ref_number_only():
    art = _bare_artifact(client="", crop="", season="", ref="WJ60421")
    name = _suggest_pdf_filename(art)
    assert "WJ60421" in name
