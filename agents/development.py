from google.adk.agents import LlmAgent, SequentialAgent
from tools import BrowserTool, search_knowledge_base
from google.adk.tools import FunctionTool

SearchTool = FunctionTool(func=search_knowledge_base)

def _create_development_agent(self, default_model: str) -> SequentialAgent:
        """Create a development agent with code review and project management capabilities"""
        code_reviewer = LlmAgent(
            name="CodeReviewer",
            model=self.config.get("agent_settings", {}).get("code_model", "gemini-1.5-pro"),
            instruction="""
            Review pull requests against the following criteria:
            1. Code quality and adherence to style guidelines
            2. Performance implications and optimization opportunities
            3. Security vulnerabilities and best practices
            4. Test coverage and quality
            5. Documentation completeness
            
            Provide specific, actionable feedback with code examples where applicable.
            Flag critical issues that should block merging.
            """,
            tools=[BrowserTool()]
        )
        
        task_allocator = LlmAgent(
            name="TaskAllocator",
            model=default_model,
            instruction="""
            Assign development tickets based on:
            1. Developer expertise and previous similar tasks
            2. Current workload and capacity
            3. Task dependencies and critical path
            4. Sprint goals and priorities
            
            Balance workload across team and maximize specialist utilization.
            """,
            tools=[SearchTool]
        )
        
        progress_analyzer = LlmAgent(
            name="ProgressAnalyzer",
            model=default_model,
            instruction="""
            Analyze sprint progress by:
            1. Comparing completed vs planned story points
            2. Identifying blocked or at-risk tasks
            3. Evaluating team velocity trends
            4. Flagging scope creep or requirement changes
            
            Generate daily progress reports with risk assessments and recommendations.
            """
        )
        
        technical_debt_monitor = LlmAgent(
            name="TechnicalDebtMonitor",
            model=self.config.get("agent_settings", {}).get("debt_model", "gemini-1.5-pro"),
            instruction="""
            Monitor codebase health metrics:
            1. Test coverage percentage
            2. Code duplication rates
            3. Complexity scores
            4. Documentation completeness
            5. Dependency currency
            
            Identify technical debt hotspots and propose remediation tasks.
            """
        )
        
        deadline_monitor = LlmAgent(
            name="DeadlineMonitor",
            model=default_model,
            instruction="""
            Track project milestones and deadlines:
            1. Calculate current completion percentage
            2. Project completion date based on velocity
            3. Identify critical path blockers
            4. Flag schedule risks with specific causes
            
            Recommend adjustments to meet deadlines when necessary.
            """
        )
        
        return SequentialAgent(
            name="DevAgent",
            sub_agents=[
                code_reviewer,
                task_allocator,
                progress_analyzer,
                technical_debt_monitor,
                deadline_monitor
            ],
            memory=self.memory_store
        )
 