"""Agent workbench — the dashboard every agent sees on /.

Answers the one question agents ask every morning: "what needs my
attention today?" One endpoint, one round-trip, assembled server-side
to avoid the N+1 pattern the /clients page currently has.

Every section is wrapped in try/except so a single missing column can't
take down the whole dashboard — a broken card just returns empty, and
the rest of the page keeps working. We log the failure so we notice.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.auth import CurrentUser, get_current_user
from app.rate_limit import limiter
from app.supabase_client import get_supabase_admin

router = APIRouter(tags=["Workbench"])

logger = logging.getLogger("sapling.workbench")

# How old an analysis must be before we flag it as "stale" on the dashboard.
# 12 months is the usual re-test cadence for annual crops; perennials can go
# further. Tunable later — expose via query param or agent preference.
STALE_ANALYSIS_MONTHS = 12

# How many items to preview in an attention card before linking out.
CARD_PREVIEW_LIMIT = 5

# How many items in the recent-activity feed.
ACTIVITY_FEED_LIMIT = 10


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _safe(section_name: str, fn, default):
    """Run a workbench section, log and fall back on any error."""
    try:
        return fn()
    except Exception as e:
        logger.warning(f"workbench.{section_name} failed: {e}", extra={"section": section_name})
        return default


# ── Individual section builders ────────────────────────────────────────────

def _get_stats(sb, agent_id: str) -> dict[str, int]:
    """At-a-glance totals shown in the stats row."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    client_count = (
        sb.table("clients")
        .select("id", count="exact")
        .eq("agent_id", agent_id)
        .is_("deleted_at", "null")
        .execute()
    ).count or 0

    farms_this_agent = (
        sb.table("clients")
        .select("id")
        .eq("agent_id", agent_id)
        .is_("deleted_at", "null")
        .execute()
    )
    client_ids = [c["id"] for c in (farms_this_agent.data or [])]

    farm_count = 0
    field_count = 0
    if client_ids:
        farms = (
            sb.table("farms")
            .select("id", count="exact")
            .in_("client_id", client_ids)
            .execute()
        )
        farm_count = farms.count or 0
        farm_ids = [f["id"] for f in (farms.data or [])]
        if farm_ids:
            fields = (
                sb.table("fields")
                .select("id", count="exact")
                .in_("farm_id", farm_ids)
                .execute()
            )
            field_count = fields.count or 0

    analyses_mtd = (
        sb.table("soil_analyses")
        .select("id", count="exact")
        .eq("agent_id", agent_id)
        .is_("deleted_at", "null")
        .gte("created_at", _iso(month_start))
        .execute()
    ).count or 0

    # Open programmes = v2 artifacts in any non-terminal state. The user's
    # mental model is "programmes still in flight", which spans drafts,
    # approved, and activated.
    active_programmes = (
        sb.table("programme_artifacts")
        .select("id", count="exact")
        .eq("user_id", agent_id)
        .in_("state", ["draft", "approved", "activated", "in_progress"])
        .execute()
    ).count or 0

    pending_quotes = (
        sb.table("quotes")
        .select("id", count="exact")
        .eq("agent_id", agent_id)
        .eq("status", "pending")
        .is_("deleted_at", "null")
        .execute()
    ).count or 0

    return {
        "clients": client_count,
        "farms": farm_count,
        "fields": field_count,
        "analyses_this_month": analyses_mtd,
        "active_programmes": active_programmes,
        "pending_quotes": pending_quotes,
    }


def _get_stale_analyses(sb, agent_id: str) -> dict[str, Any]:
    """Analyses older than STALE_ANALYSIS_MONTHS — fields ripe for re-testing.

    Approach: fetch this agent's most-recent analysis per field (via
    grouping in Python, since Supabase client doesn't do window functions),
    then filter to ones older than the cutoff.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * STALE_ANALYSIS_MONTHS)

    # Grab all this agent's non-deleted analyses with the fields we need.
    result = (
        sb.table("soil_analyses")
        .select("id, field_id, client_id, crop, customer, farm, field, created_at")
        .eq("agent_id", agent_id)
        .eq("status", "saved")
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
        .limit(500)
        .execute()
    )
    rows = result.data or []

    # Keep most-recent per field_id (or client_id if no field_id).
    latest_per_key: dict[str, dict] = {}
    for r in rows:
        key = r.get("field_id") or f"client:{r.get('client_id')}"
        if key not in latest_per_key:
            latest_per_key[key] = r

    stale = []
    for r in latest_per_key.values():
        created = r.get("created_at")
        if not created:
            continue
        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            continue
        if created_dt < cutoff:
            stale.append({
                "analysis_id": r["id"],
                "client_id": r.get("client_id"),
                "customer": r.get("customer") or "",
                "farm": r.get("farm") or "",
                "field": r.get("field") or "",
                "crop": r.get("crop") or "",
                "last_analysed_at": created,
                "days_old": (datetime.now(timezone.utc) - created_dt).days,
            })

    stale.sort(key=lambda x: x["days_old"], reverse=True)
    return {
        "count": len(stale),
        "preview": stale[:CARD_PREVIEW_LIMIT],
    }


def _get_clients_never_analysed(sb, agent_id: str) -> dict[str, Any]:
    """Clients with zero non-deleted soil analyses — onboarding gap."""
    clients = (
        sb.table("clients")
        .select("id, name")
        .eq("agent_id", agent_id)
        .is_("deleted_at", "null")
        .execute()
    )
    client_rows = clients.data or []
    if not client_rows:
        return {"count": 0, "preview": []}

    client_ids = [c["id"] for c in client_rows]
    analyses = (
        sb.table("soil_analyses")
        .select("client_id")
        .in_("client_id", client_ids)
        .is_("deleted_at", "null")
        .execute()
    )
    analysed_ids = {a["client_id"] for a in (analyses.data or []) if a.get("client_id")}

    never = [
        {"client_id": c["id"], "name": c["name"]}
        for c in client_rows
        if c["id"] not in analysed_ids
    ]
    never.sort(key=lambda c: c["name"].lower())
    return {
        "count": len(never),
        "preview": never[:CARD_PREVIEW_LIMIT],
    }


def _get_pending_quotes(sb, agent_id: str) -> dict[str, Any]:
    """Quotes with status='pending' — awaiting farmer response."""
    result = (
        sb.table("quotes")
        .select("id, client_id, customer, blend_name, created_at, status")
        .eq("agent_id", agent_id)
        .eq("status", "pending")
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
        .limit(CARD_PREVIEW_LIMIT * 2)
        .execute()
    )
    rows = result.data or []
    now = datetime.now(timezone.utc)
    preview = []
    for r in rows[:CARD_PREVIEW_LIMIT]:
        created = r.get("created_at")
        days_old = 0
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                days_old = (now - created_dt).days
            except ValueError:
                pass
        preview.append({
            "quote_id": r["id"],
            "client_id": r.get("client_id"),
            "customer": r.get("customer") or "",
            "blend_name": r.get("blend_name") or "Unnamed",
            "days_pending": days_old,
        })
    return {"count": len(rows), "preview": preview}


# NOTE: _get_overdue_applications and _get_pending_adjustments were
# v1-coupled (programmes / programme_blends / programme_applications /
# programme_adjustments). Phase 4 will rebuild these against v2
# ProgrammeArtifact's tracking surface.


def _get_unread_messages(sb, agent_id: str) -> int:
    """Quote messages on own quotes, sent by someone else, unread."""
    quotes = (
        sb.table("quotes")
        .select("id")
        .eq("agent_id", agent_id)
        .is_("deleted_at", "null")
        .execute()
    )
    quote_ids = [q["id"] for q in (quotes.data or [])]
    if not quote_ids:
        return 0
    result = (
        sb.table("quote_messages")
        .select("id", count="exact")
        .in_("quote_id", quote_ids)
        .neq("sender_id", agent_id)
        .is_("read_at", "null")
        .execute()
    )
    return result.count or 0


def _build_today(
    stale: dict[str, Any],
    never: dict[str, Any],
    pending: dict[str, Any],
    unread_count: int,
) -> list[dict]:
    """Merge attention sections into a single urgency-ranked feed.

    Urgency rubric (higher = more urgent):
      unread message       → 100
      stale analysis       → 50 + clamp(months_old - threshold, 0, 40)
      pending quote        → 40 + clamp(days_pending, 0, 30)
      never-analysed       → 20
    Ties broken by insertion order.

    Phase 4 will reintroduce overdue-application + pending-adjustment
    items once those are rebuilt against v2 ProgrammeArtifact tracking.
    """
    items: list[dict] = []

    if unread_count:
        items.append({
            "kind": "unread_messages",
            "urgency": 100,
            "title": f"{unread_count} unread quote {'message' if unread_count == 1 else 'messages'}",
            "subtitle": "Someone replied on a quote you sent",
            "badge": f"{unread_count} new",
            "href": "/quotes",
        })

    for s in stale.get("preview", []):
        months_old = max(0, s["days_old"] // 30 - STALE_ANALYSIS_MONTHS)
        items.append({
            "kind": "stale_analysis",
            "urgency": 50 + min(months_old, 40),
            "title": f"{s['customer'] or '—'}{' · ' + s['field'] if s['field'] else ''}",
            "subtitle": f"{s['crop'] or 'Unknown crop'} · last tested {s['days_old']}d ago",
            "badge": f"{s['days_old'] // 30}mo",
            "href": f"/clients/{s['client_id']}" if s.get("client_id") else "/records",
        })

    for q in pending.get("preview", []):
        days = q.get("days_pending", 0)
        items.append({
            "kind": "pending_quote",
            "urgency": 40 + min(days, 30),
            "title": q["customer"] or q["blend_name"],
            "subtitle": f"Quote: {q['blend_name']} · waiting {days}d",
            "badge": f"{days}d",
            "href": f"/quotes/{q['quote_id']}",
        })

    for c in never.get("preview", []):
        items.append({
            "kind": "never_analysed",
            "urgency": 20,
            "title": c["name"],
            "subtitle": "No soil analysis on file yet",
            "badge": "new",
            "href": f"/clients/{c['client_id']}",
        })

    items.sort(key=lambda x: x["urgency"], reverse=True)
    return items


def _get_recent_activity(sb, agent_id: str) -> list[dict]:
    """Mixed feed: latest analyses, blends, programmes, quotes."""
    feed: list[dict] = []

    blends = (
        sb.table("blends")
        .select("id, blend_name, sa_notation, client, created_at")
        .eq("agent_id", agent_id)
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
        .limit(ACTIVITY_FEED_LIMIT)
        .execute()
    )
    for b in (blends.data or []):
        feed.append({
            "type": "blend",
            "id": b["id"],
            "title": b.get("sa_notation") or b.get("blend_name") or "Blend",
            "subtitle": b.get("client") or "",
            "created_at": b["created_at"],
            "href": f"/records",  # agent records page shows the blend
        })

    analyses = (
        sb.table("soil_analyses")
        .select("id, crop, customer, farm, field, created_at")
        .eq("agent_id", agent_id)
        .eq("status", "saved")
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
        .limit(ACTIVITY_FEED_LIMIT)
        .execute()
    )
    for a in (analyses.data or []):
        feed.append({
            "type": "soil_analysis",
            "id": a["id"],
            "title": a.get("crop") or "Soil analysis",
            "subtitle": " / ".join(x for x in [a.get("customer"), a.get("farm"), a.get("field")] if x),
            "created_at": a["created_at"],
            "href": f"/records",
        })

    programmes = (
        sb.table("programme_artifacts")
        .select("id, farm_name, crop, season, state, created_at")
        .eq("user_id", agent_id)
        .order("created_at", desc=True)
        .limit(ACTIVITY_FEED_LIMIT)
        .execute()
    )
    for p in (programmes.data or []):
        title = (
            f"{p['farm_name']} — {p['crop']}"
            if p.get("farm_name")
            else (p.get("crop") or "Programme")
        )
        feed.append({
            "type": "programme",
            "id": p["id"],
            "title": title,
            "subtitle": f"{p.get('season') or ''} · {p.get('state') or ''}".strip(" ·"),
            "created_at": p["created_at"],
            "href": f"/season-manager/artifact/{p['id']}",
        })

    feed.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return feed[:ACTIVITY_FEED_LIMIT]


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.get("/workbench")
@limiter.limit("60/second; 600/minute")  # list-read tier
def get_workbench(
    request: Request,  # needed by slowapi decorator
    user: CurrentUser = Depends(get_current_user),
):
    """The agent home page, assembled in one round-trip.

    Admin users see their own agent-level view (same shape) — they can
    switch to impersonation mode to see someone else's. The admin-specific
    dashboard with VPS/Supabase/user analytics lives at
    /api/admin/dashboard/* and is separate.
    """
    sb = get_supabase_admin()
    agent_id = user.id

    stats = _safe(
        "stats",
        lambda: _get_stats(sb, agent_id),
        {"clients": 0, "farms": 0, "fields": 0, "analyses_this_month": 0,
         "active_programmes": 0, "pending_quotes": 0},
    )
    stale_analyses = _safe(
        "stale_analyses",
        lambda: _get_stale_analyses(sb, agent_id),
        {"count": 0, "preview": []},
    )
    never_analysed = _safe(
        "clients_never_analysed",
        lambda: _get_clients_never_analysed(sb, agent_id),
        {"count": 0, "preview": []},
    )
    pending_quotes = _safe(
        "pending_quotes",
        lambda: _get_pending_quotes(sb, agent_id),
        {"count": 0, "preview": []},
    )
    unread_messages = _safe("unread_messages", lambda: _get_unread_messages(sb, agent_id), 0)
    activity = _safe("recent_activity", lambda: _get_recent_activity(sb, agent_id), [])
    today = _safe(
        "today",
        lambda: _build_today(
            stale_analyses, never_analysed, pending_quotes, unread_messages,
        ),
        [],
    )

    # Onboarding state: a brand-new agent with no clients and nothing saved
    # gets a different landing experience. Detect it server-side so the
    # frontend doesn't have to guess.
    is_onboarding = (
        stats["clients"] == 0
        and stats["analyses_this_month"] == 0
        and stats["active_programmes"] == 0
        and stats["pending_quotes"] == 0
    )

    return {
        "user": {
            "id": user.id,
            "name": getattr(user, "name", None),
            "email": user.email,
            "role": user.role,
            "impersonated_by": user.impersonated_by,
        },
        "stats": stats,
        "attention": {
            "stale_analyses": stale_analyses,
            "clients_never_analysed": never_analysed,
            "pending_quotes": pending_quotes,
            "unread_messages": unread_messages,
        },
        "today": today,
        "recent_activity": activity,
        "is_onboarding": is_onboarding,
        "thresholds": {
            "stale_analysis_months": STALE_ANALYSIS_MONTHS,
        },
    }


# ── Global search ──────────────────────────────────────────────────────────

# Characters that would break a PostgREST `or()` expression. Keeping it tight
# to alphanumerics + basic separators removes ilike wildcard injection and
# comma/paren escapes in one pass.
_SEARCH_SAFE_RE = re.compile(r"[^a-zA-Z0-9 \-_.@/]")

SEARCH_PER_KIND_LIMIT = 5


def _sanitize_query(raw: str) -> str:
    return _SEARCH_SAFE_RE.sub(" ", raw).strip()[:80]


def _search_clients(sb, agent_id: str, role: str, q: str) -> list[dict]:
    query = sb.table("clients").select("id, name, contact_person, email").is_("deleted_at", "null")
    if role != "admin":
        query = query.eq("agent_id", agent_id)
    query = query.or_(
        f"name.ilike.%{q}%,contact_person.ilike.%{q}%,email.ilike.%{q}%"
    ).limit(SEARCH_PER_KIND_LIMIT)
    rows = (query.execute().data or [])
    return [{
        "kind": "client",
        "id": r["id"],
        "title": r["name"],
        "subtitle": r.get("contact_person") or r.get("email") or "",
        "href": f"/clients/{r['id']}",
    } for r in rows]


def _search_analyses(sb, agent_id: str, role: str, q: str) -> list[dict]:
    query = (
        sb.table("soil_analyses")
        .select("id, client_id, customer, farm, field, crop, created_at")
        .eq("status", "saved")
        .is_("deleted_at", "null")
    )
    if role != "admin":
        query = query.eq("agent_id", agent_id)
    query = query.or_(
        f"customer.ilike.%{q}%,farm.ilike.%{q}%,field.ilike.%{q}%,crop.ilike.%{q}%"
    ).order("created_at", desc=True).limit(SEARCH_PER_KIND_LIMIT)
    rows = (query.execute().data or [])
    return [{
        "kind": "analysis",
        "id": r["id"],
        "title": r.get("customer") or r.get("crop") or "Soil analysis",
        "subtitle": " / ".join(x for x in [r.get("farm"), r.get("field"), r.get("crop")] if x),
        "href": f"/clients/{r['client_id']}" if r.get("client_id") else "/records",
    } for r in rows]


def _search_blends(sb, agent_id: str, role: str, q: str) -> list[dict]:
    query = (
        sb.table("blends")
        .select("id, blend_name, sa_notation, client, client_id, created_at")
        .eq("status", "saved")
        .is_("deleted_at", "null")
    )
    if role != "admin":
        query = query.eq("agent_id", agent_id)
    query = query.or_(
        f"blend_name.ilike.%{q}%,client.ilike.%{q}%,sa_notation.ilike.%{q}%"
    ).order("created_at", desc=True).limit(SEARCH_PER_KIND_LIMIT)
    rows = (query.execute().data or [])
    return [{
        "kind": "blend",
        "id": r["id"],
        "title": r.get("sa_notation") or r.get("blend_name") or "Blend",
        "subtitle": r.get("client") or "",
        "href": "/records",
    } for r in rows]


def _search_quotes(sb, agent_id: str, role: str, q: str) -> list[dict]:
    query = (
        sb.table("quotes")
        .select("id, customer, blend_name, status, created_at")
        .is_("deleted_at", "null")
    )
    if role != "admin":
        query = query.eq("agent_id", agent_id)
    query = query.or_(
        f"customer.ilike.%{q}%,blend_name.ilike.%{q}%"
    ).order("created_at", desc=True).limit(SEARCH_PER_KIND_LIMIT)
    rows = (query.execute().data or [])
    return [{
        "kind": "quote",
        "id": r["id"],
        "title": r.get("customer") or r.get("blend_name") or "Quote",
        "subtitle": f"{r.get('blend_name') or ''} · {r.get('status') or ''}".strip(" ·"),
        "href": f"/quotes/{r['id']}",
    } for r in rows]


@router.get("/search")
@limiter.limit("60/second; 600/minute")
def search(
    request: Request,
    q: str = Query("", max_length=80, description="Search term"),
    user: CurrentUser = Depends(get_current_user),
):
    """Global search across clients, analyses, blends and quotes.

    Returns up to SEARCH_PER_KIND_LIMIT items per kind, scoped to the
    current agent (admins search everything). Each item has a stable
    shape: { kind, id, title, subtitle, href }.
    """
    cleaned = _sanitize_query(q)
    if len(cleaned) < 2:
        return {"query": cleaned, "results": []}

    sb = get_supabase_admin()
    results: list[dict] = []
    for name, fn in (
        ("clients", _search_clients),
        ("analyses", _search_analyses),
        ("blends", _search_blends),
        ("quotes", _search_quotes),
    ):
        results.extend(_safe(
            f"search.{name}",
            lambda fn=fn: fn(sb, user.id, user.role, cleaned),
            [],
        ))

    return {"query": cleaned, "results": results}
