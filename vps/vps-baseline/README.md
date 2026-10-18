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
