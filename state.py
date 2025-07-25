"""
State schema for Customer Support Orchestrator
This defines the data structure that flows through all agents
"""

from typing import List, Dict, Optional
from typing_extensions import TypedDict
from datetime import datetime
from enum import Enum

class QueryType():
    """Type of customer queries"""
    TECHNICAL = "technical" 
    BILLING = "billing"
    GENERAL = "general"
    SALES = "sales"
    COMPLAINT = "complaint"
    UNKNOWN = "unknown"

class UrgencyLevel(str, Enum):
    """Urgency levels for customer issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SentimentLevel(str, Enum):
    """Customer Sentiment levels"""
    VERY_HIGH = "very_high"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"
    ANGRY = "angry"

class CustomerTier(str, Enum):
    """Customer subscription tiers"""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    VIP = "vip"

class ResolutionStatus(str, Enum):
    """Status of issue resolution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    HUMAN_HANDOFF = "human_handoff"

class AgentType(str, Enum):
    """Type of support agents"""
    INTAKE = "intake"
    ROUTER = "router"
    TECHNICAL = "technical"
    BILLING = "billing"
    GENERAL = "general"
    SALES = "sales"
    QUALITY = "quality"
    ESCALATION =  "escalation"

class Message(TypedDict):
    """Individual message in conversation"""
    timestamp: str
    sender: str     # customer, agent_name, human_agent
    content: str
    agent_type: Optional[str]
    confidence_score: Optional[str]

class CustomerInfo(TypedDict):
    """Customer Information"""
    customer_id: str
    name: str
    email: str
    tier: CustomerTier
    account_status: str     # active, suspended, trial
    previous_tickets: int
    satisfaction_score: Optional[float]
    language: str

class RiskAssessment(TypedDict):
    """Risk factors for escalation decisions"""
    financial_risk: bool
    legal_risk: bool
    reputation_risk: bool
    churn_risk: bool
    complexity_risk: bool
    overall_risk_score: float

class AgentResponse(TypedDict):
    """Response from a specialist agent"""
    agent_type: AgentType
    response: str
    confidence_score: float
    suggested_actions: List[str]
    requires_escalation: bool
    resolution_time: Optional[int]

class SupportState(TypedDict):
    """Main state object that flows through the langgraph workflow"""

    # session information
    session_id: str
    timestamp: str

    # Customer information
    customer_info: CustomerInfo

    # Query Analysis
    original_query: str
    processed_query: str
    query_type: QueryType
    urgency_level: UrgencyLevel
    sentiment_level: SentimentLevel

    # Conversation History
    conversation_history: List[Message]

    # Agent workflow
    current_agent: AgentType
    assigned_agents: List[AgentType]
    completed_agents: List[AgentType]

    # Agent Response
    agent_response: List[AgentResponse]
    final_response: Optional[str]

    # Decision making
    risk_assessment: RiskAssessment
    escalation_needed: bool
    human_handoff_required: bool
    escalation_reason: Optional[str]

    # Resolution Status
    resolution_status: ResolutionStatus
    resolution_time: Optional[int]
    customer_satisfaction: Optional[float]

    # System Metadata
    workflow_step: str
    error_messages: List[str]
    debug_info: Dict[str, Any]


class SupportConfig(TypedDict):
    """Configuration for support system"""

    # Escalation Thresholds
    sentiment_escalation_threshold: float  # -0.7
    urgency_escalation_level: UrgencyLevel  # HIGH
    max_auto_refund: float  # 100.0
    max_agent_attempts: int  # 3

    # Response Time Targets (seconds)
    critical_response_time: int  # 300
    high_response_time: int  # 1800
    medium_response_time: int  # 3600
    low_response_time: int  # 7200

    # Customer Tier Settings
    enterprise_auto_escalate: bool  # True
    vip_priority_routing: bool  # True

    # Agent Settings
    enable_parallel_processing: bool  # False
    require_quality_check: bool  # True

    # Safety Settings
    enable_safety_guards: bool  # True
    log_all_interactions: bool  # True


def create_initial_state(customer_id: str, query: str, customer_info: Optional[CustomerInfo] = None)-> SupportState:
    """
    Create initial state for a new support session
    
    Args:
        customer_id: Unique customer identifier
        query: Customer's original query
        customer_info: Optional customer information
        
    Returns:
        SupportState: Initial state object
    """

    session_id = f"support_{customer_id}_{int(datetime.now().timestamp())}"

    # Default customer info if not provided
    if customer_info is None:
        customer_info = {
            "customer_id": customer_id,
            "name": "Unknown Customer",
            "email": f"{customer_id}@example.com",
            "tier": CustomerTier.BASIC,
            "account_status":"active",
            "privious_tickets": 0,
            "satisfaction_score": None,
        }

    return {
        # Session information
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),

        # Customer Information
        "customer_info": customer_info,
        
        # Query Analysis
        "original_query": query,
        "processed_query": "",
        "query_type": QueryType.UNKNOWN,
        "urgency_level": UrgencyLevel.MEDIUM,
        "sentiment_level": SentimentLevel.NEUTRAL,

        # Conversation History
        "conversation_history": [
            {
                "timestamp": datetime.now().isoformat(),
                "sender": "customer",
                "content": query,
                "agent_type": None,
                "confidence_score": None
            }
        ],

        # Agent Workflow
        "current_agent": AgentType.INTAKE,
        "assigned_agents": [],
        "completed_agents": [],

        # Agent Responses
        "agent_responses": [],
        "final_response": None,

        # Decision Making
        "risk_assessment": {
            "financial_risk": False,
            "legal_risk": False,
            "reputation_risk": False,
            "churn_risk": False,
            "complexity_risk": False,
            "overall_risk_score": 0.0
        },
        "escalation_needed": False,
        "human_handoff_required": False,
        "escalation_reason": None,

        # Resolution Status
        "resolution_status": ResolutionStatus.PENDING,
        "resolution_time": None,
        "customer_satisfaction": None,

        # System Metadata
        "workflow_step": "intake",
        "error_messages": [],
        "debug_info": {}
    }

def get_default_config()-> SupportConfig:
    """
    Get default configuration for support system
    
    Returns:
        SupportConfig: Default configuration
    """

    return {
        # Escalation Thresholds
        "sentiment_escalation_threshold": -0.7,
        "urgency_escalation_level": UrgencyLevel.HIGH,
        "max_auto_refund": 100.0,
        "max_agent_attempts": 3,
        
        # Response Time Targets (seconds)
        "critical_response_time": 300,    # 5 minutes
        "high_response_time": 1800,       # 30 minutes
        "medium_response_time": 3600,     # 1 hour
        "low_response_time": 7200,        # 2 hours
        
        # Customer Tier Settings
        "enterprise_auto_escalate": True,
        "vip_priority_routing": True,
        
        # Agent Settings
        "enable_parallel_processing": False,
        "require_quality_check": True,
        
        # Safety Settings
        "enable_safety_guards": True,
        "log_all_interactions": True
    }





