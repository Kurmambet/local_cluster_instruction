## Какой провайдер выбрать

Что подходит, зависит от ОС ноутбука:

- **Linux** — libvirt-провайдер. Это основной вариант. Последняя версия 0.9.9. Он умеет скачивать cloud-образ по URL, несколько сетей и несколько интерфейсов у одной ВМ, cloud-init. [registry.terraform](https://registry.terraform.io/providers/dmacvicar/libvirt/latest/docs)
- **Windows** — libvirt/KVM там нет. Есть community-провайдеры для VirtualBox, например `terra-farm/virtualbox`: до 4 адаптеров на ВМ, типы `nat`, `hostonly`, `bridged`. Но он давно не развивается, и его образы ищут через Vagrant-боксы. Для обучения Terraform на Windows надёжнее поставить Ubuntu в WSL2 или запустить Linux-хост. [terra-farm.github](https://terra-farm.github.io/provider-virtualbox/reference/resource_vm.html)

Ниже вариант для Linux. Если у тебя Windows, скажи, и я разберу его отдельно.

## Важно про версии провайдера

С v0.9.0 провайдер полностью переписан и **несовместим** со старым 0.8.x. HCL теперь почти 1:1 повторяет libvirt XML, поэтому описания стали многословнее. Большинство туториалов в интернете написаны под 0.7/0.8. Я привожу конфиг в стиле 0.8.x и закрепляю версию, потому что этот синтаксис я знаю. Для 0.9.x используй [примеры в репозитории](https://github.com/dmacvicar/terraform-provider-libvirt/tree/main/examples) и документацию ресурса `libvirt_domain`. Конфиг ниже я не запускал, поэтому возможны мелкие правки. [github](https://github.com/dmacvicar/terraform-provider-libvirt/discussions/1194)

## Подготовка (один раз)

```bash
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients genisoimage
sudo usermod -aG libvirt $USER   # перелогиниться
ssh-keygen -t ed25519            # если ключа ещё нет
```

Terraform ставится отдельно, из репозитория HashiCorp или через бинарник, но в рф он заблокирован, поэтому установка через зеркало описана в tf_inst.md. (см. [инструкцию](tf_inst.md))

## Запуск

```bash
terraform init
terraform plan
terraform apply
ssh ubuntu@192.168.100.11
ip a                # должны быть 2 интерфейса
terraform destroy   # снести всё и пересоздать за минуту
```

## 1. Починить доступ к libvirt

`libvirt` и `libvirt-daemon` — не команды. Демон называется `libvirtd`, а управляют им через `virsh`. Проверь:

```bash
id | grep libvirt          # пусто = сессия не знает про группу
newgrp libvirt             # временно войти в группу в этом терминале
virsh -c qemu:///system list --all
```

Пустая таблица без ошибок — значит всё хорошо. Чтобы не вводить `newgrp` каждый раз, один раз выйди из сессии и зайди снова (или перезагрузись). Если сокета нет или демон не запущен:

```bash
sudo systemctl enable --now libvirtd
```

Заодно проверь, есть ли пул хранилища:

```bash
virsh -c qemu:///system pool-list --all
```

В Ubuntu-пакете пула `default` может не оказаться. Поэтому в конфиге ниже я создаю свой пул, а не рассчитываю на него.

## 2. Что делать с кодом

Запуск:

```bash
terraform fmt
terraform validate
terraform plan      # должно быть около 13 ресурсов к созданию
terraform apply
```

Первый apply займёт несколько минут: скачивается образ примерно на 600 МБ. Потом проверь:

```bash
ssh ubuntu@192.168.100.11
ip -br a          # nic0 192.168.100.11, nic1 10.10.10.11
ping -c2 10.10.10.12
df -h /           # около 20 ГБ после автоматического growpart
```

Если SSH не пускает, смотри консоль ВМ: `virsh -c qemu:///system console cp1`. Выход — `Ctrl+]`.

## 3. Твой ~/.ssh/config

Твои старые записи `node1/node2/node3` указывают на `192.168.56.x`. Это сеть VirtualBox, и она не пересекается с новой, но имена будут путаться. Добавь новые записи с другими именами:

```
Host kc-cp1
  HostName 192.168.100.11
  User ubuntu
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
Host kc-w1
  HostName 192.168.100.12
  User ubuntu
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
Host kc-w2
  HostName 192.168.100.13
  User ubuntu
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
```

Если захочешь использовать ключ `bm_k8s`, замени путь в `ssh_pubkey` в `locals` на `~/.ssh/bm_k8s.pub`. Порты 2201–2203 тебе не нужны, потому что хост видит ВМ напрямую.

```







































```

Ты запустил три ВМ, подключился по SSH, и всё работает. Причина сбоя — защитный механизм libvirt, который не давал QEMU открыть базовый образ. Мы отключили его в `qemu.conf`, после этого заработало. Точную причину, то есть AppArmor или права на файлы, я не установил: в журнале явного отказа не было. Ниже объяснение и полная инструкция, которую можно вставить в твой файл.

## Что произошло

**Как устроена цепочка.** Terraform сам не запускает виртуалки. Он отправляет команды демону libvirtd, а тот запускает процесс QEMU. Диск каждой ВМ (`cp1.qcow2`, 196 КБ) не содержит системы, а лишь хранит изменения поверх общего базового образа `ubuntu-noble-base.qcow2` (597 МБ). Поэтому QEMU должен открыть оба файла.

**Первая проблема: нет доступа к сокету.** Ошибка `permission denied` у `/var/run/libvirt/libvirt-sock` появилась потому, что группа `libvirt` применяется только при новом входе в систему. Решение — `newgrp libvirt` или перезаход.

**Вторая проблема: QEMU не смог открыть базовый образ.** Права на файлы и каталоги были в порядке: `qemu-img` под `libvirt-qemu` всё прочитал. Значит, блокировал не обычный доступ, а защитный слой libvirt (security driver). Он ограничивает QEMU: на Ubuntu это AppArmor плюс смена владельца файлов (DAC). Каждой ВМ создаётся отдельный профиль, и в нём обычно перечислены только файлы из описания диска. Базовый образ — это backing-файл, который в описании ВМ не указан. Скорее всего, профиль его не включил. Подтвердить это логами не удалось, поэтому это гипотеза.

**Третья проблема: «domain already exists».** После каждой неудачи libvirt оставлял ВМ определённой, но незапущенной, а Terraform считал, что ресурса нет. Такие ВМ нужно удалять вручную через `virsh undefine`.

**Что сработало.** Строка `security_driver = "none"` отключила и AppArmor-профили, и смену владельцев для ВМ. После перезапуска `libvirtd` ВМ запустились. У этого решения есть цена: изоляция ВМ слабее. Для учебной лаборатории на личном ноутбуке это приемлемо, но не оставляй так на сервере. Если захочешь вернуть защиту, одно из решений — стандартный каталог `/var/lib/libvirt/images`. Я его не проверял, поэтому сначала проверь на копии.

Строки `Found left-over process (dnsmasq)` в журнале libvirtd — безобидные. Это старые процессы DHCP/DNS виртуальных сетей, которые переподхватываются после перезапуска.

## Инструкция: ВМ для Kubernetes через Terraform

Файл `main.tf` я здесь не повторяю. Условия: Linux Mint 22.x (основа Ubuntu 24.04), процессор с поддержкой виртуализации, 16 ГБ ОЗУ, 100 ГБ диска. Проект лежит в `~/projects/kuber2/first`. Terraform установлен по `tf_inst.md`.

### Шаг 1. Проверить поддержку виртуализации

```bash
sudo apt install cpu-checker
kvm-ok
```

Ожидаемо: `KVM acceleration can be used`. Если нет, включи VT-x/AMD-V в BIOS.

### Шаг 2. Установить пакеты и дать права пользователю

```bash
sudo apt update
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients genisoimage
sudo usermod -aG libvirt $USER
```

Теперь войди в группу в текущем терминале:

```bash
newgrp libvirt
id | grep libvirt
```

В выводе должна быть группа `libvirt`. Для остальных терминалов нужно один раз выйти из системы и зайти снова. До этого в каждом новом терминале придётся вводить `newgrp libvirt`.

### Шаг 3. Запустить демон и проверить

```bash
sudo systemctl enable --now libvirtd
virsh -c qemu:///system list --all
```

Пустая таблица без ошибок — норма. Команды `libvirt` и `libvirt-daemon` не существуют: демон называется `libvirtd`, а управляют им через `virsh`.

### Шаг 4. Отключить защитный драйвер libvirt

Без этого ВМ не запустятся с твоим конфигом:

```bash
sudo sed -i 's/^#\?security_driver.*/security_driver = "none"/' /etc/libvirt/qemu.conf
sudo grep security_driver /etc/libvirt/qemu.conf
sudo systemctl restart libvirtd
```

Вторая команда должна показать строку `security_driver = "none"`. Файл `/etc/libvirt/qemu.conf` читается только от root, поэтому обычный `grep` выдаёт `Permission denied`.

Чтобы вернуть защиту:

```bash
sudo sed -i 's/^security_driver = "none"/#security_driver = "selinux"/' /etc/libvirt/qemu.conf
sudo systemctl restart libvirtd
```

### Шаг 5. Подготовить SSH-ключ

```bash
ls ~/.ssh/id_ed25519.pub || ssh-keygen -t ed25519
```

Публичный ключ из этого файла попадёт на ВМ через cloud-init.

### Шаг 6. Запустить Terraform

```bash
cd ~/projects/kuber2/first
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

В `plan` должно быть 13 ресурсов к созданию: 2 сети, 1 пул, 1 базовый образ, 3 диска, 3 cloud-init диска, 3 домена. Предупреждение `Argument is deprecated ... use target.path` безобидно. `apply` спросит подтверждение, введи `yes`. Скачивание образа занимает около минуты, создание ВМ — несколько секунд.

### Шаг 7. Проверить результат

```bash
virsh -c qemu:///system list --all         # cp1, w1, w2 в состоянии running
ssh ubuntu@192.168.100.11                  # подождать 20–40 с после старта
ip -br a                                   # nic0 192.168.100.11, nic1 10.10.10.11
ping -c2 10.10.10.12                       # связь по второй сети
df -h /                                    # около 20 ГБ
cloud-init status                          # status: done
```

Если SSH не подключается, подожди ещё: cloud-init применяет настройки при первой загрузке. Если не помогло, открой консоль ВМ: `virsh -c qemu:///system console cp1`. Выход — `Ctrl+]`.

### Шаг 8. SSH-алиасы

Добавь в `~/.ssh/config`:

```
Host kc-cp1
  HostName 192.168.100.11
  User ubuntu
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
Host kc-w1
  HostName 192.168.100.12
  User ubuntu
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
Host kc-w2
  HostName 192.168.100.13
  User ubuntu
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
```

Проброс портов 2201–2203 не нужен: хост видит ВМ напрямую по IP.

### Шаг 9. Повседневное управление

```bash
virsh -c qemu:///system start cp1
virsh -c qemu:///system shutdown cp1          # корректное выключение
virsh -c qemu:///system destroy cp1           # жёсткое выключение (как выдернуть питание)
virsh -c qemu:///system autostart cp1         # запускать вместе с ноутбуком
virsh -c qemu:///system net-list --all        # обе сети должны быть active
```

После перезагрузки ноутбука ВМ выключены, поднимай их через `virsh start`. Если ВМ не получают сеть, проверь `net-list`, а неактивную сеть запусти командой `virsh -c qemu:///system net-start k8s-mgmt` (или `k8s-net`).

### Шаг 10. Пересоздать одну ВМ

```bash
terraform apply -replace='libvirt_domain.vm["cp1"]'
ssh-keygen -R 192.168.100.11
```

Вторая команда нужна всегда после пересоздания ВМ: у новой машины другой SSH-ключ хоста, и без неё SSH скажет `REMOTE HOST IDENTIFICATION HAS CHANGED`.

### Шаг 11. Если что-то пошло не так

| Симптом                                                      | Причина                               | Что делать                                              |
| ------------------------------------------------------------ | ------------------------------------- | ------------------------------------------------------- |
| `dial unix .../libvirt-sock: permission denied`              | Сессия не знает про группу `libvirt`  | `newgrp libvirt` или перезаход                          |
| `Could not open ...qcow2: Permission denied` при создании ВМ | Защитный драйвер libvirt              | Шаг 4                                                   |
| `domain 'cp1' already exists`                                | ВМ осталась после неудачного apply    | Удалить вручную (ниже)                                  |
| SSH `Connection refused` или таймаут                         | ВМ ещё грузится, или сеть не поднята  | Подождать, проверить `virsh net-list --all`, консоль ВМ |
| SSH `Permission denied (publickey)`                          | Ключ не тот                           | Сверить ключ в `locals` и `~/.ssh/id_ed25519.pub`       |
| Предупреждение `deprecated`                                  | Параметр переименован в новых версиях | Игнорировать                                            |

Удалить недозапущенные ВМ:

```bash
for d in cp1 w1 w2; do
  virsh -c qemu:///system destroy $d 2>/dev/null
  virsh -c qemu:///system undefine $d --nvram 2>/dev/null
done
virsh -c qemu:///system list --all
```

### Шаг 12. Полная очистка

Сначала штатный путь:

```bash
terraform destroy
```

Если состояние Terraform сломано и он не справляется, удали всё вручную:

```bash
for d in cp1 w1 w2; do
  virsh -c qemu:///system destroy $d 2>/dev/null
  virsh -c qemu:///system undefine $d --nvram 2>/dev/null
done
for n in k8s-mgmt k8s-net; do
  virsh -c qemu:///system net-destroy $n 2>/dev/null
  virsh -c qemu:///system net-undefine $n
done
virsh -c qemu:///system pool-destroy k8s-lab
virsh -c qemu:///system pool-undefine k8s-lab
sudo rm -rf /var/lib/libvirt/k8s-lab
cd ~/projects/kuber2/first
rm -f terraform.tfstate terraform.tfstate.backup
for ip in 192.168.100.11 192.168.100.12 192.168.100.13; do ssh-keygen -R $ip; done
```

После этого можно запускать с шага 6. Папку `.terraform` и файл `.terraform.lock.hcl` удалять не нужно.

### Шаг 13. Где смотреть причины ошибок

```bash
sudo tail -30 /var/log/libvirt/qemu/cp1.log                          # лог QEMU конкретной ВМ
sudo journalctl -u libvirtd --since "15 min ago" --no-pager | tail   # лог демона
sudo journalctl -k --since "15 min ago" | grep -i apparmor | grep -v ptrace   # отказы AppArmor
sudo -u libvirt-qemu qemu-img info --backing-chain /var/lib/libvirt/k8s-lab/cp1.qcow2   # проверка прав
```

Запомни главное правило из этой истории: если `terraform apply` упал посередине, сначала проверь `virsh list --all`, потом чини причину и только потом запускай `apply` снова.
