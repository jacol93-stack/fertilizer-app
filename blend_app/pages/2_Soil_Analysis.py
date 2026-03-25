import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from shared import (
    apply_styles, show_header, show_mobile_nav, load_materials, load_materials_with_markup,
    load_soil_norms,
    classify_soil_value, calculate_nutrient_targets, evaluate_ratios,
    build_soil_pdf, run_optimizer, find_closest_blend,
    save_soil_analysis,
    NUTRIENTS_SOIL, CLASSIFICATION_COLOURS,
    SOIL_NORMS_PATH, DARK_GREY, MED_GREY, ORANGE, COMPOST_NAME,
    sa_notation_to_pct, pct_to_sa_notation,
)
from auth import require_auth, logout_button, is_admin

st.set_page_config(page_title="Soil Analysis — Sapling", layout="wide")
apply_styles()

# ── Auth ──────────────────────────────────────────────────────────────────
auth_name, role, username = require_auth()
logout_button()
show_mobile_nav("Soil_Analysis")

show_header("Soil Analysis & Recommendations")

# ── Check norms file exists ───────────────────────────────────────────────
if not SOIL_NORMS_PATH.exists():
    st.error(
        f"Soil norms file not found at `{SOIL_NORMS_PATH}`. "
        "Please ensure `soil_norms.xlsx` is in the blend_app folder."
    )
    st.stop()

norms = load_soil_norms()
crop_df = norms["Crop_Requirements"]
suf_df = norms["Soil_Sufficiency"]
adj_df = norms["Adjustment_Factors"]
materials_df = load_materials_with_markup(role)

# ── Persist widget values across page navigation ─────────────────────────
# Streamlit deletes widget keys when the widget isn't rendered. We keep a
# mirror dict "sa_data" that survives navigation and restore from it.
_SA_KEYS = [
    "customer_name", "farm_name", "field_name", "field_area", "pop_per_ha",
    "selected_crop", "yield_target", "cultivar",
    "agent_name", "agent_cell", "agent_email", "lab_name", "analysis_date",
    "soil_pH (H2O)", "soil_pH (KCl)", "soil_Org C", "soil_CEC", "soil_Clay",
    "soil_N (total)", "soil_P (Bray-1)", "soil_K", "soil_Ca", "soil_Mg", "soil_S",
    "soil_p_citric", "soil_na",
    "soil_micro_Fe", "soil_micro_B", "soil_micro_Mn",
    "soil_micro_Zn", "soil_micro_Mo", "soil_micro_Cu",
    "product_mode", "blend_batch", "blend_compost", "blend_app_rate",
]

if "sa_data" not in st.session_state:
    st.session_state["sa_data"] = {}

# Restore saved values into widget keys BEFORE any widgets render
for _k in _SA_KEYS:
    if _k not in st.session_state and _k in st.session_state["sa_data"]:
        st.session_state[_k] = st.session_state["sa_data"][_k]


def _save_sa_state():
    """Snapshot current widget values into the persistent mirror."""
    for _k in _SA_KEYS:
        if _k in st.session_state:
            st.session_state["sa_data"][_k] = st.session_state[_k]

# ── Sidebar: Agent info ───────────────────────────────────────────────────
st.sidebar.header("Agent Info")
# Auto-populate agent name for sales agents
_default_agent = auth_name if role == "sales_agent" else ""
agent_name = st.sidebar.text_input("Agent name", value=_default_agent, key="agent_name")
agent_cell = st.sidebar.text_input("Cell number", value="", key="agent_cell")
agent_email = st.sidebar.text_input("Email", value="info@saplingfertilizer.co.za",
                                     key="agent_email")

st.sidebar.divider()
st.sidebar.header("Lab Info")
lab_name = st.sidebar.text_input("Laboratory", value="", placeholder="e.g. Nvirotek",
                                 key="lab_name")
analysis_date = st.sidebar.date_input("Analysis date", value=date.today(),
                                       key="analysis_date")

st.sidebar.divider()
st.sidebar.caption(
    "Edit soil norms, crop requirements, and ratios in "
    f"`soil_norms.xlsx`"
)


# ── Load test data helper ─────────────────────────────────────────────────
with st.expander("Load test data (development only)"):
    if st.button("Fill test data", key="load_test"):
        test_vals = {
            "customer_name": "Ikhwezi Agro Holdings", "farm_name": "Greenfield Estate",
            "field_name": "Block A", "field_area": 10.0, "pop_per_ha": 80000,
            "soil_pH (H2O)": 6.5, "soil_pH (KCl)": 5.8, "soil_Org C": 1.5,
            "soil_CEC": 12.0, "soil_Clay": 20.0,
            "soil_N (total)": 25.0, "soil_P (Bray-1)": 18.0, "soil_K": 150.0,
            "soil_Ca": 800.0, "soil_Mg": 200.0, "soil_S": 15.0,
            "soil_micro_Fe": 50.0, "soil_micro_B": 0.8, "soil_micro_Mn": 30.0,
            "soil_micro_Zn": 3.0, "soil_micro_Mo": 0.1, "soil_micro_Cu": 2.0,
            "soil_na": 30.0,
        }
        for k, v in test_vals.items():
            st.session_state[k] = v
            st.session_state["sa_data"][k] = v
        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# Section 1: Customer & Field Info
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("Customer & Field Info")

col_cust, col_field, col_crop = st.columns(3)

with col_cust:
    customer_name = st.text_input("Customer name *", placeholder="e.g. Ikhwezi Agro Holdings",
                                   key="customer_name")
    farm_name = st.text_input("Farm", placeholder="e.g. Farm 1", key="farm_name")
    field_name = st.text_input("Field", placeholder="e.g. Block A", key="field_name")

with col_field:
    field_area = st.number_input("Field size (ha)", value=None, min_value=0.1,
                                  step=1.0, format="%.1f", placeholder="e.g. 10.0",
                                  key="field_area")
    pop_per_ha = st.number_input("Plants per ha", value=None, min_value=0,
                                  step=100, placeholder="e.g. 7500", key="pop_per_ha")
    plants_per_field = None
    if field_area and pop_per_ha:
        plants_per_field = int(pop_per_ha * field_area)
        st.metric("Plants per field", f"{plants_per_field:,}")

with col_crop:
    crop_list = crop_df["Crop"].tolist()
    selected_crop = st.selectbox("Crop *", options=[""] + crop_list, key="selected_crop")

    if selected_crop:
        crop_row = crop_df[crop_df["Crop"] == selected_crop].iloc[0]
        default_yield = float(crop_row["Default_Yield"])
        yield_unit = str(crop_row["Yield_Unit"])
        crop_type = str(crop_row["Type"])

        st.caption(f"{crop_type} — default {default_yield} {yield_unit}")
        yield_target = st.number_input(
            f"Yield target ({yield_unit})", value=default_yield,
            min_value=0.1, step=1.0, format="%.1f", key="yield_target",
        )
        cultivar = st.text_input("Cultivar", placeholder=f"e.g. {selected_crop}",
                                  key="cultivar")
    else:
        yield_target = None
        yield_unit = ""
        cultivar = ""

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# Section 2: Soil Analysis Input
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("Soil Analysis Results")
st.caption("Enter values from the laboratory soil analysis report (mg/kg unless otherwise noted).")

soil_values = {}

# pH and general
col_ph1, col_ph2, col_oc, col_cec, col_clay = st.columns(5)
with col_ph1:
    v = st.number_input("pH (H2O)", value=None, min_value=0.0, max_value=14.0,
                         step=0.1, format="%.1f", placeholder="e.g. 5.8",
                         key="soil_pH (H2O)")
    if v is not None:
        soil_values["pH (H2O)"] = v
with col_ph2:
    v = st.number_input("pH (KCl)", value=None, min_value=0.0, max_value=14.0,
                         step=0.1, format="%.1f", placeholder="e.g. 5.0",
                         key="soil_pH (KCl)")
    if v is not None:
        soil_values["pH (KCl)"] = v
with col_oc:
    v = st.number_input("Organic C (%)", value=None, min_value=0.0,
                         step=0.1, format="%.2f", placeholder="e.g. 1.5",
                         key="soil_Org C")
    if v is not None:
        soil_values["Org C"] = v
with col_cec:
    v = st.number_input("CEC (cmol/kg)", value=None, min_value=0.0,
                         step=0.5, format="%.1f", placeholder="e.g. 15.0",
                         key="soil_CEC")
    if v is not None:
        soil_values["CEC"] = v
with col_clay:
    v = st.number_input("Clay (%)", value=None, min_value=0.0, max_value=100.0,
                         step=1.0, format="%.0f", placeholder="e.g. 25",
                         key="soil_Clay")
    if v is not None:
        soil_values["Clay"] = v

# Macronutrients
st.markdown("**Macronutrients (mg/kg)**")
macro_cols = st.columns(6)
macro_params = [
    ("N (total)", "N", "e.g. 25"),
    ("P (Bray-1)", "P", "e.g. 18"),
    ("K", "K", "e.g. 120"),
    ("Ca", "Ca", "e.g. 800"),
    ("Mg", "Mg", "e.g. 150"),
    ("S", "S", "e.g. 15"),
]
for i, (param, label, ph) in enumerate(macro_params):
    with macro_cols[i]:
        v = st.number_input(label, value=None, min_value=0.0,
                             step=1.0, format="%.1f", placeholder=ph,
                             key=f"soil_{param}")
        if v is not None:
            soil_values[param] = v

# Option for Citric acid P
with st.expander("Alternative P extraction"):
    v = st.number_input("P (Citric acid) mg/kg", value=None, min_value=0.0,
                         step=1.0, format="%.1f", placeholder="e.g. 25",
                         key="soil_p_citric")
    if v is not None:
        soil_values["P (Citric acid)"] = v
        st.caption("Using Citric acid P instead of Bray-1 for classification.")

# Micronutrients
st.markdown("**Micronutrients (mg/kg)**")
micro_cols = st.columns(6)
micro_params = [
    ("Fe", "Fe", "e.g. 30"),
    ("B", "B", "e.g. 0.8"),
    ("Mn", "Mn", "e.g. 25"),
    ("Zn", "Zn", "e.g. 3.0"),
    ("Mo", "Mo", "e.g. 0.2"),
    ("Cu", "Cu", "e.g. 2.0"),
]
for i, (param, label, ph) in enumerate(micro_params):
    with micro_cols[i]:
        v = st.number_input(label, value=None, min_value=0.0,
                             step=0.1, format="%.2f", placeholder=ph,
                             key=f"soil_micro_{param}")
        if v is not None:
            soil_values[param] = v

# Sodium (for ratio calculations)
with st.expander("Additional parameters"):
    na_col, _, _, _ = st.columns(4)
    with na_col:
        v = st.number_input("Na (mg/kg)", value=None, min_value=0.0,
                             step=1.0, format="%.1f", placeholder="e.g. 30",
                             key="soil_na")
        if v is not None:
            soil_values["Na"] = v

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# Section 3: Soil Classification
# ═════════════════════════════════════════════════════════════════════════════
if soil_values:
    st.subheader("Soil Analysis Classification")

    class_rows = []
    for param, value in soil_values.items():
        classification = classify_soil_value(value, param, suf_df)
        if classification:
            class_rows.append({
                "Parameter": param,
                "Value": value,
                "Classification": classification,
            })

    if class_rows:
        class_df = pd.DataFrame(class_rows)

        # Color-coded display
        def colour_class(val):
            colour = CLASSIFICATION_COLOURS.get(val, "#666666")
            return f"color: {colour}; font-weight: bold"

        styled = class_df.style.applymap(
            colour_class, subset=["Classification"]
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Nutrient Ratios ──────────────────────────────────────────────────
    ratio_results = evaluate_ratios(soil_values, norms)
    if ratio_results:
        with st.expander("Nutrient Ratios & Base Saturation"):
            ratio_df = pd.DataFrame(ratio_results)

            def colour_status(val):
                if val == "Ideal":
                    return "color: #388e3c; font-weight: bold"
                elif val == "Below ideal":
                    return "color: #f57c00; font-weight: bold"
                else:
                    return "color: #d32f2f; font-weight: bold"

            styled_r = ratio_df.style.applymap(colour_status, subset=["Status"])
            st.dataframe(styled_r, use_container_width=True, hide_index=True)
else:
    ratio_results = []

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# Section 4: Nutrient Targets & Recommendations
# ═════════════════════════════════════════════════════════════════════════════
if not selected_crop or not yield_target:
    st.info("Select a crop and yield target above to calculate nutrient recommendations.")
    _save_sa_state()
    st.stop()

st.subheader("Nutrient Targets")

nutrient_targets = calculate_nutrient_targets(
    selected_crop, yield_target, soil_values, norms
)

if not nutrient_targets:
    st.error("Could not calculate targets — crop not found in norms.")
    _save_sa_state()
    st.stop()

# Share with Cost Analysis page
st.session_state["nutrient_targets_for_cost"] = nutrient_targets
st.session_state["crop_for_cost"] = selected_crop
st.session_state["yield_for_cost"] = yield_target
st.session_state["yield_unit_for_cost"] = yield_unit
st.session_state["customer_for_cost"] = customer_name

# Display targets table
target_df = pd.DataFrame(nutrient_targets)
target_df_display = target_df.rename(columns={
    "Nutrient": "Nutrient",
    "Per_Unit": f"kg/{yield_unit.split('/')[0] if '/' in yield_unit else 'unit'}",
    "Base_Req_kg_ha": "Base Req (kg/ha)",
    "Soil_Value": "Soil Value",
    "Classification": "Soil Class",
    "Factor": "Adj. Factor",
    "Target_kg_ha": "Target (kg/ha)",
})

def colour_class_col(val):
    colour = CLASSIFICATION_COLOURS.get(val, "#666666")
    return f"color: {colour}; font-weight: bold"

styled_targets = target_df_display.style.applymap(
    colour_class_col, subset=["Soil Class"]
)
st.dataframe(styled_targets, use_container_width=True, hide_index=True)

# Summary metrics
targets_dict = {t["Nutrient"]: t["Target_kg_ha"] for t in nutrient_targets}
n_target = targets_dict.get("N", 0)
p_target = targets_dict.get("P", 0)
k_target = targets_dict.get("K", 0)

m1, m2, m3, m4 = st.columns(4)
m1.metric("N target", f"{n_target:.1f} kg/ha")
m2.metric("P target", f"{p_target:.1f} kg/ha")
m3.metric("K target", f"{k_target:.1f} kg/ha")

# NPK ratio for blend calculator
total_npk = n_target + p_target + k_target
if total_npk > 0:
    n_pct = n_target / total_npk * 100
    p_pct = p_target / total_npk * 100
    k_pct = k_target / total_npk * 100
    sa_label = pct_to_sa_notation(n_pct, p_pct, k_pct)
    m4.metric("NPK Ratio", sa_label)

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# Section 5: Product Recommendations
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("Product Recommendations")

product_mode = st.radio(
    "How would you like to meet nutrient targets?",
    ["Add products manually", "Auto-blend (use Blend Calculator)"],
    horizontal=True, key="product_mode",
)

if "products" not in st.session_state:
    st.session_state.products = []

methods_df = norms.get("Application_Methods")
method_options = methods_df["Method"].tolist() if methods_df is not None else [
    "Band Place", "Broadcast", "Fertigation", "Foliar Spray", "Side Dress"
]

# ── Auto-blend mode ──────────────────────────────────────────────────────
if product_mode == "Auto-blend (use Blend Calculator)":
    st.caption("The blend calculator will automatically create an optimised blend to meet your NPK targets.")

    ab1, ab2, ab3 = st.columns(3)
    with ab1:
        blend_batch = st.number_input("Batch size (kg)", value=1000, step=100,
                                       min_value=100, key="blend_batch")
    with ab2:
        min_compost_pct = st.slider("Min compost %", 0, 95, 50, 5, key="blend_compost")
    with ab3:
        blend_app_rate = st.number_input("Application rate (kg/ha)", value=1000.0,
                                          min_value=0.0, step=50.0, key="blend_app_rate")

    # Read material selection from Blend Calculator state, fall back to defaults
    _DEFAULT_MATS = {
        "Urea 46%", "MAP 33%", "DAP",
        "KCL (Potassium Chloride)", "Gypsum", "KAN 28%", "Calcitic Lime",
    }
    bc_data = st.session_state.get("bc_data", {})
    selected_mats = [COMPOST_NAME]
    for _, row in materials_df.iterrows():
        name = row["Material"]
        if name == COMPOST_NAME:
            continue
        wkey = f"mat_{name}"
        # Use BC selection if available, otherwise use defaults
        if wkey in bc_data:
            if bc_data[wkey]:
                selected_mats.append(name)
        elif name in _DEFAULT_MATS:
            selected_mats.append(name)
    df_mat = materials_df[materials_df["Material"].isin(selected_mats)].reset_index(drop=True)

    # Auto-run optimizer whenever inputs change
    blend_targets = {}
    if n_target > 0 and blend_app_rate > 0:
        blend_targets["N"] = n_target / blend_app_rate * 100
    if p_target > 0 and blend_app_rate > 0:
        blend_targets["P"] = p_target / blend_app_rate * 100
    if k_target > 0 and blend_app_rate > 0:
        blend_targets["K"] = k_target / blend_app_rate * 100

    if not blend_targets:
        st.warning("No NPK targets to optimise for.")
    else:
        compost_mask = df_mat["Material"] == COMPOST_NAME
        if not compost_mask.any():
            st.error(f"'{COMPOST_NAME}' not found in materials database.")
        else:
            compost_idx = df_mat.index[compost_mask][0]

            res = run_optimizer(blend_targets, df_mat, blend_batch,
                                compost_idx, min_compost_pct)
            is_relaxed = False
            relaxed_scale = 1.0

            if not res.success:
                relaxed_res, relaxed_scale = find_closest_blend(
                    blend_targets, df_mat, blend_batch,
                    compost_idx, min_compost_pct)
                if relaxed_res is not None and relaxed_res.success:
                    res, is_relaxed = relaxed_res, True

            if not res.success:
                st.error("Blend not feasible with available materials. "
                         "Try adjusting the application rate or compost %.")
            else:
                if is_relaxed:
                    st.warning(
                        f"Exact targets not achievable. Closest blend at "
                        f"**{relaxed_scale * 100:.1f}%** of requested levels.")

                result = df_mat.copy()
                result["kg"] = np.round(res.x, 2)
                result = result[result["kg"] > 0.01].copy()

                # Populate products from blend result
                st.session_state.products = []
                for _, row in result.iterrows():
                    mat_name = row["Material"]
                    kg_in_batch = row["kg"]
                    kg_ha = kg_in_batch / blend_batch * blend_app_rate
                    cost_ton = float(row.get("Cost (R/ton)", 0))
                    price_ha = kg_ha * cost_ton / 1000

                    nutrients_provided = {}
                    for nut in NUTRIENTS_SOIL:
                        if nut in row.index:
                            nutrients_provided[nut] = round(
                                kg_ha * float(row[nut]) / 100, 2)
                        else:
                            nutrients_provided[nut] = 0

                    st.session_state.products.append({
                        "product": mat_name,
                        "method": "Broadcast",
                        "timing": "Pre-plant",
                        "kg_ha": round(kg_ha, 2),
                        "price_ha": round(price_ha, 2),
                        "price_per_ton": cost_ton,
                        "nutrients": nutrients_provided,
                    })

# ── Manual product entry ─────────────────────────────────────────────────
else:
    st.caption("Add fertilizer products to meet the nutrient targets. Enter application rates per hectare.")

    with st.expander("Add Product", expanded=len(st.session_state.products) == 0):
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            prod_input = st.radio("Product source", ["Type name", "From materials"],
                                   horizontal=True, key="prod_source")
            if prod_input == "Type name":
                prod_name = st.text_input("Product name", placeholder="e.g. 19/1/5 (25)",
                                      key="sa_prod_name")
            else:
                mat_names = materials_df["Material"].tolist()
                prod_name = st.selectbox("Select material", options=[""] + mat_names,
                                     key="sa_prod_material")

        with pc2:
            app_method = st.selectbox("Application method", options=method_options,
                                      key="sa_app_method")
            app_timing = st.text_input("Application time", placeholder="e.g. At Plant, August",
                                        key="sa_app_timing")

        with pc3:
            kg_per_ha = st.number_input("Kg per ha", value=0.0, min_value=0.0, step=50.0,
                                         key="sa_kg_ha")
            price_per_ton = st.number_input("Price (R/ton)", value=0.0, min_value=0.0, step=100.0,
                                             key="sa_price_ton")

        st.markdown("**Product nutrient content (%)**")
        if prod_input == "From materials" and prod_name:
            mat_row = materials_df[materials_df["Material"] == prod_name]
            if not mat_row.empty:
                st.caption("Nutrient values loaded from materials database.")

        nut_cols = st.columns(6)
        prod_nutrients = {}
        for i, nut in enumerate(NUTRIENTS_SOIL[:6]):
            with nut_cols[i]:
                default = 0.0
                if prod_input == "From materials" and prod_name:
                    mat_row = materials_df[materials_df["Material"] == prod_name]
                    if not mat_row.empty and nut in mat_row.columns:
                        default = float(mat_row.iloc[0].get(nut, 0))
                prod_nutrients[nut] = st.number_input(
                    f"{nut} %", value=default, min_value=0.0, max_value=100.0,
                    step=0.1, format="%.2f", key=f"prod_nut_{nut}"
                )

        with st.expander("Micronutrients"):
            mic_cols = st.columns(6)
            for i, nut in enumerate(NUTRIENTS_SOIL[6:]):
                with mic_cols[i]:
                    default = 0.0
                    if prod_input == "From materials" and prod_name:
                        mat_row = materials_df[materials_df["Material"] == prod_name]
                        if not mat_row.empty and nut in mat_row.columns:
                            default = float(mat_row.iloc[0].get(nut, 0))
                    prod_nutrients[nut] = st.number_input(
                        f"{nut} %", value=default, min_value=0.0, max_value=100.0,
                        step=0.01, format="%.3f", key=f"prod_nut_{nut}"
                    )

        if st.button("Add Product") and prod_name and kg_per_ha > 0:
            nutrients_provided = {}
            for nut, pct in prod_nutrients.items():
                nutrients_provided[nut] = round(kg_per_ha * pct / 100, 2)

            price_ha = kg_per_ha * price_per_ton / 1000

            st.session_state.products.append({
                "product": prod_name,
                "method": app_method,
                "timing": app_timing,
                "kg_ha": kg_per_ha,
                "price_ha": price_ha,
                "price_per_ton": price_per_ton,
                "nutrient_pcts": prod_nutrients,
                "nutrients": nutrients_provided,
            })
            st.rerun()

# ── Display products (both modes) ────────────────────────────────────────
if st.session_state.products:
    st.markdown("**Added Products**")

    prod_display = []
    for p in st.session_state.products:
        prod_display.append({
            "Product": p["product"],
            "Method": p["method"],
            "Timing": p["timing"],
            "Kg/Ha": f"{p['kg_ha']:.0f}",
            "Price/Ha": f"R{p['price_ha']:,.2f}",
            "Price/Ton": f"R{p.get('price_per_ton', 0):,.2f}",
        })
    st.dataframe(pd.DataFrame(prod_display), use_container_width=True, hide_index=True)

    # Remove product buttons (only in manual mode)
    if product_mode == "Add products manually":
        rm_cols = st.columns(min(len(st.session_state.products), 6) + 1)
        for i, p in enumerate(st.session_state.products):
            with rm_cols[i % 6]:
                if st.button(f"Remove {p['product'][:15]}", key=f"rm_{i}"):
                    st.session_state.products.pop(i)
                    st.rerun()

    # ── Nutrient Totals and Over/Short ────────────────────────────────────
    st.markdown("**Nutrient Totals vs Targets (kg/ha)**")

    totals = {}
    for p in st.session_state.products:
        for nut, val in (p.get("nutrients") or {}).items():
            totals[nut] = totals.get(nut, 0) + val

    comparison = []
    for nut in NUTRIENTS_SOIL:
        target = targets_dict.get(nut, 0)
        total = totals.get(nut, 0)
        diff = total - target
        comparison.append({
            "Nutrient": nut,
            "Target (kg/ha)": round(target, 2),
            "Products (kg/ha)": round(total, 2),
            "Over/Short": round(diff, 2),
        })

    comp_df = pd.DataFrame(comparison)

    def colour_diff(val):
        if isinstance(val, (int, float)):
            if val > 0.5:
                return "color: #1976d2"
            elif val < -0.5:
                return "color: #d32f2f; font-weight: bold"
        return ""

    styled_comp = comp_df.style.applymap(colour_diff, subset=["Over/Short"])
    st.dataframe(styled_comp, use_container_width=True, hide_index=True)

    # Total costs
    total_cost_ha = sum(p["price_ha"] for p in st.session_state.products)

    tc1, tc2 = st.columns(2)
    tc1.metric("Total cost per ha", f"R{total_cost_ha:,.2f}")
else:
    total_cost_ha = 0

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# Section 6: Export
# ═════════════════════════════════════════════════════════════════════════════
st.subheader("Export Report")

# Required fields differ by role
if role == "sales_agent":
    can_export = bool(customer_name and farm_name and field_name and selected_crop)
    if not can_export:
        st.warning("Customer name, Farm, Field, and Crop are all required.")
else:
    can_export = bool(customer_name and selected_crop)
    if not can_export:
        st.warning("Customer name and crop are required to generate a report.")

if can_export:
    pdf_bytes = build_soil_pdf(
        customer=customer_name,
        farm=farm_name,
        field=field_name,
        crop_name=selected_crop,
        cultivar=cultivar,
        yield_target=yield_target,
        yield_unit=yield_unit,
        pop_per_ha=pop_per_ha,
        plants_per_field=plants_per_field,
        field_area_ha=field_area,
        agent_name=agent_name,
        agent_cell=agent_cell,
        agent_email=agent_email,
        lab_name=lab_name,
        analysis_date=analysis_date.strftime("%A, %B %d, %Y")
            if analysis_date else "",
        soil_values=soil_values,
        nutrient_targets=nutrient_targets,
        ratio_results=ratio_results,
        products=st.session_state.get("products", []),
        total_cost_ha=total_cost_ha,
        norms=norms,
    )
    filename = (f"Recommendation_{customer_name}_{selected_crop}"
                .replace(" ", "_") + ".pdf")

    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button(
            "Download PDF Report", pdf_bytes, filename, "application/pdf",
            key="soil_pdf_dl",
        )
    with ec2:
        if st.button("Save to Database", key="save_soil"):
            try:
                save_soil_analysis(
                    customer=customer_name,
                    farm=farm_name,
                    field=field_name,
                    crop=selected_crop,
                    cultivar=cultivar,
                    yield_target=yield_target,
                    yield_unit=yield_unit,
                    field_area_ha=field_area,
                    pop_per_ha=pop_per_ha,
                    agent_name=agent_name,
                    agent_cell=agent_cell,
                    agent_email=agent_email,
                    lab_name=lab_name,
                    analysis_date=analysis_date.strftime("%Y-%m-%d")
                        if analysis_date else "",
                    soil_values=soil_values,
                    nutrient_targets=nutrient_targets,
                    ratio_results=ratio_results,
                    products=st.session_state.get("products", []),
                    total_cost_ha=total_cost_ha,
                    created_by=username,
                )
                st.success("Soil analysis saved!")
            except Exception as e:
                st.error(f"Failed to save: {e}")

# ── Save state for cross-page persistence ─────────────────────────────────
_save_sa_state()
