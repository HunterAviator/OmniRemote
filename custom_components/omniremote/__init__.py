"""OmniRemote - Manage IR/RF remotes with Flipper Zero and Broadlink."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    DeviceCategory,
    DOMAIN,
    SceneAction,
    SERVICE_ADD_DEVICE,
    SERVICE_ADD_ROOM,
    SERVICE_CREATE_SCENE,
    SERVICE_EXPORT_FLIPPER,
    SERVICE_IMPORT_FLIPPER,
    SERVICE_LEARN_CODE,
    SERVICE_RUN_SCENE,
    SERVICE_SEND_CODE,
)
from .database import RemoteDatabase
from .panel import async_register_panel

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.REMOTE, Platform.SCENE, Platform.BUTTON, Platform.SWITCH]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the OmniRemote component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OmniRemote from a config entry."""
    _LOGGER.info("Setting up OmniRemote integration")
    
    # Create database
    database = RemoteDatabase(hass)
    await database.async_load()
    
    # Discover blasters (don't fail if this errors)
    try:
        await database.async_discover_blasters()
    except Exception as ex:
        _LOGGER.warning("Blaster discovery failed: %s", ex)
    
    # Set up Bluetooth remote manager
    bluetooth_manager = None
    try:
        from .bluetooth_remote import async_setup_bluetooth_remotes
        bluetooth_manager = await async_setup_bluetooth_remotes(hass, database)
    except Exception as e:
        _LOGGER.warning("Bluetooth remote support not available: %s", e)
    
    # Set up area remote manager
    area_manager = None
    try:
        from .area_remotes import async_setup_area_remotes
        area_manager = await async_setup_area_remotes(hass, database)
    except Exception as e:
        _LOGGER.warning("Area remote support not available: %s", e)
    
    # Set up physical remote manager (Zigbee, RF, BT, USB remotes)
    physical_remote_manager = None
    try:
        from .physical_remotes import PhysicalRemoteManager
        physical_remote_manager = PhysicalRemoteManager(hass, database)
        await physical_remote_manager.async_start()
        _LOGGER.info("Physical remote manager started")
    except Exception as e:
        _LOGGER.warning("Physical remote support not available: %s", e)
    
    # Register event listeners for button execution
    async def handle_send_ir(event):
        """Handle omniremote_send_ir event."""
        data = event.data
        device_id = data.get("device_id")
        command_name = data.get("command_name")
        blaster_id = data.get("blaster_id")
        broadlink_code = data.get("broadlink_code")
        
        _LOGGER.info("[OmniRemote] Send IR event: device=%s, cmd=%s, blaster=%s, has_code=%s", 
                    device_id, command_name, blaster_id, bool(broadlink_code))
        
        # Look up broadlink_code from device if not provided directly
        if not broadlink_code and device_id and command_name:
            if device_id in database.devices:
                device = database.devices[device_id]
                if command_name in device.commands:
                    cmd = device.commands[command_name]
                    broadlink_code = cmd.broadlink_code if hasattr(cmd, 'broadlink_code') else cmd.get("broadlink_code")
                    _LOGGER.debug("[OmniRemote] Looked up IR code for %s/%s", device_id, command_name)
                else:
                    _LOGGER.warning("[OmniRemote] Command %s not found in device %s", command_name, device_id)
            else:
                _LOGGER.warning("[OmniRemote] Device not found: %s", device_id)
        
        if not broadlink_code:
            _LOGGER.error("[OmniRemote] No IR code to send for device=%s, cmd=%s", device_id, command_name)
            return
        
        try:
            # Find the blaster to use
            blaster = None
            if blaster_id and blaster_id in database.blasters:
                blaster = database.blasters[blaster_id]
            elif database.blasters:
                # Use first available blaster
                blaster = next(iter(database.blasters.values()))
            
            if not blaster:
                _LOGGER.error("[OmniRemote] No blaster available to send IR")
                return
            
            # Send the IR code via Broadlink
            _LOGGER.info("[OmniRemote] Sending IR via blaster %s (%s)", blaster.name, blaster.host)
            
            import broadlink
            import base64
            
            device = broadlink.gendevice(
                0x5f36,  # RM4 Mini type
                (blaster.host, 80),
                bytes.fromhex(blaster.mac.replace(":", "")),
                name=blaster.name
            )
            await hass.async_add_executor_job(device.auth)
            code_bytes = base64.b64decode(broadlink_code)
            await hass.async_add_executor_job(device.send_data, code_bytes)
            _LOGGER.info("[OmniRemote] IR sent successfully via %s", blaster.name)
        except Exception as ex:
            _LOGGER.error("[OmniRemote] Error sending IR: %s", ex)
    
    async def handle_run_scene(event):
        """Handle omniremote_run_scene event."""
        scene_id = event.data.get("scene_id")
        _LOGGER.info("[OmniRemote] Run scene event: %s", scene_id)
        
        if scene_id and scene_id in database.scenes:
            scene = database.scenes[scene_id]
            _LOGGER.info("[OmniRemote] Activating scene: %s", scene.name)
            # Fire each action in the scene
            for action in scene.on_actions or scene.actions:
                if action.action_type == "ir_command" and action.device_id:
                    device = database.devices.get(action.device_id)
                    if device and action.command_name in device.commands:
                        cmd = device.commands[action.command_name]
                        hass.bus.async_fire("omniremote_send_ir", {
                            "device_id": action.device_id,
                            "command_name": action.command_name,
                            "blaster_id": action.blaster_id or scene.blaster_id,
                            "broadlink_code": cmd.broadlink_code,
                        })
                        if action.delay_seconds > 0:
                            import asyncio
                            await asyncio.sleep(action.delay_seconds)
        else:
            _LOGGER.warning("[OmniRemote] Scene not found: %s", scene_id)
    
    # Register event listeners
    hass.bus.async_listen("omniremote_send_ir", handle_send_ir)
    hass.bus.async_listen("omniremote_run_scene", handle_run_scene)
    _LOGGER.info("[OmniRemote] Event listeners registered for IR send and scene execution")
    
    # Store in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "database": database,
        "entry": entry,
        "bluetooth_manager": bluetooth_manager,
        "area_manager": area_manager,
        "physical_remote_manager": physical_remote_manager,
    }
    
    # Register services
    try:
        await _async_register_services(hass, database)
    except Exception as ex:
        _LOGGER.error("Failed to register services: %s", ex)
    
    # Register the panel (sidebar GUI) - this is critical
    try:
        await async_register_panel(hass)
        _LOGGER.info("OmniRemote panel registered successfully")
    except Exception as ex:
        _LOGGER.error("Failed to register panel: %s", ex)
    
    # Register the Lovelace card resource
    await _async_register_card_resource(hass)
    
    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("OmniRemote setup complete")
    return True


async def _async_register_card_resource(hass: HomeAssistant) -> None:
    """Register the OmniRemote Lovelace card as a frontend resource."""
    try:
        # The card JS is served via OmniRemoteCardResource view
        # Users can add it as a Lovelace resource: /api/omniremote/card.js
        _LOGGER.info(
            "OmniRemote card available at /api/omniremote/card.js - "
            "Add this as a Lovelace resource to use the card"
        )
    except Exception as ex:
        _LOGGER.warning("Could not register card resource: %s", ex)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def _async_register_services(
    hass: HomeAssistant,
    database: RemoteDatabase,
) -> None:
    """Register services for the integration."""
    
    # === Import Flipper Files ===
    async def handle_import_flipper(call: ServiceCall) -> None:
        """Import from Flipper Zero files."""
        path = call.data["path"]
        count = await database.async_import_flipper(path)
        _LOGGER.info("Imported %d devices from Flipper files", count)
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_IMPORT_FLIPPER,
        handle_import_flipper,
        schema=vol.Schema({
            vol.Required("path"): cv.string,
        }),
    )
    
    # === Export to Flipper ===
    async def handle_export_flipper(call: ServiceCall) -> None:
        """Export to Flipper Zero files."""
        path = call.data["output_path"]
        count = await hass.async_add_executor_job(
            database.export_to_flipper, path
        )
        _LOGGER.info("Exported %d devices to Flipper files", count)
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_FLIPPER,
        handle_export_flipper,
        schema=vol.Schema({
            vol.Required("output_path"): cv.string,
        }),
    )
    
    # === Learn Code ===
    async def handle_learn_code(call: ServiceCall) -> None:
        """Learn a new code."""
        device_name = call.data["device"]
        command_name = call.data["command"]
        blaster_id = call.data.get("blaster_id")
        timeout = call.data.get("timeout", 15)
        
        # Find or create device
        device = database.get_device_by_name(device_name)
        if not device:
            device = database.add_device(name=device_name)
        
        # Learn the code
        code = await database.async_learn_code(blaster_id, timeout)
        
        if code:
            code.name = command_name
            database.add_command_to_device(device.id, command_name, code)
            await database.async_save()
            
            # Fire event
            hass.bus.async_fire(
                f"{DOMAIN}_code_learned",
                {
                    "device": device_name,
                    "command": command_name,
                },
            )
            _LOGGER.info("Learned command: %s.%s", device_name, command_name)
        else:
            _LOGGER.warning("Failed to learn command")
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_LEARN_CODE,
        handle_learn_code,
        schema=vol.Schema({
            vol.Required("device"): cv.string,
            vol.Required("command"): cv.string,
            vol.Optional("blaster_id"): cv.string,
            vol.Optional("timeout", default=15): cv.positive_int,
        }),
    )
    
    # === Send Code ===
    async def handle_send_code(call: ServiceCall) -> None:
        """Send a code."""
        device_name = call.data["device"]
        command_name = call.data["command"]
        blaster_id = call.data.get("blaster_id")
        
        device = database.get_device_by_name(device_name)
        if not device:
            _LOGGER.error("Device not found: %s", device_name)
            return
        
        code = device.commands.get(command_name)
        if not code:
            _LOGGER.error("Command not found: %s.%s", device_name, command_name)
            return
        
        success = await database.async_send_code(code, blaster_id)
        if success:
            _LOGGER.debug("Sent command: %s.%s", device_name, command_name)
        else:
            _LOGGER.error("Failed to send command")
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_CODE,
        handle_send_code,
        schema=vol.Schema({
            vol.Required("device"): cv.string,
            vol.Required("command"): cv.string,
            vol.Optional("blaster_id"): cv.string,
        }),
    )
    
    # === Run Scene ===
    async def handle_run_scene(call: ServiceCall) -> None:
        """Run a scene."""
        scene_name = call.data["scene"]
        
        scene = database.get_scene_by_name(scene_name)
        if not scene:
            _LOGGER.error("Scene not found: %s", scene_name)
            return
        
        success = await database.async_run_scene(scene.id)
        if success:
            _LOGGER.info("Ran scene: %s", scene_name)
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_RUN_SCENE,
        handle_run_scene,
        schema=vol.Schema({
            vol.Required("scene"): cv.string,
        }),
    )
    
    # === Create Scene ===
    async def handle_create_scene(call: ServiceCall) -> None:
        """Create a new scene."""
        name = call.data["name"]
        actions_data = call.data["actions"]
        room_name = call.data.get("room")
        icon = call.data.get("icon", "mdi:play")
        
        # Find room if specified
        room_id = None
        if room_name:
            room = database.get_room_by_name(room_name)
            if room:
                room_id = room.id
        
        # Build actions
        actions = []
        for action_data in actions_data:
            device = database.get_device_by_name(action_data["device"])
            if device:
                actions.append(SceneAction(
                    device_id=device.id,
                    command_name=action_data["command"],
                    delay_after=action_data.get("delay", 0.5),
                ))
        
        scene = database.add_scene(
            name=name,
            actions=actions,
            room_id=room_id,
            icon=icon,
        )
        
        await database.async_save()
        _LOGGER.info("Created scene: %s with %d actions", name, len(actions))
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_SCENE,
        handle_create_scene,
        schema=vol.Schema({
            vol.Required("name"): cv.string,
            vol.Required("actions"): vol.All(
                cv.ensure_list,
                [vol.Schema({
                    vol.Required("device"): cv.string,
                    vol.Required("command"): cv.string,
                    vol.Optional("delay", default=0.5): vol.Coerce(float),
                })]
            ),
            vol.Optional("room"): cv.string,
            vol.Optional("icon", default="mdi:play"): cv.string,
        }),
    )
    
    # === Add Room ===
    async def handle_add_room(call: ServiceCall) -> None:
        """Add a new room."""
        name = call.data["name"]
        icon = call.data.get("icon", "mdi:sofa")
        
        room = database.add_room(name=name, icon=icon)
        await database.async_save()
        _LOGGER.info("Added room: %s", name)
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_ROOM,
        handle_add_room,
        schema=vol.Schema({
            vol.Required("name"): cv.string,
            vol.Optional("icon", default="mdi:sofa"): cv.string,
        }),
    )
    
    # === Add Device ===
    async def handle_add_device(call: ServiceCall) -> None:
        """Add a new device."""
        name = call.data["name"]
        category = call.data.get("category", "other")
        brand = call.data.get("brand", "")
        model = call.data.get("model", "")
        room_name = call.data.get("room")
        
        # Find room
        room_id = None
        if room_name:
            room = database.get_room_by_name(room_name)
            if room:
                room_id = room.id
        
        device = database.add_device(
            name=name,
            category=DeviceCategory(category),
            brand=brand,
            model=model,
            room_id=room_id,
        )
        
        await database.async_save()
        _LOGGER.info("Added device: %s", name)
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_DEVICE,
        handle_add_device,
        schema=vol.Schema({
            vol.Required("name"): cv.string,
            vol.Optional("category", default="other"): vol.In([
                "tv", "receiver", "soundbar", "streaming", "cable_box",
                "antenna", "projector", "ac", "fan", "light", "blind",
                "gate", "garage", "other"
            ]),
            vol.Optional("brand"): cv.string,
            vol.Optional("model"): cv.string,
            vol.Optional("room"): cv.string,
        }),
    )
