"""Button platform for OmniRemote."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
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
    """Set up button entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    database: RemoteDatabase = data["database"]
    
    entities = []
    
    # Create a button for each scene
    for scene in database.scenes.values():
        entities.append(
            FlipperSceneButton(
                hass=hass,
                database=database,
                scene_id=scene.id,
                entry=entry,
            )
        )
    
    # Create discover blasters button
    entities.append(
        FlipperDiscoverButton(
            hass=hass,
            database=database,
            entry=entry,
        )
    )
    
    async_add_entities(entities)


class FlipperSceneButton(ButtonEntity):
    """Button to run a scene."""

    def __init__(
        self,
        hass: HomeAssistant,
        database: RemoteDatabase,
        scene_id: str,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        self.hass = hass
        self._database = database
        self._scene_id = scene_id
        self._entry = entry
        
        scene = database.scenes.get(scene_id)
        
        self._attr_unique_id = f"{entry.entry_id}_btn_{scene_id}"
        self._attr_name = f"Run {scene.name}" if scene else "Run Scene"
        self._attr_icon = scene.icon if scene else "mdi:play"

    async def async_press(self) -> None:
        """Handle button press."""
        scene = self._database.scenes.get(self._scene_id)
        if scene:
            _LOGGER.info("Running scene via button: %s", scene.name)
            await self._database.async_run_scene(self._scene_id)


class FlipperDiscoverButton(ButtonEntity):
    """Button to discover blasters."""

    def __init__(
        self,
        hass: HomeAssistant,
        database: RemoteDatabase,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        self.hass = hass
        self._database = database
        self._entry = entry
        
        self._attr_unique_id = f"{entry.entry_id}_discover"
        self._attr_name = "Discover Blasters"
        self._attr_icon = "mdi:magnify"

    async def async_press(self) -> None:
        """Handle button press."""
        _LOGGER.info("Discovering blasters...")
        blasters = await self._database.async_discover_blasters()
        _LOGGER.info("Found %d blasters", len(blasters))
        
        self.hass.bus.async_fire(
            f"{DOMAIN}_blasters_discovered",
            {"count": len(blasters)},
        )
