"""Admin dashboard router — VPS metrics, Supabase metrics, user analytics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import CurrentUser, require_admin
from app.supabase_client import get_supabase_admin
from app.services.vps_metrics import get_all_metrics

router = APIRouter(tags=["Dashboard"])


# ── VPS Metrics ──────────────────────────────────────────────────────────

@router.get("/vps-metrics")
def vps_metrics(user: CurrentUser = Depends(require_admin)):
    """Current VPS metrics + 24h history from vps_metrics_history."""
    sb = get_supabase_admin()

    current = get_all_metrics()

    # Format uptime_human if present
    uptime_human = current.pop("uptime_human", None)
    if uptime_human:
        current["uptime_human"] = uptime_human

    # Fetch 24h history
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        history = (
            sb.table("vps_metrics_history")
            .select("recorded_at, cpu_percent, memory_percent, disk_percent")
            .gte("recorded_at", cutoff)
            .order("recorded_at", desc=False)
            .execute()
        )
        history_data = history.data or []
    except Exception:
        history_data = []

    return {"current": current, "history": history_data}


# ── Supabase Metrics ────────────────────────────────────────────────────

@router.get("/supabase-metrics")
def supabase_metrics(user: CurrentUser = Depends(require_admin)):
    """DB size, table sizes, connection count from Supabase."""
    sb = get_supabase_admin()

    try:
        result = sb.rpc("get_db_metrics", {}).execute()
        metrics = result.data if result.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DB metrics: {e}")

    # Format sizes
    db_size_bytes = metrics.get("db_size_bytes", 0)
    db_size_mb = round(db_size_bytes / (1024 * 1024), 1) if db_size_bytes else 0

    tables = metrics.get("tables", [])
    for t in tables:
        size_bytes = t.get("size_bytes", 0)
        t["size_mb"] = round(size_bytes / (1024 * 1024), 2) if size_bytes else 0

    return {
        "database": {
            "size_bytes": db_size_bytes,
            "size_mb": db_size_mb,
            "connection_count": metrics.get("connection_count", 0),
        },
        "tables": tables,
    }


# ── User Analytics ───────────────────────────────────────────────────────

@router.get("/user-analytics")
def user_analytics(
    days: int = Query(30, ge=1, le=365),
    user: CurrentUser = Depends(require_admin),
):
    """Aggregated user analytics — sessions, devices, daily active users."""
    sb = get_supabase_admin()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Get all profiles
    profiles_result = sb.table("profiles").select("id, name, email, role, company, last_login_at, status").execute()
    profiles = profiles_result.data or []
    profile_map = {p["id"]: p for p in profiles}

    # Get sessions in period
    sessions_result = (
        sb.table("user_sessions")
        .select("id, user_id, started_at, ended_at, duration_seconds, device_type, browser, os, ip_address")
        .gte("started_at", cutoff)
        .order("started_at", desc=True)
        .execute()
    )
    sessions = sessions_result.data or []

    # Aggregate per user
    user_stats: dict[str, dict] = {}
    for s in sessions:
        uid = s["user_id"]
        if uid not in user_stats:
            p = profile_map.get(uid, {})
            user_stats[uid] = {
                "user_id": uid,
                "name": p.get("name", "Unknown"),
                "email": p.get("email", ""),
                "role": p.get("role", ""),
                "company": p.get("company", ""),
                "last_login_at": p.get("last_login_at"),
                "session_count": 0,
                "total_seconds": 0,
                "devices": {},
                "browsers": {},
            }
        stats = user_stats[uid]
        stats["session_count"] += 1
        stats["total_seconds"] += s.get("duration_seconds") or 0

        device = s.get("device_type", "unknown")
        stats["devices"][device] = stats["devices"].get(device, 0) + 1

        browser = s.get("browser", "unknown")
        stats["browsers"][browser] = stats["browsers"].get(browser, 0) + 1

    # Compute derived fields per user
    users_list = []
    for uid, stats in user_stats.items():
        count = stats["session_count"]
        total_sec = stats["total_seconds"]
        stats["total_minutes"] = round(total_sec / 60, 1)
        stats["avg_session_minutes"] = round(total_sec / 60 / count, 1) if count else 0

        # Primary device/browser = most frequent
        stats["primary_device"] = max(stats["devices"], key=stats["devices"].get) if stats["devices"] else "unknown"
        stats["primary_browser"] = max(stats["browsers"], key=stats["browsers"].get) if stats["browsers"] else "unknown"

        # Clean up internal counters
        del stats["devices"]
        del stats["browsers"]
        del stats["total_seconds"]
        users_list.append(stats)

    users_list.sort(key=lambda u: u["session_count"], reverse=True)

    # Device breakdown (all sessions)
    device_counts: dict[str, int] = {}
    for s in sessions:
        d = s.get("device_type", "unknown")
        device_counts[d] = device_counts.get(d, 0) + 1
    device_breakdown = [{"device_type": k, "count": v} for k, v in device_counts.items()]

    # Daily active users
    dau: dict[str, set] = {}
    for s in sessions:
        day = s["started_at"][:10]  # YYYY-MM-DD
        if day not in dau:
            dau[day] = set()
        dau[day].add(s["user_id"])
    daily_active = sorted(
        [{"date": d, "count": len(uids)} for d, uids in dau.items()],
        key=lambda x: x["date"],
    )

    # Totals
    total_users = len([p for p in profiles if p.get("status") != "inactive"])
    active_users = len(user_stats)
    total_sessions = len(sessions)
    total_duration = sum(s.get("duration_seconds") or 0 for s in sessions)
    avg_session = round(total_duration / 60 / total_sessions, 1) if total_sessions else 0

    return {
        "period_days": days,
        "total_users": total_users,
        "active_users": active_users,
        "total_sessions": total_sessions,
        "avg_session_minutes": avg_session,
        "users": users_list,
        "device_breakdown": device_breakdown,
        "daily_active_users": daily_active,
    }


# ── Individual User Sessions ────────────────────────────────────────────

@router.get("/user-sessions")
def get_user_sessions(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    user: CurrentUser = Depends(require_admin),
):
    """Session history for a specific user."""
    sb = get_supabase_admin()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Get user name
    profile = sb.table("profiles").select("name, email").eq("id", user_id).execute()
    name = profile.data[0]["name"] if profile.data else "Unknown"

    sessions_result = (
        sb.table("user_sessions")
        .select("id, started_at, ended_at, duration_seconds, ip_address, device_type, browser, os")
        .eq("user_id", user_id)
        .gte("started_at", cutoff)
        .order("started_at", desc=True)
        .limit(200)
        .execute()
    )

    return {
        "user_id": user_id,
        "user_name": name,
        "sessions": sessions_result.data or [],
    }
