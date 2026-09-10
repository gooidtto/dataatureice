from search_ui_models import FavoriteStore, SearchHistory


def test_history_is_deduplicated_and_recent_first():
    h = SearchHistory(["问问星星吧", "问问风问问雨"])
    h.add("问问星星吧")
    assert h.items == ["问问星星吧", "问问风问问雨"]


def test_history_suggestions_are_limited_to_five():
    # SearchHistory receives persisted history in recent-first order.
    h = SearchHistory([f"问问{i}" for i in range(4, -1, -1)])
    h.items.extend(f"问问{i}" for i in range(5, 10))
    assert [x.text for x in h.suggestions("问问")] == [f"问问{i}" for i in range(4, -1, -1)]


def test_favorite_store_is_content_deduplicated():
    row = {"category":"手机","subtype":"device","brand":"A","series":"S","model":"M","model_code":"","condition":"好","price":"100","unit":"元"}
    f = FavoriteStore()
    assert f.add_one(row) is True
    assert f.add_one(dict(row, record_id="different")) is False
    assert len(f.items) == 1


def test_favorite_store_allows_distinct_price_conditions():
    f = FavoriteStore()
    base = {"category":"手机","subtype":"device","brand":"A","series":"S","model":"M","model_code":"","unit":"元"}
    assert f.add_one(dict(base, condition="好", price="100")) is True
    assert f.add_one(dict(base, condition="屏坏", price="50")) is True
    assert len(f.items) == 2
