import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from task import controllers
from common_lib.rabbit import RabbitMQMultiConsumer, ConsumerConfig
from common_lib.cud_event_manager import EventManager


class Command(BaseCommand):
    help = 'Consumes cud events from common message broker'

    def handle(self, *args, **options): 
        auth_service_exchange = settings.AUTH_ACCOUNT_EXCHANGE_NAME
        task_queue = settings.AUTH_ACCOUNT_TASK_QUEUE

        # define rabbit queues to consume from
        consumers = [
            ConsumerConfig(queue=task_queue, exchange=auth_service_exchange, callback=self.handle_rabbitmq_message),
        ]
        self.rmq_client = RabbitMQMultiConsumer(consumers=consumers)
        self.rmq_client.listen()
            
    def handle_rabbitmq_message(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            event_router = {
                "account_created": controllers.handle_auth_account_created,
                "account_updated": controllers.handle_auth_account_updated,
            }
            EventManager(
                mq_publisher=None,
                event_router=event_router,
                schema_basedir=settings.EVENT_SCHEMA_DIR,
            ).consume_event(event)
        except:
            logging.exception("trace")
            self.stderr.write(self.style.ERROR(f"Un ack message: {body}"))