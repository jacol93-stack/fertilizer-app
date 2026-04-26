"""Materials CRUD router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.supabase_client import get_supabase_admin, run_sb

router = APIRouter(tags=["materials"])

# ── Nutrient columns in the DB ────────────────────────────────────────────
NUTRIENT_COLS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu", "c"]


# ── Pydantic models ──────────────────────────────────────────────────────

class MaterialOut(BaseModel):
    id: str | None = None
    material: str
    type: str | None = None
    form: str | None = None
    liquid_compatible: bool = False
    cost_per_ton: float = 0
    n: float = 0
    p: float = 0
    k: float = 0
    ca: float = 0
    mg: float = 0
    s: float = 0
    fe: float = 0
    b: float = 0
    mn: float = 0
    zn: float = 0
    mo: float = 0
    cu: float = 0
    c: float = 0
    # Liquid-blend physical properties. solubility_20c is g of solute per L
    # of pure water at 20°C; sg is the material's own density (kg/L). Both
    # are optional — only liquid-compatible materials need them, and the
    # liquid optimizer falls back to safe defaults when absent.
    solubility_20c: float | None = None
    sg: float | None = None


class MaterialCreate(BaseModel):
    material: str = Field(..., min_length=1, max_length=200)
    type: str | None = Field(None, max_length=100)
    form: str = Field("solid", pattern="^(solid|liquid|chelate)$")
    liquid_compatible: bool = False
    cost_per_ton: float = Field(0, ge=0, le=10_000_000)
    n: float = Field(0, ge=0, le=100)
    p: float = Field(0, ge=0, le=100)
    k: float = Field(0, ge=0, le=100)
    ca: float = Field(0, ge=0, le=100)
    mg: float = Field(0, ge=0, le=100)
    s: float = Field(0, ge=0, le=100)
    fe: float = Field(0, ge=0, le=100)
    b: float = Field(0, ge=0, le=100)
    mn: float = Field(0, ge=0, le=100)
    zn: float = Field(0, ge=0, le=100)
    mo: float = Field(0, ge=0, le=100)
    cu: float = Field(0, ge=0, le=100)
    c: float = Field(0, ge=0, le=100)
    solubility_20c: float | None = Field(None, ge=0, le=5000, description="Solubility at 20°C — g of solute per L of water")
    sg: float | None = Field(None, ge=0.5, le=3.0, description="Material density (kg/L). Liquids: e.g. phosphoric acid 80% = 1.57")


class MaterialUpdate(BaseModel):
    material: str | None = Field(None, min_length=1, max_length=200)
    type: str | None = Field(None, max_length=100)
    form: str | None = Field(None, pattern="^(solid|liquid|chelate)$")
    liquid_compatible: bool | None = None
    cost_per_ton: float | None = Field(None, ge=0, le=10_000_000)
    n: float | None = Field(None, ge=0, le=100)
    p: float | None = Field(None, ge=0, le=100)
    k: float | None = Field(None, ge=0, le=100)
    ca: float | None = Field(None, ge=0, le=100)
    mg: float | None = Field(None, ge=0, le=100)
    s: float | None = Field(None, ge=0, le=100)
    fe: float | None = Field(None, ge=0, le=100)
    b: float | None = Field(None, ge=0, le=100)
    mn: float | None = Field(None, ge=0, le=100)
    zn: float | None = Field(None, ge=0, le=100)
    mo: float | None = Field(None, ge=0, le=100)
    cu: float | None = Field(None, ge=0, le=100)
    c: float | None = Field(None, ge=0, le=100)
    solubility_20c: float | None = Field(None, ge=0, le=5000)
    sg: float | None = Field(None, ge=0.5, le=3.0)


class MarkupOut(BaseModel):
    material: str
    markup_pct: float


class MarkupSet(BaseModel):
    markup_pct: float = Field(..., ge=0, description="Markup percentage (e.g. 15 means 15%)")

class BulkMarkupItem(BaseModel):
    material: str
    markup_pct: float = Field(..., ge=0)


class DefaultMaterialsOut(BaseModel):
    materials: list[str]
    liquid_materials: list[str] = []
    agent_min_compost_pct: float = 50
    chemical_filler_material: str = "Dolomitic Lime (Filler)"
    variability_margin: float = 15.0
    cluster_margin_default: float = 0.25


class DefaultMaterialsSet(BaseModel):
    materials: list[str] | None = None
    liquid_materials: list[str] | None = None
    agent_min_compost_pct: float | None = None
    chemical_filler_material: str | None = None
    variability_margin: float | None = None
    cluster_margin_default: float | None = Field(None, ge=0.05, le=0.5)


# ── Helpers ───────────────────────────────────────────────────────────────

def _load_markups() -> dict[str, float]:
    """Return {material_name: markup_pct} from material_markups table."""
    sb = get_supabase_admin()
    result = sb.table("material_markups").select("*").execute()
    return {r["material"]: float(r["markup_pct"]) for r in (result.data or [])}


def _apply_markups(materials: list[dict], markups: dict[str, float]) -> list[dict]:
    """Apply markup percentages to cost_per_ton for agent-visible pricing."""
    out = []
    for m in materials:
        row = dict(m)
        pct = markups.get(row["material"], 0)
        row["cost_per_ton"] = row["cost_per_ton"] * (1 + pct / 100)
        out.append(row)
    return out


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.get("/defaults", response_model=DefaultMaterialsOut)
def get_default_materials(user: CurrentUser = Depends(get_current_user)):
    """Get the admin-configured defaults: materials list + blend settings."""
    sb = get_supabase_admin()
    result = run_sb(lambda: sb.table("default_materials").select("*").execute())
    if result.data:
        row = result.data[0]
        return DefaultMaterialsOut(
            materials=row.get("materials") or [],
            liquid_materials=row.get("liquid_materials") or [],
            agent_min_compost_pct=row.get("agent_min_compost_pct", 50),
            chemical_filler_material=row.get("chemical_filler_material", "Dolomitic Lime (Filler)"),
            variability_margin=row.get("variability_margin", 15.0),
            cluster_margin_default=row.get("cluster_margin_default") or 0.25,
        )
    return DefaultMaterialsOut(materials=[
        "Urea 46%", "MAP 33%", "DAP",
        "KCL (Potassium Chloride)", "Gypsum",
        "KAN 28%", "Calcitic Lime",
    ])


@router.put("/defaults", response_model=DefaultMaterialsOut)
def set_default_materials(
    body: DefaultMaterialsSet,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only. Update default materials and/or blend settings."""
    sb = get_supabase_admin()
    update = {}
    if body.materials is not None:
        update["materials"] = body.materials
    if body.liquid_materials is not None:
        update["liquid_materials"] = body.liquid_materials
    if body.agent_min_compost_pct is not None:
        update["agent_min_compost_pct"] = body.agent_min_compost_pct
    if body.chemical_filler_material is not None:
        update["chemical_filler_material"] = body.chemical_filler_material
    if body.variability_margin is not None:
        update["variability_margin"] = body.variability_margin
    if body.cluster_margin_default is not None:
        update["cluster_margin_default"] = body.cluster_margin_default
    if update:
        update["id"] = 1
        sb.table("default_materials").upsert(update).execute()
    # Return full current state
    result = sb.table("default_materials").select("*").execute()
    row = result.data[0] if result.data else {}
    return DefaultMaterialsOut(
        materials=row.get("materials") or [],
        liquid_materials=row.get("liquid_materials") or [],
        agent_min_compost_pct=row.get("agent_min_compost_pct", 50),
        chemical_filler_material=row.get("chemical_filler_material", "Dolomitic Lime (Filler)"),
        variability_margin=row.get("variability_margin", 15.0),
        cluster_margin_default=row.get("cluster_margin_default") or 0.25,
    )


@router.get("/markups", response_model=list[MarkupOut])
def get_markups(user: CurrentUser = Depends(require_admin)):
    """Admin only. Get all material markups."""
    sb = get_supabase_admin()
    result = run_sb(lambda: sb.table("material_markups").select("*").execute())
    return [MarkupOut(**r) for r in (result.data or [])]


@router.get("/", response_model=list[MaterialOut])
def list_materials(user: CurrentUser = Depends(get_current_user)):
    """List all materials. Agents see marked-up costs; admins see raw costs."""
    sb = get_supabase_admin()
    result = run_sb(lambda: sb.table("materials").select("*").execute())
    materials = result.data or []

    if user.role != "admin":
        markups = _load_markups()
        materials = _apply_markups(materials, markups)

    return [MaterialOut(**m) for m in materials]


@router.post("/", response_model=MaterialOut, status_code=201)
def add_material(
    body: MaterialCreate,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only. Add a new material."""
    sb = get_supabase_admin()
    row = body.model_dump()
    result = sb.table("materials").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to insert material")
    return MaterialOut(**result.data[0])


@router.patch("/{material_name}", response_model=MaterialOut)
def update_material(
    material_name: str,
    body: MaterialUpdate,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only. Update fields on an existing material."""
    sb = get_supabase_admin()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = sb.table("materials").update(updates).eq("material", material_name).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Material not found")
    return MaterialOut(**result.data[0])


@router.delete("/{material_name}", status_code=204)
def delete_material(
    material_name: str,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only. Delete a material."""
    sb = get_supabase_admin()
    result = sb.table("materials").delete().eq("material", material_name).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Material not found")


@router.put("/{material_name}/markup", response_model=MarkupOut)
def set_markup(
    material_name: str,
    body: MarkupSet,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only. Set the markup percentage for a material."""
    sb = get_supabase_admin()
    mat_result = sb.table("materials").select("material").eq("material", material_name).execute()
    if not mat_result.data:
        raise HTTPException(status_code=404, detail="Material not found")

    sb.table("material_markups").upsert({
        "material": material_name,
        "markup_pct": body.markup_pct,
    }, on_conflict="material").execute()
    return MarkupOut(material=material_name, markup_pct=body.markup_pct)


@router.post("/markups/bulk", response_model=list[MarkupOut])
def set_markups_bulk(
    body: list[BulkMarkupItem],
    user: CurrentUser = Depends(require_admin),
):
    """Admin only. Set markups for multiple materials at once."""
    sb = get_supabase_admin()
    results = []
    rows = [{"material": item.material, "markup_pct": item.markup_pct} for item in body]
    if rows:
        sb.table("material_markups").upsert(rows, on_conflict="material").execute()
    for item in body:
        results.append(MarkupOut(material=item.material, markup_pct=item.markup_pct))
    return results
