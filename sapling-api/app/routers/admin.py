"""Admin router — audit log, activity, user management."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Literal
from pydantic import BaseModel, EmailStr, Field

from app.auth import CurrentUser, require_admin
from app.pagination import Page, PageParams, apply_page
from app.supabase_client import get_supabase_admin

router = APIRouter(tags=["admin"])


# ── Pydantic models ──────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str | None = Field(None, min_length=8, max_length=128)
    role: Literal["admin", "sales_agent"] = "sales_agent"
    phone: str | None = Field(None, max_length=30)
    company: str | None = Field(None, max_length=200)


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    phone: str | None = Field(None, max_length=30)
    company: str | None = Field(None, max_length=200)
    company_details: Any = None
    role: Literal["admin", "sales_agent"] | None = None


# ── Audit log ─────────────────────────────────────────────────────────────

@router.get("/audit-log")
def get_audit_log(
    page: PageParams = Depends(PageParams.as_query),
    event_type: str | None = None,
    user_id: str | None = None,
    entity_type: str | None = None,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only — query audit_log table with optional filters."""
    sb = get_supabase_admin()
    try:
        query = sb.table("audit_log").select("*", count="exact")
        if event_type:
            query = query.eq("event_type", event_type)
        if user_id:
            query = query.eq("user_id", user_id)
        if entity_type:
            query = query.eq("entity_type", entity_type)
        query = apply_page(query, page, default_order="created_at")
        result = query.execute()
        return Page.from_result(result, page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Activity summary ──────────────────────────────────────────────────────

@router.get("/activity")
def get_agent_activity(
    limit: int = Query(default=30, ge=1, le=200),
    user: CurrentUser = Depends(require_admin),
):
    """Admin only — recent agent activity: blends and soil analyses by non-admin users."""
    sb = get_supabase_admin()
    try:
        # Resolve non-admin agent IDs. Previous implementation used
        # .neq("role", "admin") on saved_blends / soil_analyses — neither table
        # has a role column, and saved_blends is not the real table name, so
        # the filter was silently a no-op.
        non_admin = (
            sb.table("profiles")
            .select("id")
            .neq("role", "admin")
            .execute()
        )
        non_admin_ids = [p["id"] for p in (non_admin.data or [])]
        if not non_admin_ids:
            return []

        blends = (
            sb.table("blends")
            .select("id, blend_name, agent_id, client, created_at")
            .in_("agent_id", non_admin_ids)
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        analyses = (
            sb.table("soil_analyses")
            .select("id, customer, agent_id, crop, created_at")
            .in_("agent_id", non_admin_ids)
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        blend_items = [{**b, "type": "blend"} for b in (blends.data or [])]
        analysis_items = [{**a, "type": "soil_analysis"} for a in (analyses.data or [])]

        combined = blend_items + analysis_items
        combined.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return combined[: limit * 2]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Deleted records (trash) ──────────────────────────────────────────────

@router.get("/deleted")
def get_deleted_records(
    page: PageParams = Depends(PageParams.as_query),
    record_type: str | None = Query(None, description="Filter: blend, soil_analysis"),
    user_id: str | None = Query(None, description="Filter by agent"),
    user: CurrentUser = Depends(require_admin),
):
    """Admin only — list all soft-deleted records across blends and soil analyses.

    Combines two tables in Python then slices for pagination. Trash is
    intentionally small (old items get hard-deleted by admins) so an
    O(N) combine is fine.
    """
    sb = get_supabase_admin()
    results: list[dict] = []

    if not record_type or record_type == "blend":
        query = sb.table("blends").select(
            "id, blend_name, client, farm, created_by, created_at, deleted_at, deleted_by, agent_id"
        ).not_.is_("deleted_at", "null").order("deleted_at", desc=True)
        if user_id:
            query = query.eq("agent_id", user_id)
        blends = query.execute().data or []
        for b in blends:
            b["_type"] = "blend"
            b["_name"] = b.get("blend_name") or "Unnamed blend"
            b["_detail"] = b.get("client") or ""
        results.extend(blends)

    if not record_type or record_type == "soil_analysis":
        query = sb.table("soil_analyses").select(
            "id, customer, farm, field, crop, created_by, created_at, deleted_at, deleted_by, agent_id"
        ).not_.is_("deleted_at", "null").order("deleted_at", desc=True)
        if user_id:
            query = query.eq("agent_id", user_id)
        soils = query.execute().data or []
        for s in soils:
            s["_type"] = "soil_analysis"
            s["_name"] = f"{s.get('crop', '')} - {s.get('customer', '')}"
            s["_detail"] = f"{s.get('farm', '')} / {s.get('field', '')}"
        results.extend(soils)

    results.sort(key=lambda r: r.get("deleted_at", ""), reverse=True)
    total = len(results)
    sliced = results[page.skip : page.skip + page.limit]
    return Page.from_list(sliced, page, total=total)


@router.delete("/deleted/{record_type}/{record_id}")
def hard_delete_record(
    record_type: str,
    record_id: str,
    user: CurrentUser = Depends(require_admin),
):
    """Admin only — permanently delete a soft-deleted record."""
    sb = get_supabase_admin()
    table = "blends" if record_type == "blend" else "soil_analyses"
    result = sb.table(table).delete().eq("id", record_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Record not found")

    try:
        sb.rpc("log_audit_event", {
            "p_event_type": "hard_delete",
            "p_entity_type": table,
            "p_entity_id": record_id,
            "p_metadata": {},
            "p_user_id": user.id,
        }).execute()
    except Exception as _audit_exc:
        import logging as _logging
        _logging.getLogger("sapling.audit").debug(
            "log_audit_event failed: %s", _audit_exc, extra={"event_type": "hard_delete"}
        )

    return {"detail": "Record permanently deleted"}


# ── User management ──────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    page: PageParams = Depends(PageParams.as_query),
    search: str | None = Query(None, description="Search name or email"),
    role: str | None = Query(None, description="Filter by role"),
    user: CurrentUser = Depends(require_admin),
):
    """Admin only — list all user profiles."""
    sb = get_supabase_admin()
    try:
        query = sb.table("profiles").select("*", count="exact")
        if search:
            query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
        if role:
            query = query.eq("role", role)
        query = apply_page(query, page, default_order="created_at")
        result = query.execute()
        return Page.from_result(result, page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users", status_code=201)
def create_user(body: UserCreate, user: CurrentUser = Depends(require_admin)):
    """Admin only — create a new user. Sends invite email so they set their own password."""
    sb = get_supabase_admin()

    # Check for duplicate email
    try:
        existing = sb.table("profiles").select("id").eq("email", body.email).execute()
        if existing.data:
            raise HTTPException(status_code=409, detail=f"A user with email {body.email} already exists")
    except HTTPException:
        raise
    except Exception:
        pass  # If check fails, proceed anyway

    try:
        if body.password:
            # Legacy: create with password directly (for backwards compat)
            auth_response = sb.auth.admin.create_user(
                {
                    "email": body.email,
                    "password": body.password,
                    "email_confirm": True,
                    "user_metadata": {
                        "name": body.name,
                        "role": body.role,
                        "phone": body.phone,
                        "company": body.company,
                    },
                }
            )
        else:
            # Invite flow: create user and send invite email
            auth_response = sb.auth.admin.invite_user_by_email(
                body.email,
                options={
                    "data": {
                        "name": body.name,
                        "role": body.role,
                        "phone": body.phone,
                        "company": body.company,
                    },
                    "redirect_to": "https://app.saplingfertilizer.co.za/auth/callback?next=/set-password",
                },
            )

        new_user = auth_response.user
        if not new_user:
            raise HTTPException(status_code=500, detail="User creation failed")

        # Update the profile row with additional fields
        sb.table("profiles").upsert(
            {
                "id": new_user.id,
                "email": body.email,
                "name": body.name,
                "role": body.role,
                "phone": body.phone,
                "company": body.company,
            },
            on_conflict="id",
        ).execute()

        return {
            "id": new_user.id,
            "email": body.email,
            "name": body.name,
            "role": body.role,
            "invited": not bool(body.password),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/users/{user_id}")
def update_user(user_id: str, body: UserUpdate, user: CurrentUser = Depends(require_admin)):
    """Admin only — update a user's profile fields."""
    sb = get_supabase_admin()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        result = (
            sb.table("profiles")
            .update(updates)
            .eq("id", user_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}")
def delete_user(user_id: str, user: CurrentUser = Depends(require_admin)):
    """Admin only — delete a user via Supabase Auth admin API."""
    sb = get_supabase_admin()

    if user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    try:
        sb.auth.admin.delete_user(user_id)
        return {"detail": "User deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DeactivateRequest(BaseModel):
    reassign_to: str | None = None  # user_id to transfer data to


@router.post("/users/{user_id}/deactivate")
def deactivate_user(user_id: str, body: DeactivateRequest, user: CurrentUser = Depends(require_admin)):
    """Deactivate a user: disable auth, optionally reassign data, mark profile inactive."""
    sb = get_supabase_admin()

    if user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    # Verify user exists
    profile = sb.table("profiles").select("*").eq("id", user_id).execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Reassign data if target specified
    if body.reassign_to:
        # Verify target exists and is active
        target = sb.table("profiles").select("id, status").eq("id", body.reassign_to).execute()
        if not target.data:
            raise HTTPException(status_code=404, detail="Reassignment target user not found")
        if target.data[0].get("status") == "inactive":
            raise HTTPException(status_code=400, detail="Cannot reassign to an inactive user")

        # Transfer all data — store original agent_id for potential reversal
        try:
            sb.table("clients").update({"agent_id": body.reassign_to, "original_agent_id": user_id}).eq("agent_id", user_id).execute()
            sb.table("soil_analyses").update({"agent_id": body.reassign_to, "original_agent_id": user_id}).eq("agent_id", user_id).execute()
            sb.table("blends").update({"agent_id": body.reassign_to, "original_agent_id": user_id}).eq("agent_id", user_id).execute()
            sb.table("feeding_plans").update({"agent_id": body.reassign_to, "original_agent_id": user_id}).eq("agent_id", user_id).execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Data reassignment failed: {e}")

    # Disable Supabase Auth (user can no longer log in)
    try:
        sb.auth.admin.update_user_by_id(
            user_id,
            {"ban_duration": "876000h"},  # ~100 years = effectively permanent
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disable auth: {e}")

    # Mark profile as inactive (keep the record for historical queries)
    sb.table("profiles").update({"status": "inactive"}).eq("id", user_id).execute()

    return {
        "detail": "User deactivated",
        "reassigned": bool(body.reassign_to),
    }


@router.post("/users/{user_id}/reactivate")
def reactivate_user(user_id: str, user: CurrentUser = Depends(require_admin)):
    """Reactivate a previously deactivated user and restore their data."""
    sb = get_supabase_admin()

    profile = sb.table("profiles").select("*").eq("id", user_id).execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Unban in Supabase Auth
    try:
        sb.auth.admin.update_user_by_id(
            user_id,
            {"ban_duration": "none"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reactivate auth: {e}")

    # Restore data that was reassigned during deactivation
    restored = False
    try:
        for table in ["clients", "soil_analyses", "blends", "feeding_plans"]:
            sb.table(table).update(
                {"agent_id": user_id, "original_agent_id": None}
            ).eq("original_agent_id", user_id).execute()
        restored = True
    except Exception:
        pass  # Data restore is best-effort

    sb.table("profiles").update({"status": "active"}).eq("id", user_id).execute()

    return {"detail": "User reactivated", "data_restored": restored}


# ── AI Usage Stats ───────────────────────────────────────────────────────


@router.get("/ai-usage")
def get_ai_usage(
    days: int = Query(30, ge=1, le=365),
    user: CurrentUser = Depends(require_admin),
):
    """Get AI usage stats — total cost, per user, per operation."""
    sb = get_supabase_admin()

    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    result = sb.table("ai_usage").select("*").gte("created_at", cutoff).order("created_at", desc=True).execute()
    rows = result.data or []

    # Aggregate
    total_cost = sum(float(r.get("cost_usd", 0)) for r in rows)
    total_input = sum(r.get("input_tokens", 0) for r in rows)
    total_output = sum(r.get("output_tokens", 0) for r in rows)

    # Per user
    by_user: dict[str, dict] = {}
    for r in rows:
        uid = r.get("user_id", "unknown")
        if uid not in by_user:
            by_user[uid] = {"user_id": uid, "calls": 0, "cost_usd": 0, "input_tokens": 0, "output_tokens": 0}
        by_user[uid]["calls"] += 1
        by_user[uid]["cost_usd"] += float(r.get("cost_usd", 0))
        by_user[uid]["input_tokens"] += r.get("input_tokens", 0)
        by_user[uid]["output_tokens"] += r.get("output_tokens", 0)

    # Per operation
    by_op: dict[str, dict] = {}
    for r in rows:
        op = r.get("operation", "unknown")
        if op not in by_op:
            by_op[op] = {"operation": op, "calls": 0, "cost_usd": 0}
        by_op[op]["calls"] += 1
        by_op[op]["cost_usd"] += float(r.get("cost_usd", 0))

    # Enrich user data with names
    if by_user:
        profiles = sb.table("profiles").select("id, name").in_("id", list(by_user.keys())).execute()
        name_map = {p["id"]: p["name"] for p in (profiles.data or [])}
        for uid, data in by_user.items():
            data["name"] = name_map.get(uid, "Unknown")

    return {
        "period_days": days,
        "total_calls": len(rows),
        "total_cost_usd": round(total_cost, 4),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "by_user": sorted(by_user.values(), key=lambda x: x["cost_usd"], reverse=True),
        "by_operation": sorted(by_op.values(), key=lambda x: x["cost_usd"], reverse=True),
        "recent": rows[:20],
    }
