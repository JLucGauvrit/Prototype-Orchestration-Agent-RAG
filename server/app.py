from fastapi import FastAPI, Request
import httpx, asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
AGENTS = ["agent-a:5000", "agent-b:5000", "agent-c:5000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # ✅ Ceci gère OPTIONS automatiquement
    allow_headers=["*"],
)

# ✅ AJOUT : Endpoint manquant
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Server running"}

# Amélioration : Gestion d'erreurs
@app.post("/query")
async def query(request: Request):
    data = await request.json()
    query = data["query"]

    async with httpx.AsyncClient() as client:
        tasks = [client.post(f"http://{agent}/rag", json={"query": query}) for agent in AGENTS]
        responses = await asyncio.gather(*tasks)

    answers = [r.json() for r in responses]
    aggregated = "\n".join([f"{a['agent']}: {a['answer']}" for a in answers])
    return {"aggregated": aggregated}
