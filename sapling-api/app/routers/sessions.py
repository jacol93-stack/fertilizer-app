"""Session tracking — start, heartbeat, end."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth import CurrentUser, get_current_user
from app.supabase_client import get_supabase_admin

router = APIRouter(tags=["Sessions"])


# ── UA parsing (lightweight, no extra dependency) ────────────────────────

_BROWSER_RE = re.compile(
    r"(Edg|Edge|OPR|Opera|Chrome|Safari|Firefox|MSIE|Trident)[/\s]?([\d.]*)", re.I
)
_OS_RE = re.compile(
    r"(Windows NT|Mac OS X|iPhone|iPad|Android|Linux|CrOS)", re.I
)

_BROWSER_MAP = {
    "edg": "Edge", "edge": "Edge", "opr": "Opera", "opera": "Opera",
    "chrome": "Chrome", "safari": "Safari", "firefox": "Firefox",
    "msie": "IE", "trident": "IE",
}
_OS_MAP = {
    "windows nt": "Windows", "mac os x": "macOS", "iphone": "iOS",
    "ipad": "iPadOS", "android": "Android", "linux": "Linux", "cros": "ChromeOS",
}


def _parse_ua(ua: str) -> tuple[str, str, str]:
    """Return (device_type, browser, os) from a User-Agent string."""
    ua_lower = ua.lower()

    # Device type
    if any(k in ua_lower for k in ("iphone", "android", "mobile")):
        device = "mobile"
    elif any(k in ua_lower for k in ("ipad", "tablet")):
        device = "tablet"
    else:
        device = "desktop"

    # Browser — order matters: Edge/Opera use Chrome's engine
    browser = "Unknown"
    for token in ("Edg", "OPR", "Opera", "Firefox", "Chrome", "Safari"):
        if token.lower() in ua_lower or token in ua:
            browser = _BROWSER_MAP.get(token.lower(), token)
            break

    # OS
    os_name = "Unknown"
    m = _OS_RE.search(ua)
    if m:
        os_name = _OS_MAP.get(m.group(1).lower(), m.group(1))

    return device, browser, os_name


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ── Models ───────────────────────────────────────────────────────────────

class SessionStartRequest(BaseModel):
    user_agent: str = ""


class SessionIdRequest(BaseModel):
    session_id: str


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/start")
def start_session(
    body: SessionStartRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
):
    """Record a new user session on login."""
    sb = get_supabase_admin()
    device, browser, os_name = _parse_ua(body.user_agent)
    ip = _get_client_ip(request)

    try:
        result = sb.table("user_sessions").insert({
            "user_id": user.id,
            "ip_address": ip,
            "user_agent": body.user_agent[:500] if body.user_agent else None,
            "device_type": device,
            "browser": browser,
            "os": os_name,
        }).execute()

        # Update last_login_at on profile
        sb.table("profiles").update({
            "last_login_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user.id).execute()

        session_id = result.data[0]["id"] if result.data else None
        return {"session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/heartbeat")
def heartbeat(
    body: SessionIdRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """Update session heartbeat. Also cleans up stale sessions."""
    sb = get_supabase_admin()
    now = datetime.now(timezone.utc).isoformat()

    try:
        # Update this session's heartbeat
        sb.table("user_sessions").update({
            "last_heartbeat": now,
        }).eq("id", body.session_id).eq("user_id", user.id).is_("ended_at", "null").execute()

        # Clean up stale sessions (no heartbeat for 5+ minutes)
        sb.rpc("cleanup_stale_sessions", {}).execute()

        return {"ok": True}
    except Exception:
        # Heartbeat failures should not break the app
        return {"ok": True}


@router.post("/end")
def end_session(
    body: SessionIdRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """End a user session on logout or tab close."""
    sb = get_supabase_admin()

    try:
        # Fetch session to compute duration
        session = (
            sb.table("user_sessions")
            .select("started_at")
            .eq("id", body.session_id)
            .eq("user_id", user.id)
            .is_("ended_at", "null")
            .execute()
        )
        if not session.data:
            return {"ok": True}  # Already ended or not found

        started = datetime.fromisoformat(session.data[0]["started_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        duration = int((now - started).total_seconds())

        sb.table("user_sessions").update({
            "ended_at": now.isoformat(),
            "duration_seconds": duration,
        }).eq("id", body.session_id).execute()

        return {"ok": True}
    except Exception:
        return {"ok": True}  # Session end should never fail visibly
