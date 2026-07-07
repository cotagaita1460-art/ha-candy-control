"""Select platform for Candy Control program selection."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, PROGRAMS, MANUFACTURER, DEVICE_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([CandyProgramSelect(hass, data, config_entry.entry_id)])


class CandyProgramSelect(SelectEntity):
    def __init__(self, hass, data, entry_id: str):
        self._hass = hass
        self._data = data
        self._entry_id = entry_id
        self._data["selected_program"] = list(PROGRAMS.keys())[0]
        self._attr_name = "Programa Lavarropas"
        self._attr_unique_id = f"{entry_id}-program"
        self._attr_icon = "mdi:washing-machine"
        self._attr_options = list(PROGRAMS.keys())
        self._attr_current_option = list(PROGRAMS.keys())[0]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
        )

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self._data["selected_program"] = option
        self.async_write_ha_state()
