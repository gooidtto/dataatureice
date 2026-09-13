"""SQLite-backed repository compatible with the canonical DataRepository contract."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .db_engine import DEFAULT_FIELDS, SQLiteFTSEngine


class SQLiteRepository:
    """Read canonical rows from the SQLite store without UI/search coupling."""

    def __init__(self, db_path: str | Path, *, engine: SQLiteFTSEngine | None = None) -> None:
        self.db_path = Path(db_path)
        self.engine = engine or SQLiteFTSEngine(self.db_path, fields=DEFAULT_FIELDS)
        self.manifest: list[dict[str, Any]] = []

    def load(self) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]], list[str]]:
        rows = self.engine.all_rows()
        snapshots: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            snapshots[row.get("data_date", "")].append(row)
        return rows, dict(sorted(snapshots.items())), []

    def replace(self, rows: list[dict[str, Any]]) -> int:
        return self.engine.replace_rows(rows)
