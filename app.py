import streamlit as st
from front.layout.sidebar import render_sidebar
from services.supabase_client import get_supabase
import importlib.util
import sys
import os

# Configuration de la page pour cacher la navigation automatique
st.set_page_config(
    page_title="THE FORGE",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger la police Inter
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialiser la page courante si elle n'existe pas
if "current_page" not in st.session_state:
    st.session_state.current_page = None

# Afficher la sidebar
render_sidebar()

# Afficher la page sélectionnée ou la page d'accueil
if st.session_state.current_page:
    try:
        # Construire le chemin complet du fichier
        page_path = os.path.join(os.path.dirname(__file__), st.session_state.current_page + ".py")
        
        # Vérifier que le fichier existe
        if os.path.exists(page_path):
            # Lire et exécuter le fichier
            with open(page_path, 'r', encoding='utf-8') as f:
                code = f.read()
            exec(code, {'st': st, '__file__': page_path})
        else:
            st.error(f"Page non trouvée : {page_path}")
            st.session_state.current_page = None
            st.title("Accueil")
            st.write("Sélectionne une page dans la sidebar")
    except Exception as e:
        st.error(f"Erreur lors du chargement de la page : {e}")
        st.session_state.current_page = None
        st.title("Accueil")
        st.write("Sélectionne une page dans la sidebar")
else:
    # PAGE D'ACCUEIL
    
    # Centrer l'image avec des colonnes
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("front/layout/assets/Theforge_logo.png", width=500)
    
    #test supabase
    st.write("SUPABASE_URL loaded:", "SUPABASE_URL" in st.secrets)
    
    if st.button("Insert test row"):
        supabase = get_supabase()

        data = {
            "flow": "hand_text",
            "status": "draft",
            "source_type": "manual",
            "source_raw": "Test insert depuis app déployée",
            "title": "Premier insert Streamlit",
            "score_global": 7.5
        }

        supabase.table("brew_items").insert(data).execute()
        st.success("Ligne insérée en base ✅")
    
    #ajouter un gif de la page d'accueil
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col3:
        st.image("front/layout/assets/pixel_epee.gif", width=300)