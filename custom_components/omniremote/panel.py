"""Panel and API for OmniRemote GUI."""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any

from aiohttp import web

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION, DeviceCategory, SceneAction, Blaster
from .database import RemoteDatabase
from .catalog import DEVICE_CATALOG, CATALOG_BY_BRAND, CATALOG_BY_CATEGORY, get_catalog_device, search_catalog, list_catalog
from .activities import Activity, ActivityAction, ActionType, ActivityRunner

_LOGGER = logging.getLogger(__name__)

PANEL_URL = "/omniremote"
PANEL_TITLE = "OmniRemote Manager"
PANEL_ICON = "mdi:remote-tv"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the panel and API."""
    import hashlib
    import time
    
    # Generate a unique cache-buster based on version AND a hash of panel.js
    panel_path = Path(__file__).parent / "panel.js"
    if panel_path.exists():
        content = panel_path.read_bytes()
        content_hash = hashlib.md5(content).hexdigest()[:8]
    else:
        content_hash = str(int(time.time()))
    
    cache_buster = f"{VERSION}-{content_hash}"
    
    # Check if we need to update (version changed)
    current_version = hass.data.get(DOMAIN, {}).get("_panel_version")
    if current_version == cache_buster:
        _LOGGER.debug("OmniRemote panel already registered with current version %s", cache_buster)
    else:
        _LOGGER.info("OmniRemote panel version change: %s -> %s", current_version, cache_buster)
        # Force re-registration by removing old panel
        if "omniremote" in hass.data.get("frontend_panels", {}):
            _LOGGER.info("Removing old OmniRemote panel for re-registration")
            try:
                hass.components.frontend.async_remove_panel("omniremote")
            except Exception as ex:
                _LOGGER.debug("Could not remove old panel: %s", ex)
    
    # Register API views (safe to call multiple times - HA handles duplicates)
    hass.http.register_view(OmniApiRooms(hass))
    hass.http.register_view(OmniApiDevices(hass))
    hass.http.register_view(OmniApiScenes(hass))
    hass.http.register_view(OmniApiBlasters(hass))
    hass.http.register_view(OmniApiCommands(hass))
    hass.http.register_view(OmniApiLearn(hass))
    hass.http.register_view(OmniPanelView(hass))
    hass.http.register_view(OmniApiCatalog(hass))
    hass.http.register_view(OmniApiActivities(hass))
    hass.http.register_view(OmniApiNetworkDevices(hass))
    hass.http.register_view(OmniApiBluetoothRemotes(hass))
    hass.http.register_view(OmniApiAreaRemotes(hass))
    hass.http.register_view(OmniRemoteCardResource(hass))
    hass.http.register_view(OmniApiVersion(hass))
    hass.http.register_view(OmniApiTest(hass))
    hass.http.register_view(OmniApiFlipperZero(hass))
    hass.http.register_view(OmniApiPhysicalRemotes(hass))
    hass.http.register_view(OmniApiRemoteBridges(hass))
    hass.http.register_view(OmniApiRemoteProfiles(hass))
    hass.http.register_view(OmniApiDebug(hass))
    hass.http.register_view(OmniIconView(hass))
    hass.http.register_view(OmniLogoView(hass))
    
    # Check if panel already exists (and is current version)
    if "omniremote" in hass.data.get("frontend_panels", {}) and current_version == cache_buster:
        _LOGGER.debug("OmniRemote panel already in frontend_panels with correct version")
        return
    
    try:
        # Register the panel with version+hash for cache-busting
        await panel_custom.async_register_panel(
            hass,
            webcomponent_name="omniremote-panel",
            frontend_url_path="omniremote",
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            module_url=f"/api/omniremote/panel.js?v={cache_buster}",
            embed_iframe=False,
            require_admin=False,
        )
        hass.data.setdefault(DOMAIN, {})["_panel_version"] = cache_buster
        _LOGGER.info("OmniRemote panel registered successfully (v%s)", cache_buster)
    except ValueError as ex:
        if "Overwriting" in str(ex) or "already registered" in str(ex).lower():
            _LOGGER.debug("Panel registration note: %s", ex)
            hass.data.setdefault(DOMAIN, {})["_panel_version"] = cache_buster
        else:
            raise

def _get_database(hass: HomeAssistant) -> RemoteDatabase | None:
    """Get the database instance."""
    for entry_data in hass.data.get(DOMAIN, {}).values():
        if "database" in entry_data:
            return entry_data["database"]
    return None


class OmniPanelView(HomeAssistantView):
    """Serve the panel JavaScript."""
    
    url = "/api/omniremote/panel.js"
    name = "api:omniremote:panel"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
        self._content_hash = None
        self._cached_content = None
    
    async def get(self, request: web.Request) -> web.Response:
        """Return the panel JavaScript."""
        import hashlib
        
        panel_path = Path(__file__).parent / "panel.js"
        
        _LOGGER.debug("Serving panel.js from: %s (exists: %s)", panel_path, panel_path.exists())
        
        if panel_path.exists():
            # Use async file read to avoid blocking
            content = await self.hass.async_add_executor_job(panel_path.read_text)
            content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
            _LOGGER.debug("Panel.js loaded, size: %d bytes, hash: %s", len(content), content_hash)
        else:
            _LOGGER.error("Panel.js not found at: %s", panel_path)
            content = "console.error('OmniRemote panel.js not found at " + str(panel_path) + "');"
            content_hash = "error"
        
        # Check If-None-Match header for conditional request
        etag = f'"{content_hash}"'
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match == etag:
            return web.Response(status=304)  # Not Modified
        
        # Add aggressive cache-control headers to prevent browser caching
        return web.Response(
            text=content,
            content_type="application/javascript",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
                "ETag": etag,
                "X-OmniRemote-Version": VERSION,
                "X-Content-Hash": content_hash,
            }
        )


class OmniApiRooms(HomeAssistantView):
    """API for room management."""
    
    url = "/api/omniremote/rooms"
    name = "api:omniremote:rooms"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all rooms."""
        import logging
        _LOGGER = logging.getLogger(__name__)
        
        database = _get_database(self.hass)
        if not database:
            _LOGGER.warning("OmniRemote database not found for rooms GET")
            return web.json_response({"rooms": [], "error": "Integration not configured"})
        
        rooms = [r.to_dict() for r in database.rooms.values()]
        return web.json_response({"rooms": rooms})
    
    async def post(self, request: web.Request) -> web.Response:
        """Create or update a room."""
        import logging
        import traceback
        _LOGGER = logging.getLogger(__name__)
        
        try:
            database = _get_database(self.hass)
            if not database:
                _LOGGER.error("OmniRemote database not found for rooms POST")
                return web.json_response({
                    "error": "Integration not configured. Go to Settings > Devices & Services > Add Integration > OmniRemote"
                }, status=500)
            
            try:
                data = await request.json()
                _LOGGER.info("Room API: %s", data)
            except Exception as ex:
                _LOGGER.error("Failed to parse room data: %s", ex)
                return web.json_response({"error": f"Invalid request data: {ex}"}, status=400)
            
            action = data.get("action", "create")
            
            if action == "update":
                # Update existing room
                room_id = data.get("id")
                if room_id and room_id in database.rooms:
                    room = database.rooms[room_id]
                    if "name" in data:
                        room.name = data["name"]
                    if "icon" in data:
                        room.icon = data["icon"]
                    if "entity_ids" in data:
                        room.entity_ids = data["entity_ids"]
                    await database.async_save()
                    return web.json_response({"room": room.to_dict(), "success": True})
                return web.json_response({"error": "Room not found"}, status=404)
            
            elif action == "delete":
                room_id = data.get("id")
                if room_id and room_id in database.rooms:
                    del database.rooms[room_id]
                    await database.async_save()
                    return web.json_response({"success": True})
                return web.json_response({"error": "Room not found"}, status=404)
            
            else:
                # Create new room
                room = database.add_room(
                    name=data.get("name", "New Room"),
                    icon=data.get("icon", "mdi:sofa"),
                )
                await database.async_save()
                _LOGGER.info("Created room: %s", room.name)
                
                return web.json_response({"room": room.to_dict(), "success": True})
        except Exception as ex:
            _LOGGER.error("Failed to process room: %s\n%s", ex, traceback.format_exc())
            return web.json_response({"error": str(ex)}, status=500)


class OmniApiDevices(HomeAssistantView):
    """API for device management."""
    
    url = "/api/omniremote/devices"
    name = "api:omniremote:devices"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all devices."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        devices = [d.to_dict() for d in database.devices.values()]
        return web.json_response({"devices": devices})
    
    async def post(self, request: web.Request) -> web.Response:
        """Create a new device."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        device = database.add_device(
            name=data.get("name", "New Device"),
            category=DeviceCategory(data.get("category", "other")),
            brand=data.get("brand", ""),
            model=data.get("model", ""),
            room_id=data.get("room_id"),
        )
        
        # Set entity_id for HA integration
        if data.get("entity_id"):
            device.entity_id = data["entity_id"]
        
        # Set catalog_id reference
        if data.get("catalog_id"):
            device.catalog_id = data["catalog_id"]
        
        # Set power commands if provided
        if data.get("power_on_command"):
            device.power_on_command = data["power_on_command"]
        if data.get("power_off_command"):
            device.power_off_command = data["power_off_command"]
        if data.get("input_commands"):
            device.input_commands = data["input_commands"]
        
        await database.async_save()
        
        return web.json_response({"device": device.to_dict()})
    
    async def put(self, request: web.Request) -> web.Response:
        """Update a device."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        device_id = data.get("id")
        
        if device_id not in database.devices:
            return web.json_response({"error": "Device not found"}, status=404)
        
        device = database.devices[device_id]
        
        if "name" in data:
            device.name = data["name"]
        if "category" in data:
            device.category = DeviceCategory(data["category"])
        if "brand" in data:
            device.brand = data["brand"]
        if "model" in data:
            device.model = data["model"]
        if "power_on_command" in data:
            device.power_on_command = data["power_on_command"]
        if "power_off_command" in data:
            device.power_off_command = data["power_off_command"]
        if "input_commands" in data:
            device.input_commands = data["input_commands"]
        if "power_state" in data:
            device.power_state = data["power_state"]
        if "current_input" in data:
            device.current_input = data["current_input"]
        if "lamp_hours" in data:
            device.lamp_hours = data["lamp_hours"]
        if "room_id" in data:
            # Remove from old room
            if device.room_id and device.room_id in database.rooms:
                old_room = database.rooms[device.room_id]
                if device_id in old_room.device_ids:
                    old_room.device_ids.remove(device_id)
            
            # Add to new room
            device.room_id = data["room_id"]
            if device.room_id and device.room_id in database.rooms:
                database.rooms[device.room_id].device_ids.append(device_id)
        
        await database.async_save()
        return web.json_response({"device": device.to_dict()})
    
    async def delete(self, request: web.Request) -> web.Response:
        """Delete a device."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        device_id = data.get("id")
        
        if database.delete_device(device_id):
            await database.async_save()
            return web.json_response({"success": True})
        
        return web.json_response({"error": "Device not found"}, status=404)


class OmniApiScenes(HomeAssistantView):
    """API for scene management."""
    
    url = "/api/omniremote/scenes"
    name = "api:omniremote:scenes"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all scenes and available HA entities."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        scenes = [s.to_dict() for s in database.scenes.values()]
        
        # Get ALL controllable HA entities for scene actions
        ha_entities = []
        
        # Domains we want to include
        controllable_domains = [
            # Media/Entertainment
            "media_player", "remote",
            # Lighting
            "light",
            # Switches & Plugs
            "switch", "input_boolean",
            # Climate & Comfort
            "climate", "fan", "humidifier",
            # Covers & Blinds
            "cover",
            # Automation
            "scene", "script", "automation",
            # Inputs
            "input_number", "input_select",
            # Misc
            "vacuum", "lock", "siren",
        ]
        
        # Get entity registry for additional info
        entity_registry = None
        device_registry = None
        area_registry = None
        try:
            from homeassistant.helpers import entity_registry as er
            from homeassistant.helpers import device_registry as dr
            from homeassistant.helpers import area_registry as ar
            entity_registry = er.async_get(self.hass)
            device_registry = dr.async_get(self.hass)
            area_registry = ar.async_get(self.hass)
        except Exception:
            pass
        
        # Domain-specific services
        domain_services = {
            "light": ["turn_on", "turn_off", "toggle"],
            "switch": ["turn_on", "turn_off", "toggle"],
            "fan": ["turn_on", "turn_off", "toggle", "set_percentage", "set_preset_mode"],
            "cover": ["open_cover", "close_cover", "stop_cover", "set_cover_position"],
            "climate": ["turn_on", "turn_off", "set_hvac_mode", "set_temperature", "set_preset_mode"],
            "media_player": ["turn_on", "turn_off", "toggle", "volume_up", "volume_down", "volume_mute", "volume_set", "media_play", "media_pause", "media_stop", "media_next_track", "media_previous_track", "select_source"],
            "remote": ["turn_on", "turn_off", "send_command"],
            "lock": ["lock", "unlock"],
            "vacuum": ["start", "stop", "pause", "return_to_base"],
            "scene": ["turn_on"],
            "script": ["turn_on", "turn_off"],
            "automation": ["turn_on", "turn_off", "trigger"],
            "input_boolean": ["turn_on", "turn_off", "toggle"],
            "input_select": ["select_option"],
            "input_number": ["set_value"],
            "humidifier": ["turn_on", "turn_off", "set_humidity"],
            "siren": ["turn_on", "turn_off"],
        }
        
        for state in self.hass.states.async_all():
            domain = state.entity_id.split(".")[0]
            if domain in controllable_domains:
                entity_data = {
                    "entity_id": state.entity_id,
                    "name": state.attributes.get("friendly_name", state.entity_id),
                    "domain": domain,
                    "state": state.state,
                    "services": domain_services.get(domain, []),
                }
                
                # Get device class
                device_class = state.attributes.get("device_class")
                if device_class:
                    entity_data["device_class"] = device_class
                
                # Get supported features bitmask
                supported_features = state.attributes.get("supported_features", 0)
                if supported_features:
                    entity_data["supported_features"] = supported_features
                
                # Get integration/platform info from entity registry
                if entity_registry:
                    entry = entity_registry.async_get(state.entity_id)
                    if entry:
                        entity_data["platform"] = entry.platform
                        entity_data["integration"] = entry.platform  # alias
                        if entry.device_id and device_registry:
                            device = device_registry.async_get(entry.device_id)
                            if device:
                                entity_data["device_name"] = device.name
                                # Get manufacturer/model
                                if device.manufacturer:
                                    entity_data["manufacturer"] = device.manufacturer
                                if device.model:
                                    entity_data["model"] = device.model
                                # Get area
                                if device.area_id and area_registry:
                                    area = area_registry.async_get_area(device.area_id)
                                    if area:
                                        entity_data["area_id"] = area.id
                                        entity_data["area_name"] = area.name
                        # Direct entity area
                        if entry.area_id and area_registry:
                            area = area_registry.async_get_area(entry.area_id)
                            if area:
                                entity_data["area_id"] = area.id
                                entity_data["area_name"] = area.name
                
                # Add domain-specific attributes
                if domain == "media_player":
                    sources = state.attributes.get("source_list", [])
                    if sources:
                        entity_data["sources"] = sources
                    entity_data["current_source"] = state.attributes.get("source")
                    entity_data["volume_level"] = state.attributes.get("volume_level")
                    entity_data["is_volume_muted"] = state.attributes.get("is_volume_muted")
                
                elif domain == "light":
                    entity_data["brightness"] = state.attributes.get("brightness")
                    entity_data["color_mode"] = state.attributes.get("color_mode")
                    entity_data["supported_color_modes"] = state.attributes.get("supported_color_modes", [])
                
                elif domain == "climate":
                    entity_data["hvac_modes"] = state.attributes.get("hvac_modes", [])
                    entity_data["current_temperature"] = state.attributes.get("current_temperature")
                    entity_data["target_temperature"] = state.attributes.get("temperature")
                    entity_data["preset_modes"] = state.attributes.get("preset_modes", [])
                
                elif domain == "cover":
                    entity_data["current_position"] = state.attributes.get("current_position")
                    # Add cover-specific services based on device class
                    if device_class == "garage":
                        entity_data["services"] = ["open_cover", "close_cover", "stop_cover", "toggle"]
                    elif device_class in ("blind", "shade", "curtain"):
                        entity_data["services"] = ["open_cover", "close_cover", "stop_cover", "set_cover_position"]
                    elif device_class == "awning":
                        entity_data["services"] = ["open_cover", "close_cover", "stop_cover"]
                
                elif domain == "fan":
                    entity_data["percentage"] = state.attributes.get("percentage")
                    entity_data["preset_modes"] = state.attributes.get("preset_modes", [])
                    entity_data["speed_count"] = state.attributes.get("speed_count")
                
                elif domain == "input_select":
                    entity_data["options"] = state.attributes.get("options", [])
                
                elif domain == "input_number":
                    entity_data["min"] = state.attributes.get("min")
                    entity_data["max"] = state.attributes.get("max")
                    entity_data["step"] = state.attributes.get("step")
                
                ha_entities.append(entity_data)
        
        return web.json_response({
            "scenes": scenes,
            "ha_entities": ha_entities,
        })
    
    async def post(self, request: web.Request) -> web.Response:
        """Create a new scene or perform scene action."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        action = data.get("action")
        
        # Scene activation/deactivation
        if action == "activate":
            scene_id = data.get("scene_id")
            success = await database.async_activate_scene(scene_id)
            return web.json_response({"success": success})
        
        if action == "deactivate":
            scene_id = data.get("scene_id")
            success = await database.async_deactivate_scene(scene_id)
            return web.json_response({"success": success})
        
        if action == "toggle":
            scene_id = data.get("scene_id")
            success = await database.async_toggle_scene(scene_id)
            scene = database.get_scene(scene_id)
            return web.json_response({
                "success": success,
                "is_active": scene.is_active if scene else False
            })
        
        # Create new scene
        on_actions = []
        for action_data in data.get("on_actions", []):
            on_actions.append(SceneAction.from_dict(action_data))
        
        off_actions = []
        for action_data in data.get("off_actions", []):
            off_actions.append(SceneAction.from_dict(action_data))
        
        scene = database.add_scene(
            name=data.get("name", "New Scene"),
            room_id=data.get("room_id"),
            icon=data.get("icon", "mdi:play"),
            blaster_id=data.get("blaster_id"),
            on_actions=on_actions,
            off_actions=off_actions,
            controlled_device_ids=data.get("controlled_device_ids", []),
            controlled_entity_ids=data.get("controlled_entity_ids", []),
        )
        await database.async_save()
        
        return web.json_response({"scene": scene.to_dict()})
    
    async def put(self, request: web.Request) -> web.Response:
        """Update a scene."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        scene_id = data.get("id")
        
        if scene_id not in database.scenes:
            return web.json_response({"error": "Scene not found"}, status=404)
        
        scene = database.scenes[scene_id]
        
        if "name" in data:
            scene.name = data["name"]
        if "icon" in data:
            scene.icon = data["icon"]
        if "room_id" in data:
            scene.room_id = data["room_id"]
        if "blaster_id" in data:
            scene.blaster_id = data["blaster_id"]
        if "controlled_device_ids" in data:
            scene.controlled_device_ids = data["controlled_device_ids"]
        if "controlled_entity_ids" in data:
            scene.controlled_entity_ids = data["controlled_entity_ids"]
        
        if "on_actions" in data:
            scene.on_actions = [SceneAction.from_dict(a) for a in data["on_actions"]]
        if "off_actions" in data:
            scene.off_actions = [SceneAction.from_dict(a) for a in data["off_actions"]]
        
        await database.async_save()
        return web.json_response({"scene": scene.to_dict()})
    
    async def delete(self, request: web.Request) -> web.Response:
        """Delete a scene."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        scene_id = data.get("id")
        
        if database.delete_scene(scene_id):
            await database.async_save()
            return web.json_response({"success": True})
        
        return web.json_response({"error": "Scene not found"}, status=404)


class OmniApiBlasters(HomeAssistantView):
    """API for blaster management."""
    
    url = "/api/omniremote/blasters"
    name = "api:omniremote:blasters"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all blasters including HA Broadlink entities."""
        database = _get_database(self.hass)
        
        blasters = []
        
        # Get blasters from our database
        if database:
            blasters = [b.to_dict() for b in database.blasters.values()]
        
        # Also look for HA's existing Broadlink remote entities
        ha_blasters = []
        try:
            for state in self.hass.states.async_all("remote"):
                entity_id = state.entity_id
                # Check if it's a Broadlink device
                if "broadlink" in entity_id.lower():
                    ha_blasters.append({
                        "id": entity_id,
                        "name": state.attributes.get("friendly_name", entity_id),
                        "host": state.attributes.get("host", "Unknown"),
                        "mac": state.attributes.get("mac", ""),
                        "device_type": "ha_broadlink",
                        "entity_id": entity_id,
                    })
        except Exception as ex:
            _LOGGER.warning("Error scanning for HA Broadlink entities: %s", ex)
        
        return web.json_response({
            "blasters": blasters,
            "ha_blasters": ha_blasters,
            "database_available": database is not None
        })
    
    async def post(self, request: web.Request) -> web.Response:
        """Discover or manually add blasters."""
        import logging
        _LOGGER = logging.getLogger(__name__)
        
        database = _get_database(self.hass)
        if not database:
            _LOGGER.error("OmniRemote database not found - is the integration configured?")
            return web.json_response({
                "error": "Database not found. Please configure OmniRemote integration first via Settings > Devices & Services > Add Integration > OmniRemote",
                "blasters": [],
                "discovered_count": 0
            })
        
        try:
            data = await request.json()
        except Exception:
            data = {}
        
        _LOGGER.info("Blaster API POST request: %s", data)
        
        # Manual add by IP
        if data.get("action") == "add" and data.get("host"):
            try:
                _LOGGER.info("Adding blaster by IP: %s", data["host"])
                blaster = await database.async_add_blaster_by_ip(
                    host=data["host"],
                    name=data.get("name")
                )
                await database.async_save()
                _LOGGER.info("Successfully added blaster: %s", blaster.name if blaster else "None")
                
                return web.json_response({
                    "success": True,
                    "blaster": blaster.to_dict() if blaster else None
                })
            except Exception as ex:
                _LOGGER.error("Failed to add blaster: %s", ex)
                return web.json_response({
                    "success": False,
                    "error": str(ex)
                })
        
        # mDNS discovery (works across VLANs)
        if data.get("action") == "mdns":
            _LOGGER.info("Starting mDNS Broadlink discovery...")
            try:
                blasters = await database.async_discover_blasters_mdns()
                await database.async_save()
                _LOGGER.info("mDNS discovery complete, found %d blasters", len(blasters))
                
                return web.json_response({
                    "blasters": [b.to_dict() for b in blasters],
                    "discovered_count": len(blasters),
                    "success": True,
                    "method": "mdns"
                })
            except Exception as ex:
                _LOGGER.error("mDNS discovery failed: %s", ex)
                return web.json_response({
                    "blasters": [],
                    "discovered_count": 0,
                    "success": False,
                    "error": str(ex)
                })
        
        # Auto-discover (broadcast - same subnet only)
        _LOGGER.info("Starting Broadlink discovery...")
        try:
            blasters = await database.async_discover_blasters()
            await database.async_save()
            _LOGGER.info("Discovery complete, found %d blasters", len(blasters))
            
            return web.json_response({
                "blasters": [b.to_dict() for b in blasters],
                "discovered_count": len(blasters),
                "success": True
            })
        except Exception as ex:
            _LOGGER.error("Discovery failed: %s", ex)
            return web.json_response({
                "blasters": [],
                "discovered_count": 0,
                "success": False,
                "error": str(ex)
            })


class OmniApiCommands(HomeAssistantView):
    """API for sending commands."""
    
    url = "/api/omniremote/commands"
    name = "api:omniremote:commands"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def post(self, request: web.Request) -> web.Response:
        """Send a command or run a scene."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        action = data.get("action")
        
        if action == "send":
            device_id = data.get("device_id")
            command_name = data.get("command_name")
            
            device = database.devices.get(device_id)
            if not device:
                return web.json_response({"error": "Device not found"}, status=404)
            
            code = device.commands.get(command_name)
            if not code:
                return web.json_response({"error": "Command not found"}, status=404)
            
            success = await database.async_send_code(code)
            return web.json_response({"success": success})
        
        elif action == "run_scene":
            scene_id = data.get("scene_id")
            success = await database.async_run_scene(scene_id)
            return web.json_response({"success": success})
        
        return web.json_response({"error": "Unknown action"}, status=400)


class OmniApiLearn(HomeAssistantView):
    """API for learning commands."""
    
    url = "/api/omniremote/learn"
    name = "api:omniremote:learn"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def post(self, request: web.Request) -> web.Response:
        """Learn a new command."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        device_id = data.get("device_id")
        command_name = data.get("command_name")
        timeout = data.get("timeout", 15)
        
        if not device_id or not command_name:
            return web.json_response({"error": "Missing device_id or command_name"}, status=400)
        
        code = await database.async_learn_code(timeout=timeout)
        
        if code:
            code.name = command_name
            database.add_command_to_device(device_id, command_name, code)
            await database.async_save()
            
            return web.json_response({
                "success": True,
                "command": command_name,
            })
        
        return web.json_response({
            "success": False,
            "error": "Timeout - no code received",
        })


class OmniApiCatalog(HomeAssistantView):
    """API for device catalog."""
    
    url = "/api/omniremote/catalog"
    name = "api:omniremote:catalog"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get the device catalog."""
        query = request.query.get("search", "")
        category = request.query.get("category", "")
        brand = request.query.get("brand", "")
        
        if query:
            results = search_catalog(query)
        elif category:
            # CATALOG_BY_CATEGORY uses string keys
            results = CATALOG_BY_CATEGORY.get(category, [])
        elif brand:
            results = CATALOG_BY_BRAND.get(brand.lower(), [])
        else:
            results = list(DEVICE_CATALOG.values())
        
        return web.json_response({
            "devices": [d.to_dict() for d in results],
            "brands": list(CATALOG_BY_BRAND.keys()),
            "categories": list(CATALOG_BY_CATEGORY.keys()),
        })
    
    async def post(self, request: web.Request) -> web.Response:
        """Add a device from the catalog to the database."""
        from .ir_encoder import encode_ir_to_broadlink
        from .const import RemoteCode
        
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        catalog_id = data.get("catalog_id")
        device_name = data.get("name", "")
        room_id = data.get("room_id")
        profile_variant = data.get("profile_variant")  # For selecting alternate profiles
        
        catalog_device = get_catalog_device(catalog_id)
        if not catalog_device:
            return web.json_response({"error": "Catalog device not found"}, status=404)
        
        # Create device with pre-loaded codes
        device = database.add_device(
            name=device_name or catalog_device.name,
            category=catalog_device.category,
            brand=catalog_device.brand,
            model=catalog_device.name,
            room_id=room_id,
        )
        
        # Store catalog info for future reference
        device.catalog_id = catalog_id
        
        converted_count = 0
        failed_count = 0
        
        # Convert and copy IR codes
        for cmd_name, ir_code in catalog_device.ir_codes.items():
            broadlink_b64 = encode_ir_to_broadlink(ir_code)
            if broadlink_b64:
                device.commands[cmd_name] = RemoteCode(
                    source="catalog",
                    broadlink_code=broadlink_b64,
                    protocol=ir_code.protocol.value if ir_code.protocol else None,
                    address=ir_code.address,
                    command=ir_code.command,
                )
                converted_count += 1
            else:
                _LOGGER.warning("Could not convert IR code: %s/%s", catalog_device.name, cmd_name)
                failed_count += 1
        
        # Copy RF codes (these might already have broadlink format or need different handling)
        for cmd_name, rf_code in catalog_device.rf_codes.items():
            # RF codes in catalog typically have frequency and data
            # For now, skip RF - would need protocol-specific handling
            pass
        
        await database.async_save()
        
        return web.json_response({
            "device": device.to_dict(),
            "commands_added": converted_count,
            "commands_failed": failed_count,
            "catalog_id": catalog_id,
        })


class OmniApiActivities(HomeAssistantView):
    """API for activities/macros."""
    
    url = "/api/omniremote/activities"
    name = "api:omniremote:activities"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
        self._runners: dict[str, ActivityRunner] = {}
    
    def _get_runner(self) -> ActivityRunner | None:
        database = _get_database(self.hass)
        if not database:
            return None
        
        entry_id = list(self.hass.data.get(DOMAIN, {}).keys())[0]
        if entry_id not in self._runners:
            self._runners[entry_id] = ActivityRunner(self.hass, database)
        
        return self._runners[entry_id]
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all activities."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        activities = getattr(database, 'activities', {})
        return web.json_response({
            "activities": [a.to_dict() for a in activities.values()]
        })
    
    async def post(self, request: web.Request) -> web.Response:
        """Create or run an activity."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        action = data.get("action", "create")
        
        if action == "run":
            activity_id = data.get("activity_id")
            activities = getattr(database, 'activities', {})
            
            if activity_id not in activities:
                return web.json_response({"error": "Activity not found"}, status=404)
            
            runner = self._get_runner()
            if not runner:
                return web.json_response({"error": "Runner not available"}, status=500)
            
            success = await runner.run_activity(activities[activity_id])
            return web.json_response({"success": success})
        
        elif action == "create":
            activity = Activity.from_dict(data.get("activity", {}))
            
            if not hasattr(database, 'activities'):
                database.activities = {}
            
            database.activities[activity.id] = activity
            await database.async_save()
            
            return web.json_response({"activity": activity.to_dict()})
        
        elif action == "create_from_template":
            template = data.get("template")
            params = data.get("params", {})
            
            from .activities import (
                create_watch_roku_activity,
                create_watch_projector_activity,
                create_gaming_activity,
            )
            
            templates = {
                "watch_roku": create_watch_roku_activity,
                "watch_projector": create_watch_projector_activity,
                "gaming": create_gaming_activity,
            }
            
            if template not in templates:
                return web.json_response({"error": "Unknown template"}, status=400)
            
            activity = templates[template](**params)
            
            if not hasattr(database, 'activities'):
                database.activities = {}
            
            database.activities[activity.id] = activity
            await database.async_save()
            
            return web.json_response({"activity": activity.to_dict()})
        
        return web.json_response({"error": "Unknown action"}, status=400)
    
    async def delete(self, request: web.Request) -> web.Response:
        """Delete an activity."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        activity_id = data.get("id")
        
        activities = getattr(database, 'activities', {})
        if activity_id in activities:
            del activities[activity_id]
            await database.async_save()
            return web.json_response({"success": True})
        
        return web.json_response({"error": "Activity not found"}, status=404)


class OmniApiNetworkDevices(HomeAssistantView):
    """API for network device discovery and control."""
    
    url = "/api/omniremote/network"
    name = "api:omniremote:network"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Discover network devices."""
        from .network_devices import discover_roku_devices
        
        device_type = request.query.get("type", "all")
        
        discovered = []
        
        if device_type in ("all", "roku"):
            roku_devices = await discover_roku_devices()
            for device in roku_devices:
                discovered.append(device.to_dict())
        
        return web.json_response({"devices": discovered})
    
    async def post(self, request: web.Request) -> web.Response:
        """Control a network device or get its apps/channels."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        action = data.get("action")
        host = data.get("host")
        device_type = data.get("device_type", "roku_ecp")
        
        from .network_devices import get_controller, RokuController
        
        controller = get_controller(device_type, host)
        if not controller:
            return web.json_response({"error": "Controller not available"}, status=400)
        
        if action == "get_apps":
            if isinstance(controller, RokuController):
                apps = await controller.get_apps()
                return web.json_response({"apps": apps})
        
        elif action == "get_channels":
            if isinstance(controller, RokuController):
                channels = await controller.get_tv_channels()
                return web.json_response({"channels": channels})
        
        elif action == "launch_app":
            app_id = data.get("app_id")
            if isinstance(controller, RokuController):
                success = await controller.launch_app(app_id)
                return web.json_response({"success": success})
        
        elif action == "tune_channel":
            channel = data.get("channel")
            if isinstance(controller, RokuController):
                success = await controller.tune_channel(channel)
                return web.json_response({"success": success})
        
        elif action == "send_command":
            command = data.get("command")
            success = await controller.send_command(command)
            return web.json_response({"success": success})
        
        return web.json_response({"error": "Unknown action"}, status=400)



# === Bluetooth Remote API ===
class OmniApiBluetoothRemotes(HomeAssistantView):
    """API for Bluetooth remote management."""
    
    url = "/api/omniremote/bluetooth_remotes"
    name = "api:omniremote:bluetooth_remotes"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request):
        """List all Bluetooth remotes."""
        data = self.hass.data.get(DOMAIN, {})
        entry_data = list(data.values())[0] if data else {}
        bt_manager = entry_data.get("bluetooth_manager")
        
        if not bt_manager:
            return self.json({"remotes": [], "error": "Bluetooth manager not initialized"})
        
        remotes = bt_manager.list_remotes()
        return self.json({
            "remotes": [r.to_dict() for r in remotes],
        })
    
    async def post(self, request):
        """Register or manage Bluetooth remotes."""
        data = await request.json()
        action = data.get("action")
        
        entry_data = list(self.hass.data.get(DOMAIN, {}).values())[0] if self.hass.data.get(DOMAIN) else {}
        bt_manager = entry_data.get("bluetooth_manager")
        
        if not bt_manager:
            return self.json({"success": False, "error": "Bluetooth manager not initialized"})
        
        if action == "register":
            remote = await bt_manager.async_register_remote(
                address=data["address"],
                name=data["name"],
                remote_type=data.get("remote_type", "Generic HID Remote"),
                area_id=data.get("area_id"),
                device_id=data.get("device_id"),
            )
            return self.json({"success": True, "remote": remote.to_dict()})
        
        elif action == "unregister":
            success = await bt_manager.async_unregister_remote(data["remote_id"])
            return self.json({"success": success})
        
        elif action == "update_mapping":
            success = await bt_manager.async_update_mapping(
                remote_id=data["remote_id"],
                hid_code=data["hid_code"],
                command=data["command"],
                device_id=data.get("device_id"),
                hold_command=data.get("hold_command"),
                double_tap_command=data.get("double_tap_command"),
            )
            return self.json({"success": success})
        
        elif action == "set_area":
            success = await bt_manager.async_set_remote_area(
                remote_id=data["remote_id"],
                area_id=data.get("area_id"),
            )
            return self.json({"success": success})
        
        elif action == "discover":
            # Start discovery
            discovered = []
            def on_discover(service_info):
                discovered.append({
                    "address": service_info.address,
                    "name": service_info.name,
                    "rssi": service_info.rssi,
                    "remote_type": bt_manager.identify_remote_type(service_info),
                })
            
            await bt_manager.async_start_discovery(on_discover, timeout=data.get("timeout", 15))
            await asyncio.sleep(data.get("timeout", 15))
            
            return self.json({"success": True, "discovered": discovered})
        
        elif action == "start_learning":
            learned_buttons = []
            def on_button(hid_code, button_name):
                learned_buttons.append({"hid_code": hid_code, "name": button_name})
            
            bt_manager.start_learning_mode(on_button)
            return self.json({"success": True, "message": "Learning mode started"})
        
        elif action == "stop_learning":
            bt_manager.stop_learning_mode()
            return self.json({"success": True})
        
        return self.json({"success": False, "error": "Unknown action"})


# === Area Remotes API ===
class OmniApiAreaRemotes(HomeAssistantView):
    """API for area-based remote management."""
    
    url = "/api/omniremote/area_remotes"
    name = "api:omniremote:area_remotes"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request):
        """Get areas and their remote configurations."""
        data = self.hass.data.get(DOMAIN, {})
        entry_data = list(data.values())[0] if data else {}
        area_manager = entry_data.get("area_manager")
        
        if not area_manager:
            return self.json({"areas": [], "error": "Area manager not initialized"})
        
        areas = area_manager.get_areas()
        return self.json({"areas": areas})
    
    async def post(self, request):
        """Manage area remotes."""
        data = await request.json()
        action = data.get("action")
        
        entry_data = list(self.hass.data.get(DOMAIN, {}).values())[0] if self.hass.data.get(DOMAIN) else {}
        area_manager = entry_data.get("area_manager")
        
        if not area_manager:
            return self.json({"success": False, "error": "Area manager not initialized"})
        
        if action == "register":
            remote = await area_manager.async_register_remote(
                area_id=data["area_id"],
                name=data["name"],
                remote_type=data.get("remote_type", "card"),
                card_template=data.get("card_template", "tv"),
                card_theme=data.get("card_theme", "default"),
                bluetooth_remote_id=data.get("bluetooth_remote_id"),
                is_primary=data.get("is_primary", False),
            )
            return self.json({"success": True, "remote": remote.to_dict()})
        
        elif action == "unregister":
            success = await area_manager.async_unregister_remote(data["remote_id"])
            return self.json({"success": success})
        
        elif action == "update":
            remote = await area_manager.async_update_remote(
                remote_id=data["remote_id"],
                **{k: v for k, v in data.items() if k not in ["action", "remote_id"]}
            )
            return self.json({"success": bool(remote), "remote": remote.to_dict() if remote else None})
        
        elif action == "set_device_mapping":
            success = await area_manager.async_set_device_mapping(
                area_id=data["area_id"],
                category=data["category"],
                device_id=data.get("device_id"),
            )
            return self.json({"success": success})
        
        elif action == "generate_card":
            config = area_manager.generate_card_config(data["remote_id"])
            return self.json({"success": True, "config": config})
        
        elif action == "generate_dashboard":
            yaml_content = area_manager.generate_dashboard_yaml(data.get("area_id"))
            return self.json({"success": True, "yaml": yaml_content})
        
        return self.json({"success": False, "error": "Unknown action"})


# === Remote Card Resources ===
class OmniRemoteCardResource(HomeAssistantView):
    """Serve the OmniRemote card JavaScript."""
    
    url = "/omniremote/omniremote-card.js"
    name = "omniremote:card:js"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request):
        """Serve the card JS file."""
        import os
        
        js_path = os.path.join(os.path.dirname(__file__), "www", "omniremote-card.js")
        
        if os.path.exists(js_path):
            with open(js_path, "r") as f:
                content = f.read()
            return web.Response(
                body=content,
                content_type="application/javascript",
                headers={"Cache-Control": "no-cache"},
            )
        
        return web.Response(status=404, text="Card not found")


class OmniApiTest(HomeAssistantView):
    """API for testing IR codes."""
    
    url = "/api/omniremote/test"
    name = "api:omniremote:test"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def post(self, request: web.Request) -> web.Response:
        """Test an IR code."""
        from .ir_encoder import encode_ir_to_broadlink
        from .catalog import get_profile
        
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        action = data.get("action", "test_command")
        
        _LOGGER.info("OmniApiTest.post: action=%s, data_keys=%s", action, list(data.keys()))
        
        if action == "test_command":
            # Test a specific command from a device
            device_id = data.get("device_id")
            command_name = data.get("command_name")
            blaster_id = data.get("blaster_id")
            
            if not device_id or not command_name:
                return web.json_response({"error": "device_id and command_name required"}, status=400)
            
            device = database.devices.get(device_id)
            if not device:
                return web.json_response({"error": f"Device not found: {device_id}"}, status=404)
            
            code = device.commands.get(command_name)
            if not code:
                return web.json_response({"error": f"Command not found: {command_name}"}, status=404)
            
            success = await database.async_send_code(code, blaster_id)
            
            return web.json_response({
                "success": success,
                "device": device.name,
                "command": command_name,
                "protocol": getattr(code, "protocol", None),
                "has_broadlink_code": bool(code.broadlink_code),
            })
        
        elif action == "test_catalog":
            # Test a catalog code directly (without adding to device)
            profile_id = data.get("profile_id")
            command_name = data.get("command_name")
            blaster_id = data.get("blaster_id")
            
            if not profile_id or not command_name:
                return web.json_response({"error": "profile_id and command_name required"}, status=400)
            
            result = await database.async_test_catalog_code(profile_id, command_name, blaster_id)
            return web.json_response(result)
        
        elif action == "list_profiles":
            # List all profiles for a brand/category
            brand = data.get("brand", "").lower()
            category = data.get("category", "")
            
            profiles = []
            for profile_id, profile in DEVICE_CATALOG.items():
                if brand and profile.brand.lower() != brand:
                    continue
                if category and profile.category.value != category:
                    continue
                profiles.append({
                    "id": profile_id,
                    "name": profile.name,
                    "brand": profile.brand,
                    "category": profile.category.value,
                    "commands": list(profile.ir_codes.keys())[:10],  # First 10 commands
                    "command_count": len(profile.ir_codes),
                })
            
            return web.json_response({"profiles": profiles})
        
        elif action == "get_profile_commands":
            # Get all commands from a profile
            profile_id = data.get("profile_id")
            
            profile = get_profile(profile_id)
            if not profile:
                return web.json_response({"error": f"Profile not found: {profile_id}"}, status=404)
            
            commands = []
            for cmd_name, ir_code in profile.ir_codes.items():
                broadlink_b64 = encode_ir_to_broadlink(ir_code)
                commands.append({
                    "name": cmd_name,
                    "protocol": ir_code.protocol.value if ir_code.protocol else None,
                    "address": ir_code.address,
                    "command": ir_code.command,
                    "can_encode": bool(broadlink_b64),
                })
            
            return web.json_response({
                "profile": profile_id,
                "name": profile.name,
                "brand": profile.brand,
                "commands": commands,
            })
        
        elif action == "switch_profile":
            # Switch a device to use a different catalog profile
            device_id = data.get("device_id")
            new_profile_id = data.get("profile_id")
            
            if not device_id or not new_profile_id:
                return web.json_response({"error": "device_id and profile_id required"}, status=400)
            
            device = database.devices.get(device_id)
            if not device:
                return web.json_response({"error": f"Device not found: {device_id}"}, status=404)
            
            profile = get_profile(new_profile_id)
            if not profile:
                return web.json_response({"error": f"Profile not found: {new_profile_id}"}, status=404)
            
            # Clear existing commands and reload from new profile
            device.commands.clear()
            device.catalog_id = new_profile_id
            
            converted_count = 0
            for cmd_name, ir_code in profile.ir_codes.items():
                broadlink_b64 = encode_ir_to_broadlink(ir_code)
                if broadlink_b64:
                    from .const import RemoteCode
                    device.commands[cmd_name] = RemoteCode(
                        source="catalog",
                        broadlink_code=broadlink_b64,
                        protocol=ir_code.protocol.value if ir_code.protocol else None,
                        address=ir_code.address,
                        command=ir_code.command,
                    )
                    converted_count += 1
            
            await database.async_save()
            
            return web.json_response({
                "success": True,
                "device": device.name,
                "new_profile": new_profile_id,
                "commands_loaded": converted_count,
            })
        
        elif action == "send_raw":
            # Send a raw base64-encoded Broadlink code
            broadlink_code = data.get("broadlink_code")
            blaster_id = data.get("blaster_id")
            
            if not broadlink_code:
                return web.json_response({"error": "broadlink_code required"}, status=400)
            
            from .ir_encoder import _log_debug
            import base64
            
            _log_debug({
                "action": "send_raw_request",
                "broadlink_bytes": len(base64.b64decode(broadlink_code)),
                "blaster_id": blaster_id,
            })
            
            # Find a blaster to use
            async with database._lock:
                if blaster_id and blaster_id in database.blasters:
                    blaster = database.blasters[blaster_id]
                    if blaster.mac not in database._blaster_connections:
                        await database.async_connect_blaster(blaster_id)
                    device = database._blaster_connections.get(blaster.mac)
                else:
                    result = database.get_any_blaster()
                    if result:
                        blaster, device = result
                    else:
                        _log_debug({
                            "action": "send_raw",
                            "status": "error",
                            "error": "No blaster available",
                        })
                        return web.json_response({"error": "No blaster available"}, status=400)
                
                if not device:
                    _log_debug({
                        "action": "send_raw",
                        "status": "error",
                        "error": "Blaster not connected",
                    })
                    return web.json_response({"error": "Blaster not connected"}, status=400)
                
                try:
                    code_bytes = base64.b64decode(broadlink_code)
                    _LOGGER.info("Sending raw IR: %d bytes via %s", len(code_bytes), blaster.name)
                    await self.hass.async_add_executor_job(device.send_data, code_bytes)
                    
                    _log_debug({
                        "action": "send_raw",
                        "status": "success",
                        "blaster_name": blaster.name,
                        "bytes_sent": len(code_bytes),
                    })
                    
                    return web.json_response({
                        "success": True,
                        "blaster": blaster.name,
                        "bytes_sent": len(code_bytes),
                    })
                except Exception as ex:
                    _log_debug({
                        "action": "send_raw",
                        "status": "exception",
                        "error": str(ex),
                    })
                    return web.json_response({"error": str(ex)}, status=500)
        
        elif action == "send_catalog_code":
            # Send a command from a catalog device
            catalog_id = data.get("catalog_id")
            command = data.get("command")
            blaster_id = data.get("blaster_id")
            
            _LOGGER.info("send_catalog_code: catalog_id=%s, command=%s, blaster_id=%s", 
                        catalog_id, command, blaster_id)
            
            if not catalog_id or not command:
                _LOGGER.error("send_catalog_code: missing catalog_id or command")
                return web.json_response({"error": "catalog_id and command required"}, status=400)
            
            try:
                profile = get_profile(catalog_id)
                if not profile:
                    _LOGGER.error("send_catalog_code: profile not found: %s", catalog_id)
                    return web.json_response({"error": f"Profile not found: {catalog_id}"}, status=404)
                
                ir_codes = getattr(profile, 'ir_codes', {})
                ir_code = ir_codes.get(command)
                if not ir_code:
                    _LOGGER.error("send_catalog_code: command not found: %s in %s (available: %s)", 
                                 command, catalog_id, list(ir_codes.keys())[:10])
                    return web.json_response({"error": f"Command not found: {command}"}, status=404)
                
                from .ir_encoder import _log_debug
                
                _log_debug({
                    "action": "send_catalog_code_request",
                    "catalog_id": catalog_id,
                    "command": command,
                    "protocol": str(getattr(ir_code, 'protocol', '?')),
                    "address": getattr(ir_code, 'address', '?'),
                    "command_hex": getattr(ir_code, 'command', '?'),
                    "blaster_id": blaster_id,
                })
                
                success = await database.async_send_catalog_code(ir_code, blaster_id)
                
                _LOGGER.info("send_catalog_code: success=%s", success)
                
                return web.json_response({
                    "success": success,
                    "catalog_id": catalog_id,
                    "command": command,
                    "protocol": str(getattr(ir_code, 'protocol', '')),
                })
            except Exception as ex:
                _LOGGER.exception("send_catalog_code error: %s", ex)
                return web.json_response({"error": str(ex)}, status=500)
        
        _LOGGER.warning("OmniApiTest: Unknown action '%s' (valid: test_command, test_catalog, list_profiles, get_profile_commands, switch_profile, send_raw, send_catalog_code)", action)
        return web.json_response({"error": f"Unknown action in /api/omniremote/test: {action}"}, status=400)


class OmniApiVersion(HomeAssistantView):
    """API for version info."""
    
    url = "/api/omniremote/version"
    name = "api:omniremote:version"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Return version info."""
        return web.json_response({
            "version": VERSION,
            "name": "OmniRemote Manager"
        })


class OmniApiDebug(HomeAssistantView):
    """API for IR command debugging and logging."""
    
    url = "/api/omniremote/debug"
    name = "api:omniremote:debug"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get debug log entries."""
        from .ir_encoder import get_debug_log
        
        return web.json_response({
            "log": get_debug_log(),
            "count": len(get_debug_log()),
        })
    
    async def post(self, request: web.Request) -> web.Response:
        """Debug actions."""
        from .ir_encoder import clear_debug_log, get_debug_log, _log_debug
        
        data = await request.json()
        action = data.get("action")
        
        if action == "clear":
            clear_debug_log()
            return web.json_response({"success": True, "message": "Debug log cleared"})
        
        elif action == "test_encode":
            # Test encoding a specific protocol/address/command
            from .ir_encoder import encode_ir_to_broadlink
            from .catalog import IRCode, IRProtocol
            
            protocol_str = data.get("protocol", "samsung32")
            address = data.get("address", "07")
            command = data.get("command", "02")
            
            # Map string to enum
            protocol_map = {
                "nec": IRProtocol.NEC,
                "nec_ext": IRProtocol.NEC_EXT,
                "samsung32": IRProtocol.SAMSUNG32,
                "sony": IRProtocol.SONY_SIRC,
                "rc5": IRProtocol.RC5,
                "rc6": IRProtocol.RC6,
                "panasonic": IRProtocol.PANASONIC,
                "jvc": IRProtocol.JVC,
            }
            
            protocol = protocol_map.get(protocol_str.lower())
            if not protocol:
                return web.json_response({"error": f"Unknown protocol: {protocol_str}"}, status=400)
            
            ir_code = IRCode(
                name="debug_test",
                protocol=protocol,
                address=address,
                command=command,
            )
            
            result = encode_ir_to_broadlink(ir_code)
            
            if result:
                import base64
                decoded = base64.b64decode(result)
                return web.json_response({
                    "success": True,
                    "protocol": protocol_str,
                    "address": address,
                    "command": command,
                    "broadlink_base64": result,
                    "broadlink_bytes": len(decoded),
                    "broadlink_hex": decoded.hex(),
                })
            else:
                return web.json_response({
                    "success": False,
                    "error": "Encoding failed - check debug log for details"
                })
        
        elif action == "test_send":
            # Test send a code
            database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Integration not configured"}, status=500)
            
            profile_id = data.get("profile_id")
            command_name = data.get("command")
            blaster_id = data.get("blaster_id")
            
            if not profile_id or not command_name:
                return web.json_response({"error": "profile_id and command required"}, status=400)
            
            from .catalog import get_profile
            
            profile = get_profile(profile_id)
            if not profile:
                return web.json_response({"error": f"Profile not found: {profile_id}"}, status=404)
            
            ir_code = profile.ir_codes.get(command_name)
            if not ir_code:
                return web.json_response({"error": f"Command not found: {command_name}"}, status=404)
            
            # Log the attempt
            _log_debug({
                "action": "test_send_request",
                "profile_id": profile_id,
                "command": command_name,
                "protocol": str(ir_code.protocol),
                "address": ir_code.address,
                "command_hex": ir_code.command,
            })
            
            success = await database.async_send_catalog_code(ir_code, blaster_id)
            
            return web.json_response({
                "success": success,
                "profile": profile_id,
                "command": command_name,
                "protocol": str(ir_code.protocol.value if hasattr(ir_code.protocol, 'value') else ir_code.protocol),
                "address": ir_code.address,
                "command_hex": ir_code.command,
            })
        
        elif action == "blaster_status":
            # Get blaster connection status
            database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Integration not configured"}, status=500)
            
            blasters_status = []
            for blaster in database.blasters.values():
                connected = blaster.mac in database._blaster_connections
                device = database._blaster_connections.get(blaster.mac)
                
                blasters_status.append({
                    "id": blaster.id,
                    "name": blaster.name,
                    "mac": blaster.mac,
                    "host": blaster.host,
                    "connected": connected,
                    "device_type": str(type(device).__name__) if device else None,
                })
            
            return web.json_response({
                "blasters": blasters_status,
                "total": len(blasters_status),
                "connected": sum(1 for b in blasters_status if b["connected"]),
            })
        
        return web.json_response({"error": "Unknown action"}, status=400)


class OmniIconView(HomeAssistantView):
    """Serve the integration icon."""
    
    url = "/api/omniremote/icon.png"
    name = "api:omniremote:icon"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Return the icon PNG."""
        icon_path = Path(__file__).parent / "icon.png"
        
        if icon_path.exists():
            content = await self.hass.async_add_executor_job(icon_path.read_bytes)
            return web.Response(
                body=content,
                content_type="image/png",
                headers={"Cache-Control": "public, max-age=86400"},
            )
        
        return web.Response(status=404, text="Icon not found")


class OmniLogoView(HomeAssistantView):
    """Serve the integration logo."""
    
    url = "/api/omniremote/logo.png"
    name = "api:omniremote:logo"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Return the logo PNG."""
        logo_path = Path(__file__).parent / "logo.png"
        
        if not logo_path.exists():
            # Fall back to icon
            logo_path = Path(__file__).parent / "icon.png"
        
        if logo_path.exists():
            content = await self.hass.async_add_executor_job(logo_path.read_bytes)
            return web.Response(
                body=content,
                content_type="image/png",
                headers={"Cache-Control": "public, max-age=86400"},
            )
        
        return web.Response(status=404, text="Logo not found")


# =============================================================================
# Physical Remotes API
# =============================================================================

class OmniApiPhysicalRemotes(HomeAssistantView):
    """API for managing physical remotes (Zigbee, RF, BT, USB)."""
    
    url = "/api/omniremote/physical_remotes"
    name = "api:omniremote:physical_remotes"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all physical remotes."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Integration not configured"}, status=500)
        
        remotes = []
        for remote in database.physical_remotes.values():
            remote_dict = remote.to_dict()
            # Add room name for display
            if remote.room_id and remote.room_id in database.rooms:
                remote_dict["room_name"] = database.rooms[remote.room_id].name
            else:
                remote_dict["room_name"] = None
            remotes.append(remote_dict)
        
        return web.json_response({"remotes": remotes})
    
    async def post(self, request: web.Request) -> web.Response:
        """Add or update a physical remote."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Integration not configured"}, status=500)
        data = await request.json()
        
        action = data.get("action", "add")
        
        if action == "add":
            from .physical_remotes import PhysicalRemote, RemoteType, ButtonMapping, ActionType
            
            remote_id = data.get("id") or str(uuid.uuid4())[:8]
            
            remote = PhysicalRemote(
                id=remote_id,
                name=data.get("name", "New Remote"),
                remote_type=RemoteType(data.get("remote_type", "zigbee")),
                room_id=data.get("room_id"),
                bridge_id=data.get("bridge_id"),
                zigbee_ieee=data.get("zigbee_ieee"),
                rf_code_prefix=data.get("rf_code_prefix"),
                bt_mac=data.get("bt_mac"),
                usb_device_name=data.get("usb_device_name"),
                profile=data.get("profile"),
            )
            
            # Apply profile defaults if specified
            if remote.profile:
                from .physical_remotes import REMOTE_PROFILES
                profile_data = REMOTE_PROFILES.get(remote.profile, {})
                for btn_id, mapping_data in profile_data.get("default_mappings", {}).items():
                    remote.button_mappings[btn_id] = ButtonMapping(
                        button_id=btn_id,
                        action_type=ActionType(mapping_data.get("action_type", "scene")),
                        action_target=mapping_data.get("action_target", ""),
                        action_data=mapping_data.get("action_data", {}),
                    )
            
            database.physical_remotes[remote.id] = remote
            await database.async_save()
            
            return web.json_response({
                "success": True,
                "remote": remote.to_dict()
            })
        
        elif action == "update":
            remote_id = data.get("id")
            if not remote_id or remote_id not in database.physical_remotes:
                return web.json_response({"error": "Remote not found"}, status=404)
            
            remote = database.physical_remotes[remote_id]
            
            # Update fields
            if "name" in data:
                remote.name = data["name"]
            if "room_id" in data:
                remote.room_id = data["room_id"]
            if "bridge_id" in data:
                remote.bridge_id = data["bridge_id"]
            if "zigbee_ieee" in data:
                remote.zigbee_ieee = data["zigbee_ieee"]
            if "rf_code_prefix" in data:
                remote.rf_code_prefix = data["rf_code_prefix"]
            if "bt_mac" in data:
                remote.bt_mac = data["bt_mac"]
            if "usb_device_name" in data:
                remote.usb_device_name = data["usb_device_name"]
            
            await database.async_save()
            
            return web.json_response({
                "success": True,
                "remote": remote.to_dict()
            })
        
        elif action == "delete":
            remote_id = data.get("id")
            if remote_id and remote_id in database.physical_remotes:
                del database.physical_remotes[remote_id]
                await database.async_save()
                return web.json_response({"success": True})
            return web.json_response({"error": "Remote not found"}, status=404)
        
        elif action == "map_button":
            # Map a button to an action
            remote_id = data.get("remote_id")
            if not remote_id or remote_id not in database.physical_remotes:
                return web.json_response({"error": "Remote not found"}, status=404)
            
            remote = database.physical_remotes[remote_id]
            
            from .physical_remotes import ButtonMapping, ActionType
            
            button_id = data.get("button_id")
            mapping = ButtonMapping(
                button_id=button_id,
                action_type=ActionType(data.get("action_type", "scene")),
                action_target=data.get("action_target", ""),
                action_data=data.get("action_data", {}),
                long_press_action=data.get("long_press_action"),
                double_press_action=data.get("double_press_action"),
            )
            
            remote.button_mappings[button_id] = mapping
            await database.async_save()
            
            return web.json_response({
                "success": True,
                "mapping": mapping.to_dict()
            })
        
        elif action == "discover_zigbee":
            # Discover Zigbee remotes from ZHA/deCONZ
            from .physical_remotes import discover_zigbee_remotes
            
            try:
                discovered = await discover_zigbee_remotes(self.hass)
                return web.json_response({
                    "success": True,
                    "discovered": discovered
                })
            except Exception as ex:
                return web.json_response({
                    "error": str(ex)
                }, status=500)
        
        return web.json_response({"error": "Unknown action"}, status=400)


class OmniApiRemoteBridges(HomeAssistantView):
    """API for managing remote bridges (Pi Zero, ESP32, Sonoff, etc.)."""
    
    url = "/api/omniremote/remote_bridges"
    name = "api:omniremote:remote_bridges"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all remote bridges."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Integration not configured"}, status=500)
        
        bridges = []
        for bridge in database.remote_bridges.values():
            bridge_dict = bridge.to_dict()
            # Add room name for display
            if bridge.room_id and bridge.room_id in database.rooms:
                bridge_dict["room_name"] = database.rooms[bridge.room_id].name
            else:
                bridge_dict["room_name"] = None
            bridges.append(bridge_dict)
        
        return web.json_response({"bridges": bridges})
    
    async def post(self, request: web.Request) -> web.Response:
        """Add or update a remote bridge."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Integration not configured"}, status=500)
        data = await request.json()
        
        action = data.get("action", "add")
        
        if action == "add":
            from .physical_remotes import RemoteBridge, BridgeType
            
            bridge_id = data.get("id") or str(uuid.uuid4())[:8]
            
            bridge = RemoteBridge(
                id=bridge_id,
                name=data.get("name", "New Bridge"),
                bridge_type=BridgeType(data.get("bridge_type", "usb_bridge")),
                room_id=data.get("room_id"),
                host=data.get("host"),
                port=data.get("port"),
                mqtt_topic=data.get("mqtt_topic"),
                device_id=data.get("device_id"),
            )
            
            database.remote_bridges[bridge.id] = bridge
            await database.async_save()
            
            return web.json_response({
                "success": True,
                "bridge": bridge.to_dict()
            })
        
        elif action == "update":
            bridge_id = data.get("id")
            if not bridge_id or bridge_id not in database.remote_bridges:
                return web.json_response({"error": "Bridge not found"}, status=404)
            
            bridge = database.remote_bridges[bridge_id]
            
            # Update fields
            if "name" in data:
                bridge.name = data["name"]
            if "room_id" in data:
                bridge.room_id = data["room_id"]
            if "host" in data:
                bridge.host = data["host"]
            if "port" in data:
                bridge.port = data["port"]
            if "mqtt_topic" in data:
                bridge.mqtt_topic = data["mqtt_topic"]
            
            await database.async_save()
            
            return web.json_response({
                "success": True,
                "bridge": bridge.to_dict()
            })
        
        elif action == "delete":
            bridge_id = data.get("id")
            if bridge_id and bridge_id in database.remote_bridges:
                del database.remote_bridges[bridge_id]
                await database.async_save()
                return web.json_response({"success": True})
            return web.json_response({"error": "Bridge not found"}, status=404)
        
        elif action == "discover":
            # Discover MQTT bridges that have registered
            discovered = []
            
            # Check for auto-discovered bridges via MQTT
            if "mqtt" in self.hass.config.components:
                # Look for retained status messages
                # This would need MQTT subscription during init
                pass
            
            return web.json_response({
                "success": True,
                "discovered": discovered
            })
        
        return web.json_response({"error": "Unknown action"}, status=400)


class OmniApiRemoteProfiles(HomeAssistantView):
    """API for remote profiles (custom and pre-defined button layouts)."""
    
    url = "/api/omniremote/remote_profiles"
    name = "api:omniremote:remote_profiles"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all remote profiles (built-in + custom)."""
        from .physical_remotes import REMOTE_PROFILES
        from .const import RemoteProfile
        
        # Built-in profiles from physical_remotes
        builtin_profiles = []
        for profile_id, profile_data in REMOTE_PROFILES.items():
            builtin_profiles.append({
                "id": profile_id,
                "name": profile_data.get("name", profile_id),
                "type": profile_data.get("type", "unknown").value if hasattr(profile_data.get("type"), "value") else str(profile_data.get("type", "unknown")),
                "buttons": profile_data.get("buttons", []),
                "default_mappings": profile_data.get("default_mappings", {}),
                "builtin": True,
            })
        
        # Custom profiles from database
        database = _get_database(self.hass)
        custom_profiles = []
        if database:
            for profile in database.remote_profiles.values():
                profile_dict = profile.to_dict()
                profile_dict["builtin"] = False
                custom_profiles.append(profile_dict)
        
        return web.json_response({
            "profiles": custom_profiles,
            "builtin_profiles": builtin_profiles,
            "templates": self._get_templates(),
        })
    
    def _get_templates(self):
        """Return pre-defined templates for creating new remotes."""
        return [
            {
                "id": "tv_basic",
                "name": "Basic TV Remote",
                "icon": "mdi:television",
                "device_type": "tv",
                "rows": 10,
                "cols": 4,
                "buttons": [
                    {"id": "power", "label": "Power", "icon": "mdi:power", "row": 0, "col": 1, "col_span": 2, "button_type": "power", "color": "#f44336"},
                    {"id": "vol_up", "label": "Vol +", "icon": "mdi:volume-plus", "row": 2, "col": 0, "button_type": "volume_up"},
                    {"id": "vol_down", "label": "Vol -", "icon": "mdi:volume-minus", "row": 3, "col": 0, "button_type": "volume_down"},
                    {"id": "mute", "label": "Mute", "icon": "mdi:volume-mute", "row": 4, "col": 0, "button_type": "mute"},
                    {"id": "ch_up", "label": "CH +", "icon": "mdi:chevron-up", "row": 2, "col": 3, "button_type": "channel_up"},
                    {"id": "ch_down", "label": "CH -", "icon": "mdi:chevron-down", "row": 3, "col": 3, "button_type": "channel_down"},
                    {"id": "input", "label": "Input", "icon": "mdi:import", "row": 4, "col": 3, "button_type": "input"},
                    {"id": "up", "label": "Up", "icon": "mdi:chevron-up", "row": 5, "col": 1, "col_span": 2, "button_type": "up", "shape": "rectangle"},
                    {"id": "left", "label": "Left", "icon": "mdi:chevron-left", "row": 6, "col": 0, "button_type": "left"},
                    {"id": "ok", "label": "OK", "icon": "mdi:check-circle", "row": 6, "col": 1, "col_span": 2, "button_type": "ok", "color": "#4caf50"},
                    {"id": "right", "label": "Right", "icon": "mdi:chevron-right", "row": 6, "col": 3, "button_type": "right"},
                    {"id": "down", "label": "Down", "icon": "mdi:chevron-down", "row": 7, "col": 1, "col_span": 2, "button_type": "down", "shape": "rectangle"},
                    {"id": "back", "label": "Back", "icon": "mdi:arrow-left", "row": 8, "col": 0, "button_type": "back"},
                    {"id": "home", "label": "Home", "icon": "mdi:home", "row": 8, "col": 1, "col_span": 2, "button_type": "home"},
                    {"id": "menu", "label": "Menu", "icon": "mdi:menu", "row": 8, "col": 3, "button_type": "menu"},
                ]
            },
            {
                "id": "receiver_basic",
                "name": "Basic Receiver Remote",
                "icon": "mdi:audio-video",
                "device_type": "receiver",
                "rows": 10,
                "cols": 4,
                "buttons": [
                    {"id": "power", "label": "Power", "icon": "mdi:power", "row": 0, "col": 1, "col_span": 2, "button_type": "power", "color": "#f44336"},
                    {"id": "vol_up", "label": "Vol +", "icon": "mdi:volume-plus", "row": 2, "col": 0, "col_span": 2, "button_type": "volume_up"},
                    {"id": "vol_down", "label": "Vol -", "icon": "mdi:volume-minus", "row": 3, "col": 0, "col_span": 2, "button_type": "volume_down"},
                    {"id": "mute", "label": "Mute", "icon": "mdi:volume-mute", "row": 4, "col": 0, "col_span": 2, "button_type": "mute"},
                    {"id": "hdmi1", "label": "HDMI 1", "icon": "mdi:hdmi-port", "row": 2, "col": 2, "col_span": 2},
                    {"id": "hdmi2", "label": "HDMI 2", "icon": "mdi:hdmi-port", "row": 3, "col": 2, "col_span": 2},
                    {"id": "hdmi3", "label": "HDMI 3", "icon": "mdi:hdmi-port", "row": 4, "col": 2, "col_span": 2},
                    {"id": "tv", "label": "TV", "icon": "mdi:television", "row": 6, "col": 0},
                    {"id": "game", "label": "Game", "icon": "mdi:gamepad-variant", "row": 6, "col": 1},
                    {"id": "music", "label": "Music", "icon": "mdi:music", "row": 6, "col": 2},
                    {"id": "movie", "label": "Movie", "icon": "mdi:movie", "row": 6, "col": 3},
                ]
            },
            {
                "id": "streaming_basic",
                "name": "Streaming Device Remote",
                "icon": "mdi:play-network",
                "device_type": "streaming",
                "rows": 8,
                "cols": 4,
                "buttons": [
                    {"id": "power", "label": "Power", "icon": "mdi:power", "row": 0, "col": 0, "button_type": "power", "color": "#f44336"},
                    {"id": "home", "label": "Home", "icon": "mdi:home", "row": 0, "col": 3, "button_type": "home"},
                    {"id": "up", "label": "Up", "icon": "mdi:chevron-up", "row": 2, "col": 1, "col_span": 2, "button_type": "up"},
                    {"id": "left", "label": "Left", "icon": "mdi:chevron-left", "row": 3, "col": 0, "button_type": "left"},
                    {"id": "ok", "label": "OK", "icon": "mdi:check-circle", "row": 3, "col": 1, "col_span": 2, "button_type": "ok", "color": "#4caf50"},
                    {"id": "right", "label": "Right", "icon": "mdi:chevron-right", "row": 3, "col": 3, "button_type": "right"},
                    {"id": "down", "label": "Down", "icon": "mdi:chevron-down", "row": 4, "col": 1, "col_span": 2, "button_type": "down"},
                    {"id": "back", "label": "Back", "icon": "mdi:arrow-left", "row": 5, "col": 0, "button_type": "back"},
                    {"id": "play", "label": "Play", "icon": "mdi:play", "row": 5, "col": 1, "col_span": 2, "button_type": "play"},
                    {"id": "menu", "label": "Menu", "icon": "mdi:menu", "row": 5, "col": 3, "button_type": "menu"},
                    {"id": "rewind", "label": "Rewind", "icon": "mdi:rewind", "row": 6, "col": 0, "button_type": "rewind"},
                    {"id": "pause", "label": "Pause", "icon": "mdi:pause", "row": 6, "col": 1, "col_span": 2, "button_type": "pause"},
                    {"id": "forward", "label": "Forward", "icon": "mdi:fast-forward", "row": 6, "col": 3, "button_type": "forward"},
                    {"id": "vol_up", "label": "Vol +", "icon": "mdi:volume-plus", "row": 7, "col": 0, "button_type": "volume_up"},
                    {"id": "mute", "label": "Mute", "icon": "mdi:volume-mute", "row": 7, "col": 1, "col_span": 2, "button_type": "mute"},
                    {"id": "vol_down", "label": "Vol -", "icon": "mdi:volume-minus", "row": 7, "col": 3, "button_type": "volume_down"},
                ]
            },
            {
                "id": "soundbar_basic",
                "name": "Soundbar Remote",
                "icon": "mdi:speaker",
                "device_type": "soundbar",
                "rows": 6,
                "cols": 4,
                "buttons": [
                    {"id": "power", "label": "Power", "icon": "mdi:power", "row": 0, "col": 1, "col_span": 2, "button_type": "power", "color": "#f44336"},
                    {"id": "vol_up", "label": "Vol +", "icon": "mdi:volume-plus", "row": 2, "col": 0, "col_span": 2, "button_type": "volume_up"},
                    {"id": "vol_down", "label": "Vol -", "icon": "mdi:volume-minus", "row": 3, "col": 0, "col_span": 2, "button_type": "volume_down"},
                    {"id": "mute", "label": "Mute", "icon": "mdi:volume-mute", "row": 2, "col": 2, "col_span": 2, "button_type": "mute"},
                    {"id": "input", "label": "Input", "icon": "mdi:import", "row": 3, "col": 2, "col_span": 2, "button_type": "input"},
                    {"id": "bass_up", "label": "Bass +", "icon": "mdi:music-note-plus", "row": 5, "col": 0},
                    {"id": "bass_down", "label": "Bass -", "icon": "mdi:music-note-minus", "row": 5, "col": 1},
                    {"id": "treble_up", "label": "Treble +", "icon": "mdi:equalizer", "row": 5, "col": 2},
                    {"id": "treble_down", "label": "Treble -", "icon": "mdi:equalizer", "row": 5, "col": 3},
                ]
            },
            {
                "id": "universal",
                "name": "Universal (Blank)",
                "icon": "mdi:remote",
                "device_type": "universal",
                "rows": 8,
                "cols": 4,
                "buttons": []
            },
        ]
    
    async def post(self, request: web.Request) -> web.Response:
        """Create, update, or delete a custom remote profile."""
        import logging
        from datetime import datetime
        from .const import RemoteProfile, RemoteButton
        
        _LOGGER = logging.getLogger(__name__)
        
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Integration not configured"}, status=500)
        
        try:
            data = await request.json()
            action = data.get("action", "create")
            
            # Handle nested profile object (from JS builder)
            profile_data = data.get("profile", data)
            
            if action in ("create", "update", "save"):
                profile_id = profile_data.get("id") or data.get("profile_id") or str(uuid.uuid4())[:8]
                
                # Parse buttons
                buttons = []
                for btn_data in profile_data.get("buttons", []):
                    buttons.append(RemoteButton.from_dict(btn_data))
                
                profile = RemoteProfile(
                    id=profile_id,
                    name=profile_data.get("name", "Custom Remote"),
                    description=profile_data.get("description", ""),
                    icon=profile_data.get("icon", "mdi:remote"),
                    rows=profile_data.get("rows", 8),
                    cols=profile_data.get("cols", 4),
                    device_type=profile_data.get("device_type", "universal"),
                    default_device_id=profile_data.get("default_device_id"),
                    buttons=buttons,
                    template=profile_data.get("template"),
                    created_at=profile_data.get("created_at") or datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                )
                
                database.remote_profiles[profile_id] = profile
                await database.async_save()
                
                _LOGGER.info("Saved remote profile: %s", profile.name)
                return web.json_response({"profile": profile.to_dict(), "success": True})
            
            elif action == "delete":
                profile_id = data.get("profile_id") or data.get("id")
                if profile_id and profile_id in database.remote_profiles:
                    del database.remote_profiles[profile_id]
                    await database.async_save()
                    return web.json_response({"success": True})
                return web.json_response({"error": "Profile not found"}, status=404)
            
            elif action == "duplicate":
                source_id = data.get("source_id")
                if source_id and source_id in database.remote_profiles:
                    source = database.remote_profiles[source_id]
                    new_id = str(uuid.uuid4())[:8]
                    new_profile = RemoteProfile(
                        id=new_id,
                        name=f"{source.name} (Copy)",
                        description=source.description,
                        icon=source.icon,
                        rows=source.rows,
                        cols=source.cols,
                        device_type=source.device_type,
                        default_device_id=source.default_device_id,
                        buttons=[RemoteButton.from_dict(b.to_dict()) for b in source.buttons],
                        template=source.template,
                        created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat(),
                    )
                    database.remote_profiles[new_id] = new_profile
                    await database.async_save()
                    return web.json_response({"profile": new_profile.to_dict(), "success": True})
                return web.json_response({"error": "Source profile not found"}, status=404)
            
            else:
                return web.json_response({"error": f"Unknown action: {action}"}, status=400)
                
        except Exception as ex:
            _LOGGER.error("Remote profile error: %s", ex)
            return web.json_response({"error": str(ex)}, status=500)


class OmniApiFlipperZero(HomeAssistantView):
    """API for Flipper Zero management."""
    
    url = "/api/omniremote/flipper"
    name = "api:omniremote:flipper"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._manager = None
    
    def _get_manager(self):
        """Get or create Flipper Zero manager."""
        if self._manager is None:
            from .flipper_zero import FlipperZeroManager
            self._manager = FlipperZeroManager(self.hass)
        return self._manager
    
    async def get(self, request: web.Request) -> web.Response:
        """Get Flipper Zero devices and status."""
        manager = self._get_manager()
        return web.json_response({
            "devices": manager.list_devices(),
        })
    
    async def post(self, request: web.Request) -> web.Response:
        """Manage Flipper Zero devices."""
        manager = self._get_manager()
        data = await request.json()
        action = data.get("action", "")
        
        if action == "discover":
            # Discover Flipper devices
            connection_type = data.get("connection_type", "all")
            
            if connection_type == "usb":
                devices = await manager.async_discover_usb()
            elif connection_type == "bluetooth":
                devices = await manager.async_discover_bluetooth()
            else:
                devices = await manager.async_discover_all()
            
            return web.json_response({
                "success": True,
                "devices": devices,
            })
        
        elif action == "add":
            # Add a discovered Flipper device
            device_id = data.get("device_id")
            name = data.get("name", "Flipper Zero")
            connection_type = data.get("connection_type")
            port = data.get("port")
            
            if not all([device_id, connection_type, port]):
                return web.json_response({
                    "error": "device_id, connection_type, and port required"
                }, status=400)
            
            device = manager.add_device(device_id, name, connection_type, port)
            
            return web.json_response({
                "success": True,
                "device": device.to_dict(),
            })
        
        elif action == "remove":
            device_id = data.get("device_id")
            if device_id:
                await manager.async_disconnect(device_id)
                manager.remove_device(device_id)
                return web.json_response({"success": True})
            return web.json_response({"error": "device_id required"}, status=400)
        
        elif action == "connect":
            device_id = data.get("device_id")
            if not device_id:
                return web.json_response({"error": "device_id required"}, status=400)
            
            success = await manager.async_connect(device_id)
            device = manager.get_device(device_id)
            
            return web.json_response({
                "success": success,
                "device": device.to_dict() if device else None,
            })
        
        elif action == "disconnect":
            device_id = data.get("device_id")
            if device_id:
                await manager.async_disconnect(device_id)
                return web.json_response({"success": True})
            return web.json_response({"error": "device_id required"}, status=400)
        
        elif action == "send_ir":
            # Send IR command via Flipper
            device_id = data.get("device_id")
            protocol = data.get("protocol")
            address = data.get("address")
            command = data.get("command")
            
            if not all([device_id, protocol, address, command]):
                return web.json_response({
                    "error": "device_id, protocol, address, and command required"
                }, status=400)
            
            success = await manager.async_send_ir(
                device_id, protocol, address, command
            )
            
            return web.json_response({"success": success})
        
        elif action == "list_files":
            # List IR files on Flipper SD card
            device_id = data.get("device_id")
            if not device_id:
                return web.json_response({"error": "device_id required"}, status=400)
            
            files = await manager.async_list_ir_files(device_id)
            return web.json_response({
                "success": True,
                "files": files,
            })
        
        elif action == "read_file":
            # Read IR file from Flipper
            device_id = data.get("device_id")
            filename = data.get("filename")
            
            if not device_id or not filename:
                return web.json_response({
                    "error": "device_id and filename required"
                }, status=400)
            
            content = await manager.async_read_ir_file(device_id, filename)
            
            # Parse the file content
            from .flipper_parser import parse_flipper_ir
            codes = parse_flipper_ir(content)
            
            return web.json_response({
                "success": True,
                "filename": filename,
                "content": content,
                "codes": codes,
            })
        
        elif action == "start_learning":
            # Start IR learning mode
            device_id = data.get("device_id")
            if not device_id:
                return web.json_response({"error": "device_id required"}, status=400)
            
            # Learning results will be stored temporarily
            learned_codes = []
            
            def on_code_received(code):
                learned_codes.append(code)
            
            success = await manager.async_start_learning(
                device_id, 
                on_code_received,
                timeout=data.get("timeout", 30.0)
            )
            
            return web.json_response({
                "success": success,
                "message": "Learning started. Point remote at Flipper and press buttons.",
            })
        
        elif action == "stop_learning":
            await manager.async_stop_learning()
            return web.json_response({"success": True})
        
        return web.json_response({"error": f"Unknown action: {action}"}, status=400)
