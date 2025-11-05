#!/bin/bash
set -e

echo "🚀 Démarrage du conteneur ${AGENT_NAME}"
echo "📂 Répertoire RAG: ${RAG_PATH}"

# Lance la vectorisation
echo "⏳ Phase 1: Vectorisation des documents..."
python vectorisation.py

# Vérifie que la vectorisation s'est bien passée
if [ $? -eq 0 ]; then
    echo "✅ Vectorisation réussie"
else
    echo "❌ Erreur lors de la vectorisation"
    exit 1
fi

# Démarre le serveur FastAPI
echo "⏳ Phase 2: Démarrage du serveur FastAPI..."
exec uvicorn agent:app --host 0.0.0.0 --port 5000
