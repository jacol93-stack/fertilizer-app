"""Blends router — optimize, save, list, update, delete."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, model_validator

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
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
    priorities: dict[str, str] | None = Field(
        None,
        description="Nutrient priorities: {nutrient: 'must_match' | 'flexible'}. If null, all treated equally."
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
    cost: float | None = None


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
    cost_per_ton: float | None = None
    sa_notation: str
    international_notation: str = ""
    pricing: dict | None = None
    batch_size: float
    min_compost_pct: float
    missed_targets: list[MissedTarget] = []
    priority_result: dict | None = None
    contact_sapling: bool = False


class BlendSave(BaseModel):
    blend_name: str = Field("Unnamed", max_length=200)
    blend_type: str = Field("dry", max_length=20)
    client_id: str | None = None
    farm_id: str | None = None
    field_id: str | None = None
    client: str | None = Field(None, max_length=200)
    farm: str | None = Field(None, max_length=200)
    field: str | None = Field(None, max_length=200)
    batch_size: float = Field(1000, gt=0, le=100_000)
    min_compost_pct: float = Field(0, ge=0, le=100)
    selling_price: float = Field(0, ge=0, le=100_000_000)
    cost_per_ton: float = Field(0, ge=0, le=100_000_000)
    targets: dict | None = None
    recipe: list[dict] | None = None
    nutrients: list[dict] | None = None
    selected_materials: list[str] | None = None
    # Liquid-specific fields
    tank_volume_l: float | None = None
    sg_estimate: float | None = None
    mixing_instructions: list[Any] | None = None
    # SA-notation liquid fields (mass-fraction flow, 2026-04-18)
    target_unit: str | None = None
    sa_notation: str | None = Field(None, max_length=120)
    international_notation: str | None = Field(None, max_length=200)
    density_kg_per_l: float | None = None
    nutrient_composition: list[dict] | None = None
    water_kg: float | None = None


class BlendOut(BaseModel):
    id: Any
    blend_name: str | None = None
    blend_type: str | None = "dry"
    client_id: str | None = None
    farm_id: str | None = None
    field_id: str | None = None
    client: str | None = None
    farm: str | None = None
    field: str | None = None
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
    # Liquid-specific fields
    tank_volume_l: float | None = None
    sg_estimate: float | None = None
    mixing_instructions: list[Any] | None = None

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


def _strip_liquid_meta(blend: dict) -> dict:
    """Remove the SA-notation `_meta` sentinel the save path stashes into
    `mixing_instructions`. Leaves human-readable string steps intact.

    TODO: once the `blends` schema grows first-class columns for
    sa_notation / international_notation / nutrient_composition /
    density_kg_per_l / water_kg, drop the stash-and-strip dance.
    """
    raw = blend.get("mixing_instructions")
    if isinstance(raw, list):
        blend["mixing_instructions"] = [
            m for m in raw
            if not (isinstance(m, dict) and m.get("_meta") == "sa_notation_label")
        ]
    return blend


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
    """Fire-and-forget audit log via Supabase RPC. Failures drop to debug."""
    try:
        sb = get_supabase_admin()
        sb.rpc("log_audit_event", {
            "p_event_type": event_type,
            "p_entity_type": entity_type,
            "p_entity_id": str(entity_id),
            "p_metadata": metadata,
            "p_user_id": user_id,
        }).execute()
    except Exception as _audit_exc:
        import logging as _logging
        _logging.getLogger("sapling.audit").debug(
            "log_audit_event failed: %s", _audit_exc, extra={"event_type": event_type}
        )


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

    priority_result = None
    contact_sapling = False

    if not res.success and body.priorities:
        # Priority-aware optimization
        from app.services.optimizer import run_priority_optimizer
        res, priority_result = run_priority_optimizer(
            targets, body.priorities, df, body.batch_size, c_idx, min_compost,
        )
        if res is None or not priority_result.get("feasible"):
            # Even with priorities, no feasible blend
            contact_sapling = True
            # Try to get a partial result for display
            res, scale = find_closest_blend(targets, df, body.batch_size, c_idx, min_compost)
            exact = False
            if res is None or not res.success:
                # Return empty result with contact_sapling flag
                return OptimizeResponse(
                    success=True,
                    exact=False,
                    scale=0,
                    recipe=[],
                    nutrients=[NutrientRow(nutrient=n, target=v, actual=0, diff=-v, kg_per_ton=0) for n, v in targets.items()],
                    cost_per_ton=0,
                    sa_notation="",
                    batch_size=body.batch_size,
                    min_compost_pct=body.min_compost_pct,
                    priority_result=priority_result,
                    contact_sapling=True,
                )
        else:
            exact = len(priority_result.get("compromised", [])) == 0
            scale = priority_result.get("scale", 1.0)

    elif not res.success:
        exact = False
        res, scale = find_closest_blend(targets, df, body.batch_size, c_idx, min_compost)
        if scale >= 0.999:
            exact = True
            scale = 1.0
        if res is None or not res.success:
            raise HTTPException(
                status_code=422,
                detail="This blend cannot be achieved with the selected materials and "
                       f"minimum compost of {int(body.min_compost_pct)}%. "
                       "Try lowering the compost minimum or adjusting your nutrient targets.",
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

        # Fetch quotes with pricing for comparables
        all_quotes = []
        try:
            q_result = sb.table("quotes").select(
                "quote_number, client_name, quoted_price, status, request_data, created_at"
            ).not_.is_("quoted_price", "null").execute()
            # Get agent names for display
            if q_result.data:
                all_quotes = q_result.data
        except Exception:
            pass

        pricing = suggest_price(
            actual_n=npk.get("N", 0),
            actual_p=npk.get("P", 0),
            actual_k=npk.get("K", 0),
            compost_pct=body.min_compost_pct,
            all_blends=all_blends,
            materials_df=materials_df,
            all_quotes=all_quotes,
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
        priority_result=priority_result,
        contact_sapling=contact_sapling,
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

    # Liquid SA-notation / Act 36 extras — the `blends` table schema has not
    # been extended with dedicated columns yet, so stash the label metadata
    # into the existing `mixing_instructions` JSONB as a single `_meta` entry
    # tacked onto the list. The PDF builder and download router can pull it
    # back out; legacy consumers iterate strings so a dict is ignored.
    # TODO: persist sa_notation / international_notation / nutrient_composition
    # / density_kg_per_l / water_kg once the blends schema is extended with
    # first-class columns (planned follow-up migration).
    _LIQUID_META_KEYS = (
        "sa_notation",
        "international_notation",
        "nutrient_composition",
        "density_kg_per_l",
        "water_kg",
        "target_unit",
    )
    liquid_meta = {k: data.pop(k) for k in _LIQUID_META_KEYS if k in data}
    if liquid_meta and data.get("blend_type") == "liquid":
        instructions = list(data.get("mixing_instructions") or [])
        instructions.append({"_meta": "sa_notation_label", **liquid_meta})
        data["mixing_instructions"] = instructions
        # Mirror density into sg_estimate (existing NUMERIC column) when the
        # caller didn't set it explicitly.
        if liquid_meta.get("density_kg_per_l") and not data.get("sg_estimate"):
            data["sg_estimate"] = liquid_meta["density_kg_per_l"]

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
    # Drop the SA-notation `_meta` entry from the mixing_instructions echo
    # so the frontend continues to see a list of human-readable strings.
    blend = _strip_liquid_meta(blend)
    return BlendOut(**blend)


@router.get("/", response_model=Page[dict])
def list_blends(
    page: PageParams = Depends(PageParams.as_query),
    search: str | None = Query(None, description="Search blend_name or client text"),
    client_id: str | None = Query(None, description="Filter by client ID"),
    farm_id: str | None = Query(None, description="Filter by farm ID"),
    field_id: str | None = Query(None, description="Filter by field ID"),
    user: CurrentUser = Depends(get_current_user),
):
    """List blends. Agents see own saved blends; admins see all."""
    sb = get_supabase_admin()
    query = sb.table("blends").select("*", count="exact")

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

    query = apply_page(query, page, default_order="created_at")
    result = query.execute()
    blends = [BlendOut(**_strip_liquid_meta(b)).model_dump() for b in (result.data or [])]
    stripped = _strip_costs(blends, user.role == "admin")
    return Page.from_list(stripped, page, total=getattr(result, "count", None))


# ── Nutrient limits (must be before /{blend_id} catch-all) ───────────

@router.get("/nutrient-limits")
def get_nutrient_limits(user: CurrentUser = Depends(get_current_user)):
    """Get nutrient safety limits for liquid blend input validation."""
    sb = get_supabase_admin()
    result = sb.table("nutrient_limits").select("nutrient,liquid_max_g_per_l,foliar_max_g_per_l").execute()
    if result.data:
        return {row["nutrient"]: {
            "liquid_max": float(row["liquid_max_g_per_l"]) if row.get("liquid_max_g_per_l") else None,
            "foliar_max": float(row["foliar_max_g_per_l"]) if row.get("foliar_max_g_per_l") else None,
        } for row in result.data}
    # Fallback
    from app.services.nutrient_limits import _FALLBACK_LIQUID_MAX, _FALLBACK_FOLIAR_MAX
    return {nut: {"liquid_max": _FALLBACK_LIQUID_MAX.get(nut), "foliar_max": _FALLBACK_FOLIAR_MAX.get(nut)} for nut in _FALLBACK_LIQUID_MAX}


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


# ── Foliar Spray ─────────────────────────────────────────────────────────

FOLIAR_NUTRIENTS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]


@router.get("/foliar-products")
def list_foliar_products(
    nutrients: str | None = Query(None, description="Comma-separated nutrients to filter by (e.g. 'zn,b,mn')"),
    user: CurrentUser = Depends(get_current_user),
):
    """List foliar spray products, optionally filtered by target nutrients.

    When nutrients are specified, only products containing at least one of them
    are returned, sorted by how many of the selected nutrients they cover (then
    by total concentration of those nutrients).
    """
    sb = get_supabase_admin()
    products = sb.table("liquid_products").select("*").eq("product_type", "foliar").order("name").execute()
    product_list = products.data or []

    wanted = [n.strip().lower() for n in nutrients.split(",") if n.strip()] if nutrients else []

    results = []
    for prod in product_list:
        breakdown = {}
        for nut in FOLIAR_NUTRIENTS:
            val = float(prod.get(nut, 0) or 0)
            if val > 0:
                breakdown[nut.upper()] = round(val, 2)

        # Filter: must contain at least one wanted nutrient
        if wanted:
            hits = [n for n in wanted if float(prod.get(n, 0) or 0) > 0]
            if not hits:
                continue
            hit_count = len(hits)
            hit_conc = sum(float(prod.get(n, 0) or 0) for n in hits)
        else:
            hit_count = 0
            hit_conc = 0

        unit = prod.get("analysis_unit", "g/kg")
        results.append({
            "name": prod["name"],
            "nutrients": breakdown,
            "analysis_unit": unit,
            "spray_volume_l_ha": prod.get("spray_volume_l_ha"),
            "dilution_rate": prod.get("dilution_rate"),
            "target_crops": prod.get("target_crops") or [],
            "notes": prod.get("notes", ""),
            "covers": [n.upper() for n in hits] if wanted else [],
            "_hit_count": hit_count,
            "_hit_conc": hit_conc,
        })

    # Sort: most nutrients covered first, then by total concentration
    if wanted:
        results.sort(key=lambda r: (-r["_hit_count"], -r["_hit_conc"]))

    for r in results:
        r.pop("_hit_count", None)
        r.pop("_hit_conc", None)

    return results


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

    return _strip_costs(BlendOut(**_strip_liquid_meta(blend)).model_dump(), user.role == "admin")


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
    targets: dict[str, float] = Field(
        ...,
        description=(
            "Nutrient targets. Interpreted as g/L (default) or m/m % of the "
            "finished solution depending on `target_unit`."
        ),
    )
    target_unit: str = Field(
        "g_per_l",
        pattern="^(g_per_l|m_m_pct)$",
        description=(
            "Unit for `targets`. 'g_per_l' keeps the legacy behaviour "
            "(grams per litre of finished solution); 'm_m_pct' uses mass/"
            "mass percentages, matching SA notation and Act 36 labels. "
            "m_m_pct is the preferred path — no SG guess is needed and the "
            "finished blend is guaranteed to hit the requested grade."
        ),
    )
    selected_materials: list[str] = Field(..., min_length=1)
    tank_volume_l: float = Field(1000, gt=0, le=100_000)
    priorities: dict[str, str] | None = Field(
        None,
        description="Nutrient priorities: {nutrient: 'must_match' | 'flexible'}. If null, all treated equally."
    )
    required_materials: dict[str, float] | None = Field(
        None,
        description="Compulsory materials: {material_name: pct_of_total_mass}. Each pct in (0, 100], sum ≤ 100."
    )


@router.post("/optimize-liquid")
def optimize_liquid(body: LiquidOptimizeRequest, user: CurrentUser = Depends(get_current_user)):
    """Optimize a custom liquid blend from selected raw materials.

    Accepts targets in either g/L (legacy) or m/m % (preferred). The m/m
    path runs a mass-fraction LP and reports the finished density as an
    output, which is how SA-registered liquid products are actually
    labelled. The g/L path still delegates to the legacy optimizer.
    """
    from app.services.liquid_optimizer import (
        optimize_liquid_blend,
        optimize_liquid_blend_mm,
        run_liquid_priority_optimizer,
        run_liquid_priority_optimizer_mm,
    )

    sb = get_supabase_admin()

    # Load selected materials (liquid-compatible only)
    all_mats = sb.table("materials").select("*").eq("liquid_compatible", True).execute()
    materials = [m for m in (all_mats.data or []) if m["material"] in body.selected_materials]

    if not materials:
        raise HTTPException(400, "No valid liquid-compatible materials selected")

    # Load compatibility rules
    compat = sb.table("material_compatibility").select("*").execute()
    compat_rules = compat.data or []

    use_mm = body.target_unit == "m_m_pct"

    if body.priorities:
        if use_mm:
            result = run_liquid_priority_optimizer_mm(
                targets_mm=body.targets,
                priorities=body.priorities,
                materials=materials,
                tank_volume_l=body.tank_volume_l,
                compatibility_rules=compat_rules,
                required_materials=body.required_materials,
            )
        else:
            result = run_liquid_priority_optimizer(
                targets=body.targets,
                priorities=body.priorities,
                materials=materials,
                tank_volume_l=body.tank_volume_l,
                compatibility_rules=compat_rules,
                required_materials=body.required_materials,
            )
    else:
        if use_mm:
            result = optimize_liquid_blend_mm(
                targets_mm=body.targets,
                materials=materials,
                tank_volume_l=body.tank_volume_l,
                compatibility_rules=compat_rules,
                required_materials=body.required_materials,
            )
        else:
            result = optimize_liquid_blend(
                targets=body.targets,
                materials=materials,
                tank_volume_l=body.tank_volume_l,
                compatibility_rules=compat_rules,
                required_materials=body.required_materials,
            )

    if not result.get("success"):
        raise HTTPException(400, result.get("error", "Optimization failed"))

    return result

