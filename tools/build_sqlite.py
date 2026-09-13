#!/usr/bin/env python3
"""Build the canonical SQLite/FTS5 database from the prepared date data."""
from pathlib import Path
import sys

# Running ``python tools/build_sqlite.py`` sets sys.path[0] to tools/ rather
# than the repository root. Add the root explicitly so the build does not
# depend on the caller's cwd.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phone_search import CAT, FIELDS, clean, read_csv, valid
from storage.csv_repository import CsvRepository
from storage.db_engine import SQLiteFTSEngine
from storage.pipeline import StoragePipeline


DATA = ROOT / "data"
DB = DATA / "search.sqlite3"
EXPECTED_ROWS = 31446


def main() -> int:
    repository = CsvRepository(
        str(DATA),
        fields=tuple(FIELDS),
        category_map=CAT,
        clean=clean,
        read_csv=read_csv,
        valid=valid,
    )
    pipeline = StoragePipeline(SQLiteFTSEngine(DB))
    rows, _snapshots, errors = pipeline.run(repository)
    if errors:
        raise SystemExit("; ".join(errors[:10]))
    if len(rows) != EXPECTED_ROWS:
        raise SystemExit(
            f"canonical row count mismatch: expected {EXPECTED_ROWS}, got {len(rows)}"
        )
    count = pipeline.engine.count()
    if count != EXPECTED_ROWS:
        raise SystemExit(
            f"SQLite row count mismatch: expected {EXPECTED_ROWS}, got {count}"
        )
    print(f"SQLITE_CANONICAL_ROWS={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
