#!/usr/bin/env python3
"""Build the canonical date database without dropping callable fields or rows."""
from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATABASE = DATA / "database"
DATE_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.csv$")
DATE_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FIELDS = ["record_id", "data_date", "category", "subtype", "brand", "series", "model", "model_code", "alias", "condition", "price", "unit", "note", "origin", "source_image", "source_path", "verified", "confidence", "verification"]
EXPECTED_COUNTS = {"2026-07-05": 503, "2026-07-10": 1128, "2026-08-25": 15400, "2026-08-31": 14415}
EXPECTED_DATES = list(EXPECTED_COUNTS)


def read_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            actual = list(row.keys())
            if actual != FIELDS:
                raise ValueError(f"input schema must be exactly 19 fields: {actual}")
            writer.writerow(row)


def snapshot_rows(date: str):
    folder = DATA / "snapshots" / date
    if not folder.is_dir():
        return []
    rows = []
    for path in sorted(folder.glob("*.csv")):
        part = read_rows(path)
        if part and list(part[0].keys()) != FIELDS:
            raise ValueError(f"{path}: schema must be exactly 19 fields")
        rows.extend(part)
    return rows


def canonicalize_root_files():
    moved = []
    for src in sorted(DATA.iterdir()):
        if not src.is_file() or not DATE_FILE.fullmatch(src.name):
            continue
        date = src.stem
        rows = read_rows(src)
        target = DATABASE / date / "price.csv"
        write_rows(target, rows)
        src.unlink()
        moved.append((date, len(rows)))
    return moved


def restore_from_snapshots():
    restored = []
    for date in EXPECTED_DATES:
        rows = snapshot_rows(date)
        if not rows:
            continue
        target = DATABASE / date / "price.csv"
        write_rows(target, rows)
        restored.append((date, len(rows)))
    return restored


def ensure_expected_folders():
    ensured = []
    for date in EXPECTED_DATES:
        target = DATABASE / date / "price.csv"
        if not target.exists():
            write_rows(target, [])
            ensured.append(date)
    return ensured


def row_tuple(row):
    return tuple(row.get(field, "") for field in FIELDS)


def validate():
    errors = []
    folders = []
    if not DATABASE.exists():
        return ["database directory missing"], folders
    for date, expected in EXPECTED_COUNTS.items():
        folder = DATABASE / date
        price = folder / "price.csv"
        if not folder.is_dir():
            errors.append(f"missing date folder: {date}")
            continue
        folders.append(date)
        if not price.is_file():
            errors.append(f"{folder}: missing price.csv")
            continue
        try:
            rows = read_rows(price)
            if list(rows[0].keys()) if rows else FIELDS != FIELDS:
                pass
            if rows and list(rows[0].keys()) != FIELDS:
                errors.append(f"{price}: database schema mismatch")
            if len(rows) != expected:
                errors.append(f"{price}: expected {expected} rows, got {len(rows)}")
            ids = [r.get("record_id", "") for r in rows]
            if len(ids) != len(set(ids)) or any(not x for x in ids):
                errors.append(f"{price}: record_id missing or duplicate")
            for line, row in enumerate(rows, 2):
                if row.get("data_date", "").strip() != date:
                    errors.append(f"{price}:{line}: data_date mismatch")
                for field in ("record_id", "category", "subtype", "model", "condition", "price", "unit", "source_image", "source_path", "verified"):
                    if not row.get(field, "").strip():
                        errors.append(f"{price}:{line}: missing {field}")
                        break
        except Exception as exc:
            errors.append(f"{price}: CSV read failed: {exc}")

        try:
            snap = snapshot_rows(date)
        except Exception as exc:
            errors.append(f"{date}: snapshot validation failed: {exc}")
            continue
        if snap:
            db_rows = read_rows(price)
            if len(snap) != expected:
                errors.append(f"{date}: snapshot expected {expected} rows, got {len(snap)}")
            if len(db_rows) != len(snap) or sorted(map(row_tuple, db_rows)) != sorted(map(row_tuple, snap)):
                errors.append(f"{date}: database record set/fields differ from snapshot")

    for p in sorted(DATA.iterdir()):
        if p.is_file() and DATE_FILE.fullmatch(p.name):
            errors.append(f"date CSV remains in data root: {p.name}")
    return errors, folders


def main() -> int:
    DATABASE.mkdir(parents=True, exist_ok=True)
    moved = canonicalize_root_files()
    restored = restore_from_snapshots()
    ensured = ensure_expected_folders()
    errors, folders = validate()
    print(f"MOVED_DATE_CSVS={moved}")
    print(f"RESTORED_FROM_SNAPSHOTS={restored}")
    print(f"ENSURED_DATE_FOLDERS={ensured}")
    print(f"DATABASE_DATE_FOLDERS={folders}")
    print(f"EXPECTED_TOTAL_ROWS={sum(EXPECTED_COUNTS.values())}")
    print(f"ERRORS={len(errors)}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
