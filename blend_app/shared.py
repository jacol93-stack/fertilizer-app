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


def show_header():
    logo_col, title_col = st.columns([2, 3])
    with logo_col:
        st.image(str(LOGO_PATH), width=320)
    with title_col:
        st.markdown(
            f"<h1 style='margin-bottom:0; color:{DARK_GREY}'>Blend Calculator</h1>",
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


# ── PDF builder ────────────────────────────────────────────────────────────
def build_pdf(blend_name, client, farm, batch, compost_pct, cost_per_ton,
              total_cost, selling_price, margin, is_relaxed, relaxed_scale,
              recipe_data, nutrient_data, sa_notation=None):
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
    kpi_items += [
        f"Batch size: {batch:,} kg",
        f"Compost: {compost_pct:.1f}%",
        f"Chemical: {100 - compost_pct:.1f}%",
        f"Cost per ton: R {cost_per_ton:,.0f}",
        f"Batch cost: R {total_cost:,.0f}",
    ]
    if margin is not None:
        kpi_items.append(f"Selling price: R {selling_price:,.0f} / ton")
        kpi_items.append(f"Margin: R {margin:,.0f} / ton")
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

    # Nutrient analysis table
    nut_cols = ["Nutrient", "Target %", "Actual %", "Diff", "kg per ton"]
    nut_widths = [30, 25, 25, 25, 25]
    pdf_table("Nutrient Analysis", nut_cols, nut_widths, nutrient_data)

    # Footer
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(0, 5, "Generated by Sapling Blend Calculator", new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
