"""Client, farm, and field management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
from app.supabase_client import get_supabase_admin

router = APIRouter(tags=["Clients"])


# ── Pydantic models ──────────────────────────────────────────────────────────


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    agent_id: Optional[str] = Field(None, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=254)
    phone: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = Field(None, max_length=2000)
    company_details: Optional[dict] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=254)
    phone: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = Field(None, max_length=2000)
    company_details: Optional[dict] = None


class FarmCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    region: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=2000)


class FarmUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    region: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=2000)


class FieldCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    size_ha: Optional[float] = Field(None, gt=0, le=100_000)
    gps_lat: Optional[float] = Field(None, ge=-90, le=90)
    gps_lng: Optional[float] = Field(None, ge=-180, le=180)
    soil_type: Optional[str] = Field(None, max_length=100)
    crop: Optional[str] = Field(None, max_length=200)
    cultivar: Optional[str] = Field(None, max_length=200)
    crop_type: Optional[str] = Field(None, pattern=r"^(?i)(annual|perennial)$")
    planting_date: Optional[str] = Field(None, max_length=20)
    tree_age: Optional[int] = Field(None, ge=0, le=200)
    pop_per_ha: Optional[int] = Field(None, gt=0, le=1_000_000)
    yield_target: Optional[float] = Field(None, gt=0, le=1_000_000)
    yield_unit: Optional[str] = Field(None, max_length=50)
    irrigation_type: Optional[str] = Field(None, pattern=r"^(drip|pivot|micro|flood|none)$")
    accepted_methods: Optional[list[str]] = None
    fertigation_months: Optional[list[int]] = None
    latest_analysis_id: Optional[str] = None


class FieldUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    size_ha: Optional[float] = Field(None, gt=0, le=100_000)
    gps_lat: Optional[float] = Field(None, ge=-90, le=90)
    gps_lng: Optional[float] = Field(None, ge=-180, le=180)
    soil_type: Optional[str] = Field(None, max_length=100)
    crop: Optional[str] = Field(None, max_length=200)
    cultivar: Optional[str] = Field(None, max_length=200)
    crop_type: Optional[str] = Field(None, pattern=r"^(?i)(annual|perennial)$")
    planting_date: Optional[str] = Field(None, max_length=20)
    tree_age: Optional[int] = Field(None, ge=0, le=200)
    pop_per_ha: Optional[int] = Field(None, gt=0, le=1_000_000)
    yield_target: Optional[float] = Field(None, gt=0, le=1_000_000)
    yield_unit: Optional[str] = Field(None, max_length=50)
    irrigation_type: Optional[str] = Field(None, pattern=r"^(drip|pivot|micro|flood|none)$")
    accepted_methods: Optional[list[str]] = None
    fertigation_months: Optional[list[int]] = None
    latest_analysis_id: Optional[str] = None


class CropHistoryCreate(BaseModel):
    crop: str = Field(..., min_length=1, max_length=200)
    cultivar: Optional[str] = Field(None, max_length=200)
    season: Optional[str] = Field(None, max_length=20)
    date_planted: Optional[str] = Field(None, max_length=20)
    date_harvested: Optional[str] = Field(None, max_length=20)
    estimated_yield: Optional[float] = Field(None, ge=0, le=1_000_000)
    yield_unit: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=2000)


class CropHistoryUpdate(BaseModel):
    crop: Optional[str] = Field(None, min_length=1, max_length=200)
    cultivar: Optional[str] = Field(None, max_length=200)
    season: Optional[str] = Field(None, max_length=20)
    date_planted: Optional[str] = Field(None, max_length=20)
    date_harvested: Optional[str] = Field(None, max_length=20)
    estimated_yield: Optional[float] = Field(None, ge=0, le=1_000_000)
    yield_unit: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=2000)


# ── Helper ────────────────────────────────────────────────────────────────────


def _audit(sb, user: CurrentUser, action: str, table: str, record_id: str | None = None, detail: dict | None = None):
    try:
        sb.rpc(
            "log_audit_event",
            {
                "p_event_type": action,
                "p_entity_type": table,
                "p_entity_id": record_id,
                "p_metadata": detail or {},
                "p_user_id": user.id,
            },
        ).execute()
    except Exception:
        pass


def _check_client_access(sb, client_id: str, user: CurrentUser) -> dict:
    """Fetch a client and verify the current user has access."""
    result = sb.table("clients").select("*").eq("id", client_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    client = result.data[0]
    if user.role != "admin" and client.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return client


def _check_farm_access(sb, farm_id: str, user: CurrentUser) -> dict:
    """Fetch a farm and verify access via its parent client."""
    result = sb.table("farms").select("*, clients(agent_id)").eq("id", farm_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Farm not found")
    farm = result.data[0]
    agent_id = farm.get("clients", {}).get("agent_id") if farm.get("clients") else farm.get("agent_id")
    if user.role != "admin" and agent_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return farm


def _check_field_access(sb, field_id: str, user: CurrentUser) -> dict:
    """Fetch a field and verify access via its parent farm → client."""
    result = sb.table("fields").select("*, farms(client_id, clients(agent_id))").eq("id", field_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Field not found")
    field = result.data[0]
    agent_id = None
    if field.get("farms") and field["farms"].get("clients"):
        agent_id = field["farms"]["clients"].get("agent_id")
    if user.role != "admin" and agent_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return field


# ── Client endpoints ─────────────────────────────────────────────────────────


@router.get("/")
def list_clients(
    page: PageParams = Depends(PageParams.as_query),
    search: str | None = Query(None, description="Search by name, company or contact"),
    user: CurrentUser = Depends(get_current_user),
):
    """List clients. Agents see their own; admins see all."""
    sb = get_supabase_admin()
    query = sb.table("clients").select("*", count="exact").is_("deleted_at", "null")
    if user.role != "admin":
        query = query.eq("agent_id", user.id)
    if search:
        query = query.or_(
            f"name.ilike.%{search}%,"
            f"contact_person.ilike.%{search}%,"
            f"email.ilike.%{search}%"
        )
    # Clients default to name-ordered (alphabetical) unlike everything
    # else which is time-ordered. Override order_desc default to ascending.
    if not page.order_by:
        query = query.order("name", desc=False)
    else:
        query = query.order(page.order_by, desc=page.order_desc)
    if page.skip:
        query = query.offset(page.skip)
    query = query.limit(page.limit)
    result = query.execute()
    return Page.from_result(result, page)


@router.post("/", status_code=201)
def create_client(body: ClientCreate, user: CurrentUser = Depends(get_current_user)):
    """Create a client. Agents own the client; admins can assign any agent_id."""
    sb = get_supabase_admin()
    data = body.model_dump(exclude_none=True)

    if user.role != "admin":
        data["agent_id"] = user.id
    elif "agent_id" not in data:
        data["agent_id"] = user.id

    result = sb.table("clients").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create client")

    record = result.data[0]
    _audit(sb, user, "create", "clients", record["id"], {"name": data.get("name")})
    return record


@router.patch("/{client_id}")
def update_client(client_id: str, body: ClientUpdate, user: CurrentUser = Depends(get_current_user)):
    """Update a client's details."""
    sb = get_supabase_admin()
    _check_client_access(sb, client_id, user)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = sb.table("clients").update(updates).eq("id", client_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update client")

    _audit(sb, user, "update", "clients", client_id, updates)
    return result.data[0]


@router.delete("/{client_id}", status_code=200)
def delete_client(client_id: str, user: CurrentUser = Depends(get_current_user)):
    """Soft-delete a client."""
    from datetime import datetime, timezone
    sb = get_supabase_admin()
    _check_client_access(sb, client_id, user)
    sb.table("clients").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user.id,
    }).eq("id", client_id).execute()
    _audit(sb, user, "soft_delete", "clients", client_id)
    return {"detail": "Client deleted"}


# ── Farm endpoints ────────────────────────────────────────────────────────────


@router.get("/{client_id}/farms")
def list_farms(client_id: str, user: CurrentUser = Depends(get_current_user)):
    """List farms for a client."""
    sb = get_supabase_admin()
    _check_client_access(sb, client_id, user)
    result = sb.table("farms").select("*").eq("client_id", client_id).order("name").execute()
    return result.data


@router.post("/{client_id}/farms", status_code=201)
def create_farm(client_id: str, body: FarmCreate, user: CurrentUser = Depends(get_current_user)):
    """Add a farm to a client."""
    sb = get_supabase_admin()
    _check_client_access(sb, client_id, user)

    data = body.model_dump(exclude_none=True)
    data["client_id"] = client_id

    result = sb.table("farms").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create farm")

    record = result.data[0]
    _audit(sb, user, "create", "farms", record["id"], {"client_id": client_id, "name": data.get("name")})
    return record


@router.patch("/farms/{farm_id}")
def update_farm(farm_id: str, body: FarmUpdate, user: CurrentUser = Depends(get_current_user)):
    """Update a farm."""
    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = sb.table("farms").update(updates).eq("id", farm_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update farm")

    _audit(sb, user, "update", "farms", farm_id, updates)
    return result.data[0]


@router.delete("/farms/{farm_id}", status_code=200)
def delete_farm(farm_id: str, user: CurrentUser = Depends(get_current_user)):
    """Delete a farm."""
    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)
    sb.table("farms").delete().eq("id", farm_id).execute()
    _audit(sb, user, "delete", "farms", farm_id)
    return {"detail": "Farm deleted"}


# ── Field endpoints ───────────────────────────────────────────────────────────


@router.get("/farms/{farm_id}/fields")
def list_fields(farm_id: str, user: CurrentUser = Depends(get_current_user)):
    """List fields for a farm."""
    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)
    result = sb.table("fields").select("*").eq("farm_id", farm_id).order("name").execute()
    return result.data


@router.post("/farms/{farm_id}/fields", status_code=201)
def create_field(farm_id: str, body: FieldCreate, user: CurrentUser = Depends(get_current_user)):
    """Add a field to a farm."""
    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)

    # Check for duplicate field name on this farm
    existing = sb.table("fields").select("id").eq("farm_id", farm_id).eq("name", body.name).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail=f"A field named '{body.name}' already exists on this farm")

    data = body.model_dump(exclude_none=True)
    data["farm_id"] = farm_id

    result = sb.table("fields").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create field")

    record = result.data[0]
    _audit(sb, user, "create", "fields", record["id"], {"farm_id": farm_id, "name": data.get("name")})
    return record


@router.get("/fields/{field_id}")
def get_field(field_id: str, user: CurrentUser = Depends(get_current_user)):
    """Get a single field by ID."""
    sb = get_supabase_admin()
    field = _check_field_access(sb, field_id, user)
    # Strip nested join data
    field.pop("farms", None)
    return field


@router.patch("/fields/{field_id}")
def update_field(field_id: str, body: FieldUpdate, user: CurrentUser = Depends(get_current_user)):
    """Update a field."""
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = sb.table("fields").update(updates).eq("id", field_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update field")

    _audit(sb, user, "update", "fields", field_id, updates)
    return result.data[0]


@router.delete("/fields/{field_id}", status_code=200)
def delete_field(field_id: str, user: CurrentUser = Depends(get_current_user)):
    """Delete a field."""
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    sb.table("fields").delete().eq("id", field_id).execute()
    _audit(sb, user, "delete", "fields", field_id)
    return {"detail": "Field deleted"}


# ── Crop History ──────────────────────────────────────────────────────────────


@router.get("/fields/{field_id}/crop-history")
def list_crop_history(field_id: str, user: CurrentUser = Depends(get_current_user)):
    """List crop history for a field."""
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    result = (
        sb.table("field_crop_history")
        .select("*")
        .eq("field_id", field_id)
        .order("date_planted", desc=True)
        .execute()
    )
    return result.data or []


@router.post("/fields/{field_id}/crop-history", status_code=201)
def create_crop_history(
    field_id: str,
    body: CropHistoryCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """Add a crop history entry to a field."""
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    data = body.model_dump(exclude_none=True)
    data["field_id"] = field_id
    result = sb.table("field_crop_history").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create crop history entry")
    _audit(sb, user, "create", "field_crop_history", result.data[0]["id"])
    return result.data[0]


@router.patch("/crop-history/{entry_id}")
def update_crop_history(
    entry_id: str,
    body: CropHistoryUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """Update a crop history entry."""
    sb = get_supabase_admin()
    # Look up the entry to get field_id for access check
    entry = sb.table("field_crop_history").select("field_id").eq("id", entry_id).execute()
    if not entry.data:
        raise HTTPException(status_code=404, detail="Crop history entry not found")
    _check_field_access(sb, entry.data[0]["field_id"], user)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = sb.table("field_crop_history").update(updates).eq("id", entry_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update")
    _audit(sb, user, "update", "field_crop_history", entry_id, updates)
    return result.data[0]


@router.delete("/crop-history/{entry_id}", status_code=200)
def delete_crop_history(
    entry_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Delete a crop history entry."""
    sb = get_supabase_admin()
    entry = sb.table("field_crop_history").select("field_id").eq("id", entry_id).execute()
    if not entry.data:
        raise HTTPException(status_code=404, detail="Crop history entry not found")
    _check_field_access(sb, entry.data[0]["field_id"], user)
    sb.table("field_crop_history").delete().eq("id", entry_id).execute()
    _audit(sb, user, "delete", "field_crop_history", entry_id)
    return {"detail": "Crop history entry deleted"}
