import time

from src.worker.celery_app import celery_app


@celery_app.task(name="tasks.slow_add")
def slow_add(a: int, b: int) -> int:
    """Имитация долгой работы: нужна, чтобы увидеть статусы PENDING -> STARTED -> SUCCESS."""
    time.sleep(3)
    return a + b
