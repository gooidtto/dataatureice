#!/usr/bin/env python3
"""Normalize generated date CSVs into data/database/YYYY-MM-DD/price.csv."""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATE_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.csv$")


def main() -> int:
    db = DATA / "database"
    db.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in sorted(DATA.iterdir()):
        if not path.is_file():
            continue
        m = DATE_FILE.fullmatch(path.name)
        if not m:
            continue
        date = m.group(1)
        target_dir = db / date
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "price.csv"
        if target.exists():
            target.unlink()
        shutil.move(str(path), str(target))
        moved += 1
        print(f"DATABASE_DATE={date} FILE={target.as_posix()}")
    folders = sorted(p.name for p in db.iterdir() if p.is_dir())
    print(f"DATABASE_DATE_FOLDERS={len(folders)} MOVED={moved}")
    for date in folders:
        print(f"DATABASE_DATE_FOLDER={date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
