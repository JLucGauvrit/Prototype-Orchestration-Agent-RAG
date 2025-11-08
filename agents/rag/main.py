from fastapi import FastAPI
import os

app = FastAPI()
DATA_PATH = os.getenv("DATA_PATH", "/app/data")
AGENT_ID = os.getenv("AGENT_ID")

@app.get("/health")
def health():
    return {"status": "ok", "agent_id": AGENT_ID}

@app.get("/query")
def query(q: str):
    return {"agent_id": AGENT_ID, "query": q, "answer": f"fake answer for {q}"}
