#!/bin/bash
#===============================================================================
# OmniRemote Pi Hub - First Boot Setup Script
# 
# This script runs once on first boot to set up a fresh Raspberry Pi as an
# OmniRemote Pi Hub. It installs all dependencies, configures services,
# and sets up Bluetooth/WiFi for remote control.
#
# Usage with Pi Imager:
#   1. Flash Raspberry Pi OS Lite (64-bit recommended)
#   2. In Pi Imager's advanced settings (gear icon):
#      - Set hostname: omniremote-hub (or your preferred name)
#      - Enable SSH with password authentication
#      - Set username/password
#      - Configure WiFi
#   3. Copy this script to /boot/firstboot.sh on the SD card
#   4. Add to /boot/cmdline.txt: systemd.run=/boot/firstboot.sh
#
# © 2026 One Eye Enterprises LLC
#===============================================================================

set -e

LOG_FILE="/var/log/omniremote-setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo "OmniRemote Pi Hub Setup"
echo "Started: $(date)"
echo "========================================"

# Check if already installed
if [ -f /opt/omniremote/.installed ]; then
    echo "OmniRemote already installed, skipping setup"
    exit 0
fi

# Wait for network
echo "Waiting for network..."
for i in {1..30}; do
    if ping -c 1 google.com &>/dev/null; then
        echo "Network ready"
        break
    fi
    sleep 2
done

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "Installing dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-evdev \
    python3-flask \
    python3-yaml \
    python3-paho-mqtt \
    bluetooth \
    bluez \
    bluez-tools \
    git \
    curl \
    openssl

# Install Python packages
echo "Installing Python packages..."
pip3 install --break-system-packages \
    flask \
    flask-cors \
    pyyaml \
    paho-mqtt \
    evdev \
    broadlink

# Create directories
echo "Creating directories..."
mkdir -p /opt/omniremote
mkdir -p /etc/omniremote
mkdir -p /var/log/omniremote

# Download OmniRemote Pi Hub from GitHub
echo "Downloading OmniRemote Pi Hub..."
cd /tmp
curl -L -o pihub.tar.gz "https://github.com/HunterAviator/OmniRemote/raw/main/pi-hub/omniremote-pi-hub.tar.gz" || {
    # Fallback: clone repo and extract
    git clone --depth 1 https://github.com/HunterAviator/OmniRemote.git
    cd OmniRemote/pi-hub
    cp -r scripts/* /opt/omniremote/
    cp -r assets/* /opt/omniremote/
    cp VERSION /opt/omniremote/
    cd /tmp
    rm -rf OmniRemote
}

# If tar download worked, extract it
if [ -f /tmp/pihub.tar.gz ]; then
    tar -xzf pihub.tar.gz -C /tmp/pihub-extract
    cp -r /tmp/pihub-extract/scripts/* /opt/omniremote/
    cp -r /tmp/pihub-extract/assets/* /opt/omniremote/ 2>/dev/null || true
    cp /tmp/pihub-extract/VERSION /opt/omniremote/
    rm -rf /tmp/pihub.tar.gz /tmp/pihub-extract
fi

# Generate SSL certificates
echo "Generating SSL certificates..."
mkdir -p /etc/omniremote/ssl
openssl req -x509 -newkey rsa:2048 -keyout /etc/omniremote/ssl/key.pem \
    -out /etc/omniremote/ssl/cert.pem -days 3650 -nodes \
    -subj "/CN=omniremote-hub/O=OmniRemote/C=US"
chmod 600 /etc/omniremote/ssl/key.pem

# Get hostname and generate hub ID
HOSTNAME=$(hostname)
HUB_ID="${HOSTNAME}_$(cat /sys/class/net/wlan0/address 2>/dev/null | tr -d ':' | tail -c 7 || echo 'unknown')"

# Create default config
echo "Creating configuration..."
cat > /etc/omniremote/config.yaml << EOF
# OmniRemote Pi Hub Configuration
# Generated on $(date)

hub_id: "${HUB_ID}"
name: "${HOSTNAME}"

mqtt:
  broker: ""  # Set your Home Assistant IP
  port: 1883
  username: ""
  password: ""
  prefix: "omniremote"

web_server:
  host: "0.0.0.0"
  port: 8125
  http_redirect_port: 8080
  ssl:
    enabled: true
    cert: "/etc/omniremote/ssl/cert.pem"
    key: "/etc/omniremote/ssl/key.pem"

logging:
  level: "INFO"
  file: "/var/log/omniremote/web.log"
  max_size_mb: 10

bluetooth:
  enabled: true
  auto_pair: false

ir_blaster:
  enabled: true
  gpio_pin: 18
EOF

# Create empty database
cat > /etc/omniremote/database.json << EOF
{
  "rooms": [],
  "devices": [],
  "physical_remotes": [],
  "scenes": [],
  "remote_bridges": []
}
EOF

# Create systemd service for web server
echo "Creating systemd services..."
cat > /etc/systemd/system/omniremote-web.service << EOF
[Unit]
Description=OmniRemote Web Server
After=network.target bluetooth.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/omniremote
ExecStart=/usr/bin/python3 /opt/omniremote/web_server.py --config /etc/omniremote/config.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for remote bridge
cat > /etc/systemd/system/omniremote-bridge.service << EOF
[Unit]
Description=OmniRemote Remote Bridge
After=network.target bluetooth.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/omniremote
ExecStart=/usr/bin/python3 /opt/omniremote/remote_bridge.py --config /etc/omniremote/config.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Configure Bluetooth
echo "Configuring Bluetooth..."
systemctl enable bluetooth
systemctl start bluetooth

# Enable and start services
echo "Enabling services..."
systemctl daemon-reload
systemctl enable omniremote-web
systemctl enable omniremote-bridge

# Mark as installed
touch /opt/omniremote/.installed
echo "$(date)" > /opt/omniremote/.installed

# Remove firstboot from cmdline.txt
sed -i 's/ systemd.run=[^ ]*//g' /boot/cmdline.txt 2>/dev/null || \
sed -i 's/ systemd.run=[^ ]*//g' /boot/firmware/cmdline.txt 2>/dev/null || true

echo "========================================"
echo "OmniRemote Pi Hub Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit /etc/omniremote/config.yaml"
echo "2. Set your MQTT broker IP and credentials"
echo "3. Reboot: sudo reboot"
echo ""
echo "Access the web UI at:"
echo "  https://$(hostname).local:8125"
echo "  https://$(hostname -I | awk '{print $1}'):8125"
echo ""

# Reboot to start services
echo "Rebooting in 10 seconds..."
sleep 10
reboot
