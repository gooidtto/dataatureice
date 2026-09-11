from search_display import DISPLAY_COLUMNS
from matrix_ui_actions import matrix_headers, matrix_values, raw_rows_for_payloads, visible_matrix_rows


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
        "condition": "开机靓好",
        "price": "700",
        "unit": "CNY/台",
        "source_image": "华为2.jpg",
    }
    base.update(kw)
    return base


def test_matrix_headers_follow_new_display_contract():
    assert matrix_headers() == [label for _field, label, _width in DISPLAY_COLUMNS]


def test_visible_matrix_row_keeps_horizontal_price_columns_and_raw_rows():
    rows = [
        row(record_id="a", condition="开机靓好", price="700"),
        row(record_id="b", condition="开机好碎", price="500"),
        row(record_id="c", condition="开机碎屏", price="320"),
        row(record_id="d", condition="开机坏配件", price="240"),
        row(record_id="e", condition="废板·整机", price="240"),
    ]
    display = visible_matrix_rows(rows)
    assert len(display) == 1
    assert matrix_values(display[0])[1] == "手机 华为 荣耀畅玩系列 畅玩7x (3+32) BND-AL00"
    assert display[0]["condition_grade"] == "700"
    assert display[0]["condition_good_broken"] == "500"
    assert display[0]["condition_cracked"] == "320"
    assert display[0]["condition_bad_parts"] == "240"
    assert display[0]["condition_waste"] == "240"
    assert "开机靓好：700 CNY/台" in display[0]["quote_detail"]
    assert "开机好碎：500 CNY/台" in display[0]["quote_detail"]
    assert "开机碎屏：320 CNY/台" in display[0]["quote_detail"]
    assert "开机坏配件：240 CNY/台" in display[0]["quote_detail"]
    assert "废板·整机：240 CNY/台" in display[0]["quote_detail"]


def test_unusual_source_condition_is_not_invented_as_another_bucket():
    rows = [row(record_id="a", condition="开机屏好外屏碎", price="60")]
    display = visible_matrix_rows(rows)
    assert len(display) == 1
    assert all(not display[0][field] for field, _label, _width in DISPLAY_COLUMNS if field.startswith("condition_"))
    assert "开机屏好外屏碎：60 CNY/台" in display[0]["quote_detail"]


def test_repeated_quote_values_are_all_rendered():
    rows = [
        row(record_id="a", condition="开机好", price="60"),
        row(record_id="b", condition="开机好", price="60", source_image="华为3.jpg"),
    ]
    display = visible_matrix_rows(rows)
    assert display[0]["condition_grade"] == "60 / 60"
    assert display[0]["quote_detail"].count("开机好：60 CNY/台") == 2
    assert display[0]["source_image"] == "华为2.jpg；华为3.jpg"


def test_matrix_favorite_payload_keeps_all_source_price_records():
    payload = {"_rows": [row(record_id="a"), row(record_id="b", condition="开机好碎", price="500"), row(record_id="a")]}
    raw = raw_rows_for_payloads([payload])
    assert [r["record_id"] for r in raw] == ["a", "b"]
