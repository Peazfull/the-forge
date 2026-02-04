import streamlit as st

def render_sidebar():

    with st.sidebar:

        # LOGO
        st.image("front/layout/assets/Theforge_logo.png", width=200)


        # HOME
        if st.button("🏠 Home", key="home", use_container_width=True):
            st.session_state.current_page = None

        st.divider()

        # ===== MENU 1 =====
        with st.expander("🍺 The brewery", expanded=False):
            if st.button("🗞️ News brewery", key="news_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/NewsBrewery"
            if st.button("📨 NL brewery", key="nl_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/NlBrewery"
            if st.button("🔺 Youtube brewery", key="youtube_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/YoutubeBrewery"
            if st.button("👨🏻‍💻 Hand brewery", key="hand_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/HandBrewery"
            if st.button("📈 Market Brewery", key="market_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/MarketBrewery"
            if st.button("📍 Market Opens", key="market_opens", use_container_width=True):
                st.session_state.current_page = "front/views/MarketOpens"
            if st.button("🚀 Vue 6", key="vue6", use_container_width=True):
                st.session_state.current_page = "front/views/vue6"

        # ===== MENU 2 =====
        with st.expander("🏛️ The Ministry", expanded=False):
            if st.button("🏷️ Enrich", key="enrich_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/EnrichBrewery"
            if st.button("⭐ Score", key="score_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/ScoreBrewery"
            if st.button("👁️ Preview finale", key="preview_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/PreviewBrewery"

        # ===== MENU 3 =====
        with st.expander("🎨 The Artist", expanded=False):
            if st.button("🌍 Carrousel Eco", key="carrousel_eco", use_container_width=True):
                st.session_state.current_page = "front/views/CarrouselEco"
            if st.button("📊 Carrousel Bourse", key="carrousel_bourse", use_container_width=True):
                st.session_state.current_page = "front/views/CarrouselBourse"
            if st.button("🇫🇷 Carrousel PEA", key="carrousel_pea", use_container_width=True):
                st.session_state.current_page = "front/views/CarrouselPEA"
            if st.button("₿ Carrousel Crypto", key="carrousel_crypto", use_container_width=True):
                st.session_state.current_page = "front/views/CarrouselCrypto"
            if st.button("⚡ Breaking", key="breaking", use_container_width=True):
                st.session_state.current_page = "front/views/Breaking"
            if st.button("📖 Story", key="story", use_container_width=True):
                st.session_state.current_page = "front/views/Story"
            if st.button("📁 Carrousel Doss'", key="carrousel_doss", use_container_width=True):
                st.session_state.current_page = "front/views/CarrouselDoss"
