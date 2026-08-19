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
    """Derive the XOR key using known-plaintext attack, with brute-force fallback."""
    known_prefix = b'{\r\n\t"statusLavat'
    if len(encrypted_response) >= len(known_prefix):
        key_bytes = bytes(encrypted_response[i] ^ known_prefix[i] for i in range(len(known_prefix)))
        try:
            key_str = key_bytes.decode("ascii")
            if all(c in string.ascii_letters + string.digits for c in key_str):
                try:
                    decrypted = decrypt(key_bytes, encrypted_response)
                    json.loads(decrypted)
                    _LOGGER.info("Key derived via known-plaintext attack")
                    return key_str
                except (ValueError, json.JSONDecodeError):
                    pass
        except (UnicodeDecodeError, ValueError):
            pass

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
                    _LOGGER.info("Device %s: encrypted without key", device_ip)
                    return Encryption.ENCRYPTION_WITHOUT_KEY, None
                except (ValueError, json.JSONDecodeError):
                    key = await asyncio.to_thread(find_key, raw)
                    if key:
                        _LOGGER.info("Device %s: encryption key found", device_ip)
                        return Encryption.ENCRYPTION, key
        except Exception:  # pylint: disable=broad-except
            pass

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
                        _LOGGER.info("Device %s: no encryption", device_ip)
                        return Encryption.NO_ENCRYPTION, None
        except Exception:  # pylint: disable=broad-except
            pass

    raise ConnectionError("Could not detect encryption for device")


def _decode_write_response(text: str, password: Optional[str]) -> tuple[bool, str]:
    """Decode a write response.

    Returns (success, decoded_text).
    Success = response was decrypted and is valid JSON (device acknowledged).
    The Candy washer returns {"statusLavatrice":{...}} on success, never "SUCCESS".
    """
    body = text.strip()
    if not body:
        return False, "<empty response>"
    if body.startswith("{"):
        try:
            data = json.loads(body)
            if "statusLavatrice" in data:
                return True, body
        except (ValueError, json.JSONDecodeError):
            pass
        return False, body
    if _is_hex(body):
        raw = bytes.fromhex(body)
        if password:
            try:
                decoded = decrypt(password.encode(), raw).decode(errors="replace")
                data = json.loads(decoded)
                if "statusLavatrice" in data:
                    return True, decoded
            except (ValueError, json.JSONDecodeError, KeyError):
                pass
        key = find_key(raw)
        if key:
            try:
                decoded = decrypt(key.encode(), raw).decode(errors="replace")
                data = json.loads(decoded)
                if "statusLavatrice" in data:
                    return True, decoded
            except (ValueError, json.JSONDecodeError, KeyError):
                pass
    return False, repr(body[:200])


async def send_command(ip: str, password: str, use_encryption: bool, params: dict,
                       retries: int = 6, hass=None) -> bool:
    """Send a write command to the device, with retries for flaky servers."""
    query = "Write=1" + "".join(f"&{k}={v}" for k, v in params.items() if v is not None)
    key = password.encode() if password else None
    if use_encryption:
        if key:
            data = bytes(b ^ key[i % len(key)] for i, b in enumerate(query.encode()))
        else:
            data = query.encode()
    else:
        data = query.encode()
    hex_data = binascii.hexlify(data).decode().upper()
    url = _WRITE_URL.format(ip=ip, data=hex_data)
    _LOGGER.info("send_command ip=%s enc=%s has_key=%s query=%s",
                 ip, use_encryption, bool(key), query)

    session = async_get_clientsession(hass) if hass else aiohttp.ClientSession()
    for attempt in range(1, retries + 1):
        try:
            async with async_timeout.timeout(5):
                resp = await session.get(url, headers=_HEADERS)
                text = await resp.text()
            success, result = _decode_write_response(text, password or None)
            _LOGGER.info("Attempt %d: HTTP %d success=%s result=%s",
                         attempt, resp.status, success, result[:200])
            if success:
                _LOGGER.info("Command sent OK: %s", query)
                return True
            if "NO GET" in result or "BAD REQUEST" in result:
                _LOGGER.warning(
                    "Device rejected command (attempt %d): %s "
                    "(is the machine off, busy, or not in remote control mode?)",
                    attempt, result,
                )
            else:
                _LOGGER.warning(
                    "Write not confirmed (attempt %d): HTTP %s %s",
                    attempt, resp.status, result,
                )
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.warning("Write failed (attempt %d): %s", attempt, err)
        await asyncio.sleep(2)
    _LOGGER.error("send_command FAILED after %d attempts for query: %s", retries, query)
    return False
