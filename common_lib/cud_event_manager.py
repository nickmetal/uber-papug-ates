import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict
from uuid import uuid4

from common_lib.rabbit import RabbitMQPublisher
from common_lib.schema.validator import Validator, get_schema

logger = logging.getLogger(__name__)


@dataclass
class CUDEvent:
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

    def __init__(
        self,
        mq_publisher: RabbitMQPublisher,
        schema_basedir: str,
        event_router: Dict = None,
    ) -> None:
        self.mq_publisher = mq_publisher
        self.event_router = event_router or {}
        self.schema_basedir = schema_basedir

    def consume_event(self, event: Dict):
        logger.debug(f"{event=}")
        self._validate_incomming_event(event)
        cb = self.event_router.get(self._normilize_event_name(event))
        if cb:
            cb(event)
        else:
            logger.debug(f"no callback provided for {event} specified")

    def send_event(self, event: CUDEvent):
        try:
            logger.debug(f"sending: {event=}")
            self._validate_event(event)
            self.mq_publisher.publish(body=asdict(event))
        except Exception:
            logger.exception(f"unable to send {event=}")
            raise

    # TODO: create 1 validation method instead of 2 
    def _validate_event(self, event: CUDEvent):
        """Validates outcomming event againts schema based on event name and event version. Raises expetion on invalid event"""
        domain = self._get_domain_by_producer_name(event.producer)
        schema_path = os.path.join(self.schema_basedir, f"schema/{domain}/{event.event_name}/{event.version}.json")
        validator = Validator(schema_path=schema_path)
        validator.validate(data=asdict(event))
        logger.debug(f"cache usage stats: {get_schema.cache_info()=}")

    def _validate_incomming_event(self, event: Dict):
        """Validates incomming event againts schema based on event name and event version. Raises expetion on invalid event"""
        domain = self._get_domain_by_producer_name(event["producer"])
        event_version = event.get("event_version") or event.get("version")
        event_name = self._normilize_event_name(event)
        schema_path = os.path.join(self.schema_basedir, f"schema/{domain}/{event_name}/{event_version}.json")
        validator = Validator(schema_path=schema_path)
        validator.validate(data=event)
        logger.debug(f"cache usage: {get_schema.cache_info()=}")

    def _normilize_event_name(self, event: Dict) -> str:
        event_name_map = {
            "AccountCreated": "account_created",
            "AccountUpdated": "account_updated",
            "AccountDeleted": "account_deleted",
        }
        event_name = event.get("event_name") or event.get("name")
        # take mapped event name or take it as it is
        return event_name_map.get(event_name, event_name)

    def _get_domain_by_producer_name(self, producer: str) -> str:
        service_2_domain_map = {
            "auth_service": "account",
            "account_service": "account",
            "analytics_service": "analytics",
            "task_service": "task",
        }
        domain = service_2_domain_map.get(producer)
        if domain:
            return domain
        raise ValueError(f'Unknown {producer=}')
