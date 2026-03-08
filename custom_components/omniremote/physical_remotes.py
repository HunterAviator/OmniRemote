"""
Physical Remote Control Support for OmniRemote.

Supports 4 types of remote inputs:
1. Zigbee remotes (IKEA, Aqara, Hue, etc.) - via ZHA/deCONZ events
2. RF 433MHz remotes (via Sonoff RF Bridge/Tasmota)
3. Bluetooth remotes (via ESP32 Bluetooth Proxy)
4. USB keyboard remotes (via Pi Zero W bridge)

All remotes and bridges are mapped to rooms for organized control.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from datetime import datetime

from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers import device_registry as dr
from homeassistant.components import mqtt

_LOGGER = logging.getLogger(__name__)


class BridgeType(Enum):
    """Types of remote bridges."""
    ZIGBEE_ZHA = "zigbee_zha"          # ZHA integration
    ZIGBEE_DECONZ = "zigbee_deconz"    # deCONZ integration
    ZIGBEE_Z2M = "zigbee_z2m"          # Zigbee2MQTT
    RF_TASMOTA = "rf_tasmota"          # Sonoff RF Bridge with Tasmota
    RF_ESPHOME = "rf_esphome"          # ESPHome RF receiver
    BLUETOOTH_PROXY = "bluetooth_proxy" # ESP32 BT Proxy
    USB_BRIDGE = "usb_bridge"          # Pi Zero W USB bridge
    NETWORK = "network"                 # Direct network (WebSocket/REST)


class RemoteType(Enum):
    """Types of physical remotes."""
    ZIGBEE = "zigbee"
    RF_433 = "rf_433"
    BLUETOOTH = "bluetooth"
    BLUETOOTH_HA = "bluetooth_ha"  # Bluetooth via HA Yellow / Built-in adapter
    USB_KEYBOARD = "usb_keyboard"
    IR = "ir"  # For remotes that send IR to a receiver


class ActionType(Enum):
    """Types of actions a button can trigger."""
    IR_COMMAND = "ir_command"      # Send IR code from device
    SCENE = "scene"                # Run OmniRemote scene
    ACTIVITY = "activity"          # Run OmniRemote activity
    HA_SERVICE = "ha_service"      # Call any HA service
    TOGGLE_DEVICE = "toggle_device" # Toggle device power
    VOLUME_UP = "volume_up"        # Room volume up
    VOLUME_DOWN = "volume_down"    # Room volume down
    MUTE = "mute"                  # Room mute toggle
    CHANNEL_UP = "channel_up"      # Room channel up
    CHANNEL_DOWN = "channel_down"  # Room channel down


@dataclass
class ButtonMapping:
    """Mapping of a button to an action."""
    button_id: str                     # e.g., "KEY_VOLUMEUP", "button_1", "on"
    action_type: ActionType
    action_target: str                 # device_id, scene_id, service name, etc.
    action_data: dict = field(default_factory=dict)  # Additional data
    long_press_action: dict | None = None   # Optional long press override
    double_press_action: dict | None = None # Optional double press override
    
    def to_dict(self) -> dict:
        result = {
            "button_id": self.button_id,
            "action_type": self.action_type.value,
            "action_target": self.action_target,
            "action_data": self.action_data,
            "long_press_action": self.long_press_action,
            "double_press_action": self.double_press_action,
        }
        
        # Add UI-friendly field names based on action type
        if self.action_type == ActionType.SCENE:
            result["scene_id"] = self.action_target
        elif self.action_type == ActionType.IR_COMMAND:
            result["device_id"] = self.action_target
            result["command_name"] = self.action_data.get("command_name", "")
            result["blaster_id"] = self.action_data.get("blaster_id", "")
        elif self.action_type == ActionType.HA_SERVICE:
            result["ha_domain"] = self.action_data.get("domain", "")
            result["ha_service"] = self.action_data.get("service", "")
            result["ha_entity_id"] = self.action_data.get("entity_id", "")
        elif self.action_type in [ActionType.VOLUME_UP, ActionType.VOLUME_DOWN, ActionType.MUTE]:
            result["room_id"] = self.action_target
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "ButtonMapping":
        return cls(
            button_id=data["button_id"],
            action_type=ActionType(data["action_type"]),
            action_target=data["action_target"],
            action_data=data.get("action_data", {}),
            long_press_action=data.get("long_press_action"),
            double_press_action=data.get("double_press_action"),
        )


@dataclass
class RemoteBridge:
    """
    A bridge that receives signals from physical remotes.
    
    Examples:
    - Pi Zero W with USB dongle (USB_BRIDGE)
    - ESP32 with Bluetooth proxy (BLUETOOTH_PROXY)
    - Sonoff RF Bridge (RF_TASMOTA)
    - ZHA coordinator (built into HA)
    """
    id: str
    name: str
    bridge_type: BridgeType
    room_id: str | None = None
    
    # Connection settings (varies by type)
    host: str | None = None            # IP address for network bridges
    port: int | None = None            # Port for network bridges
    mqtt_topic: str | None = None      # MQTT topic for Tasmota/ESPHome
    device_id: str | None = None       # HA device ID for Zigbee coordinators
    
    # Status
    online: bool = False
    last_seen: str | None = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "bridge_type": self.bridge_type.value,
            "room_id": self.room_id,
            "host": self.host,
            "port": self.port,
            "mqtt_topic": self.mqtt_topic,
            "device_id": self.device_id,
            "online": self.online,
            "last_seen": self.last_seen,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RemoteBridge":
        return cls(
            id=data["id"],
            name=data["name"],
            bridge_type=BridgeType(data["bridge_type"]),
            room_id=data.get("room_id"),
            host=data.get("host"),
            port=data.get("port"),
            mqtt_topic=data.get("mqtt_topic"),
            device_id=data.get("device_id"),
            online=data.get("online", False),
            last_seen=data.get("last_seen"),
        )


@dataclass
class PhysicalRemote:
    """
    A physical remote control device.
    
    Maps button presses to OmniRemote actions.
    """
    id: str
    name: str
    remote_type: RemoteType
    room_id: str | None = None
    bridge_id: str | None = None       # Bridge that receives this remote's signals
    
    # Identification (varies by type)
    zigbee_ieee: str | None = None     # IEEE address for Zigbee
    rf_code_prefix: str | None = None  # RF code prefix for 433MHz
    bt_mac: str | None = None          # Bluetooth MAC address
    usb_device_name: str | None = None # USB device identifier
    
    # Button mappings
    button_mappings: dict[str, ButtonMapping] = field(default_factory=dict)
    
    # Remote profile (pre-defined button layouts)
    profile: str | None = None         # e.g., "ikea_tradfri", "mx3_pro"
    model_id: str | None = None        # Reference to remote_models.py profile
    
    # Status
    battery_level: int | None = None
    last_seen: str | None = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "remote_type": self.remote_type.value,
            "room_id": self.room_id,
            "bridge_id": self.bridge_id,
            "zigbee_ieee": self.zigbee_ieee,
            "rf_code_prefix": self.rf_code_prefix,
            "bt_mac": self.bt_mac,
            "usb_device_name": self.usb_device_name,
            "button_mappings": {k: v.to_dict() for k, v in self.button_mappings.items()},
            "profile": self.profile,
            "model_id": self.model_id,
            "battery_level": self.battery_level,
            "last_seen": self.last_seen,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PhysicalRemote":
        mappings = {}
        for k, v in data.get("button_mappings", {}).items():
            mappings[k] = ButtonMapping.from_dict(v)
        
        return cls(
            id=data["id"],
            name=data["name"],
            remote_type=RemoteType(data["remote_type"]),
            room_id=data.get("room_id"),
            bridge_id=data.get("bridge_id"),
            zigbee_ieee=data.get("zigbee_ieee"),
            rf_code_prefix=data.get("rf_code_prefix"),
            bt_mac=data.get("bt_mac"),
            usb_device_name=data.get("usb_device_name"),
            button_mappings=mappings,
            profile=data.get("profile"),
            model_id=data.get("model_id"),
            battery_level=data.get("battery_level"),
            last_seen=data.get("last_seen"),
        )


# =============================================================================
# Pre-defined Remote Profiles (Button Layouts)
# =============================================================================

REMOTE_PROFILES = {
    # IKEA TRADFRI Remote (5 buttons)
    "ikea_tradfri_remote": {
        "name": "IKEA TRADFRI Remote",
        "type": RemoteType.ZIGBEE,
        "buttons": ["toggle", "brightness_up", "brightness_down", "arrow_left", "arrow_right"],
        "default_mappings": {
            "toggle": {"action_type": "scene", "description": "Power Toggle"},
            "brightness_up": {"action_type": "volume_up", "description": "Volume Up"},
            "brightness_down": {"action_type": "volume_down", "description": "Volume Down"},
            "arrow_left": {"action_type": "channel_down", "description": "Previous/Ch Down"},
            "arrow_right": {"action_type": "channel_up", "description": "Next/Ch Up"},
        },
    },
    
    # IKEA RODRET (2 buttons)
    "ikea_rodret": {
        "name": "IKEA RODRET",
        "type": RemoteType.ZIGBEE,
        "buttons": ["on", "off"],
        "default_mappings": {
            "on": {"action_type": "scene", "description": "On/Scene 1"},
            "off": {"action_type": "scene", "description": "Off/Scene 2"},
        },
    },
    
    # IKEA SOMRIG (2 buttons with short/long press)
    "ikea_somrig": {
        "name": "IKEA SOMRIG",
        "type": RemoteType.ZIGBEE,
        "buttons": ["button_1", "button_2", "button_1_long", "button_2_long"],
        "default_mappings": {
            "button_1": {"action_type": "scene", "description": "Button 1"},
            "button_2": {"action_type": "scene", "description": "Button 2"},
            "button_1_long": {"action_type": "scene", "description": "Button 1 Long"},
            "button_2_long": {"action_type": "scene", "description": "Button 2 Long"},
        },
    },
    
    # Aqara Mini Switch
    "aqara_mini_switch": {
        "name": "Aqara Mini Switch",
        "type": RemoteType.ZIGBEE,
        "buttons": ["single", "double", "long"],
        "default_mappings": {
            "single": {"action_type": "scene", "description": "Single Press"},
            "double": {"action_type": "scene", "description": "Double Press"},
            "long": {"action_type": "scene", "description": "Long Press"},
        },
    },
    
    # Aqara Cube T1 Pro
    "aqara_cube": {
        "name": "Aqara Cube T1 Pro",
        "type": RemoteType.ZIGBEE,
        "buttons": ["shake", "tap", "slide", "flip90", "flip180", "rotate_left", "rotate_right"],
        "default_mappings": {
            "shake": {"action_type": "scene", "description": "Shake"},
            "tap": {"action_type": "toggle_device", "description": "Tap - Toggle"},
            "slide": {"action_type": "scene", "description": "Slide"},
            "flip90": {"action_type": "scene", "description": "Flip 90°"},
            "flip180": {"action_type": "scene", "description": "Flip 180°"},
            "rotate_left": {"action_type": "volume_down", "description": "Rotate Left - Vol Down"},
            "rotate_right": {"action_type": "volume_up", "description": "Rotate Right - Vol Up"},
        },
    },
    
    # Hue Dimmer Switch (4 buttons)
    "hue_dimmer": {
        "name": "Philips Hue Dimmer",
        "type": RemoteType.ZIGBEE,
        "buttons": ["on_press", "up_press", "down_press", "off_press", 
                    "on_hold", "up_hold", "down_hold", "off_hold"],
        "default_mappings": {
            "on_press": {"action_type": "scene", "description": "On"},
            "up_press": {"action_type": "volume_up", "description": "Volume Up"},
            "down_press": {"action_type": "volume_down", "description": "Volume Down"},
            "off_press": {"action_type": "scene", "description": "Off"},
        },
    },
    
    # MX3 Pro Air Mouse (USB Keyboard)
    "mx3_pro": {
        "name": "MX3 Pro Air Mouse",
        "type": RemoteType.USB_KEYBOARD,
        "buttons": [
            "KEY_POWER", "KEY_HOME", "KEY_BACK", "KEY_MENU",
            "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_OK",
            "KEY_VOLUMEUP", "KEY_VOLUMEDOWN", "KEY_MUTE",
            "KEY_CHANNELUP", "KEY_CHANNELDOWN",
            "KEY_PLAYPAUSE", "KEY_STOPCD", "KEY_PREVIOUSSONG", "KEY_NEXTSONG",
            "KEY_RED", "KEY_GREEN", "KEY_YELLOW", "KEY_BLUE",
            "KEY_0", "KEY_1", "KEY_2", "KEY_3", "KEY_4",
            "KEY_5", "KEY_6", "KEY_7", "KEY_8", "KEY_9",
        ],
        "default_mappings": {
            "KEY_POWER": {"action_type": "toggle_device", "description": "Power"},
            "KEY_VOLUMEUP": {"action_type": "volume_up", "description": "Volume Up"},
            "KEY_VOLUMEDOWN": {"action_type": "volume_down", "description": "Volume Down"},
            "KEY_MUTE": {"action_type": "mute", "description": "Mute"},
            "KEY_CHANNELUP": {"action_type": "channel_up", "description": "Channel Up"},
            "KEY_CHANNELDOWN": {"action_type": "channel_down", "description": "Channel Down"},
            "KEY_RED": {"action_type": "scene", "description": "Red - Scene 1"},
            "KEY_GREEN": {"action_type": "scene", "description": "Green - Scene 2"},
            "KEY_YELLOW": {"action_type": "scene", "description": "Yellow - Scene 3"},
            "KEY_BLUE": {"action_type": "scene", "description": "Blue - Scene 4"},
        },
    },
    
    # Generic 433MHz 4-button remote
    "rf_4button": {
        "name": "433MHz 4-Button Remote",
        "type": RemoteType.RF_433,
        "buttons": ["button_a", "button_b", "button_c", "button_d"],
        "default_mappings": {
            "button_a": {"action_type": "scene", "description": "Button A"},
            "button_b": {"action_type": "scene", "description": "Button B"},
            "button_c": {"action_type": "scene", "description": "Button C"},
            "button_d": {"action_type": "scene", "description": "Button D"},
        },
    },
    
    # Generic Bluetooth Media Remote
    "bt_media_remote": {
        "name": "Bluetooth Media Remote",
        "type": RemoteType.BLUETOOTH,
        "buttons": ["play", "pause", "next", "prev", "vol_up", "vol_down"],
        "default_mappings": {
            "play": {"action_type": "ir_command", "description": "Play"},
            "pause": {"action_type": "ir_command", "description": "Pause"},
            "next": {"action_type": "channel_up", "description": "Next/Ch Up"},
            "prev": {"action_type": "channel_down", "description": "Prev/Ch Down"},
            "vol_up": {"action_type": "volume_up", "description": "Volume Up"},
            "vol_down": {"action_type": "volume_down", "description": "Volume Down"},
        },
    },
}


# =============================================================================
# Remote Event Handler
# =============================================================================

class PhysicalRemoteManager:
    """
    Manages physical remotes and handles button press events.
    
    Listens to various event sources:
    - ZHA events (zha_event)
    - deCONZ events (deconz_event)
    - Zigbee2MQTT (via MQTT)
    - Tasmota RF Bridge (via MQTT)
    - USB Bridge (via MQTT)
    - Bluetooth Proxy (via MQTT)
    """
    
    def __init__(self, hass: HomeAssistant, database: Any) -> None:
        self.hass = hass
        self.database = database
        self._listeners: list[Callable] = []
        self._action_callback: Callable | None = None
    
    def set_action_callback(self, callback: Callable) -> None:
        """Set callback for executing actions."""
        self._action_callback = callback
    
    async def async_start(self) -> None:
        """Start listening for remote events."""
        # Listen to ZHA events
        self._listeners.append(
            self.hass.bus.async_listen("zha_event", self._handle_zha_event)
        )
        
        # Listen to deCONZ events
        self._listeners.append(
            self.hass.bus.async_listen("deconz_event", self._handle_deconz_event)
        )
        
        # Listen to keyboard_remote events (for Bluetooth HID remotes)
        self._listeners.append(
            self.hass.bus.async_listen(
                "keyboard_remote_command_received", 
                self._handle_keyboard_remote_event
            )
        )
        _LOGGER.info("Registered keyboard_remote event listener for BT HID remotes")
        
        # Listen to state changes for Bluetooth remote entities
        self._listeners.append(
            self.hass.bus.async_listen("state_changed", self._handle_state_changed)
        )
        
        # Listen to MQTT for Zigbee2MQTT, Tasmota, and bridges
        if mqtt.DOMAIN in self.hass.config.components:
            await self._setup_mqtt_listeners()
        
        # Listen to custom OmniRemote bridge events
        self._listeners.append(
            self.hass.bus.async_listen("omniremote_bridge_event", self._handle_bridge_event)
        )
        
        _LOGGER.info("PhysicalRemoteManager started - listening for ZHA, deCONZ, keyboard_remote, MQTT, bridge events")
    
    async def async_stop(self) -> None:
        """Stop listening for remote events."""
        for unsub in self._listeners:
            unsub()
        self._listeners.clear()
        _LOGGER.info("PhysicalRemoteManager stopped")
    
    async def _setup_mqtt_listeners(self) -> None:
        """Setup MQTT subscriptions."""
        _LOGGER.info("[OmniRemote] Setting up MQTT listeners for physical remotes")
        
        # Zigbee2MQTT
        @callback
        def z2m_message(msg):
            """Handle Zigbee2MQTT message."""
            asyncio.create_task(self._handle_z2m_message(msg))
        
        await mqtt.async_subscribe(
            self.hass, "zigbee2mqtt/+/action", z2m_message
        )
        
        # Tasmota RF Bridge
        @callback
        def tasmota_message(msg):
            """Handle Tasmota RF message."""
            asyncio.create_task(self._handle_tasmota_message(msg))
        
        await mqtt.async_subscribe(
            self.hass, "tele/+/RESULT", tasmota_message
        )
        
        # OmniRemote USB/BT Bridge (structured topic)
        @callback
        def bridge_message(msg):
            """Handle OmniRemote bridge message."""
            asyncio.create_task(self._handle_mqtt_bridge_message(msg))
        
        await mqtt.async_subscribe(
            self.hass, "omniremote/bridge/+/event", bridge_message
        )
        
        # Pi Zero W Bridge (simple topic - omniremote/physical_remote)
        @callback
        def pi_bridge_message(msg):
            """Handle Pi Zero W bridge message."""
            asyncio.create_task(self._handle_pi_bridge_message(msg))
        
        await mqtt.async_subscribe(
            self.hass, "omniremote/physical_remote", pi_bridge_message
        )
        _LOGGER.info("[OmniRemote] MQTT listeners registered for Z2M, Tasmota, Bridge, Pi Bridge")
    
    @callback
    async def _handle_zha_event(self, event: Event) -> None:
        """Handle ZHA button press event."""
        data = event.data
        device_ieee = data.get("device_ieee")
        command = data.get("command")
        args = data.get("args", {})
        
        _LOGGER.debug("ZHA event: %s - %s - %s", device_ieee, command, args)
        
        # Find matching remote
        remote = self._find_remote_by_zigbee_ieee(device_ieee)
        if not remote:
            _LOGGER.debug("No remote configured for IEEE %s", device_ieee)
            return
        
        # Determine button ID from command
        button_id = self._zha_command_to_button(command, args)
        
        await self._execute_button_action(remote, button_id)
    
    @callback
    async def _handle_deconz_event(self, event: Event) -> None:
        """Handle deCONZ button press event."""
        data = event.data
        unique_id = data.get("unique_id", "")
        event_type = data.get("event")
        
        _LOGGER.debug("deCONZ event: %s - %s", unique_id, event_type)
        
        # Find matching remote by IEEE (unique_id often contains it)
        remote = self._find_remote_by_zigbee_ieee(unique_id.split("-")[0])
        if not remote:
            return
        
        button_id = str(event_type)
        await self._execute_button_action(remote, button_id)
    
    @callback
    async def _handle_keyboard_remote_event(self, event: Event) -> None:
        """Handle keyboard_remote button press event (Bluetooth HID remotes)."""
        data = event.data
        device_name = data.get("device_name", "")
        key_code = data.get("key_code")
        event_type = data.get("type", "key_down")  # key_up, key_down, key_hold
        
        # Only handle key_down events to avoid double-firing
        if event_type != "key_down":
            return
        
        _LOGGER.info("[OmniRemote] Keyboard remote event: device=%s, key=%s, type=%s", 
                    device_name, key_code, event_type)
        
        # Find matching remote by device name or BT MAC
        remote = self._find_remote_by_bt_device(device_name)
        if not remote:
            _LOGGER.debug("No remote configured for keyboard device: %s", device_name)
            return
        
        # Map key code to button ID
        button_id = self._key_code_to_button(key_code)
        _LOGGER.info("[OmniRemote] Executing button %s on remote %s", button_id, remote.name)
        
        await self._execute_button_action(remote, button_id)
    
    @callback
    async def _handle_state_changed(self, event: Event) -> None:
        """Handle state changes for Bluetooth remote entities."""
        data = event.data
        entity_id = data.get("entity_id", "")
        new_state = data.get("new_state")
        old_state = data.get("old_state")
        
        # Only look at remote/sensor entities that might be Bluetooth remotes
        if not entity_id.startswith(("sensor.", "remote.", "event.")):
            return
        
        # Skip if no new state or same as old
        if not new_state or (old_state and new_state.state == old_state.state):
            return
        
        # Check if this looks like a button press event
        state_value = new_state.state
        if state_value in ("unknown", "unavailable", ""):
            return
        
        # Try to find a matching remote by entity_id
        remote = self._find_remote_by_entity(entity_id)
        if not remote:
            return
        
        _LOGGER.info("[OmniRemote] Bluetooth remote state change: %s -> %s", entity_id, state_value)
        
        # The state value is typically the button name
        button_id = state_value.lower().replace(" ", "_")
        await self._execute_button_action(remote, button_id)
    
    async def _handle_z2m_message(self, msg) -> None:
        """Handle Zigbee2MQTT action message."""
        try:
            # Topic format: zigbee2mqtt/<device_name>/action
            topic_parts = msg.topic.split("/")
            if len(topic_parts) < 3:
                return
            
            device_name = topic_parts[1]
            action = msg.payload
            
            _LOGGER.debug("Z2M action: %s - %s", device_name, action)
            
            # Find remote by device name or friendly name
            remote = self._find_remote_by_name(device_name)
            if not remote:
                return
            
            await self._execute_button_action(remote, action)
        except Exception as ex:
            _LOGGER.error("Error handling Z2M message: %s", ex)
    
    async def _handle_tasmota_message(self, msg) -> None:
        """Handle Tasmota RF Bridge message."""
        try:
            # Topic format: tele/<device>/RESULT
            payload = json.loads(msg.payload)
            
            # Check for RfReceived
            rf_data = payload.get("RfReceived")
            if not rf_data:
                return
            
            rf_code = rf_data.get("Data", "")
            
            _LOGGER.debug("Tasmota RF received: %s", rf_code)
            
            # Find remote by RF code prefix
            remote = self._find_remote_by_rf_code(rf_code)
            if not remote:
                return
            
            # Determine button from code suffix
            button_id = self._rf_code_to_button(rf_code, remote.rf_code_prefix)
            
            await self._execute_button_action(remote, button_id)
        except Exception as ex:
            _LOGGER.error("Error handling Tasmota message: %s", ex)
    
    async def _handle_mqtt_bridge_message(self, msg) -> None:
        """Handle OmniRemote USB/BT bridge message."""
        try:
            # Topic format: omniremote/bridge/<bridge_id>/event
            topic_parts = msg.topic.split("/")
            if len(topic_parts) < 4:
                return
            
            bridge_id = topic_parts[2]
            payload = json.loads(msg.payload)
            
            button_id = payload.get("button") or payload.get("key")
            press_type = payload.get("type", "short")  # short, long, double
            device_name = payload.get("device")
            
            _LOGGER.debug("Bridge event: %s - %s (%s)", bridge_id, button_id, press_type)
            
            # Find remote by bridge and device
            remote = self._find_remote_by_bridge(bridge_id, device_name)
            if not remote:
                return
            
            # Handle press types
            if press_type == "long":
                button_id = f"{button_id}_long"
            elif press_type == "double":
                button_id = f"{button_id}_double"
            
            await self._execute_button_action(remote, button_id)
        except Exception as ex:
            _LOGGER.error("Error handling bridge message: %s", ex)
    
    async def _handle_pi_bridge_message(self, msg) -> None:
        """Handle Pi Zero W bridge message."""
        try:
            # Topic: omniremote/physical_remote
            # Payload: {"device": "G20S", "button": "power", "action": "press"}
            payload = json.loads(msg.payload)
            
            device_name = payload.get("device", "")
            button_id = payload.get("button") or payload.get("key", "")
            action = payload.get("action", "press")
            
            _LOGGER.info("[OmniRemote] Pi bridge event: device=%s, button=%s, action=%s", 
                        device_name, button_id, action)
            
            # Only handle press events (not release)
            if action not in ("press", "key_down", "down"):
                return
            
            # Find matching remote by device name
            remote = self._find_remote_by_bt_device(device_name)
            if not remote:
                # Try to find any Bluetooth remote
                for r in self.database.physical_remotes.values():
                    if r.remote_type in (RemoteType.BLUETOOTH, RemoteType.BLUETOOTH_HA):
                        _LOGGER.info("[OmniRemote] Using first Bluetooth remote: %s", r.name)
                        remote = r
                        break
            
            if not remote:
                _LOGGER.warning("[OmniRemote] No remote found for Pi bridge device: %s", device_name)
                return
            
            await self._execute_button_action(remote, button_id)
        except Exception as ex:
            _LOGGER.error("Error handling Pi bridge message: %s", ex)
    
    @callback
    async def _handle_bridge_event(self, event: Event) -> None:
        """Handle direct bridge events (non-MQTT)."""
        data = event.data
        bridge_id = data.get("bridge_id")
        button_id = data.get("button")
        device_name = data.get("device")
        
        remote = self._find_remote_by_bridge(bridge_id, device_name)
        if not remote:
            return
        
        await self._execute_button_action(remote, button_id)
    
    def _find_remote_by_zigbee_ieee(self, ieee: str) -> PhysicalRemote | None:
        """Find remote by Zigbee IEEE address."""
        for remote in self.database.physical_remotes.values():
            if remote.zigbee_ieee and remote.zigbee_ieee.lower() == ieee.lower():
                return remote
        return None
    
    def _find_remote_by_name(self, name: str) -> PhysicalRemote | None:
        """Find remote by name."""
        for remote in self.database.physical_remotes.values():
            if remote.name.lower() == name.lower():
                return remote
        return None
    
    def _find_remote_by_rf_code(self, code: str) -> PhysicalRemote | None:
        """Find remote by RF code prefix."""
        for remote in self.database.physical_remotes.values():
            if remote.rf_code_prefix and code.startswith(remote.rf_code_prefix):
                return remote
        return None
    
    def _find_remote_by_bridge(self, bridge_id: str, device_name: str | None) -> PhysicalRemote | None:
        """Find remote by bridge ID and optionally device name."""
        for remote in self.database.physical_remotes.values():
            if remote.bridge_id == bridge_id:
                if device_name is None or remote.usb_device_name == device_name:
                    return remote
        return None
    
    def _find_remote_by_bt_device(self, device_name: str) -> PhysicalRemote | None:
        """Find remote by Bluetooth device name or MAC address."""
        device_name_lower = device_name.lower()
        
        for remote in self.database.physical_remotes.values():
            # Check by BT MAC
            if remote.bt_mac:
                mac_clean = remote.bt_mac.lower().replace(":", "").replace("-", "")
                device_clean = device_name_lower.replace(":", "").replace("-", "")
                if mac_clean in device_clean or device_clean in mac_clean:
                    _LOGGER.debug("Matched remote %s by BT MAC %s", remote.name, remote.bt_mac)
                    return remote
            
            # Check by device name
            if remote.usb_device_name and remote.usb_device_name.lower() in device_name_lower:
                _LOGGER.debug("Matched remote %s by device name %s", remote.name, device_name)
                return remote
            
            # Check by remote name
            if remote.name.lower() in device_name_lower or device_name_lower in remote.name.lower():
                _LOGGER.debug("Matched remote %s by name", remote.name)
                return remote
            
            # Check remote type is Bluetooth
            if remote.remote_type in (RemoteType.BLUETOOTH, RemoteType.BLUETOOTH_HA):
                # Check model patterns
                if remote.model_id:
                    from .remote_models import REMOTE_MODELS
                    model = REMOTE_MODELS.get(remote.model_id)
                    if model and model.get("bluetooth_name_pattern"):
                        import re
                        pattern = model["bluetooth_name_pattern"]
                        if re.search(pattern, device_name, re.IGNORECASE):
                            _LOGGER.debug("Matched remote %s by model pattern %s", remote.name, pattern)
                            return remote
        
        return None
    
    def _find_remote_by_entity(self, entity_id: str) -> PhysicalRemote | None:
        """Find remote by Home Assistant entity ID."""
        entity_id_lower = entity_id.lower()
        
        for remote in self.database.physical_remotes.values():
            # Check if entity_id contains remote name or BT MAC
            remote_name_clean = remote.name.lower().replace(" ", "_")
            if remote_name_clean in entity_id_lower:
                return remote
            
            if remote.bt_mac:
                mac_clean = remote.bt_mac.lower().replace(":", "_")
                if mac_clean in entity_id_lower:
                    return remote
        
        return None
    
    def _key_code_to_button(self, key_code) -> str:
        """Convert keyboard key code to button ID."""
        # Map common key codes to button names
        # Key codes can be integers or strings depending on the integration
        key_map = {
            # Power/System
            116: "power", "KEY_POWER": "power",
            142: "sleep", "KEY_SLEEP": "sleep",
            
            # Navigation
            103: "up", "KEY_UP": "up",
            108: "down", "KEY_DOWN": "down",
            105: "left", "KEY_LEFT": "left",
            106: "right", "KEY_RIGHT": "right",
            28: "ok", "KEY_ENTER": "ok", "KEY_OK": "ok",
            96: "ok",  # KP_ENTER
            1: "back", "KEY_ESC": "back", "KEY_BACK": "back",
            102: "home", "KEY_HOME": "home", "KEY_HOMEPAGE": "home",
            139: "menu", "KEY_MENU": "menu",
            
            # Volume
            115: "volume_up", "KEY_VOLUMEUP": "volume_up",
            114: "volume_down", "KEY_VOLUMEDOWN": "volume_down",
            113: "mute", "KEY_MUTE": "mute",
            
            # Media
            164: "play_pause", "KEY_PLAYPAUSE": "play_pause",
            207: "play", "KEY_PLAY": "play",
            119: "pause", "KEY_PAUSE": "pause",
            128: "stop", "KEY_STOP": "stop",
            163: "next", "KEY_NEXTSONG": "next",
            165: "previous", "KEY_PREVIOUSSONG": "previous",
            168: "rewind", "KEY_REWIND": "rewind",
            208: "fast_forward", "KEY_FASTFORWARD": "fast_forward",
            
            # Numbers
            2: "num_1", "KEY_1": "num_1",
            3: "num_2", "KEY_2": "num_2",
            4: "num_3", "KEY_3": "num_3",
            5: "num_4", "KEY_4": "num_4",
            6: "num_5", "KEY_5": "num_5",
            7: "num_6", "KEY_6": "num_6",
            8: "num_7", "KEY_7": "num_7",
            9: "num_8", "KEY_8": "num_8",
            10: "num_9", "KEY_9": "num_9",
            11: "num_0", "KEY_0": "num_0",
            
            # Channel
            402: "channel_up", "KEY_CHANNELUP": "channel_up",
            403: "channel_down", "KEY_CHANNELDOWN": "channel_down",
            
            # Colors (for remotes with colored buttons)
            398: "red", "KEY_RED": "red",
            399: "green", "KEY_GREEN": "green",
            400: "yellow", "KEY_YELLOW": "yellow",
            401: "blue", "KEY_BLUE": "blue",
            
            # Info/Guide
            358: "info", "KEY_INFO": "info",
            362: "guide", "KEY_PROGRAM": "guide",
            
            # Source/Input
            175: "source", "KEY_SETUP": "source", "KEY_INPUT": "source",
        }
        
        # Try to find in map
        button = key_map.get(key_code)
        if button:
            return button
        
        # Try string conversion
        if isinstance(key_code, str):
            # Remove KEY_ prefix if present
            clean_key = key_code.replace("KEY_", "").lower()
            return clean_key
        
        # Default to key code as string
        return f"key_{key_code}"
    
    def _zha_command_to_button(self, command: str, args: dict) -> str:
        """Convert ZHA command to button ID."""
        # Common ZHA commands
        if command in ("on", "off", "toggle", "press", "release"):
            return command
        
        # IKEA commands
        if command == "move_with_on_off":
            return "brightness_up" if args.get("move_mode") == 0 else "brightness_down"
        if command == "move":
            return "brightness_up" if args.get("move_mode") == 0 else "brightness_down"
        if command == "step":
            return "arrow_right" if args.get("step_mode") == 0 else "arrow_left"
        
        # Default to command name
        return command
    
    def _rf_code_to_button(self, code: str, prefix: str) -> str:
        """Convert RF code to button ID based on suffix."""
        suffix = code[len(prefix):] if prefix else code
        
        # Common suffix patterns
        button_map = {
            "1": "button_a", "A": "button_a",
            "2": "button_b", "B": "button_b",
            "3": "button_c", "C": "button_c",
            "4": "button_d", "D": "button_d",
        }
        
        return button_map.get(suffix, f"button_{suffix}")
    
    async def _execute_button_action(self, remote: PhysicalRemote, button_id: str) -> None:
        """Execute the action mapped to a button."""
        mapping = remote.button_mappings.get(button_id)
        if not mapping:
            _LOGGER.debug("No mapping for button %s on remote %s", button_id, remote.name)
            return
        
        _LOGGER.info(
            "Executing action for %s button %s: %s -> %s",
            remote.name, button_id, mapping.action_type.value, mapping.action_target
        )
        
        # Update last seen
        remote.last_seen = datetime.now().isoformat()
        
        # Execute based on action type
        if self._action_callback:
            await self._action_callback(
                remote=remote,
                action_type=mapping.action_type,
                action_target=mapping.action_target,
                action_data=mapping.action_data,
            )
        else:
            await self._default_action_handler(remote, mapping)
    
    async def _default_action_handler(self, remote: PhysicalRemote, mapping: ButtonMapping) -> None:
        """Default action handler when no callback is set."""
        action_type = mapping.action_type
        target = mapping.action_target
        data = mapping.action_data
        
        if action_type == ActionType.HA_SERVICE:
            # Call HA service directly
            domain, service = target.split(".", 1) if "." in target else (target, "turn_on")
            await self.hass.services.async_call(
                domain, service, data, blocking=False
            )
        
        elif action_type == ActionType.SCENE:
            # Run OmniRemote scene
            if hasattr(self.database, "scenes"):
                scene = self.database.scenes.get(target)
                if scene:
                    # Fire event to run scene
                    self.hass.bus.async_fire("omniremote_run_scene", {"scene_id": target})
        
        elif action_type in (ActionType.VOLUME_UP, ActionType.VOLUME_DOWN, 
                            ActionType.MUTE, ActionType.CHANNEL_UP, ActionType.CHANNEL_DOWN):
            # Room-based media control
            await self._execute_room_media_action(remote.room_id, action_type, data)
        
        elif action_type == ActionType.IR_COMMAND:
            # Send IR command - look up the actual broadlink code
            device_id = target or data.get("device_id", "")
            command_name = data.get("command_name", "")
            blaster_id = data.get("blaster_id", "")
            
            # Look up the device and command to get the broadlink code
            broadlink_code = None
            if hasattr(self.database, "devices") and device_id in self.database.devices:
                device = self.database.devices[device_id]
                if command_name and command_name in device.commands:
                    cmd = device.commands[command_name]
                    broadlink_code = cmd.broadlink_code if hasattr(cmd, 'broadlink_code') else cmd.get("broadlink_code")
                    _LOGGER.debug("[OmniRemote] Found IR code for %s/%s", device_id, command_name)
            
            if broadlink_code:
                self.hass.bus.async_fire("omniremote_send_ir", {
                    "device_id": device_id,
                    "command_name": command_name,
                    "blaster_id": blaster_id,
                    "broadlink_code": broadlink_code,
                    "room_id": remote.room_id,
                })
            else:
                _LOGGER.warning("[OmniRemote] No IR code found for device=%s, command=%s", device_id, command_name)
    
    async def _execute_room_media_action(
        self, 
        room_id: str | None, 
        action_type: ActionType,
        data: dict
    ) -> None:
        """Execute a media action for a room (vol up/down, ch up/down, etc.)."""
        # Find the primary media device for this room
        if not room_id:
            _LOGGER.warning("No room_id for media action")
            return
        
        # Look up room's primary devices
        room = self.database.rooms.get(room_id)
        if not room:
            return
        
        # Map action to IR command
        command_map = {
            ActionType.VOLUME_UP: "vol_up",
            ActionType.VOLUME_DOWN: "vol_down",
            ActionType.MUTE: "mute",
            ActionType.CHANNEL_UP: "ch_up",
            ActionType.CHANNEL_DOWN: "ch_down",
        }
        
        command = command_map.get(action_type)
        if not command:
            return
        
        # Find devices in room that have this command
        for device in self.database.devices.values():
            if device.room_id == room_id and command in device.commands:
                self.hass.bus.async_fire("omniremote_send_ir", {
                    "device_id": device.id,
                    "command": command,
                    "room_id": room_id,
                })
                return  # Send to first matching device


# =============================================================================
# Bridge Discovery
# =============================================================================

async def discover_zigbee_remotes(hass: HomeAssistant) -> list[dict]:
    """Discover Zigbee remotes from ZHA/deCONZ."""
    remotes = []
    
    # Try ZHA
    if "zha" in hass.config.components:
        try:
            from homeassistant.components.zha.core.gateway import ZHAGateway
            zha_gateway = hass.data.get("zha", {}).get("gateway")
            if zha_gateway:
                for ieee, device in zha_gateway.devices.items():
                    # Check if device is a remote/button
                    if any(cluster.cluster_id in (6, 8, 768) 
                           for cluster in device.in_clusters.values()):
                        remotes.append({
                            "ieee": str(ieee),
                            "name": device.name,
                            "manufacturer": device.manufacturer,
                            "model": device.model,
                            "type": "zha",
                            "protocol": "zigbee",
                        })
        except Exception as ex:
            _LOGGER.debug("Could not discover ZHA remotes: %s", ex)
    
    return remotes


async def discover_bluetooth_remotes(hass: HomeAssistant) -> list[dict]:
    """Discover Bluetooth remotes via Home Assistant's bluetooth integration."""
    remotes = []
    
    # Import model matching function
    try:
        from .remote_models import get_model_for_bluetooth, REMOTE_MODELS
    except ImportError:
        get_model_for_bluetooth = None
        REMOTE_MODELS = {}
    
    # Known remote name patterns to look for
    REMOTE_NAME_PATTERNS = [
        "remote", "keyboard", "g20", "g10", "air mouse", "gyro", 
        "fire tv", "firetv", "roku", "shield", "apple tv",
        "dupad", "rupa", "wechip", "mele", "minix", "mx3",
        "rii", "ipazzport", "sofabaton", "harmony",
    ]
    
    try:
        # Check if bluetooth component is loaded
        if "bluetooth" not in hass.config.components:
            _LOGGER.debug("Bluetooth component not loaded")
            return remotes
        
        # Get discovered Bluetooth devices
        try:
            from homeassistant.components.bluetooth import async_discovered_service_info
            discovered = async_discovered_service_info(hass)
            
            for service_info in discovered:
                name = service_info.name or ""
                name_lower = name.lower()
                
                # Check if this looks like a remote
                is_remote = any(pattern in name_lower for pattern in REMOTE_NAME_PATTERNS)
                
                # Also check for HID-like service UUIDs (keyboard/mouse)
                # HID UUID: 00001812-0000-1000-8000-00805f9b34fb
                service_uuids = list(service_info.service_uuids or [])
                has_hid = any("1812" in str(uuid).lower() for uuid in service_uuids)
                
                if is_remote or has_hid:
                    manufacturer = service_info.manufacturer or "Unknown"
                    
                    # Try to match to a known model
                    model_match = None
                    if get_model_for_bluetooth:
                        model_match = get_model_for_bluetooth(
                            name, 
                            manufacturer,
                            service_uuids
                        )
                    
                    remote_data = {
                        "mac": service_info.address,
                        "name": name or f"BT Device {service_info.address[-8:]}",
                        "manufacturer": manufacturer,
                        "model": None,
                        "rssi": service_info.rssi,
                        "type": "bluetooth",
                        "protocol": "bluetooth",
                        "has_hid": has_hid,
                        "service_uuids": service_uuids[:5],  # Limit to first 5
                    }
                    
                    # Add model match info if found
                    if model_match:
                        remote_data["suggested_model_id"] = model_match["model_id"]
                        remote_data["suggested_model"] = model_match["model"]
                        remote_data["match_confidence"] = model_match["confidence"]
                        remote_data["match_reason"] = model_match["match_reason"]
                    
                    remotes.append(remote_data)
                    
        except ImportError:
            _LOGGER.debug("Could not import bluetooth discovery functions")
        except Exception as ex:
            _LOGGER.debug("Bluetooth discovery error: %s", ex)
        
        # Also check for already-paired Bluetooth devices in device registry
        try:
            from homeassistant.helpers import device_registry as dr
            device_registry = dr.async_get(hass)
            
            for device in device_registry.devices.values():
                # Check if device has bluetooth connection
                for identifier in device.identifiers:
                    if identifier[0] == "bluetooth":
                        name_lower = (device.name or "").lower()
                        is_remote = any(pattern in name_lower for pattern in REMOTE_NAME_PATTERNS)
                        
                        if is_remote:
                            # Don't add duplicates
                            mac = identifier[1] if len(identifier) > 1 else None
                            if mac and not any(r.get("mac") == mac for r in remotes):
                                manufacturer = device.manufacturer or "Unknown"
                                
                                # Try to match to a known model
                                model_match = None
                                if get_model_for_bluetooth:
                                    model_match = get_model_for_bluetooth(
                                        device.name or "",
                                        manufacturer,
                                        None
                                    )
                                
                                remote_data = {
                                    "mac": mac,
                                    "name": device.name or f"BT Device {mac[-8:]}",
                                    "manufacturer": manufacturer,
                                    "model": device.model,
                                    "type": "bluetooth_paired",
                                    "protocol": "bluetooth",
                                    "paired": True,
                                }
                                
                                if model_match:
                                    remote_data["suggested_model_id"] = model_match["model_id"]
                                    remote_data["suggested_model"] = model_match["model"]
                                    remote_data["match_confidence"] = model_match["confidence"]
                                    remote_data["match_reason"] = model_match["match_reason"]
                                
                                remotes.append(remote_data)
                                
        except Exception as ex:
            _LOGGER.debug("Device registry scan error: %s", ex)
    
    except Exception as ex:
        _LOGGER.warning("Bluetooth remote discovery failed: %s", ex)
    
    return remotes


async def discover_all_remotes(hass: HomeAssistant) -> dict:
    """Discover all types of remotes (Zigbee + Bluetooth)."""
    zigbee_remotes = await discover_zigbee_remotes(hass)
    bluetooth_remotes = await discover_bluetooth_remotes(hass)
    
    return {
        "zigbee": zigbee_remotes,
        "bluetooth": bluetooth_remotes,
        "total": len(zigbee_remotes) + len(bluetooth_remotes),
    }
