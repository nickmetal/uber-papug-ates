import json
from dataclasses import dataclass, field
from functools import partial
from logging import getLogger
from typing import Callable, Dict, List

import pika
import pika.channel

logger = getLogger(__name__)


class RabbitMQPublisher:
    def __init__(self, exchange_name: str, dsn: str) -> None:
        self.exchange_name = exchange_name
        self.dsn = dsn
        self.exchange_type = "fanout"
        self.channel = self.connect()

    def connect(self):
        connection = pika.BlockingConnection(pika.URLParameters(self.dsn))
        channel = connection.channel()
        channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type)
        return channel

    def publish(self, body: Dict):
        if self.channel.is_closed():
            logger.warning("reconnecting")
            self.channel = self.connect()

        return self.channel.basic_publish(
            exchange=self.exchange_name,
            body=json.dumps(body, default=str).encode("utf-8"),
            routing_key="",
        )


@dataclass
class ConsumerConfig:
    exchange: str
    queue: str
    callback: Callable
    exchange_type: str = "fanout"
    # see more https://www.rabbitmq.com/streams.html
    queue_arguments: dict = field(default_factory=lambda: {"x-queue-type": "stream"})
    queue_consume_arguments: dict = field(default_factory=lambda: {"x-stream-offset": "first", "prefetch-count": 10})

    def __hash__(self) -> int:
        return hash(self.exchange) + hash(self.queue)


class RabbitMQMultiConsumer:
    """Allows to attach multiple consumers for multiple exchange/queue pairs"""

    def __init__(
        self,
        dsn: str,
        consumers: List[ConsumerConfig] = None,
        auto_ack: bool = False,
    ) -> None:
        self.dsn = dsn
        self.consumers = consumers or []
        self._connections: Dict[ConsumerConfig, pika.channel.Channel] = {}
        self.auto_ack = auto_ack
        self._prefetch_default = 1

    def listen(self):
        """Run infinite event loop with scheduler consumers"""
        connection = self._connect()
        try:
            connection.ioloop.start()
        except (KeyboardInterrupt, Exception):
            connection.close()

    def _connect(self):
        parameters = pika.URLParameters(self.dsn)
        connection = pika.SelectConnection(parameters=parameters, on_open_callback=self._on_connected)
        return connection

    def _on_connected(self, connection):
        """Called when we are fully connected to RabbitMQ"""
        for consumer in self.consumers:
            logger.debug(f"creating channel for {consumer=}")
            connection.channel(on_open_callback=partial(self._on_channel_open, consumer=consumer))

    def _on_qos_setup(self, method, consumer: ConsumerConfig):
        self._connections[consumer].exchange_declare(
            consumer.exchange, exchange_type=consumer.exchange_type, auto_delete=False
        )

        self._connections[consumer].queue_declare(
            queue=consumer.queue,
            durable=True,
            auto_delete=False,
            arguments=consumer.queue_arguments,
            callback=partial(self._on_queue_declared, consumer=consumer),
        )
        self._connections[consumer].queue_bind(exchange=consumer.exchange, queue=consumer.queue)

    def _on_channel_open(self, channel: pika.channel.Channel, consumer: ConsumerConfig):
        """Called when our channel has opened"""
        if consumer in self._connections:
            raise ValueError(f"Consumer should be added once: {consumer}")
        self._connections[consumer] = channel
        channel.basic_qos(
            prefetch_count=self._prefetch_default, callback=partial(self._on_qos_setup, consumer=consumer)
        )

    def _custom_ack(self, ch: pika.channel.Channel, method, properties, body, consumer_cb: Callable):
        consumer_cb(ch, method, properties, body)
        ch.basic_ack(method.delivery_tag)

    def _on_queue_declared(self, frame, consumer: ConsumerConfig):
        """Called when RabbitMQ has told us our Queue has been declared, frame is the response from RabbitMQ"""
        cb = partial(self._custom_ack, consumer_cb=consumer.callback)
        self._connections[consumer].basic_consume(
            consumer.queue,
            cb,
            auto_ack=self.auto_ack,
            arguments=consumer.queue_consume_arguments,
        )
