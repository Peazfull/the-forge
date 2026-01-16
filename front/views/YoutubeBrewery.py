import streamlit as st
import json
from services.youtube_brewery.youtube_utils import get_channel_name_from_url, get_latest_video_from_channel
from services.youtube_brewery.storage_utils import load_channels, save_channels



# =========================
# INIT SESSION STATE
# =========================
if "yt_channels" not in st.session_state:
    # Chaque item: {"url": "", "name": "", "enabled": True}
    loaded_channels = load_channels()
    st.session_state.yt_channels = loaded_channels or [{"url": "", "name": "", "enabled": True}]
    st.session_state.yt_channels_snapshot = json.dumps(st.session_state.yt_channels, sort_keys=True)

if "yt_previews" not in st.session_state:
    st.session_state.yt_previews = []

if "yt_selected" not in st.session_state:
    # video_id -> video dict
    st.session_state.yt_selected = {}

st.title("🔺 Youtube brewery")
st.divider()

# =========================
# CHAÎNES YOUTUBE
# =========================
with st.expander("📺 Chaînes YouTube", expanded=True):

    for idx, channel in enumerate(st.session_state.yt_channels):

        col_url, col_name, col_enabled, col_delete = st.columns([4, 3, 1, 0.6])

        # ---- URL DE LA CHAÎNE ----
        with col_url:
            channel["url"] = st.text_input(
                "URL de la chaîne YouTube",
                value=channel["url"],
                key=f"yt_url_{idx}"
            )

        # ---- AUTO-DETECTION DU NOM ----
        if channel["url"] and not channel["name"]:
            detected_name = get_channel_name_from_url(channel["url"])
            if detected_name:
                channel["name"] = detected_name
                save_channels(st.session_state.yt_channels)
                st.rerun()

        # ---- NOM DE LA CHAÎNE ----
        with col_name:
            channel["name"] = st.text_input(
                "Chaîne YouTube",
                value=channel["name"],
                key=f"yt_name_{idx}"
            )

        # ---- CHAÎNE ACTIVE / INACTIVE ----
        with col_enabled:
            channel["enabled"] = st.checkbox(
                "Active",
                value=channel["enabled"],
                key=f"yt_enabled_{idx}"
            )

        # ---- SUPPRESSION DE LA CHAÎNE ----
        with col_delete:
            if st.button("❌", key=f"yt_delete_{idx}"):
                st.session_state.yt_channels.pop(idx)
                save_channels(st.session_state.yt_channels)
                st.rerun()

        st.divider()

    # ---- AJOUT D'UNE CHAÎNE ----
    if st.button("➕ Ajouter une chaîne"):
        st.session_state.yt_channels.append(
            {"url": "", "name": "", "enabled": True}
        )
        save_channels(st.session_state.yt_channels)
        st.rerun()

    # Sauvegarde automatique si modification
    current_snapshot = json.dumps(st.session_state.yt_channels, sort_keys=True)
    if current_snapshot != st.session_state.get("yt_channels_snapshot"):
        save_channels(st.session_state.yt_channels)
        st.session_state.yt_channels_snapshot = current_snapshot

# =========================
# PREVIEW DERNIÈRES VIDÉOS
# =========================
st.subheader("🎬 Dernières vidéos")

# Bouton pour lancer la récupération
if st.button("🔄 Charger les dernières vidéos"):
    st.session_state.yt_previews = []

    for channel in st.session_state.yt_channels:
        if channel["enabled"] and channel["url"]:
            video = get_latest_video_from_channel(channel["url"])
            if video:
                if channel.get("name") and not video.get("channel_name"):
                    video["channel_name"] = channel["name"]
                st.session_state.yt_previews.append(video)

# Affichage des previews
if st.session_state.yt_previews:
    for video in st.session_state.yt_previews:
        col_thumb, col_info, col_select = st.columns([2, 5, 1])

        with col_thumb:
            st.image(video.get("thumbnail", ""), width=320)

        with col_info:
            channel_name = video.get("channel_name") or "Chaîne inconnue"
            st.caption(channel_name)
            st.markdown(f"**{video.get('title', '')}**")
            published = video.get("published") or ""
            if published:
                st.caption(published)
            st.caption(f"Source: `{video.get('source', '')}`")

        with col_select:
            video_id = video.get("video_id", "")
            checked = st.checkbox(
                "Sélectionner",
                value=video_id in st.session_state.yt_selected,
                key=f"yt_select_{video_id}"
            )
            if checked and video_id:
                st.session_state.yt_selected[video_id] = video
            elif video_id and video_id in st.session_state.yt_selected:
                st.session_state.yt_selected.pop(video_id, None)

        st.markdown("---")
