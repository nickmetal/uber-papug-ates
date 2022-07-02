import json
import logging
from typing import Dict

from django.core.management.base import BaseCommand
from django.conf import settings

from task import controllers
from common_lib.offset_manager import OffsetLogManager
from common_lib.rabbit import RabbitMQMultiConsumer, ConsumerConfig
from common_lib.cud_event_manager import EventManager, FailedEventManager, ServiceName


class Command(BaseCommand):
    help = "Consumes cud events from common message broker"

    def handle(self, *args, **options):
        auth_service_exchange = settings.AUTH_ACCOUNT_EXCHANGE_NAME
        task_queue = settings.AUTH_ACCOUNT_TASK_QUEUE

        # define rabbit queues to consume from
        consumers = [
            ConsumerConfig(queue=task_queue, exchange=auth_service_exchange, callback=self.handle_rabbitmq_message),
        ]
        self.rmq_client = RabbitMQMultiConsumer(consumers=consumers, dsn=settings.RABBITMQ_DSN)

        event_router = {
            "account_created": controllers.handle_auth_account_created,
            "account_updated": controllers.handle_auth_account_updated,
        }
        self.failed_events_manager = FailedEventManager.build(
            mongo_dsn=settings.MONGO_DSN,
            db_name=settings.MONGO_DB_NAME,
            error_collection_name=settings.MONGO_ERROR_COLLECTION,
        )
        self.service_name = ServiceName.TASK_SERVICE
        self.failed_events_manager.process_failed_events_by_consumer(
            service_name=self.service_name,
            event_router=event_router,
        )
        offset_manager = OffsetLogManager.build(
            mongo_dsn=settings.MONGO_DSN,
            db_name=settings.MONGO_DB_NAME,
            collection_name=f"{self.service_name.value}_event_offset",
        )

        self.event_manager = EventManager(
            mq_publisher=None,
            event_router=event_router,
            schema_basedir=settings.EVENT_SCHEMA_DIR,
            service_name=self.service_name,
            failed_event_manager=self.failed_events_manager,
            offset_manager=offset_manager,
        )
        self.rmq_client.listen()

    def handle_rabbitmq_message(self, ch, method, properties, body: bytes):
        try:
            event = json.loads(body)
            if not isinstance(event, Dict) or not event:
                logging.warning("Unexpected json type received")
                return

            self.event_manager.consume_event(event)

        except json.decoder.JSONDecodeError as e:
            logging.error(f"Bad json data receieved: {e=}, {e.doc=}")
        except Exception:
            logging.exception("trace")
            self.stderr.write(self.style.ERROR(f"Un ack message: {body}"))
