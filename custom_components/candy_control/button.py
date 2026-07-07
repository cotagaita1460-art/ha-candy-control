"""Button platform for Candy Control."""
from __future__ import annotations

import binascii
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_USE_ENCRYPTION, PROGRAMS, MANUFACTURER, DEVICE_NAME

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

    def _xor_crypt(self, data_bytes: bytes) -> bytes:
        key = self._data["password"].encode()
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data_bytes))

    def _send_command(self, params: dict) -> bool:
        import requests
        ip = self._data["ip"]
        use_encryption = self._data["use_encryption"]
        query = "Write=1" + "".join(f"&{k}={v}" for k, v in params.items())
        url = f"http://{ip}/http-write.json?encrypted=1&data="
        if use_encryption and self._data["password"]:
            encrypted = self._xor_crypt(query.encode())
            url += binascii.hexlify(encrypted).decode().upper()
        else:
            url += binascii.hexlify(query.encode()).decode().upper()
        try:
            resp = requests.get(url, timeout=5)
            return resp.status_code == 200
        except Exception as err:
            _LOGGER.error("Command failed: %s", err)
            return False


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
        await self.hass.async_add_executor_job(self._send_command, {"StSt": "0"})


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
        selected = self._data.get("selected_program", "DIARIO 39'")
        program = PROGRAMS.get(selected) or PROGRAMS["DIARIO 39'"]
        await self.hass.async_add_executor_job(
            self._send_command, {
                "StSt": "1",
                "PrNm": str(program["pr"]),
                "PrCode": program["pr_code"],
                "TmpTgt": str(program["temp"]),
                "SpdTgt": str(program["spin"]),
            }
        )
