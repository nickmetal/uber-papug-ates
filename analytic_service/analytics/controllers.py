from copy import deepcopy
from decimal import Decimal
from logging import getLogger
from typing import Dict
from analytics.models import Account, AccountUser
from django.conf import settings
from django.db import transaction

from analytics.models import Task


logger = getLogger(__name__)


def handle_task_created(event: Dict = 1):
    """Handles task creation event

    steps:
        - creates in transaction for company
        - creates out transaction for task's assignee
        - creates task record in db
    """
    with transaction.atomic():
        company_user = get_company_user()
        company_account = company_user.account_set.first()
        assignee_account = Account.objects.get(user__public_id=event["data"]["assignee"])
        
        company_account.amount += Decimal(abs(event["data"]["fee_on_assign"]))
        company_account.save()
        
        assignee_account.amount -= Decimal(abs(event["data"]["fee_on_assign"]))
        assignee_account.save()

        task_info = {
            "public_id": event["data"]["id"],
            "title": event["data"]["title"],
            "status": event["data"]["status"],
            "description": event["data"]["description"],
            "assignee": assignee_account.user,
            "fee_on_assign": event["data"]["fee_on_assign"],
            "fee_on_complete": event["data"]["fee_on_complete"],
        }

        task = Task.objects.create(**task_info)
        task.save()


def handle_task_completed(event: Dict):
    """Handles task completion event

    steps:
        - creates in transaction for task's assignee
        - creates out transaction for company
        - updates task record in db
    """
    with transaction.atomic():
        company_user = get_company_user()
        company_account = company_user.account_set.first()
        task = Task.objects.get(public_id=event["data"]["id"])

        assignee_account = task.assignee.account_set.first()
        company_account.amount -= Decimal(abs(event["data"]["fee_on_complete"]))
        company_account.save()
        
        assignee_account.amount += Decimal(abs(event["data"]["fee_on_complete"]))
        assignee_account.save()

        task.status = "completed"
        task.save()


def handle_tasks_assigned(event: Dict):
    """Handles task completion event

    steps(for each task):
        - creates in transaction for company
        - creates out transaction for task's assignee
        - updates task record in db
    """
    with transaction.atomic():
        shuffled_tasks = event["data"]["tasks"]

        for shuffled_task in shuffled_tasks:
            task = Task.objects.get(public_id=shuffled_task["id"])
            new_assignee = AccountUser.objects.get(public_id=shuffled_task["new_assignee"])

            task.assignee = new_assignee
            task.save()
        
        logger.debug(f'updated tasks {len(shuffled_tasks)}')


def handle_auth_account_created(event: Dict):
    """Handles system(global user) account creation event

    steps:
        - creates domain user in db
        - creates domain account for specicfied user in db
    """
    user_info = {
        "public_id": event["data"]["public_id"],
        "role": event["data"]["position"] or "worker",
        "email": event["data"]["email"],
        "username": event["data"]["email"],
    }
    with transaction.atomic():
        user, is_new = AccountUser.objects.get_or_create(**user_info)
        if is_new:
            logger.info(f"added new {user=}")

        accounts = list(Account.objects.filter(user__public_id=user_info["public_id"]))
        if not accounts:
            account = Account(user=user)
            account.save()
            logger.info(f"added new {account=}")


def handle_account_changed(event: Dict):
    """Handles user's account(financial) change event"""
    
    with transaction.atomic():
        print(event)


def get_company_user() -> AccountUser:
    return AccountUser.objects.get(username=settings.COMPANY_SLUG)
