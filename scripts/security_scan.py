from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

PATTERNS = {
    "env file": re.compile(r"(^|/)\.env(\.|$)"),
    "github token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "password assignment": re.compile(r"(?i)\bpassword\s*[:=]\s*['\"][^'\"]+['\"]"),
    "credential assignment": re.compile(r"(?i)\bcredentials?\s*[:=]\s*['\"][^'\"]+['\"]"),
    "windows home path": re.compile(r"C:\\Users\\[^\\\s]+", re.IGNORECASE),
}

SKIP_PARTS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "dist", "build"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures: list[str] = []
    for path in _candidate_files(root):
        rel = path.relative_to(root).as_posix()
        data = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in PATTERNS.items():
            if pattern.search(rel) or pattern.search(data):
                failures.append(f"{rel}: {name}")
    if failures:
        for failure in failures:
            print(f"SECURITY FINDING {failure}")
        return 1
    print("security scan passed")
    return 0


def _candidate_files(root: Path) -> list[Path]:
    try:
        git = shutil.which("git")
        if git is None:
            raise OSError("git not found")
        result = subprocess.run(
            [git, "ls-files", "--others", "--cached", "--exclude-standard"],
            cwd=root,
            text=True,
            check=True,
            capture_output=True,
        )
        return [root / line for line in result.stdout.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        return [
            path
            for path in root.rglob("*")
            if path.is_file() and not set(path.relative_to(root).parts) & SKIP_PARTS
        ]


if __name__ == "__main__":
    raise SystemExit(main())
