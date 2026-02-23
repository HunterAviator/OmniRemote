# OmniRemote for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/YOUR_USERNAME/omniremote.svg)](https://github.com/YOUR_USERNAME/omniremote/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Home Assistant integration for universal remote control. Manage IR, RF, Network, and Bluetooth devices with a beautiful sidebar GUI, pre-built device catalog, and powerful activity macros.

![OmniRemote Dashboard](https://img.shields.io/badge/GUI-Sidebar%20Panel-blue)

## ✨ Features

- 🖥️ **Full Web GUI** - Beautiful sidebar panel for visual device management
- 📚 **Device Catalog** - Pre-built codes for Samsung, Philips, Roku, Fire TV, Xbox, PlayStation, BenQ, and more
- 🎬 **Activities** - Complex macros like "Watch Roku" or "Movie Night" with timing and app launching
- 📺 **Multi-Protocol** - IR, RF 433MHz, Network (Roku ECP, Fire TV ADB, Onkyo eISCP), Bluetooth
- 🏠 **Room Organization** - Group devices by room with room-specific scenes
- 📱 **App Launching** - Launch Netflix, YouTube, Disney+ by name on Roku/Fire TV
- 📡 **Channel Tuning** - Tune TV channels via IR digits or Roku ECP
- ⚡ **State Tracking** - Track power state, current input, volume for each device
- 📽️ **Projector Support** - Lamp hours, lens position, warm-up delays
- 🔄 **Flipper Zero Import** - Import .ir and .sub files from Flipper Zero
- 💾 **Broadlink Integration** - Use Broadlink RM devices as IR/RF blasters

## 📦 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add: `https://github.com/YOUR_USERNAME/omniremote`
4. Category: **Integration**
5. Click **Add** → Search for "OmniRemote" → **Download**
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from [Releases](https://github.com/YOUR_USERNAME/omniremote/releases)
2. Extract and copy `custom_components/omniremote` to your `config/custom_components/`
3. Restart Home Assistant

## 🚀 Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "OmniRemote"
3. Complete setup
4. Access the **OmniRemote** panel in your sidebar

## 🎮 Device Catalog

Pre-built IR/RF codes included for:

| Device | Brand | Control Methods | Features |
|--------|-------|-----------------|----------|
| Samsung TV | Samsung | IR, Network | 45+ commands, SmartThings |
| Philips TV | Philips | IR, Network | Ambilight, JointSpace API |
| Roku TV/Device | Roku | IR, Network | ECP API, 19 apps pre-configured |
| Amazon Fire TV | Amazon | IR, ADB, BT | 18 apps, text input |
| Onkyo Receiver | Onkyo | IR, eISCP | All inputs, listening modes |
| Xbox Series X/S | Microsoft | IR, SmartGlass | Controller buttons, media |
| PlayStation 5 | Sony | Network, BT, CEC | Streaming app IDs |
| BenQ Projector | BenQ | IR, RS232 | Lens, keystone, lamp hours |
| Shelly Shade | Shelly | HTTP, RF | Position control |
| Jensen Radio | Jensen | IR | Tuner, presets, EQ |
| LED Strip | Generic | IR, RF | Colors, modes, DIY |
| LEMOISTAR Fan | LEMOISTAR | IR, RF | Speed, timer, light |

### Pre-Configured Streaming Apps

**Roku:** Netflix, YouTube, Prime Video, Disney+, Hulu, HBO Max, Apple TV+, Peacock, Paramount+, Spotify, Plex, Tubi, Pluto TV, and more

**Fire TV:** Netflix, YouTube, Prime Video, Disney+, Hulu, HBO Max, Spotify, Plex, Twitch, Kodi, VLC, and more

## 🎬 Activities

Activities are powerful macros that control multiple devices with timing:

### Example: "Watch Roku"
1. Power on TV (wait 3s)
2. Power on receiver (wait 2s)
3. Set receiver to streaming input (wait 1s)
4. Set TV to HDMI 1 (wait 2s)
5. Launch Netflix on Roku

### Example: "Movie Night" (Projector)
1. Lower motorized screen (wait 5s)
2. Power on projector (wait 30s for warm-up)
3. Set projector to HDMI 1
4. Power on receiver
5. Dim lights (via HA service call)

### Activity Features
- **App Launching** - Launch apps by name
- **Channel Tuning** - Enter channel numbers
- **Timed Delays** - Wait for devices to warm up
- **Conditional Actions** - Check HA entity states
- **HA Service Calls** - Control lights, scenes, etc.
- **End Activities** - Automatic cleanup/power off

## 🔧 Services

```yaml
# Send a command
service: omniremote.send_code
data:
  device: "Samsung TV"
  command: "power"

# Run a scene
service: omniremote.run_scene
data:
  scene: "Watch Roku"

# Learn a new code
service: omniremote.learn_code
data:
  device: "Samsung TV"
  command: "input_game"
  timeout: 15

# Import Flipper files
service: omniremote.import_flipper
data:
  path: "/config/flipper/infrared"
```

## 🖼️ GUI Panel

The sidebar panel provides:

- **Dashboard** - Quick stats, scene buttons, device overview
- **Devices** - Full remote control with navigation pad
- **Activities** - Create and run complex macros
- **Device Catalog** - Browse and add pre-built devices
- **Rooms** - Organize devices by location
- **Scenes** - Simple command sequences
- **Blasters** - Manage Broadlink devices
- **Import/Export** - Flipper Zero file support

## 📡 Supported Hardware

### IR/RF Blasters
- Broadlink RM Mini 3
- Broadlink RM4 Mini / Pro
- Broadlink RM Pro / Pro+

### Network Devices
- Roku (ECP Protocol)
- Amazon Fire TV (ADB)
- Onkyo/Integra (eISCP)
- Shelly devices (HTTP)
- BenQ Projectors (RS232-over-IP)

### Import Sources
- Flipper Zero .ir files
- Flipper Zero .sub files (SubGHz)
- Flipper-IRDB community database

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Adding Device Codes

To add codes for a new device, edit `catalog.py`:

```python
MY_DEVICE = CatalogDevice(
    id="my_device",
    name="My Device",
    brand="Brand",
    category=DeviceCategory.TV,
    control_methods=[ControlMethod.IR],
    ir_codes={
        "power": _nec_code(0x04, 0x08, "power"),
        "volume_up": _nec_code(0x04, 0x02, "volume_up"),
        # ... more codes
    },
)
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

- [python-broadlink](https://github.com/mjg59/python-broadlink) - Broadlink device control
- [Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB) - Community IR database
- [Home Assistant](https://www.home-assistant.io/) - The best home automation platform

## ⚠️ Disclaimer

This integration is not affiliated with or endorsed by any of the device manufacturers mentioned. All trademarks are property of their respective owners.
