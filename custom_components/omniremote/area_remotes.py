"""Area-based Remote Registration for OmniRemote.

Manages remote cards and physical remotes assigned to specific Home Assistant
areas. Provides context-aware control and automatic device targeting.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class AreaRemoteConfig:
    """Configuration for a remote in a specific area."""
    id: str
    area_id: str
    name: str
    remote_type: str  # "card", "bluetooth", "physical"
    
    # Default devices for this area
    default_tv_device: str | None = None
    default_receiver_device: str | None = None
    default_streaming_device: str | None = None
    default_projector_device: str | None = None
    
    # Card configuration
    card_template: str = "tv"
    card_theme: str = "default"
    card_config: dict = field(default_factory=dict)
    
    # Bluetooth remote link
    bluetooth_remote_id: str | None = None
    
    # Activity shortcuts
    quick_activities: list[str] = field(default_factory=list)
    
    # Custom button overrides for this area
    button_overrides: dict[str, dict] = field(default_factory=dict)
    
    # Whether this is the primary remote for the area
    is_primary: bool = False
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "area_id": self.area_id,
            "name": self.name,
            "remote_type": self.remote_type,
            "default_tv_device": self.default_tv_device,
            "default_receiver_device": self.default_receiver_device,
            "default_streaming_device": self.default_streaming_device,
            "default_projector_device": self.default_projector_device,
            "card_template": self.card_template,
            "card_theme": self.card_theme,
            "card_config": self.card_config,
            "bluetooth_remote_id": self.bluetooth_remote_id,
            "quick_activities": self.quick_activities,
            "button_overrides": self.button_overrides,
            "is_primary": self.is_primary,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AreaRemoteConfig":
        return cls(
            id=data["id"],
            area_id=data["area_id"],
            name=data["name"],
            remote_type=data.get("remote_type", "card"),
            default_tv_device=data.get("default_tv_device"),
            default_receiver_device=data.get("default_receiver_device"),
            default_streaming_device=data.get("default_streaming_device"),
            default_projector_device=data.get("default_projector_device"),
            card_template=data.get("card_template", "tv"),
            card_theme=data.get("card_theme", "default"),
            card_config=data.get("card_config", {}),
            bluetooth_remote_id=data.get("bluetooth_remote_id"),
            quick_activities=data.get("quick_activities", []),
            button_overrides=data.get("button_overrides", {}),
            is_primary=data.get("is_primary", False),
        )


@dataclass 
class AreaDeviceMapping:
    """Maps device categories to specific devices in an area."""
    area_id: str
    tv: str | None = None
    receiver: str | None = None
    soundbar: str | None = None
    streaming: str | None = None
    cable_box: str | None = None
    projector: str | None = None
    fan: str | None = None
    ac: str | None = None
    lights: list[str] = field(default_factory=list)
    blinds: list[str] = field(default_factory=list)
    
    def get_device_for_category(self, category: str) -> str | None:
        """Get the device ID for a category."""
        return getattr(self, category, None)
    
    def to_dict(self) -> dict:
        return {
            "area_id": self.area_id,
            "tv": self.tv,
            "receiver": self.receiver,
            "soundbar": self.soundbar,
            "streaming": self.streaming,
            "cable_box": self.cable_box,
            "projector": self.projector,
            "fan": self.fan,
            "ac": self.ac,
            "lights": self.lights,
            "blinds": self.blinds,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AreaDeviceMapping":
        return cls(
            area_id=data["area_id"],
            tv=data.get("tv"),
            receiver=data.get("receiver"),
            soundbar=data.get("soundbar"),
            streaming=data.get("streaming"),
            cable_box=data.get("cable_box"),
            projector=data.get("projector"),
            fan=data.get("fan"),
            ac=data.get("ac"),
            lights=data.get("lights", []),
            blinds=data.get("blinds", []),
        )


class AreaRemoteManager:
    """Manages remote configurations for Home Assistant areas."""
    
    def __init__(self, hass: HomeAssistant, database) -> None:
        self.hass = hass
        self.database = database
        self._area_remotes: dict[str, list[AreaRemoteConfig]] = {}
        self._area_device_mappings: dict[str, AreaDeviceMapping] = {}
        self._area_registry: ar.AreaRegistry | None = None
    
    async def async_setup(self) -> None:
        """Set up the area remote manager."""
        self._area_registry = ar.async_get(self.hass)
        
        # Load saved configurations
        await self._async_load_configs()
        
        # Auto-discover devices in areas
        await self._async_discover_area_devices()
        
        _LOGGER.info(
            "Area remote manager initialized: %d areas configured",
            len(self._area_remotes)
        )
    
    async def _async_load_configs(self) -> None:
        """Load saved area remote configurations."""
        data = await self.database.async_load_area_remotes()
        
        for config_data in data.get("remotes", []):
            config = AreaRemoteConfig.from_dict(config_data)
            if config.area_id not in self._area_remotes:
                self._area_remotes[config.area_id] = []
            self._area_remotes[config.area_id].append(config)
        
        for mapping_data in data.get("device_mappings", []):
            mapping = AreaDeviceMapping.from_dict(mapping_data)
            self._area_device_mappings[mapping.area_id] = mapping
    
    async def async_save_configs(self) -> None:
        """Save area remote configurations."""
        remotes = []
        for area_configs in self._area_remotes.values():
            for config in area_configs:
                remotes.append(config.to_dict())
        
        mappings = [m.to_dict() for m in self._area_device_mappings.values()]
        
        await self.database.async_save_area_remotes({
            "remotes": remotes,
            "device_mappings": mappings,
        })
    
    async def _async_discover_area_devices(self) -> None:
        """Auto-discover OmniRemote devices in each area."""
        if not self._area_registry:
            return
        
        device_registry = dr.async_get(self.hass)
        entity_registry = er.async_get(self.hass)
        
        for area in self._area_registry.async_list_areas():
            area_id = area.id
            
            # Skip if already has manual mapping
            if area_id in self._area_device_mappings:
                continue
            
            mapping = AreaDeviceMapping(area_id=area_id)
            
            # Find devices in this area from our database
            for device in self.database.devices.values():
                if device.room_id:
                    # Check if room matches area
                    room = self.database.get_room(device.room_id)
                    if room and room.name.lower() == area.name.lower():
                        # Map by category
                        category = device.category.value if device.category else "other"
                        if category == "tv" and not mapping.tv:
                            mapping.tv = device.id
                        elif category == "receiver" and not mapping.receiver:
                            mapping.receiver = device.id
                        elif category == "soundbar" and not mapping.soundbar:
                            mapping.soundbar = device.id
                        elif category == "streaming" and not mapping.streaming:
                            mapping.streaming = device.id
                        elif category == "projector" and not mapping.projector:
                            mapping.projector = device.id
                        elif category == "fan" and not mapping.fan:
                            mapping.fan = device.id
                        elif category == "ac" and not mapping.ac:
                            mapping.ac = device.id
            
            if any([mapping.tv, mapping.receiver, mapping.streaming, mapping.projector]):
                self._area_device_mappings[area_id] = mapping
    
    def get_areas(self) -> list[dict[str, Any]]:
        """Get all areas with their remote configurations."""
        if not self._area_registry:
            return []
        
        result = []
        for area in self._area_registry.async_list_areas():
            area_data = {
                "id": area.id,
                "name": area.name,
                "icon": area.icon,
                "remotes": [r.to_dict() for r in self._area_remotes.get(area.id, [])],
                "device_mapping": self._area_device_mappings.get(area.id, AreaDeviceMapping(area.id)).to_dict(),
            }
            result.append(area_data)
        
        return result
    
    def get_area_remotes(self, area_id: str) -> list[AreaRemoteConfig]:
        """Get all remotes configured for an area."""
        return self._area_remotes.get(area_id, [])
    
    def get_primary_remote(self, area_id: str) -> AreaRemoteConfig | None:
        """Get the primary remote for an area."""
        remotes = self._area_remotes.get(area_id, [])
        for remote in remotes:
            if remote.is_primary:
                return remote
        return remotes[0] if remotes else None
    
    async def async_register_remote(
        self,
        area_id: str,
        name: str,
        remote_type: str = "card",
        card_template: str = "tv",
        card_theme: str = "default",
        bluetooth_remote_id: str | None = None,
        is_primary: bool = False,
    ) -> AreaRemoteConfig:
        """Register a new remote for an area."""
        import uuid
        
        remote_id = str(uuid.uuid4())[:8]
        
        # Get device mapping for defaults
        mapping = self._area_device_mappings.get(area_id, AreaDeviceMapping(area_id))
        
        config = AreaRemoteConfig(
            id=remote_id,
            area_id=area_id,
            name=name,
            remote_type=remote_type,
            default_tv_device=mapping.tv,
            default_receiver_device=mapping.receiver,
            default_streaming_device=mapping.streaming,
            default_projector_device=mapping.projector,
            card_template=card_template,
            card_theme=card_theme,
            bluetooth_remote_id=bluetooth_remote_id,
            is_primary=is_primary,
        )
        
        if area_id not in self._area_remotes:
            self._area_remotes[area_id] = []
        
        # If this is primary, unset others
        if is_primary:
            for r in self._area_remotes[area_id]:
                r.is_primary = False
        
        self._area_remotes[area_id].append(config)
        await self.async_save_configs()
        
        _LOGGER.info("Registered remote %s for area %s", name, area_id)
        
        return config
    
    async def async_unregister_remote(self, remote_id: str) -> bool:
        """Unregister a remote."""
        for area_id, remotes in self._area_remotes.items():
            for i, remote in enumerate(remotes):
                if remote.id == remote_id:
                    del remotes[i]
                    await self.async_save_configs()
                    return True
        return False
    
    async def async_update_remote(
        self,
        remote_id: str,
        **kwargs,
    ) -> AreaRemoteConfig | None:
        """Update a remote configuration."""
        for area_id, remotes in self._area_remotes.items():
            for remote in remotes:
                if remote.id == remote_id:
                    for key, value in kwargs.items():
                        if hasattr(remote, key):
                            setattr(remote, key, value)
                    await self.async_save_configs()
                    return remote
        return None
    
    async def async_set_device_mapping(
        self,
        area_id: str,
        category: str,
        device_id: str | None,
    ) -> bool:
        """Set a device mapping for an area."""
        if area_id not in self._area_device_mappings:
            self._area_device_mappings[area_id] = AreaDeviceMapping(area_id)
        
        mapping = self._area_device_mappings[area_id]
        
        if hasattr(mapping, category):
            setattr(mapping, category, device_id)
            await self.async_save_configs()
            return True
        
        return False
    
    def get_device_for_command(
        self,
        area_id: str,
        command: str,
    ) -> str | None:
        """Get the appropriate device for a command in an area.
        
        This provides context-aware device selection based on the command type.
        For example, volume commands go to the receiver if available.
        """
        mapping = self._area_device_mappings.get(area_id)
        if not mapping:
            return None
        
        # Command to device category mapping
        volume_commands = ["volume_up", "volume_down", "mute"]
        navigation_commands = ["up", "down", "left", "right", "ok", "back", "home", "menu"]
        streaming_commands = ["app_netflix", "app_youtube", "app_prime", "app_disney", "app_hulu"]
        channel_commands = ["channel_up", "channel_down"] + [f"num_{i}" for i in range(10)]
        
        if command in volume_commands:
            # Prefer receiver/soundbar for volume
            return mapping.receiver or mapping.soundbar or mapping.tv
        
        if command in streaming_commands:
            # Prefer streaming device
            return mapping.streaming or mapping.tv
        
        if command in channel_commands:
            # Prefer TV or cable box
            return mapping.cable_box or mapping.tv
        
        if command in navigation_commands:
            # Prefer streaming device for nav, then TV
            return mapping.streaming or mapping.tv
        
        if command == "power":
            # TV is primary for power
            return mapping.tv
        
        # Default to TV
        return mapping.tv
    
    def generate_card_config(self, remote_id: str) -> dict[str, Any]:
        """Generate a Lovelace card configuration for a remote."""
        for area_id, remotes in self._area_remotes.items():
            for remote in remotes:
                if remote.id == remote_id:
                    area = self._area_registry.async_get_area(area_id) if self._area_registry else None
                    area_name = area.name if area else area_id
                    
                    # Get the primary device
                    mapping = self._area_device_mappings.get(area_id, AreaDeviceMapping(area_id))
                    primary_device = mapping.tv or mapping.streaming or mapping.projector
                    
                    device = self.database.get_device(primary_device) if primary_device else None
                    
                    config = {
                        "type": "custom:omniremote-card",
                        "device": device.name if device else "",
                        "name": remote.name,
                        "area": area_name,
                        "template": remote.card_template,
                        "theme": remote.card_theme,
                        "bluetooth_remote": remote.bluetooth_remote_id,
                        **remote.card_config,
                    }
                    
                    # Add button overrides
                    if remote.button_overrides:
                        config["custom_buttons"] = remote.button_overrides
                    
                    # Add quick activities
                    if remote.quick_activities:
                        activities = []
                        for act_id in remote.quick_activities:
                            activity = self.database.get_activity(act_id)
                            if activity:
                                activities.append({
                                    "id": act_id,
                                    "name": activity.name,
                                    "icon": activity.icon or "mdi:play",
                                })
                        if activities:
                            config["activities"] = activities
                    
                    return config
        
        return {}
    
    def generate_dashboard_yaml(self, area_id: str | None = None) -> str:
        """Generate YAML for a dashboard with area remotes."""
        import yaml
        
        views = []
        
        areas_to_process = []
        if area_id:
            if self._area_registry:
                area = self._area_registry.async_get_area(area_id)
                if area:
                    areas_to_process.append(area)
        else:
            if self._area_registry:
                areas_to_process = list(self._area_registry.async_list_areas())
        
        for area in areas_to_process:
            remotes = self._area_remotes.get(area.id, [])
            if not remotes:
                continue
            
            cards = []
            for remote in remotes:
                card_config = self.generate_card_config(remote.id)
                if card_config:
                    cards.append(card_config)
            
            if cards:
                view = {
                    "title": area.name,
                    "path": area.id.replace("-", "_"),
                    "icon": area.icon or "mdi:remote",
                    "cards": cards,
                }
                views.append(view)
        
        dashboard = {
            "title": "OmniRemote",
            "views": views,
        }
        
        return yaml.dump(dashboard, default_flow_style=False, allow_unicode=True)


async def async_setup_area_remotes(hass: HomeAssistant, database) -> AreaRemoteManager:
    """Set up area-based remote management."""
    manager = AreaRemoteManager(hass, database)
    await manager.async_setup()
    return manager
