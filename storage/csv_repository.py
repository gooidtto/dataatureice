"""CSV-backed repository used as the current data source of truth."""
from __future__ import annotations

import os
import re
from collections import defaultdict
from typing import Callable


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CsvRepository:
    """Discover and load dated CSV data without knowing anything about UI/search."""

    def __init__(
        self,
        root: str,
        *,
        fields: tuple[str, ...],
        category_map: dict[str, str],
        clean: Callable[[object], str],
        read_csv: Callable[[str], list[dict]],
        valid: Callable[[dict], bool],
    ) -> None:
        self.root = root
        self.fields = fields
        self.category_map = category_map
        self.clean = clean
        self.read_csv = read_csv
        self.valid = valid

    def discover(self) -> list[tuple[str, list[str]]]:
        """Return one deterministic list of CSV paths per discovered date."""
        grouped: dict[str, list[str]] = defaultdict(list)
        db = os.path.join(self.root, "database")
        if os.path.isdir(db):
            for date in sorted(os.listdir(db)):
                if not DATE_RE.fullmatch(date):
                    continue
                folder = os.path.join(db, date)
                if not os.path.isdir(folder):
                    continue
                for name in sorted(os.listdir(folder)):
                    path = os.path.join(folder, name)
                    if name.lower().endswith(".csv") and os.path.isfile(path):
                        grouped[date].append(path)

        # Compatibility fallback for older packaged data. A date already
        # present in database/ always wins and is never loaded twice.
        snapshots = os.path.join(self.root, "snapshots")
        if os.path.isdir(snapshots):
            for date in sorted(os.listdir(snapshots)):
                if date in grouped or not DATE_RE.fullmatch(date):
                    continue
                folder = os.path.join(snapshots, date)
                if not os.path.isdir(folder):
                    continue
                for name in sorted(os.listdir(folder)):
                    path = os.path.join(folder, name)
                    if name.lower().endswith(".csv") and os.path.isfile(path):
                        grouped[date].append(path)

        return [(date, paths) for date, paths in sorted(grouped.items()) if paths]

    def load(self) -> tuple[list[dict], dict[str, list[dict]], list[str]]:
        all_rows: list[dict] = []
        snapshots: dict[str, list[dict]] = {}
        errors: list[str] = []

        for date, paths in self.discover():
            rows_for_date: list[dict] = []
            seen_ids: set[str] = set()
            for path in paths:
                try:
                    raw_rows = self.read_csv(path)
                except Exception as exc:
                    errors.append(f"{date}: {exc}")
                    continue
                for raw in raw_rows:
                    row = {field: self.clean(raw.get(field, "")) for field in self.fields}
                    row["category"] = self.category_map.get(row["category"], row["category"])
                    if row.get("data_date") != date:
                        errors.append(f"{date}: data_date不一致")
                    if row.get("category") not in self.category_map.values():
                        errors.append(f'{date}: 非标准分类 {row.get("category", "")}')
                    if not self.valid(row):
                        continue
                    record_id = row.get("record_id", "")
                    if record_id in seen_ids:
                        errors.append(f"{date}: 重复 record_id {record_id}")
                        continue
                    seen_ids.add(record_id)
                    rows_for_date.append(row)
            snapshots[date] = rows_for_date
            all_rows.extend(rows_for_date)

        return all_rows, snapshots, errors
