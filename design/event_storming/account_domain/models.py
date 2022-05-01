from datetime import datetime
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass
from dataclasses import field
from typing import List, Optional


@dataclass
class BaseEntity:
    """Base class for domain entity"""
    id: int  # snowflake id
    created_at: datetime
    updated_at: datetime
    # incremental model version for forward and backward compatibility
    # version: int = field(default=1)


"""Account Domain"""
class Role(Enum):
    ADMINISTRATOR = "administrator"
    ACCOUNTANT = "accountant"
    CEO = "ceo"
    DEVELOPER = "developer"
    MANAGER = "manager"


@dataclass
class Employee(BaseEntity):
    name: str
    email: str
    roles: List[Role]  # can be stored in db or injected from auth service


class TransactionType(Enum):
    INCOME = 'income'
    OUTCOME = 'outcome'


@dataclass
class Transaction(BaseEntity):
    type: TransactionType
    currency: field(default='US DOLLAR')
    amount: Decimal
    description: Optional[str]
    source_account_id: int
    target_account_id: int


@dataclass
class Account(BaseEntity):
    """Do sum on transactions array to get current state of account"""
    employee_id: int  # key to Employee.id
    transactions = List[int]  # list of transaction ids belong to current account(event sourcing like style)
    