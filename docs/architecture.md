# Architecture

ShipReceipt is designed as a small local CLI with no runtime dependencies.

## Data Flow

1. The CLI receives a root directory and optional signing key.
2. `inventory.collect_files` walks the directory in sorted order.
3. Each file is hashed in 1 MiB chunks with SHA-256.
4. `service.create_receipt` builds a manifest payload and hashes its canonical
   JSON form.
5. When a key is provided, the same canonical payload is signed with
   HMAC-SHA256.
6. `io.write_receipt` atomically writes the JSON receipt.
7. `service.verify_receipt` validates receipt structure, recomputes the
   manifest digest, verifies optional HMAC authentication, rescans the root, and
   reports changed, missing, and added files.

## Module Boundaries

- `canonical.py`: deterministic JSON byte encoding.
- `errors.py`: user-facing exception classes.
- `inventory.py`: filesystem boundary and hashing.
- `io.py`: JSON loading and atomic receipt writes.
- `keys.py`: local key file format.
- `models.py`: dataclasses returned by library APIs.
- `service.py`: receipt domain rules.
- `cli.py`: command-line parsing and exit codes.

## Security Boundaries

ShipReceipt refuses symbolic links and unsafe paths because a receipt must not
be able to escape the declared root directory during verification. Receipt paths
must be relative POSIX paths without `.` or `..` segments.

Signing keys are opaque 32-byte local secrets encoded in a versioned text file.
The key format is intentionally simple so it can be inspected and backed up
without extra tooling.

## Testing Strategy

- Unit tests cover inventory traversal, key file handling, deterministic
  receipts, tamper detection, and error paths.
- Integration tests verify create/write/load/verify behavior against real
  filesystem input.
- E2E tests run the CLI as a user would and validate exit codes and output.
