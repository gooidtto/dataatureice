"""Canonical ETL pipeline from a repository into the SQLite store."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .db_engine import SQLiteFTSEngine


class StoragePipeline:
    """Load, normalize, validate identity, and persist canonical rows.

    Source repositories remain responsible for source-specific parsing and
    validation. This layer owns the single persistence boundary used by the
    application and build process. A failed source load must never replace a
    previously valid canonical database.
    """

    def __init__(self, engine: SQLiteFTSEngine) -> None:
        self.engine = engine

    @staticmethod
    def normalize(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for source in rows:
            row = {
                str(key): "" if value is None else str(value).strip()
                for key, value in source.items()
            }
            record_id = row.get("record_id", "")
            data_date = row.get("data_date", "")
            if not record_id or not data_date:
                continue
            identity = (record_id, data_date)
            if identity in seen:
                continue
            seen.add(identity)
            result.append(row)
        return result

    def persist(self, rows: Iterable[Mapping[str, Any]]) -> int:
        return self.engine.replace_rows(self.normalize(rows))

    def run(
        self, repository: Any
    ) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]], list[str]]:
        """Load and persist one canonical dataset atomically at the boundary.

        Repository parsing/validation errors are returned to the caller and
        block persistence. The returned rows are the same normalized rows that
        were persisted, so callers cannot accidentally consume a pre-ETL view.
        """
        rows, snapshots, errors = repository.load()
        if errors:
            return [], {}, list(errors)
        normalized = self.normalize(rows)
        normalized_snapshots = {
            date: self.normalize(date_rows) for date, date_rows in snapshots.items()
        }
        self.engine.replace_rows(normalized)
        return normalized, normalized_snapshots, []
