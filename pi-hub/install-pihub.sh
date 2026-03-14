#!/bin/bash
#===============================================================================
# OmniRemote Pi Hub - Quick Install Script
# 
# Run this on a fresh Raspberry Pi OS installation:
#   curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/pi-hub/install-pihub.sh | sudo bash
#
# Or download and run:
#   wget https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/pi-hub/install-pihub.sh
#   chmod +x install-pihub.sh
#   sudo ./install-pihub.sh
#
# © 2026 One Eye Enterprises LLC
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
cat << 'EOF'
   ____            _  ____                      _       
  / __ \          (_)|  _ \                    | |      
 | |  | |_ __ ___  _ | |_) | ___ _ __ ___   ___| |_ ___ 
 | |  | | '_ ` _ \| ||  _ < / _ \ '_ ` _ \ / _ \ __/ _ \
 | |__| | | | | | | || |_) |  __/ | | | | | (_) | ||  __/
  \____/|_| |_| |_|_||____/ \___|_| |_| |_|\___/ \__\___|
                                                         
  Pi Hub Installer v1.5.31
  © 2026 One Eye Enterprises LLC
EOF
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root: sudo $0${NC}"
    exit 1
fi

# Check architecture
ARCH=$(uname -m)
echo -e "${BLUE}Detected architecture: ${ARCH}${NC}"

# Interactive configuration
echo ""
echo -e "${YELLOW}=== Configuration ===${NC}"
echo ""

read -p "Enter a name for this Pi Hub [omniremote-hub]: " HUB_NAME
HUB_NAME=${HUB_NAME:-omniremote-hub}

read -p "Enter your Home Assistant IP address: " HA_IP
if [ -z "$HA_IP" ]; then
    echo -e "${YELLOW}Warning: No HA IP set. You'll need to configure MQTT later.${NC}"
fi

read -p "Enter MQTT username (leave blank if none): " MQTT_USER
read -s -p "Enter MQTT password (leave blank if none): " MQTT_PASS
echo ""

echo ""
echo -e "${GREEN}Installing OmniRemote Pi Hub...${NC}"
echo ""

# Update system
echo -e "${BLUE}[1/7] Updating system packages...${NC}"
apt-get update -qq
apt-get upgrade -y -qq

# Install dependencies
echo -e "${BLUE}[2/7] Installing dependencies...${NC}"
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    bluetooth \
    bluez \
    bluez-tools \
    git \
    curl \
    openssl \
    libffi-dev

# Install Python packages
echo -e "${BLUE}[3/7] Installing Python packages...${NC}"
pip3 install --break-system-packages --quiet \
    flask \
    flask-cors \
    pyyaml \
    paho-mqtt \
    evdev \
    broadlink \
    pigpio

# Create directories
echo -e "${BLUE}[4/7] Creating directories...${NC}"
mkdir -p /opt/omniremote
mkdir -p /etc/omniremote/ssl
mkdir -p /var/log/omniremote

# Download Pi Hub
echo -e "${BLUE}[5/7] Downloading OmniRemote Pi Hub...${NC}"
cd /tmp
rm -rf OmniRemote pihub-download
git clone --depth 1 https://github.com/HunterAviator/OmniRemote.git pihub-download 2>/dev/null || {
    echo -e "${RED}Failed to download from GitHub${NC}"
    exit 1
}

# Copy files
cp pihub-download/pi-hub/scripts/* /opt/omniremote/
cp pihub-download/pi-hub/assets/* /opt/omniremote/ 2>/dev/null || true
cp pihub-download/pi-hub/VERSION /opt/omniremote/
rm -rf pihub-download

# Generate SSL certificates
echo -e "${BLUE}[6/7] Generating SSL certificates...${NC}"
openssl req -x509 -newkey rsa:2048 \
    -keyout /etc/omniremote/ssl/key.pem \
    -out /etc/omniremote/ssl/cert.pem \
    -days 3650 -nodes \
    -subj "/CN=${HUB_NAME}/O=OmniRemote/C=US" 2>/dev/null
chmod 600 /etc/omniremote/ssl/key.pem

# Generate hub ID
MAC_SUFFIX=$(cat /sys/class/net/wlan0/address 2>/dev/null | tr -d ':' | tail -c 7 || cat /sys/class/net/eth0/address 2>/dev/null | tr -d ':' | tail -c 7 || echo 'unknown')
HUB_ID="${HUB_NAME}_${MAC_SUFFIX}"

# Create config
echo -e "${BLUE}[7/7] Creating configuration...${NC}"
cat > /etc/omniremote/config.yaml << EOF
# OmniRemote Pi Hub Configuration
# Generated: $(date)

hub_id: "${HUB_ID}"
name: "${HUB_NAME}"

mqtt:
  broker: "${HA_IP}"
  port: 1883
  username: "${MQTT_USER}"
  password: "${MQTT_PASS}"
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

ir_blaster:
  enabled: true
  gpio_pin: 18
EOF

# Create database if doesn't exist
if [ ! -f /etc/omniremote/database.json ]; then
    echo '{"rooms":[],"devices":[],"physical_remotes":[],"scenes":[],"remote_bridges":[]}' > /etc/omniremote/database.json
fi

# Create systemd services
cat > /etc/systemd/system/omniremote-web.service << EOF
[Unit]
Description=OmniRemote Web Server
After=network.target bluetooth.target
Wants=bluetooth.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/omniremote
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/python3 /opt/omniremote/web_server.py --config /etc/omniremote/config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/omniremote-bridge.service << EOF
[Unit]
Description=OmniRemote Remote Bridge
After=network.target bluetooth.target omniremote-web.service
Wants=bluetooth.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/omniremote
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 /opt/omniremote/remote_bridge.py --config /etc/omniremote/config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable Bluetooth
systemctl enable bluetooth
systemctl start bluetooth

# Enable services
systemctl daemon-reload
systemctl enable omniremote-web
systemctl enable omniremote-bridge

# Set hostname
hostnamectl set-hostname "${HUB_NAME}"

# Get IP
IP_ADDR=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          OmniRemote Pi Hub Installation Complete!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Hub Name:  ${PURPLE}${HUB_NAME}${NC}"
echo -e "  Hub ID:    ${PURPLE}${HUB_ID}${NC}"
echo -e "  Version:   ${PURPLE}$(cat /opt/omniremote/VERSION)${NC}"
echo ""
echo -e "  ${YELLOW}Web UI:${NC}"
echo -e "    https://${IP_ADDR}:8125"
echo -e "    https://${HUB_NAME}.local:8125"
echo ""
if [ -n "$HA_IP" ]; then
    echo -e "  ${YELLOW}MQTT:${NC} Configured for ${HA_IP}"
else
    echo -e "  ${YELLOW}MQTT:${NC} Not configured - edit /etc/omniremote/config.yaml"
fi
echo ""
echo -e "  ${BLUE}Next Steps:${NC}"
echo -e "    1. Reboot: ${YELLOW}sudo reboot${NC}"
echo -e "    2. Access web UI and configure MQTT if needed"
echo -e "    3. Add Pi Hub in Home Assistant's OmniRemote panel"
echo ""

read -p "Reboot now? [Y/n]: " REBOOT_NOW
REBOOT_NOW=${REBOOT_NOW:-Y}
if [[ "$REBOOT_NOW" =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Rebooting...${NC}"
    reboot
fi
