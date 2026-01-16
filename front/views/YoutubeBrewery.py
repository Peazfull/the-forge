import streamlit as st
import json
from datetime import datetime, timedelta, timezone
import services.youtube_brewery.youtube_utils as youtube_utils
from services.youtube_brewery.storage_utils import load_channels, save_channels
from services.youtube_brewery.transcript_utils import fetch_video_transcript
from services.youtube_brewery.process_transcript import process_transcript
from services.raw_storage.raw_news_service import (
    enrich_raw_items,
    insert_raw_news,
    fetch_raw_news
)



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

if "yt_ai_preview_text" not in st.session_state:
    st.session_state.yt_ai_preview_text = ""

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
            detected_name = youtube_utils.get_channel_name_from_url(channel["url"])
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

col12, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1])

with col12:
    load_videos = st.button("🔄 Charger les vidéos des :", use_container_width=True)


with col3:
    hours_window = st.number_input(
        "Fenêtre (h)",
        min_value=1,
        max_value=168,
        value=24,
        step=1,
        label_visibility="collapsed"
    )

with col4:
    st.write("dernières heures")

# Bouton pour lancer la récupération
if load_videos:
    st.session_state.yt_previews = []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_window)

    for channel in st.session_state.yt_channels:
        if channel["enabled"] and channel["url"]:
            if hasattr(youtube_utils, "get_latest_videos_from_channel"):
                videos = youtube_utils.get_latest_videos_from_channel(channel["url"], limit=20)
            else:
                latest = youtube_utils.get_latest_video_from_channel(channel["url"])
                videos = [latest] if latest else []
            for video in videos:
                published_raw = video.get("published") or ""
                published_dt = None
                try:
                    if published_raw.endswith("Z"):
                        published_dt = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                    else:
                        published_dt = datetime.fromisoformat(published_raw)
                except Exception:
                    try:
                        published_dt = datetime.strptime(published_raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    except Exception:
                        published_dt = None

                if published_dt and published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)

                if published_dt and published_dt < cutoff:
                    continue

                if channel.get("name") and not video.get("channel_name"):
                    video["channel_name"] = channel["name"]

                video_id = video.get("video_id")
                if video_id and video_id not in {v.get("video_id") for v in st.session_state.yt_previews}:
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

st.divider()

# =========================
# PREVIEW OUTPUT CONCATÉNÉ
# =========================
st.subheader("🧩 Preview IA (concaténé)")

col_generate, col_clear_preview = st.columns(2)

with col_generate:
    if st.button("🚀 Générer preview IA (transcripts)", use_container_width=True):
        if not st.session_state.yt_selected:
            st.error("Aucune vidéo sélectionnée.")
        else:
            st.session_state.yt_ai_preview_text = ""
            items = []
            selected_videos = list(st.session_state.yt_selected.values())
            total = len(selected_videos)
            progress = st.progress(0)

            for idx, video in enumerate(selected_videos, start=1):
                title = video.get("title") or "Sans titre"
                channel = video.get("channel_name") or "Chaîne inconnue"
                published = video.get("published") or ""
                url = video.get("url") or ""

                st.write(f"▶️ Traitement: **{title}**")

                if not url:
                    st.error(f"URL manquante pour la vidéo: {title}")
                    progress.progress(int(idx / total * 100))
                    continue

                try:
                    with st.spinner("Récupération du transcript…"):
                        transcript = fetch_video_transcript(url)
                except Exception as e:
                    st.error(f"Transcript indisponible pour {title}")
                    st.caption(str(e))
                    progress.progress(int(idx / total * 100))
                    continue

                with st.spinner("Analyse IA en cours…"):
                    result = process_transcript(transcript)

                if result["status"] != "success":
                    st.error(f"Erreur IA pour {title}")
                    st.caption(result.get("message", "Erreur inconnue"))
                    progress.progress(int(idx / total * 100))
                    continue

                for item in result.get("items", []):
                    item["source_name"] = channel
                    item["source_link"] = url
                    item["source_date"] = published
                    item["source_raw"] = None
                    items.append(item)

                st.success(f"✅ {len(result.get('items', []))} items générés")
                progress.progress(int(idx / total * 100))

            st.session_state.yt_ai_preview_text = json.dumps(
                {"items": items},
                indent=2,
                ensure_ascii=False
            )

with col_clear_preview:
    if st.button("🧹 Clear preview", use_container_width=True):
        st.session_state.yt_ai_preview_text = ""

if st.session_state.yt_ai_preview_text:
    edited_preview = st.text_area(
        label="",
        value=st.session_state.yt_ai_preview_text,
        height=450,
        key="yt_ai_preview_editor"
    )

    col_validate, col_clear = st.columns(2)

    with col_validate:
        if st.button("✅ Envoyer en DB", use_container_width=True):
            raw_json_text = edited_preview

            try:
                data = json.loads(raw_json_text)
            except json.JSONDecodeError:
                st.error("❌ JSON invalide. Corrige la preview avant l'envoi.")
                st.stop()

            if "items" not in data or not isinstance(data["items"], list):
                st.error("❌ Format JSON invalide (clé 'items' manquante).")
                st.stop()

            if not data["items"]:
                st.error("❌ Aucun item à insérer.")
                st.stop()

            enriched_items = enrich_raw_items(
                data["items"],
                flow="youtube",
                source_type="youtube",
                source_raw=None
            )

            result = insert_raw_news(enriched_items)

            if result["status"] == "success":
                st.success(f"✅ {result['inserted']} items insérés en base")
                st.session_state.yt_ai_preview_text = ""
            else:
                st.error("❌ Erreur lors de l'insertion en DB")
                st.caption(result.get("message", "Erreur inconnue"))

    with col_clear:
        if st.button("🧹 Clear sélection", use_container_width=True):
            st.session_state.yt_selected = {}
            st.session_state.yt_ai_preview_text = ""
            st.rerun()
else:
    st.caption("Aucune preview générée pour le moment")

st.divider()

# =========================
# DERNIERS CONTENUS EN BASE
# =========================
st.subheader("🗄️ Derniers contenus en base 👇")

with st.expander("Tout voir 👀", expanded=False):
    raw_items = fetch_raw_news(limit=100)

    if not raw_items:
        st.caption("Aucun contenu en base pour le moment")
    else:
        for item in raw_items:
            st.markdown("---")
            st.caption(f"🕒 {item['processed_at']} · Source : {item['source_type']}")
            st.markdown(f"**{item['title']}**")
            st.write(item['content'])
