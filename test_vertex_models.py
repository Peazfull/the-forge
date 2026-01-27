"""
Script de test pour vérifier Nano Banana Pro via Google Gen AI SDK
À exécuter localement pour vérifier que tout fonctionne avant le déploiement
"""

from google import genai
from google.genai import types

# Configuration
PROJECT_ID = "gen-lang-client-0940349838"
LOCATION = "us-central1"

print(f"🔧 Configuration:")
print(f"   - Project ID: {PROJECT_ID}")
print(f"   - Location: {LOCATION}")
print()

# Test 1: Initialiser le client Vertex AI
print("🧪 Test 1: Initialisation du client Google Gen AI (Vertex AI)")
try:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    print("   ✅ Client initialisé avec succès")
except Exception as e:
    print(f"   ❌ Erreur d'initialisation: {e}")
    exit(1)

print()

# Test 2: Générer une image avec Nano Banana Pro
print("🧪 Test 2: Génération d'image avec Nano Banana Pro (Gemini 3 Pro Image)")
try:
    response = client.models.generate_content(
        model='gemini-3-pro-image-preview',
        contents='A simple blue circle on white background',
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
            ),
        ),
    )
    
    # Vérifier si une image a été générée
    image_found = False
    for part in response.parts:
        if part.inline_data:
            image_found = True
            break
    
    if image_found:
        print("   ✅ Image générée avec succès avec Nano Banana Pro !")
    else:
        print("   ⚠️ Aucune image trouvée dans la réponse")
        
except Exception as e:
    print(f"   ❌ Erreur lors de la génération : {e}")

print()
print("🏁 Tests terminés")
