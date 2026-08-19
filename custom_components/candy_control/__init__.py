"""Integration for Candy Control."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .client import send_command
from .const import DOMAIN, PLATFORMS, CONF_USE_ENCRYPTION, DEFAULT_PROGRAMS

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

SET_PROGRAMS_SCHEMA = vol.Schema({
    vol.Required("programs"): vol.All(
        cv.ensure_list,
        [vol.Schema({
            vol.Required("name"): cv.string,
            vol.Required("pr"): cv.positive_int,
            vol.Required("pr_code"): cv.string,
            vol.Optional("temp", default=40): int,
            vol.Optional("spin", default=10): int,
            vol.Optional("desc", default=""): cv.string,
        })],
    ),
})


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    ip = config_entry.data[CONF_IP_ADDRESS]
    password = config_entry.data.get(CONF_PASSWORD, "")
    use_encryption = config_entry.data.get(CONF_USE_ENCRYPTION, True)

    # Merge programs from options with defaults
    stored = config_entry.options.get("programs", {})
    programs = {**DEFAULT_PROGRAMS, **stored}

    data = {
        "ip": ip,
        "password": password,
        "use_encryption": use_encryption,
        "programs": programs,
        "selected_program": list(programs.keys())[0],
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
        await send_command(data["ip"], data["password"], data["use_encryption"], params, hass=hass)

    async def handle_stop(call: ServiceCall) -> None:
        await send_command(data["ip"], data["password"], data["use_encryption"], {"StSt": "0"}, hass=hass)

    async def handle_set_programs(call: ServiceCall) -> None:
        new_programs = {}
        for p in call.data["programs"]:
            new_programs[p["name"]] = {
                "pr": p["pr"],
                "pr_code": p["pr_code"],
                "temp": p.get("temp", 40),
                "spin": p.get("spin", 10),
                "desc": p.get("desc", ""),
            }
        merged = {**DEFAULT_PROGRAMS, **new_programs}
        data["programs"] = merged
        hass.config_entries.async_update_entry(
            config_entry, options={**config_entry.options, "programs": new_programs}
        )
        _LOGGER.info("Programs updated: %d total", len(merged))

    hass.services.async_register(
        DOMAIN, "start_program", handle_start, schema=START_PROGRAM_SCHEMA
    )
    hass.services.async_register(DOMAIN, "stop_program", handle_stop)
    hass.services.async_register(
        DOMAIN, "set_programs", handle_set_programs, schema=SET_PROGRAMS_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.services.async_remove(DOMAIN, "start_program")
        hass.services.async_remove(DOMAIN, "stop_program")
        hass.services.async_remove(DOMAIN, "set_programs")
    return unload_ok
