#!/bin/bash

# Script pour lancer l'application Streamlit

# Aller dans le répertoire du script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/front"

# Activer l'environnement virtuel
source ../venv/bin/activate

# Lancer Streamlit
streamlit run app.py
