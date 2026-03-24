import io
import pathlib
import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog
from fpdf import FPDF
from datetime import date

_HERE = pathlib.Path(__file__).parent
LOGO_PATH = _HERE / "logo.png"
LOGO_NO_SLOGAN_PATH = _HERE / "logo_no_slogan.png"

st.set_page_config(page_title="Sapling Blend Calculator", layout="wide")

# ── Brand colours ──────────────────────────────────────────────────────────
ORANGE = "#ff4f00"
DARK_GREY = "#191919"
MED_GREY = "#4d4d4d"
ORANGE_RGB = (255, 79, 0)
DARK_GREY_RGB = (25, 25, 25)
MED_GREY_RGB = (77, 77, 77)

# Light tints derived from brand colours (for backgrounds)
ORANGE_LIGHT = "#fff3eb"     # very soft orange wash
ORANGE_FILL_RGB = (255, 243, 235)
GREY_LIGHT_RGB = (245, 245, 245)

st.markdown(f"""
<style>
    /* ── Force white background everywhere ── */
    .stApp, .main .block-container,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"] {{
        background-color: #ffffff !important;
    }}

    /* ── Sidebar — white with subtle left border ── */
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

    /* ── Headings ── */
    h1, h2, h3 {{ color: {DARK_GREY} !important; }}
    p, li, span, label {{ color: {MED_GREY}; }}

    /* ── Metric values in brand orange ── */
    [data-testid="stMetricValue"] {{
        color: {ORANGE} !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {MED_GREY} !important;
    }}

    /* ── Buttons ── */
    .stDownloadButton > button {{
        background-color: {ORANGE} !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
    }}
    .stDownloadButton > button:hover {{
        background-color: {DARK_GREY} !important;
        color: #ffffff !important;
    }}

    /* ── Expander ── */
    .streamlit-expanderHeader {{
        color: {MED_GREY} !important;
    }}

    /* ── Divider — thin orange ── */
    hr {{
        border-color: {ORANGE} !important;
        opacity: 0.4 !important;
    }}

    /* ── Slider ── */
    .stSlider [role="slider"] {{
        background-color: {ORANGE} !important;
    }}

    /* ── Dataframe / table header ── */
    [data-testid="stDataFrame"] th {{
        background-color: {ORANGE} !important;
        color: #ffffff !important;
    }}

    /* ── Number inputs & text inputs ── */
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


# ── Load materials ──────────────────────────────────────────────────────────
@st.cache_data
def load_materials():
    df = pd.read_excel(_HERE / "materials.xlsx")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    for col in df.columns:
        if col not in ["Material", "Type"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.fillna(0)


df = load_materials()
NUTRIENTS = [c for c in df.columns if c not in ["Material", "Type", "Cost (R/ton)"]]
COMPOST_NAME = "Manure Compost"

# ── Header with logo ───────────────────────────────────────────────────────
logo_col, title_col = st.columns([2, 3])
with logo_col:
    st.image(str(LOGO_PATH), width=320)
with title_col:
    st.markdown(
        f"<h1 style='margin-bottom:0; color:{DARK_GREY}'>Blend Calculator</h1>",
        unsafe_allow_html=True,
    )

# ── Sidebar: material selection ─────────────────────────────────────────────
st.sidebar.header("Raw Materials")

# Identify compost row — always included, shown as info
compost_mask = df["Material"] == COMPOST_NAME
other_materials = df[~compost_mask]

st.sidebar.markdown(f"**Base:** {COMPOST_NAME} (always included)")
st.sidebar.divider()

# Group remaining materials by type for cleaner selection
enabled = {}
for mat_type in sorted(other_materials["Type"].unique()):
    group = other_materials[other_materials["Type"] == mat_type]
    st.sidebar.subheader(mat_type)
    for _, row in group.iterrows():
        name = row["Material"]
        # Default on for common materials
        default = name in [
            "Urea 46%", "MAP 33%", "DAP",
            "KCL (Potassium Chloride)", "Gypsum",
            "KAN 28%", "Calcitic Lime",
        ]
        enabled[name] = st.sidebar.checkbox(name, value=default, key=f"mat_{name}")

# Build the working set: compost + selected materials
selected_names = [COMPOST_NAME] + [n for n, on in enabled.items() if on]
df_use = df[df["Material"].isin(selected_names)].reset_index(drop=True)

# Find compost index in df_use
compost_idx = df_use.index[df_use["Material"] == COMPOST_NAME][0]

# ── Main: blend targets ────────────────────────────────────────────────────
col_targets, col_settings = st.columns([3, 1])

with col_settings:
    st.subheader("Settings")
    batch = st.number_input("Batch size (kg)", value=1000, step=100, min_value=100)
    min_compost_pct = st.slider("Min compost %", 0, 95, 50, 5)

with col_targets:
    st.subheader("Nutrient Targets (%)")
    st.caption("Set the desired nutrient percentages in the final blend. Leave blank to ignore.")

    # Show primary nutrients (NPK) prominently
    primary = ["N", "P", "K"]
    secondary = [n for n in NUTRIENTS if n not in primary]

    targets = {}
    cols = st.columns(3)
    for i, nut in enumerate(primary):
        with cols[i]:
            targets[nut] = st.number_input(
                nut, value=None, step=0.5, min_value=0.0, max_value=60.0,
                format="%.2f", placeholder="0.00",
            )

    with st.expander("Secondary & micro nutrients"):
        cols = st.columns(5)
        for i, nut in enumerate(secondary):
            with cols[i % 5]:
                targets[nut] = st.number_input(
                    nut, value=None, step=0.1, min_value=0.0, max_value=100.0,
                    format="%.3f", placeholder="0.000",
                )

st.divider()

# ── Optimization ────────────────────────────────────────────────────────────
# Convert None to 0 for computation, track which were set
active_targets = {n: v for n, v in targets.items() if v is not None and v > 0}

if not active_targets:
    st.info("Set at least one nutrient target above to calculate a blend.")
    st.stop()


def run_optimizer(target_dict, df_mat, batch_size, compost_idx, min_compost_pct):
    """Run the LP optimizer. Returns (result, is_success)."""
    n_mats = len(df_mat)
    c = np.zeros(n_mats)
    c[compost_idx] = -1  # maximise compost

    A_eq = []
    b_eq = []
    for nut, target_pct in target_dict.items():
        row = (df_mat[nut] / 100).to_numpy()
        A_eq.append(row)
        b_eq.append(target_pct / 100 * batch_size)

    A_eq.append(np.ones(n_mats))
    b_eq.append(batch_size)

    A_eq = np.array(A_eq)
    b_eq = np.array(b_eq)

    A_ub = np.zeros((1, n_mats))
    A_ub[0, compost_idx] = -1
    b_ub = np.array([-min_compost_pct / 100 * batch_size])

    bounds = [(0, batch_size)] * n_mats

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
    return res


def find_closest_blend(target_dict, df_mat, batch_size, compost_idx, min_compost_pct):
    """Binary search for the highest achievable fraction of the original targets."""
    lo, hi = 0.0, 1.0
    best_res = None
    best_scale = 0.0

    for _ in range(30):  # binary search iterations
        mid = (lo + hi) / 2
        scaled = {n: v * mid for n, v in target_dict.items()}
        res = run_optimizer(scaled, df_mat, batch_size, compost_idx, min_compost_pct)
        if res.success:
            best_res = res
            best_scale = mid
            lo = mid
        else:
            hi = mid

    # Also try without compost minimum
    if best_res is None:
        lo2, hi2 = 0.0, 1.0
        for _ in range(30):
            mid = (lo2 + hi2) / 2
            scaled = {n: v * mid for n, v in target_dict.items()}
            res = run_optimizer(scaled, df_mat, batch_size, compost_idx, 0)
            if res.success:
                best_res = res
                best_scale = mid
                lo2 = mid
            else:
                hi2 = mid

    return best_res, best_scale


res = run_optimizer(active_targets, df_use, batch, compost_idx, min_compost_pct)

is_relaxed = False
relaxed_scale = 1.0

if not res.success:
    # Try to find the closest feasible blend
    relaxed_res, relaxed_scale = find_closest_blend(
        active_targets, df_use, batch, compost_idx, min_compost_pct
    )

    if relaxed_res is not None and relaxed_res.success:
        res = relaxed_res
        is_relaxed = True
    else:
        st.error(
            "Blend not feasible — no combination of the selected materials can "
            "achieve these nutrient targets. Try enabling more materials or "
            "adjusting your targets."
        )
        st.stop()

# ── Results ─────────────────────────────────────────────────────────────────
result = df_use.copy()
result["kg"] = np.round(res.x, 2)
result = result[result["kg"] > 0.01].copy()
result["Cost (R)"] = (result["kg"] * result["Cost (R/ton)"] / 1000).round(2)
result["% of Blend"] = (result["kg"] / batch * 100).round(1)

total_cost = result["Cost (R)"].sum()
cost_per_ton = total_cost / batch * 1000
compost_pct = result.loc[result["Material"] == COMPOST_NAME, "kg"].sum() / batch * 100

if is_relaxed:
    st.warning(
        f"**Exact targets not achievable.** Showing the closest possible blend at "
        f"**{relaxed_scale * 100:.1f}%** of your requested nutrient levels. "
        f"See the nutrient analysis below for achieved values."
    )

# KPIs
st.subheader("Blend Result")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Compost", f"{compost_pct:.1f}%")
k2.metric("Chemical", f"{100 - compost_pct:.1f}%")
k3.metric("Cost / ton", f"R {cost_per_ton:,.0f}")
k4.metric("Batch cost", f"R {total_cost:,.0f}")

# Recipe table
recipe_df = result[["Material", "Type", "kg", "% of Blend", "Cost (R)"]]
st.dataframe(recipe_df, use_container_width=True, hide_index=True)

# Nutrient comparison
st.subheader("Nutrient Analysis")
comparison = []
for nut in NUTRIENTS:
    target_pct = targets.get(nut) or 0
    actual_pct = (result[nut] / 100 * result["kg"]).sum() / batch * 100
    row = {
        "Nutrient": nut,
        "Target %": round(target_pct, 3),
        "Actual %": round(actual_pct, 3),
        "Diff": round(actual_pct - target_pct, 3),
        "kg per ton": round(actual_pct / 100 * 1000, 2),
    }
    comparison.append(row)

comp_df = pd.DataFrame(comparison)

# Highlight: active targets vs passive
active_df = comp_df[comp_df["Target %"] > 0]
passive_df = comp_df[comp_df["Target %"] == 0]

st.markdown("**Targeted nutrients**")
st.dataframe(active_df, use_container_width=True, hide_index=True)

with st.expander("All other nutrients (from compost & materials)"):
    st.dataframe(passive_df, use_container_width=True, hide_index=True)

# ── Save / Export ───────────────────────────────────────────────────────────
st.divider()

with st.expander("Save & Export"):
    col1, col2 = st.columns(2)
    with col1:
        blend_name = st.text_input("Blend name", placeholder="e.g. Citrus 3-1-5")
        client = st.text_input("Client", placeholder="Optional")
    with col2:
        farm = st.text_input("Farm", placeholder="Optional")
        selling_price = st.number_input("Selling price (R/ton)", value=0.0, step=100.0)

    margin = selling_price - cost_per_ton if selling_price > 0 else None

    if margin is not None:
        st.metric("Margin", f"R {margin:,.0f} / ton")

    # CSV download
    export = result[["Material", "Type", "kg", "% of Blend", "Cost (R)"]].copy()
    csv = export.to_csv(index=False)
    st.download_button("Download blend as CSV", csv, "blend.csv", "text/csv")

    # PDF download
    def build_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)

        # Logo + Title header
        logo_h = 37
        if LOGO_NO_SLOGAN_PATH.exists():
            pdf.image(str(LOGO_NO_SLOGAN_PATH), x=10, y=10, h=logo_h)
        elif LOGO_PATH.exists():
            pdf.image(str(LOGO_PATH), x=10, y=10, h=logo_h)
        pdf.set_xy(55, 14)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 12, "Blend Recipe", new_x="LMARGIN", new_y="NEXT")
        pdf.set_xy(55, 28)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.cell(0, 5, "Fertilise Smarter, Grow Stronger", new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(10 + logo_h + 6)

        # Accent line in brand orange
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
        kpi_items = [
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

        # ── Helper: branded table ──
        def pdf_table(title, columns, widths, rows):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

            # Header row — orange background, white text
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(*ORANGE_RGB)
            pdf.set_text_color(255, 255, 255)
            pdf.set_draw_color(*ORANGE_RGB)
            for label, w in zip(columns, widths):
                pdf.cell(w, 6, label, border=1, fill=True)
            pdf.ln()

            # Data rows — alternating white / light grey
            pdf.set_font("Helvetica", "", 9)
            pdf.set_draw_color(220, 220, 220)
            for i, row_vals in enumerate(rows):
                if i % 2 == 1:
                    pdf.set_fill_color(*GREY_LIGHT_RGB)
                    fill = True
                else:
                    pdf.set_fill_color(255, 255, 255)
                    fill = True
                pdf.set_text_color(*DARK_GREY_RGB)
                for val, w in zip(row_vals, widths):
                    pdf.cell(w, 5, val, border="LR", fill=fill)
                pdf.ln()

            # Bottom border
            pdf.set_draw_color(*ORANGE_RGB)
            pdf.set_line_width(0.4)
            total_w = sum(widths)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + total_w, pdf.get_y())
            pdf.ln(4)

        # Recipe table
        recipe_cols = ["Material", "Type", "kg", "% of Blend", "Cost (R)"]
        col_widths = [60, 35, 25, 25, 25]
        recipe_rows = []
        for _, r in result.iterrows():
            recipe_rows.append([
                str(r["Material"]),
                str(r["Type"]),
                f"{r['kg']:.1f}",
                f"{r['% of Blend']:.1f}",
                f"{r['Cost (R)']:.2f}",
            ])
        pdf_table("Recipe", recipe_cols, col_widths, recipe_rows)

        # Nutrient analysis table
        nut_cols = ["Nutrient", "Target %", "Actual %", "Diff", "kg per ton"]
        nut_widths = [30, 25, 25, 25, 25]
        nut_rows = []
        for _, r in comp_df.iterrows():
            nut_rows.append([
                str(r["Nutrient"]),
                f"{r['Target %']:.3f}",
                f"{r['Actual %']:.3f}",
                f"{r['Diff']:.3f}",
                f"{r['kg per ton']:.2f}",
            ])
        pdf_table("Nutrient Analysis", nut_cols, nut_widths, nut_rows)

        # Footer
        pdf.ln(8)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.cell(0, 5, "Generated by Sapling Blend Calculator", new_x="LMARGIN", new_y="NEXT")

        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    pdf_bytes = build_pdf()
    filename = f"{blend_name or 'blend'}.pdf".replace(" ", "_")
    st.download_button(
        "Download blend as PDF", pdf_bytes, filename, "application/pdf",
    )
