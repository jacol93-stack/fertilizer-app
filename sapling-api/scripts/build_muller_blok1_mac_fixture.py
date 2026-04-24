"""
Generate the Muller Familie Boerdery / Laborie Boerdery / Blok 1
macadamia fixture from real soil + leaf lab data.

Soil source: NViroTek WO 197378:251927 (G40-42708), 2026-03-17
Leaf source:  NViroTek WO 197378:251823 (L14-9042), 2026-03-13

Assumptions flagged in the rendered artifact (block metadata missing
from the lab reports; Tzaneen-commercial-mac defaults used):
    - Block area: 5.0 ha (typical Tzaneen commercial block)
    - Cultivar: Beaumont (dominant Tzaneen cultivar)
    - Age: full bearing (year 8+)
    - Plant population: 312 trees/ha (SAMAC reference, 8×4 m)
    - Irrigation: micro-sprinkler
    - Target yield: 3 t DNIS/ha (per client brief — Steve's note:
      9 t/ha in husk = 3 t/ha DNIS)
    - Harvest mode: 'nuts' (husks mulched on-farm, NIS-only export)

Usage (from repo root, with the venv active):
    python sapling-api/scripts/build_muller_blok1_mac_fixture.py

Outputs:
    tests/fixtures/golden_macadamia_laborie_blok1.json  (artifact)
    tests/fixtures/golden_macadamia_laborie_blok1.md    (rendered doc)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

# Make the sapling-api package importable when running this script directly
API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))

from dotenv import load_dotenv
load_dotenv(API_ROOT / ".env")

from app.models.confidence import DataCompleteness
from app.models.methods import MethodAvailability
from app.models.variants import VariantKey
from app.services.programme_builder_orchestrator import (
    BlockInput,
    OrchestratorInput,
    build_programme,
)
from app.services.renderer import render_programme_document
from app.services.target_computation import compute_season_targets
from app.supabase_client import get_supabase_admin


# ============================================================
# Real lab data — Blok 1
# ============================================================

# Soil — G40-42708, NViroTek Mehlich-3 / Ammonium Acetate panel
SOIL_BLOK1 = {
    "pH (KCl)": 6.03,
    "P (Bray-1)": 18.0,
    "K": 181.0,
    "Na": 18.0,
    "Ca": 857.0,
    "Mg": 125.0,
    "EXCH_ACID_KCl": 0.0,
    "ACID_SAT_pct": 0.0,
    "Ca_base_sat_pct": 73.23,
    "Mg_base_sat_pct": 17.54,
    "K_base_sat_pct": 7.91,
    "Na_base_sat_pct": 1.32,
    "CEC": 5.85,
    "T Value": 5.85,
    "Ca:Mg": 4.17,
    "(Ca+Mg):K": 11.47,
    "Mg:K": 2.22,
    "Na:K": 0.17,
    "S": 3.94,
    "Dens": 1.14,
}


def load_catalog_and_materials():
    """Load real Supabase catalog so the engine has accurate refs."""
    sb = get_supabase_admin()
    from app.routers.programmes_v2 import _load_soil_catalog
    catalog = _load_soil_catalog(sb)
    # Full materials catalog (admin-mode equivalent) — fixture is a
    # reference programme, not scoped to a single agent's materials.
    materials = sb.table("materials").select("*").execute().data or []
    return catalog, materials


def build_inputs(catalog, materials) -> OrchestratorInput:
    # Compute season targets for Blok 1 using the real engine path.
    # Harvest mode 'nuts' per the client's husks-stay-on-farm practice.
    target_result = compute_season_targets(
        crop="Macadamia",
        yield_target=3.0,  # t DNIS/ha, per client brief
        soil_values=SOIL_BLOK1,
        catalog=catalog,
        subtract_harvested_removal=True,
        expected_yield_harvested=3.0,
        block_pop_per_ha=312.0,
        harvest_mode="nuts",
    )
    print(f"  computed targets: {target_result.targets}")
    print(f"  calc paths: {target_result.calc_path_by_nutrient}")

    block = BlockInput(
        block_id="laborie-blok-1",
        block_name="Blok 1",
        block_area_ha=5.0,
        soil_parameters=SOIL_BLOK1,
        season_targets=target_result.targets,
        lab_name="NViroTek",
        lab_method="Mehlich-3 / Ammonium Acetate",
        sample_date=date(2026, 3, 11),
        sample_id="G40-42708",
        pop_per_ha=312.0,  # SAMAC reference
    )

    return OrchestratorInput(
        client_name="Muller Familie Boerdery Trust",
        farm_name="Laborie Boerdery",
        prepared_for="Anton Muller",
        crop="Macadamia",
        planting_date=date(2026, 7, 1),  # programme season-start (post-harvest)
        build_date=date(2026, 4, 24),
        # Mac harvest in Tzaneen spans Apr-Jun; using June end-of-season
        # so a May application window is still in-bounds.
        expected_harvest_date=date(2027, 6, 30),
        season="2026/27",
        location="Tzaneen, Limpopo",
        ref_number="MFBT-BLOK1-2026",
        # FERTASA 5.8.1 has 4 canonical mac windows (post-harvest / pre-
        # flower / nut set / nut growth-oil). stage_count=4 matches that
        # structure and collapses adjacent stages with similar nutrient
        # profiles — supports the production blend-count bias without
        # crossing any FERTASA timing walls. See
        # project_application_timing_and_blend_count memory.
        stage_count=4,
        method_availability=MethodAvailability(
            has_drip=False,
            has_pivot=False,
            has_sprinkler=True,  # micro-sprinkler
            has_foliar_sprayer=True,
            has_granular_spreader=True,
            has_fertigation_injectors=True,
            has_seed_treatment=False,
        ),
        blocks=[block],
        available_materials=materials,
        # Farmer's operational application months. Realistic commercial
        # Tzaneen macadamia schedule on micro-sprinkler: ~5 slots spaced
        # to hit each FERTASA 5.8.1 window. Engine enforces the Nov-Feb
        # N-cutoff within these slots (December will have N zeroed if it
        # sits in the cutoff range — K still flows through).
        application_months=[8, 10, 12, 3, 5],
    )


def main() -> int:
    print("Loading catalog + materials from Supabase...")
    catalog, materials = load_catalog_and_materials()
    print(f"  crop_rows: {len(catalog.crop_rows)}")
    print(f"  sufficiency_rows: {len(catalog.sufficiency_rows)}")
    print(f"  rate_table_rows: {len(catalog.rate_table_rows or [])}")
    print(f"  materials: {len(materials)}")

    print("\nBuilding OrchestratorInput...")
    inputs = build_inputs(catalog, materials)

    print("Running build_programme(inputs)...")
    artifact = build_programme(inputs)

    print("\nArtifact summary:")
    print(f"  blocks: {len(artifact.soil_snapshots)}")
    print(f"  blends: {len(artifact.blends)}")
    print(f"  foliar events: {len(artifact.foliar_events)}")
    print(f"  risk flags: {len(artifact.risk_flags)}")
    print(f"  assumptions: {len(artifact.assumptions)}")
    print(f"  outstanding items: {len(artifact.outstanding_items)}")
    print(f"  block_totals: {artifact.block_totals}")

    if artifact.risk_flags:
        print("\nRisk flags:")
        for f in artifact.risk_flags:
            print(f"  [{f.severity.upper()}] {f.message[:120]}")

    if artifact.foliar_events:
        print("\nFoliar events:")
        for fe in artifact.foliar_events:
            print(f"  #{fe.event_number} wk{fe.week} — {fe.analysis} @ {fe.rate_per_ha} — {fe.trigger_reason[:80]}")

    print("\nRendering...")
    markdown = render_programme_document(artifact)

    fixtures_dir = API_ROOT / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = fixtures_dir / "golden_macadamia_laborie_blok1.json"
    md_path = fixtures_dir / "golden_macadamia_laborie_blok1.md"

    # Pydantic .model_dump_json for stable serialisation
    with artifact_path.open("w") as f:
        f.write(artifact.model_dump_json(indent=2))
    with md_path.open("w") as f:
        f.write(markdown)

    print(f"\n✔ Artifact: {artifact_path}")
    print(f"✔ Markdown: {md_path}  ({len(markdown)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
