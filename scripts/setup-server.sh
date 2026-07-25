#!/bin/bash
# Server setup script for ShikkhaHub deployment

set -e

echo "Setting up ShikkhaHub server..."

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create directories
mkdir -p ~/shikkhahub
mkdir -p ~/shikkhahub/backups
mkdir -p ~/shikkhahub/nginx/ssl

# Install certbot for SSL
sudo apt-get install -y certbot

# Setup SSL certificate (manual step, requires domain)
echo ""
echo "SSL Certificate Setup:"
echo "Run: sudo certbot certonly --standalone -d your-domain.com"
echo "Then copy certs to ~/shikkhahub/nginx/ssl/"
echo ""

# Create logrotate config
sudo tee /etc/logrotate.d/shikkhahub > /dev/null <<EOF
/home/*/shikkhahub/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 $USER docker
    sharedscripts
    postrotate
        /usr/bin/docker kill --signal=HUP shikkhahub-nginx 2>/dev/null || true
    endscript
}
EOF

echo "Server setup complete!"
echo "Next steps:"
echo "1. Copy your .env file to ~/shikkhahub/"
echo "2. Copy docker-compose.prod.yml to ~/shikkhahub/"
echo "3. Copy nginx.conf to ~/shikkhahub/nginx/"
echo "4. Setup SSL certificates"
echo "5. Run: ./deploy.sh"
