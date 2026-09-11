from search_display import DISPLAY_COLUMNS, build_identity, display_columns_for_rows, dynamic_quote_columns, normalize_search_results
from app_actions_fix import LEGACY_DETAIL_COLS, legacy_detail_rows


def row(**kw):
    base = {
        "record_id": "id",
        "data_date": "2026-08-31",
        "category": "手机",
        "subtype": "device",
        "brand": "华为",
        "series": "荣耀畅玩系列",
        "model": "畅玩7x (3+32)",
        "model_code": "BND-AL00",
        "condition": "",
        "price": "",
        "unit": "CNY/台",
        "source_image": "华为2.jpg",
    }
    base.update(kw)
    return base


def test_search_display_uses_each_raw_condition_and_price_descending():
    rows = [
        row(record_id="a", data_date="2026-08-31", condition="开机靓好", price="700"),
        row(record_id="b", data_date="2026-08-31", condition="开机好屏", price="500"),
        row(record_id="c", data_date="2026-08-31", condition="开机好碎", price="450"),
        row(record_id="d", data_date="2026-08-31", condition="开机碎屏", price="320"),
        row(record_id="e", data_date="2026-08-31", condition="开机坏配件", price="240"),
        row(record_id="f", data_date="2026-08-31", condition="废板·整机", price="240"),
        row(record_id="g", data_date="2026-08-31", condition="开机屏好外屏碎", price="60"),
        row(record_id="h", data_date="2026-08-25", condition="开机靓好", price="800"),
    ]
    assert dynamic_quote_columns(rows) == (
        "开机靓好", "开机好屏", "开机好碎", "开机碎屏", "开机坏配件", "废板·整机", "开机屏好外屏碎"
    )
    result = normalize_search_results(rows)
    display = [r for r in result if not r.get("_separator")]
    assert len(display) == 2
    assert display[0]["data_date"] == "2026-08-31"
    assert display[0]["identity"] == "手机 华为 荣耀畅玩系列 畅玩7x (3+32) BND-AL00"
    assert display[0]["开机靓好"] == "700"
    assert display[0]["开机好屏"] == "500"
    assert display[0]["开机好碎"] == "450"
    assert display[0]["开机碎屏"] == "320"
    assert display[0]["开机坏配件"] == "240"
    assert display[0]["废板·整机"] == "240"
    assert display[0]["开机屏好外屏碎"] == "60"
    assert display[1]["data_date"] == "2026-08-25"
    assert display[1]["开机靓好"] == "800"
    assert "开机好屏" not in display[1]
    assert rows[0]["condition"] == "开机靓好"
    assert rows[0]["price"] == "700"


def test_dynamic_columns_are_actual_raw_condition_names():
    rows = [row(condition="不开机", price="240"), row(condition="开机屏好外屏碎", price="180"), row(condition="统货", price="500")]
    labels = [label for _field, label, _width in display_columns_for_rows(rows)]
    assert labels == [
        "数据日期",
        "手机/品牌/系列/型号/网络型号",
        "统货",
        "不开机",
        "开机屏好外屏碎",
        "来源图片",
    ]


def test_source_image_is_always_the_final_column():
    rows = [row(condition="开机靓好", price="700", source_image="")]
    labels = [label for _field, label, _width in display_columns_for_rows(rows)]
    assert labels == ["数据日期", "手机/品牌/系列/型号/网络型号", "开机靓好", "来源图片"]


def test_build_identity_uses_only_available_fields():
    assert build_identity(row()) == "手机 华为 荣耀畅玩系列 畅玩7x (3+32) BND-AL00"
    assert build_identity(row(series="")) == "手机 华为 畅玩7x (3+32) BND-AL00"
    assert build_identity(row(model_code="")) == "手机 华为 荣耀畅玩系列 畅玩7x (3+32)"
    assert build_identity(row(brand="", series="")) == "手机 畅玩7x (3+32) BND-AL00"
    assert build_identity(row(category="", brand="", series="", model="", model_code="")) == ""


def test_search_display_keeps_missing_identity_fields_out_of_display():
    rows = [row(series="", model_code="", condition="开机靓好", price="700")]
    result = [r for r in normalize_search_results(rows) if not r.get("_separator")]
    assert len(result) == 1
    assert result[0]["identity"] == "手机 华为 畅玩7x (3+32)"
    assert "  " not in result[0]["identity"]
    assert "/" not in result[0]["identity"]


def test_search_display_keeps_models_separate_and_inserts_spacing():
    rows = [
        row(model="畅玩8x (3+32)", model_code="BNK-AL00", condition="开机靓好", price="900"),
        row(model="畅玩7x (3+32)", model_code="BND-AL00", condition="开机靓好", price="700"),
    ]
    result = normalize_search_results(rows)
    assert any(r.get("_separator") for r in result)
    display = [r for r in result if not r.get("_separator")]
    assert [r["identity"] for r in display] == [
        "手机 华为 荣耀畅玩系列 畅玩7x (3+32) BND-AL00",
        "手机 华为 荣耀畅玩系列 畅玩8x (3+32) BNK-AL00",
    ]


def test_legacy_detail_recovers_all_raw_price_rows():
    payload = {"_rows": [
        row(record_id="old", data_date="2026-08-25", condition="开机靓好", price="700"),
        row(record_id="new", data_date="2026-08-31", condition="开机好碎", price="500"),
        row(record_id="third", data_date="2026-08-31", condition="废板·整机", price="240"),
    ]}
    rows = legacy_detail_rows(payload)
    assert [r["record_id"] for r in rows] == ["new", "third", "old"]
    assert [r["condition"] for r in rows] == ["开机好碎", "废板·整机", "开机靓好"]
    assert "condition" in {field for field, _label, _width in LEGACY_DETAIL_COLS}
    assert "model_code" in {field for field, _label, _width in LEGACY_DETAIL_COLS}


def test_display_columns_full_contract():
    labels = [label for _field, label, _width in DISPLAY_COLUMNS]
    assert labels == ["数据日期", "手机/品牌/系列/型号/网络型号", "来源图片"]
