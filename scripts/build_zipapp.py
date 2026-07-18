from __future__ import annotations

import zipapp
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    source = root / "src"
    dist = root / "dist"
    output = dist / "shipreceipt.pyz"
    dist.mkdir(exist_ok=True)
    if output.exists():
        output.unlink()
    zipapp.create_archive(
        source,
        target=output,
        interpreter="/usr/bin/env python3",
        main="shipreceipt.cli:entrypoint",
        compressed=True,
    )
    size = output.stat().st_size
    print(f"built {output.relative_to(root)} ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
