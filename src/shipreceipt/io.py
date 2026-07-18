from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from shipreceipt.errors import ReceiptFormatError


def load_receipt(path: str | Path) -> dict[str, Any]:
    receipt_path = Path(path)
    try:
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReceiptFormatError(f"cannot load receipt: {receipt_path}") from exc
    if not isinstance(data, dict):
        raise ReceiptFormatError("receipt file must contain a JSON object")
    return data


def write_receipt(path: str | Path, receipt: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temp_name, destination)
    except OSError as exc:
        raise ReceiptFormatError(f"cannot write receipt: {destination}") from exc
    finally:
        try:
            if Path(temp_name).exists():
                Path(temp_name).unlink()
        except OSError:
            pass
