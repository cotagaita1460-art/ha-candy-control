"""Button platform for Candy Control."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
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
    async_add_entities([
        CandyStopButton(data, config_entry.entry_id),
        CandyStartSelectedButton(data, config_entry.entry_id),
    ])


class CandyButtonBase(ButtonEntity):
    def __init__(self, data, entry_id: str):
        self._data = data
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
        )

    async def _send_command(self, params: dict) -> bool:
        return await send_command(
            self._data["ip"],
            self._data["password"],
            self._data["use_encryption"],
            params,
            hass=self.hass,
        )


class CandyStopButton(CandyButtonBase):
    @property
    def name(self) -> str:
        return "Detener Lavarropas"

    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}-stop"

    @property
    def icon(self) -> str:
        return "mdi:stop"

    async def async_press(self) -> None:
        _LOGGER.info("Stop button pressed")
        await self._send_command({"StSt": "0", "PrNm": "0", "DelVl": "0"})


class CandyStartSelectedButton(CandyButtonBase):
    @property
    def name(self) -> str:
        return "Iniciar Lavarropas"

    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}-start"

    @property
    def icon(self) -> str:
        return "mdi:play"

    async def async_press(self) -> None:
        programs = self._data.get("programs", DEFAULT_PROGRAMS)
        selected = self._data.get("selected_program", list(programs.keys())[0])
        program = programs.get(selected) or list(programs.values())[0]
        _LOGGER.info("Start button pressed: program=%s", selected)
        await self._send_command({
            "StSt": "1",
            "PrNm": str(program["pr"]),
            "PrCode": program["pr_code"],
            "TmpTgt": str(program["temp"]),
            "SpdTgt": str(program["spin"]),
            "Stm": str(program.get("steam", 0)),
            "Dry": str(program.get("dry", 0)),
        })
