import logging
from typing import Dict
from task.rabbit import RabbitMQClient


logger = logging.getLogger(__name__)


class EventManager:
    """Handles CUD events"""
    
    SUPPORTED_EVENTS = [
        "AccountCreated",
        "AccountUpdated",
        "AccountDeleted",
    ]
    
    def __init__(self, mq_client: RabbitMQClient) -> None:
        self.mq_client = mq_client
        
    def process_event(self, event: Dict):
        event_name = event['event_name']
        if event_name == 'AccountCreated':
            pass
        elif event_name == 'AccountCreated':
            pass
        elif event_name == 'AccountDeleted':
            pass
        else: 
            ValueError(f'Unsupported event: {event}')
            
    def send_event(self, event: Dict):
        self.mq_client.publish(body=event)
    