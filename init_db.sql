-- Initialisation de la base de données pour le RAG multi-agents
-- Active pgvector et crée les tables nécessaires

-- Activer l'extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Table pour les documents indexés par agent
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),  -- Dimension pour Gemini embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour la recherche vectorielle
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index pour filtrer par agent
CREATE INDEX IF NOT EXISTS documents_agent_idx ON documents(agent_id);

-- Table pour les logs des requêtes MCP
CREATE TABLE IF NOT EXISTS mcp_logs (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(100) UNIQUE NOT NULL,
    user_query TEXT NOT NULL,
    orchestrator_response TEXT,
    agents_involved JSONB,
    processing_time_ms INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour le suivi des agents
CREATE TABLE IF NOT EXISTS agent_status (
    agent_id VARCHAR(50) PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100),
    status VARCHAR(50) DEFAULT 'offline',
    last_heartbeat TIMESTAMP,
    total_queries INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER DEFAULT 0
);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour updated_at
CREATE TRIGGER update_documents_updated_at 
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Insertion de données de test pour chaque agent
INSERT INTO agent_status (agent_id, agent_name, specialty, status) VALUES
('agent-1', 'Gemini General', 'general_knowledge', 'offline'),
('agent-2', 'Perplexity Current', 'current_events', 'offline'),
('agent-3', 'Gemini Analysis', 'data_analysis', 'offline')
ON CONFLICT (agent_id) DO NOTHING;

-- Documents de test pour agent-1 (Gemini General)
INSERT INTO documents (agent_id, content, metadata) VALUES
('agent-1', 'Artificial intelligence refers to the simulation of human intelligence in machines.', 
 '{"source": "knowledge_base", "topic": "AI basics"}'),
('agent-1', 'Machine learning is a subset of AI that enables systems to learn from data.', 
 '{"source": "knowledge_base", "topic": "ML basics"}'),
('agent-1', 'Data federation in distributed AI refers to the technique of training models across decentralized data sources.', 
 '{"source": "knowledge_base", "topic": "distributed AI"}')
ON CONFLICT DO NOTHING;

-- Documents de test pour agent-2 (Perplexity Current Events)
INSERT INTO documents (agent_id, content, metadata) VALUES
('agent-2', 'Latest developments in AI include multimodal models and improved reasoning capabilities.', 
 '{"source": "news", "date": "2025-11"}'),
('agent-2', 'Edge AI deployment is gaining traction for real-time processing applications.', 
 '{"source": "news", "date": "2025-11"}')
ON CONFLICT DO NOTHING;

-- Documents de test pour agent-3 (Gemini Analysis)
INSERT INTO documents (agent_id, content, metadata) VALUES
('agent-3', 'Statistical analysis of distributed systems shows improved performance with proper load balancing.', 
 '{"source": "research", "topic": "systems analysis"}'),
('agent-3', 'Performance metrics for multi-agent systems include latency, throughput, and resource utilization.', 
 '{"source": "research", "topic": "performance"}')
ON CONFLICT DO NOTHING;
