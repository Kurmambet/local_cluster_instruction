from prometheus_client import Counter, Gauge

# Число активных WebSocket-подключений ЭТОГО процесса (см. README: про несколько воркеров)
WS_ACTIVE = Gauge("ws_active_connections", "Active WebSocket connections")
TASKS_ENQUEUED = Counter(
    "celery_tasks_enqueued_total", "Celery tasks enqueued by the API", ["task"]
)
