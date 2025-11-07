"""
Serveur MCP - Agent RAG
Expose un outil 'query_rag' via le protocole MCP
"""
import os
import asyncio
import logging
from typing import List, Dict, Any
import asyncpg
import google.generativeai as genai
from fastmcp import FastMCP
import httpx

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_ID = os.getenv('AGENT_ID', 'agent-1')
AGENT_NAME = os.getenv('AGENT_NAME', 'Agent 1')
AGENT_SPECIALTY = os.getenv('AGENT_SPECIALTY', 'general')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
MCP_PORT = int(os.getenv('MCP_PORT', 8001))

# PostgreSQL
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', 5432))
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
PG_DB = os.getenv('POSTGRES_DB', 'rag_db')

# Configuration Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Pool de connexions PostgreSQL
db_pool = None


async def init_db():
    """Initialise le pool de connexions PostgreSQL"""
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DB,
            min_size=1,
            max_size=5
        )
        logger.info(f"✅ Agent {AGENT_ID} connecté à PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Erreur connexion PostgreSQL: {e}")
        raise


async def generate_embedding(text: str) -> List[float]:
    """Génère un embedding avec Gemini"""
    try:
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        logger.warning(f"Embedding failed: {e}, using random")
        import numpy as np
        return np.random.rand(1536).tolist()


async def search_documents(query_embedding: List[float], limit: int = 3) -> List[Dict]:
    """Recherche vectorielle dans PostgreSQL"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT content, metadata,
                   1 - (embedding <=> $1::vector) as similarity
            FROM documents
            WHERE agent_id = $2 AND embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $3
            """,
            query_embedding,
            AGENT_ID,
            limit
        )
        return [dict(row) for row in rows]


async def generate_response_gemini(query: str, context: str) -> str:
    """Génère une réponse avec Gemini"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""Tu es un expert en {AGENT_SPECIALTY}.

Contexte disponible:
{context}

Question: {query}

Réponds de manière concise et précise en te basant sur le contexte."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return f"Erreur de génération: {str(e)}"


async def generate_response_perplexity(query: str, context: str) -> str:
    """Génère une réponse avec Perplexity"""
    if not PERPLEXITY_API_KEY:
        return "Perplexity API key not configured"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content": f"Contexte: {context}"},
                        {"role": "user", "content": query}
                    ]
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Perplexity error: {e}")
            return f"Erreur Perplexity: {str(e)}"


# ============================================
# SERVEUR MCP avec FastMCP
# ============================================

# Créer le serveur MCP
mcp = FastMCP(
    name=f"{AGENT_NAME} MCP Server",
    instructions=f"Agent RAG spécialisé en {AGENT_SPECIALTY}"
)


@mcp.tool()
async def query_rag(query: str) -> Dict[str, Any]:
    """
    Interroge le système RAG de cet agent.
    
    Args:
        query: La question à poser au système RAG
        
    Returns:
        Un dictionnaire contenant la réponse et les sources
    """
    logger.info(f"[{AGENT_ID}] Requête RAG: {query[:50]}...")
    
    try:
        # 1. Générer l'embedding
        query_embedding = await generate_embedding(query)
        
        # 2. Recherche vectorielle
        docs = await search_documents(query_embedding, limit=3)
        logger.info(f"[{AGENT_ID}] {len(docs)} documents trouvés")
        
        # 3. Construire le contexte
        context = "\n\n".join([
            f"[Source {i+1}] {doc['content']}"
            for i, doc in enumerate(docs)
        ])
        
        # 4. Générer la réponse
        if AGENT_SPECIALTY == "current_events" and PERPLEXITY_API_KEY:
            response_text = await generate_response_perplexity(query, context)
        else:
            response_text = await generate_response_gemini(query, context)
        
        # 5. Calculer confiance
        avg_similarity = sum(d.get('similarity', 0) for d in docs) / len(docs) if docs else 0
        confidence = min(0.95, max(0.3, avg_similarity))
        
        result = {
            "agent_id": AGENT_ID,
            "agent_name": AGENT_NAME,
            "response": response_text,
            "sources": [
                {
                    "content": doc['content'][:200],
                    "similarity": float(doc.get('similarity', 0)),
                    "metadata": doc.get('metadata', {})
                }
                for doc in docs
            ],
            "confidence": confidence,
            "specialty": AGENT_SPECIALTY
        }
        
        logger.info(f"[{AGENT_ID}] Réponse générée (confiance: {confidence:.2f})")
        return result
        
    except Exception as e:
        logger.error(f"[{AGENT_ID}] Erreur: {e}")
        return {
            "agent_id": AGENT_ID,
            "agent_name": AGENT_NAME,
            "response": f"Erreur: {str(e)}",
            "sources": [],
            "confidence": 0.0,
            "specialty": AGENT_SPECIALTY,
            "error": str(e)
        }


@mcp.tool()
async def get_agent_info() -> Dict[str, Any]:
    """
    Retourne les informations sur cet agent.
    
    Returns:
        Informations sur l'agent (ID, nom, spécialité, etc.)
    """
    async with db_pool.acquire() as conn:
        doc_count = await conn.fetchval(
            "SELECT COUNT(*) FROM documents WHERE agent_id = $1",
            AGENT_ID
        )
    
    return {
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "specialty": AGENT_SPECIALTY,
        "documents_indexed": doc_count,
        "status": "online"
    }


# ============================================
# DÉMARRAGE
# ============================================

async def startup():
    """Initialisation au démarrage"""
    logger.info(f"""
╔══════════════════════════════════════════╗
║  MCP Server: {AGENT_NAME:<26} ║
║  ID: {AGENT_ID:<34} ║
║  Specialty: {AGENT_SPECIALTY:<28} ║
║  Port: {MCP_PORT:<33} ║
╚══════════════════════════════════════════╝
    """)
    
    # Initialiser la base de données
    await init_db()
    
    logger.info(f"✅ Serveur MCP {AGENT_NAME} prêt sur le port {MCP_PORT}")


if __name__ == "__main__":
    # Lancer l'initialisation
    asyncio.run(startup())
    
    # Démarrer le serveur MCP avec transport SSE (HTTP)
    mcp.run(
        transport="sse",
        port=MCP_PORT,
        host="0.0.0.0"
    )
    