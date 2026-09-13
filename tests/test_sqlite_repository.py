from storage.db_engine import SQLiteFTSEngine
from storage.pipeline import StoragePipeline
from storage.sqlite_repository import SQLiteRepository


def row(record_id, date, model):
    return {
        "record_id": record_id,
        "data_date": date,
        "category": "手机",
        "subtype": "手机",
        "brand": "OPPO",
        "series": "A",
        "model": model,
        "model_code": "",
        "alias": "",
        "condition": "开机好屏",
        "price": "500",
        "unit": "元",
        "note": "",
        "origin": "",
        "source_image": "img",
        "source_path": "",
        "verified": "1",
        "confidence": "",
        "verification": "",
    }


def test_sqlite_repository_preserves_same_record_id_across_dates(tmp_path):
    engine = SQLiteFTSEngine(tmp_path / "prices.sqlite3")
    rows = [row("same", "2026-08-30", "OPPO A59"), row("same", "2026-08-31", "OPPO A59")]
    assert StoragePipeline(engine).persist(rows) == 2
    loaded, snapshots, errors = SQLiteRepository(tmp_path / "prices.sqlite3", engine=engine).load()
    assert errors == []
    assert len(loaded) == 2
    assert sorted(snapshots) == ["2026-08-30", "2026-08-31"]


def test_pipeline_deduplicates_only_same_record_and_date(tmp_path):
    engine = SQLiteFTSEngine(tmp_path / "prices.sqlite3")
    pipeline = StoragePipeline(engine)
    rows = [
        row("r1", "2026-08-31", "OPPO A59"),
        row("r1", "2026-08-31", "OPPO A59"),
        row("r1", "2026-09-01", "OPPO A59"),
    ]
    assert pipeline.persist(rows) == 2
    assert engine.count() == 2
