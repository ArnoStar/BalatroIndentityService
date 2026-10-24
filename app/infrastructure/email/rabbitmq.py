import asyncio
import json
import logging

import aio_pika
from aio_pika.abc import AbstractExchange, AbstractRobustConnection

from app.application.exceptions.email import EmailDeliveryFailed
from app.application.ports.email_sender import EmailSender
from app.domain.value_object.email import Email

log = logging.getLogger(__name__)

EXCHANGE = "notifications"
QUEUE = "email_worker_queue"
ROUTING_KEY = "email.send"


class RabbitMqEmailSender(EmailSender):
    """Publishes ``{"email", "subject", "body"}`` (JSON) to the durable
    ``notifications`` exchange, routing key ``email.send``, bound to the
    ``email_worker_queue`` queue, for a mail worker to deliver. One connection
    for the whole process, opened at the first email."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._connection: AbstractRobustConnection | None = None
        self._exchange: AbstractExchange | None = None
        self._lock = asyncio.Lock()

    async def _get_exchange(self) -> AbstractExchange:
        async with self._lock:
            if self._exchange is None:
                self._connection = await aio_pika.connect_robust(self.url)
                channel = await self._connection.channel()
                exchange = await channel.declare_exchange(
                    EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True
                )
                queue = await channel.declare_queue(QUEUE, durable=True)
                await queue.bind(exchange, routing_key=ROUTING_KEY)
                self._exchange = exchange
            return self._exchange

    async def send(self, email: Email, subject: str, body: str) -> None:
        message = aio_pika.Message(
            body=json.dumps(
                {"email": email.value, "subject": subject, "body": body}
            ).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        try:
            exchange = await self._get_exchange()
            await exchange.publish(message, routing_key=ROUTING_KEY)
        except (OSError, aio_pika.exceptions.AMQPError) as exc:
            log.exception("could not publish the email to RabbitMQ")
            raise EmailDeliveryFailed from exc

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
