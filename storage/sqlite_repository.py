"""SQLite-backed repository compatible with the canonical DataRepository contract."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from .db_engine import DEFAULT_FIELDS, SQLiteFTSEngine


class SQLiteRepository:
    """Read canonical rows from the SQLite store without UI/search coupling."""

    def __init__(self, db_path: str | Path, *, engine: SQLiteFTSEngine | None = None, manifest_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path)
        self.engine = engine or SQLiteFTSEngine(self.db_path, fields=DEFAULT_FIELDS)
        self.manifest_path = Path(manifest_path) if manifest_path is not None else self.db_path.parent / "source_image_manifest.csv"
        self.manifest: list[dict[str, Any]] = []

    def _load_manifest(self) -> list[dict[str, Any]]:
        if not self.manifest_path.is_file():
            return []
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
            try:
                with self.manifest_path.open("r", encoding=encoding, newline="") as handle:
                    return list(csv.DictReader(handle))
            except UnicodeDecodeError:
                continue
            except OSError:
                return []
        return []

    def load(self) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]], list[str]]:
        rows = self.engine.all_rows()
        snapshots: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            snapshots[row.get("data_date", "")].append(row)
        self.manifest = self._load_manifest()
        return rows, dict(sorted(snapshots.items())), []

    def replace(self, rows: list[dict[str, Any]]) -> int:
        return self.engine.replace_rows(rows)
