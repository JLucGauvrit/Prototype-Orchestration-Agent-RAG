
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os, chromadb, requests

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_NAME = os.getenv("AGENT_NAME", "AgentX")
API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Initialisation ChromaDB
client = chromadb.Client()
collection = client.get_or_create_collection(name="local_docs")

collection.add(
    documents=[
        "Data federation allows distributed databases to work together seamlessly.",
        "Federated learning trains models without centralizing data.",
        "Regulatory compliance ensures data sovereignty and privacy."
    ],
    ids=["1", "2", "3"]
)

def ask_perplexity(prompt):
    """Interroge Perplexity avec timeout augmenté"""
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 128
    }

    try:
        # 🔥 Timeout augmenté à 60 secondes pour Perplexity
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60.0  # Perplexity peut prendre du temps
        )

        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return f"API Error ({resp.status_code}): {resp.text[:200]}"

    except requests.Timeout:
        return "Error: Perplexity API timeout (took longer than 60s)"
    except requests.ConnectionError as e:
        return f"Error: Connection to Perplexity failed: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.post("/rag")
async def rag(request: Request):
    """Endpoint RAG : recherche locale + enrichissement Perplexity"""
    data = await request.json()
    query_text = data["query"]

    try:
        # Étape 1 : Recherche locale dans ChromaDB
        results = collection.query(query_texts=[query_text], n_results=2)
        retrieved = " ".join(results["documents"][0])

        # Étape 2 : Enrichissement via Perplexity
        combined_prompt = f"Context: {retrieved}\nQuestion: {query_text}"
        answer = ask_perplexity(combined_prompt)

        return {
            "agent": AGENT_NAME,
            "answer": answer,
            "context": retrieved[:100] + "..."  # Pour debug
        }

    except Exception as e:
        return {
            "agent": AGENT_NAME,
            "answer": f"Internal error: {str(e)}",
            "error": str(e)
        }

@app.get("/")
async def root():
    return {"agent": AGENT_NAME, "status": "running"}

@app.get("/health")
async def health():
    return {"agent": AGENT_NAME, "status": "healthy"}

@app.options("/{path_name:path}")
async def options_handler(path_name: str):
    return {}