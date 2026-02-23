# Contributing to OmniRemote

Thank you for your interest in contributing to OmniRemote! This document provides guidelines and instructions for contributing.

## Ways to Contribute

### 1. Adding Device Codes

The most common contribution is adding IR/RF codes for new devices.

#### Steps:
1. Fork the repository
2. Edit `custom_components/omniremote/catalog.py`
3. Add your device following the existing pattern:

```python
MY_NEW_DEVICE = CatalogDevice(
    id="my_new_device",
    name="My New Device",
    brand="Brand Name",
    category=DeviceCategory.TV,  # or RECEIVER, STREAMING, etc.
    control_methods=[ControlMethod.IR],
    ir_codes={
        "power": _nec_code(0x04, 0x08, "power"),
        "volume_up": _nec_code(0x04, 0x02, "volume_up"),
        "volume_down": _nec_code(0x04, 0x03, "volume_down"),
        # Add more commands...
    },
)

# Don't forget to add it to DEVICE_CATALOG at the bottom:
DEVICE_CATALOG["my_new_device"] = MY_NEW_DEVICE
```

#### Finding IR Codes:
- Use a Flipper Zero to capture codes
- Check [Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB)
- Use LIRC database
- Capture with a Broadlink device

#### Protocol Helpers:
- `_nec_code(address, command, name)` - NEC protocol (most common)
- `_samsung_code(address, command, name)` - Samsung32 protocol
- `_rc5_code(address, command, name)` - RC5 protocol (Philips)
- `_rc6_code(address, command, name)` - RC6 protocol
- `_raw_ir_code(frequency, data, name)` - Raw timing data

### 2. Adding Network Device Support

To add support for a new network-controllable device:

1. Create a new controller class in `network_devices.py`:

```python
class MyDeviceController(NetworkController):
    def __init__(self, host: str, port: int = 8080):
        self.host = host
        self.port = port
    
    async def connect(self) -> bool:
        # Test connection
        pass
    
    async def send_command(self, command: str) -> bool:
        # Send command
        pass
    
    async def get_state(self) -> dict:
        # Get current state
        pass
```

2. Add to the controller factory in `get_controller()`

### 3. Bug Fixes

1. Check existing issues first
2. Create a new issue describing the bug
3. Fork and create a fix
4. Submit a pull request referencing the issue

### 4. Feature Requests

1. Open an issue with the "enhancement" label
2. Describe the feature and use case
3. Discuss with maintainers before implementing

## Development Setup

```bash
# Clone your fork
git clone https://github.com/HunterAviator/omniremote.git
cd omniremote

# Create a symlink in your HA config (for testing)
ln -s $(pwd)/custom_components/omniremote ~/.homeassistant/custom_components/omniremote

# Make changes and restart HA to test
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings to functions and classes
- Keep lines under 100 characters

## Pull Request Process

1. Update README.md if adding new features
2. Update catalog documentation if adding devices
3. Test your changes with Home Assistant
4. Create a pull request with a clear description
5. Wait for review and address any feedback

## Questions?

Open an issue with the "question" label or start a discussion.

Thank you for contributing! 🎉
