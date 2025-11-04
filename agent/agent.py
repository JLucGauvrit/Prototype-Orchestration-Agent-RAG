from fastapi import FastAPI, Request
import os, chromadb, requests

app = FastAPI()
AGENT_NAME = os.getenv("AGENT_NAME", "AgentX")
API_KEY = os.getenv("PERPLEXITY_API_KEY")

# --- Initialisation de la base locale ---
client = chromadb.Client()
collection = client.get_or_create_collection(name="local_docs")

# Exemple de documents locaux
collection.add(
    documents=[
        "Data federation allows distributed databases to work together seamlessly.",
        "Federated learning trains models without centralizing data.",
        "Regulatory compliance ensures data sovereignty and privacy."
    ],
    ids=["1", "2", "3"]
)

# --- Fonction pour requêter Perplexity ---
def ask_perplexity(prompt):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3-sonar-small-online",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 128
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    return f"Error: {resp.text}"

@app.post("/rag")
async def rag(request: Request):
    data = await request.json()
    query = data["query"]

    # Étape 1 : recherche locale
    results = collection.query(query_texts=[query], n_results=2)
    retrieved = " ".join(results["documents"][0])

    # Étape 2 : génération via Perplexity
    combined_prompt = f"Context: {retrieved}\nQuestion: {query}"
    answer = ask_perplexity(combined_prompt)

    return {"agent": AGENT_NAME, "answer": answer}
