import json
from django.core.management.base import BaseCommand
from task.models import Task


from task.rabbit import RabbitMQClient
from task.cud_event_manager import EventManager


class Command(BaseCommand):
    help = ''

    # def add_arguments(self, parser):
        # parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options): 
        tasks = Task.objects.all()
        
        self.rmq_client = RabbitMQClient()
        self.rmq_client.listen(cb=self.handle_rabbitmq_message)
        
    def handle_rabbitmq_message(self, ch, method, properties, body):
        try:
            event = json.loads(body)
            if event.get('event_name') in EventManager.SUPPORTED_EVENTS:
                EventManager(self.rmq_client).process_event(event)
            else:
                self.stdout.write(f'skip unknown event: {event}')
                
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Un ack message: {body} due to {e}'))
        
    