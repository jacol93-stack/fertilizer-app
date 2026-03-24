import io
import pathlib
import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog
from fpdf import FPDF
from datetime import date

_HERE = pathlib.Path(__file__).parent

st.set_page_config(page_title="Blend Calculator", layout="wide")


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

st.title("Blend Calculator")

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

        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, "Blend Recipe", new_x="LMARGIN", new_y="NEXT")

        # Meta info
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        meta_parts = [f"Date: {date.today().strftime('%Y-%m-%d')}"]
        if blend_name:
            meta_parts.insert(0, f"Blend: {blend_name}")
        if client:
            meta_parts.append(f"Client: {client}")
        if farm:
            meta_parts.append(f"Farm: {farm}")
        pdf.cell(0, 6, "  |  ".join(meta_parts), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

        # KPI summary
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
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
            pdf.set_text_color(180, 80, 0)
            pdf.cell(
                0, 5,
                f"Note: Targets relaxed to {relaxed_scale * 100:.1f}% of requested levels.",
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

        # Recipe table
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Recipe", new_x="LMARGIN", new_y="NEXT")

        recipe_cols = ["Material", "Type", "kg", "% of Blend", "Cost (R)"]
        col_widths = [60, 35, 25, 25, 25]

        # Header
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        for label, w in zip(recipe_cols, col_widths):
            pdf.cell(w, 6, label, border=1, fill=True)
        pdf.ln()

        # Rows
        pdf.set_font("Helvetica", "", 9)
        for _, r in result.iterrows():
            vals = [
                str(r["Material"]),
                str(r["Type"]),
                f"{r['kg']:.1f}",
                f"{r['% of Blend']:.1f}",
                f"{r['Cost (R)']:.2f}",
            ]
            for val, w in zip(vals, col_widths):
                pdf.cell(w, 5, val, border=1)
            pdf.ln()
        pdf.ln(4)

        # Nutrient analysis table
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Nutrient Analysis", new_x="LMARGIN", new_y="NEXT")

        nut_cols = ["Nutrient", "Target %", "Actual %", "Diff", "kg per ton"]
        nut_widths = [30, 25, 25, 25, 25]

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        for label, w in zip(nut_cols, nut_widths):
            pdf.cell(w, 6, label, border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for _, r in comp_df.iterrows():
            vals = [
                str(r["Nutrient"]),
                f"{r['Target %']:.3f}",
                f"{r['Actual %']:.3f}",
                f"{r['Diff']:.3f}",
                f"{r['kg per ton']:.2f}",
            ]
            for val, w in zip(vals, nut_widths):
                pdf.cell(w, 5, val, border=1)
            pdf.ln()

        # Footer
        pdf.ln(8)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(140, 140, 140)
        pdf.cell(0, 5, "Generated by Blend Calculator", new_x="LMARGIN", new_y="NEXT")

        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    pdf_bytes = build_pdf()
    filename = f"{blend_name or 'blend'}.pdf".replace(" ", "_")
    st.download_button(
        "Download blend as PDF", pdf_bytes, filename, "application/pdf",
    )
