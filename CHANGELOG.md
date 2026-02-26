# OmniRemote Release Notes

## v1.8.0 - Enhanced Room View & HA Entity Integration (2024-02-26)

### ✨ New Features

#### Enhanced Room View
- **Complete room overview** showing scenes, devices, and HA entities in one place
- **Quick action buttons** for devices and entities directly in room view
- **Add items from room** - Add scenes, devices, or HA entities without leaving the room
- **Room editing** - Update room name and icon, or delete room
- **Quick power buttons** for IR devices

#### HA Entity Integration Improvements
- **Search by integration name** - Search for "onkyo", "universal_devices", etc.
- **Filter by domain** - Filter to show only lights, covers, media_players, etc.
- **Available services display** - See open_cover, close_cover, volume_up, etc. for each entity
- **Device type assignment** - Assign icons like projector_screen, receiver, tv, fan to HA entities
- **Quick controls** - One-click buttons for power, open/close, volume, lock/unlock

#### Entity Data Enhancements
API now returns richer HA entity data:
- `integration` / `platform` - The integration providing the entity
- `manufacturer` / `model` - Device manufacturer and model info  
- `area_id` / `area_name` - HA area assignment
- `device_class` - Entity device class (garage, blind, etc.)
- `services` - List of available service calls for the entity
- `supported_features` - Feature bitmask

#### Room Entity Management  
- Assign HA entities to OmniRemote rooms
- `entity_ids` stored on Room objects
- Auto-matches entities by HA area name

---

## v1.7.0 - Icon Picker & Help Wiki (2024-02-26)

### ✨ New Features

#### Visual Icon Picker for Scenes
- Browse icons by category: Media, Lighting, Climate, Activities, Security, Power, Time
- Live preview of selected icon
- Custom icon input with mdi: prefix support
- Click to select, instant visual feedback

#### Help & Wiki Section
New comprehensive documentation built into the panel:
- **Getting Started** - Quick start guide and hardware overview
- **IR Blasters** - Setup for Broadlink and Flipper Zero
- **Adding Devices** - Catalog, manual, learning, and importing
- **Scenes & Automation** - Creating scenes with examples
- **IR Protocols & Codes** - Protocol reference and resources
- **Troubleshooting** - Common issues and solutions
- **API & Services** - Home Assistant service calls and REST API

---

## v1.6.9 - API Auth Fix (2024-02-26)
Imported devices show with the HA icon and can be used in scenes alongside IR devices.

### 🐛 Bug Fixes

#### Improved Cache Busting
- More aggressive version mismatch detection
- Prominent orange "Reload Panel" banner when update available
- Direct reload button (no manual cache clearing needed)
- URL parameter cache-busting for version API

#### Scene Room Assignment
- Added debug logging for scene save
- Fixed empty string vs null handling for room_id
- Check browser console for save details

### 📝 Also Includes
- All fixes from v1.6.9 (API auth)
- Corrected Onkyo IR codes (v1.6.8)
- Flipper Zero support (v1.6.7)

---

## v1.6.9 - API Auth Fix (2024-02-26)

### 🐛 Bug Fixes

- **Fixed HTTP 401 errors** on debug/test API calls
  - All internal panel APIs now use `requires_auth = False`
  - Panel authentication is handled by HA's panel system
  - Fixes "Encoding failed: HTTP 401: Unauthorized" error

### 📝 Also Includes

- **Corrected Onkyo IR codes** (from v1.6.8)
  - Power toggle: `0x04` (was `0x1D`)
