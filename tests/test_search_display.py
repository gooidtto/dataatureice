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


def labels(columns):
    return [label for _field, label, _width in columns]


def test_search_display_uses_each_raw_condition_and_price_descending():
    rows = [
        row(record_id="a", data_date="2026-08-31", condition="开机靓好", price="700"),
        row(record_id="b", data_date="2026-08-31", condition="开机好屏", price="500"),
        row(record_id="c", data_date="2026-08-31", condition="开机好碎", price="450"),
        row(record_id="d", data_date="2026-08-31", condition="开机碎屏", price="320"),
        row(record_id="e", data_date="2026-08-31", condition="开机坏配件", price="240"),
        row(record_id="f", data_date="2026-08-31", condition="废板·整机", price="240"),
        row(record_id="g", data_date="2026-08-31", condition="开机屏好外屏碎", price="60"),
    ]
    assert dynamic_quote_columns(rows) == (
        "开机靓好", "开机好屏", "开机好碎", "开机碎屏", "开机坏配件", "废板·整机", "开机屏好外屏碎"
    )
    result = normalize_search_results(rows)
    assert len(result) == 1
    display = result[0]
    assert labels(display["_columns"]) == [
        "数据日期", "手机/品牌/系列/型号/网络型号", "开机靓好", "开机好屏", "开机好碎", "开机碎屏", "开机坏配件", "废板·整机", "开机屏好外屏碎", "来源图片"
    ]
    assert display["开机靓好"] == "700"
    assert display["开机好屏"] == "500"
    assert display["开机好碎"] == "450"
    assert display["开机碎屏"] == "320"
    assert display["开机坏配件"] == "240"
    assert display["废板·整机"] == "240"
    assert display["开机屏好外屏碎"] == "60"


def test_each_result_has_its_own_columns():
    rows = [
        row(record_id="a", data_date="2026-08-31", model="畅玩7x", condition="开机靓好", price="700"),
        row(record_id="b", data_date="2026-08-31", model="畅玩7x", condition="开机好屏", price="500"),
        row(record_id="c", data_date="2026-08-21", model="畅玩6x", condition="统货", price="600"),
        row(record_id="d", data_date="2026-08-21", model="畅玩6x", condition="屏坏", price="180"),
    ]
    result = normalize_search_results(rows)
    assert len(result) == 2
    first, second = result
    assert labels(first["_columns"]) == ["数据日期", "手机/品牌/系列/型号/网络型号", "开机靓好", "开机好屏", "来源图片"]
    assert labels(second["_columns"]) == ["数据日期", "手机/品牌/系列/型号/网络型号", "统货", "屏坏", "来源图片"]
    assert "统货" not in first
    assert "开机靓好" not in second


def test_same_condition_values_are_sorted_high_to_low_inside_its_column():
    rows = [
        row(record_id="a", condition="开机好", price="60"),
        row(record_id="b", condition="开机好", price="600"),
        row(record_id="c", condition="开机好", price="120"),
    ]
    result = normalize_search_results(rows)
    assert result[0]["开机好"] == "600\n120\n60"


def test_source_image_is_always_the_final_column():
    rows = [row(condition="开机靓好", price="700", source_image="")]
    assert labels(display_columns_for_rows(rows)) == ["数据日期", "手机/品牌/系列/型号/网络型号", "开机靓好", "来源图片"]


def test_identity_is_first_two_columns_and_quote_columns_follow():
    rows = [row(condition="开机靓好", price="700")]
    cols = display_columns_for_rows(rows)
    assert cols[0][0] == "data_date"
    assert cols[1][0] == "identity"
    assert cols[2][0] == "开机靓好"
    assert cols[-1][0] == "source_image"


def test_build_identity_uses_only_available_fields():
    assert build_identity(row()) == "手机 华为 荣耀畅玩系列 畅玩7x (3+32) BND-AL00"
    assert build_identity(row(series="")) == "手机 华为 畅玩7x (3+32) BND-AL00"
    assert build_identity(row(model_code="")) == "手机 华为 荣耀畅玩系列 畅玩7x (3+32)"
    assert build_identity(row(brand="", series="")) == "手机 畅玩7x (3+32) BND-AL00"
    assert build_identity(row(category="", brand="", series="", model="", model_code="")) == ""


def test_search_display_keeps_missing_identity_fields_out_of_display():
    rows = [row(series="", model_code="", condition="开机靓好", price="700")]
    result = normalize_search_results(rows)
    assert len(result) == 1
    assert result[0]["identity"] == "手机 华为 畅玩7x (3+32)"
    assert "  " not in result[0]["identity"]
    assert "/" not in result[0]["identity"]


def test_search_display_keeps_models_and_dates_as_separate_results():
    rows = [
        row(record_id="a", data_date="2026-08-31", model="畅玩7x", condition="开机靓好", price="700"),
        row(record_id="b", data_date="2026-08-21", model="畅玩6x", condition="统货", price="600"),
    ]
    result = normalize_search_results(rows)
    assert [(r["data_date"], r["identity"]) for r in result] == [
        ("2026-08-21", "手机 华为 荣耀畅玩系列 畅玩6x BND-AL00"),
        ("2026-08-31", "手机 华为 荣耀畅玩系列 畅玩7x BND-AL00"),
    ] or [(r["data_date"], r["identity"]) for r in result] == [
        ("2026-08-31", "手机 华为 荣耀畅玩系列 畅玩7x BND-AL00"),
        ("2026-08-21", "手机 华为 荣耀畅玩系列 畅玩6x BND-AL00"),
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


def test_display_columns_full_contract_is_fixed_only():
    assert labels(DISPLAY_COLUMNS) == ["数据日期", "手机/品牌/系列/型号/网络型号", "来源图片"]
