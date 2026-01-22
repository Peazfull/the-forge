"""
===========================================
🍺 MARKET BREWERY — MARKET SCREENER
===========================================
Daily & Weekly market movements (close-based)
"""

import streamlit as st
import pandas as pd
from services.marketbrewery.market_brewery_service import (
    refresh_data,
    get_top_flop_daily,
    get_top_flop_weekly
)


# ======================================================
# HELPER FUNCTIONS
# ======================================================

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
    
    # Renommer les colonnes
    df = df.rename(columns={
        "symbol": "Symbol",
        "close": "Close",
        "pct_change": "% Change",
        "date": "Date"
    })
    
    # Sélectionner uniquement les colonnes nécessaires
    df = df[["Symbol", "% Change", "Close", "Date"]]
    
    # Formater
    df["Close"] = df["Close"].apply(lambda x: f"${x:,.2f}")
    df["% Change"] = df["% Change"].apply(lambda x: f"{x:+.2f}%")
    
    return df


def render_zone_section(zone_code, zone_name, zone_flag):
    """
    Affiche une section complète pour une zone
    (Top/Flop Daily + Top/Flop Weekly)
    """
    st.markdown(f"## {zone_flag} {zone_name}")
    
    # ========== DAILY ==========
    st.markdown("### 📅 Daily Performance")
    
    daily_data = get_top_flop_daily(zone_code, limit=10)
    
    col_top_daily, col_flop_daily = st.columns(2)
    
    with col_top_daily:
        st.markdown("#### 🟢 Top 10 Daily")
        if daily_data["status"] == "success" and daily_data["top"]:
            df_top = create_performance_table(daily_data["top"], "Top Daily")
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée disponible")
    
    with col_flop_daily:
        st.markdown("#### 🔴 Flop 10 Daily")
        if daily_data["status"] == "success" and daily_data["flop"]:
            df_flop = create_performance_table(daily_data["flop"], "Flop Daily")
            st.dataframe(df_flop, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune donnée disponible")
    
    # ========== WEEKLY ==========
    st.markdown("### 📊 Weekly Performance")
    
    weekly_data = get_top_flop_weekly(zone_code, limit=10)
    
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

st.title("🍺 Market Brewery — Market Screener")
st.markdown("*Daily & Weekly market movements (close-based)*")

st.divider()

# ========== REFRESH BUTTON ==========

col_refresh, col_spacer = st.columns([1, 3])

with col_refresh:
    if st.button("🔄 Refresh Market Data", use_container_width=True, type="primary"):
        with st.spinner("Rafraîchissement des données en cours..."):
            result = refresh_data()
            
            if result["status"] == "success":
                st.success("✅ " + result["message"])
                st.rerun()
            else:
                st.error(f"❌ Erreur : {result['message']}")

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
st.markdown("*Source : Yahoo Finance · Data refreshed daily*")