# OmniRemote for Home Assistant

<p align="center">
  <img src="https://raw.githubusercontent.com/HunterAviator/omniremote/main/images/banner.svg" alt="OmniRemote Banner" width="100%">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS"></a>
  <a href="https://github.com/HunterAviator/omniremote/releases"><img src="https://img.shields.io/github/release/HunterAviator/omniremote.svg" alt="Release"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
</p>

> [!WARNING]
> **NOTE:** This is Public and Production only because HACS requires it. It is still being developed and so does not function yet. I will be updating frequently until at least minimum functionality is there. Please be patient as I have a day job and this is just a personal project that I will be sharing.

A comprehensive Home Assistant integration for universal remote control. Manage IR, RF, Network, and Bluetooth devices with a beautiful sidebar GUI, customizable Lovelace cards, pre-built device catalog, and powerful activity macros.

<p align="center">
  <img src="https://raw.githubusercontent.com/HunterAviator/omniremote/main/images/logo.svg" alt="OmniRemote Logo" width="200">
</p>

## ✨ Features

### Core Features
- 🖥️ **Full Web GUI** - Beautiful sidebar panel for visual device management
- 📚 **Device Catalog** - Pre-built codes for Samsung, Philips, Roku, Fire TV, Xbox, PlayStation, BenQ, and more
- 🎬 **Activities** - Complex macros like "Watch Roku" or "Movie Night" with timing and app launching
- 📺 **Multi-Protocol** - IR, RF 433MHz, Network (Roku ECP, Fire TV ADB, Onkyo eISCP), Bluetooth

### NEW: Physical Remote Control System
Use real physical remotes to control your devices and run scenes:

| Remote Type | Connection | Examples |
|------------|------------|----------|
| 🔷 **Zigbee** | Direct to HA | IKEA TRADFRI, Aqara, Hue Dimmer |
| 📡 **RF 433MHz** | Sonoff RF Bridge | Any cheap 433MHz remote |
| 🔵 **Bluetooth** | ESP32 Proxy | Media buttons, presenter remotes |
| 🔌 **USB Keyboard** | Pi Zero W Bridge | MX3 Air Mouse, WeChip, Rii |

- 🎯 **Room-Based Mapping** - Assign remotes to rooms, buttons auto-target room devices
- 🎛️ **Button Mapping** - Map any button to scenes, IR commands, or HA services
- 📦 **Pi Bridge Included** - Install script for Raspberry Pi Zero W USB bridge
- 🔍 **Auto-Discovery** - Bridges announce via MQTT, Zigbee remotes via ZHA/Z2M

### Customizable Remote Cards
- 🎛️ **Lovelace Remote Card** - Fully customizable remote control card for your dashboards
- 🎨 **Multiple Themes** - Default, Dark, Glass, Retro, Neon themes
- 📐 **Template Layouts** - Pre-built layouts for TV, Streaming, Receiver, Projector, Fan
- ✏️ **Visual Editor** - Drag-and-drop button arrangement in edit mode
- 📱 **Touch Optimized** - Haptic feedback, hold-to-repeat, double-tap support

### Area-Based Organization
- 🏠 **Room Assignment** - Register all devices, remotes, and blasters to rooms
- 🎯 **Smart Targeting** - Volume goes to receiver, navigation to streaming device
- 📊 **Device Mapping** - Set default TV, receiver, streaming device per area
- 📋 **Dashboard Generation** - Auto-generate Lovelace dashboards per area

## 📦 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add: `https://github.com/HunterAviator/omniremote`
4. Category: **Integration**
5. Click **Add** → Search for "OmniRemote" → **Download**
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from [Releases](https://github.com/HunterAviator/omniremote/releases)
2. Extract and copy `custom_components/omniremote` to your `config/custom_components/`
3. Restart Home Assistant

## 🚀 Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "OmniRemote"
3. Complete setup
4. Access the **OmniRemote** panel in your sidebar

## 🎛️ Remote Card Usage

### Add the Card Resource

Add to your Lovelace resources:
```yaml
url: /local/omniremote/omniremote-card.js
type: module
```

### Basic Card Configuration

```yaml
type: custom:omniremote-card
device: "Living Room TV"
template: tv
theme: dark
```

### Full Configuration Options

```yaml
type: custom:omniremote-card
device: "Living Room TV"           # OmniRemote device name
entity: remote.living_room         # Or use a remote entity
area: "Living Room"                # Area assignment
name: "Main Remote"                # Display name
template: streaming                # tv, streaming, receiver, projector, fan, minimal, custom
theme: glass                       # default, dark, glass, retro, neon
button_size: 48                    # Button size in pixels
button_gap: 8                      # Gap between buttons
border_radius: 12                  # Card corner radius
show_name: true                    # Show remote name
show_device_state: true            # Show power state
haptic: true                       # Enable haptic feedback
bluetooth_remote: "abc123"         # Link to BT remote
activities:                        # Quick activity buttons
  - id: watch_roku
    name: "Watch Roku"
    icon: mdi:television
custom_buttons:                    # Override button definitions
  netflix:
    icon: mdi:netflix
    color: "#E50914"
    command: app_netflix
```

### Available Templates

| Template | Description | Best For |
|----------|-------------|----------|
| `tv` | Full TV remote with number pad | Cable/Antenna TV |
| `streaming` | Navigation + streaming apps | Roku, Fire TV, Apple TV |
| `receiver` | Volume, inputs, sound modes | AV Receivers |
| `projector` | Lens, keystone, inputs | Projectors |
| `fan` | Speed, timer, modes | Fans and AC units |
| `minimal` | Just navigation + power | Simple control |
| `custom` | Build your own layout | Advanced users |

## 🎮 Bluetooth Remote Setup

### Pairing a Remote

1. Go to **OmniRemote** → **Bluetooth Remotes**
2. Click **Discover Remotes**
3. Put your remote in pairing mode
4. Select the discovered remote
5. Assign to an area and device

### Supported Remotes

- Amazon Fire TV Remote
- Roku Remote
- Apple TV Remote (Siri Remote)
- Generic Bluetooth HID remotes

### Button Mapping

```yaml
# Example custom mapping
button_mappings:
  0x42:  # Menu Up HID code
    command: up
    device_id: living_room_tv
    hold_command: page_up
    double_tap_command: home
```

## 🏠 Area Registration

### Setting Up Areas

1. Go to **OmniRemote** → **Areas**
2. Select an area (from Home Assistant)
3. Click **Add Remote**
4. Configure device mappings:
   - Primary TV
   - Receiver/Soundbar
   - Streaming Device
   - Projector

### Smart Command Routing

When a button is pressed:
- **Volume commands** → Receiver or Soundbar
- **Navigation commands** → Streaming device
- **Channel commands** → Cable box or TV
- **Power commands** → Primary TV

### Generate Dashboard

Click **Generate Dashboard** to create a Lovelace view with all your area remotes automatically configured.

## 🎬 Activities

Activities are powerful macros that control multiple devices with timing:

### Example: "Watch Roku"
```yaml
actions:
  - type: power_on
    device: Living Room TV
    delay_after: 3
  - type: power_on
    device: Onkyo Receiver
    delay_after: 2
  - type: set_input
    device: Onkyo Receiver
    input: streaming
    delay_after: 1
  - type: launch_app
    device: Roku
    app_id: "12"  # Netflix
```

## 🔧 Services

```yaml
# Send a command
service: omniremote.send_code
data:
  device: "Samsung TV"
  command: "power"

# Run an activity
service: omniremote.run_activity
data:
  activity: "watch_roku"

# Learn a new code
service: omniremote.learn_code
data:
  device: "Samsung TV"
  command: "input_game"
  timeout: 15
```

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

### Bluetooth Remotes
- Amazon Fire TV Remote
- Roku Remote
- Apple TV Remote
- Generic HID remotes

### Import Sources
- Flipper Zero .ir files
- Flipper Zero .sub files (SubGHz)
- Flipper-IRDB community database

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits

- [python-broadlink](https://github.com/mjg59/python-broadlink) - Broadlink device control
- [Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB) - Community IR database
- [Home Assistant](https://www.home-assistant.io/) - The best home automation platform

## ⚠️ Disclaimer

This integration is not affiliated with or endorsed by any of the device manufacturers mentioned.
