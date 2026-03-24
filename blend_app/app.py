import pathlib
import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

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
    st.caption("Set the desired nutrient percentages in the final blend. Leave at 0 to ignore.")

    # Show primary nutrients (NPK) prominently
    primary = ["N", "P", "K"]
    secondary = [n for n in NUTRIENTS if n not in primary]

    targets = {}
    cols = st.columns(3)
    for i, nut in enumerate(primary):
        with cols[i]:
            targets[nut] = st.number_input(
                nut, value=0.0, step=0.5, min_value=0.0, max_value=60.0, format="%.2f"
            )

    with st.expander("Secondary & micro nutrients"):
        cols = st.columns(5)
        for i, nut in enumerate(secondary):
            with cols[i % 5]:
                targets[nut] = st.number_input(
                    nut, value=0.0, step=0.1, min_value=0.0, max_value=100.0,
                    format="%.3f",
                )

st.divider()

# ── Optimization ────────────────────────────────────────────────────────────
active_targets = {n: v for n, v in targets.items() if v > 0}

if not active_targets:
    st.info("Set at least one nutrient target above to calculate a blend.")
    st.stop()

# Build LP: maximise compost  ⟹  minimise -compost
n_mats = len(df_use)

# Objective: minimise c·x  where c = 0 everywhere except compost index = -1
c = np.zeros(n_mats)
c[compost_idx] = -1  # maximise compost

# Equality constraints: nutrient targets + total = batch
A_eq = []
b_eq = []

for nut, target_pct in active_targets.items():
    row = (df_use[nut] / 100).to_numpy()
    A_eq.append(row)
    b_eq.append(target_pct / 100 * batch)

# Sum of all materials = batch
A_eq.append(np.ones(n_mats))
b_eq.append(batch)

A_eq = np.array(A_eq)
b_eq = np.array(b_eq)

# Inequality constraint: compost >= min_compost_pct% of batch
# -x_compost <= -min_compost_pct/100 * batch
A_ub = np.zeros((1, n_mats))
A_ub[0, compost_idx] = -1
b_ub = np.array([-min_compost_pct / 100 * batch])

bounds = [(0, batch)] * n_mats

res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds)

if not res.success:
    # Try without compost minimum to diagnose
    res_relaxed = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds)

    if res_relaxed.success:
        compost_kg = res_relaxed.x[compost_idx]
        max_compost_pct = compost_kg / batch * 100
        st.error(
            f"Cannot achieve {min_compost_pct}% compost with these targets. "
            f"Maximum possible compost is **{max_compost_pct:.1f}%**. "
            f"Lower the minimum compost % or adjust nutrient targets."
        )
    else:
        # Check which nutrients are impossible
        limiting = []
        for nut, target_pct in active_targets.items():
            max_possible = (df_use[nut] / 100).sum() * batch  # if 100% of each material
            required = target_pct / 100 * batch
            if max_possible < required:
                limiting.append(nut)

        if limiting:
            st.error(
                f"Blend not feasible. These nutrients cannot be reached with selected materials: "
                f"**{', '.join(limiting)}**"
            )
        else:
            st.error(
                "Blend not feasible — the combination of nutrient targets "
                "is impossible with the selected materials. Try enabling more materials."
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

# KPIs
st.subheader("Blend Result")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Compost", f"{compost_pct:.1f}%")
k2.metric("Chemical", f"{100 - compost_pct:.1f}%")
k3.metric("Cost / ton", f"R {cost_per_ton:,.0f}")
k4.metric("Batch cost", f"R {total_cost:,.0f}")

# Recipe table
st.dataframe(
    result[["Material", "Type", "kg", "% of Blend", "Cost (R)"]],
    use_container_width=True,
    hide_index=True,
)

# Nutrient comparison
st.subheader("Nutrient Analysis")
comparison = []
for nut in NUTRIENTS:
    target_pct = targets.get(nut, 0)
    actual_pct = (result[nut] / 100 * result["kg"]).sum() / batch * 100
    row = {
        "Nutrient": nut,
        "Target %": round(target_pct, 3),
        "Actual %": round(actual_pct, 3),
        "Diff": round(actual_pct - target_pct, 3),
    }
    # Only show kg/ton for context
    row["kg per ton"] = round(actual_pct / 100 * 1000, 2)
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
