# OmniRemote Release Notes

## v1.6.9 - API Auth Fix (2024-02-26)

### 🐛 Bug Fixes

- **Fixed HTTP 401 errors** on debug/test API calls
  - All internal panel APIs now use `requires_auth = False`
  - Panel authentication is handled by HA's panel system
  - Fixes "Encoding failed: HTTP 401: Unauthorized" error

### 📝 Also Includes

- **Corrected Onkyo IR codes** (from v1.6.8)
  - Power toggle: `0x04` (was `0x1D`)
  - Fixed input select commands
  - Added navigation and tone controls

---

## v1.6.8 - Onkyo IR Code Fix (2024-02-26)

- Corrected Onkyo AVR IR command codes using verified IRDB data
- Power toggle: 0x04, Volume: 0x02/0x03, Mute: 0x05
- Fixed input selection codes

---

## v1.6.7 - Flipper Zero Integration (2024-02-26)

### ✨ New Features

#### Flipper Zero Support
Connect your Flipper Zero directly to OmniRemote via USB or Bluetooth!

**Features:**
- **USB Connection**: Auto-detect Flipper on USB ports
- **Bluetooth LE**: Scan and connect wirelessly
- **Send IR Commands**: Use Flipper as an IR blaster with any protocol
- **Browse SD Card**: View and import .ir files from Flipper's SD card
- **Real-time Learning**: Capture IR codes from other remotes (coming soon)

**To Use:**
1. Go to **Blasters** tab
2. Click **Find USB** or **Find Bluetooth** in Flipper section
3. Select your Flipper from discovered devices
4. Click **Connect**
5. Use **Test** to send IR commands

**Requirements:**
- For USB: `pyserial` and `pyserial-asyncio` packages
- For Bluetooth: `bleak` package
- Flipper Zero with IR module

**Protocols Supported:**
Samsung32, NEC, NECext, Sony SIRC, RC5, RC6, Kaseikyo (Panasonic), and more

---

## v1.6.6 - Debug Logging for Catalog Test (2024-02-26)

### 🔧 Debugging

Added extensive logging to diagnose "Quick Test from Catalog" 400 error:
- Browser console: Logs data attributes from button clicks
- Browser console: Logs API request and response
- HA logs: Logs action and data keys received
- HA logs: Logs catalog lookup results

**To debug:**
1. Install v1.6.6, restart HA
2. Open browser dev tools (F12) → Console tab
3. Go to OmniRemote → IR Debugger
4. Select a category, device, click a command button
5. Check browser console for `[OmniRemote]` messages
6. Check HA logs for `omniremote` messages

---

## v1.6.5 - Debugger Fixes & Encoding Help (2024-02-26)

### 🐛 Bug Fixes

#### Quick Test from Catalog Fixed
- Fixed HTTP 400 error when testing catalog commands from debugger
- Separated debugger catalog test (`debug-catalog-test`) from catalog preview test (`test-catalog-cmd`)
- Both now work correctly with their respective contexts

### 📝 Enhanced Documentation

#### Expanded IR Encoding Help
Click "Help" button in IR Debugger for comprehensive encoding reference:
- **Protocol descriptions** - Which brands use which protocol
- **Common address codes** - Samsung (07), LG (04), Sony (01), NEC (00/04)
- **Common command codes** - Power, volume, mute for each protocol
- **Resource links** - IRDB Wiki, GitHub IRDB for code lookups

---

## v1.6.4 - Debugger UX & Jensen Radio Support (2024-02-26)

### ✨ New Features

#### Enhanced IR Debugger
- **Blaster Selection**: Clear dropdown to select which IR blaster to use for all tests
- **Embedded Help**: Toggle "Help" button explains how to use Test IR Encoding
- **Quick Test Any Device**: Select any device from catalog by category → device → command
- **Full Debug Log**: All commands show protocol, address, command, blaster used, bytes sent

#### Jensen Radio Support
- Added Jensen car stereo, marine/RV stereo, and portable radio profiles
- 4 profiles with 30+ commands each (NEC protocol)
- New "Radio/Car Stereo" category in catalog

### 🐛 Bug Fixes

#### Catalog Search Fixed
- Fixed keyboard input being captured by Home Assistant shortcuts
- Search now properly debounces and maintains focus
- Event propagation stopped on all input fields

#### API Improvements
- New `send_catalog_code` action for testing catalog commands with specific blaster
- All debug commands now respect selected blaster
- Better error messages in debug log

### 📝 Documentation
- Added "Adding Devices to Catalog" section in Debugger
- Clearer troubleshooting tips
- Help button for Test IR Encoding explains protocol, address, command

---

## v1.6.3 - Samsung IR Encoding Fix (2024-02-25)

### 🐛 Critical Bug Fixes

#### Samsung32 IR Encoding - Complete Rewrite
The Samsung IR encoding was fundamentally broken. Fixed two major issues:

**Issue 1: Wrong Time Unit**
- Before: Used carrier-frequency-based calculation (13.158µs for 38kHz)
- After: Uses fixed Broadlink time unit (8192/269 ≈ 30.45µs)
- This is the actual time base Broadlink devices use internally

**Issue 2: Wrong Bit Encoding Method**  
Samsung TVs controlled via Broadlink use a **mark-based** encoding variant:

| Bit | Before (WRONG)              | After (CORRECT)             |
|-----|-----------------------------|-----------------------------|
| 0   | 560µs mark, 560µs space     | 560µs mark, 560µs space     |
| 1   | 560µs mark, 1690µs space    | **1690µs mark**, 560µs space|

The bit value is determined by the **mark duration**, not the space duration.

**Testing Your Samsung TV:**
1. Install v1.6.3
2. Go to IR Debugger in the OmniRemote panel
3. Click "Power" in Quick Test - Samsung TV section
4. If power doesn't work, try "power_off" command (0x98) which is a discrete off

---

## v1.6.2 - Cache Busting Fix (2024-02-25)

### 🐛 Bug Fixes

#### Panel Update / Cache Issues
- **Content Hash Cache-Busting**: Panel URL now includes MD5 hash of panel.js content
- **Auto Re-registration**: Panel automatically re-registers when version changes
- **Force Remove Old Panel**: Removes old panel registration before re-adding
- **Prominent Version Mismatch Banner**: Orange warning banner with clear reload instructions
- **Console Logging**: Detailed version logging for debugging cache issues

**If panel doesn't update after reinstall:**
1. Check browser console for `[OmniRemote] Panel v1.6.2 loaded` message
2. If version mismatch banner appears, click "Clear Cache & Reload"
3. Try Ctrl+Shift+R (Cmd+Shift+R on Mac) for hard refresh
4. Restart Home Assistant completely

---

## v1.6.1 - IR Debugger & Catalog Improvements (2024-02-25)

### 🐛 Bug Fixes

#### Samsung IR Encoding Fix
- **Repeat Signals**: Samsung TVs now receive 2 repeated frames (was single frame)
- **Proper Timing**: Added 46ms gap between repeat frames as per Samsung spec
- **Power Commands**: Fixed power on/off reliability

### ✨ New Features

#### Visual IR Debugger
New "IR Debugger" section in the panel for troubleshooting IR commands:

| Feature | Description |
|---------|-------------|
| **Blaster Status** | Live connection status for all configured blasters |
| **Test Encoding** | Encode any protocol/address/command without sending |
| **Quick Test Buttons** | One-click Samsung TV commands (power, vol, ch, etc.) |
| **Command Log** | Real-time log of all IR encoding and transmission |

- View detailed encoding info: timings, packet bytes, base64 output
- Send raw encoded commands for testing
- Clear troubleshooting tips for common issues

#### Catalog Category Tiles
- **Visual Categories**: Browse by device type with icon tiles
- **Click to Browse**: Select a category to see all devices in that category
- **Better Navigation**: Back button to return to category overview
- **Category Counts**: Shows number of devices per category

| Category | Icon | Example Devices |
|----------|------|-----------------|
| TVs | 📺 | Samsung, LG, Sony, Vizio |
| Receivers | 🔊 | Denon, Yamaha, Onkyo |
| Soundbars | 🎵 | Bose, Sonos, Samsung |
| Streamers | 📡 | Roku, Fire TV, Apple TV |
| Projectors | 🎬 | BenQ, Epson, JVC |
| And more... | | |

### 🔧 Technical Improvements

#### Enhanced Logging
- Full debug logging in `ir_encoder.py` with timing details
- Command send logging with blaster info and byte counts
- In-memory debug log accessible via API (`/api/omniremote/debug`)
- Log entries include: timestamp, action, protocol, status, errors

#### New API Endpoints
- `GET /api/omniremote/debug` - Retrieve debug log
- `POST /api/omniremote/debug` - Debug actions (clear, test_encode, test_send, blaster_status)
- `POST /api/omniremote/test` with `action: send_raw` - Send raw base64 Broadlink codes

---

## v1.6.0 - Physical Remote Control System (2024-02-25)

### ✨ New Features

#### Physical Remote Support
Complete system for using physical remotes (not just IR blasters) to control your devices:

| Remote Type | Connection | Examples |
|------------|------------|----------|
| **Zigbee** | Direct to HA | IKEA TRADFRI, Aqara, Hue Dimmer |
| **RF 433MHz** | Sonoff RF Bridge | Any 433MHz remote |
| **Bluetooth** | ESP32 Proxy | Media buttons, presenters |
| **USB Keyboard** | Pi Zero W Bridge | MX3 Air Mouse, WeChip |

#### Bridge System
- **USB Bridge**: Python script for Pi Zero W to capture USB keyboard remotes
- **Bluetooth Proxy**: Support for ESP32 Bluetooth proxies
- **RF Bridge**: Integration with Tasmota-flashed Sonoff RF bridges
- **Auto-Discovery**: MQTT-based bridge discovery

#### Room-Based Mapping
- Every entity can be assigned to a room:
  - Devices (IR-controlled equipment)
  - Blasters (IR transmitters)
  - Scenes (automation sequences)
  - Physical Remotes (button controllers)
  - Bridges (signal receivers)
- Button actions automatically target room devices

#### Button Mapping
- Map any button to:
  - Run OmniRemote scenes
  - Send IR commands
  - Volume Up/Down (room-based)
  - Channel Up/Down (room-based)
  - Mute toggle
  - Toggle device power
  - Call any Home Assistant service
- Pre-defined profiles for popular remotes:
  - IKEA TRADFRI Remote
  - IKEA RODRET/SOMRIG
  - Aqara Mini Switch
  - Aqara Cube T1 Pro
  - Hue Dimmer Switch
  - MX3 Pro Air Mouse

#### New Panel UI
- **Physical Remotes** section in sidebar
- Add/edit/delete remotes and bridges
- Visual button mapping editor
- Bridge online/offline status
- Quick setup guides for each remote type

### 📦 Pi Zero W Bridge
Included `remote_bridge/` folder contains:
- `omniremote_bridge.py` - Python script for Pi
- `install.sh` - One-line installation
- `omniremote-bridge.service` - Systemd service
- `README.md` - Setup documentation

Install on Pi:
```bash
curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/remote_bridge/install.sh | sudo bash
```

### 🔧 Technical Details
- New `physical_remotes.py` module (~800 lines)
- `PhysicalRemoteManager` class listens to multiple event sources
- Support for ZHA, deCONZ, Zigbee2MQTT events
- MQTT subscriptions for Tasmota and custom bridges
- Long-press and double-press detection

---

## v1.5.5 - IR Protocol Encoding (2024-02-25)

### 🐛 Bug Fixes
- **Critical**: Fixed catalog IR codes not working with Broadlink devices
- Catalog now properly converts protocol codes (NEC, Samsung32, etc.) to Broadlink raw format

### ✨ New Features
- **IR Protocol Encoder**: Full encoder for 8 protocols
- **Test Buttons**: Test commands before adding devices
- **Profile Switching**: Try different profiles for same device
- **Learn Code**: Learn IR codes directly from existing remotes

---

## v1.5.0 - Comprehensive Device Catalog (2024-02-25)

### ✨ New Features
- **Expanded Device Catalog**: 94 device profiles across 12 categories
- **Organized Catalog Structure**: Device profiles now organized in subfolders by category
- **Multiple Control Profiles**: Devices with different control methods have separate profiles
  - Example: Samsung TV has IR Standard, IR 2020+, and Network/SmartThings profiles
  - Example: Denon AVR has IR, Telnet, and HTTP REST API profiles
- **Year/Version-Specific Profiles**: Different profiles for device generations
  - Samsung TV 2015-2020 vs 2020+ QLED
  - PlayStation 4 vs PlayStation 5
  - Chromecast Original vs Chromecast with Google TV

### 📁 New Catalog Categories
| Category | Brands | Profiles |
|----------|--------|----------|
| TV | Samsung, LG, Sony, Vizio, TCL, Hisense, Philips, Panasonic, Sharp, Toshiba | 20 |
| Receiver | Denon, Yamaha, Onkyo, Marantz, Pioneer | 11 |
| Soundbar | Bose, Samsung, Sonos, Vizio | 5 |
| Streamer | Roku, Fire TV, Apple TV, Shield, Chromecast/Google TV | 12 |
| Projector | Epson, BenQ, Optoma, JVC | 8 |
| Cable/Satellite | DirecTV, Dish, TiVo, Xfinity | 8 |
| Game Console | Xbox, PlayStation, Nintendo | 5 |
| Blu-ray | Sony, Samsung, LG, Panasonic | 6 |
| AC | Daikin, LG, Mitsubishi, Fujitsu, Carrier | 5 |
| Fan | Hampton Bay, Hunter | 3 |
| Garage | Chamberlain/MyQ, Genie, Shelly, ratgdo | 6 |
| Lighting | Bond Bridge, Lutron Caseta, WLED | 5 |

### 🔧 Protocol Support
- **IR Protocols**: NEC, Samsung32, Sony SIRC (12/15/20-bit), RC5, RC6, Panasonic/Kaseikyo, JVC
- **RF Protocols**: 315MHz, 433MHz, 303MHz (ceiling fans)
- **Network Protocols**: HTTP REST, Telnet, WebSocket, ADB, Cast, MQTT, LEAP, eISCP

---

## v1.4.5 - JavaScript Fix (2024-02-24)

### 🐛 Bug Fixes
- **Fixed JavaScript syntax error** in panel.js that prevented the panel from rendering
- Removed orphaned HTML template code at line 1522 that was outside any function
- Panel now renders correctly in the browser

### 📝 Notes
- If upgrading from v1.4.4 or earlier, clear your browser cache (Ctrl+Shift+R)

---

## v1.4.4 - Runtime Fixes (2024-02-24)

### 🐛 Bug Fixes
- **Fixed blocking `read_text()` call** - Now uses `async_add_executor_job` to avoid blocking the event loop
- **Removed deprecated `register_static_path`** - This API was removed in newer Home Assistant versions
- **Fixed `DeviceCategory` enum** - Added missing values: `STREAMER`, `BLURAY`, `DVR`, `CABLE`, `GAME_CONSOLE`
- **Fixed version mismatch** - Panel.js and const.py now have matching version numbers

---

## v1.4.3 - Import Error Fix (2024-02-24)

### 🐛 Bug Fixes
- **Fixed catalog.py import error** - DeviceCategory enum values in catalog.py now match const.py
- Added missing enum values to `DeviceCategory`:
  - `STREAMER` (was using non-existent value)
  - `BLURAY` (new)
  - `DVR` (new)
  - `CABLE` (new)
  - `GAME_CONSOLE` (new)

---

## v1.4.2 - Config Flow Simplification (2024-02-24)

### 🔧 Changes
- Simplified `config_flow.py` to avoid import chain issues
- Hardcoded DOMAIN in config_flow to prevent circular imports
- Minimal config step with no data fields required

---

## v1.4.1 - Config Flow Fix (2024-02-24)

### 🐛 Bug Fixes
- **Fixed "Invalid handler specified" error** when adding integration
- Removed `bluetooth` from manifest.json dependencies (was causing failures on systems without Bluetooth)
- Bluetooth functionality remains available but optional
- Cleaned up strings.json to match Home Assistant format requirements

---

## v1.4.0 - Scene Editor & HA Entity Integration (2024-02-24)

### ✨ New Features

#### Scene Editor Improvements
- **Fixed device command loading** - Device dropdown now properly populates command options
- Added `onchange` handlers to device/entity/service dropdowns
- Dynamic service data fields based on selected entity domain

#### Home Assistant Entity Integration
Expanded from 6 to 14 controllable entity domains in scenes:

| Category | Domains |
|----------|---------|
| Media/Entertainment | `media_player`, `remote` |
| Lighting | `light` (with brightness, color support) |
| Switches | `switch`, `input_boolean` |
| Climate | `climate`, `fan`, `humidifier` |
| Covers | `cover` (blinds, curtains, garage doors) |
| Automation | `scene`, `script`, `automation` |
| Inputs | `input_number`, `input_select` |
| Other | `vacuum`, `lock`, `siren` |

#### Domain-Specific Services
- **Light**: turn_on/off/toggle, brightness_set, color_temp_set
- **Climate**: set_hvac_mode, set_preset_mode, set_temperature
- **Cover**: open_cover, close_cover, stop_cover, set_cover_position
- **Fan**: set_percentage, set_preset_mode
- **Media Player**: select_source, volume controls, playback controls
- **Input Number**: set_value, increment, decrement
- **Input Select**: select_option, select_next, select_previous

#### IR Device Catalog (Initial)
- 38 pre-built device profiles across 8 categories
- IR protocol helpers: NEC, Samsung32, Sony SIRC, RC5, RC6
- Brand logos from CDN for UI display

---

## v1.3.1 - Bug Fixes (2024-02-24)

### 🐛 Bug Fixes
- Fixed JSON parsing issues with BOM (Byte Order Mark) in uploaded files
- Fixed API authentication 401 errors with Bearer token
- Improved error handling for malformed JSON responses

---

## v1.3.0 - Scene System Overhaul (2024-02-24)

### ✨ New Features
- **Complete scene system redesign** with ON/OFF sequences
- Smart device state tracking to skip redundant commands
- Delay actions between commands
- Scene editor GUI in panel

### 🔧 Changes
- Scenes now have separate `on_actions` and `off_actions` lists
- Each action supports: IR command, RF command, delay, or HA service call
- "Skip if already on/off" option for power commands

---

## v1.2.0 - Network Devices & Bluetooth (2024-02-23)

### ✨ New Features
- **Network device support**: Control devices via REST API, Telnet, ADB
- **Bluetooth remote pairing**: Map physical BT remotes to OmniRemote commands
- **Area-based remotes**: Assign remotes to Home Assistant areas
- **mDNS discovery**: Auto-discover Broadlink devices across VLANs

### Supported Network Devices
- Roku (ECP API)
- Fire TV (ADB)
- Onkyo AVR (eISCP)
- Shelly devices
- BenQ Projectors

---

## v1.1.0 - Activities & Brand Logos (2024-02-22)

### ✨ New Features
- **Activities**: Complex multi-device workflows with timing
- **App launching**: Launch apps on Roku, Fire TV, etc.
- **Channel tuning**: Tune to specific channels with number pad sequences
- **Brand logos**: Display manufacturer logos in the UI
- **HACS integration**: Proper HACS repository structure

---

## v1.0.0 - Initial Release (2024-02-22)

### ✨ Features
- **Flipper Zero IR import**: Import .ir files from Flipper Zero
- **Broadlink integration**: Send IR/RF codes via Broadlink devices
- **Room organization**: Organize devices by room
- **Device management**: Add, edit, delete devices and their codes
- **Code learning**: Learn new IR codes from existing remotes
- **Panel GUI**: Full web-based management interface
- **Home Assistant integration**: Native HA config flow and entities

### Supported Platforms
- `remote` - Remote control entities for each device
- `scene` - Scene entities for automation
- `button` - Button entities for individual commands
- `switch` - Switch entities for power control

---

## Installation

### From HACS (Recommended)
1. Add custom repository: `https://github.com/HunterAviator/OmniRemote`
2. Install "OmniRemote"
3. Restart Home Assistant
4. Add integration: Settings → Devices & Services → Add Integration → OmniRemote

### Manual Installation
1. Download the latest release
2. Extract to `/config/custom_components/omniremote/`
3. Restart Home Assistant
4. Add integration via UI

---

## Upgrade Notes

### Upgrading to v1.5.0
- The catalog structure has changed significantly
- Old catalog.py is replaced with organized subfolders
- Backward compatibility maintained via catalog.py wrapper

### Upgrading to v1.4.x
- Clear browser cache after upgrading (Ctrl+Shift+R)
- Scene data structure is backward compatible

### Upgrading from v1.2.x or earlier
- Scene format changed in v1.3.0
- Existing scenes will need to be recreated

---

## Support

- **Issues**: https://github.com/HunterAviator/OmniRemote/issues
- **Discussions**: https://github.com/HunterAviator/OmniRemote/discussions

