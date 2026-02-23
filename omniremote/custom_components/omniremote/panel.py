"""Panel and API for OmniRemote GUI."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aiohttp import web

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DeviceCategory, SceneAction
from .database import RemoteDatabase
from .catalog import DEVICE_CATALOG, CATALOG_BY_BRAND, CATALOG_BY_CATEGORY, get_catalog_device, search_catalog, list_catalog
from .activities import Activity, ActivityAction, ActionType, ActivityRunner

_LOGGER = logging.getLogger(__name__)

PANEL_URL = "/omniremote"
PANEL_TITLE = "Remote Manager"
PANEL_ICON = "mdi:remote-tv"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the panel and API."""
    # Register API views
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
    
    # Register the panel
    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="omniremote-panel",
        frontend_url_path="omniremote",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        module_url="/api/omniremote/panel.js",
        embed_iframe=False,
        require_admin=False,
    )
    
    _LOGGER.info("OmniRemote panel registered")


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
    
    async def get(self, request: web.Request) -> web.Response:
        """Return the panel JavaScript."""
        panel_path = Path(__file__).parent / "panel.js"
        
        if panel_path.exists():
            content = panel_path.read_text()
        else:
            content = "console.error('Panel not found');"
        
        return web.Response(
            text=content,
            content_type="application/javascript",
        )


class OmniApiRooms(HomeAssistantView):
    """API for room management."""
    
    url = "/api/omniremote/rooms"
    name = "api:omniremote:rooms"
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all rooms."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        rooms = [r.to_dict() for r in database.rooms.values()]
        return web.json_response({"rooms": rooms})
    
    async def post(self, request: web.Request) -> web.Response:
        """Create a new room."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        room = database.add_room(
            name=data.get("name", "New Room"),
            icon=data.get("icon", "mdi:sofa"),
        )
        await database.async_save()
        
        return web.json_response({"room": room.to_dict()})


class OmniApiDevices(HomeAssistantView):
    """API for device management."""
    
    url = "/api/omniremote/devices"
    name = "api:omniremote:devices"
    
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
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all scenes."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        scenes = [s.to_dict() for s in database.scenes.values()]
        return web.json_response({"scenes": scenes})
    
    async def post(self, request: web.Request) -> web.Response:
        """Create a new scene."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        
        actions = []
        for action_data in data.get("actions", []):
            actions.append(SceneAction(
                device_id=action_data.get("device_id", ""),
                command_name=action_data.get("command_name", ""),
                delay_after=action_data.get("delay_after", 0.5),
            ))
        
        scene = database.add_scene(
            name=data.get("name", "New Scene"),
            actions=actions,
            room_id=data.get("room_id"),
            icon=data.get("icon", "mdi:play"),
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
        if "actions" in data:
            scene.actions = []
            for action_data in data["actions"]:
                scene.actions.append(SceneAction(
                    device_id=action_data.get("device_id", ""),
                    command_name=action_data.get("command_name", ""),
                    delay_after=action_data.get("delay_after", 0.5),
                ))
        
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
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass
    
    async def get(self, request: web.Request) -> web.Response:
        """Get all blasters."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        blasters = [b.to_dict() for b in database.blasters.values()]
        return web.json_response({"blasters": blasters})
    
    async def post(self, request: web.Request) -> web.Response:
        """Discover blasters."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        blasters = await database.async_discover_blasters()
        await database.async_save()
        
        return web.json_response({
            "blasters": [b.to_dict() for b in blasters]
        })


class OmniApiCommands(HomeAssistantView):
    """API for sending commands."""
    
    url = "/api/omniremote/commands"
    name = "api:omniremote:commands"
    
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
            cat = DeviceCategory(category)
            results = CATALOG_BY_CATEGORY.get(cat, [])
        elif brand:
            results = CATALOG_BY_BRAND.get(brand, [])
        else:
            results = list(DEVICE_CATALOG.values())
        
        return web.json_response({
            "devices": [d.to_dict() for d in results],
            "brands": list(CATALOG_BY_BRAND.keys()),
            "categories": [c.value for c in DeviceCategory],
        })
    
    async def post(self, request: web.Request) -> web.Response:
        """Add a device from the catalog to the database."""
        database = _get_database(self.hass)
        if not database:
            return web.json_response({"error": "Database not found"}, status=500)
        
        data = await request.json()
        catalog_id = data.get("catalog_id")
        device_name = data.get("name", "")
        room_id = data.get("room_id")
        
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
        
        # Copy IR codes
        for cmd_name, code in catalog_device.ir_codes.items():
            device.commands[cmd_name] = code
        
        # Copy RF codes
        for cmd_name, code in catalog_device.rf_codes.items():
            device.commands[cmd_name] = code
        
        await database.async_save()
        
        return web.json_response({
            "device": device.to_dict(),
            "commands_added": len(device.commands),
        })


class OmniApiActivities(HomeAssistantView):
    """API for activities/macros."""
    
    url = "/api/omniremote/activities"
    name = "api:omniremote:activities"
    
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

