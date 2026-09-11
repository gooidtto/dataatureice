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


def test_matrix_values_use_each_payloads_own_columns():
    rows = [
        row(record_id="a", condition="开机靓好", price="700"),
        row(record_id="b", condition="开机好屏", price="500"),
    ]
    display = visible_matrix_rows(rows)[0]
    assert matrix_headers(display["_rows"]) == ["数据日期", "手机/品牌/系列/型号/网络型号", "开机靓好", "开机好屏", "来源图片"]
    values = matrix_values(display, display["_rows"])
    assert values[2:4] == ["700", "500"]
    assert values[-1] == "华为2.jpg"


def test_unusual_raw_condition_is_a_real_column():
    rows = [row(record_id="a", condition="开机屏好外屏碎", price="60")]
    display = visible_matrix_rows(rows)[0]
    assert [c[1] for c in display["_columns"]] == ["数据日期", "手机/品牌/系列/型号/网络型号", "开机屏好外屏碎", "来源图片"]
    assert display["开机屏好外屏碎"] == "60"


def test_independent_results_do_not_inherit_quote_columns():
    rows = [
        row(record_id="a", data_date="2026-08-31", model="畅玩7x", condition="开机靓好", price="700"),
        row(record_id="b", data_date="2026-08-21", model="畅玩6x", condition="统货", price="600"),
    ]
    displays = visible_matrix_rows(rows)
    assert len(displays) == 2
    first, second = displays
    first_labels = [label for _field, label, _width in first["_columns"]]
    second_labels = [label for _field, label, _width in second["_columns"]]
    assert first_labels[-2] == "开机靓好"
    assert second_labels[-2] == "统货"
    assert "统货" not in first
    assert "开机靓好" not in second


def test_repeated_prices_are_sorted_high_to_low_inside_same_condition():
    rows = [
        row(record_id="a", condition="开机好", price="60"),
        row(record_id="b", condition="开机好", price="600"),
        row(record_id="c", condition="开机好", price="120"),
    ]
    display = visible_matrix_rows(rows)[0]
    assert display["开机好"] == "600\n120\n60"


def test_matrix_favorite_payload_keeps_all_source_price_records():
    payload = {"_rows": [row(record_id="a"), row(record_id="b", condition="开机好碎", price="500"), row(record_id="a")]}
    raw = raw_rows_for_payloads([payload])
    assert [r["record_id"] for r in raw] == ["a", "b"]


def test_columns_accept_fixed_width_contract():
    assert DISPLAY_COLUMNS[0][2] == 115
    assert DISPLAY_COLUMNS[1][2] == 380
    assert DISPLAY_COLUMNS[-1][2] == 140
    assert display_columns_for_rows([row(condition="开机靓好", price="700")])[-1][0] == "source_image"
