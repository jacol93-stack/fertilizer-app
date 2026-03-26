import json
import streamlit as st
import pandas as pd
from datetime import datetime
import bcrypt
from shared import (
    apply_styles, show_header, show_mobile_nav, build_pdf, build_soil_pdf, pct_to_sa_notation,
    sa_notation_to_pct, fetch_blends, fetch_all_blends, restore_blends,
    update_blend, delete_blend, soft_delete_blend,
    fetch_unique_clients, fetch_unique_farms,
    fetch_blends_by_client, fetch_blends_by_farm,
    fetch_unique_agents, fetch_blends_by_agent, fetch_soil_by_agent,
    fetch_soil_analyses, fetch_all_soil_analyses,
    delete_soil_analysis, soft_delete_soil_analysis,
    load_soil_norms, load_materials, load_markups, save_markup,
    fetch_all_users, create_user, update_user, delete_user,
    get_supabase, NUTRIENTS_SOIL, ORANGE, DARK_GREY, MED_GREY,
)
from auth import require_auth, logout_button, is_admin, reload_auth

st.set_page_config(page_title="Database — Sapling", layout="wide")
apply_styles()

# ── Auth ──────────────────────────────────────────────────────────────────
auth_name, role, username = require_auth()
logout_button()
show_mobile_nav("Database")

# Agents cannot access Database page — hide it completely
if role == "sales_agent":
    st.markdown(
        "<style>[data-testid='stSidebarNav'] li:nth-child(1) {display: none;}</style>",
        unsafe_allow_html=True,
    )
    st.warning("You do not have access to the Database page.")
    st.stop()

show_header("Database")

# ── Agent activity notifications ─────────────────────────────────────────
_last_seen_key = "admin_last_seen_activity"
if _last_seen_key not in st.session_state:
    st.session_state[_last_seen_key] = None

def _get_agent_activity():
    """Fetch recent agent-created and soft-deleted records."""
    sb = get_supabase()

    # New records created by agents (non-admin)
    new_blends = (sb.table("blends")
                  .select("blend_name,client,created_by,created_at")
                  .not_.is_("created_by", "null")
                  .order("created_at", desc=True)
                  .limit(30).execute()).data
    new_soil = (sb.table("soil_analyses")
                .select("customer,crop,created_by,created_at")
                .not_.is_("created_by", "null")
                .order("created_at", desc=True)
                .limit(30).execute()).data

    # Soft-deleted records
    del_blends = (sb.table("blends")
                  .select("blend_name,client,deleted_by,deleted_at")
                  .not_.is_("deleted_at", "null")
                  .order("deleted_at", desc=True)
                  .limit(20).execute()).data
    del_soil = (sb.table("soil_analyses")
                .select("customer,crop,deleted_by,deleted_at")
                .not_.is_("deleted_at", "null")
                .order("deleted_at", desc=True)
                .limit(20).execute()).data

    return new_blends, new_soil, del_blends, del_soil

_new_blends, _new_soil, _del_blends, _del_soil = _get_agent_activity()

# Filter out admin's own records — only show agent activity
_admin_username = username
_created = []
for d in _new_blends:
    if d.get("created_by") != _admin_username:
        _created.append({
            "type": "Blend",
            "name": d.get("blend_name") or "Unnamed",
            "detail": d.get("client") or "",
            "by": d.get("created_by") or "unknown",
            "at": d.get("created_at") or "",
            "action": "created",
        })
for d in _new_soil:
    if d.get("created_by") != _admin_username:
        _created.append({
            "type": "Soil Analysis",
            "name": d.get("customer") or "Unknown",
            "detail": d.get("crop") or "",
            "by": d.get("created_by") or "unknown",
            "at": d.get("created_at") or "",
            "action": "created",
        })

_deleted = []
for d in _del_blends:
    _deleted.append({
        "type": "Blend",
        "name": d.get("blend_name") or "Unnamed",
        "detail": d.get("client") or "",
        "by": d.get("deleted_by") or "unknown",
        "at": d.get("deleted_at") or "",
        "action": "deleted",
    })
for d in _del_soil:
    _deleted.append({
        "type": "Soil Analysis",
        "name": d.get("customer") or "Unknown",
        "detail": d.get("crop") or "",
        "by": d.get("deleted_by") or "unknown",
        "at": d.get("deleted_at") or "",
        "action": "deleted",
    })

# Show only activity since last dismiss (or all on first visit)
last_seen = st.session_state[_last_seen_key]
if last_seen:
    new_created = [d for d in _created if d["at"] > last_seen]
    new_deleted = [d for d in _deleted if d["at"] > last_seen]
else:
    new_created = _created
    new_deleted = _deleted

_all_timestamps = [d["at"] for d in _created + _deleted if d["at"]]

if new_created or new_deleted:
    total = len(new_created) + len(new_deleted)
    with st.expander(f"Agent activity: {total} update(s) since last visit", expanded=True):
        if new_created:
            st.markdown(f"**New records ({len(new_created)})**")
            for d in sorted(new_created, key=lambda x: x["at"], reverse=True):
                try:
                    dt = datetime.fromisoformat(d["at"]).strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    dt = d["at"]
                detail = f" — {d['detail']}" if d["detail"] else ""
                st.markdown(f"- **{d['type']}:** {d['name']}{detail} — by **{d['by']}** on {dt}")

        if new_deleted:
            st.markdown(f":red[**Deleted records ({len(new_deleted)})**]")
            for d in sorted(new_deleted, key=lambda x: x["at"], reverse=True):
                try:
                    dt = datetime.fromisoformat(d["at"]).strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    dt = d["at"]
                detail = f" — {d['detail']}" if d["detail"] else ""
                st.markdown(f"- :red[**{d['type']}:** {d['name']}{detail} — deleted by **{d['by']}** on {dt}]")

        if st.button("Dismiss"):
            st.session_state[_last_seen_key] = max(_all_timestamps)
            st.rerun()


# ── Helper: display a blend card ───────────────────────────────────────────
def blend_card(blend, prefix=""):
    bid = blend["id"]
    key_prefix = f"{prefix}{bid}"
    created = datetime.fromisoformat(blend["created_at"]).strftime("%Y-%m-%d %H:%M")
    name = blend["blend_name"] or "Unnamed"
    client = blend.get("client") or ""
    farm = blend.get("farm") or ""
    cost = blend.get("cost_per_ton") or 0

    created_by = blend.get("created_by") or ""
    deleted_by = blend.get("deleted_by") or ""
    deleted_at = blend.get("deleted_at") or ""

    header = f"**{name}**"
    if client:
        header += f"  |  {client}"
    if farm:
        header += f"  |  {farm}"
    header += f"  |  R {cost:,.0f}/ton  |  {created}"
    if created_by:
        header += f"  |  by {created_by}"
    if deleted_at:
        del_time = datetime.fromisoformat(deleted_at).strftime("%Y-%m-%d %H:%M")
        header += f"  |  :red[DELETED by {deleted_by} on {del_time}]"

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
            try:
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
                ] if recipe else []
                nutrient_rows = [
                    [n.get("nutrient", ""), f"{n.get('target', 0):.3f}",
                     f"{n.get('actual', 0):.3f}", f"{n.get('diff', 0):.3f}",
                     f"{n.get('kg_per_ton', 0):.2f}"]
                    for n in nutrients
                ] if nutrients else []

                nut_map = {n.get("nutrient"): n.get("actual", 0) for n in nutrients}
                sa_nota = pct_to_sa_notation(
                    nut_map.get("N", 0), nut_map.get("P", 0), nut_map.get("K", 0)
                ) if nutrients else ""
                pdf_bytes = build_pdf(
                    new_name or "Unnamed", new_client or "", new_farm or "",
                    batch_size, compost_pct, cost_pt, total_cost, selling_price,
                    margin, False, 1.0, recipe_rows, nutrient_rows,
                    sa_notation=sa_nota,
                )
                dl_name = f"{new_name or 'blend'}_{new_client or 'unknown'}.pdf".replace(" ", "_")
                st.download_button(
                    "Reprint PDF", pdf_bytes, dl_name,
                    "application/pdf", key=f"dl_{key_prefix}",
                )
            except Exception as e:
                st.error(f"Could not generate PDF: {e}")

        with bc3:
            if st.button("Delete", key=f"del_{key_prefix}"):
                delete_blend(bid)
                st.success("Deleted!")
                st.rerun()


# ── Tabs ────────────────────────────────────────────────────────────────────
tab_search, tab_clients, tab_farms, tab_agents, tab_nutrients, tab_soil, tab_users, tab_markup, tab_backup = st.tabs(
    ["Search", "By Client", "By Farm", "By Agent", "By Nutrients", "Soil Analyses", "Users", "Markups", "Backup"]
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

# ── By Agent tab ───────────────────────────────────────────────────────────
with tab_agents:
    agents = fetch_unique_agents()
    if not agents:
        st.info("No agent records found.")
    else:
        selected_agent = st.selectbox("Select agent", agents, key="agent_filter")
        if selected_agent:
            agent_blends = fetch_blends_by_agent(selected_agent)
            agent_soil = fetch_soil_by_agent(selected_agent)

            active_blends = [b for b in agent_blends if not b.get("deleted_at")]
            deleted_blends = [b for b in agent_blends if b.get("deleted_at")]
            active_soil = [s for s in agent_soil if not s.get("deleted_at")]
            deleted_soil = [s for s in agent_soil if s.get("deleted_at")]

            m1, m2 = st.columns(2)
            m1.metric("Blends", f"{len(active_blends)} active, {len(deleted_blends)} deleted")
            m2.metric("Soil Analyses", f"{len(active_soil)} active, {len(deleted_soil)} deleted")

            if agent_blends:
                st.markdown("**Blends**")
                for b in agent_blends:
                    blend_card(b, prefix="agent_")

            if agent_soil:
                st.markdown("**Soil Analyses**")
                for sa in agent_soil:
                    sa_id = sa["id"]
                    created = datetime.fromisoformat(sa["created_at"]).strftime("%Y-%m-%d %H:%M")
                    cust = sa.get("customer") or "Unknown"
                    farm_sa = sa.get("farm") or ""
                    field_sa = sa.get("field") or ""
                    crop_sa = sa.get("crop") or ""
                    cost = sa.get("total_cost_ha") or 0
                    sa_deleted_by = sa.get("deleted_by") or ""
                    sa_deleted_at = sa.get("deleted_at") or ""

                    header = f"**{cust}**"
                    if farm_sa:
                        header += f"  |  {farm_sa}"
                    if field_sa:
                        header += f"  |  {field_sa}"
                    if crop_sa:
                        header += f"  |  {crop_sa}"
                    header += f"  |  R{cost:,.0f}/ha  |  {created}"
                    if sa_deleted_at:
                        del_time = datetime.fromisoformat(sa_deleted_at).strftime("%Y-%m-%d %H:%M")
                        header += f"  |  :red[DELETED by {sa_deleted_by} on {del_time}]"

                    with st.expander(header):
                        sv = sa.get("soil_values") or {}
                        if sv:
                            st.markdown("**Soil Values**")
                            sv_df = pd.DataFrame([
                                {"Parameter": k, "Value": v} for k, v in sv.items()
                            ])
                            st.dataframe(sv_df, use_container_width=True, hide_index=True)

                        nt = sa.get("nutrient_targets") or []
                        if nt:
                            with st.expander("Nutrient Targets"):
                                nt_df = pd.DataFrame(nt)
                                st.dataframe(nt_df, use_container_width=True, hide_index=True)

                        prods = sa.get("products") or []
                        if prods:
                            st.markdown("**Products**")
                            prod_df = pd.DataFrame([{
                                "Product": p.get("product", ""),
                                "Method": p.get("method", ""),
                                "Timing": p.get("timing", ""),
                                "Kg/Ha": f"{p.get('kg_ha', 0):.0f}",
                                "Price/Ton": f"R{p.get('price_per_ton', 0):,.2f}",
                                "Price/Ha": f"R{p.get('price_ha', 0):,.2f}",
                            } for p in prods])
                            st.dataframe(prod_df, use_container_width=True, hide_index=True)

                        rr = sa.get("ratio_results") or []
                        if rr:
                            with st.expander("Nutrient Ratios"):
                                rr_df = pd.DataFrame(rr)
                                st.dataframe(rr_df, use_container_width=True, hide_index=True)

                        try:
                            norms = load_soil_norms()
                            plants_pf = None
                            if sa.get("pop_per_ha") and sa.get("field_area_ha"):
                                plants_pf = int(sa["pop_per_ha"] * sa["field_area_ha"])
                            pdf_bytes = build_soil_pdf(
                                customer=cust, farm=farm_sa, field=field_sa,
                                crop_name=crop_sa,
                                cultivar=sa.get("cultivar") or crop_sa,
                                yield_target=sa.get("yield_target") or 0,
                                yield_unit=sa.get("yield_unit") or "",
                                pop_per_ha=sa.get("pop_per_ha"),
                                plants_per_field=plants_pf,
                                field_area_ha=sa.get("field_area_ha"),
                                agent_name=sa.get("agent_name") or "",
                                agent_cell=sa.get("agent_cell") or "",
                                agent_email=sa.get("agent_email") or "",
                                lab_name=sa.get("lab_name") or "",
                                analysis_date=sa.get("analysis_date") or "",
                                soil_values=sv,
                                nutrient_targets=nt,
                                ratio_results=rr,
                                products=prods,
                                total_cost_ha=cost,
                                norms=norms,
                                role=role,
                            )
                            dl_name = f"Recommendation_{cust}_{crop_sa}.pdf".replace(" ", "_")
                            st.download_button(
                                "Reprint PDF", pdf_bytes, dl_name,
                                "application/pdf", key=f"agent_sa_dl_{sa_id}",
                            )
                        except Exception as e:
                            st.error(f"PDF error: {e}")

            if not agent_blends and not agent_soil:
                st.info(f"No records found for {selected_agent}.")

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

# ── Soil Analyses tab ──────────────────────────────────────────────────────
with tab_soil:
    soil_search = st.text_input("Search soil analyses",
                                 placeholder="Search by customer, farm, or crop...",
                                 key="soil_search")
    analyses = fetch_soil_analyses(soil_search if soil_search else None)

    if not analyses:
        st.info("No soil analyses found.")
    else:
        st.caption(f"{len(analyses)} analysis/analyses")

        for sa in analyses:
            sa_id = sa["id"]
            created = datetime.fromisoformat(sa["created_at"]).strftime("%Y-%m-%d %H:%M")
            cust = sa.get("customer") or "Unknown"
            farm_sa = sa.get("farm") or ""
            field_sa = sa.get("field") or ""
            crop_sa = sa.get("crop") or ""
            cost = sa.get("total_cost_ha") or 0
            sa_created_by = sa.get("created_by") or ""
            sa_deleted_by = sa.get("deleted_by") or ""
            sa_deleted_at = sa.get("deleted_at") or ""

            header = f"**{cust}**"
            if farm_sa:
                header += f"  |  {farm_sa}"
            if field_sa:
                header += f"  |  {field_sa}"
            if crop_sa:
                header += f"  |  {crop_sa}"
            header += f"  |  R{cost:,.0f}/ha  |  {created}"
            if sa_created_by:
                header += f"  |  by {sa_created_by}"
            if sa_deleted_at:
                del_time = datetime.fromisoformat(sa_deleted_at).strftime("%Y-%m-%d %H:%M")
                header += f"  |  :red[DELETED by {sa_deleted_by} on {del_time}]"

            with st.expander(header):
                # Soil values
                sv = sa.get("soil_values") or {}
                if sv:
                    st.markdown("**Soil Values**")
                    sv_df = pd.DataFrame([
                        {"Parameter": k, "Value": v} for k, v in sv.items()
                    ])
                    st.dataframe(sv_df, use_container_width=True, hide_index=True)

                # Nutrient targets
                nt = sa.get("nutrient_targets") or []
                if nt:
                    with st.expander("Nutrient Targets"):
                        nt_df = pd.DataFrame(nt)
                        st.dataframe(nt_df, use_container_width=True, hide_index=True)

                # Products
                prods = sa.get("products") or []
                if prods:
                    st.markdown("**Products / Blend**")
                    prod_df = pd.DataFrame([{
                        "Product": p.get("product", ""),
                        "Method": p.get("method", ""),
                        "Timing": p.get("timing", ""),
                        "Kg/Ha": f"{p.get('kg_ha', 0):.0f}",
                        "Price/Ha": f"R{p.get('price_ha', 0):,.2f}",
                        "Price/Ton": f"R{p.get('price_per_ton', 0):,.2f}",
                    } for p in prods])
                    st.dataframe(prod_df, use_container_width=True, hide_index=True)

                # Ratio results
                rr = sa.get("ratio_results") or []
                if rr:
                    with st.expander("Nutrient Ratios"):
                        rr_df = pd.DataFrame(rr)
                        st.dataframe(rr_df, use_container_width=True, hide_index=True)

                # Actions
                st.markdown("---")
                ac1, ac2 = st.columns(2)

                # Reprint PDF
                with ac1:
                    try:
                        norms = load_soil_norms()
                        plants_pf = None
                        if sa.get("pop_per_ha") and sa.get("field_area_ha"):
                            plants_pf = int(sa["pop_per_ha"] * sa["field_area_ha"])
                        pdf_bytes = build_soil_pdf(
                            customer=cust,
                            farm=farm_sa,
                            field=field_sa,
                            crop_name=crop_sa,
                            cultivar=sa.get("cultivar") or crop_sa,
                            yield_target=sa.get("yield_target") or 0,
                            yield_unit=sa.get("yield_unit") or "",
                            pop_per_ha=sa.get("pop_per_ha"),
                            plants_per_field=plants_pf,
                            field_area_ha=sa.get("field_area_ha"),
                            agent_name=sa.get("agent_name") or "",
                            agent_cell=sa.get("agent_cell") or "",
                            agent_email=sa.get("agent_email") or "",
                            lab_name=sa.get("lab_name") or "",
                            analysis_date=sa.get("analysis_date") or "",
                            soil_values=sv,
                            nutrient_targets=nt,
                            ratio_results=rr,
                            products=prods,
                            total_cost_ha=cost,
                            norms=norms,
                            role=role,
                        )
                        dl_name = f"Recommendation_{cust}_{crop_sa}.pdf".replace(" ", "_")
                        st.download_button(
                            "Reprint PDF", pdf_bytes, dl_name,
                            "application/pdf", key=f"sa_dl_{sa_id}",
                        )
                    except Exception as e:
                        st.error(f"PDF error: {e}")

                # Delete
                with ac2:
                    if st.button("Delete", key=f"sa_del_{sa_id}"):
                        delete_soil_analysis(sa_id)
                        st.success("Deleted!")
                        st.rerun()

# ── Users tab ──────────────────────────────────────────────────────────────
with tab_users:
    st.markdown("**User Management**")
    st.caption(
        "Edit user details directly in the table below. "
        "Click **Save Changes** to persist. To reset a password or delete a user, "
        "use the controls below the table."
    )

    users = fetch_all_users()

    if users:
        # Build editable dataframe
        user_rows = []
        for u in users:
            user_rows.append({
                "Username": u["username"],
                "Name": u["name"],
                "Email": u.get("email") or "",
                "Phone": u.get("phone") or "",
                "Company": u.get("company") or "",
                "Role": u["role"],
            })
        user_df = pd.DataFrame(user_rows)

        user_col_config = {
            "Username": st.column_config.TextColumn("Username", disabled=True),
            "Name": st.column_config.TextColumn("Name", required=True),
            "Email": st.column_config.TextColumn("Email"),
            "Phone": st.column_config.TextColumn("Phone"),
            "Company": st.column_config.TextColumn("Company"),
            "Role": st.column_config.SelectboxColumn(
                "Role", options=["sales_agent", "admin"], required=True,
            ),
        }

        edited_users = st.data_editor(
            user_df,
            column_config=user_col_config,
            num_rows="fixed",
            use_container_width=True,
            hide_index=True,
            key="users_editor",
        )

        if st.button("Save Changes", key="save_users_btn"):
            updated_count = 0
            for _, row in edited_users.iterrows():
                uname = row["Username"]
                orig = next((u for u in users if u["username"] == uname), None)
                if not orig:
                    continue
                changes = {}
                if row["Name"] != orig["name"]:
                    changes["name"] = row["Name"]
                if row["Email"] != (orig.get("email") or ""):
                    changes["email"] = row["Email"] or None
                if row["Phone"] != (orig.get("phone") or ""):
                    changes["phone"] = row["Phone"] or None
                if row["Company"] != (orig.get("company") or ""):
                    changes["company"] = row["Company"] or None
                if row["Role"] != orig["role"]:
                    changes["role"] = row["Role"]
                if changes:
                    try:
                        update_user(uname, changes)
                        updated_count += 1
                    except Exception as e:
                        st.error(f"Failed to update {uname}: {e}")
            if updated_count > 0:
                reload_auth()
                # Clear cached user profile so soil analysis picks up changes
                st.session_state.pop("_user_profile", None)
                st.success(f"Updated {updated_count} user(s).")
                st.rerun()
            else:
                st.info("No changes detected.")

        # Reset password / Delete user
        st.markdown("---")
        st.markdown("**Reset Password / Delete User**")
        user_names = [u["username"] for u in users]
        selected_user = st.selectbox("Select user", user_names, key="pw_user_select")

        pw1, pw2 = st.columns(2)
        with pw1:
            new_pw = st.text_input("New password", type="password", key="reset_pw")
            if st.button("Reset Password", key="reset_pw_btn"):
                if not new_pw:
                    st.warning("Enter a new password.")
                else:
                    pw_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                    try:
                        update_user(selected_user, {"password_hash": pw_hash})
                        reload_auth()
                        st.success(f"Password reset for '{selected_user}'.")
                    except Exception as e:
                        st.error(f"Failed: {e}")

        with pw2:
            if selected_user != username:
                st.markdown("")  # spacing
                st.markdown("")
                if st.button("Delete User", key="delete_user_btn"):
                    try:
                        delete_user(selected_user)
                        reload_auth()
                        st.success(f"User '{selected_user}' deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")
            else:
                st.caption("Cannot delete your own account.")

    st.markdown("---")
    st.markdown("**Add New User**")

    uc1, uc2 = st.columns(2)
    with uc1:
        new_username = st.text_input("Username *", placeholder="e.g. jsmith",
                                      key="new_username")
        new_name = st.text_input("Full name *", placeholder="e.g. John Smith",
                                  key="new_fullname")
        new_email = st.text_input("Email", placeholder="e.g. john@example.com",
                                   key="new_email")
    with uc2:
        new_phone = st.text_input("Phone", placeholder="e.g. 082 123 4567",
                                   key="new_phone")
        new_company = st.text_input("Company", placeholder="e.g. AgriCo Resellers",
                                     key="new_company")
        new_role = st.selectbox("Role", ["sales_agent", "admin"], key="new_role")

    new_password = st.text_input("Password *", type="password", key="new_password")

    if st.button("Create User", key="create_user_btn"):
        if not new_username or not new_name or not new_password:
            st.warning("Username, full name, and password are required.")
        elif any(u["username"] == new_username for u in users):
            st.error(f"Username '{new_username}' already exists.")
        else:
            pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            try:
                create_user(new_username, new_name, new_email, new_phone,
                           new_company, new_role, pw_hash)
                reload_auth()
                st.success(f"User '{new_username}' created!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create user: {e}")

# ── Materials & Markups tab ────────────────────────────────────────────────
with tab_markup:
    st.markdown("**Raw Materials & Agent Markups**")
    st.caption(
        "Edit materials, costs, and nutrient content directly. "
        "Set markup % per material — agents see Base Cost x (1 + Markup %). "
        "Add or remove rows as needed. Click **Save Changes** to persist."
    )

    from shared import save_materials

    mat_df = load_materials()
    markups = load_markups()

    # Build editable dataframe with markup column
    edit_df = mat_df.copy()
    edit_df.insert(3, "Markup %", edit_df["Material"].map(markups).fillna(0))
    edit_df.insert(4, "Agent Price (R/ton)",
                   edit_df["Cost (R/ton)"] * (1 + edit_df["Markup %"] / 100))

    # Column config for the editor
    col_config = {
        "Material": st.column_config.TextColumn("Material", required=True),
        "Type": st.column_config.SelectboxColumn(
            "Type", options=sorted(mat_df["Type"].unique().tolist()),
            required=True,
        ),
        "Cost (R/ton)": st.column_config.NumberColumn(
            "Base Cost (R/ton)", min_value=0, format="R%.2f", required=True,
        ),
        "Markup %": st.column_config.NumberColumn(
            "Markup %", min_value=0, format="%.1f",
        ),
        "Agent Price (R/ton)": st.column_config.NumberColumn(
            "Agent Price (R/ton)", format="R%.2f", disabled=True,
        ),
    }
    # Nutrient columns
    nutrient_cols = [c for c in mat_df.columns if c not in ["Material", "Type", "Cost (R/ton)"]]
    for nc in nutrient_cols:
        col_config[nc] = st.column_config.NumberColumn(nc, min_value=0, format="%.4f")

    edited = st.data_editor(
        edit_df,
        column_config=col_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="materials_editor",
    )

    if st.button("Save Changes", key="save_materials_btn"):
        # Separate markup data from material data
        new_markups = {}
        for _, row in edited.iterrows():
            mat_name = row.get("Material")
            if mat_name:
                m_pct = row.get("Markup %", 0) or 0
                if m_pct > 0:
                    new_markups[mat_name] = m_pct

        # Save markups to Supabase
        for mat_name, m_pct in new_markups.items():
            save_markup(mat_name, m_pct)
        # Clear markups for removed materials
        for old_mat in markups:
            if old_mat not in new_markups:
                save_markup(old_mat, 0)

        # Save materials to Supabase (drop markup columns)
        save_df = edited.drop(columns=["Markup %", "Agent Price (R/ton)"], errors="ignore")
        save_df = save_df.dropna(subset=["Material"])  # remove empty rows

        try:
            save_materials(save_df)
            load_markups.clear()
            st.success(f"Saved {len(save_df)} materials and {len(new_markups)} markups.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save: {e}")

# ── Backup tab ──────────────────────────────────────────────────────────────
with tab_backup:
    st.markdown("**Download Backup**")
    st.caption("Export all blends as a JSON file. IDs are included so restoring won't create duplicates.")

    if st.button("Generate Backup"):
        all_blends = fetch_all_blends()
        all_soil = fetch_all_soil_analyses()
        backup = {"blends": all_blends, "soil_analyses": all_soil}
        backup_json = json.dumps(backup, indent=2, default=str)
        st.download_button(
            f"Download backup ({len(all_blends)} blends, {len(all_soil)} soil analyses)",
            backup_json,
            f"sapling_backup_{datetime.now().strftime('%Y%m%d')}.json",
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
