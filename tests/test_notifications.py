"""The message for the notification service (its email.confirmation_code v1
contract: BalatroNotificationService/docs/messages.md)."""

import json
from datetime import datetime
from typing import Any

import aio_pika
import pytest

from app.application.exceptions.email import EmailDeliveryFailed
from app.application.ports.confirmation_codes import CodePurpose
from app.domain.value_object.email import Email
from app.infrastructure.notifications.rabbitmq import NotificationServiceCodeSender


class FakeExchange:
    def __init__(self, error: Exception | None = None) -> None:
        self.published: list[tuple[aio_pika.Message, str, bool]] = []
        self.error = error

    async def publish(
        self, message: aio_pika.Message, routing_key: str, mandatory: bool = False
    ) -> None:
        if self.error:
            raise self.error
        self.published.append((message, routing_key, mandatory))


def sender(exchange: FakeExchange) -> NotificationServiceCodeSender:
    s = NotificationServiceCodeSender("amqp://unused")

    async def get_exchange() -> Any:
        return exchange

    s._get_exchange = get_exchange  # type: ignore[method-assign]
    return s


@pytest.mark.anyio
async def test_the_message() -> None:
    exchange = FakeExchange()
    await sender(exchange).send_code(
        Email("Player@Example.com"), CodePurpose.RESET_PASSWORD, "042137"
    )

    message, routing_key, mandatory = exchange.published[0]
    body = json.loads(message.body)
    assert routing_key == "email.confirmation_code" and mandatory
    assert message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
    assert message.content_type == "application/json"
    assert message.message_id == body["id"]
    assert body["type"] == "confirmation_code" and body["version"] == 1
    assert body["to"] == "player@example.com"
    assert body["purpose"] == "reset_password"
    assert body["code"] == "042137"
    assert body["expires_in_minutes"] == 10
    assert datetime.fromisoformat(body["created_at"]).tzinfo is not None


class Unroutable(aio_pika.exceptions.DeliveryError):
    """What RabbitMQ answers when no queue is bound (the notification service
    never ran)."""

    def __repr__(self) -> str:
        return "Unroutable()"


@pytest.mark.anyio
async def test_a_message_rabbitmq_refuses() -> None:
    error = Unroutable(None, None)  # type: ignore[arg-type]
    with pytest.raises(EmailDeliveryFailed):
        await sender(FakeExchange(error)).send_code(
            Email("player@example.com"), CodePurpose.VERIFY_EMAIL, "123456"
        )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
