from redis.asyncio import Redis

from app.infrastructure.config.settings import settings

redis = Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
