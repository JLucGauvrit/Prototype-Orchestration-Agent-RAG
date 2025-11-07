#!/bin/bash

# Script de démarrage rapide pour RAG Multi-Agent Orchestrator
# Ce script configure et démarre automatiquement tout le système

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   RAG Multi-Agent Orchestrator - Setup Script          ║"
echo "║   Orchestration avec MCP + PostgreSQL + pgvector        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Vérification des prérequis
info "Vérification des prérequis..."

if ! command -v docker &> /dev/null; then
    error "Docker n'est pas installé. Veuillez installer Docker Desktop."
    exit 1
fi
success "Docker installé"

if ! docker compose version &> /dev/null; then
    error "Docker Compose n'est pas disponible."
    exit 1
fi
success "Docker Compose disponible"

# Création de la structure de dossiers
info "Création de la structure de dossiers..."

mkdir -p orchestrator/static
mkdir -p agents/{agent_1,agent_2,agent_3}
mkdir -p shared

success "Structure de dossiers créée"

# Configuration des fichiers
info "Configuration des fichiers..."

# Placer les fichiers dans les bons dossiers
cat > orchestrator/static/.gitkeep << EOF
# Placeholder
EOF

success "Fichiers de configuration créés"

# Configuration des variables d'environnement
if [ ! -f .env ]; then
    info "Création du fichier .env..."
    cat > .env << EOF
# Configuration RAG Multi-Agent Orchestrator
# Généré automatiquement le $(date)

# IMPORTANT: Remplacez ces valeurs par vos vraies clés API
GEMINI_API_KEY=your_gemini_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Configuration PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=rag_db

# Configuration serveurs
ORCHESTRATOR_HOST=localhost
ORCHESTRATOR_PORT=8000
MCP_SERVER_PORT=8001

# Logging
LOG_LEVEL=INFO
EOF
    
    warning "Fichier .env créé avec des valeurs par défaut"
    warning "⚠️  IMPORTANT: Éditez le fichier .env et ajoutez vos clés API !"
    echo ""
    echo "Pour obtenir vos clés API:"
    echo "  • Gemini: https://ai.google.dev/gemini-api/docs/api-key"
    echo "  • Perplexity: https://docs.perplexity.ai/docs/getting-started"
    echo ""
    read -p "Appuyez sur Entrée quand vous avez configuré vos clés API..."
else
    success "Fichier .env existant trouvé"
fi

# Vérification des clés API
if grep -q "your_gemini_api_key_here" .env; then
    warning "La clé Gemini n'est pas configurée !"
    warning "Certaines fonctionnalités ne seront pas disponibles."
fi

# Demander si l'utilisateur veut démarrer
echo ""
info "Prêt à démarrer le système. Cela va:"
echo "  1. Construire les images Docker"
echo "  2. Démarrer PostgreSQL avec pgvector"
echo "  3. Initialiser la base de données"
echo "  4. Démarrer l'orchestrateur"
echo "  5. Démarrer les 3 agents RAG"
echo ""

read -p "Voulez-vous continuer ? (o/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    info "Arrêt du script."
    exit 0
fi

# Arrêter les conteneurs existants
info "Arrêt des conteneurs existants (si présents)..."
docker compose down 2>/dev/null || true
success "Conteneurs arrêtés"

# Construction et démarrage
info "Construction des images Docker..."
docker compose build --no-cache

success "Images construites"

info "Démarrage des services..."
docker compose up -d

# Attendre que PostgreSQL soit prêt
info "Attente du démarrage de PostgreSQL..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        success "PostgreSQL prêt"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
    echo -n "."
done

if [ $attempt -eq $max_attempts ]; then
    error "PostgreSQL n'a pas démarré à temps"
    exit 1
fi

# Attendre que l'orchestrateur soit prêt
info "Attente du démarrage de l'orchestrateur..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/api/health &> /dev/null; then
        success "Orchestrateur prêt"
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
    echo -n "."
done

echo ""
success "Système démarré avec succès !"
echo ""

# Afficher l'état des services
info "État des services:"
docker compose ps

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  SYSTÈME OPÉRATIONNEL                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Interface Web:        http://localhost:8000"
echo "📡 API Orchestrateur:    http://localhost:8000/api"
echo "🔍 Health Check:         http://localhost:8000/api/health"
echo "📚 API Docs (Swagger):   http://localhost:8000/docs"
echo ""
echo "📊 PostgreSQL:"
echo "   Host: localhost:5432"
echo "   User: postgres"
echo "   DB:   rag_db"
echo ""
echo "🤖 Agents:"
echo "   Agent 1 (Gemini General):      http://localhost:8080"
echo "   Agent 2 (Perplexity Current):  Interne Docker"
echo "   Agent 3 (Gemini Analysis):     Interne Docker"
echo ""
echo "📋 Commandes utiles:"
echo "   Logs en temps réel:   docker compose logs -f"
echo "   Arrêter:              docker compose down"
echo "   Redémarrer:           docker compose restart"
echo "   État:                 docker compose ps"
echo ""

# Tester une requête
info "Test de la connexion..."
if curl -s http://localhost:8000/api/agents | grep -q "agent"; then
    success "Les agents sont connectés !"
    
    # Afficher les agents connectés
    echo ""
    echo "Agents connectés:"
    curl -s http://localhost:8000/api/agents | python3 -m json.tool 2>/dev/null || echo "  (utilisez 'curl http://localhost:8000/api/agents' pour voir les détails)"
else
    warning "Les agents mettent du temps à se connecter. Attendez 10-20 secondes."
fi

echo ""
info "Ouvrez http://localhost:8000 dans votre navigateur pour commencer !"
echo ""

# Option pour suivre les logs
read -p "Voulez-vous suivre les logs ? (o/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    docker compose logs -f
fi
