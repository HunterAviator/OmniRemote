# OmniRemote™ Pi Zero W Hub

<p align="center">
  <img src="https://omniremote.com/logo.png" width="120" alt="OmniRemote">
  <br>
  <strong>One Remote to Rule Them All</strong>
  <br>
  <em>© 2026 One Eye Enterprises LLC</em>
</p>

Transform a ~$45 Raspberry Pi Zero into a universal remote control hub for Home Assistant.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **USB HID Remotes** | G20S, MX3, and 2.4GHz air mice via USB dongle |
| **Bluetooth HID** | Optional built-in Bluetooth support |
| **GPIO IR Blaster** | ~$2 DIY IR transmitter |
| **Web Interface** | Mobile-friendly, works standalone or with HA |
| **HA Sync** | Devices sync between web UI and Home Assistant |
| **Upgrade Support** | In-place upgrades with settings preservation |

## 🚀 Quick Install

```bash
# Create install directory and extract
sudo mkdir -p /opt/omniremote
cd /opt/omniremote
sudo tar -xzf /path/to/omniremote-pi-hub.tar.gz

# Run installer
sudo bash install.sh
```

## 🔄 Upgrade

```bash
# Extract new version to same location (overwrites old files)
cd /opt/omniremote
sudo tar -xzf /path/to/omniremote-pi-hub.tar.gz

# Run installer (auto-detects upgrade, preserves config)
sudo bash install.sh
```

## 📦 What's Included

```
├── install.sh           # Interactive installer with upgrade support
├── scripts/
│   ├── remote_bridge.py # USB HID → MQTT
│   ├── ir_blaster.py    # GPIO IR transmitter
│   ├── web_server.py    # Standalone web server
│   └── panel.js         # Web UI (same as HA integration)
├── assets/
└── VERSION
```

## 💰 Pricing

| Product | Price |
|---------|-------|
| **HA Integration** | FREE (via HACS) |
| **Pi Hub Software** | This package |
| **Pre-configured SD** | Available at omniremote.com |
| **Hardware Bundles** | Available at omniremote.com |

## 🔧 Commands

```bash
# Upgrade to latest version
sudo bash install.sh --upgrade

# Check version
sudo bash install.sh --version

# View logs
journalctl -u omniremote-bridge -f

# Restart
sudo systemctl restart omniremote-bridge
```

## 🌐 Web Interface

Access at `http://<pi-ip>:8080`

- Works standalone OR with Home Assistant
- Devices sync automatically via MQTT
- Mobile-optimized responsive design

## 📡 Home Assistant Setup

Add to `configuration.yaml`:

```yaml
mqtt:
  sensor:
    - name: "OmniRemote Button"
      state_topic: "omniremote/physical_remote"
      value_template: "{{ value_json.button }}"
```

## 🛒 Recommended Hardware

| Product | Price | Link |
|---------|-------|------|
| Raspberry Pi Zero 2 W | $20 | [Amazon](https://omniremote.com/go/pizero) |
| G20S Pro Remote | $18 | [Amazon](https://omniremote.com/go/g20s) |
| Broadlink RM4 Mini | $25 | [Amazon](https://omniremote.com/go/rm4) |

*Links support OmniRemote development*

## 📄 License

This software is proprietary. See LICENSE file for terms.

**Free for personal use. Commercial use requires a license.**

---

<p align="center">
  <strong>OmniRemote™</strong> - One Remote to Rule Them All
  <br>
  © 2026 One Eye Enterprises LLC
  <br>
  <a href="https://omniremote.com">omniremote.com</a>
</p>
