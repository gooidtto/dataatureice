"""Storage boundary for the price database.

The application talks to a repository instead of depending on a particular
on-disk representation. CSV remains the source of truth for now; SQLite/FTS5
can be introduced behind this boundary later without changing search, display,
favorites, or export semantics.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Mapping, Sequence

Row = Mapping[str, object]
LoadResult = tuple[list[dict], dict[str, list[dict]], list[str]]


class DataRepository(ABC):
    """Minimal read contract used by the application data layer."""

    @abstractmethod
    def load(self) -> LoadResult:
        """Return rows, date snapshots, and validation errors."""
        raise NotImplementedError


class InMemoryRepository(DataRepository):
    """Small repository implementation for tests and deterministic services."""

    def __init__(
        self,
        rows: Iterable[Row] | None = None,
        snapshots: Mapping[str, Sequence[Row]] | None = None,
        errors: Iterable[str] | None = None,
    ) -> None:
        self._rows = [dict(row) for row in (rows or [])]
        self._snapshots = {
            str(date): [dict(row) for row in rows_for_date]
            for date, rows_for_date in (snapshots or {}).items()
        }
        self._errors = [str(error) for error in (errors or [])]

    def load(self) -> LoadResult:
        return (
            [dict(row) for row in self._rows],
            {date: [dict(row) for row in rows] for date, rows in self._snapshots.items()},
            list(self._errors),
        )
