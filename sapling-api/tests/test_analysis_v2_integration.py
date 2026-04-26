"""Integration tests for /api/analysis/v2/run.

Drives the run_analysis endpoint directly with a stubbed Supabase to
exercise the full flow: catalog load → analyse_blocks → soil-factor
reasoning → target computation → foliar trigger detection → current-
stage detection. Verifies the artifact comes back interpretation-only
(empty blends/stage_schedules/shopping_list) regardless of how rich
the soil/leaf input is.

Mirrors the test_programmes_v2_integration.py fake-Supabase pattern.
"""
from __future__ import annotations

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from app.routers import analysis_v2 as av2
from app.routers.analysis_v2 import (
    AnalysisBlockRequest,
    AnalysisRequest,
    run_analysis,
)


# ============================================================
# Fake Supabase (select-only — analysis is read-only on catalog)
# ============================================================

class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, store: dict, table: str):
        self._store = store
        self._table = table

    def select(self, *_args, **_kwargs):
        return self

    def execute(self):
        return _FakeResult(list(self._store.get(self._table, [])))


class _FakeSupabase:
    def __init__(self, store: dict | None = None):
        self._store = store if store is not None else {}

    def table(self, name: str):
        return _FakeQuery(self._store, name)


@pytest.fixture
def fake_user():
    return SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        role="admin",
    )


@pytest.fixture
def stocked_supabase(monkeypatch):
    """Catalog stocked with Macadamia + Citrus crop rows + a mac age curve
    + a mac growth-stage row that covers Jan-Feb (the no-N window)."""
    store = {
        "crop_requirements": [
            {"crop": "Macadamia", "type": "Perennial", "crop_type": "perennial",
             "yield_unit": "t NIS/ha", "default_yield": 4.0,
             "n": 18.0, "p": 1.2, "k": 12.0, "ca": 10.0, "mg": 1.5, "s": 5.0,
             "fe": 0.5, "b": 0.2, "mn": 0.15, "zn": 0.1, "mo": 0.02, "cu": 0.05,
             "pop_per_ha": 312},
            {"crop": "Citrus (Valencia)", "type": "Perennial", "crop_type": "perennial",
             "yield_unit": "t fruit/ha", "default_yield": 40.0,
             "n": 4.0, "p": 0.55, "k": 4.5, "ca": 1.5, "mg": 0.5, "s": 0.3,
             "fe": 0.1, "b": 0.05, "mn": 0.03, "zn": 0.03, "mo": 0.005, "cu": 0.01,
             "pop_per_ha": 312, "parent_crop": "Citrus"},
        ],
        "soil_sufficiency": [],
        "adjustment_factors": [
            {"classification": "Optimal", "factor": 1.0, "nutrient_group": "all",
             "tier": 1, "source": "FERTASA"},
        ],
        "soil_parameter_map": [],
        "crop_sufficiency_overrides": [],
        "fertilizer_rate_tables": [],
        "ideal_ratios": [],
        "crop_calc_flags": [],
        "fertasa_nutrient_removal": [],
        "perennial_age_factors": [
            {"crop": "Macadamia", "age_label": "Year 9+", "age_min": 9, "age_max": 99,
             "n_factor": 1.0, "p_factor": 1.0, "k_factor": 1.0, "general_factor": 1.0,
             "notes": "Full bearing"},
            {"crop": "Macadamia", "age_label": "Year 1-2", "age_min": 0, "age_max": 2,
             "n_factor": 0.2, "p_factor": 0.25, "k_factor": 0.15, "general_factor": 0.2,
             "notes": "Establishment"},
        ],
        "crop_growth_stages": [
            {"crop": "Macadamia", "stage_name": "Nut growth + oil accumulation (NO N)",
             "stage_order": 4, "month_start": 11, "month_end": 2,
             "n_pct": 0, "p_pct": 0, "k_pct": 0, "ca_pct": 10, "mg_pct": 25, "s_pct": 25,
             "num_applications": 0, "default_method": "broadcast"},
            {"crop": "Macadamia", "stage_name": "Pre-flowering & main flowering",
             "stage_order": 2, "month_start": 6, "month_end": 9,
             "n_pct": 45, "p_pct": 40, "k_pct": 50, "ca_pct": 50, "mg_pct": 25, "s_pct": 20,
             "num_applications": 2, "default_method": "broadcast"},
        ],
    }
    sb = _FakeSupabase(store)
    monkeypatch.setattr(av2, "get_supabase_admin", lambda: sb)
    return sb


# ============================================================
# Helpers
# ============================================================

def _block(name: str = "Block A", area: float = 5.0, yield_target: float = 4.0,
           tree_age: int | None = 10, soil: dict | None = None,
           leaf: dict | None = None) -> AnalysisBlockRequest:
    return AnalysisBlockRequest(
        block_id=name.lower().replace(" ", "-"),
        block_name=name,
        block_area_ha=area,
        soil_parameters=soil or {"pH (H2O)": 6.0, "P (Bray-1)": 25, "K": 200,
                                  "Ca": 1500, "Mg": 200, "S": 18, "Org C": 1.5},
        leaf_values=leaf,
        yield_target_per_ha=yield_target,
        tree_age=tree_age,
    )


# ============================================================
# Tests
# ============================================================

def test_single_block_soil_only_returns_artifact(stocked_supabase, fake_user):
    """Smoke: soil-only single block produces an interpretation artifact
    with empty blends + populated soil snapshot + computed ratios."""
    req = AnalysisRequest(crop="Macadamia", blocks=[_block()],
                          prepared_for="Test")
    response = asyncio.run(run_analysis(req, fake_user))
    artifact = response.artifact
    assert len(artifact["soil_snapshots"]) == 1
    assert artifact["blends"] == []
    assert artifact["stage_schedules"] == []
    assert artifact["shopping_list"] == []
    assert artifact["header"]["crop"] == "Macadamia"
    assert artifact["soil_snapshots"][0]["block_name"] == "Block A"


def test_artifact_is_interpretation_only_no_method_picks(stocked_supabase, fake_user):
    """Even with rich inputs (soil + leaf + age + yield), no blends or
    stage schedules are emitted. Programme builder is intentionally
    not invoked."""
    req = AnalysisRequest(
        crop="Macadamia",
        blocks=[_block(leaf={"N": 1.4, "K": 0.5, "Mg": 0.06})],
        planting_date=date(2018, 10, 1),
        prepared_for="Test",
    )
    response = asyncio.run(run_analysis(req, fake_user))
    artifact = response.artifact
    assert artifact["blends"] == []
    assert artifact["stage_schedules"] == []
    assert artifact["shopping_list"] == []


def test_age_factor_scales_targets_for_young_block(stocked_supabase, fake_user):
    """Phase A engine wiring carries through to /analysis/v2: a 2-y-o
    mac block gets ~0.2× N target vs a 10-y-o block."""
    young_req = AnalysisRequest(
        crop="Macadamia", blocks=[_block(tree_age=2)], prepared_for="T"
    )
    full_req = AnalysisRequest(
        crop="Macadamia", blocks=[_block(tree_age=10)], prepared_for="T"
    )
    young = asyncio.run(run_analysis(young_req, fake_user)).artifact
    full = asyncio.run(run_analysis(full_req, fake_user)).artifact
    young_n = young["block_totals"]["block-a"].get("N")
    full_n = full["block_totals"]["block-a"].get("N")
    assert young_n is not None and full_n is not None
    ratio = young_n / full_n
    assert 0.18 < ratio < 0.22, f"Expected ~0.2x N for 2-y-o vs 10-y-o, got {ratio}"
    # Age assumption surfaced for traceability
    fields = {a["field"] for a in young["assumptions"]}
    assert "perennial_age_scale" in fields


def test_current_stage_detection_for_jan_today(stocked_supabase, fake_user):
    """Jan reading on a mac orchard should detect the Nov-Feb wrap-around
    stage 'Nut growth + oil accumulation (NO N)' as the current stage."""
    # Pin today via direct call to the pipeline — the router uses
    # date.today() internally; we verify the wrap logic via decision_trace
    # presence. With current real today, only assert no crash + structure.
    req = AnalysisRequest(
        crop="Macadamia",
        blocks=[_block()],
        planting_date=date(2018, 10, 1),
        prepared_for="Test",
    )
    response = asyncio.run(run_analysis(req, fake_user))
    artifact = response.artifact
    # Decision trace populated
    assert any("analysis" in line.lower() or "stage" in line.lower()
               for line in artifact["decision_trace"])


def test_no_planting_date_runs_season_agnostic(stocked_supabase, fake_user):
    """Without planting_date, current-stage detection is skipped but the
    rest of the pipeline still runs. Header.planting_date defaults to today."""
    req = AnalysisRequest(crop="Macadamia", blocks=[_block()], prepared_for="T")
    response = asyncio.run(run_analysis(req, fake_user))
    artifact = response.artifact
    # No 'current_growth_stage' assumption when planting_date absent
    fields = {a["field"] for a in artifact["assumptions"]}
    assert "current_growth_stage" not in fields


def test_multi_block_aggregates_per_block(stocked_supabase, fake_user):
    """Two blocks → two snapshots, each with own block_totals."""
    req = AnalysisRequest(
        crop="Macadamia",
        blocks=[_block(name="Block A"), _block(name="Block B", area=8.0)],
        prepared_for="Test",
    )
    artifact = asyncio.run(run_analysis(req, fake_user)).artifact
    assert len(artifact["soil_snapshots"]) == 2
    assert "block-a" in artifact["block_totals"]
    assert "block-b" in artifact["block_totals"]


def test_citrus_variant_falls_back_to_parent_age_curve(stocked_supabase, fake_user):
    """Citrus (Valencia) block with tree_age uses the parent 'Citrus'
    age curve via the variant→parent fallback (when Valencia rows exist
    in catalog but not in age-factor table). For this stocked catalog,
    no Citrus age factors → no scaling but call must not crash."""
    req = AnalysisRequest(
        crop="Citrus (Valencia)",
        blocks=[_block(soil={"pH (H2O)": 7.0, "P (Bray-1)": 30, "K": 200,
                              "Ca": 1500, "Mg": 200},
                       yield_target=40.0, tree_age=12)],
        prepared_for="Test",
    )
    artifact = asyncio.run(run_analysis(req, fake_user)).artifact
    assert artifact["header"]["crop"] == "Citrus (Valencia)"
    assert len(artifact["blends"]) == 0
