"""Rate limiting — path-classifying middleware.

Why not SlowAPI's per-route decorator? We have ~150 endpoints across 14
routers, most of them in untracked files. Decorating each one is a huge
diff surface. Instead, this module ships a single middleware that
classifies the request by path prefix and applies a tiered limit.

Tiers (decided with user 2026-04-14 — workload is "sporadic but intense"):

  engine   30/second; 300/minute    heavy calc endpoints — blend optimize,
                                    soil classify/targets/compare, feeding
                                    generate, foliar/liquid/leaf. Allows
                                    rapid slider-tweak bursts, caps abuse.
  list     60/second; 600/minute    GETs on list endpoints. Rapid browsing.
  admin    20/minute                POST/PATCH/DELETE on /api/admin/*.
                                    Low volume, intentional.
  ai       5/minute; 50/hour        AI-backed / expensive ops (lab extract,
                                    crop-norm generation). Cost control.
  session  10/minute; 200/hour      Session start/heartbeat. Anti-spam.
  default  200/minute               Everything else.

Keying: client IP from X-Forwarded-For (first hop) with a fallback to
request.client.host. TODO: switch to user_id after auth dependency runs
— requires reading the Authorization header here or deferring the check
until after routing. IP is good enough for a first pass.

Storage: in-memory deque per (rule, key). Single uvicorn worker assumed;
swap to Redis if you horizontally scale.

The `limiter` object is still exported for backwards-compatibility with
anything that already imports it (e.g. main.py's exception handler).
"""

from __future__ import annotations

import logging
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger("sapling.ratelimit")


# ── Legacy SlowAPI limiter ────────────────────────────────────────────────
# Kept for backward compatibility with main.py's exception handler and any
# old @limiter.limit decorators that may still be around. The real limiting
# is done by RateLimitMiddleware below.

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ── Tiered rules ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RateLimitRule:
    """A single rule: which paths + what the limits are.

    `limits` is a list of (max_requests, window_seconds) pairs — ALL must be
    satisfied. `30/second; 300/minute` → [(30, 1), (300, 60)].
    """
    name: str
    pattern: re.Pattern
    methods: frozenset[str]  # empty = all methods
    limits: tuple[tuple[int, int], ...]

    def matches(self, method: str, path: str) -> bool:
        if self.methods and method not in self.methods:
            return False
        return bool(self.pattern.search(path))


def _compile(*patterns: str) -> re.Pattern:
    return re.compile("|".join(patterns))


# Order matters — first match wins. Keep most-specific rules first.
RULES: tuple[RateLimitRule, ...] = (
    # ── AI / expensive operations ────────────────────────────────────────
    RateLimitRule(
        name="ai",
        pattern=_compile(
            r"^/api/soil/extract",           # lab PDF → Claude extraction
            r"^/api/leaf/extract",           # leaf lab extraction
            r"^/api/crop-norms/generate",    # Claude-generated crop norms
            r"^/api/soil/batch-analyze",     # bulk AI processing
        ),
        methods=frozenset({"POST", "PUT"}),
        limits=((5, 60), (50, 3600)),
    ),

    # ── Admin writes ─────────────────────────────────────────────────────
    RateLimitRule(
        name="admin",
        pattern=_compile(
            r"^/api/admin/",
            r"^/api/materials/",           # admin-only writes to materials
            r"^/api/crop-norms/",          # admin writes norms (reads stay default)
        ),
        methods=frozenset({"POST", "PUT", "PATCH", "DELETE"}),
        limits=((20, 60),),
    ),

    # ── Session / heartbeat ──────────────────────────────────────────────
    RateLimitRule(
        name="session",
        pattern=_compile(r"^/api/sessions/"),
        methods=frozenset(),  # any method
        limits=((10, 60), (200, 3600)),
    ),

    # ── Engine / calculation endpoints ───────────────────────────────────
    RateLimitRule(
        name="engine",
        pattern=_compile(
            r"^/api/blends/optimize",
            r"^/api/blends/priority-optimize",
            r"^/api/soil/classify",
            r"^/api/soil/targets",
            r"^/api/soil/compare",
            r"^/api/soil/corrections",
            r"^/api/feeding-plans/generate",
            r"^/api/feeding-plans/practical",
            r"^/api/foliar/",
            r"^/api/liquid/",
            r"^/api/leaf/diagnose",
            r"^/api/programmes/generate",
        ),
        methods=frozenset({"POST", "PUT"}),
        limits=((30, 1), (300, 60)),
    ),

    # ── List reads (trailing slash = list endpoint convention) ───────────
    RateLimitRule(
        name="list",
        pattern=_compile(
            r"^/api/blends/?$",
            r"^/api/soil/?$",
            r"^/api/clients/?$",
            r"^/api/quotes/?$",
            r"^/api/programmes/?$",
            r"^/api/leaf/?$",
            r"^/api/feeding-plans/?$",
            r"^/api/records",
            r"^/api/workbench/",
        ),
        methods=frozenset({"GET"}),
        limits=((60, 1), (600, 60)),
    ),
)

# Default rule if nothing matches — the outer `200/minute` cap so nothing
# is truly unlimited.
DEFAULT_LIMITS: tuple[tuple[int, int], ...] = ((200, 60),)
DEFAULT_NAME = "default"


# ── In-memory sliding-window store ────────────────────────────────────────

_buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = Lock()


def _prune(dq: deque[float], now: float, window: int) -> None:
    cutoff = now - window
    while dq and dq[0] < cutoff:
        dq.popleft()


def _check(rule_name: str, key: str, limits: tuple[tuple[int, int], ...]) -> tuple[bool, int | None]:
    """Return (allowed, retry_after_seconds). Mutates the bucket on allow."""
    now = time.monotonic()
    bucket_key = (rule_name, key)
    with _lock:
        dq = _buckets[bucket_key]
        # Prune against the LONGEST window first — that covers all shorter
        # ones for free and keeps the deque bounded.
        longest_window = max(w for _, w in limits)
        _prune(dq, now, longest_window)
        # Check each limit
        for max_req, window in limits:
            in_window = sum(1 for t in dq if t >= now - window)
            if in_window >= max_req:
                # Retry-after = time until the oldest in-window entry falls off
                oldest_in_window = next((t for t in dq if t >= now - window), now)
                retry = int(window - (now - oldest_in_window)) + 1
                return False, max(retry, 1)
        dq.append(now)
    return True, None


# ── Middleware ────────────────────────────────────────────────────────────

def _client_ip(request: Request) -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _classify(method: str, path: str) -> tuple[str, tuple[tuple[int, int], ...]]:
    for rule in RULES:
        if rule.matches(method, path):
            return rule.name, rule.limits
    return DEFAULT_NAME, DEFAULT_LIMITS


# Paths that bypass rate limiting entirely (health checks, static, OpenAPI).
_BYPASS = re.compile(r"^/api/health|^/openapi|^/docs|^/redoc|^/favicon")


async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    if _BYPASS.search(path):
        return await call_next(request)

    method = request.method
    rule_name, limits = _classify(method, path)
    key = _client_ip(request)
    allowed, retry_after = _check(rule_name, key, limits)

    if not allowed:
        logger.info(
            "rate_limit.blocked",
            extra={
                "rule": rule_name,
                "method": method,
                "path": path,
                "key": key,
                "retry_after": retry_after,
            },
        )
        # Best-effort limit header: the first (smallest-window) limit
        smallest = min(limits, key=lambda lw: lw[1])
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "rule": rule_name,
                "retry_after": retry_after,
            },
            headers={
                "Retry-After": str(retry_after or 1),
                "X-RateLimit-Rule": rule_name,
                "X-RateLimit-Limit": f"{smallest[0]}/{smallest[1]}s",
            },
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Rule"] = rule_name
    return response
