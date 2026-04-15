"""Shared material loading and blend building utilities.

Used by both the Quick Blend optimizer (blends.py) and the programme engine.
"""

import pandas as pd
from app.supabase_client import get_supabase_admin

COMPOST_NAME = "Manure Compost"
FILLER_NAME = "Dolomitic Lime (Filler)"

NUTRIENT_COLS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu", "c"]

DB_TO_UPPER = {
    "n": "N", "p": "P", "k": "K", "ca": "Ca", "mg": "Mg", "s": "S",
    "fe": "Fe", "b": "B", "mn": "Mn", "zn": "Zn", "mo": "Mo", "cu": "Cu", "c": "C",
}


def load_materials_df(selected_names: list[str] | None = None) -> pd.DataFrame:
    """Load materials from DB into a DataFrame with uppercase nutrient columns.

    Args:
        selected_names: if provided, filter to only these materials.
    Returns:
        DataFrame with columns: material, type, cost_per_ton, N, P, K, Ca, Mg, S, etc.
    """
    sb = get_supabase_admin()
    result = sb.table("materials").select("*").execute()
    if not result.data:
        return pd.DataFrame()

    df = pd.DataFrame(result.data)

    if selected_names:
        df = df[df["material"].isin(selected_names)].reset_index(drop=True)

    rename_map = {db: up for db, up in DB_TO_UPPER.items() if db in df.columns}
    df = df.rename(columns=rename_map)

    for col in DB_TO_UPPER.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def load_default_materials() -> tuple[list[str], float]:
    """Load the admin-configured default material names and min compost %.

    Returns:
        (material_names, min_compost_pct)
    """
    sb = get_supabase_admin()
    result = sb.table("default_materials").select("*").execute()
    if result.data:
        row = result.data[0]
        return row.get("materials") or [], row.get("agent_min_compost_pct", 50)
    return [], 50


def find_compost_index(df: pd.DataFrame) -> int | None:
    """Find the index of the compost material, or None."""
    matches = df.index[df["material"] == COMPOST_NAME].tolist()
    return matches[0] if matches else None


def find_filler_index(df: pd.DataFrame) -> int | None:
    """Find the index of the filler material, or None."""
    matches = df.index[df["material"] == FILLER_NAME].tolist()
    return matches[0] if matches else None


def build_recipe(df: pd.DataFrame, amounts: list[float], batch_size: float) -> list[dict]:
    """Build recipe rows from optimizer result amounts."""
    rows = []
    for i, kg in enumerate(amounts):
        if kg < 0.01:
            continue
        row = df.iloc[i]
        cost_per_ton = float(row.get("cost_per_ton", 0))
        rows.append({
            "material": row["material"],
            "type": row.get("type", ""),
            "kg": round(kg, 2),
            "pct": round(kg / batch_size * 100, 2),
            "cost": round(kg * cost_per_ton / 1000, 2),
        })
    return rows


def build_nutrients(
    df: pd.DataFrame, amounts: list[float], targets: dict[str, float], batch_size: float,
) -> list[dict]:
    """Build nutrient summary rows."""
    rows = []
    for nut in DB_TO_UPPER.values():
        if nut not in df.columns:
            continue
        actual_kg = sum(
            amounts[i] * float(df.iloc[i].get(nut, 0)) / 100
            for i in range(len(amounts))
        )
        actual_pct = actual_kg / batch_size * 100 if batch_size else 0
        target_pct = targets.get(nut, 0)
        rows.append({
            "nutrient": nut,
            "target": round(target_pct, 3),
            "actual": round(actual_pct, 3),
            "diff": round(actual_pct - target_pct, 3),
            "kg_per_ton": round(actual_pct * 10, 2),
        })
    return rows
