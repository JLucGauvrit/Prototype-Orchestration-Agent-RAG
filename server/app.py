from mcp.server.fastmcp import FastMCP
from typing import Any
import httpx
import asyncio

# Initialiser le serveur MCP
mcp = FastMCP("rag-orchestrator")

# Liste des agents disponibles
AGENTS = {
    "agent-a": "http://agent-a:5000",
    "agent-b": "http://agent-b:5000", 
    "agent-c": "http://agent-c:5000"
}

@mcp.tool()
async def query_all_agents(query: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        tasks = [
            client.post(
                f"{url}/query",
                json={"query": query},
                timeout=120.0
            )
            for url in AGENTS.values()
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        for agent_name, resp in zip(AGENTS.keys(), responses):
            if isinstance(resp, Exception):
                results[agent_name] = {"error": str(resp)}
            else:
                results[agent_name] = resp.json()
        
        return results

@mcp.tool()
async def query_specific_agent(agent_name: str, query: str) -> dict[str, Any]:
    """
    Envoie une requête à un agent RAG spécifique.
    
    Args:
        agent_name: Nom de l'agent (agent-a, agent-b, agent-c)
        query: La question à poser
    
    Returns:
        Réponse de l'agent
    """
    if agent_name not in AGENTS:
        return {"error": f"Agent {agent_name} inconnu"}
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{AGENTS[agent_name]}/query",
            json={"query": query},
            timeout=120.0
        )
        return resp.json()

@mcp.resource("agents://list")
def list_available_agents() -> str:
    """Liste tous les agents RAG disponibles"""
    return "\n".join([f"- {name}: {url}" for name, url in AGENTS.items()])

if __name__ == "__main__":
    mcp.run(transport='stdio')
