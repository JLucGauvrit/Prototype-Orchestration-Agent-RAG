from fastapi import FastAPI, Request
from mcp.client import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os
import chromadb

app = FastAPI()

AGENT_NAME = os.getenv("AGENT_NAME", "AgentX")

# Initialisation ChromaDB pour RAG local
client = chromadb.Client()
collection = client.get_or_create_collection(name="local_docs")

# Connexion aux serveurs MCP externes
mcp_servers = {}

async def connect_to_mcp_servers():
    """Connecte l'agent aux serveurs MCP configurés"""
    global mcp_servers
    
    # Connexion au serveur Gmail MCP (si configuré)
    if os.getenv("GMAIL_MCP_ENABLED") == "true":
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-gmail"],
            env={"GMAIL_API_KEY": os.getenv("GMAIL_API_KEY", "")}
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_servers["gmail"] = session
    
    # Connexion au serveur PostgreSQL MCP (si configuré)
    if os.getenv("POSTGRES_MCP_ENABLED") == "true":
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres"],
            env={
                "POSTGRES_URL": os.getenv("POSTGRES_URL", ""),
                "POSTGRES_USER": os.getenv("POSTGRES_USER", ""),
                "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "")
            }
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_servers["postgres"] = session

@app.on_event("startup")
async def startup():
    """Initialise les connexions MCP au démarrage"""
    await connect_to_mcp_servers()

@app.post("/query")
async def process_query(request: Request):
    """
    Traite une requête avec RAG local + outils MCP externes
    """
    data = await request.json()
    query_text = data["query"]
    
    try:
        # Étape 1: RAG local (ChromaDB)
        results = collection.query(query_texts=[query_text], n_results=3)
        local_context = " ".join(results["documents"][0])
        
        # Étape 2: Enrichissement via outils MCP
        external_data = {}
        
        # Exemple: utiliser Gmail MCP si disponible
        if "gmail" in mcp_servers:
            gmail_result = await mcp_servers["gmail"].call_tool(
                "search_emails",
                arguments={"query": query_text, "max_results": 5}
            )
            external_data["emails"] = gmail_result
        
        # Exemple: utiliser PostgreSQL MCP si disponible
        if "postgres" in mcp_servers:
            db_result = await mcp_servers["postgres"].call_tool(
                "query",
                arguments={"sql": f"SELECT * FROM docs WHERE content ILIKE '%{query_text}%' LIMIT 5"}
            )
            external_data["database"] = db_result
        
        # Étape 3: Génération de réponse avec contexte enrichi
        combined_context = f"Local: {local_context}\nExternal: {external_data}"
        
        return {
            "agent": AGENT_NAME,
            "answer": combined_context,
            "sources": {
                "local_rag": len(results["documents"][0]),
                "external_tools": list(external_data.keys())
            }
        }
        
    except Exception as e:
        return {
            "agent": AGENT_NAME,
            "error": str(e)
        }

@app.get("/health")
async def health():
    return {
        "agent": AGENT_NAME,
        "status": "healthy",
        "mcp_connections": list(mcp_servers.keys())
    }
