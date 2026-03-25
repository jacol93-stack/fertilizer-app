import streamlit as st
import pandas as pd
import numpy as np
from shared import (
    apply_styles, show_header, show_mobile_nav, load_materials, load_materials_with_markup,
    build_pdf, save_blend,
    sa_notation_to_pct, pct_to_sa_notation, suggest_price,
    run_optimizer, find_closest_blend,
    DARK_GREY, MED_GREY, COMPOST_NAME,
)
from auth import require_auth, logout_button, is_admin

st.set_page_config(page_title="Sapling Blend Calculator", layout="wide")
apply_styles()

# ── Auth ──────────────────────────────────────────────────────────────────
name, role, username = require_auth()
logout_button()
show_mobile_nav("Blend_Calculator")

df = load_materials_with_markup(role)
NUTRIENTS = [c for c in df.columns if c not in ["Material", "Type", "Cost (R/ton)"]]

# ── Persist widget values across page navigation ─────────────────────────
if "bc_data" not in st.session_state:
    st.session_state["bc_data"] = {}

_DEFAULT_MATS = {
    "Urea 46%", "MAP 33%", "DAP",
    "KCL (Potassium Chloride)", "Gypsum",
    "KAN 28%", "Calcitic Lime",
}

# Restore saved material selections before widgets render
for _, row in df.iterrows():
    name = row["Material"]
    if name == COMPOST_NAME:
        continue
    wkey = f"mat_{name}"
    if wkey not in st.session_state and wkey in st.session_state["bc_data"]:
        st.session_state[wkey] = st.session_state["bc_data"][wkey]

# Restore other BC widget keys
for _k in ["bc_batch", "bc_compost", "bc_input_mode", "bc_blend_name",
            "bc_client", "bc_farm", "bc_selling_price",
            "intl_N", "intl_P", "intl_K", "sa_n", "sa_p", "sa_k", "sa_total"]:
    if _k not in st.session_state and _k in st.session_state["bc_data"]:
        st.session_state[_k] = st.session_state["bc_data"][_k]
for nut in [c for c in df.columns if c not in ["Material", "Type", "Cost (R/ton)", "N", "P", "K"]]:
    _k = f"bc_sec_{nut}"
    if _k not in st.session_state and _k in st.session_state["bc_data"]:
        st.session_state[_k] = st.session_state["bc_data"][_k]

def _save_bc_state():
    """Snapshot current widget values into the persistent mirror."""
    _bc = st.session_state["bc_data"]
    for _, row in df.iterrows():
        name = row["Material"]
        if name == COMPOST_NAME:
            continue
        wkey = f"mat_{name}"
        if wkey in st.session_state:
            _bc[wkey] = st.session_state[wkey]
    for _k in ["bc_batch", "bc_compost", "bc_input_mode", "bc_blend_name",
                "bc_client", "bc_farm", "bc_selling_price",
                "intl_N", "intl_P", "intl_K", "sa_n", "sa_p", "sa_k", "sa_total"]:
        if _k in st.session_state:
            _bc[_k] = st.session_state[_k]
    for nut in [c for c in df.columns if c not in ["Material", "Type", "Cost (R/ton)", "N", "P", "K"]]:
        _k = f"bc_sec_{nut}"
        if _k in st.session_state:
            _bc[_k] = st.session_state[_k]

# ── Header with logo ───────────────────────────────────────────────────────
show_header()

# ── Sidebar: material selection (admin only) ──────────────────────────────
compost_mask = df["Material"] == COMPOST_NAME
other_materials = df[~compost_mask]

if is_admin():
    st.sidebar.header("Raw Materials")
    st.sidebar.markdown(f"**Base:** {COMPOST_NAME} (always included)")
    st.sidebar.divider()

    enabled = {}
    for mat_type in sorted(other_materials["Type"].unique()):
        group = other_materials[other_materials["Type"] == mat_type]
        st.sidebar.subheader(mat_type)
        for _, row in group.iterrows():
            mat_name = row["Material"]
            default = mat_name in _DEFAULT_MATS
            enabled[mat_name] = st.sidebar.checkbox(mat_name, value=default,
                                                     key=f"mat_{mat_name}")
    selected_names = [COMPOST_NAME] + [n for n, on in enabled.items() if on]
else:
    # Agents use all default materials — no selection UI
    selected_names = [COMPOST_NAME] + list(_DEFAULT_MATS)

df_use = df[df["Material"].isin(selected_names)].reset_index(drop=True)
compost_idx = df_use.index[df_use["Material"] == COMPOST_NAME][0]

# ── Main: blend targets ────────────────────────────────────────────────────
col_targets, col_settings = st.columns([3, 1])

with col_settings:
    st.subheader("Settings")
    batch = st.number_input("Batch size (kg)", value=1000, step=100, min_value=100,
                            key="bc_batch")
    min_compost_pct = st.slider("Min compost %", 0, 95, 50, 5, key="bc_compost")

primary = ["N", "P", "K"]
secondary = [n for n in NUTRIENTS if n not in primary]

with col_targets:
    st.subheader("Nutrient Targets")
    input_mode = st.radio(
        "Input format",
        ["International (NPK %)", "SA Local (ratio & total)"],
        horizontal=True, key="bc_input_mode",
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
                    format="%.3f", placeholder="0.000", key=f"bc_sec_{nut}",
                )

st.divider()

# ── Optimization ────────────────────────────────────────────────────────────
active_targets = {n: v for n, v in targets.items() if v is not None and v > 0}

if not active_targets:
    st.info("Set at least one nutrient target above to calculate a blend.")
    _save_bc_state()
    st.stop()



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
        _save_bc_state()
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

intl_label = f"N {actual_n:.1f}%  |  P {actual_p:.1f}%  |  K {actual_k:.1f}%"

st.markdown(
    f"**SA Notation:** {sa_label}  \n"
    f"**International:** {intl_label}  \n"
    f"**Compost:** {compost_pct:.1f}%"
)

if is_admin():
    k1, k2 = st.columns(2)
    k1.metric("Cost / ton", f"R {cost_per_ton:,.0f}")
    k2.metric("Batch cost", f"R {total_cost:,.0f}")

    recipe_df = result[["Material", "Type", "kg", "% of Blend", "Cost (R)"]]
    st.dataframe(recipe_df, use_container_width=True, hide_index=True)
else:
    st.metric("Estimated Price / ton", f"R {cost_per_ton:,.0f}")

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

# ── Pricing Suggestion (admin only) ───────────────────────────────────────
suggestion = None
if is_admin():
    st.divider()
    st.subheader("Suggested Selling Price")

    suggestion = suggest_price(actual_n, actual_p, actual_k, compost_pct)

    if suggestion is None:
        st.info("No historical blend data available for pricing suggestions.")
    else:
        w = suggestion.get("weights", {})
        w_note = (f"N: R{w.get('N',0):,.0f}/%  ·  "
                  f"P: R{w.get('P',0):,.0f}/%  ·  "
                  f"K: R{w.get('K',0):,.0f}/%" if w else "")

        if suggestion["method"] == "tight":
            st.caption(
                f"Based on **{suggestion['found']}** similar blends "
                f"(within R500 cost-weighted nutrient distance)  \n"
                f"Nutrient weights from current material prices — {w_note}"
            )
        elif suggestion["method"] == "widened":
            st.caption(
                f"Based on **{suggestion['found']}** broadly similar blends "
                f"(within R1,000 — widened due to few close matches)  \n"
                f"Nutrient weights from current material prices — {w_note}"
            )
        else:
            st.caption(
                f"No close matches found — estimate from regression model "
                f"using all historical blends  \n"
                f"Nutrient weights from current material prices — {w_note}"
            )

        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("Your Cost", f"R {cost_per_ton:,.0f}")
        pc2.metric("Low", f"R {suggestion['low']:,.0f}",
                   delta=f"R {suggestion['low'] - cost_per_ton:,.0f} margin",
                   delta_color="normal")
        pc3.metric("Mid", f"R {suggestion['mid']:,.0f}",
                   delta=f"R {suggestion['mid'] - cost_per_ton:,.0f} margin",
                   delta_color="normal")
        pc4.metric("High", f"R {suggestion['high']:,.0f}",
                   delta=f"R {suggestion['high'] - cost_per_ton:,.0f} margin",
                   delta_color="normal")

    if suggestion.get("regression"):
        reg = suggestion["regression"]
        st.caption(
            f"Model estimate: **R {reg['predicted']:,.0f}**/ton  "
            f"(R {reg['r_per_weighted_npk']:,.0f} per weighted NPK unit, "
            f"R {reg['r_per_compost_pct']:,.0f} per % compost)"
        )

    if suggestion["comparables"]:
        with st.expander(f"View {len(suggestion['comparables'])} comparable blends"):
            comp_rows = []
            for c in suggestion["comparables"]:
                comp_rows.append({
                    "Blend": c["blend_name"],
                    "Client": c["client"],
                    "Price (R/ton)": f"R {c['price']:,.0f}",
                    "Cost (R/ton)": f"R {c['cost']:,.0f}",
                    "Distance (R)": f"R {c.get('distance', 0):,.0f}",
                    "Compost %": f"{c['compost_pct']}%",
                    "N%": f"{c['npk']['N']:.1f}",
                    "P%": f"{c['npk']['P']:.1f}",
                    "K%": f"{c['npk']['K']:.1f}",
                    "Date": c["date"],
                })
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True,
                         hide_index=True)

# ── Save / Export ───────────────────────────────────────────────────────────
st.divider()

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

if is_admin():
    # ── Admin: full save & export ─────────────────────────────────────────
    with st.expander("Save & Export"):
        col1, col2 = st.columns(2)
        with col1:
            blend_name = st.text_input("Blend name *", placeholder="e.g. Citrus 3-1-5",
                                       key="bc_blend_name")
            client = st.text_input("Client *", placeholder="e.g. Smith Farms",
                                   key="bc_client")
        with col2:
            farm = st.text_input("Farm", placeholder="Optional", key="bc_farm")
            selling_price = st.number_input("Selling price (R/ton)", value=0.0, step=100.0,
                                             key="bc_selling_price")

        margin = selling_price - cost_per_ton if selling_price > 0 else None

        if margin is not None:
            st.metric("Margin", f"R {margin:,.0f} / ton")

        can_save = bool(blend_name and client)
        if not can_save:
            st.warning("Blend name and Client are required to save or download.")

        btn_cols = st.columns(2)
        with btn_cols[0]:
            if can_save:
                pdf_bytes = build_pdf(
                    blend_name, client, farm, batch, compost_pct, cost_per_ton,
                    total_cost, selling_price, margin, is_relaxed, relaxed_scale,
                    recipe_rows, nutrient_rows, sa_notation=sa_label,
                    pricing_suggestion=suggestion,
                )
                filename = f"{blend_name}_{client}.pdf".replace(" ", "_")
                st.download_button("Download PDF", pdf_bytes, filename,
                                   "application/pdf")

        with btn_cols[1]:
            if can_save and st.button("Save to Database"):
                try:
                    save_blend(
                        blend_name, client, farm, batch, min_compost_pct,
                        selling_price, cost_per_ton, target_json,
                        recipe_json, nutrient_json, selected_names,
                        created_by=username,
                    )
                    st.success("Blend saved!")
                except Exception as e:
                    st.error(f"Failed to save: {e}")
else:
    # ── Agent: required fields, auto-save, no raw costs in PDF ────────────
    st.subheader("Save Blend")
    col1, col2 = st.columns(2)
    with col1:
        blend_name = st.text_input("Blend name *", placeholder="e.g. Citrus 3-1-5",
                                   key="bc_blend_name")
        client = st.text_input("Client *", placeholder="e.g. Smith Farms",
                               key="bc_client")
    with col2:
        farm = st.text_input("Farm *", placeholder="e.g. Greenfield Estate",
                             key="bc_farm")

    can_save = bool(blend_name and client and farm)
    if not can_save:
        st.warning("Blend name, Client, and Farm are required.")

    if can_save:
        # Agent PDF — no recipe details, no raw costs
        agent_nutrient_rows = [
            [str(r["Nutrient"]), f"{r['Target %']:.3f}",
             f"{r['Actual %']:.3f}", f"{r['Diff']:.3f}", f"{r['kg per ton']:.2f}"]
            for _, r in comp_df.iterrows()
        ]
        pdf_bytes = build_pdf(
            blend_name, client, farm, batch, compost_pct, cost_per_ton,
            total_cost, 0, None, is_relaxed, relaxed_scale,
            [], agent_nutrient_rows, sa_notation=sa_label,
        )
        filename = f"{blend_name}_{client}.pdf".replace(" ", "_")
        st.download_button("Download PDF", pdf_bytes, filename,
                           "application/pdf")

        # Auto-save
        if st.button("Save to Database", key="agent_save_blend"):
            try:
                save_blend(
                    blend_name, client, farm, batch, min_compost_pct,
                    0, cost_per_ton, target_json,
                    recipe_json, nutrient_json, selected_names,
                    created_by=username,
                )
                st.success("Blend saved!")
            except Exception as e:
                st.error(f"Failed to save: {e}")

_save_bc_state()
