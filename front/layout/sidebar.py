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
        with st.expander("🍺 The brewery", expanded=True):
            if st.button("🗞️ News brewery", key="news_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/NewsBrewery"
            if st.button("📨 NL brewery", key="nl_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/NlBrewery"
            if st.button("🔺 Youtube brewery", key="youtube_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/YoutubeBrewery"
            if st.button("👨🏻‍💻 Hand brewery", key="hand_brewery", use_container_width=True):
                st.session_state.current_page = "front/views/HandBrewery"
            if st.button("📈 Market Brewery", key="vue5", use_container_width=True):
                st.session_state.current_page = "front/views/vue5"
            if st.button("🚀 Vue 6", key="vue6", use_container_width=True):
                st.session_state.current_page = "front/views/vue6"
