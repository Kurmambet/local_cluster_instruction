from redis.asyncio import Redis

from src.core.config import settings

redis_client: Redis = Redis.from_url(settings.redis_url(0), decode_responses=True)


async def close_redis() -> None:
    await redis_client.aclose()
