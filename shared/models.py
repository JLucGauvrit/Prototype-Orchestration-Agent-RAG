"""
Modèles Pydantic partagés entre orchestrateur et agents
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class AgentSpecialty(str, Enum):
    """Types de spécialités des agents"""
    GENERAL_KNOWLEDGE = "general_knowledge"
    CURRENT_EVENTS = "current_events"
    DATA_ANALYSIS = "data_analysis"
    TECHNICAL = "technical"


class AgentStatus(str, Enum):
    """États possibles d'un agent"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


class MCPRequestType(str, Enum):
    """Types de requêtes MCP"""
    QUERY = "query"
    INGEST = "ingest"
    HEALTH_CHECK = "health_check"
    AGENT_REGISTER = "agent_register"


class Document(BaseModel):
    """Document à indexer dans le RAG"""
    id: Optional[int] = None
    agent_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MCPRequest(BaseModel):
    """Requête MCP standardisée"""
    request_id: str
    request_type: MCPRequestType
    agent_id: Optional[str] = None  # Pour cibler un agent spécifique
    query: Optional[str] = None
    documents: Optional[List[Document]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MCPResponse(BaseModel):
    """Réponse MCP standardisée"""
    request_id: str
    agent_id: str
    agent_name: str
    response: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    processing_time_ms: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentInfo(BaseModel):
    """Informations sur un agent"""
    agent_id: str
    agent_name: str
    specialty: AgentSpecialty
    status: AgentStatus
    endpoint: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    total_queries: int = 0
    avg_response_time_ms: int = 0


class OrchestratedResponse(BaseModel):
    """Réponse agrégée de l'orchestrateur"""
    request_id: str
    original_query: str
    synthesized_response: str
    agent_responses: List[MCPResponse]
    total_processing_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserQuery(BaseModel):
    """Requête utilisateur depuis l'interface"""
    query: str
    target_agents: Optional[List[str]] = None  # Si None, tous les agents
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthCheckResponse(BaseModel):
    """Réponse au health check"""
    agent_id: str
    status: AgentStatus
    uptime_seconds: int
    documents_indexed: int
    last_query_time: Optional[datetime] = None
