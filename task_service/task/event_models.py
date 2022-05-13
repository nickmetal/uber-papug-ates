from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import Dict
from uuid import uuid4
from task.models import TaskDTO


logger = logging.getLogger(__name__)


@dataclass
class TaskServiceCUDEvent:
    """Base CUD model for current service"""
    data: Dict
    id: uuid4 = field(default_factory=uuid4)
    version: int = field(default=1)
    event_name: str = field(default="<not_set>")  # <not_set> is dataclass issue, implementation workaround
    producer: str = field(default="<not_set>")  # <not_set> is dataclass issue, implementation workaround
    event_time: datetime = field(default_factory=datetime.utcnow)
    producer: str = field(default="task_service")
    

@dataclass
class TaskCreatedEvent(TaskServiceCUDEvent):
    data: TaskDTO
    event_name: str = field(default="task_created")
    version: int = 2


@dataclass
class TaskCompletedEvent(TaskServiceCUDEvent):
    data: dict
    """data:
    {'id': id}
    """
    event_name: str = field(default="task_completed")


@dataclass
class TasksAssignedEvent(TaskServiceCUDEvent):
    data: dict
    """data:
    
    {"tasks": [{"id": 1, "assignee": "nick", "fee"}]}  # todo: update
    """
    event_name: str = field(default="tasks_assigned")