from dataclasses import dataclass
from functools import partial
import json
from logging import getLogger
from typing import Callable, Dict, List
import pika
from django.conf import settings


logger = getLogger(__name__)


class RabbitMQPublisher:
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
        logger.info("Receive: {}".format(body))

    def listen(self, cb=None, routing_key: str = None):
        cb = cb or self.default_callback

        try:
            self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=routing_key)
            self.channel.basic_consume(on_message_callback=cb, queue=self.queue_name, auto_ack=False)
            logger.info("Waiting for messages. To exit press CTRL+C")
            self.channel.start_consuming()
        except Exception as e:
            logger.info(f"Closing connection due to {e}")
            self.channel.close()

    def publish(self, body: Dict, exchange_name: str, routing_key: str = ""):
        return self.channel.basic_publish(
            # TODO: add smart dt encoder
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(body, default=str).encode("utf-8"),
        )


@dataclass
class ConsumerConfig:
    exchange: str
    queue: str
    callback: Callable
    exchange_type: str = "fanout"

    def __hash__(self) -> int:
        return hash(self.exchange) + hash(self.queue)


class RabbitMQMultiConsumer:
    """Allows to attach multiple consumers for multiple exchange/queue pairs"""

    def __init__(
        self, dsn: str = settings.RABBITMQ_DSN, consumers: List[ConsumerConfig] = None, auto_ack: bool = False
    ) -> None:
        self.dsn = dsn
        self.consumers = consumers or []
        self._connections = {}
        self.auto_ack = auto_ack

    def connect(self):
        parameters = pika.URLParameters(self.dsn)
        connection = pika.SelectConnection(parameters=parameters, on_open_callback=self.on_connected)
        return connection

    def on_connected(self, connection):
        """Called when we are fully connected to RabbitMQ"""
        for consumer in self.consumers:
            logger.debug(f"creating channel for {consumer=}")
            connection.channel(on_open_callback=partial(self.on_channel_open, consumer=consumer))

    def on_channel_open(self, channel, consumer: ConsumerConfig):
        """Called when our channel has opened"""
        self._connections[consumer] = channel
        channel.queue_declare(
            queue=consumer.queue,
            durable=True,
            exclusive=True,
            auto_delete=False,
            callback=partial(self.on_queue_declared, consumer=consumer),
        )
        channel.queue_bind(exchange=consumer.exchange, queue=consumer.queue)

    def _custom_ack(self, ch, method, properties, body, consumer_cb: Callable):
        consumer_cb(ch, method, properties, body)
        ch.basic_ack(method.delivery_tag)

    def on_queue_declared(self, frame, consumer: ConsumerConfig):
        """Called when RabbitMQ has told us our Queue has been declared, frame is the response from RabbitMQ"""
        cb = partial(self._custom_ack, consumer_cb=consumer.callback)
        self._connections[consumer].basic_consume(consumer.queue, cb, auto_ack=self.auto_ack)

    def listen(self):
        connection = self.connect()
        try:
            connection.ioloop.start()
        except (KeyboardInterrupt, Exception):
            connection.close()
