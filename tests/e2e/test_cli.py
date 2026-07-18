import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    source = str(project_root / "src")
    environment["PYTHONPATH"] = source + os.pathsep + environment.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "shipreceipt", *args],
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.e2e
def test_user_can_keygen_create_inspect_and_verify(tmp_path: Path) -> None:
    project_root = Path(__file__).parents[2]
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "deliverable.txt").write_text("customer delivery\n", encoding="utf-8")
    key = tmp_path / "release.key"
    receipt = tmp_path / "delivery.json"

    keygen = run_cli(project_root, "keygen", str(key))
    created = run_cli(
        project_root,
        "create",
        str(bundle),
        "--output",
        str(receipt),
        "--key",
        str(key),
        "--label",
        "Customer A",
    )
    inspected = run_cli(project_root, "inspect", str(receipt), "--json")
    verified = run_cli(
        project_root,
        "verify",
        str(receipt),
        "--root",
        str(bundle),
        "--key",
        str(key),
    )

    assert keygen.returncode == 0, keygen.stderr
    assert created.returncode == 0, created.stderr
    assert inspected.returncode == 0, inspected.stderr
    assert json.loads(inspected.stdout)["label"] == "Customer A"
    assert verified.returncode == 0, verified.stderr
    assert "VERIFIED" in verified.stdout


@pytest.mark.e2e
def test_verify_returns_nonzero_after_real_tampering(tmp_path: Path) -> None:
    project_root = Path(__file__).parents[2]
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    artifact = bundle / "artifact.bin"
    artifact.write_bytes(b"original")
    receipt = tmp_path / "delivery.json"
    assert run_cli(
        project_root, "create", str(bundle), "--output", str(receipt)
    ).returncode == 0
    artifact.write_bytes(b"tampered")

    result = run_cli(project_root, "verify", str(receipt), "--root", str(bundle))

    assert result.returncode == 1
    assert "FAILED" in result.stdout
    assert "artifact.bin" in result.stdout

