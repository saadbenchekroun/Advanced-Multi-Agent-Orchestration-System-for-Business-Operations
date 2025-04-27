"""Configuration generator for the agent system"""

import yaml

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