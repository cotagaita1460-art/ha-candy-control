"""Config flow for Candy Control."""
from __future__ import annotations

import json
import logging
from typing import Any
from urllib import request as url_request
from urllib.error import URLError

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_USE_ENCRYPTION, XOR_KEY_LEN

_LOGGER = logging.getLogger(__name__)

STEP_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_IP_ADDRESS, default="192.168.1.52"): str,
})


async def _detect_encryption(ip: str):
    """Detect encryption type and key for a Candy device."""
    import binascii
    import itertools
    import string

    KEY_CHARS = [ord(c) for c in string.ascii_letters + string.digits]
    PRINTABLE = [ord(c) for c in string.printable]

    def _xor_decrypt(key: bytes, data: bytes) -> bytes:
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    def _candidate_key_codepoints(encrypted: bytes, offset: int):
        check = encrypted[offset::XOR_KEY_LEN]
        for point in KEY_CHARS:
            if all(point ^ b in PRINTABLE for b in check):
                yield point

    def _find_key(encrypted: bytes):
        candidates = [list(_candidate_key_codepoints(encrypted, i)) for i in range(XOR_KEY_LEN)]
        for key in itertools.product(*candidates):
            decrypted = _xor_decrypt(bytes(key), encrypted)
            try:
                json.loads(decrypted)
                return "".join(chr(p) for p in key)
            except json.JSONDecodeError:
                pass
        return None

    status_url = f"http://{ip}/http-read.json?encrypted="

    try:
        req = url_request.Request(status_url + "0", method="GET")
        with url_request.urlopen(req, timeout=5) as resp:
            json.loads(resp.read())
            _LOGGER.info("No encryption needed for %s", ip)
            return False, None
    except Exception:
        pass

    try:
        req = url_request.Request(status_url + "1", method="GET")
        with url_request.urlopen(req, timeout=5) as resp:
            hex_data = resp.read().decode().strip()
            raw = binascii.unhexlify(hex_data)
            try:
                json.loads(raw)
                _LOGGER.info("Encryption flag but no actual encryption for %s", ip)
                return True, ""
            except json.JSONDecodeError:
                key = _find_key(raw)
                if key:
                    _LOGGER.info("Found key for %s: %s", ip, key)
                    return True, key
                raise ValueError("Could not brute-force encryption key")
    except Exception as err:
        raise ValueError(f"Cannot connect to {ip}: {err}") from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_DATA_SCHEMA)

        ip = user_input[CONF_IP_ADDRESS]
        errors = {}

        try:
            use_encryption, key = await self.hass.async_add_executor_job(
                _detect_encryption, ip
            )
        except ValueError as err:
            errors["base"] = "cannot_connect"
            _LOGGER.error("Detection failed: %s", err)
        except Exception as err:
            errors["base"] = "unknown"
            _LOGGER.exception("Unexpected error: %s", err)
        else:
            data = {
                CONF_IP_ADDRESS: ip,
                CONF_USE_ENCRYPTION: use_encryption,
                CONF_PASSWORD: key or "",
            }
            return self.async_create_entry(title="Candy Control", data=data)

        return self.async_show_form(
            step_id="user", data_schema=STEP_DATA_SCHEMA, errors=errors
        )
