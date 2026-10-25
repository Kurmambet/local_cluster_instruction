# vps-baseline — универсальная настройка VPS под docker-compose проекты

Роли: base, firewall, fail2ban, docker, nginx (+certbot), app_dirs, ssh_hardening.
Плейбуки: `bootstrap.yml` (создать админа) и `site.yml` (всё остальное).
Проект НЕ запускался на реальном сервере: сначала прогоняй на лабораторной ВМ.

## Быстрый старт на лабораторной ВМ (из Terraform-лаборатории)

```bash
    cd vps-baseline
    ansible-playbook site.yml --limit lab-vm --check --diff   # пробный прогон
    ansible-playbook site.yml --limit lab-vm
    ansible-playbook site.yml --limit lab-vm                  # второй раз: ожидаем changed=0
    ssh ubuntu@192.168.100.14 'docker compose version; sudo ufw status; sudo sshd -T | grep -Ei "permitroot|passwordauth"'

    ssh ubuntu@192.168.100.14 'sudo sshd -T | grep -Ei "permitrootlogin|passwordauthentication|allowusers"'
    ssh ubuntu@192.168.100.14 'sudo ufw status verbose; sudo fail2ban-client status sshd'
    curl -I http://192.168.100.14
```

Режим `--check` для ролей docker/nginx частично недостоверен (часть задач зависит от результатов предыдущих).

### если уже зашифровал vault:

```bash
ansible-vault encrypt group_vars/vps/vault.yml     # спросит пароль дважды
ansible-vault view group_vars/vps/vault.yml        # посмотреть
ansible-vault edit group_vars/vps/vault.yml        # править (перешифрует при сохранении)
ansible-playbook site.yml --limit lab-vm --ask-vault-pass
```

на все команды добавляем `--ask-vault-pass`
или же надо содать файл вне гита, где будем хранить пароль:
`~/.vault_pass` (`chmod 600`, вне репозитория) и добавь в `ansible.cfg` строку `vault_password_file = ~/.vault_pass`. Редактируй через `edit`, а не `view`: просмотр выводит содержимое в терминал и оставляет его в истории.

## Реальный VPS

1. Заполни `admin_ssh_public_keys`, `deploy_ssh_public_keys`, `certbot_email`, `nginx_sites` в `group_vars/vps/main.yml`.
2. Секреты: `cp group_vars/vps/vault.yml.example group_vars/vps/vault.yml && ansible-vault encrypt group_vars/vps/vault.yml`.
3. Добавь хост в `inventory/hosts.yml` (ansible_user: root для первого запуска).
4. `ansible-playbook bootstrap.yml --limit prod1 --ask-vault-pass`
5. Поменяй `ansible_user` на `admin_user`, проверь `ssh devops@host`, затем:
   `ansible-playbook site.yml --limit prod1 --ask-vault-pass`
6. DNS домена должен указывать на сервер ДО запуска: иначе certbot упадёт.

## Если потерял доступ по SSH

Используй веб-консоль/VNC провайдера, удали `/etc/ssh/sshd_config.d/10-hardening.conf`,
выполни `systemctl reload ssh`.

## Полезные команды

    ansible-playbook site.yml --tags nginx --limit prod1     # только nginx
    ansible-playbook site.yml --limit prod1 --diff           # показывать изменения файлов
    ansible-inventory --host prod1                           # переменные хоста
    ansible prod1 -b -a "nginx -t"

```










```

Проект лежит в `/opt/fastapi-demo`, а не в домашней папке `ubuntu`.

## Где проект и секреты

Каталог `/opt/fastapi-demo` принадлежит пользователю `deploy` с правами `0750`, и `ubuntu` без `sudo` его не прочитает. Зайди через `sudo` (у `ubuntu` он без пароля):

```bash
ssh ubuntu@192.168.100.14
sudo ls -la /opt/fastapi-demo /opt/fastapi-demo/shared
sudo cat /opt/fastapi-demo/shared/secrets.env
```

В `shared/` лежат четыре файла: `compose.env` (имена БД, `GRAFANA_ADMIN_USER`, `GRAFANA_ROOT_URL`), `api.env` (несекретные настройки), `secrets.env` (сгенерированные пароли и JWT) и пустой маркер `.first_deploy_ok`.

Для Grafana логин `admin`, а пароль возьми одной командой:

```bash
sudo grep GRAFANA_ADMIN_PASSWORD /opt/fastapi-demo/shared/secrets.env
```

В лабораторном конфиге у `/grafana/` нет basic auth в nginx, поэтому вход только один, Grafana. Дашборд «Demo overview» должен подключиться сам.

Заодно поправлю мою подсказку из конца плейбука: она предлагает `ssh deploy@…`, но в лаборатории у `deploy` нет SSH-ключа (список `deploy_ssh_public_keys` пуст). Пока заходи как `ubuntu` с `sudo`. Когда добавишь свой публичный ключ в `deploy_ssh_public_keys`, подсказка заработает.

## Что проверить дальше

- **Идемпотентность.** Запусти `ansible-playbook site.yml --limit lab-vm` ещё раз. Файл `secrets.env` не должен измениться (он создаётся один раз), а сборка должна пропуститься. Принудительный перезапуск: `-e app_force_deploy=true`.
- **Мониторинг.** Prometheus и Alertmanager слушают только `127.0.0.1`. Открой их через SSH-туннель: `ssh -L 9090:127.0.0.1:9090 -L 9093:127.0.0.1:9093 ubuntu@192.168.100.14`, затем `http://localhost:9090/targets` (все цели должны быть `UP`) и `http://localhost:9093`.
- **Счётчик WebSocket.** На главной странице нажми «Подключиться» в нескольких вкладках, затем в Grafana на дашборде посмотри `ws_active_connections`.

В `free -h` у тебя свободно только 158 МБ, но доступно 2,9 ГБ: это кэш файловой системы, которого хватает с запасом. Сборка с запасом уместилась в 4 ГБ.

Для реального проекта сохрани копию `secrets.env`: пароли лежат только на сервере. Если сервер пропадёт, а база с данными будет нужна, без пароля её не открыть.
