import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog
from shared import (
    apply_styles, show_header, load_materials, build_pdf, save_blend,
    sa_notation_to_pct, pct_to_sa_notation,
    DARK_GREY, MED_GREY, COMPOST_NAME,
)

st.set_page_config(page_title="Sapling Blend Calculator", layout="wide")
apply_styles()

df = load_materials()
NUTRIENTS = [c for c in df.columns if c not in ["Material", "Type", "Cost (R/ton)"]]

# ── Header with logo ───────────────────────────────────────────────────────
show_header()

# ── Sidebar: material selection ─────────────────────────────────────────────
st.sidebar.header("Raw Materials")

compost_mask = df["Material"] == COMPOST_NAME
other_materials = df[~compost_mask]

st.sidebar.markdown(f"**Base:** {COMPOST_NAME} (always included)")
st.sidebar.divider()

enabled = {}
for mat_type in sorted(other_materials["Type"].unique()):
    group = other_materials[other_materials["Type"] == mat_type]
    st.sidebar.subheader(mat_type)
    for _, row in group.iterrows():
        name = row["Material"]
        default = name in [
            "Urea 46%", "MAP 33%", "DAP",
            "KCL (Potassium Chloride)", "Gypsum",
            "KAN 28%", "Calcitic Lime",
        ]
        enabled[name] = st.sidebar.checkbox(name, value=default, key=f"mat_{name}")

selected_names = [COMPOST_NAME] + [n for n, on in enabled.items() if on]
df_use = df[df["Material"].isin(selected_names)].reset_index(drop=True)
compost_idx = df_use.index[df_use["Material"] == COMPOST_NAME][0]

# ── Main: blend targets ────────────────────────────────────────────────────
col_targets, col_settings = st.columns([3, 1])

with col_settings:
    st.subheader("Settings")
    batch = st.number_input("Batch size (kg)", value=1000, step=100, min_value=100)
    min_compost_pct = st.slider("Min compost %", 0, 95, 50, 5)

primary = ["N", "P", "K"]
secondary = [n for n in NUTRIENTS if n not in primary]

with col_targets:
    st.subheader("Nutrient Targets")
    input_mode = st.radio(
        "Input format",
        ["International (NPK %)", "SA Local (ratio & total)"],
        horizontal=True,
    )

    targets = {}

    if input_mode == "International (NPK %)":
        st.caption("Set the desired nutrient percentages in the final blend. Leave blank to ignore.")
        cols = st.columns(3)
        for i, nut in enumerate(primary):
            with cols[i]:
                targets[nut] = st.number_input(
                    nut, value=None, step=0.5, min_value=0.0, max_value=60.0,
                    format="%.2f", placeholder="0.00", key=f"intl_{nut}",
                )
    else:
        st.caption("Enter the NPK ratio and total %. e.g. 2:3:2 (22) → N=6.3%, P=9.4%, K=6.3%")
        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            sa_n = st.number_input("N ratio", value=None, min_value=0, step=1,
                                   placeholder="e.g. 2", key="sa_n")
        with rc2:
            sa_p = st.number_input("P ratio", value=None, min_value=0, step=1,
                                   placeholder="e.g. 3", key="sa_p")
        with rc3:
            sa_k = st.number_input("K ratio", value=None, min_value=0, step=1,
                                   placeholder="e.g. 2", key="sa_k")
        with rc4:
            sa_total = st.number_input("Total %", value=None, min_value=0.0,
                                       max_value=100.0, step=1.0,
                                       placeholder="e.g. 22", key="sa_total")

        if sa_n is not None and sa_p is not None and sa_k is not None and sa_total is not None:
            n_pct, p_pct, k_pct = sa_notation_to_pct(sa_n, sa_p, sa_k, sa_total)
            st.info(f"**{sa_n}:{sa_p}:{sa_k} ({sa_total:.0f})** → N: {n_pct:.2f}%  |  P: {p_pct:.2f}%  |  K: {k_pct:.2f}%")
            targets["N"] = n_pct if n_pct > 0 else None
            targets["P"] = p_pct if p_pct > 0 else None
            targets["K"] = k_pct if k_pct > 0 else None
        else:
            targets["N"] = None
            targets["P"] = None
            targets["K"] = None

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
active_targets = {n: v for n, v in targets.items() if v is not None and v > 0}

if not active_targets:
    st.info("Set at least one nutrient target above to calculate a blend.")
    st.stop()


def run_optimizer(target_dict, df_mat, batch_size, c_idx, min_pct):
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
    lo, hi, best_res, best_scale = 0.0, 1.0, None, 0.0
    for _ in range(30):
        mid = (lo + hi) / 2
        scaled = {n: v * mid for n, v in target_dict.items()}
        res = run_optimizer(scaled, df_mat, batch_size, c_idx, min_pct)
        if res.success:
            best_res, best_scale, lo = res, mid, mid
        else:
            hi = mid
    if best_res is None:
        lo2, hi2 = 0.0, 1.0
        for _ in range(30):
            mid = (lo2 + hi2) / 2
            scaled = {n: v * mid for n, v in target_dict.items()}
            res = run_optimizer(scaled, df_mat, batch_size, c_idx, 0)
            if res.success:
                best_res, best_scale, lo2 = res, mid, mid
            else:
                hi2 = mid
    return best_res, best_scale


res = run_optimizer(active_targets, df_use, batch, compost_idx, min_compost_pct)
is_relaxed = False
relaxed_scale = 1.0

if not res.success:
    relaxed_res, relaxed_scale = find_closest_blend(
        active_targets, df_use, batch, compost_idx, min_compost_pct
    )
    if relaxed_res is not None and relaxed_res.success:
        res, is_relaxed = relaxed_res, True
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

# Compute actual NPK for SA notation output
actual_n = (result["N"] / 100 * result["kg"]).sum() / batch * 100 if "N" in result.columns else 0
actual_p = (result["P"] / 100 * result["kg"]).sum() / batch * 100 if "P" in result.columns else 0
actual_k = (result["K"] / 100 * result["kg"]).sum() / batch * 100 if "K" in result.columns else 0
sa_label = pct_to_sa_notation(actual_n, actual_p, actual_k)

st.subheader("Blend Result")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("SA Notation", sa_label)
k2.metric("Compost", f"{compost_pct:.1f}%")
k3.metric("Chemical", f"{100 - compost_pct:.1f}%")
k4.metric("Cost / ton", f"R {cost_per_ton:,.0f}")
k5.metric("Batch cost", f"R {total_cost:,.0f}")

recipe_df = result[["Material", "Type", "kg", "% of Blend", "Cost (R)"]]
st.dataframe(recipe_df, use_container_width=True, hide_index=True)

# Nutrient comparison
st.subheader("Nutrient Analysis")
comparison = []
for nut in NUTRIENTS:
    target_pct = targets.get(nut) or 0
    actual_pct = (result[nut] / 100 * result["kg"]).sum() / batch * 100
    comparison.append({
        "Nutrient": nut,
        "Target %": round(target_pct, 3),
        "Actual %": round(actual_pct, 3),
        "Diff": round(actual_pct - target_pct, 3),
        "g/kg": round(actual_pct * 10, 2),
        "kg per ton": round(actual_pct / 100 * 1000, 2),
    })

comp_df = pd.DataFrame(comparison)
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
        blend_name = st.text_input("Blend name *", placeholder="e.g. Citrus 3-1-5")
        client = st.text_input("Client *", placeholder="e.g. Smith Farms")
    with col2:
        farm = st.text_input("Farm", placeholder="Optional")
        selling_price = st.number_input("Selling price (R/ton)", value=0.0, step=100.0)

    margin = selling_price - cost_per_ton if selling_price > 0 else None

    if margin is not None:
        st.metric("Margin", f"R {margin:,.0f} / ton")

    # Check required fields
    can_save = bool(blend_name and client)
    if not can_save:
        st.warning("Blend name and Client are required to save or download.")

    # Prepare data for PDF and saving
    recipe_rows = []
    for _, r in result.iterrows():
        recipe_rows.append([
            str(r["Material"]), str(r["Type"]),
            f"{r['kg']:.1f}", f"{r['% of Blend']:.1f}", f"{r['Cost (R)']:.2f}",
        ])

    nutrient_rows = []
    for _, r in comp_df.iterrows():
        nutrient_rows.append([
            str(r["Nutrient"]), f"{r['Target %']:.3f}",
            f"{r['Actual %']:.3f}", f"{r['Diff']:.3f}", f"{r['kg per ton']:.2f}",
        ])

    btn_cols = st.columns(2)

    # PDF download
    with btn_cols[0]:
        if can_save:
            pdf_bytes = build_pdf(
                blend_name, client, farm, batch, compost_pct, cost_per_ton,
                total_cost, selling_price, margin, is_relaxed, relaxed_scale,
                recipe_rows, nutrient_rows, sa_notation=sa_label,
            )
            filename = f"{blend_name}_{client}.pdf".replace(" ", "_")
            st.download_button("Download PDF", pdf_bytes, filename, "application/pdf")

    # Save to database
    with btn_cols[1]:
        if can_save and st.button("Save to Database"):
            # Build JSON-friendly data for storage
            recipe_json = []
            for _, r in result.iterrows():
                recipe_json.append({
                    "material": str(r["Material"]),
                    "type": str(r["Type"]),
                    "kg": round(float(r["kg"]), 2),
                    "pct": round(float(r["% of Blend"]), 1),
                    "cost": round(float(r["Cost (R)"]), 2),
                })
            nutrient_json = []
            for _, r in comp_df.iterrows():
                nutrient_json.append({
                    "nutrient": str(r["Nutrient"]),
                    "target": round(float(r["Target %"]), 3),
                    "actual": round(float(r["Actual %"]), 3),
                    "diff": round(float(r["Diff"]), 3),
                    "kg_per_ton": round(float(r["kg per ton"]), 2),
                })
            target_json = {n: v for n, v in targets.items() if v is not None and v > 0}

            try:
                save_blend(
                    blend_name, client, farm, batch, min_compost_pct,
                    selling_price, cost_per_ton, target_json,
                    recipe_json, nutrient_json, selected_names,
                )
                st.success("Blend saved!")
            except Exception as e:
                st.error(f"Failed to save: {e}")
