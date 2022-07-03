import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

from dependency_injector.wiring import inject, Provide

from common_lib.rabbit import RabbitMQMultiConsumer, ConsumerConfig
from common_lib.cud_event_manager import EventManager, FailedEventManager, ServiceName
from common_lib.di_container import Container

from account import controllers


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

        service_name = ServiceName.ACCOUNT_SERVICE
        failed_event_manager.process_failed_events_by_consumer(service_name=service_name, event_router=event_router)
        self.event_manager = event_manager
        self.rmq_client = RabbitMQMultiConsumer(consumers=consumers, dsn=settings.RABBITMQ_DSN)
        self.rmq_client.listen()

    def handle_rabbitmq_message(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            self.event_manager.consume_event(event)
        except Exception:
            logging.exception("trace")
            self.stderr.write(self.style.ERROR(f"Un ack message: {body}"))
