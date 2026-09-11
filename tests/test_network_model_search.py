from search_core import search_rows
import app_actions_fix


def row(**kw):
    r = {
        "record_id": "id",
        "data_date": "2026-08-31",
        "category": "手机",
        "brand": "华为/荣耀",
        "series": "",
        "model": "MATE X3",
        "model_code": "ALT-AL00",
        "alias": "ALT-AL00",
    }
    r.update(kw)
    return r


def test_network_model_query_matches_model_code():
    rows = [row(record_id="huawei", model_code="ATU-AL00", model="MATE 10"),
            row(record_id="other", brand="其它", model_code="ATU-AL00", model="OTHER")]
    result = search_rows(rows, "华为 ATU-AL00")
    assert [r["record_id"] for r in result] == ["huawei"]


def test_network_model_exact_match_ranks_first():
    rows = [row(record_id="prefix", model="ATU-AL00 Pro", model_code="ABC-ATU-AL00"),
            row(record_id="exact", model="MATE 10", model_code="ATU-AL00")]
    result = search_rows(rows, "ATU-AL00")
    assert result[0]["record_id"] == "exact"


def test_network_model_display_column_is_visible():
    fields = [field for field, _label, _width in app_actions_fix.DISPLAY_COLS]
    labels = {field: label for field, label, _width in app_actions_fix.DISPLAY_COLS}
    assert "model_code" in fields
    assert labels["model_code"] == "网络型号"
