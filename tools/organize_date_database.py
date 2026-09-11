#!/usr/bin/env python3
"""Validate the canonical data/database/YYYY-MM-DD/price.csv tree."""
from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATE_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.csv$")
DATE_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def main() -> int:
    db = DATA / "database"
    db.mkdir(parents=True, exist_ok=True)
    errors=[]
    root_dates=[]
    for p in sorted(DATA.iterdir()):
        if p.is_file() and DATE_FILE.fullmatch(p.name): root_dates.append(p.name)
    if root_dates: errors.append(f"date CSVs remain in data root: {root_dates}")
    folders=[]
    for p in sorted(db.iterdir()):
        if not p.is_dir() or not DATE_DIR.fullmatch(p.name): continue
        folders.append(p.name)
        price=p/'price.csv'
        if not price.is_file():
            errors.append(f"{p}: missing price.csv"); continue
        try:
            with price.open('r',encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f)
                for line,row in enumerate(reader,2):
                    if row.get('data_date','').strip()!=p.name:
                        errors.append(f"{price}:{line}: data_date mismatch")
        except Exception as exc:
            errors.append(f"{price}: CSV read failed: {exc}")
    print(f"DATABASE_DATE_FOLDERS={folders}")
    print(f"ROOT_DATE_CSVS={root_dates}")
    print(f"ERRORS={len(errors)}")
    for e in errors: print(f"ERROR: {e}")
    return 1 if errors else 0

if __name__ == '__main__': raise SystemExit(main())
