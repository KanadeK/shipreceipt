# Receipt Format

ShipReceipt v0.1.0 writes JSON receipts with schema `shipreceipt/v1`.

```json
{
  "schema": "shipreceipt/v1",
  "version": 1,
  "created_at": "2026-07-18T00:00:00Z",
  "label": "release-name",
  "source": {
    "name": "release-bundle"
  },
  "excludes": [
    "*.pyc",
    ".git",
    ".git/*",
    "__pycache__",
    "__pycache__/*"
  ],
  "files": [
    {
      "path": "artifact.txt",
      "size": 7,
      "sha256": "239f59ed55e737c77147cf55e0315467016b0c35bb4b52d1ca544cddae7f5e93"
    }
  ],
  "manifest_sha256": "64 lowercase hex characters",
  "receipt_id": "sha256:64 lowercase hex characters",
  "authentication": {
    "algorithm": "hmac-sha256",
    "key_id": "sha256:64 lowercase hex characters",
    "signature": "64 lowercase hex characters"
  }
}
```

`authentication` is omitted for unsigned receipts.

## Canonical Digest

The manifest digest is computed from the canonical JSON encoding of:

- `schema`
- `version`
- `created_at`
- `label`
- `source`
- `excludes`
- `files`

Canonical JSON is UTF-8 encoded with sorted object keys and compact separators.
The digest is SHA-256 over those bytes. HMAC signatures use the same canonical
payload.

## Path Rules

File paths in receipts must:

- Be relative.
- Use `/` separators.
- Avoid empty, `.`, or `..` path segments.
- Not be Windows absolute paths.
- Be sorted and unique.
