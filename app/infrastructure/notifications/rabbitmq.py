"""Hands confirmation codes to the notification service
(BalatroNotificationService) through RabbitMQ. The message is its
``email.confirmation_code`` v1 contract (its docs/messages.md)."""

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime

import aio_pika
from aio_pika.abc import AbstractExchange, AbstractRobustConnection

from app.application.exceptions.email import EmailDeliveryFailed
from app.application.ports.code_sender import CodeSender
from app.application.ports.confirmation_codes import CODE_LIFETIME_MINUTES, CodePurpose
from app.domain.value_object.email import Email

log = logging.getLogger(__name__)

EXCHANGE = "notifications"
CONFIRMATION_CODE = "email.confirmation_code"


class NotificationServiceCodeSender(CodeSender):
    """Publishes to the durable ``notifications`` exchange, persistent, with
    publisher confirms and ``mandatory``: a message RabbitMQ didn't store, or
    couldn't route (the notification service never declared its queue), is
    EmailDeliveryFailed, so the user is told to ask for another code. One
    connection for the process, opened at the first code."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._connection: AbstractRobustConnection | None = None
        self._exchange: AbstractExchange | None = None
        self._lock = asyncio.Lock()

    async def _get_exchange(self) -> AbstractExchange:
        async with self._lock:
            if self._exchange is None:
                self._connection = await aio_pika.connect_robust(self.url)
                channel = await self._connection.channel(
                    publisher_confirms=True, on_return_raises=True
                )
                self._exchange = await channel.declare_exchange(
                    EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True
                )
            return self._exchange

    async def send_code(self, email: Email, purpose: CodePurpose, code: str) -> None:
        message_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        body = {
            "type": "confirmation_code",
            "version": 1,
            "id": message_id,
            "to": email.value,
            "purpose": purpose.value,
            "code": code,
            "created_at": now.isoformat(),
            "expires_in_minutes": CODE_LIFETIME_MINUTES,
        }
        try:
            exchange = await self._get_exchange()
            await exchange.publish(
                aio_pika.Message(
                    body=json.dumps(body).encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=message_id,
                    type="confirmation_code",
                    timestamp=now,
                    app_id="balatro-identity",
                ),
                routing_key=CONFIRMATION_CODE,
                mandatory=True,
            )
        except (OSError, aio_pika.exceptions.AMQPError) as exc:
            log.error(
                "the notification service didn't get the %s code: %r", purpose, exc
            )
            raise EmailDeliveryFailed from exc

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
