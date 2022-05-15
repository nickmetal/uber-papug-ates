from logging import getLogger
from typing import Dict
from task.models import TaskTrackerUser


logger = getLogger(__name__)


def handle_auth_account_created(event: Dict):
    role = event["data"].get('position') or 'worker'
    public_id = event["data"].get('public_id')
    django_user = {
        "email": event["data"]["email"],
        "username": event["data"]["email"],
        "is_staff": True,
        "role": role,
        "public_id": public_id,
    }
    logger.debug(f'{django_user}=')
    TaskTrackerUser.objects.create(**django_user)
    logger.info(f"added new django user: {django_user=}")
    
    
def handle_auth_account_updated(event: Dict):
    event["data"].pop("id", None)
    role = event["data"].get('position') or 'worker'
    public_id = event["data"].get('public_id') or 'test_id'  # TODO: make sure we receive public_id in the event
    django_user = {
        "email": event["data"]["email"],
        "username": event["data"]["email"],
        "is_staff": True,
        "role": role,
        "public_id": public_id,
    }
    logger.debug(f'{django_user}=')
    user, is_created = TaskTrackerUser.objects.filter(email=event["data"]["email"]).update_or_create(django_user)
    if is_created:
        user.save()
        logger.info(f"added new django user: {django_user=}")
    else:
        logger.info(f"updated django user: {django_user=}")