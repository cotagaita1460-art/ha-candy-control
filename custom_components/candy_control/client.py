"""Client utilities for Candy Control.

Handles device discovery, XOR decryption key detection and command sending
for Candy / Simply-Fi appliances.
"""
from __future__ import annotations

import asyncio
import binascii
import itertools
import json
import logging
import math
import socket
import string
from typing import Iterable, Optional

import aiohttp
import async_timeout
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

KEY_LEN = 16
_KEY_CHARSET_CODEPOINTS = [ord(c) for c in string.ascii_letters + string.digits]
_PLAINTEXT_CHARSET_CODEPOINTS = [ord(c) for c in string.printable]
_HEADERS = {"Connection": "close"}
_MAX_KEY_CANDIDATES = 1_000_000
_WRITE_URL = "http://{ip}/http-write.json?encrypted=1&data={data}"
_READ_URL = "http://{ip}/http-read.json?encrypted={encrypted}"


class Encryption:
    """Encryption mode of the device."""

    NO_ENCRYPTION = 1
    ENCRYPTION = 2
    ENCRYPTION_WITHOUT_KEY = 3


def decrypt(key: bytes, encrypted_response: bytes) -> bytes:
    """XOR decrypt the response using a repeating key."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted_response))


def _is_hex(text: str) -> bool:
    text = text.strip()
    if not text or len(text) % 2 != 0 or len(text) < 8:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in text)


def _find_candidate_key_codepoints(encrypted: bytes, offset: int) -> Iterable[int]:
    bytes_to_check = encrypted[offset::KEY_LEN]
    for point in _KEY_CHARSET_CODEPOINTS:
        if all(point ^ byte in _PLAINTEXT_CHARSET_CODEPOINTS for byte in bytes_to_check):
            yield point


def find_key(encrypted_response: bytes) -> Optional[str]:
    """Brute force the 16-byte alphanumeric XOR key from an encrypted response."""
    candidates = [
        list(_find_candidate_key_codepoints(encrypted_response, i)) for i in range(KEY_LEN)
    ]
    if not all(candidates):
        return None
    total = math.prod(len(c) for c in candidates)
    if total > _MAX_KEY_CANDIDATES:
        _LOGGER.warning("Too many key candidates (%d), giving up", total)
        return None
    for key in itertools.product(*candidates):
        try:
            json.loads(decrypt(key, encrypted_response))
        except (ValueError, json.JSONDecodeError):
            continue
        return "".join(chr(point) for point in key)
    return None


def _get_source_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 80))
        return sock.getsockname()[0]
    finally:
        sock.close()


async def discover_devices(hass) -> list[str]:
    """Scan the local /24 subnet for Candy appliances and return their IPs."""
    local_ip = await hass.async_add_executor_job(_get_source_ip)
    network = ".".join(local_ip.split(".")[:3])
    hosts = [f"{network}.{i}" for i in range(1, 255) if f"{network}.{i}" != local_ip]

    session = async_get_clientsession(hass)
    semaphore = asyncio.Semaphore(60)
    async def probe(host: str) -> Optional[str]:
        async with semaphore:
            try:
                async with async_timeout.timeout(1.5):
                    resp = await session.get(
                        _READ_URL.format(ip=host, encrypted=1), headers=_HEADERS
                    )
                    text = await resp.text()
                    if _is_hex(text):
                        return host
            except Exception:  # pylint: disable=broad-except
                pass
        return None

    results = await asyncio.gather(*(probe(host) for host in hosts))
    return sorted(ip for ip in results if ip)


async def detect_encryption(session, device_ip: str):
    """Determine the encryption mode and recover the XOR key if needed."""
    for _attempt in range(4):
        try:
            async with async_timeout.timeout(5):
                resp = await session.get(
                    _READ_URL.format(ip=device_ip, encrypted=0), headers=_HEADERS
                )
                text = await resp.text()
                if text.strip().startswith("{"):
                    data = json.loads(text)
                    if isinstance(data, dict) and not data.get("response"):
                        return Encryption.NO_ENCRYPTION, None
        except Exception:  # pylint: disable=broad-except
            pass

    for _attempt in range(6):
        try:
            async with async_timeout.timeout(5):
                resp = await session.get(
                    _READ_URL.format(ip=device_ip, encrypted=1), headers=_HEADERS
                )
                text = await resp.text()
                if not _is_hex(text):
                    continue
                raw = bytes.fromhex(text)
                try:
                    json.loads(raw)
                    return Encryption.ENCRYPTION_WITHOUT_KEY, None
                except (ValueError, json.JSONDecodeError):
                    key = await asyncio.to_thread(find_key, raw)
                    if key:
                        return Encryption.ENCRYPTION, key
        except Exception:  # pylint: disable=broad-except
            pass

    raise ConnectionError("Could not detect encryption for device")


def _decode_write_response(text: str, password: Optional[str]) -> str:
    """Decode a write response (plaintext JSON, encrypted hex or empty)."""
    body = text.strip()
    if not body:
        return "<empty response>"
    if body.startswith("{"):
        return body
    if password and _is_hex(body):
        try:
            return decrypt(password.encode(), bytes.fromhex(body)).decode(errors="replace")
        except ValueError:
            pass
    return repr(body[:80])


async def send_command(ip: str, password: str, use_encryption: bool, params: dict,
                       retries: int = 6, hass=None) -> bool:
    """Send a write command to the device, with retries for flaky servers."""
    query = "Write=1" + "".join(f"&{k}={v}" for k, v in params.items() if v is not None)
    if use_encryption and password:
        key = password.encode()
        data = bytes(b ^ key[i % len(key)] for i, b in enumerate(query.encode()))
    else:
        data = query.encode()
    url = _WRITE_URL.format(ip=ip, data=binascii.hexlify(data).decode().upper())

    session = async_get_clientsession(hass) if hass else aiohttp.ClientSession()
    for attempt in range(1, retries + 1):
        try:
            async with async_timeout.timeout(5):
                resp = await session.get(url, headers=_HEADERS)
                text = await resp.text()
            result = _decode_write_response(
                text, password if use_encryption else None
            )
            if "SUCCESS" in result:
                _LOGGER.info("Command sent: %s -> %s", query, result)
                return True
            if "NO GET" in result or "BAD REQUEST" in result:
                _LOGGER.warning(
                    "Device did not accept the command (attempt %d): %s %s",
                    attempt,
                    result,
                    "(machine off, busy or not in remote control mode?)",
                )
            else:
                _LOGGER.warning(
                    "Write not confirmed (attempt %d): HTTP %s %s",
                    attempt,
                    resp.status,
                    result,
                )
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.warning("Write failed (attempt %d): %s", attempt, err)
        await asyncio.sleep(2)
    return False
