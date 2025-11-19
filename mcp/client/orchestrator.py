"""
Orchestrateur avec Perplexity routing + MCP tools
1. Connexion au serveur MCP pour récupérer la liste des agents
2. Perplexity décide quel agent utiliser (structured output JSON)
3. Appel manuel du tool MCP correspondant
"""
import asyncio
import os
import json
from typing import Optional, Dict, Any
from contextlib import AsyncExitStack
from openai import OpenAI

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv
load_dotenv()

# Configuration Perplexity
PPLX_MODEL = "sonar"
PPLX_API_KEY = os.getenv("PPLX_API_KEY")


class MCPClientWithPerplexityRouter:
    """Client MCP avec routage intelligent via Perplexity"""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.available_tools = []

        if not PPLX_API_KEY:
            raise ValueError("La variable d'environnement PPLX_API_KEY n'est pas définie.")

        # Client Perplexity pour le routing
        self.perplexity = OpenAI(
            api_key=PPLX_API_KEY,
            base_url="https://api.perplexity.ai"
        )

    async def connect_to_server(self, server_script_path: str):
        """Connexion au serveur MCP et récupération des tools disponibles"""
        print(f" Connexion au serveur MCP à {server_script_path}...")

        command = "python"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()

        # Récupérer la liste des tools (agents RAG) disponibles
        response = await self.session.list_tools()
        self.available_tools = response.tools

        print(f" Connecté au serveur MCP")
        print(f" Agents disponibles: {[tool.name for tool in self.available_tools]}")

    async def route_with_perplexity(self, user_query: str) -> Dict[str, Any]:
        """Utilise Perplexity pour décider quel agent MCP appeler"""

        # Construire la description des agents depuis les tools MCP
        agents_description = ""
        agent_names = []

        for tool in self.available_tools:
            agents_description += f"- {tool.name}: {tool.description}\n"
            agent_names.append(tool.name)

        # Schéma JSON dynamique basé sur les tools disponibles
        routing_schema = {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "enum": agent_names,
                    "description": "Nom du tool MCP à appeler"
                },
                "query": {
                    "type": "string",
                    "description": "Requête reformulée pour l'agent"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explication du choix de l'agent"
                }
            },
            "required": ["tool_name", "query", "reasoning"]
        }

        routing_prompt = f"""Tu es un routeur intelligent pour un système multi-agents RAG.

Agents disponibles:
{agents_description}

Requête utilisateur: "{user_query}"

Choisis le meilleur agent pour cette requête."""

        try:
            response = self.perplexity.chat.completions.create(
                model=PPLX_MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un expert en routage de requêtes."},
                    {"role": "user", "content": routing_prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "agent_routing",
                        "strict": True,
                        "schema": routing_schema
                    }
                },
                max_tokens=500
            )

            # Parser le JSON
            routing_decision = json.loads(response.choices[0].message.content)
            print(f" Décision de routing: {routing_decision}")
            return routing_decision

        except Exception as e:
            print(f" Erreur lors du routing: {e}")
            # Fallback: premier agent disponible
            return {
                "tool_name": self.available_tools[0].name if self.available_tools else "query_agent_1",
                "query": user_query,
                "reasoning": f"Erreur de routing, utilisation de l'agent par défaut: {str(e)}"
            }

    async def call_mcp_tool(self, tool_name: str, query: str) -> str:
        """Appelle un tool MCP avec la requête"""
        if self.session is None:
            raise RuntimeError("Session MCP non initialisée")

        print(f"Appel du tool MCP: {tool_name}")

        try:
            # Appel du tool MCP
            result = await self.session.call_tool(tool_name, {"query": query})

            # Extraire le texte de la réponse
            if hasattr(result, 'content') and result.content:
                if isinstance(result.content, list):
                    # Concaténer tous les contenus texte
                    return " ".join([
                        item.text if hasattr(item, 'text') else str(item)
                        for item in result.content
                    ])
                return str(result.content)

            return str(result)

        except Exception as e:
            print(f"Erreur lors de l'appel du tool {tool_name}: {e}")
            return f"Erreur lors de l'appel de l'agent: {str(e)}"

    async def process_query(self, user_query: str) -> str:
        """
        Pipeline complet:
        1. Router la requête avec Perplexity
        2. Appeler le tool MCP correspondant
        3. Retourner la réponse
        """
        if self.session is None:
            raise RuntimeError("Session MCP non initialisée. Appelez connect_to_server() d'abord.")

        print(f"\n Requête utilisateur: {user_query}")

        routing_decision = await self.route_with_perplexity(user_query)

        tool_name = routing_decision["tool_name"]
        query = routing_decision["query"]

        response = await self.call_mcp_tool(tool_name, query)

        print(f"✅ Réponse reçue\n")
        return response

    async def cleanup(self):
        """Nettoyage des ressources"""
        if self.exit_stack:
            print(" Fermeture de la connexion MCP...")
            await self.exit_stack.aclose()


# Instance globale
mcp_adapter = MCPClientWithPerplexityRouter()
