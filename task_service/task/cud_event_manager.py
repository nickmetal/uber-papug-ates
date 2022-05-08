from dataclasses import asdict, dataclass, field
from datetime import datetime
import logging
from typing import Dict
from uuid import uuid4
from task.rabbit import RabbitMQClient

from task.models import TaskDTO
from task.models import TaskTrackerUser


logger = logging.getLogger(__name__)


@dataclass
class TaskServiceCUDEvent:
    """Base CUD model for current service"""
    data: Dict
    id: uuid4 = field(default_factory=uuid4)
    event_time: datetime = field(default_factory=datetime.utcnow)
    producer: str = "task_service"
    

@dataclass
class TaskCreatedEvent(TaskServiceCUDEvent):
    data: TaskDTO
    event_name: str = "TaskCreated"


@dataclass
class TaskReAssignedEvent(TaskServiceCUDEvent):
    data: TaskDTO
    event_name: str = "TaskReAssigned"


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
        logger.debug(f"{event=}")
        event_name = event["event_name"]
        if event_name == "AccountCreated":
            event["data"].pop("id", None)
            role = event["data"].get('position') or 'worker'
            public_id = event["data"].get('public_id') or 'test_id'  # TODO: make sure we receive public_id in the event
            django_user = {
                "email": event["data"]["email"],
                "username": event["data"]["full_name"] or event["data"]["email"],
                "is_staff": True,
                "role": role,
                "public_id": public_id,
            }
            logger.debug(f'{django_user}=')
            user = TaskTrackerUser(**django_user)
            user.save()
            logger.info(f"added new django user: {django_user=}")
        elif event_name == "AccountUpdated":
            event["data"].pop("id", None)
            role = event["data"].get('position') or 'worker'
            public_id = event["data"].get('public_id') or 'test_id'  # TODO: make sure we receive public_id in the event
            django_user = {
                "email": event["data"]["email"],
                "username": event["data"]["full_name"],
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
        elif event_name == "AccountDeleted":
            logging.warning(f"FIXME: {event}")
        else:
            ValueError(f"Unsupported event: {event}")

    def send_event(self, event: TaskServiceCUDEvent):
        logger.debug(f'sending: {event=} to {self.task_service_exchange_name=}')
        self.mq_client.publish(body=asdict(event), exchange_name=self.task_service_exchange_name)

