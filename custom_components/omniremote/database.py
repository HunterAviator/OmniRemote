"""Database manager for OmniRemote."""
from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any

import broadlink
from broadlink.exceptions import BroadlinkException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    Blaster,
    Device,
    DeviceCategory,
    RemoteCode,
    RemoteProfile,
    Room,
    Scene,
    SceneAction,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .flipper_parser import FlipperParser

_LOGGER = logging.getLogger(__name__)


class RemoteDatabase:
    """Manage the database of rooms, devices, codes, and scenes."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the database."""
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        
        self.rooms: dict[str, Room] = {}
        self.devices: dict[str, Device] = {}
        self.scenes: dict[str, Scene] = {}
        self.blasters: dict[str, Blaster] = {}
        self.physical_remotes: dict[str, "PhysicalRemote"] = {}
        self.remote_bridges: dict[str, "RemoteBridge"] = {}
        self.remote_profiles: dict[str, RemoteProfile] = {}
        
        self._blaster_connections: dict[str, broadlink.Device] = {}
        self._lock = asyncio.Lock()

    async def async_load(self) -> None:
        """Load database from storage."""
        data = await self.store.async_load()
        
        if data:
            # Load rooms
            for room_data in data.get("rooms", {}).values():
                room = Room.from_dict(room_data)
                self.rooms[room.id] = room
            
            # Load devices
            for device_data in data.get("devices", {}).values():
                device = Device.from_dict(device_data)
                self.devices[device.id] = device
            
            # Load scenes
            for scene_data in data.get("scenes", {}).values():
                scene = Scene.from_dict(scene_data)
                self.scenes[scene.id] = scene
            
            # Load blasters
            for blaster_data in data.get("blasters", {}).values():
                blaster = Blaster.from_dict(blaster_data)
                self.blasters[blaster.id] = blaster
            
            # Load physical remotes
            for remote_data in data.get("physical_remotes", {}).values():
                try:
                    from .physical_remotes import PhysicalRemote
                    remote = PhysicalRemote.from_dict(remote_data)
                    self.physical_remotes[remote.id] = remote
                except Exception as e:
                    _LOGGER.warning("Failed to load remote %s: %s", remote_data.get("id", "unknown"), e)
            
            # Load remote bridges
            for bridge_data in data.get("remote_bridges", {}).values():
                try:
                    from .physical_remotes import RemoteBridge
                    bridge = RemoteBridge.from_dict(bridge_data)
                    self.remote_bridges[bridge.id] = bridge
                except Exception as e:
                    _LOGGER.warning("Failed to load bridge %s: %s", bridge_data.get("id", "unknown"), e)
            
            # Load remote profiles (custom remote layouts)
            for profile_data in data.get("remote_profiles", {}).values():
                profile = RemoteProfile.from_dict(profile_data)
                self.remote_profiles[profile.id] = profile
            
            _LOGGER.info(
                "Loaded database: %d rooms, %d devices, %d scenes, %d blasters, %d remotes, %d bridges, %d profiles",
                len(self.rooms),
                len(self.devices),
                len(self.scenes),
                len(self.blasters),
                len(self.physical_remotes),
                len(self.remote_bridges),
                len(self.remote_profiles),
            )

    async def async_save(self) -> None:
        """Save database to storage."""
        data = {
            "rooms": {r.id: r.to_dict() for r in self.rooms.values()},
            "devices": {d.id: d.to_dict() for d in self.devices.values()},
            "scenes": {s.id: s.to_dict() for s in self.scenes.values()},
            "blasters": {b.id: b.to_dict() for b in self.blasters.values()},
            "physical_remotes": {r.id: r.to_dict() for r in self.physical_remotes.values()},
            "remote_bridges": {b.id: b.to_dict() for b in self.remote_bridges.values()},
            "remote_profiles": {p.id: p.to_dict() for p in self.remote_profiles.values()},
        }
        await self.store.async_save(data)
        
        # Publish config to MQTT for Pi Hub sync
        await self._publish_config_to_mqtt(data)
    
    async def _publish_config_to_mqtt(self, data: dict) -> None:
        """Publish configuration to MQTT for Pi Hub standalone sync."""
        try:
            from homeassistant.components import mqtt
            import json
            
            if "mqtt" not in self.hass.config.components:
                return
            
            # Publish physical remotes config (retained so Pi Hubs get it on connect)
            await mqtt.async_publish(
                self.hass,
                "omniremote/config/physical_remotes",
                json.dumps({"remotes": data.get("physical_remotes", {})}),
                qos=1,
                retain=True
            )
            
            # Publish rooms config
            await mqtt.async_publish(
                self.hass,
                "omniremote/config/rooms",
                json.dumps({"rooms": data.get("rooms", {})}),
                qos=1,
                retain=True
            )
            
            # Publish devices config
            await mqtt.async_publish(
                self.hass,
                "omniremote/config/devices",
                json.dumps({"devices": data.get("devices", {})}),
                qos=1,
                retain=True
            )
            
            # Also publish full database sync (retained)
            await self._publish_full_database_sync()
            
            _LOGGER.debug("Published config to MQTT for Pi Hub sync")
        except Exception as e:
            _LOGGER.debug("Could not publish config to MQTT: %s", e)
    
    async def _publish_full_database_sync(self) -> None:
        """Publish full database to MQTT for Pi Hub sync - HA is source of truth."""
        try:
            from homeassistant.components import mqtt
            import json
            from datetime import datetime
            
            if "mqtt" not in self.hass.config.components:
                return
            
            # Build full database payload
            sync_payload = {
                "source": "home_assistant",
                "timestamp": datetime.now().isoformat(),
                "rooms": {r.id: r.to_dict() for r in self.rooms.values()},
                "devices": {d.id: d.to_dict() for d in self.devices.values()},
                "scenes": {s.id: s.to_dict() for s in self.scenes.values()},
                "physical_remotes": self._data.get("physical_remotes", {}),
                "remote_profiles": self._data.get("remote_profiles", []),
                "remote_bridges": self._data.get("remote_bridges", {}),
            }
            
            # Publish retained so Pi Hubs get it immediately on connect
            await mqtt.async_publish(
                self.hass,
                "omniremote/sync/database",
                json.dumps(sync_payload),
                qos=1,
                retain=True
            )
            
            _LOGGER.info("Published full database sync to MQTT (%d rooms, %d devices)", 
                        len(sync_payload["rooms"]), len(sync_payload["devices"]))
        except Exception as e:
            _LOGGER.warning("Could not publish full database sync: %s", e)

    # === Room Management ===

    def add_room(self, name: str, icon: str = "mdi:sofa") -> Room:
        """Add a new room."""
        room = Room(name=name, icon=icon)
        self.rooms[room.id] = room
        return room

    def get_room(self, room_id: str) -> Room | None:
        """Get a room by ID."""
        return self.rooms.get(room_id)

    def get_room_by_name(self, name: str) -> Room | None:
        """Get a room by name."""
        for room in self.rooms.values():
            if room.name.lower() == name.lower():
                return room
        return None

    def delete_room(self, room_id: str) -> bool:
        """Delete a room."""
        if room_id in self.rooms:
            # Remove room reference from devices
            for device in self.devices.values():
                if device.room_id == room_id:
                    device.room_id = None
            
            del self.rooms[room_id]
            return True
        return False

    # === Device Management ===

    def add_device(
        self,
        name: str,
        category: DeviceCategory = DeviceCategory.OTHER,
        brand: str = "",
        model: str = "",
        room_id: str | None = None,
    ) -> Device:
        """Add a new device."""
        device = Device(
            name=name,
            category=category,
            brand=brand,
            model=model,
            room_id=room_id,
        )
        self.devices[device.id] = device
        
        # Add to room's device list
        if room_id and room_id in self.rooms:
            self.rooms[room_id].device_ids.append(device.id)
        
        return device

    def get_device(self, device_id: str) -> Device | None:
        """Get a device by ID."""
        return self.devices.get(device_id)

    def get_device_by_name(self, name: str) -> Device | None:
        """Get a device by name."""
        for device in self.devices.values():
            if device.name.lower() == name.lower():
                return device
        return None

    def get_devices_in_room(self, room_id: str) -> list[Device]:
        """Get all devices in a room."""
        return [d for d in self.devices.values() if d.room_id == room_id]

    def delete_device(self, device_id: str) -> bool:
        """Delete a device."""
        if device_id in self.devices:
            device = self.devices[device_id]
            
            # Remove from room
            if device.room_id and device.room_id in self.rooms:
                room = self.rooms[device.room_id]
                if device_id in room.device_ids:
                    room.device_ids.remove(device_id)
            
            del self.devices[device_id]
            return True
        return False

    def add_command_to_device(
        self,
        device_id: str,
        command_name: str,
        code: RemoteCode,
    ) -> bool:
        """Add a command to a device."""
        if device_id not in self.devices:
            return False
        
        self.devices[device_id].commands[command_name] = code
        return True

    # === Scene Management ===

    def add_scene(
        self,
        name: str,
        room_id: str | None = None,
        icon: str = "mdi:play",
        blaster_id: str | None = None,
        on_actions: list[SceneAction] | None = None,
        off_actions: list[SceneAction] | None = None,
        controlled_device_ids: list[str] | None = None,
        controlled_entity_ids: list[str] | None = None,
        actions: list[SceneAction] | None = None,  # Legacy
    ) -> Scene:
        """Add a new scene."""
        scene = Scene(
            name=name,
            icon=icon,
            room_id=room_id,
            blaster_id=blaster_id,
            on_actions=on_actions or [],
            off_actions=off_actions or [],
            controlled_device_ids=controlled_device_ids or [],
            controlled_entity_ids=controlled_entity_ids or [],
            actions=actions or [],
        )
        self.scenes[scene.id] = scene
        return scene

    def update_scene(self, scene_id: str, **kwargs) -> Scene | None:
        """Update a scene."""
        scene = self.scenes.get(scene_id)
        if not scene:
            return None
        
        for key, value in kwargs.items():
            if hasattr(scene, key):
                setattr(scene, key, value)
        
        return scene

    def get_scene(self, scene_id: str) -> Scene | None:
        """Get a scene by ID."""
        return self.scenes.get(scene_id)

    def get_scene_by_name(self, name: str) -> Scene | None:
        """Get a scene by name."""
        for scene in self.scenes.values():
            if scene.name.lower() == name.lower():
                return scene
        return None

    def delete_scene(self, scene_id: str) -> bool:
        """Delete a scene."""
        if scene_id in self.scenes:
            del self.scenes[scene_id]
            return True
        return False

    def get_active_scenes(self) -> list[Scene]:
        """Get all currently active scenes."""
        return [s for s in self.scenes.values() if s.is_active]

    def get_devices_in_use(self) -> set[str]:
        """Get device IDs currently in use by active scenes."""
        device_ids = set()
        for scene in self.get_active_scenes():
            device_ids.update(scene.controlled_device_ids)
        return device_ids

    def get_entities_in_use(self) -> set[str]:
        """Get entity IDs currently in use by active scenes."""
        entity_ids = set()
        for scene in self.get_active_scenes():
            entity_ids.update(scene.controlled_entity_ids)
        return entity_ids

    async def async_activate_scene(self, scene_id: str) -> bool:
        """Activate a scene, running its ON sequence with smart device handling."""
        scene = self.get_scene(scene_id)
        if not scene:
            _LOGGER.error("Scene not found: %s", scene_id)
            return False
        
        _LOGGER.info("Activating scene: %s", scene.name)
        
        # Get devices already in use by other active scenes
        devices_in_use = self.get_devices_in_use()
        entities_in_use = self.get_entities_in_use()
        
        # Deactivate other scenes in the same room that share devices
        if scene.room_id:
            for other_scene in self.scenes.values():
                if (other_scene.id != scene_id and 
                    other_scene.room_id == scene.room_id and 
                    other_scene.is_active):
                    # Check if they share devices
                    shared_devices = set(scene.controlled_device_ids) & set(other_scene.controlled_device_ids)
                    shared_entities = set(scene.controlled_entity_ids) & set(other_scene.controlled_entity_ids)
                    
                    if shared_devices or shared_entities:
                        _LOGGER.info("Scene %s shares devices with %s, marking as inactive but not running OFF sequence",
                                    scene.name, other_scene.name)
                        other_scene.is_active = False
        
        # Run ON actions
        for action in sorted(scene.on_actions, key=lambda a: a.order):
            try:
                # Check if we should skip this action
                if action.skip_if_on:
                    if action.device_id and action.device_id in devices_in_use:
                        _LOGGER.info("Skipping action for device %s - already on from another scene", action.device_id)
                        continue
                    if action.entity_id and action.entity_id in entities_in_use:
                        _LOGGER.info("Skipping action for entity %s - already on from another scene", action.entity_id)
                        continue
                
                await self._execute_action(action, scene.blaster_id)
                
                # Wait after action
                if action.delay_seconds > 0:
                    await asyncio.sleep(action.delay_seconds)
                    
            except Exception as ex:
                _LOGGER.error("Error executing action in scene %s: %s", scene.name, ex)
        
        scene.is_active = True
        await self.async_save()
        return True

    async def async_deactivate_scene(self, scene_id: str) -> bool:
        """Deactivate a scene, running its OFF sequence."""
        scene = self.get_scene(scene_id)
        if not scene:
            _LOGGER.error("Scene not found: %s", scene_id)
            return False
        
        if not scene.is_active:
            _LOGGER.info("Scene %s is not active", scene.name)
            return True
        
        _LOGGER.info("Deactivating scene: %s", scene.name)
        
        # Check which devices are still needed by other active scenes
        other_active_scenes = [s for s in self.get_active_scenes() if s.id != scene_id]
        devices_still_needed = set()
        entities_still_needed = set()
        
        for other_scene in other_active_scenes:
            devices_still_needed.update(other_scene.controlled_device_ids)
            entities_still_needed.update(other_scene.controlled_entity_ids)
        
        # Run OFF actions, but skip devices still in use
        for action in sorted(scene.off_actions, key=lambda a: a.order):
            try:
                # Skip if device/entity is still needed by another scene
                if action.device_id and action.device_id in devices_still_needed:
                    _LOGGER.info("Skipping OFF for device %s - still needed by another scene", action.device_id)
                    continue
                if action.entity_id and action.entity_id in entities_still_needed:
                    _LOGGER.info("Skipping OFF for entity %s - still needed by another scene", action.entity_id)
                    continue
                
                await self._execute_action(action, scene.blaster_id)
                
                if action.delay_seconds > 0:
                    await asyncio.sleep(action.delay_seconds)
                    
            except Exception as ex:
                _LOGGER.error("Error executing OFF action in scene %s: %s", scene.name, ex)
        
        scene.is_active = False
        await self.async_save()
        return True

    async def async_toggle_scene(self, scene_id: str) -> bool:
        """Toggle a scene on/off."""
        scene = self.get_scene(scene_id)
        if not scene:
            return False
        
        if scene.is_active:
            return await self.async_deactivate_scene(scene_id)
        else:
            return await self.async_activate_scene(scene_id)

    async def _execute_action(self, action: SceneAction, default_blaster_id: str | None = None) -> bool:
        """Execute a single scene action."""
        _LOGGER.debug("Executing action: type=%s", action.action_type)
        
        if action.action_type == "delay":
            # Just a delay - handled by caller
            return True
        
        elif action.action_type == "ir_command":
            # Send IR command via blaster
            device = self.devices.get(action.device_id) if action.device_id else None
            if not device:
                _LOGGER.warning("Device not found for action: %s", action.device_id)
                return False
            
            code = None
            for c in device.codes:
                if c.name == action.command_name:
                    code = c
                    break
            
            if not code:
                _LOGGER.warning("Command not found: %s for device %s", action.command_name, device.name)
                return False
            
            blaster_id = action.blaster_id or default_blaster_id
            return await self.async_send_code(code, blaster_id)
        
        elif action.action_type == "ha_service":
            # Call Home Assistant service
            if not action.ha_service or not action.entity_id:
                _LOGGER.warning("Missing ha_service or entity_id for HA action")
                return False
            
            try:
                domain, service = action.ha_service.split(".", 1)
                service_data = dict(action.service_data) if action.service_data else {}
                service_data["entity_id"] = action.entity_id
                
                await self.hass.services.async_call(domain, service, service_data)
                _LOGGER.info("Called HA service: %s.%s for %s", domain, service, action.entity_id)
                return True
            except Exception as ex:
                _LOGGER.error("Failed to call HA service: %s", ex)
                return False
        
        elif action.action_type == "network_command":
            # Send network command (Roku, Fire TV, etc.)
            from .network_devices import get_network_device_manager
            
            manager = get_network_device_manager(self.hass)
            if not manager:
                _LOGGER.warning("Network device manager not available")
                return False
            
            try:
                return await manager.async_send_command(
                    action.network_device_id,
                    action.network_command
                )
            except Exception as ex:
                _LOGGER.error("Failed to send network command: %s", ex)
                return False
        
        else:
            _LOGGER.warning("Unknown action type: %s", action.action_type)
            return False

    # === Blaster Management ===

    async def async_discover_blasters(self) -> list[Blaster]:
        """Discover Broadlink devices on the network."""
        discovered = []
        
        try:
            import socket
            
            # Try to get local IP for better discovery
            local_ip = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                _LOGGER.info("Discovering Broadlink devices from local IP: %s", local_ip)
            except Exception as e:
                _LOGGER.warning("Could not determine local IP: %s", e)
            
            # Method 1: Standard discovery with local IP
            _LOGGER.info("Starting Broadlink discovery (timeout=10s)...")
            try:
                if local_ip:
                    devices = await self.hass.async_add_executor_job(
                        lambda: broadlink.discover(timeout=10, local_ip_address=local_ip)
                    )
                else:
                    devices = await self.hass.async_add_executor_job(
                        lambda: broadlink.discover(timeout=10)
                    )
                _LOGGER.info("Discovery found %d devices", len(devices))
            except Exception as e:
                _LOGGER.error("Discovery failed: %s", e)
                devices = []
            
            # Method 2: If no devices found, try without local_ip
            if not devices and local_ip:
                _LOGGER.info("Retrying discovery without local_ip restriction...")
                try:
                    devices = await self.hass.async_add_executor_job(
                        lambda: broadlink.discover(timeout=10)
                    )
                    _LOGGER.info("Second discovery found %d devices", len(devices))
                except Exception as e:
                    _LOGGER.error("Second discovery failed: %s", e)
            
            for device in devices:
                try:
                    _LOGGER.info("Found device: %s at %s (type: 0x%x)", 
                                 device.model, device.host[0], device.devtype)
                    
                    await self.hass.async_add_executor_job(device.auth)
                    _LOGGER.info("Successfully authenticated with %s", device.host[0])
                    
                    mac = ":".join(f"{b:02x}" for b in device.mac)
                    
                    # Check if already exists
                    existing = None
                    for b in self.blasters.values():
                        if b.mac == mac:
                            existing = b
                            break
                    
                    if existing:
                        existing.host = device.host[0]
                        discovered.append(existing)
                        _LOGGER.info("Updated existing blaster: %s", existing.name)
                    else:
                        blaster = Blaster(
                            name=f"{device.model} ({device.host[0]})",
                            host=device.host[0],
                            mac=mac,
                            device_type=hex(device.devtype),
                        )
                        self.blasters[blaster.id] = blaster
                        discovered.append(blaster)
                        _LOGGER.info("Added new blaster: %s (MAC: %s)", blaster.name, mac)
                    
                    self._blaster_connections[mac] = device
                    
                except Exception as ex:
                    _LOGGER.warning("Error authenticating device %s: %s", device.host, ex)
            
        except Exception as ex:
            _LOGGER.error("Error in discovery process: %s", ex)
        
        _LOGGER.info("Discovery complete. Found %d blaster(s)", len(discovered))
        return discovered
    
    async def async_discover_blasters_mdns(self) -> list[Blaster]:
        """Discover Broadlink devices via mDNS (works across VLANs if mDNS is relayed)."""
        discovered = []
        
        try:
            from homeassistant.components import zeroconf
            
            # Get zeroconf instance
            zc = await zeroconf.async_get_instance(self.hass)
            
            # Service types for Broadlink devices
            service_types = ["_broadlink._tcp.local."]
            
            from zeroconf import ServiceBrowser, ServiceListener
            import socket
            
            found_hosts = []
            
            class BroadlinkListener(ServiceListener):
                def add_service(self, zc, service_type, name):
                    info = zc.get_service_info(service_type, name)
                    if info and info.addresses:
                        ip = socket.inet_ntoa(info.addresses[0])
                        found_hosts.append((ip, name))
                        _LOGGER.info("mDNS found Broadlink: %s at %s", name, ip)
                
                def remove_service(self, zc, service_type, name):
                    pass
                
                def update_service(self, zc, service_type, name):
                    pass
            
            listener = BroadlinkListener()
            browsers = []
            
            for svc in service_types:
                try:
                    browser = ServiceBrowser(zc.zeroconf, svc, listener)
                    browsers.append(browser)
                except Exception as e:
                    _LOGGER.debug("Could not browse %s: %s", svc, e)
            
            # Wait for discovery
            await asyncio.sleep(5)
            
            # Cancel browsers
            for browser in browsers:
                try:
                    browser.cancel()
                except:
                    pass
            
            _LOGGER.info("mDNS discovery found %d hosts", len(found_hosts))
            
            # Connect to each found host
            for host, mdns_name in found_hosts:
                try:
                    blaster = await self.async_add_blaster_by_ip(host, mdns_name.split('.')[0])
                    if blaster:
                        discovered.append(blaster)
                except Exception as e:
                    _LOGGER.warning("Failed to connect to mDNS host %s: %s", host, e)
            
        except ImportError:
            _LOGGER.warning("Zeroconf not available for mDNS discovery")
        except Exception as ex:
            _LOGGER.error("mDNS discovery error: %s", ex)
        
        return discovered
    
    async def async_add_blaster_by_ip(self, host: str, name: str = None) -> Blaster | None:
        """Add a blaster by IP address (manual add)."""
        try:
            _LOGGER.info("Attempting to connect to Broadlink device at %s", host)
            
            # Try hello first
            device = await self.hass.async_add_executor_job(
                lambda: broadlink.hello(host)
            )
            
            _LOGGER.info("Found device: %s (type: 0x%x)", device.model, device.devtype)
            
            # Authenticate
            await self.hass.async_add_executor_job(device.auth)
            _LOGGER.info("Successfully authenticated with %s", host)
            
            mac = ":".join(f"{b:02x}" for b in device.mac)
            
            # Check if already exists
            for b in self.blasters.values():
                if b.mac == mac:
                    _LOGGER.info("Device already registered: %s", b.name)
                    b.host = host  # Update IP
                    self._blaster_connections[mac] = device
                    return b
            
            # Create new blaster
            blaster = Blaster(
                name=name or f"{device.model} ({host})",
                host=host,
                mac=mac,
                device_type=hex(device.devtype),
            )
            self.blasters[blaster.id] = blaster
            self._blaster_connections[mac] = device
            
            _LOGGER.info("Added blaster: %s (MAC: %s)", blaster.name, mac)
            return blaster
            
        except Exception as ex:
            _LOGGER.error("Failed to add blaster at %s: %s", host, ex)
            raise

    async def async_connect_blaster(self, blaster_id: str) -> bool:
        """Connect to a specific blaster."""
        if blaster_id not in self.blasters:
            return False
        
        blaster = self.blasters[blaster_id]
        
        # Check if already connected
        if blaster.mac in self._blaster_connections:
            return True
        
        try:
            device = await self.hass.async_add_executor_job(
                broadlink.hello, blaster.host
            )
            
            if device:
                await self.hass.async_add_executor_job(device.auth)
                self._blaster_connections[blaster.mac] = device
                return True
                
        except Exception as ex:
            _LOGGER.error("Error connecting to blaster: %s", ex)
        
        return False

    def get_blaster_for_room(self, room_id: str) -> Blaster | None:
        """Get the blaster assigned to a room."""
        for blaster in self.blasters.values():
            if blaster.room_id == room_id:
                return blaster
        return None

    def get_any_blaster(self) -> tuple[Blaster, broadlink.Device] | None:
        """Get any available connected blaster."""
        for blaster in self.blasters.values():
            if blaster.mac in self._blaster_connections:
                return (blaster, self._blaster_connections[blaster.mac])
        return None

    # === Code Operations ===

    async def async_send_code(
        self,
        code: RemoteCode,
        blaster_id: str | None = None,
    ) -> bool:
        """Send a code using a blaster."""
        from .ir_encoder import _log_debug
        
        debug_entry = {
            "action": "send_code",
            "code_source": code.source if hasattr(code, 'source') else "unknown",
            "blaster_id": blaster_id,
            "status": "started",
        }
        
        async with self._lock:
            # Find blaster to use
            if blaster_id and blaster_id in self.blasters:
                blaster = self.blasters[blaster_id]
                debug_entry["blaster_name"] = blaster.name
                debug_entry["blaster_mac"] = blaster.mac
                if blaster.mac not in self._blaster_connections:
                    await self.async_connect_blaster(blaster_id)
                device = self._blaster_connections.get(blaster.mac)
            else:
                result = self.get_any_blaster()
                if result:
                    blaster, device = result
                    debug_entry["blaster_name"] = blaster.name
                    debug_entry["blaster_mac"] = blaster.mac
                else:
                    debug_entry["status"] = "error"
                    debug_entry["error"] = "No blaster available"
                    _log_debug(debug_entry)
                    _LOGGER.error("No blaster available")
                    return False
            
            if not device:
                debug_entry["status"] = "error"
                debug_entry["error"] = "Blaster not connected"
                _log_debug(debug_entry)
                _LOGGER.error("Blaster not connected")
                return False
            
            # Get code to send
            if code.broadlink_code:
                code_bytes = base64.b64decode(code.broadlink_code)
                debug_entry["code_bytes"] = len(code_bytes)
                debug_entry["code_preview"] = code.broadlink_code[:50] + "..." if len(code.broadlink_code) > 50 else code.broadlink_code
            else:
                debug_entry["status"] = "error"
                debug_entry["error"] = "No Broadlink-compatible code available"
                _log_debug(debug_entry)
                _LOGGER.error("No Broadlink-compatible code available")
                return False
            
            try:
                _LOGGER.info(
                    "Sending IR code via %s (%s): %d bytes",
                    blaster.name, blaster.mac, len(code_bytes)
                )
                await self.hass.async_add_executor_job(
                    device.send_data, code_bytes
                )
                debug_entry["status"] = "success"
                _log_debug(debug_entry)
                return True
            except Exception as ex:
                debug_entry["status"] = "exception"
                debug_entry["error"] = str(ex)
                _log_debug(debug_entry)
                _LOGGER.error("Error sending code: %s", ex)
                return False

    async def async_send_catalog_code(
        self,
        ir_code: "IRCode",
        blaster_id: str | None = None,
    ) -> bool:
        """Send a catalog IRCode using a blaster."""
        from .ir_encoder import encode_ir_to_broadlink, _log_debug
        
        debug_entry = {
            "action": "send_catalog_code",
            "ir_code_name": getattr(ir_code, 'name', 'unknown'),
            "protocol": str(ir_code.protocol.value if hasattr(ir_code.protocol, 'value') else ir_code.protocol),
            "address": ir_code.address,
            "command": ir_code.command,
            "blaster_id": blaster_id,
            "status": "started",
        }
        
        # Convert IRCode to Broadlink format
        broadlink_b64 = encode_ir_to_broadlink(ir_code)
        if not broadlink_b64:
            debug_entry["status"] = "error"
            debug_entry["error"] = f"Could not encode IR code for protocol {ir_code.protocol}"
            _log_debug(debug_entry)
            _LOGGER.error("Could not encode IR code for protocol %s", ir_code.protocol)
            return False
        
        debug_entry["encoded_bytes"] = len(base64.b64decode(broadlink_b64))
        
        async with self._lock:
            # Find blaster to use
            if blaster_id and blaster_id in self.blasters:
                blaster = self.blasters[blaster_id]
                debug_entry["blaster_name"] = blaster.name
                debug_entry["blaster_mac"] = blaster.mac
                if blaster.mac not in self._blaster_connections:
                    await self.async_connect_blaster(blaster_id)
                device = self._blaster_connections.get(blaster.mac)
            else:
                result = self.get_any_blaster()
                if result:
                    blaster, device = result
                    debug_entry["blaster_name"] = blaster.name
                    debug_entry["blaster_mac"] = blaster.mac
                else:
                    debug_entry["status"] = "error"
                    debug_entry["error"] = "No blaster available"
                    _log_debug(debug_entry)
                    _LOGGER.error("No blaster available")
                    return False
            
            if not device:
                debug_entry["status"] = "error"
                debug_entry["error"] = "Blaster not connected"
                _log_debug(debug_entry)
                _LOGGER.error("Blaster not connected")
                return False
            
            try:
                code_bytes = base64.b64decode(broadlink_b64)
                _LOGGER.info(
                    "Sending catalog IR: %s (protocol=%s, addr=%s, cmd=%s) via %s - %d bytes",
                    getattr(ir_code, 'name', 'code'),
                    ir_code.protocol,
                    ir_code.address,
                    ir_code.command,
                    blaster.name,
                    len(code_bytes)
                )
                await self.hass.async_add_executor_job(
                    device.send_data, code_bytes
                )
                debug_entry["status"] = "success"
                _log_debug(debug_entry)
                return True
            except Exception as ex:
                debug_entry["status"] = "exception"
                debug_entry["error"] = str(ex)
                _log_debug(debug_entry)
                _LOGGER.error("Error sending catalog code: %s", ex)
                return False

    async def async_test_catalog_code(
        self,
        profile_id: str,
        command_name: str,
        blaster_id: str | None = None,
    ) -> dict:
        """Test a catalog code and return debug info."""
        from .catalog import get_profile
        from .ir_encoder import encode_ir_to_broadlink
        
        profile = get_profile(profile_id)
        if not profile:
            return {"success": False, "error": f"Profile not found: {profile_id}"}
        
        ir_code = profile.ir_codes.get(command_name)
        if not ir_code:
            return {"success": False, "error": f"Command not found: {command_name}"}
        
        # Get encoding info
        broadlink_b64 = encode_ir_to_broadlink(ir_code)
        if not broadlink_b64:
            return {
                "success": False, 
                "error": f"Could not encode protocol: {ir_code.protocol.value}",
                "protocol": ir_code.protocol.value,
                "address": ir_code.address,
                "command": ir_code.command,
            }
        
        # Try to send
        result = await self.async_send_catalog_code(ir_code, blaster_id)
        
        return {
            "success": result,
            "profile": profile_id,
            "command": command_name,
            "protocol": ir_code.protocol.value,
            "address": ir_code.address,
            "command_hex": ir_code.command,
            "broadlink_length": len(base64.b64decode(broadlink_b64)),
        }

    async def async_learn_code(
        self,
        blaster_id: str | None = None,
        timeout: int = 15,
    ) -> RemoteCode | None:
        """Learn a code from a remote."""
        async with self._lock:
            # Find blaster to use
            if blaster_id and blaster_id in self.blasters:
                blaster = self.blasters[blaster_id]
                if blaster.mac not in self._blaster_connections:
                    await self.async_connect_blaster(blaster_id)
                device = self._blaster_connections.get(blaster.mac)
            else:
                result = self.get_any_blaster()
                if result:
                    blaster, device = result
                else:
                    _LOGGER.error("No blaster available")
                    return None
            
            if not device:
                _LOGGER.error("Blaster not connected")
                return None
            
            try:
                # Enter learning mode
                await self.hass.async_add_executor_job(device.enter_learning)
                _LOGGER.info("Learning mode entered, press remote button...")
                
                # Wait for code
                code_bytes = None
                for _ in range(timeout):
                    await asyncio.sleep(1)
                    try:
                        code_bytes = await self.hass.async_add_executor_job(
                            device.check_data
                        )
                        if code_bytes:
                            break
                    except Exception:
                        pass
                
                if code_bytes:
                    code = RemoteCode(
                        source="learned",
                        broadlink_code=base64.b64encode(code_bytes).decode('ascii'),
                    )
                    return code
                else:
                    _LOGGER.warning("No code received within timeout")
                    return None
                    
            except Exception as ex:
                _LOGGER.error("Error learning code: %s", ex)
                return None

    async def async_run_scene(self, scene_id: str) -> bool:
        """Run a scene."""
        scene = self.scenes.get(scene_id)
        if not scene:
            _LOGGER.error("Scene not found: %s", scene_id)
            return False
        
        _LOGGER.info("Running scene: %s", scene.name)
        
        for action in scene.actions:
            device = self.devices.get(action.device_id)
            if not device:
                _LOGGER.warning("Device not found: %s", action.device_id)
                continue
            
            code = device.commands.get(action.command_name)
            if not code:
                _LOGGER.warning(
                    "Command not found: %s.%s",
                    device.name,
                    action.command_name,
                )
                continue
            
            # Send the code
            success = await self.async_send_code(code)
            if not success:
                _LOGGER.warning(
                    "Failed to send: %s.%s",
                    device.name,
                    action.command_name,
                )
            
            # Wait before next action
            if action.delay_after > 0:
                await asyncio.sleep(action.delay_after)
        
        return True

    # === Import/Export ===

    async def async_import_flipper(self, path: str) -> int:
        """Import devices from Flipper Zero files."""
        parser = FlipperParser()
        
        imported = await self.hass.async_add_executor_job(
            parser.parse_directory, path
        )
        
        # Merge imported devices
        for device in imported.values():
            # Check if device with same name exists
            existing = self.get_device_by_name(device.name)
            if existing:
                # Merge commands
                existing.commands.update(device.commands)
            else:
                self.devices[device.id] = device
        
        await self.async_save()
        
        total_commands = sum(len(d.commands) for d in imported.values())
        _LOGGER.info(
            "Imported %d devices with %d commands",
            len(imported),
            total_commands,
        )
        
        return len(imported)

    def export_to_flipper(self, output_dir: str) -> int:
        """Export devices to Flipper Zero files."""
        from .flipper_parser import generate_flipper_ir
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for device in self.devices.values():
            if not device.commands:
                continue
            
            # Generate IR file
            content = generate_flipper_ir(device)
            
            # Create filename
            filename = device.name.replace(" ", "_") + ".ir"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            count += 1
        
        _LOGGER.info("Exported %d devices to %s", count, output_dir)
        return count

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the database."""
        return {
            "rooms": len(self.rooms),
            "devices": len(self.devices),
            "scenes": len(self.scenes),
            "blasters": len(self.blasters),
            "total_commands": sum(len(d.commands) for d in self.devices.values()),
            "connected_blasters": len(self._blaster_connections),
        }


    # === Bluetooth Remote Storage ===
    async def async_load_bluetooth_remotes(self) -> list[dict]:
        """Load Bluetooth remote configurations."""
        store = Store(self.hass, 1, f"{DOMAIN}_bluetooth_remotes")
        data = await store.async_load()
        return data.get("remotes", []) if data else []
    
    async def async_save_bluetooth_remotes(self, remotes: list[dict]) -> None:
        """Save Bluetooth remote configurations."""
        store = Store(self.hass, 1, f"{DOMAIN}_bluetooth_remotes")
        await store.async_save({"remotes": remotes})
    
    # === Area Remote Storage ===
    async def async_load_area_remotes(self) -> dict:
        """Load area remote configurations."""
        store = Store(self.hass, 1, f"{DOMAIN}_area_remotes")
        data = await store.async_load()
        return data or {"remotes": [], "device_mappings": []}
    
    async def async_save_area_remotes(self, data: dict) -> None:
        """Save area remote configurations."""
        store = Store(self.hass, 1, f"{DOMAIN}_area_remotes")
        await store.async_save(data)
    
    def get_devices_by_area(self, area_id: str) -> list:
        """Get all devices in a specific area/room."""
        # Try to match by room name to area
        from homeassistant.helpers import area_registry as ar
        area_registry = ar.async_get(self.hass)
        area = area_registry.async_get_area(area_id)
        
        if not area:
            return []
        
        result = []
        for device in self.devices.values():
            if device.room_id:
                room = self.rooms.get(device.room_id)
                if room and room.name.lower() == area.name.lower():
                    result.append(device)
        
        return result
    
    def get_activity(self, activity_id: str):
        """Get an activity by ID."""
        return self.activities.get(activity_id) if hasattr(self, 'activities') else None
