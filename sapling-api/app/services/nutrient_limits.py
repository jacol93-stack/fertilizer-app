"""Nutrient toxicity thresholds and safe limits.

Loads from the `nutrient_limits`, `tissue_toxicity`, and `nutrient_interactions`
database tables. Falls back to hardcoded defaults if DB is unavailable.

Sources: FAO, FERTASA, CRI, SAMAC, SAAGA, Reuter & Robinson, Marschner.
"""

from functools import lru_cache

# ── Hardcoded fallbacks (used if DB unavailable) ─────────────────────────

_FALLBACK_LIQUID_MAX = {
    "n": 20.0, "p": 15.0, "k": 20.0, "ca": 15.0, "mg": 10.0, "s": 15.0,
    "fe": 2.0, "b": 0.5, "mn": 3.0, "zn": 3.0, "mo": 0.3, "cu": 1.0,
}

_FALLBACK_FOLIAR_MAX = {
    "n": 5.0, "p": 2.0, "k": 5.0, "ca": 4.0, "mg": 4.0, "s": 10.0,
    "fe": 1.0, "b": 0.2, "mn": 2.5, "zn": 2.5, "mo": 0.25, "cu": 0.5,
}

_FALLBACK_FERTIGATION_MAX = {
    "n": 250, "p": 100, "k": 300, "ca": 200, "mg": 60, "s": 500,
    "fe": 5.0, "b": 1.0, "mn": 2.0, "zn": 2.0, "mo": 0.05, "cu": 0.2,
}


# ── Database loaders ─────────────────────────────────────────────────────

def _load_from_db():
    """Load nutrient limits from the database. Returns None if unavailable."""
    try:
        from app.supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        result = sb.table("nutrient_limits").select("*").execute()
        if not result.data:
            return None
        return result.data
    except Exception:
        return None


def get_liquid_blend_limits() -> dict[str, float]:
    """Get liquid blend max g/L limits. Loads from DB, falls back to hardcoded."""
    rows = _load_from_db()
    if rows:
        limits = {}
        for row in rows:
            val = row.get("liquid_max_g_per_l")
            if val is not None:
                limits[row["nutrient"]] = float(val)
        if limits:
            return limits
    return dict(_FALLBACK_LIQUID_MAX)


def get_foliar_limits() -> dict[str, float]:
    """Get foliar spray max g/L limits."""
    rows = _load_from_db()
    if rows:
        limits = {}
        for row in rows:
            val = row.get("foliar_max_g_per_l")
            if val is not None:
                limits[row["nutrient"]] = float(val)
        if limits:
            return limits
    return dict(_FALLBACK_FOLIAR_MAX)


def get_fertigation_limits() -> dict[str, float]:
    """Get fertigation max mg/L limits."""
    rows = _load_from_db()
    if rows:
        limits = {}
        for row in rows:
            val = row.get("fertigation_max_mg_per_l")
            if val is not None:
                limits[row["nutrient"]] = float(val)
        if limits:
            return limits
    return dict(_FALLBACK_FERTIGATION_MAX)


def get_soil_toxicity() -> dict[str, dict]:
    """Get soil toxicity thresholds."""
    rows = _load_from_db()
    if rows:
        tox = {}
        for row in rows:
            if row.get("soil_tox_threshold") is not None:
                tox[row["nutrient"]] = {
                    "method": row.get("soil_tox_method", ""),
                    "threshold": float(row["soil_tox_threshold"]),
                    "notes": row.get("soil_tox_notes", ""),
                }
        if tox:
            return tox
    return {}


def get_tissue_toxicity(crop: str | None = None) -> list[dict]:
    """Get tissue toxicity thresholds, optionally filtered by crop."""
    try:
        from app.supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        query = sb.table("tissue_toxicity").select("*")
        if crop:
            query = query.eq("crop", crop.lower())
        result = query.execute()
        return result.data or []
    except Exception:
        return []


def get_nutrient_interactions() -> list[dict]:
    """Get nutrient interaction warnings."""
    try:
        from app.supabase_client import get_supabase_admin
        sb = get_supabase_admin()
        result = sb.table("nutrient_interactions").select("*").execute()
        return result.data or []
    except Exception:
        return []


# ── Convenience: backwards-compatible dict for liquid optimizer ──────────
# The optimizer imports this directly. It calls the DB loader each time
# which is fine for per-request usage.

LIQUID_BLEND_MAX_G_PER_L = _FALLBACK_LIQUID_MAX  # Default at import time


def load_liquid_limits():
    """Reload liquid limits from DB. Call at request time."""
    return get_liquid_blend_limits()
