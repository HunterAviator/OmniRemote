# OmniRemote Pi Hub

The OmniRemote Pi Hub is a dedicated Raspberry Pi device that captures button presses from USB and Bluetooth remotes, then sends commands to your Home Assistant via MQTT.

## Features

- 📱 **Captive Portal Setup** - Connect to "OmniRemote-Setup" WiFi, configure via phone browser
- 🔵 **Bluetooth Remote Support** - Pair any Bluetooth HID remote directly to the Pi
- 🔌 **USB Remote Support** - Works with USB 2.4GHz air mouse remotes (MX3, G20, etc.)
- 📡 **IR Blaster** - Control TVs and receivers with IR commands
- 🔄 **OTA Updates** - One-click updates from the web UI
- 🔒 **Secure** - HTTPS with auto-generated certificates

## Get OmniRemote Pi Hub

### Pre-Built Image (Recommended)

The easiest way to get started is with our pre-built Raspberry Pi image:

**[Buy OmniRemote Pi Hub Image](https://oneeyeenterprises.com/omniremote-pihub)** - $19.99

Includes:
- ✅ Ready-to-flash SD card image
- ✅ Captive portal WiFi setup (no SSH needed)
- ✅ Web-based configuration wizard
- ✅ 1 year of OTA updates
- ✅ Email support

### Complete Kit

Want a fully assembled, ready-to-use device?

**[Buy Complete Pi Hub Kit](https://oneeyeenterprises.com/omniremote-kit)** - $79.99

Includes:
- ✅ Raspberry Pi Zero 2 W
- ✅ Pre-flashed 32GB SD card
- ✅ Premium case
- ✅ USB-C power supply
- ✅ 1 year of OTA updates
- ✅ Priority email support

---

## DIY Option

For technical users who prefer to build their own, see the [Remote Bridge](../remote_bridge/) folder for a basic DIY script.

The DIY option requires:
- SSH access and command line skills
- Manual YAML configuration
- Manual updates

---

## Hardware Compatibility

| Device | Type | Connection |
|--------|------|------------|
| Raspberry Pi Zero 2 W | Recommended | Built-in WiFi/BT |
| Raspberry Pi 3/4 | Supported | Built-in WiFi/BT |
| MX3 Air Mouse | USB Remote | 2.4GHz Dongle |
| G20S / G30S | USB Remote | 2.4GHz Dongle |
| WeChip W1/W2 | USB Remote | 2.4GHz Dongle |
| Any Bluetooth HID | BT Remote | Pair to Pi |
| Broadlink RM4 Mini | IR Blaster | WiFi |

---

## Support

- 📧 Email: support@oneeyeenterprises.com
- 📖 Documentation: [GitHub Wiki](https://github.com/HunterAviator/OmniRemote/wiki)
- 🐛 Issues: [GitHub Issues](https://github.com/HunterAviator/OmniRemote/issues)

---

© 2026 One Eye Enterprises LLC | [oneeyeenterprises.com](https://oneeyeenterprises.com)
