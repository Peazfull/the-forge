"""
===========================================
📈 MARKET BREWERY — MARKET SCREENER
===========================================
Weekly market movements (close-based)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from db.supabase_client import get_supabase
from services.marketbrewery.market_brewery_service import (
    refresh_data,
    get_top_flop_weekly
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
def get_last_refresh_date():
    """
    Récupère la date et l'heure du dernier refresh depuis la DB
    """
    try:
        supabase = get_supabase()
        response = supabase.table("market_daily_close")\
            .select("date, created_at")\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            # Utiliser created_at pour avoir l'heure exacte
            created_at_str = response.data[0].get("created_at")
            if created_at_str:
                # Format ISO : 2026-01-22T14:30:00+00:00
                dt_obj = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                return dt_obj.strftime("%d/%m/%Y à %Hh%M")
            else:
                # Fallback sur date seule
                date_str = response.data[0]["date"]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return date_obj.strftime("%d/%m/%Y")
        else:
            return None
    except Exception as e:
        return None


@st.cache_data
def get_top_flop_weekly_cached(zone, limit=10):
    """
    Version cachée de get_top_flop_weekly
    """
    return get_top_flop_weekly(zone, limit)


def format_pct(value):
    """Formate un pourcentage avec couleur"""
    color = "green" if value >= 0 else "red"
    sign = "+" if value >= 0 else ""
    return f":{color}[{sign}{value:.2f}%]"


def create_performance_table(data, title):
    """
    Crée un DataFrame stylisé pour l'affichage avec couleurs conditionnelles
    """
    if not data:
        return pd.DataFrame({"Message": ["Aucune donnée disponible"]})
    
    df = pd.DataFrame(data)
    
    # Vérifier si la colonne 'name' existe (pour compatibilité avec cache)
    has_name = 'name' in df.columns
    
    # Renommer les colonnes
    rename_dict = {
        "symbol": "Symbol",
        "close": "Close",
        "pct_change": "% Change",
        "date": "Date"
    }
    
    if has_name:
        rename_dict["name"] = "Name"
    
    df = df.rename(columns=rename_dict)
    
    # Sélectionner uniquement les colonnes nécessaires
    if has_name:
        df = df[["Name", "Symbol", "% Change", "Close"]]
    else:
        df = df[["Symbol", "% Change", "Close"]]
    
    # Formater
    df["Close"] = df["Close"].apply(lambda x: f"${x:,.2f}")
    
    # Fonction de style pour % Change avec couleurs
    def color_pct_change(val):
        """Applique des couleurs selon le signe"""
        try:
            num_val = float(val.replace('%', '').replace('+', ''))
            color = '#10b981' if num_val >= 0 else '#ef4444'  # vert ou rouge
            bg_color = 'rgba(16, 185, 129, 0.1)' if num_val >= 0 else 'rgba(239, 68, 68, 0.1)'
            return f'color: {color}; background-color: {bg_color}; font-weight: 600; padding: 4px 8px; border-radius: 4px;'
        except:
            return ''
    
    # Appliquer le formatage
    df["% Change"] = df["% Change"].apply(lambda x: f"{x:+.2f}%")
    
    return df


def style_dataframe(df):
    """Applique un style moderne au dataframe"""
    
    def highlight_pct(val):
        """Style pour la colonne % Change"""
        try:
            if isinstance(val, str) and '%' in val:
                num_val = float(val.replace('%', '').replace('+', ''))
                if num_val >= 0:
                    return 'color: #10b981; background-color: rgba(16, 185, 129, 0.1); font-weight: 600;'
                else:
                    return 'color: #ef4444; background-color: rgba(239, 68, 68, 0.1); font-weight: 600;'
        except:
            pass
        return ''
    
    # Appliquer les styles
    styled = df.style.applymap(highlight_pct, subset=['% Change'])
    
    return styled


def render_zone_section(zone_code, zone_name, zone_flag):
    """
    Affiche une section complète pour une zone (version minimaliste)
    """
    weekly_data = get_top_flop_weekly_cached(zone_code, limit=10)
    
    # Calculer le nombre d'actifs
    num_assets = len(weekly_data.get("top", [])) if weekly_data.get("status") == "success" else 0
    
    # Header simple avec séparateur
    st.markdown(f"""
    <div class="zone-header">
        <h2>{zone_flag} {zone_name}</h2>
        <span class="badge badge-info">{num_assets} actifs</span>
    </div>
    """, unsafe_allow_html=True)
    
    col_top_weekly, col_flop_weekly = st.columns(2, gap="large")
    
    with col_top_weekly:
        st.markdown('<p class="section-title">🟢 Top 10 Weekly</p>', unsafe_allow_html=True)
        if weekly_data["status"] == "success" and weekly_data["top"]:
            df_top_w = create_performance_table(weekly_data["top"], "Top Weekly")
            styled_df = style_dataframe(df_top_w)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée disponible")
    
    with col_flop_weekly:
        st.markdown('<p class="section-title">🔴 Flop 10 Weekly</p>', unsafe_allow_html=True)
        if weekly_data["status"] == "success" and weekly_data["flop"]:
            df_flop_w = create_performance_table(weekly_data["flop"], "Flop Weekly")
            styled_df = style_dataframe(df_flop_w)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée disponible")


# ======================================================
# MAIN PAGE
# ======================================================

# Injecter le CSS custom
inject_custom_css()

# Header stylé
st.markdown("""
<div class="market-header">
    <h1>📈 Market Brewery</h1>
    <p>Weekly Performance Tracker · Close-Based Analysis</p>
</div>
""", unsafe_allow_html=True)

# ========== REFRESH BUTTON & DATE ==========

col_refresh, col_spacer, col_date = st.columns([1, 0.5, 1.5])

with col_refresh:
    if st.button("🔄 Refresh Market Data", use_container_width=True, type="primary"):
        with st.spinner("Rafraîchissement des données en cours..."):
            result = refresh_data()
            
            if result["status"] == "success":
                # Vider le cache pour forcer le rechargement
                st.cache_data.clear()
                st.success("✅ " + result["message"])
                st.rerun()
            else:
                st.error(f"❌ Erreur : {result['message']}")

with col_date:
    last_refresh = get_last_refresh_date()
    if last_refresh:
        st.markdown(f'<div class="date-badge">📅 Dernières données : {last_refresh}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="date-badge">📅 Aucune donnée — Lancer un refresh</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========== ZONES ==========

# 🇺🇸 US
render_zone_section("US", "United States — Top 200", "🇺🇸")

# 🇫🇷 France
render_zone_section("FR", "France — SBF 120", "🇫🇷")

# 🇪🇺 Europe
render_zone_section("EU", "Europe — Top 200", "🇪🇺")

# 🪙 Crypto
render_zone_section("CRYPTO", "Crypto — Top 30", "🪙")

# ========== FOOTER ==========

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 14px; padding: 24px 0;">
    <p style="margin: 0;">Source: Yahoo Finance · Data refreshed weekly</p>
    <p style="margin: 8px 0 0 0; font-size: 12px;">Market Brewery v1.0</p>
</div>
""", unsafe_allow_html=True)
