#!/usr/bin/env bash
# Тестовый деплой без CI: копирует проект на сервер и запускает сборку там.
#   bash scripts/deploy_test.sh deploy@192.168.100.14 [/opt/fastapi-demo]
# shared/ НЕ трогаем (там секреты от Ansible), поэтому --exclude shared.
set -Eeuo pipefail
HOST="${1:?usage: $0 user@host [/opt/fastapi-demo]}"
DIR="${2:-/opt/fastapi-demo}"
cd "$(dirname "$0")/.."

rsync -az --delete \
  --exclude shared --exclude .git --exclude node_modules --exclude .venv \
  --exclude 'src/.env' --exclude 'frontend/dist' --exclude '__pycache__' \
  ./ "$HOST:$DIR/"
ssh "$HOST" "cd $DIR && MODE=build bash scripts/remote_deploy.sh"
