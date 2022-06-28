from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
import uuid
from django.db import models
from snowflake import SnowflakeGenerator
from django.contrib.auth.models import User


@dataclass
class BaseEntity:
    """Base class for domain entity"""

    id: int  # snowflake id
    created_at: datetime
    updated_at: datetime


class AccountUser(User):
    public_id = models.CharField(max_length=250)
    role = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TransactionType(Enum):
    INCOME = "income"
    OUTCOME = "outcome"


@dataclass
class TransactionDTO(BaseEntity):
    type: TransactionType
    currency: field(default="US DOLLAR")
    amount: Decimal
    description: Optional[str]
    source_account_id: int
    target_account_id: int


def get_id(id_generator=SnowflakeGenerator(42)) -> int:
    return next(id_generator)


class BaseModel(models.Model):
    id = models.BigIntegerField(primary_key=True, editable=False, default=get_id)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Account(BaseModel):
    user = models.ForeignKey(AccountUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)


class AccountTransaction(BaseModel):
    currency = models.CharField(default="US DOLLAR", max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    type = models.CharField(choices=[(item.value, item.value) for item in TransactionType], max_length=100)
    description = models.TextField()
    source_account_id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="source_account")
    target_account_id = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="target_account")


class Task(BaseModel):
    title = models.CharField(max_length=250)
    status = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    assignee = models.ForeignKey(AccountUser, on_delete=models.CASCADE)
    fee_on_assign = models.DecimalField(max_digits=15, decimal_places=10)
    fee_on_complete = models.DecimalField(max_digits=15, decimal_places=10)
    public_id = models.BigIntegerField(editable=False, unique=True)
