"""Constants and data models for OmniRemote."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import uuid

DOMAIN = "omniremote"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.database"

# Services
SERVICE_IMPORT_FLIPPER = "import_flipper"
SERVICE_EXPORT_FLIPPER = "export_flipper"
SERVICE_LEARN_CODE = "learn_code"
SERVICE_SEND_CODE = "send_code"
SERVICE_RUN_SCENE = "run_scene"
SERVICE_CREATE_SCENE = "create_scene"
SERVICE_ADD_DEVICE = "add_device"
SERVICE_ADD_ROOM = "add_room"

# Defaults
DEFAULT_IR_FREQUENCY = 38000
DEFAULT_IR_DUTY_CYCLE = 0.33


class CodeType(str, Enum):
    """Type of remote code."""
    IR_PARSED = "ir_parsed"
    IR_RAW = "ir_raw"
    RF_PARSED = "rf_parsed"
    RF_RAW = "rf_raw"


class DeviceCategory(str, Enum):
    """Device category for organization."""
    TV = "tv"
    RECEIVER = "receiver"
    SOUNDBAR = "soundbar"
    STREAMING = "streaming"  # Roku, Fire TV, Apple TV
    CABLE_BOX = "cable_box"
    ANTENNA = "antenna"
    PROJECTOR = "projector"
    AC = "ac"
    FAN = "fan"
    LIGHT = "light"
    BLIND = "blind"
    GATE = "gate"
    GARAGE = "garage"
    OTHER = "other"


# Common button names (standardized)
STANDARD_BUTTONS = {
    "tv": [
        "power", "power_on", "power_off",
        "volume_up", "volume_down", "mute",
        "channel_up", "channel_down",
        "input", "source", "hdmi1", "hdmi2", "hdmi3",
        "up", "down", "left", "right", "ok", "enter",
        "back", "home", "menu", "exit",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    ],
    "streaming": [
        "power", "home", "back",
        "up", "down", "left", "right", "ok", "select",
        "play", "pause", "play_pause", "stop",
        "rewind", "fast_forward", "skip_back", "skip_forward",
        "volume_up", "volume_down", "mute",
        "netflix", "hulu", "disney", "amazon", "youtube",
    ],
    "receiver": [
        "power", "power_on", "power_off",
        "volume_up", "volume_down", "mute",
        "input", "hdmi1", "hdmi2", "hdmi3", "optical", "bluetooth",
        "surround", "stereo", "movie", "music", "game",
    ],
    "ac": [
        "power", "power_on", "power_off",
        "temp_up", "temp_down",
        "mode_cool", "mode_heat", "mode_auto", "mode_fan", "mode_dry",
        "fan_low", "fan_medium", "fan_high", "fan_auto",
        "swing", "timer",
    ],
}


@dataclass
class RemoteCode:
    """A single remote control code."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    code_type: CodeType = CodeType.IR_RAW
    
    # IR fields
    protocol: str | None = None
    address: str | None = None
    command: str | None = None
    frequency: int = DEFAULT_IR_FREQUENCY
    duty_cycle: float = DEFAULT_IR_DUTY_CYCLE
    raw_data: list[int] | None = None
    
    # RF fields
    rf_frequency: int | None = None  # e.g., 433920000
    rf_preset: str | None = None
    rf_bit: int | None = None
    rf_key: str | None = None
    rf_te: int | None = None
    
    # Broadlink compatible code (base64)
    broadlink_code: str | None = None
    
    # Source info
    source: str = "manual"  # flipper, broadlink, learned, manual
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "code_type": self.code_type.value,
            "protocol": self.protocol,
            "address": self.address,
            "command": self.command,
            "frequency": self.frequency,
            "duty_cycle": self.duty_cycle,
            "raw_data": self.raw_data,
            "rf_frequency": self.rf_frequency,
            "rf_preset": self.rf_preset,
            "rf_bit": self.rf_bit,
            "rf_key": self.rf_key,
            "rf_te": self.rf_te,
            "broadlink_code": self.broadlink_code,
            "source": self.source,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RemoteCode":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            code_type=CodeType(data.get("code_type", "ir_raw")),
            protocol=data.get("protocol"),
            address=data.get("address"),
            command=data.get("command"),
            frequency=data.get("frequency", DEFAULT_IR_FREQUENCY),
            duty_cycle=data.get("duty_cycle", DEFAULT_IR_DUTY_CYCLE),
            raw_data=data.get("raw_data"),
            rf_frequency=data.get("rf_frequency"),
            rf_preset=data.get("rf_preset"),
            rf_bit=data.get("rf_bit"),
            rf_key=data.get("rf_key"),
            rf_te=data.get("rf_te"),
            broadlink_code=data.get("broadlink_code"),
            source=data.get("source", "manual"),
        )


@dataclass
class Device:
    """A controllable device (TV, Roku, etc.)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    category: DeviceCategory = DeviceCategory.OTHER
    brand: str = ""
    model: str = ""
    room_id: str | None = None
    commands: dict[str, RemoteCode] = field(default_factory=dict)
    
    # State tracking
    power_state: bool = False  # On/Off
    current_input: str | None = None  # Current input (HDMI1, etc.)
    volume_level: int | None = None  # 0-100
    muted: bool = False
    
    # Projector-specific
    lamp_hours: int | None = None
    lens_position: str | None = None  # "home", "custom1", etc.
    
    # Power on/off commands (for state tracking)
    power_on_command: str | None = None
    power_off_command: str | None = None
    
    # Input mappings: input_name -> command_name
    input_commands: dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "brand": self.brand,
            "model": self.model,
            "room_id": self.room_id,
            "commands": {k: v.to_dict() for k, v in self.commands.items()},
            "power_state": self.power_state,
            "current_input": self.current_input,
            "volume_level": self.volume_level,
            "muted": self.muted,
            "lamp_hours": self.lamp_hours,
            "lens_position": self.lens_position,
            "power_on_command": self.power_on_command,
            "power_off_command": self.power_off_command,
            "input_commands": self.input_commands,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Device":
        commands = {}
        for k, v in data.get("commands", {}).items():
            commands[k] = RemoteCode.from_dict(v)
        
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            category=DeviceCategory(data.get("category", "other")),
            brand=data.get("brand", ""),
            model=data.get("model", ""),
            room_id=data.get("room_id"),
            commands=commands,
            power_state=data.get("power_state", False),
            current_input=data.get("current_input"),
            volume_level=data.get("volume_level"),
            muted=data.get("muted", False),
            lamp_hours=data.get("lamp_hours"),
            lens_position=data.get("lens_position"),
            power_on_command=data.get("power_on_command"),
            power_off_command=data.get("power_off_command"),
            input_commands=data.get("input_commands", {}),
        )


@dataclass
class Room:
    """A room containing devices."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    icon: str = "mdi:sofa"
    device_ids: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "device_ids": self.device_ids,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Room":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            icon=data.get("icon", "mdi:sofa"),
            device_ids=data.get("device_ids", []),
        )


@dataclass
class SceneAction:
    """A single action within a scene."""
    device_id: str = ""
    command_name: str = ""
    delay_after: float = 0.5  # seconds to wait after this action
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "command_name": self.command_name,
            "delay_after": self.delay_after,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SceneAction":
        return cls(
            device_id=data.get("device_id", ""),
            command_name=data.get("command_name", ""),
            delay_after=data.get("delay_after", 0.5),
        )


@dataclass
class Scene:
    """A scene that runs multiple actions."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    icon: str = "mdi:play"
    room_id: str | None = None
    actions: list[SceneAction] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "room_id": self.room_id,
            "actions": [a.to_dict() for a in self.actions],
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scene":
        actions = [SceneAction.from_dict(a) for a in data.get("actions", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            icon=data.get("icon", "mdi:play"),
            room_id=data.get("room_id"),
            actions=actions,
        )


@dataclass
class Blaster:
    """A physical IR/RF blaster device (Broadlink, etc.)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    host: str = ""
    mac: str = ""
    device_type: str = ""
    room_id: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "mac": self.mac,
            "device_type": self.device_type,
            "room_id": self.room_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Blaster":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            host=data.get("host", ""),
            mac=data.get("mac", ""),
            device_type=data.get("device_type", ""),
            room_id=data.get("room_id"),
        )


# Example scenes for common activities
EXAMPLE_SCENES = {
    "watch_antenna_tv": {
        "name": "Watch Antenna TV",
        "icon": "mdi:antenna",
        "description": "Turn on TV and switch to antenna input",
        "actions": [
            {"device": "TV", "command": "power"},
            {"device": "TV", "command": "input_antenna", "delay": 2},
        ]
    },
    "watch_roku": {
        "name": "Watch Roku",
        "icon": "mdi:roku",
        "description": "Turn on TV and Receiver, switch to Roku input",
        "actions": [
            {"device": "TV", "command": "power"},
            {"device": "Receiver", "command": "power", "delay": 1},
            {"device": "TV", "command": "hdmi1", "delay": 2},
            {"device": "Receiver", "command": "hdmi2", "delay": 1},
        ]
    },
    "watch_cable": {
        "name": "Watch Cable",
        "icon": "mdi:television-classic",
        "description": "Turn on TV and cable box",
        "actions": [
            {"device": "TV", "command": "power"},
            {"device": "Cable Box", "command": "power", "delay": 1},
            {"device": "TV", "command": "hdmi2", "delay": 2},
        ]
    },
    "all_off": {
        "name": "All Off",
        "icon": "mdi:power-off",
        "description": "Turn off all entertainment devices",
        "actions": [
            {"device": "TV", "command": "power_off"},
            {"device": "Receiver", "command": "power_off", "delay": 0.5},
            {"device": "Cable Box", "command": "power_off", "delay": 0.5},
        ]
    },
}
