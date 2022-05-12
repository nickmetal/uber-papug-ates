from dataclasses import asdict, dataclass, field
from datetime import datetime
import logging
from typing import Dict
from uuid import uuid4
from schema.validator import Validator, get_schema
from account.rabbit import RabbitMQPublisher

from account.models import AccountUser


logger = logging.getLogger(__name__)


@dataclass
class AccountCUDEvent:
    """Base CUD model for current service"""
    data: Dict
    id: uuid4 = field(default_factory=uuid4)
    version: int = field(default=1)
    event_name: str = field(default="<not_set>")  # <not_set> is dataclass issue, implementation workaround
    producer: str = field(default="<not_set>")  # <not_set> is dataclass issue, implementation workaround
    event_time: datetime = field(default_factory=datetime.utcnow)
    producer: str = field(default="task_service")
    

class EventManager:
    """Handles CUD events"""

    def __init__(self, mq_publisher: RabbitMQPublisher, service_exchange_name: str = 'account_stream', event_router: Dict = None) -> None:
        self.mq_publisher = mq_publisher
        self.task_service_exchange_name = service_exchange_name
        self.event_router = event_router or {}

    def consume_event(self, event: Dict):
        logger.debug(f"{event=}")
        self._validate_incomming_event(event)
        cb = self.event_router.get(self._normilize_event_name(event))
        if cb:
            cb(event)
        else:
            logger.debug(f'no callback for {event} specified')

    def send_event(self, event: AccountCUDEvent):
        try:
            logger.debug(f'sending: {event=} to {self.task_service_exchange_name=}')
            self._validate_event(event)
            self.mq_publisher.publish(body=asdict(event), exchange_name=self.task_service_exchange_name)
        except Exception:
            logger.exception(f'unable to send {event=}')
            raise 

    def _validate_event(self, event: AccountCUDEvent):
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
            'account_service': 'account',
            'analytics_service': 'analytics',
            'task_service': 'task',
        }

        domain = service_2_domain_map[event['producer']]
        event_version = event.get('event_version') or event.get('version')
        event_name = self._normilize_event_name(event)
        
        schema_path = f'{base_dir}schema/{domain}/{event_name}/{event_version}.json'
        validator = Validator(schema_path=schema_path)
        validator.validate(data=event)
        logger.debug(f'cache usage: {get_schema.cache_info()=}')
        
    def _normilize_event_name(self, event: Dict) -> str:
        event_name_map = {
            "AccountCreated": "account_created",
            "AccountUpdated": "account_updated",
            "AccountDeleted": "account_deleted",
        }
        event_name = event.get("event_name") or event.get("name")
        # take mapped event name or take it as it is 
        return event_name_map.get(event_name, event_name)
        