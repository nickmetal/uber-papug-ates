import json
import logging
from typing import Dict

from django.core.management.base import BaseCommand
from django.conf import settings

from dependency_injector.wiring import inject, Provide

from common_lib.rabbit import RabbitMQMultiConsumer, ConsumerConfig
from common_lib.cud_event_manager import EventManager, FailedEventManager, ServiceName
from common_lib.di_container import Container

from task import controllers


class Command(BaseCommand):
    help = "Consumes cud events from common message broker"

    @inject
    def handle(
        self,
        *args,
        event_manager: EventManager = Provide[Container.event_manager],
        failed_event_manager: FailedEventManager = Provide[Container.failed_event_manager],
        **options,
    ):
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
        self.service_name = ServiceName.TASK_SERVICE
        failed_event_manager.process_failed_events_by_consumer(
            service_name=self.service_name, event_router=event_router
        )

        self.event_manager = event_manager
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
