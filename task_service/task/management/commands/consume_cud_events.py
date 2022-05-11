import json
import logging
from django.core.management.base import BaseCommand
from task.models import Task


from task.rabbit import RabbitMQClient
from task.cud_event_manager import EventManager


class Command(BaseCommand):
    help = 'Consumes cud events from common message broker'

    def handle(self, *args, **options): 
        self.rmq_client = RabbitMQClient()
        self.rmq_client.listen(cb=self.handle_rabbitmq_message)
        
    def handle_rabbitmq_message(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            EventManager(self.rmq_client).consume_event(event)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except:
            logging.exception('trace')
            self.stderr.write(self.style.ERROR(f'Un ack message: {body}'))
        
    