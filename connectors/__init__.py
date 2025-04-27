"""Integration connectors for external services"""

from typing import Dict
import logging

from connectors.crm import CRMConnector
from connectors.slack import SlackConnector
from connectors.github import GitHubConnector
from connectors.figma import FigmaConnector
from connectors.quickbooks import QuickBooksConnector
from connectors.jira import JiraConnector
from connectors.analytics import GoogleAnalyticsConnector

logger = logging.getLogger("agent_system")

def setup_connectors(config: Dict) -> Dict:
    """Initialize integration connectors based on configuration"""
    connectors = {}
    connector_config = config.get("connectors", {})
    api_keys = config.get("api_keys", {})
    
    # Setup available connectors based on configuration
    if "crm" in connector_config:
        connectors["crm"] = CRMConnector(
            api_key=api_keys.get("crm"),
            base_url=connector_config["crm"].get("base_url")
        )
    
    if "slack" in connector_config:
        connectors["slack"] = SlackConnector(
            api_key=api_keys.get("slack"),
            channels=connector_config["slack"].get("channels", [])
        )
        
    if "github" in connector_config:
        connectors["github"] = GitHubConnector(
            api_key=api_keys.get("github"),
            repositories=connector_config["github"].get("repositories", [])
        )
        
    if "figma" in connector_config:
        connectors["figma"] = FigmaConnector(
            api_key=api_keys.get("figma"),
            project_ids=connector_config["figma"].get("project_ids", [])
        )
        
    if "quickbooks" in connector_config:
        connectors["quickbooks"] = QuickBooksConnector(
            api_key=api_keys.get("quickbooks"),
            company_id=connector_config["quickbooks"].get("company_id")
        )
        
    if "jira" in connector_config:
        connectors["jira"] = JiraConnector(
            api_key=api_keys.get("jira"),
            base_url=connector_config["jira"].get("base_url"),
            project_keys=connector_config["jira"].get("project_keys", [])
        )
        
    if "analytics" in connector_config:
        connectors["analytics"] = GoogleAnalyticsConnector(
            api_key=api_keys.get("analytics"),
            view_id=connector_config["analytics"].get("view_id")
        )
        
    logger.info(f"Initialized {len(connectors)} connectors: {list(connectors.keys())}")
    return connectors