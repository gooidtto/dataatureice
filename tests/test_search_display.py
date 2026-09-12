from search_display import build_display_columns, build_identity, normalize_search_results
from app_actions_fix import legacy_detail_rows


def row(**kw):
    base={"record_id":"id","data_date":"2026-08-31","category":"手机","subtype":"device","brand":"华为","series":"荣耀畅玩系列","model":"畅玩7x (3+32)","model_code":"BND-AL00","condition":"","price":"","source_image":"华为2.jpg"}
    base.update(kw); return base


def payloads(result): return [r for r in result if not r.get("_separator")]


def test_search_display_generates_condition_columns_from_actual_result():
    rows=[row(record_id="a",condition="开机靓好",price="700"),row(record_id="b",condition="开机好碎",price="500"),row(record_id="c",condition="开机碎屏",price="320"),row(record_id="d",condition="开机坏配件",price="240"),row(record_id="e",condition="废板·整机",price="240")]
    columns=build_display_columns(rows); labels=[label for _field,label,_width in columns]
    assert labels[:2]==["数据日期","手机/品牌/系列/型号/网络型号"]
    assert labels[-1]=="来源图片"
    assert set(labels[2:-1])=={"开机靓好","开机好碎","开机碎屏","开机坏配件","废板·整机"}
    display=payloads(normalize_search_results(rows))[0]; by_label={title:field for field,title,_width in columns}
    assert display[by_label["开机靓好"]]=="700"; assert display[by_label["开机好碎"]]=="500"; assert display[by_label["开机碎屏"]]=="320"; assert display[by_label["开机坏配件"]]=="240"; assert display[by_label["废板·整机"]]=="240"


def test_duplicate_condition_rows_are_not_silently_dropped():
    rows=[row(record_id="a",condition="开机靓好",price="700"),row(record_id="b",condition="开机靓好",price="680")]
    display=payloads(normalize_search_results(rows))[0]; field=next(field for field,title,_width in build_display_columns(rows) if title=="开机靓好")
    assert display[field]=="700 / 680"; assert len(display["_rows"])==2


def test_different_periods_are_newest_first_with_one_blank_separator():
    rows=[row(record_id="old",data_date="2026-08-25",condition="开机靓好",price="800"),row(record_id="new",data_date="2026-08-31",condition="开机好碎",price="500")]
    result=normalize_search_results(rows); separators=[r for r in result if r.get("_separator")]
    assert [r.get("data_date") for r in result if not r.get("_separator")=="period"] == ["2026-08-31", "2026-08-25"]
    assert len([r for r in separators if r.get("_separator")=="period"])==1
    assert [r["_period_index"] for r in payloads(result)]==[0,1]


def test_different_models_get_two_blank_separators():
    rows=[row(record_id="a",model="畅玩8x (3+32)",model_code="BNK-AL00",condition="开机靓好",price="900"),row(record_id="b",model="畅玩7x (3+32)",model_code="BND-AL00",condition="开机靓好",price="700")]
    result=normalize_search_results(rows)
    assert sum(1 for r in result if r.get("_separator")=="model")==2
    assert [r["_model_index"] for r in payloads(result)]==[0,1]


def test_same_model_different_periods_have_distinct_period_indexes():
    rows=[row(record_id="a",data_date="2026-08-31",condition="开机靓好",price="700"),row(record_id="b",data_date="2026-08-25",condition="开机靓好",price="800")]
    result=payloads(normalize_search_results(rows))
    assert [(r["data_date"],r["_model_index"],r["_period_index"]) for r in result]==[("2026-08-31",0,0),("2026-08-25",0,1)]


def test_build_identity_uses_only_available_fields():
    assert build_identity(row())=="手机 华为 荣耀畅玩系列 畅玩7x (3+32) BND-AL00"
    assert build_identity(row(series=""))=="手机 华为 畅玩7x (3+32) BND-AL00"
    assert build_identity(row(model_code=""))=="手机 华为 荣耀畅玩系列 畅玩7x (3+32)"
    assert build_identity(row(brand="",series=""))=="手机 畅玩7x (3+32) BND-AL00"
    assert build_identity(row(category="",brand="",series="",model="",model_code=""))==""


def test_detail_recovers_all_raw_price_rows_in_canonical_value_order():
    payload={"_rows":[row(record_id="old",data_date="2026-08-25",condition="开机靓好",price="700"),row(record_id="new",data_date="2026-08-31",condition="开机好碎",price="500"),row(record_id="third",data_date="2026-08-31",condition="废板·整机",price="240")]}
    rows=legacy_detail_rows(payload); assert [r["record_id"] for r in rows]==["old","new","third"]; assert len(rows)==3
