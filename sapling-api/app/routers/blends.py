"""Blends router — optimize, save, list, update, delete."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator

from app.auth import CurrentUser, get_current_user, require_admin
from app.rate_limit import limiter
from app.services.notation import pct_to_sa_notation
from app.services.optimizer import find_closest_blend, run_optimizer
from app.services.pricing import suggest_price
from app.supabase_client import get_supabase_admin

router = APIRouter(tags=["blends"])

COMPOST_NAME = "Manure Compost"

# Nutrient columns: DB lowercase -> optimizer uppercase
NUTRIENT_COLS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu", "c"]
NUTRIENT_UPPER = [c.upper() if len(c) <= 2 else c.capitalize() for c in NUTRIENT_COLS]
# Explicit mapping to match optimizer expectations
DB_TO_UPPER = {
    "n": "N", "p": "P", "k": "K", "ca": "Ca", "mg": "Mg", "s": "S",
    "fe": "Fe", "b": "B", "mn": "Mn", "zn": "Zn", "mo": "Mo", "cu": "Cu", "c": "C",
}


# ── Pydantic models ──────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    targets: dict[str, float] = Field(
        ..., description="Nutrient targets as {nutrient: pct}, e.g. {'N': 5.2, 'P': 1.8}"
    )
    selected_materials: list[str] = Field(
        ..., min_length=1, max_length=50,
        description="List of material names to include in optimization"
    )
    batch_size: float = Field(default=1000, gt=0, le=100_000)
    min_compost_pct: float = Field(default=0, ge=0, le=100)
    blend_mode: str = Field(
        default="compost", max_length=20,
        description="'compost' = compost-based blend, 'chemical' = pure chemical with filler (admin only)"
    )

    @model_validator(mode="after")
    def validate_targets_non_negative(self):
        for nutrient, value in self.targets.items():
            if value < 0:
                raise ValueError(f"Nutrient target '{nutrient}' cannot be negative ({value})")
        return self


class RecipeRow(BaseModel):
    material: str
    type: str | None = None
    kg: float
    pct: float
    cost: float


class NutrientRow(BaseModel):
    nutrient: str
    target: float
    actual: float
    diff: float
    kg_per_ton: float


class MissedTarget(BaseModel):
    nutrient: str
    target: float
    actual: float
    shortfall: float
    suggested_materials: list[str] = []


class OptimizeResponse(BaseModel):
    success: bool
    exact: bool
    scale: float
    recipe: list[RecipeRow]
    nutrients: list[NutrientRow]
    cost_per_ton: float
    sa_notation: str
    international_notation: str = ""
    pricing: dict | None = None
    batch_size: float
    min_compost_pct: float
    missed_targets: list[MissedTarget] = []


class BlendSave(BaseModel):
    blend_name: str = Field("Unnamed", max_length=200)
    client_id: str | None = None
    farm_id: str | None = None
    field_id: str | None = None
    client: str | None = Field(None, max_length=200)
    farm: str | None = Field(None, max_length=200)
    batch_size: float = Field(1000, gt=0, le=100_000)
    min_compost_pct: float = Field(0, ge=0, le=100)
    selling_price: float = Field(0, ge=0, le=100_000_000)
    cost_per_ton: float = Field(0, ge=0, le=100_000_000)
    targets: dict | None = None
    recipe: list[dict] | None = None
    nutrients: list[dict] | None = None
    selected_materials: list[str] | None = None


class BlendOut(BaseModel):
    id: Any
    blend_name: str | None = None
    client_id: str | None = None
    farm_id: str | None = None
    field_id: str | None = None
    client: str | None = None
    farm: str | None = None
    batch_size: float | None = None
    min_compost_pct: float | None = None
    selling_price: float | None = None
    cost_per_ton: float | None = None
    targets: dict | None = None
    recipe: list[dict] | None = None
    nutrients: list[dict] | None = None
    selected_materials: list[str] | None = None
    agent_id: str | None = None
    status: str | None = None
    created_at: str | None = None
    deleted_at: str | None = None
    deleted_by: str | None = None

    model_config = {"from_attributes": True}


class BlendUpdate(BaseModel):
    blend_name: str | None = Field(None, max_length=200)
    client: str | None = Field(None, max_length=200)
    farm: str | None = Field(None, max_length=200)
    client_id: str | None = None
    farm_id: str | None = None
    field_id: str | None = None
    selling_price: float | None = Field(None, ge=0, le=100_000_000)
    cost_per_ton: float | None = Field(None, ge=0, le=100_000_000)
    status: str | None = Field(None, max_length=20)
    targets: dict | None = None
    recipe: list[dict] | None = None
    nutrients: list[dict] | None = None
    selected_materials: list[str] | None = None


# ── Helpers ───────────────────────────────────────────────────────────────


def _strip_costs(data: dict | list, is_admin: bool) -> dict | list:
    """Remove cost fields from blend data for non-admin users."""
    if is_admin:
        return data

    COST_FIELDS = {"cost_per_ton", "selling_price", "pricing", "margin"}

    if isinstance(data, list):
        return [_strip_costs(item, is_admin) for item in data]

    if isinstance(data, dict):
        result = {k: v for k, v in data.items() if k not in COST_FIELDS}
        # Strip cost from recipe items
        if "recipe" in result and isinstance(result["recipe"], list):
            result["recipe"] = [
                {k: v for k, v in row.items() if k != "cost"} for row in result["recipe"]
            ]
        return result

    return data


def _load_materials_df(selected_names: list[str] | None = None) -> pd.DataFrame:
    """Load materials from DB into a DataFrame with uppercase nutrient columns."""
    sb = get_supabase_admin()
    result = sb.table("materials").select("*").execute()
    if not result.data:
        raise HTTPException(status_code=400, detail="No materials in database")

    df = pd.DataFrame(result.data)

    # Filter to selected materials if provided
    if selected_names:
        df = df[df["material"].isin(selected_names)].reset_index(drop=True)
        if df.empty:
            raise HTTPException(status_code=400, detail="None of the selected materials found")

    # Rename DB columns to uppercase for optimizer
    rename_map = {db: up for db, up in DB_TO_UPPER.items() if db in df.columns}
    df = df.rename(columns=rename_map)

    # Ensure numeric
    for col in DB_TO_UPPER.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def _find_compost_index(df: pd.DataFrame) -> int | None:
    """Find the index of the compost material, or None if not selected."""
    matches = df.index[df["material"] == COMPOST_NAME].tolist()
    return matches[0] if matches else None


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


def _audit_log(event_type: str, entity_type: str, entity_id: str, metadata: dict, user_id: str | None = None):
    """Fire-and-forget audit log via Supabase RPC."""
    try:
        sb = get_supabase_admin()
        sb.rpc("log_audit_event", {
            "p_event_type": event_type,
            "p_entity_type": entity_type,
            "p_entity_id": str(entity_id),
            "p_metadata": metadata,
            "p_user_id": user_id,
        }).execute()
    except Exception:
        pass  # Audit logging should never break the request


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/optimize", response_model=OptimizeResponse)
@limiter.limit("10/minute")
def optimize_blend(
    request: Request,
    body: OptimizeRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Run the blend optimizer and return recipe + nutrients + pricing."""
    # Chemical mode: admin only, uses filler instead of compost
    if body.blend_mode == "chemical" and user.role != "admin":
        raise HTTPException(status_code=403, detail="Chemical blend mode is admin-only")

    # Load materials
    materials_list = list(body.selected_materials)
    sb = get_supabase_admin()

    if body.blend_mode == "chemical":
        # Ensure filler is in the materials list
        defaults = sb.table("default_materials").select("chemical_filler_material").execute()
        filler_name = (defaults.data[0]["chemical_filler_material"]
                       if defaults.data else "Dolomitic Lime (Filler)")
        if filler_name not in materials_list:
            materials_list.append(filler_name)
    else:
        # Compost mode: ensure Manure Compost is included
        if COMPOST_NAME not in materials_list:
            materials_list.append(COMPOST_NAME)

    df = _load_materials_df(materials_list)

    if body.blend_mode == "chemical":
        filler_matches = df.index[df["material"] == filler_name].tolist()
        c_idx = filler_matches[0] if filler_matches else 0
        min_compost = 5  # Minimum 5% filler for consistency
    else:
        c_idx = _find_compost_index(df)
        min_compost = body.min_compost_pct
        if c_idx is None:
            c_idx = 0
            min_compost = 0

    # Normalize target keys to match DataFrame columns
    _KEY_MAP = {k.lower(): v for k, v in DB_TO_UPPER.items()}
    all_targets = {}
    for k, v in body.targets.items():
        normalized = _KEY_MAP.get(k.lower(), k)
        if v > 0:
            all_targets[normalized] = v

    # Optimize for ALL specified targets (not just NPK)
    targets = dict(all_targets)

    # Try exact optimization first
    exact = True
    scale = 1.0
    try:
        res = run_optimizer(targets, df, body.batch_size, c_idx, min_compost)
    except KeyError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Nutrient column {e} not found in materials data. Check target names.",
        )

    if not res.success:
        exact = False
        res, scale = find_closest_blend(targets, df, body.batch_size, c_idx, min_compost)
        if scale >= 0.999:
            exact = True
            scale = 1.0
        if res is None or not res.success:
            raise HTTPException(
                status_code=422,
                detail="Optimizer could not find a feasible blend with the given materials and targets. "
                       "Try reducing nutrient targets or adding more materials.",
            )

    amounts = res.x.tolist()

    # Build recipe and nutrient rows
    recipe = _build_recipe(df, amounts, body.batch_size)
    nutrients = _build_nutrients(df, amounts, all_targets, body.batch_size)
    cost_per_ton = sum(r["cost"] for r in recipe) / (body.batch_size / 1000) if body.batch_size else 0

    # SA notation from actual NPK + secondary nutrients that were targeted
    npk = {r["nutrient"]: r["actual"] for r in nutrients if r["nutrient"] in ("N", "P", "K")}
    secondary_targeted = {
        r["nutrient"]: r["actual"]
        for r in nutrients
        if r["nutrient"] not in ("N", "P", "K") and body.targets.get(r["nutrient"], 0) > 0
    }
    sa_notation, international_notation = pct_to_sa_notation(
        npk.get("N", 0), npk.get("P", 0), npk.get("K", 0),
        secondary_pcts=secondary_targeted if secondary_targeted else None,
    )

    # Pricing suggestion
    pricing = None
    try:
        sb = get_supabase_admin()
        all_blends = sb.table("blends").select("*").execute().data or []
        # Build materials_df with lowercase columns for pricing engine
        mat_result = sb.table("materials").select("*").execute()
        materials_df = pd.DataFrame(mat_result.data) if mat_result.data else pd.DataFrame()

        pricing = suggest_price(
            actual_n=npk.get("N", 0),
            actual_p=npk.get("P", 0),
            actual_k=npk.get("K", 0),
            compost_pct=body.min_compost_pct,
            all_blends=all_blends,
            materials_df=materials_df,
        )
    except Exception:
        pass  # Pricing is best-effort

    # Check for missed targets and suggest materials
    missed_targets = []
    if not exact or any(abs(n["diff"]) > 0.05 for n in nutrients if n["target"] > 0):
        # Load ALL materials (not just selected) to find suggestions
        all_mats_result = get_supabase_admin().table("materials").select("material, type, " + ", ".join(NUTRIENT_COLS)).execute()
        all_mats = all_mats_result.data or []

        for n in nutrients:
            if n["target"] > 0 and n["actual"] < n["target"] - 0.05:
                nut_key = n["nutrient"]
                db_key = nut_key.lower()
                shortfall = round(n["target"] - n["actual"], 2)

                # Find materials rich in this nutrient that aren't already selected
                suggestions = []
                for m in all_mats:
                    mat_name = m["material"]
                    if mat_name in body.selected_materials or mat_name == COMPOST_NAME:
                        continue
                    nut_val = float(m.get(db_key, 0) or 0)
                    if nut_val > 1:  # At least 1% of this nutrient
                        suggestions.append((mat_name, nut_val))

                suggestions.sort(key=lambda x: -x[1])
                top_suggestions = [f"{name} ({val}% {nut_key})" for name, val in suggestions[:3]]

                missed_targets.append(MissedTarget(
                    nutrient=nut_key,
                    target=n["target"],
                    actual=n["actual"],
                    shortfall=shortfall,
                    suggested_materials=top_suggestions,
                ))

    # Auto-save draft for audit trail (admin visibility only)
    try:
        draft_data = {
            "agent_id": user.id,
            "blend_name": f"[Draft] {sa_notation}",
            "batch_size": int(body.batch_size),
            "min_compost_pct": int(body.min_compost_pct),
            "cost_per_ton": round(cost_per_ton, 2),
            "targets": dict(body.targets),
            "recipe": recipe,
            "nutrients": nutrients,
            "selected_materials": list(body.selected_materials),
            "status": "draft",
        }
        draft_result = sb.table("blends").insert(draft_data).execute()
        if draft_result.data:
            _audit_log("blend_draft", "blends", str(draft_result.data[0]["id"]), {
                "sa_notation": sa_notation,
            }, user_id=user.id)
    except Exception:
        pass

    response = OptimizeResponse(
        success=True,
        exact=exact,
        scale=round(scale, 4),
        recipe=[RecipeRow(**r) for r in recipe],
        nutrients=[NutrientRow(**n) for n in nutrients],
        cost_per_ton=round(cost_per_ton, 2),
        sa_notation=sa_notation,
        international_notation=international_notation,
        pricing=pricing,
        batch_size=body.batch_size,
        min_compost_pct=body.min_compost_pct,
        missed_targets=missed_targets,
    )
    # Strip cost fields for non-admin users
    return _strip_costs(response.model_dump(), user.role == "admin")


@router.post("/", response_model=BlendOut, status_code=201)
def save_blend(
    body: BlendSave,
    user: CurrentUser = Depends(get_current_user),
):
    """Save a blend to the database."""
    sb = get_supabase_admin()
    data = body.model_dump(exclude_none=True)
    data["agent_id"] = user.id
    data["status"] = "saved"
    # Ensure integer types for DB columns that expect integer
    if "batch_size" in data:
        data["batch_size"] = int(data["batch_size"])
    if "min_compost_pct" in data:
        data["min_compost_pct"] = int(data["min_compost_pct"])

    result = sb.table("blends").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save blend")

    blend = result.data[0]
    audit_meta = {
        "blend_name": body.blend_name,
        "agent_id": user.id,
        "agent_email": user.email,
    }
    if user.impersonated_by:
        audit_meta["impersonated_by"] = user.impersonated_by
        audit_meta["impersonation"] = True
    _audit_log("blend_save", "blends", str(blend["id"]), audit_meta, user_id=user.impersonated_by or user.id)
    return BlendOut(**blend)


@router.get("/", response_model=list[BlendOut])
def list_blends(
    search: str | None = Query(None, description="Search blend_name or client text"),
    client_id: str | None = Query(None, description="Filter by client ID"),
    farm_id: str | None = Query(None, description="Filter by farm ID"),
    field_id: str | None = Query(None, description="Filter by field ID"),
    user: CurrentUser = Depends(get_current_user),
):
    """List blends. Agents see own saved blends; admins see all."""
    sb = get_supabase_admin()
    query = sb.table("blends").select("*").order("created_at", desc=True)

    if user.role != "admin":
        query = query.eq("agent_id", user.id).eq("status", "saved").is_("deleted_at", "null")

    if search:
        query = query.or_(
            f"blend_name.ilike.%{search}%,client.ilike.%{search}%"
        )
    if client_id:
        query = query.eq("client_id", client_id)
    if farm_id:
        query = query.eq("farm_id", farm_id)
    if field_id:
        query = query.eq("field_id", field_id)

    result = query.execute()
    blends = [BlendOut(**b).model_dump() for b in (result.data or [])]
    return _strip_costs(blends, user.role == "admin")


# ── Liquid & Foliar (must be before /{blend_id} catch-all) ─────────────


@router.get("/liquid-materials")
def list_liquid_materials(user: CurrentUser = Depends(get_current_user)):
    """List all liquid-compatible materials with solubility data."""
    sb = get_supabase_admin()
    result = sb.table("materials").select("*").eq("liquid_compatible", True).execute()
    return result.data or []


@router.get("/liquid-products")
def list_liquid_products(
    product_type: str | None = Query(None, description="Filter by type: foliar, fertigation, hydroponic"),
    user: CurrentUser = Depends(get_current_user),
):
    """List all liquid/foliar products from the catalog."""
    sb = get_supabase_admin()
    query = sb.table("liquid_products").select("*").order("name")
    if product_type:
        query = query.eq("product_type", product_type)
    result = query.execute()
    return result.data or []


@router.get("/{blend_id}")
def get_blend(
    blend_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Get a single blend. Agents can only access their own."""
    sb = get_supabase_admin()
    result = sb.table("blends").select("*").eq("id", blend_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Blend not found")

    blend = result.data[0]

    # Agents can only see their own blends
    if user.role != "admin" and blend.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return _strip_costs(BlendOut(**blend).model_dump(), user.role == "admin")


@router.patch("/{blend_id}", response_model=BlendOut)
def update_blend(
    blend_id: str,
    body: BlendUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Update blend fields (blend_name, selling_price, etc.)."""
    sb = get_supabase_admin()

    # Check ownership for non-admins
    if user.role != "admin":
        existing = sb.table("blends").select("agent_id").eq("id", blend_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Blend not found")
        if existing.data[0].get("agent_id") != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = sb.table("blends").update(updates).eq("id", blend_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Blend not found")

    _audit_log("blend_update", "blends", str(blend_id), {
        "updated_fields": list(updates.keys()),
        "user_id": user.id,
    }, user_id=user.id)
    return BlendOut(**result.data[0])


@router.post("/{blend_id}/delete", status_code=200)
def soft_delete_blend(
    blend_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Soft-delete a blend (set deleted_at and deleted_by)."""
    sb = get_supabase_admin()

    # Check ownership for non-admins
    if user.role != "admin":
        existing = sb.table("blends").select("agent_id").eq("id", blend_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Blend not found")
        if existing.data[0].get("agent_id") != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    result = sb.table("blends").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user.id,
    }).eq("id", blend_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Blend not found")

    _audit_log("blend_soft_delete", "blends", str(blend_id), {
        "deleted_by": user.id,
    }, user_id=user.id)
    return {"detail": "Blend soft-deleted"}


@router.post("/{blend_id}/restore")
def restore_blend(
    blend_id: str,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only. Restore a soft-deleted blend."""
    sb = get_supabase_admin()
    result = sb.table("blends").update({
        "deleted_at": None,
        "deleted_by": None,
    }).eq("id", blend_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Blend not found")

    _audit_log("blend_restore", "blends", str(blend_id), {
        "restored_by": user.id,
    }, user_id=user.id)
    return {"detail": "Blend restored"}


@router.delete("/{blend_id}", status_code=204)
def hard_delete_blend(
    blend_id: str,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only. Permanently delete a blend."""
    sb = get_supabase_admin()

    _audit_log("blend_hard_delete", "blends", str(blend_id), {
        "deleted_by": user.id,
    }, user_id=user.id)

    result = sb.table("blends").delete().eq("id", blend_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Blend not found")


# ── Liquid Blend ─────────────────────────────────────────────────────────


class LiquidOptimizeRequest(BaseModel):
    targets: dict[str, float] = Field(..., description="Nutrient targets in g/L")
    selected_materials: list[str] = Field(..., min_length=1)
    tank_volume_l: float = Field(1000, gt=0, le=100_000)


@router.post("/optimize-liquid")
def optimize_liquid(body: LiquidOptimizeRequest, user: CurrentUser = Depends(get_current_user)):
    """Optimize a custom liquid blend from selected raw materials.

    Targets are in g/L. Returns recipe with mixing instructions,
    SG estimate, and compatibility warnings.
    """
    from app.services.liquid_optimizer import optimize_liquid_blend

    sb = get_supabase_admin()

    # Load selected materials (liquid-compatible only)
    all_mats = sb.table("materials").select("*").eq("liquid_compatible", True).execute()
    materials = [m for m in (all_mats.data or []) if m["material"] in body.selected_materials]

    if not materials:
        raise HTTPException(400, "No valid liquid-compatible materials selected")

    # Load compatibility rules
    compat = sb.table("material_compatibility").select("*").execute()
    compat_rules = compat.data or []

    result = optimize_liquid_blend(
        targets=body.targets,
        materials=materials,
        tank_volume_l=body.tank_volume_l,
        compatibility_rules=compat_rules,
    )

    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Optimization failed"))

    return result


# ── Foliar Spray ─────────────────────────────────────────────────────────


class FoliarRecommendRequest(BaseModel):
    deficit: dict[str, float] = Field(..., description="Nutrient deficit in kg/ha")
    crop: str | None = Field(None, max_length=200)
    max_products: int = Field(3, ge=1, le=10)


@router.post("/recommend-foliar")
def recommend_foliar(body: FoliarRecommendRequest, user: CurrentUser = Depends(get_current_user)):
    """Recommend foliar spray products to cover a nutrient deficit.

    Deficit is in kg/ha. Returns ranked product recommendations with
    application rates, dilution, and coverage analysis.
    """
    from app.services.foliar_engine import recommend_foliar_products

    sb = get_supabase_admin()

    # Load foliar products
    products = sb.table("liquid_products").select("*").execute()
    product_list = products.data or []

    if not product_list:
        raise HTTPException(404, "No foliar products in catalog")

    result = recommend_foliar_products(
        deficit=body.deficit,
        products=product_list,
        crop=body.crop,
        max_products=body.max_products,
    )

    return result
