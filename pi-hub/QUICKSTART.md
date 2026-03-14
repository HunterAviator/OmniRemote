# OmniRemote Pi Hub - Quick Start Guide

## 1. Flash Raspberry Pi OS Lite

### Using Raspberry Pi Imager (Easiest)
1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Select **Raspberry Pi OS Lite (64-bit)** or **(32-bit)** for Pi Zero W
3. Click the **gear icon** ⚙️ for advanced options:
   - ✅ Enable SSH (use password authentication)
   - Set username: `pi` and password: `omniremote` (or your choice)
   - ✅ Configure WiFi (enter your SSID and password)
   - Set hostname: `omniremote-hub` (optional)
4. Flash to SD card
5. Insert SD card into Pi Zero and power on

### Manual Setup (Alternative)
After flashing, create these files in the `/boot` partition:

**Enable SSH** - Create empty file named `ssh`:
```bash
touch /boot/ssh
```

**Configure WiFi** - Create `wpa_supplicant.conf`:
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_WIFI_NAME"
    psk="YOUR_WIFI_PASSWORD"
    key_mgmt=WPA-PSK
}
```

---

## 2. Find Your Pi on the Network

### Option A: mDNS/Bonjour (Easiest)
After boot (wait ~2 minutes), try:
```bash
ping raspberrypi.local
# or if you set hostname:
ping omniremote-hub.local
```

### Option B: Check Your Router
Look at connected devices in your router admin page for "raspberrypi" or the MAC starting with `B8:27:EB` (Pi Zero W) or `DC:A6:32` (Pi Zero 2 W).

### Option C: Network Scan
```bash
# Linux/Mac
nmap -sn 192.168.1.0/24 | grep -B2 "Raspberry"

# Or use arp-scan
sudo arp-scan --localnet | grep -i raspberry
```

### Option D: From Android
- Install **Fing** app and scan network
- Look for "Raspberry Pi" devices

### Option E: From iPhone
- Install **Network Analyzer** or **Fing**
- Scan for devices on your network

---

## 3. Install OmniRemote Pi Hub

### One-Line Install
SSH into your Pi and run:
```bash
curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/pi-hub/quick-install.sh | sudo bash
```

That's it! The script will:
- Install all dependencies
- Download OmniRemote Pi Hub
- Generate SSL certificates
- Create and start services
- Show you the URL to access the web UI

---

## 4. Connect to Home Assistant

1. Open the Pi Hub web UI: `https://<PI_IP>:8125`
2. Accept the self-signed certificate warning
3. Go to **Settings** tab
4. Enter your MQTT broker details:
   - Broker: Your HA IP (e.g., `192.168.1.100`)
   - Port: `1883`
   - Username/Password: Your MQTT credentials
5. Click **Save** and **Test Connection**

---

## Troubleshooting

### Can't find Pi on network?
- Wait 2-3 minutes after first boot
- Check WiFi credentials in `wpa_supplicant.conf`
- Connect HDMI monitor to see boot messages
- Try connecting Pi via ethernet if available

### SSH connection refused?
- Make sure `ssh` file exists in `/boot`
- Try rebooting the Pi

### Web UI not loading?
```bash
# Check service status
sudo systemctl status omniremote-web

# View logs
sudo journalctl -u omniremote-web -f

# Restart services
sudo systemctl restart omniremote-web omniremote-bridge
```

### Reset to defaults?
```bash
sudo systemctl stop omniremote-web omniremote-bridge
sudo rm /etc/omniremote/database.json
sudo systemctl start omniremote-web omniremote-bridge
```

---

## Hardware

| Item | Price | Link |
|------|-------|------|
| Raspberry Pi Zero 2 W | $15 | [raspberrypi.com](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) |
| MicroSD Card (16GB+) | $8 | Amazon |
| USB Power Supply (5V 2A) | $10 | Amazon |
| (Optional) USB OTG Adapter | $3 | For USB remotes |
| (Optional) Broadlink RM4 Mini | $25 | For IR blasting |

---

© 2026 One Eye Enterprises LLC
