from fastapi import FastAPI
import requests, os

app = FastAPI()
MCP_SERVER = os.getenv("MCP_SERVER_URL")

@app.get("/health")
def health():
    return {"status": "client ok"}

@app.post("/notify")
def notify(msg: str):
    requests.post(f"{MCP_SERVER}/notify", json={"msg": msg})
    return {"sent": msg}
