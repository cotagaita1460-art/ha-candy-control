"""Config flow for Candy Control."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_USE_ENCRYPTION

_LOGGER = logging.getLogger(__name__)

STEP_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS, default="192.168.1.52"): str,
    vol.Optional(CONF_PASSWORD, default="jjdcilaidmaijbfe"): str,
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_DATA_SCHEMA)

        ip = user_input[CONF_IP_ADDRESS]
        password = user_input.get(CONF_PASSWORD, "")

        data = {
            CONF_IP_ADDRESS: ip,
            CONF_USE_ENCRYPTION: bool(password),
            CONF_PASSWORD: password,
        }
        return self.async_create_entry(title="Candy Control", data=data)
