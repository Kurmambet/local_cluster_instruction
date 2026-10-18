import asyncio

from celery.result import AsyncResult
from fastapi import APIRouter, status

from src.core.metrics import TASKS_ENQUEUED
from src.schemas.schemas import AddRequest, TaskCreated, TaskStatus
from src.worker.celery_app import celery_app
from src.worker.tasks import slow_add

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/add", response_model=TaskCreated, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_add(payload: AddRequest) -> TaskCreated:
    # delay() синхронный (ходит в Redis) — не блокируем event loop
    result = await asyncio.to_thread(slow_add.delay, payload.a, payload.b)
    TASKS_ENQUEUED.labels(task="slow_add").inc()
    return TaskCreated(task_id=result.id)


@router.get("/{task_id}", response_model=TaskStatus)
async def task_status(task_id: str) -> TaskStatus:
    def read() -> TaskStatus:
        res = AsyncResult(task_id, app=celery_app)
        return TaskStatus(
            task_id=task_id,
            state=res.state,
            result=res.result if res.successful() else None,
            error=str(res.result) if res.failed() else None,
        )

    return await asyncio.to_thread(read)
