Да, это блокировка: с марта 2022 года HashiCorp не отдаёт Terraform и Packer пользователям с российскими IP-адресами. Из-за этого ключ из репозитория даёт 404, а `apt.releases.hashicorp.com` не отдаёт Release-файл. Сайт документации открывается, потому что блокируется только раздача дистрибутивов. Для apt-репозитория HashiCorp в России путей нет, поэтому ставим бинарник с зеркала Яндекса.

## 1. Очистка

```bash
sudo rm -f /etc/apt/sources.list.d/hashicorp.list
sudo rm -f /usr/share/keyrings/hashicorp-archive-keyring.gpg
rm -rf ~/terraform_install
sudo apt update
```

После этого в `apt update` не должно остаться ошибок про hashicorp. Пакеты `gpg` и `wget` можно не трогать.

## 2. Установка с зеркала Яндекса

Скрипт сам берёт последнюю стабильную версию, без alpha, beta и rc. Я не мог проверить зеркало отсюда, поэтому версию определяет скрипт на твоей машине.

```bash
sudo apt install -y unzip curl
mkdir -p ~/terraform_install && cd ~/terraform_install

BASE=https://hashicorp-releases.yandexcloud.net/terraform
VER=$(curl -fsS $BASE/ | grep -oP 'terraform_\K[0-9]+\.[0-9]+\.[0-9]+(?=<)' | sort -uV | tail -1)
echo "Версия: $VER"

wget $BASE/$VER/terraform_${VER}_linux_amd64.zip
unzip terraform_${VER}_linux_amd64.zip
sudo install -m 0755 terraform /usr/local/bin/terraform

terraform -version
```

Если `curl` через прокси ведёт себя странно, добавь `--noproxy '*'`. Зеркало российское и должно открываться напрямую. То же для wget: `wget --no-proxy ...`.

Если `VER` пустой, посмотри список вручную в браузере: [https://hashicorp-releases.yandexcloud.net/terraform/](https://hashicorp-releases.yandexcloud.net/terraform/). Запасное зеркало: [https://mirror.yandex.ru/mirrors/releases.hashicorp.com/](https://mirror.yandex.ru/mirrors/releases.hashicorp.com/). Тогда задай версию так: `VER=1.x.y`. [mirror.yandex](https://mirror.yandex.ru/mirrors/releases.hashicorp.com/)

## 3. Зеркало провайдеров

`terraform init` качает провайдеры из `registry.terraform.io`, а они тоже могут быть недоступны. Поэтому подключи сетевое зеркало Яндекса: [habr](https://habr.com/ru/companies/otus/articles/957982/)

```bash
cat > ~/.terraformrc <<'EOF'
provider_installation {
  network_mirror {
    url     = "https://terraform-mirror.yandexcloud.net/"
    include = ["registry.terraform.io/*/*"]
  }
  direct {
    exclude = ["registry.terraform.io/*/*"]
  }
}
EOF
```

## Альтернатива: OpenTofu. -не понадобилось-

OpenTofu — открытый форк Terraform, который работает как прямая замена. Бинарник называется `tofu`, а команды и `.tf`-файлы те же. У него есть свой apt-репозиторий на `packages.opentofu.org` и релизы на GitHub. Если зеркало Яндекса не заработает, можно взять бинарник с GitHub (через твой прокси) и положить его в `/usr/local/bin/`. [opentofu](https://opentofu.org/docs/intro/install/deb/)

```bash
curl -Lo tofu.zip https://github.com/opentofu/opentofu/releases/download/v1.11.4/tofu_1.11.4_linux_amd64.zip
unzip tofu.zip && sudo install -m 0755 tofu /usr/local/bin/tofu
```
