#!/bin/bash
#
# OmniRemote Bridge Installation Script
# Run on Raspberry Pi Zero W (or any Linux with USB/Bluetooth)
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/remote_bridge/install.sh | sudo bash
#
# Or manually:
#   wget https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/remote_bridge/install.sh
#   chmod +x install.sh
#   sudo ./install.sh
#

set -e

INSTALL_DIR="/opt/omniremote-bridge"
CONFIG_DIR="/etc/omniremote-bridge"
REPO_URL="https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/remote_bridge"

echo "============================================"
echo "  OmniRemote Bridge Installer"
echo "============================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    apt-get update
    apt-get install -y python3 python3-pip
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install evdev paho-mqtt

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"

# Download bridge script
echo "Downloading bridge script..."
if command -v curl &> /dev/null; then
    curl -sSL "$REPO_URL/omniremote_bridge.py" -o "$INSTALL_DIR/omniremote_bridge.py"
elif command -v wget &> /dev/null; then
    wget -q "$REPO_URL/omniremote_bridge.py" -O "$INSTALL_DIR/omniremote_bridge.py"
else
    echo "ERROR: curl or wget required"
    exit 1
fi

chmod +x "$INSTALL_DIR/omniremote_bridge.py"

# Download and install systemd service
echo "Installing systemd service..."
if command -v curl &> /dev/null; then
    curl -sSL "$REPO_URL/omniremote-bridge.service" -o /etc/systemd/system/omniremote-bridge.service
else
    wget -q "$REPO_URL/omniremote-bridge.service" -O /etc/systemd/system/omniremote-bridge.service
fi

systemctl daemon-reload

# Run setup wizard
echo ""
echo "============================================"
echo "  Configuration"
echo "============================================"
echo ""

python3 "$INSTALL_DIR/omniremote_bridge.py" --setup -c "$CONFIG_DIR/config.json"

# Enable and start service
echo ""
echo "Starting service..."
systemctl enable omniremote-bridge
systemctl start omniremote-bridge

# Check status
sleep 2
if systemctl is-active --quiet omniremote-bridge; then
    echo ""
    echo "============================================"
    echo "  Installation Complete!"
    echo "============================================"
    echo ""
    echo "Bridge is running and connected to MQTT."
    echo ""
    echo "Useful commands:"
    echo "  Check status:   sudo systemctl status omniremote-bridge"
    echo "  View logs:      sudo journalctl -u omniremote-bridge -f"
    echo "  Restart:        sudo systemctl restart omniremote-bridge"
    echo "  Reconfigure:    sudo python3 $INSTALL_DIR/omniremote_bridge.py --setup"
    echo ""
else
    echo ""
    echo "WARNING: Service may not have started correctly."
    echo "Check logs with: sudo journalctl -u omniremote-bridge"
fi
