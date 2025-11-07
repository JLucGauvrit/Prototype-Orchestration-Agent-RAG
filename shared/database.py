"""
Gestion de la base de données PostgreSQL avec pgvector
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
from pgvector.asyncpg import register_vector


class Database:
    """Gestionnaire de connexion et requêtes PostgreSQL"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = int(os.getenv('POSTGRES_PORT', 5432))
        self.user = os.getenv('POSTGRES_USER', 'postgres')
        self.password = os.getenv('POSTGRES_PASSWORD', 'postgres_password')
        self.database = os.getenv('POSTGRES_DB', 'rag_db')
    
    async def connect(self):
        """Établit la connexion au pool PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=2,
                max_size=10
            )
            
            # Enregistrer le type pgvector
            async with self.pool.acquire() as conn:
                await register_vector(conn)
            
            print(f"✅ Connecté à PostgreSQL: {self.host}:{self.port}/{self.database}")
        except Exception as e:
            print(f"❌ Erreur de connexion PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Ferme le pool de connexions"""
        if self.pool:
            await self.pool.close()
            print("🔌 Déconnecté de PostgreSQL")
    
    async def log_mcp_request(
        self,
        request_id: str,
        user_query: str,
        orchestrator_response: str,
        agents_involved: List[str],
        processing_time_ms: int,
        status: str
    ):
        """Enregistre une requête MCP dans les logs"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO mcp_logs 
                (request_id, user_query, orchestrator_response, agents_involved, processing_time_ms, status)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                request_id,
                user_query,
                orchestrator_response,
                agents_involved,
                processing_time_ms,
                status
            )
    
    async def update_agent_status(
        self,
        agent_id: str,
        status: str,
        agent_name: str = None,
        specialty: str = None
    ):
        """Met à jour le statut d'un agent"""
        async with self.pool.acquire() as conn:
            if agent_name and specialty:
                await conn.execute(
                    """
                    INSERT INTO agent_status (agent_id, agent_name, specialty, status, last_heartbeat)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (agent_id) 
                    DO UPDATE SET 
                        status = $4,
                        last_heartbeat = NOW()
                    """,
                    agent_id, agent_name, specialty, status
                )
            else:
                await conn.execute(
                    """
                    UPDATE agent_status 
                    SET status = $2, last_heartbeat = NOW()
                    WHERE agent_id = $1
                    """,
                    agent_id, status
                )
    
    async def update_agent_stats(
        self,
        agent_id: str,
        response_time_ms: int
    ):
        """Met à jour les statistiques d'un agent"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE agent_status
                SET 
                    total_queries = total_queries + 1,
                    avg_response_time_ms = (
                        (avg_response_time_ms * total_queries + $2) / (total_queries + 1)
                    )::INTEGER
                WHERE agent_id = $1
                """,
                agent_id, response_time_ms
            )
    
    async def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les logs récents"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM mcp_logs
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]
    
    async def search_documents(
        self,
        agent_id: str,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Recherche vectorielle dans les documents d'un agent"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, content, metadata, 
                       1 - (embedding <=> $2::vector) as similarity
                FROM documents
                WHERE agent_id = $1 AND embedding IS NOT NULL
                ORDER BY embedding <=> $2::vector
                LIMIT $3
                """,
                agent_id,
                query_embedding,
                limit
            )
            return [dict(row) for row in rows]
    
    async def insert_document(
        self,
        agent_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> int:
        """Insère un nouveau document"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO documents (agent_id, content, metadata, embedding)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                agent_id,
                content,
                metadata,
                embedding
            )
            return row['id']
