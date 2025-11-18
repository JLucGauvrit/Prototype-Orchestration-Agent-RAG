import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import docker

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Orchestrator API",
    description="API pour la gestion des agents RAG",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines exactes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    client = docker.from_env()
    logger.info("Connexion Docker établie avec succès")
except Exception as e:
    logger.error(f"Erreur lors de la connexion à Docker: {e}")
    raise

@app.get("/")
def read_root():
    """Route racine pour vérifier que l'API est en ligne"""
    return JSONResponse({"status": "ok", "message": "Orchestrator API is running"})

@app.get("/agents")
def list_agents():
    containers = client.containers.list(filters={"name": "agent-rag"})
    return [c.name for c in containers]

@app.post("/agents")
def create_agent():
    try:
        # Trouver le prochain index disponible
        containers = client.containers.list(filters={"name": "agent-rag"})
        idx = len(containers) + 1
        name = f"agent-rag-{idx}"
        
        logger.info(f"Tentative de création de l'agent: {name}")
        
        # Créer le conteneur avec l'image prototypeprocom-agent-rag-template
        client.containers.run(
            "prototypeprocom-agent-rag-template",  # Nom corrigé de l'image
            name=name,
            network="prototypeprocom_backend",  # Nom complet du réseau
            detach=True,
            environment={
                "AGENT_ID": str(idx),
                "DATA_PATH": f"/app/data/agent_{idx}",
                "POSTGRES_URL": "postgresql://rag_user:rag_pass@postgres:5432/rag_db"
            },
            volumes={
                "prototypeprocom_rag_data": {"bind": "/app/data", "mode": "rw"}
            }
        )
        logger.info(f"Agent créé avec succès: {name}")
        return {"created": name}
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/agents/{name}")
def delete_agent(name: str):
    try:
        c = client.containers.get(name)
        c.stop()
        c.remove()
        return {"deleted": name}
    except docker.errors.NotFound:
        return {"error": "not found"}
