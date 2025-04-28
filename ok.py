"""
Advanced Multi-Agent Orchestration System for Business Operations

This system implements a comprehensive agent-based architecture for automating
business operations with robust error handling, monitoring, scheduling,
and integration with real-world business systems.
"""

import logging
import yaml
import json
import datetime
import time
import os
import argparse
import sys
import threading
import queue
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

import schedule
from google.adk.agents import Agent, SequentialAgent, LlmAgent, ParallelAgent
from tools import BrowserTool, calculate_reimbursement, search_knowledge_base
from google.adk.tools import FunctionTool
from google.adk.memory import MemoryStore, VectorMemory
from connectors import (
    CRMConnector, SlackConnector, GitHubConnector, 
    FigmaConnector, QuickBooksConnector, HubSpotConnector,
    JiraConnector, GoogleAnalyticsConnector
)

SearchTool = FunctionTool(func=search_knowledge_base)
CalculatorTool = FunctionTool(func=calculate_reimbursement)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("agent_system")

# Agent priority and state management
class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_HUMAN_INTERVENTION = "needs_human"

@dataclass
class Task:
    id: str
    description: str
    agent_name: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    dependencies: List[str] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3

class AgentSystem:
    """Main controller for the agent system orchestration"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the agent system with configuration"""
        self.config = self._load_config(config_path)
        self.task_queue = queue.PriorityQueue()
        self.completed_tasks = {}
        self.agents = {}
        self.connectors = {}
        self.memory_store = self._setup_memory()
        self._setup_connectors()
        self._setup_agents()
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=self.config.get("max_workers", 10))
        
    def _load_config(self, config_path: str) -> Dict:
        """Load system configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                logger.info(f"Configuration loaded from {config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Provide sensible defaults
            return {
                "api_keys": {},
                "agent_settings": {"default_model": "gemini-1.5-pro"},
                "max_workers": 5,
                "memory_settings": {"vector_db_path": "./vector_db"}
            }
    
    def _setup_memory(self) -> MemoryStore:
        """Setup the memory store for agents"""
        memory_config = self.config.get("memory_settings", {})
        return VectorMemory(
            path=memory_config.get("vector_db_path", "./vector_db"),
            dimension=memory_config.get("dimension", 1536)
        )
    
    def _setup_connectors(self):
        """Initialize integration connectors based on configuration"""
        connector_config = self.config.get("connectors", {})
        api_keys = self.config.get("api_keys", {})
        
        # Setup available connectors based on configuration
        if "crm" in connector_config:
            self.connectors["crm"] = CRMConnector(
                api_key=api_keys.get("crm"),
                base_url=connector_config["crm"].get("base_url")
            )
        
        if "slack" in connector_config:
            self.connectors["slack"] = SlackConnector(
                api_key=api_keys.get("slack"),
                channels=connector_config["slack"].get("channels", [])
            )
            
        if "github" in connector_config:
            self.connectors["github"] = GitHubConnector(
                api_key=api_keys.get("github"),
                repositories=connector_config["github"].get("repositories", [])
            )
            
        if "figma" in connector_config:
            self.connectors["figma"] = FigmaConnector(
                api_key=api_keys.get("figma"),
                project_ids=connector_config["figma"].get("project_ids", [])
            )
            
        if "quickbooks" in connector_config:
            self.connectors["quickbooks"] = QuickBooksConnector(
                api_key=api_keys.get("quickbooks"),
                company_id=connector_config["quickbooks"].get("company_id")
            )
            
        if "jira" in connector_config:
            self.connectors["jira"] = JiraConnector(
                api_key=api_keys.get("jira"),
                base_url=connector_config["jira"].get("base_url"),
                project_keys=connector_config["jira"].get("project_keys", [])
            )
            
        if "analytics" in connector_config:
            self.connectors["analytics"] = GoogleAnalyticsConnector(
                api_key=api_keys.get("analytics"),
                view_id=connector_config["analytics"].get("view_id")
            )
            
        logger.info(f"Initialized {len(self.connectors)} connectors: {list(self.connectors.keys())}")
    
    def _create_tool_set(self, tool_names: List[str]) -> List[Any]:
        """Create a set of tools for an agent based on tool names"""
        tools = []
        for tool in tool_names:
            if tool == "browser":
                tools.append(BrowserTool())
            elif tool == "search":
                tools.append(SearchTool)
            elif tool == "calculator":
                tools.append(CalculatorTool())
        return tools
            
    def _setup_agents(self):
        """Initialize all agents defined in the configuration"""
        default_model = self.config.get("agent_settings", {}).get("default_model", "gemini-1.5-flash")
        
        # 1. Customer Support Agent with advanced capabilities
        self.agents["customer_support"] = self._create_customer_support_agent(default_model)
        
        # 2. Sales/Lead Gen Agent
        self.agents["sales"] = self._create_sales_agent(default_model)
        
        # 3. Development Agent
        self.agents["development"] = self._create_development_agent(default_model)
        
        # 4. Marketing Agent
        self.agents["marketing"] = self._create_marketing_agent(default_model)
        
        # 5. Admin/Project Management Agent
        self.agents["admin"] = self._create_admin_agent(default_model)
        
        # 6. Design/UX Agent
        self.agents["design"] = self._create_design_agent(default_model)
        
        # 7. Finance Agent
        self.agents["finance"] = self._create_finance_agent(default_model)
        
        # 8. Top-level Orchestrator Agent (Meta-Agent)
        self.agents["orchestrator"] = self._create_orchestrator_agent(default_model)
        
        logger.info(f"Initialized {len(self.agents)} agent systems")
    
    def _create_customer_support_agent(self, default_model: str) -> SequentialAgent:
        """Create an advanced customer support agent with sentiment analysis and ticket routing"""
        sentiment_analyzer = LlmAgent(
            name="SentimentAnalyzer",
            model=self.config.get("agent_settings", {}).get("sentiment_model", default_model),
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
            model=self.config.get("agent_settings", {}).get("response_model", "gemini-1.5-pro"),
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
            memory=self.memory_store
        )
    
    def _create_sales_agent(self, default_model: str) -> SequentialAgent:
        """Create an advanced sales agent with lead qualification and pipeline management"""
        lead_finder = LlmAgent(
            name="LeadFinder",
            model=default_model,
            instruction="""
            Search CRM for potential leads based on:
            1. Recent website visitors who spent >2 minutes on pricing pages
            2. Existing customers approaching renewal dates
            3. Contacts who downloaded resources but haven't been contacted
            4. Participants from recent webinars or events
            
            For each lead, calculate a lead score (1-100) based on engagement signals.
            """,
            tools=[SearchTool]
        )
        
        lead_qualifier = LlmAgent(
            name="LeadQualifier",
            model=self.config.get("agent_settings", {}).get("qualifier_model", "gemini-1.5-pro"),
            instruction="""
            Assess lead quality using BANT criteria:
            - Budget: Financial capacity to purchase
            - Authority: Decision-making power
            - Need: Clear problem our solution addresses
            - Timeline: Purchasing timeline
            
            Assign qualification status: Cold, Warm, Hot, or Sales-Ready.
            Include specific next actions for each lead.
            """
        )
        
        email_composer = LlmAgent(
            name="EmailComposer",
            model=self.config.get("agent_settings", {}).get("composer_model", "gemini-1.5-pro"),
            instruction="""
            Craft personalized outreach emails based on:
            1. Lead's industry and role
            2. Previous interactions
            3. Specific pain points identified
            4. Recent company news or developments
            
            Emails should be concise, include a clear value proposition, and one specific call-to-action.
            """
        )
        
        follow_up_scheduler = LlmAgent(
            name="FollowUpScheduler",
            model=default_model,
            instruction="""
            Create a strategic follow-up sequence based on:
            1. Lead qualification status
            2. Previous response rates
            3. Optimal contact timing
            
            Schedule follow-ups in CRM with specific talking points for each interaction.
            """
        )
        
        crm_updater = LlmAgent(
            name="CRMUpdater",
            model=default_model,
            instruction="""
            Log all lead interactions in CRM with:
            1. Interaction summary
            2. Updated qualification status
            3. Next steps and action items
            4. Updated probability percentages
            5. Relevant notes for sales team
            """
        )
        
        return SequentialAgent(
            name="SalesAgent",
            sub_agents=[
                lead_finder,
                lead_qualifier,
                email_composer,
                follow_up_scheduler,
                crm_updater
            ],
            memory=self.memory_store
        )
    
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
    
    def _create_marketing_agent(self, default_model: str) -> SequentialAgent:
        """Create a marketing agent with content creation and analytics capabilities"""
        audience_analyzer = LlmAgent(
            name="AudienceAnalyzer",
            model=self.config.get("agent_settings", {}).get("analytics_model", "gemini-1.5-pro"),
            instruction="""
            Analyze audience metrics from:
            1. Website analytics (traffic sources, behavior patterns)
            2. Social media engagement (post performance by type/topic)
            3. Email campaign data (open rates, click-through, conversions)
            4. Customer survey feedback
            
            Identify top-performing content types, topics, and formats by segment.
            """,
            tools=[SearchTool]
        )
        
        content_planner = LlmAgent(
            name="ContentPlanner",
            model=self.config.get("agent_settings", {}).get("content_model", "gemini-1.5-pro"),
            instruction="""
            Develop content calendar based on:
            1. Audience analysis insights
            2. Product roadmap and release schedule
            3. Seasonal trends and industry events
            4. Content gaps and opportunities
            
            Create a balanced mix of educational, promotional, and engagement content.
            Align content with buyer journey stages and persona needs.
            """
        )
        
        content_writer = LlmAgent(
            name="ContentWriter",
            model=self.config.get("agent_settings", {}).get("writer_model", "gemini-1.5-pro"),
            instruction="""
            Generate high-quality, engaging content:
            1. Blog posts with original insights and research
            2. Social media posts optimized for each platform
            3. Email newsletters with personalized segments
            4. Landing page copy focused on conversion
            
            Maintain consistent brand voice while adapting to channel and audience.
            Include SEO optimization for relevant content.
            """,
            tools=[SearchTool]
        )
        
        content_optimizer = LlmAgent(
            name="ContentOptimizer",
            model=default_model,
            instruction="""
            Analyze and optimize content for:
            1. SEO performance (keyword usage, structure, metadata)
            2. Readability scores and comprehension level
            3. Engagement potential (emotional triggers, CTAs)
            4. Brand voice consistency
            
            Provide specific optimization recommendations with before/after examples.
            """
        )
        
        scheduler = LlmAgent(
            name="ContentScheduler",
            model=default_model,
            instruction="""
            Schedule content publication based on:
            1. Optimal posting times for each platform
            2. Content sequencing and campaign flow
            3. Competitive posting patterns
            4. Audience availability patterns
            
            Avoid scheduling conflicts and maintain consistent cadence.
            """
        )
        
        campaign_analyzer = LlmAgent(
            name="CampaignAnalyzer",
            model=self.config.get("agent_settings", {}).get("campaign_model", "gemini-1.5-pro"),
            instruction="""
            Analyze marketing campaign performance:
            1. Key metrics vs. benchmarks and goals
            2. Channel performance comparison
            3. Conversion funnel analysis
            4. ROI and cost per acquisition
            
            Identify optimization opportunities and success factors.
            """
        )
        
        return SequentialAgent(
            name="MarketingAgent",
            sub_agents=[
                audience_analyzer,
                content_planner,
                content_writer,
                content_optimizer,
                scheduler,
                campaign_analyzer
            ],
            memory=self.memory_store
        )
    
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
    
    def _create_finance_agent(self, default_model: str) -> SequentialAgent:
        """Create a finance agent with accounting and financial analysis capabilities"""
        invoice_generator = LlmAgent(
            name="InvoiceGenerator",
            model=default_model,
            instruction="""
            Create and send invoices:
            1. Generate accurate invoices from contract terms
            2. Apply proper tax rates and discounts
            3. Include all required legal and payment information
            4. Send invoices with appropriate cover messages
            
            Maintain invoice numbering system and filing structure.
            """
        )
        
        payment_tracker = LlmAgent(
            name="PaymentTracker",
            model=default_model,
            instruction="""
            Track payment status:
            1. Monitor incoming payments against invoices
            2. Flag overdue accounts with aging breakdowns
            3. Generate payment reminder sequences
            4. Reconcile payments with invoices
            
            Prepare weekly accounts receivable reports.
            """
        )
        
        expense_processor = LlmAgent(
            name="ExpenseProcessor",
            model=default_model,
            instruction="""
            Process expense reports and receipts:
            1. Extract and categorize expense information
            2. Verify compliance with expense policies
            3. Flag unusual or potentially unauthorized expenses
            4. Calculate reimbursement amounts
            
            Process expenses within 48 hours of submission.
            """,
            tools=[CalculatorTool()]
        )
        
        cash_flow_monitor = LlmAgent(
            name="CashFlowMonitor",
            model=self.config.get("agent_settings", {}).get("financial_model", "gemini-1.5-pro"),
            instruction="""
            Monitor cash flow metrics:
            1. Track actual vs. projected cash position
            2. Create 30/60/90 day cash forecasts
            3. Identify cash flow constraints and risks
            4. Model impacts of payment timing scenarios
            
            Generate cash flow alerts when thresholds are triggered.
            """,
            tools=[CalculatorTool()]
        )
        
        financial_reporter = LlmAgent(
            name="FinancialReporter",
            model=self.config.get("agent_settings", {}).get("reporting_model", "gemini-1.5-pro"),
            instruction="""
            Generate financial reports:
            1. P&L statements with variance analysis
            2. Balance sheet and key ratio calculations
            3. Department-level budget vs. actual comparisons
            4. Customer and product profitability analysis
            
            Include executive summaries highlighting key insights.
            """,
            tools=[CalculatorTool()]
        )
        
        integration_manager = LlmAgent(
            name="IntegrationManager",
            model=default_model,
            instruction="""
            Manage financial system integrations:
            1. Synchronize data between accounting systems
            2. Reconcile discrepancies between platforms
            3. Validate data integrity across systems
            4. Update integration mappings when chart of accounts changes
            
            Maintain audit trails of all system synchronizations.
            """
        )
        
        return SequentialAgent(
            name="FinanceAgent",
            sub_agents=[
                invoice_generator,
                payment_tracker,
                expense_processor,
                cash_flow_monitor,
                financial_reporter,
                integration_manager
            ],
            memory=self.memory_store
        )
    
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
    
    def add_task(self, task: Task):
        """Add a task to the priority queue"""
        # Queue items are (priority, count, task) - count used as tiebreaker for equal priorities
        count = time.monotonic()
        self.task_queue.put((task.priority.value, count, task))
        logger.info(f"Task added: {task.id} - {task.description} (Priority: {task.priority.name})")
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next task from the priority queue"""
        try:
            if not self.task_queue.empty():
                _, _, task = self.task_queue.get(block=False)
                return task
            return None
        except queue.Empty:
            return None
    
    def process_task(self, task: Task):
        """Process a single task using the appropriate agent"""
        try:
            # Check if all dependencies are completed
            for dep_id in task.dependencies:
                if dep_id not in self.completed_tasks or self.completed_tasks[dep_id].status != TaskStatus.COMPLETED:
                    logger.info(f"Task {task.id} waiting for dependency {dep_id}")
                    # Re-queue with a delay
                    task.retries += 1
                    self.add_task(task)
                    return
            
            logger.info(f"Processing task: {task.id} - {task.description}")
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.datetime.now()
            
            # Get the appropriate agent
            agent = self.agents.get(task.agent_name)
            if not agent:
                raise ValueError(f"No agent found with name: {task.agent_name}")
            
            # Execute the task
            context = agent.invoke(task.description)
            
            # Update task with result
            task.result = context.state
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.datetime.now()
            self.completed_tasks[task.id] = task
            
            logger.info(f"Task completed: {task.id}")
            return task
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.updated_at = datetime.datetime.now()
            logger.error(f"Task failed: {task.id} - {e}")
            
            # Retry logic for failed tasks
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.PENDING
                logger.info(f"Requeuing task: {task.id} (Attempt {task.retries}/{task.max_retries})")
                self.add_task(task)
            else:
                # If max retries reached, mark for human intervention
                task.status = TaskStatus.NEEDS_HUMAN_INTERVENTION
                logger.warning(f"Task {task.id} requires human intervention after {task.retries} failed attempts")
                
            return task
    
    def start(self):
        """Start the agent system and process tasks"""
        if self.running:
            logger.warning("Agent system is already running")
            return
        
        self.running = True
        logger.info("Agent system started")
        
        # Start a separate thread for scheduling
        threading.Thread(target=self._run_scheduler, daemon=True).start()
        
        try:
            while self.running:
                task = self.get_next_task()
                if task:
                    # Process task in thread pool
                    self.executor.submit(self.process_task, task)
                else:
                    # If no tasks, sleep briefly to avoid CPU spinning
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            logger.info("Agent system interrupted")
            self.stop()
        except Exception as e:
            logger.error(f"Agent system error: {e}")
            self.stop()
    
    def _run_scheduler(self):
        """Run the scheduler for periodic tasks"""
        # Set up daily jobs
        schedule.every().day.at("08:00").do(self._morning_routine)
        schedule.every().day.at("17:00").do(self._evening_routine)
        
        # Set up hourly jobs
        schedule.every().hour.do(self._hourly_check)
        
        # Set up weekly jobs
        schedule.every().monday.at("09:00").do(self._weekly_planning)
        schedule.every().friday.at("16:00").do(self._weekly_review)
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def _morning_routine(self):
        """Morning routine tasks"""
        # Add various morning tasks to the queue
        self.add_task(Task(
            id=f"morning-review-{datetime.date.today()}",
            description="Review overnight customer support tickets and prioritize responses",
            agent_name="customer_support",
            priority=TaskPriority.HIGH
        ))
        
        self.add_task(Task(
            id=f"daily-standup-{datetime.date.today()}",
            description="Prepare daily standup agenda and project status updates",
            agent_name="admin",
            priority=TaskPriority.MEDIUM
        ))
        
        self.add_task(Task(
            id=f"social-content-{datetime.date.today()}",
            description="Schedule today's social media posts based on content calendar",
            agent_name="marketing",
            priority=TaskPriority.MEDIUM
        ))
    
    def _evening_routine(self):
        """Evening routine tasks"""
        self.add_task(Task(
            id=f"daily-summary-{datetime.date.today()}",
            description="Generate end-of-day summary report for all departments",
            agent_name="orchestrator",
            priority=TaskPriority.MEDIUM
        ))
        
        self.add_task(Task(
            id=f"cash-position-{datetime.date.today()}",
            description="Update daily cash position and next-day forecast",
            agent_name="finance",
            priority=TaskPriority.MEDIUM
        ))
    
    def _hourly_check(self):
        """Hourly check tasks"""
        # Check for new tickets
        self.add_task(Task(
            id=f"support-check-{datetime.datetime.now().strftime('%Y%m%d-%H')}",
            description="Check for new high-priority support tickets",
            agent_name="customer_support",
            priority=TaskPriority.HIGH
        ))
        
        # Check development progress
        self.add_task(Task(
            id=f"dev-check-{datetime.datetime.now().strftime('%Y%m%d-%H')}",
            description="Check for blocked development tasks and PR status",
            agent_name="development",
            priority=TaskPriority.MEDIUM
        ))
    
    def _weekly_planning(self):
        """Weekly planning tasks"""
        self.add_task(Task(
            id=f"sprint-planning-{datetime.date.today()}",
            description="Prepare sprint planning materials and resource allocations",
            agent_name="development",
            priority=TaskPriority.HIGH
        ))
        
        self.add_task(Task(
            id=f"content-planning-{datetime.date.today()}",
            description="Plan next week's content calendar and marketing activities",
            agent_name="marketing",
            priority=TaskPriority.MEDIUM
        ))
        
        self.add_task(Task(
            id=f"cash-forecast-{datetime.date.today()}",
            description="Generate weekly cash flow forecast and payment schedule",
            agent_name="finance",
            priority=TaskPriority.HIGH
        ))
    
    def _weekly_review(self):
        """Weekly review tasks"""
        self.add_task(Task(
            id=f"week-review-{datetime.date.today()}",
            description="Generate weekly performance report across all departments",
            agent_name="orchestrator",
            priority=TaskPriority.HIGH
        ))
        
        self.add_task(Task(
            id=f"marketing-metrics-{datetime.date.today()}",
            description="Analyze weekly marketing metrics and campaign performance",
            agent_name="marketing",
            priority=TaskPriority.MEDIUM
        ))
    
    def stop(self):
        """Stop the agent system"""
        logger.info("Stopping agent system")
        self.running = False
        self.executor.shutdown(wait=False)
        logger.info("Agent system stopped")
    
    def get_system_status(self) -> Dict:
        """Get the current status of the agent system"""
        pending_tasks = self.task_queue.qsize()
        completed_tasks = len([t for t in self.completed_tasks.values() if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.completed_tasks.values() if t.status == TaskStatus.FAILED])
        needs_intervention = len([t for t in self.completed_tasks.values() if t.status == TaskStatus.NEEDS_HUMAN_INTERVENTION])
        
        return {
            "status": "running" if self.running else "stopped",
            "tasks": {
                "pending": pending_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "needs_intervention": needs_intervention
            },
            "agents": list(self.agents.keys()),
            "connectors": list(self.connectors.keys()),
            "uptime": datetime.datetime.now().timestamp() - self.start_time.timestamp() if hasattr(self, 'start_time') else 0
        }
    
    def get_agent_performance(self, agent_name: str) -> Dict:
        """Get performance metrics for a specific agent"""
        if agent_name not in self.agents:
            raise ValueError(f"No agent found with name: {agent_name}")
            
        agent_tasks = [t for t in self.completed_tasks.values() if t.agent_name == agent_name]
        completed = [t for t in agent_tasks if t.status == TaskStatus.COMPLETED]
        failed = [t for t in agent_tasks if t.status == TaskStatus.FAILED]
        
        # Calculate average processing time for completed tasks
        if completed:
            avg_time = sum((t.updated_at - t.created_at).total_seconds() for t in completed) / len(completed)
        else:
            avg_time = 0
            
        return {
            "agent_name": agent_name,
            "total_tasks": len(agent_tasks),
            "completed_tasks": len(completed),
            "failed_tasks": len(failed),
            "success_rate": len(completed) / len(agent_tasks) if agent_tasks else 0,
            "average_processing_time": avg_time
        }

class AgentSystemCLI:
    """Command-line interface for the agent system"""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.agent_system = None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the command-line argument parser"""
        parser = argparse.ArgumentParser(description="Agent System CLI")
        parser.add_argument("--config", type=str, default="config.yaml", help="Path to configuration file")
        
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")
        
        # Start command
        start_parser = subparsers.add_parser("start", help="Start the agent system")
        start_parser.add_argument("--daemon", action="store_true", help="Run as daemon")
        
        # Stop command
        subparsers.add_parser("stop", help="Stop the agent system")
        
        # Status command
        subparsers.add_parser("status", help="Get agent system status")
        
        # Add task command
        add_task_parser = subparsers.add_parser("add-task", help="Add a task to the system")
        add_task_parser.add_argument("--id", type=str, required=True, help="Task ID")
        add_task_parser.add_argument("--description", type=str, required=True, help="Task description")
        add_task_parser.add_argument("--agent", type=str, required=True, help="Agent name")
        add_task_parser.add_argument("--priority", type=str, default="MEDIUM", 
                                    choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"], 
                                    help="Task priority")
        
        # List tasks command
        list_tasks_parser = subparsers.add_parser("list-tasks", help="List tasks")
        list_tasks_parser.add_argument("--status", type=str, 
                                      choices=["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "NEEDS_HUMAN"],
                                      help="Filter by task status")
        
        # Performance command
        perf_parser = subparsers.add_parser("performance", help="Get agent performance metrics")
        perf_parser.add_argument("--agent", type=str, help="Agent name")
        
        return parser
    
    def run(self):
        """Run the CLI"""
        args = self.parser.parse_args()
        
        if args.command == "start":
            self._start_command(args)
        elif args.command == "stop":
            self._stop_command()
        elif args.command == "status":
            self._status_command()
        elif args.command == "add-task":
            self._add_task_command(args)
        elif args.command == "list-tasks":
            self._list_tasks_command(args)
        elif args.command == "performance":
            self._performance_command(args)
        else:
            self.parser.print_help()
    
    def _start_command(self, args):
        """Start the agent system"""
        try:
            self.agent_system = AgentSystem(config_path=args.config)
            print(f"Starting agent system with config: {args.config}")
            
            if args.daemon:
                # Run in background
                pid = os.fork()
                if pid > 0:
                    # Exit parent process
                    print(f"Agent system started in background (PID: {pid})")
                    sys.exit(0)
                    
                # Detach from terminal
                os.setsid()
                os.umask(0)
                
                # Redirect standard file descriptors
                sys.stdout.flush()
                sys.stderr.flush()
                
                with open('/dev/null', 'r') as f:
                    os.dup2(f.fileno(), sys.stdin.fileno())
                with open('agent_system.log', 'a') as f:
                    os.dup2(f.fileno(), sys.stdout.fileno())
                    os.dup2(f.fileno(), sys.stderr.fileno())
                    
                # Store PID for later use
                with open('agent_system.pid', 'w') as f:
                    f.write(str(os.getpid()))
            
            # Start the system
            self.agent_system.start()
            
        except Exception as e:
            print(f"Error starting agent system: {e}")
            sys.exit(1)
    
    def _stop_command(self):
        """Stop the agent system"""
        try:
            # Try to read PID file
            try:
                with open('agent_system.pid', 'r') as f:
                    pid = int(f.read().strip())
                    
                # Send SIGTERM to the process
                os.kill(pid, signal.SIGTERM)
                print(f"Sent stop signal to agent system (PID: {pid})")
                
                # Remove PID file
                os.remove('agent_system.pid')
                
            except FileNotFoundError:
                print("No running agent system found")
                
        except Exception as e:
            print(f"Error stopping agent system: {e}")
            sys.exit(1)
    
    def _status_command(self):
        """Get agent system status"""
        try:
            # Check if PID file exists
            try:
                with open('agent_system.pid', 'r') as f:
                    pid = int(f.read().strip())
                    
                    # Check if process is running
                    try:
                        os.kill(pid, 0)  # Signal 0 doesn't actually send a signal
                        print(f"Agent system is running (PID: {pid})")
                    except OSError:
                        print("Agent system is not running (stale PID file)")
                        os.remove('agent_system.pid')
                        
            except FileNotFoundError:
                print("Agent system is not running")
                
        except Exception as e:
            print(f"Error checking agent system status: {e}")
            sys.exit(1)
    
    def _add_task_command(self, args):
        """Add a task to the system"""
        try:
            # Create a task descriptor file
            task = {
                "id": args.id,
                "description": args.description,
                "agent_name": args.agent,
                "priority": args.priority,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Write to tasks directory
            os.makedirs("tasks/pending", exist_ok=True)
            with open(f"tasks/pending/{args.id}.json", 'w') as f:
                json.dump(task, f, indent=2)
                
            print(f"Task added: {args.id}")
            
        except Exception as e:
            print(f"Error adding task: {e}")
            sys.exit(1)
    
    def _list_tasks_command(self, args):
        """List tasks"""
        try:
            tasks = []
            
            # Check all task directories
            for status in ["pending", "in_progress", "completed", "failed", "needs_human"]:
                if args.status and status != args.status.lower():
                    continue
                    
                dir_path = f"tasks/{status}"
                if os.path.exists(dir_path):
                    for file in os.listdir(dir_path):
                        if file.endswith(".json"):
                            with open(os.path.join(dir_path, file), 'r') as f:
                                task = json.load(f)
                                task["status"] = status.upper()
                                tasks.append(task)
            
            # Print tasks
            if tasks:
                print(f"Found {len(tasks)} tasks:")
                for task in tasks:
                    print(f"ID: {task['id']}")
                    print(f"  Description: {task['description']}")
                    print(f"  Agent: {task['agent_name']}")
                    print(f"  Priority: {task['priority']}")
                    print(f"  Status: {task['status']}")
                    print(f"  Created: {task['created_at']}")
                    print()
            else:
                print("No tasks found")
                
        except Exception as e:
            print(f"Error listing tasks: {e}")
            sys.exit(1)
    
    def _performance_command(self, args):
        """Get agent performance metrics"""
        try:
            # Read performance data from logs
            performance = {
                "system": {
                    "tasks_processed": 0,
                    "success_rate": 0,
                    "avg_processing_time": 0
                },
                "agents": {}
            }
            
            # Parse log file to extract performance metrics
            agent_completions = {}
            agent_failures = {}
            agent_times = {}
            
            with open("agent_system.log", 'r') as f:
                for line in f:
                    if "Task completed" in line:
                        task_id = line.split("Task completed: ")[1].strip()
                        agent = task_id.split("-")[0]
                        
                        if agent not in agent_completions:
                            agent_completions[agent] = 0
                        agent_completions[agent] += 1
                        
                    elif "Task failed" in line:
                        task_id = line.split("Task failed: ")[1].split(" -")[0].strip()
                        agent = task_id.split("-")[0]
                        
                        if agent not in agent_failures:
                            agent_failures[agent] = 0
                        agent_failures[agent] += 1
            
            # Calculate performance metrics
            for agent in set(list(agent_completions.keys()) + list(agent_failures.keys())):
                completions = agent_completions.get(agent, 0)
                failures = agent_failures.get(agent, 0)
                total = completions + failures
                
                if total > 0:
                    performance["agents"][agent] = {
                        "tasks_total": total,
                        "tasks_completed": completions,
                        "tasks_failed": failures,
                        "success_rate": completions / total
                    }
            
            # Filter by agent if specified
            if args.agent:
                if args.agent in performance["agents"]:
                    print(f"Performance for agent '{args.agent}':")
                    agent_perf = performance["agents"][args.agent]
                    print(f"  Total tasks: {agent_perf['tasks_total']}")
                    print(f"  Completed: {agent_perf['tasks_completed']}")
                    print(f"  Failed: {agent_perf['tasks_failed']}")
                    print(f"  Success rate: {agent_perf['success_rate']:.2%}")
                else:
                    print(f"No performance data found for agent '{args.agent}'")
            else:
                # Print overall system performance
                total_tasks = sum(a["tasks_total"] for a in performance["agents"].values())
                total_completed = sum(a["tasks_completed"] for a in performance["agents"].values())
                
                print("System performance:")
                print(f"  Total tasks processed: {total_tasks}")
                print(f"  Success rate: {total_completed / total_tasks:.2%}" if total_tasks > 0 else "  Success rate: N/A")
                print("\nAgent performance:")
                
                for agent, metrics in performance["agents"].items():
                    print(f"  {agent}:")
                    print(f"    Tasks: {metrics['tasks_total']}")
                    print(f"    Success rate: {metrics['success_rate']:.2%}")
                
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
            sys.exit(1)

# Example implementation of a configuration file generator
def generate_default_config(output_path="config.yaml"):
    """Generate a default configuration file"""
    config = {
        "api_keys": {
            "search": "YOUR_SEARCH_API_KEY",
            "crm": "YOUR_CRM_API_KEY",
            "slack": "YOUR_SLACK_API_KEY",
            "github": "YOUR_GITHUB_API_KEY",
            "figma": "YOUR_FIGMA_API_KEY",
            "quickbooks": "YOUR_QUICKBOOKS_API_KEY",
            "jira": "YOUR_JIRA_API_KEY",
            "analytics": "YOUR_ANALYTICS_API_KEY"
        },
        "agent_settings": {
            "default_model": "gemini-1.5-flash",
            "code_model": "gemini-1.5-pro",
            "response_model": "gemini-1.5-pro",
            "content_model": "gemini-1.5-pro",
            "analytics_model": "gemini-1.5-pro",
            "financial_model": "gemini-1.5-pro",
            "prioritizer_model": "gemini-1.5-pro"
        },
        "memory_settings": {
            "vector_db_path": "./vector_db",
            "dimension": 1536
        },
        "max_workers": 10,
        "connectors": {
            "crm": {
                "base_url": "https://api.crm.example.com/v1",
                "sync_interval": 3600
            },
            "slack": {
                "channels": ["general", "support", "sales", "engineering"]
            },
            "github": {
                "repositories": ["main-app", "backend", "frontend", "mobile"]
            },
            "jira": {
                "base_url": "https://your-company.atlassian.net",
                "project_keys": ["PROJ", "SUPP", "DEV"]
            },
            "quickbooks": {
                "company_id": "YOUR_COMPANY_ID"
            }
        },
        "scheduling": {
            "daily_start": "08:00",
            "daily_end": "18:00",
            "weekend_monitoring": False
        }
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"Default configuration generated at {output_path}")

# Entry point for the system
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Agent Orchestration System")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to configuration file")
    parser.add_argument("--generate-config", action="store_true", help="Generate default configuration file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger("agent_system").setLevel(logging.DEBUG)
    
    # Generate default config if requested
    if args.generate_config:
        generate_default_config(args.config)
        sys.exit(0)
    
    # Check if config exists
    if not os.path.exists(args.config):
        print(f"Configuration file not found: {args.config}")
        print("Run with --generate-config to create a default configuration")
        sys.exit(1)
    
    try:
        # Initialize the agent system
        agent_system = AgentSystem(config_path=args.config)
        
        # Record start time
        agent_system.start_time = datetime.datetime.now()
        
        # Print basic system info
        print(f"Agent System Initialized")
        print(f"Agents: {', '.join(agent_system.agents.keys())}")
        print(f"Connectors: {', '.join(agent_system.connectors.keys())}")
        print("Starting system...")
        
        # Start the system
        agent_system.start()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        if 'agent_system' in locals():
            agent_system.stop()
    except Exception as e:
        print(f"Error: {e}")
        if logging.getLogger("agent_system").level <= logging.DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)