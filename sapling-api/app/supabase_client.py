"""Supabase client factories + a thin retry helper.

Supabase-py uses httpx with HTTP/2 under the hood. Idle connections in the
shared pool can go stale (macOS reports `Errno 35 EAGAIN` as
`httpx.ReadError`), and the client doesn't auto-retry. One transient blip
here bubbles up as a 500 for whatever endpoint was unlucky — most often
/api/materials/ because it's called on every admin page-load.

`run_sb` wraps a Supabase call and retries once on read/connect errors.
The second attempt grabs a fresh connection from the pool (the stale one
gets discarded by httpx), so we don't need to bust the cached client.
"""

from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import Callable, TypeVar

import httpx
import httpcore
from supabase import Client, create_client

from app.config import get_settings

logger = logging.getLogger("sapling.supabase")

T = TypeVar("T")

# Network errors that usually resolve on a second attempt against a fresh
# connection. We deliberately keep the list tight — not catching generic
# exceptions, so real bugs still surface.
_TRANSIENT = (
    httpx.ReadError,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    httpcore.ReadError,
    httpcore.ConnectError,
    httpcore.RemoteProtocolError,
)


def run_sb(fn: Callable[[], T], *, retries: int = 1, backoff: float = 0.15) -> T:
    """Run a Supabase call, retrying once on transient network errors."""
    last_exc: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except _TRANSIENT as e:
            last_exc = e
            if attempt < retries:
                logger.warning(
                    "supabase transient error (attempt %d/%d): %s",
                    attempt + 1, retries + 1, e,
                )
                time.sleep(backoff)
                continue
            raise
    assert last_exc is not None  # unreachable — loop always raises or returns
    raise last_exc


@lru_cache
def get_supabase_admin() -> Client:
    """Supabase client with service_role key — bypasses RLS."""
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


def get_supabase_for_user(access_token: str) -> Client:
    """Supabase client authenticated as a specific user (respects RLS)."""
    s = get_settings()
    client = create_client(s.supabase_url, s.supabase_anon_key)
    client.auth.set_session(access_token, "")
    return client
