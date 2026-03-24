import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog
import os
from datetime import datetime

st.set_page_config(layout="wide")

st.title("Fertilizer Blend Calculator")

# =========================
# LOAD MATERIALS
# =========================
df = pd.read_excel("materials.xlsx")
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

for col in df.columns:
    if col not in ["ID","Material","Type","Category"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.fillna(0)

# =========================
# DETECT NUTRIENTS
# =========================
exclude_cols = ["ID","Material","Cost (R/ton)","Type","Category"]
nutrients = [c for c in df.columns if c not in exclude_cols]

# =========================
# MATERIAL SELECTION
# =========================
st.sidebar.header("Select Materials")

selected_ids = []
default_materials = ["urea", "map", "kcl", "gypsum", "compost"]

for _, row in df.iterrows():
    mat = str(row["Material"]).lower()
    default = any(x in mat for x in default_materials)

    if st.sidebar.checkbox(
        f"{row['Material']} (ID {row['ID']})",
        value=default
    ):
        selected_ids.append(row["ID"])

df_use = df[df["ID"].isin(selected_ids)]

if df_use.empty:
    st.warning("Select at least one material")
    st.stop()

# =========================
# TARGETS
# =========================
st.sidebar.header("Targets (%)")

targets = {}
for n in nutrients:
    targets[n] = st.sidebar.number_input(n, value=0.0, step=0.1)

batch = st.sidebar.number_input("Batch size (kg)", value=1000)
min_org = st.sidebar.number_input("Minimum Organic %", value=0.0)

# =========================
# SOLVE
# =========================
if st.sidebar.button("Optimize"):

    if all(v == 0 for v in targets.values()):
        st.error("Enter at least one nutrient target")
        st.stop()

    n = len(df_use)

    cost = pd.to_numeric(df_use["Cost (R/ton)"], errors="coerce").fillna(0) / 1000
    c = np.array(cost, dtype=float)

    A_eq = []
    b_eq = []

    for nut in nutrients:
        if targets[nut] > 0:
            A_eq.append((df_use[nut] / 100).to_numpy())
            b_eq.append(targets[nut]/100 * batch)

    A_eq.append(np.ones(n))
    b_eq.append(batch)

    A_eq = np.array(A_eq)
    b_eq = np.array(b_eq)

    organic_mask = (df_use["Type"].astype(str).str.strip() == "Organic").astype(int).to_numpy()

    A_ub = np.array([-organic_mask])
    b_ub = np.array([-min_org/100 * batch])

    bounds = [(0, batch)] * n

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds)

    if res.success:
        result = df_use.copy()
        result["kg"] = res.x
        st.session_state["result"] = result
        st.success("Blend found")

    else:
        res_no_org = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds)

        if res_no_org.success:
            result = df_use.copy()
            result["kg"] = res_no_org.x
            st.session_state["result"] = result

            organic = result[result["Type"]=="Organic"]["kg"].sum()
            organic_pct = organic / batch * 100

            st.warning(
                f"Not possible with {min_org}% organic. "
                f"Minimum required: {organic_pct:.1f}%"
            )

        else:
            st.error("Blend not feasible with selected materials")

            limiting = []

            for nut in nutrients:
                if targets[nut] > 0:
                    max_possible = (df_use[nut] / 100 * batch).sum()
                    required = targets[nut] / 100 * batch

                    if max_possible < required:
                        limiting.append(nut)

            if limiting:
                st.warning(f"Limiting nutrients: {', '.join(limiting)}")
            else:
                st.warning("Combination of constraints prevents solution")

            st.stop()

# =========================
# RESULTS (PERSISTENT)
# =========================
if "result" in st.session_state:

    result = st.session_state["result"].copy()

    result = result[result["kg"] > 0.001]
    result["kg"] = result["kg"].round(2)

    result["Cost (R)"] = result["kg"] * result["Cost (R/ton)"] / 1000

    st.subheader("Blend Result")
    st.dataframe(result[["ID","Material","kg","Cost (R)"]])

    # =========================
    # SUMMARY
    # =========================
    st.subheader("Target vs Actual")

    summary = []

    for nut in nutrients:
        target = targets[nut]
        actual = (result[nut] * result["kg"]).sum() / batch

        summary.append([
            nut,
            round(target,2),
            round(actual,2),
            round(actual-target,2)
        ])

    st.table(pd.DataFrame(summary, columns=["Nutrient","Target","Actual","Diff"]))

    # =========================
    # ORGANIC VS CHEMICAL
    # =========================
    organic = result[result["Type"]=="Organic"]["kg"].sum()
    chemical = result[result["Type"]=="Chemical"]["kg"].sum()

    st.write(f"Organic: {organic/batch*100:.1f}%")
    st.write(f"Chemical: {chemical/batch*100:.1f}%")

    total_cost = result["Cost (R)"].sum()
    cost_per_ton = total_cost / batch * 1000

    st.write(f"Cost per ton: R {cost_per_ton:,.2f}")

    # =========================
    # SAVE BLEND
    # =========================
    st.subheader("Save Blend")

    col1, col2 = st.columns(2)

    with col1:
        product_name = st.text_input("Blend Name")
        client = st.text_input("Client")

    with col2:
        farm = st.text_input("Farm")
        selling_price = st.number_input("Selling Price (R/ton)", value=0.0, step=100.0)

    if st.button("Save Blend"):

        now = datetime.now().replace(second=0, microsecond=0)
        blend_id = str(now.timestamp())

        if product_name.strip() == "":
            product_name = f"Blend {now.strftime('%Y-%m-%d %H:%M')}"

        organic_pct = organic / batch * 100

        summary_row = {
            "ID": blend_id,
            "Date": now,
            "Product": product_name,
            "Client": client,
            "Farm": farm,
            "Cost_per_ton": cost_per_ton,
            "Selling_price": selling_price,
            "Margin": selling_price - cost_per_ton,
            "Organic_%": organic_pct
        }

        details = result.copy()
        details["ID"] = blend_id

        pd.DataFrame([summary_row]).to_csv(
            "blend_summary.csv",
            mode="a",
            header=not os.path.exists("blend_summary.csv"),
            index=False
        )

        details.to_csv(
            "blend_details.csv",
            mode="a",
            header=not os.path.exists("blend_details.csv"),
            index=False
        )

        st.success("Blend saved!")

# =========================
# SAVED BLENDS
# =========================
st.subheader("Saved Blends")

if os.path.exists("blend_summary.csv"):

    summary = pd.read_csv("blend_summary.csv")

    for col in ["Selling_price", "Margin", "Organic_%", "Client", "Farm"]:
        if col not in summary.columns:
            summary[col] = ""

    st.dataframe(
        summary[["Product","Client","Farm","Date","Cost_per_ton","Selling_price","Margin","Organic_%"]]
    )

    selected_index = st.selectbox(
        "Select blend",
        summary.index,
        format_func=lambda i: summary.loc[i,"Product"]
    )

    selected_id = summary.loc[selected_index, "ID"]

    if os.path.exists("blend_details.csv"):
        details = pd.read_csv("blend_details.csv")
        st.dataframe(details[details["ID"] == selected_id])

    if st.button("Delete Selected Blend"):

        summary = summary[summary["ID"] != selected_id]
        summary.to_csv("blend_summary.csv", index=False)

        details = pd.read_csv("blend_details.csv")
        details = details[details["ID"] != selected_id]
        details.to_csv("blend_details.csv", index=False)

        st.success("Deleted!")
        st.rerun()

else:
    st.info("No saved blends yet")