"""
Script de test pour vérifier la disponibilité des modèles Gemini via Vertex AI
À exécuter localement pour vérifier que tout fonctionne avant le déploiement
"""

import vertexai
from vertexai.preview.generative_models import GenerativeModel
import streamlit as st

# Configuration (à adapter)
try:
    PROJECT_ID = st.secrets["GCP_PROJECT_ID"]
    LOCATION = st.secrets["VERTEX_AI_LOCATION"]
except:
    PROJECT_ID = "gen-lang-client-0940349838"
    LOCATION = "us-central1"

print(f"🔧 Configuration:")
print(f"   - Project ID: {PROJECT_ID}")
print(f"   - Location: {LOCATION}")
print()

# Initialiser Vertex AI
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print("✅ Vertex AI initialisé avec succès")
except Exception as e:
    print(f"❌ Erreur d'initialisation Vertex AI: {e}")
    exit(1)

print()

# Test 1: Gemini 3 Pro Image Preview
print("🧪 Test 1: Chargement de Gemini 3 Pro Image Preview (Nano Banana Pro)")
try:
    model_3_pro_image = GenerativeModel("gemini-3-pro-image-preview")
    print("   ✅ Gemini 3 Pro Image Preview chargé avec succès !")
except Exception as e:
    print(f"   ❌ Erreur lors du chargement de Gemini 3 Pro Image : {e}")

print()

# Test 2: Gemini 2.5 Flash Image
print("🧪 Test 2: Chargement de Gemini 2.5 Flash Image")
try:
    model_2_5_flash_image = GenerativeModel("gemini-2.5-flash-image")
    print("   ✅ Gemini 2.5 Flash Image chargé avec succès !")
except Exception as e:
    print(f"   ❌ Erreur lors du chargement de Gemini 2.5 Flash Image : {e}")

print()
print("🏁 Tests terminés")
