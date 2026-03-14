# OmniRemote Pi Hub - Easy Setup Guide

## Option 1: One-Command Install (Easiest)

### What You Need
- Raspberry Pi Zero 2 W (recommended) or any Raspberry Pi with WiFi
- MicroSD card (8GB+)
- Power supply
- Computer with SD card reader

### Step 1: Flash Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert your SD card
3. Open Raspberry Pi Imager
4. Click **Choose OS** → **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (64-bit)**
5. Click **Choose Storage** → Select your SD card
6. Click the **⚙️ gear icon** for advanced options:
   - ✅ Set hostname: `omniremote-hub`
   - ✅ Enable SSH (Use password authentication)
   - ✅ Set username and password (remember these!)
   - ✅ Configure wireless LAN (your WiFi network)
   - ✅ Set locale settings
7. Click **Save**, then **Write**

### Step 2: First Boot

1. Insert SD card into Raspberry Pi
2. Connect power
3. Wait 2-3 minutes for first boot

### Step 3: Install OmniRemote

**From your computer**, open Terminal (Mac/Linux) or PowerShell (Windows):

```bash
ssh pi@omniremote-hub.local
```
(Use the username/password you set in Step 1)

Then run:
```bash
curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/pi-hub/install-pihub.sh | sudo bash
```

Follow the prompts to enter your Home Assistant IP and MQTT credentials.

### Step 4: Access Web UI

After reboot, open in your browser:
- https://omniremote-hub.local:8125
- Or: https://[Pi-IP-Address]:8125

Accept the self-signed certificate warning.

---

## Option 2: Pre-Built SD Card Image (Coming Soon)

Download our pre-built image and flash it directly - no commands needed!

[Download OmniRemote Pi Hub Image](#) *(Coming Soon)*

---

## Option 3: Manual Installation

If you prefer manual control:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip bluetooth bluez git

# Install Python packages
sudo pip3 install --break-system-packages flask flask-cors pyyaml paho-mqtt evdev broadlink

# Download OmniRemote
cd /tmp
git clone https://github.com/HunterAviator/OmniRemote.git
sudo mkdir -p /opt/omniremote /etc/omniremote
sudo cp OmniRemote/pi-hub/scripts/* /opt/omniremote/

# Generate SSL cert
sudo mkdir -p /etc/omniremote/ssl
sudo openssl req -x509 -newkey rsa:2048 -keyout /etc/omniremote/ssl/key.pem \
    -out /etc/omniremote/ssl/cert.pem -days 3650 -nodes -subj "/CN=omniremote-hub"

# Create config (edit with your settings)
sudo nano /etc/omniremote/config.yaml

# Create service
sudo nano /etc/systemd/system/omniremote-web.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable omniremote-web
sudo systemctl start omniremote-web
```

---

## Troubleshooting

### Can't connect via SSH
- Make sure Pi is powered on and connected to WiFi
- Try using the IP address instead: `ssh pi@192.168.x.x`
- Check your router for the Pi's IP address

### Web UI won't load
- Check service status: `sudo systemctl status omniremote-web`
- View logs: `sudo journalctl -u omniremote-web -f`
- Make sure to use `https://` not `http://`

### MQTT not connecting
- Verify Home Assistant IP is correct
- Check MQTT credentials
- Make sure Mosquitto broker is running in HA

### Bluetooth remotes not found
- Put remote in pairing mode (usually hold Home+Back)
- Check Bluetooth status: `bluetoothctl show`
- Enable Bluetooth: `sudo systemctl start bluetooth`

---

## Hardware Recommendations

| Item | Recommended | Link |
|------|-------------|------|
| Pi Zero 2 W | Best for dedicated hub | [Buy](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) |
| MicroSD Card | SanDisk 32GB+ | Amazon |
| Power Supply | Official 5V 2.5A | [Buy](https://www.raspberrypi.com/products/micro-usb-power-supply/) |
| USB Remote | G20S Pro / MX3 | Amazon |
| IR Blaster | Broadlink RM4 Mini | Amazon |

---

## Support

- GitHub Issues: https://github.com/HunterAviator/OmniRemote/issues
- Documentation: https://github.com/HunterAviator/OmniRemote/wiki

© 2026 One Eye Enterprises LLC
