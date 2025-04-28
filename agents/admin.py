from google.adk.agents import LlmAgent, SequentialAgent
from tools import BrowserTool, search_knowledge_base
from google.adk.tools import FunctionTool

SearchTool = FunctionTool(func=search_knowledge_base)

def _create_admin_agent(self, default_model: str) -> SequentialAgent:
    """Create an admin agent with project management capabilities"""
    meeting_scheduler = LlmAgent(
        name="MeetingScheduler",
        model=default_model,
        instruction="""
        Schedule team meetings considering:
        1. Participant availability and time zones
        2. Meeting purpose and required duration
        3. Previous meeting patterns and preferences
        4. Resource availability (rooms, equipment)
        
        Prepare and distribute clear agendas with pre-reading materials.
        """,
        tools=[BrowserTool()]
    )
    
    meeting_summarizer = LlmAgent(
        name="MeetingSummarizer",
        model=self.config.get("agent_settings", {}).get("summary_model", "gemini-1.5-pro"),
        instruction="""
        Create comprehensive meeting summaries including:
        1. Key discussion points and decisions
        2. Action items with assigned owners and deadlines
        3. Open questions and parking lot items
        4. Follow-up meeting requirements
        
        Distribute summaries within 2 hours of meeting completion.
        """
    )
    
    document_manager = LlmAgent(
        name="DocumentManager",
        model=default_model,
        instruction="""
        Maintain internal documentation:
        1. Organize documents by project, department, and type
        2. Update documentation based on recent changes
        3. Flag outdated information for review
        4. Create clear templates for common documents
        
        Ensure documentation is accessible and searchable.
        """
    )
    
    resource_allocator = LlmAgent(
        name="ResourceAllocator",
        model=default_model,
        instruction="""
        Optimize resource allocation across projects:
        1. Track resource utilization rates
        2. Identify capacity constraints and availability
        3. Match resource skills to project requirements
        4. Propose reallocation to balance workloads
        
        Flag resource conflicts and recommend resolution options.
        """
    )
    
    milestone_tracker = LlmAgent(
        name="MilestoneTracker",
        model=default_model,
        instruction="""
        Track project milestones and deliverables:
        1. Monitor progress against timeline
        2. Calculate completion percentages
        3. Identify dependencies and critical path items
        4. Flag at-risk milestones with specific causes
        
        Send alerts for approaching deadlines and missed targets.
        """
    )
    
    return SequentialAgent(
        name="AdminAgent",
        sub_agents=[
            meeting_scheduler,
            meeting_summarizer,
            document_manager,
            resource_allocator,
            milestone_tracker
        ],
        memory=self.memory_store
    )
