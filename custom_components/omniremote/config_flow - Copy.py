"""Config flow for OmniRemote."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class FlipperRemoteManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OmniRemote."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Check if already configured
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        
        if user_input is not None:
            return self.async_create_entry(
                title="OmniRemote",
                data=user_input,
            )
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("import_path", default=""): str,
            }),
            description_placeholders={
                "description": "Set up OmniRemote to control IR/RF devices"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> FlipperRemoteManagerOptionsFlow:
        """Get the options flow."""
        return FlipperRemoteManagerOptionsFlow(config_entry)


class FlipperRemoteManagerOptionsFlow(config_entries.OptionsFlow):
    """Handle options for OmniRemote."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "import_path",
                    default=self.config_entry.options.get("import_path", ""),
                ): str,
            }),
        )
