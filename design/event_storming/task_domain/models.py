from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


@dataclass
class BaseEntity:
    """Base class for domain entity"""
    id: int  # snowflake id
    created_at: datetime
    updated_at: datetime
    # incremental model version for forward and backward compatibility
    # version: int = field(default=1)


class TaskStatus(Enum):
    NEW = "new"
    COMPLETED = "completed"


@dataclass
class Task(BaseEntity):
    title: str
    description: str
    status: TaskStatus
    assignee: int  # foreing key to  account_domain.Employee.id
    fee: Decimal