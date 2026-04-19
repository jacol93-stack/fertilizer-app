"""Seed demo scenarios for the multi-sample / multi-block workstream.

Creates 4 client/farm setups, each exercising a distinct feature path so
the agronomist (or future-me) can click through the real UI with realistic
data instead of a single empty test client.

Scenarios:
    1. Vrystaat Vennote (Bothaville, Free State) — 5 maize blocks with
       deliberately varied P/K targets. Build a programme across them to
       trigger the Phase 6 heterogeneity warning.
    2. Letaba Mac Estate (Tzaneen, Limpopo) — 3 macadamia fields, each
       seeded with a multi-zone composite analysis (area-weighted). Shows
       the composite badge + drawer panel in the field view.
    3. KZN Cane Co-op (Eshowe, KZN) — 4 sugarcane blocks with tight soil
       consistency. Baseline: programme build should NOT warn.
    4. Boland Wines (Paarl, WC) — one field with a legacy single-sample
       analysis from 2 days ago. Uploading fresh values triggers the
       Phase 7 conflict modal; merge-as-composite promotes the legacy row
       non-destructively.

Idempotent: deletes prior rows under clients with the `[DEMO]` name prefix
before re-seeding. Run from `sapling-api/`:

    ./venv/bin/python -m seeds.seed_multi_sample_demo

All numbers are grounded in FERTASA ranges for the relevant region/crop.
They're plausible, not field-measured — the point is to exercise the
aggregation math with realistic shapes.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from app.services.aggregation import aggregate_samples
from app.services.soil_engine import (
    adjust_targets_for_ratios,
    calculate_nutrient_targets,
    classify_soil_value,
    evaluate_ratios,
)
from app.supabase_client import get_supabase_admin

DEMO_PREFIX = "[DEMO]"
DEFAULT_AGENT_EMAIL = "info@saplingfertilizer.co.za"


# ─── Reference-data cache ────────────────────────────────────────────────


def _load_reference(sb):
    suf = sb.table("soil_sufficiency").select("*").execute().data or []
    ratios = sb.table("ideal_ratios").select("*").execute().data or []
    adjustments = sb.table("adjustment_factors").select("*").execute().data or []
    param_map = sb.table("soil_parameter_map").select("*").execute().data or []
    crop_reqs = sb.table("crop_requirements").select("*").execute().data or []
    return {
        "sufficiency": suf,
        "ratios": ratios,
        "adjustments": adjustments,
        "param_map": param_map,
        "crop_reqs": crop_reqs,
    }


def _compute_analysis_fields(crop: str, yield_target: float, soil_values: dict, ref: dict) -> dict:
    """Return the derived fields an analysis row needs — classifications,
    ratios, nutrient_targets — using the real soil engine.
    """
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
        raise SystemExit(
            f"No profile found for {email}. Pass --email <address> of an existing agent."
        )
    return r.data[0]["id"]


def _purge_demo(sb, agent_id: str):
    clients = (
        sb.table("clients")
        .select("id")
        .eq("agent_id", agent_id)
        .like("name", f"{DEMO_PREFIX}%")
        .execute()
    )
    for c in clients.data or []:
        cid = c["id"]
        # Explicit cascade — don't rely on ON DELETE CASCADE we can't guarantee.
        farm_rows = sb.table("farms").select("id").eq("client_id", cid).execute().data or []
        farm_ids = [f["id"] for f in farm_rows]
        if farm_ids:
            field_rows = sb.table("fields").select("id").in_("farm_id", farm_ids).execute().data or []
            field_ids = [f["id"] for f in field_rows]
            if field_ids:
                # Detach field→analysis link before deleting analyses, then the fields
                sb.table("fields").update({"latest_analysis_id": None}).in_("id", field_ids).execute()
                sb.table("soil_analyses").delete().in_("field_id", field_ids).execute()
            sb.table("soil_analyses").delete().in_("farm_id", farm_ids).execute()
            if field_ids:
                sb.table("fields").delete().in_("id", field_ids).execute()
            sb.table("farms").delete().in_("id", farm_ids).execute()
        sb.table("soil_analyses").delete().eq("client_id", cid).execute()
        sb.table("clients").delete().eq("id", cid).execute()


def _insert_client(sb, agent_id: str, name: str, contact: str, email: str, phone: str, notes: str) -> str:
    r = sb.table("clients").insert({
        "agent_id": agent_id,
        "name": f"{DEMO_PREFIX} {name}",
        "contact_person": contact,
        "email": email,
        "phone": phone,
        "notes": notes,
    }).execute()
    return r.data[0]["id"]


def _insert_farm(sb, client_id: str, name: str, region: str, notes: str) -> str:
    r = sb.table("farms").insert({
        "client_id": client_id,
        "name": name,
        "region": region,
        "notes": notes,
    }).execute()
    return r.data[0]["id"]


def _insert_field(
    sb, farm_id: str, name: str, area_ha: float, crop: str, crop_type: str,
    yield_target: float, yield_unit: str,
) -> str:
    r = sb.table("fields").insert({
        "farm_id": farm_id,
        "name": name,
        "size_ha": area_ha,
        "crop": crop,
        "crop_type": crop_type,
        "yield_target": yield_target,
        "yield_unit": yield_unit,
        "irrigation_type": "pivot" if crop == "Maize (dryland)" else "micro",
    }).execute()
    return r.data[0]["id"]


def _insert_single_analysis(
    sb, agent_id, client_id, farm_id, field_id, client_name, farm_name, field_name,
    crop, cultivar, yield_target, yield_unit, soil_values, analysis_date, ref,
) -> str:
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
        "lab_name": "NviroTek (demo)",
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


def _insert_composite_analysis(
    sb, agent_id, client_id, farm_id, field_id, client_name, farm_name, field_name,
    crop, cultivar, yield_target, yield_unit, zones, ref,
) -> str:
    """Aggregate N zone samples via the real primitive and persist the
    composite row with component retention. Mirrors what the soil.py
    create endpoint does when component_samples are supplied.
    """
    components = [
        {
            "values": {k: v for k, v in z["values"].items() if v is not None},
            **({"weight_ha": z["weight_ha"]} if z.get("weight_ha") is not None else {}),
            **({"location_label": z["location_label"]} if z.get("location_label") else {}),
            **({"depth_cm": z["depth_cm"]} if z.get("depth_cm") is not None else {}),
        }
        for z in zones
    ]
    weights = (
        [float(z["weight_ha"]) for z in zones]
        if all(z.get("weight_ha") and z["weight_ha"] > 0 for z in zones)
        else None
    )
    agg = aggregate_samples(components, weights=weights)
    derived = _compute_analysis_fields(crop, yield_target, agg.values, ref)

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
        "lab_name": "NviroTek (demo)",
        "analysis_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "soil_values": agg.values,
        "classifications": derived["classifications"],
        "ratio_results": derived["ratio_results"],
        "nutrient_targets": derived["nutrient_targets"],
        "status": "saved",
        "composition_method": agg.composition_method,
        "replicate_count": agg.replicate_count,
        "component_samples": components,
        "aggregation_stats": agg.stats_as_dict(),
    }
    r = sb.table("soil_analyses").insert(row).execute()
    analysis_id = r.data[0]["id"]
    sb.table("fields").update({"latest_analysis_id": analysis_id}).eq("id", field_id).execute()
    return analysis_id


# ─── Scenario definitions ────────────────────────────────────────────────


def _scenario_heterogeneous_maize(sb, agent_id: str, ref: dict):
    """Free State dryland maize — 5 blocks with varied soil P/K. A programme
    built across them should trip the Phase 6 heterogeneity warning (P CV
    clearly above 50%, K CV in the 25–35% band)."""
    client_id = _insert_client(
        sb, agent_id, "Vrystaat Vennote",
        "Jan de Villiers", "jan@vrystaat.example", "082 555 0001",
        "5-block maize farm, heterogeneous soils — use to demo programme CV warning",
    )
    farm_id = _insert_farm(sb, client_id, "Bothaville Hoof", "Free State", "Dryland maize on red Hutton")
    client_name = f"{DEMO_PREFIX} Vrystaat Vennote"
    farm_name = "Bothaville Hoof"

    blocks = [
        # (name, ha, soil_values)
        ("Block A", 40, {"pH (H2O)": 6.2, "Org C": 2.0, "P (Bray-1)": 12, "K": 150, "Ca": 800, "Mg": 180, "S": 10, "N (total)": 25, "Clay": 35}),
        ("Block B", 35, {"pH (H2O)": 6.1, "Org C": 1.8, "P (Bray-1)": 22, "K": 200, "Ca": 750, "Mg": 160, "S": 12, "N (total)": 22, "Clay": 32}),
        ("Block C", 50, {"pH (H2O)": 6.5, "Org C": 2.3, "P (Bray-1)": 35, "K": 280, "Ca": 920, "Mg": 210, "S": 15, "N (total)": 30, "Clay": 40}),
        ("Block D", 30, {"pH (H2O)": 6.3, "Org C": 2.1, "P (Bray-1)": 50, "K": 320, "Ca": 880, "Mg": 190, "S": 14, "N (total)": 28, "Clay": 38}),
        ("Block E", 45, {"pH (H2O)": 5.9, "Org C": 1.7, "P (Bray-1)": 18, "K": 180, "Ca": 700, "Mg": 140, "S": 9,  "N (total)": 20, "Clay": 28}),
    ]
    analysis_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for name, area, soil in blocks:
        field_id = _insert_field(sb, farm_id, name, area, "Maize (dryland)", "annual", 10.0, "t/ha")
        _insert_single_analysis(
            sb, agent_id, client_id, farm_id, field_id, client_name, farm_name, name,
            "Maize (dryland)", "PAN 5R-591", 10.0, "t/ha", soil, analysis_date, ref,
        )
    print(f"  · Vrystaat Vennote: 5 blocks, {sum(b[1] for b in blocks)} ha total")


def _scenario_multi_zone_macadamia(sb, agent_id: str, ref: dict):
    """Limpopo macadamia — 3 fields, each with 2–3 area-weighted zone
    composites already saved. Demonstrates composite badges and drawer
    component panel."""
    client_id = _insert_client(
        sb, agent_id, "Letaba Mac Estate",
        "Marlize van Zyl", "marlize@letabamac.example", "083 555 0002",
        "Three macadamia fields pre-seeded with multi-zone composite analyses",
    )
    farm_id = _insert_farm(sb, client_id, "Letaba Hoof", "Limpopo", "Premium macadamia at 600m elevation")
    client_name = f"{DEMO_PREFIX} Letaba Mac Estate"
    farm_name = "Letaba Hoof"

    fields = [
        {
            "name": "Field 1 — 788",
            "area": 18, "cultivar": "Beaumont",
            "zones": [
                {"location_label": "North ridge", "weight_ha": 5, "depth_cm": 30, "values": {"pH (H2O)": 5.8, "Org C": 1.2, "P (Bray-1)": 18, "K": 120, "Ca": 520, "Mg": 110, "S": 9, "Zn": 1.2, "B": 0.4}},
                {"location_label": "Mid-slope", "weight_ha": 8, "depth_cm": 30, "values": {"pH (H2O)": 6.0, "Org C": 1.4, "P (Bray-1)": 22, "K": 150, "Ca": 600, "Mg": 125, "S": 11, "Zn": 1.5, "B": 0.5}},
                {"location_label": "Foot-slope",  "weight_ha": 5, "depth_cm": 30, "values": {"pH (H2O)": 6.3, "Org C": 1.8, "P (Bray-1)": 30, "K": 180, "Ca": 680, "Mg": 145, "S": 13, "Zn": 1.7, "B": 0.6}},
            ],
        },
        {
            "name": "Field 2 — A4",
            "area": 12, "cultivar": "816",
            "zones": [
                {"location_label": "Irrigated corner", "weight_ha": 4, "depth_cm": 30, "values": {"pH (H2O)": 6.1, "Org C": 1.6, "P (Bray-1)": 25, "K": 160, "Ca": 630, "Mg": 130, "S": 12, "Zn": 1.4, "B": 0.5}},
                {"location_label": "Main block",      "weight_ha": 8, "depth_cm": 30, "values": {"pH (H2O)": 6.0, "Org C": 1.5, "P (Bray-1)": 23, "K": 155, "Ca": 610, "Mg": 128, "S": 11, "Zn": 1.3, "B": 0.5}},
            ],
        },
        {
            "name": "Field 3 — Riverblock",
            "area": 9, "cultivar": "Beaumont",
            "zones": [
                # Deliberately unequal — Wet patch has much lower pH/P
                {"location_label": "Wet patch (near river)", "weight_ha": 2, "depth_cm": 30, "values": {"pH (H2O)": 5.2, "Org C": 2.1, "P (Bray-1)": 9,  "K": 90,  "Ca": 380, "Mg": 80,  "S": 7, "Zn": 0.9, "B": 0.3}},
                {"location_label": "Dry plateau",            "weight_ha": 7, "depth_cm": 30, "values": {"pH (H2O)": 6.2, "Org C": 1.3, "P (Bray-1)": 26, "K": 165, "Ca": 640, "Mg": 130, "S": 12, "Zn": 1.5, "B": 0.5}},
            ],
        },
    ]
    for f in fields:
        field_id = _insert_field(sb, farm_id, f["name"], f["area"], "Macadamia", "perennial", 4.5, "t NIS/ha")
        _insert_composite_analysis(
            sb, agent_id, client_id, farm_id, field_id, client_name, farm_name, f["name"],
            "Macadamia", f["cultivar"], 4.5, "t NIS/ha", f["zones"], ref,
        )
    print(f"  · Letaba Mac Estate: 3 fields with multi-zone composites")


def _scenario_homogeneous_sugarcane(sb, agent_id: str, ref: dict):
    """KZN sugarcane — 4 blocks with tight soil consistency. Building a
    programme should NOT trigger the heterogeneity warning. Baseline to
    prove the gate isn't false-alarming."""
    client_id = _insert_client(
        sb, agent_id, "KZN Cane Co-op",
        "Thabo Ngcobo", "thabo@kzncane.example", "079 555 0003",
        "4 tightly matched sugarcane blocks — programme should build clean",
    )
    farm_id = _insert_farm(sb, client_id, "Eshowe Hoof", "KwaZulu-Natal", "Rain-fed sugarcane, Avalon soils")
    client_name = f"{DEMO_PREFIX} KZN Cane Co-op"
    farm_name = "Eshowe Hoof"

    # Tight clustering: P within ±10%, K within ±8%, etc.
    blocks = [
        ("Noord 1", 22, {"pH (H2O)": 5.6, "Org C": 2.5, "P (Bray-1)": 28, "K": 180, "Ca": 520, "Mg": 130, "S": 14, "N (total)": 32, "Clay": 38}),
        ("Noord 2", 25, {"pH (H2O)": 5.7, "Org C": 2.4, "P (Bray-1)": 30, "K": 190, "Ca": 540, "Mg": 135, "S": 15, "N (total)": 33, "Clay": 40}),
        ("Suid 1",  20, {"pH (H2O)": 5.6, "Org C": 2.6, "P (Bray-1)": 27, "K": 175, "Ca": 515, "Mg": 128, "S": 14, "N (total)": 31, "Clay": 37}),
        ("Suid 2",  24, {"pH (H2O)": 5.8, "Org C": 2.5, "P (Bray-1)": 29, "K": 185, "Ca": 525, "Mg": 132, "S": 15, "N (total)": 32, "Clay": 39}),
    ]
    analysis_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for name, area, soil in blocks:
        field_id = _insert_field(sb, farm_id, name, area, "Sugarcane", "annual", 75.0, "t/ha")
        _insert_single_analysis(
            sb, agent_id, client_id, farm_id, field_id, client_name, farm_name, name,
            "Sugarcane", "N41", 75.0, "t/ha", soil, analysis_date, ref,
        )
    print(f"  · KZN Cane Co-op: 4 homogeneous blocks (control)")


def _scenario_conflict_boland(sb, agent_id: str, ref: dict):
    """Western Cape wine grapes — one field carries a legacy single-sample
    analysis from 2 days ago. Uploading fresh values via the UI opens the
    Phase 7 conflict modal; merge-as-composite promotes the legacy row
    into a 2-component composite."""
    client_id = _insert_client(
        sb, agent_id, "Boland Wines",
        "Anelri Smit", "anelri@bolandwines.example", "084 555 0004",
        "Single-field Paarl vineyard — has a recent analysis to demo the conflict modal",
    )
    farm_id = _insert_farm(sb, client_id, "Paarl Hoofplaas", "Western Cape", "Shiraz on decomposed granite, dryland")
    client_name = f"{DEMO_PREFIX} Boland Wines"
    farm_name = "Paarl Hoofplaas"

    field_id = _insert_field(sb, farm_id, "Block Noord", 6.0, "Wine grapes", "perennial", 12.0, "t/ha")
    # 2-day-old analysis — inside the 7-day conflict window
    old_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    _insert_single_analysis(
        sb, agent_id, client_id, farm_id, field_id, client_name, farm_name, "Block Noord",
        "Wine grapes", "Shiraz SH 9C", 12.0, "t/ha",
        {"pH (H2O)": 6.1, "Org C": 1.6, "P (Bray-1)": 28, "K": 180, "Ca": 680, "Mg": 135, "S": 12, "Zn": 2.1, "B": 0.5, "Clay": 22},
        old_date, ref,
    )
    print(f"  · Boland Wines: 1 field with 2-day-old legacy analysis (upload to trigger conflict modal)")


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

    print("Purging prior [DEMO] clients...")
    _purge_demo(sb, agent_id)

    print("Loading reference data...")
    ref = _load_reference(sb)

    print("Seeding scenarios...")
    _scenario_heterogeneous_maize(sb, agent_id, ref)
    _scenario_multi_zone_macadamia(sb, agent_id, ref)
    _scenario_homogeneous_sugarcane(sb, agent_id, ref)
    _scenario_conflict_boland(sb, agent_id, ref)

    print("\nDone. Clients tagged with [DEMO] prefix — re-run to reset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
