"""
Agent RAG générique avec client MCP
Peut être configuré pour différentes spécialités
"""
import os
import sys
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
import google.generativeai as genai

sys.path.append('/app/shared')
from models import MCPResponse, AgentSpecialty
from database import Database


# Configuration depuis les variables d'environnement
AGENT_ID = os.getenv('AGENT_ID', 'agent-unknown')
AGENT_NAME = os.getenv('AGENT_NAME', 'Unknown Agent')
AGENT_SPECIALTY = os.getenv('AGENT_SPECIALTY', 'general_knowledge')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
ORCHESTRATOR_HOST = os.getenv('ORCHESTRATOR_HOST', 'orchestrator')
MCP_SERVER_PORT = int(os.getenv('MCP_SERVER_PORT', 8001))

# Configuration Gemini si la clé est disponible
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    gemini_embedding = genai.GenerativeModel('models/embedding-001')
else:
    gemini_model = None
    gemini_embedding = None

# Base de données
db = Database()

# État de démarrage
start_time = datetime.utcnow()


class QueryRequest(BaseModel):
    """Requête de l'orchestrateur"""
    request_id: str
    query: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'agent"""
    print(f"🤖 Démarrage de {AGENT_NAME} ({AGENT_ID})")
    
    # Connexion à la BDD
    await db.connect()
    
    # Enregistrement auprès de l'orchestrateur
    await register_with_orchestrator()
    
    # Démarrer le heartbeat
    asyncio.create_task(heartbeat_loop())
    
    yield
    
    print(f"🛑 Arrêt de {AGENT_NAME}")
    await db.disconnect()


app = FastAPI(
    title=f"RAG Agent - {AGENT_NAME}",
    description=f"Agent RAG spécialisé: {AGENT_SPECIALTY}",
    version="1.0.0",
    lifespan=lifespan
)


async def register_with_orchestrator():
    """S'enregistre auprès de l'orchestrateur MCP"""
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            # L'endpoint de l'agent est accessible via le réseau Docker
            agent_endpoint = f"http://{AGENT_ID}:8080"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Pour l'instant, on utilise HTTP direct
                # Dans une vraie implémentation MCP, on utiliserait le protocole MCP
                response = await client.post(
                    f"http://{ORCHESTRATOR_HOST}:8000/api/register_agent",
                    json={
                        "agent_id": AGENT_ID,
                        "agent_name": AGENT_NAME,
                        "specialty": AGENT_SPECIALTY,
                        "endpoint": agent_endpoint
                    }
                )
                
                if response.status_code == 200:
                    print(f"✅ Enregistré auprès de l'orchestrateur")
                    return
                    
        except Exception as e:
            print(f"⚠️ Tentative {attempt + 1}/{max_retries} d'enregistrement échouée: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
    
    print(f"❌ Impossible de s'enregistrer après {max_retries} tentatives")


async def heartbeat_loop():
    """Envoie périodiquement un heartbeat à l'orchestrateur"""
    while True:
        await asyncio.sleep(30)  # Heartbeat toutes les 30 secondes
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"http://{ORCHESTRATOR_HOST}:8000/api/agent_heartbeat",
                    json={"agent_id": AGENT_ID}
                )
        except Exception as e:
            print(f"⚠️ Heartbeat échoué: {e}")


@app.post("/query", response_model=MCPResponse)
async def process_query(request: QueryRequest):
    """
    Traite une requête RAG
    1. Génère l'embedding de la requête
    2. Recherche dans la base vectorielle
    3. Génère la réponse avec le LLM
    """
    start_time_local = time.time()
    
    print(f"\n📨 Requête reçue: {request.query[:50]}...")
    
    try:
        # 1. Générer l'embedding de la requête
        query_embedding = await generate_embedding(request.query)
        
        # 2. Recherche vectorielle dans la BDD
        relevant_docs = await db.search_documents(
            agent_id=AGENT_ID,
            query_embedding=query_embedding,
            limit=5
        )
        
        print(f"  📚 {len(relevant_docs)} documents trouvés")
        
        # 3. Construire le contexte
        context = "\n\n".join([
            f"[Source {i+1}] {doc['content']}"
            for i, doc in enumerate(relevant_docs)
        ])
        
        # 4. Générer la réponse avec le LLM
        response_text = await generate_response(request.query, context)
        
        # 5. Calculer le temps de traitement
        processing_time_ms = int((time.time() - start_time_local) * 1000)
        
        # 6. Préparer la réponse MCP
        mcp_response = MCPResponse(
            request_id=request.request_id,
            agent_id=AGENT_ID,
            agent_name=AGENT_NAME,
            response=response_text,
            sources=[
                {
                    "content": doc['content'][:200],
                    "similarity": float(doc.get('similarity', 0)),
                    "metadata": doc.get('metadata', {})
                }
                for doc in relevant_docs
            ],
            confidence=calculate_confidence(relevant_docs),
            processing_time_ms=processing_time_ms,
            metadata={
                "specialty": AGENT_SPECIALTY,
                "documents_found": len(relevant_docs)
            }
        )
        
        print(f"  ✅ Réponse générée en {processing_time_ms}ms")
        
        return mcp_response
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_embedding(text: str) -> List[float]:
    """Génère l'embedding d'un texte avec Gemini"""
    if not gemini_embedding:
        # Fallback: embedding aléatoire pour le développement
        import numpy as np
        return np.random.rand(1536).tolist()
    
    try:
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        print(f"⚠️ Erreur génération embedding: {e}")
        # Fallback
        import numpy as np
        return np.random.rand(1536).tolist()


async def generate_response(query: str, context: str) -> str:
    """Génère une réponse avec le LLM"""
    
    # Adapter le prompt selon la spécialité
    specialty_prompts = {
        "general_knowledge": "Tu es un expert en connaissances générales. Réponds de manière précise et pédagogique.",
        "current_events": "Tu es un expert en actualités et événements récents. Fournis des informations à jour et contextualisées.",
        "data_analysis": "Tu es un expert en analyse de données. Fournis des insights analytiques et des interprétations basées sur les données.",
        "technical": "Tu es un expert technique. Fournis des réponses détaillées et techniques."
    }
    
    system_prompt = specialty_prompts.get(AGENT_SPECIALTY, specialty_prompts["general_knowledge"])
    
    prompt = f"""{system_prompt}

Contexte disponible:
{context}

Question: {query}

Réponds à la question en te basant sur le contexte fourni. Si le contexte ne contient pas l'information, indique-le clairement."""
    
    # Utiliser Gemini si disponible
    if gemini_model and AGENT_SPECIALTY != "current_events":
        try:
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️ Erreur Gemini: {e}")
    
    # Utiliser Perplexity pour les actualités
    if PERPLEXITY_API_KEY and AGENT_SPECIALTY == "current_events":
        try:
            return await query_perplexity(query, context)
        except Exception as e:
            print(f"⚠️ Erreur Perplexity: {e}")
    
    # Fallback: réponse basique
    return f"Basé sur le contexte disponible:\n\n{context[:500]}...\n\n[Note: LLM non disponible, réponse tronquée]"


async def query_perplexity(query: str, context: str) -> str:
    """Interroge l'API Perplexity"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": f"Contexte: {context}"
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            },
            timeout=30.0
        )
        
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']


def calculate_confidence(documents: List[Dict[str, Any]]) -> float:
    """Calcule un score de confiance basé sur la similarité des documents"""
    if not documents:
        return 0.3
    
    similarities = [doc.get('similarity', 0) for doc in documents]
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0
    
    # Normaliser entre 0.3 et 0.95
    return min(0.95, max(0.3, avg_similarity))


@app.get("/health")
async def health_check():
    """Health check de l'agent"""
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    # Compter les documents indexés
    async with db.pool.acquire() as conn:
        doc_count = await conn.fetchval(
            "SELECT COUNT(*) FROM documents WHERE agent_id = $1",
            AGENT_ID
        )
    
    return {
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "specialty": AGENT_SPECIALTY,
        "status": "online",
        "uptime_seconds": int(uptime),
        "documents_indexed": doc_count,
        "llm_available": gemini_model is not None or PERPLEXITY_API_KEY is not None
    }


@app.post("/ingest")
async def ingest_document(document: Dict[str, Any]):
    """Ingère un nouveau document dans la base RAG"""
    try:
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        # Générer l'embedding
        embedding = await generate_embedding(content)
        
        # Insérer dans la BDD
        doc_id = await db.insert_document(
            agent_id=AGENT_ID,
            content=content,
            metadata=metadata,
            embedding=embedding
        )
        
        return {
            "status": "success",
            "document_id": doc_id,
            "agent_id": AGENT_ID
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║   RAG Agent: {AGENT_NAME:<43} ║
    ║   Specialty: {AGENT_SPECIALTY:<42} ║
    ║   ID: {AGENT_ID:<50} ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
