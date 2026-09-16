from search_display import build_display_columns, build_identity, canonical_display_sort, model_family, normalize_search_results


def legacy_detail_rows(payload): return list(payload.get("_rows", []))
def row(**kw):
    base={"record_id":"id","data_date":"2026-08-31","category":"手机","subtype":"device","brand":"华为","series":"荣耀畅玩系列","model":"畅玩7x (3+32)","model_code":"BND-AL00","condition":"","price":"","source_image":"华为2.jpg"};base.update(kw);return base
def payloads(result): return [r for r in result if not r.get("_separator")]
def labels(columns): return [label for _field,label,_width in columns]

def test_search_display_generates_condition_columns_from_actual_result():
    rows=[row(record_id="a",condition="开机靓好",price="700"),row(record_id="b",condition="开机好碎",price="500"),row(record_id="c",condition="开机碎屏",price="320"),row(record_id="d",condition="开机坏配件",price="240"),row(record_id="e",condition="废板·整机",price="240")]
    columns=build_display_columns(rows);assert labels(columns)[:2]==["数据日期","手机/品牌/系列/型号/网络型号"];assert labels(columns)[-1]=="来源图片";assert set(labels(columns)[2:-1])=={"开机靓好","开机好碎","开机碎屏","开机坏配件","废板·整机"}
    display=payloads(normalize_search_results(rows))[0];by_label={title:field for field,title,_width in columns};assert display[by_label["开机靓好"]]=="700";assert display[by_label["开机好碎"]]=="500";assert display[by_label["开机碎屏"]]=="320";assert display[by_label["开机坏配件"]]=="240";assert display[by_label["废板·整机"]]=="240"

def test_each_result_block_owns_only_its_own_condition_columns():
    rows=[row(record_id="new",data_date="2026-08-31",condition="开机靓好",price="700"),row(record_id="old",data_date="2026-08-25",condition="废板·整机",price="240")];blocks=payloads(normalize_search_results(rows));assert labels(blocks[0]["_columns"])==["数据日期","手机/品牌/系列/型号/网络型号","开机靓好","来源图片"];assert labels(blocks[1]["_columns"])==["数据日期","手机/品牌/系列/型号/网络型号","废板·整机","来源图片"];assert [blocks[0][field] for field,title,_ in blocks[0]["_columns"] if title=="开机靓好"]==["700"];assert [blocks[1][field] for field,title,_ in blocks[1]["_columns"] if title=="废板·整机"]==["240"];assert "废板·整机" not in labels(blocks[0]["_columns"]);assert "开机靓好" not in labels(blocks[1]["_columns"])

def test_different_model_blocks_do_not_share_dynamic_columns():
    rows=[row(record_id="a",model="畅玩8x (3+32)",model_code="BNK-AL00",condition="开机好碎",price="900"),row(record_id="b",model="畅玩7x (3+32)",model_code="BND-AL00",condition="开机碎屏",price="700")];blocks=payloads(normalize_search_results(rows));assert set(labels(blocks[0]["_columns"])[2:-1])=={"开机碎屏"};assert set(labels(blocks[1]["_columns"])[2:-1])=={"开机好碎"}

def test_duplicate_condition_rows_are_not_silently_dropped():
    rows=[row(record_id="a",condition="开机靓好",price="700"),row(record_id="b",condition="开机靓好",price="680")];display=payloads(normalize_search_results(rows))[0];field=next(field for field,title,_width in build_display_columns(rows) if title=="开机靓好");assert display[field]=="700 / 680";assert len(display["_rows"])==2

def test_different_periods_are_sorted_newest_first_inside_the_same_model_group():
    rows=[row(record_id="old",data_date="2026-08-25",condition="开机靓好",price="800"),row(record_id="new",data_date="2026-08-31",condition="开机好碎",price="500")];result=normalize_search_results(rows);separators=[r for r in result if r.get("_separator")];assert [r["data_date"] for r in payloads(result)]==["2026-08-31","2026-08-25"];assert len([r for r in separators if r.get("_separator")=="period"])==0;assert [r["_period_index"] for r in payloads(result)]==[0,1]

def test_different_models_get_one_blank_separator_in_canonical_order():
    rows=[row(record_id="a",model="畅玩8x (3+32)",model_code="BNK-AL00",condition="开机靓好",price="900"),row(record_id="b",model="畅玩7x (3+32)",model_code="BND-AL00",condition="开机靓好",price="700")];result=normalize_search_results(rows);assert sum(1 for r in result if r.get("_separator")=="model")==1;assert [r["identity"] for r in payloads(result)]==["手机 华为 荣耀畅玩系列 畅玩7x (3+32) BND-AL00","手机 华为 荣耀畅玩系列 畅玩8x (3+32) BNK-AL00"];assert [r["_model_index"] for r in payloads(result)]==[0,1]

def test_interleaved_rows_are_reassembled_into_contiguous_model_groups():
    rows=[row(record_id="a1",brand="OPPO",series="A系列",model="A59",data_date="2026-08-31",condition="开机好屏",price="500"),row(record_id="b1",brand="华为",series="荣耀系列",model="畅玩7x",data_date="2026-08-31",condition="开机好屏",price="450"),row(record_id="a2",brand="OPPO",series="A系列",model="A59s",data_date="2026-08-25",condition="开机靓好",price="480")]
    result=normalize_search_results(rows);blocks=payloads(result)
    assert [b["_model_index"] for b in blocks]==[0,0,1]
    assert [b["data_date"] for b in blocks]==["2026-08-31","2026-08-25","2026-08-31"]
    assert [s["_separator"] for s in result if s.get("_separator")] == ["model"]

def test_same_model_different_network_codes_stay_in_one_model_group():
    rows=[row(record_id="new",data_date="2026-08-31",model_code="CPH1609",condition="开机好屏",price="500"),row(record_id="old",data_date="2026-08-25",model_code="CPH1701",condition="开机碎屏",price="260")]
    result=normalize_search_results(rows);blocks=payloads(result);assert len(blocks)==2;assert [b["_model_index"] for b in blocks]==[0,0];assert [b["_period_index"] for b in blocks]==[0,1];assert [s["_separator"] for s in result if s.get("_separator")] == []

def test_oppo_a59_suffix_candidates_share_one_model_family_across_dates():
    assert [model_family(v) for v in ["A59","A59s","A59m","A59t","A59 5G"]] == ["a59","a59","a59","a59","a59"]
    rows=[row(record_id="a59",brand="OPPO",series="A系列",model="A59",model_code="",data_date="2026-08-31",condition="开机好屏",price="500"),row(record_id="a59s",brand="OPPO",series="A系列",model="A59s",model_code="",data_date="2026-08-25",condition="开机靓好",price="480"),row(record_id="a59m",brand="OPPO",series="A系列",model="A59m",model_code="",data_date="2026-08-20",condition="开机好碎",price="300")]
    result=normalize_search_results(rows);blocks=payloads(result);assert [b["_model_index"] for b in blocks]==[0,0,0];assert [b["_period_index"] for b in blocks]==[0,1,2];assert [s["_separator"] for s in result if s.get("_separator")] == [];assert [b["identity"] for b in blocks] == ["手机 OPPO A系列 A59", "手机 OPPO A系列 A59s", "手机 OPPO A系列 A59m"]

def test_series_spelling_does_not_split_same_brand_model_family():
    rows=[row(record_id="new",brand="OPPO",series="A系列",model="A59",data_date="2026-08-31",condition="开机好屏",price="500"),row(record_id="old",brand="OPPO",series="A系列手机",model="A59s",data_date="2026-08-25",condition="开机靓好",price="480")]
    result=normalize_search_results(rows);blocks=payloads(result);assert len(blocks)==2;assert [b["_model_index"] for b in blocks]==[0,0];assert [b["data_date"] for b in blocks]==["2026-08-31","2026-08-25"];assert [s["_separator"] for s in result if s.get("_separator")] == []

def test_unrelated_model_numbers_remain_separate_families():
    rows=[row(record_id="a59",brand="OPPO",series="A系列",model="A59",condition="开机好屏",price="500"),row(record_id="a57",brand="OPPO",series="A系列",model="A57",condition="开机好屏",price="450")]
    result=normalize_search_results(rows);assert [b["_model_index"] for b in payloads(result)] == [0,1];assert [s["_separator"] for s in result if s.get("_separator")] == ["model"]

def test_build_identity_uses_only_available_fields():
    assert build_identity(row())=="手机 华为 荣耀畅玩系列 畅玩7x (3+32) BND-AL00";assert build_identity(row(series=""))=="手机 华为 畅玩7x (3+32) BND-AL00";assert build_identity(row(model_code=""))=="手机 华为 荣耀畅玩系列 畅玩7x (3+32)";assert build_identity(row(brand="",series=""))=="手机 畅玩7x (3+32) BND-AL00";assert build_identity(row(category="",brand="",series="",model="",model_code=""))==""

def test_detail_recovers_all_raw_price_rows_in_canonical_value_order():
    payload={"_rows":[row(record_id="old",data_date="2026-08-25",condition="开机靓好",price="700"),row(record_id="new",data_date="2026-08-31",condition="开机好碎",price="500"),row(record_id="third",data_date="2026-08-31",condition="废板·整机",price="240")]};rows=legacy_detail_rows(payload);assert [r["record_id"] for r in rows]==["old","new","third"];assert len(rows)==3

def test_canonical_display_sort_is_deterministic_and_ignores_input_order():
    rows=[row(record_id="b",brand="OPPO",series="A系列手机",model="A59s",data_date="2026-08-25"),row(record_id="a",brand="OPPO",series="A系列",model="A59",data_date="2026-08-31"),row(record_id="c",brand="华为",series="荣耀系列",model="畅玩7x",data_date="2026-08-31")]
    forward=canonical_display_sort(rows);reverse=canonical_display_sort(list(reversed(rows)))
    assert [(r["brand"],r["model"],r["data_date"]) for r in forward]==[(r["brand"],r["model"],r["data_date"]) for r in reverse]
    assert [(r["model"],r["data_date"]) for r in forward[:2]]==[("A59","2026-08-31"),("A59s","2026-08-25")]
