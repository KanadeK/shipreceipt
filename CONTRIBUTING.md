# Contributing

Thank you for improving ShipReceipt.

## Development Setup

```console
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m build
```

## Pull Request Expectations

- Keep changes focused on one behavior or maintenance concern.
- Add or update tests for user-visible behavior.
- Do not commit generated caches, local keys, receipts, virtual environments, or build output.
- Run the test and lint commands before opening a pull request.
- Update documentation when command behavior changes.

## Commit Style

Use conventional commit messages:

```text
feat(core): add receipt verification
fix(cli): return non-zero on changed files
docs(readme): clarify signed receipt flow
```

## Reporting Security Issues

Do not open a public issue for a vulnerability. Follow [SECURITY.md](SECURITY.md).
