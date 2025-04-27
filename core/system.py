"""Main controller for the agent orchestration system"""

import datetime
import logging
import queue
import threading
import time
import yaml
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import schedule

from core.task import Task, TaskPriority, TaskStatus
from core.memory import setup_memory
from agents.customer_support import create_customer_support_agent
from agents.sales import create_sales_agent
from agents.development import create_development_agent
from agents.marketing import create_marketing_agent
from agents.admin import create_admin_agent
from agents.design import create_design_agent
from agents.finance import create_finance_agent
from agents.orchestrator import create_orchestrator_agent
from connectors import setup_connectors

logger = logging.getLogger("agent_system")

class AgentSystem:
    """Main controller for the agent system orchestration"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the agent system with configuration"""
        self.config = self._load_config(config_path)
        self.task_queue = queue.PriorityQueue()
        self.completed_tasks = {}
        self.agents = {}
        self.connectors = {}
        self.memory_store = setup_memory(self.config)
        self.connectors = setup_connectors(self.config)
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
            
    def _setup_agents(self):
        """Initialize all agents defined in the configuration"""
        default_model = self.config.get("agent_settings", {}).get("default_model", "gemini-1.5-flash")
        
        # Initialize all specialized agents
        self.agents["customer_support"] = create_customer_support_agent(default_model, self.config, self.memory_store)
        self.agents["sales"] = create_sales_agent(default_model, self.config, self.memory_store)
        self.agents["development"] = create_development_agent(default_model, self.config, self.memory_store)
        self.agents["marketing"] = create_marketing_agent(default_model, self.config, self.memory_store)
        self.agents["admin"] = create_admin_agent(default_model, self.config, self.memory_store)
        self.agents["design"] = create_design_agent(default_model, self.config, self.memory_store)
        self.agents["finance"] = create_finance_agent(default_model, self.config, self.memory_store)
        self.agents["orchestrator"] = create_orchestrator_agent(default_model, self.config, self.memory_store)
        
        logger.info(f"Initialized {len(self.agents)} agent systems")
    
    # ...rest of the AgentSystem class methods for task management and scheduling