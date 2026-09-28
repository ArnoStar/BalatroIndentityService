from collections.abc import AsyncGenerator

import aio_pika

from app.infrastructure.config.settings import settings


async def get_rabbitmq_chanel() -> AsyncGenerator[aio_pika.abc.AbstractChannel]:
    connection = await aio_pika.connect_robust(
        settings.rabbitmq_uri,
    )
    async with connection:
        channel = await connection.channel()

        yield channel
