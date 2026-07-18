from datetime import datetime, timezone
from pathlib import Path

import pytest

from shipreceipt.errors import ReceiptFormatError
from shipreceipt.service import create_receipt, verify_receipt

NOW = datetime(2026, 7, 17, 1, 2, 3, tzinfo=timezone.utc)


def test_receipt_is_deterministic_for_the_same_inputs(tmp_path: Path) -> None:
    (tmp_path / "artifact.bin").write_bytes(b"real payload")

    first = create_receipt(tmp_path, label="Release 7", created_at=NOW)
    second = create_receipt(tmp_path, label="Release 7", created_at=NOW)

    assert first == second
    assert first["receipt_id"].startswith("sha256:")
    assert first["manifest_sha256"] == first["receipt_id"].removeprefix("sha256:")


def test_verify_reports_changed_missing_and_added_files(tmp_path: Path) -> None:
    (tmp_path / "change.txt").write_text("before", encoding="utf-8")
    (tmp_path / "missing.txt").write_text("present", encoding="utf-8")
    receipt = create_receipt(tmp_path, created_at=NOW)
    (tmp_path / "change.txt").write_text("after", encoding="utf-8")
    (tmp_path / "missing.txt").unlink()
    (tmp_path / "added.txt").write_text("new", encoding="utf-8")

    report = verify_receipt(receipt, tmp_path)

    assert not report.ok
    assert report.changed == ("change.txt",)
    assert report.missing == ("missing.txt",)
    assert report.added == ("added.txt",)


def test_signed_receipt_requires_the_matching_key(tmp_path: Path) -> None:
    (tmp_path / "artifact.txt").write_text("signed", encoding="utf-8")
    key = b"k" * 32
    receipt = create_receipt(tmp_path, key=key, created_at=NOW)

    assert verify_receipt(receipt, tmp_path, key=key).ok
    assert verify_receipt(receipt, tmp_path).authenticity == "key-required"
    assert not verify_receipt(receipt, tmp_path).ok
    assert verify_receipt(receipt, tmp_path, key=b"w" * 32).authenticity == "invalid"


def test_manifest_tampering_is_detected_before_filesystem_comparison(tmp_path: Path) -> None:
    (tmp_path / "artifact.txt").write_text("payload", encoding="utf-8")
    receipt = create_receipt(tmp_path, created_at=NOW)
    receipt["label"] = "forged"

    report = verify_receipt(receipt, tmp_path)

    assert not report.integrity_ok
    assert not report.ok


def test_unsafe_receipt_path_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "artifact.txt").write_text("payload", encoding="utf-8")
    receipt = create_receipt(tmp_path, created_at=NOW)
    receipt["files"][0]["path"] = "../artifact.txt"

    with pytest.raises(ReceiptFormatError, match="unsafe file path"):
        verify_receipt(receipt, tmp_path)

