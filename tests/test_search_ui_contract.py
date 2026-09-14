import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("phone_search", ROOT / "phone_search.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(**kw):
    r = {k: "" for k in mod.FIELDS}
    r.update({"data_date": "2026-08-31", "category": "手机", "subtype": "device", "brand": "A", "series": "S", "model": "M", "condition": "好", "price": "100", "unit": "元", "verified": "1"})
    r.update(kw)
    return r


def _ui_module():
    spec = importlib.util.spec_from_file_location("ui_bootstrap", ROOT / "ui_bootstrap.py")
    ui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ui)
    return ui


def test_one_click_favorite_is_content_level_deduped():
    fav = mod.Favorites("unused")
    added, duplicate = fav.add([row(record_id="one"), row(record_id="two")])
    assert len(added) == 1
    assert len(duplicate) == 1
    assert len(fav.items) == 1


def test_favorite_content_key_changes_for_condition_or_price():
    fav = mod.Favorites("unused")
    assert fav.identity(row(condition="开机屏好", price="100")) != fav.identity(row(condition="开机屏坏", price="80"))


def test_favorite_groups_share_canonical_model_date_contract():
    ui = _ui_module()
    app = object.__new__(mod.App)
    app.fav = mod.Favorites("unused")
    app.fav.items = [row(record_id="m2-old", model="M2", data_date="2026-08-20", price="80"), row(record_id="m1-old", model="M1", data_date="2026-08-20", price="70"), row(record_id="m1-new", model="M1", data_date="2026-08-31", price="100"), row(record_id="m2-new", model="M2", data_date="2026-08-31", price="110")]
    groups = ui.favorite_groups(app)
    assert [key[3] for key, _ in groups] == ["M1", "M2"]
    assert all(len(blocks) == 2 for _, blocks in groups)
    assert [blocks[0][0]["data_date"] for _, blocks in groups] == ["2026-08-31", "2026-08-31"]
    assert [blocks[1][0]["data_date"] for _, blocks in groups] == ["2026-08-20", "2026-08-20"]


def test_search_and_favorites_use_the_same_identity_grouping():
    ui = _ui_module()
    rows = [row(record_id="a1", model="M1", data_date="2026-08-20", condition="开机屏坏", price="999"), row(record_id="a2", model="M1", data_date="2026-08-31", condition="开机屏好", price="1"), row(record_id="b1", model="M2", data_date="2026-08-31", condition="不开机", price="9999")]
    grouped = ui.group_model_dates(rows)
    display = [item for item in ui.normalize_search_results(rows) if not item.get("_separator")]
    assert [key[3] for key, _ in grouped] == ["M1", "M2"]
    assert [item["_model_key"][3] for item in display] == ["M1", "M1", "M2"]
    assert [item["_period_key"] for item in display] == ["2026-08-31", "2026-08-20", "2026-08-31"]


def test_display_block_contract_keeps_dynamic_columns_local():
    ui = _ui_module()
    blocks = [x for x in ui.normalize_search_results([row(model="M1", condition="开机屏好", price="100", source_image="a.jpg"), row(model="M2", condition="不开机", price="80", source_image="b.jpg")]) if not x.get("_separator")]
    assert len(blocks) == 2
    assert [c[1] for c in blocks[0]["_columns"]] == ["数据日期", "手机/品牌/系列/型号/网络型号", "开机屏好", "来源图片"]
    assert [c[1] for c in blocks[1]["_columns"]] == ["数据日期", "手机/品牌/系列/型号/网络型号", "不开机", "来源图片"]
    assert blocks[0]["source_image"] == "a.jpg"
    assert blocks[1]["source_image"] == "b.jpg"
