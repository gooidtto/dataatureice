#!/usr/bin/env python3
"""Canonicalize date CSVs into data/database/YYYY-MM-DD/price.csv."""
from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATABASE = DATA / "database"
DATE_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.csv$")
DATE_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FIELDS = ["data_date", "category", "subtype", "brand", "series", "model", "condition", "price", "unit", "note", "source_image"]
EXPECTED_DATES = ["2026-07-05", "2026-07-10", "2026-08-25", "2026-08-31"]


def read_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def canonicalize_root_files():
    moved = []
    for src in sorted(DATA.iterdir()):
        if not src.is_file() or not DATE_FILE.fullmatch(src.name):
            continue
        date = src.stem
        target = DATABASE / date / "price.csv"
        rows = read_rows(src)
        write_rows(target, rows)
        src.unlink()
        moved.append((date, len(rows)))
    return moved


def ensure_expected_folders():
    ensured = []
    for date in EXPECTED_DATES:
        target = DATABASE / date / "price.csv"
        if not target.exists():
            write_rows(target, [])
            ensured.append(date)
    return ensured


def validate():
    errors = []
    folders = []
    if not DATABASE.exists():
        return ["database directory missing"], folders
    for p in sorted(DATABASE.iterdir()):
        if not p.is_dir() or not DATE_DIR.fullmatch(p.name):
            continue
        folders.append(p.name)
        price = p / "price.csv"
        if not price.is_file():
            errors.append(f"{p}: missing price.csv")
            continue
        try:
            for line, row in enumerate(read_rows(price), 2):
                if row.get("data_date", "").strip() != p.name:
                    errors.append(f"{price}:{line}: data_date mismatch")
        except Exception as exc:
            errors.append(f"{price}: CSV read failed: {exc}")
    for p in sorted(DATA.iterdir()):
        if p.is_file() and DATE_FILE.fullmatch(p.name):
            errors.append(f"date CSV remains in data root: {p.name}")
    return errors, folders


def main() -> int:
    DATABASE.mkdir(parents=True, exist_ok=True)
    moved = canonicalize_root_files()
    ensured = ensure_expected_folders()
    errors, folders = validate()
    print(f"MOVED_DATE_CSVS={moved}")
    print(f"ENSURED_DATE_FOLDERS={ensured}")
    print(f"DATABASE_DATE_FOLDERS={folders}")
    print(f"ERRORS={len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
