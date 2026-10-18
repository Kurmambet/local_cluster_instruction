from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base import get_db_session
from src.schemas.schemas import LivenessResponse, ReadinessResponse
from src.services.readiness import run_readiness_checks

DbSession = Annotated[AsyncSession, Depends(get_db_session)]

router_system = APIRouter(tags=["system"])
public_router = APIRouter(tags=["system"])


@router_system.get("/livez", response_model=LivenessResponse)
async def livez() -> LivenessResponse:
    """Liveness: процесс жив. НЕ ходит в зависимости (иначе сбой БД перезапускал бы приложение)."""
    return LivenessResponse(status="ok")


@router_system.get("/readyz", response_model=ReadinessResponse)
async def readyz(response: Response, db: DbSession) -> ReadinessResponse:
    """Readiness: приложение и его зависимости готовы принимать трафик."""
    checks = await run_readiness_checks(db)
    ready = all(value == "ok" for value in checks.values())
    if not ready:
        response.status_code = 503
    return ReadinessResponse(ready=ready, checks=checks)


@public_router.get("/status", response_model=ReadinessResponse)
async def public_status(response: Response, db: DbSession) -> ReadinessResponse:
    """То же, что /readyz, но доступно через nginx (для страницы статуса во фронтенде)."""
    return await readyz(response, db)
