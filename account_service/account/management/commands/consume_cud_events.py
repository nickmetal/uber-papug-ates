import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from common_lib.offset_mager import OffsetLogManager
from common_lib.rabbit import RabbitMQMultiConsumer, ConsumerConfig
from common_lib.cud_event_manager import EventManager, FailedEventManager, ServiceName
from account import controllers


class Command(BaseCommand):
    help = "Consumes cud events from common message broker"

    def handle(self, *args, **options):
        task_exchange = settings.TASKS_EXCHANGE_NAME
        task_queue = settings.TASKS_TO_ACCOUNT_QUEUE

        auth_account_exchange = settings.AUTH_ACCOUNT_EXCHANGE_NAME
        auth_account_queue = settings.AUTH_ACCOUNT_ACCOUNT_QUEUE

        # define rabbit queues to consume from
        consumers = [
            ConsumerConfig(queue=task_queue, exchange=task_exchange, callback=self.handle_rabbitmq_message),
            ConsumerConfig(
                queue=auth_account_queue, exchange=auth_account_exchange, callback=self.handle_rabbitmq_message
            ),
        ]
        event_router = {
            "task_created": controllers.handle_task_created,
            "task_completed": controllers.handle_task_completed,
            "tasks_assigned": controllers.handle_tasks_assigned,
            "account_created": controllers.handle_auth_account_created,
        }
        self.failed_events_manager = FailedEventManager.build(
            mongo_dsn=settings.MONGO_DSN,
            db_name=settings.MONGO_DB_NAME,
            error_collection_name=settings.MONGO_ERROR_COLLECTION,
        )
        self.service_name = ServiceName.ACCOUNT_SERVICE
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
        self.rmq_client = RabbitMQMultiConsumer(consumers=consumers)
        self.rmq_client.listen()

    def handle_rabbitmq_message(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            self.event_manager.consume_event(event)
        except Exception:
            logging.exception("trace")
            self.stderr.write(self.style.ERROR(f"Un ack message: {body}"))
