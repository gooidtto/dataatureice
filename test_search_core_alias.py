from search_core import search_rows


def test_oppo_a59_matches_model_and_alias_without_leaking_brand():
    rows = [
        {"category": "手机", "brand": "OPPO", "series": "A系列", "model": "A59", "model_code": "A59", "alias": "A59 4G"},
        {"category": "手机", "brand": "OPPO", "series": "A系列", "model": "A59s", "model_code": "A59s", "alias": ""},
        {"category": "手机", "brand": "vivo", "series": "A系列", "model": "A59", "model_code": "A59", "alias": ""},
        {"category": "手机", "brand": "OPPO", "series": "R系列", "model": "R11", "model_code": "R11", "alias": ""},
    ]
    result = search_rows(rows, "oppo A59")
    assert [r["model"] for r in result] == ["A59", "A59s"]


def test_alias_can_be_used_as_model_search_term():
    rows = [
        {"category": "手机", "brand": "OPPO", "series": "A系列", "model": "A5", "model_code": "CPH1701", "alias": "A59"},
        {"category": "手机", "brand": "OPPO", "series": "A系列", "model": "A57", "model_code": "CPH1701", "alias": ""},
    ]
    result = search_rows(rows, "OPPO A59")
    assert len(result) == 1
    assert result[0]["model"] == "A5"
