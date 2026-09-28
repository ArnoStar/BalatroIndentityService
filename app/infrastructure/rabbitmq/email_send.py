import json

import aio_pika

from app.application.ports.email_sender import EmailSender
from app.domain.value_object.email import Email


class RabbitMqEmailSender(EmailSender):
    def __init__(
        self,
        chanel: aio_pika.abc.AbstractChannel,
    ) -> None:
        self.chanel = chanel

    async def send(
        self,
        email: Email,
        subject: str,
        body: str,
    ) -> None:
        message = aio_pika.Message(
            body=json.dumps(
                {
                    "email": email.value,
                    "subject": subject,
                    "body": body,
                }
            ).encode(),
            content_type="application/json",
        )

        queue = await self.chanel.declare_queue(
            name="email_worker_queue", durable=True, auto_delete=False
        )

        exchange = await self.chanel.declare_exchange(
            "notifications",
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        await queue.bind(exchange=exchange, routing_key="email.send")

        await exchange.publish(
            message,
            routing_key="email.send",
        )
