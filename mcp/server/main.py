import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("rag-agents")

AGENTS = {
    "agent-1": {
        "name": "Machine Learning Expert",
        "endpoint": "http://agent-rag-1:9000",
        "description": "Expert in machine learning, AI, neural networks, deep learning, and data science concepts"
    },
    "agent-2": {
        "name": "Programming Expert",
        "endpoint": "http://agent-rag-2:9000",
        "description": "Expert in programming languages, DevOps, cloud computing, APIs, and software development"
    }
}


@mcp.tool()
async def query_agent_1(query: str) -> str:
    """
    Search in Machine Learning Expert knowledge base.
    Use this for questions about AI, ML, neural networks, deep learning, and data science.

    Args:
        query: The question about machine learning
    """
    return await _call_agent("agent-1", query)


@mcp.tool()
async def query_agent_2(query: str) -> str:
    """
    Search in Programming Expert knowledge base.
    Use this for questions about programming, DevOps, cloud, APIs, and software development.

    Args:
        query: The question about programming
    """
    return await _call_agent("agent-2", query)


async def _call_agent(agent_id: str, query: str) -> str:
    agent = AGENTS[agent_id]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{agent['endpoint']}/query",
                json={"query": query},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            return result.get("answer", str(result))

    except Exception as e:
        return f"Error calling {agent['name']}: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
