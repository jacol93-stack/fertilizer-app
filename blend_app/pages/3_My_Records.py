import streamlit as st
import pandas as pd
from datetime import datetime
from shared import (
    apply_styles, show_header, show_mobile_nav, build_pdf, build_soil_pdf, pct_to_sa_notation,
    fetch_blends, fetch_soil_analyses,
    soft_delete_blend, soft_delete_soil_analysis,
    load_soil_norms, NUTRIENTS_SOIL, ORANGE, DARK_GREY, MED_GREY,
)
from auth import require_auth, logout_button, is_admin

st.set_page_config(page_title="My Records — Sapling", layout="wide")
apply_styles()

name, role, username = require_auth()
logout_button()
show_mobile_nav("My_Records")

# Admin uses the full Database page instead
if is_admin():
    st.info("Admin: use the **Database** page for full access.")
    st.stop()

show_header("My Records")

tab_blends, tab_soil = st.tabs(["My Blends", "My Soil Analyses"])

# ── My Blends ─────────────────────────────────────────────────────────────
with tab_blends:
    search = st.text_input("Search my blends", placeholder="Search by name, client, or farm...",
                            key="mr_blend_search")
    blends = fetch_blends(search_term=search if search else None,
                          role=role, username=username)

    if not blends:
        st.info("No blends found.")
    else:
        st.caption(f"{len(blends)} blend(s)")

        for b in blends:
            bid = b["id"]
            created = datetime.fromisoformat(b["created_at"]).strftime("%Y-%m-%d %H:%M")
            bname = b.get("blend_name") or "Unnamed"
            client = b.get("client") or ""
            farm = b.get("farm") or ""
            cost = b.get("cost_per_ton") or 0

            header = f"**{bname}**"
            if client:
                header += f"  |  {client}"
            if farm:
                header += f"  |  {farm}"
            header += f"  |  R{cost:,.0f}/ton  |  {created}"

            with st.expander(header):
                # Nutrient analysis (no raw costs)
                nutrients = b.get("nutrients") or []
                if nutrients:
                    nut_df = pd.DataFrame(nutrients).rename(columns={
                        "nutrient": "Nutrient", "target": "Target %",
                        "actual": "Actual %", "diff": "Diff",
                        "kg_per_ton": "kg per ton",
                    })
                    st.dataframe(nut_df, use_container_width=True, hide_index=True)

                col1, col2 = st.columns(2)

                # Reprint PDF (no recipe details for agents)
                with col1:
                    try:
                        batch_size = b.get("batch_size") or 1000
                        cost_pt = float(b.get("cost_per_ton") or 0)
                        recipe = b.get("recipe") or []
                        total_kg = sum(r.get("kg", 0) for r in recipe)
                        total_cost = sum(r.get("cost", 0) for r in recipe)
                        compost_kg = sum(r.get("kg", 0) for r in recipe
                                         if r.get("material") == "Manure Compost")
                        compost_pct = (compost_kg / total_kg * 100) if total_kg > 0 else 0

                        nut_map = {n.get("nutrient"): n.get("actual", 0) for n in nutrients}
                        sa_nota = pct_to_sa_notation(
                            nut_map.get("N", 0), nut_map.get("P", 0), nut_map.get("K", 0)
                        ) if nutrients else ""

                        nutrient_rows = [
                            [n.get("nutrient", ""), f"{n.get('target', 0):.3f}",
                             f"{n.get('actual', 0):.3f}", f"{n.get('diff', 0):.3f}",
                             f"{n.get('kg_per_ton', 0):.2f}"]
                            for n in nutrients
                        ] if nutrients else []

                        # Agent PDF: no recipe rows
                        pdf_bytes = build_pdf(
                            bname, client, farm, batch_size,
                            compost_pct, cost_pt, total_cost, 0,
                            None, False, 1.0, [], nutrient_rows,
                            sa_notation=sa_nota,
                        )
                        dl_name = f"{bname}_{client}.pdf".replace(" ", "_")
                        st.download_button(
                            "Reprint PDF", pdf_bytes, dl_name,
                            "application/pdf", key=f"mr_dl_{bid}",
                        )
                    except Exception as e:
                        st.error(f"PDF error: {e}")

                # Soft delete
                with col2:
                    if st.button("Delete", key=f"mr_del_{bid}"):
                        soft_delete_blend(bid, username)
                        st.success("Removed from your records.")
                        st.rerun()

# ── My Soil Analyses ──────────────────────────────────────────────────────
with tab_soil:
    soil_search = st.text_input("Search my soil analyses",
                                 placeholder="Search by customer, farm, or crop...",
                                 key="mr_soil_search")
    analyses = fetch_soil_analyses(search_term=soil_search if soil_search else None,
                                   role=role, username=username)

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

            header = f"**{cust}**"
            if farm_sa:
                header += f"  |  {farm_sa}"
            if field_sa:
                header += f"  |  {field_sa}"
            if crop_sa:
                header += f"  |  {crop_sa}"
            header += f"  |  R{cost:,.0f}/ha  |  {created}"

            with st.expander(header):
                # Soil values
                sv = sa.get("soil_values") or {}
                if sv:
                    st.markdown("**Soil Values**")
                    sv_df = pd.DataFrame([
                        {"Parameter": k, "Value": v} for k, v in sv.items()
                    ])
                    st.dataframe(sv_df, use_container_width=True, hide_index=True)

                # Products (no raw costs visible — prices are already marked up)
                prods = sa.get("products") or []
                if prods:
                    st.markdown("**Products**")
                    prod_df = pd.DataFrame([{
                        "Product": p.get("product", ""),
                        "Kg/Ha": f"{p.get('kg_ha', 0):.0f}",
                        "Price/Ha": f"R{p.get('price_ha', 0):,.2f}",
                    } for p in prods])
                    st.dataframe(prod_df, use_container_width=True, hide_index=True)

                col1, col2 = st.columns(2)

                # Reprint PDF
                with col1:
                    try:
                        norms = load_soil_norms()
                        nt = sa.get("nutrient_targets") or []
                        rr = sa.get("ratio_results") or []
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
                            "application/pdf", key=f"mr_sa_dl_{sa_id}",
                        )
                    except Exception as e:
                        st.error(f"PDF error: {e}")

                # Soft delete
                with col2:
                    if st.button("Delete", key=f"mr_sa_del_{sa_id}"):
                        soft_delete_soil_analysis(sa_id, username)
                        st.success("Removed from your records.")
                        st.rerun()
