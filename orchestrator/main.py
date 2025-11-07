"""
Orchestrateur - FastAPI + MCP Client
Interface web unique + Communication MCP avec les agents
"""
import os
import asyncio
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from fastmcp import Client

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
AGENT1_URL = os.getenv('AGENT1_URL', 'http://agent-1:8001')
AGENT2_URL = os.getenv('AGENT2_URL', 'http://agent-2:8002')
AGENT3_URL = os.getenv('AGENT3_URL', 'http://agent-3:8003')

# Configuration Gemini pour la synthèse
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

# FastAPI
app = FastAPI(title="RAG Multi-Agent Orchestrator")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserQuery(BaseModel):
    query: str


class AgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    response: str
    sources: List[Dict]
    confidence: float
    specialty: str


class OrchestratedResponse(BaseModel):
    original_query: str
    synthesized_response: str
    agent_responses: List[AgentResponse]


# ============================================
# MCP CLIENT - Communication avec les agents
# ============================================

async def query_agent_via_mcp(agent_url: str, query: str) -> Dict[str, Any]:
    """
    Interroge un agent via MCP Client
    
    Args:
        agent_url: URL du serveur MCP (ex: http://agent-1:8001)
        query: Question à poser
        
    Returns:
        Réponse de l'agent
    """
    try:
        logger.info(f"🔗 Connexion MCP à {agent_url}")
        
        # Créer le client MCP avec l'URL SSE
        mcp_url = f"{agent_url}/sse"
        
        async with Client(mcp_url) as client:
            # Appeler l'outil 'query_rag' exposé par le serveur MCP
            result = await client.call_tool(
                "query_rag",
                arguments={"query": query}
            )
            
            # Extraire la réponse (format MCP)
            if result.content and len(result.content) > 0:
                # Le contenu est dans result.content[0].text
                import json
                response_data = json.loads(result.content[0].text)
                logger.info(f"✅ Réponse reçue de {response_data.get('agent_name')}")
                return response_data
            else:
                logger.warning(f"⚠️ Réponse vide de {agent_url}")
                return {
                    "agent_id": "unknown",
                    "agent_name": "Unknown",
                    "response": "Pas de réponse",
                    "sources": [],
                    "confidence": 0.0,
                    "specialty": "unknown"
                }
                
    except Exception as e:
        logger.error(f"❌ Erreur MCP avec {agent_url}: {e}")
        return {
            "agent_id": "error",
            "agent_name": "Error",
            "response": f"Erreur de communication: {str(e)}",
            "sources": [],
            "confidence": 0.0,
            "specialty": "error",
            "error": str(e)
        }


async def query_all_agents(query: str) -> List[AgentResponse]:
    """
    Interroge tous les agents en parallèle via MCP
    
    Args:
        query: Question à poser
        
    Returns:
        Liste des réponses des agents
    """
    logger.info(f"📡 Distribution de la requête aux 3 agents MCP")
    
    # Lancer les requêtes en parallèle
    tasks = [
        query_agent_via_mcp(AGENT1_URL, query),
        query_agent_via_mcp(AGENT2_URL, query),
        query_agent_via_mcp(AGENT3_URL, query),
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convertir en AgentResponse
    agent_responses = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Exception: {result}")
            continue
        
        agent_responses.append(AgentResponse(**result))
    
    logger.info(f"✅ {len(agent_responses)} réponses reçues")
    return agent_responses


def synthesize_responses(query: str, responses: List[AgentResponse]) -> str:
    """
    Synthétise les réponses des agents avec Gemini
    
    Args:
        query: Question originale
        responses: Réponses des agents
        
    Returns:
        Réponse synthétisée
    """
    if not gemini_model:
        # Fallback sans Gemini
        return "\n\n".join([
            f"**{r.agent_name}** ({r.specialty}):\n{r.response}"
            for r in responses
        ])
    
    # Construire le contexte
    context = "\n\n".join([
        f"**{r.agent_name}** (spécialité: {r.specialty}, confiance: {r.confidence:.0%}):\n{r.response}"
        for r in responses
    ])
    
    prompt = f"""Tu es un assistant qui synthétise les réponses de plusieurs agents d'IA spécialisés.

Question originale: {query}

Réponses des agents spécialisés:
{context}

Synthétise ces réponses en une réponse complète et cohérente. Combine les informations pertinentes.
Si les agents se complètent, intègre leurs réponses. Si ils se contredisent, mentionne les différentes perspectives.
Sois concis mais complet."""
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Erreur synthèse Gemini: {e}")
        # Fallback
        return context


# ============================================
# API ENDPOINTS
# ============================================


@app.post("/api/query", response_model=OrchestratedResponse)
async def process_query(user_query: UserQuery):
    """
    Point d'entrée principal - Interroge les agents via MCP et synthétise
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"📥 Nouvelle requête: {user_query.query}")
    
    try:
        # 1. Interroger tous les agents via MCP
        agent_responses = await query_all_agents(user_query.query)
        
        if not agent_responses:
            raise HTTPException(
                status_code=503,
                detail="Aucun agent n'a pu répondre"
            )
        
        # 2. Synthétiser les réponses
        synthesized = synthesize_responses(user_query.query, agent_responses)
        
        # 3. Retourner la réponse orchestrée
        result = OrchestratedResponse(
            original_query=user_query.query,
            synthesized_response=synthesized,
            agent_responses=agent_responses
        )
        
        logger.info(f"✅ Requête complétée avec {len(agent_responses)} réponses")
        logger.info(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "orchestrator": "online",
        "mcp_client": "enabled"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("""
╔══════════════════════════════════════════════════════════╗
║   RAG Multi-Agent Orchestrator with MCP                 ║
║   FastAPI + MCP Client + Interface Web unique           ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    