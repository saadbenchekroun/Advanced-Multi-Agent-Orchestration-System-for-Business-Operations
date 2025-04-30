"""Command-line interface for controlling the agent system"""

import argparse
import datetime
import json
import os
import signal
import sys

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

if __name__ == "__main__":
    cli = AgentSystemCLI()
    cli.run()