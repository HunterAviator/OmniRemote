"""Bluetooth Remote Support for OmniRemote.

Allows pairing physical Bluetooth remotes and mapping their buttons
to OmniRemote commands. Supports area-based remote registration.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Common Bluetooth HID usage codes for remote buttons
HID_USAGE_CODES = {
    # Consumer Control (0x0C)
    0x30: "power",
    0x40: "menu",
    0x41: "menu_pick",
    0x42: "menu_up",
    0x43: "menu_down",
    0x44: "menu_left",
    0x45: "menu_right",
    0x46: "menu_escape",
    0x9C: "channel_up",
    0x9D: "channel_down",
    0xB0: "play",
    0xB1: "pause",
    0xB2: "record",
    0xB3: "fast_forward",
    0xB4: "rewind",
    0xB5: "scan_next",
    0xB6: "scan_previous",
    0xB7: "stop",
    0xCD: "play_pause",
    0xE2: "mute",
    0xE9: "volume_up",
    0xEA: "volume_down",
    0x221: "search",
    0x223: "home",
    0x224: "back",
    
    # Keyboard codes (0x07)
    0x28: "ok",  # Enter
    0x29: "back",  # Escape
    0x4F: "right",
    0x50: "left",
    0x51: "down",
    0x52: "up",
    
    # Number keys
    0x1E: "num_1",
    0x1F: "num_2",
    0x20: "num_3",
    0x21: "num_4",
    0x22: "num_5",
    0x23: "num_6",
    0x24: "num_7",
    0x25: "num_8",
    0x26: "num_9",
    0x27: "num_0",
}

# Known Bluetooth remote device signatures
KNOWN_REMOTES = {
    "Amazon Fire TV Remote": {
        "manufacturer": "Amazon",
        "service_uuids": ["00001812-0000-1000-8000-00805f9b34fb"],  # HID
        "default_mapping": {
            "home": "home",
            "back": "back",
            "menu": "menu",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "ok": "ok",
            "play_pause": "play_pause",
            "rewind": "rewind",
            "fast_forward": "fast_forward",
            "volume_up": "volume_up",
            "volume_down": "volume_down",
            "mute": "mute",
        }
    },
    "Roku Remote": {
        "manufacturer": "Roku",
        "name_patterns": ["Roku", "RC"],
        "default_mapping": {
            "home": "home",
            "back": "back",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "ok": "ok",
            "play_pause": "play_pause",
            "rewind": "rewind",
            "fast_forward": "fast_forward",
            "power": "power",
            "volume_up": "volume_up",
            "volume_down": "volume_down",
            "mute": "mute",
        }
    },
    "Apple TV Remote": {
        "manufacturer": "Apple",
        "name_patterns": ["Apple TV", "Siri Remote"],
        "default_mapping": {
            "menu": "back",
            "home": "home",
            "play_pause": "play_pause",
            "volume_up": "volume_up",
            "volume_down": "volume_down",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "ok": "ok",
        }
    },
    "Generic HID Remote": {
        "service_uuids": ["00001812-0000-1000-8000-00805f9b34fb"],
        "default_mapping": {
            "power": "power",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "ok": "ok",
            "back": "back",
            "home": "home",
            "volume_up": "volume_up",
            "volume_down": "volume_down",
            "mute": "mute",
        }
    },
}


class RemoteConnectionState(Enum):
    """Bluetooth remote connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    PAIRING = "pairing"
    ERROR = "error"


@dataclass
class ButtonMapping:
    """Maps a physical button to an OmniRemote command."""
    hid_code: int
    command: str
    device_id: str | None = None  # Specific device, or None for area default
    hold_command: str | None = None  # Command when held
    double_tap_command: str | None = None
    
    def to_dict(self) -> dict:
        return {
            "hid_code": self.hid_code,
            "command": self.command,
            "device_id": self.device_id,
            "hold_command": self.hold_command,
            "double_tap_command": self.double_tap_command,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ButtonMapping":
        return cls(
            hid_code=data["hid_code"],
            command=data["command"],
            device_id=data.get("device_id"),
            hold_command=data.get("hold_command"),
            double_tap_command=data.get("double_tap_command"),
        )


@dataclass
class BluetoothRemote:
    """Represents a registered Bluetooth remote."""
    id: str
    name: str
    address: str
    remote_type: str
    area_id: str | None = None
    device_id: str | None = None  # Default target device
    button_mappings: dict[int, ButtonMapping] = field(default_factory=dict)
    state: RemoteConnectionState = RemoteConnectionState.DISCONNECTED
    battery_level: int | None = None
    last_seen: float | None = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "remote_type": self.remote_type,
            "area_id": self.area_id,
            "device_id": self.device_id,
            "button_mappings": {
                str(k): v.to_dict() for k, v in self.button_mappings.items()
            },
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BluetoothRemote":
        mappings = {}
        for k, v in data.get("button_mappings", {}).items():
            mappings[int(k)] = ButtonMapping.from_dict(v)
        
        return cls(
            id=data["id"],
            name=data["name"],
            address=data["address"],
            remote_type=data.get("remote_type", "Generic HID Remote"),
            area_id=data.get("area_id"),
            device_id=data.get("device_id"),
            button_mappings=mappings,
        )


class BluetoothRemoteManager:
    """Manages Bluetooth remote connections and button mappings."""
    
    def __init__(self, hass: HomeAssistant, database) -> None:
        self.hass = hass
        self.database = database
        self._remotes: dict[str, BluetoothRemote] = {}
        self._discovery_callback: Callable | None = None
        self._button_callbacks: list[Callable] = []
        self._scan_cancel: Callable | None = None
        self._learning_mode: bool = False
        self._learning_callback: Callable | None = None
        
    async def async_setup(self) -> None:
        """Set up the Bluetooth remote manager."""
        # Load saved remotes
        await self._async_load_remotes()
        
        # Register Bluetooth callback for HID devices
        bluetooth.async_register_callback(
            self.hass,
            self._async_bluetooth_callback,
            bluetooth.BluetoothCallbackMatcher(
                service_uuid="00001812-0000-1000-8000-00805f9b34fb"
            ),
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
        
        _LOGGER.info("Bluetooth remote manager initialized with %d remotes", len(self._remotes))
    
    async def _async_load_remotes(self) -> None:
        """Load saved remotes from database."""
        data = await self.database.async_load_bluetooth_remotes()
        for remote_data in data:
            remote = BluetoothRemote.from_dict(remote_data)
            self._remotes[remote.id] = remote
    
    async def async_save_remotes(self) -> None:
        """Save remotes to database."""
        data = [r.to_dict() for r in self._remotes.values()]
        await self.database.async_save_bluetooth_remotes(data)
    
    @callback
    def _async_bluetooth_callback(
        self,
        service_info: BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        """Handle Bluetooth device updates."""
        address = service_info.address
        
        # Check if this is a registered remote
        for remote in self._remotes.values():
            if remote.address == address:
                if change == bluetooth.BluetoothChange.ADVERTISEMENT:
                    remote.state = RemoteConnectionState.CONNECTED
                    remote.last_seen = service_info.time
                    
                    # Fire state change event
                    self.hass.bus.async_fire(
                        f"{DOMAIN}_bt_remote_state",
                        {"remote_id": remote.id, "state": remote.state.value}
                    )
                return
        
        # New device discovered during scan
        if self._discovery_callback:
            self._discovery_callback(service_info)
    
    async def async_start_discovery(
        self,
        callback: Callable[[BluetoothServiceInfoBleak], None],
        timeout: int = 30,
    ) -> None:
        """Start scanning for Bluetooth remotes."""
        self._discovery_callback = callback
        
        # Cancel after timeout
        async def cancel_discovery():
            await asyncio.sleep(timeout)
            self._discovery_callback = None
        
        self.hass.async_create_task(cancel_discovery())
        
        _LOGGER.info("Started Bluetooth remote discovery for %d seconds", timeout)
    
    def stop_discovery(self) -> None:
        """Stop Bluetooth discovery."""
        self._discovery_callback = None
    
    async def async_register_remote(
        self,
        address: str,
        name: str,
        remote_type: str = "Generic HID Remote",
        area_id: str | None = None,
        device_id: str | None = None,
    ) -> BluetoothRemote:
        """Register a new Bluetooth remote."""
        import uuid
        
        remote_id = str(uuid.uuid4())[:8]
        
        # Get default mappings for this remote type
        default_mappings = {}
        if remote_type in KNOWN_REMOTES:
            remote_info = KNOWN_REMOTES[remote_type]
            for btn_name, cmd_name in remote_info.get("default_mapping", {}).items():
                # Find HID code for this button
                for code, name in HID_USAGE_CODES.items():
                    if name == btn_name:
                        default_mappings[code] = ButtonMapping(
                            hid_code=code,
                            command=cmd_name,
                            device_id=device_id,
                        )
                        break
        
        remote = BluetoothRemote(
            id=remote_id,
            name=name,
            address=address,
            remote_type=remote_type,
            area_id=area_id,
            device_id=device_id,
            button_mappings=default_mappings,
        )
        
        self._remotes[remote_id] = remote
        await self.async_save_remotes()
        
        _LOGGER.info("Registered Bluetooth remote: %s (%s) in area %s", name, address, area_id)
        
        return remote
    
    async def async_unregister_remote(self, remote_id: str) -> bool:
        """Unregister a Bluetooth remote."""
        if remote_id not in self._remotes:
            return False
        
        del self._remotes[remote_id]
        await self.async_save_remotes()
        
        return True
    
    def get_remote(self, remote_id: str) -> BluetoothRemote | None:
        """Get a remote by ID."""
        return self._remotes.get(remote_id)
    
    def get_remotes_by_area(self, area_id: str) -> list[BluetoothRemote]:
        """Get all remotes in a specific area."""
        return [r for r in self._remotes.values() if r.area_id == area_id]
    
    def list_remotes(self) -> list[BluetoothRemote]:
        """List all registered remotes."""
        return list(self._remotes.values())
    
    async def async_update_mapping(
        self,
        remote_id: str,
        hid_code: int,
        command: str,
        device_id: str | None = None,
        hold_command: str | None = None,
        double_tap_command: str | None = None,
    ) -> bool:
        """Update a button mapping for a remote."""
        remote = self._remotes.get(remote_id)
        if not remote:
            return False
        
        remote.button_mappings[hid_code] = ButtonMapping(
            hid_code=hid_code,
            command=command,
            device_id=device_id or remote.device_id,
            hold_command=hold_command,
            double_tap_command=double_tap_command,
        )
        
        await self.async_save_remotes()
        return True
    
    async def async_set_remote_area(self, remote_id: str, area_id: str | None) -> bool:
        """Set the area for a remote."""
        remote = self._remotes.get(remote_id)
        if not remote:
            return False
        
        remote.area_id = area_id
        await self.async_save_remotes()
        
        _LOGGER.info("Set remote %s to area %s", remote_id, area_id)
        return True
    
    async def async_set_remote_device(self, remote_id: str, device_id: str | None) -> bool:
        """Set the default target device for a remote."""
        remote = self._remotes.get(remote_id)
        if not remote:
            return False
        
        remote.device_id = device_id
        await self.async_save_remotes()
        
        return True
    
    def start_learning_mode(self, callback: Callable[[int, str], None]) -> None:
        """Start learning mode to capture button presses."""
        self._learning_mode = True
        self._learning_callback = callback
        _LOGGER.info("Started button learning mode")
    
    def stop_learning_mode(self) -> None:
        """Stop learning mode."""
        self._learning_mode = False
        self._learning_callback = None
        _LOGGER.info("Stopped button learning mode")
    
    async def async_handle_button_press(
        self,
        remote_id: str,
        hid_code: int,
        is_held: bool = False,
        is_double_tap: bool = False,
    ) -> None:
        """Handle a button press from a Bluetooth remote."""
        remote = self._remotes.get(remote_id)
        if not remote:
            _LOGGER.warning("Unknown remote: %s", remote_id)
            return
        
        # Learning mode - just report the button
        if self._learning_mode and self._learning_callback:
            button_name = HID_USAGE_CODES.get(hid_code, f"unknown_{hid_code}")
            self._learning_callback(hid_code, button_name)
            return
        
        # Find mapping
        mapping = remote.button_mappings.get(hid_code)
        if not mapping:
            _LOGGER.debug("No mapping for HID code %d on remote %s", hid_code, remote_id)
            return
        
        # Determine command based on press type
        if is_double_tap and mapping.double_tap_command:
            command = mapping.double_tap_command
        elif is_held and mapping.hold_command:
            command = mapping.hold_command
        else:
            command = mapping.command
        
        # Determine target device
        device_id = mapping.device_id or remote.device_id
        
        if not device_id:
            # Try to find device in same area
            if remote.area_id:
                area_devices = self.database.get_devices_by_area(remote.area_id)
                if area_devices:
                    device_id = area_devices[0].id
        
        if not device_id:
            _LOGGER.warning("No target device for remote %s button %s", remote_id, command)
            return
        
        # Send the command
        device = self.database.get_device(device_id)
        if device:
            code = device.commands.get(command)
            if code:
                await self.database.async_send_code(code)
                _LOGGER.debug("Sent command %s to device %s from BT remote", command, device.name)
                
                # Fire event
                self.hass.bus.async_fire(
                    f"{DOMAIN}_bt_button_press",
                    {
                        "remote_id": remote_id,
                        "remote_name": remote.name,
                        "button": command,
                        "device": device.name,
                        "area": remote.area_id,
                    }
                )
            else:
                _LOGGER.warning("Command %s not found on device %s", command, device.name)
    
    def identify_remote_type(self, service_info: BluetoothServiceInfoBleak) -> str:
        """Identify the type of remote from Bluetooth info."""
        name = service_info.name or ""
        manufacturer = service_info.manufacturer_data
        
        for remote_type, info in KNOWN_REMOTES.items():
            # Check name patterns
            if "name_patterns" in info:
                for pattern in info["name_patterns"]:
                    if pattern.lower() in name.lower():
                        return remote_type
            
            # Check manufacturer
            if "manufacturer" in info:
                if info["manufacturer"].lower() in name.lower():
                    return remote_type
        
        return "Generic HID Remote"


class BluetoothRemoteEntity:
    """Entity representing a Bluetooth remote's state."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        remote: BluetoothRemote,
        manager: BluetoothRemoteManager,
    ) -> None:
        self.hass = hass
        self.remote = remote
        self.manager = manager
        self._attr_name = f"BT Remote {remote.name}"
        self._attr_unique_id = f"omniremote_bt_{remote.id}"
    
    @property
    def state(self) -> str:
        """Return the state of the remote."""
        return self.remote.state.value
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "address": self.remote.address,
            "remote_type": self.remote.remote_type,
            "area": self.remote.area_id,
            "target_device": self.remote.device_id,
            "battery_level": self.remote.battery_level,
            "last_seen": self.remote.last_seen,
            "button_count": len(self.remote.button_mappings),
        }


async def async_setup_bluetooth_remotes(hass: HomeAssistant, database) -> BluetoothRemoteManager:
    """Set up Bluetooth remote support."""
    manager = BluetoothRemoteManager(hass, database)
    await manager.async_setup()
    return manager
