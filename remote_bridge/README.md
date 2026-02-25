# OmniRemote USB/Bluetooth Bridge

This bridge runs on a Raspberry Pi Zero W (or any Linux device) and captures button presses from USB keyboard remotes (like MX3 Air Mouse) or Bluetooth remotes, then sends them to Home Assistant via MQTT.

## Supported Remotes

| Remote | Type | Connection |
|--------|------|------------|
| MX3 Pro Air Mouse | USB 2.4GHz | USB dongle |
| WeChip W1/W2 | USB 2.4GHz | USB dongle |
| Rii Mini i8 | USB 2.4GHz | USB dongle |
| G10/G20/G30 Air Mouse | USB 2.4GHz | USB dongle |
| Any USB keyboard remote | USB | USB dongle |
| Bluetooth media buttons | Bluetooth | Pair to Pi |

## Hardware Requirements

- Raspberry Pi Zero W ($15) - or any Pi with WiFi
- USB OTG adapter (if using Pi Zero) - $2
- MX3 remote with USB dongle - $15
- MicroSD card (8GB+) - $5
- Micro USB power supply - $5

**Total: ~$40 per room**

## Installation

### Quick Install (on Pi)

```bash
curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/remote_bridge/install.sh | sudo bash
```

### Manual Install

1. **Install dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip
   pip3 install evdev paho-mqtt
   ```

2. **Download bridge script:**
   ```bash
   sudo mkdir -p /opt/omniremote-bridge
   sudo curl -o /opt/omniremote-bridge/omniremote_bridge.py \
     https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/remote_bridge/omniremote_bridge.py
   sudo chmod +x /opt/omniremote-bridge/omniremote_bridge.py
   ```

3. **Run setup:**
   ```bash
   sudo python3 /opt/omniremote-bridge/omniremote_bridge.py --setup
   ```

4. **Install service:**
   ```bash
   sudo curl -o /etc/systemd/system/omniremote-bridge.service \
     https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/remote_bridge/omniremote-bridge.service
   sudo systemctl daemon-reload
   sudo systemctl enable omniremote-bridge
   sudo systemctl start omniremote-bridge
   ```

## Configuration

Configuration is stored in `/etc/omniremote-bridge/config.json`:

```json
{
  "bridge_id": "living-room-bridge",
  "bridge_name": "Living Room Remote Bridge",
  "mqtt_host": "homeassistant.local",
  "mqtt_port": 1883,
  "mqtt_username": "mqtt_user",
  "mqtt_password": "mqtt_pass",
  "device_paths": ["/dev/input/event4"],
  "grab_devices": true,
  "long_press_ms": 500,
  "double_press_ms": 300
}
```

### Finding Device Paths

Run discovery to find your remote:

```bash
sudo python3 /opt/omniremote-bridge/omniremote_bridge.py --discover
```

Output:
```
Found 5 input device(s):

  [0] 2.4G Composite Device
      Path: /dev/input/event4
      Phys: usb-0000:00:14.0-1/input0

Remote-like devices:
  - /dev/input/event4
```

## MQTT Topics

The bridge publishes to these topics:

| Topic | Description |
|-------|-------------|
| `omniremote/bridge/{bridge_id}/status` | `online` or `offline` |
| `omniremote/bridge/{bridge_id}/config` | Bridge discovery info (JSON) |
| `omniremote/bridge/{bridge_id}/event` | Button press events (JSON) |

### Event Payload

```json
{
  "device": "2.4G Composite Device",
  "button": "KEY_VOLUMEUP",
  "type": "short",
  "timestamp": 1708900000.123
}
```

Button types:
- `short` - Normal press (<500ms)
- `long` - Long press (>500ms)
- `double` - Double press (<300ms between presses)

## Troubleshooting

### Check service status
```bash
sudo systemctl status omniremote-bridge
```

### View logs
```bash
sudo journalctl -u omniremote-bridge -f
```

### Test manually
```bash
sudo python3 /opt/omniremote-bridge/omniremote_bridge.py -v
```

### Common issues

**"No remote devices found"**
- Make sure the USB dongle is plugged in
- Run `--discover` to see available devices
- Add device path manually to config

**"Permission denied"**
- Run as root or add user to `input` group:
  ```bash
  sudo usermod -aG input $USER
  ```

**"Failed to connect to MQTT"**
- Check MQTT broker is running
- Verify hostname/IP is correct
- Check username/password
- Make sure MQTT port (1883) is open

## Home Assistant Setup

1. Make sure you have the Mosquitto MQTT broker add-on installed
2. Add the OmniRemote integration
3. Go to **OmniRemote → Remotes → Add Bridge**
4. The bridge should auto-discover via MQTT
5. Add a remote and map buttons to actions

## Multiple Bridges

You can run multiple bridges for different rooms:

1. Change `bridge_id` in each config
2. Use unique names for identification
3. OmniRemote will discover all bridges automatically
