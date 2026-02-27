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

## [1.8.1] - 2024-02-26

### Fixed
- **CRITICAL: Blank page fix** - Fixed JavaScript syntax error (escaped backticks) in wiki view that caused panel to show blank page
- **API Error fix** - Fixed KeyError: 'database' in physical remotes and remote bridges API endpoints by using safe `_get_database()` helper
- All API endpoints now gracefully handle cases where integration isn't fully configured


## [1.8.3] - 2024-02-26

### Fixed
- **CRITICAL: Blank page fix** - Fixed JavaScript syntax error (escaped backticks) in wiki view that caused panel to show blank page
- **API Error fix** - Fixed KeyError: 'database' in physical remotes and remote bridges API endpoints by using safe `_get_database()` helper
- All API endpoints now gracefully handle cases where integration isn't fully configured


## [1.8.4] - 2024-02-26

### Added
- **Refresh Data button** - Added refresh button (🔄) to header on all views for easy data reload
- Dashboard, Devices, Scenes, Blasters, Room views now have visible refresh button
- Refresh calls _loadData() to re-fetch all data from API

### Fixed  
- Reload button was only visible during version mismatch - now always available


## [1.9.0] - 2024-02-26

### Added
- **Remote Builder** - New visual remote profile builder
  - Create custom remote layouts with drag-and-drop button placement
  - Choose from templates: TV, Receiver, Streaming, Soundbar, Universal
  - Visual grid editor with real-time preview
  - Button configuration: label, icon, color, shape, size (span multiple cells)
  - Action mapping: IR commands, HA services, scenes
  - Preview mode to test buttons
  - Save profiles to sync with mobile apps
  - Duplicate and delete profiles
- New navigation item "Remote Builder" in sidebar
- API endpoints for custom profile CRUD operations
- Profile templates with pre-defined button layouts

### Technical
- Added RemoteProfile and RemoteButton model support in API
- Profile persistence in OmniRemote database
- Template system for quick profile creation


## [1.8.5] - 2024-02-26

### Added
- **Remote Profile Builder** - Full visual remote layout editor with:
  - Profile list view with create/edit/delete/duplicate
  - Visual grid-based button placement editor
  - Pre-built templates (TV, Receiver, Streaming, Soundbar, more)
  - Button property panel with icon picker
  - Quick-add buttons for common commands
  - Grid settings (rows, columns, device type)
  - Default device assignment for all buttons
  - Button action types: IR Command, HA Service, Scene
  - Button customization: shape, color, span, labels
  - Profiles sync to mobile apps via API

### Changed
- Remote Profiles API now handles nested profile objects from builder
- Builder state variables added for profile editing


## [1.8.5] - 2024-02-26

### Added
- **Remote Profile Builder** - Visual drag-and-drop remote layout editor
  - Create custom remote profiles that sync to mobile apps
  - Pre-built templates: TV, Receiver, Streaming, Soundbar, Projector, AC, Universal
  - Visual grid editor with click-to-add buttons
  - Button properties: label, icon, shape, color, size (spanning cells)
  - Action types: IR Command, HA Service, Scene, None
  - Quick-add buttons for common controls (power, volume, navigation, etc.)
  - Default device assignment per profile
  - Grid settings: resize rows/cols, change device type, icon, description
  - Save/duplicate/delete profiles
  - Profiles saved to database and sync-ready for mobile apps

### Fixed
- Removed duplicate _builderView functions that were causing conflicts
- Consolidated builder code into single comprehensive implementation


## [1.9.1] - 2024-02-27

### Fixed
- **Critical: Blank page fix** - Removed duplicate builder action handlers that called undefined methods
- Builder actions now correctly dispatch to _handleBuilderAction handler


## [1.9.2] - 2024-02-27

### Fixed
- **Enhanced cache-busting** - Added ETag headers and content hash for better cache invalidation
- Panel now includes X-Content-Hash header for debugging cache issues
- Improved logging of panel.js hash on load

### Notes
If panel version is stuck, try these steps in order:
1. Restart Home Assistant completely
2. Hard refresh browser (Ctrl+Shift+R)
3. Clear browser cache and cookies for your HA instance
4. Try incognito/private browsing mode

