import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Importe le client adapté pour l'API
from orchestrator import mcp_adapter


class QueryRequest(BaseModel):
    query: str    

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le démarrage et l'arrêt des ressources (connexion MCP).
    """
    try:
        await mcp_adapter.connect_to_server("./mcp_server_rag.py")
        print("API FastAPI et Client MCP initialisés.")
        yield
    except Exception as e:
        print(f"Échec critique au démarrage: {e}")
        raise
    finally:
        await mcp_adapter.cleanup()
        print("API FastAPI et Client MCP arrêtés.")

app = FastAPI(
    title="Perplexity MCP Agent API",
    description="Endpoint pour interroger l'agent Perplexity Tool-Using (RAG Agent via MCP)",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/chat")
async def chat_endpoint(request: QueryRequest):

    if mcp_adapter.session is None:
        raise HTTPException(
            status_code=503, 
            detail="Service non disponible. La connexion au serveur MCP a échoué."
        )

    try:

        response_text = await mcp_adapter.process_query(request.query)
        
        return {
            "query": request.query,
            "response": response_text
        }
    except Exception as e:
        print(f"Erreur lors du traitement de la requête: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur lors du traitement LLM/MCP: {e}")

@app.get("/health")
def health_check():
    """Vérification simple de l'état de l'API."""
    status = "running" if mcp_adapter.session is not None else "initializing"
    return {"status": status}