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
    Crée un DataFrame stylisé pour l'affichage
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
    df["% Change"] = df["% Change"].apply(lambda x: f"{x:+.2f}%")
    
    return df


def render_zone_section(zone_code, zone_name, zone_flag):
    """
    Affiche une section complète pour une zone
    (Top/Flop Weekly uniquement)
    """
    st.markdown(f"## {zone_flag} {zone_name}")
    
    weekly_data = get_top_flop_weekly_cached(zone_code, limit=10)
    
    col_top_weekly, col_flop_weekly = st.columns(2)
    
    with col_top_weekly:
        st.markdown("#### 🟢 Top 10 Weekly")
        if weekly_data["status"] == "success" and weekly_data["top"]:
            df_top_w = create_performance_table(weekly_data["top"], "Top Weekly")
            st.dataframe(df_top_w, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée disponible")
    
    with col_flop_weekly:
        st.markdown("#### 🔴 Flop 10 Weekly")
        if weekly_data["status"] == "success" and weekly_data["flop"]:
            df_flop_w = create_performance_table(weekly_data["flop"], "Flop Weekly")
            st.dataframe(df_flop_w, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée disponible")
    
    st.divider()


# ======================================================
# MAIN PAGE
# ======================================================

st.title("📈 Market Brewery — Market Screener")
st.markdown("*Weekly market movements (close-based)*")

st.divider()

# ========== REFRESH BUTTON ==========

col_refresh, col_date = st.columns([1, 3])

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
        st.markdown(f"📅 **Dernières données :** {last_refresh}")
    else:
        st.markdown("📅 **Aucune donnée** — Lancer un refresh")

st.divider()

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

st.divider()
st.markdown("*Source : Yahoo Finance · Data refreshed weekly*")
