from storage.db_engine import SQLiteFTSEngine
from storage.pipeline import StoragePipeline


def row(record_id, date, model):
    return {
        "record_id": record_id,
        "data_date": date,
        "category": "手机",
        "subtype": "device",
        "brand": "OPPO",
        "series": "A59",
        "model": model,
        "model_code": "",
        "alias": "",
        "condition": "开机好屏",
        "price": "500",
        "unit": "美元",
        "note": "",
        "origin": "",
        "source_image": "img-a",
        "source_path": "",
        "verified": "1",
        "confidence": "",
        "verification": "",
    }


def test_normalize_deduplicates_only_same_record_and_date():
    rows = [
        row("same", "2026-08-31", "OPPO A59"),
        row("same", "2026-08-31", "OPPO A59"),
        row("same", "2026-08-25", "OPPO A59"),
        row("missing-date", "", "OPPO A59"),
    ]
    normalized = StoragePipeline.normalize(rows)
    assert [(r["record_id"], r["data_date"]) for r in normalized] == [
        ("same", "2026-08-31"),
        ("same", "2026-08-25"),
    ]


def test_pipeline_persists_rows_and_builds_queryable_fts(tmp_path):
    engine = SQLiteFTSEngine(tmp_path / "search.sqlite3")
    rows = [
        row("one", "2026-08-31", "OPPO A59"),
        row("two", "2026-08-25", "OPPO A59 5G"),
    ]
    assert StoragePipeline(engine).persist(rows) == 2
    assert engine.count() == 2
    assert [r["model"] for r in engine.fts_search("OPPO A59")] == [
        "OPPO A59",
        "OPPO A59 5G",
    ]


def test_pipeline_preserves_same_record_id_across_dates(tmp_path):
    engine = SQLiteFTSEngine(tmp_path / "search.sqlite3")
    rows = [
        row("same", "2026-08-31", "OPPO A59"),
        row("same", "2026-08-25", "OPPO A59"),
    ]
    assert StoragePipeline(engine).persist(rows) == 2
    assert {(r["record_id"], r["data_date"]) for r in engine.all_rows()} == {
        ("same", "2026-08-31"),
        ("same", "2026-08-25"),
    }


def test_run_does_not_persist_when_repository_reports_errors(tmp_path):
    engine = SQLiteFTSEngine(tmp_path / "search.sqlite3")
    pipeline = StoragePipeline(engine)
    pipeline.persist([row("existing", "2026-08-31", "OPPO A59")])

    class BrokenRepository:
        def load(self):
            return [row("new", "2026-08-31", "OPPO A60")], {}, ["2026-08-31: bad source"]

    rows, snapshots, errors = pipeline.run(BrokenRepository())
    assert rows == []
    assert snapshots == {}
    assert errors == ["2026-08-31: bad source"]
    assert engine.count() == 1
    assert engine.all_rows()[0]["record_id"] == "existing"


def test_run_returns_exactly_the_normalized_rows_it_persists(tmp_path):
    engine = SQLiteFTSEngine(tmp_path / "search.sqlite3")
    pipeline = StoragePipeline(engine)

    class Repository:
        def load(self):
            rows = [row("same", "2026-08-31", " OPPO A59 "), row("same", "2026-08-31", "duplicate")]
            return rows, {"2026-08-31": rows}, []

    rows, snapshots, errors = pipeline.run(Repository())
    assert errors == []
    assert rows == [row("same", "2026-08-31", "OPPO A59")]
    assert snapshots == {"2026-08-31": [row("same", "2026-08-31", "OPPO A59")]}
    assert engine.all_rows() == rows
