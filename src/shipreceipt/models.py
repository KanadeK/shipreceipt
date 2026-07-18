from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True, order=True)
class FileEntry:
    path: str
    size: int
    sha256: str

    def to_json(self) -> dict[str, object]:
        return {"path": self.path, "size": self.size, "sha256": self.sha256}


@dataclass(slots=True)
class VerificationReport:
    ok: bool
    integrity_ok: bool
    authenticity: str
    changed: tuple[str, ...] = field(default_factory=tuple)
    missing: tuple[str, ...] = field(default_factory=tuple)
    added: tuple[str, ...] = field(default_factory=tuple)

    @property
    def clean(self) -> bool:
        return not self.changed and not self.missing and not self.added
