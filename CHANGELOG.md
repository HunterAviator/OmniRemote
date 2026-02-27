# OmniRemote Changelog

## [1.9.2] - 2024-02-27

### Fixed
- **Critical: Blank page fix** - Removed duplicate action handlers that called undefined methods
- **Cache-busting improved** - Added ETag and X-Content-Hash headers for better cache invalidation
- **Version sync** - All version numbers now synchronized (const.py, manifest.json, panel.js)

### Added
- **Remote Builder** - Visual remote profile builder for creating custom layouts
  - Start from templates: TV, Receiver, Streaming, Soundbar, Universal
  - Drag-and-drop button placement on grid
  - Configure button appearance: label, icon, color, shape, size
  - Map buttons to IR commands, HA services, or scenes
  - Preview mode to test buttons live
  - Save profiles to sync with mobile apps

### Notes
If panel version is stuck, try:
1. Restart Home Assistant completely
2. Hard refresh browser (Ctrl+Shift+R)
3. Clear browser cache
4. Try incognito/private browsing mode

## [1.8.x] - Previous Releases

### Features
- Room organization with custom icons
- Device management with IR code learning
- Scene automation with multi-step actions
- Blaster discovery (Broadlink RM devices)
- Device catalog with 90+ pre-built IR profiles
- Physical remote support (Zigbee, RF, Bluetooth)
- Flipper Zero integration (USB/Bluetooth)
- IR Debugger with visual feedback
- Help & Wiki section
- Home Assistant entity integration (14 domains)
- Brand logos for devices
- HACS compatibility

## [1.0.0] - Initial Release

- Basic IR remote control via Broadlink
- Device and room management
- Simple scene automation

## [1.9.3] - 2024-02-27

### Enhanced
- **Import from Home Assistant** - Major improvements to entity import modal:
  - **Integration dropdown filter** - Filter entities by integration (e.g., Onkyo, Roku, Hue)
  - **Domain dropdown filter** - Filter by entity type (media_player, light, switch, etc.)
  - **Enhanced search** - Search by name, entity_id, integration, manufacturer, or model
  - **Device info display** - Shows manufacturer and model from device registry
  - **Grouped by integration** - Entities organized by their source integration
  - **Entity count** - Shows filtered count vs total
  - Added more domains: sensor, binary_sensor, button, scene


## [1.9.4] - 2024-02-27

### Fixed
- **Flipper Zero Add button** - Fixed data passing, added error handling and logging
- **Template creation** - All templates now properly create remotes (projector, AC, fan, etc.)

### Enhanced
- **Remote Builder Templates** - Added more templates:
  - Device templates: TV, Receiver, Streaming, Soundbar, Projector, AC, Ceiling Fan
  - Design variations: Blackout (stealth dark), Backlit (neon glow), Minimal Circles, Gaming Controller
  - Templates categorized into Device, Design, and Blank sections
  
- **Bluetooth Remote Pairing** - New support for HA Yellow / built-in Bluetooth:
  - Bluetooth adapter selection (hci0 built-in, hci1 USB dongle)
  - Device scanning with RSSI display
  - One-click pairing from discovered devices
  - Manual MAC address entry option
  - Uses HA's bluetooth component or falls back to bluetoothctl

### Added
- New Bluetooth API endpoint for HA built-in Bluetooth adapter
- Bluetooth scan, pair, unpair, and list_paired actions


## [1.9.5] - 2024-02-27

### Fixed
- **HA Entity Import button** - Import buttons now work after filtering
  - Click handlers properly attached after list updates
  - Added detailed console logging for debugging
  - Added try-catch with error alerts


## [1.9.5] - 2024-02-27

### Fixed
- **Flipper Zero Add button** - Complete fix: buttons now use direct onclick handlers with visual feedback (shows "Adding..." while processing)
- Dynamic button click handlers now work reliably in all contexts

### Enhanced
- **Remote Builder Icon Picker** - Complete visual icon browser:
  - Categorized icon grid: Power, Navigation, Volume, Input, Numbers, TV, Climate, Lighting, Gaming, etc.
  - Visual icon search filter
  - Custom MDI icon input with link to icon library
  - **Photo Upload Tab**: Upload custom images for buttons
  - Image scaling slider (50-200%)
  - Output size selection (48-128px)
  - Live preview at different button sizes (small, medium, wide)
  - Base64 encoding for profile storage

- **Bluetooth Device Search** - Filter discovered devices:
  - Real-time search by device name or MAC address
  - Search field integrated into scan UI
  - Better visual feedback during pairing


## [1.9.6] - 2024-02-27

### Fixed
- **HA Entity Import button** - Fixed using event delegation on modal container
  - Click events now properly bubble up and are handled
  - Works with dynamically filtered/re-rendered entity lists
  - Added console logging for debugging


## [1.9.7] - 2024-02-27

### Fixed
- **Flipper Zero connection error handling** - Now shows helpful error messages explaining why connection failed (USB port busy, Bluetooth out of range, etc.)
- **Flipper Add flow** - Device is added even if initial connection fails, with clear messaging

### Added
- **HACS validation files** - Added hacs.json for proper HACS repository validation
- **Streaming Service Icons** - Quick-add buttons for major streaming apps:
  - Netflix, YouTube, Prime Video, Disney+, Hulu, Max (HBO), Apple TV+
  - Peacock, Paramount+, Spotify, Tubi, Pluto TV, Vudu, Plex
  - Crunchyroll, Twitch
- **TV Channel Icons** - ESPN, FOX, NBC, CBS, ABC, CNN
- **Number Pad Buttons** - 0-9 quick-add buttons
- **Color Buttons** - Red, Green, Yellow, Blue TV color buttons
- **Organized Quick-Add** - Buttons now grouped by category (Controls, Navigation, Media, Streaming, Channels, Numbers, Colors)


## [1.9.8] - 2024-02-27

### Fixed
- **HACS Installation** - Removed zip_release requirement from hacs.json
  - HACS now downloads directly from repository (standard method)
  - No longer requires attached zip file on releases


## [1.9.9] - 2024-02-27

### Fixed
- **Flipper Zero Bluetooth Connection** - Uses bleak-retry-connector for reliable BLE connections
  - Integrates with Home Assistant's Bluetooth component for better device management
  - Falls back to direct connection if HA Bluetooth integration not available
  - Added connection timeout (10 seconds)
  - Up to 3 connection retry attempts


## [1.10.0] - 2024-02-27

### Fixed
- **Bluetooth Remote Pairing** - Complete rewrite of Bluetooth pairing system
  - Uses D-Bus (dbus_fast) to communicate directly with BlueZ
  - Works properly inside HA OS Docker container
  - Falls back to HA's Bluetooth integration for BLE devices
  - Properly detects already-paired devices
  - Better error messages when pairing fails

### Note
- For classic Bluetooth remotes (non-BLE), pairing may still need to be done via HA Settings > Devices > Bluetooth
- BLE (Bluetooth Low Energy) remotes should pair directly from OmniRemote


## [1.10.0] - 2024-02-27

### Fixed
- **Bluetooth Remote Pairing** - Complete rewrite of pairing system
  - Now scans for both BLE and Classic Bluetooth devices using bluetoothctl
  - Pairing tries multiple methods: bluetoothctl → D-Bus → BLE connect
  - Better error messages explaining what went wrong
  - 30-second pairing timeout with clear feedback
  - Works with physical remotes (game controllers, media remotes, etc.)

### Changed
- Bluetooth scan now shows devices from both bluetoothctl and HA Bluetooth
- Pairing attempts classic Bluetooth pairing first (via bluetoothctl)
- Falls back to D-Bus and then BLE connection for different device types


## [1.9.10] - 2024-02-27

### Fixed
- **Bluetooth Remote Pairing** - Improved bluetoothctl pairing sequence
  - Uses NoInputNoOutput agent for auto-accept pairing
  - Enables scan mode before pairing attempt
  - Better error messages for common failure scenarios
  - Increased timeout to 45 seconds for slow devices
  - Falls back to HA Settings > Bluetooth if pairing fails


## [1.9.10] - 2024-02-27

### Fixed
- **Bluetooth Remote Pairing** - Improved pairing for HA Yellow/OS
  - Uses Home Assistant's native Bluetooth integration first
  - Better error messages with guidance to pair via HA Settings
  - Added info banner explaining recommended pairing workflow
  - Falls back to multiple pairing methods (HA Bluetooth → D-Bus → bluetoothctl)

### Changed
- Bluetooth pairing UI now shows tip to pair via Settings first


## [1.10.0] - 2024-02-27

### Fixed
- **Flipper Zero Bluetooth Connection**
  - Fixed `async_ble_device_from_address` not being awaited (it's not async)
  - Corrected Flipper BLE Serial service UUIDs
  - Added 20 second timeout for BLE connections
  - Better error messages with troubleshooting steps in logs
  
- **Bluetooth Remote Pairing**
  - Made HA Yellow/OS limitation more prominent (red warning banner)
  - Clear guidance to pair via Settings → Devices & Services → Bluetooth first
  - Better error alert when pairing fails

### Changed
- **Flipper Zero UI**
  - Added "USB Recommended" indicator
  - "Find USB" button is now primary/highlighted
  - Added setup instructions for Bluetooth (RPC over Bluetooth)
  
- **Bluetooth Remote UI**
  - Warning banner explains containerized HA limitation
  - Scan results show note about paired devices having green icon
  - Manual MAC input has helper text


## [1.10.1] - 2024-02-27

### Fixed
- **Bluetooth Pairing** - Major improvements to pairing on HA Yellow/OS
  - Added `dbus-fast` to requirements for D-Bus pairing support
  - Added `bluetooth` as dependency for proper HA integration
  - Fixed `async_ble_device_from_address` await bug in panel.py
  - D-Bus pairing now triggers discovery first to ensure device is found
  - Better error messages from D-Bus (AuthenticationCanceled, AuthenticationFailed, etc.)
  - Reordered pairing methods: D-Bus first (most reliable), then HA Bluetooth, then bluetoothctl

### Changed
- **Bluetooth UI** - Cleaner, less alarming
  - Removed scary red warning banner
  - Scan button is now primary (highlighted)
  - Pairing status shows in green/red with clear messages
  - No more popup alerts on failure

