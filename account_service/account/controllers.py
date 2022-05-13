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

        task_title = event["data"]["title"]
        trx_outcome = {
            "public_id": event["data"]["id"],
            "amount": event["data"]["fee_on_assign"],
            "type": TransactionType.OUTCOME.value,
            "description": f"task `{task_title}` assign fee",
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
        if task.status == 'completed':
            logger.warning(f'{task=} already completed, skipping its processing')
            return 

        assignee_account = task.assignee.account_set.first()

        trx_outcome = {
            "amount": task.fee_on_complete,
            "type": TransactionType.OUTCOME.value,
            "description": f"task `{task.title}` completion fee",
            "source_account_id": company_account,
            "target_account_id": assignee_account,
        }

        trx_income = deepcopy(trx_outcome)
        trx_income["type"] = TransactionType.INCOME.value
        trx_income["source_account_id"] = assignee_account
        trx_income["target_account_id"] = company_account

        trx_out = models.AccountTransaction(**trx_outcome)
        trx_out.save()

        trx_in = models.AccountTransaction(**trx_income)
        trx_in.save()

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
        transactions_to_insert = []
        company_user = get_company_user()
        company_account = company_user.account_set.first()

        for shuffled_task in shuffled_tasks:
            task = Task.objects.get(public_id=shuffled_task["id"])
            new_assignee = AccountUser.objects.get(public_id=shuffled_task["new_assignee"])
            assignee_account = new_assignee.account_set.first()

            task.assignee = new_assignee
            task.save()

            trx_outcome = {
                "amount": task.fee_on_assign,
                "type": TransactionType.OUTCOME.value,
                "description": f"task `{task.title}` assign fee(due to reshuffle)",
                "source_account_id": assignee_account,
                "target_account_id": company_account,
            }

            trx_income = deepcopy(trx_outcome)
            trx_income["type"] = TransactionType.INCOME.value
            trx_income["source_account_id"] = company_account
            trx_income["target_account_id"] = assignee_account

            trx_out = models.AccountTransaction(**trx_outcome)
            transactions_to_insert.append(trx_out)

            trx_in = models.AccountTransaction(**trx_income)
            transactions_to_insert.append(trx_in)
            
        models.AccountTransaction.objects.bulk_create(transactions_to_insert)
        
        logger.debug(f'updated tasks {len(shuffled_tasks)}')
        logger.debug(f'added transactions {len(transactions_to_insert)}')


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
        user, is_new = models.AccountUser.objects.get_or_create(**user_info)
        if is_new:
            logger.info(f"added new {user=}")

        accounts = list(Account.objects.filter(user__public_id=user_info["public_id"]))
        if not accounts:
            account = Account(user=user)
            account.save()
            logger.info(f"added new {account=}")


def get_company_user() -> AccountUser:
    return AccountUser.objects.get(username=settings.COMPANY_SLUG)
