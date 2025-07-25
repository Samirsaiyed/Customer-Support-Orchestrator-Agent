"""
Configuration settings for Customer Support Orchestrator
"""

from dotenv import load_dotenv
from state import SupportConfig, get_default_config, UrgencyLevel
import os

# Load the env
load_dotenv()

class Config:
    """Main configuration class"""

    # API keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # LLM Settings
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))

    # Support System Settings
    SUPPORT_CONFIG = get_default_config()

    # Override with env vairables if present
    SUPPORT_CONFIG["sentiment_escalation_threshold"] = float(os.getenv(["ESCALATION_THRESHOLD_SENTIMENT", "-0.7"]))
    SUPPORT_CONFIG["max_auto_refund"] = float(os.getenv("MAX_AUTO_REFUND", "100.0"))
    SUPPORT_CONFIG["critical_response_time"] = int(os.getenv("CRITICAL_RESPONSE_TIME", "300"))

    # FILE PATHS
    DATA_DIR = os.getenv("DATA_DIR", "./data")
    CUSTOMER_DB_PATH = os.getenv("CUSTOMER_DB_PATH", f"{DATA_DIR}/customer_data.json")
    ESCALATION_RULES_PATH = f"{DATA_DIR}/escalation_rules.json"
    RESPONSE_TEMPLATES_PATH = f"{DATA_DIR}/response_templates.json"

    # LOGGING
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = "./outputs/logs"

    # Safety and Risk Assessment
    SAFETY_KEYWORDS = [
        "lawsuit", "legal", "lawyer", "sue", "court",
        "discrimination", "harassment", "threat",
        "delete account", "cancel subscription",
        "data breach", "privacy violation",
        "refund", "chargeback", "dispute"
    ]

    URGENCY_KEYWORDS = {
        UrgencyLevel.CRITICAL: [
            "down", "outage", "emergency", "urgent", "immediately",
            "production", "critical", "broken", "not working",
            "angry", "furious", "unacceptable"
        ],
        UrgencyLevel.HIGH: [
            "important", "asap", "soon", "quick", "fast",
            "problem", "issue", "error", "bug", "help"
        ],
        UrgencyLevel.MEDIUM: [
            "question", "how to", "when", "where", "why",
            "information", "details", "clarification"
        ],
        UrgencyLevel.LOW: [
            "curious", "wondering", "sometime", "eventually",
            "general", "basic", "simple"
        ]
    }

    # Sentiment Analysis Settings
    SENTIMENT_THRESHOLDS = {
        "very_positive": 0.5,
        "positive": 0.1,
        "neutral": -0.1,
        "negative": -0.5,
        "very_negative": -0.7,
        "angry": -0.8
    }

    # Agent Routing Rules
    ROUTING_KEYWORDS = {
        "technical": [
            "api", "integration", "code", "error", "bug",
            "not working", "broken", "technical", "development",
            "webhook", "authentication", "database", "server"
        ],
        "billing": [
            "payment", "charge", "bill", "invoice", "refund",
            "subscription", "pricing", "cost", "money",
            "credit card", "bank", "transaction"
        ],
        "sales": [
            "upgrade", "plan", "features", "demo", "trial",
            "purchase", "buy", "pricing", "quote",
            "enterprise", "custom", "contract"
        ],
        "general": [
            "account", "profile", "settings", "password",
            "login", "access", "how to", "tutorial",
            "documentation", "guide"
        ]
    }

    # Customer Tier Configurations
    TIER_SETTINGS = {
        "basic": {
            "max_auto_refund": 50.0,
            "response_time_multiplier": 1.0,
            "auto_escalate": False,
            "priority_score": 1
        },
        "premium": {
            "max_auto_refund": 200.0,
            "response_time_multiplier": 0.8,
            "auto_escalate": False,
            "priority_score": 2
        },
        "enterprise": {
            "max_auto_refund": 1000.0,
            "response_time_multiplier": 0.5,
            "auto_escalate": True,
            "priority_score": 4
        },
        "vip": {
            "max_auto_refund": 5000.0,
            "response_time_multiplier": 0.3,
            "auto_escalate": True,
            "priority_score": 5
        }
    }

    @classmethod
    def validate_config(cls)-> bool:
        """
        Validate that all required configuration is present
        
        Returns:
            bool: True if configuration is valid
        """
        if not cls.OPENAI_API_KEY:
            print("❌ Error: OPENAI_API_KEY not found in environment variables")
            return False

        # Create required directories
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.LOG_DIR, exist_ok=True)

        return True

    @classmethod
    def get_tier_settings(cls, tier: str) -> dict:
        """
        Get settings for a specific customer tier
        
        Args:
            tier: Customer tier (basic, premium, enterprise, vip)
            
        Returns:
            dict: Tier-specific settings
        """
        return cls.TIER_SETTINGS.get(tier.lower(), cls.TIER_SETTINGS["basic"])

    @classmethod
    def should_auto_escalate(cls, tier: str, urgency: str, sentiment_score: float) -> bool:
        """
        Determine if issue should be auto-escalated based on rules
        
        Args:
            tier: Customer tier
            urgency: Urgency level
            sentiment_score: Sentiment analysis score
            
        Returns:
            bool: True if should escalate immediately
        """
        tier_settings = cls.get_tier_settings(tier)
        
        # Enterprise/VIP customers with high urgency
        if tier_settings["auto_escalate"] and urgency in ["high", "critical"]:
            return True
        
        # Very negative sentiment
        if sentiment_score <= cls.SUPPORT_CONFIG["sentiment_escalation_threshold"]:
            return True
        
        # Critical urgency regardless of tier
        if urgency == "critical":
            return True
        
        return False


# Export commonly used config values
SUPPORT_CONFIG = Config.SUPPORT_CONFIG
SAFETY_KEYWORDS = Config.SAFETY_KEYWORDS
URGENCY_KEYWORDS = Config.URGENCY_KEYWORDS
ROUTING_KEYWORDS = Config.ROUTING_KEYWORDS
SENTIMENT_THRESHOLDS = Config.SENTIMENT_THRESHOLDS
