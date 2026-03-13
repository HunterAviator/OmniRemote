"""
OmniRemote™ Pi Hub Manager

Discovers and manages Pi Zero Hubs via MQTT auto-discovery.
Hubs announce themselves when they connect to MQTT and are
automatically registered as bridges for IR/Bluetooth/USB remotes.

© 2026 One Eye Enterprises LLC
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant, callback
from homeassistant.components import mqtt
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

MQTT_TOPIC_PREFIX = "omniremote"


@dataclass
class PiHubBridge:
    """A Pi Hub that can be used as an IR/BT/USB bridge."""
    id: str
    hub_id: str
    name: str
    ip: str
    bridge_type: str = "pi_hub"  # pi_hub, broadlink, etc.
    capabilities: dict = field(default_factory=dict)
    status: str = "offline"
    version: str = "unknown"
    room_id: Optional[str] = None  # Room this bridge is assigned to
    
    @property
    def has_ir(self) -> bool:
        return self.capabilities.get("ir_blaster", False)
    
    @property
    def has_bluetooth(self) -> bool:
        return self.capabilities.get("bluetooth", False)
    
    @property
    def has_usb(self) -> bool:
        return self.capabilities.get("usb_hid", True)
    
    @property
    def is_online(self) -> bool:
        return self.status == "online"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "hub_id": self.hub_id,
            "name": self.name,
            "ip": self.ip,
            "bridge_type": self.bridge_type,
            "capabilities": self.capabilities,
            "has_ir": self.has_ir,
            "has_bluetooth": self.has_bluetooth,
            "has_usb": self.has_usb,
            "status": self.status,
            "online": self.is_online,
            "version": self.version,
            "room_id": self.room_id,
        }


class PiHub:
    """Represents a discovered Pi Hub."""
    
    def __init__(self, hub_id: str, config: dict):
        self.hub_id = hub_id
        self.name = config.get("name", f"Pi Hub ({hub_id})")
        self.version = config.get("version", "unknown")
        self.ip = config.get("ip", "unknown")
        self.status = config.get("status", "unknown")
        self.started = config.get("started")
        self.capabilities = config.get("capabilities", {})
        self.web_ui = config.get("web_ui", "")
        self.button_count = config.get("button_count", 0)
        self.devices: list = []
        self.last_seen = datetime.now()
    
    @property
    def is_online(self) -> bool:
        return self.status == "online"
    
    @property
    def has_bluetooth(self) -> bool:
        return self.capabilities.get("bluetooth", False)
    
    @property
    def bluetooth_status(self) -> str:
        return self.capabilities.get("bluetooth_status", "unknown")
    
    @property
    def has_usb(self) -> bool:
        return self.capabilities.get("usb_hid", True)
    
    @property
    def has_ir(self) -> bool:
        return self.capabilities.get("ir_blaster", False)
    
    def to_dict(self) -> dict:
        return {
            "id": self.hub_id,  # For panel.js compatibility
            "hub_id": self.hub_id,
            "name": self.name,
            "version": self.version,
            "ip": self.ip,
            "status": self.status,
            "online": self.is_online,
            "started": self.started,
            "capabilities": self.capabilities,
            "has_bluetooth": self.has_bluetooth,
            "bluetooth_status": self.bluetooth_status,
            "has_usb": self.has_usb,
            "has_ir": self.has_ir,
            "web_ui": self.web_ui,
            "button_count": self.button_count,
            "devices": self.devices,
            "last_seen": self.last_seen.isoformat(),
        }
    
    def to_bridge(self) -> PiHubBridge:
        """Convert to a bridge for use in blaster/bridge lists."""
        return PiHubBridge(
            id=f"pihub_{self.hub_id}",
            hub_id=self.hub_id,
            name=self.name,
            ip=self.ip,
            capabilities=self.capabilities,
            status=self.status,
            version=self.version,
        )


class PiHubManager:
    """Manages Pi Hub discovery and communication via MQTT."""
    
    def __init__(self, hass: HomeAssistant, database):
        self.hass = hass
        self.database = database
        self.hubs: Dict[str, PiHub] = {}
        self.bridges: Dict[str, PiHubBridge] = {}
        self._subscribed = False
        self._unsub_interval = None
    
    async def async_start(self):
        """Start listening for Pi Hub announcements via MQTT."""
        # Check if MQTT is available
        if not await self._mqtt_available():
            _LOGGER.info("MQTT not available - Pi Hub discovery disabled")
            return
        
        try:
            # Subscribe to hub discovery topics
            await mqtt.async_subscribe(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/hub/+/config",
                self._handle_hub_config
            )
            await mqtt.async_subscribe(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/hub/+/status",
                self._handle_hub_status
            )
            await mqtt.async_subscribe(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/hub/+/devices",
                self._handle_hub_devices
            )
            await mqtt.async_subscribe(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/physical_remote",
                self._handle_remote_button
            )
            
            # Subscribe to config sync from HA (for standalone Pi Hubs)
            await mqtt.async_subscribe(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/config/physical_remotes",
                self._handle_config_sync
            )
            await mqtt.async_subscribe(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/config/rooms",
                self._handle_rooms_sync
            )
            
            # Subscribe to sync requests from Pi Hubs
            await mqtt.async_subscribe(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/sync/request",
                self._handle_sync_request
            )
            
            # Subscribe to command requests from Pi Hubs (for sending IR via HA-controlled blasters)
            await mqtt.async_subscribe(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/command",
                self._handle_command_request
            )
            
            self._subscribed = True
            _LOGGER.info("Pi Hub MQTT subscriptions active")
            
            # Request discovery from any connected hubs
            await self._request_discovery()
            
            # Set up periodic cleanup of stale hubs
            self._unsub_interval = async_track_time_interval(
                self.hass, self._cleanup_stale_hubs, timedelta(minutes=5)
            )
            
        except Exception as e:
            _LOGGER.warning("Could not subscribe to MQTT: %s", e)
    
    async def async_stop(self):
        """Stop the manager."""
        if self._unsub_interval:
            self._unsub_interval()
    
    async def _mqtt_available(self) -> bool:
        """Check if MQTT integration is available."""
        return "mqtt" in self.hass.config.components
    
    async def _request_discovery(self):
        """Request all hubs to announce themselves."""
        try:
            await mqtt.async_publish(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/hub/discover",
                json.dumps({"command": "announce"}),
                qos=0
            )
            _LOGGER.debug("Sent hub discovery request")
        except Exception as e:
            _LOGGER.debug("Could not send discovery request: %s", e)
    
    def _register_bridge(self, hub: PiHub):
        """Register a Pi Hub as a bridge in the system."""
        bridge = hub.to_bridge()
        self.bridges[bridge.id] = bridge
        
        # Also add to database.remote_bridges if it exists
        if hasattr(self.database, 'remote_bridges'):
            self.database.remote_bridges[bridge.id] = bridge
        
        _LOGGER.info("Registered Pi Hub bridge: %s (%s)", bridge.name, bridge.id)
    
    @callback
    def _handle_hub_config(self, msg):
        """Handle hub configuration/discovery message."""
        try:
            # Extract hub_id from topic: omniremote/hub/{hub_id}/config
            parts = msg.topic.split("/")
            if len(parts) >= 4:
                hub_id = parts[2]
            else:
                return
            
            payload = json.loads(msg.payload)
            
            if hub_id in self.hubs:
                # Update existing hub
                hub = self.hubs[hub_id]
                hub.name = payload.get("name", hub.name)
                hub.version = payload.get("version", hub.version)
                hub.ip = payload.get("ip", hub.ip)
                hub.status = payload.get("status", "online")
                hub.capabilities = payload.get("capabilities", hub.capabilities)
                hub.web_ui = payload.get("web_ui", hub.web_ui)
                hub.button_count = payload.get("button_count", hub.button_count)
                hub.last_seen = datetime.now()
                _LOGGER.debug("Updated hub: %s", hub_id)
            else:
                # New hub discovered
                hub = PiHub(hub_id, payload)
                self.hubs[hub_id] = hub
                _LOGGER.info("Discovered new Pi Hub: %s at %s", hub.name, hub.ip)
            
            # Auto-register as a bridge
            self._register_bridge(hub)
            
            # Fire event for UI updates
            self.hass.bus.async_fire("omniremote_hub_discovered", {
                "hub_id": hub_id,
                "hub": hub.to_dict()
            })
            
        except Exception as e:
            _LOGGER.error("Error handling hub config: %s", e)
    
    @callback
    def _handle_hub_status(self, msg):
        """Handle hub status update."""
        try:
            parts = msg.topic.split("/")
            if len(parts) >= 4:
                hub_id = parts[2]
            else:
                return
            
            payload = json.loads(msg.payload)
            status = payload.get("status", "unknown")
            
            if hub_id in self.hubs:
                self.hubs[hub_id].status = status
                self.hubs[hub_id].last_seen = datetime.now()
                
                # Update bridge status too
                bridge_id = f"pihub_{hub_id}"
                if bridge_id in self.bridges:
                    self.bridges[bridge_id].status = status
                
                _LOGGER.debug("Hub %s status: %s", hub_id, status)
            
        except Exception as e:
            _LOGGER.debug("Error handling hub status: %s", e)
    
    @callback
    def _handle_hub_devices(self, msg):
        """Handle hub device list update."""
        try:
            parts = msg.topic.split("/")
            if len(parts) >= 4:
                hub_id = parts[2]
            else:
                return
            
            payload = json.loads(msg.payload)
            devices = payload.get("devices", [])
            
            if hub_id in self.hubs:
                self.hubs[hub_id].devices = devices
                self.hubs[hub_id].last_seen = datetime.now()
                _LOGGER.debug("Hub %s has %d devices", hub_id, len(devices))
            
        except Exception as e:
            _LOGGER.debug("Error handling hub devices: %s", e)
    
    @callback
    def _handle_remote_button(self, msg):
        """Handle button press from physical remote."""
        try:
            payload = json.loads(msg.payload)
            hub_id = payload.get("hub_id")
            device = payload.get("device", "unknown")
            button = payload.get("button", "unknown")
            action = payload.get("action", "press")
            
            _LOGGER.debug("Button: %s from %s (hub: %s)", button, device, hub_id)
            
            # Update hub last seen
            if hub_id and hub_id in self.hubs:
                self.hubs[hub_id].last_seen = datetime.now()
                self.hubs[hub_id].button_count = payload.get("button_count", 
                    self.hubs[hub_id].button_count + 1)
            
            # Fire event for automations
            self.hass.bus.async_fire("omniremote_button", {
                "hub_id": hub_id,
                "device": device,
                "button": button,
                "action": action,
            })
            
        except Exception as e:
            _LOGGER.debug("Error handling button: %s", e)
    
    @callback
    def _handle_config_sync(self, msg):
        """Handle physical remotes config sync (legacy - for Pi Hubs subscribing to HA)."""
        # This is for HA receiving config - but HA is source of truth, so we ignore incoming
        _LOGGER.debug("Received config sync message (ignoring - HA is source of truth)")
    
    @callback
    def _handle_rooms_sync(self, msg):
        """Handle rooms config sync (legacy - for Pi Hubs subscribing to HA)."""
        # This is for HA receiving config - but HA is source of truth, so we ignore incoming
        _LOGGER.debug("Received rooms sync message (ignoring - HA is source of truth)")
    
    @callback
    def _handle_sync_request(self, msg):
        """Handle database sync request from Pi Hub."""
        try:
            payload = json.loads(msg.payload)
            hub_id = payload.get("hub_id", "unknown")
            
            _LOGGER.info("📤 Sync request received from Pi Hub: %s", hub_id)
            
            # Publish full database - run async in background
            self.hass.async_create_task(self._publish_full_sync())
            
        except Exception as e:
            _LOGGER.debug("Error handling sync request: %s", e)
    
    @callback
    def _handle_command_request(self, msg):
        """Handle IR command request from Pi Hub standalone UI."""
        try:
            payload = json.loads(msg.payload)
            device_id = payload.get("device_id")
            command_name = payload.get("command")
            blaster_id = payload.get("blaster_id")
            broadlink_code = payload.get("broadlink_code")
            
            _LOGGER.info("📡 Command request from Pi Hub: device=%s, command=%s", device_id, command_name)
            
            # Execute the command via HA in background
            self.hass.async_create_task(
                self._execute_command_request(device_id, command_name, blaster_id, broadlink_code, payload)
            )
            
        except Exception as e:
            _LOGGER.error("Error handling command request: %s", e)
    
    async def _execute_command_request(self, device_id: str, command_name: str, blaster_id: str, broadlink_code: str, payload: dict):
        """Execute an IR command request from Pi Hub."""
        from .const import DOMAIN
        
        try:
            # Get the database
            db = None
            if DOMAIN in self.hass.data:
                for entry_data in self.hass.data[DOMAIN].values():
                    if isinstance(entry_data, dict) and "database" in entry_data:
                        db = entry_data.get("database")
                        break
            
            if not db:
                _LOGGER.warning("Database not found for command request")
                return
            
            # Method 1: If we have device_id and command, look it up
            if device_id and command_name:
                device = db.devices.get(device_id)
                if device:
                    code = device.commands.get(command_name)
                    if code:
                        success = await db.async_send_code(code, blaster_id)
                        _LOGGER.info("Command executed via device lookup: %s", "success" if success else "failed")
                        return
            
            # Method 2: If we have a raw broadlink code, send it directly
            if broadlink_code:
                # Find a blaster to use
                blasters = db.blasters + db.ha_blasters
                target_blaster = None
                
                if blaster_id:
                    target_blaster = next((b for b in blasters if b.get("id") == blaster_id), None)
                if not target_blaster and blasters:
                    target_blaster = blasters[0]
                
                if target_blaster:
                    entity_id = target_blaster.get("entity_id")
                    if entity_id:
                        # Send via HA remote.send_command
                        import base64
                        await self.hass.services.async_call(
                            "remote", "send_command",
                            {"entity_id": entity_id, "command": f"b64:{broadlink_code}"},
                            blocking=True
                        )
                        _LOGGER.info("Command sent via broadlink code to %s", entity_id)
                        return
            
            _LOGGER.warning("Could not execute command: no valid method found")
            
        except Exception as e:
            _LOGGER.error("Error executing command request: %s", e)
    
    async def _publish_full_sync(self):
        """Publish full database sync to MQTT."""
        try:
            from .const import DOMAIN
            
            # Get the database
            db = None
            if DOMAIN in self.hass.data:
                for entry_data in self.hass.data[DOMAIN].values():
                    if isinstance(entry_data, dict) and "database" in entry_data:
                        db = entry_data.get("database")
                        break
            
            if db:
                await db._publish_full_database_sync()
                _LOGGER.info("✅ Full database sync published to MQTT")
            else:
                _LOGGER.warning("Could not find database for sync")
                
        except Exception as e:
            _LOGGER.error("Error publishing sync: %s", e)
    
    async def _cleanup_stale_hubs(self, now=None):
        """Mark hubs as offline if not seen recently."""
        stale_threshold = datetime.now() - timedelta(minutes=10)
        
        for hub_id, hub in self.hubs.items():
            if hub.last_seen < stale_threshold and hub.status == "online":
                hub.status = "offline"
                # Update bridge too
                bridge_id = f"pihub_{hub_id}"
                if bridge_id in self.bridges:
                    self.bridges[bridge_id].status = "offline"
                _LOGGER.info("Hub %s marked offline (not seen recently)", hub_id)
    
    async def async_send_command(self, hub_id: str, command: str, **kwargs):
        """Send a command to a specific hub."""
        if not self._subscribed:
            _LOGGER.warning("MQTT not available")
            return False
        
        try:
            payload = {"command": command, **kwargs}
            await mqtt.async_publish(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/hub/{hub_id}/command",
                json.dumps(payload),
                qos=1
            )
            _LOGGER.info("Sent command '%s' to hub %s", command, hub_id)
            return True
        except Exception as e:
            _LOGGER.error("Error sending command: %s", e)
            return False
    
    async def async_send_ir(self, hub_id: str, code: str, protocol: str = "raw"):
        """Send an IR code via a Pi Hub."""
        if not self._subscribed:
            _LOGGER.warning("MQTT not available")
            return False
        
        try:
            payload = {
                "command": "send_ir",
                "code": code,
                "protocol": protocol,
            }
            await mqtt.async_publish(
                self.hass,
                f"{MQTT_TOPIC_PREFIX}/hub/{hub_id}/ir/send",
                json.dumps(payload),
                qos=1
            )
            _LOGGER.info("Sent IR code to hub %s", hub_id)
            return True
        except Exception as e:
            _LOGGER.error("Error sending IR: %s", e)
            return False
    
    def get_hubs(self) -> list:
        """Get list of all discovered hubs."""
        return [hub.to_dict() for hub in self.hubs.values()]
    
    def get_hub(self, hub_id: str) -> Optional[dict]:
        """Get a specific hub by ID."""
        if hub_id in self.hubs:
            return self.hubs[hub_id].to_dict()
        return None
    
    def get_online_hubs(self) -> list:
        """Get list of online hubs only."""
        return [hub.to_dict() for hub in self.hubs.values() if hub.is_online]
    
    def get_bridges(self) -> list:
        """Get all Pi Hub bridges."""
        return [bridge.to_dict() for bridge in self.bridges.values()]
    
    def get_online_bridges(self) -> list:
        """Get online Pi Hub bridges only."""
        return [bridge.to_dict() for bridge in self.bridges.values() if bridge.is_online]
