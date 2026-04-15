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
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends

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

    active_programmes = (
        sb.table("programmes")
        .select("id", count="exact")
        .eq("agent_id", agent_id)
        .eq("status", "active")
        .is_("deleted_at", "null")
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
        sb.table("programmes")
        .select("id, name, season, status, created_at")
        .eq("agent_id", agent_id)
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
        .limit(ACTIVITY_FEED_LIMIT)
        .execute()
    )
    for p in (programmes.data or []):
        feed.append({
            "type": "programme",
            "id": p["id"],
            "title": p.get("name") or "Programme",
            "subtitle": f"{p.get('season') or ''} · {p.get('status') or ''}".strip(" ·"),
            "created_at": p["created_at"],
            "href": f"/season-manager/{p['id']}",
        })

    feed.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return feed[:ACTIVITY_FEED_LIMIT]


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.get("/workbench")
@limiter.limit("60/second; 600/minute")  # list-read tier
def get_workbench(
    request: Any,  # needed by slowapi decorator
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
        "recent_activity": activity,
        "is_onboarding": is_onboarding,
        "thresholds": {
            "stale_analysis_months": STALE_ANALYSIS_MONTHS,
        },
    }
