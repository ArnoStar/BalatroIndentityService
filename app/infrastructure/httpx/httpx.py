from collections.abc import AsyncGenerator

from httpx import AsyncClient


async def get_httpx_client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient() as client:
        yield client
