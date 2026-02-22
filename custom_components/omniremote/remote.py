"""Remote platform for OmniRemote."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Iterable

from homeassistant.components.remote import (
    ATTR_COMMAND,
    ATTR_DELAY_SECS,
    ATTR_DEVICE,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    RemoteEntity,
    RemoteEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .database import RemoteDatabase

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up remote entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    database: RemoteDatabase = data["database"]
    
    entities = []
    
    # Create a remote entity for each blaster
    for blaster in database.blasters.values():
        entities.append(
            FlipperRemote(
                hass=hass,
                database=database,
                blaster_id=blaster.id,
                blaster_name=blaster.name,
                entry=entry,
            )
        )
    
    # If no blasters, create a virtual remote
    if not entities:
        entities.append(
            FlipperRemote(
                hass=hass,
                database=database,
                blaster_id=None,
                blaster_name="Flipper Remote",
                entry=entry,
            )
        )
    
    async_add_entities(entities)


class FlipperRemote(RemoteEntity):
    """Flipper Remote entity."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        RemoteEntityFeature.LEARN_COMMAND | RemoteEntityFeature.DELETE_COMMAND
    )

    def __init__(
        self,
        hass: HomeAssistant,
        database: RemoteDatabase,
        blaster_id: str | None,
        blaster_name: str,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the remote."""
        self.hass = hass
        self._database = database
        self._blaster_id = blaster_id
        self._blaster_name = blaster_name
        self._entry = entry
        
        self._attr_unique_id = f"{entry.entry_id}_{blaster_id or 'virtual'}"
        self._attr_name = blaster_name
        self._attr_is_on = True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        summary = self._database.get_summary()
        
        # Build device/command list
        devices = {}
        for device in self._database.devices.values():
            devices[device.name] = {
                "category": device.category.value,
                "commands": list(device.commands.keys()),
            }
        
        return {
            "rooms": [r.name for r in self._database.rooms.values()],
            "devices": devices,
            "scenes": [s.name for s in self._database.scenes.values()],
            "blasters": [b.name for b in self._database.blasters.values()],
            **summary,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the remote on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the remote off."""
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send commands."""
        device_name = kwargs.get(ATTR_DEVICE)
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, 1)
        delay_secs = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        
        for _ in range(num_repeats):
            for cmd in command:
                await self._send_command(cmd, device_name)
                
                if delay_secs > 0:
                    await asyncio.sleep(delay_secs)

    async def _send_command(self, command: str, device_name: str | None) -> None:
        """Send a single command."""
        # Parse command format: device.command or just command
        if "." in command:
            parts = command.rsplit(".", 1)
            device_name = parts[0]
            cmd_name = parts[1]
        else:
            cmd_name = command
        
        if not device_name:
            _LOGGER.error("No device specified for command: %s", command)
            return
        
        device = self._database.get_device_by_name(device_name)
        if not device:
            _LOGGER.error("Device not found: %s", device_name)
            return
        
        code = device.commands.get(cmd_name)
        if not code:
            _LOGGER.error("Command not found: %s.%s", device_name, cmd_name)
            return
        
        success = await self._database.async_send_code(code, self._blaster_id)
        if success:
            _LOGGER.debug("Sent: %s.%s", device_name, cmd_name)
        else:
            _LOGGER.error("Failed to send: %s.%s", device_name, cmd_name)

    async def async_learn_command(self, **kwargs: Any) -> None:
        """Learn a command."""
        device_name = kwargs.get(ATTR_DEVICE, "learned")
        commands = kwargs.get(ATTR_COMMAND, [])
        
        if isinstance(commands, str):
            commands = [commands]
        
        for cmd_name in commands:
            _LOGGER.info("Learning: %s.%s (press remote button...)", device_name, cmd_name)
            
            code = await self._database.async_learn_code(self._blaster_id, timeout=15)
            
            if code:
                # Find or create device
                device = self._database.get_device_by_name(device_name)
                if not device:
                    device = self._database.add_device(name=device_name)
                
                code.name = cmd_name
                self._database.add_command_to_device(device.id, cmd_name, code)
                await self._database.async_save()
                
                _LOGGER.info("Learned: %s.%s", device_name, cmd_name)
                
                self.hass.bus.async_fire(
                    f"{DOMAIN}_code_learned",
                    {"device": device_name, "command": cmd_name},
                )
            else:
                _LOGGER.warning("Failed to learn: %s.%s", device_name, cmd_name)

    async def async_delete_command(self, **kwargs: Any) -> None:
        """Delete a command."""
        device_name = kwargs.get(ATTR_DEVICE)
        commands = kwargs.get(ATTR_COMMAND, [])
        
        if isinstance(commands, str):
            commands = [commands]
        
        device = self._database.get_device_by_name(device_name)
        if not device:
            _LOGGER.error("Device not found: %s", device_name)
            return
        
        for cmd_name in commands:
            if cmd_name in device.commands:
                del device.commands[cmd_name]
                _LOGGER.info("Deleted: %s.%s", device_name, cmd_name)
        
        await self._database.async_save()
