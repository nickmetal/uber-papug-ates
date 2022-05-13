from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from django.db import models
from snowflake import SnowflakeGenerator
from django.contrib.auth.models import User


@dataclass
class BaseEntity:
    """Base class for domain entity"""

    id: int  # snowflake id
    created_at: datetime
    updated_at: datetime


class TaskTrackerUser(User):
    public_id = models.CharField(max_length=250)
    role = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TaskStatus(Enum):
    NEW = "new"
    COMPLETED = "completed"


@dataclass
class TaskDTO(BaseEntity):
    title: str
    description: str
    status: TaskStatus
    assignee: str  # foreing key to  account_domain.Employee.id
    fee_on_assign: Decimal
    fee_on_complete: Decimal
    jira_id: field(
        default=None
    )  # made it optional for tasks instanses without jira_id, might me removed after proper migration

    def __post_init__(self):
        if all(char in self.title for char in "[]"):
            raise ValueError("Field 'title' cannot contain jira id.")


def get_id(id_generator=SnowflakeGenerator(42)) -> int:
    return next(id_generator)


class BaseModel(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False, default=get_id)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Task(BaseModel):
    title = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    status = models.CharField(choices=[(item.value, item.value) for item in TaskStatus], max_length=100)
    assignee = models.ForeignKey(TaskTrackerUser, on_delete=models.CASCADE)
    fee_on_assign = models.DecimalField(max_digits=15, decimal_places=10)
    fee_on_complete = models.DecimalField(max_digits=15, decimal_places=10)
    jira_id = models.CharField(max_length=100, blank=True)
