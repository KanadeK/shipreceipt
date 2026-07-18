# Changelog

All notable changes to ShipReceipt are documented here.

## v0.1.0 - 2026-07-18

### Added

- Directory receipt creation with streaming SHA-256 inventory.
- Deterministic receipt manifest digest and `sha256:` receipt IDs.
- Receipt verification for changed, missing, and added files.
- Optional HMAC-SHA256 receipt authentication.
- Local signing key generation.
- CLI commands: `keygen`, `create`, `verify`, and `inspect`.
- Unit, integration, and E2E tests.
- Build, checksum, and local security scan scripts.
