from copy import deepcopy
from logging import getLogger
from typing import Dict
from account import models
from account.models import Account, AccountUser, TransactionType
from django.conf import settings
from django.db import transaction

from account.models import Task


logger = getLogger(__name__)


def handle_task_created(event: Dict = 1):
    with transaction.atomic():
        company_user = get_company_user()
        company_account = company_user.account_set.first()
        assignee_account = Account.objects.get(user__public_id=event["data"]["assignee"])
        
        task_title = event["data"]["title"]
        trx_outcome = {
            "amount": event["data"]["fee_on_assign"],
            "type": TransactionType.OUTCOME.value,
            "description": f"task `{task_title}` fee",
            "source_account_id": assignee_account,
            "target_account_id": company_account,
        }
        
        trx_income = deepcopy(trx_outcome)
        trx_income["type"] = TransactionType.INCOME.value
        trx_income["source_account_id"] = company_account
        trx_income["target_account_id"] = assignee_account

        task_info = {
            "public_id": event["data"]["id"],
            "title": event["data"]["title"],
            "status": event["data"]["status"],
            "description": event["data"]["description"],
            "assignee": assignee_account.user,
            "fee_on_assign": event["data"]["fee_on_assign"],
            "fee_on_complete": event["data"]["fee_on_complete"],
        }
        trx_out = models.AccountTransaction(**trx_outcome)
        trx_out.save()
        
        trx_in = models.AccountTransaction(**trx_income)
        trx_in.save()
        
        task = Task.objects.create(**task_info)
        task.save()


def handle_task_completed(event: Dict):
    company_user = get_company_user()
    assignee = AccountUser.objects.get(public_id="assignee")
    task_title = event["data"]["title"]
    trx_info = {
        "amount": event["data"]["fee_on_assign"],
        "type": TransactionType.OUTCOME.value,
        "description": f"task `{task_title}` fee",
        "source_account_id": assignee,
        "target_account_id": company_user,
    }

    trx = models.AccountTransaction(**trx_info)
    trx.save()
    company_user.get_total()


def handle_tasks_assigned(event: Dict):
    pass


def handle_auth_account_created(event: Dict):
    user_info = {
        "public_id": event["data"]["public_id"],
        "role": event["data"]["position"] or "worker",
        "email": event["data"]["email"],
        "username": event["data"]["email"],
    }
    with transaction.atomic():
        user, is_new = models.AccountUser.objects.get_or_create(**user_info)
        if is_new:
            logger.info(f"added new {user=}")
            
        accounts = list(Account.objects.filter(user__public_id=user_info['public_id']))
        if not accounts:
            account = Account(user=user)
            account.save()
            logger.info(f"added new {account=}")
        

def get_company_user() -> AccountUser:
    return AccountUser.objects.get(username=settings.COMPANY_SLUG)
