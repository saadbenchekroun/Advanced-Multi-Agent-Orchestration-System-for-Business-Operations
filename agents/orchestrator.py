from google.adk.agents import LlmAgent, ParallelAgent
from tools import BrowserTool, search_knowledge_base
from google.adk.tools import FunctionTool

SearchTool = FunctionTool(func=search_knowledge_base)

def _create_orchestrator_agent(self, default_model: str) -> ParallelAgent:
    """Create a top-level orchestrator agent"""
    task_prioritizer = LlmAgent(
        name="TaskPrioritizer",
        model=self.config.get("agent_settings", {}).get("prioritizer_model", "gemini-1.5-pro"),
        instruction="""
        Prioritize tasks across all business functions:
        1. Evaluate business impact and urgency
        2. Consider dependencies and blockers
        3. Balance short-term needs with strategic goals
        4. Allocate resources efficiently across departments
        
        Create a daily priority queue with clear rationale.
        """
    )
    
    workflow_coordinator = LlmAgent(
        name="WorkflowCoordinator",
        model=self.config.get("agent_settings", {}).get("coordinator_model", "gemini-1.5-pro"),
        instruction="""
        Coordinate cross-functional workflows:
        1. Identify handoff points between departments
        2. Ensure information flows properly between agents
        3. Prevent bottlenecks and duplication of effort
        4. Optimize end-to-end business processes
        
        Design workflows that maximize automation opportunities.
        """
    )
    
    performance_monitor = LlmAgent(
        name="PerformanceMonitor",
        model=default_model,
        instruction="""
        Monitor system-wide performance:
        1. Track agent completion rates and quality
        2. Measure response times and throughput
        3. Identify performance bottlenecks
        4. Compare actual vs. expected outcomes
        
        Generate daily performance dashboards with trends.
        """
    )
    
    escalation_handler = LlmAgent(
        name="EscalationHandler",
        model=self.config.get("agent_settings", {}).get("escalation_model", "gemini-1.5-pro"),
        instruction="""
        Handle exceptions and escalations:
        1. Analyze root causes of failures or issues
        2. Route complex problems to appropriate human experts
        3. Provide comprehensive context for human decision-makers
        4. Learn from resolution patterns to improve future handling
        
        Maintain clear documentation of all escalation cases.
        """
    )
    
    return ParallelAgent(
        name="StartupOrchestrator",
        sub_agents=[
            task_prioritizer,
            performance_monitor,
            workflow_coordinator,
            escalation_handler
        ],
        memory=self.memory_store
    )