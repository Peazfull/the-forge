import streamlit as st
from services.hand_brewery.process_text import process_text
from datetime import datetime

# ======================================================
# CALLBACKS (AVANT LES WIDGETS)
# ======================================================

def clear_text_input():
    st.session_state.hand_text_input = ""
    st.session_state.text_status = []
    st.session_state.text_progress = 0
    st.session_state.ai_preview_text = ""

# ======================================================
# TITRE PAGE
# ======================================================

st.title("👨🏻‍💻 Hand Brewery")
st.divider()

# ======================================================
# SESSION STATE (FRONT ONLY)
# ======================================================

# --- URL workflow ---
if "url_status" not in st.session_state:
    st.session_state.url_status = []

if "url_progress" not in st.session_state:
    st.session_state.url_progress = 0

# --- TEXTE workflow ---
if "text_status" not in st.session_state:
    st.session_state.text_status = []

if "text_progress" not in st.session_state:
    st.session_state.text_progress = 0

if "ai_preview_text" not in st.session_state:
    st.session_state.ai_preview_text = ""


# ======================================================
# BLOC 1 — URL
# ======================================================

st.subheader("📰 Ajouter une URL d’article")

# Layout : input 3/5 – bouton lancer 1/5 – bouton clear 1/5
col_input, col_launch, col_clear = st.columns([3, 1, 1])

with col_input:
    url = st.text_input(
    label="",
    placeholder="https://example.com/article",
    label_visibility="collapsed"
)


with col_launch:
    if st.button("🚀 Lancer", use_container_width=True):
        # TODO: process_url(url)
        st.session_state.url_progress = 20
        st.session_state.url_status = [
            "Traitement scrapping en cours",
            "Envoi du texte à l’IA",
            "Output de l’IA",
            "X news retournées",
            "Traitement JSON pour DB",
            f"Ajout en DB à {datetime.now().strftime('%H:%M:%S')}",
        ]

with col_clear:
    if st.button("🧹 Clear", use_container_width=True):
        url = ""
        st.session_state.url_status = []
        st.session_state.url_progress = 0

# --- STATUT URL ---
if st.session_state.url_status:
    st.progress(st.session_state.url_progress)
    for step in st.session_state.url_status:
        st.write(f"⏳ {step}")

st.divider()

# ======================================================
# BLOC 2 — TEXTE LIBRE
# ======================================================

st.subheader("✍️ Coller du texte")

text_input = st.text_area(
    "Texte à analyser",
    placeholder="Colle ici ton article ou ton texte brut…",
    height=250,
    key="hand_text_input"
)

col_text_1, col_text_2 = st.columns(2)

with col_text_1:
    if st.button("🚀 Lancer le workflow TEXTE", use_container_width=True):

        # --- STATUT 1 : démarrage
        st.session_state.text_progress = 20
        st.session_state.text_status = [
            "Traitement du texte en cours",
        ]

        result = process_text(text_input)

        if result["status"] == "success":

            # --- STATUT 2 : succès backend
            st.session_state.text_progress = 60
            st.session_state.text_status.extend([
                "JSON structuré généré",
                f"{len(result['items'])} news retournées",
            ])

            # --- Génération preview
            preview_blocks = []
            for item in result.get("items", []):
                block = f"""
### {item['title']}
Zone: {', '.join(item['zone'])}
Tags: {', '.join(item['tags'])}

{item['content']}
---
"""
                preview_blocks.append(block)

            st.session_state.ai_preview_text = "\n".join(preview_blocks)

        else:
            # --- STATUT ERREUR
            st.session_state.text_progress = 0
            st.session_state.text_status = ["Erreur lors du traitement"]
            st.error(f"Erreur : {result['message']}")

with col_text_2:
    st.button(
        "🧹 Clear TEXTE",
        use_container_width=True,
        on_click=clear_text_input
    )


# --- AFFICHAGE STATUT TEXTE ---
if st.session_state.text_status:
    st.progress(st.session_state.text_progress)
    for step in st.session_state.text_status:
        st.write(f"⏳ {step}")

st.divider()



#======================================================
# BLOC 3 — PREVIEW AI
#======================================================
st.subheader("👀 Preview de l'IA")

# ---- Bouton lancer (simule l'output IA)
if st.button("🚀 Générer preview IA", key="generate_preview"):
    st.session_state.ai_preview_text = f"""
### Marchés européens en hausse
Zone: Europe
Thème: Bourse
Labels: CAC 40, Actions

Les marchés européens ont progressé ce matin portés par le secteur bancaire.

---

### Inflation sous contrôle aux États-Unis
Zone: US
Thème: Macro
Labels: Inflation, Fed

Les derniers chiffres montrent un ralentissement de l’inflation, rassurant les investisseurs.

---

Généré à {datetime.now().strftime('%H:%M:%S')}
"""

# ---- Zone éditable globale
if st.session_state.ai_preview_text:
    edited_preview = st.text_area(
        label="",
        value=st.session_state.ai_preview_text,
        height=450,
        key="ai_preview_editor"
    )

    col_validate, col_clear = st.columns([1, 1])

    # ---- Bouton valider
    with col_validate:
        if st.button("✅ Valider et envoyer en DB", key="validate_preview", use_container_width=True):
            # TODO :
            # - parser edited_preview
            # - répartir en blocs
            # - insérer en DB
            st.success("Contenu validé (DB à brancher)")
    
    # ---- Bouton clear
    with col_clear:
        if st.button("🧹 Clear preview", key="clear_preview", use_container_width=True):
            st.session_state.ai_preview_text = ""
            st.rerun()

st.divider()

# ======================================================
# BLOC 4 — TABLE DB (MOCK)
# ======================================================

st.subheader("🗄️ Contenu de la base de données")

# MOCK DB — FRONT ONLY
mock_db = [
    {
        "id": 1,
        "source": "URL",
        "input": "https://example.com/article-1",
        "nb_news": 4,
        "status": "DONE",
        "finished_at": "2026-01-12 14:32",
    },
    {
        "id": 2,
        "source": "TEXTE",
        "input": "Copié / collé",
        "nb_news": 7,
        "status": "DONE",
        "finished_at": "2026-01-12 14:45",
    },
]

st.dataframe(
    mock_db,
    use_container_width=True,
    hide_index=True
)

st.divider()
