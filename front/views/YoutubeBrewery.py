import streamlit as st

# =========================
# INIT SESSION STATE
# =========================
if "yt_channels" not in st.session_state:
    # Chaque item: {"url": "", "name": "", "enabled": True}
    st.session_state.yt_channels = [
        {"url": "", "name": "", "enabled": True}
    ]

st.title("🔺 Youtube brewery")
st.divider()

# =========================
# CHAÎNES YOUTUBE
# =========================
with st.expander("📺 Chaînes YouTube", expanded=True):

    for idx, channel in enumerate(st.session_state.yt_channels):

        col_url, col_name, col_enabled, col_delete = st.columns([4, 3, 1, 0.6])


        with col_url:
            channel["url"] = st.text_input(
                "URL de la chaîne YouTube",
                value=channel["url"],
                key=f"yt_url_{idx}"
)


        with col_name:
            channel["name"] = st.text_input(
                "Chaîne YouTube",
                value=channel["name"],
                key=f"yt_name_{idx}"
)


        with col_enabled:
            channel["enabled"] = st.checkbox(
                "Active",
                value=channel["enabled"],
                key=f"yt_enabled_{idx}"
            )


        with col_delete:
            if st.button("❌", key=f"yt_delete_{idx}"):
                st.session_state.yt_channels.pop(idx)
                st.rerun()

        st.divider()

    if st.button("➕ Ajouter une chaîne"):
        st.session_state.yt_channels.append(
            {"url": "", "name": "", "enabled": True}
        )
        st.rerun()

st.divider()

