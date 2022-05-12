import json
from typing import Dict
import pika
from django.conf import settings


class RabbitMQClient:
    def __init__(
        self, queue="account_events", exchange_name="accounts-stream", dsn: str = settings.RABBITMQ_DSN
    ) -> None:
        self.queue_name = queue
        self.exchange_name = exchange_name
        self.dsn = dsn
        self.channel = self.connect()

    def connect(self):
        connection = pika.BlockingConnection(pika.URLParameters(self.dsn))
        channel = connection.channel()
        channel.queue_declare(queue=self.queue_name, durable=True)
        channel.exchange_declare(exchange=self.exchange_name, exchange_type="fanout")

        return channel

    def default_callback(self, ch, method, properties, body):
        print("Receive: {}".format(body))

    def listen(self, cb=None, routing_key: str = None):
        cb = cb or self.default_callback

        try:
            self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=routing_key)
            self.channel.basic_consume(on_message_callback=cb, queue=self.queue_name, auto_ack=False)
            print("Waiting for messages. To exit press CTRL+C")
            self.channel.start_consuming()
        except Exception as e:
            print(f"Closing connection due to {e}")

            self.channel.close()

    def publish(self, body: Dict, exchange_name: str, routing_key: str = ""):
        return self.channel.basic_publish(
            # TODO: add smart dt encoder
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(body, default=str).encode("utf-8"),
        )