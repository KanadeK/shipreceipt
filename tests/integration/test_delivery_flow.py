import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from shipreceipt.io import load_receipt, write_receipt
from shipreceipt.keys import generate_key_file, load_key
from shipreceipt.service import create_receipt, verify_receipt


@pytest.mark.integration
def test_signed_receipt_survives_serialization_and_verifies_real_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "app.exe").write_bytes(bytes(range(256)) * 4)
    (bundle / "manual.txt").write_text("Run app.exe\n", encoding="utf-8")
    key_path = tmp_path / "release.key"
    key = generate_key_file(key_path)
    output = tmp_path / "delivery.receipt.json"
    receipt = create_receipt(
        bundle,
        label="Desktop delivery",
        key=key,
        created_at=datetime(2026, 7, 17, tzinfo=timezone.utc),
    )

    write_receipt(output, receipt)
    on_disk = load_receipt(output)
    report = verify_receipt(on_disk, bundle, key=load_key(key_path))

    assert report.ok
    assert report.authenticity == "valid"
    assert json.loads(output.read_text(encoding="utf-8"))["files"][0]["path"] == "app.exe"

