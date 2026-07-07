"""Integration for Candy Control."""
from __future__ import annotations

import binascii
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS, CONF_USE_ENCRYPTION

_LOGGER = logging.getLogger(__name__)

START_PROGRAM_SCHEMA = vol.Schema({
    vol.Required("pr_nm"): cv.positive_int,
    vol.Required("pr_code"): cv.string,
    vol.Optional("temp", default=40): vol.All(vol.Coerce(int), vol.In([0, 20, 30, 40, 60, 90])),
    vol.Optional("spin", default=10): vol.All(vol.Coerce(int), vol.Range(min=0, max=16)),
    vol.Optional("steam", default=0): vol.Any(0, 1),
    vol.Optional("dry", default=0): vol.Any(0, 1),
    vol.Optional("delay"): vol.All(vol.Coerce(int), vol.Range(min=0, max=96)),
})


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    ip = config_entry.data[CONF_IP_ADDRESS]
    password = config_entry.data.get(CONF_PASSWORD, "")
    use_encryption = config_entry.data.get(CONF_USE_ENCRYPTION, True)

    data = {
        "ip": ip,
        "password": password,
        "use_encryption": use_encryption,
    }
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = data

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    async def handle_start(call: ServiceCall) -> None:
        params = {
            "StSt": "1",
            "PrNm": str(call.data["pr_nm"]),
            "PrCode": str(call.data["pr_code"]),
            "TmpTgt": str(call.data.get("temp", 40)),
            "SpdTgt": str(call.data.get("spin", 10)),
            "Stm": str(call.data.get("steam", 0)),
            "Dry": str(call.data.get("dry", 0)),
        }
        if call.data.get("delay"):
            params["DelVl"] = str(call.data["delay"])
        await hass.async_add_executor_job(_send_command, data, params)

    async def handle_stop(call: ServiceCall) -> None:
        await hass.async_add_executor_job(_send_command, data, {"StSt": "0"})

    hass.services.async_register(DOMAIN, "start_program", handle_start, schema=START_PROGRAM_SCHEMA)
    hass.services.async_register(DOMAIN, "stop_program", handle_stop)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.services.async_remove(DOMAIN, "start_program")
        hass.services.async_remove(DOMAIN, "stop_program")
    return unload_ok


def _send_command(data: dict, params: dict) -> bool:
    import requests

    ip = data["ip"]
    password = data["password"]
    use_encryption = data["use_encryption"]
    query = "Write=1" + "".join(f"&{k}={v}" for k, v in params.items())

    url = f"http://{ip}/http-write.json?encrypted=1&data="
    if use_encryption and password:
        key = password.encode()
        encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(query.encode()))
        url += binascii.hexlify(encrypted).decode().upper()
    else:
        url += binascii.hexlify(query.encode()).decode().upper()

    try:
        resp = requests.get(url, timeout=5)
        return resp.status_code == 200
    except Exception as err:
        _LOGGER.error("Send command failed: %s", err)
        return False
