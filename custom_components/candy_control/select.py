"""Select platform for Candy Control program selection."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .client import send_command
from .const import DOMAIN, DEFAULT_PROGRAMS, MANUFACTURER, DEVICE_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([CandyProgramSelect(hass, data, config_entry.entry_id)])


class CandyProgramSelect(SelectEntity):
    def __init__(self, hass, data, entry_id: str):
        self._data = data
        self._entry_id = entry_id
        programs = data.get("programs", DEFAULT_PROGRAMS)
        self._data["programs"] = programs
        first = list(programs.keys())[0]
        self._data["selected_program"] = first
        self._attr_name = "Programa Lavarropas"
        self._attr_unique_id = f"{entry_id}-program"
        self._attr_icon = "mdi:washing-machine"
        self._attr_options = list(programs.keys())
        self._attr_current_option = first
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
        )

    @property
    def extra_state_attributes(self):
        programs = self._data.get("programs", DEFAULT_PROGRAMS)
        sel = self._attr_current_option
        prog = programs.get(sel, {})
        return {
            "program_code": prog.get("pr_code", ""),
            "temperature": f"{prog.get('temp', 0)}°C",
            "spin_speed": f"{prog.get('spin', 0) * 100} RPM",
            "description": prog.get("desc", ""),
        }

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self._data["selected_program"] = option
        self.async_write_ha_state()
        programs = self._data.get("programs", DEFAULT_PROGRAMS)
        program = programs.get(option)
        if not program:
            _LOGGER.error("Program '%s' not found in program list", option)
            return
        params = {
            "StSt": "1",
            "PrNm": str(program["pr"]),
            "PrCode": program["pr_code"],
            "TmpTgt": str(program["temp"]),
            "SpdTgt": str(program["spin"]),
            "Stm": str(program.get("steam", 0)),
            "Dry": str(program.get("dry", 0)),
        }
        _LOGGER.info("Auto-starting wash: %s -> %s", option, params)
        await send_command(
            self._data["ip"],
            self._data["password"],
            self._data["use_encryption"],
            params,
            hass=self.hass,
        )
