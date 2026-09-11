#!/usr/bin/env python3
"""Canonical paths and CSV helpers for the date-partitioned price database."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATABASE = DATA / "database"
FIELDS = ['record_id','data_date','category','subtype','brand','series','model','model_code','alias','condition','price','unit','note','origin','source_image','source_path','verified','confidence','verification']


def path(date: str) -> Path:
    target = DATABASE / date / 'price.csv'
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def load(date: str):
    target = path(date)
    if not target.exists():
        return []
    with target.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write(date: str, rows) -> Path:
    target = path(date)
    with target.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return target
