
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx, asyncio

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENTS = ["agent-a:5000", "agent-b:5000", "agent-c:5000"]

@app.get("/health")
async def health():
    return {"status": "healthy", "server": "mcp-orchestrator"}

@app.get("/")
async def root():
    return {"message": "MCP Orchestrator running", "agents": AGENTS}

@app.post("/query")
async def query(request: Request):
    """Agrège les réponses de tous les agents avec timeouts augmentés"""
    data = await request.json()
    query_text = data["query"]

    try:
        # 🔥 TIMEOUT AUGMENTÉ : 120 secondes pour permettre à Perplexity de répondre
        # Chaque appel peut prendre 30-60 secondes avec les retries de Perplexity
        async with httpx.AsyncClient(timeout=120.0) as client:
            tasks = [
                client.post(
                    f"http://{agent}/rag",
                    json={"query": query_text},
                    timeout=120.0  # 🔥 Important : timeout au niveau de la requête aussi
                )
                for agent in AGENTS
            ]

            # Attendre les réponses avec une limite de temps globale
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Traiter les réponses
        answers = []
        for i, resp in enumerate(responses):
            agent_name = AGENTS[i].split(":")[0] if i < len(AGENTS) else "Unknown"

            if isinstance(resp, asyncio.TimeoutError):
                answers.append({
                    "agent": agent_name,
                    "answer": "Error: Request timeout - Agent took too long to respond"
                })
            elif isinstance(resp, Exception):
                answers.append({
                    "agent": agent_name,
                    "answer": f"Error: {str(resp)}"
                })
            else:
                try:
                    json_resp = resp.json()
                    answers.append({
                        "agent": json_resp.get("agent", agent_name),
                        "answer": json_resp.get("answer", "No answer returned")
                    })
                except Exception as e:
                    answers.append({
                        "agent": agent_name,
                        "answer": f"Error parsing response: {str(e)}"
                    })

        # Agréger les réponses
        aggregated = "\n".join([
            f"{a.get('agent', 'Unknown')}: {a.get('answer', 'No answer')}"
            for a in answers
        ])

        return {
            "aggregated": aggregated,
            "agents_count": len(AGENTS),
            "responses_count": len(answers)
        }

    except Exception as e:
        return {
            "aggregated": f"Error in orchestrator: {str(e)}",
            "error": str(e)
        }

# Endpoint OPTIONS pour CORS preflight
@app.options("/{path_name:path}")
async def options_handler(path_name: str):
    return {}