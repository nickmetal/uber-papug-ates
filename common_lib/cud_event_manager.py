import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional
from uuid import uuid4

from pymongo.collection import Collection
from pymongo.mongo_client import MongoClient

from common_lib.rabbit import RabbitMQPublisher
from common_lib.schema.validator import Validator, get_schema

logger = logging.getLogger(__name__)


@dataclass
class CUDEvent:
    """Base CUD model for current service"""

    data: Dict
    id: uuid4 = field(default_factory=uuid4)
    version: int = field(default=1)
    event_name: str = field(
        default="<not_set>"
    )  # <not_set> is dataclass issue, implementation workaround
    producer: str = field(
        default="<not_set>"
    )  # <not_set> is dataclass issue, implementation workaround
    event_time: datetime = field(default_factory=datetime.utcnow)


class ServiceName(Enum):
    TASK_SERVICE = "task_service"
    ACCOUNT_SERVICE = "account_service"
    ANALYTIC_SERVICE = "analytic_service"
    AUTH_SERVICE = "auth_service"


class FailedEventManager:
    """Handles events that were failed during publish/consume stages"""

    def __init__(
        self, error_collection: Collection
    ) -> None:
        self.error_collection = error_collection

    @classmethod
    def build(
        cls,
        mongo_dsn: str,
        db_name: str,
        error_collection_name: str,
    ) -> "FailedEventManager":
        error_collection = MongoClient(mongo_dsn)[db_name][error_collection_name]
        return cls(error_collection=error_collection)

    def store_failed_produce_event(self, exception: Exception, origin_event: Dict):
        error_event = {
            "producer": ServiceName(origin_event["producer"]).value,
            "origin_event": origin_event,
            "exception": {
                "type": exception.__class__.__name__,
                "message": str(exception),
                "stack_trace": "TODO",
            },
        }
        self._store_event(error_event)

    def store_failed_consume_event(
        self, exception: Exception, origin_event: Dict, consumer: ServiceName
    ):
        error_event = {
            "consumer": consumer.value,
            "origin_event": origin_event,
            "exception": {
                "type": exception.__class__.__name__,
                "message": str(exception),
                "stack_trace": "TODO",
            },
        }
        self._store_event(error_event)

    def _store_event(self, event: Dict):
        logger.debug(f"storing event in db: {event=}")
        self.error_collection.insert_one(event)

    def read_failed_event_by_id(self, event_id: str) -> Optional[Dict]:
        self.error_collection.find_one({"event_id": event_id})

    def read_produce_events_by_service(self, service_name: ServiceName) -> List[Dict]:
        return self.error_collection.find({"producer": service_name.value}) or []

    def read_consume_events_by_service(self, service_name: ServiceName) -> List[Dict]:
        return self.error_collection.find({"consumer": service_name.value}) or []

    def remove_event(self, mongo_id):
        self.error_collection.delete_one({"_id": mongo_id})

    def process_failed_events_by_consumer(self, service_name: ServiceName, event_router: Dict[str, Callable]):
        consume_events = self.read_consume_events_by_service(service_name=service_name)
        for event in consume_events:
            logger.info(f"processing faield eventfor {service_name=}, {event=}")
            callback = event_router[event["event_name"]]
            try:
                callback(event["origin_event"])
            except Exception as e:
                raise Exception(f"Can not reprocess {event=} due to {e=}")
            event_db_id = event["_id"]
            self.remove_event(event_db_id)


class EventManager:
    """Handles CUD events"""

    def __init__(
        self,
        mq_publisher: RabbitMQPublisher,
        schema_basedir: str,
        failed_event_manager: FailedEventManager,
        service_name: ServiceName,
        event_router: Dict = None,
    ) -> None:
        self.mq_publisher = mq_publisher
        self.event_router = event_router or {}
        self.schema_basedir = schema_basedir
        self.failed_event_manager = failed_event_manager
        self.service_name = service_name

    def consume_event(self, event: Dict):
        logger.debug(f"{event=}")
        cb = self.event_router.get(self._normilize_event_name(event))
        if cb:
            try:
                self._validate_incomming_event(event)
                cb(event)
            except Exception as e:
                logger.exception(f"consume callback({cb=}) failed during {event=}")
                self.failed_event_manager.store_failed_consume_event(
                    exception=e, origin_event=event, consumer=self.service_name
                )
        else:
            logger.debug(f"no callback provided for {event} specified")

    def send_event(self, event: CUDEvent):
        try:
            logger.debug(f"sending: {event=}")
            self._validate_event(event)
            self.mq_publisher.publish(body=asdict(event))
        except Exception as e:
            logger.exception(f"unable to send {event=}")
            self.failed_event_manager.store_failed_produce_event(
                exception=e, origin_event=asdict(event)
            )

    # TODO: create 1 validation method instead of 2
    def _validate_event(self, event: CUDEvent):
        """Validates outcomming event againts schema based on event name and event version. Raises expetion on invalid event"""
        # validate producer name value
        ServiceName(event.producer)

        # validate event data  against schema
        domain = self._get_domain_by_producer_name(event.producer)
        schema_path = os.path.join(
            self.schema_basedir,
            f"schema/{domain}/{event.event_name}/{event.version}.json",
        )
        validator = Validator(schema_path=schema_path)
        validator.validate(data=asdict(event))

        # check schema cache metrics
        logger.debug(f"cache usage stats: {get_schema.cache_info()=}")

    def _validate_incomming_event(self, event: Dict):
        """Validates incomming event againts schema based on event name and event version. Raises expetion on invalid event"""
        domain = self._get_domain_by_producer_name(event["producer"])
        event_version = event.get("event_version") or event.get("version")
        event_name = self._normilize_event_name(event)
        schema_path = os.path.join(
            self.schema_basedir, f"schema/{domain}/{event_name}/{event_version}.json"
        )
        validator = Validator(schema_path=schema_path)
        validator.validate(data=event)
        logger.debug(f"cache usage: {get_schema.cache_info()=}")

    def _normilize_event_name(self, event: Dict) -> str:
        """Maps events from external services to the common format"""
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
        raise ValueError(f"Unknown {producer=}")
