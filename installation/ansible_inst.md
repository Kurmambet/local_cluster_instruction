## Установка Ansible через uv

```bash
uv python list
# надо 3.12 >=

uv tool install --with-executables-from ansible-core ansible
uv tool update-shell
exec $SHELL -l

# which ansible ansible-lint

ansible --version
# ansible-lint --version


# uv tool install --force --with ansible-lint --with-executables-from ansible-core,ansible-lint ansible ненадо это выполнять. это переустановит инструмент.
```

- Пакет `ansible` сам не даёт команд, это набор коллекций поверх `ansible-core`. Поэтому нужен флаг `--with-executables-from ansible-core`. Он выставляет в PATH `ansible`, `ansible-playbook`, `ansible-galaxy`, `ansible-vault` и остальные. Без него uv скажет, что у пакета нет исполняемых файлов.
- `uv tool update-shell` добавляет `~/.local/bin` в PATH. Если `ansible` и так находится, этот шаг можно пропустить.
- Если нужен только движок без коллекций: `uv tool install ansible-core`.

## Почему не обычный pip

На Ubuntu 24.04 (и на Mint на её основе) системный `pip install ...` вне venv упрётся в ошибку `externally-managed-environment`. Системный Python защищён от таких установок. Поэтому для CLI-программ используют изолированные инструменты: `uv tool`, `pipx` или venv. Для твоих проектов с `uv venv` и `uv add` ничего не меняется.

## Управление

```bash
uv tool list                 # что установлено
uv tool upgrade ansible      # обновление
uv tool uninstall ansible    # удаление
```

тест:

```bash
mkdir -p ~/ansible-lab && cd ~/ansible-lab
printf '%s\n' '[local]' 'localhost ansible_connection=local' > inventory.ini
printf '%s\n' '[defaults]' 'inventory = ./inventory.ini' 'interpreter_python = auto_silent' > ansible.cfg
ansible all -m ansible.builtin.ping
```

В ответе должно быть `"ping": "pong"`. Это проверка запуска модуля, а не сетевой ICMP-пинг.
