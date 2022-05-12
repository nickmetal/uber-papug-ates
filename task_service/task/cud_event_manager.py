from dataclasses import asdict, dataclass, field
from datetime import datetime
import logging
from typing import Dict
from uuid import uuid4
from schema.validator import Validator, get_schema
from task.rabbit import RabbitMQClient

from task.models import TaskDTO
from task.models import TaskTrackerUser


logger = logging.getLogger(__name__)


@dataclass
class TaskServiceCUDEvent:
    """Base CUD model for current service"""
    data: Dict
    id: uuid4 = field(default_factory=uuid4)
    version: int = field(default=1)
    event_name: str = field(default="<not_set>")  # <not_set> is dataclass issue, implementation workaround
    producer: str = field(default="<not_set>")  # <not_set> is dataclass issue, implementation workaround
    event_time: datetime = field(default_factory=datetime.utcnow)
    producer: str = field(default="task_service")
    

@dataclass
class TaskCreatedEvent(TaskServiceCUDEvent):
    data: TaskDTO
    event_name: str = field(default="task_created")
    version: int = 2


@dataclass
class TaskCompletedEvent(TaskServiceCUDEvent):
    data: dict
    """data:
    {'id': id}
    """
    event_name: str = field(default="task_completed")


@dataclass
class TasksAssignedEvent(TaskServiceCUDEvent):
    data: dict
    """data:
    
    {"tasks": [{"id": 1, "assignee": "nick", "fee"}]}  # todo: update
    """
    event_name: str = field(default="tasks_assigned")
    version: int = 2


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

    def consume_event(self, event: Dict):
        logger.debug(f"{event=}")
        self._validate_incomming_event(event)
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
        try:
            logger.debug(f'sending: {event=} to {self.task_service_exchange_name=}')
            self._validate_event(event)
            self.mq_client.publish(body=asdict(event), exchange_name=self.task_service_exchange_name)
        except Exception:
            logger.exception(f'unable to send {event=}')
            raise 

    def _validate_event(self, event: TaskServiceCUDEvent):
        """Validates outcomming event againts schema based on event name and event version. Raises expetion on invalid event"""
        base_dir = './'
        schema_path = f'{base_dir}schema/task/{event.event_name}/{event.version}.json'
        validator = Validator(schema_path=schema_path)
        validator.validate(data=asdict(event))
        logger.debug(f'cache usage: {get_schema.cache_info()=}')

    def _validate_incomming_event(self, event: Dict):
        """Validates incomming event againts schema based on event name and event version. Raises expetion on invalid event"""
        base_dir = './'
        
        service_2_domain_map = {
            'auth_service': 'account',
            'account': 'account',
            'analytics': 'analytics',
            'task': 'task',
        }
        event_name_map = {
            "AccountCreated": "account_created",
            "AccountUpdated": "account_updated",
            "AccountDeleted": "account_deleted",
        }
        domain = service_2_domain_map[event['producer']]
        event_version = event.get('event_version') or event.get('version')
        event_name = event_name_map[event.get("event_name") or event.get("name")]
        
        schema_path = f'{base_dir}schema/{domain}/{event_name}/{event_version}.json'
        validator = Validator(schema_path=schema_path)
        validator.validate(data=event)
        logger.debug(f'cache usage: {get_schema.cache_info()=}')