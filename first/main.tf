terraform {
  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "~> 0.8.3"
    }
  }
}

# Подключение к демону libvirt по адресу qemu:///system
provider "libvirt" {
  uri = "qemu:///system"
}

# Переменные: словарь трёх нод с IP и MAC-адресами
locals {
  ssh_pubkey = file("~/.ssh/id_ed25519.pub")

  nodes = {
    cp1 = { ip_mgmt = "192.168.100.11", ip_k8s = "10.10.10.11", mac_mgmt = "52:54:00:aa:01:01", mac_k8s = "52:54:00:bb:01:01" }
    w1  = { ip_mgmt = "192.168.100.12", ip_k8s = "10.10.10.12", mac_mgmt = "52:54:00:aa:01:02", mac_k8s = "52:54:00:bb:01:02" }
    w2  = { ip_mgmt = "192.168.100.13", ip_k8s = "10.10.10.13", mac_mgmt = "52:54:00:aa:01:03", mac_k8s = "52:54:00:bb:01:03" }
  }
}

# Папка /var/lib/libvirt/k8s-lab, где лежат диски
resource "libvirt_pool" "k8s" {
  name = "k8s-lab"
  type = "dir"
  path = "/var/lib/libvirt/k8s-lab"
}

# Сеть 1: NAT, интернет и SSH с хоста
resource "libvirt_network" "mgmt" {
  name      = "k8s-mgmt"
  mode      = "nat"
  addresses = ["192.168.100.0/24"]
  dhcp { enabled = false }
}

# Сеть 2: изолированная, только для трафика Kubernetes
resource "libvirt_network" "k8s" {
  name      = "k8s-net"
  mode      = "none"
  addresses = ["10.10.10.0/24"]
  dhcp { enabled = false }
}

resource "libvirt_volume" "base" {
  name   = "ubuntu-noble-base.qcow2"
  pool   = libvirt_pool.k8s.name
  source = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
  format = "qcow2"
}

resource "libvirt_volume" "disk" {
  for_each       = local.nodes
  name           = "${each.key}.qcow2"
  pool           = libvirt_pool.k8s.name
  base_volume_id = libvirt_volume.base.id
  size           = 20 * 1024 * 1024 * 1024
}

resource "libvirt_cloudinit_disk" "init" {
  for_each = local.nodes
  name     = "${each.key}-init.iso"
  pool     = libvirt_pool.k8s.name

  user_data = <<-EOF
    #cloud-config
    hostname: ${each.key}
    manage_etc_hosts: true
    users:
      - name: ubuntu
        sudo: ALL=(ALL) NOPASSWD:ALL
        shell: /bin/bash
        lock_passwd: true
        ssh_authorized_keys:
          - ${local.ssh_pubkey}
  EOF

  network_config = <<-EOF
    version: 2
    ethernets:
      nic0:
        match:
          macaddress: "${each.value.mac_mgmt}"
        set-name: nic0
        dhcp4: false
        addresses: ["${each.value.ip_mgmt}/24"]
        routes:
          - to: default
            via: 192.168.100.1
        nameservers:
          addresses: [192.168.100.1, 1.1.1.1]
      nic1:
        match:
          macaddress: "${each.value.mac_k8s}"
        set-name: nic1
        dhcp4: false
        addresses: ["${each.value.ip_k8s}/24"]
    EOF
}

resource "libvirt_domain" "vm" {
  for_each  = local.nodes
  name      = each.key
  memory    = 2048
  vcpu      = 2
  cloudinit = libvirt_cloudinit_disk.init[each.key].id

  network_interface {
    network_id = libvirt_network.mgmt.id
    mac        = each.value.mac_mgmt
  }
  network_interface {
    network_id = libvirt_network.k8s.id
    mac        = each.value.mac_k8s
  }

  disk {
    volume_id = libvirt_volume.disk[each.key].id
  }

  console {
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }
}

output "ssh" {
  value = { for k, v in local.nodes : k => "ssh ubuntu@${v.ip_mgmt}" }
}
