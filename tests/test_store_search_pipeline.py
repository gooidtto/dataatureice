from phone_search import Store
from search_service import SearchService
from storage.repository import InMemoryRepository


def row(record_id, model, *, category="手机", brand="OPPO", series="A59", alias="", date="2026-08-31", condition="开机好屏", price="500"):
    return {
        "record_id": record_id,
        "data_date": date,
        "category": category,
        "subtype": "",
        "brand": brand,
        "series": series,
        "model": model,
        "model_code": "",
        "alias": alias,
        "condition": condition,
        "price": price,
        "unit": "美元",
        "note": "",
        "origin": "",
        "source_image": "img-a",
        "source_path": "",
        "verified": "1",
        "confidence": "",
        "verification": "",
    }


def test_store_load_updates_search_service_and_uses_repository():
    rows = [
        row("1", "OPPO A59"),
        row("2", "OPPO A59 5G", date="2026-08-25", condition="开机碎屏", price="300"),
        row("3", "vivo Y100", brand="vivo", series="Y", alias="Y100青春版", date="2026-08-31"),
    ]
    repo = InMemoryRepository(rows, {"2026-08-31": [rows[0], rows[2]], "2026-08-25": [rows[1]]})
    store = Store("unused", repository=repo)

    assert store.load() is None
    assert len(store.rows) == 3
    assert store.snapshots["2026-08-25"][0]["model"] == "OPPO A59 5G"
    assert [r["model"] for r in store.search("OPPO A59")] == ["OPPO A59", "OPPO A59 5G"]
    assert [r["model"] for r in store.search("vivo", "手机")] == ["vivo Y100"]
    assert [r["model"] for r in store.search("Y100青春版", "手机")] == ["vivo Y100"]
    assert store.search("Y100青春版", "平板") == []


def test_store_accepts_search_service_injection_and_replaces_index_on_reload():
    first = [row("1", "OPPO A59")]
    second = [row("2", "OPPO A59 5G", date="2026-08-25")]
    repo = InMemoryRepository(first, {"2026-08-31": first})
    service = SearchService([])
    store = Store("unused", repository=repo, search_service=service)

    store.load()
    assert store.search_service is service
    assert store.search("OPPO A59")[0]["model"] == "OPPO A59"

    repo._rows = second
    repo._snapshots = {"2026-08-25": second}
    store.load()
    assert [r["model"] for r in store.search("OPPO A59")] == ["OPPO A59 5G"]
