"""Quote request and management endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user, require_admin
from app.pagination import Page, PageParams, apply_page
from app.supabase_client import get_supabase_admin
from app.services.email_service import (
    send_quote_request_email,
    send_quote_response_email,
    send_quote_accepted_email,
    send_quote_declined_email,
    send_quote_revision_email,
    send_new_message_email,
    ADMIN_EMAIL,
)

router = APIRouter(tags=["Quotes"])


# ── Models ────────────────────────────────────────────────────────────────────

class QuoteCreate(BaseModel):
    quote_type: str = Field(..., max_length=50)
    client_id: str | None = None
    client_name: str = Field(..., min_length=1, max_length=200)
    farm_name: str | None = Field(None, max_length=200)
    field_name: str | None = Field(None, max_length=200)
    blend_id: str | None = None
    soil_analysis_id: str | None = None
    feeding_plan_id: str | None = None
    request_data: dict
    agent_notes: str | None = Field(None, max_length=5000)
    payment_terms: str | None = Field(None, max_length=50)
    delivery_date_from: str | None = Field(None, max_length=20)
    delivery_date_to: str | None = Field(None, max_length=20)
    delivery_notes: str | None = Field(None, max_length=2000)


class QuotePrice(BaseModel):
    quoted_price: float = Field(..., gt=0, le=100_000_000)
    price_unit: str = Field("per_ton", max_length=50)
    valid_until: str | None = Field(None, max_length=20)
    admin_notes: str | None = Field(None, max_length=5000)


class QuoteAction(BaseModel):
    content: str | None = Field(None, max_length=5000)


class QuoteEdit(BaseModel):
    """Admin edits to a quote — changes are tracked in the thread."""
    quoted_price: float | None = Field(None, gt=0, le=100_000_000)
    price_unit: str | None = Field(None, max_length=50)
    valid_until: str | None = Field(None, max_length=20)
    payment_terms: str | None = Field(None, max_length=50)
    delivery_date_from: str | None = Field(None, max_length=20)
    delivery_date_to: str | None = Field(None, max_length=20)
    delivery_notes: str | None = Field(None, max_length=2000)
    admin_notes: str | None = Field(None, max_length=5000)


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_agent_profile(sb, user_id: str) -> dict:
    result = sb.table("profiles").select("name, email, role, company, company_details").eq("id", user_id).execute()
    if not result.data:
        return {"name": "Unknown", "email": "", "role": ""}
    return result.data[0]


def _create_message(sb, quote_id: str, sender_id: str, sender_role: str,
                     message_type: str, content: str = None, metadata: dict = None) -> dict:
    """Create a quote message. Returns the created message."""
    msg = {
        "quote_id": quote_id,
        "sender_id": sender_id,
        "sender_role": sender_role,
        "message_type": message_type,
        "content": content,
        "metadata": metadata or {},
    }
    result = sb.table("quote_messages").insert(msg).execute()
    return result.data[0] if result.data else msg


# ── Agent Endpoints ──────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_quote(body: QuoteCreate, user: CurrentUser = Depends(get_current_user)):
    """Submit a new quote request."""
    sb = get_supabase_admin()

    # Generate quote number
    try:
        num_result = sb.rpc("generate_quote_number", {}).execute()
        quote_number = num_result.data if isinstance(num_result.data, str) else f"QR-{datetime.now().strftime('%Y')}-0000"
    except Exception:
        quote_number = f"QR-{datetime.now().strftime('%Y-%m%d-%H%M%S')}"

    quote_data = {
        "quote_number": quote_number,
        "agent_id": user.id,
        "quote_type": body.quote_type,
        "client_id": body.client_id,
        "client_name": body.client_name,
        "farm_name": body.farm_name,
        "field_name": body.field_name,
        "blend_id": body.blend_id,
        "soil_analysis_id": body.soil_analysis_id,
        "feeding_plan_id": body.feeding_plan_id,
        "request_data": body.request_data,
        "agent_notes": body.agent_notes,
        "payment_terms": body.payment_terms,
        "delivery_date_from": body.delivery_date_from,
        "delivery_date_to": body.delivery_date_to,
        "delivery_notes": body.delivery_notes,
        "status": "pending",
    }

    result = sb.table("quotes").insert(quote_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create quote request")

    quote = result.data[0]

    # Create initial message
    msg = _create_message(
        sb, quote["id"], user.id, user.role,
        "request", body.agent_notes or "Quote requested",
        {"quote_type": body.quote_type, "client": body.client_name},
    )

    # Send email to admin
    agent_profile = _get_agent_profile(sb, user.id)
    try:
        send_quote_request_email(
            quote=quote,
            agent_name=agent_profile.get("name", ""),
            agent_email=agent_profile.get("email", ""),
            message_id=msg.get("id", ""),
        )
        # Mark email as sent
        if msg.get("id"):
            sb.table("quote_messages").update(
                {"email_sent_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", msg["id"]).execute()
    except Exception:
        pass

    return quote


@router.get("/")
def list_quotes(
    page: PageParams = Depends(PageParams.as_query),
    status: str | None = Query(None),
    user: CurrentUser = Depends(get_current_user),
):
    """List quote requests. Agents see own; admins see all."""
    sb = get_supabase_admin()
    query = sb.table("quotes").select("*", count="exact")

    if user.role != "admin":
        query = query.eq("agent_id", user.id)
        # Hide cancelled quotes for agents unless explicitly filtered
        if not status:
            query = query.neq("status", "cancelled")

    if status:
        query = query.eq("status", status)

    query = apply_page(query, page, default_order="created_at")
    result = query.execute()
    quotes = result.data or []

    # Add unread count per quote (only for the current page — cheap)
    for q in quotes:
        try:
            unread = (
                sb.table("quote_messages")
                .select("id", count="exact")
                .eq("quote_id", q["id"])
                .neq("sender_id", user.id)
                .is_("read_at", "null")
                .execute()
            )
            q["unread_count"] = unread.count or 0
        except Exception as _e:
            import logging as _logging
            _logging.getLogger("sapling.quotes").debug("unread_count failed: %s", _e)
            q["unread_count"] = 0

    return Page.from_list(quotes, page, total=getattr(result, "count", None))


@router.get("/unread-count")
def unread_count(user: CurrentUser = Depends(get_current_user)):
    """Get total unread messages across all quotes for this user."""
    sb = get_supabase_admin()
    try:
        if user.role != "admin":
            # Agent: unread messages on own quotes, sent by others
            quotes = sb.table("quotes").select("id").eq("agent_id", user.id).execute()
            quote_ids = [q["id"] for q in (quotes.data or [])]
            if not quote_ids:
                return {"count": 0}
            result = (
                sb.table("quote_messages")
                .select("id", count="exact")
                .in_("quote_id", quote_ids)
                .neq("sender_id", user.id)
                .is_("read_at", "null")
                .execute()
            )
        else:
            # Admin: unread messages from others (not sent by this admin)
            result = (
                sb.table("quote_messages")
                .select("id", count="exact")
                .neq("sender_id", user.id)
                .is_("read_at", "null")
                .execute()
            )
        return {"count": result.count or 0}
    except Exception:
        return {"count": 0}


@router.get("/{quote_id}")
def get_quote(quote_id: str, user: CurrentUser = Depends(get_current_user)):
    """Get a single quote with all messages."""
    sb = get_supabase_admin()

    result = sb.table("quotes").select("*").eq("id", quote_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote = result.data[0]

    # Access control
    if user.role != "admin" and quote["agent_id"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Add agent name
    agent_profile = _get_agent_profile(sb, quote["agent_id"])
    quote["agent_name"] = agent_profile.get("name", "Unknown")
    quote["agent_email"] = agent_profile.get("email", "")

    # Get messages
    msgs = (
        sb.table("quote_messages")
        .select("*")
        .eq("quote_id", quote_id)
        .order("created_at")
        .execute()
    )
    quote["messages"] = msgs.data or []

    # Get sender names
    sender_ids = set(m["sender_id"] for m in quote["messages"])
    profiles = {}
    for sid in sender_ids:
        p = _get_agent_profile(sb, sid)
        profiles[sid] = p.get("name", "Unknown")
    for m in quote["messages"]:
        m["sender_name"] = profiles.get(m["sender_id"], "Unknown")

    # Mark messages as read (ones not sent by this user)
    try:
        sb.table("quote_messages").update(
            {"read_at": datetime.now(timezone.utc).isoformat()}
        ).eq("quote_id", quote_id).neq("sender_id", user.id).is_("read_at", "null").execute()
    except Exception:
        pass

    return quote


@router.post("/{quote_id}/accept")
def accept_quote(quote_id: str, body: QuoteAction, user: CurrentUser = Depends(get_current_user)):
    """Agent accepts a quoted price."""
    sb = get_supabase_admin()

    result = sb.table("quotes").select("*").eq("id", quote_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote = result.data[0]

    if quote["agent_id"] != user.id and not user.impersonated_by:
        raise HTTPException(status_code=403, detail="Access denied")
    if quote["status"] != "quoted":
        raise HTTPException(status_code=400, detail="Quote is not in 'quoted' status")

    sb.table("quotes").update({
        "status": "accepted",
        "responded_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", quote_id).execute()

    msg = _create_message(sb, quote_id, user.id, "sales_agent", "accepted", body.content)

    # Email admin
    agent = _get_agent_profile(sb, user.id)
    try:
        send_quote_accepted_email(quote, agent.get("name", ""), msg.get("id", ""))
    except Exception:
        pass

    return {"detail": "Quote accepted"}


@router.post("/{quote_id}/decline")
def decline_quote(quote_id: str, body: QuoteAction, user: CurrentUser = Depends(get_current_user)):
    """Agent declines a quoted price."""
    sb = get_supabase_admin()

    result = sb.table("quotes").select("*").eq("id", quote_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote = result.data[0]

    if quote["agent_id"] != user.id and not user.impersonated_by:
        raise HTTPException(status_code=403, detail="Access denied")
    if quote["status"] != "quoted":
        raise HTTPException(status_code=400, detail="Quote is not in 'quoted' status")

    sb.table("quotes").update({
        "status": "declined",
        "responded_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", quote_id).execute()

    msg = _create_message(sb, quote_id, user.id, "sales_agent", "declined", body.content or "Declined")

    agent = _get_agent_profile(sb, user.id)
    try:
        send_quote_declined_email(quote, agent.get("name", ""), body.content or "", msg.get("id", ""))
    except Exception:
        pass

    return {"detail": "Quote declined"}


@router.post("/{quote_id}/revision")
def request_revision(quote_id: str, body: QuoteAction, user: CurrentUser = Depends(get_current_user)):
    """Agent requests revision of a quote."""
    sb = get_supabase_admin()

    result = sb.table("quotes").select("*").eq("id", quote_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote = result.data[0]

    if quote["agent_id"] != user.id and not user.impersonated_by:
        raise HTTPException(status_code=403, detail="Access denied")
    if quote["status"] != "quoted":
        raise HTTPException(status_code=400, detail="Quote is not in 'quoted' status")

    sb.table("quotes").update({
        "status": "revision_requested",
    }).eq("id", quote_id).execute()

    msg = _create_message(sb, quote_id, user.id, "sales_agent", "revision_requested", body.content or "Revision requested")

    agent = _get_agent_profile(sb, user.id)
    try:
        send_quote_revision_email(quote, agent.get("name", ""), body.content or "", msg.get("id", ""))
    except Exception:
        pass

    return {"detail": "Revision requested"}


@router.post("/{quote_id}/cancel")
def cancel_quote(quote_id: str, body: QuoteAction, user: CurrentUser = Depends(get_current_user)):
    """Agent requests cancellation of a quote."""
    sb = get_supabase_admin()

    result = sb.table("quotes").select("*").eq("id", quote_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote = result.data[0]

    if quote["agent_id"] != user.id and user.role != "admin" and not user.impersonated_by:
        raise HTTPException(status_code=403, detail="Access denied")
    if quote["status"] in ("accepted", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a quote that is '{quote['status']}'")

    sb.table("quotes").update({
        "status": "cancelled",
        "responded_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", quote_id).execute()

    role = "admin" if user.role == "admin" else "sales_agent"
    msg = _create_message(sb, quote_id, user.id, role, "status_change",
                          body.content or "Quote cancellation requested",
                          {"new_status": "cancelled"})

    # Email admin
    agent = _get_agent_profile(sb, user.id)
    try:
        from app.services.email_service import send_new_message_email, ADMIN_EMAIL
        send_new_message_email(
            quote, ADMIN_EMAIL, agent.get("name", ""),
            f"Cancellation requested: {body.content or 'No reason given'}",
            True, msg.get("id", ""),
        )
    except Exception:
        pass

    return {"detail": "Quote cancelled"}


@router.post("/{quote_id}/message")
def add_message(quote_id: str, body: MessageCreate, user: CurrentUser = Depends(get_current_user)):
    """Add a message to the quote thread."""
    sb = get_supabase_admin()

    result = sb.table("quotes").select("*").eq("id", quote_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote = result.data[0]

    if user.role != "admin" and quote["agent_id"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    sender_role = "admin" if user.role == "admin" else "sales_agent"
    msg = _create_message(sb, quote_id, user.id, sender_role, "note", body.content)

    # Fetch thread history for email
    thread_messages = []
    try:
        thread_result = sb.table("quote_messages").select("*").eq("quote_id", quote_id).order("created_at").execute()
        if thread_result.data:
            # Add sender names
            for m in thread_result.data:
                p = _get_agent_profile(sb, m["sender_id"])
                m["sender_name"] = p.get("name", "Unknown")
            thread_messages = thread_result.data
    except Exception:
        pass

    # Email the other party with full thread
    try:
        sender_profile = _get_agent_profile(sb, user.id)
        if sender_role == "admin":
            agent = _get_agent_profile(sb, quote["agent_id"])
            send_new_message_email(
                quote, agent.get("email", ""), sender_profile.get("name", ""),
                body.content[:100], False, msg.get("id", ""),
                thread_messages=thread_messages,
            )
        else:
            send_new_message_email(
                quote, ADMIN_EMAIL, sender_profile.get("name", ""),
                body.content[:100], True, msg.get("id", ""),
                thread_messages=thread_messages,
            )
    except Exception:
        pass

    return msg


class AdminQuoteCreate(BaseModel):
    """Admin creates a quote directly (for external clients not on the app)."""
    client_name: str = Field(..., min_length=1, max_length=200)
    farm_name: str | None = Field(None, max_length=200)
    client_id: str | None = None
    request_data: dict
    quoted_price: float = Field(..., gt=0, le=100_000_000)
    price_unit: str = Field("per_ton", max_length=50)
    valid_until: str | None = Field(None, max_length=20)
    admin_notes: str | None = Field(None, max_length=5000)
    blend_id: str | None = None
    client_company_details: dict | None = None
    payment_terms: str | None = Field(None, max_length=50)
    delivery_date_from: str | None = Field(None, max_length=20)
    delivery_date_to: str | None = Field(None, max_length=20)
    delivery_notes: str | None = Field(None, max_length=2000)
    quantity_tons: float | None = Field(None, gt=0, le=1_000_000)
    include_vat: bool = False
    vat_rate: float | None = Field(None, ge=0, le=100)


# ── Admin Endpoints ──────────────────────────────────────────────────────────

@router.post("/admin/create", status_code=201)
def admin_create_quote(body: AdminQuoteCreate, user: CurrentUser = Depends(require_admin)):
    """Admin creates a quote directly — already priced, status=quoted."""
    sb = get_supabase_admin()

    try:
        num_result = sb.rpc("generate_quote_number", {}).execute()
        quote_number = num_result.data if isinstance(num_result.data, str) else f"QR-{datetime.now().strftime('%Y')}-0000"
    except Exception:
        quote_number = f"QR-{datetime.now().strftime('%Y-%m%d-%H%M%S')}"

    # If client_id provided, try to pull their company_details
    client_cd = body.client_company_details or {}
    if body.client_id and not client_cd:
        try:
            cr = sb.table("clients").select("company_details").eq("id", body.client_id).execute()
            if cr.data and cr.data[0].get("company_details"):
                client_cd = cr.data[0]["company_details"]
        except Exception:
            pass

    quote_data = {
        "quote_number": quote_number,
        "agent_id": user.id,
        "quote_type": "blend",
        "client_id": body.client_id,
        "client_name": body.client_name,
        "farm_name": body.farm_name,
        "blend_id": body.blend_id,
        "request_data": body.request_data,
        "status": "quoted",
        "quoted_price": body.quoted_price,
        "price_unit": body.price_unit,
        "valid_until": body.valid_until,
        "quoted_at": datetime.now(timezone.utc).isoformat(),
        "quoted_by": user.id,
        "client_company_details": client_cd or None,
        "payment_terms": body.payment_terms,
        "delivery_date_from": body.delivery_date_from,
        "delivery_date_to": body.delivery_date_to,
        "delivery_notes": body.delivery_notes,
    }
    # Store quantity and VAT in request_data
    extra = {}
    if body.quantity_tons:
        extra["quantity_tons"] = body.quantity_tons
    if body.include_vat:
        extra["include_vat"] = True
        extra["vat_rate"] = body.vat_rate or 15
    if extra:
        quote_data["request_data"] = {**body.request_data, **extra}

    result = sb.table("quotes").insert(quote_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create quote")

    quote = result.data[0]

    _create_message(
        sb, quote["id"], user.id, "admin", "quote_sent",
        body.admin_notes or f"Quote created at R{body.quoted_price:.2f}/{body.price_unit}",
        {"quoted_price": body.quoted_price, "price_unit": body.price_unit},
    )

    return quote


@router.get("/admin/list")
def admin_list_quotes(
    status: str | None = Query(None),
    agent_id: str | None = Query(None),
    user: CurrentUser = Depends(require_admin),
):
    """Admin: list all quote requests."""
    sb = get_supabase_admin()
    query = sb.table("quotes").select("*").order("created_at", desc=True)

    if status:
        query = query.eq("status", status)
    if agent_id:
        query = query.eq("agent_id", agent_id)

    result = query.execute()
    quotes = result.data or []

    # Add agent names and unread counts
    agent_cache = {}
    for q in quotes:
        aid = q["agent_id"]
        if aid not in agent_cache:
            agent_cache[aid] = _get_agent_profile(sb, aid)
        q["agent_name"] = agent_cache[aid].get("name", "Unknown")
        q["agent_email"] = agent_cache[aid].get("email", "")

        try:
            unread = (
                sb.table("quote_messages")
                .select("id", count="exact")
                .eq("quote_id", q["id"])
                .eq("sender_role", "sales_agent")
                .is_("read_at", "null")
                .execute()
            )
            q["unread_count"] = unread.count or 0
        except Exception:
            q["unread_count"] = 0

    return quotes


@router.get("/admin/stats")
def admin_stats(user: CurrentUser = Depends(require_admin)):
    """Admin: dashboard stats."""
    sb = get_supabase_admin()
    try:
        pending = sb.table("quotes").select("id", count="exact").eq("status", "pending").execute()
        quoted = sb.table("quotes").select("id", count="exact").eq("status", "quoted").execute()
        accepted = sb.table("quotes").select("id", count="exact").eq("status", "accepted").execute()
        revision = sb.table("quotes").select("id", count="exact").eq("status", "revision_requested").execute()
        total = sb.table("quotes").select("id", count="exact").execute()
        return {
            "pending": pending.count or 0,
            "quoted": quoted.count or 0,
            "accepted": accepted.count or 0,
            "revision_requested": revision.count or 0,
            "total": total.count or 0,
        }
    except Exception:
        return {"pending": 0, "quoted": 0, "accepted": 0, "revision_requested": 0, "total": 0}


@router.post("/admin/{quote_id}/quote")
def admin_send_quote(quote_id: str, body: QuotePrice, user: CurrentUser = Depends(require_admin)):
    """Admin: set price and send quote to agent."""
    sb = get_supabase_admin()

    result = sb.table("quotes").select("*").eq("id", quote_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote = result.data[0]

    sb.table("quotes").update({
        "status": "quoted",
        "quoted_price": body.quoted_price,
        "price_unit": body.price_unit,
        "valid_until": body.valid_until,
        "quoted_at": datetime.now(timezone.utc).isoformat(),
        "quoted_by": user.id,
    }).eq("id", quote_id).execute()

    msg = _create_message(
        sb, quote_id, user.id, "admin", "quote_sent",
        body.admin_notes,
        {"quoted_price": body.quoted_price, "price_unit": body.price_unit, "valid_until": body.valid_until},
    )

    # Email agent
    agent = _get_agent_profile(sb, quote["agent_id"])
    try:
        send_quote_response_email(
            quote, agent.get("email", ""), agent.get("name", ""),
            body.quoted_price, body.price_unit,
            body.admin_notes or "", body.valid_until or "",
            msg.get("id", ""),
        )
        if msg.get("id"):
            sb.table("quote_messages").update(
                {"email_sent_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", msg["id"]).execute()
    except Exception:
        pass

    return {"detail": "Quote sent to agent"}


@router.patch("/admin/{quote_id}")
def admin_edit_quote(quote_id: str, body: QuoteEdit, user: CurrentUser = Depends(require_admin)):
    """Admin: edit quote details. Changes are tracked in the message thread."""
    sb = get_supabase_admin()

    result = sb.table("quotes").select("*").eq("id", quote_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Quote not found")

    old_quote = result.data[0]
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Track what changed for the message thread
    changes = []
    for key, new_val in updates.items():
        if key == "admin_notes":
            continue
        old_val = old_quote.get(key)
        if str(old_val) != str(new_val):
            label = key.replace("_", " ").title()
            changes.append(f"{label}: {old_val or '-'} -> {new_val}")

    # Apply updates (exclude admin_notes from DB update)
    db_updates = {k: v for k, v in updates.items() if k != "admin_notes"}
    if db_updates:
        sb.table("quotes").update(db_updates).eq("id", quote_id).execute()

    # Log changes in thread
    if changes:
        change_text = body.admin_notes or "Quote details updated"
        _create_message(
            sb, quote_id, user.id, "admin", "price_update",
            change_text,
            {"changes": changes},
        )

    return {"detail": "Quote updated", "changes": changes}


@router.post("/admin/{quote_id}/message")
def admin_add_message(quote_id: str, body: MessageCreate, user: CurrentUser = Depends(require_admin)):
    """Admin: add a message to the quote thread."""
    return add_message(quote_id, body, user)


# ── Quote PDF ─────────────────────────────────────────────────────────────────

@router.get("/{quote_id}/pdf")
def download_quote_pdf(quote_id: str, user: CurrentUser = Depends(get_current_user)):
    """Download a branded quote PDF."""
    from app.services.pdf_builder import build_quote_pdf
    from fastapi.responses import StreamingResponse
    import io

    sb = get_supabase_admin()
    result = sb.table("quotes").select("*").eq("id", quote_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Quote not found")

    quote = result.data[0]
    if user.role != "admin" and quote["agent_id"] != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch admin company details for PDF header (sender = Sapling)
    agent_profile = _get_agent_profile(sb, user.id)
    company_details = agent_profile.get("company_details") or {}

    # If quote has no client_company_details but has client_id, try to pull from client record
    if not quote.get("client_company_details") and quote.get("client_id"):
        try:
            cr = sb.table("clients").select("company_details").eq("id", quote["client_id"]).execute()
            if cr.data and cr.data[0].get("company_details"):
                quote["client_company_details"] = cr.data[0]["company_details"]
        except Exception:
            pass

    pdf_bytes = build_quote_pdf(quote, company_details=company_details)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Quote_{quote["quote_number"]}.pdf"'},
    )


# ── Email Tracking ───────────────────────────────────────────────────────────

@router.get("/email/track/{message_id}.png")
def track_email_open(message_id: str):
    """1x1 tracking pixel — records when email was opened."""
    sb = get_supabase_admin()
    try:
        sb.table("quote_messages").update(
            {"email_opened_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", message_id).is_("email_opened_at", "null").execute()
    except Exception:
        pass

    # Return 1x1 transparent PNG
    pixel = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
        0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
        0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x62, 0x00, 0x00, 0x00, 0x02,
        0x00, 0x01, 0xE5, 0x27, 0xDE, 0xFC, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
        0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
    ])
    return Response(content=pixel, media_type="image/png")
