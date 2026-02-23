"""Scene platform for OmniRemote."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.scene import Scene
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
    """Set up scene entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    database: RemoteDatabase = data["database"]
    
    entities = []
    
    for scene in database.scenes.values():
        entities.append(
            FlipperScene(
                hass=hass,
                database=database,
                scene_id=scene.id,
                entry=entry,
            )
        )
    
    async_add_entities(entities)
    
    # Register callback for new scenes
    async def async_reload_scenes() -> None:
        """Reload scenes when database changes."""
        # This would be called when scenes are added/removed
        pass


class FlipperScene(Scene):
    """Flipper Remote scene entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        database: RemoteDatabase,
        scene_id: str,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the scene."""
        self.hass = hass
        self._database = database
        self._scene_id = scene_id
        self._entry = entry
        
        scene = database.scenes.get(scene_id)
        
        self._attr_unique_id = f"{entry.entry_id}_scene_{scene_id}"
        self._attr_name = scene.name if scene else "Unknown Scene"
        self._attr_icon = scene.icon if scene else "mdi:play"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        scene = self._database.scenes.get(self._scene_id)
        if not scene:
            return {}
        
        actions = []
        for action in scene.actions:
            device = self._database.devices.get(action.device_id)
            actions.append({
                "device": device.name if device else "Unknown",
                "command": action.command_name,
                "delay": action.delay_after,
            })
        
        return {
            "actions": actions,
            "room": scene.room_id,
        }

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        _LOGGER.info("Activating scene: %s", self._attr_name)
        
        success = await self._database.async_run_scene(self._scene_id)
        
        if success:
            self.hass.bus.async_fire(
                f"{DOMAIN}_scene_activated",
                {"scene": self._attr_name},
            )
