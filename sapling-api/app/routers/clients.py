"""Client, farm, and field management endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
from app.services.crop_canonicaliser import (
    CanonicaliseResult,
    canonicalise_crop,
)
from app.supabase_client import get_supabase_admin, run_sb

router = APIRouter(tags=["Clients"])


def _load_canonical_crop_names(sb) -> list[str]:
    """One catalog read per request — caller passes the result through
    every canonicalise_crop() call to avoid repeating the query."""
    rows = run_sb(
        lambda: sb.table("crop_requirements").select("crop").execute()
    ).data or []
    return sorted({r["crop"] for r in rows if r.get("crop")})


def _resolve_crop_or_raise(
    sb,
    *,
    raw: Optional[str],
    default_variant: Optional[str] = None,
    field_path: str = "crop",
) -> Optional[str]:
    """Single-field write helper. Returns the canonical name (or the
    original input when nothing was supplied), and raises HTTP 400 on
    ambiguity / no-match — single-field writes shouldn't silently store
    a name the engine can't match downstream."""
    if not raw:
        return raw
    catalog = _load_canonical_crop_names(sb)
    result = canonicalise_crop(
        raw, catalog_crops=catalog, default_variant=default_variant,
    )
    if result.canonical:
        return result.canonical
    if result.matched_via == "ambiguous":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ambiguous_crop",
                "message": result.warning,
                "field": field_path,
                "candidates": list(result.candidates),
            },
        )
    raise HTTPException(
        status_code=400,
        detail={
            "error": "unknown_crop",
            "message": result.warning,
            "field": field_path,
        },
    )


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
        # Filter out soft-deleted farms/fields so the card-view count
        # tracks the detail-view count. Without the deleted_at filter
        # a deleted-but-not-yet-purged farm shows up in the aggregate
        # and the agronomist sees "2 farms" while the detail page only
        # lists one — which is exactly what just happened with the
        # MFB Trust Laborie test.
        farm_rows = run_sb(lambda: sb.table("farms").select(
            "id,client_id"
        ).in_("client_id", client_ids).is_("deleted_at", "null").execute()).data or []
        for fr in farm_rows:
            cid = fr["client_id"]
            farm_counts[cid] = farm_counts.get(cid, 0) + 1
            farm_to_client[fr["id"]] = cid
        if farm_to_client:
            field_rows = run_sb(lambda: sb.table("fields").select(
                "farm_id"
            ).in_("farm_id", list(farm_to_client.keys())).is_("deleted_at", "null").execute()).data or []
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
    from postgrest.exceptions import APIError as PostgrestAPIError

    sb = get_supabase_admin()
    data = body.model_dump(exclude_none=True)

    if user.role != "admin":
        data["agent_id"] = user.id
    elif "agent_id" not in data:
        data["agent_id"] = user.id

    try:
        result = sb.table("clients").insert(data).execute()
    except PostgrestAPIError as e:
        # 23505 = Postgres unique-constraint violation. The (agent_id, name)
        # pair has a uniqueness rule so two clients on the same account
        # can't share a name. Translate to a clean 409 instead of leaking
        # a generic 500 — the agronomist sees the actual reason.
        if getattr(e, "code", None) == "23505":
            raise HTTPException(
                status_code=409,
                detail=f"A client named '{data.get('name')}' already exists on your account.",
            )
        raise
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


# Tables with field_id + deleted_at — soft-delete cascades to all of
# them when a parent field/farm/client is deleted. Order doesn't
# matter for soft-delete (no FK enforcement), but we keep the list
# alphabetical for diff readability.
_FIELD_CHILD_TABLES = (
    "blends",
    "field_applications",
    "field_crop_history",
    "field_events",
    "leaf_analyses",
    "soil_analyses",
    "yield_records",
)


def _cascade_soft_delete_fields(sb, *, field_ids: list[str], user_id: str) -> None:
    """Stamp deleted_at on all child rows of the given field_ids across
    every dependent table. Only updates rows that aren't already
    soft-deleted to keep audit semantics clean (we don't re-stamp an
    older deletion)."""
    if not field_ids:
        return
    from datetime import datetime, timezone
    payload = {
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user_id,
    }
    for tbl in _FIELD_CHILD_TABLES:
        sb.table(tbl).update(payload).in_(
            "field_id", field_ids,
        ).is_("deleted_at", "null").execute()


def _cascade_soft_delete_farm(sb, *, farm_id: str, user_id: str) -> None:
    """Soft-delete every active field under the farm + all of their
    children. Caller has already (or will) soft-delete the farm row
    itself."""
    from datetime import datetime, timezone
    fields_resp = sb.table("fields").select("id").eq(
        "farm_id", farm_id,
    ).is_("deleted_at", "null").execute()
    field_ids = [r["id"] for r in (fields_resp.data or []) if r.get("id")]
    if field_ids:
        sb.table("fields").update({
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": user_id,
        }).in_("id", field_ids).execute()
        _cascade_soft_delete_fields(sb, field_ids=field_ids, user_id=user_id)


@router.delete("/{client_id}", status_code=200)
def delete_client(client_id: str, user: CurrentUser = Depends(get_current_user)):
    """Soft-delete a client and cascade to every farm + field + analysis
    record under it. Re-using the same client name later won't conflict
    because the unique index on (agent_id, name) is partial — see
    migration 091_partial_unique_for_soft_delete."""
    from datetime import datetime, timezone
    sb = get_supabase_admin()
    _check_client_access(sb, client_id, user)

    # Cascade through farms → fields → field-children. We keep the
    # client deletion as the LAST step so any failure mid-cascade
    # leaves the client visible (callers can retry).
    farms_resp = sb.table("farms").select("id").eq(
        "client_id", client_id,
    ).is_("deleted_at", "null").execute()
    for farm in (farms_resp.data or []):
        _cascade_soft_delete_farm(sb, farm_id=farm["id"], user_id=user.id)

    deletion_stamp = {
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user.id,
    }
    if farms_resp.data:
        sb.table("farms").update(deletion_stamp).eq(
            "client_id", client_id,
        ).is_("deleted_at", "null").execute()

    sb.table("clients").update(deletion_stamp).eq("id", client_id).execute()
    _audit(sb, user, "soft_delete", "clients", client_id)
    return {"detail": "Client deleted"}


# ── Farm endpoints ────────────────────────────────────────────────────────────


@router.get("/{client_id}/farms")
def list_farms(client_id: str, user: CurrentUser = Depends(get_current_user)):
    """List farms for a client. Hides soft-deleted unless caller is admin
    and explicitly opts in via include_deleted=true (admin restore UI)."""
    sb = get_supabase_admin()
    _check_client_access(sb, client_id, user)
    q = sb.table("farms").select("*").eq("client_id", client_id).is_("deleted_at", "null")
    result = run_sb(lambda: q.order("name").execute())
    return result.data


@router.post("/{client_id}/farms", status_code=201)
def create_farm(client_id: str, body: FarmCreate, user: CurrentUser = Depends(get_current_user)):
    """Add a farm to a client."""
    from postgrest.exceptions import APIError as PostgrestAPIError

    sb = get_supabase_admin()
    _check_client_access(sb, client_id, user)

    data = body.model_dump(exclude_none=True)
    data["client_id"] = client_id

    try:
        result = sb.table("farms").insert(data).execute()
    except PostgrestAPIError as e:
        # 23505 = unique violation on (client_id, name). Migration 091
        # made this index partial on deleted_at IS NULL, so this only
        # fires when a *currently active* farm has the same name.
        if getattr(e, "code", None) == "23505":
            raise HTTPException(
                status_code=409,
                detail=f"A farm named '{data.get('name')}' already exists on this client.",
            )
        raise
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
    """Soft-delete a farm and cascade to every field + analysis under
    it. The unique index on (client_id, name) is partial-indexed on
    deleted_at IS NULL (migration 091), so re-creating a farm with the
    same name after deletion succeeds cleanly. Admins can hard-delete
    via the admin endpoint if they need the row gone permanently."""
    from datetime import datetime, timezone
    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)
    _cascade_soft_delete_farm(sb, farm_id=farm_id, user_id=user.id)
    sb.table("farms").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user.id,
    }).eq("id", farm_id).execute()
    _audit(sb, user, "soft_delete", "farms", farm_id)
    return {"detail": "Farm deleted"}


# ── Field endpoints ───────────────────────────────────────────────────────────


_CORE_SOIL_KEYS = ("K", "Ca", "Mg", "P (Bray-1)", "P (Citric acid)")


def _compute_field_health(field: dict, analysis: dict | None) -> dict:
    """Per-field data-completeness summary.

    The engine has implicit input contracts that fail silently when a
    soft-required field is missing — this surface puts those failures
    on the field card so the agronomist can fix at the source rather
    than discovering them after a programme build.

    Tier breakdown:
      * critical — missing data the engine *needs* (size, crop, soil link).
        Programme can't build correctly until resolved.
      * warning  — missing data that triggers an Assumption fallback
        (tree_age on a perennial, yield_target, irrigation_type, etc.).
        Programme builds but on weakened reasoning.
      * info     — optional data that improves quality (full micros,
        cultivar, GPS).
    """
    from app.services.soil_engine import normalise_soil_values

    critical: list[str] = []
    warnings: list[str] = []

    # ── Engine-critical inputs ────────────────────────────────────
    if not field.get("size_ha"):
        critical.append("size")
    if not field.get("crop"):
        critical.append("crop")
    if not field.get("latest_analysis_id"):
        critical.append("soil_analysis")

    # ── Engine-soft inputs (programme builds, but with assumptions) ──
    crop_type = (field.get("crop_type") or "").lower()
    if crop_type == "perennial" and field.get("tree_age") in (None, ""):
        warnings.append("tree_age")
    if crop_type == "annual" and not field.get("planting_date"):
        warnings.append("planting_date")
    if not field.get("yield_target"):
        warnings.append("yield_target")
    if not field.get("irrigation_type"):
        warnings.append("irrigation_type")
    if not (field.get("accepted_methods") or []):
        warnings.append("accepted_methods")
    if crop_type == "perennial" and not field.get("pop_per_ha"):
        warnings.append("pop_per_ha")

    # Soil-content quality: even with a linked analysis, an empty or
    # macros-only soil_values dict means the engine reasons on far less
    # than it could. We only inspect this when an analysis IS linked —
    # absence of the link is already a critical above.
    if analysis:
        soil_values = normalise_soil_values(analysis.get("soil_values") or {})
        if "pH (KCl)" not in soil_values and "pH (H2O)" not in soil_values:
            warnings.append("soil_pH_missing")
        if "CEC" not in soil_values:
            warnings.append("soil_CEC_missing")
        # At least one of the core macro keys must be present for the
        # engine to do soil-state target adjustment on N/P/K.
        if not any(k in soil_values for k in _CORE_SOIL_KEYS):
            critical.append("soil_macros_missing")

    if critical:
        level = "critical"
    elif warnings:
        level = "warn"
    else:
        level = "ok"
    return {"level": level, "critical": critical, "warnings": warnings}


@router.get("/farms/{farm_id}/fields")
def list_fields(farm_id: str, user: CurrentUser = Depends(get_current_user)):
    """List fields for a farm.

    Each field is enriched with:
      * `latest_analysis_composite` — composition summary of the linked
        soil analysis (single / composite, replicate count) so the
        field card can render a "N samples" badge without a second
        round-trip per field.
      * `latest_analysis_date` — the actual sample date of the linked
        soil analysis, for the per-block data-inventory display.
      * `health` — `{level, critical[], warnings[]}` breakdown of
        which engine-relevant inputs are missing or weak. Drives the
        field-card health pill.
    """
    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)
    result = run_sb(lambda: sb.table("fields").select("*").eq(
        "farm_id", farm_id,
    ).is_("deleted_at", "null").order("name").execute())
    fields_data = result.data or []

    analysis_ids = [f["latest_analysis_id"] for f in fields_data if f.get("latest_analysis_id")]
    analyses_by_id: dict[str, dict] = {}
    composites: dict[str, dict] = {}
    if analysis_ids:
        analyses = run_sb(lambda: sb.table("soil_analyses").select(
            "id, composition_method, replicate_count, soil_values, analysis_date, lab_name"
        ).in_("id", analysis_ids).execute())
        for a in (analyses.data or []):
            analyses_by_id[a["id"]] = a
            composites[a["id"]] = {
                "composition_method": a.get("composition_method") or "single",
                "replicate_count": a.get("replicate_count") or 1,
            }

    for f in fields_data:
        aid = f.get("latest_analysis_id")
        analysis = analyses_by_id.get(aid) if aid else None
        f["latest_analysis_composite"] = composites.get(aid) if aid else None
        f["latest_analysis_date"] = (analysis or {}).get("analysis_date")
        f["latest_analysis_lab"] = (analysis or {}).get("lab_name")
        f["health"] = _compute_field_health(f, analysis)

    return fields_data


@router.post("/farms/{farm_id}/fields", status_code=201)
def create_field(farm_id: str, body: FieldCreate, user: CurrentUser = Depends(get_current_user)):
    """Add a field to a farm."""
    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)

    # Check for duplicate field name on this farm. Only ACTIVE fields
    # block the name — soft-deleted ones are free for reuse since the
    # partial unique index is filtered on deleted_at IS NULL (migration
    # 091).
    existing = sb.table("fields").select("id").eq(
        "farm_id", farm_id,
    ).eq("name", body.name).is_("deleted_at", "null").execute()
    if existing.data:
        raise HTTPException(status_code=409, detail=f"A field named '{body.name}' already exists on this farm")

    data = body.model_dump(exclude_none=True)
    if data.get("crop"):
        # Source of truth is crop_requirements.crop. Reject ambiguous /
        # unknown crops at the boundary so downstream catalog joins
        # don't silently return zero rows ("no methods for this crop").
        data["crop"] = _resolve_crop_or_raise(sb, raw=data["crop"])
    data["farm_id"] = farm_id

    result = sb.table("fields").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create field")

    record = result.data[0]
    _audit(sb, user, "create", "fields", record["id"], {"farm_id": farm_id, "name": data.get("name")})
    return record


@router.get("/fields/{field_id}")
def get_field(field_id: str, user: CurrentUser = Depends(get_current_user)):
    """Get a single field by ID, enriched with `health` (data
    completeness summary) + `latest_analysis_date` so the field
    detail page can show the same inventory tile + health pill the
    list view shows. Mirrors the per-row enrichment in
    `list_fields`."""
    sb = get_supabase_admin()
    field = _check_field_access(sb, field_id, user)
    # Strip nested join data — frontend doesn't need the embedded farm
    farm_data = field.pop("farms", None)

    analysis: dict | None = None
    aid = field.get("latest_analysis_id")
    if aid:
        a_resp = run_sb(lambda: sb.table("soil_analyses").select(
            "id, composition_method, replicate_count, soil_values, analysis_date, lab_name"
        ).eq("id", aid).limit(1).execute())
        if a_resp.data:
            analysis = a_resp.data[0]
            field["latest_analysis_composite"] = {
                "composition_method": analysis.get("composition_method") or "single",
                "replicate_count": analysis.get("replicate_count") or 1,
            }
            field["latest_analysis_date"] = analysis.get("analysis_date")
            field["latest_analysis_lab"] = analysis.get("lab_name")
    field["health"] = _compute_field_health(field, analysis)

    # Restore the nested farm join so callers that depend on it (the
    # block detail page header reads farms.name + farms.region) keep
    # working — we only stripped it temporarily so it didn't bleed
    # into the health calc.
    if farm_data is not None:
        field["farms"] = farm_data
    return field


@router.patch("/fields/{field_id}")
def update_field(field_id: str, body: FieldUpdate, user: CurrentUser = Depends(get_current_user)):
    """Update a field."""
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "crop" in updates and updates["crop"]:
        updates["crop"] = _resolve_crop_or_raise(sb, raw=updates["crop"])

    result = sb.table("fields").update(updates).eq("id", field_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update field")

    _audit(sb, user, "update", "fields", field_id, updates)
    return result.data[0]


# ── Yield records (per field) ────────────────────────────────────────────────


class YieldRecordIn(BaseModel):
    season: str = Field(..., min_length=1, max_length=50)
    yield_actual: float = Field(..., gt=0, le=1_000_000)
    yield_unit: str = Field(..., min_length=1, max_length=50)
    harvest_date: Optional[str] = None
    source: str = Field("self_reported", max_length=50)
    notes: Optional[str] = None


@router.get("/fields/{field_id}/yields")
def list_yield_records(field_id: str, user: CurrentUser = Depends(get_current_user)):
    """Yield records for a field, ordered most-recent first."""
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    result = (
        sb.table("yield_records")
        .select("*")
        .eq("field_id", field_id)
        .is_("deleted_at", "null")
        .order("harvest_date", desc=True, nullsfirst=False)
        .order("season", desc=True)
        .execute()
    )
    return result.data or []


@router.post("/fields/{field_id}/yields", status_code=201)
def create_yield_record(
    field_id: str,
    body: YieldRecordIn,
    user: CurrentUser = Depends(get_current_user),
):
    """Add a single yield record. (field_id, season) is unique."""
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    payload = body.model_dump(exclude_none=True)
    payload["field_id"] = field_id
    payload["created_by"] = user.id
    try:
        result = sb.table("yield_records").insert(payload).execute()
    except Exception as e:
        raise HTTPException(409, f"Yield for {body.season} already exists on this field") from e
    if not result.data:
        raise HTTPException(500, "Failed to create yield record")
    _audit(sb, user, "create", "yield_records", result.data[0]["id"])
    return result.data[0]


@router.delete("/yields/{yield_id}", status_code=200)
def delete_yield_record(yield_id: str, user: CurrentUser = Depends(get_current_user)):
    """Soft-delete a yield record. Admins can hard-delete via admin endpoint."""
    from datetime import datetime, timezone
    sb = get_supabase_admin()
    row = sb.table("yield_records").select("field_id").eq("id", yield_id).execute()
    if not row.data:
        raise HTTPException(404, "Yield record not found")
    _check_field_access(sb, row.data[0]["field_id"], user)
    sb.table("yield_records").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user.id,
    }).eq("id", yield_id).execute()
    _audit(sb, user, "soft_delete", "yield_records", yield_id)
    return {"detail": "Yield record deleted"}


@router.get("/fields/{field_id}/benchmarks")
def get_yield_benchmarks_for_field(field_id: str, user: CurrentUser = Depends(get_current_user)):
    """Look up yield benchmark band for this field's crop + cultivar +
    irrigation regime. Returns the most-specific match (cultivar+regime),
    falling back to generic-cultivar matches in priority order. Empty
    list if the crop has no benchmarks seeded."""
    sb = get_supabase_admin()
    field = _check_field_access(sb, field_id, user)
    crop = field.get("crop")
    cultivar = field.get("cultivar")
    if not crop:
        return []
    # Derive irrigation regime: rainfed | irrigated | fertigated.
    irrigation_type = field.get("irrigation_type")
    fertigation = field.get("fertigation_capable") is True
    regime = (
        "rainfed" if not irrigation_type or irrigation_type == "none"
        else "fertigated" if fertigation
        else "irrigated"
    )
    # Try cultivar-specific match first, then generic
    rows = (
        sb.table("crop_yield_benchmarks")
        .select("*")
        .eq("crop", crop)
        .eq("irrigation_regime", regime)
        .execute()
        .data
        or []
    )
    if cultivar:
        cultivar_match = [r for r in rows if r.get("cultivar") == cultivar]
        if cultivar_match:
            return cultivar_match
    generic = [r for r in rows if r.get("cultivar") is None]
    return generic if generic else rows


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
    # 0 / blank = "use crop_requirements.default_yield". Common for young
    # / non-bearing perennials and new plantings.
    yield_target: Optional[float] = Field(None, ge=0, le=1_000_000)
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
    # Per-row warnings — populated when the canonicaliser auto-resolves
    # a free-text crop name (e.g. 'macadamia' → 'Macadamia',
    # 'navel' → 'Citrus (Navel)') or flags an ambiguous parent that the
    # row was skipped on.
    crop_warnings: list[dict] = Field(default_factory=list)


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
    crop_warnings: list[dict] = []

    # Load the canonical crop list once for the whole batch.
    catalog_crops = _load_canonical_crop_names(sb)

    for row in body.rows:
        norm_name = row.name.strip().lower()
        match = existing_by_name.get(norm_name)
        # Build payload from non-null values only
        payload = row.model_dump(exclude_none=True, exclude={"key"})
        if "crop_type" in payload and payload["crop_type"]:
            payload["crop_type"] = payload["crop_type"].lower()

        # Canonicalise crop. We collect warnings rather than 400-ing the
        # whole batch — agronomists are mid-import + want to see which
        # rows need attention. Ambiguous parents (e.g. "citrus" without
        # a variant) skip the row and surface in `crop_warnings`.
        if payload.get("crop"):
            cres: CanonicaliseResult = canonicalise_crop(
                payload["crop"], catalog_crops=catalog_crops,
            )
            if cres.canonical:
                if cres.canonical != payload["crop"] and cres.matched_via != "exact":
                    crop_warnings.append({
                        "row_key": row.key,
                        "block_name": row.name,
                        "raw_crop": payload["crop"],
                        "resolved_to": cres.canonical,
                        "matched_via": cres.matched_via,
                    })
                payload["crop"] = cres.canonical
            else:
                crop_warnings.append({
                    "row_key": row.key,
                    "block_name": row.name,
                    "raw_crop": payload["crop"],
                    "resolved_to": None,
                    "matched_via": cres.matched_via,
                    "candidates": list(cres.candidates),
                    "warning": cres.warning,
                })
                # Skip rows we couldn't resolve — better than storing a
                # name that the engine will silently fail on later.
                skipped.append({
                    "name": row.name,
                    "skipped_reason": "unresolved_crop",
                    "raw_crop": payload["crop"],
                })
                continue

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
        crop_warnings=crop_warnings,
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


# ── Bulk-import xlsx templates ──────────────────────────────────────────────

_XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


@router.get("/templates/fields")
def download_fields_template(user: CurrentUser = Depends(get_current_user)):
    """Empty fields-master xlsx with one example row, dropdowns for
    crop_type / irrigation / fertigation, and an Instructions sheet.
    User opens in Excel, fills rows, saves as CSV, uploads via the
    bulk import page."""
    from fastapi.responses import Response

    from app.services.import_templates import build_fields_template_xlsx

    payload = build_fields_template_xlsx()
    return Response(
        content=payload,
        media_type=_XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": (
                'attachment; filename="sapling-fields-template.xlsx"'
            ),
        },
    )


@router.get("/farms/{farm_id}/templates/yields")
def download_yields_template(
    farm_id: str, user: CurrentUser = Depends(get_current_user),
):
    """Yields-records xlsx pre-populated with one row per existing
    field on the farm. The user fills in season + yield + unit per
    row and saves as CSV before uploading."""
    from fastapi.responses import Response

    from app.services.import_templates import build_yields_template_xlsx

    sb = get_supabase_admin()
    _check_farm_access(sb, farm_id, user)
    fields_resp = run_sb(
        lambda: sb.table("fields").select("name").eq(
            "farm_id", farm_id,
        ).is_("deleted_at", "null").order("name").execute()
    )
    field_names = [f["name"] for f in (fields_resp.data or []) if f.get("name")]
    payload = build_yields_template_xlsx(field_names)
    return Response(
        content=payload,
        media_type=_XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": (
                'attachment; filename="sapling-yields-template.xlsx"'
            ),
        },
    )


@router.delete("/fields/{field_id}", status_code=200)
def delete_field(field_id: str, user: CurrentUser = Depends(get_current_user)):
    """Soft-delete a field and cascade to every soil/leaf analysis,
    yield record, blend, application, etc. tied to it. Re-creating a
    field with the same name on the same farm later succeeds because
    the (farm_id, name) unique index is partial on deleted_at IS NULL
    (migration 091). Admins can hard-delete via admin endpoint."""
    from datetime import datetime, timezone
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    _cascade_soft_delete_fields(sb, field_ids=[field_id], user_id=user.id)
    sb.table("fields").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user.id,
    }).eq("id", field_id).execute()
    _audit(sb, user, "soft_delete", "fields", field_id)
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
        .is_("deleted_at", "null")
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
    """Soft-delete a crop history entry."""
    from datetime import datetime, timezone
    sb = get_supabase_admin()
    entry = sb.table("field_crop_history").select("field_id").eq("id", entry_id).execute()
    if not entry.data:
        raise HTTPException(status_code=404, detail="Crop history entry not found")
    _check_field_access(sb, entry.data[0]["field_id"], user)
    sb.table("field_crop_history").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user.id,
    }).eq("id", entry_id).execute()
    _audit(sb, user, "soft_delete", "field_crop_history", entry_id)
    return {"detail": "Crop history entry deleted"}


# ── Field applications (historical-analysis tool) ─────────────────────────────


class FieldApplicationCreate(BaseModel):
    applied_date: str = Field(..., description="ISO date the application happened")
    product_label: Optional[str] = Field(None, max_length=400)
    rate_kg_ha: Optional[float] = Field(None, ge=0, le=100_000)
    rate_l_ha: Optional[float] = Field(None, ge=0, le=100_000)
    method: Optional[str] = Field(None, max_length=80)
    nutrients_kg_per_ha: Optional[dict] = None
    notes: Optional[str] = Field(None, max_length=2000)


class FieldApplicationUpdate(BaseModel):
    applied_date: Optional[str] = None
    product_label: Optional[str] = Field(None, max_length=400)
    rate_kg_ha: Optional[float] = Field(None, ge=0, le=100_000)
    rate_l_ha: Optional[float] = Field(None, ge=0, le=100_000)
    method: Optional[str] = Field(None, max_length=80)
    nutrients_kg_per_ha: Optional[dict] = None
    notes: Optional[str] = Field(None, max_length=2000)


@router.get("/fields/{field_id}/applications")
def list_field_applications(
    field_id: str, user: CurrentUser = Depends(get_current_user),
):
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    res = (
        sb.table("field_applications")
        .select("*")
        .eq("field_id", field_id)
        .is_("deleted_at", "null")
        .order("applied_date", desc=True)
        .execute()
    )
    return res.data or []


@router.post("/fields/{field_id}/applications", status_code=201)
def create_field_application(
    field_id: str,
    body: FieldApplicationCreate,
    user: CurrentUser = Depends(get_current_user),
):
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    payload = body.model_dump(exclude_none=True)
    payload["field_id"] = field_id
    payload["created_by"] = user.id
    payload["source"] = "manual"
    res = sb.table("field_applications").insert(payload).execute()
    if not res.data:
        raise HTTPException(500, "Failed to create application")
    _audit(sb, user, "create", "field_applications", res.data[0]["id"])
    return res.data[0]


@router.patch("/applications/{application_id}")
def update_field_application(
    application_id: str,
    body: FieldApplicationUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    sb = get_supabase_admin()
    row = sb.table("field_applications").select("field_id").eq("id", application_id).execute()
    if not row.data:
        raise HTTPException(404, "Application not found")
    _check_field_access(sb, row.data[0]["field_id"], user)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    res = sb.table("field_applications").update(updates).eq("id", application_id).execute()
    if not res.data:
        raise HTTPException(500, "Failed to update")
    _audit(sb, user, "update", "field_applications", application_id, updates)
    return res.data[0]


@router.delete("/applications/{application_id}", status_code=200)
def delete_field_application(
    application_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """Soft-delete a field application. Hard-delete + restore live on
    admin endpoints."""
    from datetime import datetime, timezone
    sb = get_supabase_admin()
    row = sb.table("field_applications").select("field_id").eq("id", application_id).execute()
    if not row.data:
        raise HTTPException(404, "Application not found")
    _check_field_access(sb, row.data[0]["field_id"], user)
    sb.table("field_applications").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user.id,
    }).eq("id", application_id).execute()
    _audit(sb, user, "soft_delete", "field_applications", application_id)
    return {"detail": "Application deleted"}


# ── Field events (cultivar change, replant, weather, etc.) ────────────────────


class FieldEventCreate(BaseModel):
    event_date: str
    event_type: str = Field(..., max_length=80)
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    metadata: Optional[dict] = None


@router.get("/fields/{field_id}/events")
def list_field_events(
    field_id: str, user: CurrentUser = Depends(get_current_user),
):
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    res = (
        sb.table("field_events")
        .select("*")
        .eq("field_id", field_id)
        .is_("deleted_at", "null")
        .order("event_date", desc=True)
        .execute()
    )
    return res.data or []


@router.post("/fields/{field_id}/events", status_code=201)
def create_field_event(
    field_id: str,
    body: FieldEventCreate,
    user: CurrentUser = Depends(get_current_user),
):
    sb = get_supabase_admin()
    _check_field_access(sb, field_id, user)
    payload = body.model_dump(exclude_none=True)
    payload["field_id"] = field_id
    payload["created_by"] = user.id
    res = sb.table("field_events").insert(payload).execute()
    if not res.data:
        raise HTTPException(500, "Failed to create event")
    _audit(sb, user, "create", "field_events", res.data[0]["id"])
    return res.data[0]


@router.delete("/events/{event_id}", status_code=200)
def delete_field_event(
    event_id: str, user: CurrentUser = Depends(get_current_user),
):
    """Soft-delete a field event. Hard-delete + restore live on admin
    endpoints."""
    from datetime import datetime, timezone
    sb = get_supabase_admin()
    row = sb.table("field_events").select("field_id").eq("id", event_id).execute()
    if not row.data:
        raise HTTPException(404, "Event not found")
    _check_field_access(sb, row.data[0]["field_id"], user)
    sb.table("field_events").update({
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": user.id,
    }).eq("id", event_id).execute()
    _audit(sb, user, "soft_delete", "field_events", event_id)
    return {"detail": "Event deleted"}
