```bash
for n in vault_demo_postgres_password vault_demo_redis_password vault_demo_grafana_password nginx_basic_auth_password; do echo "$n: \"$(openssl rand -hex 24)\""; done
echo "vault_demo_jwt_secret: \"$(openssl rand -hex 32)\""


ansible-vault encrypt group_vars/vps/vault.yml     # спросит пароль дважды !!!
ansible-vault view group_vars/vps/vault.yml        # посмотреть
ansible-vault edit group_vars/vps/vault.yml        # править (перешифрует при сохранении)
ansible-playbook site.yml --limit lab-vm --ask-vault-pass

openssl rand -hex 24    # для паролей
openssl rand -hex 32    # для JWT и nginx
# и открой файл через ansible-vault edit group_vars/vps/vault.yml
```

```text
---
nginx_basic_auth_user: admin
nginx_basic_auth_password: "..."
vault_demo_postgres_password: "..."
vault_demo_redis_password: "..."
vault_demo_jwt_secret: "..."
vault_demo_grafana_password: "..."
```
