from pathlib import Path
import csv

from storage.csv_repository import CsvRepository


FIELDS = ("record_id", "data_date", "category", "model", "condition", "price", "verified")
CATEGORY_MAP = {"phone": "手机", "手机": "手机"}


def _repo(tmp_path: Path) -> CsvRepository:
    def read_csv(path: str) -> list[dict]:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    return CsvRepository(
        str(tmp_path),
        fields=FIELDS,
        category_map=CATEGORY_MAP,
        clean=lambda value: "" if value is None else str(value).strip(),
        read_csv=read_csv,
        valid=lambda row: bool(row.get("model") and row.get("condition") and row.get("price") and row.get("verified") == "1"),
    )


def _write(path: Path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("record_id,data_date,category,model,condition,price,verified\n" + "\n".join(rows) + "\n", encoding="utf-8")


def test_new_date_is_discovered_without_code_change(tmp_path: Path):
    _write(tmp_path / "database" / "2026-08-31" / "price.csv", ["a,2026-08-31,手机,OPPO A59,开机好屏,100,1"])
    _write(tmp_path / "database" / "2026-09-14" / "price.csv", ["b,2026-09-14,手机,OPPO A59 5G,开机好屏,120,1"])

    rows, snapshots, errors = _repo(tmp_path).load()

    assert not errors
    assert sorted(snapshots) == ["2026-08-31", "2026-09-14"]
    assert {row["record_id"] for row in rows} == {"a", "b"}


def test_database_date_wins_over_legacy_snapshot(tmp_path: Path):
    _write(tmp_path / "database" / "2026-08-31" / "price.csv", ["db,2026-08-31,手机,OPPO A59,开机好屏,100,1"])
    _write(tmp_path / "snapshots" / "2026-08-31" / "price.csv", ["old,2026-08-31,手机,OPPO A59,开机好屏,90,1"])

    rows, snapshots, errors = _repo(tmp_path).load()

    assert not errors
    assert [row["record_id"] for row in rows] == ["db"]
    assert [row["record_id"] for row in snapshots["2026-08-31"]] == ["db"]


def test_invalid_and_duplicate_records_are_excluded(tmp_path: Path):
    _write(
        tmp_path / "database" / "2026-09-14" / "price.csv",
        [
            "same,2026-09-14,手机,OPPO A59,开机好屏,100,1",
            "same,2026-09-14,手机,OPPO A59,开机碎屏,80,1",
            "invalid,2026-09-14,手机,,开机好屏,50,1",
        ],
    )

    rows, snapshots, errors = _repo(tmp_path).load()

    assert len(rows) == 1
    assert rows[0]["record_id"] == "same"
    assert any("重复 record_id same" in error for error in errors)
