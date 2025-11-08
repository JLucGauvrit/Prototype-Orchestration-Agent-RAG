from fastapi import FastAPI
import docker

app = FastAPI()
client = docker.from_env()

@app.get("/agents")
def list_agents():
    containers = client.containers.list(filters={"name": "agent-rag"})
    return [c.name for c in containers]

@app.post("/agents")
def create_agent():
    idx = len(client.containers.list(filters={"name": "agent-rag"})) + 1
    name = f"agent-rag-{idx}"
    client.containers.run(
        "agents_rag",
        name=name,
        network="backend",
        detach=True,
        environment={
            "AGENT_ID": str(idx),
            "DATA_PATH": f"/app/data/agent_{idx}",
            "POSTGRES_URL": "postgresql://rag_user:rag_pass@postgres:5432/rag_db"
        },
        volumes={"rag_data": {"bind": "/app/data", "mode": "rw"}}
    )
    return {"created": name}

@app.delete("/agents/{name}")
def delete_agent(name: str):
    try:
        c = client.containers.get(name)
        c.stop()
        c.remove()
        return {"deleted": name}
    except docker.errors.NotFound:
        return {"error": "not found"}
