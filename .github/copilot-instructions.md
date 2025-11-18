## Instructions rapides pour les agents IA (GitHub Copilot / AI coding agents)

But : rendre un agent IA productif rapidement sur ce dépôt en expliquant l'architecture, les points d'intégration et les commandes de dev/diagnostic précises.

- **Architecture (haute-niveau)** : l'app orchestre plusieurs services Docker : `ui`, `orchestrator`, `mcp-server`, un template `mcp-client-template`, un template d'agent `agent-rag-template` et `postgres` (voir `docker-compose.yml`). L'orchestrateur utilise le SDK Docker pour créer/stopper dynamiquement des conteneurs agents (`orchestrator/main.py`).

- **Points d'entrée HTTP importants** :
  - Orchestrateur (`orchestrator/main.py`) expose `/` (health), `GET /agents`, `POST /agents` (crée un conteneur agent via Docker SDK) et `DELETE /agents/{name}`.
  - Agents RAG (ex. `agents/rag/main.py`) exposent au minimum `/health` et `/query?q=...`.
  - MCP server minimal : `mcp/server/main.py` expose `/health`.
  - MCP clients (ex. `mcp/client/main.py`) exposent `/health` et un endpoint `POST /notify` qui envoie des notifications au MCP server.
  - UI (`ui/app.js`) consomme l'API backend via `API_URL` ; il appelle notamment `GET /agents`, `POST /agents` et (dans le code) `POST /prompt` — vérifier la correspondance des routes si le front renvoie des 404.

- **Variables d'environnement clés** : définies dans `env.example` (copier en `.env`)
  - `GEMINI_API_KEY`, `PERPLEXITY_API_KEY` (LLM)
  - `POSTGRES_*` (accès DB)
  - `ORCHESTRATOR_HOST`, `ORCHESTRATOR_PORT`, `MCP_SERVER_PORT`

- **Flux de données / responsabilité des composants** :
  - L'utilisateur → UI → Orchestrateur : l'orchestrateur répartit les tâches vers MCP server/clients, ou crée dynamiquement des agents.
  - Agents → indexent / interagissent avec PostgreSQL + pgvector (DB vectorielle) pour le RAG.

- **Exemples de commandes utiles (dev / debug)** :
  - Démarrage complet : `docker compose up --build`
  - Mode détaché : `docker compose up -d --build`
  - Logs : `docker compose logs -f` ou `docker compose logs -f orchestrator`
  - Créer un agent (via API orchestrateur) :
    ```bash
    curl -X POST http://localhost:8000/agents
    ```
  - Lister les agents : `curl http://localhost:8000/agents`
  - Health check agent : `curl http://localhost:9000/health` (adapter le port selon le conteneur)

- **Patterns spécifiques au projet (à respecter / regarder)**
  - Orchestrateur crée des conteneurs en nombre séquentiel `agent-rag-<n>` et monte un volume partagé `rag_data` (voir `orchestrator/main.py`).
  - Noms des services/volumes/réseaux : `frontend`, `backend`, `rag_data`, `pg_data` (utilisés dans `docker-compose.yml`).
  - Le code assume les URL internes Docker (ex. `http://mcp-server:7000`, `postgres`), donc lors de tests locaux hors Docker adapter `POSTGRES_URL` et `MCP_SERVER_URL`.
  - Frontend attend un endpoint `POST /prompt` pour soumettre une requête (vérifier correspondance avec les routes exposées par l'orchestrateur si le front renvoie des erreurs).

- **Fichiers de référence rapide** :
  - `docker-compose.yml` : topologie des services, noms de conteneurs, réseaux et volumes
  - `orchestrator/main.py` : logique de création/déletion d'agents (Docker SDK) et routes API exposées
  - `agents/rag/main.py` : exemple minimal d'API agent (`/health`, `/query`)
  - `mcp/server/main.py` et `mcp/client/main.py` : pattern minimal du protocole MCP (notify / health)
  - `ui/app.js` : attentes front-end (endpoints, payloads) et UX flows (create/delete agents, prompt)

- **Risques et points à vérifier avant de modifier** :
  - Assurez-vous que les noms de réseau/volumes dans `orchestrator` (client.containers.run) correspondent exactement à ceux de `docker-compose.yml`.
  - Le front et l'orchestrateur peuvent utiliser des chemins d'API différents (`/api/query` vs `/prompt`). Rechercher les deux variantes dans le code si vous corrigez des 404.
  - Les clés LLM (Gemini, Perplexity) ne sont pas committées — utiliser `.env` local et ne pas les pousser.

- **Choses concrètes qu'un agent IA peut aider à faire ici** :
  - Ajouter ou corriger des routes HTTP pour correspondre au front (`/prompt` vs `/api/query`). Indiquer clairement la route souhaitée et mettre à jour `ui/app.js` ou `orchestrator/main.py`.
  - Améliorer la création d'agents : validation des noms, gestion d'erreurs et retour JSON cohérent (ex. inclure `agent_name` et `container_id`).
  - Documenter la procédure de provisionnement de la DB vectorielle si `init_db.sql` existe ou est attendu.

Si une section manque de détails (ex. mapping exact `POST /prompt` → code backend), dites-moi quelle route vous voulez prioriser et je fusionne/ajuste le fichier pour correspondre exactement au code.
