from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "app",
    broker=settings.redis_url(1),
    backend=settings.redis_url(2),
    include=["src.worker.tasks"],
)
celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    timezone="UTC",
    enable_utc=True,
)
