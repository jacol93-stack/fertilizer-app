import json
import streamlit as st
import pandas as pd
from datetime import datetime
from shared import (
    apply_styles, show_header, build_pdf, pct_to_sa_notation,
    sa_notation_to_pct, fetch_blends, fetch_all_blends, restore_blends,
    update_blend, delete_blend, fetch_unique_clients, fetch_unique_farms,
    fetch_blends_by_client, fetch_blends_by_farm,
    ORANGE, DARK_GREY, MED_GREY,
)

st.set_page_config(page_title="Database — Sapling", layout="wide")
apply_styles()
show_header("Database")


# ── Helper: display a blend card ───────────────────────────────────────────
def blend_card(blend, prefix=""):
    bid = blend["id"]
    key_prefix = f"{prefix}{bid}"
    created = datetime.fromisoformat(blend["created_at"]).strftime("%Y-%m-%d %H:%M")
    name = blend["blend_name"] or "Unnamed"
    client = blend.get("client") or ""
    farm = blend.get("farm") or ""
    cost = blend.get("cost_per_ton") or 0

    header = f"**{name}**"
    if client:
        header += f"  |  {client}"
    if farm:
        header += f"  |  {farm}"
    header += f"  |  R {cost:,.0f}/ton  |  {created}"

    with st.expander(header):
        recipe = blend.get("recipe") or []
        if recipe:
            recipe_df = pd.DataFrame(recipe).rename(columns={
                "material": "Material", "type": "Type", "kg": "kg",
                "pct": "% of Blend", "cost": "Cost (R)",
            })
            st.markdown("**Recipe**")
            st.dataframe(recipe_df, use_container_width=True, hide_index=True)

        nutrients = blend.get("nutrients") or []
        if nutrients:
            nut_df = pd.DataFrame(nutrients).rename(columns={
                "nutrient": "Nutrient", "target": "Target %",
                "actual": "Actual %", "diff": "Diff",
                "kg_per_ton": "kg per ton",
            })
            with st.expander("Nutrient Analysis"):
                st.dataframe(nut_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("**Edit**")
        ec1, ec2 = st.columns(2)
        with ec1:
            new_name = st.text_input("Blend name", value=blend["blend_name"] or "",
                                     key=f"name_{key_prefix}")
            new_client = st.text_input("Client", value=client, key=f"client_{key_prefix}")
        with ec2:
            new_farm = st.text_input("Farm", value=farm, key=f"farm_{key_prefix}")
            new_price = st.number_input(
                "Selling price (R/ton)",
                value=float(blend.get("selling_price") or 0),
                step=100.0, key=f"price_{key_prefix}",
            )

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            if st.button("Update", key=f"update_{key_prefix}"):
                update_blend(bid, {
                    "blend_name": new_name,
                    "client": new_client or None,
                    "farm": new_farm or None,
                    "selling_price": float(new_price),
                })
                st.success("Updated!")
                st.rerun()

        with bc2:
            if st.button("Reprint PDF", key=f"pdf_{key_prefix}"):
                batch_size = blend.get("batch_size") or 1000
                selling_price = float(blend.get("selling_price") or 0)
                cost_pt = float(blend.get("cost_per_ton") or 0)
                total_kg = sum(r.get("kg", 0) for r in recipe)
                total_cost = sum(r.get("cost", 0) for r in recipe)
                compost_kg = sum(r.get("kg", 0) for r in recipe
                                 if r.get("material") == "Manure Compost")
                compost_pct = (compost_kg / total_kg * 100) if total_kg > 0 else 0
                margin = selling_price - cost_pt if selling_price > 0 else None

                recipe_rows = [
                    [r.get("material", ""), r.get("type", ""),
                     f"{r.get('kg', 0):.1f}", f"{r.get('pct', 0):.1f}",
                     f"{r.get('cost', 0):.2f}"]
                    for r in recipe
                ]
                nutrient_rows = [
                    [n.get("nutrient", ""), f"{n.get('target', 0):.3f}",
                     f"{n.get('actual', 0):.3f}", f"{n.get('diff', 0):.3f}",
                     f"{n.get('kg_per_ton', 0):.2f}"]
                    for n in nutrients
                ]

                nut_map = {n.get("nutrient"): n.get("actual", 0) for n in nutrients}
                sa_nota = pct_to_sa_notation(
                    nut_map.get("N", 0), nut_map.get("P", 0), nut_map.get("K", 0)
                )
                pdf_bytes = build_pdf(
                    new_name, new_client, new_farm, batch_size,
                    compost_pct, cost_pt, total_cost, selling_price,
                    margin, False, 1.0, recipe_rows, nutrient_rows,
                    sa_notation=sa_nota,
                )
                dl_name = f"{new_name or 'blend'}_{new_client or 'unknown'}.pdf".replace(" ", "_")
                st.download_button(
                    "Download PDF", pdf_bytes, dl_name,
                    "application/pdf", key=f"dl_{key_prefix}",
                )

        with bc3:
            if st.button("Delete", key=f"del_{key_prefix}"):
                delete_blend(bid)
                st.success("Deleted!")
                st.rerun()


# ── Tabs ────────────────────────────────────────────────────────────────────
tab_search, tab_clients, tab_farms, tab_nutrients, tab_backup = st.tabs(
    ["Search", "By Client", "By Farm", "By Nutrients", "Backup"]
)

# ── Search tab ──────────────────────────────────────────────────────────────
with tab_search:
    search = st.text_input("Search blends", placeholder="Search by name, client, or farm...")
    blends = fetch_blends(search if search else None)
    if not blends:
        st.info("No blends found.")
    else:
        st.caption(f"{len(blends)} blend(s)")
        for b in blends:
            blend_card(b, prefix="search_")

# ── By Client tab ───────────────────────────────────────────────────────────
with tab_clients:
    clients = fetch_unique_clients()
    if not clients:
        st.info("No clients found.")
    else:
        selected_client = st.selectbox("Select client", clients)
        if selected_client:
            client_blends = fetch_blends_by_client(selected_client)
            st.caption(f"{len(client_blends)} blend(s) for {selected_client}")
            for b in client_blends:
                blend_card(b, prefix="client_")

# ── By Farm tab ─────────────────────────────────────────────────────────────
with tab_farms:
    farms = fetch_unique_farms()
    if not farms:
        st.info("No farms found.")
    else:
        selected_farm = st.selectbox("Select farm", farms)
        if selected_farm:
            farm_blends = fetch_blends_by_farm(selected_farm)
            st.caption(f"{len(farm_blends)} blend(s) for {selected_farm}")
            for b in farm_blends:
                blend_card(b, prefix="farm_")

# ── By Nutrients tab ────────────────────────────────────────────────────────
with tab_nutrients:
    st.caption("Find blends by nutrient content. Set targets and a tolerance for similar matches.")

    nut_input_mode = st.radio(
        "Search format",
        ["International (NPK %)", "SA Local (ratio & total)"],
        horizontal=True, key="nut_search_mode",
    )

    search_targets = {}

    if nut_input_mode == "International (NPK %)":
        ncol1, ncol2, ncol3, ncol4 = st.columns(4)
        with ncol1:
            search_n = st.number_input("N %", value=None, min_value=0.0, step=0.5,
                                       format="%.2f", placeholder="Any", key="sn_n")
        with ncol2:
            search_p = st.number_input("P %", value=None, min_value=0.0, step=0.5,
                                       format="%.2f", placeholder="Any", key="sn_p")
        with ncol3:
            search_k = st.number_input("K %", value=None, min_value=0.0, step=0.5,
                                       format="%.2f", placeholder="Any", key="sn_k")
        with ncol4:
            tolerance = st.number_input("Tolerance %", value=0.5, min_value=0.0,
                                        step=0.1, format="%.1f", key="sn_tol")
        if search_n is not None:
            search_targets["N"] = search_n
        if search_p is not None:
            search_targets["P"] = search_p
        if search_k is not None:
            search_targets["K"] = search_k
    else:
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        with sc1:
            sa_sn = st.number_input("N ratio", value=None, min_value=0, step=1,
                                    placeholder="e.g. 3", key="sa_sn")
        with sc2:
            sa_sp = st.number_input("P ratio", value=None, min_value=0, step=1,
                                    placeholder="e.g. 1", key="sa_sp")
        with sc3:
            sa_sk = st.number_input("K ratio", value=None, min_value=0, step=1,
                                    placeholder="e.g. 5", key="sa_sk")
        with sc4:
            sa_st = st.number_input("Total %", value=None, min_value=0.0,
                                    max_value=100.0, step=1.0,
                                    placeholder="e.g. 26", key="sa_st")
        with sc5:
            tolerance = st.number_input("Tolerance %", value=0.5, min_value=0.0,
                                        step=0.1, format="%.1f", key="sn_tol_sa")

        if sa_sn is not None and sa_sp is not None and sa_sk is not None and sa_st is not None:
            sn_pct, sp_pct, sk_pct = sa_notation_to_pct(sa_sn, sa_sp, sa_sk, sa_st)
            st.info(f"**{sa_sn}:{sa_sp}:{sa_sk} ({sa_st:.0f})** → N: {sn_pct:.2f}%  |  P: {sp_pct:.2f}%  |  K: {sk_pct:.2f}%")
            if sn_pct > 0:
                search_targets["N"] = sn_pct
            if sp_pct > 0:
                search_targets["P"] = sp_pct
            if sk_pct > 0:
                search_targets["K"] = sk_pct

    if search_targets:
        all_blends = fetch_all_blends()
        exact_matches = []
        similar_matches = []

        for b in all_blends:
            nutrients = b.get("nutrients") or []
            nut_map = {n["nutrient"]: n.get("actual", 0) for n in nutrients}

            is_exact = True
            is_similar = True
            for nut, target_val in search_targets.items():
                actual = nut_map.get(nut, 0)
                diff = abs(actual - target_val)
                if diff > 0.01:
                    is_exact = False
                if diff > tolerance:
                    is_similar = False

            if is_exact:
                exact_matches.append(b)
            elif is_similar:
                similar_matches.append(b)

        if exact_matches:
            st.markdown(f"**Exact matches ({len(exact_matches)})**")
            for b in exact_matches:
                blend_card(b, prefix="nexact_")

        if similar_matches:
            st.markdown(f"**Similar matches within {tolerance}% ({len(similar_matches)})**")
            for b in similar_matches:
                blend_card(b, prefix="nsim_")

        if not exact_matches and not similar_matches:
            st.info("No matching blends found.")
    else:
        st.info("Set at least one nutrient value to search.")

# ── Backup tab ──────────────────────────────────────────────────────────────
with tab_backup:
    st.markdown("**Download Backup**")
    st.caption("Export all blends as a JSON file. IDs are included so restoring won't create duplicates.")

    if st.button("Generate Backup"):
        all_data = fetch_all_blends()
        backup_json = json.dumps(all_data, indent=2, default=str)
        st.download_button(
            f"Download backup ({len(all_data)} blends)",
            backup_json,
            f"blends_backup_{datetime.now().strftime('%Y%m%d')}.json",
            "application/json",
            key="backup_dl",
        )

    st.markdown("---")
    st.markdown("**Restore from Backup**")
    st.caption("Upload a previously downloaded backup file. Existing blends won't be duplicated.")

    uploaded = st.file_uploader("Upload backup JSON", type=["json"], key="restore_upload")
    if uploaded:
        try:
            backup_data = json.loads(uploaded.read())
            st.info(f"File contains {len(backup_data)} blend(s).")
            if st.button("Restore"):
                count = restore_blends(backup_data)
                if count > 0:
                    st.success(f"Restored {count} new blend(s). Duplicates were skipped.")
                else:
                    st.info("All blends already exist — nothing to restore.")
                st.rerun()
        except Exception as e:
            st.error(f"Invalid backup file: {e}")
