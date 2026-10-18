Шифровать `vault.yml` перед этим прогоном было не обязательно: Ansible читает незашифрованный файл так же, как зашифрованный. Шифрование защищает файл в репозитории, на сам запуск оно не влияет. Отдельно разберём упавший nginx: там простая ошибка в моём шаблоне.

## Как работает vault

**Где лежат секреты.** В файле на твоём компьютере (`group_vars/vps/vault.yml`), а не на сервере. После `ansible-vault encrypt` файл превращается в шифротекст AES-256. Пароль от vault в репозиторий не кладут: его вводят при запуске или хранят в файле вне проекта с правами `600`. Потерянный пароль восстановить нельзя. Сейчас в твоём `vault.yml` лежит открытый текст с заглушкой `change-me`, так что он пока ничего не защищает. Для лаборатории это нормально, но перед тем как отправлять проект куда-либо, зашифруй файл. [ansiblepilot](https://www.ansiblepilot.com/articles/ansible-vault-encrypt-decrypt-secrets-complete-guide-2026)

**Как секреты попадают на сервер.** Ansible расшифровывает значения в памяти на твоём ноутбуке и передаёт их модулям. На сервер они попадают в том виде, в каком их пишут задачи: [digitalocean](https://www.digitalocean.com/community/tutorials/how-to-use-vault-to-protect-sensitive-ansible-data)

- **Пароль для basic auth.** Модуль `htpasswd` записывает в `/etc/nginx/.htpasswd` хеш, а не сам пароль.
- **Env-файлы приложений.** Роль `app_dirs` пишет значения из `apps[].env_files` в `/opt/<проект>/shared/` открытым текстом с правами `0600` для пользователя `deploy`. Приложению нужен именно открытый пароль.

Vault защищает данные только в состоянии покоя: после расшифровки он ничем не помогает. Поэтому в задачах с секретами стоит `no_log: true`, чтобы значения не попали в вывод. [habr](https://habr.com/ru/companies/otus/articles/722106/)

**Что туда записывать.** Только то, что действительно секретно: пароли БД, Grafana и basic auth, `APP_SECRET_KEY`, токены, приватные ключи TLS. Публичные ключи SSH, домены, порты и обычные настройки шифровать не нужно. Принято называть секретные переменные с префиксом `vault_` и ссылаться на них из обычных файлов: `POSTGRES_PASSWORD: "{{ vault_myapp_db_password }}"`. Тогда сразу видно, что откуда берётся. Сейчас в нашем проекте `nginx_basic_auth_password` лежит прямо в `vault.yml`, и для лаборатории это допустимо. Пароли генерируй случайными, например командой `openssl rand -hex 24` (в hex нет спецсимволов, которые ломают URL подключения к БД). [ansiblepilot](https://www.ansiblepilot.com/articles/ansible-vault-encrypt-decrypt-secrets-complete-guide-2026)

## Команды

```bash
ansible-vault encrypt group_vars/vps/vault.yml     # спросит пароль дважды
ansible-vault view group_vars/vps/vault.yml        # посмотреть
ansible-vault edit group_vars/vps/vault.yml        # править (перешифрует при сохранении)
ansible-playbook site.yml --limit lab-vm --ask-vault-pass
```

Если запустить плейбук без пароля после шифрования, Ansible ответит `Attempting to decrypt but no vault secrets found`. Чтобы не вводить пароль каждый раз, создай файл `~/.vault_pass` (`chmod 600`, вне репозитория) и добавь в `ansible.cfg` строку `vault_password_file = ~/.vault_pass`. Редактируй через `edit`, а не `view`: просмотр выводит содержимое в терминал и оставляет его в истории. [stackharbor](https://stackharbor.com/en/knowledge-base/ansible-vault-secrets/)

В нашем `.gitignore` файл `vault.yml` стоит в списке игнорируемых, поэтому он не попадёт в git даже зашифрованным. Если захочешь версионировать зашифрованный файл, убери эту строку: зашифрованные vault-файлы в git хранить можно, нельзя хранить только пароль от них. [khimananda](https://khimananda.com/blog/ansible-vault-for-secrets)

## Ошибка nginx

Дубль директивы `gzip` — это мой недосмотр. В стандартном `/etc/nginx/nginx.conf` Ubuntu уже есть `gzip on;`, а я добавил то же самое в `00-global.conf`. Исправление: удали строку `gzip on;` из `roles/nginx/templates/00-global.conf.j2`. Остальные `gzip_*` оставь, они не дублируются. Затем снова запусти плейбук: он перезапишет шаблон, пройдёт `nginx -t`, перезагрузит nginx и дойдёт до ролей `app_dirs` и `ssh_hardening`, которые ещё не выполнялись.

Всё, что было до этой ошибки, во втором прогоне прошло с `changed=0`: идемпотентность работает. Сам nginx сейчас продолжает работать на старой конфигурации, потому что перезагрузка не выполнялась. Предупреждение про `remote_tmp` безвредно: оно появляется, когда Ansible создаёт временный каталог для `root`. Пришли вывод следующего запуска.
