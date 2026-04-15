"""Feeding plans router — generate, save, list, update, optimize, delete."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
from app.rate_limit import limiter
from app.services.feeding_engine import generate_feeding_plan, build_practical_plan, validate_methods
from app.services.optimizer import find_closest_blend, run_optimizer
from app.supabase_client import get_supabase_admin

router = APIRouter(tags=["feeding_plans"])

# Nutrient columns: DB lowercase -> optimizer uppercase
DB_TO_UPPER = {
    "n": "N", "p": "P", "k": "K", "ca": "Ca", "mg": "Mg", "s": "S",
    "fe": "Fe", "b": "B", "mn": "Mn", "zn": "Zn", "mo": "Mo", "cu": "Cu", "c": "C",
}

COMPOST_NAME = "Manure Compost"

# Nutrient kg/ha columns on feeding_plan_items
NUTRIENT_KG_COLS = [
    "n_kg_ha", "p_kg_ha", "k_kg_ha", "ca_kg_ha", "mg_kg_ha", "s_kg_ha",
    "fe_kg_ha", "b_kg_ha", "mn_kg_ha", "zn_kg_ha", "mo_kg_ha", "cu_kg_ha",
]

# Map from kg column to uppercase nutrient name
KG_COL_TO_NUTRIENT = {
    "n_kg_ha": "N", "p_kg_ha": "P", "k_kg_ha": "K",
    "ca_kg_ha": "Ca", "mg_kg_ha": "Mg", "s_kg_ha": "S",
    "fe_kg_ha": "Fe", "b_kg_ha": "B", "mn_kg_ha": "Mn",
    "zn_kg_ha": "Zn", "mo_kg_ha": "Mo", "cu_kg_ha": "Cu",
}


# ── Pydantic models ──────────────────────────────────────────────────────

class NutrientTarget(BaseModel):
    Nutrient: str = Field(..., max_length=20)
    Target_kg_ha: float = Field(..., ge=0, le=10_000)


class GenerateRequest(BaseModel):
    soil_analysis_id: str | None = None
    crop: str = Field(..., min_length=1, max_length=200)
    crop_type: str = Field("perennial", max_length=20)
    tree_age: int | None = Field(None, ge=0, le=200)
    yield_target: float | None = Field(None, gt=0, le=1_000_000)
    field_area_ha: float | None = Field(None, gt=0, le=100_000)
    nutrient_targets: list[NutrientTarget]


class FeedingItemIn(BaseModel):
    stage_name: str = Field(..., max_length=200)
    feeding_order: int = Field(..., ge=0, le=100)
    month_target: int | None = Field(None, ge=1, le=12)
    method: str | None = Field("broadcast", max_length=50)
    n_kg_ha: float = Field(0, ge=0, le=10_000)
    p_kg_ha: float = Field(0, ge=0, le=10_000)
    k_kg_ha: float = Field(0, ge=0, le=10_000)
    ca_kg_ha: float = Field(0, ge=0, le=10_000)
    mg_kg_ha: float = Field(0, ge=0, le=10_000)
    s_kg_ha: float = Field(0, ge=0, le=10_000)
    fe_kg_ha: float = Field(0, ge=0, le=1_000)
    b_kg_ha: float = Field(0, ge=0, le=1_000)
    mn_kg_ha: float = Field(0, ge=0, le=1_000)
    zn_kg_ha: float = Field(0, ge=0, le=1_000)
    mo_kg_ha: float = Field(0, ge=0, le=1_000)
    cu_kg_ha: float = Field(0, ge=0, le=1_000)
    is_edited: bool = False
    notes: str | None = Field(None, max_length=2000)
    blend_recipe: list[dict] | None = None
    blend_nutrients: list[dict] | None = None
    blend_cost_per_ton: float | None = Field(None, ge=0, le=100_000_000)
    application_rate_kg_ha: float | None = Field(None, ge=0, le=100_000)
    cost_per_ha: float | None = Field(None, ge=0, le=100_000_000)


class PlanSave(BaseModel):
    plan_name: str = Field("Unnamed Plan", max_length=200)
    soil_analysis_id: str | None = None
    crop: str = Field(..., min_length=1, max_length=200)
    crop_type: str = Field("perennial", max_length=20)
    tree_age: int | None = Field(None, ge=0, le=200)
    yield_target: float | None = Field(None, gt=0, le=1_000_000)
    field_area_ha: float | None = Field(None, gt=0, le=100_000)
    total_cost_ha: float | None = Field(None, ge=0, le=100_000_000)
    notes: str | None = Field(None, max_length=2000)
    status: str = Field("draft", max_length=20)
    items: list[FeedingItemIn]


class PlanOut(BaseModel):
    id: Any
    plan_name: str | None = None
    soil_analysis_id: str | None = None
    crop: str | None = None
    crop_type: str | None = None
    tree_age: int | None = None
    yield_target: float | None = None
    field_area_ha: float | None = None
    total_cost_ha: float | None = None
    notes: str | None = None
    status: str | None = None
    agent_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
    deleted_by: str | None = None
    items: list[dict] | None = None

    model_config = {"from_attributes": True}


class PlanListOut(BaseModel):
    """Lighter model for list endpoint (no items)."""
    id: Any
    plan_name: str | None = None
    soil_analysis_id: str | None = None
    crop: str | None = None
    crop_type: str | None = None
    tree_age: int | None = None
    yield_target: float | None = None
    field_area_ha: float | None = None
    total_cost_ha: float | None = None
    notes: str | None = None
    status: str | None = None
    agent_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class PlanUpdate(BaseModel):
    plan_name: str | None = Field(None, max_length=200)
    notes: str | None = Field(None, max_length=2000)
    status: str | None = Field(None, max_length=20)
    total_cost_ha: float | None = Field(None, ge=0, le=100_000_000)
    yield_target: float | None = Field(None, gt=0, le=1_000_000)
    field_area_ha: float | None = Field(None, gt=0, le=100_000)


class ItemUpdate(BaseModel):
    stage_name: str | None = Field(None, max_length=200)
    feeding_order: int | None = Field(None, ge=0, le=100)
    month_target: int | None = Field(None, ge=1, le=12)
    method: str | None = Field(None, max_length=50)
    n_kg_ha: float | None = Field(None, ge=0, le=10_000)
    p_kg_ha: float | None = Field(None, ge=0, le=10_000)
    k_kg_ha: float | None = Field(None, ge=0, le=10_000)
    ca_kg_ha: float | None = Field(None, ge=0, le=10_000)
    mg_kg_ha: float | None = Field(None, ge=0, le=10_000)
    s_kg_ha: float | None = Field(None, ge=0, le=10_000)
    fe_kg_ha: float | None = Field(None, ge=0, le=1_000)
    b_kg_ha: float | None = Field(None, ge=0, le=1_000)
    mn_kg_ha: float | None = Field(None, ge=0, le=1_000)
    zn_kg_ha: float | None = Field(None, ge=0, le=1_000)
    mo_kg_ha: float | None = Field(None, ge=0, le=1_000)
    cu_kg_ha: float | None = Field(None, ge=0, le=1_000)
    notes: str | None = Field(None, max_length=2000)
    application_rate_kg_ha: float | None = Field(None, ge=0, le=100_000)


class OptimizeItemRequest(BaseModel):
    selected_materials: list[str] | None = None
    application_rate_kg_ha: float = Field(default=750, gt=0)
    batch_size: float = Field(default=1000, gt=0)
    min_compost_pct: float = Field(default=0, ge=0, le=100)


# ── Helpers ───────────────────────────────────────────────────────────────

def _audit_log(event_type: str, entity_type: str, entity_id: str, metadata: dict):
    """Fire-and-forget audit log via Supabase RPC. Failures drop to debug."""
    try:
        sb = get_supabase_admin()
        sb.rpc("log_audit_event", {
            "p_event_type": event_type,
            "p_entity_type": entity_type,
            "p_entity_id": str(entity_id),
            "p_metadata": metadata,
        }).execute()
    except Exception as _audit_exc:
        import logging as _logging
        _logging.getLogger("sapling.audit").debug(
            "log_audit_event failed: %s", _audit_exc, extra={"event_type": event_type}
        )


def _check_plan_ownership(plan: dict, user: CurrentUser):
    """Raise 403 if non-admin user does not own the plan."""
    if user.role != "admin" and plan.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")


def _get_plan_or_404(plan_id: str) -> dict:
    """Fetch a single feeding plan or raise 404."""
    sb = get_supabase_admin()
    result = sb.table("feeding_plans").select("*").eq("id", plan_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Feeding plan not found")
    return result.data[0]


def _get_item_or_404(item_id: str, plan_id: str) -> dict:
    """Fetch a single feeding plan item, verifying it belongs to the plan."""
    sb = get_supabase_admin()
    result = (
        sb.table("feeding_plan_items")
        .select("*")
        .eq("id", item_id)
        .eq("feeding_plan_id", plan_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Feeding plan item not found")
    return result.data[0]


def _load_materials_df(selected_names: list[str] | None = None) -> pd.DataFrame:
    """Load materials from DB into a DataFrame with uppercase nutrient columns."""
    sb = get_supabase_admin()
    result = sb.table("materials").select("*").execute()
    if not result.data:
        raise HTTPException(status_code=400, detail="No materials in database")

    df = pd.DataFrame(result.data)

    if selected_names:
        df = df[df["material"].isin(selected_names)].reset_index(drop=True)
        if df.empty:
            raise HTTPException(status_code=400, detail="None of the selected materials found")

    rename_map = {db: up for db, up in DB_TO_UPPER.items() if db in df.columns}
    df = df.rename(columns=rename_map)

    for col in DB_TO_UPPER.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def _find_compost_index(df: pd.DataFrame) -> int:
    """Find the index of the compost material in the DataFrame."""
    matches = df.index[df["material"] == COMPOST_NAME].tolist()
    if not matches:
        raise HTTPException(
            status_code=400,
            detail=f"Compost material '{COMPOST_NAME}' not found in selected materials. "
                   "Please include it in your selection.",
        )
    return matches[0]


def _build_recipe(df: pd.DataFrame, amounts: list[float], batch_size: float) -> list[dict]:
    """Build recipe rows from optimizer result amounts."""
    rows = []
    for i, kg in enumerate(amounts):
        if kg < 0.01:
            continue
        row = df.iloc[i]
        cost_per_ton = float(row.get("cost_per_ton", 0))
        rows.append({
            "material": row["material"],
            "type": row.get("type", ""),
            "kg": round(kg, 2),
            "pct": round(kg / batch_size * 100, 2),
            "cost": round(kg * cost_per_ton / 1000, 2),
        })
    return rows


def _build_nutrients(
    df: pd.DataFrame, amounts: list[float], targets: dict[str, float], batch_size: float,
) -> list[dict]:
    """Build nutrient summary rows."""
    rows = []
    all_nutrients = list(DB_TO_UPPER.values())
    for nut in all_nutrients:
        if nut not in df.columns:
            continue
        actual_kg = sum(
            amounts[i] * float(df.iloc[i].get(nut, 0)) / 100
            for i in range(len(amounts))
        )
        actual_pct = actual_kg / batch_size * 100 if batch_size else 0
        target_pct = targets.get(nut, 0)
        rows.append({
            "nutrient": nut,
            "target": round(target_pct, 3),
            "actual": round(actual_pct, 3),
            "diff": round(actual_pct - target_pct, 3),
            "kg_per_ton": round(actual_pct * 10, 2),
        })
    return rows


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/generate")
def generate_plan(
    body: GenerateRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Generate a feeding plan from nutrient targets and crop growth stages.

    Returns the generated items (not saved yet) so the user can review.
    """
    sb = get_supabase_admin()

    # 1. Load growth stages for the crop
    stages_result = (
        sb.table("crop_growth_stages")
        .select("*")
        .eq("crop", body.crop)
        .order("stage_order")
        .execute()
    )
    growth_stages = stages_result.data or []
    if not growth_stages:
        raise HTTPException(
            status_code=404,
            detail=f"No growth stages found for crop '{body.crop}'",
        )

    # 2. Load age factors for perennials
    age_factors = None
    if body.crop_type == "perennial":
        af_result = (
            sb.table("perennial_age_factors")
            .select("*")
            .eq("crop", body.crop)
            .execute()
        )
        age_factors = af_result.data or None

    # 3. Call the feeding engine
    nutrient_dicts = [nt.model_dump() for nt in body.nutrient_targets]
    items = generate_feeding_plan(
        nutrient_targets=nutrient_dicts,
        growth_stages=growth_stages,
        crop_type=body.crop_type,
        tree_age=body.tree_age,
        age_factors=age_factors,
        field_area_ha=body.field_area_ha,
    )

    # 4. Validate methods against crop_application_methods
    try:
        cam_result = sb.table("crop_application_methods").select("*").eq("crop", body.crop).execute()
        if cam_result.data:
            items = validate_methods(items, cam_result.data)
    except Exception:
        pass  # Method validation is best-effort

    return {
        "crop": body.crop,
        "crop_type": body.crop_type,
        "tree_age": body.tree_age,
        "field_area_ha": body.field_area_ha,
        "items": items,
    }


class PracticalPlanRequest(BaseModel):
    crop: str = Field(..., min_length=1, max_length=200)
    crop_type: str = Field("perennial", max_length=20)
    tree_age: int | None = Field(None, ge=0, le=200)
    yield_target: float | None = Field(None, gt=0, le=1_000_000)
    field_area_ha: float | None = Field(None, gt=0, le=100_000)
    plants_per_ha: int = Field(0, ge=0, le=1_000_000)
    nutrient_targets: list[NutrientTarget]
    application_months: list[int] = Field(
        ..., min_length=1, description="Months (1-12) the farmer will actually fertilize"
    )


@router.post("/practical")
def practical_plan(
    body: PracticalPlanRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Generate a practical feeding plan grouped into the farmer's chosen months.

    First generates the ideal plan from growth stages, then consolidates
    into the chosen application windows and groups similar blends.
    """
    sb = get_supabase_admin()

    # Load growth stages
    stages = sb.table("crop_growth_stages").select("*").eq("crop", body.crop).order("stage_order").execute()
    growth_stages = stages.data or []
    if not growth_stages:
        raise HTTPException(status_code=404, detail=f"No growth stages for '{body.crop}'")

    # Load age factors
    age_factors = None
    if body.crop_type == "perennial":
        af = sb.table("perennial_age_factors").select("*").eq("crop", body.crop).execute()
        age_factors = af.data or None

    # Generate ideal plan
    nutrient_dicts = [nt.model_dump() for nt in body.nutrient_targets]
    ideal_items = generate_feeding_plan(
        nutrient_targets=nutrient_dicts,
        growth_stages=growth_stages,
        crop_type=body.crop_type,
        tree_age=body.tree_age,
        age_factors=age_factors,
        field_area_ha=body.field_area_ha,
    )

    # Validate methods
    try:
        cam_result = sb.table("crop_application_methods").select("*").eq("crop", body.crop).execute()
        if cam_result.data:
            ideal_items = validate_methods(ideal_items, cam_result.data)
    except Exception:
        pass

    # Build practical plan
    applications = build_practical_plan(
        ideal_items=ideal_items,
        application_months=body.application_months,
        plants_per_ha=body.plants_per_ha,
    )

    # Auto-blend each application
    is_admin = user.role == "admin"
    mat_result = sb.table("materials").select("*").execute()
    all_materials = mat_result.data or []

    # Load defaults for material selection
    defaults = sb.table("default_materials").select("*").execute()
    default_row = defaults.data[0] if defaults.data else {}
    default_mat_names = default_row.get("materials", [])
    min_compost_pct = float(default_row.get("agent_min_compost_pct", 50))

    # Include compost
    COMPOST = "Manure Compost"
    selected_names = list(set(default_mat_names + [COMPOST]))

    # Build DataFrame for optimizer
    import numpy as np
    selected_mats = [m for m in all_materials if m["material"] in selected_names]
    if not selected_mats:
        selected_mats = all_materials

    df = pd.DataFrame(selected_mats)
    for col in DB_TO_UPPER:
        upper = DB_TO_UPPER.get(col, col.upper())
        if col in df.columns:
            df[upper] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Find compost index
    compost_matches = df.index[df["material"] == COMPOST].tolist()
    c_idx = compost_matches[0] if compost_matches else 0

    # Load markups for agent pricing
    markups = {}
    if not is_admin:
        mk_result = sb.table("material_markups").select("*").execute()
        markups = {r["material"]: float(r["markup_pct"]) for r in (mk_result.data or [])}

    total_cost_ha = 0
    blend_summaries = {}  # blend_group -> blend details

    for app in applications:
        # Calculate target kg/ha for NPK
        npk_kg = {nut: app.get(f"{nut.lower()}_kg_ha", 0) for nut in ["N", "P", "K"]}
        total_npk = sum(npk_kg.values())
        if total_npk < 0.1:
            app["blend_recipe"] = []
            app["blend_cost_per_ton"] = 0
            app["application_rate_kg_ha"] = 0
            app["cost_per_ha"] = 0
            continue

        # 50% compost is a manufacturing hard deck — non-negotiable.
        # At 50% compost, some nutrients (especially P) will be over-delivered.
        # Strategy: set app rate based on the HIGHEST-DEMAND nutrient (N or K)
        # so that one is hit correctly, and accept over/under on the rest.
        compost_row = df.iloc[c_idx]

        # Calculate what 50% compost provides per ton of blend
        compost_n_pct = float(compost_row.get("N", 0))  # e.g. 2.13%
        compost_k_pct = float(compost_row.get("K", 0))  # e.g. 1.64%

        # N from compost at 50%: compost_n_pct * 50 / 100 = effective N% from compost
        # Chemical can add more N on top. So we need app_rate where:
        # app_rate * target_N_pct / 100 = N_kg_ha
        # We want target_N_pct to be achievable given materials.
        # A good starting point: the N requirement drives the rate.
        n_kg = npk_kg.get("N", 0)
        k_kg = npk_kg.get("K", 0)

        # The blend will have some total N% — at 50% compost + chemicals.
        # Compost gives ~1.07% N (at 50% of blend), chemicals can add up to ~20% more.
        # So max blend N% is ~21%. Typical is 3-8% for compost blends.
        # Use the N target to determine rate: rate = N_kg / (blend_N_pct / 100)
        # Estimate blend N% based on what's achievable
        max_chem_n = max(float(df.iloc[i].get("N", 0)) for i in range(len(df)) if i != c_idx)
        # At 50% compost + 50% of the highest-N chemical:
        est_max_n_pct = compost_n_pct * 0.5 + max_chem_n * 0.5
        # Target a blend where N is about 60% of max (reasonable middle ground)
        est_n_pct = max(est_max_n_pct * 0.4, 2.0)  # At least 2%

        if n_kg > 0.1:
            app_rate = n_kg / (est_n_pct / 100)
        elif k_kg > 0.1:
            est_k_pct = max(compost_k_pct * 0.5 + 25 * 0.5, 2.0)  # KCL is 50% K
            app_rate = k_kg / (est_k_pct / 100)
        else:
            app_rate = 500

        app_rate = max(200, min(3000, round(app_rate, 0)))

        # Only constrain N and K — P will be over-delivered by compost
        # (agronomically acceptable for compost-based blends)
        targets = {}
        for nut in ["N", "K"]:
            kg = npk_kg.get(nut, 0)
            if kg > 0.01:
                targets[nut] = kg / app_rate * 100

        if not targets:
            continue

        try:
            # Hard minimum 50% compost — no exceptions
            res = run_optimizer(targets, df, app_rate, c_idx, min_compost_pct)
            if not res.success:
                # Try adjusting app rate up/down to find feasibility
                for rate_adj in [1.2, 1.5, 0.8, 2.0, 0.6]:
                    adj_rate = round(app_rate * rate_adj, 0)
                    adj_targets = {nut: kg / adj_rate * 100 for nut, kg in targets.items() if kg > 0}
                    res = run_optimizer(adj_targets, df, adj_rate, c_idx, min_compost_pct)
                    if res.success:
                        app_rate = adj_rate
                        targets = adj_targets
                        break
            if not res or not res.success:
                res, _ = find_closest_blend(targets, df, app_rate, c_idx, min_compost_pct)

            if res and res.success:
                amounts = res.x.tolist()
                recipe = []
                cost_per_ton = 0
                for i, kg in enumerate(amounts):
                    if kg < 0.01:
                        continue
                    row = df.iloc[i]
                    mat_cost = float(row.get("cost_per_ton", 0))
                    if not is_admin and row["material"] in markups:
                        mat_cost *= (1 + markups[row["material"]] / 100)
                    item_cost = kg * mat_cost / 1000
                    recipe.append({
                        "material": row["material"],
                        "type": row.get("type", ""),
                        "kg": round(kg, 2),
                        "pct": round(kg / app_rate * 100, 2),
                        "cost": round(item_cost, 2),
                    })
                    cost_per_ton += item_cost

                cost_per_ton = cost_per_ton / (app_rate / 1000) if app_rate else 0
                cost_ha = cost_per_ton * app_rate / 1000

                app["blend_recipe"] = recipe if is_admin else []
                app["blend_cost_per_ton"] = round(cost_per_ton, 2)
                app["application_rate_kg_ha"] = round(app_rate, 0)
                app["cost_per_ha"] = round(cost_ha, 2)
                if body.plants_per_ha and body.plants_per_ha > 0:
                    app["cost_per_tree"] = round(cost_ha / body.plants_per_ha, 2)
                    app["rate_kg_tree"] = round(app_rate / body.plants_per_ha, 3)

                total_cost_ha += cost_ha

                # Track blend summary per group
                group = app.get("blend_group", "A")
                if group not in blend_summaries:
                    blend_summaries[group] = {
                        "group": group,
                        "recipe": recipe if is_admin else [],
                        "cost_per_ton": round(cost_per_ton, 2),
                        "npk_ratio": app.get("npk_ratio", ""),
                        "months": [],
                    }
                blend_summaries[group]["months"].append(app.get("month_name", ""))
        except Exception:
            app["blend_recipe"] = []
            app["blend_cost_per_ton"] = 0
            app["application_rate_kg_ha"] = 0
            app["cost_per_ha"] = 0

    total_cost_field = total_cost_ha * (body.field_area_ha or 1)

    result = {
        "crop": body.crop,
        "applications": applications,
        "num_applications": len(applications),
        "blend_groups": list(blend_summaries.values()),
        "total_cost_ha": round(total_cost_ha, 2),
        "total_cost_tree": round(total_cost_ha / body.plants_per_ha, 2) if body.plants_per_ha else None,
        "plants_per_ha": body.plants_per_ha,
    }

    # Auto-save draft for audit trail
    try:
        draft_data = {
            "agent_id": user.id,
            "plan_name": f"[Draft] {body.crop}",
            "crop": body.crop,
            "crop_type": body.crop_type,
            "tree_age": body.tree_age,
            "yield_target": body.yield_target,
            "field_area_ha": body.field_area_ha,
            "total_cost_ha": round(total_cost_ha, 2),
            "status": "draft",
        }
        draft_result = sb.table("feeding_plans").insert(draft_data).execute()
        if draft_result.data:
            _audit_log("feeding_plan_draft", "feeding_plans", str(draft_result.data[0]["id"]), {
                "crop": body.crop,
                "agent_id": user.id,
            })
    except Exception:
        pass

    return result


@router.post("/", response_model=PlanOut, status_code=201)
def save_plan(
    body: PlanSave,
    user: CurrentUser = Depends(get_current_user),
):
    """Save a feeding plan with all items to the database."""
    sb = get_supabase_admin()

    # Insert plan metadata
    plan_data = body.model_dump(exclude={"items"}, exclude_none=True)
    plan_data["agent_id"] = user.id

    plan_result = sb.table("feeding_plans").insert(plan_data).execute()
    if not plan_result.data:
        raise HTTPException(status_code=500, detail="Failed to save feeding plan")

    plan = plan_result.data[0]
    plan_id = plan["id"]

    # Insert all items
    items_data = []
    for item in body.items:
        item_dict = item.model_dump(exclude_none=True)
        item_dict["feeding_plan_id"] = plan_id
        items_data.append(item_dict)

    if items_data:
        items_result = sb.table("feeding_plan_items").insert(items_data).execute()
        plan["items"] = items_result.data or []
    else:
        plan["items"] = []

    _audit_log("feeding_plan_save", "feeding_plan", str(plan_id), {
        "plan_name": body.plan_name,
        "crop": body.crop,
        "agent_id": user.id,
        "agent_email": user.email,
        "item_count": len(items_data),
    })

    return PlanOut(**plan)


@router.get("/", response_model=Page[PlanListOut])
def list_plans(
    page: PageParams = Depends(PageParams.as_query),
    search: str | None = Query(None, description="Search plan_name or crop text"),
    soil_analysis_ids: str | None = Query(None, description="Comma-separated soil analysis IDs"),
    user: CurrentUser = Depends(get_current_user),
):
    """List feeding plans. Agents see own; admins see all."""
    sb = get_supabase_admin()
    query = sb.table("feeding_plans").select("*", count="exact")

    if user.role != "admin":
        query = query.eq("agent_id", user.id).is_("deleted_at", "null")

    if search:
        query = query.or_(
            f"plan_name.ilike.%{search}%,crop.ilike.%{search}%"
        )
    if soil_analysis_ids:
        ids_list = [s.strip() for s in soil_analysis_ids.split(",") if s.strip()]
        if ids_list:
            query = query.in_("soil_analysis_id", ids_list)

    query = apply_page(query, page, default_order="created_at")
    result = query.execute()
    items = [PlanListOut(**p) for p in (result.data or [])]
    return Page.from_list(items, page, total=getattr(result, "count", None))


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(
    plan_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Get a single feeding plan with all items."""
    plan = _get_plan_or_404(plan_id)
    _check_plan_ownership(plan, user)

    # Load items
    sb = get_supabase_admin()
    items_result = (
        sb.table("feeding_plan_items")
        .select("*")
        .eq("feeding_plan_id", plan_id)
        .order("feeding_order")
        .execute()
    )
    plan["items"] = items_result.data or []

    return PlanOut(**plan)


@router.patch("/{plan_id}", response_model=PlanOut)
def update_plan(
    plan_id: str,
    body: PlanUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Update plan metadata (notes, status, total_cost_ha, etc.)."""
    sb = get_supabase_admin()

    # Ownership check
    plan = _get_plan_or_404(plan_id)
    _check_plan_ownership(plan, user)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = sb.table("feeding_plans").update(updates).eq("id", plan_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update feeding plan")

    updated_plan = result.data[0]

    # Load items for response
    items_result = (
        sb.table("feeding_plan_items")
        .select("*")
        .eq("feeding_plan_id", plan_id)
        .order("feeding_order")
        .execute()
    )
    updated_plan["items"] = items_result.data or []

    _audit_log("feeding_plan_update", "feeding_plan", str(plan_id), {
        "updated_fields": list(updates.keys()),
        "user_id": user.id,
    })

    return PlanOut(**updated_plan)


@router.patch("/{plan_id}/items/{item_id}")
def update_item(
    plan_id: str,
    item_id: str,
    body: ItemUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Update a single feeding plan item. Sets is_edited=true."""
    sb = get_supabase_admin()

    # Ownership check via the plan
    plan = _get_plan_or_404(plan_id)
    _check_plan_ownership(plan, user)

    # Verify item belongs to plan
    _get_item_or_404(item_id, plan_id)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates["is_edited"] = True

    result = (
        sb.table("feeding_plan_items")
        .update(updates)
        .eq("id", item_id)
        .eq("feeding_plan_id", plan_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update feeding plan item")

    _audit_log("feeding_item_update", "feeding_plan_item", str(item_id), {
        "plan_id": plan_id,
        "updated_fields": list(updates.keys()),
        "user_id": user.id,
    })

    return result.data[0]


@router.post("/{plan_id}/items/{item_id}/optimize")
@limiter.limit("10/minute")
def optimize_item(
    request: Request,
    plan_id: str,
    item_id: str,
    body: OptimizeItemRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Run the blend optimizer for a single feeding plan item.

    Converts the item's nutrient kg/ha values into blend target percentages
    based on the application rate, then optimizes a blend recipe.
    """
    sb = get_supabase_admin()

    # Ownership check
    plan = _get_plan_or_404(plan_id)
    _check_plan_ownership(plan, user)

    # Get the item
    item = _get_item_or_404(item_id, plan_id)

    # 1. Extract nutrient kg/ha values from the item
    nutrient_kg = {}
    for col, nut in KG_COL_TO_NUTRIENT.items():
        val = float(item.get(col, 0))
        if val > 0:
            nutrient_kg[nut] = val

    if not nutrient_kg:
        raise HTTPException(
            status_code=400,
            detail="Item has no nutrient values to optimize.",
        )

    # 2. Load materials
    df = _load_materials_df(body.selected_materials)
    c_idx = _find_compost_index(df)

    # 3. Convert nutrients to blend target percentages
    #    target_pct = (nutrient_kg_ha / application_rate_kg_ha) * 100
    app_rate = body.application_rate_kg_ha
    targets = {}
    for nut, kg in nutrient_kg.items():
        pct = (kg / app_rate) * 100
        if pct > 0:
            targets[nut] = round(pct, 4)

    if not targets:
        raise HTTPException(
            status_code=400,
            detail="Calculated target percentages are all zero.",
        )

    # 4. Run optimizer — exact first, fallback to closest blend
    exact = True
    scale = 1.0
    res = run_optimizer(targets, df, body.batch_size, c_idx, body.min_compost_pct)

    if not res.success:
        exact = False
        res, scale = find_closest_blend(
            targets, df, body.batch_size, c_idx, body.min_compost_pct,
        )
        if res is None or not res.success:
            raise HTTPException(
                status_code=422,
                detail="Optimizer could not find a feasible blend with the given materials and targets.",
            )

    amounts = res.x.tolist()

    # 5. Build recipe and nutrient rows
    recipe = _build_recipe(df, amounts, body.batch_size)
    nutrients = _build_nutrients(df, amounts, targets, body.batch_size)
    cost_per_ton = (
        sum(r["cost"] for r in recipe) / (body.batch_size / 1000)
        if body.batch_size else 0
    )
    cost_per_ha = round(cost_per_ton * app_rate / 1000, 2)

    # 6. Update the item in the database
    item_updates = {
        "blend_recipe": recipe,
        "blend_nutrients": nutrients,
        "blend_cost_per_ton": round(cost_per_ton, 2),
        "application_rate_kg_ha": app_rate,
        "cost_per_ha": cost_per_ha,
    }

    result = (
        sb.table("feeding_plan_items")
        .update(item_updates)
        .eq("id", item_id)
        .eq("feeding_plan_id", plan_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update item with blend data")

    updated_item = result.data[0]

    _audit_log("feeding_item_optimize", "feeding_plan_item", str(item_id), {
        "plan_id": plan_id,
        "exact": exact,
        "scale": round(scale, 4),
        "cost_per_ton": round(cost_per_ton, 2),
        "cost_per_ha": cost_per_ha,
        "user_id": user.id,
    })

    return {
        **updated_item,
        "optimizer_result": {
            "success": True,
            "exact": exact,
            "scale": round(scale, 4),
            "cost_per_ton": round(cost_per_ton, 2),
            "cost_per_ha": cost_per_ha,
        },
    }


@router.delete("/{plan_id}", status_code=200)
def delete_plan(
    plan_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Delete a feeding plan. Agents: soft-delete. Admins: hard delete."""
    sb = get_supabase_admin()
    plan = _get_plan_or_404(plan_id)
    _check_plan_ownership(plan, user)

    if user.role == "admin":
        # Hard delete: remove items first, then plan
        sb.table("feeding_plan_items").delete().eq("feeding_plan_id", plan_id).execute()
        result = sb.table("feeding_plans").delete().eq("id", plan_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Feeding plan not found")

        _audit_log("feeding_plan_hard_delete", "feeding_plan", str(plan_id), {
            "deleted_by": user.id,
        })
        return {"detail": "Feeding plan permanently deleted"}
    else:
        # Soft delete
        result = sb.table("feeding_plans").update({
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": user.id,
        }).eq("id", plan_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Feeding plan not found")

        _audit_log("feeding_plan_soft_delete", "feeding_plan", str(plan_id), {
            "deleted_by": user.id,
        })
        return {"detail": "Feeding plan soft-deleted"}
