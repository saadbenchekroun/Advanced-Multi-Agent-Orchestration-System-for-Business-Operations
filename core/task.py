"""Task management data structures for the agent system"""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

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
 