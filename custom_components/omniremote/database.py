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
            
            _LOGGER.info(
                "Loaded database: %d rooms, %d devices, %d scenes, %d blasters",
                len(self.rooms),
                len(self.devices),
                len(self.scenes),
                len(self.blasters),
            )

    async def async_save(self) -> None:
        """Save database to storage."""
        data = {
            "rooms": {r.id: r.to_dict() for r in self.rooms.values()},
            "devices": {d.id: d.to_dict() for d in self.devices.values()},
            "scenes": {s.id: s.to_dict() for s in self.scenes.values()},
            "blasters": {b.id: b.to_dict() for b in self.blasters.values()},
        }
        await self.store.async_save(data)

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
        actions: list[SceneAction],
        room_id: str | None = None,
        icon: str = "mdi:play",
    ) -> Scene:
        """Add a new scene."""
        scene = Scene(
            name=name,
            icon=icon,
            room_id=room_id,
            actions=actions,
        )
        self.scenes[scene.id] = scene
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

    # === Blaster Management ===

    async def async_discover_blasters(self) -> list[Blaster]:
        """Discover Broadlink devices on the network."""
        discovered = []
        
        try:
            devices = await self.hass.async_add_executor_job(
                broadlink.discover, 5
            )
            
            for device in devices:
                try:
                    await self.hass.async_add_executor_job(device.auth)
                    
                    mac = ":".join(f"{b:02x}" for b in device.mac)
                    
                    # Check if already exists
                    existing = None
                    for b in self.blasters.values():
                        if b.mac == mac:
                            existing = b
                            break
                    
                    if existing:
                        # Update host in case it changed
                        existing.host = device.host[0]
                        discovered.append(existing)
                    else:
                        blaster = Blaster(
                            name=f"{device.model} ({device.host[0]})",
                            host=device.host[0],
                            mac=mac,
                            device_type=hex(device.devtype),
                        )
                        self.blasters[blaster.id] = blaster
                        discovered.append(blaster)
                    
                    # Store connection
                    self._blaster_connections[mac] = device
                    
                except Exception as ex:
                    _LOGGER.warning("Error authenticating device: %s", ex)
            
        except Exception as ex:
            _LOGGER.error("Error discovering devices: %s", ex)
        
        return discovered

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
                    return False
            
            if not device:
                _LOGGER.error("Blaster not connected")
                return False
            
            # Get code to send
            if code.broadlink_code:
                code_bytes = base64.b64decode(code.broadlink_code)
            else:
                _LOGGER.error("No Broadlink-compatible code available")
                return False
            
            try:
                await self.hass.async_add_executor_job(
                    device.send_data, code_bytes
                )
                return True
            except Exception as ex:
                _LOGGER.error("Error sending code: %s", ex)
                return False

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
