# 🐳 Prototype Procom – Multi Agents RAG avec Orchestrateur & UI

Interface graphique de débogage + architecture multi-agents RAG, orchestrée via FastAPI et Docker Compose.

## 🚀 Prérequis

- **Docker Desktop** installé ([Win/Mac/Linux])[1]
- **Docker Compose** ≥ v2.22 (pour support du mode `watch`)
- Un navigateur récent (Chrome, Firefox, Edge)

## ⚙️ Installation du projet

1. **Clone le repo** (exemple)
   ```bash
   git clone https://github.com/JLucGauvrit/Prototype-Orchestration-Agent-RAG && cd Prototype-Orchestration-Agent-RAG
   ```
2. **Configure tes variables d’environnement**  
   Crée un fichier `.env` à la racine pour la clé Perplexity :
   ```
   PERPLEXITY_API_KEY=xxxxxxxxxxxxxxxxxxxxxxx
   ```

3. **Structure recommandée**
   ```
   .
   ├── docker-compose.yml
   ├── agent/
   │   └── agent.py
   ├── server/
   │   └── app.py
   ├── rag_data/
   │   └── agent_a/ agent_b/ agent_c/
   ├── debug-ui/
   │   └── index.html style.css script.js
   ```

## 🐳 Lancement en mode développement

### 1. **Build initial des images**

```bash
docker compose build --no-cache
```

### 2. **Démarrer en mode watch auto-sync/restart**
```bash
docker compose up --watch
```
- Les services se rebuild et redémarrent automatiquement à chaque modification (hot reload).
- Les logs s’affichent en temps réel.

***

## 🌐 Lancer l’interface graphique

Accède à l’UI de debug sur :
```
http://localhost:3000
```

- Tu peux tester les endpoints santé et query, voir les logs, copier/coller les réponses agents, et vérifier la connectivité des services.

***

## 🧪 Tester les endpoints

- **Santé du serveur orchestrateur :**
  ```bash
  curl http://localhost:8000/health
  ```
- **Requête d’agrégation agents :**
  ```bash
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What is data federation in distributed AI?"}'
  ```

***

## 🛠️ Résolution des problèmes fréquents

- **Erreur CORS / Failed to fetch :**  
  Vérifie que le `CORSMiddleware` est bien présent dans tous tes FastAPI ([voir fix-http-errors.md]).[1]

- **404 / 405 endpoints :**  
  Vérifie que `/health` et `/` existent bien dans ton `app.py`. Les requêtes OPTIONS (CORS preflight) doivent retourner 200.

- **Rebuild manuel si besoin :**
  ```bash
  docker compose build
  docker compose up --watch
  ```
***

## ⚠️ Points de vigilance

Pour l'instant, cet outil est en phase expérimentale. Voici quelques limitations à garder en tête :
- **Performance** : Le mode `watch` peut ralentir les performances globales. Utilise-le principalement en développement.
- **RAG basique** : L’orchestrateur RAG est un prototype simple. Pour des cas d’usage complexes, une architecture plus robuste est recommandée.
- **Sécurité** : Ne pas utiliser en production sans audits de sécurité approfondis.
- **Multi-user** : L’UI de debug n’est pas conçue pour un usage multi-utilisateurs simultané.
- **Logs volumineux** : Les logs en temps réel peuvent devenir volumineux. Pensez à les nettoyer régulièrement.
- **


***

## 📚 Ressources utiles

- Documentation Compose Watch (officiel)
- Exemple complet avec Watch et synchronisation

***

## ✨ Fonctionnalités principales

- Debug visuel en temps réel
- Orchestrateur multi-agents RAG
- Auto-rebuild/sync lors des modifications de code
- UI accessible sur localhost:3000
- Résilience aux erreurs agents

## Licence

MIT License © 2025 JLucGauvrit
