import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request
from app.supabase_client import get_supabase_admin, run_sb
from supabase import create_client
from app.config import get_settings

logger = logging.getLogger("sapling.auth")

# Tightened from 60 minutes to 15. Impersonation is a footgun (it gives
# full access to another user's data); long-lived sessions amplify mistakes.
IMPERSONATION_TIMEOUT_MINUTES = 15

# Process-local fallback cache — only used if the impersonation_sessions
# table is unavailable (e.g. migration 035 not yet applied). Intentionally
# not the primary store; it is inconsistent across worker processes and
# lost on restart.
_impersonation_fallback: dict[str, datetime] = {}


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _latest_impersonation(sb_admin, admin_id: str) -> dict | None:
    """Return the most recent impersonation_sessions row for this admin,
    regardless of active/expired state, or None if there is no row.

    Caller distinguishes "active" / "expired" / "ended" via the returned
    expires_at and ended_at fields. This two-step design mirrors the
    original in-memory behavior: an expired session causes a hard error
    on the next request (forcing the admin to restart), instead of
    silently rolling over.
    """
    try:
        result = (
            sb_admin.table("impersonation_sessions")
            .select("id, admin_id, target_id, started_at, expires_at, ended_at")
            .eq("admin_id", admin_id)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        logger.warning(f"impersonation_sessions lookup failed, using fallback: {e}")
        start = _impersonation_fallback.get(admin_id)
        if start is None:
            return None
        expires = start + timedelta(minutes=IMPERSONATION_TIMEOUT_MINUTES)
        return {
            "started_at": start.isoformat(),
            "expires_at": expires.isoformat(),
            "ended_at": None,
            "_fallback": True,
        }


def _mark_impersonation_ended(sb_admin, session_id: str, reason: str) -> None:
    try:
        sb_admin.table("impersonation_sessions").update({
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "end_reason": reason,
        }).eq("id", session_id).execute()
    except Exception as e:
        logger.warning(f"impersonation_sessions ended-at update failed: {e}")


def _start_impersonation(sb_admin, admin_id: str, target_id: str, request: Request) -> None:
    """Create a new impersonation_sessions row (or fallback to in-memory)."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=IMPERSONATION_TIMEOUT_MINUTES)
    try:
        sb_admin.table("impersonation_sessions").insert({
            "admin_id": admin_id,
            "target_id": target_id,
            "started_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "ip_address": _get_client_ip(request),
            "user_agent": (request.headers.get("User-Agent") or "")[:500] or None,
        }).execute()
    except Exception as e:
        logger.warning(f"impersonation_sessions insert failed, using fallback: {e}")
        _impersonation_fallback[admin_id] = now


@dataclass
class CurrentUser:
    id: str
    role: str
    email: str | None = None
    impersonated_by: str | None = None  # admin user_id if impersonating


def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return auth[7:]


def get_current_user(request: Request) -> CurrentUser:
    """FastAPI dependency: verify Supabase JWT and return user info.

    If an admin sends X-Impersonate-User header, the returned CurrentUser
    will have the impersonated user's id/role/email, with impersonated_by
    set to the admin's id. Non-admins cannot impersonate.
    """
    token = _extract_token(request)
    settings = get_settings()

    # Use Supabase's own auth to verify the token
    try:
        sb = create_client(settings.supabase_url, settings.supabase_anon_key)
        user_response = run_sb(lambda: sb.auth.get_user(token))
        user = user_response.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # Get role from profiles table
    sb_admin = get_supabase_admin()
    result = run_sb(
        lambda: sb_admin.table("profiles").select("role, email").eq("id", user_id).execute()
    )
    if not result.data:
        raise HTTPException(status_code=401, detail="User profile not found")

    profile = result.data[0]
    caller_role = profile["role"]

    # Check for impersonation header
    impersonate_id = request.headers.get("X-Impersonate-User")
    if impersonate_id:
        if caller_role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can impersonate users")

        # Enforce impersonation timeout via the DB-backed session table.
        # Semantics (preserved from the old in-memory implementation):
        #   - No prior session          -> open a fresh 15-min window, proceed.
        #   - Prior session ended       -> open a fresh window, proceed.
        #   - Active session            -> proceed, do not extend.
        #   - Expired session (ended_at still NULL) -> mark ended="expired",
        #     raise 403 so the admin consciously restarts.
        now = datetime.now(timezone.utc)
        latest = _latest_impersonation(sb_admin, user_id)
        if latest is None or latest.get("ended_at"):
            _start_impersonation(sb_admin, user_id, impersonate_id, request)
        else:
            expires_at_str = latest.get("expires_at", "")
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                expires_at = now  # force expired on parse failure
            if now >= expires_at:
                session_id = latest.get("id")
                if session_id and not latest.get("_fallback"):
                    _mark_impersonation_ended(sb_admin, session_id, "expired")
                else:
                    _impersonation_fallback.pop(user_id, None)
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"Impersonation session expired after "
                        f"{IMPERSONATION_TIMEOUT_MINUTES} minutes. "
                        "Please start a new session."
                    ),
                )
            # Active session — still within expires_at, proceed.

        # Load the impersonated user's profile
        imp_result = sb_admin.table("profiles").select("role, email").eq("id", impersonate_id).execute()
        if not imp_result.data:
            raise HTTPException(status_code=404, detail="Impersonated user not found")

        imp_profile = imp_result.data[0]

        # Audit log the impersonation
        try:
            sb_admin.rpc("log_audit_event", {
                "p_user_id": user_id,
                "p_user_role": caller_role,
                "p_event_type": "impersonation",
                "p_entity_type": "user",
                "p_entity_id": impersonate_id,
                "p_metadata": {
                    "impersonated_user_email": imp_profile.get("email"),
                    "impersonated_user_role": imp_profile["role"],
                },
            }).execute()
        except Exception as _audit_exc:
            # Audit failure must never block auth — drop to debug so we can
            # still see it via structured logs if something's off.
            logger.debug(f"log_audit_event failed: {_audit_exc}", extra={"event_type": "impersonation"})

        return CurrentUser(
            id=impersonate_id,
            role=imp_profile["role"],
            email=imp_profile.get("email"),
            impersonated_by=user_id,
        )

    return CurrentUser(
        id=user_id,
        role=caller_role,
        email=profile.get("email"),
    )


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """FastAPI dependency: require admin role.

    If impersonating, checks the ORIGINAL caller's role (must be admin).
    """
    if user.impersonated_by:
        # The original caller was already verified as admin in get_current_user
        return user
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
