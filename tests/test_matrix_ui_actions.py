from search_display import DISPLAY_COLUMNS, display_columns_for_rows
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


def test_matrix_headers_default_to_fixed_contract():
    assert matrix_headers() == ["数据日期", "手机/品牌/系列/型号/网络型号", "来源图片"]


def test_matrix_headers_follow_raw_search_columns():
    rows = [row(condition="开机靓好", price="700"), row(condition="废板·整机", price="240")]
    expected = [label for _field, label, _width in display_columns_for_rows(rows)]
    assert matrix_headers(rows) == expected


def test_visible_matrix_row_keeps_each_raw_condition():
    rows = [
        row(record_id="a", condition="开机靓好", price="700"),
        row(record_id="b", condition="开机好屏", price="500"),
        row(record_id="c", condition="开机好碎", price="450"),
        row(record_id="d", condition="开机碎屏", price="320"),
        row(record_id="e", condition="开机坏配件", price="240"),
        row(record_id="f", condition="废板·整机", price="240"),
    ]
    display = visible_matrix_rows(rows)
    assert len(display) == 1
    assert matrix_values(display[0], rows)[1] == "手机 华为 荣耀畅玩系列 畅玩7x (3+32) BND-AL00"
    assert display[0]["开机靓好"] == "700"
    assert display[0]["开机好屏"] == "500"
    assert display[0]["开机好碎"] == "450"
    assert display[0]["开机碎屏"] == "320"
    assert display[0]["开机坏配件"] == "240"
    assert display[0]["废板·整机"] == "240"


def test_unusual_screen_quote_keeps_its_original_condition_name():
    rows = [row(record_id="a", condition="开机屏好外屏碎", price="60")]
    display = visible_matrix_rows(rows)
    assert len(display) == 1
    assert display[0]["开机屏好外屏碎"] == "60"


def test_repeated_prices_are_all_rendered_high_to_low_in_same_condition():
    rows = [
        row(record_id="a", condition="开机好", price="60"),
        row(record_id="b", condition="开机好", price="600", source_image="华为3.jpg"),
    ]
    display = visible_matrix_rows(rows)
    assert display[0]["开机好"] == "600\n60"
    assert display[0]["source_image"] == "华为2.jpg；华为3.jpg"


def test_matrix_favorite_payload_keeps_all_source_price_records():
    payload = {"_rows": [row(record_id="a"), row(record_id="b", condition="开机好碎", price="500"), row(record_id="a")]}
    raw = raw_rows_for_payloads([payload])
    assert [r["record_id"] for r in raw] == ["a", "b"]
