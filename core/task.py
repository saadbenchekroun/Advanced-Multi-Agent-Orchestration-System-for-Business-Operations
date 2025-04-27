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