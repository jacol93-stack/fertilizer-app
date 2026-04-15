"""Pricing suggestion engine — cost-weighted nutrient similarity."""

import statistics
import numpy as np
import pandas as pd


def cost_per_nutrient_pct(materials_df: pd.DataFrame) -> dict:
    """Calculate R cost to add 1% of each nutrient to a 1-ton blend.

    Args:
        materials_df: DataFrame with columns: cost_per_ton, n, p, k (lowercase DB columns)
    """
    result = {}
    for nut in ("n", "p", "k"):
        best = float("inf")
        for _, row in materials_df.iterrows():
            pct = row.get(nut, 0)
            cost = row.get("cost_per_ton", 0)
            if pct > 1 and 0 < cost < 500_000:
                kg_needed = 10.0 / (pct / 100)
                r_cost = kg_needed * (cost / 1000)
                if r_cost < best:
                    best = r_cost
        result[nut.upper()] = round(best, 1) if best < float("inf") else 1.0
    return result


def get_nutrient_weights(materials_df: pd.DataFrame):
    """Return weights normalised so the cheapest = 1.0."""
    cpn = cost_per_nutrient_pct(materials_df)
    min_cost = min(cpn.values())
    weights = {k: round(v / min_cost, 2) for k, v in cpn.items()}
    return weights, cpn


def _npk_dict(nutrients_list):
    """Extract {N, P, K} actual percentages from nutrients array."""
    d = {"N": 0, "P": 0, "K": 0}
    for n in (nutrients_list or []):
        if n["nutrient"] in d:
            d[n["nutrient"]] = n.get("actual", 0)
    return d


def suggest_price(actual_n, actual_p, actual_k, compost_pct,
                  all_blends, materials_df,
                  cost_tolerance=500, min_matches=3,
                  all_quotes=None):
    """Suggest selling price based on historical blends and quotes.

    Args:
        actual_n, actual_p, actual_k: actual nutrient percentages
        compost_pct: compost percentage in blend
        all_blends: list of blend dicts from DB
        materials_df: DataFrame of materials (for cost calculations)
        cost_tolerance: max acceptable R distance
        min_matches: minimum comparable blends before widening
        all_quotes: optional list of quote dicts with quoted_price and request_data
    """
    _, cpn = get_nutrient_weights(materials_df)

    if not all_blends and not all_quotes:
        return None

    def cost_distance(npk):
        return (abs(npk["N"] - actual_n) * cpn["N"]
                + abs(npk["P"] - actual_p) * cpn["P"]
                + abs(npk["K"] - actual_k) * cpn["K"])

    def find_matches(tol):
        matches = []
        for b in all_blends:
            npk = _npk_dict(b.get("nutrients"))
            dist = cost_distance(npk)
            if dist <= tol:
                price = b.get("selling_price") or b.get("cost_per_ton") or 0
                if price > 0:
                    matches.append({
                        "blend_name": b["blend_name"],
                        "client": b.get("client", ""),
                        "price": price,
                        "cost": b.get("cost_per_ton", 0),
                        "compost_pct": b.get("min_compost_pct", 0),
                        "npk": npk,
                        "distance": round(dist),
                        "date": (b.get("created_at") or "")[:10],
                    })
        return matches

    matches = find_matches(cost_tolerance)
    method = "tight"

    if len(matches) < min_matches:
        matches = find_matches(cost_tolerance * 2)
        method = "widened"

    # Also match against past quotes with pricing
    quote_comparables = []
    for q in (all_quotes or []):
        price = q.get("quoted_price") or 0
        if price <= 0:
            continue
        rd = q.get("request_data") or {}
        npk = _npk_dict(rd.get("nutrients"))
        if npk["N"] == 0 and npk["P"] == 0 and npk["K"] == 0:
            continue
        dist = cost_distance(npk)
        if dist <= cost_tolerance * 2:
            quote_comparables.append({
                "blend_name": rd.get("sa_notation") or q.get("quote_number", ""),
                "client": q.get("client_name", ""),
                "price": price,
                "cost": 0,
                "compost_pct": rd.get("min_compost_pct", 0),
                "npk": npk,
                "distance": round(dist),
                "date": (q.get("created_at") or "")[:10],
                "source": "quote",
                "status": q.get("status", ""),
                "quote_number": q.get("quote_number", ""),
                "agent_name": q.get("agent_name", ""),
            })

    # Regression fallback
    prices_all = []
    features_all = []
    for b in all_blends:
        price = b.get("selling_price") or b.get("cost_per_ton") or 0
        if price <= 0:
            continue
        npk = _npk_dict(b.get("nutrients"))
        w = npk["N"] * cpn["N"] + npk["P"] * cpn["P"] + npk["K"] * cpn["K"]
        cp = b.get("min_compost_pct", 50)
        features_all.append((w, cp))
        prices_all.append(price)

    regression = None
    if len(prices_all) >= 5:
        X = np.array([[f[0], f[1], 1] for f in features_all])
        y = np.array(prices_all)
        try:
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            w_new = actual_n * cpn["N"] + actual_p * cpn["P"] + actual_k * cpn["K"]
            predicted = coeffs[0] * w_new + coeffs[1] * compost_pct + coeffs[2]
            regression = {
                "predicted": round(max(predicted, 0), 0),
                "r_per_weighted_npk": round(coeffs[0], 2),
                "r_per_compost_pct": round(coeffs[1], 0),
            }
        except Exception:
            pass

    if not matches and regression:
        p = regression["predicted"]
        return {
            "found": 0,
            "low": round(p * 0.90),
            "mid": round(p),
            "high": round(p * 1.10),
            "comparables": [],
            "quote_comparables": sorted(quote_comparables, key=lambda m: m["distance"]),
            "method": "regression",
            "regression": regression,
            "weights": cpn,
        }

    if not matches and not quote_comparables:
        return None

    prices = sorted(m["price"] for m in matches) if matches else []

    if len(prices) == 0:
        low = mid = high = 0
    elif len(prices) == 1:
        low = mid = high = prices[0]
    elif len(prices) == 2:
        low, high = prices[0], prices[1]
        mid = statistics.mean(prices)
    else:
        low = prices[len(prices) // 4]
        mid = statistics.median(prices)
        high = prices[-(len(prices) // 4) - 1]

    return {
        "found": len(matches),
        "low": round(low),
        "mid": round(mid),
        "high": round(high),
        "comparables": sorted(matches, key=lambda m: m["distance"]),
        "quote_comparables": sorted(quote_comparables, key=lambda m: m["distance"]),
        "method": method,
        "regression": regression,
        "weights": cpn,
    }
