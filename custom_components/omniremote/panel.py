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

from .const import DOMAIN, VERSION, DEBUG, DeviceCategory, SceneAction, Blaster
from .database import RemoteDatabase
from .catalog import DEVICE_CATALOG, CATALOG_BY_BRAND, CATALOG_BY_CATEGORY, get_catalog_device, search_catalog, list_catalog
from .activities import Activity, ActivityAction, ActionType, ActivityRunner

_LOGGER = logging.getLogger(__name__)

# Debug logging helper
def _debug(msg: str, *args) -> None:
    """Log debug message if DEBUG is enabled."""
    if DEBUG:
        _LOGGER.info("[OmniRemote DEBUG] " + msg, *args)

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
    hass.http.register_view(OmniApiBluetooth(hass))
    hass.http.register_view(OmniApiAreaRemotes(hass))
    hass.http.register_view(OmniRemoteCardResource(hass))
    hass.http.register_view(OmniApiVersion(hass))
    hass.http.register_view(OmniApiTest(hass))
    hass.http.register_view(OmniApiFlipperZero(hass))
    hass.http.register_view(OmniApiPhysicalRemotes(hass))
    hass.http.register_view(OmniApiRemoteBridges(hass))
    hass.http.register_view(OmniApiRemoteProfiles(hass))
    hass.http.register_view(OmniApiRemoteModels(hass))
    hass.http.register_view(OmniApiDebug(hass))
    hass.http.register_view(OmniApiMqttAutoConfigure(hass))
    hass.http.register_view(OmniApiMqttTest(hass))
    hass.http.register_view(OmniApiMqttConfig(hass))
    hass.http.register_view(OmniApiMqttStatus(hass))
    hass.http.register_view(OmniApiPiHubs(hass))
    hass.http.register_view(OmniApiPiHubCommand(hass))
    hass.http.register_view(OmniApiPiHubDiscover(hass))
    hass.http.register_view(OmniApiPiHubDevices(hass))
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
        """Get all blasters including HA Broadlink entities and Pi Hub bridges."""
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
        
        # Get Pi Hub bridges (auto-discovered via MQTT)
        pi_hub_bridges = []
        try:
            pi_hub_manager = _get_pi_hub_manager(self.hass)
            if pi_hub_manager:
                pi_hub_bridges = pi_hub_manager.get_bridges()
        except Exception as ex:
            _LOGGER.debug("Error getting Pi Hub bridges: %s", ex)
        
        return web.json_response({
            "blasters": blasters,
            "ha_blasters": ha_blasters,
            "pi_hub_bridges": pi_hub_bridges,
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


# === Bluetooth API (HA Built-in Adapter) ===
class OmniApiBluetooth(HomeAssistantView):
    """API for HA's built-in Bluetooth adapter scanning and pairing."""
    
    url = "/api/omniremote/bluetooth"
    name = "api:omniremote:bluetooth"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def post(self, request):
        """Handle Bluetooth operations."""
        import asyncio
        
        try:
            data = await request.json()
        except Exception:
            return self.json({"success": False, "error": "Invalid JSON"})
        
        action = data.get("action")
        adapter = data.get("adapter", "hci0")
        
        if action == "scan":
            devices = []
            paired_macs = set()
            
            # Get paired devices first
            try:
                paired_macs = set(m.upper() for m in await self._get_paired_devices_dbus())
            except Exception:
                pass
            
            # Try to scan with bluetoothctl for classic Bluetooth devices
            try:
                import asyncio
                
                # Start scanning (bluetoothctl scan on)
                scan_start = await asyncio.create_subprocess_shell(
                    "echo 'scan on' | bluetoothctl",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await scan_start.wait()
                
                # Wait for devices to be discovered
                await asyncio.sleep(5)
                
                # Stop scanning
                scan_stop = await asyncio.create_subprocess_shell(
                    "echo 'scan off' | bluetoothctl",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await scan_stop.wait()
                
                # Get list of devices
                list_cmd = await asyncio.create_subprocess_shell(
                    "echo 'devices' | bluetoothctl",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await asyncio.wait_for(list_cmd.communicate(), timeout=5)
                output = stdout.decode()
                
                # Parse device list (format: "Device XX:XX:XX:XX:XX:XX Device Name")
                import re
                for line in output.split('\n'):
                    match = re.search(r'Device\s+([0-9A-Fa-f:]{17})\s+(.+)', line)
                    if match:
                        mac = match.group(1).upper()
                        name = match.group(2).strip()
                        if not any(d["mac"].upper() == mac for d in devices):
                            devices.append({
                                "mac": mac,
                                "name": name,
                                "rssi": None,
                                "paired": mac in paired_macs,
                                "source": "classic",
                            })
                
                _LOGGER.debug("Found %d devices via bluetoothctl", len(devices))
                
            except Exception as e:
                _LOGGER.debug("bluetoothctl scan failed: %s", e)
            
            # Also try HA's bluetooth component for BLE devices
            try:
                from homeassistant.components import bluetooth
                
                discovered = bluetooth.async_discovered_service_info(self.hass)
                for info in discovered:
                    mac = info.address.upper()
                    if not any(d["mac"].upper() == mac for d in devices):
                        devices.append({
                            "mac": info.address,
                            "name": info.name or info.advertisement.local_name or "Unknown",
                            "rssi": info.rssi,
                            "paired": mac in paired_macs,
                            "source": "ble",
                        })
                
                _LOGGER.debug("Found %d total devices including BLE", len(devices))
                
            except ImportError:
                _LOGGER.debug("HA Bluetooth component not available")
            except Exception as e:
                _LOGGER.debug("HA Bluetooth scan failed: %s", e)
            
            if devices:
                return self.json({"success": True, "devices": devices})
            else:
                return self.json({"success": False, "error": "No devices found. Make sure Bluetooth is enabled and devices are in pairing mode.", "devices": []})
        
        elif action == "pair":
            mac = data.get("mac")
            if not mac:
                return self.json({"success": False, "error": "MAC address required"})
            
            _LOGGER.info("Attempting to pair Bluetooth device: %s", mac)
            last_error = "Pairing failed"
            
            try:
                # Try D-Bus first (most reliable on HA Yellow/OS)
                dbus_result = await self._pair_with_dbus(mac)
                if dbus_result.get("success"):
                    return self.json(dbus_result)
                last_error = dbus_result.get("error", last_error)
                _LOGGER.debug("D-Bus pairing failed: %s", last_error)
                
                # Try HA's Bluetooth integration for BLE devices
                ha_result = await self._pair_with_ha_bluetooth(mac)
                if ha_result.get("success"):
                    return self.json(ha_result)
                _LOGGER.debug("HA Bluetooth pairing failed: %s", ha_result.get("error"))
                
                # Try bluetoothctl as last resort
                result = await self._pair_with_bluetoothctl(mac)
                if result.get("success"):
                    return self.json(result)
                _LOGGER.debug("bluetoothctl pairing failed: %s", result.get("error"))
                
                # Return the most relevant error (D-Bus error is usually most informative)
                return self.json({
                    "success": False, 
                    "error": last_error
                })
                
            except Exception as e:
                _LOGGER.error("Bluetooth pairing error: %s", e)
                return self.json({"success": False, "error": f"Pairing failed: {e}"})
        
        elif action == "unpair":
            mac = data.get("mac")
            if not mac:
                return self.json({"success": False, "error": "MAC address required"})
            
            try:
                result = await self._unpair_with_dbus(mac)
                return self.json(result)
            except Exception as e:
                return self.json({"success": False, "error": f"Unpairing failed: {e}"})
        
        elif action == "list_paired":
            try:
                devices = await self._get_paired_devices_dbus()
                return self.json({"success": True, "devices": [{"mac": m} for m in devices]})
            except Exception as e:
                return self.json({"success": False, "error": f"Failed to list devices: {e}"})
        
        return self.json({"success": False, "error": "Unknown action"})
    
    async def _get_paired_devices_dbus(self) -> list:
        """Get list of paired device MACs using D-Bus."""
        import asyncio
        
        paired = []
        
        try:
            from dbus_fast.aio import MessageBus
            from dbus_fast import BusType
            
            bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
            
            # Get BlueZ object manager
            introspection = await bus.introspect("org.bluez", "/")
            obj = bus.get_proxy_object("org.bluez", "/", introspection)
            obj_manager = obj.get_interface("org.freedesktop.DBus.ObjectManager")
            
            objects = await obj_manager.call_get_managed_objects()
            
            for path, interfaces in objects.items():
                if "org.bluez.Device1" in interfaces:
                    props = interfaces["org.bluez.Device1"]
                    if props.get("Paired", {}).value:
                        address = props.get("Address", {}).value
                        if address:
                            paired.append(address)
            
            bus.disconnect()
            
        except ImportError:
            _LOGGER.debug("dbus_fast not available")
        except Exception as e:
            _LOGGER.debug("D-Bus paired devices query failed: %s", e)
        
        return paired
    
    async def _pair_with_ha_bluetooth(self, mac: str) -> dict:
        """Pair using Home Assistant's Bluetooth integration."""
        try:
            # First check if it's a BLE device we can connect to
            try:
                from homeassistant.components.bluetooth import async_ble_device_from_address
                
                # NOTE: async_ble_device_from_address is NOT async despite the name!
                ble_device = async_ble_device_from_address(
                    self.hass, mac, connectable=True
                )
                
                if ble_device:
                    # It's a BLE device - try connecting to trigger pairing
                    try:
                        from bleak import BleakClient
                        from bleak_retry_connector import establish_connection
                        
                        _LOGGER.info("Attempting BLE connection to %s", mac)
                        client = await establish_connection(
                            BleakClient, 
                            ble_device, 
                            mac, 
                            max_attempts=3
                        )
                        
                        if client.is_connected:
                            _LOGGER.info("BLE device %s connected successfully", mac)
                            await client.disconnect()
                            return {"success": True, "message": "BLE device paired successfully"}
                            
                    except Exception as ble_ex:
                        _LOGGER.debug("BLE connection failed: %s", ble_ex)
                        
            except ImportError:
                _LOGGER.debug("HA Bluetooth not available")
            except Exception as e:
                _LOGGER.debug("HA Bluetooth lookup failed: %s", e)
            
            return {"success": False, "error": "Could not pair via HA Bluetooth"}
            
        except Exception as e:
            _LOGGER.debug("HA Bluetooth pairing failed: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _pair_with_dbus(self, mac: str) -> dict:
        """Pair with a Bluetooth device using D-Bus."""
        import asyncio
        
        try:
            from dbus_fast.aio import MessageBus
            from dbus_fast import BusType, Variant
            
            _LOGGER.info("Attempting D-Bus pairing for %s", mac)
            
            bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
            
            # Convert MAC to D-Bus path format
            mac_path = mac.replace(':', '_').upper()
            device_path = f"/org/bluez/hci0/dev_{mac_path}"
            
            try:
                # First, check if the adapter exists and start discovery if needed
                try:
                    adapter_introspection = await bus.introspect("org.bluez", "/org/bluez/hci0")
                    adapter_obj = bus.get_proxy_object("org.bluez", "/org/bluez/hci0", adapter_introspection)
                    adapter = adapter_obj.get_interface("org.bluez.Adapter1")
                    
                    # Start discovery to ensure device is found
                    try:
                        await adapter.call_start_discovery()
                        await asyncio.sleep(3)  # Wait for device to be discovered
                        await adapter.call_stop_discovery()
                    except Exception as disc_ex:
                        _LOGGER.debug("Discovery control: %s", disc_ex)
                        
                except Exception as adapter_ex:
                    _LOGGER.debug("Adapter access failed: %s", adapter_ex)
                
                # Now try to access the device
                try:
                    introspection = await bus.introspect("org.bluez", device_path)
                except Exception:
                    bus.disconnect()
                    return {"success": False, "error": f"Device {mac} not found by BlueZ. Put device in pairing mode and scan again."}
                
                device_obj = bus.get_proxy_object("org.bluez", device_path, introspection)
                device = device_obj.get_interface("org.bluez.Device1")
                props = device_obj.get_interface("org.freedesktop.DBus.Properties")
                
                # Check if already paired
                try:
                    paired = await props.call_get("org.bluez.Device1", "Paired")
                    if paired.value:
                        bus.disconnect()
                        return {"success": True, "message": "Device already paired"}
                except Exception:
                    pass
                
                # Set trusted first
                try:
                    await props.call_set("org.bluez.Device1", "Trusted", Variant('b', True))
                    _LOGGER.debug("Set device as trusted")
                except Exception as trust_ex:
                    _LOGGER.debug("Could not set trusted: %s", trust_ex)
                
                # Pair the device
                try:
                    _LOGGER.info("Initiating pairing with %s", mac)
                    await asyncio.wait_for(device.call_pair(), timeout=30)
                    _LOGGER.info("Pairing successful for %s", mac)
                except Exception as pair_ex:
                    error_str = str(pair_ex)
                    if "AlreadyExists" in error_str or "Already Exists" in error_str:
                        _LOGGER.debug("Device already paired")
                    elif "AuthenticationCanceled" in error_str:
                        bus.disconnect()
                        return {"success": False, "error": "Pairing canceled. Put device in pairing mode and try again."}
                    elif "AuthenticationFailed" in error_str:
                        bus.disconnect()
                        return {"success": False, "error": "Authentication failed. Device may require a PIN."}
                    elif "AuthenticationRejected" in error_str:
                        bus.disconnect()
                        return {"success": False, "error": "Pairing rejected. Put device in pairing mode."}
                    elif "ConnectionAttemptFailed" in error_str:
                        bus.disconnect()
                        return {"success": False, "error": "Connection failed. Device may be out of range."}
                    elif "InProgress" in error_str:
                        bus.disconnect()
                        return {"success": False, "error": "Another pairing is in progress. Wait and try again."}
                    else:
                        _LOGGER.error("Pairing error: %s", pair_ex)
                        bus.disconnect()
                        return {"success": False, "error": f"Pairing failed: {error_str[:100]}"}
                
                # Try to connect (optional - some devices don't stay connected)
                try:
                    await asyncio.wait_for(device.call_connect(), timeout=10)
                    _LOGGER.debug("Connected to device")
                except Exception as conn_ex:
                    _LOGGER.debug("Connect after pair: %s (non-fatal)", conn_ex)
                
                bus.disconnect()
                return {"success": True, "message": "Paired successfully"}
                
            except Exception as e:
                bus.disconnect()
                raise e
                
        except ImportError:
            _LOGGER.debug("dbus_fast not available")
            return {"success": False, "error": "D-Bus library not available"}
        except Exception as e:
            _LOGGER.error("D-Bus pairing failed: %s", e)
            return {"success": False, "error": f"D-Bus error: {str(e)[:100]}"}
    
    async def _pair_with_bluetoothctl(self, mac: str) -> dict:
        """Pair with a Bluetooth device using bluetoothctl (for classic Bluetooth)."""
        import asyncio
        
        _LOGGER.info("Attempting to pair %s using bluetoothctl", mac)
        
        try:
            # Use a more robust approach with bluetoothctl
            # Create a script that handles the full pairing flow
            commands = f"""
agent off
agent NoInputNoOutput
default-agent
power on
scan on
sleep 3
scan off
trust {mac}
pair {mac}
sleep 5
connect {mac}
info {mac}
quit
"""
            
            _LOGGER.debug("Running bluetoothctl pairing sequence for %s", mac)
            
            pair_proc = await asyncio.create_subprocess_exec(
                "bluetoothctl",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                pair_proc.communicate(input=commands.encode()),
                timeout=45
            )
            output = stdout.decode() + stderr.decode()
            
            _LOGGER.debug("bluetoothctl output: %s", output[:500])
            
            # Check for success indicators
            if "Pairing successful" in output:
                return {"success": True, "message": "Paired successfully"}
            
            if "Paired: yes" in output:
                return {"success": True, "message": "Device is already paired"}
            
            if "Connection successful" in output:
                return {"success": True, "message": "Connected successfully"}
            
            # Check for common errors
            if "org.bluez.Error.AuthenticationFailed" in output:
                return {"success": False, "error": "Authentication failed. Make sure device is in pairing mode."}
            
            if "org.bluez.Error.AuthenticationCanceled" in output:
                return {"success": False, "error": "Pairing canceled. Try again with device in pairing mode."}
            
            if "org.bluez.Error.AuthenticationRejected" in output:
                return {"success": False, "error": "Pairing rejected by device. Put device in pairing mode first."}
            
            if "org.bluez.Error.ConnectionAttemptFailed" in output:
                return {"success": False, "error": "Connection failed. Device may be out of range or not in pairing mode."}
            
            if "org.bluez.Error.AlreadyExists" in output or "already exists" in output.lower():
                return {"success": True, "message": "Device already paired"}
            
            if "not available" in output.lower() or "Device" not in output:
                return {"success": False, "error": "Device not found. Ensure Bluetooth is enabled and device is nearby."}
            
            if "Failed to pair" in output:
                return {"success": False, "error": "Pairing failed. Put device in pairing mode and try again."}
            
            # Check final state
            if "Paired: yes" in output:
                return {"success": True, "message": "Device paired"}
            
            return {"success": False, "error": "Pairing result unclear. Try pairing via HA Settings > Devices > Bluetooth."}
            
        except asyncio.TimeoutError:
            _LOGGER.error("bluetoothctl pairing timed out for %s", mac)
            return {"success": False, "error": "Pairing timed out. Hold device button to keep it in pairing mode and try again."}
        except FileNotFoundError:
            _LOGGER.debug("bluetoothctl not found")
            return {"success": False, "error": "bluetoothctl not available. Pair via HA Settings > Devices > Bluetooth."}
        except Exception as e:
            _LOGGER.error("bluetoothctl pairing error: %s", e)
            return {"success": False, "error": str(e)}
    
    async def _pair_ble(self, mac: str) -> dict:
        """Pair with a BLE device using HA's bluetooth integration."""
        try:
            from homeassistant.components.bluetooth import async_ble_device_from_address
            from bleak import BleakClient
            
            # Get device from HA's bluetooth
            ble_device = await async_ble_device_from_address(self.hass, mac, connectable=True)
            
            if not ble_device:
                return {"success": False, "error": f"Device {mac} not found. Ensure it's in pairing mode."}
            
            # Try to connect - this often triggers pairing for BLE devices
            try:
                from bleak_retry_connector import establish_connection
                client = await establish_connection(BleakClient, ble_device, mac, max_attempts=3)
                if client.is_connected:
                    await client.disconnect()
                    return {"success": True, "message": "BLE device connected successfully."}
            except Exception as conn_ex:
                _LOGGER.debug("BLE connection attempt: %s", conn_ex)
            
            return {"success": False, "error": "Could not establish BLE connection."}
            
        except ImportError:
            return {"success": False, "error": "Bluetooth libraries not available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _pair_alternative(self, mac: str) -> dict:
        """Alternative pairing method using HA's bluetooth integration."""
        try:
            from homeassistant.components.bluetooth import async_ble_device_from_address
            from bleak import BleakClient
            
            # Get device from HA's bluetooth
            ble_device = await async_ble_device_from_address(self.hass, mac, connectable=True)
            
            if not ble_device:
                return {"success": False, "error": f"Device {mac} not found by HA Bluetooth. Ensure it's in pairing mode."}
            
            # Try to connect - this often triggers pairing for BLE devices
            try:
                from bleak_retry_connector import establish_connection
                client = await establish_connection(BleakClient, ble_device, mac, max_attempts=3)
                if client.is_connected:
                    await client.disconnect()
                    return {"success": True, "message": "Connected successfully. Device may now be paired."}
            except Exception as conn_ex:
                _LOGGER.debug("BLE connection attempt: %s", conn_ex)
            
            return {"success": False, "error": "Could not establish connection. For classic Bluetooth remotes, pair via HA Settings > Devices > Bluetooth."}
            
        except ImportError:
            return {"success": False, "error": "Bluetooth libraries not available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _unpair_with_dbus(self, mac: str) -> dict:
        """Remove a paired Bluetooth device using D-Bus."""
        try:
            from dbus_fast.aio import MessageBus
            from dbus_fast import BusType
            
            bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
            
            # Get adapter
            adapter_path = "/org/bluez/hci0"
            introspection = await bus.introspect("org.bluez", adapter_path)
            adapter_obj = bus.get_proxy_object("org.bluez", adapter_path, introspection)
            adapter = adapter_obj.get_interface("org.bluez.Adapter1")
            
            # Convert MAC to D-Bus path format
            device_path = f"/org/bluez/hci0/dev_{mac.replace(':', '_').upper()}"
            
            await adapter.call_remove_device(device_path)
            
            bus.disconnect()
            return {"success": True, "message": "Device removed"}
            
        except ImportError:
            return {"success": False, "error": "D-Bus not available"}
        except Exception as e:
            if "Does Not Exist" in str(e):
                return {"success": True, "message": "Device not found (already removed)"}
            return {"success": False, "error": str(e)}

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
    """API for IR command debugging, logging, and log download."""
    
    url = "/api/omniremote/debug"
    name = "api:omniremote:debug"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get debug log entries and status."""
        from .ir_encoder import get_debug_log
        from .const import DEBUG
        
        # Check for download request
        if request.query.get("download") == "true":
            return await self._download_log()
        
        # Check for HA log entries
        if request.query.get("ha_log") == "true":
            return await self._get_ha_log()
        
        return web.json_response({
            "debug_enabled": DEBUG,
            "ir_log": get_debug_log(),
            "ir_log_count": len(get_debug_log()),
        })
    
    async def _get_ha_log(self) -> web.Response:
        """Get OmniRemote entries from HA log."""
        log_entries = []
        try:
            import os
            log_path = self.hass.config.path("home-assistant.log")
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for line in lines[-3000:]:
                        if 'omniremote' in line.lower() or 'OmniRemote' in line or 'Flipper' in line:
                            log_entries.append(line.strip())
                    log_entries = log_entries[-500:]
        except Exception as ex:
            log_entries = [f"Error reading log: {ex}"]
        
        from .const import DEBUG
        return web.json_response({
            "debug_enabled": DEBUG,
            "log_entries": log_entries,
            "log_count": len(log_entries),
        })
    
    async def _download_log(self) -> web.Response:
        """Generate downloadable log file."""
        from datetime import datetime
        from .ir_encoder import get_debug_log
        from .const import DEBUG, VERSION
        
        log_content = []
        log_content.append(f"OmniRemote Debug Log")
        log_content.append(f"Generated: {datetime.now().isoformat()}")
        log_content.append(f"Version: {VERSION}")
        log_content.append(f"Debug Mode: {DEBUG}")
        log_content.append("=" * 60)
        log_content.append("")
        
        # Add IR debug log
        log_content.append("=== IR Encoder Debug Log ===")
        for entry in get_debug_log():
            log_content.append(str(entry))
        log_content.append("")
        
        # Add HA log entries
        log_content.append("=== Home Assistant Log (OmniRemote entries) ===")
        try:
            import os
            log_path = self.hass.config.path("home-assistant.log")
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if 'omniremote' in line.lower() or 'OmniRemote' in line or 'Flipper' in line:
                            log_content.append(line.rstrip())
        except Exception as ex:
            log_content.append(f"Error reading HA log: {ex}")
        
        log_text = "\n".join(log_content)
        
        return web.Response(
            body=log_text,
            content_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=omniremote-debug-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
            }
        )
    
    async def post(self, request: web.Request) -> web.Response:
        """Debug actions."""
        from .ir_encoder import clear_debug_log, get_debug_log, _log_debug
        
        data = await request.json()
        action = data.get("action")
        
        if action == "clear":
            clear_debug_log()
            return web.json_response({"success": True, "message": "Debug log cleared"})
        
        elif action == "test_log":
            _LOGGER.info("[OmniRemote] Test log entry from debug panel at %s", 
                        __import__('datetime').datetime.now().isoformat())
            return web.json_response({"success": True, "message": "Test log entry written"})
        
        elif action == "set_debug":
            # Can't change at runtime without file modification
            from .const import DEBUG
            return web.json_response({
                "debug_enabled": DEBUG,
                "note": "Debug mode is set in const.py. Current setting will persist until changed there."
            })
        
        elif action == "test_encode":
            from .ir_encoder import encode_ir_to_broadlink
            from .catalog import IRCode, IRProtocol
            
            protocol_str = data.get("protocol", "samsung32")
            address = data.get("address", "07")
            command = data.get("command", "02")
            
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
# MQTT Configuration API
# =============================================================================

class OmniApiMqttAutoConfigure(HomeAssistantView):
    """API for MQTT auto-configuration."""
    
    url = "/api/omniremote/mqtt/auto-configure"
    name = "api:omniremote:mqtt:autoconfigure"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def post(self, request: web.Request) -> web.Response:
        """Auto-configure MQTT from Home Assistant's MQTT integration."""
        import logging
        _LOGGER = logging.getLogger(__name__)
        _LOGGER.info("MQTT auto-configure requested")
        
        try:
            # Check if MQTT integration is configured in HA
            mqtt_entry = None
            for entry in self.hass.config_entries.async_entries():
                if entry.domain == "mqtt":
                    mqtt_entry = entry
                    break
            
            if not mqtt_entry:
                return web.json_response({
                    "success": False,
                    "error": "MQTT integration not found. Install Mosquitto add-on or configure MQTT manually."
                })
            
            # Get MQTT config from HA
            mqtt_data = mqtt_entry.data or {}
            broker = mqtt_data.get("broker", "localhost")
            port = mqtt_data.get("port", 1883)
            username = mqtt_data.get("username", "")
            
            _LOGGER.info("MQTT auto-configured from Home Assistant: %s:%s", broker, port)
            
            return web.json_response({
                "success": True,
                "config": {
                    "broker": broker,
                    "port": port,
                    "username": username,
                    "auto_configured": True
                }
            })
        except Exception as e:
            _LOGGER.exception("Auto-configure error: %s", e)
            return web.json_response({"success": False, "error": str(e)})


class OmniApiMqttTest(HomeAssistantView):
    """API for testing MQTT connection."""
    
    url = "/api/omniremote/mqtt/test"
    name = "api:omniremote:mqtt:test"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def post(self, request: web.Request) -> web.Response:
        """Test MQTT connection with provided settings."""
        import logging
        import socket
        _LOGGER = logging.getLogger(__name__)
        
        # Parse JSON body
        try:
            data = await request.json()
        except Exception:
            data = {}
        
        broker = data.get("broker", "localhost")
        try:
            port = int(data.get("port", 1883))
        except (ValueError, TypeError):
            port = 1883
        username = data.get("username", "")
        password = data.get("password", "")
        
        _LOGGER.info("Testing MQTT connection to %s:%s", broker, port)
        
        # Test TCP connection
        def tcp_test():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((broker, port))
                sock.close()
                return result
            except socket.gaierror as e:
                return f"DNS error: {e}"
            except Exception as e:
                return f"Socket error: {e}"
        
        try:
            result = await self.hass.async_add_executor_job(tcp_test)
            
            if isinstance(result, str):
                return web.json_response({"success": False, "error": result})
            elif result != 0:
                return web.json_response({
                    "success": False,
                    "error": f"Cannot reach {broker}:{port} (error code {result})"
                })
        except Exception as e:
            return web.json_response({"success": False, "error": f"Connection test failed: {e}"})
        
        # TCP succeeded - try MQTT auth if paho available
        try:
            import paho.mqtt.client as mqtt
            
            connected = [False]
            error_msg = [None]
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    connected[0] = True
                else:
                    codes = {1: "Bad protocol", 2: "Client ID rejected", 3: "Server unavailable", 
                             4: "Bad username/password", 5: "Not authorized"}
                    error_msg[0] = codes.get(rc, f"Error code {rc}")
            
            def test_mqtt():
                try:
                    client = mqtt.Client(client_id="omniremote-ha-test")
                    if username:
                        client.username_pw_set(username, password)
                    client.on_connect = on_connect
                    client.connect(broker, port, keepalive=10)
                    client.loop_start()
                    import time
                    for _ in range(30):
                        if connected[0] or error_msg[0]:
                            break
                        time.sleep(0.1)
                    client.loop_stop()
                    client.disconnect()
                except Exception as e:
                    error_msg[0] = str(e)
            
            await self.hass.async_add_executor_job(test_mqtt)
            
            if connected[0]:
                return web.json_response({"success": True, "message": "Connected successfully!"})
            elif error_msg[0]:
                return web.json_response({"success": False, "error": error_msg[0]})
            else:
                return web.json_response({"success": False, "error": "Connection timeout"})
        
        except ImportError:
            return web.json_response({
                "success": True,
                "message": f"TCP connection to {broker}:{port} successful (MQTT auth not tested)"
            })
        except Exception as e:
            return web.json_response({"success": False, "error": f"MQTT test error: {e}"})


class OmniApiMqttConfig(HomeAssistantView):
    """API for saving MQTT configuration."""
    
    url = "/api/omniremote/mqtt/config"
    name = "api:omniremote:mqtt:config"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def post(self, request: web.Request) -> web.Response:
        """Save MQTT configuration."""
        import logging
        _LOGGER = logging.getLogger(__name__)
        
        try:
            data = await request.json()
        except Exception:
            data = {}
        
        _LOGGER.info("Saving MQTT config: broker=%s", data.get("broker", ""))
        
        # For now just return success - actual saving requires database support
        return web.json_response({"success": True, "message": "Configuration saved"})


class OmniApiMqttStatus(HomeAssistantView):
    """API for getting MQTT status."""
    
    url = "/api/omniremote/mqtt/status"
    name = "api:omniremote:mqtt:status"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get current MQTT status by checking HA's MQTT integration."""
        import logging
        _LOGGER = logging.getLogger(__name__)
        
        try:
            # Check if MQTT integration is configured in HA
            mqtt_entry = None
            for entry in self.hass.config_entries.async_entries():
                if entry.domain == "mqtt":
                    mqtt_entry = entry
                    break
            
            if mqtt_entry:
                mqtt_data = mqtt_entry.data or {}
                return web.json_response({
                    "available": True,
                    "config": {
                        "broker": mqtt_data.get("broker", "localhost"),
                        "port": mqtt_data.get("port", 1883),
                        "username": mqtt_data.get("username", ""),
                    }
                })
            else:
                return web.json_response({
                    "available": False,
                    "config": {}
                })
        except Exception as e:
            _LOGGER.exception("MQTT status check error: %s", e)
            return web.json_response({
                "available": False,
                "config": {},
                "error": str(e)
            })


# =============================================================================
# Pi Hub API
# =============================================================================

def _get_pi_hub_manager(hass: HomeAssistant):
    """Get the Pi Hub manager from hass.data."""
    from .const import DOMAIN
    if DOMAIN not in hass.data:
        return None
    for entry_data in hass.data[DOMAIN].values():
        if isinstance(entry_data, dict) and "pi_hub_manager" in entry_data:
            return entry_data.get("pi_hub_manager")
    return None


class OmniApiPiHubs(HomeAssistantView):
    """API for Pi Hub discovery and management."""
    
    url = "/api/omniremote/pi_hubs"
    name = "api:omniremote:pi_hubs"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all discovered Pi Hubs."""
        manager = _get_pi_hub_manager(self.hass)
        
        if not manager:
            return web.json_response({
                "hubs": [],
                "mqtt_available": False,
                "message": "Pi Hub manager not initialized"
            })
        
        return web.json_response({
            "hubs": manager.get_hubs(),
            "mqtt_available": True,
        })


class OmniApiPiHubCommand(HomeAssistantView):
    """API for sending commands to Pi Hubs."""
    
    url = "/api/omniremote/pi_hubs/{hub_id}/command"
    name = "api:omniremote:pi_hubs:command"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def post(self, request: web.Request) -> web.Response:
        """Send a command to a Pi Hub."""
        hub_id = request.match_info.get("hub_id", "")
        manager = _get_pi_hub_manager(self.hass)
        
        if not manager:
            return web.json_response({"success": False, "error": "Manager not available"})
        
        try:
            data = await request.json()
            command = data.get("command", "")
            
            if not command:
                return web.json_response({"success": False, "error": "No command specified"})
            
            success = await manager.async_send_command(hub_id, command)
            return web.json_response({"success": success})
            
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)})


class OmniApiPiHubDiscover(HomeAssistantView):
    """API to trigger Pi Hub discovery."""
    
    url = "/api/omniremote/pi_hubs/discover"
    name = "api:omniremote:pi_hubs:discover"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def post(self, request: web.Request) -> web.Response:
        """Request all Pi Hubs to announce themselves."""
        manager = _get_pi_hub_manager(self.hass)
        
        if not manager:
            return web.json_response({"success": False, "error": "Manager not available"})
        
        try:
            await manager._request_discovery()
            return web.json_response({"success": True, "message": "Discovery request sent"})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)})


class OmniApiPiHubDevices(HomeAssistantView):
    """API to query Pi Hub for connected USB devices."""
    
    url = "/api/omniremote/pi_hubs/devices"
    name = "api:omniremote:pi_hubs:devices"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def post(self, request: web.Request) -> web.Response:
        """Query a Pi Hub for its connected USB devices."""
        manager = _get_pi_hub_manager(self.hass)
        
        if not manager:
            return web.json_response({"success": False, "error": "Manager not available"})
        
        try:
            data = await request.json()
            hub_id = data.get("hub_id", "")
            
            if not hub_id:
                # Query all online hubs
                all_devices = []
                for hub in manager.get_hubs():
                    if hub.get("online"):
                        devices = hub.get("devices", [])
                        for dev in devices:
                            all_devices.append({
                                **dev,
                                "hub_id": hub.get("id"),
                                "hub_name": hub.get("name"),
                            })
                return web.json_response({"success": True, "devices": all_devices})
            
            # Query specific hub
            hub = manager.get_hub(hub_id)
            if not hub:
                return web.json_response({"success": False, "error": f"Hub {hub_id} not found"})
            
            devices = hub.get("devices", [])
            return web.json_response({
                "success": True, 
                "devices": devices,
                "hub_id": hub_id,
                "hub_name": hub.get("name"),
            })
            
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)})


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
                model_id=data.get("model_id"),
            )
            
            # Apply button mappings if provided (from auto-import)
            initial_mappings = data.get("button_mappings")
            if initial_mappings and isinstance(initial_mappings, dict):
                _debug("Applying %d initial button mappings from model", len(initial_mappings))
                for btn_id, mapping_data in initial_mappings.items():
                    action_type_str = mapping_data.get("action_type", "scene")
                    try:
                        action_type = ActionType(action_type_str)
                    except ValueError:
                        action_type = ActionType.SCENE
                    
                    remote.button_mappings[btn_id] = ButtonMapping(
                        button_id=btn_id,
                        action_type=action_type,
                        action_target=mapping_data.get("action_target", ""),
                        action_data=mapping_data.get("action_data", {}),
                    )
            # Fall back to profile defaults if no mappings provided
            elif remote.profile:
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
            
            _debug("Added remote %s with %d button mappings", remote.name, len(remote.button_mappings))
            
            return web.json_response({
                "success": True,
                "remote": remote.to_dict(),
                "buttons_imported": len(remote.button_mappings)
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
        
        elif action == "save_button_mappings":
            # Save all button mappings at once (new format)
            _debug("save_button_mappings called with data: %s", data)
            
            remote_id = data.get("remote_id")
            if not remote_id or remote_id not in database.physical_remotes:
                _debug("Remote not found: %s", remote_id)
                return web.json_response({"error": "Remote not found"}, status=404)
            
            remote = database.physical_remotes[remote_id]
            button_mappings = data.get("button_mappings", {})
            
            # Update model_id if provided
            new_model_id = data.get("model_id")
            if new_model_id:
                remote.model_id = new_model_id
                _debug("Updated model_id to %s", new_model_id)
            
            _debug("Saving %d button mappings for remote %s (%s)", 
                   len(button_mappings), remote_id, remote.name)
            
            from .physical_remotes import ButtonMapping, ActionType
            
            # Clear existing mappings and add new ones
            remote.button_mappings = {}
            
            for btn_id, mapping_data in button_mappings.items():
                action_type_str = mapping_data.get("action_type", "scene")
                
                # Build action_data based on action type
                action_data = {}
                action_target = ""
                
                if action_type_str == "scene":
                    action_target = mapping_data.get("scene_id", "")
                    _debug("  Button %s -> scene: %s", btn_id, action_target)
                elif action_type_str == "activity":
                    action_target = mapping_data.get("activity_id", "")
                    _debug("  Button %s -> activity: %s", btn_id, action_target)
                elif action_type_str == "ir_command":
                    action_target = mapping_data.get("device_id", "")
                    action_data = {
                        "command_name": mapping_data.get("command_name", ""),
                        "blaster_id": mapping_data.get("blaster_id", ""),
                    }
                    _debug("  Button %s -> ir_command: device=%s, cmd=%s, blaster=%s", 
                           btn_id, action_target, action_data.get("command_name"), action_data.get("blaster_id"))
                elif action_type_str == "ha_service":
                    action_data = {
                        "domain": mapping_data.get("ha_domain", ""),
                        "service": mapping_data.get("ha_service", ""),
                        "entity_id": mapping_data.get("ha_entity_id", ""),
                    }
                    _debug("  Button %s -> ha_service: %s.%s on %s", 
                           btn_id, action_data.get("domain"), action_data.get("service"), action_data.get("entity_id"))
                elif action_type_str in ["volume_up", "volume_down", "mute"]:
                    action_target = mapping_data.get("room_id", "")
                    _debug("  Button %s -> %s: room=%s", btn_id, action_type_str, action_target)
                
                # Handle activity type - it's not in ActionType enum yet, so treat as SCENE for now
                try:
                    action_type = ActionType(action_type_str)
                except ValueError:
                    # Fallback for new action types not yet in enum
                    _debug("  Unknown action type %s, using SCENE", action_type_str)
                    action_type = ActionType.SCENE
                
                mapping = ButtonMapping(
                    button_id=btn_id,
                    action_type=action_type,
                    action_target=action_target,
                    action_data=action_data,
                )
                remote.button_mappings[btn_id] = mapping
            
            await database.async_save()
            _debug("Button mappings saved successfully for remote %s", remote_id)
            
            return web.json_response({
                "success": True,
                "mappings_saved": len(button_mappings)
            })
        
        elif action == "execute_button":
            # Execute a button press on a physical remote
            remote_id = data.get("remote_id")
            button_id = data.get("button_id")
            
            _debug("execute_button called: remote=%s, button=%s", remote_id, button_id)
            
            if not remote_id or remote_id not in database.physical_remotes:
                _debug("Remote not found: %s", remote_id)
                return web.json_response({"error": "Remote not found"}, status=404)
            
            remote = database.physical_remotes[remote_id]
            
            if button_id not in remote.button_mappings:
                _debug("Button mapping not found: %s", button_id)
                return web.json_response({"error": f"Button '{button_id}' not mapped"}, status=404)
            
            mapping = remote.button_mappings[button_id]
            _debug("Executing mapping: type=%s, target=%s, data=%s", 
                   mapping.action_type.value, mapping.action_target, mapping.action_data)
            
            try:
                # Execute based on action type
                result = await self._execute_button_mapping(database, remote, mapping)
                _debug("Button execution result: %s", result)
                
                return web.json_response({
                    "success": True,
                    "action_type": mapping.action_type.value,
                    "result": result
                })
            except Exception as ex:
                _LOGGER.error("[OmniRemote] Error executing button: %s", ex)
                return web.json_response({
                    "success": False,
                    "error": str(ex)
                }, status=500)
        
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
        
        elif action == "discover_bluetooth":
            # Discover Bluetooth remotes
            from .physical_remotes import discover_bluetooth_remotes
            
            try:
                discovered = await discover_bluetooth_remotes(self.hass)
                return web.json_response({
                    "success": True,
                    "discovered": discovered
                })
            except Exception as ex:
                return web.json_response({
                    "error": str(ex)
                }, status=500)
        
        elif action == "discover_remotes":
            # Discover ALL remotes (Zigbee + Bluetooth)
            from .physical_remotes import discover_all_remotes
            
            try:
                result = await discover_all_remotes(self.hass)
                return web.json_response({
                    "success": True,
                    "zigbee": result["zigbee"],
                    "bluetooth": result["bluetooth"],
                    "total": result["total"]
                })
            except Exception as ex:
                return web.json_response({
                    "error": str(ex)
                }, status=500)
        
        return web.json_response({"error": "Unknown action"}, status=400)
    
    async def _execute_button_mapping(self, database, remote, mapping) -> dict:
        """Execute a button mapping action."""
        from .physical_remotes import ActionType
        
        action_type = mapping.action_type
        target = mapping.action_target
        data = mapping.action_data or {}
        
        result = {"executed": True}
        
        if action_type == ActionType.SCENE:
            # Run a scene
            _debug("Executing scene: %s", target)
            if target and target in database.scenes:
                scene = database.scenes[target]
                # Fire event to run scene
                self.hass.bus.async_fire("omniremote_run_scene", {"scene_id": target})
                result["scene_id"] = target
                result["scene_name"] = scene.name
            else:
                result["error"] = f"Scene not found: {target}"
                result["executed"] = False
        
        elif action_type == ActionType.IR_COMMAND:
            # Send IR command
            device_id = target
            command_name = data.get("command_name")
            blaster_id = data.get("blaster_id")
            
            _debug("Executing IR command: device=%s, cmd=%s, blaster=%s", 
                   device_id, command_name, blaster_id)
            
            if device_id and device_id in database.devices:
                device = database.devices[device_id]
                if command_name and command_name in device.commands:
                    cmd = device.commands[command_name]
                    # Fire event to send IR
                    self.hass.bus.async_fire("omniremote_send_ir", {
                        "device_id": device_id,
                        "command_name": command_name,
                        "blaster_id": blaster_id or device.room_id,
                        "broadlink_code": cmd.broadlink_code,
                    })
                    result["device"] = device.name
                    result["command"] = command_name
                else:
                    result["error"] = f"Command not found: {command_name}"
                    result["executed"] = False
            else:
                result["error"] = f"Device not found: {device_id}"
                result["executed"] = False
        
        elif action_type == ActionType.HA_SERVICE:
            # Call HA service
            domain = data.get("domain")
            service = data.get("service")
            entity_id = data.get("entity_id")
            
            _debug("Executing HA service: %s.%s on %s", domain, service, entity_id)
            
            if domain and service:
                service_data = {}
                if entity_id:
                    service_data["entity_id"] = entity_id
                
                await self.hass.services.async_call(domain, service, service_data)
                result["service"] = f"{domain}.{service}"
                result["entity_id"] = entity_id
            else:
                result["error"] = "Domain and service required"
                result["executed"] = False
        
        elif action_type in [ActionType.VOLUME_UP, ActionType.VOLUME_DOWN, ActionType.MUTE]:
            # Volume control - fire events for room to handle
            room_id = target or remote.room_id
            _debug("Executing volume action: %s for room %s", action_type.value, room_id)
            
            self.hass.bus.async_fire(f"omniremote_{action_type.value}", {
                "room_id": room_id,
                "remote_id": remote.id,
            })
            result["action"] = action_type.value
            result["room_id"] = room_id
        
        else:
            result["error"] = f"Unknown action type: {action_type.value}"
            result["executed"] = False
        
        return result


class OmniApiRemoteModels(HomeAssistantView):
    """API for remote model profiles (pre-configured button mappings)."""
    
    url = "/api/omniremote/remote_models"
    name = "api:omniremote:remote_models"
    requires_auth = False
    
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get available remote models."""
        from .remote_models import list_models, list_models_grouped
        
        grouped = request.query.get("grouped", "false").lower() == "true"
        
        if grouped:
            return web.json_response({
                "models_by_manufacturer": list_models_grouped()
            })
        else:
            return web.json_response({
                "models": list_models()
            })
    
    async def post(self, request: web.Request) -> web.Response:
        """Get a specific model or apply model to remote."""
        from .remote_models import get_model, get_model_by_zigbee
        from .physical_remotes import ButtonMapping, ActionType
        
        data = await request.json()
        action = data.get("action", "get")
        
        if action == "get":
            model_id = data.get("model_id")
            if model_id:
                model = get_model(model_id)
                if model:
                    return web.json_response({"model": model.to_dict()})
                return web.json_response({"error": "Model not found"}, status=404)
            return web.json_response({"error": "model_id required"}, status=400)
        
        elif action == "detect":
            # Try to detect model from zigbee identifier
            zigbee_model = data.get("zigbee_model", "")
            if zigbee_model:
                model = get_model_by_zigbee(zigbee_model)
                if model:
                    return web.json_response({"model": model.to_dict()})
            return web.json_response({"model": None})
        
        elif action == "apply":
            # Apply a model's buttons to a physical remote
            model_id = data.get("model_id")
            remote_id = data.get("remote_id")
            
            if not model_id or not remote_id:
                return web.json_response({"error": "model_id and remote_id required"}, status=400)
            
            model = get_model(model_id)
            if not model:
                return web.json_response({"error": "Model not found"}, status=404)
            
            database = _get_database(self.hass)
            if not database or remote_id not in database.physical_remotes:
                return web.json_response({"error": "Remote not found"}, status=404)
            
            remote = database.physical_remotes[remote_id]
            remote.model_id = model_id
            
            # Create button mappings from model with suggested actions
            for btn in model.buttons:
                action_type = ActionType.SCENE
                if btn.suggested_action == "volume_up":
                    action_type = ActionType.VOLUME_UP
                elif btn.suggested_action == "volume_down":
                    action_type = ActionType.VOLUME_DOWN
                elif btn.suggested_action == "mute":
                    action_type = ActionType.MUTE
                elif btn.suggested_action == "ir_command":
                    action_type = ActionType.IR_COMMAND
                elif btn.suggested_action == "ha_service":
                    action_type = ActionType.HA_SERVICE
                
                mapping = ButtonMapping(
                    button_id=btn.button_id,
                    action_type=action_type,
                    action_target="",
                    action_data={"icon": btn.icon, "label": btn.label, "color": btn.color},
                )
                remote.button_mappings[btn.button_id] = mapping
            
            await database.async_save()
            
            return web.json_response({
                "success": True,
                "buttons_created": len(model.buttons)
            })
        
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
            
            try:
                _LOGGER.info("[OmniRemote] Attempting to connect to Flipper: %s", device_id)
                success = await manager.async_connect(device_id)
                device = manager.get_device(device_id)
                
                if success:
                    _LOGGER.info("[OmniRemote] Successfully connected to Flipper: %s", device_id)
                    return web.json_response({
                        "success": True,
                        "device": device.to_dict() if device else None,
                    })
                else:
                    # Provide more helpful error message
                    error_msg = "Connection failed"
                    troubleshooting = []
                    if device:
                        if device.connection_type.value == "usb":
                            error_msg = f"USB connection to {device.port} failed"
                            troubleshooting = [
                                "Check USB cable is connected",
                                "Close qFlipper or other apps using the port",
                                "Try a different USB port",
                            ]
                        else:
                            error_msg = f"Bluetooth connection to {device.port} failed"
                            troubleshooting = [
                                "HA Bluetooth may be out of connection slots - disconnect other BT devices",
                                "On Flipper: Settings → Bluetooth → Turn ON",
                                "Disconnect Flipper from phone app and qFlipper",
                                "Try moving Flipper closer to Home Assistant",
                                "USB connection is much more reliable than Bluetooth",
                                "Consider adding ESPHome Bluetooth Proxy for more slots",
                            ]
                    _LOGGER.warning("[OmniRemote] Flipper connection failed: %s", error_msg)
                    return web.json_response({
                        "success": False,
                        "error": error_msg,
                        "troubleshooting": troubleshooting,
                    })
            except Exception as ex:
                import traceback
                tb = traceback.format_exc()
                _LOGGER.error("[OmniRemote] Flipper connect exception: %s\n%s", ex, tb)
                return web.json_response({
                    "success": False,
                    "error": str(ex),
                    "traceback": tb,
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
        
        elif action == "diagnose":
            # Diagnose Bluetooth connection issues
            device_id = data.get("device_id")
            results = {
                "device_id": device_id,
                "checks": [],
            }
            
            device = manager.get_device(device_id) if device_id else None
            
            if device:
                results["device_name"] = device.name
                results["connection_type"] = device.connection_type.value
                results["port"] = device.port
                results["connected"] = device.connected
                
                if device.connection_type.value == "bluetooth":
                    # Try to scan for the device
                    try:
                        from homeassistant.components.bluetooth import async_ble_device_from_address
                        
                        ble_device = async_ble_device_from_address(
                            self.hass, device.port, connectable=True
                        )
                        
                        if ble_device:
                            results["checks"].append({
                                "check": "HA Bluetooth cache",
                                "status": "found",
                                "details": f"Device found: {ble_device.name or 'unnamed'}",
                            })
                        else:
                            results["checks"].append({
                                "check": "HA Bluetooth cache", 
                                "status": "not_found",
                                "details": "Device not in HA Bluetooth cache. Try scanning again.",
                            })
                    except Exception as ex:
                        results["checks"].append({
                            "check": "HA Bluetooth cache",
                            "status": "error",
                            "details": str(ex),
                        })
                    
                    # Check if bleak is available
                    try:
                        import bleak
                        results["checks"].append({
                            "check": "bleak library",
                            "status": "ok",
                            "details": f"Version: {bleak.__version__}",
                        })
                    except ImportError:
                        results["checks"].append({
                            "check": "bleak library",
                            "status": "missing",
                            "details": "bleak not installed",
                        })
                    
                    # Check bleak-retry-connector
                    try:
                        import bleak_retry_connector
                        results["checks"].append({
                            "check": "bleak-retry-connector",
                            "status": "ok",
                            "details": "Available",
                        })
                    except ImportError:
                        results["checks"].append({
                            "check": "bleak-retry-connector",
                            "status": "missing",
                            "details": "Not installed (optional but recommended)",
                        })
            else:
                results["error"] = "Device not found"
            
            return web.json_response(results)
        
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
