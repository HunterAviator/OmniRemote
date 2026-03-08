# OmniRemote Changelog

## [1.10.14] - 2026-03-07

### Added
- **Import Buttons from Model** - Button mapping modal now has "Import Buttons" feature
  - Select any remote model and click Import to add all its buttons
  - Automatically sets suggested action types (volume_up, mute, etc.)
  - Shows button icons and colors from model definition
  - Shows button descriptions/hints for each button
  
- **Activity Action Type** - Map buttons to run OmniRemote activities
  - New "🎯 Run Activity" option in action type dropdown
  - Activities dropdown shows all configured activities

### Changed
- Button mapping modal now auto-loads buttons from remote's `model_id`
- Each button row shows icon, label, and description from model
- Model_id is now saved when saving button mappings
- Added Enter key support for adding new buttons

### Fixed
- Button mapping now properly shows buttons from new `remote_models.py` system
- Activity action type now properly handled in save/load

## [1.10.13] - 2026-03-07

### Added
- **Smart Discovery Modal** - Discover button now shows interactive modal instead of alert
  - Direct "Add" button on each discovered device
  - Auto-detects matching remote model based on device name patterns
  - Shows confidence indicators (high/medium/low) for model matches
  - Pre-fills device details (MAC/IEEE, model, manufacturer) when adding
  - Back button to return to discovery results

- **Bluetooth Model Auto-Detection** - New pattern matching system in `remote_models.py`
  - Matches device names to known models (Fire TV, G20S, Apple TV, etc.)
  - Detects HID service UUID for generic keyboard/remote devices
  - Returns match confidence and reasoning
  - Suggests best-fit model for unknown devices

### Changed
- Discovery flow is now modal-based with device cards
- Adding discovered remotes pre-fills form with detected settings
- Model selection auto-selects based on device detection

### Technical
- Added `get_model_for_bluetooth()` function in remote_models.py
- Added `match_bluetooth_device()` for name pattern matching
- Discovery now returns `suggested_model_id`, `match_confidence`, `match_reason`
- New panel actions: `add-discovered-remote`, `back-to-discovery`

## [1.10.12] - 2026-03-07

### Added
- **Bluetooth Remote Discovery** - Discover button now searches for both Zigbee AND Bluetooth remotes
  - Scans Home Assistant's Bluetooth integration for remote-like devices
  - Detects devices by name patterns (G20, Air Mouse, Fire TV, Roku, etc.)
  - Identifies HID (keyboard/mouse) devices by service UUID
  - Shows RSSI signal strength for Bluetooth devices
  - Checks both discovered and already-paired Bluetooth devices

### Changed
- **Discover Remotes** - Now shows combined results from Zigbee and Bluetooth
  - Displays device type (Zigbee vs Bluetooth) in results
  - Shows IEEE address for Zigbee, MAC address for Bluetooth
  - Better instructions when no remotes found

### API
- Added `discover_bluetooth` action to physical_remotes API
- Added `discover_remotes` action that returns both Zigbee and Bluetooth
- Returns `{zigbee: [], bluetooth: [], total: N}` format

## [1.10.11] - 2026-03-07

### Added
- **Wiki: Flipper Zero Setup** - USB vs Bluetooth recommendations, troubleshooting
- **Wiki: Bluetooth Proxy Setup** - Full 10-step ESP32 setup guide with YAML template

## [1.10.10] - 2026-03-07

### Added
- New remote models: RUPA BT Voice, Dupad Story BT, Amazon Fire TV L5B83G, G20S Pro Plus

## [1.10.9] - 2026-03-07

### Fixed
- Flipper Bluetooth connection with retry logic and slot detection

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


## [1.10.2] - 2024-02-27

### Fixed
- **500 Error Adding Bluetooth Remote** - Added `bluetooth_ha` to RemoteType enum
- **Bluetooth/Area Remote Import Errors** - Made bluetooth imports defensive (optional)
- **Flipper Zero Discovery** - Now uses HA Bluetooth integration for BLE discovery on HA Yellow

### Added
- `pyserial` to requirements for USB port discovery
- Debug logging for USB port discovery
- HA Bluetooth integration fallback for Flipper discovery

### Changed
- Bluetooth remote manager now gracefully handles missing bluetooth module


## [1.10.3] - 2024-02-27

### Fixed
- **Remote Builder "New Remote" Button** - Added missing `_showBuilderNewModal()` function
- **Remote Builder Command Selection** - Now shows dropdown with available commands from selected device
- **Device command dropdown** - Re-renders when device selection changes

### Changed
- Builder property panel now shows command count when commands are available
- Helpful messages when no commands found for a device


## [1.10.4] - 2024-02-28

### Fixed
- **Physical Remote Button Mapping** - Complete rewrite of button mapping UI
  - Now properly supports: Scenes, IR Commands (with device/command/blaster), HA Services, Volume controls
  - Dynamic dropdowns update when device selection changes
  - Added blaster selection for IR commands
  - Proper form field collection on save
- **API save_button_mappings** - New endpoint to save all button mappings at once with proper field mapping
- **Flipper Zero async_discover_all** - Fixed broken function definition

### Changed
- **Flipper Bluetooth Discovery** - Much more detailed logging to help diagnose issues
  - Logs total number of BLE devices found by HA
  - Logs individual device names for debugging
  - Clear instructions in logs for Flipper setup

### Notes
For Flipper Bluetooth to work:
1. On Flipper: Settings → Bluetooth → ON
2. Flipper must NOT be connected to qFlipper or mobile app
3. Check HA logs for "Starting Flipper Zero Bluetooth discovery..."


## [1.10.5] - 2024-02-28

### Fixed
- **Discover Button** - Now shows discovered devices with type, IP, MAC in a modal instead of just a count. Added "Add" button for each discovered device.
- **Physical Remote Button Mapping** - Fixed "Add Button" not saving or showing newly added buttons. Modal now properly preserves state when re-rendering.

### Added
- **Remote Builder - Room Selection** - Associate remote profiles with rooms for context-aware control
- **Remote Builder - Blaster Selection** - Set a default blaster for the remote profile
- **Remote Builder - Default Device** - Set a default IR device for command-based buttons
- **Dashboard Card Button** - New "Dashboard Card" button in builder shows YAML to copy for adding remote as a Lovelace card
- **Dashboard Card Instructions** - Step-by-step guide for adding remote card to dashboard

### Changed
- Grid Settings modal renamed to "Remote Settings" with expanded options
- Improved discovery UI with device details modal


## [1.10.6] - 2024-02-28

### Fixed
- **Flipper Zero Bluetooth Discovery** - Complete rewrite of discovery function
  - Now shows modal with results if inline UI elements not available
  - Better error handling and user feedback
  - Detailed logging for debugging
  - Shows Bluetooth vs USB icon for each discovered device
- **Flipper Add Button** - Fixed click handlers not being attached properly

### Changed
- **Discovery UI** - Results now shown in proper modal with device details
- **Card Profile Support** - omniremote-card.js now supports loading profiles from Remote Builder
  - Use `profile: profile_id` in card YAML
  - Automatically loads buttons, layout, room, and blaster from saved profile

### Dashboard Card Usage
```yaml
type: custom:omniremote-card
profile: profile_abc123
# Optional overrides:
# name: Living Room TV
# blaster: rm4_living_room
# show_header: true
```


## [1.10.7] - 2024-02-28

### Fixed
- **Button Mapping Save** - Fixed mappings not persisting after save
  - ButtonMapping.to_dict() now includes UI-friendly field names (scene_id, device_id, etc.)
  - Frontend now correctly collects all mapping fields
  - Added comprehensive console logging for debugging

### Added
- **Debug Mode** - Added DEBUG = True flag in const.py for verbose logging
  - All OmniRemote operations now log to HA with [OmniRemote] prefix
  - Flipper discovery logs all BLE devices found
  - Button mapping save logs each button being processed
  - API calls log request/response data

- **Event Handlers** - Added listeners for omniremote_send_ir and omniremote_run_scene events
  - Physical remote button presses now actually trigger IR sends
  - Scene activation fires proper events

- **execute_button API** - New action to test button mappings from the UI
  - Executes the mapped action (scene, IR, HA service, volume)
  - Returns detailed result for debugging

### How to Debug
1. After installing, check HA logs for `[OmniRemote]` messages
2. Open browser DevTools (F12) → Console tab
3. When saving button mappings, you'll see:
   - `[OmniRemote] Saving button mappings for remote: ...`
   - `[OmniRemote] Processing button: ... action_type: ...`
   - `[OmniRemote] Final mappings object: {...}`
4. In HA logs you'll see:
   - `[OmniRemote DEBUG] save_button_mappings called with data: ...`
   - `[OmniRemote DEBUG] Button ... -> scene: ...`


## [1.10.8] - 2024-02-28

### Added
- **Remote Model Database** - Pre-configured button profiles for 15+ popular remotes:
  - IKEA: SYMFONISK Gen 2, TRÅDFRI Remote, TRÅDFRI Dimmer, STYRBAR, RODRET
  - Philips Hue: Dimmer Switch, Tap Dial
  - Aqara: Opple 6-Button, Mini Switch, Magic Cube
  - Lutron: Pico Remote
  - Sonoff: SNZB-01
  - Tuya: 4-Button Scene Controller
  - Apple TV Remote, Amazon Fire TV Remote
  
- **Model Selection in UI** - When adding a physical remote:
  - Dropdown to select remote model by manufacturer
  - Auto-populates button mappings with suggested actions
  - Icons, labels, and colors pre-configured

- **Enhanced Debug Panel**:
  - Debug Mode status indicator (shows if DEBUG=True in const.py)
  - "Test Log" button - writes test entry to HA log
  - "View HA Log" button - shows OmniRemote entries from home-assistant.log
  - "Download Log" button - downloads complete debug log file with:
    - IR encoder debug entries
    - All OmniRemote/Flipper entries from HA log
    - Version and timestamp info

### API Endpoints
- `GET /api/omniremote/remote_models` - List all remote model profiles
- `GET /api/omniremote/remote_models?grouped=true` - List grouped by manufacturer
- `POST /api/omniremote/remote_models` with action=apply - Apply model to physical remote
- `GET /api/omniremote/debug?download=true` - Download debug log file
- `GET /api/omniremote/debug?ha_log=true` - Get HA log entries

### Fixed
- Debug log refresh now shows debug_enabled status
- Fixed indentation error in original OmniApiDebug class
- Removed duplicate OmniApiDebug class definition


## [1.10.9] - 2024-02-28

### Flipper Zero Bluetooth Connection Improvements
- **Better error messages** - Connection failures now show specific troubleshooting steps
- **Diagnose button** - For Bluetooth Flippers, click the stethoscope icon to run diagnostics
- **Enhanced logging** - All connection attempts logged with `[OmniRemote]` prefix at INFO level
- **Traceback capture** - Full error details captured and shown in browser console

### Key Troubleshooting for Flipper Bluetooth
If connection fails, check:
1. **Flipper → Settings → Bluetooth → ON**
2. **Flipper → Settings → Bluetooth → Remote Control → Enable** (this is critical!)
3. **Disconnect Flipper from phone app and qFlipper**
4. **USB is more reliable** - consider using USB instead of Bluetooth

### Diagnose Feature
Click the stethoscope icon (🩺) next to a Bluetooth Flipper to run diagnostics:
- Checks if device is in HA Bluetooth cache
- Verifies bleak library is installed
- Checks bleak-retry-connector availability
- Shows current connection status


## [1.10.10] - 2024-02-28

### New Remote Models Added
- **RUPA** Bluetooth Voice Remote
- **Dupad Story** Bluetooth Remote
- **Amazon Fire TV Voice Remote L5B83G** (with app shortcut buttons)
- **G20S Pro Plus** Air Mouse (20BTS Plus with gyroscope, backlight, IR learning)

### Flipper Zero Bluetooth Connection Fixes
- **Connection Slot Detection** - Now properly detects when HA Bluetooth adapter is out of connection slots
- **Better Error Messages** - Shows specific troubleshooting for slot exhaustion
- **Removed incorrect setting** - Removed reference to non-existent "Remote Control → Enable" setting

### Connection Slot Issue Explained
Your HA Yellow's Bluetooth adapter has limited connection slots (typically 3-7). If you have other Bluetooth devices connected (sensors, trackers, etc.), the Flipper can't connect.

**Solutions:**
1. **Use USB instead** - Most reliable option
2. **Disconnect other BT devices** - Free up slots
3. **Add ESPHome Bluetooth Proxy** - https://esphome.github.io/bluetooth-proxies/

### What to Do
1. Plug Flipper into HA via USB cable
2. In OmniRemote, click "Find USB" instead of "Find Bluetooth"
3. USB connection is faster and more reliable anyway


## [1.10.11] - 2024-02-28

### Wiki Updates
- **New: Flipper Zero Setup** - Complete guide for USB and Bluetooth connection
- **New: Bluetooth Proxy Setup** - Step-by-step ESP32 Bluetooth Proxy instructions including:
  - Driver installation (CP210x)
  - ESPHome Dashboard configuration
  - YAML template with bluetooth_proxy config
  - Web flashing instructions (web.esphome.io)
  - Troubleshooting common issues
  - Pre-built device alternatives (Athom, GL-S10)

### Flipper Bluetooth Notes
- Clarified that "connection slot" errors are HA Bluetooth adapter limits
- USB connection strongly recommended over Bluetooth
- Bluetooth Proxy adds slots but USB is still more reliable

