"""Switch platform for OmniRemote - Device power control."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DeviceCategory
from .database import RemoteDatabase

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities for device power control."""
    data = hass.data[DOMAIN][entry.entry_id]
    database: RemoteDatabase = data["database"]
    
    entities = []
    
    # Create a switch for each device that has power commands
    for device in database.devices.values():
        # Check if device has any power-related commands
        has_power = any(
            "power" in cmd.lower() 
            for cmd in device.commands.keys()
        )
        
        if has_power:
            entities.append(
                DevicePowerSwitch(
                    hass=hass,
                    database=database,
                    device_id=device.id,
                    entry=entry,
                )
            )
    
    async_add_entities(entities)


class DevicePowerSwitch(SwitchEntity):
    """Switch to control device power state."""

    def __init__(
        self,
        hass: HomeAssistant,
        database: RemoteDatabase,
        device_id: str,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        self.hass = hass
        self._database = database
        self._device_id = device_id
        self._entry = entry
        
        device = database.devices.get(device_id)
        
        self._attr_unique_id = f"{entry.entry_id}_power_{device_id}"
        self._attr_name = f"{device.name} Power" if device else "Device Power"
        self._attr_icon = self._get_icon(device)
        
    def _get_icon(self, device) -> str:
        """Get icon based on device category."""
        if not device:
            return "mdi:power"
        
        icons = {
            DeviceCategory.TV: "mdi:television",
            DeviceCategory.PROJECTOR: "mdi:projector",
            DeviceCategory.RECEIVER: "mdi:speaker",
            DeviceCategory.SOUNDBAR: "mdi:soundbar",
            DeviceCategory.STREAMING: "mdi:cast",
            DeviceCategory.AC: "mdi:air-conditioner",
            DeviceCategory.FAN: "mdi:fan",
            DeviceCategory.LIGHT: "mdi:lightbulb",
        }
        return icons.get(device.category, "mdi:power")

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        device = self._database.devices.get(self._device_id)
        return device.power_state if device else False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self._database.devices.get(self._device_id)
        if not device:
            return {}
        
        attrs = {
            "device_id": device.id,
            "category": device.category.value,
            "brand": device.brand,
            "model": device.model,
            "current_input": device.current_input,
        }
        
        if device.category == DeviceCategory.PROJECTOR:
            attrs["lamp_hours"] = device.lamp_hours
            attrs["lens_position"] = device.lens_position
        
        if device.volume_level is not None:
            attrs["volume_level"] = device.volume_level
            attrs["muted"] = device.muted
        
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        device = self._database.devices.get(self._device_id)
        if not device:
            return
        
        # Find power on command
        cmd_name = device.power_on_command
        if not cmd_name:
            # Try common power command names
            for name in ["power_on", "power", "on"]:
                if name in device.commands:
                    cmd_name = name
                    break
        
        if cmd_name and cmd_name in device.commands:
            code = device.commands[cmd_name]
            success = await self._database.async_send_code(code)
            
            if success:
                device.power_state = True
                await self._database.async_save()
                self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        device = self._database.devices.get(self._device_id)
        if not device:
            return
        
        # Find power off command
        cmd_name = device.power_off_command
        if not cmd_name:
            # Try common power command names
            for name in ["power_off", "power", "off"]:
                if name in device.commands:
                    cmd_name = name
                    break
        
        if cmd_name and cmd_name in device.commands:
            code = device.commands[cmd_name]
            success = await self._database.async_send_code(code)
            
            if success:
                device.power_state = False
                await self._database.async_save()
                self.async_write_ha_state()
