from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class LedgerEntry:
    seq: int
    period: int
    family: str
    payload: dict[str, Any]

@dataclass
class ImmutableLedger:
    _entries: list[LedgerEntry]=field(default_factory=list)

    def append(self, period: int, family: str, **payload: Any) -> LedgerEntry:
        e=LedgerEntry(len(self._entries), period, family, dict(payload))
        self._entries.append(e)
        return e

    @property
    def entries(self) -> tuple[LedgerEntry,...]:
        return tuple(self._entries)

    def replay(self) -> tuple[LedgerEntry,...]:
        # Entries are append-only; replay intentionally returns the immutable sequence.
        return self.entries
