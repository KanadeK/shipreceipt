from __future__ import annotations

import fnmatch
import hashlib
from collections.abc import Iterable
from pathlib import Path

from shipreceipt.errors import UnsafePathError
from shipreceipt.models import FileEntry

DEFAULT_EXCLUDES = (".git", ".git/*", "__pycache__", "__pycache__/*", "*.pyc", "*.pyo")
CHUNK_SIZE = 1024 * 1024


def normalize_excludes(excludes: Iterable[str] | None = None) -> tuple[str, ...]:
    merged = [*DEFAULT_EXCLUDES]
    if excludes:
        merged.extend(pattern.replace("\\", "/") for pattern in excludes)
    return tuple(sorted(dict.fromkeys(pattern for pattern in merged if pattern)))


def collect_files(
    root: str | Path,
    *,
    excludes: Iterable[str] | None = None,
    ignored_paths: Iterable[str | Path] | None = None,
) -> list[FileEntry]:
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise UnsafePathError(f"root is not a directory: {root}")

    ignored = {Path(path).resolve() for path in ignored_paths or ()}
    patterns = normalize_excludes(excludes)
    entries: list[FileEntry] = []

    candidates = sorted(
        root_path.rglob("*"),
        key=lambda candidate: _relative_posix(root_path, candidate),
    )
    for path in candidates:
        resolved = path.resolve()
        if resolved in ignored:
            continue
        rel = _relative_posix(root_path, path)
        if _is_excluded(rel, patterns):
            if path.is_symlink():
                continue
            continue
        if path.is_symlink():
            raise UnsafePathError(f"refusing to follow symbolic link: {rel}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise UnsafePathError(f"unsupported filesystem entry: {rel}")
        entries.append(FileEntry(path=rel, size=path.stat().st_size, sha256=_sha256_file(path)))

    return entries


def _relative_posix(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    return rel.as_posix()


def _is_excluded(path: str, patterns: tuple[str, ...]) -> bool:
    parts = path.split("/")
    for pattern in patterns:
        if fnmatch.fnmatchcase(path, pattern) or any(
            fnmatch.fnmatchcase(part, pattern) for part in parts
        ):
            return True
    return False


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
