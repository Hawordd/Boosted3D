#!/bin/bash
set -euo pipefail

read -p "Enter your domain name (e.g., 3d-api.yourdomain.com): " DOMAIN
read -p "Enter your email address for Let's Encrypt: " EMAIL

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Error: Domain and Email are required!"
    exit 1
fi

echo "🚀 Starting Idempotent Setup for $DOMAIN..."

# 1. System Updates & Prerequisites
if ! dpkg -l | grep -q curl; then
    apt-get update && apt-get install -y curl software-properties-common apt-transport-https
fi

# 2. NVIDIA Drivers & CUDA Toolkit (Ubuntu 24.04/22.04)
if ! command -v nvidia-smi &> /dev/null; then
    echo "Installing NVIDIA Drivers..."
    apt-get install -y ubuntu-drivers-common
    ubuntu-drivers autoinstall
fi

# 3. Docker & NVIDIA Container Toolkit
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
fi

if ! dpkg -l | grep -q nvidia-container-toolkit; then
    echo "Installing NVIDIA Container Toolkit..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    apt-get update && apt-get install -y nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker
    systemctl restart docker
fi

# 4. Nginx Directory Setup (For Docker bind mounts)
mkdir -p ./nginx/ssl ./nginx/conf.d ./certbot/conf ./certbot/www

# 5. Bootstrap SSL Certificate (Certbot)
if [ ! -d "./certbot/conf/live/$DOMAIN" ]; then
    echo "Generating Initial SSL Certificate for $DOMAIN..."
    # Spin up temporary Nginx for ACME challenge
    docker run --rm -p 80:80 \
      -v "$(pwd)/nginx/conf.d:/etc/nginx/conf.d" \
      -v "$(pwd)/certbot/www:/var/www/certbot" \
      nginx:alpine \
      sh -c "echo 'server { listen 80; server_name $DOMAIN; location /.well-known/acme-challenge/ { root /var/www/certbot; } }' > /etc/nginx/conf.d/init.conf && nginx -g 'daemon off;'" &
    NGINX_PID=$!
    
    sleep 3 # Wait for Nginx
    docker run --rm \
      -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
      -v "$(pwd)/certbot/www:/var/www/certbot" \
      certbot/certbot certonly --webroot -w /var/www/certbot \
      -d "$DOMAIN" --email "$EMAIL" --rsa-key-size 4096 --agree-tos --non-interactive
      
    kill $NGINX_PID
    rm ./nginx/conf.d/init.conf
fi

echo "✅ Host Setup Complete. Run 'docker compose up -d' next."
