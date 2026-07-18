from pathlib import Path

import pytest

from shipreceipt.errors import UnsafePathError
from shipreceipt.inventory import collect_files


def test_collect_files_is_sorted_and_hashes_real_content(tmp_path: Path) -> None:
    (tmp_path / "z.txt").write_bytes(b"last\n")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "a.txt").write_bytes(b"first\n")

    entries = collect_files(tmp_path)

    assert [entry.path for entry in entries] == ["nested/a.txt", "z.txt"]
    assert entries[0].size == 6
    assert entries[0].sha256 == "b640e840b19d378660b32fb51ae18d67dccb4a8596a29e7bd72c1b2ae5928f41"


def test_collect_files_applies_default_and_user_exclusions(tmp_path: Path) -> None:
    (tmp_path / "keep.txt").write_text("keep", encoding="utf-8")
    (tmp_path / "skip.log").write_text("skip", encoding="utf-8")
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("private", encoding="utf-8")

    entries = collect_files(tmp_path, excludes=("*.log",))

    assert [entry.path for entry in entries] == ["keep.txt"]


def test_collect_files_rejects_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("target", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks are not available for this user")

    with pytest.raises(UnsafePathError, match="symbolic link"):
        collect_files(tmp_path)
