# fastapi-stack-demo

Тестовый проект под плейбук `vps-baseline`: FastAPI + PostgreSQL (asyncpg, SQLAlchemy, Alembic) +
Redis + Celery + Vue 3/Vite/TypeScript + Prometheus/Grafana/Alertmanager.

## Что где лежит

| Путь                              | Назначение                                                                                                                                                |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/`                            | Код FastAPI: `api/routes` (system, users, tasks, ws), `core` (config, security, redis, metrics), `db`, `models`, `schemas`, `services`, `worker` (Celery) |
| `alembic/`                        | Миграции (`versions/0001_create_users.py`)                                                                                                                |
| `frontend/`                       | Vue-приложение, свой `Dockerfile` и `nginx.conf` (только статика)                                                                                         |
| `Dockerfile.fastapi`              | Один образ для api, migrate и worker                                                                                                                      |
| `docker-compose.fastapi.dev.yml`  | Локальная разработка                                                                                                                                      |
| `docker-compose.fastapi.prod.yml` | Сервер (тест или прод)                                                                                                                                    |
| `monitoring/`                     | Prometheus, Alertmanager, Grafana (дашборд и источник данных подключаются сами)                                                                           |
| `scripts/`                        | `remote_deploy.sh` (выполняется на сервере), `deploy_test.sh` (ручной тест без CI)                                                                        |
| `.github/workflows/ci.yml`        | Пример CI/CD: тесты, сборка образов в GHCR, деплой по SSH                                                                                                 |
| `ansible/`                        | Куски конфигурации для `vps-baseline` (хост-переменные, vault)                                                                                            |

Пробы: `GET /livez` (процесс жив, зависимости НЕ проверяет) и `GET /readyz` (проверяет PostgreSQL и Redis, при сбое отвечает 503).
Nginx хоста наружу их не проксирует; для страницы статуса есть `GET /api/status` (то же, что `/readyz`).
`/metrics` тоже не проксируется наружу: его читает только Prometheus внутри сети Docker.

## Секреты: что, где, как доставляется

| Секрет                                             | Источник правды                                                     | Как попадает на сервер                                                             | Кто читает                                                                    |
| -------------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Пароль PostgreSQL, пароль Redis                    | `vault.yml` (`vault_demo_db_password`, `vault_demo_redis_password`) | Ansible (роль `app_dirs`) пишет `/opt/fastapi-demo/shared/compose.env`, права 0600 | `docker compose` подставляет в `db`, `redis` и в окружение api/migrate/worker |
| JWT-секрет                                         | `vault.yml` (`vault_demo_jwt_secret`)                               | `shared/api.env`                                                                   | api, migrate, worker (`env_file`)                                             |
| Пароль Grafana                                     | `vault.yml`                                                         | `shared/monitoring.env`                                                            | Grafana                                                                       |
| Пароль basic auth для `/grafana/`                  | `vault.yml` (`nginx_basic_auth_password`)                           | Хеш в `/etc/nginx/.htpasswd`                                                       | nginx хоста                                                                   |
| Приватный ключ деплоя                              | GitHub Secrets `DEPLOY_SSH_PRIVATE_KEY`                             | Не попадает на сервер                                                              | CI                                                                            |
| Публичный ключ деплоя                              | `deploy_ssh_public_keys` в Ansible                                  | `authorized_keys` пользователя `deploy`                                            | sshd                                                                          |
| `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KNOWN_HOSTS` | GitHub Secrets                                                      | Не попадают на сервер                                                              | CI                                                                            |
| Токен чтения GHCR                                  | Вводится один раз на сервере: `docker login ghcr.io`                | `~/.docker/config.json` пользователя `deploy`                                      | `docker compose pull`                                                         |

Не секреты (лежат открыто в `host_vars`): имя и пользователь БД, `FASTAPI_DEBUG`, размеры пулов.
`src/.env` существует только на ноутбуке для разработки и в git не попадает.

## Первый запуск

1. Создай lock-файлы (я не мог их сгенерировать офлайн): `uv lock`, затем `cd frontend && npm install`. Закоммить `uv.lock` и `frontend/package-lock.json`: Dockerfile-ы используют `uv sync --frozen` и `npm ci`.
2. Разработка: `cp src/.env.example src/.env`, затем
   `docker compose -f docker-compose.fastapi.dev.yml --env-file src/.env up --build`.
   Frontend: `cd frontend && cp .env.example .env && npm run dev`.
   Тесты: `uv run pytest`. Линтер: `uv run ruff check .`.

## Тест на лабораторной ВМ (без CI)

1. Дай тестовой ВМ 4 ГБ ОЗУ (`memory = 4096` в Terraform для `vps1`): на 2 ГБ сборка frontend и мониторинг не поместятся. Либо убери блок `monitoring.env` из `apps` и собирай образы на своём ноутбуке.
2. В `vps-baseline`: замени `host_vars/lab-vm.yml` содержимым `ansible/host_vars_lab-vm.example.yml` (впиши свой публичный ключ), добавь значения из `ansible/vault.yml.add.example` в vault.
3. `ansible-playbook site.yml --limit lab-vm --tags apps,nginx`
4. `bash scripts/deploy_test.sh deploy@192.168.100.14`
5. Проверка: `curl http://192.168.100.14/api/status`; в браузере `http://192.168.100.14/` (регистрация, задача Celery, WebSocket) и `http://192.168.100.14/grafana/` (сначала пароль nginx, затем вход в Grafana).

На сервере сборка идёт прямо там (`MODE=build`). Это допустимо для теста, но для боя собирай образы в CI (`MODE=pull`).

## Что изменено по сравнению с исходным проектом

| Было                                         | Стало                                                | Почему                                                    |
| -------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------- |
| `/health`, `/health/ready`                   | `/livez`, `/readyz` (+ Redis)                        | Liveness не должен зависеть от БД                         |
| `init_db()` на старте приложения             | Убрано                                               | Падение при недоступной БД; это работа readiness          |
| `env_file: src/.env` у контейнера БД         | БД получает только свои `POSTGRES_*`                 | Принцип минимальных прав                                  |
| Дубли `POSTGRES_*` и `FASTAPI_POSTGRES_*`    | Один набор `FASTAPI_*`                               | Один источник правды                                      |
| gunicorn `-w 4`, `curl` в образе             | Один uvicorn, проверка через python                  | Экономия памяти; счётчик WebSocket и `/metrics` корректны |
| `uv:latest`                                  | Параметр `UV_VERSION` (в CI закрепи)                 | Воспроизводимость                                         |
| Миграции в `entrypoint.sh`                   | Отдельный сервис `migrate`                           | Нет гонок при нескольких репликах                         |
| `User.id == sub` (строка)                    | `uuid.UUID(sub)`                                     | Корректное сравнение с UUID-колонкой                      |
| `%` в пароле ломал Alembic                   | Экранирование `%%` в `env.py`                        | `configparser` интерполирует `%`                          |
| В `pyproject.toml` не было `pyjwt`, `pwdlib` | Добавлены `pyjwt`, `pwdlib[argon2]`, `celery[redis]` | Код их импортирует                                        |

## Ограничение: несколько процессов

Счётчик WebSocket и метрики живут в памяти процесса. Один uvicorn-процесс считает всё верно. Если запустишь несколько воркеров или реплик, счётчик станет «по процессу». Тогда переведи его на Redis (`INCR`/`DECR` и pub/sub) или включи multiprocess-режим `prometheus_client`.
