"""Config flow for Candy Control."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import async_timeout
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import (
    Encryption, detect_encryption, discover_devices, find_key,
    _is_hex, _READ_URL,
)
from .const import DOMAIN, CONF_USE_ENCRYPTION

_LOGGER = logging.getLogger(__name__)

STEP_MANUAL_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS): str,
    vol.Optional(CONF_PASSWORD, default=""): str,
})

STEP_DISCOVER_SCHEMA = vol.Schema({
    vol.Required("scan", default=True): bool,
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Candy Control."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Offer automatic discovery or manual setup."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["discover", "manual"],
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Set up the appliance manually."""
        errors: dict[str, str] = {}
        if user_input is not None:
            ip = user_input.get(CONF_IP_ADDRESS, "").strip()
            password = user_input.get(CONF_PASSWORD, "").strip()
            if not ip:
                errors[CONF_IP_ADDRESS] = "invalid_ip"
            elif password:
                return await self._create_entry(ip, True, password)
            else:
                try:
                    async with async_timeout.timeout(60):
                        use_encryption, key = await self._detect(ip)
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Error detecting key for %s", ip)
                    errors["base"] = "detect_encryption"
                else:
                    return await self._create_entry(ip, use_encryption, key or "")

        return self.async_show_form(
            step_id="manual",
            data_schema=STEP_MANUAL_SCHEMA,
            errors=errors,
        )

    async def async_step_discover(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Scan the local network for Candy appliances."""
        if user_input is None:
            return self.async_show_form(step_id="discover", data_schema=STEP_DISCOVER_SCHEMA)

        try:
            async with async_timeout.timeout(90):
                devices = await discover_devices(self.hass)
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Error during discovery")
            devices = []

        if not devices:
            return self.async_show_form(
                step_id="discover",
                data_schema=STEP_DISCOVER_SCHEMA,
                errors={"base": "no_devices_found"},
            )

        self._discovered_devices = devices
        if len(devices) == 1:
            return await self._configure_discovered(devices[0], from_step="discover")
        return await self._show_device_step()

    async def async_step_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Pick the appliance from the discovered devices."""
        devices = getattr(self, "_discovered_devices", [])
        if not devices:
            return self.async_abort(reason="no_devices_found")
        if user_input is None:
            return await self._show_device_step()
        return await self._configure_discovered(user_input["device"], from_step="device")

    async def _show_device_step(self, errors: dict[str, str] | None = None) -> FlowResult:
        schema = vol.Schema({vol.Required("device"): vol.In(self._discovered_devices)})
        return self.async_show_form(step_id="device", data_schema=schema, errors=errors)

    async def _configure_discovered(self, ip: str, from_step: str) -> FlowResult:
        try:
            async with async_timeout.timeout(60):
                use_encryption, key = await self._detect(ip)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error detecting key for %s", ip)
            if from_step == "device":
                return await self._show_device_step(errors={"base": "detect_encryption"})
            return self.async_show_form(
                step_id="discover",
                data_schema=STEP_DISCOVER_SCHEMA,
                errors={"base": "detect_encryption"},
            )
        return await self._create_entry(ip, use_encryption, key or "")

    async def _detect(self, ip: str):
        session = async_get_clientsession(self.hass)
        encryption, key = await detect_encryption(session, ip)
        _LOGGER.info("Detection for %s: encryption=%s key=%s", ip, encryption, bool(key))
        if encryption == Encryption.NO_ENCRYPTION:
            for _attempt in range(6):
                try:
                    async with async_timeout.timeout(5):
                        resp = await session.get(
                            _READ_URL.format(ip=ip, encrypted=1), headers=_HEADERS
                        )
                        text = await resp.text()
                        if _is_hex(text):
                            raw = bytes.fromhex(text)
                            found_key = await asyncio.to_thread(find_key, raw)
                            if found_key:
                                _LOGGER.info("Key recovered from encrypted read for %s", ip)
                                return True, found_key
                except Exception:  # pylint: disable=broad-except
                    pass
            return False, ""
        if encryption == Encryption.ENCRYPTION_WITHOUT_KEY:
            return True, ""
        return True, key or ""

    async def _create_entry(self, ip: str, use_encryption: bool, password: str) -> FlowResult:
        await self.async_set_unique_id(ip)
        self._abort_if_unique_id_configured()
        data = {
            CONF_IP_ADDRESS: ip,
            CONF_USE_ENCRYPTION: use_encryption,
            CONF_PASSWORD: password,
        }
        return self.async_create_entry(title="Candy Control", data=data)
