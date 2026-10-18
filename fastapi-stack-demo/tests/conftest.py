import os

# Переменные должны быть заданы ДО импорта src.* (Settings читает их при импорте)
os.environ.update(
    {
        "FASTAPI_DEBUG": "false",
        "FASTAPI_JWT_SECRET_KEY": "test-secret-key-test-secret-key-0000",
        "FASTAPI_POSTGRES_DB": "test",
        "FASTAPI_POSTGRES_USER": "test",
        "FASTAPI_POSTGRES_PASSWORD": "test",
        "FASTAPI_POSTGRES_HOST": "localhost",
        "FASTAPI_REDIS_HOST": "localhost",
        "FASTAPI_REDIS_PASSWORD": "test",
    }
)
