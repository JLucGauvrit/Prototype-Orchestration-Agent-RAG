"""
Agent RAG simple avec fichiers texte et vectorisation
"""
from fastapi import FastAPI
from pydantic import BaseModel
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict

app = FastAPI()


AGENT_ID = os.getenv("AGENT_ID", "agent-1")
DATA_PATH = os.getenv("DATA_PATH", "/app/data")

documents = []
embeddings = None


class QueryRequest(BaseModel):
    query: str


def load_model():
    """Charge le modèle d'embedding"""
    global model
    print(f" Chargement du modèle d'embedding...")
    model = SentenceTransformer('all-MiniLM-L6-v2') 
    print(f" Modèle chargé")


def load_documents():
    """Charge les documents depuis le fichier texte"""
    global documents, embeddings

    file_path = f"{DATA_PATH}/knowledge.txt"

    if not os.path.exists(file_path):
        print(f" Fichier {file_path} introuvable, création d'un fichier par défaut")
        os.makedirs(DATA_PATH, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("Ceci est un document de test.\nIl contient des informations de base.")
        documents = ["Ceci est un document de test.", "Il contient des informations de base."]
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            documents = [line.strip() for line in content.split('\n') if line.strip()]

    print(f" {len(documents)} documents chargés depuis {file_path}")

    if documents and model:
        print(f" Vectorisation des documents...")
        embeddings = model.encode(documents, convert_to_numpy=True)
        print(f" Documents vectorisés: {embeddings.shape}")


def cosine_similarity(a, b):
    """Calcule la similarité cosine entre deux vecteurs"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def search(query: str, top_k: int = 3) -> List[Dict]:
    """Recherche les documents les plus similaires à la requête"""
    if not documents or embeddings is None:
        return []

    query_embedding = model.encode([query], convert_to_numpy=True)[0]

    similarities = []
    for i, doc_embedding in enumerate(embeddings):
        sim = cosine_similarity(query_embedding, doc_embedding)
        similarities.append({
            "text": documents[i],
            "score": float(sim),
            "index": i
        })

    similarities.sort(key=lambda x: x["score"], reverse=True)

    return similarities[:top_k]


@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    print(f" Démarrage de l'agent RAG: {AGENT_ID}")
    load_model()
    load_documents()


@app.get("/health")
def health():
    """Health check"""
    return {
        "status": "ok",
        "agent_id": AGENT_ID,
        "documents_count": len(documents)
    }


@app.post("/query")
def query(request: QueryRequest):
    """Endpoint de requête RAG"""
    print(f" Requête: {request.query}")

    results = search(request.query, top_k=3)

    if not results:
        return {
            "agent_id": AGENT_ID,
            "query": request.query,
            "answer": "Aucun document trouvé dans la base de connaissances."
        }

    answer_parts = [f"Voici ce que j'ai trouvé (Agent {AGENT_ID}):\n"]
    for i, result in enumerate(results, 1):
        answer_parts.append(f"{i}. {result['text']} (score: {result['score']:.2f})")

    answer = "\n".join(answer_parts)

    return {
        "agent_id": AGENT_ID,
        "query": request.query,
        "answer": answer,
        "sources": results
    }
