# 🚀 Prototype Procom – Architecture MCP Multi-Agents RAG

Architecture moderne basée sur le **Model Context Protocol (MCP)** avec orchestrateur centralisé et agents RAG distribués, connectés à des outils externes (Gmail, PostgreSQL, Perplexity).

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              UI Debug (localhost:3000)              │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/JSON-RPC
┌──────────────────▼──────────────────────────────────┐
│         MCP Server Orchestrateur (port 8000)        │
│  • Reçoit et route les requêtes                     │
│  • Expose des outils MCP (tools)                    │
│  • Agrège les résultats des agents                  │
│  • Gère les ressources (resources)                  │
└──┬────────────┬────────────┬─────────────────────────┘
   │ MCP        │ MCP        │ MCP
   │            │            │
┌──▼──────┐  ┌─▼────────┐  ┌▼──────────┐
│ Agent A │  │ Agent B  │  │ Agent C   │
│ (5001)  │  │ (5002)   │  │ (5003)    │
│         │  │          │  │           │
│ RAG +   │  │ RAG +    │  │ RAG +     │
│ Gmail   │  │ Postgres │  │ Hybride   │
└──┬──────┘  └─┬────────┘  └┬──────────┘
   │            │             │
   │ MCP        │ MCP         │ MCP
   │            │             │
┌──▼──────┐  ┌─▼────────┐  ┌▼──────────┐
│ Gmail   │  │PostgreSQL│  │ Gmail +   │
│ MCP     │  │ MCP      │  │ Postgres  │
│ Server  │  │ Server   │  │ MCP       │
└─────────┘  └──────────┘  └───────────┘
```

## ✨ Fonctionnalités principales

### 🎯 Serveur MCP Orchestrateur
- **Distribution intelligente** des requêtes vers les agents appropriés
- **Agrégation** des résultats multi-agents
- **Exposition d'outils MCP** (`query_all_agents`, `query_specific_agent`)
- **Gestion des ressources** (liste des agents disponibles)
- **Protocole standardisé** MCP pour toutes les communications

### 🤖 Agents RAG Autonomes
- **RAG local** via ChromaDB avec vectorisation automatique
- **Connexions MCP externes** modulaires (Gmail, PostgreSQL, etc.)
- **Traitement contextuel** enrichi par outils externes
- **Isolation complète** : chaque agent a ses propres connexions
- **API FastAPI** pour communication avec l'orchestrateur

### 🔌 Intégrations MCP Disponibles
- **Gmail MCP** : recherche d'emails, envoi, marquage, gestion de dossiers
- **PostgreSQL MCP** : requêtes SQL sécurisées, exploration de schémas
- **Extensible** : ajout facile de nouveaux serveurs MCP (Slack, Notion, etc.)

### 🎨 Interface de Debug
- **Tests d'endpoints** en temps réel
- **Visualisation des logs** agrégés
- **Monitoring** de l'état des services
- **Copie rapide** des réponses JSON

## 🚀 Prérequis

- **Docker Desktop** installé ([Win/Mac/Linux](https://www.docker.com/products/docker-desktop))
- **Docker Compose** ≥ v2.22 (pour support du mode `watch`)
- **Node.js** ≥ 18 (pour les serveurs MCP npm)
- Un navigateur récent (Chrome, Firefox, Edge)

## ⚙️ Installation

### 1. Cloner le projet

```
git clone https://github.com/JLucGauvrit/Prototype-MCP-Orchestration-RAG
cd Prototype-MCP-Orchestration-RAG
```

### 2. Configuration des variables d'environnement

Créez un fichier `.env` à la racine du projet :

# API Keys

```
PERPLEXITY_API_KEY=your_perplexity_key_here
```

# Gmail MCP (Agent A et C)

```
GMAIL_API_KEY=your_gmail_api_key_here
GMAIL_MCP_ENABLED=true
```

# PostgreSQL MCP (Agent B et C)
```
POSTGRES_URL=postgresql://user:password@host:5432/dbname
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_MCP_ENABLED=true
```

# Configuration MCP

```
MCP_TRANSPORT=stdio
MCP_LOG_LEVEL=info
```

### 3. Structure du projet

```
.
├── docker-compose.yml          # Orchestration des services
├── .env                        # Variables d'environnement
│
├── server/
│   ├── mcp_server.py          # Serveur MCP orchestrateur
│   ├── Dockerfile
│   └── requirements.txt
│
├── agent/
│   ├── mcp_agent.py           # Agent RAG avec clients MCP
│   ├── vectorisation.py       # Utilitaires RAG
│   ├── Dockerfile
│   └── requirements.txt
│
├── rag_data/
│   ├── agent_a/               # Documents pour Agent A
│   ├── agent_b/               # Documents pour Agent B
│   └── agent_c/               # Documents pour Agent C
│
└── ui-MCP/
    ├── index.html             # Interface de debug
    ├── style.css
    └── script.js
```

### 4. Préparer les données RAG (optionnel)

Placez vos documents dans les dossiers `rag_data/agent_*/` :
- Formats supportés : `.txt`, `.pdf`, `.jsonl`, `.md`
- Les documents seront automatiquement vectorisés au démarrage

# Exemple : vectorisation manuelle

```
python agent/vectorisation.py --input ./rag_data/agent_a --output ./rag_data/agent_a/chroma_db
```

## 🐳 Lancement

### Mode développement (avec hot-reload)

# Build initial

```
docker compose build --no-cache
```

# Démarrage avec watch (auto-reload sur modifications)
docker compose up --watch

Les services se rebuild et redémarrent automatiquement à chaque modification du code.

### Mode production

```
docker compose up -d
```

## 🌐 Accès aux services

| Service | URL | Description |
|---------|-----|-------------|
| **UI Debug** | http://localhost:3000 | Interface graphique de test |
| **MCP Server** | http://localhost:8000 | Orchestrateur MCP principal |
| **Agent A** | http://localhost:5001/health | Agent RAG + Gmail |
| **Agent B** | http://localhost:5002/health | Agent RAG + PostgreSQL |
| **Agent C** | http://localhost:5003/health | Agent RAG + Hybride |

## 🧪 Tester l'architecture

### Via l'interface UI (recommandé)

1. Ouvrez http://localhost:3000
2. Tapez votre question dans le champ de recherche
3. Visualisez les réponses agrégées de tous les agents

### Via curl

**Interroger tous les agents :**

```
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Quels emails récents parlent de data federation?"}'
```

**Interroger un agent spécifique :**

```
curl -X POST http://localhost:8000/query-agent \
  -H "Content-Type: application/json" \
  -d '{"agent": "agent-a", "query": "Recherche mes emails non lus"}'
```

**Vérifier la santé des services :**
# Orchestrateur
```
curl http://localhost:8000/health
```
# Agent A
```
curl http://localhost:5001/health
```

### Exemples de requêtes MCP

**Lister les agents disponibles :**
```
curl http://localhost:8000/resources/agents
```

**Appeler un outil MCP directement :**
```
curl -X POST http://localhost:8000/tools/query_all_agents \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"query": "Explique-moi le RAG"}}'
```
## 🔧 Configuration avancée

### Ajouter un nouvel agent

1. **Modifiez `docker-compose.yml`** :
```
agent-d:
  build: ./agent
  container_name: agent-d
  ports:
    - "5004:5000"
  environment:
    - AGENT_NAME=AgentD
    - RAG_PATH=/rag_data/agent_d
    # Ajoutez vos connexions MCP
  volumes:
    - ./rag_data/agent_d:/rag_data/agent_d
```

2. **Mettez à jour `server/mcp_server.py`** :

```
AGENTS = {
    "agent-a": "http://agent-a:5000",
    "agent-b": "http://agent-b:5000",
    "agent-c": "http://agent-c:5000",
    "agent-d": "http://agent-d:5000"  # Nouveau
}
```

### Connecter un nouvel outil MCP

Dans `agent/mcp_agent.py`, ajoutez la connexion :

```
# Exemple : connexion à Slack MCP
if os.getenv("SLACK_MCP_ENABLED") == "true":
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-slack"],
        env={"SLACK_TOKEN": os.getenv("SLACK_TOKEN", "")}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_servers["slack"] = session
```

## 🛠️ Résolution des problèmes

### Erreur : "MCP server not responding"

**Cause :** Le serveur MCP n'a pas démarré correctement.

**Solution :**
# Vérifiez les logs
```
docker logs mcp-server
```

# Redémarrez le service
```
docker compose restart mcp-server
```

### Erreur : "Gmail MCP connection failed"

**Cause :** Clé API Gmail invalide ou non configurée.

**Solution :**
1. Vérifiez que `GMAIL_API_KEY` est bien défini dans `.env`
2. Assurez-vous que l'API Gmail est activée dans Google Cloud Console
3. Vérifiez les logs de l'agent :
docker logs agent-a

### Erreur : "PostgreSQL connection refused"

**Cause :** URL de connexion PostgreSQL incorrecte.

**Solution :**
# Testez la connexion manuellement
```
docker exec -it agent-b python -c "import psycopg2; psycopg2.connect('$POSTGRES_URL')"
```

# Vérifiez le format de POSTGRES_URL dans .env
# Format attendu : `postgresql://user:password@host:5432/database`

### Erreur : "ChromaDB collection not found"

**Cause :** Les données RAG n'ont pas été vectorisées.

**Solution :**
# Vectorisez manuellement

```
docker exec -it agent-a python vectorisation.py --input /rag_data/agent_a
```

### Performance lente avec mode watch

**Cause :** Le mode watch surveille tous les fichiers.

**Solution :**
```
# Utilisez le mode standard en développement
docker compose up

# Ou ajoutez des exclusions dans docker-compose.yml
watch:
  - path: ./agent
    action: rebuild
    ignore:
      - "**/__pycache__"
      - "**/.pytest_cache"
```

## ⚠️ Limitations et considérations

### Phase expérimentale
- **Architecture en évolution** : Le protocole MCP évolue rapidement
- **Tests limités** : Testez intensivement avant usage en production
- **Sécurité** : Auditez les connexions MCP externes avant déploiement

### Performance
- **Latence** : Les appels MCP en cascade ajoutent de la latence
- **Timeouts** : Configurez des timeouts appropriés (120s recommandé)
- **Cache** : Implémentez un cache Redis pour les requêtes fréquentes

### Scalabilité
- **Agents limités** : Architecture actuelle limitée à ~10 agents
- **Pas de load balancing** : Implémentez Nginx/HAProxy pour production
- **État éphémère** : Les données ChromaDB sont perdues au redémarrage des conteneurs

### Sécurité
- **Clés API exposées** : Utilisez Docker secrets en production
- **CORS permissif** : Restreignez les origins en production
- **SQL Injection** : L'agent PostgreSQL nécessite une validation stricte

## 📚 Ressources et documentation

### Model Context Protocol (MCP)
- [Documentation officielle MCP](https://modelcontextprotocol.io/)
- [Spécification MCP](https://modelcontextprotocol.io/specification/2025-03-26/architecture)
- [Tutoriel : Build Your First MCP Server](https://towardsdatascience.com/model-context-protocol-mcp-tutorial-build-your-first-mcp-server-in-6-steps/)

### Serveurs MCP utilisés
- [Gmail MCP Server](https://github.com/jeremyjordan/mcp-gmail) - Intégration Gmail
- [PostgreSQL MCP Server](https://github.com/crystaldba/postgres-mcp) - Intégration PostgreSQL
- [MCP Servers Directory](https://modelcontextprotocol.io/examples) - Catalogue officiel

### RAG et Architecture
- [Integrating Agentic RAG with MCP](https://becomingahacker.org/integrating-agentic-rag-with-mcp-servers-technical-implementation-guide-1aba8fd4e442)
- [MCP Server Patterns](https://dev.to/codanyks/mcp-server-wrap-up-patterns-libraries-scaling-context-1f02)
- [Security-First MCP Architecture](https://prefactor.tech/blog/security-first-mcp-architecture-patterns)

### Technologies utilisées
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web Python
- [ChromaDB](https://www.trychroma.com/) - Base vectorielle pour RAG
- [Docker Compose](https://docs.docker.com/compose/) - Orchestration multi-conteneurs
- [Sentence Transformers](https://www.sbert.net/) - Embeddings de texte

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Pushez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 Roadmap

### Version 0.2 (Q1 2025)
- [ ] Support de serveurs MCP additionnels (Notion, Slack, GitHub)
- [ ] Implémentation d'un cache Redis pour améliorer les performances
- [ ] Interface UI améliorée avec visualisation de graphes d'agents
- [ ] Système de logging centralisé (ELK stack)

### Version 0.3 (Q2 2025)
- [ ] Authentification et autorisation (JWT tokens)
- [ ] Load balancing des agents avec Nginx
- [ ] Persistance des données ChromaDB avec volumes Docker
- [ ] Métriques Prometheus et dashboards Grafana

### Version 1.0 (Q3 2025)
- [ ] Déploiement Kubernetes avec Helm charts
- [ ] Auto-scaling des agents basé sur la charge
- [ ] Support multi-tenancy
- [ ] Documentation API OpenAPI complète

## 📄 Licence

MIT License © 2025 JLucGauvrit

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

## 👨‍💻 Auteur

**Jean-Luc Gauvrit** - [@JLucGauvrit](https://github.com/JLucGauvrit)

## 🙏 Remerciements

- [Anthropic](https://www.anthropic.com/) pour le développement du Model Context Protocol
- La communauté MCP pour les serveurs et exemples open source
- [Perplexity AI](https://www.perplexity.ai/) pour l'API de génération de contenu

---

**⭐ Si ce projet vous est utile, n'hésitez pas à lui donner une étoile !**

## Licence
MIT License © 2025 JLucGauvrit
