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