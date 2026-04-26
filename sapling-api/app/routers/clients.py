"""Client, farm, and field management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
from app.supabase_client import get_supabase_admin, run_sb

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
    fertigation_capable: Optional[bool] = None
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
    fertigation_capable: Optional[bool] = None
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
    result = run_sb(lambda: sb.table("clients").select("*").eq(
        "id", client_id
    ).execute())
    if not result.data:
        raise HTTPException(status_code=404, detail="Client not found")
    client = result.data[0]
    if user.role != "admin" and client.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return client


def _check_farm_access(sb, farm_id: str, user: CurrentUser) -> dict:
    """Fetch a farm and verify access via its parent client."""
    result = run_sb(lambda: sb.table("farms").select(
        "*, clients(agent_id)"
    ).eq("id", farm_id).execute())
    if not result.data:
        raise HTTPException(status_code=404, detail="Farm not found")
    farm = result.data[0]
    agent_id = farm.get("clients", {}).get("agent_id") if farm.get("clients") else farm.get("agent_id")
    if user.role != "admin" and agent_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return farm


def _check_field_access(sb, field_id: str, user: CurrentUser) -> dict:
    """Fetch a field and verify access via its parent farm → client."""
    result = run_sb(lambda: sb.table("fields").select(
        "*, farms(client_id, clients(agent_id))"
    ).eq("id", field_id).execute())
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
    result = run_sb(lambda: query.execute())

    # Enrich each client with farm_count + field_count in two batch
    # queries so the frontend doesn't have to fire N + N*M follow-ups
    # (which was flooding the Supabase HTTP/2 pool and producing CORS-
    # looking 500s on the /clients page).
    client_ids = [c["id"] for c in (result.data or [])]
    farm_counts: dict[str, int] = {}
    field_counts: dict[str, int] = {}
    farm_to_client: dict[str, str] = {}
    if client_ids:
        farm_rows = run_sb(lambda: sb.table("farms").select(
            "id,client_id"
        ).in_("client_id", client_ids).execute()).data or []
        for fr in farm_rows:
            cid = fr["client_id"]
            farm_counts[cid] = farm_counts.get(cid, 0) + 1
            farm_to_client[fr["id"]] = cid
        if farm_to_client:
            field_rows = run_sb(lambda: sb.table("fields").select(
                "farm_id"
            ).in_("farm_id", list(farm_to_client.keys())).execute()).data or []
            for fd in field_rows:
                cid = farm_to_client.get(fd["farm_id"])
                if cid:
                    field_counts[cid] = field_counts.get(cid, 0) + 1

    for c in (result.data or []):
        c["farm_count"] = farm_counts.get(c["id"], 0)
        c["field_count"] = field_counts.get(c["id"], 0)

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
    result = run_sb(lambda: sb.table("farms").select("*").eq(
        "client_id", client_id
    ).order("name").execute())
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
    """List fields for a farm.

    Each field is enriched with `latest_analysis_composite` — a tiny
    summary of how the linked soil analysis was composed. Callers (e.g.
    the field card) use this to render a "N samples" badge without
    having to fire a second round-trip per field.
    """
    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)
    result = run_sb(lambda: sb.table("fields").select("*").eq(
        "farm_id", farm_id
    ).order("name").execute())
    fields_data = result.data or []

    analysis_ids = [f["latest_analysis_id"] for f in fields_data if f.get("latest_analysis_id")]
    composites: dict[str, dict] = {}
    if analysis_ids:
        analyses = run_sb(lambda: sb.table("soil_analyses").select(
            "id, composition_method, replicate_count"
        ).in_("id", analysis_ids).execute())
        for a in (analyses.data or []):
            composites[a["id"]] = {
                "composition_method": a.get("composition_method") or "single",
                "replicate_count": a.get("replicate_count") or 1,
            }

    for f in fields_data:
        aid = f.get("latest_analysis_id")
        f["latest_analysis_composite"] = composites.get(aid) if aid else None

    return fields_data


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


# ── Bulk import: fields + yields ─────────────────────────────────────────────


class BulkFieldRow(BaseModel):
    """One row in a fields-bulk-import payload. Same shape as FieldCreate
    plus a stable `key` the importer uses to match rows on retry."""
    key: str = Field(..., max_length=200)  # block name or external id
    name: str = Field(..., min_length=1, max_length=200)
    size_ha: Optional[float] = Field(None, gt=0, le=100_000)
    crop: Optional[str] = Field(None, max_length=200)
    cultivar: Optional[str] = Field(None, max_length=200)
    crop_type: Optional[str] = Field(None, pattern=r"^(?i)(annual|perennial)$")
    planting_date: Optional[str] = Field(None, max_length=20)
    tree_age: Optional[int] = Field(None, ge=0, le=200)
    pop_per_ha: Optional[int] = Field(None, gt=0, le=1_000_000)
    yield_target: Optional[float] = Field(None, gt=0, le=1_000_000)
    yield_unit: Optional[str] = Field(None, max_length=50)
    irrigation_type: Optional[str] = Field(None, pattern=r"^(drip|pivot|micro|flood|none)$")
    fertigation_capable: Optional[bool] = None
    soil_type: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class BulkFieldsRequest(BaseModel):
    farm_id: str
    rows: list[BulkFieldRow] = Field(..., min_length=1, max_length=500)
    # 'skip' = leave existing fields with the same name on the farm
    # 'update' = patch existing matches in-place
    on_conflict: str = Field("skip", pattern=r"^(skip|update)$")


class BulkFieldsResult(BaseModel):
    created: int
    updated: int
    skipped: int
    fields: list[dict]


@router.post("/farms/{farm_id}/fields/bulk", response_model=BulkFieldsResult, status_code=201)
def bulk_create_fields(
    farm_id: str,
    body: BulkFieldsRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Bulk-create fields under a farm from a parsed CSV/spreadsheet.

    Matches existing fields by (farm_id, name). on_conflict controls
    duplicate handling: 'skip' (default) leaves them alone, 'update'
    patches them with the new row's non-null values.
    """
    if body.farm_id != farm_id:
        raise HTTPException(400, "farm_id mismatch between path and body")

    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)

    # Pre-fetch existing fields on this farm so we can match by name
    existing = (
        sb.table("fields").select("*").eq("farm_id", farm_id).execute().data or []
    )
    existing_by_name = {f["name"].strip().lower(): f for f in existing}

    created: list[dict] = []
    updated: list[dict] = []
    skipped: list[dict] = []

    for row in body.rows:
        norm_name = row.name.strip().lower()
        match = existing_by_name.get(norm_name)
        # Build payload from non-null values only
        payload = row.model_dump(exclude_none=True, exclude={"key"})
        if "crop_type" in payload and payload["crop_type"]:
            payload["crop_type"] = payload["crop_type"].lower()

        if match:
            if body.on_conflict == "update":
                update_payload = {k: v for k, v in payload.items() if k != "name"}
                if update_payload:
                    res = sb.table("fields").update(update_payload).eq("id", match["id"]).execute()
                    if res.data:
                        updated.append(res.data[0])
                        _audit(sb, user, "bulk_update", "fields", match["id"], {"row_key": row.key})
                        continue
            skipped.append(match)
            continue

        payload["farm_id"] = farm_id
        res = sb.table("fields").insert(payload).execute()
        if res.data:
            created.append(res.data[0])
            _audit(sb, user, "bulk_create", "fields", res.data[0]["id"], {"row_key": row.key})

    return BulkFieldsResult(
        created=len(created),
        updated=len(updated),
        skipped=len(skipped),
        fields=created + updated + skipped,
    )


# ── Bulk yield records ──────────────────────────────────────────────────────


class BulkYieldRow(BaseModel):
    """One yield record in a bulk import. Field is matched by name within
    the farm; if it doesn't exist the row is reported as unmatched (no
    auto-create — yields without a backing field aren't useful).
    """
    field_name: str = Field(..., min_length=1, max_length=200)
    season: str = Field(..., min_length=1, max_length=50)  # e.g. "2024/25"
    yield_actual: float = Field(..., gt=0, le=1_000_000)
    yield_unit: str = Field(..., min_length=1, max_length=50)  # "t/ha", "t NIS/ha", etc.
    harvest_date: Optional[str] = None
    source: str = Field("imported", max_length=50)
    notes: Optional[str] = None


class BulkYieldsRequest(BaseModel):
    farm_id: str
    rows: list[BulkYieldRow] = Field(..., min_length=1, max_length=2000)
    # 'skip' = leave existing (field_id, season) yields alone
    # 'update' = overwrite the actual value
    on_conflict: str = Field("skip", pattern=r"^(skip|update)$")


class BulkYieldsResult(BaseModel):
    created: int
    updated: int
    skipped: int
    unmatched: list[str]  # field_names with no matching field on the farm


@router.post("/farms/{farm_id}/yields/bulk", response_model=BulkYieldsResult, status_code=201)
def bulk_create_yields(
    farm_id: str,
    body: BulkYieldsRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Bulk-create yield_records under a farm. Matches each row's
    field_name against existing fields on the farm; unmatched rows are
    reported back in `unmatched`.

    Conflict on (field_id, season) is the table's unique constraint;
    on_conflict='update' overwrites yield_actual + harvest_date + notes,
    'skip' leaves the existing row.
    """
    if body.farm_id != farm_id:
        raise HTTPException(400, "farm_id mismatch between path and body")

    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)

    fields = (
        sb.table("fields").select("id, name").eq("farm_id", farm_id).execute().data or []
    )
    by_name = {f["name"].strip().lower(): f["id"] for f in fields}

    field_ids = [v for v in by_name.values()]
    existing_yields_rows = []
    if field_ids:
        existing_yields_rows = (
            sb.table("yield_records")
            .select("id, field_id, season")
            .in_("field_id", field_ids)
            .execute()
            .data
            or []
        )
    existing_by_pair = {(y["field_id"], y["season"]): y for y in existing_yields_rows}

    created = 0
    updated = 0
    skipped = 0
    unmatched: list[str] = []

    for row in body.rows:
        field_id = by_name.get(row.field_name.strip().lower())
        if not field_id:
            unmatched.append(row.field_name)
            continue
        existing = existing_by_pair.get((field_id, row.season))
        payload = {
            "field_id": field_id,
            "season": row.season,
            "yield_actual": row.yield_actual,
            "yield_unit": row.yield_unit,
            "harvest_date": row.harvest_date,
            "source": row.source,
            "notes": row.notes,
            "created_by": user.id,
        }
        if existing:
            if body.on_conflict == "update":
                sb.table("yield_records").update({
                    k: v for k, v in payload.items()
                    if k not in ("field_id", "season", "created_by")
                }).eq("id", existing["id"]).execute()
                updated += 1
                _audit(sb, user, "bulk_update", "yield_records", existing["id"])
            else:
                skipped += 1
            continue
        res = sb.table("yield_records").insert(payload).execute()
        if res.data:
            created += 1
            _audit(sb, user, "bulk_create", "yield_records", res.data[0]["id"])

    return BulkYieldsResult(
        created=created, updated=updated, skipped=skipped, unmatched=unmatched,
    )


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
