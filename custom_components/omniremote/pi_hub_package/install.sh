#!/bin/bash
#===============================================================================
# OmniRemote™ Pi Zero W Hub - Installation & Upgrade Script
# 
# Version: 1.4.3
# © 2026 One Eye Enterprises LLC
#
# Features:
# - Fresh install or upgrade existing installation
# - Version tracking and changelog
# - Settings persistence across upgrades
# - Automatic backup before upgrade
#
# Usage: 
#   sudo bash install.sh           # Interactive install/upgrade
#   sudo bash install.sh --upgrade # Force upgrade mode
#   sudo bash install.sh --version # Show version info
#===============================================================================

set -e

# Version
CURRENT_VERSION="1.5.22"
RELEASE_DATE="2026-03-10"
GITHUB_REPO="omniremote/pi-zero-hub"
GITHUB_RELEASES="https://api.github.com/repos/$GITHUB_REPO/releases/latest"

# Colors (OmniRemote Brand)
PURPLE='\033[38;2;124;58;237m'  # #7C3AED
BLUE='\033[38;2;37;99;235m'     # #2563EB
GREEN='\033[38;2;16;185;129m'   # #10B981
RED='\033[0;31m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m'
BOLD='\033[1m'

# Paths
INSTALL_DIR="/opt/omniremote"
CONFIG_DIR="/etc/omniremote"
CONFIG_FILE="$CONFIG_DIR/config.yaml"
DATA_FILE="$CONFIG_DIR/devices.json"
VERSION_FILE="$INSTALL_DIR/.version"
SAVED_SETTINGS="$CONFIG_DIR/.install_settings"
BACKUP_DIR="$CONFIG_DIR/backups"
LOG_DIR="/var/log/omniremote"
INSTALL_LOG="$LOG_DIR/install.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$LOG_DIR" "$CONFIG_DIR"

#-------------------------------------------------------------------------------
# Changelog
#-------------------------------------------------------------------------------

CHANGELOG="
${WHITE}${BOLD}v1.4.3${NC} ${GRAY}(2026-03-10)${NC}
  ${GREEN}+${NC} Shared UI with Home Assistant integration
  ${GREEN}+${NC} panel.js now installed for web UI
  ${GREEN}+${NC} Version displayed in sidebar
  ${GREEN}+${NC} ha-icon polyfill for standalone mode
  ${GREEN}+${NC} Fixed click handling with event delegation

${WHITE}${BOLD}v1.3.x${NC} ${GRAY}(2026-03-10)${NC}
  ${GREEN}+${NC} IR blaster via MQTT commands
  ${GREEN}+${NC} Pi Hub auto-discovery
  ${GREEN}+${NC} Trademark branding colors

${WHITE}${BOLD}v1.2.0${NC} ${GRAY}(2026-03-10)${NC}
  ${GREEN}+${NC} Version tracking and upgrade support
  ${GREEN}+${NC} Automatic backup before upgrades
  ${GREEN}+${NC} OmniRemote branded web interface
  ${GREEN}+${NC} Device sync between Pi and Home Assistant
  ${GREEN}+${NC} Improved logging with rotation

${WHITE}${BOLD}v1.1.0${NC} ${GRAY}(2026-03-09)${NC}
  ${GREEN}+${NC} Settings persistence across reinstalls
  ${GREEN}+${NC} Optional Bluetooth support
  ${GREEN}+${NC} Web server URL display
  ${GREEN}+${NC} Install logging

${WHITE}${BOLD}v1.0.0${NC} ${GRAY}(2026-03-08)${NC}
  ${GREEN}+${NC} Initial release
  ${GREEN}+${NC} USB HID remote bridge
  ${GREEN}+${NC} GPIO IR blaster
  ${GREEN}+${NC} Basic web interface
"

#-------------------------------------------------------------------------------
# Logging
#-------------------------------------------------------------------------------

log_file() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$INSTALL_LOG"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
    log_file "INFO: $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
    log_file "OK: $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    log_file "WARN: $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    log_file "ERROR: $1"
}

log_step() {
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}${BOLD}$1${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    log_file "=== $1 ==="
}

run_cmd() {
    log_file "CMD: $*"
    "$@" >> "$INSTALL_LOG" 2>&1
    return $?
}

#-------------------------------------------------------------------------------
# Banner
#-------------------------------------------------------------------------------

show_banner() {
    clear
    echo -e "${PURPLE}"
    cat << 'EOF'
  ╔══════════════════════════════════════════════════════════════════╗
  ║                                                                  ║
EOF
    # OmniRemote with underline (trademark style)
    echo -e "  ║       ${WHITE}${BOLD}OmniRemote${NC}${PURPLE}™                                              ║"
    echo -e "  ║       ${GREEN}══════════${PURPLE}                                              ║"
    echo -e "  ║                                                                  ║"
    echo -e "  ║       ${WHITE}Pi Zero W Remote Hub${PURPLE}  •  ${GREEN}v$CURRENT_VERSION${PURPLE}                       ║"
    echo -e "  ║       ${GRAY}© 2026 One Eye Enterprises LLC${PURPLE}                          ║"
    echo -e "  ╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    log_file "========================================"
    log_file "OmniRemote Pi Zero Hub v$CURRENT_VERSION"
    log_file "Started: $(date)"
    log_file "========================================"
}

#-------------------------------------------------------------------------------
# Version Management
#-------------------------------------------------------------------------------

get_installed_version() {
    if [ -f "$VERSION_FILE" ]; then
        head -1 "$VERSION_FILE"
    else
        echo "0.0.0"
    fi
}

save_version() {
    echo "$CURRENT_VERSION" > "$VERSION_FILE"
    echo "$RELEASE_DATE" >> "$VERSION_FILE"
}

version_compare() {
    # Returns: 0 if equal, 1 if $1 > $2, 2 if $1 < $2
    if [ "$1" = "$2" ]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=0; i<${#ver1[@]}; i++)); do
        if ((10#${ver1[i]:-0} > 10#${ver2[i]:-0})); then
            return 1
        fi
        if ((10#${ver1[i]:-0} < 10#${ver2[i]:-0})); then
            return 2
        fi
    done
    return 0
}

check_for_updates() {
    if command -v curl &> /dev/null && [ -n "$GITHUB_REPO" ]; then
        log_info "Checking for updates..."
        local latest=$(curl -s "$GITHUB_RELEASES" 2>/dev/null | grep '"tag_name"' | head -1 | cut -d'"' -f4 | tr -d 'v')
        if [ -n "$latest" ]; then
            version_compare "$latest" "$CURRENT_VERSION"
            if [ $? -eq 1 ]; then
                echo -e "${YELLOW}⬆ New version available: v$latest${NC}"
                echo -e "  Download: ${BLUE}https://github.com/$GITHUB_REPO/releases${NC}"
                echo ""
            fi
        fi
    fi
}

show_version() {
    echo -e "${PURPLE}Omni${BLUE}Remote${NC} Pi Zero Hub"
    echo -e "Version: ${GREEN}$CURRENT_VERSION${NC}"
    echo -e "Release: $RELEASE_DATE"
    echo ""
    installed=$(get_installed_version)
    if [ "$installed" != "0.0.0" ]; then
        echo -e "Installed: ${WHITE}$installed${NC}"
    else
        echo -e "Installed: ${GRAY}Not installed${NC}"
    fi
    exit 0
}

#-------------------------------------------------------------------------------
# Backup & Restore
#-------------------------------------------------------------------------------

create_backup() {
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup config
    [ -f "$CONFIG_FILE" ] && cp "$CONFIG_FILE" "$backup_path/"
    [ -f "$DATA_FILE" ] && cp "$DATA_FILE" "$backup_path/"
    [ -f "$SAVED_SETTINGS" ] && cp "$SAVED_SETTINGS" "$backup_path/"
    [ -f "$VERSION_FILE" ] && cp "$VERSION_FILE" "$backup_path/"
    
    # Backup scripts
    [ -d "$INSTALL_DIR" ] && cp -r "$INSTALL_DIR"/*.py "$backup_path/" 2>/dev/null || true
    
    log_success "Backup created: $backup_name"
    echo "$backup_path"
}

#-------------------------------------------------------------------------------
# Installation Mode Detection
#-------------------------------------------------------------------------------

detect_install_mode() {
    local installed_version=$(get_installed_version)
    log_file "Installed version: '$installed_version'"
    log_file "Current version: '$CURRENT_VERSION'"
    
    if [ "$installed_version" = "0.0.0" ]; then
        INSTALL_MODE="fresh"
        log_info "Fresh installation detected"
    else
        # Temporarily disable exit on error for version compare
        set +e
        version_compare "$CURRENT_VERSION" "$installed_version"
        local result=$?
        set -e
        
        if [ $result -eq 0 ]; then
            INSTALL_MODE="reinstall"
            log_info "Reinstalling v$installed_version"
        elif [ $result -eq 1 ]; then
            INSTALL_MODE="upgrade"
            log_info "Upgrading from v$installed_version to v$CURRENT_VERSION"
        else
            INSTALL_MODE="downgrade"
            log_warn "Downgrading from v$installed_version to v$CURRENT_VERSION"
        fi
    fi
}

show_install_mode() {
    local installed_version=$(get_installed_version)
    
    case $INSTALL_MODE in
        fresh)
            echo -e "${GREEN}Fresh Installation${NC}"
            ;;
        upgrade)
            echo -e "${BLUE}Upgrade${NC}: v$installed_version → v$CURRENT_VERSION"
            echo ""
            echo -e "${WHITE}What's New:${NC}"
            echo -e "$CHANGELOG" | head -20
            ;;
        reinstall)
            echo -e "${YELLOW}Reinstall${NC}: v$installed_version"
            ;;
        downgrade)
            echo -e "${RED}Downgrade${NC}: v$installed_version → v$CURRENT_VERSION"
            ;;
    esac
    echo ""
}

#-------------------------------------------------------------------------------
# Checks
#-------------------------------------------------------------------------------

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root: ${YELLOW}sudo bash install.sh${NC}"
        exit 1
    fi
}

check_raspberry_pi() {
    if ! grep -q -E "Raspberry Pi|BCM" /proc/cpuinfo 2>/dev/null; then
        log_warn "Not detected as Raspberry Pi"
        if [ "$UNATTENDED" = "1" ]; then
            log_info "Unattended mode: continuing anyway"
        else
            echo -n "Continue anyway? (y/n): "
            read -r REPLY
            [[ ! $REPLY =~ ^[Yy]$ ]] && { log_error "Aborted"; exit 1; }
        fi
    else
        PI_MODEL=$(grep -E "Model|Hardware" /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)
        log_success "Detected: ${PI_MODEL:-Raspberry Pi}"
    fi
}

#-------------------------------------------------------------------------------
# Settings
#-------------------------------------------------------------------------------

load_saved_settings() {
    if [ -f "$SAVED_SETTINGS" ]; then
        source "$SAVED_SETTINGS"
        return 0
    fi
    return 1
}

save_settings() {
    cat > "$SAVED_SETTINGS" << EOF
# OmniRemote Settings - $(date)
MQTT_BROKER="$MQTT_BROKER"
MQTT_PORT="$MQTT_PORT"
MQTT_USER="$MQTT_USER"
MQTT_PASS="$MQTT_PASS"
ENABLE_BLUETOOTH="$ENABLE_BLUETOOTH"
ENABLE_IR_BLASTER="$ENABLE_IR_BLASTER"
ENABLE_WEB_SERVER="$ENABLE_WEB_SERVER"
WEB_PORT="$WEB_PORT"
EOF
    chmod 600 "$SAVED_SETTINGS"
}

configure_installation() {
    log_step "Configuration"
    
    show_install_mode
    
    # For upgrades, always use existing settings
    if [ "$INSTALL_MODE" = "upgrade" ] && load_saved_settings; then
        echo -e "${WHITE}Current Settings:${NC}"
        echo "  Web Port: $WEB_PORT"
        echo "  Bluetooth: $ENABLE_BLUETOOTH | IR: $ENABLE_IR_BLASTER"
        echo ""
        log_success "Keeping existing settings (configure MQTT in web UI)"
        save_settings
        return
    fi
    
    # Fresh install - check for existing settings
    if load_saved_settings; then
        echo -e "${WHITE}Found existing settings - keeping them${NC}"
        save_settings
        return
    fi
    
    # Set defaults for new installation
    MQTT_BROKER=""  # Configure in web UI
    MQTT_PORT="1883"
    MQTT_USER=""
    MQTT_PASS=""
    ENABLE_BLUETOOTH="no"
    ENABLE_IR_BLASTER="no"
    ENABLE_WEB_SERVER="yes"
    WEB_PORT="8080"
    
    # In unattended mode, use defaults without prompts
    if [ "$UNATTENDED" = "1" ]; then
        log_info "Unattended mode: using default settings"
        echo "  Bluetooth: $ENABLE_BLUETOOTH | IR: $ENABLE_IR_BLASTER"
        echo "  Web Server: port $WEB_PORT"
        save_settings
        return
    fi
    
    echo -e "${WHITE}Quick Setup${NC}"
    echo ""
    echo -e "The web interface will be available at ${GREEN}http://<pi-ip>:8080${NC}"
    echo -e "You can configure MQTT and other settings in the web UI."
    echo ""
    
    echo -e "${WHITE}Optional Hardware Features:${NC}"
    
    echo -e "\n${PURPLE}Bluetooth HID${NC} (for Bluetooth remotes - most use USB dongle instead)"
    echo -n "Enable Bluetooth? (y/N): "
    read -r input
    [[ $input =~ ^[Yy]$ ]] && ENABLE_BLUETOOTH="yes" || ENABLE_BLUETOOTH="no"
    
    echo -e "\n${PURPLE}GPIO IR Blaster${NC} (for DIY IR transmitter on GPIO - skip if using Broadlink)"
    echo -n "Enable IR Blaster? (y/N): "
    read -r input
    [[ $input =~ ^[Yy]$ ]] && ENABLE_IR_BLASTER="yes" || ENABLE_IR_BLASTER="no"
    
    echo -e "\n${PURPLE}Web Port${NC}"
    echo -n "Web server port [$WEB_PORT]: "
    read -r input
    WEB_PORT="${input:-$WEB_PORT}"
    
    save_settings
    
    echo ""
    echo -e "${PURPLE}━━━ Configuration Summary ━━━${NC}"
    echo "  Bluetooth: $ENABLE_BLUETOOTH | IR: $ENABLE_IR_BLASTER"
    echo "  Web Server: port $WEB_PORT"
    echo "  MQTT: Configure in web UI after install"
    echo ""
    echo -n "Proceed with installation? (Y/n): "
    read -r REPLY
    [[ $REPLY =~ ^[Nn]$ ]] && { log_info "Cancelled."; exit 0; }
}

#-------------------------------------------------------------------------------
# Installation
#-------------------------------------------------------------------------------

install_dependencies() {
    log_step "Installing Dependencies"
    
    log_info "Updating packages..."
    run_cmd apt-get update -qq
    
    log_info "Installing base packages..."
    run_cmd apt-get install -y python3 python3-pip python3-dev python3-evdev \
        mosquitto-clients git build-essential unzip wget || {
        log_error "Failed. See $INSTALL_LOG"; exit 1
    }
    log_success "Base packages"
    
    # Always install Bluetooth packages (needed for remote discovery)
    log_info "Installing Bluetooth..."
    DEBIAN_FRONTEND=noninteractive timeout 120 apt-get install -y -q bluetooth bluez python3-dbus >> "$INSTALL_LOG" 2>&1 || {
        log_warn "Bluetooth install failed or timed out"
    }
    
    # Ensure Bluetooth service is enabled and started
    if command -v bluetoothctl &> /dev/null; then
        log_info "Enabling Bluetooth service..."
        systemctl enable bluetooth >> "$INSTALL_LOG" 2>&1 || true
        systemctl start bluetooth >> "$INSTALL_LOG" 2>&1 || true
        
        # Unblock Bluetooth if blocked by rfkill
        if command -v rfkill &> /dev/null; then
            rfkill unblock bluetooth >> "$INSTALL_LOG" 2>&1 || true
        fi
        
        # Power on adapter
        sleep 1
        bluetoothctl power on >> "$INSTALL_LOG" 2>&1 || true
        
        log_success "Bluetooth enabled"
    else
        log_warn "Bluetooth not available"
    fi
    
    if [ "$ENABLE_IR_BLASTER" = "yes" ]; then
        log_info "Building pigpio..."
        cd /tmp && rm -rf pigpio-master pigpio.zip 2>/dev/null
        if wget -q https://github.com/joan2937/pigpio/archive/master.zip -O pigpio.zip; then
            unzip -q pigpio.zip && cd pigpio-master
            if make -j$(nproc) >> "$INSTALL_LOG" 2>&1 && make install >> "$INSTALL_LOG" 2>&1; then
                log_success "pigpio"
                run_cmd pip3 install --break-system-packages --quiet pigpio
            else
                log_warn "pigpio failed"; ENABLE_IR_BLASTER="no"
            fi
            cd /tmp && rm -rf pigpio-master pigpio.zip
        else
            log_warn "pigpio download failed"; ENABLE_IR_BLASTER="no"
        fi
    fi
    
    log_info "Installing Python packages..."
    run_cmd pip3 install --break-system-packages --quiet evdev paho-mqtt PyYAML || {
        log_error "Python packages failed"; exit 1
    }
    log_success "Python packages"
    
    if [ "$ENABLE_WEB_SERVER" = "yes" ]; then
        log_info "Installing Flask..."
        run_cmd pip3 install --break-system-packages --quiet flask flask-cors || {
            log_warn "Flask failed"; ENABLE_WEB_SERVER="no"
        }
        [ "$ENABLE_WEB_SERVER" = "yes" ] && log_success "Flask"
    fi
    
    save_settings
}

setup_directories() {
    log_step "Setting Up Directories"
    mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$LOG_DIR" "$BACKUP_DIR"
    [ ! -f "$DATA_FILE" ] && echo '{"devices":[],"scenes":[],"remotes":[]}' > "$DATA_FILE"
    chmod 644 "$DATA_FILE"
    log_success "Directories created"
}

install_scripts() {
    log_step "Installing Scripts"
    
    # Backup if upgrading
    if [ "$INSTALL_MODE" = "upgrade" ]; then
        log_info "Creating backup..."
        create_backup
    fi
    
    cp "$SCRIPT_DIR/scripts/remote_bridge.py" "$INSTALL_DIR/" && chmod +x "$INSTALL_DIR/remote_bridge.py"
    log_success "remote_bridge.py"
    
    [ "$ENABLE_IR_BLASTER" = "yes" ] && [ -f "$SCRIPT_DIR/scripts/ir_blaster.py" ] && {
        cp "$SCRIPT_DIR/scripts/ir_blaster.py" "$INSTALL_DIR/" && chmod +x "$INSTALL_DIR/ir_blaster.py"
        log_success "ir_blaster.py"
    }
    
    [ "$ENABLE_WEB_SERVER" = "yes" ] && [ -f "$SCRIPT_DIR/scripts/web_server.py" ] && {
        cp "$SCRIPT_DIR/scripts/web_server.py" "$INSTALL_DIR/" && chmod +x "$INSTALL_DIR/web_server.py"
        log_success "web_server.py"
        
        # Copy panel.js for the web UI
        [ -f "$SCRIPT_DIR/scripts/panel.js" ] && {
            cp "$SCRIPT_DIR/scripts/panel.js" "$INSTALL_DIR/"
            log_success "panel.js (web UI)"
        }
    }
    
    [ -d "$SCRIPT_DIR/assets" ] && cp -r "$SCRIPT_DIR/assets" "$INSTALL_DIR/"
    [ -f "$SCRIPT_DIR/VERSION" ] && cp "$SCRIPT_DIR/VERSION" "$INSTALL_DIR/.version"
    
    save_version
}

create_config() {
    log_step "Creating Configuration"
    
    # Extract existing MQTT credentials if config exists (ALWAYS preserve across updates/reinstalls)
    local EXISTING_MQTT_USER=""
    local EXISTING_MQTT_PASS=""
    local EXISTING_MQTT_BROKER=""
    local EXISTING_MQTT_PORT=""
    
    if [ -f "$CONFIG_FILE" ]; then
        # Extract existing values using grep/sed (works without python yaml)
        EXISTING_MQTT_BROKER=$(grep -E "^\s*broker:" "$CONFIG_FILE" 2>/dev/null | head -1 | sed 's/.*broker:\s*["'\'']\?\([^"'\'']*\)["'\'']\?.*/\1/' | tr -d ' ')
        EXISTING_MQTT_PORT=$(grep -E "^\s*port:" "$CONFIG_FILE" 2>/dev/null | head -1 | sed 's/.*port:\s*//' | tr -d ' ')
        EXISTING_MQTT_USER=$(grep -E "^\s*username:" "$CONFIG_FILE" 2>/dev/null | head -1 | sed 's/.*username:\s*["'\'']\?\([^"'\'']*\)["'\'']\?.*/\1/')
        EXISTING_MQTT_PASS=$(grep -E "^\s*password:" "$CONFIG_FILE" 2>/dev/null | head -1 | sed 's/.*password:\s*["'\'']\?\([^"'\'']*\)["'\'']\?.*/\1/')
        
        if [ -n "$EXISTING_MQTT_USER" ] || [ -n "$EXISTING_MQTT_BROKER" ]; then
            log_info "Preserving existing MQTT configuration"
        fi
    fi
    
    # ALWAYS use existing values if available (preserve across ANY install type)
    MQTT_BROKER="${EXISTING_MQTT_BROKER:-$MQTT_BROKER}"
    MQTT_PORT="${EXISTING_MQTT_PORT:-${MQTT_PORT:-1883}}"
    MQTT_USER="${EXISTING_MQTT_USER:-$MQTT_USER}"
    MQTT_PASS="${EXISTING_MQTT_PASS:-$MQTT_PASS}"
    
    # For upgrades where we have valid existing config, skip rewriting entirely
    if [ -f "$CONFIG_FILE" ] && [ "$INSTALL_MODE" = "upgrade" ] && [ -n "$EXISTING_MQTT_BROKER" ]; then
        log_info "Preserving existing config (upgrade mode)"
        return
    fi
    
    # Backup existing config before rewriting
    if [ -f "$CONFIG_FILE" ]; then
        cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
        log_info "Backed up config to ${CONFIG_FILE}.bak"
    fi
    
    cat > "$CONFIG_FILE" << EOF
# OmniRemote™ Pi Zero Hub v$CURRENT_VERSION
# Generated: $(date)
# © 2026 One Eye Enterprises LLC

# Unique hub identifier (auto-generated from MAC address)
hub_id: "pihub_$(cat /sys/class/net/*/address 2>/dev/null | head -1 | tr -d ':' | tail -c 13)"
hub_name: "Pi Hub $(hostname)"

mqtt:
  broker: "$MQTT_BROKER"
  port: $MQTT_PORT
  username: "$MQTT_USER"
  password: "$MQTT_PASS"
  topic_prefix: "omniremote"
  client_id: "omniremote-pi-hub"

bridge:
  enable_usb_hid: true
  enable_bluetooth: $([ "$ENABLE_BLUETOOTH" = "yes" ] && echo "true" || echo "false")
  device_patterns:
    - ".*[Rr]emote.*"
    - ".*[Kk]eyboard.*"
    - ".*[Gg]20.*"
    - ".*[Gg]30.*"
    - ".*[Aa]ir.*[Mm]ouse.*"

ir_blaster:
  enabled: $([ "$ENABLE_IR_BLASTER" = "yes" ] && echo "true" || echo "false")
  gpio_pin: 18
  carrier_frequency: 38000

web_server:
  enabled: $([ "$ENABLE_WEB_SERVER" = "yes" ] && echo "true" || echo "false")
  port: $WEB_PORT
  host: "0.0.0.0"
  data_file: "$DATA_FILE"
  panel_js: "$INSTALL_DIR/panel.js"
  sync_mode: "ha_sync"

logging:
  level: INFO
  file: /var/log/omniremote/bridge.log
  max_size_mb: 10
EOF
    chmod 600 "$CONFIG_FILE"
    log_success "Config created (MQTT credentials preserved)"
}

create_log_symlinks() {
    log_step "Creating Log Symlinks"
    
    # Create symlinks in /opt/omniremote for easy access
    mkdir -p "$INSTALL_DIR/logs"
    
    # Symlink to actual log directory
    if [ -d "$LOG_DIR" ]; then
        ln -sf "$LOG_DIR/web.log" "$INSTALL_DIR/logs/web.log" 2>/dev/null || true
        ln -sf "$LOG_DIR/bridge.log" "$INSTALL_DIR/logs/bridge.log" 2>/dev/null || true
        ln -sf "$LOG_DIR/install.log" "$INSTALL_DIR/logs/install.log" 2>/dev/null || true
        ln -sf "$LOG_DIR" "$INSTALL_DIR/logs/all" 2>/dev/null || true
        log_success "Log symlinks: $INSTALL_DIR/logs/"
    fi
}

create_services() {
    log_step "Creating Services"
    
    cat > /etc/systemd/system/omniremote-bridge.service << EOF
[Unit]
Description=OmniRemote Bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 $INSTALL_DIR/remote_bridge.py --config $CONFIG_FILE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    log_success "omniremote-bridge.service"
    
    [ "$ENABLE_IR_BLASTER" = "yes" ] && {
        cat > /etc/systemd/system/omniremote-ir.service << EOF
[Unit]
Description=OmniRemote IR
After=network-online.target pigpiod.service

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 $INSTALL_DIR/ir_blaster.py --config $CONFIG_FILE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        log_success "omniremote-ir.service"
        run_cmd systemctl enable pigpiod
    }
    
    [ "$ENABLE_WEB_SERVER" = "yes" ] && {
        cat > /etc/systemd/system/omniremote-web.service << EOF
[Unit]
Description=OmniRemote Web
After=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/web_server.py --config $CONFIG_FILE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        log_success "omniremote-web.service"
    }
    
    run_cmd systemctl daemon-reload
}

start_services() {
    log_step "Starting Services"
    
    run_cmd systemctl enable omniremote-bridge
    run_cmd systemctl restart omniremote-bridge
    sleep 2
    systemctl is-active --quiet omniremote-bridge && log_success "Bridge running" || log_warn "Bridge issues"
    
    [ "$ENABLE_IR_BLASTER" = "yes" ] && {
        run_cmd systemctl enable omniremote-ir
        run_cmd systemctl restart omniremote-ir
        sleep 1
        systemctl is-active --quiet omniremote-ir && log_success "IR running" || log_warn "IR issues"
    }
    
    [ "$ENABLE_WEB_SERVER" = "yes" ] && {
        run_cmd systemctl enable omniremote-web
        run_cmd systemctl restart omniremote-web
        sleep 2
        systemctl is-active --quiet omniremote-web && log_success "Web running" || log_warn "Web issues"
    }
}

show_completion() {
    PI_IP=$(hostname -I | awk '{print $1}')
    PI_HOST=$(hostname)
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           ${WHITE}✨ Installation Complete! ✨${GREEN}                       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    
    if [ "$ENABLE_WEB_SERVER" = "yes" ]; then
        echo ""
        echo -e "${PURPLE}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${NC}"
        echo -e "${PURPLE}┃${NC}  ${WHITE}${BOLD}🌐 NEXT STEP: Open the Web Interface${NC}                       ${PURPLE}┃${NC}"
        echo -e "${PURPLE}┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫${NC}"
        echo -e "${PURPLE}┃${NC}                                                              ${PURPLE}┃${NC}"
        printf "${PURPLE}┃${NC}     ${GREEN}${BOLD}%-50s${NC}       ${PURPLE}┃${NC}\n" "http://$PI_IP:$WEB_PORT"
        echo -e "${PURPLE}┃${NC}                                                              ${PURPLE}┃${NC}"
        echo -e "${PURPLE}┃${NC}  ${YELLOW}→${NC} Go to Settings to configure MQTT connection            ${PURPLE}┃${NC}"
        echo -e "${PURPLE}┃${NC}  ${GREEN}✓${NC} Works standalone OR syncs with Home Assistant          ${PURPLE}┃${NC}"
        echo -e "${PURPLE}┃${NC}                                                              ${PURPLE}┃${NC}"
        echo -e "${PURPLE}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
    fi
    
    echo ""
    echo -e "${WHITE}Version:${NC} $CURRENT_VERSION"
    [ "$INSTALL_MODE" = "upgrade" ] && echo -e "${GREEN}Upgraded from $(get_installed_version)${NC}"
    echo ""
    echo -e "${WHITE}Logs:${NC}"
    echo -e "  Easy access: ${YELLOW}/opt/omniremote/logs/${NC}"
    echo -e "  Full logs:   ${YELLOW}/var/log/omniremote/${NC}"
    echo -e "  Live view:   ${YELLOW}journalctl -u omniremote-web -f${NC}"
    echo ""
    echo -e "${WHITE}Commands:${NC}"
    echo -e "  Restart: ${YELLOW}sudo systemctl restart omniremote-web omniremote-bridge${NC}"
    echo ""
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "  ${PURPLE}Omni${BLUE}Remote${NC}™ • © 2026 One Eye Enterprises LLC"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
    
    log_file "Completed at $(date)"
}

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

main() {
    # Parse arguments
    FORCE_UPGRADE=0
    UNATTENDED=0
    
    for arg in "$@"; do
        case "$arg" in
            --version|-v) show_version ;;
            --upgrade|-u) FORCE_UPGRADE=1 ;;
            --unattended|-y) UNATTENDED=1 ;;
            --help|-h)
                echo "Usage: sudo bash install.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --version, -v     Show version info"
                echo "  --upgrade, -u     Force upgrade mode"
                echo "  --unattended, -y  Non-interactive mode (use defaults)"
                echo "  --help, -h        Show this help"
                exit 0
                ;;
        esac
    done
    
    # Detect if running without TTY (e.g., from subprocess)
    if [ ! -t 0 ]; then
        UNATTENDED=1
    fi
    
    show_banner
    check_root
    check_raspberry_pi
    detect_install_mode
    check_for_updates
    configure_installation
    install_dependencies
    setup_directories
    install_scripts
    create_config
    create_log_symlinks
    create_services
    start_services
    show_completion
}

main "$@"
