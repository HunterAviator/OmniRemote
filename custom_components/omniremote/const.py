"""Constants and data models for OmniRemote."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import uuid

DOMAIN = "omniremote"
VERSION = "1.10.48"

# Debug flag - set to True for verbose logging
DEBUG = True

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
    STREAMING = "streaming"  # Roku, Fire TV, Apple TV (legacy)
    STREAMER = "streamer"    # Roku, Fire TV, Apple TV
    CABLE_BOX = "cable_box"
    CABLE = "cable"          # Alias for cable_box
    DVR = "dvr"              # TiVo, DVRs
    BLURAY = "bluray"        # Blu-ray/DVD players
    GAME_CONSOLE = "game_console"  # Xbox, PlayStation, Switch
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
    
    # Home Assistant entity integration
    entity_id: str | None = None  # e.g., "media_player.living_room_tv"
    catalog_id: str | None = None  # Reference to catalog profile
    
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
        # Handle category being either enum or string
        category_value = self.category.value if hasattr(self.category, 'value') else str(self.category)
        
        return {
            "id": self.id,
            "name": self.name,
            "category": category_value,
            "brand": self.brand,
            "model": self.model,
            "room_id": self.room_id,
            "entity_id": self.entity_id,
            "catalog_id": self.catalog_id,
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
            entity_id=data.get("entity_id"),
            catalog_id=data.get("catalog_id"),
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
    entity_ids: list[str] = field(default_factory=list)  # HA entity IDs assigned to this room
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "device_ids": self.device_ids,
            "entity_ids": self.entity_ids,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Room":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            icon=data.get("icon", "mdi:sofa"),
            device_ids=data.get("device_ids", []),
            entity_ids=data.get("entity_ids", []),
        )


@dataclass
class SceneAction:
    """A single action within a scene sequence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    order: int = 0
    action_type: str = "ir_command"  # ir_command, ha_service, network_command, delay, condition
    
    # For IR commands (via OmniRemote devices/blasters)
    device_id: str | None = None
    command_name: str | None = None
    blaster_id: str | None = None
    
    # For Home Assistant services
    entity_id: str | None = None
    ha_service: str | None = None  # e.g., "media_player.turn_on"
    service_data: dict[str, Any] = field(default_factory=dict)
    
    # For network devices (Roku, Fire TV, etc.)
    network_device_id: str | None = None
    network_command: str | None = None
    
    # Delay (in seconds)
    delay_seconds: float = 0.5
    
    # Condition - skip if device already in state
    skip_if_on: bool = False  # Skip power on if device already on from another scene
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "order": self.order,
            "action_type": self.action_type,
            "device_id": self.device_id,
            "command_name": self.command_name,
            "blaster_id": self.blaster_id,
            "entity_id": self.entity_id,
            "ha_service": self.ha_service,
            "service_data": self.service_data,
            "network_device_id": self.network_device_id,
            "network_command": self.network_command,
            "delay_seconds": self.delay_seconds,
            "skip_if_on": self.skip_if_on,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SceneAction":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            order=data.get("order", 0),
            action_type=data.get("action_type", "ir_command"),
            device_id=data.get("device_id"),
            command_name=data.get("command_name"),
            blaster_id=data.get("blaster_id"),
            entity_id=data.get("entity_id"),
            ha_service=data.get("ha_service"),
            service_data=data.get("service_data", {}),
            network_device_id=data.get("network_device_id"),
            network_command=data.get("network_command"),
            delay_seconds=data.get("delay_seconds", data.get("delay_after", 0.5)),
            skip_if_on=data.get("skip_if_on", False),
        )


@dataclass
class Scene:
    """A scene with ON and OFF sequences that manages device states."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    icon: str = "mdi:play"
    room_id: str | None = None
    
    # Linked blaster for IR commands
    blaster_id: str | None = None
    
    # Device IDs this scene controls (for state tracking)
    controlled_device_ids: list[str] = field(default_factory=list)
    controlled_entity_ids: list[str] = field(default_factory=list)
    
    # Action sequences
    on_actions: list[SceneAction] = field(default_factory=list)
    off_actions: list[SceneAction] = field(default_factory=list)
    
    # Legacy support
    actions: list[SceneAction] = field(default_factory=list)
    
    # Runtime state
    is_active: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "room_id": self.room_id,
            "blaster_id": self.blaster_id,
            "controlled_device_ids": self.controlled_device_ids,
            "controlled_entity_ids": self.controlled_entity_ids,
            "on_actions": [a.to_dict() for a in self.on_actions],
            "off_actions": [a.to_dict() for a in self.off_actions],
            "actions": [a.to_dict() for a in self.actions],
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scene":
        on_actions = [SceneAction.from_dict(a) for a in data.get("on_actions", [])]
        off_actions = [SceneAction.from_dict(a) for a in data.get("off_actions", [])]
        actions = [SceneAction.from_dict(a) for a in data.get("actions", [])]
        
        # Migrate legacy actions to on_actions if needed
        if not on_actions and actions:
            on_actions = actions
        
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            icon=data.get("icon", "mdi:play"),
            room_id=data.get("room_id"),
            blaster_id=data.get("blaster_id"),
            controlled_device_ids=data.get("controlled_device_ids", []),
            controlled_entity_ids=data.get("controlled_entity_ids", []),
            on_actions=on_actions,
            off_actions=off_actions,
            actions=actions,
            is_active=data.get("is_active", False),
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


# ============================================================
# Custom Remote Profile Models
# ============================================================

class ButtonType(str, Enum):
    """Types of buttons on a remote."""
    POWER = "power"
    NAVIGATION = "navigation"  # D-pad, OK, back, home
    VOLUME = "volume"
    CHANNEL = "channel"
    NUMBER = "number"
    PLAYBACK = "playback"  # play, pause, stop, etc
    INPUT = "input"
    MENU = "menu"
    COLOR = "color"  # red, green, yellow, blue
    CUSTOM = "custom"


class ButtonShape(str, Enum):
    """Shape of button."""
    SQUARE = "square"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    OVAL = "oval"


@dataclass
class RemoteButton:
    """A button on a custom remote profile."""
    id: str
    label: str
    icon: str | None = None
    
    # Position in grid (row, col) - 0-indexed
    row: int = 0
    col: int = 0
    row_span: int = 1
    col_span: int = 1
    
    # Appearance
    button_type: ButtonType = ButtonType.CUSTOM
    shape: ButtonShape = ButtonShape.SQUARE
    color: str | None = None  # hex color or None for default
    
    # Action - what happens when pressed
    action_type: str = "ir_command"  # ir_command, ha_service, scene, none
    device_id: str | None = None
    command_name: str | None = None
    
    # For catalog commands
    catalog_id: str | None = None
    
    # For HA service calls
    ha_domain: str | None = None
    ha_service: str | None = None
    ha_entity_id: str | None = None
    ha_service_data: dict | None = None
    
    # For scene triggers
    scene_id: str | None = None
    scene_action: str = "on"  # on or off
    
    # Long press action (optional)
    long_press_action: str | None = None
    long_press_device_id: str | None = None
    long_press_command: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "icon": self.icon,
            "row": self.row,
            "col": self.col,
            "row_span": self.row_span,
            "col_span": self.col_span,
            "button_type": self.button_type.value if isinstance(self.button_type, ButtonType) else self.button_type,
            "shape": self.shape.value if isinstance(self.shape, ButtonShape) else self.shape,
            "color": self.color,
            "action_type": self.action_type,
            "device_id": self.device_id,
            "command_name": self.command_name,
            "catalog_id": self.catalog_id,
            "ha_domain": self.ha_domain,
            "ha_service": self.ha_service,
            "ha_entity_id": self.ha_entity_id,
            "ha_service_data": self.ha_service_data,
            "scene_id": self.scene_id,
            "scene_action": self.scene_action,
            "long_press_action": self.long_press_action,
            "long_press_device_id": self.long_press_device_id,
            "long_press_command": self.long_press_command,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RemoteButton":
        button_type = data.get("button_type", "custom")
        if isinstance(button_type, str):
            try:
                button_type = ButtonType(button_type)
            except ValueError:
                button_type = ButtonType.CUSTOM
        
        shape = data.get("shape", "square")
        if isinstance(shape, str):
            try:
                shape = ButtonShape(shape)
            except ValueError:
                shape = ButtonShape.SQUARE
        
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            label=data.get("label", ""),
            icon=data.get("icon"),
            row=data.get("row", 0),
            col=data.get("col", 0),
            row_span=data.get("row_span", 1),
            col_span=data.get("col_span", 1),
            button_type=button_type,
            shape=shape,
            color=data.get("color"),
            action_type=data.get("action_type", "ir_command"),
            device_id=data.get("device_id"),
            command_name=data.get("command_name"),
            catalog_id=data.get("catalog_id"),
            ha_domain=data.get("ha_domain"),
            ha_service=data.get("ha_service"),
            ha_entity_id=data.get("ha_entity_id"),
            ha_service_data=data.get("ha_service_data"),
            scene_id=data.get("scene_id"),
            scene_action=data.get("scene_action", "on"),
            long_press_action=data.get("long_press_action"),
            long_press_device_id=data.get("long_press_device_id"),
            long_press_command=data.get("long_press_command"),
        )


@dataclass
class RemoteProfile:
    """A custom remote profile with button layout."""
    id: str
    name: str
    description: str = ""
    icon: str = "mdi:remote"
    
    # Grid dimensions
    rows: int = 8
    cols: int = 4
    
    # Device type this remote is for
    device_type: str = "universal"  # tv, receiver, streaming, universal, etc
    
    # Default device to send commands to (if not specified per-button)
    default_device_id: str | None = None
    
    # Buttons
    buttons: list[RemoteButton] = field(default_factory=list)
    
    # Template this was based on (if any)
    template: str | None = None
    
    # Timestamps
    created_at: str | None = None
    updated_at: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "rows": self.rows,
            "cols": self.cols,
            "device_type": self.device_type,
            "default_device_id": self.default_device_id,
            "buttons": [b.to_dict() for b in self.buttons],
            "template": self.template,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RemoteProfile":
        buttons = [RemoteButton.from_dict(b) for b in data.get("buttons", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "Custom Remote"),
            description=data.get("description", ""),
            icon=data.get("icon", "mdi:remote"),
            rows=data.get("rows", 8),
            cols=data.get("cols", 4),
            device_type=data.get("device_type", "universal"),
            default_device_id=data.get("default_device_id"),
            buttons=buttons,
            template=data.get("template"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


# Pre-built remote templates
REMOTE_TEMPLATES = {
    "tv_basic": {
        "name": "Basic TV Remote",
        "description": "Standard TV remote with power, volume, channels, and navigation",
        "icon": "mdi:television",
        "device_type": "tv",
        "rows": 10,
        "cols": 4,
        "buttons": [
            # Row 0: Power, Input
            {"id": "power", "label": "Power", "icon": "mdi:power", "row": 0, "col": 1, "col_span": 2, "button_type": "power", "color": "#f44336", "command_name": "power"},
            
            # Row 1: Input, Mute
            {"id": "input", "label": "Input", "icon": "mdi:import", "row": 1, "col": 0, "button_type": "input", "command_name": "source"},
            {"id": "mute", "label": "Mute", "icon": "mdi:volume-off", "row": 1, "col": 3, "button_type": "volume", "command_name": "mute"},
            
            # Row 2-3: Vol/Ch
            {"id": "vol_up", "label": "Vol+", "icon": "mdi:volume-plus", "row": 2, "col": 0, "button_type": "volume", "command_name": "volume_up"},
            {"id": "ch_up", "label": "CH+", "icon": "mdi:chevron-up", "row": 2, "col": 3, "button_type": "channel", "command_name": "channel_up"},
            {"id": "vol_down", "label": "Vol-", "icon": "mdi:volume-minus", "row": 3, "col": 0, "button_type": "volume", "command_name": "volume_down"},
            {"id": "ch_down", "label": "CH-", "icon": "mdi:chevron-down", "row": 3, "col": 3, "button_type": "channel", "command_name": "channel_down"},
            
            # Row 4-6: Navigation
            {"id": "up", "label": "Up", "icon": "mdi:chevron-up", "row": 4, "col": 1, "col_span": 2, "button_type": "navigation", "command_name": "up"},
            {"id": "left", "label": "Left", "icon": "mdi:chevron-left", "row": 5, "col": 0, "button_type": "navigation", "command_name": "left"},
            {"id": "ok", "label": "OK", "icon": "mdi:checkbox-blank-circle", "row": 5, "col": 1, "col_span": 2, "button_type": "navigation", "color": "#2196f3", "command_name": "enter"},
            {"id": "right", "label": "Right", "icon": "mdi:chevron-right", "row": 5, "col": 3, "button_type": "navigation", "command_name": "right"},
            {"id": "down", "label": "Down", "icon": "mdi:chevron-down", "row": 6, "col": 1, "col_span": 2, "button_type": "navigation", "command_name": "down"},
            
            # Row 7: Back, Home, Menu
            {"id": "back", "label": "Back", "icon": "mdi:arrow-left", "row": 7, "col": 0, "button_type": "navigation", "command_name": "back"},
            {"id": "home", "label": "Home", "icon": "mdi:home", "row": 7, "col": 1, "col_span": 2, "button_type": "navigation", "command_name": "home"},
            {"id": "menu", "label": "Menu", "icon": "mdi:menu", "row": 7, "col": 3, "button_type": "menu", "command_name": "menu"},
            
            # Row 8-9: Numbers
            {"id": "1", "label": "1", "row": 8, "col": 0, "button_type": "number", "command_name": "num_1"},
            {"id": "2", "label": "2", "row": 8, "col": 1, "button_type": "number", "command_name": "num_2"},
            {"id": "3", "label": "3", "row": 8, "col": 2, "button_type": "number", "command_name": "num_3"},
            {"id": "4", "label": "4", "row": 9, "col": 0, "button_type": "number", "command_name": "num_4"},
            {"id": "5", "label": "5", "row": 9, "col": 1, "button_type": "number", "command_name": "num_5"},
            {"id": "6", "label": "6", "row": 9, "col": 2, "button_type": "number", "command_name": "num_6"},
        ]
    },
    "streaming_basic": {
        "name": "Streaming Device Remote",
        "description": "Simple remote for Roku, Fire TV, Apple TV, etc.",
        "icon": "mdi:cast",
        "device_type": "streaming",
        "rows": 8,
        "cols": 3,
        "buttons": [
            {"id": "power", "label": "Power", "icon": "mdi:power", "row": 0, "col": 1, "button_type": "power", "color": "#f44336", "command_name": "power"},
            
            {"id": "up", "label": "Up", "icon": "mdi:chevron-up", "row": 2, "col": 1, "button_type": "navigation", "command_name": "up"},
            {"id": "left", "label": "Left", "icon": "mdi:chevron-left", "row": 3, "col": 0, "button_type": "navigation", "command_name": "left"},
            {"id": "ok", "label": "OK", "icon": "mdi:checkbox-blank-circle", "row": 3, "col": 1, "button_type": "navigation", "color": "#2196f3", "command_name": "select"},
            {"id": "right", "label": "Right", "icon": "mdi:chevron-right", "row": 3, "col": 2, "button_type": "navigation", "command_name": "right"},
            {"id": "down", "label": "Down", "icon": "mdi:chevron-down", "row": 4, "col": 1, "button_type": "navigation", "command_name": "down"},
            
            {"id": "back", "label": "Back", "icon": "mdi:arrow-left", "row": 5, "col": 0, "button_type": "navigation", "command_name": "back"},
            {"id": "home", "label": "Home", "icon": "mdi:home", "row": 5, "col": 2, "button_type": "navigation", "command_name": "home"},
            
            {"id": "rewind", "label": "Rew", "icon": "mdi:rewind", "row": 6, "col": 0, "button_type": "playback", "command_name": "rewind"},
            {"id": "play", "label": "Play", "icon": "mdi:play-pause", "row": 6, "col": 1, "button_type": "playback", "command_name": "play"},
            {"id": "forward", "label": "FF", "icon": "mdi:fast-forward", "row": 6, "col": 2, "button_type": "playback", "command_name": "forward"},
        ]
    },
    "receiver_basic": {
        "name": "AV Receiver Remote",
        "description": "Audio/video receiver with input selection",
        "icon": "mdi:speaker",
        "device_type": "receiver",
        "rows": 6,
        "cols": 4,
        "buttons": [
            {"id": "power", "label": "Power", "icon": "mdi:power", "row": 0, "col": 1, "col_span": 2, "button_type": "power", "color": "#f44336", "command_name": "power"},
            
            {"id": "vol_up", "label": "Vol+", "icon": "mdi:volume-plus", "row": 1, "col": 0, "button_type": "volume", "command_name": "volume_up"},
            {"id": "mute", "label": "Mute", "icon": "mdi:volume-off", "row": 1, "col": 1, "col_span": 2, "button_type": "volume", "command_name": "mute"},
            {"id": "vol_down", "label": "Vol-", "icon": "mdi:volume-minus", "row": 2, "col": 0, "button_type": "volume", "command_name": "volume_down"},
            
            {"id": "hdmi1", "label": "HDMI 1", "icon": "mdi:video-input-hdmi", "row": 3, "col": 0, "button_type": "input", "command_name": "input_hdmi1"},
            {"id": "hdmi2", "label": "HDMI 2", "icon": "mdi:video-input-hdmi", "row": 3, "col": 1, "button_type": "input", "command_name": "input_hdmi2"},
            {"id": "hdmi3", "label": "HDMI 3", "icon": "mdi:video-input-hdmi", "row": 3, "col": 2, "button_type": "input", "command_name": "input_hdmi3"},
            {"id": "hdmi4", "label": "HDMI 4", "icon": "mdi:video-input-hdmi", "row": 3, "col": 3, "button_type": "input", "command_name": "input_hdmi4"},
            
            {"id": "tv", "label": "TV", "icon": "mdi:television", "row": 4, "col": 0, "button_type": "input", "command_name": "input_tv"},
            {"id": "game", "label": "Game", "icon": "mdi:gamepad-variant", "row": 4, "col": 1, "button_type": "input", "command_name": "input_game"},
            {"id": "cd", "label": "CD", "icon": "mdi:disc", "row": 4, "col": 2, "button_type": "input", "command_name": "input_cd"},
            {"id": "net", "label": "NET", "icon": "mdi:wifi", "row": 4, "col": 3, "button_type": "input", "command_name": "input_net"},
        ]
    },
    "universal": {
        "name": "Universal Remote",
        "description": "Multi-device remote with TV, receiver, and streaming controls",
        "icon": "mdi:remote",
        "device_type": "universal",
        "rows": 12,
        "cols": 4,
        "buttons": [
            # TV Power / Receiver Power
            {"id": "tv_power", "label": "TV", "icon": "mdi:television", "row": 0, "col": 0, "col_span": 2, "button_type": "power", "color": "#f44336"},
            {"id": "rcv_power", "label": "RCV", "icon": "mdi:speaker", "row": 0, "col": 2, "col_span": 2, "button_type": "power", "color": "#ff9800"},
            
            # Volume / Mute
            {"id": "vol_up", "label": "Vol+", "icon": "mdi:volume-plus", "row": 1, "col": 0, "button_type": "volume"},
            {"id": "mute", "label": "Mute", "icon": "mdi:volume-off", "row": 1, "col": 1, "col_span": 2, "button_type": "volume"},
            {"id": "input", "label": "Input", "icon": "mdi:import", "row": 1, "col": 3, "button_type": "input"},
            {"id": "vol_down", "label": "Vol-", "icon": "mdi:volume-minus", "row": 2, "col": 0, "button_type": "volume"},
            
            # Navigation
            {"id": "up", "label": "Up", "icon": "mdi:chevron-up", "row": 3, "col": 1, "col_span": 2, "button_type": "navigation"},
            {"id": "left", "label": "Left", "icon": "mdi:chevron-left", "row": 4, "col": 0, "button_type": "navigation"},
            {"id": "ok", "label": "OK", "icon": "mdi:checkbox-blank-circle", "row": 4, "col": 1, "col_span": 2, "button_type": "navigation", "color": "#2196f3"},
            {"id": "right", "label": "Right", "icon": "mdi:chevron-right", "row": 4, "col": 3, "button_type": "navigation"},
            {"id": "down", "label": "Down", "icon": "mdi:chevron-down", "row": 5, "col": 1, "col_span": 2, "button_type": "navigation"},
            
            # Menu controls
            {"id": "back", "label": "Back", "icon": "mdi:arrow-left", "row": 6, "col": 0, "button_type": "navigation"},
            {"id": "home", "label": "Home", "icon": "mdi:home", "row": 6, "col": 1, "col_span": 2, "button_type": "navigation"},
            {"id": "menu", "label": "Menu", "icon": "mdi:menu", "row": 6, "col": 3, "button_type": "menu"},
            
            # Playback
            {"id": "rewind", "label": "Rew", "icon": "mdi:rewind", "row": 7, "col": 0, "button_type": "playback"},
            {"id": "play", "label": "Play", "icon": "mdi:play", "row": 7, "col": 1, "button_type": "playback"},
            {"id": "pause", "label": "Pause", "icon": "mdi:pause", "row": 7, "col": 2, "button_type": "playback"},
            {"id": "forward", "label": "FF", "icon": "mdi:fast-forward", "row": 7, "col": 3, "button_type": "playback"},
            
            # Number row 1
            {"id": "1", "label": "1", "row": 8, "col": 0, "button_type": "number"},
            {"id": "2", "label": "2", "row": 8, "col": 1, "button_type": "number"},
            {"id": "3", "label": "3", "row": 8, "col": 2, "button_type": "number"},
            {"id": "ch_up", "label": "CH+", "icon": "mdi:chevron-up", "row": 8, "col": 3, "button_type": "channel"},
            
            # Number row 2
            {"id": "4", "label": "4", "row": 9, "col": 0, "button_type": "number"},
            {"id": "5", "label": "5", "row": 9, "col": 1, "button_type": "number"},
            {"id": "6", "label": "6", "row": 9, "col": 2, "button_type": "number"},
            {"id": "ch_down", "label": "CH-", "icon": "mdi:chevron-down", "row": 9, "col": 3, "button_type": "channel"},
            
            # Number row 3
            {"id": "7", "label": "7", "row": 10, "col": 0, "button_type": "number"},
            {"id": "8", "label": "8", "row": 10, "col": 1, "button_type": "number"},
            {"id": "9", "label": "9", "row": 10, "col": 2, "button_type": "number"},
            {"id": "guide", "label": "Guide", "icon": "mdi:view-grid", "row": 10, "col": 3, "button_type": "menu"},
            
            # Number row 4
            {"id": "prev", "label": "Prev", "icon": "mdi:skip-previous", "row": 11, "col": 0, "button_type": "channel"},
            {"id": "0", "label": "0", "row": 11, "col": 1, "button_type": "number"},
            {"id": "info", "label": "Info", "icon": "mdi:information", "row": 11, "col": 2, "button_type": "menu"},
            {"id": "exit", "label": "Exit", "icon": "mdi:exit-to-app", "row": 11, "col": 3, "button_type": "menu"},
        ]
    },
}
