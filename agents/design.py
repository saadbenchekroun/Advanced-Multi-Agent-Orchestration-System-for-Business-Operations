from google.adk.agents import LlmAgent, SequentialAgent
from tools import BrowserTool, search_knowledge_base
from google.adk.tools import FunctionTool

SearchTool = FunctionTool(func=search_knowledge_base)

def _create_design_agent(self, default_model: str) -> SequentialAgent:
    """Create a design agent with UX and prototyping capabilities"""
    requirements_analyzer = LlmAgent(
        name="RequirementsAnalyzer",
        model=self.config.get("agent_settings", {}).get("requirements_model", "gemini-1.5-pro"),
        instruction="""
        Analyze design requirements by:
        1. Identifying explicit and implicit user needs
        2. Mapping requirements to user personas
        3. Prioritizing features by impact and feasibility
        4. Flagging ambiguous or conflicting requirements
        
        Create clear design briefs with measurable success criteria.
        """
    )
    
    competitive_analyzer = LlmAgent(
        name="CompetitiveAnalyzer",
        model=default_model,
        instruction="""
        Analyze competitor designs:
        1. Document UI patterns and interaction models
        2. Evaluate strengths and weaknesses
        3. Identify differentiation opportunities
        4. Note emerging trends and industry standards
        
        Create comparison matrices of key features and approaches.
        """,
        tools=[BrowserTool()]
    )
    
    prototype_generator = LlmAgent(
        name="PrototypeGenerator",
        model=self.config.get("agent_settings", {}).get("prototype_model", "gemini-1.5-pro"),
        instruction="""
        Generate Figma wireframes and prototypes:
        1. Create low-fidelity wireframes for initial concepts
        2. Develop interactive prototypes for testing
        3. Apply design system components consistently
        4. Document interaction specifications
        
        Include responsive variants for all major breakpoints.
        """
    )
    
    accessibility_checker = LlmAgent(
        name="AccessibilityChecker",
        model=default_model,
        instruction="""
        Evaluate designs for accessibility:
        1. Check color contrast ratios (WCAG AA/AAA)
        2. Verify text sizing and readability
        3. Ensure keyboard navigability
        4. Test screen reader compatibility
        
        Provide specific remediation recommendations for issues.
        """
    )
    
    feedback_handler = LlmAgent(
        name="FeedbackHandler",
        model=default_model,
        instruction="""
        Process and prioritize design feedback:
        1. Categorize feedback by type and source
        2. Identify patterns and common themes
        3. Evaluate impact and implementation difficulty
        4. Reconcile conflicting feedback
        
        Create actionable feedback summaries with specific design tasks.
        """
    )
    
    return SequentialAgent(
        name="DesignAgent",
        sub_agents=[
            requirements_analyzer,
            competitive_analyzer,
            prototype_generator,
            accessibility_checker,
            feedback_handler
        ],
        memory=self.memory_store
    )