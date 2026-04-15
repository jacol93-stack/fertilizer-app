"""Blend optimizer using scipy linear programming."""

import numpy as np
from scipy.optimize import linprog


def run_optimizer(target_dict, df_mat, batch_size, c_idx, min_pct):
    """Linear-program blend optimizer. Returns scipy OptimizeResult.

    Args:
        target_dict: {nutrient: target_pct} e.g. {"N": 5.2, "P": 1.8}
        df_mat: DataFrame with nutrient columns (N, P, K, etc.) as percentages
        batch_size: total kg in the blend
        c_idx: index of compost material in df_mat
        min_pct: minimum compost percentage (0-100)
    """
    n_mats = len(df_mat)
    c = np.zeros(n_mats)
    c[c_idx] = -1

    A_eq, b_eq = [], []
    for nut, target_pct in target_dict.items():
        A_eq.append((df_mat[nut] / 100).to_numpy())
        b_eq.append(target_pct / 100 * batch_size)
    A_eq.append(np.ones(n_mats))
    b_eq.append(batch_size)

    A_ub = np.zeros((1, n_mats))
    A_ub[0, c_idx] = -1
    b_ub = np.array([-min_pct / 100 * batch_size])

    bounds = [(0, batch_size)] * n_mats
    return linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=np.array(A_eq),
                   b_eq=np.array(b_eq), bounds=bounds)


def find_closest_blend(target_dict, df_mat, batch_size, c_idx, min_pct):
    """Binary-search for the highest achievable fraction of targets.

    Always respects the minimum compost constraint — never relaxes it.

    Returns:
        (result, scale) — scale is the fraction of targets achieved (0-1).
    """
    lo, hi, best_res, best_scale = 0.0, 1.0, None, 0.0
    for _ in range(30):
        mid = (lo + hi) / 2
        scaled = {n: v * mid for n, v in target_dict.items()}
        res = run_optimizer(scaled, df_mat, batch_size, c_idx, min_pct)
        if res.success:
            best_res, best_scale, lo = res, mid, mid
        else:
            hi = mid
    return best_res, best_scale


def run_priority_optimizer(target_dict, priorities, df_mat, batch_size, c_idx, min_pct):
    """Optimize with nutrient priorities — satisfy must_match first, flex on the rest.

    Args:
        target_dict: {nutrient: target_pct}
        priorities: {nutrient: "must_match" | "flexible"}
        df_mat: DataFrame with nutrient columns
        batch_size: total kg
        c_idx: compost/filler index
        min_pct: minimum compost %

    Returns:
        (scipy_result, metadata) where metadata is:
        {
            "matched": ["N", "P", ...],
            "compromised": [{"nutrient": "Ca", "target": 4.0, "actual": 2.3}, ...],
            "feasible": bool,
            "scale": float,
        }
    """
    # 1. Try all targets first (maybe it works)
    res = run_optimizer(target_dict, df_mat, batch_size, c_idx, min_pct)
    if res.success:
        return res, {
            "matched": list(target_dict.keys()),
            "compromised": [],
            "feasible": True,
            "scale": 1.0,
        }

    # 2. Separate must_match and flexible targets
    must_match = {n: v for n, v in target_dict.items() if priorities.get(n) == "must_match"}
    flexible = [(n, v) for n, v in target_dict.items() if priorities.get(n) != "must_match"]
    # Sort flexible by target value ascending (drop smallest impact first)
    flexible.sort(key=lambda x: x[1])

    # 3. Try removing flexible targets one at a time
    remaining_flex = list(flexible)
    best_res = None
    dropped = []

    while remaining_flex:
        # Build target dict: must_match + remaining flexible
        trial = dict(must_match)
        for n, v in remaining_flex:
            trial[n] = v

        res = run_optimizer(trial, df_mat, batch_size, c_idx, min_pct)
        if res.success:
            best_res = res
            break

        # Drop the lowest-value flexible nutrient
        dropped_nutrient = remaining_flex.pop(0)
        dropped.append(dropped_nutrient)

    # 4. If still no luck with any flexible, try just must_match
    if best_res is None:
        res = run_optimizer(must_match, df_mat, batch_size, c_idx, min_pct)
        if res.success:
            best_res = res
            dropped = list(flexible)  # All flexible were dropped

    # 5. If even must_match alone fails, scale down must_match
    scale = 1.0
    if best_res is None:
        if must_match:
            best_res, scale = find_closest_blend(must_match, df_mat, batch_size, c_idx, min_pct)
            dropped = list(flexible)
        if best_res is None:
            # Completely infeasible
            return None, {
                "matched": [],
                "compromised": [{"nutrient": n, "target": v, "actual": 0} for n, v in target_dict.items()],
                "feasible": False,
                "scale": 0,
            }

    # 6. Calculate actual delivery for all nutrients (including dropped ones)
    amounts = best_res.x
    matched = []
    compromised = []

    for nut, target in target_dict.items():
        actual_kg = sum(amounts[i] * (df_mat.iloc[i][nut] / 100) for i in range(len(amounts)))
        actual_pct = actual_kg / batch_size * 100

        was_dropped = nut in [d[0] for d in dropped]
        was_scaled = scale < 0.999 and nut in must_match

        if not was_dropped and not was_scaled and abs(actual_pct - target) < 0.05:
            matched.append(nut)
        else:
            compromised.append({
                "nutrient": nut,
                "target": round(target, 2),
                "actual": round(actual_pct, 2),
            })

    return best_res, {
        "matched": matched,
        "compromised": compromised,
        "feasible": True,
        "scale": round(scale, 4),
    }
