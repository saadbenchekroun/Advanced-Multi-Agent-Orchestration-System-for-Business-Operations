"""Customer support agent implementation"""

from google.adk.agents import LlmAgent, SequentialAgent
from tools import BrowserTool, search_knowledge_base
from google.adk.tools import FunctionTool

# Create the search tool
SearchTool = FunctionTool(func=search_knowledge_base)

def create_customer_support_agent(default_model: str, config: dict, memory_store) -> SequentialAgent:
    """Create an advanced customer support agent with sentiment analysis and ticket routing"""
    sentiment_analyzer = LlmAgent(
        name="SentimentAnalyzer",
        model=config.get("agent_settings", {}).get("sentiment_model", default_model),
        instruction="""
        Analyze customer message sentiment on a scale from 1-10:
        1-3: Upset/Angry
        4-6: Neutral
        7-10: Positive
        Include specific emotional cues and urgency indicators.
        """
    )
    
    ticket_classifier = LlmAgent(
        name="TicketClassifier",
        model=default_model,
        instruction="""
        Classify support tickets into the following categories:
        - billing_issue: Payment, invoice, or subscription problems
        - technical_problem: Software bugs or technical difficulties
        - feature_request: Requests for new features or improvements
        - account_access: Login problems or permission issues
        - general_inquiry: General questions about products or services
        Output format: {"category": "category_name", "confidence": 0.XX, "priority": 1-5}
        """
    )
    
    response_generator = LlmAgent(
        name="ResponseGenerator",
        model=config.get("agent_settings", {}).get("response_model", "gemini-1.5-pro"),
        instruction="""
        Generate helpful, empathetic customer support responses based on:
        1. Customer query
        2. Sentiment analysis
        3. Ticket classification
        4. Available knowledge base articles
        5. Customer history and account information
        
        For high-priority or complex issues, include an escalation path.
        For technical issues, include troubleshooting steps when applicable.
        For billing issues, reference specific policies.
        """
    )
    
    follow_up_scheduler = LlmAgent(
        name="FollowUpScheduler",
        model=default_model,
        instruction="""
        Determine if and when a follow-up is needed based on:
        1. Issue complexity
        2. Resolution status
        3. Customer satisfaction indicators
        
        Output format: {"needs_followup": true/false, "timeframe": "24h/48h/72h", "reason": "explanation"}
        """
    )
    
    knowledge_retriever = LlmAgent(
        name="KnowledgeRetriever",
        model=default_model,
        instruction="""
        Search the knowledge base for relevant articles and solutions.
        Prioritize exact matches, then similar issues.
        Return top 3 most relevant resources with confidence scores.
        """,
        tools=[SearchTool]
    )
    
    return SequentialAgent(
        name="CustomerSupportAgent",
        sub_agents=[
            sentiment_analyzer,
            ticket_classifier,
            knowledge_retriever,
            response_generator,
            follow_up_scheduler
        ],
        memory=memory_store
    )