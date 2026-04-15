"""SA and international fertilizer notation utilities."""


def sa_notation_to_pct(n_ratio, p_ratio, k_ratio, total_pct):
    """Convert SA notation like 2:3:2 (22) to individual N, P, K percentages."""
    ratio_sum = n_ratio + p_ratio + k_ratio
    if ratio_sum == 0:
        return 0.0, 0.0, 0.0
    per_part = total_pct / ratio_sum
    return n_ratio * per_part, p_ratio * per_part, k_ratio * per_part


def pct_to_sa_notation(n_pct, p_pct, k_pct, secondary_pcts=None):
    """Convert N, P, K percentages to SA notation like '2:3:2 (22)'.

    If secondary_pcts is provided (dict of {nutrient: pct}), appends them:
    e.g., '4:1:4 (9) + Ca 4%'

    Also returns the international notation as a second value:
    e.g., 'N 8% P 2% K 10% Ca 4%'

    Returns: (sa_notation, international_notation)
    """
    total = n_pct + p_pct + k_pct
    if total < 0.01:
        sa = "0:0:0 (0)"
        intl = "N 0% P 0% K 0%"
        if secondary_pcts:
            extras = _format_secondaries(secondary_pcts)
            if extras:
                sa += f" + {extras}"
                intl += f" {extras}"
        return sa, intl

    vals = [n_pct, p_pct, k_pct]
    non_zero = [v for v in vals if v > 0.001]
    if not non_zero:
        sa = f"0:0:0 ({total:.0f})"
        intl = f"N 0% P 0% K 0%"
        return sa, intl

    best_ratios = None
    best_error = float("inf")

    for denom_x10 in range(1, 200):
        denom = denom_x10 / 10.0
        trial = [round(v / denom) if v > 0.001 else 0 for v in vals]
        if max(trial) > 20 or max(trial) == 0:
            continue
        ratio_sum = sum(trial)
        if ratio_sum == 0:
            continue
        error = 0
        for i in range(3):
            expected_pct = trial[i] / ratio_sum
            actual_pct = vals[i] / total if total > 0 else 0
            error += abs(expected_pct - actual_pct)
        if (error < best_error - 0.002
                or (abs(error - best_error) < 0.002 and sum(trial) < sum(best_ratios or [999]))):
            best_error = error
            best_ratios = trial

    if best_ratios is None:
        min_val = min(non_zero)
        best_ratios = [round(v / min_val) for v in vals]

    sa = f"{best_ratios[0]}:{best_ratios[1]}:{best_ratios[2]} ({total:.0f})"
    intl = f"N {n_pct:.1f}% P {p_pct:.1f}% K {k_pct:.1f}%"

    if secondary_pcts:
        extras = _format_secondaries(secondary_pcts)
        if extras:
            sa += f" + {extras}"
            intl += f" {extras}"

    return sa, intl


def _format_secondaries(secondary_pcts):
    """Format secondary nutrient percentages for notation display."""
    if not secondary_pcts:
        return ""
    parts = []
    # Standard order for secondary nutrients
    order = ["Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Mo", "Cu"]
    for nut in order:
        pct = secondary_pcts.get(nut, 0)
        if pct and pct > 0.01:
            parts.append(f"{nut} {pct:.1f}%")
    return " + ".join(parts)
