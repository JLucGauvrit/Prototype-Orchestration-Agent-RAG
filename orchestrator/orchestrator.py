import asyncio
import os
import json
import uuid
import httpx
from typing import Optional, Dict, Any, List, Callable
from contextlib import AsyncExitStack

# Constantes pour l'API Perplexity
PPLX_API_URL = "https://api.perplexity.ai/chat/completions"
PPLX_MODEL = "pplx-70b-online" 


from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client



from dotenv import load_dotenv
load_dotenv() 

# --- Client API Perplexity Réel (inchangé) ---
class PerplexityAPIClient:
    """
    Client asynchrone pour l'API Perplexity.
    """
    def __init__(self):
        self.api_key = os.getenv("PPLX_API_KEY")
        if not self.api_key:
            raise ValueError("La variable d'environnement PPLX_API_KEY n'est pas définie.")

    async def create(self, model: str, max_tokens: int, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Any:

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "tools": tools,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(PPLX_API_URL, headers=headers, json=payload, timeout=20)
                response.raise_for_status()
                
                response_data = response.json()
                
                if response_data and response_data.get('choices'):
                    assistant_response_content = response_data['choices'][0]['message']['content']
                    # S'assure que le format correspond à ce que la boucle process_query attend
                    if not isinstance(assistant_response_content, list):
                        # Gère le cas où PPLX renvoie une chaîne de texte simple au lieu d'une liste de contenus
                         assistant_response_content = [{"type": "text", "text": assistant_response_content}]
                    
                    return {"content": assistant_response_content}
                
                else:
                    return {"content": [{"type": "text", "text": "Erreur API : Réponse PPLX vide ou mal formatée."}]}
                    
        except httpx.HTTPStatusError as e:
            error_message = f"Erreur HTTP: {e.response.status_code} - {e.response.text}"
            print(f" ERREUR API PPLX: {error_message}")
            return {"content": [{"type": "text", "text": error_message}]}
        except Exception as e:
            print(f" ERREUR générale lors de l'appel PPLX: {e}")
            return {"content": [{"type": "text", "text": f"Erreur PPLX inattendue: {e}"}]}

# --- Classe Cliente MCP (Adaptée pour API) ---

class MCPClientAPIAdapter:

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        try:
            self.llm_api = PerplexityAPIClient()
        except ValueError as e:
            print(f" ERREUR DE CONFIGURATION : {e}")
            self.llm_api = None

    async def connect_to_server(self, server_script_path: str):
        if self.llm_api is None:
            raise RuntimeError("Impossible de se connecter au serveur car la configuration API a échoué.")
            
        print(f"Connecting to server at {server_script_path}...")
        
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
        
        response = await self.session.list_tools()
        tools = response.tools
        print(f" Connecté au serveur MCP avec les outils: {[tool.name for tool in tools]}")


    async def process_query(self, query: str) -> str:

        if self.session is None or self.llm_api is None:
            return json.dumps({"error": "MCP Client non initialisé ou API Key manquante."}, indent=2)
            
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        
        response = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        } for tool in response.tools]
        
        final_text = []
        
        for i in range(5): 
            llm_response = await self.llm_api.create(
                model=PPLX_MODEL, 
                max_tokens=2000,
                messages=messages,
                tools=available_tools
            )

            assistant_message_content = []
            tool_called = False
            
            # Traitement de la réponse du LLM
            for content in llm_response.get('content', []):
                if content['type'] == 'text':
                    final_text.append(content['text'])
                    assistant_message_content.append(content)
                elif content['type'] == 'tool_use':
                    tool_called = True
                    tool_name = content['name']
                    tool_args = content['input']
                    tool_use_id = content['id']
                    
                    # Logique de l'appel d'outil
                    assistant_message_content.append(content)
                    messages.append({ "role": "assistant", "content": assistant_message_content })
                    
                    print(f" EXÉCUTION DE L'OUTIL {tool_name} SUR LE SERVEUR...")
                    try:
                        # Appel à l'agent RAG via MCP
                        result = await self.session.call_tool(tool_name, tool_args)
                        print(f" RÉSULTAT REÇU : {result.content}")

                        # Ajout du résultat de l'outil pour le prochain appel LLM
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": result.content
                                }
                            ]
                        })
                    except Exception as e:
                        print(f" Erreur lors de l'appel de l'outil {tool_name}: {e}")
                        # En cas d'erreur, ajoute un message d'erreur pour que l'LLM réponde
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": f"Erreur du serveur d'outils: {e}"
                                }
                            ]
                        })

            if not tool_called:
                break
        
        return "\n".join(final_text)

    async def cleanup(self):
        """Nettoyage des ressources (appelé à l'arrêt de l'API)."""
        if self.exit_stack:
            print(" Fermeture de la connexion MCP...")
            await self.exit_stack.aclose()

mcp_adapter = MCPClientAPIAdapter()