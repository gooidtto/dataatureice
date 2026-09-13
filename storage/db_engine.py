"""SQLite storage engine with an FTS5 search index."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Sequence

DEFAULT_FIELDS = (
    "record_id", "data_date", "category", "subtype", "brand", "series",
    "model", "model_code", "alias", "condition", "price", "unit", "note",
    "origin", "source_image", "source_path", "verified", "confidence",
    "verification",
)
FTS_FIELDS = (
    "category", "subtype", "brand", "series", "model", "model_code",
    "alias", "condition", "note", "origin", "source_image",
)


class SQLiteFTSEngine:
    """Persistent canonical rows plus an SQLite FTS5 index.

    A record identity is scoped by date so that a repeated source ``record_id``
    on another snapshot cannot overwrite the historical record.
    """

    def __init__(self, path: str | Path, fields: Sequence[str] = DEFAULT_FIELDS):
        self.path = Path(path)
        self.fields = tuple(fields)
        required = {"record_id", "data_date"}
        missing = required.difference(self.fields)
        if missing:
            raise ValueError(f"fields must contain {sorted(missing)}")
        missing_fts = set(FTS_FIELDS).difference(self.fields)
        if missing_fts:
            raise ValueError(f"fields missing FTS columns: {sorted(missing_fts)}")

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def initialize(self, conn: sqlite3.Connection | None = None) -> None:
        own = conn is None
        conn = conn or self.connect()
        try:
            cols = ", ".join(f'"{field}" TEXT' for field in self.fields)
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS records ({cols}, "
                "PRIMARY KEY (record_id, data_date))"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_records_date ON records(data_date)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_records_identity "
                "ON records(category,subtype,brand,series,model,model_code)"
            )
            conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5("
                "record_id UNINDEXED,"
                + ",".join(FTS_FIELDS)
                + ",content='records',content_rowid='rowid')"
            )
            conn.execute(
                "CREATE TRIGGER IF NOT EXISTS records_ai AFTER INSERT ON records BEGIN "
                "INSERT INTO records_fts(rowid,record_id,category,subtype,brand,series,model,model_code,alias,condition,note,origin,source_image) "
                "VALUES(new.rowid,new.record_id,new.category,new.subtype,new.brand,new.series,new.model,new.model_code,new.alias,new.condition,new.note,new.origin,new.source_image); END"
            )
            conn.execute(
                "CREATE TRIGGER IF NOT EXISTS records_ad AFTER DELETE ON records BEGIN "
                "INSERT INTO records_fts(records_fts,rowid,record_id,category,subtype,brand,series,model,model_code,alias,condition,note,origin,source_image) "
                "VALUES('delete',old.rowid,old.record_id,old.category,old.subtype,old.brand,old.series,old.model,old.model_code,old.alias,old.condition,old.note,old.origin,old.source_image); END"
            )
            conn.execute(
                "CREATE TRIGGER IF NOT EXISTS records_au AFTER UPDATE ON records BEGIN "
                "INSERT INTO records_fts(records_fts,rowid,record_id,category,subtype,brand,series,model,model_code,alias,condition,note,origin,source_image) "
                "VALUES('delete',old.rowid,old.record_id,old.category,old.subtype,old.brand,old.series,old.model,old.model_code,old.alias,old.condition,old.note,old.origin,old.source_image); "
                "INSERT INTO records_fts(rowid,record_id,category,subtype,brand,series,model,model_code,alias,condition,note,origin,source_image) "
                "VALUES(new.rowid,new.record_id,new.category,new.subtype,new.brand,new.series,new.model,new.model_code,new.alias,new.condition,new.note,new.origin,new.source_image); END"
            )
            conn.commit()
        finally:
            if own:
                conn.close()

    def replace_rows(self, rows: Iterable[Mapping[str, object]]) -> int:
        materialized = [dict(row) for row in rows]
        with self.connect() as conn:
            self.initialize(conn)
            conn.execute("DELETE FROM records")
            sql = (
                f"INSERT INTO records ({','.join(self.fields)}) "
                f"VALUES ({','.join('?' for _ in self.fields)})"
            )
            conn.executemany(
                sql,
                [tuple(str(row.get(field, "") or "") for field in self.fields) for row in materialized],
            )
            conn.execute("INSERT INTO records_fts(records_fts) VALUES('rebuild')")
            conn.commit()
        return len(materialized)

    def count(self) -> int:
        with self.connect() as conn:
            self.initialize(conn)
            return int(conn.execute("SELECT COUNT(*) FROM records").fetchone()[0])

    def all_rows(self) -> list[dict[str, str]]:
        with self.connect() as conn:
            self.initialize(conn)
            return [dict(row) for row in conn.execute("SELECT * FROM records ORDER BY data_date, rowid")]

    def fts_search(self, query: str, limit: int = 1000) -> list[dict[str, str]]:
        query = (query or "").strip()
        if not query:
            return self.all_rows()[:limit]
        match = " AND ".join(
            f'"{token.replace(chr(34), chr(34) * 2)}"'
            for token in query.split()
            if token
        )
        with self.connect() as conn:
            self.initialize(conn)
            return [
                dict(row)
                for row in conn.execute(
                    "SELECT r.* FROM records_fts f "
                    "JOIN records r ON r.rowid=f.rowid "
                    "WHERE records_fts MATCH ? ORDER BY r.data_date DESC, r.rowid LIMIT ?",
                    (match, limit),
                )
            ]

    def rebuild_fts(self) -> None:
        with self.connect() as conn:
            self.initialize(conn)
            conn.execute("INSERT INTO records_fts(records_fts) VALUES('rebuild')")
            conn.commit()
