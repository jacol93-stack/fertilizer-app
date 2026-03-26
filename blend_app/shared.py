import io
import pathlib
import json
import numpy as np
import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import date
from supabase import create_client

_HERE = pathlib.Path(__file__).parent
LOGO_PATH = _HERE / "assets" / "logo.png"
LOGO_NO_SLOGAN_PATH = _HERE / "assets" / "logo_no_slogan.png"

COMPOST_NAME = "Manure Compost"

# ── SA Notation helpers ────────────────────────────────────────────────────
def sa_notation_to_pct(n_ratio, p_ratio, k_ratio, total_pct):
    """Convert SA notation like 2:3:2 (22) to individual N, P, K percentages."""
    ratio_sum = n_ratio + p_ratio + k_ratio
    if ratio_sum == 0:
        return 0.0, 0.0, 0.0
    per_part = total_pct / ratio_sum
    return n_ratio * per_part, p_ratio * per_part, k_ratio * per_part


def pct_to_sa_notation(n_pct, p_pct, k_pct):
    """Convert N, P, K percentages to SA notation like '2:3:2 (22)'.
    Tries multipliers to find the best small whole-number ratio that
    accurately represents the proportions."""
    total = n_pct + p_pct + k_pct
    if total < 0.01:
        return "0:0:0 (0)"

    vals = [n_pct, p_pct, k_pct]
    non_zero = [v for v in vals if v > 0.001]
    if not non_zero:
        return f"0:0:0 ({total:.0f})"

    # Try many possible divisors to find the cleanest small integer ratio.
    # For each candidate divisor, round to integers and measure error
    # against the original proportions.
    best_ratios = None
    best_error = float("inf")
    best_max = float("inf")

    for denom_x10 in range(1, 200):  # try divisors from 0.1 to 20.0
        denom = denom_x10 / 10.0
        trial = [round(v / denom) if v > 0.001 else 0 for v in vals]
        if max(trial) > 20 or max(trial) == 0:
            continue
        ratio_sum = sum(trial)
        if ratio_sum == 0:
            continue
        # Measure proportional error
        error = 0
        for i in range(3):
            expected_pct = trial[i] / ratio_sum
            actual_pct = vals[i] / total if total > 0 else 0
            error += abs(expected_pct - actual_pct)
        # Prefer smaller ratios when error is similar
        if (error < best_error - 0.002
            or (abs(error - best_error) < 0.002 and sum(trial) < sum(best_ratios or [999]))):
            best_error = error
            best_ratios = trial
            best_max = max(trial)

    if best_ratios is None:
        min_val = min(non_zero)
        best_ratios = [round(v / min_val) for v in vals]

    return f"{best_ratios[0]}:{best_ratios[1]}:{best_ratios[2]} ({total:.0f})"


# ── Brand colours ──────────────────────────────────────────────────────────
ORANGE = "#ff4f00"
DARK_GREY = "#191919"
MED_GREY = "#4d4d4d"
ORANGE_RGB = (255, 79, 0)
DARK_GREY_RGB = (25, 25, 25)
MED_GREY_RGB = (77, 77, 77)
ORANGE_LIGHT = "#fff3eb"
ORANGE_FILL_RGB = (255, 243, 235)
GREY_LIGHT_RGB = (245, 245, 245)


def apply_styles():
    st.markdown(f"""
    <style>
        /* ── Import professional font ────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* ── Base ────────────────────────────────────────────── */
        html, body, .stApp, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}
        .stApp, .main .block-container,
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"] {{
            background-color: #f8f9fa !important;
        }}
        .main .block-container {{
            max-width: 1200px !important;
            padding-top: 2rem !important;
        }}

        /* ── Dark sidebar ────────────────────────────────────── */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {DARK_GREY} 0%, #2a2a2a 100%) !important;
            border-right: none !important;
            box-shadow: 4px 0 20px rgba(0,0,0,0.15);
        }}
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: #ffffff !important;
            font-weight: 600 !important;
            letter-spacing: -0.01em;
        }}
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stCaption p {{
            color: #b0b0b0 !important;
        }}
        section[data-testid="stSidebar"] input {{
            background-color: #333333 !important;
            border-color: #444444 !important;
            color: #ffffff !important;
        }}
        section[data-testid="stSidebar"] input:focus {{
            border-color: {ORANGE} !important;
            box-shadow: 0 0 0 1px {ORANGE} !important;
        }}
        section[data-testid="stSidebar"] .stCheckbox label span {{
            color: #cccccc !important;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: #444444 !important;
            opacity: 0.6 !important;
        }}
        /* sidebar nav links */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{
            color: #cccccc !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{
            color: {ORANGE} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-selected="true"] {{
            color: {ORANGE} !important;
            font-weight: 600;
        }}
        /* sidebar selectbox / dropdown */
        section[data-testid="stSidebar"] [data-baseweb="select"] {{
            background-color: #333333 !important;
        }}
        section[data-testid="stSidebar"] [data-baseweb="select"] * {{
            color: #ffffff !important;
            background-color: transparent !important;
        }}

        /* ── Typography ──────────────────────────────────────── */
        h1 {{
            color: {DARK_GREY} !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
            font-size: 1.8rem !important;
        }}
        h2 {{
            color: {DARK_GREY} !important;
            font-weight: 600 !important;
            letter-spacing: -0.01em;
            font-size: 1.3rem !important;
            border-bottom: 2px solid {ORANGE};
            padding-bottom: 0.4rem;
            margin-bottom: 1rem !important;
        }}
        h3 {{
            color: {MED_GREY} !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
        }}
        p, li, span, label {{
            color: {MED_GREY};
            font-size: 0.92rem;
        }}

        /* ── Metrics ─────────────────────────────────────────── */
        [data-testid="stMetricValue"] {{
            color: {ORANGE} !important;
            font-weight: 700 !important;
            font-size: 1.6rem !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: {MED_GREY} !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            font-size: 0.75rem !important;
            letter-spacing: 0.05em;
        }}
        [data-testid="stMetricDelta"] {{
            font-weight: 500 !important;
        }}
        /* Metric card wrapper */
        [data-testid="stMetric"] {{
            background: #ffffff;
            border: 1px solid #e8e8e8;
            border-radius: 10px;
            padding: 1rem 1.2rem !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }}

        /* ── Buttons ─────────────────────────────────────────── */
        .stDownloadButton > button, .stButton > button {{
            background-color: {ORANGE} !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            padding: 0.5rem 1.2rem !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 6px rgba(255,79,0,0.25) !important;
            letter-spacing: 0.01em;
        }}
        .stDownloadButton > button:hover, .stButton > button:hover {{
            background-color: {DARK_GREY} !important;
            color: #ffffff !important;
            box-shadow: 0 2px 8px rgba(25,25,25,0.3) !important;
            transform: translateY(-1px);
        }}
        .stDownloadButton > button:active, .stButton > button:active {{
            transform: translateY(0);
        }}

        /* ── Inputs ──────────────────────────────────────────── */
        .stNumberInput input, .stTextInput input, .stDateInput input {{
            border: 1.5px solid #e0e0e0 !important;
            border-radius: 8px !important;
            color: {DARK_GREY} !important;
            background-color: #ffffff !important;
            padding: 0.5rem 0.75rem !important;
            font-size: 0.9rem !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }}
        .stNumberInput input:focus, .stTextInput input:focus, .stDateInput input:focus {{
            border-color: {ORANGE} !important;
            box-shadow: 0 0 0 3px rgba(255,79,0,0.12) !important;
        }}
        /* Input labels */
        .stNumberInput label, .stTextInput label, .stSelectbox label,
        .stDateInput label, .stSlider label {{
            font-weight: 500 !important;
            color: {MED_GREY} !important;
            font-size: 0.85rem !important;
        }}

        /* ── Radio buttons & checkboxes ──────────────────────── */
        .stRadio [role="radiogroup"] label {{
            background: #ffffff;
            border: 1.5px solid #e0e0e0;
            border-radius: 8px;
            padding: 0.4rem 1rem !important;
            margin-right: 0.5rem;
            transition: all 0.15s ease;
        }}
        .stRadio [role="radiogroup"] label:has(input:checked) {{
            background: {ORANGE} !important;
            border-color: {ORANGE} !important;
            color: #ffffff !important;
        }}
        .stRadio [role="radiogroup"] label:has(input:checked) p,
        .stRadio [role="radiogroup"] label:has(input:checked) span {{
            color: #ffffff !important;
        }}

        /* ── Tabs ────────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0;
            background: #ffffff;
            border-radius: 10px;
            padding: 4px;
            border: 1px solid #e8e8e8;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 0.5rem 1.2rem;
            font-weight: 500;
            color: {MED_GREY};
            border: none;
            background: transparent;
        }}
        .stTabs [aria-selected="true"] {{
            background: {ORANGE} !important;
            color: #ffffff !important;
            font-weight: 600;
            box-shadow: 0 2px 6px rgba(255,79,0,0.2);
        }}
        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] {{
            display: none !important;
        }}

        /* ── Expanders ───────────────────────────────────────── */
        .streamlit-expanderHeader {{
            color: {MED_GREY} !important;
            font-weight: 500 !important;
            font-size: 0.92rem !important;
            background: #ffffff;
            border-radius: 8px;
        }}
        [data-testid="stExpander"] {{
            background: #ffffff;
            border: 1px solid #e8e8e8 !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            overflow: hidden;
        }}
        [data-testid="stExpander"] details {{
            border: none !important;
        }}

        /* ── Data tables ─────────────────────────────────────── */
        [data-testid="stDataFrame"] {{
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }}

        /* ── Dividers ────────────────────────────────────────── */
        hr {{
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, #e0e0e0, transparent) !important;
            margin: 1.5rem 0 !important;
            opacity: 1 !important;
        }}

        /* ── Sliders ─────────────────────────────────────────── */
        .stSlider [role="slider"] {{
            background-color: {ORANGE} !important;
        }}
        .stSlider [data-baseweb="slider"] div[role="progressbar"] > div {{
            background-color: {ORANGE} !important;
        }}

        /* ── Alerts / Info boxes ──────────────────────────────── */
        .stAlert {{
            border-radius: 10px !important;
            border: none !important;
            font-size: 0.9rem;
        }}

        /* ── Selectbox ───────────────────────────────────────── */
        [data-baseweb="select"] > div {{
            border-radius: 8px !important;
            border-color: #e0e0e0 !important;
        }}
        [data-baseweb="select"] > div:focus-within {{
            border-color: {ORANGE} !important;
            box-shadow: 0 0 0 3px rgba(255,79,0,0.12) !important;
        }}

        /* ── Scrollbar ───────────────────────────────────────── */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #ccc;
            border-radius: 3px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {ORANGE};
        }}

        /* ── Mobile bottom nav bar ─────────────────────────── */
        @media (max-width: 768px) {{
            .mobile-nav {{
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: {DARK_GREY};
                border-top: none;
                display: flex;
                justify-content: space-around;
                align-items: center;
                z-index: 999999;
                padding: 8px 0 env(safe-area-inset-bottom, 8px);
                box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
            }}
            .mobile-nav a {{
                text-decoration: none;
                color: #999999;
                font-size: 0.7rem;
                text-align: center;
                padding: 4px 2px;
                flex: 1;
                line-height: 1.2;
                font-weight: 500;
                transition: color 0.15s ease;
            }}
            .mobile-nav a.active {{
                color: {ORANGE};
                font-weight: 700;
            }}
            .mobile-nav a:hover {{
                color: {ORANGE};
            }}
            .mobile-nav a span.nav-icon {{
                font-size: 1.3rem;
                display: block;
                margin-bottom: 2px;
            }}
            .main .block-container {{
                padding-bottom: 80px !important;
            }}
        }}
        @media (min-width: 769px) {{
            .mobile-nav {{ display: none; }}
        }}
    </style>
    """, unsafe_allow_html=True)


def show_mobile_nav(current_page="Blend_Calculator"):
    """Render a fixed bottom nav bar visible only on mobile (≤768px)."""
    role = st.session_state.get("auth_role", "sales_agent")
    pages = [
        ("Blend_Calculator", "/", "🧪", "Blend Calc"),
    ]
    if role == "admin":
        pages.append(("Database", "/Database", "🗄️", "Database"))
    pages += [
        ("Soil_Analysis", "/Soil_Analysis", "🌱", "Soil Analysis"),
        ("My_Records", "/My_Records", "📋", "My Records"),
    ]

    links = []
    for key, href, icon, label in pages:
        cls = ' class="active"' if key == current_page else ""
        links.append(
            f'<a href="{href}" target="_self"{cls}><span class="nav-icon">{icon}</span>{label}</a>'
        )
    st.markdown(
        f'<div class="mobile-nav">{"".join(links)}</div>',
        unsafe_allow_html=True,
    )


def show_header(title="Blend Calculator"):
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 1.2rem;
        padding: 0.6rem 1.5rem;
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #e8e8e8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem;
        min-height: 94px;
    ">
        <img src="data:image/png;base64,{_logo_base64()}" style="height: 80px; width: auto;" />
        <div>
            <h1 style="margin:0; padding:0; font-size:1.5rem; color:{DARK_GREY}; border:none; letter-spacing:-0.02em">{title}</h1>
            <p style="margin:0; padding:0; font-size:0.8rem; color:#999; letter-spacing:0.02em">Fertilise Smarter, Grow Stronger</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


LOGO_ICON_PATH = _HERE / "assets" / "logo_icon_only.png"

def _logo_base64():
    """Return base64-encoded logo for inline HTML embedding."""
    import base64
    # Prefer the tight-cropped icon, then no-slogan, then full logo
    for p in [LOGO_ICON_PATH, LOGO_NO_SLOGAN_PATH, LOGO_PATH]:
        if p.exists():
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""


# ── Supabase ───────────────────────────────────────────────────────────────
def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


@st.cache_data(ttl=120)
def load_materials():
    """Load materials from Supabase. Raises error if unavailable."""
    sb = get_supabase()
    result = sb.table("materials").select("*").execute()
    if not result.data:
        raise RuntimeError("No materials found in database. Add materials via the Markups tab.")
    col_map = {
        "material": "Material", "type": "Type", "cost_per_ton": "Cost (R/ton)",
        "n": "N", "p": "P", "k": "K", "ca": "Ca", "mg": "Mg", "s": "S",
        "fe": "Fe", "b": "B", "mn": "Mn", "zn": "Zn", "mo": "Mo",
        "cu": "Cu", "c": "C",
    }
    df = pd.DataFrame(result.data).rename(columns=col_map)
    expected = ["Material", "Type", "Cost (R/ton)",
                "N", "P", "K", "Ca", "Mg", "S",
                "Fe", "B", "Mn", "Zn", "Mo", "Cu", "C"]
    df = df[[c for c in expected if c in df.columns]]
    for col in df.columns:
        if col not in ["Material", "Type"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.fillna(0)


# ── User management ───────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_all_users():
    try:
        sb = get_supabase()
        result = sb.table("users").select("*").order("created_at", desc=True).execute()
        return result.data
    except Exception:
        return []


def save_materials(df):
    """Save materials DataFrame to Supabase (upsert all, delete removed)."""
    sb = get_supabase()
    col_map = {
        "Material": "material", "Type": "type", "Cost (R/ton)": "cost_per_ton",
        "N": "n", "P": "p", "K": "k", "Ca": "ca", "Mg": "mg", "S": "s",
        "Fe": "fe", "B": "b", "Mn": "mn", "Zn": "zn", "Mo": "mo",
        "Cu": "cu", "C": "c",
    }
    rows = []
    new_names = set()
    for _, row in df.iterrows():
        r = {}
        for ui_col, db_col in col_map.items():
            if ui_col in row.index:
                val = row[ui_col]
                r[db_col] = str(val) if db_col in ("material", "type") else float(val or 0)
            else:
                r[db_col] = 0
        if r["material"]:
            rows.append(r)
            new_names.add(r["material"])

    # Upsert current materials
    if rows:
        sb.table("materials").upsert(rows).execute()

    # Delete materials that were removed
    existing = sb.table("materials").select("material").execute()
    for e in existing.data:
        if e["material"] not in new_names:
            sb.table("materials").delete().eq("material", e["material"]).execute()

    load_materials.clear()


def fetch_user(username):
    sb = get_supabase()
    result = sb.table("users").select("*").eq("username", username).execute()
    return result.data[0] if result.data else None


def create_user(username, name, email, phone, company, role, password_hash):
    sb = get_supabase()
    sb.table("users").insert({
        "username": username,
        "name": name,
        "email": email or None,
        "phone": phone or None,
        "company": company or None,
        "role": role,
        "password_hash": password_hash,
    }).execute()
    fetch_all_users.clear()


def update_user(username, updates):
    sb = get_supabase()
    sb.table("users").update(updates).eq("username", username).execute()
    fetch_all_users.clear()


def delete_user(username):
    sb = get_supabase()
    sb.table("users").delete().eq("username", username).execute()
    fetch_all_users.clear()


# ── Markup helpers ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_markups():
    try:
        sb = get_supabase()
        result = sb.table("material_markups").select("*").execute()
        return {r["material"]: float(r["markup_pct"]) for r in result.data}
    except Exception:
        return {}


def save_markup(material, markup_pct):
    sb = get_supabase()
    sb.table("material_markups").upsert({
        "material": material,
        "markup_pct": float(markup_pct),
    }).execute()
    load_markups.clear()


def load_materials_with_markup(role="admin"):
    """Return materials df. For sales_agent, replace Cost (R/ton) with marked-up cost."""
    df = load_materials()
    if role == "admin":
        return df
    markups = load_markups()
    df = df.copy()
    for i, row in df.iterrows():
        m = markups.get(row["Material"], 0)
        df.at[i, "Cost (R/ton)"] = row["Cost (R/ton)"] * (1 + m / 100)
    return df


# ── Default material selections (admin → agent) ─────────────────────────

_HARDCODED_DEFAULTS = {
    "Urea 46%", "MAP 33%", "DAP",
    "KCL (Potassium Chloride)", "Gypsum",
    "KAN 28%", "Calcitic Lime",
}


@st.cache_data(ttl=120)
def _load_default_materials_cached():
    """Load admin-set default material names from Supabase (cached).
    Falls back to hardcoded defaults if the table/row doesn't exist."""
    try:
        sb = get_supabase()
        result = sb.table("default_materials").select("materials").execute()
        if result.data and result.data[0].get("materials"):
            return list(result.data[0]["materials"])
    except Exception:
        pass
    return list(_HARDCODED_DEFAULTS)


def load_default_materials():
    """Return the admin-set default materials as a set."""
    return set(_load_default_materials_cached())


def save_default_materials(material_names):
    """Persist the admin's selected default materials to Supabase.
    Uses a single row with id=1 (upsert)."""
    sb = get_supabase()
    sb.table("default_materials").upsert({
        "id": 1,
        "materials": list(material_names),
    }).execute()
    _load_default_materials_cached.clear()


# ── Blend CRUD ────────────────────────────────────────────────────────────

def save_blend(blend_name, client, farm, batch_size, min_compost_pct,
               selling_price, cost_per_ton, targets, recipe_rows, nutrients,
               selected_materials, created_by=None):
    sb = get_supabase()
    data = {
        "blend_name": blend_name or "Unnamed",
        "client": client or None,
        "farm": farm or None,
        "batch_size": batch_size,
        "min_compost_pct": min_compost_pct,
        "selling_price": float(selling_price),
        "cost_per_ton": float(cost_per_ton),
        "targets": targets,
        "recipe": recipe_rows,
        "nutrients": nutrients,
        "selected_materials": selected_materials,
        "created_by": created_by,
    }
    result = sb.table("blends").insert(data).execute()
    return result


def fetch_blends(search_term=None, role="admin", username=None):
    sb = get_supabase()
    query = sb.table("blends").select("*").order("created_at", desc=True)
    if role == "sales_agent" and username:
        query = query.eq("created_by", username).is_("deleted_at", "null")
    if search_term:
        query = query.or_(
            f"blend_name.ilike.%{search_term}%,"
            f"client.ilike.%{search_term}%,"
            f"farm.ilike.%{search_term}%"
        )
    result = query.execute()
    return result.data


def update_blend(blend_id, updates):
    sb = get_supabase()
    sb.table("blends").update(updates).eq("id", blend_id).execute()


def soft_delete_blend(blend_id, username):
    """Soft-delete: mark as deleted but keep record."""
    sb = get_supabase()
    from datetime import datetime
    sb.table("blends").update({
        "deleted_by": username,
        "deleted_at": datetime.utcnow().isoformat(),
    }).eq("id", blend_id).execute()


def delete_blend(blend_id):
    sb = get_supabase()
    sb.table("blends").delete().eq("id", blend_id).execute()


def fetch_all_blends():
    """Fetch all blends for backup export."""
    sb = get_supabase()
    result = sb.table("blends").select("*").order("created_at", desc=True).execute()
    return result.data


def restore_blends(blends_json):
    """Restore blends from backup JSON, skipping duplicates by ID."""
    sb = get_supabase()
    existing = sb.table("blends").select("id").execute()
    existing_ids = {r["id"] for r in existing.data}

    new_blends = [b for b in blends_json if b["id"] not in existing_ids]
    if not new_blends:
        return 0

    sb.table("blends").insert(new_blends).execute()
    return len(new_blends)


def fetch_unique_clients():
    sb = get_supabase()
    result = sb.table("blends").select("client").not_.is_("client", "null").execute()
    return sorted(set(r["client"] for r in result.data if r["client"]))


def fetch_unique_farms():
    sb = get_supabase()
    result = sb.table("blends").select("farm").not_.is_("farm", "null").execute()
    return sorted(set(r["farm"] for r in result.data if r["farm"]))


def fetch_blends_by_client(client_name):
    sb = get_supabase()
    result = (sb.table("blends").select("*")
              .eq("client", client_name)
              .order("created_at", desc=True).execute())
    return result.data


def fetch_blends_by_farm(farm_name):
    sb = get_supabase()
    result = (sb.table("blends").select("*")
              .eq("farm", farm_name)
              .order("created_at", desc=True).execute())
    return result.data


def fetch_unique_agents():
    """Return sorted list of unique created_by usernames (non-null)."""
    sb = get_supabase()
    blend_rows = sb.table("blends").select("created_by").not_.is_("created_by", "null").execute()
    soil_rows = sb.table("soil_analyses").select("created_by").not_.is_("created_by", "null").execute()
    agents = set()
    for r in blend_rows.data:
        if r["created_by"]:
            agents.add(r["created_by"])
    for r in soil_rows.data:
        if r["created_by"]:
            agents.add(r["created_by"])
    return sorted(agents)


def fetch_blends_by_agent(agent_username):
    sb = get_supabase()
    result = (sb.table("blends").select("*")
              .eq("created_by", agent_username)
              .order("created_at", desc=True).execute())
    return result.data


def fetch_soil_by_agent(agent_username):
    sb = get_supabase()
    result = (sb.table("soil_analyses").select("*")
              .eq("created_by", agent_username)
              .order("created_at", desc=True).execute())
    return result.data


# ── Soil Analysis CRUD ────────────────────────────────────────────────────

def save_soil_analysis(customer, farm, field, crop, cultivar,
                       yield_target, yield_unit, field_area_ha, pop_per_ha,
                       agent_name, agent_cell, agent_email,
                       lab_name, analysis_date,
                       soil_values, nutrient_targets, ratio_results,
                       products, total_cost_ha, created_by=None):
    sb = get_supabase()
    data = {
        "customer": customer or None,
        "farm": farm or None,
        "field": field or None,
        "crop": crop or None,
        "cultivar": cultivar or None,
        "yield_target": float(yield_target) if yield_target else None,
        "yield_unit": yield_unit or None,
        "field_area_ha": float(field_area_ha) if field_area_ha else None,
        "pop_per_ha": int(pop_per_ha) if pop_per_ha else None,
        "agent_name": agent_name or None,
        "agent_cell": agent_cell or None,
        "agent_email": agent_email or None,
        "lab_name": lab_name or None,
        "analysis_date": str(analysis_date) if analysis_date else None,
        "soil_values": soil_values,
        "nutrient_targets": nutrient_targets,
        "ratio_results": ratio_results,
        "products": products,
        "total_cost_ha": float(total_cost_ha) if total_cost_ha else 0,
        "created_by": created_by,
    }
    result = sb.table("soil_analyses").insert(data).execute()
    return result


def fetch_soil_analyses(search_term=None, role="admin", username=None):
    sb = get_supabase()
    query = sb.table("soil_analyses").select("*").order("created_at", desc=True)
    if role == "sales_agent" and username:
        query = query.eq("created_by", username).is_("deleted_at", "null")
    if search_term:
        query = query.or_(
            f"customer.ilike.%{search_term}%,"
            f"farm.ilike.%{search_term}%,"
            f"crop.ilike.%{search_term}%"
        )
    result = query.execute()
    return result.data


def fetch_all_soil_analyses():
    sb = get_supabase()
    result = sb.table("soil_analyses").select("*").order("created_at", desc=True).execute()
    return result.data


def soft_delete_soil_analysis(analysis_id, username):
    """Soft-delete: mark as deleted but keep record."""
    sb = get_supabase()
    from datetime import datetime
    sb.table("soil_analyses").update({
        "deleted_by": username,
        "deleted_at": datetime.utcnow().isoformat(),
    }).eq("id", analysis_id).execute()


def delete_soil_analysis(analysis_id):
    """Hard delete (admin only)."""
    sb = get_supabase()
    sb.table("soil_analyses").delete().eq("id", analysis_id).execute()


# ── Pricing suggestion ─────────────────────────────────────────────────────

def _cost_per_nutrient_pct():
    """Calculate R cost to add 1% of each nutrient to a 1-ton blend,
    using the cheapest viable source from materials.xlsx.

    Returns dict like {"N": 255.6, "P": 312.5, "K": 219.0}
    """
    df = load_materials()
    cost_col = "Cost (R/ton)"
    result = {}
    for nut in ("N", "P", "K"):
        best = float("inf")
        for _, row in df.iterrows():
            pct = row.get(nut, 0)
            cost = row.get(cost_col, 0)
            # Skip compost (mixed source) and placeholder-priced materials
            if pct > 1 and 0 < cost < 500_000:
                # R to get 10kg of nutrient (= 1% of 1 ton)
                kg_needed = 10.0 / (pct / 100)
                r_cost = kg_needed * (cost / 1000)
                if r_cost < best:
                    best = r_cost
        result[nut] = round(best, 1) if best < float("inf") else 1.0
    return result


def _get_nutrient_weights():
    """Return weights proportional to R-per-% for each nutrient,
    normalised so the cheapest = 1.0."""
    cpn = _cost_per_nutrient_pct()
    min_cost = min(cpn.values())
    return {k: round(v / min_cost, 2) for k, v in cpn.items()}, cpn


def _npk_dict(nutrients_list):
    """Extract {N, P, K} actual percentages."""
    d = {"N": 0, "P": 0, "K": 0}
    for n in (nutrients_list or []):
        if n["nutrient"] in d:
            d[n["nutrient"]] = n.get("actual", 0)
    return d


def suggest_price(actual_n, actual_p, actual_k, compost_pct,
                  cost_tolerance=500, min_matches=3):
    """Look up historical blends near the given NPK profile and return
    pricing suggestions.

    Similarity is measured as a cost-weighted distance:
      distance = sum( |diff_nutrient| * R_per_%_nutrient )
    This means a 1% difference in P (expensive) counts more than
    a 1% difference in N (cheaper).

    cost_tolerance is the max acceptable distance in Rands -i.e.
    "these two blends differ by no more than R500 worth of nutrients".

    Returns dict with keys:
        found      – number of comparable blends
        low        – low-end selling price (25th percentile)
        mid        – median selling price
        high       – high-end selling price (75th percentile)
        comparables – list of dicts with blend details
        method     – 'tight' | 'widened' | 'regression'
        weights    – the R/% weights used
    or None if no data at all.
    """
    weights, cpn = _get_nutrient_weights()

    sb = get_supabase()
    all_blends = sb.table("blends").select(
        "blend_name, client, cost_per_ton, selling_price, "
        "min_compost_pct, nutrients, created_at"
    ).order("created_at", desc=True).execute().data

    if not all_blends:
        return None

    import statistics

    # ── Step 1: find comparable blends by cost-weighted distance ──────────
    def cost_distance(npk):
        return (abs(npk["N"] - actual_n) * cpn["N"]
                + abs(npk["P"] - actual_p) * cpn["P"]
                + abs(npk["K"] - actual_k) * cpn["K"])

    def find_matches(tol):
        matches = []
        for b in all_blends:
            npk = _npk_dict(b.get("nutrients"))
            dist = cost_distance(npk)
            if dist <= tol:
                price = b.get("selling_price") or b.get("cost_per_ton") or 0
                if price > 0:
                    matches.append({
                        "blend_name": b["blend_name"],
                        "client": b.get("client", ""),
                        "price": price,
                        "cost": b.get("cost_per_ton", 0),
                        "compost_pct": b.get("min_compost_pct", 0),
                        "npk": npk,
                        "distance": round(dist),
                        "date": (b.get("created_at") or "")[:10],
                    })
        return matches

    matches = find_matches(cost_tolerance)
    method = "tight"

    if len(matches) < min_matches:
        matches = find_matches(cost_tolerance * 2)
        method = "widened"

    # ── Step 2: regression fallback using ALL blends ──────────────────────
    prices_all = []
    features_all = []
    for b in all_blends:
        price = b.get("selling_price") or b.get("cost_per_ton") or 0
        if price <= 0:
            continue
        npk = _npk_dict(b.get("nutrients"))
        w = npk["N"] * cpn["N"] + npk["P"] * cpn["P"] + npk["K"] * cpn["K"]
        cp = b.get("min_compost_pct", 50)
        features_all.append((w, cp))
        prices_all.append(price)

    regression = None
    if len(prices_all) >= 5:
        import numpy as _np
        X = _np.array([[f[0], f[1], 1] for f in features_all])
        y = _np.array(prices_all)
        try:
            coeffs, _, _, _ = _np.linalg.lstsq(X, y, rcond=None)
            w_new = (actual_n * cpn["N"] + actual_p * cpn["P"]
                     + actual_k * cpn["K"])
            predicted = coeffs[0] * w_new + coeffs[1] * compost_pct + coeffs[2]
            regression = {
                "predicted": round(max(predicted, 0), 0),
                "r_per_weighted_npk": round(coeffs[0], 2),
                "r_per_compost_pct": round(coeffs[1], 0),
            }
        except Exception:
            pass

    # ── Step 3: build result ──────────────────────────────────────────────
    if not matches and regression:
        p = regression["predicted"]
        return {
            "found": 0,
            "low": round(p * 0.90),
            "mid": round(p),
            "high": round(p * 1.10),
            "comparables": [],
            "method": "regression",
            "regression": regression,
            "weights": cpn,
        }

    if not matches:
        return None

    prices = sorted(m["price"] for m in matches)

    if len(prices) == 1:
        low = mid = high = prices[0]
    elif len(prices) == 2:
        low, high = prices[0], prices[1]
        mid = statistics.mean(prices)
    else:
        low = prices[len(prices) // 4]
        mid = statistics.median(prices)
        high = prices[-(len(prices) // 4) - 1]

    return {
        "found": len(matches),
        "low": round(low),
        "mid": round(mid),
        "high": round(high),
        "comparables": sorted(matches, key=lambda m: m["distance"]),
        "method": method,
        "regression": regression,
        "weights": cpn,
    }


# ── PDF builder ────────────────────────────────────────────────────────────
def build_pdf(blend_name, client, farm, batch, compost_pct, cost_per_ton,
              total_cost, selling_price, margin, is_relaxed, relaxed_scale,
              recipe_data, nutrient_data, sa_notation=None,
              pricing_suggestion=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Header: logo top-right, title + slogan just above orange line
    logo_h = 50
    top_margin = 10
    line_y = top_margin + logo_h + 6

    logo_path = LOGO_NO_SLOGAN_PATH if LOGO_NO_SLOGAN_PATH.exists() else LOGO_PATH
    if logo_path.exists():
        pdf.image(str(logo_path), x=200 - logo_h * 1.2, y=top_margin, h=logo_h)

    pdf.set_xy(10, line_y - 17)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(0, 12, "Blend Recipe", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(0, 5, "Fertilise Smarter, Grow Stronger", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(line_y)

    # Accent line
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
    kpi_items = []
    if sa_notation:
        kpi_items.append(f"SA Notation: {sa_notation}")
    # International NPK from nutrient_data (first 3 rows are N, P, K)
    if nutrient_data:
        intl_parts = []
        for row in nutrient_data[:3]:
            # row = [Nutrient, Target%, Actual%, Diff, kg_per_ton]
            try:
                intl_parts.append(f"{float(row[2]):.1f}")
            except (ValueError, IndexError):
                intl_parts.append("0.0")
        if len(intl_parts) == 3:
            kpi_items.append(f"International: N {intl_parts[0]}% - P {intl_parts[1]}% - K {intl_parts[2]}%")
    kpi_items.append(f"Batch size: {batch:,} kg")
    if recipe_data:
        # Only show compost/chemical breakdown for admin (who gets recipe_data)
        kpi_items.append(f"Compost: {compost_pct:.1f}%")
        kpi_items.append(f"Chemical: {100 - compost_pct:.1f}%")
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

    def pdf_table(title, columns, widths, rows):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 9)
        header_y = pdf.get_y()
        total_w = sum(widths)
        pdf.set_fill_color(*ORANGE_RGB)
        pdf.rect(pdf.l_margin, header_y, total_w, 6, "F")
        pdf.set_text_color(255, 255, 255)
        for label, w in zip(columns, widths):
            pdf.cell(w, 6, label)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for i, row_vals in enumerate(rows):
            row_y = pdf.get_y()
            if i % 2 == 1:
                pdf.set_fill_color(*GREY_LIGHT_RGB)
                pdf.rect(pdf.l_margin, row_y, total_w, 5, "F")
            pdf.set_text_color(*DARK_GREY_RGB)
            for val, w in zip(row_vals, widths):
                pdf.cell(w, 5, val)
            pdf.ln()

        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.4)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + total_w, pdf.get_y())
        pdf.ln(4)

    # Recipe table
    if recipe_data:
        recipe_cols = ["Material", "Type", "kg", "% of Blend", "Cost (R)"]
        col_widths = [60, 35, 25, 25, 25]
        pdf_table("Recipe", recipe_cols, col_widths, recipe_data)

    # Nutrient analysis table -only show targeted nutrients
    if nutrient_data:
        nut_cols = ["Nutrient", "Target %", "Actual %", "Diff", "kg per ton"]
        nut_widths = [30, 25, 25, 25, 25]
        try:
            targeted_rows = [r for r in nutrient_data if float(r[1]) > 0]
        except (ValueError, IndexError):
            targeted_rows = nutrient_data
        pdf_table("Nutrient Analysis", nut_cols, nut_widths, targeted_rows)

    # ── Page 2: Pricing Analysis (if available) ──────────────────────────
    if pricing_suggestion and pricing_suggestion.get("found", 0) > 0:
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 12, "Pricing Analysis", new_x="LMARGIN", new_y="NEXT")

        # Accent line
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        # Method note
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MED_GREY_RGB)
        w = pricing_suggestion.get("weights", {})
        if pricing_suggestion["method"] == "tight":
            method_txt = (f"Based on {pricing_suggestion['found']} similar blends "
                          f"(within R500 cost-weighted nutrient distance)")
        elif pricing_suggestion["method"] == "widened":
            method_txt = (f"Based on {pricing_suggestion['found']} broadly similar blends "
                          f"(within R1,000 -widened due to few close matches)")
        else:
            method_txt = "Estimate from regression model using all historical blends"
        pdf.cell(0, 5, method_txt, new_x="LMARGIN", new_y="NEXT")
        if w:
            pdf.cell(0, 5,
                     f"Nutrient cost weights:  N: R{w.get('N',0):,.0f}/%   "
                     f"P: R{w.get('P',0):,.0f}/%   K: R{w.get('K',0):,.0f}/%",
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Price summary boxes
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 8, "Suggested Selling Price", new_x="LMARGIN", new_y="NEXT")

        box_y = pdf.get_y()
        box_w = 45
        box_h = 22
        gap = 3
        labels = ["Your Cost", "Low", "Mid", "High"]
        values = [
            f"R {cost_per_ton:,.0f}",
            f"R {pricing_suggestion['low']:,.0f}",
            f"R {pricing_suggestion['mid']:,.0f}",
            f"R {pricing_suggestion['high']:,.0f}",
        ]
        margins_list = [
            None,
            pricing_suggestion['low'] - cost_per_ton,
            pricing_suggestion['mid'] - cost_per_ton,
            pricing_suggestion['high'] - cost_per_ton,
        ]

        for i, (lbl, val, mgn) in enumerate(zip(labels, values, margins_list)):
            x = pdf.l_margin + i * (box_w + gap)
            # Box background
            if i == 0:
                pdf.set_fill_color(*GREY_LIGHT_RGB)
            else:
                pdf.set_fill_color(*ORANGE_FILL_RGB)
            pdf.rect(x, box_y, box_w, box_h, "F")
            # Border
            pdf.set_draw_color(*ORANGE_RGB)
            pdf.set_line_width(0.3)
            pdf.rect(x, box_y, box_w, box_h, "D")
            # Label
            pdf.set_xy(x, box_y + 2)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(box_w, 4, lbl, align="C")
            # Value
            pdf.set_xy(x, box_y + 7)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(box_w, 6, val, align="C")
            # Margin
            if mgn is not None:
                pdf.set_xy(x, box_y + 15)
                pdf.set_font("Helvetica", "", 7)
                color = (0, 130, 0) if mgn >= 0 else (200, 0, 0)
                pdf.set_text_color(*color)
                pdf.cell(box_w, 4, f"R {mgn:,.0f} margin", align="C")

        pdf.set_y(box_y + box_h + 6)

        # Regression note
        if pricing_suggestion.get("regression"):
            reg = pricing_suggestion["regression"]
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(0, 5,
                     f"Regression model estimate: R {reg['predicted']:,.0f}/ton",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        # Comparable blends table
        comps = pricing_suggestion.get("comparables", [])
        if comps:
            comp_cols = ["Blend", "Client", "Price", "Cost", "Dist.", "N%", "P%", "K%", "Date"]
            comp_widths = [38, 22, 20, 20, 16, 12, 12, 12, 22]
            comp_rows = []
            for c in comps:
                comp_rows.append([
                    str(c["blend_name"])[:22],
                    str(c.get("client", ""))[:12],
                    f"R{c['price']:,.0f}",
                    f"R{c['cost']:,.0f}",
                    f"R{c.get('distance', 0):,.0f}",
                    f"{c['npk']['N']:.1f}",
                    f"{c['npk']['P']:.1f}",
                    f"{c['npk']['K']:.1f}",
                    str(c.get("date", ""))[:10],
                ])
            pdf_table("Comparable Historical Blends", comp_cols, comp_widths,
                      comp_rows)

    elif pricing_suggestion and pricing_suggestion.get("method") == "regression":
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 12, "Pricing Analysis", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.cell(0, 6, "No close historical matches. Regression estimate:",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_GREY_RGB)
        for lbl, val in [("Low", pricing_suggestion["low"]),
                         ("Mid", pricing_suggestion["mid"]),
                         ("High", pricing_suggestion["high"])]:
            pdf.cell(0, 6, f"{lbl}: R {val:,.0f}  "
                     f"(margin R {val - cost_per_ton:,.0f})",
                     new_x="LMARGIN", new_y="NEXT")

    # Footer on last page
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(0, 5, "Generated by Sapling Blend Calculator - Internal Document",
             new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ── Soil Analysis helpers ─────────────────────────────────────────────────

SOIL_NORMS_PATH = _HERE / "data" / "soil_norms.xlsx"

NUTRIENTS_SOIL = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Mo", "Cu"]

SOIL_CLASSIFICATIONS = ["Very Low", "Low", "Optimal", "High", "Very High"]

CLASSIFICATION_COLOURS = {
    "Very Low":  "#d32f2f",
    "Low":       "#f57c00",
    "Optimal":   "#388e3c",
    "High":      "#1976d2",
    "Very High": "#7b1fa2",
}


@st.cache_data
def load_soil_norms():
    """Load all sheets from soil_norms.xlsx into a dict of DataFrames.
    Numeric columns are auto-coerced and NaN filled with 0, just like
    load_materials()."""
    xls = pd.ExcelFile(SOIL_NORMS_PATH)
    norms = {}
    # Columns that are always text -everything else gets coerced to numeric
    TEXT_COLS = {
        "Crop", "Type", "Yield_Unit", "Parameter", "Unit", "Notes",
        "Classification", "Description", "Ratio", "Method",
        "Typical_Crops", "Crop_Nutrient", "Soil_Parameter",
    }
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, header=1)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        for col in df.columns:
            if col not in TEXT_COLS:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.fillna(0)
        norms[sheet] = df
    return norms


def classify_soil_value(value, param_name, sufficiency_df):
    """Classify a soil analysis value against sufficiency thresholds.
    Returns one of: Very Low, Low, Optimal, High, Very High, or '' if no match."""
    if value is None or pd.isna(value):
        return ""
    row = sufficiency_df[sufficiency_df["Parameter"] == param_name]
    if row.empty:
        return ""
    r = row.iloc[0]
    if value <= r["Very_Low_Max"]:
        return "Very Low"
    elif value <= r["Low_Max"]:
        return "Low"
    elif value <= r["Optimal_Max"]:
        return "Optimal"
    elif value <= r["High_Max"]:
        return "High"
    else:
        return "Very High"


def get_adjustment_factor(classification, adjustment_df):
    """Look up the adjustment factor for a soil classification level."""
    if not classification:
        return 1.0
    row = adjustment_df[adjustment_df["Classification"] == classification]
    if row.empty:
        return 1.0
    return float(row.iloc[0]["Factor"])


def calculate_nutrient_targets(crop_name, yield_target, soil_values, norms):
    """Calculate adjusted nutrient targets (kg/ha) for a crop.

    Args:
        crop_name: Name matching Crop column in Crop_Requirements
        yield_target: Expected yield in the crop's yield unit
        soil_values: Dict of {soil_parameter: value} from lab results
        norms: Dict of DataFrames from load_soil_norms()

    Returns:
        List of dicts with nutrient, base_req, adjustment, adjusted_target, classification
    """
    crop_df = norms["Crop_Requirements"]
    suf_df = norms["Soil_Sufficiency"]
    adj_df = norms["Adjustment_Factors"]
    param_map_df = norms["Soil_Parameter_Map"]

    crop_row = crop_df[crop_df["Crop"] == crop_name]
    if crop_row.empty:
        return []

    crop_row = crop_row.iloc[0]
    results = []

    for nut in NUTRIENTS_SOIL:
        per_unit = float(crop_row.get(nut, 0) or 0)
        base_req = round(per_unit * yield_target, 2)

        # Find the soil parameter that maps to this crop nutrient
        map_row = param_map_df[param_map_df["Crop_Nutrient"] == nut]
        soil_param = map_row.iloc[0]["Soil_Parameter"] if not map_row.empty else nut
        soil_val = soil_values.get(soil_param)

        classification = classify_soil_value(soil_val, soil_param, suf_df)
        factor = get_adjustment_factor(classification, adj_df)
        adjusted = round(base_req * factor, 2)

        results.append({
            "Nutrient": nut,
            "Per_Unit": per_unit,
            "Base_Req_kg_ha": base_req,
            "Soil_Value": soil_val if soil_val is not None else "",
            "Classification": classification,
            "Factor": factor,
            "Target_kg_ha": adjusted,
        })

    return results


def evaluate_ratios(soil_values, norms):
    """Evaluate soil nutrient ratios against ideal ranges.

    Args:
        soil_values: Dict of {soil_parameter: value}
        norms: Dict of DataFrames from load_soil_norms()

    Returns:
        List of dicts with ratio name, actual value, ideal range, status
    """
    ratio_df = norms["Ideal_Ratios"]
    results = []

    # Helper to get soil value by partial match
    def sv(key):
        v = soil_values.get(key)
        if v is not None and v > 0:
            return v
        return None

    ca = sv("Ca")
    mg = sv("Mg")
    k = sv("K")
    na = sv("Na")
    fe = sv("Fe")
    mn = sv("Mn")
    p = sv("P (Bray-1)") or sv("P (Citric acid)")
    zn = sv("Zn")
    n = sv("N (total)")
    s = sv("S")
    cec = sv("CEC")

    computed = {}
    if ca and mg:
        computed["Ca:Mg"] = round(ca / mg, 2)
    if ca and k:
        computed["Ca:K"] = round(ca / k, 2)
    if mg and k:
        computed["Mg:K"] = round(mg / k, 2)
    if ca and mg and k:
        computed["(Ca+Mg):K"] = round((ca + mg) / k, 2)
    if p and zn:
        computed["P:Zn"] = round(p / zn, 2)
    if fe and mn:
        computed["Fe:Mn"] = round(fe / mn, 2)
    if n and s:
        computed["N:S"] = round(n / s, 2)
    if k and na:
        computed["K:Na"] = round(k / na, 2)

    # Base saturation (if CEC available, convert mg/kg to cmol/kg)
    if cec and cec > 0:
        # Conversion: mg/kg to cmol/kg using equivalent weights
        ca_cmol = (ca / 200.4) if ca else 0
        mg_cmol = (mg / 121.6) if mg else 0
        k_cmol = (k / 390.96) if k else 0
        na_cmol = (na / 230.0) if na else 0
        computed["Ca base sat."] = round(ca_cmol / cec * 100, 1)
        computed["Mg base sat."] = round(mg_cmol / cec * 100, 1)
        computed["K base sat."] = round(k_cmol / cec * 100, 1)
        computed["Na base sat."] = round(na_cmol / cec * 100, 1)
        total_bases = ca_cmol + mg_cmol + k_cmol + na_cmol
        computed["H+Al base sat."] = round(max((cec - total_bases) / cec * 100, 0), 1)

    for _, row in ratio_df.iterrows():
        name = row["Ratio"]
        actual = computed.get(name)
        if actual is None:
            continue
        ideal_min = float(row["Ideal_Min"])
        ideal_max = float(row["Ideal_Max"])
        if actual < ideal_min:
            status = "Below ideal"
        elif actual > ideal_max:
            status = "Above ideal"
        else:
            status = "Ideal"

        results.append({
            "Ratio": name,
            "Actual": actual,
            "Ideal_Min": ideal_min,
            "Ideal_Max": ideal_max,
            "Unit": row["Unit"],
            "Status": status,
        })

    return results


# ── Soil Analysis PDF builder ─────────────────────────────────────────────

# Visual chart colour palette (RGB tuples)
_CLS_RGB = {
    "Very Low":  (229, 57, 53),
    "Low":       (255, 152, 0),
    "Optimal":   (67, 160, 71),
    "High":      (41, 121, 255),
    "Very High": (142, 36, 170),
}
_CLS_LIGHT = {
    "Very Low":  (255, 205, 210),
    "Low":       (255, 224, 178),
    "Optimal":   (200, 230, 201),
    "High":      (187, 222, 251),
    "Very High": (225, 190, 231),
}
_STATUS_RGB = {
    "Below ideal": (229, 57, 53),
    "Ideal":       (67, 160, 71),
    "Above ideal": (41, 121, 255),
}


# ── Blend Optimizer ──────────────────────────────────────────────────────────

def run_optimizer(target_dict, df_mat, batch_size, c_idx, min_pct):
    """Linear-program blend optimizer. Returns scipy OptimizeResult."""
    from scipy.optimize import linprog
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
    """Binary-search for the highest achievable fraction of targets."""
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


def build_soil_pdf(customer, farm, field, crop_name, cultivar, yield_target,
                   yield_unit, pop_per_ha, plants_per_field, field_area_ha,
                   agent_name, agent_cell, agent_email,
                   lab_name, analysis_date,
                   soil_values, nutrient_targets, ratio_results,
                   products, total_cost_ha,
                   norms=None, total_cost_field=None, role="admin"):
    """Build a Fertilizer Recommendation Report PDF with visual analysis.

    Args:
        products: list of dicts with keys: product, method, timing,
                  kg_ha, kg_field, price_ha, price_field, nutrients (dict)
        norms: dict of DataFrames from load_soil_norms() (for gauge thresholds)
    """
    pdf = FPDF(orientation="L")
    pdf.set_auto_page_break(auto=False)

    page_w = 297  # A4 landscape
    page_h = 210
    margin = 10
    content_w = page_w - 2 * margin

    logo_path = LOGO_NO_SLOGAN_PATH if LOGO_NO_SLOGAN_PATH.exists() else LOGO_PATH

    # ─── Shared helpers ─────────────────────────────────────────────────

    def page_header(title):
        if logo_path.exists():
            pdf.image(str(logo_path), x=margin, y=8, h=22)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.set_xy(margin + 30, 10)
        pdf.cell(content_w - 30, 10, title, align="C")
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.8)
        pdf.line(margin, 30, page_w - margin, 30)

    def page_footer():
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.set_xy(margin, page_h - 12)
        pdf.cell(content_w / 2, 4,
                 "Generated by Sapling Blend Calculator")
        pdf.cell(content_w / 2, 4,
                 f"Date Printed:  {date.today().strftime('%Y-%m-%d')}",
                 align="R")

    def section_label(y, text):
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(content_w, 5, text, new_x="LMARGIN", new_y="NEXT")
        # thin accent underline
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.3)
        pdf.line(margin, y + 5.5, margin + content_w, y + 5.5)

    # ─── Gauge-bar drawing ──────────────────────────────────────────────

    def draw_gauge(x, y, w, h, value, thresholds):
        """Draw a horizontal gauge bar with 5 coloured zones, marker, and scale."""
        vl, lo, opt, hi = thresholds
        max_scale = hi * 1.35 if hi > 0 else 1
        if value > max_scale:
            max_scale = value * 1.15

        zones = [
            (0,   vl,  _CLS_RGB["Very Low"]),
            (vl,  lo,  _CLS_RGB["Low"]),
            (lo,  opt, _CLS_RGB["Optimal"]),
            (opt, hi,  _CLS_RGB["High"]),
            (hi,  max_scale, _CLS_RGB["Very High"]),
        ]

        # Draw each zone
        for z_start, z_end, colour in zones:
            x0 = x + (z_start / max_scale) * w
            x1 = x + min(z_end / max_scale, 1.0) * w
            zw = x1 - x0
            if zw < 0.2:
                continue
            light = _CLS_LIGHT.get(
                [k for k, v in _CLS_RGB.items() if v == colour][0], colour)
            pdf.set_fill_color(*light)
            pdf.set_draw_color(*colour)
            pdf.set_line_width(0.15)
            pdf.rect(x0, y, zw, h, "FD")

        # Optimal zone highlight
        ox0 = x + (lo / max_scale) * w
        ox1 = x + min(opt / max_scale, 1.0) * w
        pdf.set_draw_color(*_CLS_RGB["Optimal"])
        pdf.set_line_width(0.5)
        pdf.rect(ox0, y, ox1 - ox0, h, "D")

        # Scale labels below bar — zone boundaries
        scale_y = y + h + 0.8
        pdf.set_font("Helvetica", "B", 7)
        boundaries = [vl, lo, opt, hi]
        for bv in boundaries:
            bx = x + (bv / max_scale) * w
            fmt = ".0f" if bv >= 10 else (".1f" if bv >= 1 else ".2f")
            # Tick mark
            pdf.set_draw_color(150, 150, 150)
            pdf.set_line_width(0.15)
            pdf.line(bx, y + h, bx, y + h + 1.5)
            # Label
            pdf.set_text_color(100, 100, 100)
            pdf.set_xy(bx - 6, scale_y)
            pdf.cell(12, 4, f"{bv:{fmt}}", align="C")

        # Value marker — diamond
        marker_x = x + min(value / max_scale, 1.0) * w
        marker_y = y + h / 2
        d = h * 0.45
        pdf.set_fill_color(*DARK_GREY_RGB)
        pdf.set_draw_color(*DARK_GREY_RGB)
        pdf.set_line_width(0.1)
        pdf.polygon([
            (marker_x, marker_y - d),
            (marker_x + d * 0.6, marker_y),
            (marker_x, marker_y + d),
            (marker_x - d * 0.6, marker_y),
        ], style="F")

    def draw_classification_badge(x, y, w, h, classification):
        colour = _CLS_RGB.get(classification, MED_GREY_RGB)
        pdf.set_fill_color(*colour)
        pdf.set_draw_color(*colour)
        pdf.rect(x, y, w, h, "F")
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(x, y)
        pdf.cell(w, h, classification, align="C")

    def draw_gauge_row(y, label, value, unit, thresholds, classification):
        """Draw one complete gauge row: label | value | gauge | badge.
        Returns total height consumed including scale labels."""
        bar_h = 5
        scale_h = 5          # space for scale text below bar
        row_total = bar_h + scale_h + 2
        lbl_w = 30
        val_w = 24
        badge_w = 21
        gauge_w = content_w - lbl_w - val_w - badge_w - 8

        # Label
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(lbl_w, bar_h, label)

        # Value + unit
        pdf.set_xy(margin + lbl_w, y)
        pdf.set_font("Helvetica", "B", 8)
        colour = _CLS_RGB.get(classification, MED_GREY_RGB)
        pdf.set_text_color(*colour)
        val_txt = f"{value:.2f}" if value < 100 else f"{value:.1f}"
        pdf.cell(val_w, bar_h, f"{val_txt} {unit}", align="R")

        # Gauge bar
        gauge_x = margin + lbl_w + val_w + 4
        if thresholds:
            draw_gauge(gauge_x, y, gauge_w, bar_h, value, thresholds)

        # Badge (vertically centred on bar)
        badge_x = margin + content_w - badge_w
        if classification:
            draw_classification_badge(badge_x, y + 0.3, badge_w, bar_h - 0.6,
                                      classification)
        return row_total

    # ─── Ratio range-bar drawing ────────────────────────────────────────

    def draw_ratio_row(y, ratio_name, actual, ideal_min, ideal_max, unit, status,
                       row_total=None):
        """Draw a ratio analysis row with ideal range indicator and scale.
        Returns total height consumed."""
        import math
        if row_total is None:
            row_total = 14
        bar_h = row_total * 0.43
        scale_h = row_total * 0.43
        lbl_w = 32
        val_w = 22
        badge_w = 24
        bar_w = content_w - lbl_w - val_w - badge_w - 10

        # Scale range
        if ideal_max > 100:
            scale_max = max(actual * 1.5, ideal_min * 3) if actual > 0 else ideal_min * 3
        else:
            scale_max = max(ideal_max * 1.8, actual * 1.3) if actual > 0 else ideal_max * 2
        if scale_max <= 0:
            scale_max = 1

        bar_x = margin + lbl_w + val_w + 5
        bar_y = y
        scale_y = bar_y + bar_h + 1

        # Background track
        pdf.set_fill_color(235, 235, 235)
        pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")

        # Ideal range zone (green)
        ix0 = bar_x + (ideal_min / scale_max) * bar_w
        ix1 = bar_x + min(ideal_max / scale_max, 1.0) * bar_w
        pdf.set_fill_color(*_CLS_LIGHT["Optimal"])
        pdf.set_draw_color(*_CLS_RGB["Optimal"])
        pdf.set_line_width(0.5)
        pdf.rect(ix0, bar_y, ix1 - ix0, bar_h, "FD")

        # Scale ticks
        raw_step = scale_max / 5
        magnitude = 10 ** math.floor(math.log10(raw_step)) if raw_step > 0 else 1
        nice_steps = [1, 2, 2.5, 5, 10]
        step = magnitude * min(nice_steps,
                               key=lambda s: abs(s * magnitude - raw_step))
        pdf.set_draw_color(180, 180, 180)
        pdf.set_line_width(0.15)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(130, 130, 130)
        tick_val = 0
        while tick_val <= scale_max * 1.01:
            tx = bar_x + (tick_val / scale_max) * bar_w
            if tx <= bar_x + bar_w + 0.5:
                pdf.line(tx, bar_y + bar_h, tx, bar_y + bar_h + 1.5)
                fmt_t = ".0f" if tick_val >= 10 else (
                    ".1f" if tick_val >= 1 else ".2f")
                pdf.set_xy(tx - 6, scale_y)
                pdf.cell(12, 4, f"{tick_val:{fmt_t}}", align="C")
            tick_val += step

        # Ideal boundary labels (bold green, over the ticks)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*_CLS_RGB["Optimal"])
        fmt = ".0f" if ideal_min >= 10 else (".1f" if ideal_min >= 1 else ".2f")
        pdf.set_xy(ix0 - 6, scale_y)
        pdf.cell(12, 4, f"{ideal_min:{fmt}}", align="C")
        if ideal_max < 100:
            pdf.set_xy(ix1 - 6, scale_y)
            pdf.cell(12, 4, f"{ideal_max:{fmt}}", align="C")

        # Actual value marker
        marker_x = bar_x + min(actual / scale_max, 1.0) * bar_w
        status_colour = _STATUS_RGB.get(status, DARK_GREY_RGB)
        pdf.set_draw_color(*status_colour)
        pdf.set_line_width(0.7)
        pdf.line(marker_x, bar_y - 1, marker_x, bar_y + bar_h + 1)
        d = 1.4
        cy = bar_y + bar_h / 2
        pdf.set_fill_color(*status_colour)
        pdf.polygon([
            (marker_x, cy - d),
            (marker_x + d * 0.7, cy),
            (marker_x, cy + d),
            (marker_x - d * 0.7, cy),
        ], style="F")

        # Row label
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(lbl_w, bar_h, ratio_name)

        # Actual value text
        pdf.set_xy(margin + lbl_w, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*status_colour)
        val_txt = f"{actual:.1f}" if unit == "%" else f"{actual:.2f}"
        pdf.cell(val_w, bar_h, val_txt, align="R")

        # Status badge
        badge_x = margin + content_w - badge_w
        pdf.set_fill_color(*status_colour)
        pdf.rect(badge_x, y + 0.5, badge_w, bar_h - 1, "F")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(badge_x, y + 0.5)
        pdf.cell(badge_w, bar_h - 1, status, align="C")

        return row_total

    # ─── Target-vs-Actual horizontal bar chart ──────────────────────────

    def draw_target_vs_actual(y_start, targets_d, totals_d, nutrients_list):
        """Draw grouped horizontal bars: target (orange) vs actual (grey).
        Dynamically sizes rows to fit on a single page."""
        lbl_w = 14
        num_w = 22
        bar_area_w = content_w - lbl_w - num_w * 2 - 10

        n_items = len(nutrients_list)
        # Available height: from y_start to footer area
        avail_h = (page_h - 18) - y_start
        # Compute pair_h to fit all items (legend takes ~6mm)
        legend_h = 6
        if n_items > 0:
            pair_h = max((avail_h - legend_h) / n_items, 6)
        else:
            pair_h = 13.5
        row_h = pair_h * 0.42
        gap = pair_h * 0.08

        all_vals = list(targets_d.values()) + list(totals_d.values())
        max_val = max(all_vals) if all_vals else 1
        if max_val <= 0:
            max_val = 1

        bar_x = margin + lbl_w + num_w + 4
        y = y_start

        # Legend
        pdf.set_fill_color(*ORANGE_RGB)
        pdf.rect(bar_x, y - 5, 4, 3, "F")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.set_xy(bar_x + 5, y - 5.5)
        pdf.cell(15, 3.5, "Target")
        pdf.set_fill_color(*MED_GREY_RGB)
        pdf.rect(bar_x + 28, y - 5, 4, 3, "F")
        pdf.set_xy(bar_x + 33, y - 5.5)
        pdf.cell(15, 3.5, "Products")
        y += 1

        for nut in nutrients_list:
            target_v = targets_d.get(nut, 0)
            actual_v = totals_d.get(nut, 0)

            # Label
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(lbl_w, pair_h, nut)

            # Target bar
            t_w = (target_v / max_val) * bar_area_w if target_v > 0 else 0
            pdf.set_fill_color(*ORANGE_RGB)
            if t_w > 0.5:
                pdf.rect(bar_x, y + 0.5, t_w, row_h - 1, "F")
            pdf.set_xy(margin + lbl_w, y)
            pdf.set_font("Helvetica", "", 6.5)
            pdf.set_text_color(*ORANGE_RGB)
            pdf.cell(num_w, row_h, f"{target_v:.1f}", align="R")

            # Actual bar
            a_w = (actual_v / max_val) * bar_area_w if actual_v > 0 else 0
            pdf.set_fill_color(*MED_GREY_RGB)
            if a_w > 0.5:
                pdf.rect(bar_x, y + row_h + gap - 0.5, a_w, row_h - 1, "F")
            pdf.set_xy(margin + lbl_w, y + row_h + gap)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(num_w, row_h, f"{actual_v:.1f}", align="R")

            # Over/short label
            diff = actual_v - target_v
            if abs(diff) > 0.01:
                pdf.set_xy(bar_x + max(t_w, a_w) + 2,
                           y + (row_h + gap) / 2 - 1.5)
                pdf.set_font("Helvetica", "B", 6)
                if diff >= 0:
                    pdf.set_text_color(*_CLS_RGB["Optimal"])
                    pdf.cell(18, 3, f"+{diff:.1f}")
                else:
                    pdf.set_text_color(*_CLS_RGB["Very Low"])
                    pdf.cell(18, 3, f"{diff:.1f}")

            y += pair_h

        return y

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 1 -Fertilizer Recommendation Report
    # ═════════════════════════════════════════════════════════════════════
    pdf.add_page()
    page_header("FERTILIZER RECOMMENDATION REPORT")

    # Info boxes
    box_w = (content_w - 6) / 3
    box_y = 34

    def info_box(x, y_top, title, items):
        pdf.set_xy(x, y_top)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.set_fill_color(*ORANGE_FILL_RGB)
        pdf.cell(box_w, 6, title, fill=True, align="C",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MED_GREY_RGB)
        for label, value in items:
            pdf.set_x(x)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(25, 4.5, f"{label}:", new_x="END")
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(box_w - 25, 4.5, str(value or ""),
                     new_x="LMARGIN", new_y="NEXT")

    info_box(margin, box_y, "Customer", [
        ("Name", customer), ("Farm", farm), ("Field", field),
    ])
    field_info = [
        ("Yield Target", f"{yield_target} {yield_unit}" if yield_target else ""),
        ("Pop/Ha", f"{pop_per_ha:,}" if pop_per_ha else ""),
    ]
    if plants_per_field:
        field_info.append(("Plants/Field", f"{plants_per_field:,}"))
    if field_area_ha:
        field_info.append(("Field Size", f"{field_area_ha} ha"))
    info_box(margin + box_w + 3, box_y, "Field Info", field_info)
    info_box(margin + 2 * (box_w + 3), box_y, "Agent", [
        ("Name", agent_name), ("Cell No", agent_cell), ("E-mail", agent_email),
    ])

    box_y2 = box_y + 30
    info_box(margin, box_y2, "Soil Analysis", [
        ("Date", analysis_date), ("Lab", lab_name),
    ])
    info_box(margin + box_w + 3, box_y2, "Crop", [
        ("Crop", crop_name), ("Cultivar", cultivar or crop_name),
    ])
    # Total cost box
    pdf.set_xy(margin + 2 * (box_w + 3), box_y2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.set_fill_color(*ORANGE_FILL_RGB)
    pdf.cell(box_w, 6, "Total Cost", fill=True, align="C",
             new_x="LMARGIN", new_y="NEXT")
    x_cost = margin + 2 * (box_w + 3)
    pdf.set_x(x_cost)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(25, 4.5, "Per Ha:", new_x="END")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(box_w - 25, 4.5, f"R{total_cost_ha:,.2f}" if total_cost_ha else "",
             align="R", new_x="LMARGIN", new_y="NEXT")

    # Nutrient Totals table
    nut_y = box_y2 + 24
    pdf.set_xy(margin, nut_y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(content_w, 6, "Nutrient Totals and Targets", align="C",
             new_x="LMARGIN", new_y="NEXT")
    nut_y += 7

    nutrients_display = NUTRIENTS_SOIL
    label_w = 22
    nut_w = (content_w - label_w) / len(nutrients_display)

    # Header row
    pdf.set_xy(margin, nut_y)
    pdf.set_fill_color(*ORANGE_RGB)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(label_w, 5, "", fill=True)
    for nut in nutrients_display:
        pdf.cell(nut_w, 5, nut, fill=True, align="C")
    nut_y += 5

    targets_dict = {t["Nutrient"]: t["Target_kg_ha"] for t in nutrient_targets}
    totals_dict = {}
    for p in products:
        for nk, nv in (p.get("nutrients") or {}).items():
            totals_dict[nk] = totals_dict.get(nk, 0) + (nv or 0)

    for row_label, row_vals, bold, is_diff in [
        ("Targets", targets_dict, True, False),
        ("Totals", totals_dict, False, False),
        ("Over/Short", None, True, True),
    ]:
        pdf.set_xy(margin, nut_y)
        alt = (nut_y - box_y2) % 2 == 0
        pdf.set_fill_color(*GREY_LIGHT_RGB) if alt else pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "B" if bold else "", 8)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(label_w, 5, row_label, fill=True)
        for nut in nutrients_display:
            if is_diff:
                v = totals_dict.get(nut, 0) - targets_dict.get(nut, 0)
                if abs(v) > 0.01:
                    pdf.set_text_color(0, 130, 0) if v >= 0 else pdf.set_text_color(200, 0, 0)
                    pdf.cell(nut_w, 5, f"{v:.2f}", fill=True, align="C")
                    pdf.set_text_color(*DARK_GREY_RGB)
                else:
                    pdf.cell(nut_w, 5, "", fill=True, align="C")
            else:
                v = row_vals.get(nut, 0)
                pdf.cell(nut_w, 5, f"{v:.2f}" if v != 0 else "",
                         fill=True, align="C")
        nut_y += 5

    # Accent line
    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(0.4)
    pdf.line(margin, nut_y, page_w - margin, nut_y)

    # Products table
    prod_y = nut_y + 5
    pdf.set_xy(margin, prod_y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(content_w, 6, "Products", align="C")
    prod_y += 7

    if role == "admin":
        prod_cols = ["Product", "Application Method", "Application Time",
                     "Kg Per Ha", "Price Per Ton", "Price Per Ha"]
        prod_widths = [60, 45, 40, 35, 40, 40]
    else:
        prod_cols = ["Product", "Application Method", "Application Time",
                     "Kg Per Ha", "Price Per Ha"]
        prod_widths = [100, 45, 40, 35, 40]

    pdf.set_xy(margin, prod_y)
    pdf.set_fill_color(*ORANGE_RGB)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(255, 255, 255)
    for lbl, w in zip(prod_cols, prod_widths):
        pdf.cell(w, 5, lbl, fill=True, align="C")
    prod_y += 5

    pdf.set_font("Helvetica", "", 8)
    for i, p in enumerate(products):
        pdf.set_xy(margin, prod_y)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.set_fill_color(*GREY_LIGHT_RGB) if i % 2 == 1 else pdf.set_fill_color(255, 255, 255)
        if role == "admin":
            vals = [
                str(p.get("product", "")), str(p.get("method", "")),
                str(p.get("timing", "")), f"{p.get('kg_ha', 0):.2f}",
                f"R{p.get('price_per_ton', 0):,.2f}",
                f"R{p.get('price_ha', 0):,.2f}",
            ]
        else:
            vals = [
                str(p.get("product", "")), str(p.get("method", "")),
                str(p.get("timing", "")), f"{p.get('kg_ha', 0):.2f}",
                f"R{p.get('price_ha', 0):,.2f}",
            ]
        for val, w in zip(vals, prod_widths):
            pdf.cell(w, 5, val, fill=True, align="C")
        prod_y += 5

    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(0.4)
    pdf.line(margin, prod_y, margin + sum(prod_widths), prod_y)

    page_footer()

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 2 -Soil Health Analysis (gauge charts)
    # ═════════════════════════════════════════════════════════════════════
    if soil_values and norms:
        suf_df = norms.get("Soil_Sufficiency")
        if suf_df is not None:
            pdf.add_page()
            page_header("SOIL HEALTH ANALYSIS")

            # Subtitle
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.set_xy(margin, 32)
            parts = [customer, farm, f"Lab: {lab_name}", str(analysis_date)]
            pdf.cell(content_w, 4, "  |  ".join(p for p in parts if p),
                     align="C")

            # Summary strip -count classifications
            class_counts = {}
            classifications_list = []
            for _, row in suf_df.iterrows():
                param = row["Parameter"]
                val = soil_values.get(param)
                if val is not None:
                    cls = classify_soil_value(val, param, suf_df)
                    if cls:
                        class_counts[cls] = class_counts.get(cls, 0) + 1
                        classifications_list.append(
                            (param, val, str(row["Unit"]),
                             [row["Very_Low_Max"], row["Low_Max"],
                              row["Optimal_Max"], row["High_Max"]],
                             cls))

            # Draw summary pills
            pill_y = 37
            pill_x = margin
            total_params = sum(class_counts.values())
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.set_xy(pill_x, pill_y)
            pdf.cell(30, 6, f"{total_params} parameters:")
            pill_x += 31

            for cls_name in ["Very Low", "Low", "Optimal", "High", "Very High"]:
                count = class_counts.get(cls_name, 0)
                if count == 0:
                    continue
                colour = _CLS_RGB[cls_name]
                pw = 32
                pdf.set_fill_color(*colour)
                pdf.rect(pill_x, pill_y, pw, 6, "F")
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(255, 255, 255)
                pdf.set_xy(pill_x, pill_y)
                pdf.cell(pw, 6, f"{count} {cls_name}", align="C")
                pill_x += pw + 2

            # Group parameters
            macro_params = ["N (total)", "P (Bray-1)", "K", "Ca", "Mg", "S"]
            general_params = ["pH (H2O)", "pH (KCl)", "Org C", "CEC", "Clay"]
            micro_params = ["Fe", "Mn", "Zn", "Cu", "B", "Mo"]

            cls_lookup = {c[0]: c for c in classifications_list}

            y_cursor = 46

            for group_label, params in [
                ("Macronutrients", macro_params),
                ("General Soil Properties", general_params),
                ("Micronutrients", micro_params),
            ]:
                group_items = [cls_lookup[p] for p in params if p in cls_lookup]
                if not group_items:
                    continue

                # If we'd overflow, start a new page
                row_step = 10  # row_h(7) + scale(3)
                needed = 7 + len(group_items) * row_step
                if y_cursor + needed > page_h - 25:
                    page_footer()
                    pdf.add_page()
                    page_header("SOIL HEALTH ANALYSIS (cont.)")
                    y_cursor = 34

                section_label(y_cursor, group_label)
                y_cursor += 7

                for param, val, unit, thresholds, cls in group_items:
                    rh = draw_gauge_row(y_cursor, param, val, unit,
                                        thresholds, cls)
                    y_cursor += rh

                y_cursor += 1.5  # gap between groups

            # ── Key Findings box ────────────────────────────────────────
            findings = []
            vl_count = class_counts.get("Very Low", 0)
            lo_count = class_counts.get("Low", 0)
            hi_count = class_counts.get("High", 0)
            vh_count = class_counts.get("Very High", 0)

            if vl_count + lo_count > 0:
                deficient = [c[0] for c in classifications_list
                             if c[4] in ("Very Low", "Low")]
                findings.append(
                    f"Deficient ({vl_count + lo_count}): "
                    + ", ".join(deficient)
                    + " -adjustment factors applied to increase targets."
                )
            if hi_count + vh_count > 0:
                excess = [c[0] for c in classifications_list
                          if c[4] in ("High", "Very High")]
                findings.append(
                    f"Elevated ({hi_count + vh_count}): "
                    + ", ".join(excess)
                    + " -targets reduced or zeroed."
                )

            opt_count = class_counts.get("Optimal", 0)
            if opt_count > 0:
                optimal = [c[0] for c in classifications_list if c[4] == "Optimal"]
                findings.append(
                    f"Optimal ({opt_count}): "
                    + ", ".join(optimal)
                    + " -maintenance rates applied."
                )

            if findings:
                # If not enough room, start new page
                needed = 10 + len(findings) * 7
                if y_cursor + needed > page_h - 18:
                    page_footer()
                    pdf.add_page()
                    page_header("SOIL HEALTH ANALYSIS (cont.)")
                    y_cursor = 36

                y_cursor += 4
                section_label(y_cursor, "Key Findings")
                y_cursor += 9

                # Boxed summary area
                box_h = len(findings) * 7 + 4
                pdf.set_fill_color(250, 250, 250)
                pdf.set_draw_color(*ORANGE_RGB)
                pdf.set_line_width(0.4)
                pdf.rect(margin, y_cursor, content_w, box_h, "FD")

                y_cursor += 2
                for finding in findings:
                    pdf.set_xy(margin + 4, y_cursor)
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_text_color(*ORANGE_RGB)
                    pdf.cell(4, 5, ">")
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(*DARK_GREY_RGB)
                    pdf.cell(content_w - 10, 5, finding)
                    y_cursor += 7
                y_cursor += 4

            page_footer()

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 3 -Nutrient Ratios & Target vs Actual
    # ═════════════════════════════════════════════════════════════════════
    has_ratios = bool(ratio_results)
    has_products = bool(products)

    if has_ratios or has_products:
        pdf.add_page()
        page_header("NUTRIENT BALANCE & RATIOS")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.set_xy(margin, 32)
        pdf.cell(content_w, 4,
                 f"{crop_name}  |  Yield target: {yield_target} {yield_unit}"
                 f"  |  {customer}",
                 align="C")

        y_cursor = 39

        # ── Ratio analysis (left/top) ───────────────────────────────────
        if has_ratios:
            section_label(y_cursor, "Nutrient Ratios")
            y_cursor += 8

            # Ratio summary pills
            r_counts = {}
            for r in ratio_results:
                s = r["Status"]
                r_counts[s] = r_counts.get(s, 0) + 1

            pill_x = margin
            for status_name in ["Below ideal", "Ideal", "Above ideal"]:
                count = r_counts.get(status_name, 0)
                if count == 0:
                    continue
                colour = _STATUS_RGB[status_name]
                pw = 30
                pdf.set_fill_color(*colour)
                pdf.rect(pill_x, y_cursor, pw, 5, "F")
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(255, 255, 255)
                pdf.set_xy(pill_x, y_cursor)
                pdf.cell(pw, 5, f"{count} {status_name}", align="C")
                pill_x += pw + 3
            y_cursor += 8

            # Compute interpretation box height in advance
            below = [r for r in ratio_results if r["Status"] == "Below ideal"]
            above = [r for r in ratio_results if r["Status"] == "Above ideal"]
            interp_lines = []
            if below:
                names = ", ".join(r["Ratio"] for r in below)
                interp_lines.append(
                    ("Below ideal:", names,
                     "Consider corrective amendments.",
                     _STATUS_RGB["Below ideal"]))
            if above:
                names = ", ".join(r["Ratio"] for r in above)
                interp_lines.append(
                    ("Above ideal:", names,
                     "Monitor and reduce contributing inputs.",
                     _STATUS_RGB["Above ideal"]))
            interp_h = (len(interp_lines) * 8 + 10) if interp_lines else 0

            # Dynamically size ratio rows to fit page
            n_ratios = len(ratio_results)
            avail_for_ratios = (page_h - 18) - y_cursor - interp_h
            ratio_row_h = max(avail_for_ratios / n_ratios, 8) if n_ratios > 0 else 14

            for r in ratio_results:
                rh = draw_ratio_row(
                    y_cursor, r["Ratio"], r["Actual"],
                    r["Ideal_Min"], r["Ideal_Max"],
                    r["Unit"], r["Status"],
                    row_total=ratio_row_h,
                )
                y_cursor += rh

            # Ratio interpretation box
            y_cursor += 4
            if interp_lines:
                box_h = len(interp_lines) * 8 + 4
                pdf.set_fill_color(250, 250, 250)
                pdf.set_draw_color(*ORANGE_RGB)
                pdf.set_line_width(0.4)
                pdf.rect(margin, y_cursor, content_w, box_h, "FD")
                y_cursor += 2
                for label, names, action, colour in interp_lines:
                    pdf.set_xy(margin + 4, y_cursor)
                    pdf.set_font("Helvetica", "B", 8.5)
                    pdf.set_text_color(*colour)
                    pdf.cell(28, 6, label)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(*DARK_GREY_RGB)
                    pdf.cell(content_w - 36, 6, f"{names}  -  {action}")
                    y_cursor += 8
                y_cursor += 4

            y_cursor += 2

        # ── Target vs Actual bar chart (own page, fitted) ─────────────
        if has_products:
            page_footer()
            pdf.add_page()
            page_header("TARGET vs PRODUCT SUPPLY")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.set_xy(margin, 33)
            pdf.cell(content_w, 4,
                     f"{crop_name}  |  Yield target: {yield_target} {yield_unit}"
                     f"  |  {customer}", align="C")
            y_cursor = 40
            section_label(y_cursor, "Target vs Product Supply (kg/ha)")
            y_cursor += 12
            draw_target_vs_actual(y_cursor, targets_dict, totals_dict,
                                  NUTRIENTS_SOIL)

        page_footer()

    # ═════════════════════════════════════════════════════════════════════
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
