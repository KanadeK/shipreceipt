from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

from shipreceipt import __version__
from shipreceipt.errors import ShipReceiptError
from shipreceipt.io import load_receipt, write_receipt
from shipreceipt.keys import generate_key_file, load_key
from shipreceipt.service import create_receipt, verify_receipt


def entrypoint() -> None:
    raise SystemExit(main())


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        func = cast(Callable[[argparse.Namespace], int], args.func)
        return func(args)
    except ShipReceiptError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shipreceipt",
        description="Create and verify tamper-evident delivery receipts.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(required=True)

    keygen = subparsers.add_parser("keygen", help="Create a local HMAC signing key.")
    keygen.add_argument("path", type=Path)
    keygen.set_defaults(func=_keygen)

    create = subparsers.add_parser("create", help="Create a receipt for a directory.")
    create.add_argument("root", type=Path)
    create.add_argument("--output", "-o", required=True, type=Path)
    create.add_argument("--key", type=Path)
    create.add_argument("--label")
    create.add_argument("--exclude", action="append", default=[])
    create.add_argument("--quiet", action="store_true", help="suppress output except for errors")
    create.set_defaults(func=_create)
    inspect = subparsers.add_parser("inspect", help="Inspect a receipt.")
    inspect.add_argument("receipt", type=Path)
    inspect.add_argument("--json", action="store_true")
    inspect.set_defaults(func=_inspect)

    verify = subparsers.add_parser("verify", help="Verify files against a receipt.")
    verify.add_argument("receipt", type=Path)
    verify.add_argument("--root", required=True, type=Path)
    verify.add_argument("--key", type=Path)
    verify.add_argument("--require-signature", action="store_true")
    verify.set_defaults(func=_verify)
    return parser


def _keygen(args: argparse.Namespace) -> int:
    generate_key_file(args.path)
    print(f"KEY CREATED {args.path}")
    return 0


def _create(args: argparse.Namespace) -> int:
    key = load_key(args.key) if args.key else None
    ignored_paths = _ignored_paths(args.root, args.output, args.key)
    receipt = create_receipt(
        args.root,
        label=args.label,
        key=key,
        excludes=tuple(args.exclude),
        ignored_paths=ignored_paths,
    )
    write_receipt(args.output, receipt)
    if not args.quiet:
        auth = "signed" if "authentication" in receipt else "unsigned"
        print(
            f"CREATED {args.output} "
            f"files={len(receipt['files'])} "
            f"id={receipt['receipt_id']} "
            f"auth={auth}",
        )
    return 0


def _inspect(args: argparse.Namespace) -> int:
    receipt = load_receipt(args.receipt)
    if args.json:
        print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
        return 0
    print(f"Receipt: {receipt.get('receipt_id', 'unknown')}")
    print(f"Files: {len(receipt.get('files', []))}")
    print(f"Label: {receipt.get('label') or '-'}")
    print(f"Authentication: {'signed' if 'authentication' in receipt else 'unsigned'}")
    return 0


def _verify(args: argparse.Namespace) -> int:
    receipt = load_receipt(args.receipt)
    key = load_key(args.key) if args.key else None
    ignored_paths = _ignored_paths(args.root, args.receipt, args.key)
    report = verify_receipt(
        receipt,
        args.root,
        key=key,
        require_signature=args.require_signature,
        ignored_paths=ignored_paths,
    )
    if report.ok:
        print(f"VERIFIED {receipt['receipt_id']}")
        return 0
    print("FAILED")
    if not report.integrity_ok:
        print("integrity: invalid")
    if report.authenticity not in {"unsigned", "valid"}:
        print(f"authenticity: {report.authenticity}")
    for path in report.changed:
        print(f"changed: {path}")
    for path in report.missing:
        print(f"missing: {path}")
    for path in report.added:
        print(f"added: {path}")
    return 1


def _ignored_paths(root: Path, *paths: Path | None) -> tuple[Path, ...]:
    root_resolved = root.resolve()
    ignored: list[Path] = []
    for path in paths:
        if path is None:
            continue
        resolved = path.resolve()
        try:
            resolved.relative_to(root_resolved)
        except ValueError:
            continue
        ignored.append(resolved)
    return tuple(ignored)
