import io
import pathlib
import json
import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import date
from supabase import create_client

_HERE = pathlib.Path(__file__).parent
LOGO_PATH = _HERE / "logo.png"
LOGO_NO_SLOGAN_PATH = _HERE / "logo_no_slogan.png"

COMPOST_NAME = "Manure Compost"

# ── SA Notation helpers ────────────────────────────────────────────────────
def sa_notation_to_pct(n_ratio, p_ratio, k_ratio, total_pct):
    """Convert SA notation like 2:3:2 (22) to individual N, P, K percentages."""
    ratio_sum = n_ratio + p_ratio + k_ratio
    if ratio_sum == 0:
        return 0.0, 0.0, 0.0
    per_part = total_pct / ratio_sum
    return n_ratio * per_part, p_ratio * per_part, k_ratio * per_part


def pct_to_sa_notation(n_pct, p_pct, k_pct):
    """Convert N, P, K percentages to SA notation like '2:3:2 (22)'.
    Tries multipliers to find the best small whole-number ratio that
    accurately represents the proportions."""
    total = n_pct + p_pct + k_pct
    if total < 0.01:
        return "0:0:0 (0)"

    vals = [n_pct, p_pct, k_pct]
    non_zero = [v for v in vals if v > 0.001]
    if not non_zero:
        return f"0:0:0 ({total:.0f})"

    # Try many possible divisors to find the cleanest small integer ratio.
    # For each candidate divisor, round to integers and measure error
    # against the original proportions.
    best_ratios = None
    best_error = float("inf")
    best_max = float("inf")

    for denom_x10 in range(1, 200):  # try divisors from 0.1 to 20.0
        denom = denom_x10 / 10.0
        trial = [round(v / denom) if v > 0.001 else 0 for v in vals]
        if max(trial) > 20 or max(trial) == 0:
            continue
        ratio_sum = sum(trial)
        if ratio_sum == 0:
            continue
        # Measure proportional error
        error = 0
        for i in range(3):
            expected_pct = trial[i] / ratio_sum
            actual_pct = vals[i] / total if total > 0 else 0
            error += abs(expected_pct - actual_pct)
        # Prefer smaller ratios when error is similar
        if (error < best_error - 0.002
            or (abs(error - best_error) < 0.002 and sum(trial) < sum(best_ratios or [999]))):
            best_error = error
            best_ratios = trial
            best_max = max(trial)

    if best_ratios is None:
        min_val = min(non_zero)
        best_ratios = [round(v / min_val) for v in vals]

    return f"{best_ratios[0]}:{best_ratios[1]}:{best_ratios[2]} ({total:.0f})"


# ── Brand colours ──────────────────────────────────────────────────────────
ORANGE = "#ff4f00"
DARK_GREY = "#191919"
MED_GREY = "#4d4d4d"
ORANGE_RGB = (255, 79, 0)
DARK_GREY_RGB = (25, 25, 25)
MED_GREY_RGB = (77, 77, 77)
ORANGE_LIGHT = "#fff3eb"
ORANGE_FILL_RGB = (255, 243, 235)
GREY_LIGHT_RGB = (245, 245, 245)


def apply_styles():
    st.markdown(f"""
    <style>
        .stApp, .main .block-container,
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"] {{
            background-color: #ffffff !important;
        }}
        section[data-testid="stSidebar"] {{
            background-color: #ffffff !important;
            border-right: 2px solid {ORANGE} !important;
        }}
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: {DARK_GREY} !important;
        }}
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] label {{
            color: {MED_GREY} !important;
        }}
        h1, h2, h3 {{ color: {DARK_GREY} !important; }}
        p, li, span, label {{ color: {MED_GREY}; }}
        [data-testid="stMetricValue"] {{ color: {ORANGE} !important; }}
        [data-testid="stMetricLabel"] {{ color: {MED_GREY} !important; }}
        .stDownloadButton > button, .stButton > button {{
            background-color: {ORANGE} !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 6px !important;
        }}
        .stDownloadButton > button:hover, .stButton > button:hover {{
            background-color: {DARK_GREY} !important;
            color: #ffffff !important;
        }}
        .streamlit-expanderHeader {{ color: {MED_GREY} !important; }}
        hr {{ border-color: {ORANGE} !important; opacity: 0.4 !important; }}
        .stSlider [role="slider"] {{ background-color: {ORANGE} !important; }}
        [data-testid="stDataFrame"] th {{
            background-color: {ORANGE} !important;
            color: #ffffff !important;
        }}
        .stNumberInput input, .stTextInput input {{
            border-color: #dddddd !important;
            color: {DARK_GREY} !important;
            background-color: #ffffff !important;
        }}
        .stNumberInput input:focus, .stTextInput input:focus {{
            border-color: {ORANGE} !important;
            box-shadow: 0 0 0 1px {ORANGE} !important;
        }}
    </style>
    """, unsafe_allow_html=True)


def show_header(title="Blend Calculator"):
    logo_col, title_col = st.columns([2, 3])
    with logo_col:
        st.image(str(LOGO_PATH), width=320)
    with title_col:
        st.markdown(
            f"<h1 style='margin-bottom:0; color:{DARK_GREY}'>{title}</h1>",
            unsafe_allow_html=True,
        )


@st.cache_data
def load_materials():
    df = pd.read_excel(_HERE / "materials.xlsx")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    for col in df.columns:
        if col not in ["Material", "Type"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.fillna(0)


# ── Supabase ───────────────────────────────────────────────────────────────
def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def save_blend(blend_name, client, farm, batch_size, min_compost_pct,
               selling_price, cost_per_ton, targets, recipe_rows, nutrients,
               selected_materials):
    sb = get_supabase()
    data = {
        "blend_name": blend_name or "Unnamed",
        "client": client or None,
        "farm": farm or None,
        "batch_size": batch_size,
        "min_compost_pct": min_compost_pct,
        "selling_price": float(selling_price),
        "cost_per_ton": float(cost_per_ton),
        "targets": targets,
        "recipe": recipe_rows,
        "nutrients": nutrients,
        "selected_materials": selected_materials,
    }
    result = sb.table("blends").insert(data).execute()
    return result


def fetch_blends(search_term=None):
    sb = get_supabase()
    query = sb.table("blends").select("*").order("created_at", desc=True)
    if search_term:
        query = query.or_(
            f"blend_name.ilike.%{search_term}%,"
            f"client.ilike.%{search_term}%,"
            f"farm.ilike.%{search_term}%"
        )
    result = query.execute()
    return result.data


def update_blend(blend_id, updates):
    sb = get_supabase()
    sb.table("blends").update(updates).eq("id", blend_id).execute()


def delete_blend(blend_id):
    sb = get_supabase()
    sb.table("blends").delete().eq("id", blend_id).execute()


def fetch_all_blends():
    """Fetch all blends for backup export."""
    sb = get_supabase()
    result = sb.table("blends").select("*").order("created_at", desc=True).execute()
    return result.data


def restore_blends(blends_json):
    """Restore blends from backup JSON, skipping duplicates by ID."""
    sb = get_supabase()
    existing = sb.table("blends").select("id").execute()
    existing_ids = {r["id"] for r in existing.data}

    new_blends = [b for b in blends_json if b["id"] not in existing_ids]
    if not new_blends:
        return 0

    sb.table("blends").insert(new_blends).execute()
    return len(new_blends)


def fetch_unique_clients():
    sb = get_supabase()
    result = sb.table("blends").select("client").not_.is_("client", "null").execute()
    return sorted(set(r["client"] for r in result.data if r["client"]))


def fetch_unique_farms():
    sb = get_supabase()
    result = sb.table("blends").select("farm").not_.is_("farm", "null").execute()
    return sorted(set(r["farm"] for r in result.data if r["farm"]))


def fetch_blends_by_client(client_name):
    sb = get_supabase()
    result = (sb.table("blends").select("*")
              .eq("client", client_name)
              .order("created_at", desc=True).execute())
    return result.data


def fetch_blends_by_farm(farm_name):
    sb = get_supabase()
    result = (sb.table("blends").select("*")
              .eq("farm", farm_name)
              .order("created_at", desc=True).execute())
    return result.data


# ── Pricing suggestion ─────────────────────────────────────────────────────

def _cost_per_nutrient_pct():
    """Calculate R cost to add 1% of each nutrient to a 1-ton blend,
    using the cheapest viable source from materials.xlsx.

    Returns dict like {"N": 255.6, "P": 312.5, "K": 219.0}
    """
    df = load_materials()
    cost_col = "Cost (R/ton)"
    result = {}
    for nut in ("N", "P", "K"):
        best = float("inf")
        for _, row in df.iterrows():
            pct = row.get(nut, 0)
            cost = row.get(cost_col, 0)
            # Skip compost (mixed source) and placeholder-priced materials
            if pct > 1 and 0 < cost < 500_000:
                # R to get 10kg of nutrient (= 1% of 1 ton)
                kg_needed = 10.0 / (pct / 100)
                r_cost = kg_needed * (cost / 1000)
                if r_cost < best:
                    best = r_cost
        result[nut] = round(best, 1) if best < float("inf") else 1.0
    return result


def _get_nutrient_weights():
    """Return weights proportional to R-per-% for each nutrient,
    normalised so the cheapest = 1.0."""
    cpn = _cost_per_nutrient_pct()
    min_cost = min(cpn.values())
    return {k: round(v / min_cost, 2) for k, v in cpn.items()}, cpn


def _npk_dict(nutrients_list):
    """Extract {N, P, K} actual percentages."""
    d = {"N": 0, "P": 0, "K": 0}
    for n in (nutrients_list or []):
        if n["nutrient"] in d:
            d[n["nutrient"]] = n.get("actual", 0)
    return d


def suggest_price(actual_n, actual_p, actual_k, compost_pct,
                  cost_tolerance=500, min_matches=3):
    """Look up historical blends near the given NPK profile and return
    pricing suggestions.

    Similarity is measured as a cost-weighted distance:
      distance = sum( |diff_nutrient| * R_per_%_nutrient )
    This means a 1% difference in P (expensive) counts more than
    a 1% difference in N (cheaper).

    cost_tolerance is the max acceptable distance in Rands — i.e.
    "these two blends differ by no more than R500 worth of nutrients".

    Returns dict with keys:
        found      – number of comparable blends
        low        – low-end selling price (25th percentile)
        mid        – median selling price
        high       – high-end selling price (75th percentile)
        comparables – list of dicts with blend details
        method     – 'tight' | 'widened' | 'regression'
        weights    – the R/% weights used
    or None if no data at all.
    """
    weights, cpn = _get_nutrient_weights()

    sb = get_supabase()
    all_blends = sb.table("blends").select(
        "blend_name, client, cost_per_ton, selling_price, "
        "min_compost_pct, nutrients, created_at"
    ).order("created_at", desc=True).execute().data

    if not all_blends:
        return None

    import statistics

    # ── Step 1: find comparable blends by cost-weighted distance ──────────
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

    # ── Step 2: regression fallback using ALL blends ──────────────────────
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
        import numpy as _np
        X = _np.array([[f[0], f[1], 1] for f in features_all])
        y = _np.array(prices_all)
        try:
            coeffs, _, _, _ = _np.linalg.lstsq(X, y, rcond=None)
            w_new = (actual_n * cpn["N"] + actual_p * cpn["P"]
                     + actual_k * cpn["K"])
            predicted = coeffs[0] * w_new + coeffs[1] * compost_pct + coeffs[2]
            regression = {
                "predicted": round(max(predicted, 0), 0),
                "r_per_weighted_npk": round(coeffs[0], 2),
                "r_per_compost_pct": round(coeffs[1], 0),
            }
        except Exception:
            pass

    # ── Step 3: build result ──────────────────────────────────────────────
    if not matches and regression:
        p = regression["predicted"]
        return {
            "found": 0,
            "low": round(p * 0.90),
            "mid": round(p),
            "high": round(p * 1.10),
            "comparables": [],
            "method": "regression",
            "regression": regression,
            "weights": cpn,
        }

    if not matches:
        return None

    prices = sorted(m["price"] for m in matches)

    if len(prices) == 1:
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
        "method": method,
        "regression": regression,
        "weights": cpn,
    }


# ── PDF builder ────────────────────────────────────────────────────────────
def build_pdf(blend_name, client, farm, batch, compost_pct, cost_per_ton,
              total_cost, selling_price, margin, is_relaxed, relaxed_scale,
              recipe_data, nutrient_data, sa_notation=None,
              pricing_suggestion=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Header: logo top-right, title + slogan just above orange line
    logo_h = 50
    top_margin = 10
    line_y = top_margin + logo_h + 6

    logo_path = LOGO_NO_SLOGAN_PATH if LOGO_NO_SLOGAN_PATH.exists() else LOGO_PATH
    if logo_path.exists():
        pdf.image(str(logo_path), x=200 - logo_h * 1.2, y=top_margin, h=logo_h)

    pdf.set_xy(10, line_y - 17)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(0, 12, "Blend Recipe", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(0, 5, "Fertilise Smarter, Grow Stronger", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(line_y)

    # Accent line
    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Meta info
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MED_GREY_RGB)
    meta_parts = [f"Date: {date.today().strftime('%Y-%m-%d')}"]
    if blend_name:
        meta_parts.insert(0, f"Blend: {blend_name}")
    if client:
        meta_parts.append(f"Client: {client}")
    if farm:
        meta_parts.append(f"Farm: {farm}")
    pdf.cell(0, 6, "  |  ".join(meta_parts), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # KPI summary
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MED_GREY_RGB)
    kpi_items = []
    if sa_notation:
        kpi_items.append(f"SA Notation: {sa_notation}")
    # International NPK from nutrient_data (first 3 rows are N, P, K)
    intl_parts = []
    for row in nutrient_data[:3]:
        # row = [Nutrient, Target%, Actual%, Diff, kg_per_ton]
        try:
            intl_parts.append(f"{float(row[2]):.1f}")
        except (ValueError, IndexError):
            intl_parts.append("0.0")
    if intl_parts:
        kpi_items.append(f"International: N {intl_parts[0]}% - P {intl_parts[1]}% - K {intl_parts[2]}%")
    kpi_items += [
        f"Batch size: {batch:,} kg",
        f"Compost: {compost_pct:.1f}%",
        f"Chemical: {100 - compost_pct:.1f}%",
    ]
    for item in kpi_items:
        pdf.cell(0, 5, item, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    if is_relaxed:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*ORANGE_RGB)
        pdf.cell(
            0, 5,
            f"Note: Targets relaxed to {relaxed_scale * 100:.1f}% of requested levels.",
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(2)

    def pdf_table(title, columns, widths, rows):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 9)
        header_y = pdf.get_y()
        total_w = sum(widths)
        pdf.set_fill_color(*ORANGE_RGB)
        pdf.rect(pdf.l_margin, header_y, total_w, 6, "F")
        pdf.set_text_color(255, 255, 255)
        for label, w in zip(columns, widths):
            pdf.cell(w, 6, label)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for i, row_vals in enumerate(rows):
            row_y = pdf.get_y()
            if i % 2 == 1:
                pdf.set_fill_color(*GREY_LIGHT_RGB)
                pdf.rect(pdf.l_margin, row_y, total_w, 5, "F")
            pdf.set_text_color(*DARK_GREY_RGB)
            for val, w in zip(row_vals, widths):
                pdf.cell(w, 5, val)
            pdf.ln()

        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.4)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + total_w, pdf.get_y())
        pdf.ln(4)

    # Recipe table
    recipe_cols = ["Material", "Type", "kg", "% of Blend", "Cost (R)"]
    col_widths = [60, 35, 25, 25, 25]
    pdf_table("Recipe", recipe_cols, col_widths, recipe_data)

    # Nutrient analysis table — only show targeted nutrients
    nut_cols = ["Nutrient", "Target %", "Actual %", "Diff", "kg per ton"]
    nut_widths = [30, 25, 25, 25, 25]
    targeted_rows = [r for r in nutrient_data if float(r[1]) > 0]
    pdf_table("Nutrient Analysis", nut_cols, nut_widths, targeted_rows)

    # ── Page 2: Pricing Analysis (if available) ──────────────────────────
    if pricing_suggestion and pricing_suggestion.get("found", 0) > 0:
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 12, "Pricing Analysis", new_x="LMARGIN", new_y="NEXT")

        # Accent line
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        # Method note
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MED_GREY_RGB)
        w = pricing_suggestion.get("weights", {})
        if pricing_suggestion["method"] == "tight":
            method_txt = (f"Based on {pricing_suggestion['found']} similar blends "
                          f"(within R500 cost-weighted nutrient distance)")
        elif pricing_suggestion["method"] == "widened":
            method_txt = (f"Based on {pricing_suggestion['found']} broadly similar blends "
                          f"(within R1,000 — widened due to few close matches)")
        else:
            method_txt = "Estimate from regression model using all historical blends"
        pdf.cell(0, 5, method_txt, new_x="LMARGIN", new_y="NEXT")
        if w:
            pdf.cell(0, 5,
                     f"Nutrient cost weights:  N: R{w.get('N',0):,.0f}/%   "
                     f"P: R{w.get('P',0):,.0f}/%   K: R{w.get('K',0):,.0f}/%",
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Price summary boxes
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 8, "Suggested Selling Price", new_x="LMARGIN", new_y="NEXT")

        box_y = pdf.get_y()
        box_w = 45
        box_h = 22
        gap = 3
        labels = ["Your Cost", "Low", "Mid", "High"]
        values = [
            f"R {cost_per_ton:,.0f}",
            f"R {pricing_suggestion['low']:,.0f}",
            f"R {pricing_suggestion['mid']:,.0f}",
            f"R {pricing_suggestion['high']:,.0f}",
        ]
        margins_list = [
            None,
            pricing_suggestion['low'] - cost_per_ton,
            pricing_suggestion['mid'] - cost_per_ton,
            pricing_suggestion['high'] - cost_per_ton,
        ]

        for i, (lbl, val, mgn) in enumerate(zip(labels, values, margins_list)):
            x = pdf.l_margin + i * (box_w + gap)
            # Box background
            if i == 0:
                pdf.set_fill_color(*GREY_LIGHT_RGB)
            else:
                pdf.set_fill_color(*ORANGE_FILL_RGB)
            pdf.rect(x, box_y, box_w, box_h, "F")
            # Border
            pdf.set_draw_color(*ORANGE_RGB)
            pdf.set_line_width(0.3)
            pdf.rect(x, box_y, box_w, box_h, "D")
            # Label
            pdf.set_xy(x, box_y + 2)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(box_w, 4, lbl, align="C")
            # Value
            pdf.set_xy(x, box_y + 7)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(box_w, 6, val, align="C")
            # Margin
            if mgn is not None:
                pdf.set_xy(x, box_y + 15)
                pdf.set_font("Helvetica", "", 7)
                color = (0, 130, 0) if mgn >= 0 else (200, 0, 0)
                pdf.set_text_color(*color)
                pdf.cell(box_w, 4, f"R {mgn:,.0f} margin", align="C")

        pdf.set_y(box_y + box_h + 6)

        # Regression note
        if pricing_suggestion.get("regression"):
            reg = pricing_suggestion["regression"]
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(0, 5,
                     f"Regression model estimate: R {reg['predicted']:,.0f}/ton",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        # Comparable blends table
        comps = pricing_suggestion.get("comparables", [])
        if comps:
            comp_cols = ["Blend", "Client", "Price", "Cost", "Dist.", "N%", "P%", "K%", "Date"]
            comp_widths = [38, 22, 20, 20, 16, 12, 12, 12, 22]
            comp_rows = []
            for c in comps:
                comp_rows.append([
                    str(c["blend_name"])[:22],
                    str(c.get("client", ""))[:12],
                    f"R{c['price']:,.0f}",
                    f"R{c['cost']:,.0f}",
                    f"R{c.get('distance', 0):,.0f}",
                    f"{c['npk']['N']:.1f}",
                    f"{c['npk']['P']:.1f}",
                    f"{c['npk']['K']:.1f}",
                    str(c.get("date", ""))[:10],
                ])
            pdf_table("Comparable Historical Blends", comp_cols, comp_widths,
                      comp_rows)

    elif pricing_suggestion and pricing_suggestion.get("method") == "regression":
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 12, "Pricing Analysis", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.cell(0, 6, "No close historical matches. Regression estimate:",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_GREY_RGB)
        for lbl, val in [("Low", pricing_suggestion["low"]),
                         ("Mid", pricing_suggestion["mid"]),
                         ("High", pricing_suggestion["high"])]:
            pdf.cell(0, 6, f"{lbl}: R {val:,.0f}  "
                     f"(margin R {val - cost_per_ton:,.0f})",
                     new_x="LMARGIN", new_y="NEXT")

    # Footer on last page
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(0, 5, "Generated by Sapling Blend Calculator - Internal Document",
             new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
