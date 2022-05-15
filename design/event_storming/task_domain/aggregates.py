from ast import Dict
from datetime import datetime
from dataclasses import dataclass

from enum import Enum
from typing import List


class Task:
    """the same as Task model from models.py file"""

class Tasks:
    """Collections of tasks from db"""
    tasks: List[Task] # from models.py file


@dataclass
class TaskTransactionLog:
    transaction: Dict  # cope of the recorn from account_domain.Transaction table
    task: Dict  # task content which belongs to transaction
  

class AuditLogType(Enum):
    TASK_TRANSACTION = 'task_transaction'
    DAILY_REVENUE_INCOME = 'daily_revenue_income' 
        
        
@dataclass
class BaseEntity:
    """Base class for domain entity"""
    id: int  # snowflake id
    created_at: datetime



@dataclass
class AuditLog(BaseEntity):
    """Record in timeseries Mongo collection"""
    type: AuditLogType
    payload: Dict  #specific audit log content, e.g. TaskTransactionLog.json() or DailyRevenueIncome.json()
    