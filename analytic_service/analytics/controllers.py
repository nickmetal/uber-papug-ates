from decimal import Decimal
from logging import getLogger
from typing import Dict
from analytics.models import Account, AccountUser
from django.db import transaction

from analytics.models import Task


logger = getLogger(__name__)


def handle_task_created(event: Dict = 1):
    """Handles task creation event"""
    with transaction.atomic():
        task_info = {
            "public_id": event["data"]["id"],
            "title": event["data"]["title"],
            "status": event["data"]["status"],
            "fee_on_assign": event["data"]["fee_on_assign"],
            "fee_on_complete": event["data"]["fee_on_complete"],
        }
        task = Task.objects.create(**task_info)
        task.save()


def handle_task_completed(event: Dict):
    """Handles task completion event"""
    with transaction.atomic():
        task = Task.objects.get(public_id=event["data"]["id"])
        task.status = "completed"
        task.save()
        

def handle_auth_account_created(event: Dict):
    """Handles system(global user) account creation event"""
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


def handle_billing_account_changed(event: Dict):
    """Handles user's account(financial) change event"""
    account = Account.objects.get(public_id=event['data']['public_id'])
    account.amount += Decimal(event['data']['amount'])
    account.save()


def handle_billing_account_created(event: Dict):
    """Handles user's account(financial) create event"""
    user, is_new = AccountUser.objects.get_or_create(public_id=event['data']['user_public_id'], role=event['data']['role'])
    account, is_new = Account.objects.get_or_create(public_id=event['data']['account_public_id'], user=user)
    if is_new:
        logger.info(f"added new {account.public_id=}")