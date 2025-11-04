# Cahier des Charges - Déploiement d'Agents LLM Décentralisés avec RAG Distribué

**Projet PROCOM - IMT**
**Partenaire Industrie**: Manta-Tech
**Durée**: Semestre académique 2024-2025

---

## 1. Contexte et Présentation de Manta

### 1.1 Vision Technologique

Manta est une plateforme d'orchestration d'IA périphérique (edge AI) qui révolutionne le déploiement de modèles d'apprentissage automatique sur des équipements distribués. Dans le contexte de ce projet étudiant, Manta offre un environnement pour expérimenter avec des architectures d'IA décentralisées où les données et les modèles restent au plus près de leur source.

### 1.2 Capacités Techniques Pertinentes

#### Orchestration Edge-Native

- **Déploiement distribué**: Gestion automatisée de modèles sur 100+ nœuds périphériques
- **Latence critique**: Communication inter-agents pour applications temps réel
- **Tolérance aux pannes**: Architecture résiliente avec failover automatique

#### Architecture Fédérée

- **Apprentissage fédéré**: Coordination d'entraînement sans centralisation des données
- **Consensus distribué**: Protocoles de synchronisation pour bases de connaissances partagées
- **Souveraineté des données**: Conformité RGPD native, données jamais centralisées

#### Interface Data Scientist

- **Abstraction de l'infrastructure**: Focus sur les algorithmes, pas sur le DevOps
- **API unifiée**: Déploiement seamless du prototype au production
- **Monitoring intégré**: Observabilité complète des systèmes multi-agents

### 1.3 Avantages pour les Systèmes RAG Multi-Agents

1. **Confidentialité by Design**: Chaque agent peut maintenir sa base de connaissances localement
2. **Scalabilité Horizontale**: Addition dynamique de nouveaux agents sans reconfiguration
3. **Robustesse**: Pas de point de défaillance unique (SPOF)
4. **Performance**: Réduction de la latence par proximité data-computation
5. **Compliance**: Respect automatique des réglementations de localisation des données

---

## 2. Spécifications du Projet

### 2.1 Objectifs Pédagogiques

#### Objectif Principal

Concevoir et implémenter un système d'agents LLM décentralisés capables de collaborer pour répondre à des requêtes complexes en utilisant des bases de connaissances distribuées via la technologie RAG (Retrieval-Augmented Generation).

#### Objectifs Secondaires

- Maîtriser les concepts d'IA fédéré appliqués aux LLM
- Expérimenter avec des architectures distribuées
- Explorer les défis de synchronisation dans les systèmes multi-agents
- Comprendre les enjeux de souveraineté et privacy des données

### 2.2 Livrables Attendus

#### 2.2.1 Livrables Techniques

1. **Architecture Système** (Semaine 4)
   - Diagrammes d'architecture multi-agents
   - Spécification des protocoles de communication
   - Design des bases de connaissances distribuées
   - Plan de déploiement sur infrastructure Manta

2. **Implémentation Fonctionnelle** (Semaine 10)
   - Code source complet avec documentation
   - Suite de tests unitaires et d'intégration
   - Configuration de déploiement Manta

3. **Démonstration** (Semaine 12)
   - Prototype fonctionnel sur au moins 3 nœuds
   - Interface utilisateur pour interaction avec le système
   - Métriques de performance et benchmarks
   - Cas d'usage représentatifs

#### 2.2.2 Livrables Académiques

1. **État de l'Art** (Semaine 6)
   - Revue critique de la littérature
   - Positionnement des approches existantes
   - Identification des gaps et opportunités d'innovation

2. **Rapport Technique Final** (Semaine 14)
   - Methodology et design choices
   - Évaluation expérimentale approfondie
   - Discussion des limitations et perspectives
   - Contribution à la communauté open-source

3. **Article de Recherche** (Bonus)
   - Soumission à workshop ou conférence étudiante
   - Format IEEE ou ACM selon le venue choisi

### 2.3 Contraintes Techniques

#### 2.3.1 Contraintes Logicielles

- **Compatibilité Manta**: Utilisation obligatoire de l'API Manta pour l'orchestration
- **Models LLM**: Modèles ouverts uniquement (Llama 2/3, Mistral, Gemma)
- **Frameworks**: Python 3.9+, transformers, langchain/llamaindex recommandés
- **Bases vectorielles**: FAISS, Chroma, ou Qdrant pour l'embedding storage

#### 2.3.2 Contraintes de Performance

- **Latence maximale**: Réponse système <5 secondes pour requêtes simples
- **Throughput**: Support de 10 requêtes concurrentes minimum
- **Accuracy**: Score F1 >0.7 sur dataset de référence fourni

---

## 3. Architectures Suggérées

### 3.1 Architecture Hiérarchique (Recommandée pour Débutants)

```
Coordinateur Central
├── Agent Spécialisé A (Domaine Technique)
├── Agent Spécialisé B (Domaine Business)
└── Agent Spécialisé C (Domaine Réglementaire)
```

**Avantages**: Simplicité de coordination, debugging facilité
**Inconvénients**: Point de défaillance unique, scalabilité limitée

### 3.2 Architecture P2P avec Consensus (Niveau Avancé)

```
Agent A ←→ Agent B
    ↑         ↓
Agent D ←→ Agent C
```

**Avantages**: Résilience maximale, scalabilité native
**Inconvénients**: Complexité de consensus, debugging difficile

### 3.3 Architecture Hybride (Innovation Encouragée)

Combinaison des approches précédentes avec des mécanismes adaptatifs selon la charge et la disponibilité des nœuds.

---

## 4. Cas d'Usage Possibles

### 4.1 Assistant Juridique Distribué

- **Contexte**: Cabinet d'avocats multi-sites
- **Agents**: Droit commercial, droit social, jurisprudence, veille réglementaire
- **Bases de connaissances**: Codes juridiques, jurisprudences locales, contrats types
- **Défi**: Synchronisation des évolutions réglementaires

### 4.2 Support Technique Industriel

- **Contexte**: Maintenance d'équipements industriels distribués
- **Agents**: Diagnostic, documentation technique, historique pannes, pièces détachées
- **Bases de connaissances**: Manuels techniques, logs d'incidents, catalogues
- **Défi**: Corrélation d'incidents multi-sites

### 4.3 Recherche Académique Collaborative

- **Contexte**: Consortium de laboratoires de recherche
- **Agents**: Publications, datasets, expertises, financements
- **Bases de connaissances**: Articles, data catalogs, profiles chercheurs
- **Défi**: Découverte de collaborations et recommandations

### 4.4 Intelligence Économique

- **Contexte**: Veille concurrentielle multi-sectorielle
- **Agents**: Analyse financière, brevets, presse, réseaux sociaux
- **Bases de connaissances**: Rapports, patents, news feed, données marché
- **Défi**: Fusion d'informations hétérogènes et détection de signaux faibles

---

## 5. Références Académiques

### 5.1 Multi-Agent Systems & LLM

**AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation** (2023)
*Wu, Q. et al. - Microsoft Research*
[arXiv:2308.08155](https://arxiv.org/abs/2308.08155)
> Framework fondamental pour les conversations multi-agents avec LLM, référence pour l'orchestration.

**Multi-Agent Collaboration: Harnessing the Power of Intelligent LLM Agents** (2024)
*Chen, W. et al. - AAAI 2024*
[arXiv:2402.01680](https://arxiv.org/abs/2402.01680)
> État de l'art sur la collaboration entre agents LLM, taxonomie des architectures.

**Communicative Agents for Software Development** (2023)
*Qian, C. et al. - ICML 2023*
[arXiv:2307.07924](https://arxiv.org/abs/2307.07924)
> Étude de cas détaillée sur la coordination d'agents spécialisés.

### 5.2 Retrieval-Augmented Generation

**Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks** (2020)
*Lewis, P. et al. - NeurIPS 2020*
[arXiv:2005.11401](https://arxiv.org/abs/2005.11401)
> Papier fondateur du RAG, concepts de base indispensables.

**Dense Passage Retrieval for Open-Domain Question Answering** (2020)
*Karpukhin, V. et al. - EMNLP 2020*
[arXiv:2004.04906](https://arxiv.org/abs/2004.04906)
> Techniques de retrieval dense, optimisation des embeddings.

**FiD: Fusion-in-Decoder for Open-Domain Question Answering** (2021)
*Izacard, G. & Grave, E. - ICML 2021*
[arXiv:2007.01282](https://arxiv.org/abs/2007.01282)
> Fusion d'informations multiples dans les architectures RAG.

### 5.3 Federated Learning & Distributed AI

**Towards Federated Learning at Scale: System Design** (2019)
*Bonawitz, K. et al. - SysML 2019*
[arXiv:1902.01046](https://arxiv.org/abs/1902.01046)
> Architecture système pour FL à grande échelle, considérations pratiques.

**FedAvg: Communication-Efficient Learning of Deep Networks from Decentralized Data** (2017)
*McMahan, B. et al. - AISTATS 2017*
[arXiv:1602.05629](https://arxiv.org/abs/1602.05629)
> Algorithme de référence pour l'apprentissage fédéré.

**Flower: A Friendly Federated Learning Framework** (2021)
*Beutel, D.J. et al. - ICML 2021 Workshop*
[arXiv:2007.14390](https://arxiv.org/abs/2007.14390)
> Framework open-source, comparaison avec l'approche Manta recommandée.

### 5.4 Edge AI & Distributed Systems

**Edge Intelligence: Paving the Last Mile of Artificial Intelligence with Edge Computing** (2019)
*Zhou, Z. et al. - Proceedings of IEEE*
[arXiv:1905.10083](https://arxiv.org/abs/1905.10083)
> Vision d'ensemble de l'IA périphérique, contexte industriel.

**Federated Learning for Mobile Edge Computing: A Comprehensive Survey** (2020)
*Lim, W.Y.B. et al. - IEEE Communications Surveys & Tutorials*
[IEEE Xplore](https://ieeexplore.ieee.org/document/8972913)
> Survey complet FL + Edge, défis techniques.

### 5.5 Modèles de Référence

**Gemma: Open Models Based on Gemini Research and Technology** (2024)
*Google DeepMind Team - arXiv:2403.08295*
[arXiv:2403.08295](https://arxiv.org/abs/2403.08295)
> Famille de modèles ouverts optimisés pour l'efficacité, excellent pour edge deployment.

**Llama 2: Open Foundation and Fine-Tuned Chat Models** (2023)
*Touvron, H. et al. - arXiv:2307.09288*
[arXiv:2307.09288](https://arxiv.org/abs/2307.09288)
> Référence pour les modèles ouverts, techniques de fine-tuning.

**Mistral 7B** (2023)
*Jiang, A.Q. et al. - arXiv:2310.06825*
[arXiv:2310.06825](https://arxiv.org/abs/2310.06825)
> Modèle compact haute performance, idéal pour contraintes edge.

---

**Contact**:
Hugo Miralles - CEO Manta-Tech
<hugomiralles@manta-tech.io> | LinkedIn: /in/hugomiralles

**Dernière mise à jour**: Septembre 2025
