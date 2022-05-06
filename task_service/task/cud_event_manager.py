from dataclasses import asdict, dataclass
import logging
from typing import Dict
from task.rabbit import RabbitMQClient
from django.contrib.auth.models import User

from task.models import TaskDTO


logger = logging.getLogger(__name__)


@dataclass
class TaskServiceCUDEvent:
    """Base CUD model for current service"""
    data: Dict
    event_name: str = "AccountCreated"
    producer: str = "task_service"


@dataclass
class TaskCreatedEvent(TaskServiceCUDEvent):
    data: TaskDTO


class EventManager:
    """Handles CUD events"""

    SUPPORTED_EVENTS = [
        "AccountCreated",
        "AccountUpdated",
        "AccountDeleted",
    ]

    def __init__(self, mq_client: RabbitMQClient, service_exchange_name: str = 'task_stream') -> None:
        self.mq_client = mq_client
        self.task_service_exchange_name = service_exchange_name
        self.mq_client.channel.exchange_declare(exchange=self.task_service_exchange_name, exchange_type='fanout')

    def process_event(self, event: Dict):
        logger.debug(f"process_event: {event}")
        event_name = event["event_name"]

        if event_name == "AccountCreated":
            event["data"].pop("id", None)
            django_user = {
                "email": event["data"]["email"],
                "username": event["data"]["full_name"] or event["data"]["email"],
                "is_superuser": False,
                "is_staff": True,
            }
            user = User(**django_user)
            user.save()
            logger.info(f"added new django user: {django_user=}")
        elif event_name == "AccountUpdated":
            django_user = {
                "email": event["data"]["email"],
                "username": event["data"]["full_name"],
                "is_superuser": False,
                "is_staff": True,
            }
            user, is_created = User.objects.filter(email=event["data"]["email"]).update_or_create(django_user)
            if is_created:
                user.save()
                logger.info(f"added new django user: {django_user=}")
            else:
                logger.info(f"updated django user: {django_user=}")
        elif event_name == "AccountDeleted":
            logging.warning(f"FIXME: {event}")
        else:
            ValueError(f"Unsupported event: {event}")

    def send_event(self, event: TaskServiceCUDEvent):
        logger.debug(f'sending: {event=} to {self.task_service_exchange_name=}')
        self.mq_client.publish(body=asdict(event), exchange_name=self.task_service_exchange_name)

