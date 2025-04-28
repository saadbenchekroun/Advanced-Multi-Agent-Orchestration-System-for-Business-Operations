from google.adk.agents import LlmAgent, SequentialAgent
from tools import BrowserTool, search_knowledge_base
from google.adk.tools import FunctionTool

SearchTool = FunctionTool(func=search_knowledge_base)

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
