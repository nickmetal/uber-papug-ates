from asyncio.log import logger
import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from common_lib.rabbit import RabbitMQMultiConsumer, ConsumerConfig
from common_lib.cud_event_manager import EventManager, FailedEventManager, ServiceName
from analytics import controllers


class Command(BaseCommand):
    help = "Consumes cud events from common message broker"

    def handle(self, *args, **options):
        task_exchange = settings.TASKS_EXCHANGE_NAME
        task_queue = settings.TASKS_TO_ANALYTICS_QUEUE

        auth_account_exchange = settings.AUTH_ACCOUNT_EXCHANGE_NAME
        auth_account_queue = settings.AUTH_ACCOUNT_ANALYTICS_QUEUE

        billing_account_exchange = settings.BILLING_EXCHANGE_NAME
        billing_account_2_analytic_queue = settings.BILLING_2_ANALYTICS_QUEUE

        # define rabbit queues to consume from
        consumers = [
            ConsumerConfig(queue=task_queue, exchange=task_exchange, callback=self.handle_rabbitmq_message),
            ConsumerConfig(
                queue=auth_account_queue,
                exchange=auth_account_exchange,
                callback=self.handle_rabbitmq_message,
            ),
            ConsumerConfig(
                queue=billing_account_2_analytic_queue,
                exchange=billing_account_exchange,
                callback=self.handle_rabbitmq_message,
            ),
        ]
        self.rmq_client = RabbitMQMultiConsumer(consumers=consumers)
        event_router = {
            "task_created": controllers.handle_task_created,
            "task_completed": controllers.handle_task_completed,
            "account_created": controllers.handle_auth_account_created,
            "billing_account_created": controllers.handle_billing_account_created,
            "billing_account_changed": controllers.handle_billing_account_changed,
        }
        self.failed_events_manager = FailedEventManager.build(
            mongo_dsn=settings.MONGO_DSN,
            db_name=settings.MONGO_DB_NAME,
            error_collection_name=settings.MONGO_ERROR_COLLECTION,
        )
        self.service_name = ServiceName.ANALYTIC_SERVICE
        self.failed_events_manager.process_failed_events_by_consumer(
            service_name=self.service_name,
            event_router=event_router,
        )
        self.event_manager = EventManager(
            mq_publisher=None,
            event_router=event_router,
            schema_basedir=settings.EVENT_SCHEMA_DIR,
            service_name=self.service_name,
            failed_event_manager=self.failed_events_manager,
        )
        self.rmq_client.listen()

    def handle_rabbitmq_message(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            self.event_manager.consume_event(event)
        except:
            logging.exception("trace")
            self.stderr.write(self.style.ERROR(f"Un ack message: {body}"))
