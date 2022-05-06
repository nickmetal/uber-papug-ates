from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from django.db import models
from snowflake import SnowflakeGenerator


@dataclass
class BaseEntity:
    """Base class for domain entity"""
    id: int  # snowflake id
    created_at: datetime
    updated_at: datetime


class TaskStatus(Enum):
    NEW = "new"
    COMPLETED = "completed"


@dataclass
class TaskDTO(BaseEntity):
    title: str
    description: str
    status: TaskStatus
    assignee: int  # foreing key to  account_domain.Employee.id
    fee: Decimal


def get_id(id_generator=SnowflakeGenerator(42)) -> int:
    return next(id_generator)

    
class BaseModel(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False, default=get_id)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Task(BaseModel):
    title = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    status = models.CharField(choices=[(item.value, item.value) for item in TaskStatus], max_length=100)
    assignee = models.BigIntegerField()
    fee = models.DecimalField(max_digits=15, decimal_places=10)
