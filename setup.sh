#!/bin/bash
set -euo pipefail

read -p "Enter your domain name (e.g., 3d-api.yourdomain.com): " DOMAIN
read -p "Enter your email address for Let's Encrypt: " EMAIL

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Error: Domain and Email are required!"
    exit 1
fi

echo "🚀 Starting Idempotent Setup for $DOMAIN..."

# 0. DigitalOcean Image Recommendation
echo "Note: DigitalOcean strongly recommends using their AI/ML-ready image (slug: gpu-h100x1-base) which has Ubuntu 22.04, CUDA 12.9, and Drivers 575 pre-installed."

# 1. System Updates & Prerequisites
if ! dpkg -l | grep -q curl; then
    apt-get update && apt-get install -y curl software-properties-common apt-transport-https wget
fi

# 2. NVIDIA Drivers & CUDA Toolkit
# If the user didn't use the recommended DO image, install the specific DO recommended packages.
if ! command -v nvidia-smi &> /dev/null; then
    echo "Installing NVIDIA Drivers (575) and CUDA Toolkit (12.9) per DigitalOcean specs..."
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
    dpkg -i cuda-keyring_1.1-1_all.deb
    apt-get update
    apt-get install -y cuda-drivers-575 cuda-toolkit-12-9
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
    mkdir -p ./tmp_nginx_conf
    echo "server { listen 80; server_name $DOMAIN; location /.well-known/acme-challenge/ { root /var/www/certbot; } }" > ./tmp_nginx_conf/init.conf
    docker run --name temp_nginx --rm -d -p 80:80 \
      -v "$(pwd)/tmp_nginx_conf:/etc/nginx/conf.d" \
      -v "$(pwd)/certbot/www:/var/www/certbot" \
      nginx:alpine
    
    sleep 3 # Wait for Nginx
    docker run --rm \
      -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
      -v "$(pwd)/certbot/www:/var/www/certbot" \
      certbot/certbot certonly --webroot -w /var/www/certbot \
      -d "$DOMAIN" --email "$EMAIL" --rsa-key-size 4096 --agree-tos --non-interactive
      
    docker stop temp_nginx
    rm -rf ./tmp_nginx_conf
fi

echo "✅ Host Setup Complete. Run 'docker compose up -d' next."
