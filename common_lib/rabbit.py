import json
from dataclasses import dataclass
from functools import partial
from logging import getLogger
from typing import Callable, Dict, List

import pika
from django.conf import settings

logger = getLogger(__name__)


class RabbitMQPublisher:
    def __init__(self, exchange_name: str, dsn: str = settings.RABBITMQ_DSN) -> None:
        self.exchange_name = exchange_name
        self.dsn = dsn
        self.exchange_type = "fanout"
        self.channel = self.connect()

    def connect(self):
        connection = pika.BlockingConnection(pika.URLParameters(self.dsn))
        channel = connection.channel()
        channel.exchange_declare(
            exchange=self.exchange_name, exchange_type=self.exchange_type
        )
        return channel

    def publish(self, body: Dict):
        return self.channel.basic_publish(
            exchange=self.exchange_name,
            body=json.dumps(body, default=str).encode("utf-8"),
            routing_key='',
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
        self,
        dsn: str = settings.RABBITMQ_DSN,
        consumers: List[ConsumerConfig] = None,
        auto_ack: bool = False,
    ) -> None:
        self.dsn = dsn
        self.consumers = consumers or []
        self._connections = {}
        self.auto_ack = auto_ack

    def connect(self):
        parameters = pika.URLParameters(self.dsn)
        connection = pika.SelectConnection(
            parameters=parameters, on_open_callback=self.on_connected
        )
        return connection

    def on_connected(self, connection):
        """Called when we are fully connected to RabbitMQ"""
        for consumer in self.consumers:
            logger.debug(f"creating channel for {consumer=}")
            connection.channel(
                on_open_callback=partial(self.on_channel_open, consumer=consumer)
            )

    def on_channel_open(self, channel, consumer: ConsumerConfig):
        """Called when our channel has opened"""
        self._connections[consumer] = channel
        channel.exchange_declare(
            consumer.exchange, exchange_type=consumer.exchange_type, auto_delete=False
        )

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
        self._connections[consumer].basic_consume(
            consumer.queue, cb, auto_ack=self.auto_ack
        )

    def listen(self):
        connection = self.connect()
        try:
            connection.ioloop.start()
        except (KeyboardInterrupt, Exception):
            connection.close()
