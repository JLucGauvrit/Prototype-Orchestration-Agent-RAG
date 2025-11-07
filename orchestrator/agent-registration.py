"""
Extension de l'orchestrateur pour l'enregistrement HTTP des agents
(Simplifié car FastMCP ne gère pas encore complètement le serveur MCP)
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["agent-registration"])


class AgentRegistration(BaseModel):
    agent_id: str
    agent_name: str
    specialty: str
    endpoint: str


@router.post("/register_agent")
async def register_agent_http(registration: AgentRegistration):
    """
    Endpoint HTTP pour l'enregistrement des agents
    (Utilisé en attendant une implémentation MCP complète)
    """
    from main import connected_agents, db, broadcast_to_monitors
    from models import AgentInfo, AgentStatus, AgentSpecialty
    from datetime import datetime
    
    agent_info = AgentInfo(
        agent_id=registration.agent_id,
        agent_name=registration.agent_name,
        specialty=AgentSpecialty(registration.specialty),
        status=AgentStatus.ONLINE,
        endpoint=registration.endpoint,
        last_heartbeat=datetime.utcnow()
    )
    
    connected_agents[registration.agent_id] = agent_info
    
    # Mettre à jour la BDD
    await db.update_agent_status(
        agent_id=registration.agent_id,
        status="online",
        agent_name=registration.agent_name,
        specialty=registration.specialty
    )
    
    # Notifier les clients de monitoring
    await broadcast_to_monitors({
        "type": "agent_registered",
        "agent": agent_info.model_dump(mode='json')
    })
    
    print(f"✅ Agent enregistré via HTTP: {registration.agent_name} ({registration.agent_id})")
    
    return {
        "status": "registered",
        "agent_id": registration.agent_id,
        "message": f"Agent {registration.agent_name} successfully registered"
    }


@router.post("/agent_heartbeat")
async def agent_heartbeat_http(heartbeat: dict):
    """Endpoint HTTP pour les heartbeats des agents"""
    from main import connected_agents
    from datetime import datetime
    from models import AgentStatus
    
    agent_id = heartbeat.get("agent_id")
    
    if agent_id in connected_agents:
        connected_agents[agent_id].last_heartbeat = datetime.utcnow()
        connected_agents[agent_id].status = AgentStatus.ONLINE
        return {"status": "ok", "agent_id": agent_id}
    
    return {"status": "unknown_agent", "agent_id": agent_id}


# Ajouter ce router dans main.py avec:
# from agent_registration import router as agent_router
# app.include_router(agent_router)
