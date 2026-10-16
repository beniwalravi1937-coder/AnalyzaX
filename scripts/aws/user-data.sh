#!/bin/bash
# ==============================================================================
# AnalyzaX — EC2 first-boot bootstrap (Ubuntu 24.04)
# Installs Docker Engine + Compose/Buildx plugins from Docker's official apt repo
# and adds swap so the frontend build fits in memory.
# ==============================================================================
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

# 4 GB swap file (frontend Vite build + DuckDB headroom)
if [ ! -f /swapfile ]; then
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

apt-get update
apt-get install -y ca-certificates curl openssl

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable --now docker
usermod -aG docker ubuntu

mkdir -p /opt/analyzax
chown ubuntu:ubuntu /opt/analyzax

touch /var/lib/analyzax-bootstrap-done
