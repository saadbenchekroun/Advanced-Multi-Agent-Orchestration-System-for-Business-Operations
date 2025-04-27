"""
Advanced Multi-Agent Orchestration System for Business Operations

This system implements a comprehensive agent-based architecture for automating
business operations with robust error handling, monitoring, scheduling,
and integration with real-world business systems.
"""

import argparse
import logging
import os
import sys

from core.system import AgentSystem
from config_generator import generate_default_config

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