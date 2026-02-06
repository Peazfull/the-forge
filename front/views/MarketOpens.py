"""
===========================================
📈 MARKET OPENS — EUROPE
===========================================
Open du jour (open vs close précédent)
"""

import streamlit as st
import pandas as pd

from services.marketbrewery.market_opens_service import (
    refresh_data,
    get_open_top_flop,
    get_open_performances,
    get_last_open_date,
    get_today_open_date,
)
from services.marketbrewery.listes_market import (
    EU_TOP_200,
    EU_INDICES,
    EU_FX_PAIRS,
    FR_SBF_120,
    COMMODITIES_MAJOR,
    CRYPTO_MAJOR,
    EU_BONDS_10Y,
)


# ======================================================
# CUSTOM CSS
# ======================================================

def inject_custom_css():
    """Injecte le CSS custom pour un look moderne"""
    st.markdown("""
    <style>
    /* Variables de couleurs */
    :root {
        --green: #10b981;
        --red: #ef4444;
        --blue: #3b82f6;
        --gray-50: #f9fafb;
        --gray-100: #f3f4f6;
        --gray-200: #e5e7eb;
        --gray-600: #4b5563;
        --gray-900: #111827;
    }
    
    /* Réduire l'espace en haut */
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* Zone headers - sans card, juste texte */
    .zone-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 0 12px 0;
        border-bottom: 1px solid var(--gray-200);
        margin: 32px 0 20px 0;
    }
    
    .zone-header h2 {
        margin: 0 !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        color: var(--gray-900);
    }
    
    /* Header section - version épurée */
    .market-header {
        background: transparent;
        color: var(--gray-900);
        padding: 24px 0;
        margin-bottom: 24px;
        border-bottom: 2px solid var(--gray-200);
    }
    
    .market-header h1 {
        margin: 0 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    .market-header p {
        margin: 4px 0 0 0 !important;
        color: var(--gray-600);
        font-size: 14px !important;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 500;
        margin-right: 8px;
    }
    
    .badge-info {
        background: rgba(59, 130, 246, 0.1);
        color: var(--blue);
    }
    
    /* Tableaux Streamlit - override */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Bouton refresh custom */
    .stButton button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    
    /* Date badge */
    .date-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: white;
        border: 1px solid var(--gray-200);
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        color: var(--gray-900);
    }
    
    /* Section headers - version compacte */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
    }
    
    .section-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--gray-900);
        margin: 0 0 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)


# ======================================================
# HELPER FUNCTIONS
# ======================================================

@st.cache_data
def get_open_top_flop_cached(symbols, limit=10):
    """
    Version cachée de get_open_top_flop
    """
    return get_open_top_flop(symbols, limit)


def format_pct(value):
    """Formate un pourcentage avec couleur"""
    color = "green" if value >= 0 else "red"
    sign = "+" if value >= 0 else ""
    return f":{color}[{sign}{value:.2f}%]"


def create_performance_table(data):
    """
    Crée un DataFrame stylisé pour l'affichage avec couleurs conditionnelles
    """
    if not data:
        return pd.DataFrame({"Message": ["Aucune donnée disponible"]})
    
    df = pd.DataFrame(data)
    has_name = "name" in df.columns

    rename_dict = {
        "symbol": "Symbol",
        "open": "Open",
        "pct_change": "% Change",
        "date": "Date",
    }
    if has_name:
        rename_dict["name"] = "Name"

    df = df.rename(columns=rename_dict)

    if has_name:
        df = df[["Name", "Symbol", "% Change", "Open"]]
    else:
        df = df[["Symbol", "% Change", "Open"]]

    df["Open"] = df["Open"].apply(lambda x: f"${x:,.2f}")
    df["% Change"] = df["% Change"].apply(lambda x: f"{x:+.2f}%")

    return df


def style_dataframe(df):
    """Applique un style moderne au dataframe"""

    def highlight_pct(val):
        """Style pour la colonne % Change"""
        try:
            if isinstance(val, str) and "%" in val:
                num_val = float(val.replace("%", "").replace("+", ""))
                if num_val >= 0:
                    return "color: #10b981; background-color: rgba(16, 185, 129, 0.1); font-weight: 600;"
                return "color: #ef4444; background-color: rgba(239, 68, 68, 0.1); font-weight: 600;"
        except Exception:
            pass
        return ""

    styled = df.style.applymap(highlight_pct, subset=["% Change"])
    return styled


def render_zone_section(symbols, zone_name, zone_flag):
    """
    Affiche une section complète pour une zone (version minimaliste)
    """
    open_data = get_open_top_flop(symbols, limit=10)
    num_assets = len(open_data.get("top", [])) if open_data.get("status") == "success" else 0

    st.markdown(f"""
    <div class="zone-header">
        <h2>{zone_flag} {zone_name}</h2>
        <span class="badge badge-info">{num_assets} actifs</span>
    </div>
    """, unsafe_allow_html=True)

    col_top, col_flop = st.columns(2, gap="large")

    with col_top:
        st.markdown('<p class="section-title">🟢 Top 10 Open</p>', unsafe_allow_html=True)
        if open_data["status"] == "success" and open_data["top"]:
            df_top = create_performance_table(open_data["top"])
            styled_df = style_dataframe(df_top)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée disponible")

    with col_flop:
        st.markdown('<p class="section-title">🔴 Flop 10 Open</p>', unsafe_allow_html=True)
        if open_data["status"] == "success" and open_data["flop"]:
            df_flop = create_performance_table(open_data["flop"])
            styled_df = style_dataframe(df_flop)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée disponible")

def render_simple_section(symbols, zone_name, zone_flag):
    """
    Affiche une section simple (liste complète, sans top/flop)
    """
    data = get_open_performances(symbols)
    items = data.get("items", []) if data.get("status") == "success" else []
    num_assets = len(items)

    st.markdown(f"""
    <div class="zone-header">
        <h2>{zone_flag} {zone_name}</h2>
        <span class="badge badge-info">{num_assets} actifs</span>
    </div>
    """, unsafe_allow_html=True)

    if items:
        df = create_performance_table(items)
        styled_df = style_dataframe(df)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée disponible")


# ======================================================
# MAIN PAGE
# ======================================================

inject_custom_css()

st.markdown("""
<div class="market-header">
    <h1>📈 Market Opens</h1>
    <p>Europe Open Tracker · Open vs Close précédent</p>
</div>
""", unsafe_allow_html=True)

col_refresh, col_spacer, col_date = st.columns([1, 0.5, 1.5])

with col_refresh:
    if st.button("🔄 Refresh Market Data", use_container_width=True, type="primary"):
        with st.spinner("Rafraîchissement des données en cours..."):
            result = refresh_data()
            if result["status"] == "success":
                st.cache_data.clear()
                st.success("✅ " + result["message"])
                st.rerun()
            else:
                st.error(f"❌ Erreur : {result['message']}")

with col_date:
    today_date = get_today_open_date()
    last_date = get_last_open_date()
    if today_date:
        label = f"📅 Date du jour : {today_date}"
        if last_date and last_date != today_date:
            label += f" · Dernière en base : {last_date}"
        st.markdown(f'<div class="date-badge">{label}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="date-badge">📅 Aucune date disponible</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========== SECTIONS ==========

render_zone_section(EU_TOP_200, "Actions européennes — Top 200", "🇪🇺")
render_zone_section(FR_SBF_120, "Actions françaises — SBF 120", "🇫🇷")
render_simple_section(EU_INDICES, "Indices européens", "📊")
render_simple_section(EU_BONDS_10Y, "Obligations 10Y — Europe", "📈")
render_simple_section(EU_FX_PAIRS, "Devises EUR — Paires majeures", "💱")
render_simple_section(COMMODITIES_MAJOR, "Commodities — majeures", "🛢️")
render_simple_section(CRYPTO_MAJOR, "Crypto — majeures", "🪙")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 14px; padding: 24px 0;">
    <p style="margin: 0;">Source: Yahoo Finance · Données rafraîchies via pipeline Market</p>
    <p style="margin: 8px 0 0 0; font-size: 12px;">Market Opens v1.0</p>
</div>
""", unsafe_allow_html=True)
