#!/bin/bash
#===============================================================================
# OmniRemote Pi Hub - Quick Install
# 
# Usage: curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/pi-hub/quick-install.sh | sudo bash
#
# © 2026 One Eye Enterprises LLC
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}"
cat << 'EOF'
   ____                  _ ____                      _       
  / __ \                (_)  _ \                    | |      
 | |  | |_ __ ___  _ __  _| |_) | ___ _ __ ___   ___ | |_ ___ 
 | |  | | '_ ` _ \| '_ \| |  _ < / _ \ '_ ` _ \ / _ \| __/ _ \
 | |__| | | | | | | | | | | |_) |  __/ | | | | | (_) | ||  __/
  \____/|_| |_| |_|_| |_|_|____/ \___|_| |_| |_|\___/ \__\___|
                                                              
  Pi Hub Quick Install
  © 2026 One Eye Enterprises LLC
EOF
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root: sudo bash $0${NC}"
    exit 1
fi

# Check if Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}[1/6] Updating system...${NC}"
apt-get update -qq

echo -e "${GREEN}[2/6] Installing dependencies...${NC}"
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    bluetooth bluez \
    openssl \
    git curl wget \
    > /dev/null

# Install Python packages
pip3 install --break-system-packages -q \
    flask flask-cors \
    pyyaml \
    paho-mqtt \
    evdev \
    requests

echo -e "${GREEN}[3/6] Downloading OmniRemote Pi Hub...${NC}"
INSTALL_DIR="/opt/omniremote"
CONFIG_DIR="/etc/omniremote"
LOG_DIR="/var/log/omniremote"

mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR"

# Download latest from GitHub
REPO_URL="https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/pi-hub"
curl -sSL "$REPO_URL/scripts/web_server.py" -o "$INSTALL_DIR/web_server.py"
curl -sSL "$REPO_URL/scripts/remote_bridge.py" -o "$INSTALL_DIR/remote_bridge.py"
curl -sSL "$REPO_URL/scripts/ir_blaster.py" -o "$INSTALL_DIR/ir_blaster.py"
curl -sSL "$REPO_URL/scripts/panel.js" -o "$INSTALL_DIR/panel.js"
curl -sSL "$REPO_URL/VERSION" -o "$INSTALL_DIR/.version"

chmod +x "$INSTALL_DIR"/*.py

echo -e "${GREEN}[4/6] Generating SSL certificates...${NC}"
SSL_DIR="$CONFIG_DIR/ssl"
mkdir -p "$SSL_DIR"

if [ ! -f "$SSL_DIR/server.key" ]; then
    HOSTNAME=$(hostname)
    IP_ADDR=$(hostname -I | awk '{print $1}')
    
    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "$SSL_DIR/server.key" \
        -out "$SSL_DIR/server.crt" \
        -days 3650 \
        -subj "/CN=$HOSTNAME" \
        -addext "subjectAltName=DNS:$HOSTNAME,DNS:$HOSTNAME.local,IP:$IP_ADDR,IP:127.0.0.1" \
        2>/dev/null
    
    chmod 600 "$SSL_DIR/server.key"
    echo -e "  SSL cert created for ${YELLOW}$HOSTNAME${NC} / ${YELLOW}$IP_ADDR${NC}"
fi

echo -e "${GREEN}[5/6] Creating configuration...${NC}"
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    # Generate unique hub ID
    HUB_ID="pihub_$(cat /sys/class/net/$(ip route show default | awk '/default/ {print $5}')/address 2>/dev/null | tr -d ':' | tail -c 7)"
    
    cat > "$CONFIG_DIR/config.yaml" << YAML
# OmniRemote Pi Hub Configuration
hub_id: "$HUB_ID"
name: "$(hostname)"

mqtt:
  broker: ""  # Will be configured via UI or auto-discovered
  port: 1883
  username: ""
  password: ""
  topic_prefix: "omniremote"

web_server:
  host: "0.0.0.0"
  port: 8125
  http_redirect_port: 8080
  ssl:
    enabled: true
    cert: "$SSL_DIR/server.crt"
    key: "$SSL_DIR/server.key"

logging:
  level: INFO
  file: "$LOG_DIR/web.log"
  max_size_mb: 10
  backup_count: 3
YAML
    echo -e "  Config created: ${YELLOW}$CONFIG_DIR/config.yaml${NC}"
fi

# Initialize empty database
if [ ! -f "$CONFIG_DIR/database.json" ]; then
    echo '{"rooms":[],"devices":[],"scenes":[],"physical_remotes":[],"remote_profiles":[],"remote_bridges":[]}' > "$CONFIG_DIR/database.json"
fi

echo -e "${GREEN}[6/6] Creating systemd services...${NC}"

# Web server service
cat > /etc/systemd/system/omniremote-web.service << 'SERVICE'
[Unit]
Description=OmniRemote Web
After=network.target bluetooth.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/omniremote/web_server.py
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
SERVICE

# Remote bridge service
cat > /etc/systemd/system/omniremote-bridge.service << 'SERVICE'
[Unit]
Description=OmniRemote Bridge
After=network.target bluetooth.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/omniremote/remote_bridge.py
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable omniremote-web omniremote-bridge
systemctl start omniremote-web omniremote-bridge

# Enable Bluetooth
systemctl enable bluetooth
rfkill unblock bluetooth

# Get IP for display
IP_ADDR=$(hostname -I | awk '{print $1}')
VERSION=$(cat "$INSTALL_DIR/.version" 2>/dev/null || echo "unknown")

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}  ${PURPLE}OmniRemote Pi Hub v$VERSION installed!${NC}                      ${GREEN}║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}                                                              ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Web UI:  ${YELLOW}https://$IP_ADDR:8125${NC}                       ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}           ${YELLOW}http://$IP_ADDR:8080${NC} (redirects to HTTPS)   ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                              ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Next: Configure MQTT in the Settings tab to connect to HA  ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}                                                              ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
