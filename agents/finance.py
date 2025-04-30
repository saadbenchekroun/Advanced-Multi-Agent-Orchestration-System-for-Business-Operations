from google.adk.agents import LlmAgent, SequentialAgent
from tools import BrowserTool, search_knowledge_base
from google.adk.tools import FunctionTool

SearchTool = FunctionTool(func=search_knowledge_base)

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