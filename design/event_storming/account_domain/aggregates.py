from ast import Dict
from datetime import datetime
from dataclasses import dataclass

from enum import Enum


@dataclass
class BaseEntity:
    """Base class for domain entity"""
    id: int  # snowflake id
    created_at: datetime

    # incremental model version for forward and backward compatibility
    # version: int = field(default=1)


class AuditLogType(Enum):
    TASK_TRANSACTION = 'task_transaction'
    DAILY_REVENUE_INCOME = 'daily_revenue_income'
    
    
@dataclass
class DailyRevenueIncome:
    transaction: Dict  # cope of the recorn from account_domain.Transaction table
        

@dataclass
class AuditLog(BaseEntity):
    """Record in timeseries Mongo collection"""
    type: AuditLogType
    payload: Dict  #specific audit log content, e.g. TaskTransactionLog.json() or DailyRevenueIncome.json()
    