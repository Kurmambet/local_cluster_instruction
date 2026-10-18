from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.router import api_router, root_router
from src.core.config import settings
from src.core.redis import close_redis
from src.db.base import close_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Приложение НЕ падает на старте, если БД/Redis недоступны: за это отвечает /readyz
    yield
    await close_redis()
    await close_database()


app = FastAPI(
    title="FastAPI stack demo",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(root_router)
app.include_router(api_router)

# /metrics НЕ проксируется nginx наружу — его читает только Prometheus внутри сети Docker
Instrumentator(excluded_handlers=["/metrics", "/livez", "/readyz"]).instrument(
    app
).expose(app, endpoint="/metrics", include_in_schema=False)
