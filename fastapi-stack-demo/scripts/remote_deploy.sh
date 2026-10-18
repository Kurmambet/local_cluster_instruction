#!/usr/bin/env bash
# Запускается НА СЕРВЕРЕ из каталога проекта (/opt/fastapi-demo). Обычно его вызывает Ansible
# (роль app) или CI:
#   MODE=build bash scripts/remote_deploy.sh   # собрать образы на сервере (тест без реестра)
#   MODE=pull  bash scripts/remote_deploy.sh   # скачать образы из реестра (боевой режим, CI)
set -Eeuo pipefail
cd "$(dirname "$0")/.."

# compose.env — несекретные настройки, secrets.env — пароли (создаёт Ansible)
ENV_ARGS=(--env-file shared/compose.env --env-file shared/secrets.env)
if [ -f shared/images.env ]; then
  ENV_ARGS+=(--env-file shared/images.env)
fi
DC=(docker compose -f docker-compose.fastapi.prod.yml "${ENV_ARGS[@]}")

if [ "${MODE:-build}" = "pull" ]; then
  "${DC[@]}" pull
else
  "${DC[@]}" build
fi
"${DC[@]}" up -d --remove-orphans

echo "Ждём readiness (/readyz)..."
ready=0
for i in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:8000/readyz > /dev/null; then
    ready=1
    break
  fi
  sleep 3
done
if [ "$ready" != 1 ]; then
  echo "API не стал готов за 2 минуты" >&2
  "${DC[@]}" logs --tail=100 api migrate
  exit 1
fi

# Мониторинг запускается, только если для него сгенерирован пароль Grafana
if grep -qs '^GRAFANA_ADMIN_PASSWORD=' shared/secrets.env; then
  docker compose -f monitoring/compose.monitoring.yml \
    --env-file shared/compose.env --env-file shared/secrets.env up -d --remove-orphans
else
  echo "GRAFANA_ADMIN_PASSWORD не задан — мониторинг пропущен"
fi

"${DC[@]}" ps
