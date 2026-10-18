import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.redis import redis_client

CHECK_TIMEOUT_SECONDS = 2


async def run_readiness_checks(session: AsyncSession) -> dict[str, str]:
    """Проверяет зависимости. Readiness = «можно принимать трафик»."""

    async def check_database() -> None:
        await session.execute(text("SELECT 1"))

    async def check_redis() -> None:
        await redis_client.ping()

    results: dict[str, str] = {}
    for name, check in (("database", check_database), ("redis", check_redis)):
        try:
            await asyncio.wait_for(check(), timeout=CHECK_TIMEOUT_SECONDS)
            results[name] = "ok"
        except Exception:  # noqa: BLE001 - любая ошибка зависимости означает «не готов»
            results[name] = "unavailable"
    return results
