# ShipReceipt

ShipReceipt is a local-first command-line tool for creating and verifying
tamper-evident delivery receipts for file bundles. It records every delivered
file path, size, and SHA-256 digest in a deterministic JSON receipt, then can
verify whether the bundle is unchanged later.

ShipReceipt has no runtime dependencies. Optional HMAC-SHA256 signing lets a
team prove that a receipt was created with a shared local signing key.

## Run Example

```console
$ shipreceipt keygen signing.key
KEY CREATED signing.key

$ shipreceipt create ./release-bundle --output release.receipt.json --key signing.key --label v0.1.0
CREATED release.receipt.json files=2 id=sha256:... auth=signed

$ shipreceipt verify release.receipt.json --root ./release-bundle --key signing.key
VERIFIED sha256:...
```

When a file changes, verification returns a non-zero exit code:

```console
$ shipreceipt verify release.receipt.json --root ./release-bundle --key signing.key
FAILED
changed: app.bin
```

## Why This Exists

Small teams often pass build artifacts, datasets, reports, and release bundles
through storage systems that do not provide a simple, portable delivery record.
Checksums help, but a plain checksum file rarely captures paths, sizes,
exclusions, creation metadata, and optional authenticity in one auditable
artifact. ShipReceipt provides that receipt as deterministic JSON.

## Features

- Recursively inventories a directory with streaming SHA-256 hashing.
- Stores relative POSIX paths, file sizes, and content digests.
- Produces deterministic canonical receipt digests for repeatable builds.
- Detects changed, missing, and added files.
- Supports optional HMAC-SHA256 receipt authentication.
- Refuses unsafe receipt paths and local symbolic links.
- Writes receipts atomically.
- Provides `create`, `verify`, `inspect`, and `keygen` CLI commands.

## Install

From a clone:

```console
python -m pip install .
```

For development:

```console
python -m pip install -e ".[dev]"
```

The project also builds a standalone Python zipapp:

```console
python scripts/build_zipapp.py
python dist/shipreceipt.pyz --version
```

## Quick Start

```console
mkdir release-bundle
echo "payload" > release-bundle/artifact.txt
shipreceipt create release-bundle --output release.receipt.json --label first-drop
shipreceipt verify release.receipt.json --root release-bundle
```

Signed receipt flow:

```console
shipreceipt keygen signing.key
shipreceipt create release-bundle --output release.receipt.json --key signing.key
shipreceipt verify release.receipt.json --root release-bundle --key signing.key
```

## Commands

```console
shipreceipt keygen PATH
shipreceipt create ROOT --output RECEIPT [--key KEY] [--label LABEL] [--exclude PATTERN]
shipreceipt verify RECEIPT --root ROOT [--key KEY] [--require-signature]
shipreceipt inspect RECEIPT [--json]
```

`--exclude` uses shell-style patterns such as `*.log` and can be repeated.
ShipReceipt always excludes `.git`, `__pycache__`, and Python bytecode files.

## Configuration

ShipReceipt is configured through command-line flags. It does not read global
configuration files, environment variables, or network services.

Signing keys are local files created by `shipreceipt keygen`. Keep them outside
the delivered directory when possible. If a key or output receipt is inside the
root being scanned, the CLI excludes that path from the inventory for the
current command.

## Architecture

The package is split into small modules:

- `inventory`: filesystem traversal, exclusions, and streaming hashes.
- `service`: receipt creation, manifest digesting, signing, and verification.
- `keys`: local signing key generation and loading.
- `io`: receipt JSON loading and atomic writes.
- `cli`: user-facing command parsing and exit codes.

See [docs/architecture.md](docs/architecture.md) and
[docs/receipt-format.md](docs/receipt-format.md) for details.

## Performance

File contents are hashed in 1 MiB chunks, so memory use does not scale with the
largest file size. The receipt itself is kept in memory because it is intended
to be small compared with the delivered files.

## Security

ShipReceipt is an integrity and authenticity tool, not an encryption tool. It
does not hide file names, sizes, or metadata included in receipts. HMAC signing
only proves that someone with the shared local key created the receipt.

Security policy: [SECURITY.md](SECURITY.md).

## Roadmap

- v0.1.x: stabilize receipt schema and CLI output.
- v0.2.x: add machine-readable verification reports.
- v0.3.x: add optional public-key signature support.
- v0.4.x: add reproducible release bundle helpers.

## Contributing

Contributions are welcome through issues and pull requests. Start with
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

ShipReceipt is released under the MIT License. See [LICENSE](LICENSE).
