from search_display import normalize_search_results


def _row(date, condition, price, model_code="CPH0001", source_image="img-a"):
    return {
        "category": "手机",
        "brand": "OPPO",
        "series": "A",
        "model": "A59",
        "model_code": model_code,
        "data_date": date,
        "condition": condition,
        "price": price,
        "source_image": source_image,
        "record_id": f"{date}-{condition}-{price}",
    }


def test_oppo_a59_result_contract_keeps_required_column_order_and_local_conditions():
    rows = [
        _row("2026-08-31", "开机好屏", "500"),
        _row("2026-08-31", "开机碎屏", "300"),
        _row("2026-08-25", "开机好屏", "480", source_image="img-b"),
    ]
    blocks = [x for x in normalize_search_results(rows) if not x.get("_separator")]
    assert len(blocks) == 2

    for block in blocks:
        columns = block["_columns"]
        titles = [title for _field, title, _width in columns]
        assert titles[0] == "数据日期"
        assert titles[1] == "手机/品牌/系列/型号/网络型号"
        assert titles[-1] == "来源图片"
        assert titles.index("数据日期") < titles.index("来源图片")
        assert titles.index("手机/品牌/系列/型号/网络型号") < titles.index("来源图片")
        assert block["identity"] == "手机 OPPO A A59 CPH0001"

    newest = blocks[0]
    older = blocks[1]
    assert "开机好屏" in [title for _field, title, _width in newest["_columns"]]
    assert "开机碎屏" in [title for _field, title, _width in newest["_columns"]]
    assert "开机碎屏" not in [title for _field, title, _width in older["_columns"]]
    assert newest["source_image"] == "img-a"
    assert older["source_image"] == "img-b"


def test_result_blocks_never_use_a_global_condition_column_set():
    a = _row("2026-08-31", "开机好屏", "500", model_code="A59", source_image="a")
    b = _row("2026-08-31", "废板·整机", "100", model_code="A60", source_image="b")
    blocks = [x for x in normalize_search_results([a, b]) if not x.get("_separator")]
    assert len(blocks) == 2
    titles = [[title for _field, title, _width in x["_columns"]] for x in blocks]
    assert "开机好屏" in titles[0]
    assert "废板·整机" not in titles[0]
    assert "废板·整机" in titles[1]
    assert "开机好屏" not in titles[1]
