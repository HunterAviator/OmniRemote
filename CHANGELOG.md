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

