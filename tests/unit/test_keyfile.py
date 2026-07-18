from pathlib import Path

import pytest

from shipreceipt.errors import KeyFileError
from shipreceipt.keys import generate_key_file, load_key


def test_key_file_round_trip_and_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "signing.key"

    generated = generate_key_file(path)

    assert len(generated) == 32
    assert load_key(path) == generated
    assert "shipreceipt-key-v1:" in path.read_text(encoding="ascii")
    with pytest.raises(KeyFileError, match="already exists"):
        generate_key_file(path)


def test_malformed_key_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.key"
    path.write_text("not-a-key", encoding="ascii")

    with pytest.raises(KeyFileError, match="invalid key file"):
        load_key(path)

