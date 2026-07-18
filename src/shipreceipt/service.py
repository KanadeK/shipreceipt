from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from shipreceipt.canonical import canonical_bytes
from shipreceipt.errors import ReceiptFormatError
from shipreceipt.inventory import collect_files, normalize_excludes
from shipreceipt.models import FileEntry, VerificationReport

SCHEMA = "shipreceipt/v1"


def create_receipt(
    root: str | Path,
    *,
    label: str | None = None,
    key: bytes | None = None,
    created_at: datetime | None = None,
    excludes: tuple[str, ...] | list[str] | None = None,
    ignored_paths: tuple[str | Path, ...] | list[str | Path] | None = None,
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    effective_excludes = normalize_excludes(excludes)
    files = collect_files(root_path, excludes=excludes, ignored_paths=ignored_paths)
    receipt = _base_receipt(root_path, label, created_at, effective_excludes, files)
    _attach_integrity(receipt)
    if key is not None:
        receipt["authentication"] = _authentication(key, _manifest_payload(receipt))
    return receipt


def verify_receipt(
    receipt: dict[str, Any],
    root: str | Path,
    *,
    key: bytes | None = None,
    require_signature: bool = False,
    ignored_paths: tuple[str | Path, ...] | list[str | Path] | None = None,
) -> VerificationReport:
    normalized = _validate_receipt(receipt)
    current_files = collect_files(
        root,
        excludes=tuple(normalized["excludes"]),
        ignored_paths=ignored_paths,
    )
    expected = {entry["path"]: entry for entry in normalized["files"]}
    actual = {entry.path: entry for entry in current_files}

    changed = tuple(
        path
        for path in sorted(expected.keys() & actual.keys())
        if expected[path]["sha256"] != actual[path].sha256
        or expected[path]["size"] != actual[path].size
    )
    missing = tuple(sorted(expected.keys() - actual.keys()))
    added = tuple(sorted(actual.keys() - expected.keys()))
    authenticity = _verify_authentication(normalized, key, require_signature)
    ok = (
        normalized["_integrity_ok"]
        and authenticity in {"unsigned", "valid"}
        and not changed
        and not missing
        and not added
    )
    return VerificationReport(
        ok=ok,
        integrity_ok=normalized["_integrity_ok"],
        authenticity=authenticity,
        changed=changed,
        missing=missing,
        added=added,
    )


def _base_receipt(
    root: Path,
    label: str | None,
    created_at: datetime | None,
    excludes: tuple[str, ...],
    files: list[FileEntry],
) -> dict[str, Any]:
    timestamp = _timestamp(created_at)
    return {
        "schema": SCHEMA,
        "version": 1,
        "created_at": timestamp,
        "label": label,
        "source": {"name": root.name},
        "excludes": list(excludes),
        "files": [entry.to_json() for entry in files],
    }


def _timestamp(value: datetime | None) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def _attach_integrity(receipt: dict[str, Any]) -> None:
    digest = hashlib.sha256(canonical_bytes(_manifest_payload(receipt))).hexdigest()
    receipt["manifest_sha256"] = digest
    receipt["receipt_id"] = f"sha256:{digest}"


def _authentication(key: bytes, payload: dict[str, Any]) -> dict[str, str]:
    return {
        "algorithm": "hmac-sha256",
        "key_id": "sha256:" + hashlib.sha256(key).hexdigest(),
        "signature": hmac.new(key, canonical_bytes(payload), hashlib.sha256).hexdigest(),
    }


def _manifest_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": receipt["schema"],
        "version": receipt["version"],
        "created_at": receipt["created_at"],
        "label": receipt["label"],
        "source": receipt["source"],
        "excludes": receipt["excludes"],
        "files": receipt["files"],
    }


def _validate_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ReceiptFormatError("receipt must be a JSON object")
    normalized = dict(receipt)
    required_fields = (
        "schema",
        "version",
        "created_at",
        "source",
        "excludes",
        "files",
        "manifest_sha256",
        "receipt_id",
    )
    for field in required_fields:
        if field not in normalized:
            raise ReceiptFormatError(f"missing receipt field: {field}")
    if normalized["schema"] != SCHEMA or normalized["version"] != 1:
        raise ReceiptFormatError("unsupported receipt schema")
    if not isinstance(normalized["created_at"], str):
        raise ReceiptFormatError("created_at must be a string")
    if not (isinstance(normalized["label"], str) or normalized["label"] is None):
        raise ReceiptFormatError("label must be a string or null")
    if not isinstance(normalized["source"], dict) or not isinstance(
        normalized["source"].get("name"),
        str,
    ):
        raise ReceiptFormatError("source.name must be a string")
    if not isinstance(normalized["excludes"], list) or not all(
        isinstance(item, str) for item in normalized["excludes"]
    ):
        raise ReceiptFormatError("excludes must be a string list")
    normalized["files"] = _validate_files(normalized["files"])
    payload = _manifest_payload(normalized)
    digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    normalized["_integrity_ok"] = (
        normalized["manifest_sha256"] == digest
        and normalized["receipt_id"] == f"sha256:{digest}"
    )
    return normalized


def _validate_files(files: Any) -> list[dict[str, object]]:
    if not isinstance(files, list):
        raise ReceiptFormatError("files must be a list")
    normalized: list[dict[str, object]] = []
    seen: set[str] = set()
    previous = ""
    for item in files:
        if not isinstance(item, dict):
            raise ReceiptFormatError("file entry must be an object")
        path = item.get("path")
        size = item.get("size")
        digest = item.get("sha256")
        if not isinstance(path, str) or not _is_safe_receipt_path(path):
            raise ReceiptFormatError(f"unsafe file path: {path}")
        if path in seen:
            raise ReceiptFormatError(f"duplicate receipt path: {path}")
        if path < previous:
            raise ReceiptFormatError("receipt files must be sorted by path")
        if not isinstance(size, int) or size < 0:
            raise ReceiptFormatError(f"invalid file size for {path}")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise ReceiptFormatError(f"invalid sha256 for {path}")
        seen.add(path)
        previous = path
        normalized.append({"path": path, "size": size, "sha256": digest})
    return normalized


def _is_safe_receipt_path(path: str) -> bool:
    if not path or "\\" in path:
        return False
    posix = PurePosixPath(path)
    windows = PureWindowsPath(path)
    if posix.is_absolute() or windows.is_absolute():
        return False
    return all(part not in {"", ".", ".."} for part in posix.parts)


def _verify_authentication(
    receipt: dict[str, Any],
    key: bytes | None,
    require_signature: bool,
) -> str:
    auth = receipt.get("authentication")
    if auth is None:
        return "key-required" if require_signature else "unsigned"
    if not isinstance(auth, dict) or auth.get("algorithm") != "hmac-sha256":
        raise ReceiptFormatError("unsupported authentication block")
    signature = auth.get("signature")
    key_id = auth.get("key_id")
    if not isinstance(signature, str) or len(signature) != 64:
        raise ReceiptFormatError("invalid authentication signature")
    if not isinstance(key_id, str):
        raise ReceiptFormatError("invalid authentication key id")
    if key is None:
        return "key-required"
    expected = _authentication(key, _manifest_payload(receipt))
    if not hmac.compare_digest(expected["key_id"], key_id):
        return "invalid"
    return "valid" if hmac.compare_digest(expected["signature"], signature) else "invalid"
