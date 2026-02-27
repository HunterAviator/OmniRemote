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
