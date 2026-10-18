from fastapi import APIRouter

from src.api.routes.system import public_router, router_system
from src.api.routes.tasks import router as tasks_router
from src.api.routes.users import router as users_router
from src.api.routes.ws import router as ws_router

# Пробы и метрики — в корне (их читают Docker/Prometheus, а не пользователи)
root_router = APIRouter()
root_router.include_router(router_system)
root_router.include_router(ws_router)

# Всё, что видит пользователь, — под /api (так nginx проксирует location /api/)
api_router = APIRouter(prefix="/api")
api_router.include_router(public_router)
api_router.include_router(users_router)
api_router.include_router(tasks_router)
