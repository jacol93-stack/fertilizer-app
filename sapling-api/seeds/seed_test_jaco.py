"""Seed a single test client owned by jaco@saplingfertilizer.co.za.

One client, two farms (Macadamia + Citrus), four fields each, every field
carrying a single saved soil analysis with engine-derived classifications,
ratios, and nutrient targets.

The fields cover a realistic age + cultivar spread so the wizard exercises:
- young vs mature trees (perennial_age_factors path)
- mixed cultivars per crop (parent-variant fallback)
- soil values varied around published SA norms (Manson & Sheard 2007 +
  FERTASA 5.8.1 for mac; FERTASA 5.7.3 + Citrus Academy NQ2 for citrus)

Idempotent: deletes prior `[TEST]` clients owned by jaco before re-seeding.
Run from `sapling-api/`:

    ./venv/bin/python -m seeds.seed_test_jaco
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from app.services.aggregation import aggregate_samples  # noqa: F401 (parity import)
from app.services.soil_engine import (
    adjust_targets_for_ratios,
    calculate_nutrient_targets,
    classify_soil_value,
    evaluate_ratios,
)
from app.supabase_client import get_supabase_admin

TEST_PREFIX = "[TEST]"
DEFAULT_AGENT_EMAIL = "jaco@saplingfertilizer.co.za"


# ─── Reference-data cache ────────────────────────────────────────────────


def _load_reference(sb):
    return {
        "sufficiency": sb.table("soil_sufficiency").select("*").execute().data or [],
        "ratios": sb.table("ideal_ratios").select("*").execute().data or [],
        "adjustments": sb.table("adjustment_factors").select("*").execute().data or [],
        "param_map": sb.table("soil_parameter_map").select("*").execute().data or [],
        "crop_reqs": sb.table("crop_requirements").select("*").execute().data or [],
    }


def _compute_analysis_fields(crop: str, yield_target: float, soil_values: dict, ref: dict) -> dict:
    classifications = {
        p: classify_soil_value(v, p, ref["sufficiency"])
        for p, v in soil_values.items() if v is not None
    }
    ratio_results = evaluate_ratios(soil_values, ref["ratios"])
    targets = calculate_nutrient_targets(
        crop, yield_target, soil_values,
        ref["crop_reqs"], ref["sufficiency"], ref["adjustments"], ref["param_map"],
    )
    nutrient_targets = adjust_targets_for_ratios(
        targets, ratio_results, soil_values, ref["ratios"],
    ) if targets else []
    return {
        "classifications": classifications,
        "ratio_results": [dict(r) for r in ratio_results],
        "nutrient_targets": nutrient_targets,
    }


# ─── DB helpers ──────────────────────────────────────────────────────────


def _find_agent(sb, email: str) -> str:
    r = sb.table("profiles").select("id").eq("email", email).execute()
    if not r.data:
        raise SystemExit(f"No profile found for {email}.")
    return r.data[0]["id"]


def _purge_test(sb, agent_id: str):
    clients = (
        sb.table("clients").select("id")
        .eq("agent_id", agent_id).like("name", f"{TEST_PREFIX}%").execute()
    )
    for c in clients.data or []:
        cid = c["id"]
        farm_rows = sb.table("farms").select("id").eq("client_id", cid).execute().data or []
        farm_ids = [f["id"] for f in farm_rows]
        if farm_ids:
            field_rows = sb.table("fields").select("id").in_("farm_id", farm_ids).execute().data or []
            field_ids = [f["id"] for f in field_rows]
            if field_ids:
                sb.table("fields").update({"latest_analysis_id": None}).in_("id", field_ids).execute()
                sb.table("soil_analyses").delete().in_("field_id", field_ids).execute()
            sb.table("soil_analyses").delete().in_("farm_id", farm_ids).execute()
            if field_ids:
                sb.table("fields").delete().in_("id", field_ids).execute()
            sb.table("farms").delete().in_("id", farm_ids).execute()
        sb.table("soil_analyses").delete().eq("client_id", cid).execute()
        sb.table("clients").delete().eq("id", cid).execute()


def _insert_client(sb, agent_id, name, contact, email, phone, notes) -> str:
    r = sb.table("clients").insert({
        "agent_id": agent_id,
        "name": f"{TEST_PREFIX} {name}",
        "contact_person": contact,
        "email": email,
        "phone": phone,
        "notes": notes,
    }).execute()
    return r.data[0]["id"]


def _insert_farm(sb, client_id, name, region, notes) -> str:
    r = sb.table("farms").insert({
        "client_id": client_id, "name": name, "region": region, "notes": notes,
    }).execute()
    return r.data[0]["id"]


def _insert_field(sb, farm_id, *, name, area_ha, crop, cultivar, crop_type,
                  planting_date, tree_age, pop_per_ha, yield_target, yield_unit,
                  irrigation_type) -> str:
    r = sb.table("fields").insert({
        "farm_id": farm_id,
        "name": name,
        "size_ha": area_ha,
        "crop": crop,
        "cultivar": cultivar,
        "crop_type": crop_type,
        "planting_date": planting_date,
        "tree_age": tree_age,
        "pop_per_ha": pop_per_ha,
        "yield_target": yield_target,
        "yield_unit": yield_unit,
        "irrigation_type": irrigation_type,
    }).execute()
    return r.data[0]["id"]


def _insert_single_analysis(sb, *, agent_id, client_id, farm_id, field_id,
                            client_name, farm_name, field_name, crop, cultivar,
                            yield_target, yield_unit, soil_values, analysis_date,
                            lab_name, ref) -> str:
    derived = _compute_analysis_fields(crop, yield_target, soil_values, ref)
    row = {
        "agent_id": agent_id,
        "client_id": client_id,
        "farm_id": farm_id,
        "field_id": field_id,
        "customer": client_name,
        "farm": farm_name,
        "field": field_name,
        "crop": crop,
        "cultivar": cultivar,
        "yield_target": yield_target,
        "yield_unit": yield_unit,
        "lab_name": lab_name,
        "analysis_date": analysis_date,
        "soil_values": soil_values,
        "classifications": derived["classifications"],
        "ratio_results": derived["ratio_results"],
        "nutrient_targets": derived["nutrient_targets"],
        "status": "saved",
        "composition_method": "single",
        "replicate_count": 1,
    }
    r = sb.table("soil_analyses").insert(row).execute()
    analysis_id = r.data[0]["id"]
    sb.table("fields").update({"latest_analysis_id": analysis_id}).eq("id", field_id).execute()
    return analysis_id


# ─── Field plans (realistic SA values, varied around published norms) ────


# Macadamia: based on reference_mac_levubu.json (Levubu, Mehlich-3) — pH 5.8,
# OC 2.5, P 22, K 145, Ca 980, Mg 185, S 12, Zn 3.0, B 0.35, CEC 10.2.
# Spread across 4 blocks: one near-reference, one acidified upper-slope,
# one calcareous foot-slope, one young replant block.
MAC_FIELDS = [
    {
        "name": "Blok A4 — Beaumont mature",
        "area_ha": 8.5, "cultivar": "Beaumont", "tree_age": 12,
        "planting_date": "2014-09-15", "pop_per_ha": 312, "yield_target": 4.8,
        "soil": {
            "pH (H2O)": 5.8, "Org C": 2.5, "P (Bray-1)": 22, "K": 145,
            "Ca": 980, "Mg": 185, "S": 12, "Zn": 3.0, "B": 0.35,
            "Mn": 180, "Fe": 95, "Cu": 6.5, "CEC": 10.2,
        },
    },
    {
        "name": "Blok 788 — A4 9 jaar",
        "area_ha": 6.2, "cultivar": "A4", "tree_age": 9,
        "planting_date": "2017-10-01", "pop_per_ha": 312, "yield_target": 4.2,
        "soil": {
            "pH (H2O)": 5.4, "Org C": 1.9, "P (Bray-1)": 16, "K": 110,
            "Ca": 720, "Mg": 140, "S": 10, "Zn": 2.1, "B": 0.28,
            "Mn": 220, "Fe": 130, "Cu": 5.5, "CEC": 8.4,
        },
    },
    {
        "name": "Blok 816 — Foot-slope",
        "area_ha": 5.8, "cultivar": "816", "tree_age": 15,
        "planting_date": "2011-08-20", "pop_per_ha": 280, "yield_target": 5.2,
        "soil": {
            "pH (H2O)": 6.4, "Org C": 2.8, "P (Bray-1)": 32, "K": 195,
            "Ca": 1180, "Mg": 230, "S": 16, "Zn": 3.8, "B": 0.45,
            "Mn": 160, "Fe": 80, "Cu": 7.2, "CEC": 12.6,
        },
    },
    {
        "name": "Blok N5 — Young Beaumont/A4",
        "area_ha": 3.4, "cultivar": "Beaumont", "tree_age": 4,
        "planting_date": "2022-09-10", "pop_per_ha": 333, "yield_target": 1.5,
        "soil": {
            "pH (H2O)": 5.6, "Org C": 1.6, "P (Bray-1)": 14, "K": 95,
            "Ca": 640, "Mg": 120, "S": 9, "Zn": 1.8, "B": 0.25,
            "Mn": 200, "Fe": 110, "Cu": 4.8, "CEC": 7.1,
        },
    },
]

# Citrus: based on reference_citrus_svr.json (Sundays River Valley, Mehlich-3)
# — pH 6.0, OC 1.5, P 25, K 95, Ca 780, Mg 115, S 10, Zn 1.8, B 0.3.
# Spread: Valencia mature, Navel mid-age, Eureka lemon young, Star Ruby grapefruit.
CIT_FIELDS = [
    {
        "name": "SRV Valencia — Block 12",
        "area_ha": 9.5, "cultivar": "Valencia", "tree_age": 12,
        "planting_date": "2014-08-12", "pop_per_ha": 555, "yield_target": 55,
        "soil": {
            "pH (H2O)": 6.0, "Org C": 1.5, "P (Bray-1)": 25, "K": 95,
            "Ca": 780, "Mg": 115, "S": 10, "Zn": 1.8, "B": 0.30,
            "Mn": 65, "Fe": 110, "Cu": 4.2, "CEC": 8.5,
        },
    },
    {
        "name": "SRV Navel — Block 7",
        "area_ha": 7.2, "cultivar": "Navel", "tree_age": 8,
        "planting_date": "2018-09-05", "pop_per_ha": 555, "yield_target": 48,
        "soil": {
            "pH (H2O)": 6.3, "Org C": 1.7, "P (Bray-1)": 32, "K": 110,
            "Ca": 920, "Mg": 140, "S": 12, "Zn": 2.4, "B": 0.36,
            "Mn": 70, "Fe": 95, "Cu": 4.8, "CEC": 9.4,
        },
    },
    {
        "name": "SRV Eureka — Young replant",
        "area_ha": 4.8, "cultivar": "Eureka Lemon", "tree_age": 5,
        "planting_date": "2021-08-22", "pop_per_ha": 500, "yield_target": 28,
        "soil": {
            "pH (H2O)": 5.7, "Org C": 1.2, "P (Bray-1)": 18, "K": 75,
            "Ca": 620, "Mg": 90, "S": 8, "Zn": 1.4, "B": 0.22,
            "Mn": 85, "Fe": 140, "Cu": 3.6, "CEC": 7.2,
        },
    },
    {
        "name": "SRV Star Ruby — Mature grapefruit",
        "area_ha": 6.8, "cultivar": "Star Ruby", "tree_age": 18,
        "planting_date": "2008-09-18", "pop_per_ha": 416, "yield_target": 60,
        "soil": {
            "pH (H2O)": 6.6, "Org C": 1.9, "P (Bray-1)": 38, "K": 130,
            "Ca": 1080, "Mg": 165, "S": 14, "Zn": 2.6, "B": 0.42,
            "Mn": 60, "Fe": 85, "Cu": 5.2, "CEC": 10.8,
        },
    },
]


# ─── Scenario ────────────────────────────────────────────────────────────


def _seed(sb, agent_id: str, ref: dict):
    client_id = _insert_client(
        sb, agent_id,
        name="Loskop Boerdery",
        contact="Jaco Labuschagne",
        email="jaco@saplingfertilizer.co.za",
        phone="082 555 0099",
        notes="Internal manual-test client — two farms (mac + citrus), 4 blocks each. Re-runs of seed_test_jaco wipe and rebuild.",
    )
    client_name = f"{TEST_PREFIX} Loskop Boerdery"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Farm 1 — Macadamia (Limpopo / Levubu)
    mac_farm_id = _insert_farm(
        sb, client_id,
        name="Levubu Macs",
        region="Limpopo",
        notes="600 m elevation, micro-irrigated, red apedal Hutton soils",
    )
    for f in MAC_FIELDS:
        field_id = _insert_field(
            sb, mac_farm_id,
            name=f["name"], area_ha=f["area_ha"],
            crop="Macadamia", cultivar=f["cultivar"], crop_type="perennial",
            planting_date=f["planting_date"], tree_age=f["tree_age"],
            pop_per_ha=f["pop_per_ha"],
            yield_target=f["yield_target"], yield_unit="t NIS/ha",
            irrigation_type="micro",
        )
        _insert_single_analysis(
            sb,
            agent_id=agent_id, client_id=client_id, farm_id=mac_farm_id, field_id=field_id,
            client_name=client_name, farm_name="Levubu Macs", field_name=f["name"],
            crop="Macadamia", cultivar=f["cultivar"],
            yield_target=f["yield_target"], yield_unit="t NIS/ha",
            soil_values=f["soil"], analysis_date=today,
            lab_name="NViroTek (test)", ref=ref,
        )
    print(f"  · Levubu Macs: {len(MAC_FIELDS)} fields")

    # Farm 2 — Citrus (Sundays River Valley, Eastern Cape)
    cit_farm_id = _insert_farm(
        sb, client_id,
        name="Sundays River Citrus",
        region="Eastern Cape",
        notes="Sundays River Valley, micro-irrigated, alluvial Oakleaf soils",
    )
    for f in CIT_FIELDS:
        field_id = _insert_field(
            sb, cit_farm_id,
            name=f["name"], area_ha=f["area_ha"],
            crop="Citrus", cultivar=f["cultivar"], crop_type="perennial",
            planting_date=f["planting_date"], tree_age=f["tree_age"],
            pop_per_ha=f["pop_per_ha"],
            yield_target=f["yield_target"], yield_unit="t/ha",
            irrigation_type="micro",
        )
        _insert_single_analysis(
            sb,
            agent_id=agent_id, client_id=client_id, farm_id=cit_farm_id, field_id=field_id,
            client_name=client_name, farm_name="Sundays River Citrus", field_name=f["name"],
            crop="Citrus", cultivar=f["cultivar"],
            yield_target=f["yield_target"], yield_unit="t/ha",
            soil_values=f["soil"], analysis_date=today,
            lab_name="NViroTek (test)", ref=ref,
        )
    print(f"  · Sundays River Citrus: {len(CIT_FIELDS)} fields")


# ─── Entry point ─────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    email = DEFAULT_AGENT_EMAIL
    for arg in argv:
        if arg.startswith("--email="):
            email = arg.split("=", 1)[1]

    sb = get_supabase_admin()
    agent_id = _find_agent(sb, email)
    print(f"Agent: {email} ({agent_id})")

    print("Purging prior [TEST] clients owned by this agent...")
    _purge_test(sb, agent_id)

    print("Loading reference data...")
    ref = _load_reference(sb)

    print("Seeding [TEST] Loskop Boerdery...")
    _seed(sb, agent_id, ref)

    print("\nDone. Re-run to reset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
