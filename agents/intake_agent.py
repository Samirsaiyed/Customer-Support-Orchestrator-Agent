import json
from datetime import datetime
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from state import SupportState, QueryType, UrgencyLevel, SentimentLevel, Message
from config import Config, URGENCY_KEYWORDS, ROUTING_KEYWORDS, SENTIMENT_THRESHOLDS

class IntakeAgent:
    """
    Analyzes incoming customer queries and extracts key information
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.MODEL_NAME,
            temperature = Config.TEMPERATURE,
            max_tokens = Config.MAX_TOKENS,
            api_key=Config.OPENAI_API_KEY
        )
        
        self.sentiemnt_analyzer = SentimentIntensityAnalyzer()

    def analyzer_query_type(self, query:str)-> QueryType:
        """
        Classify the query type based on keywords and content
        
        Args:
            query: Customer's query text
            
        Returns:
            QueryType: Classified query type
        """

        query_lower = query.lower()

        # Count keyword matches for each category
        type_scores = {}
        for query_type, keywords in ROUTING_KEYWORDS.items():
            scope = sum(1 for keyword in keywords if keyword in query_lower)
            type_scores[query_type] = score

        # Return the type with highest score, or UNKNOWN if no matches
        if max(type_scores.values()) > 0:
            return QueryType(max(type_scores, key=type_scores.get))

        # Use LLM as fallback for complex classification
        return self._llm_classify_query(query)

    def analyzer_urgency(self, query: str)-> UrgencyLevel:
        """
        Determine urgency level based on keywords and sentiment
        
        Args:
            query: Customer's query text
            
        Returns:
            UrgencyLevel: Classified urgency level
        """

        query_lower = query.lower()
        
        # Check for urgency keywords
        for urgency_level, keywords in URGENCY_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                return urgency_level
        
        # Default to medium if no clear indicators
        return UrgencyLevel.MEDIUM

    def analyze_sentiment(self, query:str)-> tuple[SentimentLevel, float]:
        """
        Analyze customer sentiment using multiple methods
        
        Args:
            query: Customer's query text
            
        Returns:
            tuple: (SentimentLevel, sentiment_score)
        """

        # Use VADER sentiment analyzer
        vader_scores = self.sentiment_analyzer.polarity_scores(query)
        compound_score = vader_scores['compound']
        
        # Also use TextBlob as backup
        blob = TextBlob(query)
        textblob_score = blob.sentiment.polarity
        
        # Average the scores
        avg_score = (compound_score + textblob_score) / 2

        # Classify sentiment based on thresholds
        if avg_score >= SENTIMENT_THRESHOLDS["very_positive"]:
            sentiment_level = SentimentLevel.VERY_POSITIVE
        elif avg_score >= SENTIMENT_THRESHOLDS["positive"]:
            sentiment_level = SentimentLevel.POSITIVE
        elif avg_score >= SENTIMENT_THRESHOLDS["neutral"]:
            sentiment_level = SentimentLevel.NEUTRAL
        elif avg_score >= SENTIMENT_THRESHOLDS["negative"]:
            sentiment_level = SentimentLevel.NEGATIVE
        elif avg_score >= SENTIMENT_THRESHOLDS["very_negative"]:
            sentiment_level = SentimentLevel.VERY_NEGATIVE
        else:
            sentiment_level = SentimentLevel.ANGRY
        
        return sentiment_level, avg_score
    
    def _llm_classify_query(self, query: str) -> QueryType:
        """
        Use LLM to classify complex queries
        
        Args:
            query: Customer's query text
            
        Returns:
            QueryType: Classified query type
        """
        prompt = f"""
        Classify this customer support query into one of these categories:
        - technical: API issues, bugs, integrations, technical problems
        - billing: payments, refunds, subscriptions, pricing, invoices
        - sales: upgrades, demos, new features, purchasing
        - general: account questions, how-to, basic support
        - complaint: complaints, dissatisfaction, problems with service
        
        Query: "{query}"
        
        Return only the category name (technical, billing, sales, general, or complaint):
        """

        try:
            response = self.llm.invoke(prompt)
            classification = response.content.strip().lower()

            # Map to our enum
            if classification in ["technical"]:
                return QueryType.TECHNICAL
            elif classification in ["billing"]:
                return QueryType.BILLING
            elif classification in ["sales"]:
                return QueryType.SALES
            elif classification in ["general"]:
                return QueryType.GENERAL
            elif classification in ["complaint"]:
                return QueryType.COMPLAINT
            else:
                return QueryType.UNKNOWN
                
        except Exception as e:
            print(f"LLM classification failed: {e}")
            return QueryType.UNKNOWN

    def process_query(self, state: SupportState)-> SupportState:
        """
        Main function to process incoming query and update state
        
        Args:
            state: Current support state
            
        Returns:
            SupportState: Updated state with analysis
        """

        query = state["original_query"]

        print(f"🔍 Intake Agent analyzing query: {query[:50]}...")

        try:
            # Analyze query components
            query_type = self.analyze_query_type(query)
            urgency_level = self.analyze_urgency(query)
            sentiment_level, sentiment_score = self.analyze_sentiment(query)

            # Update state with analysis
            state["query_type"] = query_type
            state["urgency_level"] = urgency_level
            state["sentiment_level"] = sentiment_level
            state["processed_query"] = query  # Could add cleaning/normalization here
            state["current_agent"] = "router"
            state["workflow_step"] = "routing"

            # Add sentiment score to debug info
            state["debug_info"]["sentiment_score"] = sentiment_score
            state["debug_info"]["intake_analysis"] = {
                "query_type": query_type.value,
                "urgency_level": urgency_level.value,
                "sentiment_level": sentiment_level.value,
                "sentiment_score": sentiment_score
            }

            # Add intake agent to completed agents
            state["completed_agents"].append("intake")

            # Add analysis message to conversation history
            analysis_message: Message = {
                "timestamp": datetime.now().isoformat(),
                "sender": "intake_agent",
                "content": f"Query analyzed - Type: {query_type.value}, Urgency: {urgency_level.value}, Sentiment: {sentiment_level.value}",
                "agent_type": "intake",
                "confidence_score": 0.8
            }
            state["conversation_history"].append(analysis_message)

            print(f"✅ Analysis complete:")
            print(f"   Type: {query_type.value}")
            print(f"   Urgency: {urgency_level.value}")
            print(f"   Sentiment: {sentiment_level.value} (score: {sentiment_score:.2f})")

        except Exception as e:
            error_msg = f"Intake analysis failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"❌ {error_msg}")
            
            # Set defaults on error
            state["query_type"] = QueryType.UNKNOWN
            state["urgency_level"] = UrgencyLevel.MEDIUM
            state["sentiment_level"] = SentimentLevel.NEUTRAL
        
    return state

# Create global instance
intake_agent = IntakeAgent()

# Node function for LangGraph
def intake_node(state: SupportState) -> SupportState:
    """
    LangGraph node function for intake processing
    
    Args:
        state: Current support state
        
    Returns:
        SupportState: Updated state
    """
    return intake_agent.process_query(state)
    