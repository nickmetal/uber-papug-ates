from logging import getLogger
from typing import Dict
from account import models
from account.models import Account, AccountUser, TransactionType
from django.conf import settings
from django.db import transaction

from account.models import Task


logger = getLogger(__name__)


def handle_task_created(event: Dict):
    with transaction.atomic():
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

        task_info = {
            "public_id": event["data"]["id"],
            "title": event["data"]["title"],
            "description": event["data"]["description"],
            "assignee": assignee,
            "fee_on_assign": event["data"]["fee_on_assign"],
            "fee_on_complete": event["data"]["fee_on_complete"],
        }

        trx = models.AccountTransaction(**trx_info)
        task = Task.objects.create(**task_info)
        company_user.get_total()


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
    }
    user = models.AccountUser.objects.create(**user_info)
    account, is_new = Account.objects.get_or_create(id=user.id)
    logger.info(f"added new {user=}")


def get_company_user() -> AccountUser:
    return AccountUser.objects.get(username=settings.COMPANY_SLUG)
