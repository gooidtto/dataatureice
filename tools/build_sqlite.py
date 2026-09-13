#!/usr/bin/env python3
"""Build the canonical SQLite/FTS5 database from the prepared date data."""
from pathlib import Path

from phone_search import CAT, FIELDS, clean, read_csv, valid
from storage.csv_repository import CsvRepository
from storage.db_engine import SQLiteFTSEngine
from storage.pipeline import StoragePipeline


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "search.sqlite3"


def main() -> int:
    repository = CsvRepository(
        str(DATA),
        fields=tuple(FIELDS),
        category_map=CAT,
        clean=clean,
        read_csv=read_csv,
        valid=valid,
    )
    rows, _snapshots, errors = repository.load()
    if errors:
        raise SystemExit("; ".join(errors[:10]))
    count = StoragePipeline(SQLiteFTSEngine(DB)).persist(rows)
    print(f"SQLITE_CANONICAL_ROWS={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
