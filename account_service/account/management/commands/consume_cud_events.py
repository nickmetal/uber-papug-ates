import json
import logging
from django.core.management.base import BaseCommand
from account.rabbit import RabbitMQMultiConsumer, ConsumerConfig
from account.cud_event_manager import EventManager
from account import controllers


class Command(BaseCommand):
    help = "Consumes cud events from common message broker"

    def handle(self, *args, **options):
        task_exchange = "task_stream"
        task_queue = "task_to_account_queue"

        auth_account_exchange = "accounts-stream"
        auth_account_queue = "auth_account_to_account_queue"

        # define rabbit queues to consume from
        consumers = [
            ConsumerConfig(queue=task_queue, exchange=task_exchange, callback=self.handle_rabbitmq_message),
            ConsumerConfig(
                queue=auth_account_queue, exchange=auth_account_exchange, callback=self.handle_rabbitmq_message
            ),
        ]
        self.rmq_client = RabbitMQMultiConsumer(consumers=consumers)
        self.rmq_client.listen()

    def handle_rabbitmq_message(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            event_router = {
                "task_created": controllers.handle_task_created,
                "task_completed": controllers.handle_task_completed,
                "tasks_assigned": controllers.handle_tasks_assigned,
                "account_created": controllers.handle_auth_account_created,
            }
            EventManager(mq_publisher=None, event_router=event_router).consume_event(event)
        except:
            logging.exception("trace")
            self.stderr.write(self.style.ERROR(f"Un ack message: {body}"))
