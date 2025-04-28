from google.adk.agents import LlmAgent, SequentialAgent
from tools import BrowserTool, search_knowledge_base
from google.adk.tools import FunctionTool

SearchTool = FunctionTool(func=search_knowledge_base)

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
