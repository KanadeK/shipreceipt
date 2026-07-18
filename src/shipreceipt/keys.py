from __future__ import annotations

import base64
import secrets
from contextlib import suppress
from pathlib import Path

from shipreceipt.errors import KeyFileError

KEY_PREFIX = "shipreceipt-key-v1:"
KEY_SIZE = 32


def generate_key_file(path: str | Path) -> bytes:
    key = secrets.token_bytes(KEY_SIZE)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = KEY_PREFIX + base64.urlsafe_b64encode(key).decode("ascii") + "\n"
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise KeyFileError(f"key file already exists: {destination}") from exc
    except OSError as exc:
        raise KeyFileError(f"cannot write key file: {destination}") from exc
    with suppress(OSError):
        destination.chmod(0o600)
    return key


def load_key(path: str | Path) -> bytes:
    key_path = Path(path)
    try:
        text = key_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise KeyFileError(f"cannot read key file: {key_path}") from exc
    if not text.startswith(KEY_PREFIX):
        raise KeyFileError("invalid key file format")
    encoded = text[len(KEY_PREFIX) :]
    try:
        key = base64.urlsafe_b64decode(encoded.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise KeyFileError("invalid key file material") from exc
    if len(key) != KEY_SIZE:
        raise KeyFileError("invalid key file length")
    return key
